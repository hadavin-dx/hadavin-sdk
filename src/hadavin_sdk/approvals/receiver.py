"""Inbound approval callbacks. Framework-free: ``handle_action`` maps (headers, body) to (status, body).

It verifies the request, records the decision (``record_only``) and answers well inside the reply deadline of an
interactive channel (the tightest one known is 3 seconds). It never executes: ``tick`` reconcile runs approved
plans, so a repeated delivery can never cause double work. Production hosting is decided at S11; ``serve`` is a
stdlib server for the demo stage and local runs, with no limit on the number of connections open at once (each
gets its own thread): production hosting (S11) must limit them. Any other host must route by
``callback_path(approvals)``.
"""

from __future__ import annotations

import io
import logging
import socket
import sys
import threading
import time
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hadavin_sdk.approvals.channel import CALLBACK_PATH_MAX_CHARS, valid_callback_path
from hadavin_sdk.approvals.hmac_v0 import MAX_HEADER_DIGITS, is_plain_digits
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.defaults import (
    RECEIVER_BACKLOG,
    RECEIVER_READ_TIMEOUT_MAX_S,
    RECEIVER_READ_TIMEOUT_S,
)
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.protocol import NotFound

MAX_BODY = 64 * 1024  # interactive callback payloads are a few KB
_MAX_NAME_CHARS = 64  # of a channel name shown in a refusal message
_MAX_LOG_CHARS = 200  # of a logged request line
_MAX_KINDS = 5  # error kinds named in one log line
_ERROR_LINE = "a request ended with an error: %s"
_LOG = logging.getLogger("hadavin_sdk.receiver")


def _plain(text: str, limit: int) -> str:
    """`text` cut to `limit` characters with every non-printable character (a line break, a terminal escape)
    replaced by `?`, so text that a caller wrote cannot forge or hide a log line."""
    return "".join(c if c.isprintable() else "?" for c in text[:limit])


class _Reported(threading.local):
    """Per request thread: has the failure of the click handler been logged (at error level) yet?"""

    flag = False


def _kinds(exc: BaseException | None) -> str:
    """The kinds (class names only, never the message) of `exc` and of the errors it was raised while handling,
    joined by `while handling`: at most five, and the walk stops at an error it has already named (a chain that
    loops back on itself); `...` is appended when the chain goes on."""
    kinds: list[str] = []
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen and len(kinds) < _MAX_KINDS:
        seen.add(id(exc))
        kinds.append(type(exc).__name__)
        exc = exc.__context__
    if exc is not None:
        kinds.append("...")
    return " while handling ".join(kinds)


def _shown_name(channel: object) -> str:
    """The channel's name for a refusal message: its `name` when that is a non-empty str, else its class name;
    whichever was chosen is then cut to 64 characters and every non-printable character becomes `?`."""
    name = getattr(channel, "name", None)
    chosen = name if isinstance(name, str) and name else type(channel).__name__
    return (
        _plain(str.__str__(chosen), _MAX_NAME_CHARS) or "?"
    )  # a plain str, also for a str subclass


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
    """401 for a bad or stale signature, 413 for an oversize body, else 200 (the outcome is audited, and tick
    updates the channel message; a refused click is not an HTTP error)."""
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
    character that is not an ASCII digit (so `5 ` with a trailing space is refused too: fail closed, stricter than
    HTTP). A number of more than 12 digits is answered as too large without being converted: `int()` raises past
    Python's digit limit (the same check as `hmac_v0.verify`: `MAX_HEADER_DIGITS` and `is_plain_digits`)."""
    if not values:
        return 0
    raw = values[0]
    if len(values) > 1 or not is_plain_digits(raw):
        return None
    return int(raw) if len(raw) <= MAX_HEADER_DIGITS else MAX_BODY + 1


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
    ``serve_forever()`` on the result. Raises ``ConfigError`` when the channel names no valid path or
    ``read_timeout_s`` is not a number (an int or a float, not a bool) above 0 and at most
    ``defaults.RECEIVER_READ_TIMEOUT_MAX_S``.

    A request (its first line, its headers and its body together) must arrive within ``read_timeout_s`` seconds;
    after that the connection is closed without an answer, which is what the standard library server does for a
    timeout. A failure while a click is handled is answered 500, so a sender that retries on 5xx delivers it again,
    and is logged at error level, once, where it happens (whatever kind of error it is, also a refused connection
    to a store that is down). No error of a request prints a traceback: the kind of error is logged in one line
    (enable debug level on the logger ``hadavin_sdk.receiver`` for the request lines and the hang-ups)."""
    if (
        type(read_timeout_s) not in (int, float)
        or not 0 < read_timeout_s <= RECEIVER_READ_TIMEOUT_MAX_S
    ):
        raise ConfigError(
            "read_timeout_s must be a number of seconds above 0 and at most "
            f"{RECEIVER_READ_TIMEOUT_MAX_S:g} (an int or a float, not a bool)"
        )
    path = callback_path(approvals)
    reported = _Reported()

    class Handler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            super().setup()
            reported.flag = False  # one thread serves one request; nothing is carried over
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
            # sender that retries on 5xx delivers the click again. It is logged here, at error level, BEFORE the
            # answer is written and whatever its kind (a refused connection to a store is a handler failure, not a
            # caller hanging up): if the write then fails, the standard library may swallow that error as a timeout
            # without ever calling `handle_error`, and the failure would be lost. `reported` tells `handle_error`
            # that this request's failure has its error line already, so the request gets exactly one.
            status, out, failed = 500, b"", True
            try:
                status, out = handle_action(approvals, dict(self.headers), body)
                failed = False
            finally:
                if failed:
                    reported.flag = True
                    _LOG.error(_ERROR_LINE, _kinds(sys.exception()))
                self._answer(status, out)

        def _answer(self, status: int, out: bytes = b"") -> None:
            # the answer is a few bytes: writing it has the same bound as reading the request
            self.connection.settimeout(read_timeout_s)
            self.send_response(status)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, format: str, *args: object) -> None:
            # The request line is in the arguments and any caller can write anything in it (a line break, a
            # terminal escape): build the text, cut it, and replace what is not printable before it is logged.
            # An error among the arguments (the standard library logs `Request timed out: %r` with the error) is
            # shown by its kind only: its message could carry request data.
            args = tuple(type(a).__name__ if isinstance(a, BaseException) else a for a in args)
            try:
                text = format % args
            except (TypeError, ValueError):
                text = format
            _LOG.debug("%s", _plain(text, _MAX_LOG_CHARS))

    class Server(ThreadingHTTPServer):
        request_queue_size = (
            RECEIVER_BACKLOG  # the standard library's 5 delays callers that arrive together
        )

        def handle_error(self, request: object, client_address: object) -> None:
            # Every error that ends a request arrives here; the standard library would print a traceback. One log
            # line with the kind of error only: no request text, no error message (it could carry request data).
            # A request gets exactly one error level line. When the click handler failed, `do_POST` has already
            # written it (the state `reported`, not the class of the error, says so: a store that refuses the
            # connection raises a `ConnectionError` too), and what arrives here is only a debug line. Otherwise a
            # caller that resets or closes the connection early is not a fault of this server: debug level, when
            # the hang-up is the whole story (no other error is its context); anything else is error level. An
            # operator who sees only the kind of error can enable debug level for the request lines.
            exc = sys.exception()
            already_logged = reported.flag
            hung_up = isinstance(exc, ConnectionError) and exc.__context__ is None
            _LOG.log(
                logging.DEBUG if already_logged or hung_up else logging.ERROR,
                _ERROR_LINE,
                _kinds(exc),
            )

    return Server((host, port), Handler)
