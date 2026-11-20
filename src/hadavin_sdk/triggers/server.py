"""The stdlib server classes of the trigger worker, made quiet.

The stock classes answer a broken request with a page of text that repeats the request line, print a
traceback when a client stalls before its headers end, and answer a failed application with a line of
text. Here every refusal has an empty body, nothing is printed, and a failure is one log line on
``hadavin_sdk.triggers`` with the status or the class name of the exception: never its message, the
request line, a header or the body.

Answers written here, before the endpoint is reached: 400 for a request line or header block that is
not HTTP, and for a client that sends nothing more until the socket timeout; 414 for a request line
over the stdlib cap; 431 for too many or too long headers; 503 when the application raised. A client
that is gone gets nothing; its connection is closed.

Also refused here with 400, before the body is read: an HTTP version of 2.0 or higher (the stdlib
parser says 505; no refusal made here is a 5xx); a header whose name holds an underscore (the
application sees `X_Name` and `X-Name` as one name, and a proxy in front may not, so a caller could
pass a header the proxy never checked); more than one Content-Length header, equal or not; any
Transfer-Encoding header. A request line with no version (the old `GET /path` form) gets no answer:
the connection is closed. The application sees only what the request and the server set: no variable
of the process environment can stand in for a header that was not sent. These refusals are logged at
DEBUG: their number is chosen by whoever can reach the port.
"""

from __future__ import annotations

import logging
import socketserver
import sys
from email.message import Message
from typing import Any, ClassVar, Final
from wsgiref.simple_server import ServerHandler, WSGIRequestHandler, WSGIServer

from hadavin_sdk.triggers.endpoint import STATUS_TEXT

MAX_REQUEST_LINE: Final[int] = 65536  # the cap the stdlib handler uses
STALLED_STATUS: Final[int] = 400  # the client sent nothing more until the socket timeout
LONG_LINE_STATUS: Final[int] = 414
SERVER_ERROR: Final[int] = 500  # no refusal made here has a status from this number up

_LOG = logging.getLogger("hadavin_sdk.triggers")


class _NoStream:
    """Takes the place of stderr for the stdlib code: what is written to it is dropped."""

    def write(self, text: str) -> int:
        return len(text)

    def writelines(self, lines: Any) -> None:
        return None

    def flush(self) -> None:
        return None


class QuietWSGIHandler(ServerHandler):
    """Runs the application for one request. A failure is 503 with an empty body, logged by class name."""

    server_software = None  # no Server header: it would name the Python version
    error_status = STATUS_TEXT[503]
    error_headers: ClassVar[list[tuple[str, str]]] = [("Content-Length", "0")]
    error_body = b""
    os_environ: ClassVar[
        dict[str, str]
    ] = {}  # the stdlib default is a copy of the process environment

    def log_exception(self, exc_info: Any) -> None:
        kind = exc_info[0] if exc_info else None
        _LOG.error("trigger server: application error: %s", getattr(kind, "__name__", "unknown"))

    def error_output(self, environ: Any, start_response: Any) -> list[bytes]:
        start_response(self.error_status, self.error_headers[:], sys.exc_info())
        return [self.error_body]


class QuietRequestHandler(WSGIRequestHandler):
    """One connection, one request. Refusals made before the application runs have an empty body."""

    server_version = "trigger"  # the stdlib default names its own and the Python version
    sys_version = ""
    _answer_begun = False  # True once a refusal's status line was handed to the socket

    def log_message(self, format: str, *args: Any) -> None:
        """Nothing: the arguments hold the request line, which is text chosen by the caller."""

    def get_stderr(self) -> Any:
        return _NoStream()

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Status line and an empty body. `message` and `explain` can repeat the request and are dropped."""
        if (
            code >= SERVER_ERROR
        ):  # the stdlib parser answers 505 for HTTP/2.0 and up: a caller's mistake
            code = STALLED_STATUS
        self._answer_begun = True
        _LOG.debug("trigger status=%d sender=- (refused before the endpoint)", code)
        self.send_response_only(code)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

    def handle(self) -> None:
        try:
            self._serve()
        except Exception as exc:  # noqa: BLE001 - one broken connection never prints or stops the server
            _LOG.warning("trigger server: connection ended: %s", type(exc).__name__)

    def _serve(self) -> None:
        """The steps of the stdlib `handle`, with the quiet application handler. A socket timeout counts as
        a stalled client only while the request line and the headers are read (the endpoint reads the body
        and answers a timeout there itself); one raised later, by the application or while the answer is
        written, is not answered a second time."""
        try:
            self.raw_requestline = self.rfile.readline(MAX_REQUEST_LINE + 1)
        except TimeoutError:
            self._refuse_stalled()
            return
        if len(self.raw_requestline) > MAX_REQUEST_LINE:
            self.requestline = self.request_version = self.command = ""
            self.send_error(LONG_LINE_STATUS)
            return
        try:
            parsed = self.parse_request()
        except TimeoutError:
            self._refuse_stalled()
            return
        if not parsed:  # it has answered through send_error, or the client sent nothing
            return
        if not isinstance(
            self.headers, Message
        ):  # a request line with no version has no header block
            _LOG.debug(
                "trigger server: request line without an HTTP version, closed with no answer"
            )
            return
        if self._bad_headers():
            self.send_error(STALLED_STATUS)
            return
        handler = QuietWSGIHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ(), multithread=True
        )
        handler.request_handler = self  # type: ignore[attr-defined]  # as the stdlib does, for close()
        handler.run(self.server.get_app())  # type: ignore[attr-defined]

    def _bad_headers(self) -> bool:
        """True for header names and framing headers that are refused before the body is read."""
        if any("_" in name for name in self.headers.keys()):
            return True
        if len(self.headers.get_all("Content-Length", [])) > 1:
            return True
        return "Transfer-Encoding" in self.headers

    def _refuse_stalled(self) -> None:
        """The socket timed out while the request line or the headers were read. If an answer was begun
        (the timeout came while a refusal was written), nothing more is written: only the close is left."""
        if self._answer_begun:
            _LOG.debug("trigger server: timeout while an answer was written, closed")
            return
        if not hasattr(self, "request_version"):
            self.request_version = ""
        try:
            self.send_error(STALLED_STATUS)
        except OSError as exc:  # not writable any more: just close
            _LOG.debug("trigger server: stalled client gone: %s", type(exc).__name__)


class QuietServer(socketserver.ThreadingMixIn, WSGIServer):
    """One thread per connection, so a request that waits for its row does not hold up the next one."""

    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        """The stdlib prints the traceback and the client address here; this logs the class name."""
        exc = sys.exception()
        _LOG.warning("trigger server: connection error: %s", type(exc).__name__)
