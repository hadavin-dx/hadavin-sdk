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
"""

from __future__ import annotations

import logging
import socketserver
import sys
from typing import Any, ClassVar, Final
from wsgiref.simple_server import ServerHandler, WSGIRequestHandler, WSGIServer

from hadavin_sdk.triggers.endpoint import STATUS_TEXT

MAX_REQUEST_LINE: Final[int] = 65536  # the cap the stdlib handler uses
STALLED_STATUS: Final[int] = 400  # the client sent nothing more until the socket timeout
LONG_LINE_STATUS: Final[int] = 414

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

    error_status = STATUS_TEXT[503]
    error_headers: ClassVar[list[tuple[str, str]]] = [("Content-Length", "0")]
    error_body = b""

    def log_exception(self, exc_info: Any) -> None:
        kind = exc_info[0] if exc_info else None
        _LOG.error("trigger server: application error: %s", getattr(kind, "__name__", "unknown"))

    def error_output(self, environ: Any, start_response: Any) -> list[bytes]:
        start_response(self.error_status, self.error_headers[:], sys.exc_info())
        return [self.error_body]


class QuietRequestHandler(WSGIRequestHandler):
    """One connection, one request. Refusals made before the application runs have an empty body."""

    def log_message(self, format: str, *args: Any) -> None:
        """Nothing: the arguments hold the request line, which is text chosen by the caller."""

    def get_stderr(self) -> Any:
        return _NoStream()

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Status line and an empty body. `message` and `explain` can repeat the request and are dropped."""
        _LOG.info("trigger status=%d sender=- (refused before the endpoint)", code)
        self.send_response_only(code)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

    def handle(self) -> None:
        try:
            self._serve()
        except TimeoutError:
            self._refuse_stalled()
        except Exception as exc:  # noqa: BLE001 - one broken connection never prints or stops the server
            _LOG.warning("trigger server: connection ended: %s", type(exc).__name__)

    def _serve(self) -> None:
        """The steps of the stdlib `handle`, with the quiet application handler."""
        self.raw_requestline = self.rfile.readline(MAX_REQUEST_LINE + 1)
        if len(self.raw_requestline) > MAX_REQUEST_LINE:
            self.requestline = self.request_version = self.command = ""
            self.send_error(LONG_LINE_STATUS)
            return
        if (
            not self.parse_request()
        ):  # it has answered through send_error, or the client sent nothing
            return
        handler = QuietWSGIHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ(), multithread=True
        )
        handler.request_handler = self  # type: ignore[attr-defined]  # as the stdlib does, for close()
        handler.run(self.server.get_app())  # type: ignore[attr-defined]

    def _refuse_stalled(self) -> None:
        """The socket timed out while the request line or the headers were read: nothing was answered yet."""
        if not hasattr(self, "request_version"):
            self.request_version = ""
        try:
            self.send_error(STALLED_STATUS)
        except OSError as exc:  # not writable any more: just close
            _LOG.info("trigger server: stalled client gone: %s", type(exc).__name__)


class QuietServer(socketserver.ThreadingMixIn, WSGIServer):
    """One thread per connection, so a request that waits for its row does not hold up the next one."""

    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        """The stdlib prints the traceback and the client address here; this logs the class name."""
        exc = sys.exception()
        _LOG.warning("trigger server: connection error: %s", type(exc).__name__)
