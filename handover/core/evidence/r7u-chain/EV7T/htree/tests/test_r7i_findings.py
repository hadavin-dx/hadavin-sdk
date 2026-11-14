"""Round 7I: tests for the mutants of the r7g mutant pass (pass 9) that no test saw. A mutant is a one-line change to
the code; "survived" means the whole test set stayed green, so the behaviour it changed was not checked. Made-up data
only, loopback only; sockets are fakes that record the time limit they are given.

Header table (finding | mutant | what the test pins | why it matters). Every row is a PIN: the code was already right,
the test was missing; the proof is that each test FAILS on its mutant (see R7I-RESULTS.md).
  i1 | M9-22 | SmtpOutbox.send("") refuses with "empty send key" and opens no connection
     | a mail with an empty count key can never be matched by the count, so a double send stays hidden
  i2 | M9-02 | (test_order_* in test_r7h_findings.py kill it) a refused call leaves the send cap whole
     | a bad secret must not cost a send
  i3 | M9-12 | the login is accepted only on exactly 235 | any other 2xx is not a login
  i4 | M9-03 | the provider's own limit caps the caller's time; 0 or less means that limit
     | a caller cannot lengthen the provider send
  i5 | M9-18 | SmtpOutbox: 0 or less means the outbox's own limit, never a zero budget
     | 0 must not turn every send into "unreachable"
  i6 | M9-08 | the TLS handshake gets the time left, not an older limit of the socket
     | a handshake that never ends must stop inside the budget
  i7 | M9-19 | the connect of SmtpOutbox gets the time left | same, for the connect
  i8 | M9-23 | a command is written with the time left, not an older limit | same, for the write
  i10 | sibling of M9-23 | the message text (smtp_outbox and smtp_provider) is written with the time left
     | same class, found by the sweep
  i11 | sibling of M9-08 | the mailbox (imap_count) handshake gets the time left of the total | same class
  i9 | M9-30 | a TLS version that is None, empty or unknown is refused; only 1.2 and 1.3 pass
     | a missing answer must not count as a good one"""

from __future__ import annotations

import socket
import ssl
import threading
import time
import types
from pathlib import Path
from typing import Any

import pytest
from test_r7f_findings import _Certs, _provider
from test_smtp_outbox import SUBJECT, TO, Script

from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp
from lead_desk import smtp_outbox, smtp_provider
from lead_desk.contract import SendRefused, SendUnreachable
from lead_desk.smtp_outbox import SmtpOutbox, SmtpSettings, _Budget, _command
from lead_desk.tls_trust import TLS_OK_VERSIONS, CaFileRefused, require_modern_protocol

LOOP = "127.0.0." + "1"


class _TimedSock:
    """Records the time limit that is set on it when each call is made. Starts with an OLD limit (10 s) on purpose: a
    send that does not set the time left would then run with the old one."""

    def __init__(self, first: float | None = 10.0) -> None:
        self.t = first
        self.log: list[tuple[str, float | None]] = []

    def settimeout(self, t: float | None) -> None:
        self.t = t

    def gettimeout(self) -> float | None:
        return self.t

    def sendall(self, _data: bytes) -> None:
        self.log.append(("send", self.t))

    def recv(self, _n: int) -> bytes:
        self.log.append(("recv", self.t))
        return b"250 ok\r\n"

    def connect(self, _address: Any) -> None:
        self.log.append(("connect", self.t))
        raise ConnectionRefusedError("refused")

    def close(self) -> None:
        pass


# ---- i1: M9-22 ----


def _listener() -> socket.socket:
    srv = socket.socket()
    srv.bind((LOOP, 0))
    srv.listen(4)
    srv.setblocking(False)
    return srv


def test_i1_an_empty_send_key_is_refused_and_no_connection_is_opened() -> None:
    """Kills M9-22 (the empty-key check removed: the mail went out with an empty X-Send-Key no count can match)."""
    srv = _listener()
    try:
        box = SmtpOutbox(SmtpSettings(host=LOOP, port=srv.getsockname()[1]))
        with pytest.raises(SendRefused) as e:
            box.send("", TO, SUBJECT, "Hi", 2.0)
        assert str(e.value) == "empty send key"
        with pytest.raises(BlockingIOError):  # nothing is waiting to be accepted: the desk never connected
            srv.accept()
    finally:
        srv.close()


def test_i1_the_provider_also_refuses_an_empty_send_key_before_the_network(tmp_path: Path) -> None:
    """Sibling path (pin): the provider's key pattern needs 1 to 64 characters; nothing is counted, nothing connects."""
    certs = _Certs(tmp_path)
    srv = FakeSmtp(certs.cert, certs.key, "localhost")
    try:
        box = _provider(tmp_path, srv.port, certs.context())
        with pytest.raises(SendRefused):
            box.send("", TO, SUBJECT, "Hi", 2.0)
        assert srv.commands == [] and box.attempts == 0
    finally:
        srv.close()


# ---- i2: M9-02 (extra pin: a refused call leaves the cap whole) ----


def test_i2_a_call_refused_for_a_bad_password_file_does_not_use_up_the_send_cap(tmp_path: Path) -> None:
    """Kills M9-02 a second way: with a cap of 1, a bad password file is refused, then a good file still sends."""
    certs = _Certs(tmp_path)
    srv = FakeSmtp(certs.cert, certs.key, "localhost")
    try:
        bad = tmp_path / "bad-secret.txt"  # missing
        box = _provider(tmp_path, srv.port, certs.context(), max_sends=1, password_file=bad)
        with pytest.raises(SendRefused):
            box.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0)
        assert box.attempts == 0 and srv.commands == []
        good = tmp_path / "good-secret.txt"
        good.write_text(srv.password + "\n", encoding="utf-8")
        box2 = _provider(tmp_path, srv.port, certs.context(), max_sends=1, password_file=good)
        assert box2.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0) == "SENT"
    finally:
        srv.close()


# ---- i3: M9-12 ----


@pytest.mark.parametrize("code", [200, 234, 236, 250, 299])
def test_i3_a_login_reply_that_is_a_2xx_but_not_235_is_refused_and_nothing_goes_further(
    code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills M9-12 (any 2xx accepted as a login). The fake server really says 235; the reply the desk reads is changed
    to `code`, so the desk sees "250 ok" where only 235 is a login. MAIL FROM must never be sent."""
    certs = _Certs(tmp_path)
    srv = FakeSmtp(certs.cert, certs.key, "localhost")
    real = smtp_provider._command

    def changed(conn: Any, budget: Any, buf: bytearray, line: str) -> int:
        got = real(conn, budget, buf, line)
        return code if line.startswith("AUTH PLAIN") else got

    monkeypatch.setattr(smtp_provider, "_command", changed)
    try:
        box = _provider(tmp_path, srv.port, certs.context())
        with pytest.raises(SendRefused) as e:
            box.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0)
        assert str(e.value) == "login refused"
        assert "MAIL" not in srv.commands and srv.messages == [] and box.sent == 0
    finally:
        srv.close()


# ---- i4 / i5: M9-03, M9-18 (the time limit of one send) ----


class _RecordingBudget(_Budget):
    seen: list[float] = []

    def __init__(self, seconds: float) -> None:
        type(self).seen.append(seconds)
        super().__init__(seconds)


def _no_connect(*_a: Any) -> Any:
    raise SendUnreachable("stop here: the budget was read")


@pytest.mark.parametrize(("asked", "expected"), [(30.0, 2.0), (1.0, 1.0), (2.0, 2.0), (0.0, 2.0), (-5.0, 2.0)])
def test_i4_the_provider_never_runs_longer_than_its_own_limit_and_zero_means_that_limit(
    asked: float, expected: float, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills M9-03 (the provider's cap ignored: the caller's 30 s was used). The provider limit here is 2.0 s."""
    monkeypatch.setattr(_RecordingBudget, "seen", [])
    monkeypatch.setattr(smtp_provider, "_Budget", _RecordingBudget)
    box = _provider(tmp_path, 9, ssl.create_default_context(), timeout_seconds=2.0)
    monkeypatch.setattr(box, "_connect", _no_connect)
    with pytest.raises(SendUnreachable):
        box.send("RUN1-L-001", TO, SUBJECT, "Hi", asked)
    assert _RecordingBudget.seen == [expected]


@pytest.mark.parametrize(("asked", "expected"), [(30.0, 30.0), (1.0, 1.0), (0.0, 2.0), (-5.0, 2.0)])
def test_i5_the_outbox_takes_zero_or_less_as_its_own_limit_never_as_a_zero_budget(
    asked: float, expected: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills M9-18 (`timeout >= 0`: a time of 0 became a zero budget, so every send ended as unreachable)."""
    monkeypatch.setattr(_RecordingBudget, "seen", [])
    monkeypatch.setattr(smtp_outbox, "_Budget", _RecordingBudget)
    box = SmtpOutbox(SmtpSettings(host=LOOP, port=9, timeout_seconds=2.0))
    monkeypatch.setattr(box, "_connect", _no_connect)
    with pytest.raises(SendUnreachable):
        box.send("K-1", TO, SUBJECT, "Hi", asked)
    assert _RecordingBudget.seen == [expected]


def test_i5_a_send_with_time_0_really_goes_through_to_a_server_that_answers() -> None:
    """Kills M9-18 end to end: a full dialogue (EHLO refused once, HELO fallback, final 250) with timeout 0."""
    s = Script("ehlo_500")
    try:
        assert SmtpOutbox(SmtpSettings(host=LOOP, port=s.port)).send("K-2", TO, SUBJECT, "Hi", 0.0) == "SENT"
    finally:
        s.close()


# ---- i6 / i7 / i8: M9-08, M9-19, M9-23 (every step is given the time LEFT) ----


def test_i6_the_tls_handshake_is_given_the_time_left_not_an_older_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills M9-08 (the settimeout before wrap_socket removed: the handshake ran with the old 10 s limit)."""
    ctx = ssl.create_default_context()
    seen: list[float | None] = []

    def wrap(sock: Any, server_hostname: str | None = None) -> Any:
        seen.append(sock.gettimeout())
        raise ssl.SSLError("stop here")

    monkeypatch.setattr(ctx, "wrap_socket", wrap)
    box = _provider(tmp_path, 9, ctx, timeout_seconds=2.0)
    sock: Any = _TimedSock(first=10.0)
    with pytest.raises(ssl.SSLError):
        box._wrap(sock, _Budget(2.0))
    assert len(seen) == 1 and seen[0] is not None and 0 < seen[0] <= 2.0


def test_i6_a_server_that_takes_the_connection_and_never_speaks_tls_ends_inside_the_budget(tmp_path: Path) -> None:
    """PIN (end to end, passes on the mutant by design: the old limit is about as long as the budget): TLS from the
    first byte against a plain listener that never answers."""
    srv = socket.socket()
    srv.bind(("localhost", 0))
    srv.listen(2)
    held: list[socket.socket] = []
    stop = threading.Event()

    def take() -> None:
        srv.settimeout(0.2)
        while not stop.is_set():
            try:
                held.append(srv.accept()[0])
            except OSError:
                pass

    th = threading.Thread(target=take, daemon=True)
    th.start()
    try:
        box = _provider(
            tmp_path, srv.getsockname()[1], ssl.create_default_context(), security="ssl", timeout_seconds=0.8
        )
        t0 = time.monotonic()
        with pytest.raises(SendUnreachable):
            box.send("RUN1-L-001", TO, SUBJECT, "Hi", 30.0)
        assert time.monotonic() - t0 < 2.5
    finally:
        stop.set()
        th.join(2)
        for c in held:
            c.close()
        srv.close()


def test_i7_the_connect_of_the_outbox_is_given_the_time_left(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills M9-19 (the settimeout before connect removed: the connect could wait without a limit)."""
    made: list[_TimedSock] = []

    def make(_family: int, _kind: int) -> _TimedSock:
        made.append(_TimedSock(first=None))  # a new socket has no limit
        return made[-1]

    shim = types.SimpleNamespace(
        socket=make, AF_INET=socket.AF_INET, AF_INET6=socket.AF_INET6, SOCK_STREAM=socket.SOCK_STREAM
    )
    monkeypatch.setattr(smtp_outbox, "socket", shim)
    box = SmtpOutbox(SmtpSettings(host=LOOP, port=9, timeout_seconds=2.0))
    with pytest.raises(SendUnreachable):
        box.send("K-3", TO, SUBJECT, "Hi", 2.0)
    ((step, limit),) = made[0].log
    assert step == "connect" and limit is not None and 0 < limit <= 2.0


def test_i8_a_command_is_written_with_the_time_left_not_an_older_limit() -> None:
    """Kills M9-23 (the settimeout before sendall removed) and pins the read (M9-20 is killed elsewhere)."""
    sock: Any = _TimedSock(first=10.0)
    assert _command(sock, _Budget(2.0), bytearray(), "NOOP") == 250
    assert [s for s, _ in sock.log] == ["send", "recv"]
    assert all(t is not None and 0 < t <= 2.0 for _, t in sock.log)


# ---- i9: M9-30 ----


class _Conn:
    def __init__(self, version: str | None) -> None:
        self._v = version

    def version(self) -> str | None:
        return self._v


@pytest.mark.parametrize("version", [None, "", "TLSv1.4", "TLSv9", "TLSv1.1", "TLSv1", "SSLv3", "DTLSv1.2", "tlsv1.3"])
def test_i9_a_tls_version_that_is_missing_unknown_or_old_is_refused(version: str | None) -> None:
    """Kills M9-30 (the check changed to a list of old versions: None and unknown names passed)."""
    with pytest.raises(CaFileRefused):
        require_modern_protocol(_Conn(version), "the TLS connection")


@pytest.mark.parametrize("version", TLS_OK_VERSIONS)
def test_i9_control_tls_1_2_and_1_3_pass(version: str) -> None:
    require_modern_protocol(_Conn(version), "the TLS connection")


def test_i9_the_handshake_result_with_no_version_is_refused_before_the_login_and_the_socket_is_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills M9-30 through `_wrap`: a connection whose version is None gets SendRefused and is closed."""
    closed: list[bool] = []

    class _Wrapped(_Conn):
        def close(self) -> None:
            closed.append(True)

    ctx = ssl.create_default_context()
    monkeypatch.setattr(ctx, "wrap_socket", lambda sock, server_hostname=None: _Wrapped(None))
    box = _provider(tmp_path, 9, ctx)
    fake_sock: Any = _TimedSock()
    with pytest.raises(SendRefused):
        box._wrap(fake_sock, _Budget(2.0))
    assert closed == [True]


# ---- sibling sweep: the same class (a step is given the time LEFT, not the time of an earlier step) ----


class _ScriptedSock(_TimedSock):
    """Answers each read with the next scripted reply; the read for `slow` takes 0.6 s, so the budget shrinks."""

    def __init__(self, replies: list[bytes], slow: int) -> None:
        super().__init__(first=10.0)
        self._replies, self._slow, self._n = replies, slow, 0

    def recv(self, _n: int) -> bytes:
        if self._n == self._slow:
            time.sleep(0.6)
        self.log.append(("recv", self.t))
        self._n += 1
        return self._replies.pop(0)

    def sendall(self, data: bytes) -> None:
        self.log.append(("data" if data.endswith(b"\r\n.\r\n") else "send", self.t))


def _data_write_limit(sock: _ScriptedSock) -> float | None:
    return next(t for step, t in sock.log if step == "data")


def test_i10_the_outbox_writes_the_message_text_with_the_time_left() -> None:
    """Sibling of M9-23 (found by the sweep: `settimeout` before `sendall(wire)` in smtp_outbox removed survived). The
    reply to DATA takes 0.6 s of a 5 s budget (r7l: was 2 s);
    the text must then be written with at most the 4.4 s that is left."""
    replies = [b"220 ok\r\n", b"250 ok\r\n", b"250 ok\r\n", b"250 ok\r\n", b"354 go\r\n", b"250 queued\r\n"]
    sock: Any = _ScriptedSock(replies, slow=4)
    box = SmtpOutbox(SmtpSettings(host=LOOP, port=9, timeout_seconds=2.0))
    box._dialogue(sock, _Budget(5.0), TO, b"Subject: x\r\n\r\nhi\r\n.\r\n")
    t = _data_write_limit(sock)
    assert t is not None and 0 < t < 4.5


def test_i10_the_provider_writes_the_message_text_with_the_time_left(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sibling of M9-23 for smtp_provider (`conn.settimeout` before `conn.sendall(wire)` removed survived)."""
    replies = [
        b"220 ok\r\n",
        b"250 ok\r\n",
        b"235 ok\r\n",
        b"250 ok\r\n",
        b"250 ok\r\n",
        b"354 go\r\n",
        b"250 queued\r\n",
    ]
    sock: Any = _ScriptedSock(replies, slow=5)
    sock.version = lambda: "TLSv1.3"
    ctx = ssl.create_default_context()
    monkeypatch.setattr(ctx, "wrap_socket", lambda s, server_hostname=None: sock)
    box = _provider(tmp_path, 9, ctx, security="ssl", timeout_seconds=2.0)
    box._dialogue(sock, _Budget(5.0), FAKE_PASSWORD, "inbox-a@example.test", b"Subject: x\r\n\r\nhi\r\n.\r\n")
    t = _data_write_limit(sock)
    assert t is not None and 0 < t < 4.5


def test_i11_the_mailbox_handshake_is_given_the_time_left_of_the_total(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sibling of M9-08 in imap_count (`sock.settimeout` before the TLS wrap removed survived). The connect takes 0.6 s
    of a 5 s total (r7l: was 2 s); the connect gave the socket an old 10 s limit."""
    from lead_desk import imap_count

    seen: list[float | None] = []
    fake: Any = _TimedSock(first=10.0)

    def slow_connect(_host: str, _port: int, _seconds: float) -> Any:
        time.sleep(0.6)
        return fake

    def wrap(sock: Any, server_hostname: str | None = None) -> str:
        seen.append(sock.gettimeout())
        return "wrapped"

    monkeypatch.setattr(imap_count, "connect_bounded", slow_connect)
    ctx: Any = types.SimpleNamespace(wrap_socket=wrap)
    box = object.__new__(imap_count._BoundedImap)
    box.host, box.port, box.ssl_context = "mail.example.test", 993, ctx
    box.deadline, box.step_seconds = time.monotonic() + 5.0, 10.0
    assert box._create_socket(10.0) == "wrapped"
    assert seen[0] is not None and 0 < seen[0] < 4.5
