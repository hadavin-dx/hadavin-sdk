"""The trigger server on a real loopback socket (ORDER 009, E2): what a broken or slow client gets back.

Each test binds `worker.make_server` to a free loopback port, talks to it with a raw socket (so the exact bytes are
the test's own) and closes server, thread and socket in a `finally`. The endpoint is the real `make_wsgi`; only
`start` is a fake. Every case asserts three things: an answer that is not 2xx has an empty body; no answer byte
holds anything of the request (document, key, signature, secret) or a traceback; and neither the process's stderr
nor the log does. The `drive_*` functions do the socket work and return what was seen; they hold no assertion, so
a script can call them to write down the raw behaviour.
"""

from __future__ import annotations

import contextlib
import json
import socket
import struct
import threading
import time
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.triggers import endpoint, worker
from hadavin_sdk.triggers import server as server_module

TENANT, SENDER, AGENT, PRINCIPAL = "tenant-a", "sender-a", "test-agent", "svc:test-agent"
SECRET = "w" * 20 + "5" * 20  # a fake, built from parts
KEY = "zq7-key-marker"
DOC_MARK = "ZQ7-document-marker-41c9"
LINE_MARK = "ZQ7-line-marker-88d2"
BOOM_MARK = "ZQ7-private-failure-text"
SOCKET_TIMEOUT_S = 0.5  # the server's read timeout in these tests
CLIENT_TIMEOUT_S = 8.0
MAX_LINE = 65536  # the stdlib cap on a request line
HANDLER_THREAD = "process_request_thread"


@dataclass
class Seen:
    """What one client saw: the raw answer, how the connection ended and after how many seconds."""

    raw: bytes
    end: str  # "closed", "reset" or "client timeout"
    seconds: float

    @property
    def status_line(self) -> bytes:
        return self.raw.split(b"\r\n", 1)[0]

    @property
    def status(self) -> int | None:
        parts = self.status_line.split(b" ")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

    @property
    def head(self) -> bytes:
        return self.raw.partition(b"\r\n\r\n")[0]

    @property
    def body(self) -> bytes:
        return self.raw.partition(b"\r\n\r\n")[2]


class FakeStart:
    """Stands for `Runner.start`: counts its calls and may wait at `gate` before it answers."""

    def __init__(self) -> None:
        self.calls: list[endpoint.Accepted] = []
        self.entered = threading.Event()
        self.gate = threading.Event()
        self.gate.set()

    def __call__(self, req: endpoint.Accepted) -> tuple[int, dict[str, str]]:
        self.calls.append(req)
        self.entered.set()
        self.gate.wait(CLIENT_TIMEOUT_S)
        # more than the two answer fields, to see that the endpoint drops the rest
        return 202, {"run_id": req.run_id, "state": "RECEIVED", "trigger_ref": req.trigger_ref}


def make_wsgi(start: FakeStart):
    sender = SimpleNamespace(id=SENDER, agent_id=AGENT, principal_id=PRINCIPAL)
    settings = SimpleNamespace(tenant=TENANT, senders=[sender], max_body_bytes=65536)
    return endpoint.make_wsgi(settings, {SENDER: (SECRET,)}, start)


def _handlers_done(timeout_s: float = CLIENT_TIMEOUT_S) -> bool:
    """True once no connection thread of a server is alive."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not [t for t in threading.enumerate() if HANDLER_THREAD in t.name]:
            return True
        time.sleep(0.01)
    return False


@contextlib.contextmanager
def serving(wsgi, timeout_s: float = SOCKET_TIMEOUT_S):
    """The real server on a free loopback port; shut down, joined and closed on the way out."""
    server = worker.make_server(worker.LOOPBACK, 0, wsgi, timeout_s)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    try:
        thread.start()
        yield server
    finally:
        if thread.is_alive():
            server.shutdown()
            thread.join(CLIENT_TIMEOUT_S)
        server.server_close()
        done = _handlers_done()
    if thread.is_alive() or not done:
        raise AssertionError("a server thread is still running")


def body_bytes() -> bytes:
    return json.dumps({"key": KEY, "document": f"alert {DOC_MARK} from the checkout"}).encode()


def request(body: bytes, *, declared: int | None, complete: bool = True) -> bytes:
    """A signed POST. `declared` is the Content-Length (None = no such header); `complete` False leaves the
    header block open (no empty line, no body)."""
    lines = [f"POST {endpoint.PATH} HTTP/1.1", f"Host: {worker.LOOPBACK}"]
    if declared is not None:
        lines.append(f"Content-Length: {declared}")
    signed = hmac_v0.sign(body, int(time.time()), SECRET, endpoint.PREFIX)
    lines += [f"{name}: {value}" for name, value in signed.items()]
    head = "\r\n".join(lines).encode("ascii") + b"\r\n"
    return head + b"\r\n" + body if complete else head


def exchange(port: int, data: bytes, *, half_close: bool = False) -> Seen:
    """Send `data`, then read until the server closes (or the client's own timeout)."""
    sock = socket.create_connection((worker.LOOPBACK, port), timeout=CLIENT_TIMEOUT_S)
    try:
        if data:
            sock.sendall(data)
        if half_close:
            sock.shutdown(socket.SHUT_WR)
        began, raw, end = time.monotonic(), b"", "closed"
        try:
            while part := sock.recv(65536):
                raw += part
        except ConnectionResetError:
            end = "reset"
        except TimeoutError:
            end = "client timeout"
        return Seen(raw, end, time.monotonic() - began)
    finally:
        sock.close()


# --- the cases: socket work only ---------------------------------------------------------------------------


def drive_signed(port: int) -> Seen:
    body = body_bytes()
    return exchange(port, request(body, declared=len(body)))


def drive_short_then_half_close(port: int) -> Seen:
    body = body_bytes()
    return exchange(port, request(body, declared=len(body) + 50), half_close=True)


def drive_short_then_stall(port: int) -> Seen:
    body = body_bytes()
    return exchange(port, request(body, declared=len(body) + 50))


def drive_headers_then_stall(port: int) -> Seen:
    return exchange(port, request(body_bytes(), declared=10, complete=False))


def drive_silent_client(port: int) -> Seen:
    return exchange(port, b"")


def drive_garbage(port: int) -> Seen:
    return exchange(port, b"\x16\x03\x01\x02" + LINE_MARK.encode() + b"\n")


def drive_long_request_line(port: int) -> Seen:
    line = b"POST /" + LINE_MARK.encode()
    return exchange(
        port, line + b"a" * (MAX_LINE + 1 - len(line))
    )  # one byte over the cap, no more


def drive_no_content_length(port: int) -> Seen:
    return exchange(port, request(body_bytes(), declared=None))


def drive_client_gone(port: int, start: FakeStart) -> Seen:
    """The client waits until `start` runs, then drops the connection hard; the answer meets a dead socket."""
    body = body_bytes()
    start.gate.clear()
    start.entered.clear()
    sock = socket.create_connection((worker.LOOPBACK, port), timeout=CLIENT_TIMEOUT_S)
    try:
        began = time.monotonic()
        sock.sendall(request(body, declared=len(body)))
        entered = start.entered.wait(CLIENT_TIMEOUT_S)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    finally:
        sock.close()
        start.gate.set()
    return Seen(b"", "client gone" if entered else "start not reached", time.monotonic() - began)


def broken_app(environ, start_response):
    raise RuntimeError(BOOM_MARK)


# --- the assertions every case shares ------------------------------------------------------------------------


def needles() -> list[str]:
    body = body_bytes()
    return [DOC_MARK, KEY, LINE_MARK, BOOM_MARK, SECRET, body.decode(), "Traceback", 'File "']


def check_quiet(seen: Seen, capsys, caplog) -> None:
    """Call after the server is closed, so every connection thread has written what it writes."""
    if seen.raw:
        assert seen.raw.startswith(b"HTTP/1."), seen.raw[:80]
        assert seen.status is not None
        if not 200 <= seen.status < 300:
            assert seen.body == b"", seen.body[:200]
            assert b"content-type" not in seen.head.lower()
        assert b"python" not in seen.head.lower() and b"wsgiserver" not in seen.head.lower()
        assert b"\r\nserver:" not in seen.head.lower()
    captured = capsys.readouterr()
    for name, text in (
        ("answer", seen.raw.decode("latin-1")),
        ("stderr", captured.err),
        ("stdout", captured.out),
        ("log", caplog.text),
    ):
        for needle in needles():
            assert needle not in text, f"{needle!r} in the {name}: {text[:300]!r}"
        assert not [s for s in _signatures if s in text], f"a signature in the {name}"
    assert captured.err == "", captured.err[:300]


_signatures: list[str] = []


@pytest.fixture(autouse=True)
def _watch(monkeypatch, caplog):
    """Remember every signature made in the test, and capture the trigger log from DEBUG up."""
    made: list[str] = []
    real = hmac_v0.sign

    def sign(*args, **kwargs):
        headers = real(*args, **kwargs)
        wanted = endpoint.SIGNATURE_HEADER.lower()
        made.extend(v.rpartition("=")[2] for k, v in headers.items() if k.lower() == wanted)
        return headers

    monkeypatch.setattr(hmac_v0, "sign", sign)
    monkeypatch.setattr("tests.triggers.test_t5_wsgiref._signatures", made)
    caplog.set_level("DEBUG", logger="hadavin_sdk.triggers")


# --- tests ---------------------------------------------------------------------------------------------------


def test_signed_request_over_the_socket_is_acked_with_run_id_and_state_only(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_signed(server.server_port)
    assert seen.status == 202 and seen.end == "closed", seen
    answer = json.loads(seen.body)
    assert set(answer) == {"run_id", "state"}
    assert answer == {"run_id": endpoint.derive_run_id(TENANT, SENDER, KEY), "state": "RECEIVED"}
    assert len(start.calls) == 1 and DOC_MARK.encode() in start.calls[0].document
    check_quiet(seen, capsys, caplog)


def test_fewer_bytes_than_content_length_then_half_close_is_400_empty(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_short_then_half_close(server.server_port)
    assert seen.status_line.endswith(b" 400 Bad Request") and seen.end == "closed", seen
    assert seen.seconds < SOCKET_TIMEOUT_S  # answered at the end of the stream, not at the timeout
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


def test_fewer_bytes_than_content_length_then_stall_is_400_empty_at_the_timeout(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_short_then_stall(server.server_port)
    assert seen.status_line.endswith(b" 400 Bad Request") and seen.end == "closed", seen
    assert (
        SOCKET_TIMEOUT_S * 0.8 <= seen.seconds < SOCKET_TIMEOUT_S + 3.0
    )  # the thread is held this long
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


@pytest.mark.parametrize("drive", [drive_headers_then_stall, drive_silent_client])
def test_stall_before_the_headers_end_is_400_empty_at_the_timeout(drive, capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive(server.server_port)
    assert seen.status_line.endswith(b" 400 Bad Request") and seen.end == "closed", seen
    assert SOCKET_TIMEOUT_S * 0.8 <= seen.seconds < SOCKET_TIMEOUT_S + 3.0
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


def test_garbage_instead_of_a_request_line_is_400_empty(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_garbage(server.server_port)
    assert seen.status_line.endswith(b" 400 Bad Request") and seen.end == "closed", seen
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


def test_request_line_over_64_kb_is_414_empty(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_long_request_line(server.server_port)
    assert seen.status == 414 and seen.end == "closed", (seen.raw[:200], seen.end)
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


def test_no_content_length_is_400_empty(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_no_content_length(server.server_port)
    # The body was sent but is not read, so the close may reach the client as a reset after the answer.
    assert seen.status_line.endswith(b" 400 Bad Request"), seen
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


def test_client_gone_before_the_answer_leaves_the_server_quiet_and_serving(capsys, caplog):
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        gone = drive_client_gone(server.server_port, start)
        assert gone.end == "client gone"
        assert _handlers_done()  # the answer was written to the dead socket, or dropped
        after = drive_signed(server.server_port)
    assert after.status == 202 and len(start.calls) == 2
    check_quiet(after, capsys, caplog)


def test_an_app_that_raises_is_503_empty_and_logged_by_class_name_only(capsys, caplog):
    with serving(broken_app) as server:
        seen = drive_signed(server.server_port)
    assert seen.status_line.endswith(b" 503 Service Unavailable") and seen.end == "closed", seen
    assert "RuntimeError" in caplog.text
    check_quiet(seen, capsys, caplog)


class TimeoutStart(FakeStart):
    """A `start` whose own work timed out (a store call, say): the client was not slow."""

    def __call__(self, req: endpoint.Accepted) -> tuple[int, dict[str, str]]:
        self.calls.append(req)
        raise TimeoutError(BOOM_MARK)


def timeout_app(environ, start_response):
    raise TimeoutError(BOOM_MARK)


@pytest.mark.parametrize("where", ["start", "application"])
def test_a_timeout_raised_by_the_code_behind_the_socket_is_503_empty_not_a_slow_client(
    where, capsys, caplog
):
    """Review 2, Minor 2. Request: complete and correctly signed; the timeout is raised by `start`, or by
    the application itself. Expected: 503 with an empty body, the class name in the log, and no line
    of the slow-client refusal (400 before the endpoint)."""
    start = TimeoutStart()
    with serving(make_wsgi(start) if where == "start" else timeout_app) as server:
        seen = drive_signed(server.server_port)
    assert seen.status_line.endswith(b" 503 Service Unavailable") and seen.end == "closed", seen
    assert seen.raw.count(b"HTTP/1.") == 1  # one answer head, no second one after it
    assert len(start.calls) == (1 if where == "start" else 0)
    assert "TimeoutError" in caplog.text
    assert "refused before the endpoint" not in caplog.text and "status=400" not in caplog.text
    check_quiet(seen, capsys, caplog)


def test_a_timeout_after_the_read_phase_writes_no_stalled_client_answer(monkeypatch, capsys, caplog):
    """Review 2, Minor 2. A timeout that leaves the application handler (the stdlib lets one through
    when the answer cannot be written) is not a client that sent too little: no 400 head is written
    after it, the connection is closed, and the log holds the class name only."""

    def run(self, application):
        raise TimeoutError(BOOM_MARK)

    monkeypatch.setattr(server_module.QuietWSGIHandler, "run", run)
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = drive_signed(server.server_port)
    assert seen.raw == b"" and seen.end == "closed", seen
    assert start.calls == []
    assert "connection ended: TimeoutError" in caplog.text
    assert "refused before the endpoint" not in caplog.text
    check_quiet(seen, capsys, caplog)
