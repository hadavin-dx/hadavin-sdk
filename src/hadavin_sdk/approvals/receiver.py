"""Inbound approval callbacks. Framework-free: ``handle_slack_action`` maps (headers, body) to (status, body).

It verifies the request, records the decision (``record_only``) and answers in well under Slack's 3 seconds.
It never executes: ``tick`` reconcile runs approved plans, so a Slack retry can never cause double work.
Production hosting is decided at S11; ``serve`` is a stdlib server for development.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler
from socketserver import BaseServer

from hadavin_sdk import defaults
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
    longer an exact ``Approvals`` (its class was swapped), or it holds a real service now. Empty: serve it."""
    if type(approvals) is not Approvals:
        return ("the approvals object is no longer an exact Approvals",)
    return Approvals.real_now(approvals)


_LAST_LOGGED: dict[str, float] = {}


def _refused(now_real: tuple[str, ...]) -> None:
    """One WARNING line for a refused request, at most one per ``BIND_REFUSAL_LOG_INTERVAL_S`` seconds for each
    set of services named (a client that keeps calling cannot fill the log). The clock is ``time.monotonic``."""
    key = ", ".join(now_real)
    now = time.monotonic()
    last = _LAST_LOGGED.get(key)
    if last is not None and now - last < defaults.BIND_REFUSAL_LOG_INTERVAL_S:
        return
    if len(_LAST_LOGGED) >= defaults.BIND_REFUSAL_LOG_KEYS:  # bounded: forget the oldest entries
        _LAST_LOGGED.pop(next(iter(_LAST_LOGGED)))
    _LAST_LOGGED[key] = now
    _LOG.warning(
        "request refused: a real service is held on a public bind with no reason (%s)", key
    )


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
    is no longer an exact ``Approvals`` (a swapped ``__class__``); the private slots are set once by ``__setattr__``,
    and a person who writes them with ``object.__setattr__`` is caught by that request check."""
    if type(approvals) is not Approvals:
        raise BindRefused(
            "serve needs an Approvals made by the core (not a subclass or a look-alike): the guard cannot trust "
            "an object that answers for itself"
        )
    if approvals.config is None:
        raise BindRefused(
            "serve needs approvals built with a config (Approvals(..., config=config), or build()); "
            "these were built by hand with no config"
        )
    if approvals.config is not config:
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
        held=Approvals.held_services(approvals),
        frozen=approvals.config_facts,
    )
