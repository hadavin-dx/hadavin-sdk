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


def test_a_timeout_after_the_read_phase_is_not_answered_as_a_stall(monkeypatch, capsys, caplog):
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


# --- design review 1 and the fuzz findings F1 to F4 --------------------------------------------------------


def custom(
    body: bytes,
    *,
    line: str | None = None,
    lengths: tuple[int, ...] | None = None,
    underscore: bool = False,
    sign: bool = True,
    more: tuple[str, ...] = (),
    with_body: bool = True,
) -> bytes:
    """A complete request whose request line, length headers and header names are the test's own."""
    lines = [
        line if line is not None else f"POST {endpoint.PATH} HTTP/1.1",
        f"Host: {worker.LOOPBACK}",
    ]
    lines += [f"Content-Length: {n}" for n in ((len(body),) if lengths is None else lengths)]
    if sign:
        signed = hmac_v0.sign(body, int(time.time()), SECRET, endpoint.PREFIX)
        lines += [
            f"{name.replace('-', '_') if underscore else name}: {value}"
            for name, value in signed.items()
        ]
    lines += more
    head = "\r\n".join(lines).encode("ascii") + b"\r\n\r\n"
    return head + body if with_body else head


def trigger_records(caplog) -> list[tuple[str, str]]:
    return [
        (r.levelname, r.getMessage()) for r in caplog.records if r.name == "hadavin_sdk.triggers"
    ]


@pytest.mark.parametrize("version", ["HTTP/2.0", "HTTP/3.0", "HTTP/9.9", "HTTP/10.1"])
def test_f1_http_version_2_or_higher_is_400_empty_never_a_5xx(version, capsys, caplog):
    """Fuzz F1. The stdlib parser answers 505 for these; the quiet server turns every 5xx of the
    parser into 400 with an empty body. The log line holds the status that was sent."""
    start = FakeStart()
    body = body_bytes()
    with serving(make_wsgi(start)) as server:
        seen = exchange(server.server_port, custom(body, line=f"POST {endpoint.PATH} {version}"))
    assert seen.status_line.endswith(b" 400 Bad Request"), seen
    assert start.calls == []
    assert (
        "DEBUG",
        "trigger status=400 sender=- (refused before the endpoint)",
    ) in trigger_records(caplog)
    assert "505" not in caplog.text
    check_quiet(seen, capsys, caplog)


def test_f2_a_request_line_without_a_version_is_closed_on_purpose(capsys, caplog):
    """Fuzz F2. `GET /v1/trigger` with no version: no answer, the connection is closed, and the log
    holds one fixed DEBUG line, not the class name of an internal error."""
    start = FakeStart()
    with serving(make_wsgi(start)) as server:
        seen = exchange(server.server_port, custom(body_bytes(), line=f"GET {endpoint.PATH}"))
    assert seen.raw == b"" and seen.end in ("closed", "reset"), seen
    assert start.calls == []
    assert trigger_records(caplog) == [
        ("DEBUG", "trigger server: request line without an HTTP version, closed with no answer")
    ]
    check_quiet(seen, capsys, caplog)


@pytest.mark.parametrize("case", ["signed names", "one more header"])
def test_f3_a_header_name_with_an_underscore_is_400_empty(case, capsys, caplog):
    """Fuzz F3. The signature and timestamp headers written with underscores verified as if they had
    hyphens; any header name with an underscore is refused before the endpoint."""
    start = FakeStart()
    body = body_bytes()
    data = (
        custom(body, underscore=True)
        if case == "signed names"
        else custom(body, more=("X_Other: 1",))
    )
    with serving(make_wsgi(start)) as server:
        seen = exchange(server.server_port, data)
        hyphens = exchange(server.server_port, custom(body, more=("X-Other: 1",)))
    assert seen.status_line.endswith(b" 400 Bad Request"), seen
    assert hyphens.status == 202 and len(start.calls) == 1  # the hyphen form is still taken
    check_quiet(seen, capsys, caplog)


@pytest.mark.parametrize(
    "case", ["two equal lengths", "two different lengths", "chunked", "identity", "no body sent"]
)
def test_f4_two_content_lengths_or_a_transfer_encoding_is_400_before_the_body_is_read(
    case, capsys, caplog
):
    """Fuzz F4. `no body sent`: the header block ends and no body byte follows; the answer comes at
    once, long before the socket timeout, so nothing waited for a body."""
    start = FakeStart()
    body = body_bytes()
    n = len(body)
    data = {
        "two equal lengths": custom(body, lengths=(n, n)),
        "two different lengths": custom(body, lengths=(n, n + 1)),
        "chunked": custom(body, more=("Transfer-Encoding: chunked",)),
        "identity": custom(body, more=("transfer-encoding: identity",)),
        "no body sent": custom(body, lengths=(n, n), with_body=False),
    }[case]
    timeout_s = 4.0
    with serving(make_wsgi(start), timeout_s) as server:
        seen = exchange(server.server_port, data)
    assert seen.status_line.endswith(b" 400 Bad Request"), seen
    assert seen.seconds < timeout_s / 2
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


class _TimesOutOnce:
    """Stands for a socket whose send buffer is full: the first write times out, later ones are kept."""

    def __init__(self, attempts: list[bytes]) -> None:
        self.attempts = attempts

    def write(self, data: bytes) -> int:
        self.attempts.append(bytes(data))
        if len(self.attempts) == 1:
            raise TimeoutError(BOOM_MARK)
        return len(data)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_n9_a_timeout_while_a_refusal_is_written_gives_no_second_status_line(
    monkeypatch, capsys, caplog
):
    """Review N9. The stdlib parser writes the 431 itself, inside the step whose timeout counts as a
    stalled client. When that write times out, nothing more is written: one attempt, then the close."""
    attempts: list[bytes] = []
    real_setup = server_module.QuietRequestHandler.setup

    def setup(self):
        real_setup(self)
        self.wfile = _TimesOutOnce(attempts)

    monkeypatch.setattr(server_module.QuietRequestHandler, "setup", setup)
    start = FakeStart()
    many = tuple(f"X-N{i}: {i}" for i in range(120))
    with serving(make_wsgi(start)) as server:
        seen = exchange(server.server_port, custom(body_bytes(), more=many))
    assert seen.raw == b"", seen
    assert len(attempts) == 1 and attempts[0].startswith(b"HTTP/1.0 431 "), attempts
    assert ("DEBUG", "trigger server: timeout while an answer was written, closed") in (
        trigger_records(caplog)
    )
    assert start.calls == []
    check_quiet(seen, capsys, caplog)


LARGE_ANSWER = 8 * 1024 * 1024


def large_app(environ, start_response):
    start_response("200 OK", [("Content-Length", str(LARGE_ANSWER))])
    return [b"a" * LARGE_ANSWER]


@pytest.mark.parametrize("answer", ["endpoint", "large"])
def test_n9_a_client_that_never_reads_gets_one_status_line_and_the_server_goes_on(
    answer, monkeypatch, capsys, caplog
):
    """Review N9 on a real socket: a valid request from a client with a small receive buffer that
    does not read. `endpoint`: the short answer fits in the socket buffers. `large`: the write
    times out in the middle of the body. Either way the bytes that arrived hold one status line,
    the connection thread ends, and the next request is served."""
    real_setup = server_module.QuietRequestHandler.setup

    def setup(self):
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        real_setup(self)

    monkeypatch.setattr(server_module.QuietRequestHandler, "setup", setup)
    start = FakeStart()
    body = body_bytes()
    with serving(make_wsgi(start) if answer == "endpoint" else large_app) as server:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
            sock.settimeout(CLIENT_TIMEOUT_S)
            sock.connect((worker.LOOPBACK, server.server_port))
            sock.sendall(request(body, declared=len(body)))
            assert _handlers_done()  # not one byte was read by the client, and the thread is gone
            raw = b""
            with contextlib.suppress(ConnectionResetError):
                while part := sock.recv(65536):
                    raw += part
        finally:
            sock.close()
        after = drive_signed(server.server_port)
    seen = Seen(raw[:4096], "closed", 0.0)
    assert raw.count(b"HTTP/1.") == 1 and raw.startswith(b"HTTP/1.0 20"), raw[:120]
    if answer == "large":
        assert len(raw) < LARGE_ANSWER  # the write did time out
        assert "TimeoutError" in caplog.text
        assert after.status == 200
    else:
        assert after.status == 202 and len(start.calls) == 2
    assert "refused before the endpoint" not in caplog.text
    check_quiet(seen if answer == "endpoint" else Seen(b"", "closed", 0.0), capsys, caplog)


def test_n10_refusals_before_the_signature_are_debug_and_a_verified_request_is_info(capsys, caplog):
    """Review N10. Whoever reaches the port chooses how many of these there are: an idle connection,
    a broken or too long request line, 400 on the length, 401, 404, 405. None writes a line above
    DEBUG. A verified request keeps its one INFO line."""
    start = FakeStart()
    body = body_bytes()
    n = len(body)
    with serving(make_wsgi(start)) as server:
        port = server.server_port
        statuses = [
            drive_silent_client(port).status,
            drive_garbage(port).status,
            drive_long_request_line(port).status,
            drive_no_content_length(port).status,
            exchange(port, custom(body, sign=False)).status,
            exchange(port, custom(body, line="POST /v1/other HTTP/1.1")).status,
            exchange(port, custom(body, line=f"GET {endpoint.PATH} HTTP/1.1")).status,
            exchange(port, custom(body, lengths=(n, n))).status,
        ]
        assert statuses == [400, 400, 414, 400, 401, 404, 405, 400]
        assert _handlers_done()
        refusals = trigger_records(caplog)
        caplog.clear()
        seen = drive_signed(port)
    assert len(refusals) == len(statuses), refusals
    assert {level for level, _ in refusals} == {"DEBUG"}, refusals
    assert seen.status == 202
    assert trigger_records(caplog) == [("INFO", f"trigger status=202 sender={SENDER}")]
    check_quiet(seen, capsys, caplog)


def test_n11_a_process_variable_cannot_stand_in_for_a_missing_header(monkeypatch, capsys, caplog):
    """Review N11. The stdlib application handler starts every request environment from a copy of
    the process environment (taken when `wsgiref.handlers` is first imported, so the test takes the
    copy again after it planted its variables). A request without the signature and timestamp
    headers must be 401 although the process holds variables with a valid signature for its body;
    one without Content-Length must be 400 although the process holds the right length."""
    import wsgiref.handlers

    start = FakeStart()
    body = body_bytes()
    signed = hmac_v0.sign(body, int(time.time()), SECRET, endpoint.PREFIX)
    for name, value in signed.items():
        monkeypatch.setenv("HTTP_" + name.upper().replace("-", "_"), value)
    monkeypatch.setenv("CONTENT_LENGTH", str(len(body)))
    monkeypatch.setenv("CONTENT_TYPE", "text/" + LINE_MARK)
    planted = wsgiref.handlers.read_environ()
    assert len([k for k in planted if k.startswith("HTTP_X_HADAVIN_")]) == 2
    monkeypatch.setattr(wsgiref.handlers.BaseHandler, "os_environ", planted)
    seen_environs: list[dict[str, object]] = []
    wsgi = make_wsgi(start)

    def spy(environ, start_response):
        seen_environs.append(dict(environ))
        return wsgi(environ, start_response)

    with serving(spy) as server:
        unsigned = exchange(server.server_port, custom(body, sign=False))
        no_length = exchange(server.server_port, custom(body, lengths=()))
        control = exchange(server.server_port, custom(body))
    assert unsigned.status == 401, unsigned
    assert no_length.status == 400, no_length
    assert control.status == 202 and len(start.calls) == 1
    # the refused requests never reach the application; the signed one is the control, and it
    # must carry none of the planted values (only what the handler itself built from the request)
    (seen_environ,) = seen_environs
    leaked = {k for k, v in seen_environ.items() if k in planted and planted[k] == v}
    assert not leaked - {"HTTP_X_HADAVIN_REQUEST_TIMESTAMP", "HTTP_X_HADAVIN_SIGNATURE"}, leaked
    assert seen_environ["CONTENT_TYPE"] == "text/plain"  # the stdlib's own default, not the variable
    check_quiet(unsigned, capsys, caplog)
