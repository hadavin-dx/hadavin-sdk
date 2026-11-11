"""Inbound approval callbacks. Framework-free: ``handle_action`` maps (headers, body) to (status, body).

It verifies the request, records the decision (``record_only``) and answers well inside the reply deadline of an
interactive channel (the tightest one known is 3 seconds). It never executes: ``tick`` reconcile runs approved
plans, so a repeated delivery can never cause double work. Production hosting is decided at S11; ``serve`` is a
stdlib server for the demo stage and local runs. Any other host must route by ``callback_path(approvals)``.
"""

from __future__ import annotations

import io
import logging
import socket
import sys
import time
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hadavin_sdk.approvals.channel import CALLBACK_PATH_MAX_CHARS, valid_callback_path
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.defaults import RECEIVER_READ_TIMEOUT_S
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.protocol import NotFound

MAX_BODY = 64 * 1024  # interactive callback payloads are a few KB
_MAX_NAME_CHARS = 64  # of a channel name shown in a refusal message
_LOG = logging.getLogger("hadavin_sdk.receiver")


def _shown_name(channel: object) -> str:
    """The channel's name for a refusal message: its `name` when that is a non-empty str, else its class name;
    whichever was chosen is then cut to 64 characters and every non-printable character becomes `?`."""
    name = getattr(channel, "name", None)
    chosen = name if isinstance(name, str) and name else type(channel).__name__
    text = str.__str__(chosen)[:_MAX_NAME_CHARS]  # a plain str, also for a str subclass
    return "".join(c if c.isprintable() else "?" for c in text) or "?"


def callback_path(approvals: Approvals) -> str:
    """The URL path the configured channel kind's callbacks are posted to, checked: there is no fallback path."""
    channel = approvals.channel
    # `getattr` only so that a missing attribute gives this message; it never supplies a path.
    path = getattr(channel, "callback_path", None)
    if not valid_callback_path(path):
        raise ConfigError(
            f"channel {_shown_name(channel)}: callback_path must be a path such as /channel/actions (a `/`, then "
            f"lower-case letters and digits in parts joined by `/` or `-`, at most {CALLBACK_PATH_MAX_CHARS} "
            "characters)"
        )
    return path


def handle_action(
    approvals: Approvals, headers: Mapping[str, str], body: bytes
) -> tuple[int, bytes]:
    """401 for a bad or stale signature, 413 for an oversize body, else 200 (the outcome is audited and the
    channel message updated; a refused click is not an HTTP error)."""
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


def body_length(values: list[str]) -> int | None:
    """The body length a request states, from every `Content-Length` header line it carries. No such line: 0.
    None (the request is refused with 400) for more than one line, an empty value, a sign, a space, or any
    character that is not an ASCII digit. A number of more than 12 digits is answered as too large without being
    converted: `int()` raises past Python's digit limit (the same guard as `hmac_v0.verify`)."""
    if not values:
        return 0
    raw = values[0]
    if len(values) > 1 or not (raw.isascii() and raw.isdigit()):
        return None
    return int(raw) if len(raw) <= 12 else MAX_BODY + 1


class _DeadlineReader(io.RawIOBase):
    """Reads from the connection until one fixed moment: every read waits only for the time that is left, so a
    caller who sends slowly, or less than announced, cannot hold the thread past that moment."""

    def __init__(self, connection: socket.socket, seconds: float) -> None:
        self._connection, self._end = connection, time.monotonic() + seconds

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        left = self._end - time.monotonic()
        if left <= 0:
            raise TimeoutError("the request was not received in time")
        self._connection.settimeout(left)
        return self._connection.recv_into(buffer)


def serve(
    approvals: Approvals,
    host: str = "127.0.0.1",
    port: int = 8080,
    read_timeout_s: float = RECEIVER_READ_TIMEOUT_S,
) -> ThreadingHTTPServer:
    """A stdlib server for ``POST`` to the configured channel's ``callback_path`` (every other path: 404); call
    ``serve_forever()`` on the result. Raises ``ConfigError`` when the channel names no valid path.

    A request (its first line, its headers and its body together) must arrive within ``read_timeout_s`` seconds;
    after that the connection is closed without an answer, which is what the standard library server does for a
    timeout. A failure while a click is handled is answered 500, so the sender delivers it again. No error of a
    request prints a traceback: the kind of error is logged in one line."""
    path = callback_path(approvals)

    class Handler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            super().setup()
            unbounded, self.rfile = (
                self.rfile,
                io.BufferedReader(_DeadlineReader(self.connection, read_timeout_s)),
            )
            unbounded.close()  # closes the file object only, not the connection

        def do_POST(self) -> None:
            # The path as written in the first line of the request (its second word). `self.path` is not used:
            # the standard library rewrites a path that starts with `//` to a single `/` before this method runs.
            # The path is compared first, so a request for any other path costs no further work.
            if self.requestline.split()[1:2] != [path]:
                return self._answer(404)
            length = body_length(self.headers.get_all("Content-Length") or [])
            if length is None:
                return self._answer(400)
            if length > MAX_BODY:
                return self._answer(413)
            body = self.rfile.read(length)
            # A failure while the click is handled (the store or the channel is down) is answered 500, so the
            # sender delivers the click again; the error then goes on to `handle_error` below.
            status, out = 500, b""
            try:
                status, out = handle_action(approvals, dict(self.headers), body)
            finally:
                self._answer(status, out)

        def _answer(self, status: int, out: bytes = b"") -> None:
            # the answer is a few bytes: writing it has the same bound as reading the request
            self.connection.settimeout(read_timeout_s)
            self.send_response(status)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, format: str, *args: object) -> None:
            _LOG.debug(format, *args)

    class Server(ThreadingHTTPServer):
        def handle_error(self, request: object, client_address: object) -> None:
            # Every error that ends a request arrives here; the standard library would print a traceback. One log
            # line with the kind of error only: no request text, no error message (it could carry request data).
            # A caller that resets or closes the connection early is not a fault of this server: debug level.
            exc = sys.exception()
            kinds: list[str] = []
            while exc is not None:
                kinds.append(type(exc).__name__)
                exc = exc.__context__
            hung_up = isinstance(sys.exception(), ConnectionError) and len(kinds) == 1
            _LOG.log(
                logging.DEBUG if hung_up else logging.ERROR,
                "a request ended with an error: %s",
                " while handling ".join(kinds),
            )

    return Server((host, port), Handler)
