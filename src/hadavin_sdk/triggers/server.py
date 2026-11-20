"""The stdlib server classes of the trigger worker, made quiet.

The stock classes answer a broken request with a page of text that repeats the request line, print a
traceback when a client stalls before its headers end, and answer a failed application with a line of
text. Here every refusal has an empty body, nothing is printed, and a failure is one log line on
``hadavin_sdk.triggers`` with the status or the class name of the exception: never its message, the
request line, a header or the body.

Answers written here, before the endpoint is reached: 400 for a request line or header block that is
not HTTP, and for a client that sends nothing more until the socket timeout; 414 for a request line
over the stdlib cap; 431 for too many or too long headers. A 503 is also written here when the application
raised: that is a failure, not a refusal of the request. A client
that is gone gets nothing; its connection is closed.

Also refused here with 400, before the body is read: an HTTP version of 2.0 or higher (the stdlib
parser says 505; no refusal made here is a 5xx; only the failure above is); a header whose name holds an underscore (the
application sees `X_Name` and `X-Name` as one name, and a proxy in front may not, so a caller could
pass a header the proxy never checked); more than one Content-Length header, equal or not; any
Transfer-Encoding header. A request line with no version (the old `GET /path` form) gets no answer:
the connection is closed. The application sees only what the request and the server set: no variable
of the process environment can stand in for a header that was not sent. These refusals are logged at
DEBUG: their number is chosen by whoever can reach the port.

Two bounds on what a client can hold: at most `max_connections` connection threads at one time (a connection over
the cap is closed at once, nothing is read or answered; logged at WARNING at most once a minute), and an absolute deadline, `read_deadline_s`, on the
TOTAL time from the accept until the request line, the headers and the body have been read (a client that
sends one byte every few seconds never trips the pause limit of a single read, but is cut at the deadline: the
read raises TimeoutError, which is answered 400 like a stalled client). The deadline ends with the last read;
the time the application then spends (waiting for its row) and the answer are not counted.
"""

from __future__ import annotations

import logging
import os
import socket
import socketserver
import sys
import threading
import time
from email.message import Message
from typing import Any, ClassVar, Final
from wsgiref.simple_server import ServerHandler, WSGIRequestHandler, WSGIServer

from hadavin_sdk.triggers.endpoint import STATUS_TEXT

MAX_REQUEST_LINE: Final[int] = 65536  # the cap the stdlib handler uses
STALLED_STATUS: Final[int] = 400  # the client sent nothing more until the socket timeout
LONG_LINE_STATUS: Final[int] = 414
MAX_CONNECTIONS: Final[int] = (
    256  # connection threads at one time; above `MAX_WAITING` of the worker
)
READ_DEADLINE_S: Final[float] = (
    30.0  # total time to read the request line, the headers and the body
)
SERVER_ERROR: Final[int] = 500  # no refusal made here has a status from this number up

CAP_WARN_EVERY_S: Final[float] = 60.0  # the connection cap is logged at WARNING at most this often

_LOG = logging.getLogger("hadavin_sdk.triggers")
_monotonic = time.monotonic  # the clock of the cap warning (a test replaces it)


def _level(exc: BaseException | None) -> int:
    """DEBUG for a connection that was reset, dropped or timed out (a port probe, a client that left: the
    number is chosen by whoever can reach the port); WARNING for anything else, which is a fault here."""
    return logging.DEBUG if isinstance(exc, OSError) else logging.WARNING


class _NoStream:
    """Takes the place of stderr for the stdlib code: what is written to it is dropped."""

    def write(self, text: str) -> int:
        return len(text)

    def writelines(self, lines: Any) -> None:
        return None

    def flush(self) -> None:
        return None


class _DeadlineReader:
    """The read side of a connection with an absolute deadline. Each `recv` waits at most the lesser of the
    pause limit of the handler and what is left of the deadline; when nothing is left it raises TimeoutError.
    The socket's own timeout is put back after each `recv`, so the answer is written under the usual limit.
    Only the calls that the HTTP parser and the endpoint make are here: `readline` and `read`."""

    def __init__(self, sock: socket.socket, deadline_s: float, pause_s: float | None) -> None:
        self._sock, self._pause_s = sock, pause_s
        self._end = time.monotonic() + deadline_s
        self._buf = bytearray()
        self.closed = False

    def _fill(self) -> bool:
        """One `recv` into the buffer; False at the end of the stream."""
        left = self._end - time.monotonic()
        if left <= 0:
            raise TimeoutError("request read deadline")
        self._sock.settimeout(left if self._pause_s is None else min(left, self._pause_s))
        try:
            data = self._sock.recv(65536)
        finally:
            self._sock.settimeout(self._pause_s)
        self._buf += data
        return bool(data)

    def _take(self, n: int) -> bytes:
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def readline(self, size: int | None = -1) -> bytes:
        limit = -1 if size is None else size
        start = 0
        while True:
            end = self._buf.find(b"\n", start)
            if end >= 0 and (limit < 0 or end < limit):
                return self._take(end + 1)
            if 0 <= limit <= len(self._buf):
                return self._take(limit)
            start = len(self._buf)
            if not self._fill():
                return self._take(len(self._buf))

    def read(self, size: int | None = -1) -> bytes:
        want = -1 if size is None else size
        while want < 0 or len(self._buf) < want:
            if not self._fill():
                break
        return self._take(len(self._buf) if want < 0 else want)

    def close(self) -> None:
        self.closed = True


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
    read_deadline_s: float = READ_DEADLINE_S

    def setup(self) -> None:
        super().setup()
        self.rfile.close()  # the buffered reader of the stdlib: reads here go through the deadline
        self.rfile = _DeadlineReader(self.connection, self.read_deadline_s, self.timeout)  # type: ignore[assignment]

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
            _LOG.log(_level(exc), "trigger server: connection ended: %s", type(exc).__name__)

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
        if any("_" in name for name in self.headers):
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
    """One thread per connection, so a request that waits for its row does not hold up the next one.

    Port exclusivity: on Windows the reuse option of the stdlib lets a second process bind a port that is
    already in use, so it is off there and `SO_EXCLUSIVEADDRUSE` is set before the bind instead (a bind to a
    port in use then fails). Elsewhere the reuse option stays on (a restart is not held up by sockets in
    TIME_WAIT) and a bind to a port in use fails as it should."""

    daemon_threads = True
    allow_reuse_address = os.name != "nt"

    def __init__(self, *args: Any, max_connections: int = MAX_CONNECTIONS, **kwargs: Any) -> None:
        if max_connections < 1:
            raise ValueError("max_connections must be at least 1")
        self._slots = threading.BoundedSemaphore(max_connections)
        self._cap_warned_at: float | None = None
        super().__init__(*args, **kwargs)

    def process_request(self, request: Any, client_address: Any) -> None:
        """A thread per connection up to the cap; above it the connection is closed at once, unread."""
        if not self._slots.acquire(blocking=False):
            self._warn_cap()
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def _warn_cap(self) -> None:
        """One WARNING at most every `CAP_WARN_EVERY_S` (monotonic) for a connection over the cap: no client
        address, no data; the rest of the hits in the window are dropped quietly."""
        at = _monotonic()
        if self._cap_warned_at is None or at - self._cap_warned_at >= CAP_WARN_EVERY_S:
            self._cap_warned_at = at
            _LOG.warning(
                "trigger server: connection cap reached, connections closed with no answer"
            )

    def server_bind(self) -> None:
        exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)  # only where the platform has it
        if exclusive is not None:
            self.socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        super().server_bind()

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        """The stdlib steps, but a BaseException also goes to `handle_error`: left alone it would reach the
        thread hook of the process, which prints a traceback."""
        try:
            self.finish_request(request, client_address)
        except BaseException:  # noqa: BLE001 - one connection never prints or stops the server
            self.handle_error(request, client_address)
        finally:
            try:
                self.shutdown_request(request)
            finally:  # a shutdown that raises must not leak the slot
                self._slots.release()

    def handle_error(self, request: Any, client_address: Any) -> None:
        """The stdlib prints the traceback and the client address here; this logs the class name."""
        exc = sys.exception()
        _LOG.log(_level(exc), "trigger server: connection error: %s", type(exc).__name__)
