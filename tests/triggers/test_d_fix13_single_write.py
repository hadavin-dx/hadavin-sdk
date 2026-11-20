"""d-fix13: every answer of the trigger server is ONE write to the socket.

Cause: `wbufsize` of the stdlib handler is 0, so `wsgiref` sent the status line, the Date line, the header block
and the body as four `sendall` calls; a worker killed between two of them left the client with `HTTP/1.0 202
Accepted` and nothing else, which `http.client` reads as status 202 with an empty body and no error (a 2xx that
cannot be told from a complete answer). `QuietWSGIHandler` now keeps what the stdlib writes and sends it once.

The server is the real one on a loopback port; every accepted connection is wrapped in a recorder that notes each
`send`, `sendall` and `sendfile` call. The golden bytes below were taken from the server BEFORE the change (the
Date value is replaced by `DATE`), so the wire format is shown to be byte for byte the same."""

from __future__ import annotations

import contextlib
import http.client
import io
import json
import re
import socket
import threading
import time
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.triggers import endpoint, worker

TENANT, SENDER, AGENT, PRINCIPAL = "tenant-a", "sender-a", "test-agent", "svc:test-agent"
SECRET = "w" * 20 + "5" * 20
OTHER_SECRET = "q" * 20 + "7" * 20
KEY = "k13-key"
CLIENT_TIMEOUT_S = 8.0
BODY = json.dumps({"key": KEY, "document": "alert from the checkout"}).encode()
RUN_ID = endpoint.derive_run_id(TENANT, SENDER, KEY)


class Recorder:
    """Stands for the accepted socket: every call that writes is noted, all else goes to the real socket."""

    def __init__(self, sock: socket.socket, log: list[list[bytes]]) -> None:
        self._sock = sock
        self.writes: list[bytes] = []
        log.append(self.writes)

    def sendall(self, data, *args):
        self.writes.append(bytes(data))
        return self._sock.sendall(data, *args)

    def send(self, data, *args):
        self.writes.append(bytes(data))
        return self._sock.send(data, *args)

    def sendfile(self, *args, **kwargs):  # pragma: no cover - the server never calls it
        self.writes.append(b"<sendfile>")
        return self._sock.sendfile(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _start(status, answer=None):
    def start(req):
        return status, (
            {"run_id": req.run_id, "state": "RECEIVED", "trigger_ref": req.trigger_ref}
            if answer is None
            else answer
        )

    return start


def _wsgi(start=None, *, health=None, max_body=65536):
    sender = SimpleNamespace(id=SENDER, agent_id=AGENT, principal_id=PRINCIPAL)
    settings = SimpleNamespace(tenant=TENANT, senders=[sender], max_body_bytes=max_body)
    return endpoint.make_wsgi(settings, {SENDER: (SECRET,)}, start or _start(202), health=health)


def _post(secret=SECRET, body=BODY, declared=None, path=endpoint.PATH, method="POST") -> bytes:
    signed = hmac_v0.sign(body, int(time.time()), secret, endpoint.PREFIX)
    lines = [f"{method} {path} HTTP/1.1", f"Host: {worker.LOOPBACK}"]
    lines.append(f"Content-Length: {len(body) if declared is None else declared}")
    lines += [f"{name}: {value}" for name, value in signed.items()]
    return "\r\n".join(lines).encode() + b"\r\n\r\n" + body


def _get(path, method="GET") -> bytes:
    return f"{method} {path} HTTP/1.1\r\nHost: {worker.LOOPBACK}\r\n\r\n".encode()


def _boom(environ, start_response):
    raise RuntimeError("boom")


# name -> (wsgi, request bytes, expected status, expected body)
def _cases():
    ok = json.dumps({"run_id": RUN_ID, "state": "RECEIVED"}).encode()
    return {
        "202": (_wsgi(_start(202)), _post(), 202, ok),
        "200": (_wsgi(_start(200)), _post(), 200, ok),
        "409-empty": (_wsgi(_start(409)), _post(), 409, b""),
        "401-empty": (_wsgi(), _post(secret=OTHER_SECRET), 401, b""),
        "503-empty": (_wsgi(_start(503)), _post(), 503, b""),
        "413": (_wsgi(max_body=10), _post(), 413, b""),
        "404": (_wsgi(), _get("/nope"), 404, b""),
        "405": (_wsgi(), _get(endpoint.PATH), 405, b""),
        "400-bad-body": (_wsgi(), _post(body=b"x", declared=1), 400, b""),
        "health-200": (
            _wsgi(health=lambda: (True, 0)),
            _get("/health"),
            200,
            b'{"status": "ok", "store_failures": 0}',
        ),
        "health-503": (
            _wsgi(health=lambda: (False, 2)),
            _get("/health"),
            503,
            b'{"status": "store_down", "store_failures": 2}',
        ),
        "health-405": (_wsgi(health=lambda: (True, 0)), _get("/health", "POST"), 405, b""),
        "app-raises-503": (_boom, _post(), 503, b""),
        # refused by the request handler before the application (send_error)
        "414-long-line": (_wsgi(), b"POST /" + b"a" * 70000, 414, b""),
        "400-garbage": (_wsgi(), b"\x16\x03\x01\x02 junk\n", 400, b""),
        "400-no-length": (
            _wsgi(),
            f"POST {endpoint.PATH} HTTP/1.1\r\nHost: x\r\n\r\n".encode(),
            400,
            b"",
        ),
    }


@contextlib.contextmanager
def _serving(wsgi, log):
    server = worker.make_server(worker.LOOPBACK, 0, wsgi, 2.0)
    real = server.get_request

    def get_request():
        sock, addr = real()
        return Recorder(sock, log), addr

    server.get_request = get_request
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(CLIENT_TIMEOUT_S)
        server.server_close()


def _exchange(name: str):
    """(raw bytes the client read, the list of writes the server made for that connection)."""
    wsgi, data, _status, _body = _cases()[name]
    log: list[list[bytes]] = []
    with _serving(wsgi, log) as server:
        sock = socket.create_connection(
            (worker.LOOPBACK, server.server_address[1]), timeout=CLIENT_TIMEOUT_S
        )
        try:
            sock.sendall(data)
            raw = b""
            with contextlib.suppress(ConnectionResetError, TimeoutError):
                while part := sock.recv(65536):
                    raw += part
        finally:
            sock.close()
    assert len(log) == 1
    return raw, log[0]


def _parse(raw: bytes) -> http.client.HTTPResponse:
    class _Sock:
        def makefile(self, *_a, **_k):
            return io.BytesIO(raw)

    resp = http.client.HTTPResponse(_Sock())  # type: ignore[arg-type]
    resp.begin()
    return resp


def _normal(raw: bytes) -> bytes:
    return re.sub(rb"\r\nDate: [^\r]*\r\n", b"\r\nDate: DATE\r\n", raw, count=1)


NAMES = list(_cases())

# The stdlib, not this server, decides these two (see the d-fix15 note in the ticket):
# - `400-garbage` is a two-word line whose command is not GET, so `parse_request` calls `send_error` while
#   `request_version` is still the default HTTP/0.9. CPython 3.12 and 3.13.12 write nothing for an HTTP/0.9
#   answer (no status line, no headers) and close; 3.13.18 sets `request_version = ''` first and answers 400.
#   Both are legitimate for an unparseable line; what must hold on every Python is: no write at all, or the
#   whole answer in exactly one write, never a split one.
# - `414-long-line` is answered by our own `send_error`, but the reason phrase comes from `http.HTTPStatus`,
#   which CPython renamed in 3.13 ("Request-URI Too Long" became "URI Too Long"): the phrase is not compared.
MAY_BE_SILENT = {"400-garbage"}
PHRASE_VARIES = {"414-long-line"}


def _silent(name, raw, writes):
    """True when this case may stay unanswered and did (nothing written, nothing read)."""
    if name in MAY_BE_SILENT and not writes:
        assert raw == b""
        return True
    return False


def _no_phrase(raw: bytes) -> bytes:
    return re.sub(rb"^(HTTP/1\.\d \d{3})[^\r]*", rb"\1", raw)


@pytest.mark.parametrize("name", NAMES)
def test_every_answer_is_one_write(name):
    raw, writes = _exchange(name)
    if _silent(name, raw, writes):
        return
    assert len(writes) == 1, [w[:40] for w in writes]
    assert writes[0] == raw  # nothing else reached the client


@pytest.mark.parametrize("name", NAMES)
def test_the_one_write_holds_status_line_headers_and_the_whole_body(name):
    """A kill between writes is impossible when the first and only write is the complete answer.
    A case in MAY_BE_SILENT may instead write nothing (stdlib HTTP/0.9 handling, older CPython): never a part."""
    _app, _data, status, body = _cases()[name]
    raw, writes = _exchange(name)
    if _silent(name, raw, writes):
        return
    first = writes[0]
    _head, sep, tail = first.partition(b"\r\n\r\n")
    assert sep and first.startswith(b"HTTP/1.")
    assert tail == body
    resp = _parse(first)
    assert resp.status == status
    assert resp.read() == body
    assert int(resp.getheader("Content-Length")) == len(body)


@pytest.mark.parametrize("name", NAMES)
def test_the_bytes_on_the_wire_are_those_of_the_stdlib_writes(name):
    """Byte for byte what the four-write server sent (taken before the change; Date replaced)."""
    raw, writes = _exchange(name)
    if _silent(name, raw, writes):
        return
    got, want = _normal(raw), GOLDEN[name]
    if name in PHRASE_VARIES:
        got, want = _no_phrase(got), _no_phrase(want)
    assert got == want


def test_a_failure_after_the_headers_still_sends_what_the_stdlib_would_have_sent():
    """The application raises while its body is iterated, after the first chunk: the client gets the chunk once."""

    def app(environ, start_response):
        start_response("200 OK", [("Content-Length", "10")])

        def body():
            yield b"abc"
            raise RuntimeError("late")

        return body()

    log: list[list[bytes]] = []
    with _serving(app, log) as server:
        sock = socket.create_connection(
            (worker.LOOPBACK, server.server_address[1]), timeout=CLIENT_TIMEOUT_S
        )
        try:
            sock.sendall(_get("/x"))
            raw = b""
            with contextlib.suppress(ConnectionResetError, TimeoutError):
                while part := sock.recv(65536):
                    raw += part
        finally:
            sock.close()
    assert len(log[0]) == 1
    assert raw.startswith(b"HTTP/1.0 200 OK\r\n") and raw.endswith(b"\r\n\r\nabc")


GOLDEN: dict[str, bytes] = {
    "202": b'HTTP/1.0 202 Accepted\r\nDate: DATE\r\nContent-Length: 71\r\nContent-Type: application/json\r\n\r\n{"run_id": "run-2ef744c750de65546f94c3facbb10c8b", "state": "RECEIVED"}',
    "200": b'HTTP/1.0 200 OK\r\nDate: DATE\r\nContent-Length: 71\r\nContent-Type: application/json\r\n\r\n{"run_id": "run-2ef744c750de65546f94c3facbb10c8b", "state": "RECEIVED"}',
    "409-empty": b"HTTP/1.0 409 Conflict\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "401-empty": b"HTTP/1.0 401 Unauthorized\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "503-empty": b"HTTP/1.0 503 Service Unavailable\r\nDate: DATE\r\nContent-Length: 0\r\nRetry-After: 1\r\n\r\n",
    "413": b"HTTP/1.0 413 Content Too Large\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "404": b"HTTP/1.0 404 Not Found\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "405": b"HTTP/1.0 405 Method Not Allowed\r\nDate: DATE\r\nContent-Length: 0\r\nAllow: POST\r\n\r\n",
    "400-bad-body": b"HTTP/1.0 400 Bad Request\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "health-200": b'HTTP/1.0 200 OK\r\nDate: DATE\r\nContent-Length: 37\r\nContent-Type: application/json\r\n\r\n{"status": "ok", "store_failures": 0}',
    "health-503": b'HTTP/1.0 503 Service Unavailable\r\nDate: DATE\r\nContent-Length: 45\r\nContent-Type: application/json\r\nRetry-After: 1\r\n\r\n{"status": "store_down", "store_failures": 2}',
    "health-405": b"HTTP/1.0 405 Method Not Allowed\r\nDate: DATE\r\nContent-Length: 0\r\nAllow: GET\r\n\r\n",
    "app-raises-503": b"HTTP/1.0 503 Service Unavailable\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
    "414-long-line": b"HTTP/1.0 414 URI Too Long\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
    "400-garbage": b"HTTP/1.0 400 Bad Request\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
    "400-no-length": b"HTTP/1.0 400 Bad Request\r\nDate: DATE\r\nContent-Length: 0\r\n\r\n",
}
