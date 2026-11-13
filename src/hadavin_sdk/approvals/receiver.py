"""Inbound approval callbacks. Framework-free: ``handle_slack_action`` maps (headers, body) to (status, body).

It verifies the request, records the decision (``record_only``) and answers in well under Slack's 3 seconds.
It never executes: ``tick`` reconcile runs approved plans, so a Slack retry can never cause double work.
Production hosting is decided at S11; ``serve`` is a stdlib server for development.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler
from socketserver import BaseServer

from hadavin_sdk import defaults, standins
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.bindguard import BindRefused, listen
from hadavin_sdk.config import Config
from hadavin_sdk.netguard import LOOPBACK_V4, is_loopback_host
from hadavin_sdk.store.protocol import NotFound

MAX_BODY = 64 * 1024  # Slack interactive payloads are a few KB
PATH = "/slack/actions"
_LOG = logging.getLogger("hadavin_sdk.receiver")


def handle_slack_action(
    approvals: Approvals, headers: Mapping[str, str], body: bytes
) -> tuple[int, bytes]:
    """401 for a bad or stale signature, 413 for an oversize body, else 200 (the outcome is audited and the
    Slack message updated; a refused click is not an HTTP error)."""
    if len(body) > MAX_BODY:
        return 413, b""
    try:
        _, reason = approvals.receive(headers, body, record_only=True)
    except NotFound:  # signed, but for an approval this deployment does not have
        _LOG.warning("channel action for an unknown approval")
        return 200, b""
    if reason == "bad_signature":
        return 401, b""
    _LOG.info("channel action: %s", reason)
    return 200, b""


def _recheck(approvals: object) -> tuple[str, ...]:
    """What makes this request refused on a bind other computers can reach with no reason given: the object is no
    longer an exact ``Approvals`` (its class was swapped), the ``Approvals`` class itself was changed since it was
    pinned, a slot is missing (``object.__delattr__``), or it holds a real service now. Empty: serve it. Never
    raises: any error reads as a refusal (the request is answered 503, not dropped)."""
    try:
        if type(approvals) is not Approvals:
            return ("the approvals object is no longer an exact Approvals",)
        if not standins.is_pinned_instance(approvals):
            return ("the Approvals class was changed after it was pinned",)
        # every slot is read: an empty one raises AttributeError, answered 503
        for slot in Approvals.__slots__:
            object.__getattribute__(approvals, slot)
        return Approvals.real_now(approvals)
    except (
        standins.SURPRISE_ERRORS
    ):  # a deleted slot or any unreadable state is refused, never dropped
        return ("the approvals object could not be read (a slot is missing)",)


_LAST_LOGGED: dict[str, float] = {}
_LAST_LOGGED_LOCK = threading.Lock()


def _refused(now_real: tuple[str, ...]) -> None:
    """One WARNING line for a refused request, at most one per ``BIND_REFUSAL_LOG_INTERVAL_S`` seconds for each
    set of services named (a client that keeps calling cannot fill the log). The clock is ``time.monotonic``.
    Every call moves its set to the end of the memory (the one forgotten first is the one used longest ago), under
    a lock; nothing raised here can stop the 503 from being written."""
    try:
        key = ", ".join(now_real)
        now = time.monotonic()
        with _LAST_LOGGED_LOCK:
            last = _LAST_LOGGED.pop(key, None)
            quiet = last is not None and now - last < defaults.BIND_REFUSAL_LOG_INTERVAL_S
            while len(_LAST_LOGGED) >= defaults.BIND_REFUSAL_LOG_KEYS:  # bounded: forget the oldest
                _LAST_LOGGED.pop(next(iter(_LAST_LOGGED)), None)
            _LAST_LOGGED[key] = last if quiet and last is not None else now
        if not quiet:
            _LOG.warning(
                "request refused: a real service is held on a public bind with no reason (%s)", key
            )
    except (
        standins.SURPRISE_ERRORS
    ):  # a log failure must not turn the 503 into a dropped connection
        return


def serve(
    approvals: Approvals,
    *,
    config: Config,
    host: str = LOOPBACK_V4,
    port: int = 8080,
    allow_public_bind_reason: str | None = None,
) -> BaseServer:  # not the concrete class: the repo scan reads that name as a server made here
    """A development server for ``POST /slack/actions``; call ``serve_forever()`` on the result.

    ``approvals`` must be an exact ``Approvals`` (a subclass or look-alike is refused: the guard cannot trust an
    object that answers for itself). ``config`` is required and must be the deployment's own (the one ``approvals``
    was built from: the check is ``approvals.config is config``). The services the approvals really hold are
    counted too: a real channel, store, model or source handed to ``build()`` (or a real channel, store or detector
    given to ``Approvals(...)``) makes a public bind refused even beside a stand-in config, and the refusal names
    it. What the config reached is the answer frozen when the approvals were made. Approvals built by hand have no
    config and are refused.

    The server is made by ``bindguard.listen``, the only place that creates a server socket: a ``host`` that other
    computers can reach is refused while any real service is configured, unless ``allow_public_bind_reason`` says
    why it must be (the usual setup is an HTTPS reverse proxy in front; the reason is logged). On such a bind with
    no reason the question is asked again at every request (answer 503, empty body, one log line): the objects the
    approvals hold can be replaced after the server started. The request check also refuses an object that
    is no longer an exact ``Approvals`` (a swapped ``__class__``), an ``Approvals`` class that changed since it was
    pinned, and a missing slot (answered 503 too, and ``serve`` itself refuses an object with any slot missing: every slot is read at the start); the private slots are set once by ``__setattr__`` and cannot be
    deleted by ``__delattr__``, and a person who writes or deletes them with ``object.__setattr__`` or
    ``object.__delattr__`` is caught by that request check (every slot is read, so each deleted slot is answered 503).
    Every class the guard judges is compared by identity, never by ``==`` or hash. A value too big to read within the
    budget counts as real (the public bind is refused, and the refusal line says ``over budget``, not ``real``).
    At the start the ``Approvals`` class is compared with its pin too: a method replaced or added after the pin
    is a ``BindRefused`` ("changed after it was pinned"), not a late 503.
    Only an ``on_decided`` made by ``make_on_decided`` (with an empty holder or, for approvals made by ``build()``,
    the core runtime in it) and a ``clock`` that is ``models.now`` or a ``fixed_clock`` of a plain ``datetime`` (no
    ``tzinfo`` or ``datetime.UTC``) are trusted as not holding a service. A refusal line shows
    only a plain word (an ASCII identifier of at most 40 characters) for a held name, a class name or an operator-config
    name, and a fixed label for anything else."""
    if type(approvals) is not Approvals:
        raise BindRefused(
            "serve needs an Approvals made by the core (not a subclass or a look-alike): the guard cannot trust "
            "an object that answers for itself"
        )
    # every attribute of the approvals is read here, inside the one refusal type: an unreadable object (a slot
    # deleted with ``object.__delattr__``, a mapping that raises) is a ``BindRefused``, not some other error
    try:
        # the question the per-request check asks first
        pinned = standins.is_pinned_instance(approvals)
        for slot in (
            Approvals.__slots__
        ):  # a deleted slot (any of them) is a refusal at the start, not a late 503
            object.__getattribute__(approvals, slot)
        approvals_config = approvals.config
        held = Approvals.held_services(approvals)
        frozen = approvals.config_facts
    except standins.SURPRISE_ERRORS:  # any error while reading is a refusal of the one type
        raise BindRefused(
            "serve could not read what the approvals hold (a slot is missing or an object raised): "
            "nothing is served"
        ) from None
    if not pinned:
        raise BindRefused(
            "the Approvals class was changed after it was pinned (a method was replaced or added): nothing is served"
        )
    if approvals_config is None:
        raise BindRefused(
            "serve needs approvals built with a config (Approvals(..., config=config), or build()); "
            "these were built by hand with no config"
        )
    if approvals_config is not config:
        raise BindRefused(
            "serve needs the config the approvals were built with (Approvals(..., config=config)); "
            "the config given is not that one"
        )

    # on a bind other computers can reach with no reason given, every request asks again what the approvals
    # hold, because a channel, store or detector can be replaced after the server started
    recheck = allow_public_bind_reason is None and not is_loopback_host(host)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if recheck and (now_real := _recheck(approvals)):
                _refused(now_real)
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            raw = self.headers.get("Content-Length") or "0"
            length = int(raw) if raw.isascii() and raw.isdigit() else -1
            if self.path != PATH:
                status, out = 404, b""
            elif length < 0:
                status, out = 400, b""
            elif length > MAX_BODY:
                status, out = 413, b""
            else:
                status, out = handle_slack_action(
                    approvals, dict(self.headers), self.rfile.read(length)
                )
            self.send_response(status)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, format: str, *args: object) -> None:
            _LOG.debug(format, *args)

    return listen(
        config,
        host,
        port,
        Handler,
        allow_public_bind_reason=allow_public_bind_reason,
        held=held,
        frozen=frozen,
    )


# Pin the classes the guard trusts NOW (at import), not at the first question: a change made after this import is
# seen. (A test fixture that patches one of them before this module is imported is outside the model.)
standins.pin_all()
