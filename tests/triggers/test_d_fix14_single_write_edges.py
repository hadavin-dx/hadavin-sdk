"""d-fix14: edges of the one-write answer (`QuietWSGIHandler.finish_response`).

Found in the code: the endpoint answers every method but POST with 405 and an empty body (`/health` every
method but GET), so a HEAD request gets the 405 status line, `Content-Length: 0` and no body, in one write: the
stdlib handler does not strip a body for HEAD, and no body is produced for one here.

The final send of the buffered answer can fail. `finish_response` of the stdlib calls `close()` first, which
resets `headers_sent`; without the guard in `finish_response` a failing send other than a gone client made
`handle_error` build an error page from `environ=None` (a TypeError, logged as noise). The application that
raises before `start_response` (503 once, one write) is covered by `test_d_fix13_single_write.py`."""

from __future__ import annotations

import contextlib
import logging
import socket
import threading
from types import SimpleNamespace

import pytest

from hadavin_sdk.triggers import endpoint, worker

CLIENT_TIMEOUT_S = 8.0


class Wrapped:
    """The accepted socket: notes each write; `fail` (an exception) is raised by the write instead of sending."""

    def __init__(self, sock, log, fail=None):
        self._sock, self._fail = sock, fail
        self.writes: list[bytes] = []
        log.append(self.writes)

    def sendall(self, data, *args):
        self.writes.append(bytes(data))
        if self._fail is not None:
            raise self._fail
        return self._sock.sendall(data, *args)

    def send(self, data, *args):
        self.writes.append(bytes(data))
        if self._fail is not None:
            raise self._fail
        return self._sock.send(data, *args)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _app(body: bytes = b"", status: str = "200 OK"):
    def app(environ, start_response):
        start_response(status, [("Content-Length", str(len(body)))])
        return [body]

    return app


def _exchange(app, request: bytes, fail=None):
    """(raw bytes the client read, writes the server made, the log records of the server)."""
    log: list[list[bytes]] = []
    records: list[logging.LogRecord] = []

    class Grab(logging.Handler):
        def emit(self, record):
            records.append(record)

    logger = logging.getLogger("hadavin_sdk.triggers")
    grab = Grab(level=logging.DEBUG)
    old_level = logger.level
    logger.addHandler(grab)
    logger.setLevel(logging.DEBUG)
    server = worker.make_server(worker.LOOPBACK, 0, app, 2.0)
    real = server.get_request

    def get_request():
        sock, addr = real()
        return Wrapped(sock, log, fail), addr

    server.get_request = get_request
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    thread.start()
    try:
        sock = socket.create_connection(
            (worker.LOOPBACK, server.server_address[1]), timeout=CLIENT_TIMEOUT_S
        )
        try:
            sock.sendall(request)
            raw = b""
            with contextlib.suppress(ConnectionResetError, TimeoutError):
                while part := sock.recv(1 << 20):
                    raw += part
        finally:
            sock.close()
    finally:
        server.shutdown()
        thread.join(CLIENT_TIMEOUT_S)
        server.server_close()
        logger.removeHandler(grab)
        logger.setLevel(old_level)
    assert len(log) == 1
    return raw, log[0], records


def _get(path="/x", method="GET") -> bytes:
    return f"{method} {path} HTTP/1.1\r\nHost: {worker.LOOPBACK}\r\n\r\n".encode()


def test_a_head_request_gets_the_405_in_one_write_and_no_body():
    sender = SimpleNamespace(id="s", agent_id="a", principal_id="p")
    settings = SimpleNamespace(tenant="t", senders=[sender], max_body_bytes=65536)
    wsgi = endpoint.make_wsgi(settings, {"s": ("x" * 40,)}, lambda req: (202, {}))
    raw, writes, _records = _exchange(wsgi, _get(endpoint.PATH, "HEAD"))
    assert len(writes) == 1 and writes[0] == raw
    head, sep, tail = raw.partition(b"\r\n\r\n")
    assert head.startswith(b"HTTP/1.0 405 ") and b"Content-Length: 0" in head
    assert sep and tail == b""


def test_a_large_body_is_still_one_write_and_arrives_whole():
    body = bytes(range(256)) * 4096  # 1 MiB
    raw, writes, _records = _exchange(_app(body), _get())
    assert len(writes) == 1
    head, sep, tail = raw.partition(b"\r\n\r\n")
    assert sep and head.startswith(b"HTTP/1.0 200 OK")
    assert tail == body


def test_a_timeout_on_the_final_send_is_logged_once_by_class_and_nothing_else():
    raw, writes, records = _exchange(_app(b"hello"), _get(), fail=TimeoutError("secret detail"))
    assert len(writes) == 1  # the one attempt: no second answer, no error page
    assert raw == b""
    texts = [r.getMessage() for r in records if r.levelno >= logging.WARNING]
    assert texts == ["trigger server: application error: TimeoutError"], texts
    assert not any("secret detail" in r.getMessage() for r in records)


@pytest.mark.parametrize("exc", [BrokenPipeError, ConnectionResetError, ConnectionAbortedError])
def test_a_gone_client_on_the_final_send_is_silent(exc):
    raw, writes, records = _exchange(_app(b"hello"), _get(), fail=exc())
    assert len(writes) == 1 and raw == b""
    assert [r for r in records if r.levelno >= logging.WARNING] == []
