"""One answer for a request the fake servers cannot read, at the ONE place every handler method passes through.

Bug class: a request whose body or query has the wrong shape (a JSON list where an object is expected, a missing key,
`?limit=abc`) made a handler method raise KeyError, TypeError, ValueError, AttributeError or IndexError; the server
printed a traceback on its error output and sent NO answer, so the client waited for its own time limit. Fix: a handler
class that inherits `AnswersBadRequests` has every `do_*` method it defines wrapped here; such an error ends with ONE
fixed answer (status 400, no echo of what was sent) unless the answer had already started. The handler supplies the
answer in `_send_bad_request` (each fake has its own reply helper).

Standard: RFC 9110 section 15.5.1 (400: the server cannot process the request because of something that looks like a
client error). The handler methods are found by name (`do_GET`, `do_POST`, `do_PATCH`, `do_DELETE`, `do_PUT`)."""

from __future__ import annotations

import functools
import sys
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from lead_desk.config import is_loopback_host
from scripts.http_guard import HeadDeadline
from tools.refusing_args import LOOPBACK_HOST_TEXT

BAD_REQUEST_ERRORS = (KeyError, TypeError, ValueError, AttributeError, IndexError, RecursionError)
METHOD_NAMES = ("do_GET", "do_POST", "do_PATCH", "do_DELETE", "do_PUT")
BAD_REQUEST_TEXT = "bad request"  # the one fixed line every fake answers with
CLIENT_GONE = (ConnectionResetError, BrokenPipeError, ConnectionAbortedError, TimeoutError)
"""Errors that only mean the other side left or stalled (the same class src/lead_desk/server.py `_GONE` names)."""


def require_loopback_host(host: object) -> str:
    """The one refusal of a fake's listening host: only this computer (localhost or a loopback address). An empty or
    blank host is refused too (to a socket an empty host means "every interface"); fails closed on anything that is not
    text. Every fake (the three web fakes through QuietServer, the two mail fakes directly) calls this before it makes
    a socket."""
    if not isinstance(host, str) or not is_loopback_host(host):
        raise ValueError(LOOPBACK_HOST_TEXT)
    return host


class QuietServer(ThreadingHTTPServer):
    """The server class of every fake. The standard library prints a traceback to the error output for ANY exception in
    a handler thread; a test client that hangs up on purpose (a request with no body, a bad one, a late body) made the
    fake write its answer to a closed connection and print `Exception occurred during processing of request` into the
    middle of a test run. Fix at this one place: a client that left is silent; every other error is still reported.

    Second job, at the same one place: a fake has no sign-in, so it must listen on this computer only. The refusal of a
    host that is not loopback (the all-interfaces address, another computer's address, a name, an empty host) is made
    BEFORE the base class opens the port, so every fake and every future fake that extends this class has it. The one
    rule is `lead_desk.config.is_loopback_host`; there is no second copy."""

    daemon_threads = True

    def __init__(self, server_address: Any, request_handler_class: Any, bind_and_activate: bool = True) -> None:
        host = server_address[0] if isinstance(server_address, tuple) and server_address else None
        require_loopback_host(host)  # fails closed: anything unreadable is refused
        super().__init__(server_address, request_handler_class, bind_and_activate)

    def handle_error(self, request: Any, client_address: Any) -> None:
        if isinstance(sys.exception(), CLIENT_GONE):
            return
        super().handle_error(request, client_address)


def _shield(method: Callable[[Any], None]) -> Callable[[Any], None]:
    @functools.wraps(method)
    def run(self: AnswersBadRequests) -> None:
        try:
            method(self)
        except BAD_REQUEST_ERRORS:
            self.close_connection = True
            if not self._answer_started:
                self._send_bad_request()

    return run


class AnswersBadRequests(HeadDeadline, BaseHTTPRequestHandler):
    """Mix-in for a fake server's handler (list it BEFORE BaseHTTPRequestHandler, or just subclass it)."""

    _answer_started = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for name in METHOD_NAMES:
            method = cls.__dict__.get(name)
            if method is not None and not getattr(method, "__wrapped__", None):
                setattr(cls, name, _shield(method))

    def send_response(self, code: int, message: str | None = None) -> None:
        self._answer_started = True
        super().send_response(code, message)

    def _send_bad_request(self) -> None:
        raise NotImplementedError
