"""Round 7G: the r7f review (netconnect and the load driver). Real loopback sockets, made-up data only.

Every test says in its docstring whether it FAILS on r7f (a real run is in R7G-RESULTS.md) or is a CONTROL (passes on
r7f as well), and which mutant it kills (a mutant really run, in R7G-RESULTS.md)."""

from __future__ import annotations

import json
import socket
import threading
import time
import types
from pathlib import Path
from typing import Any

import pytest
from test_r7d_findings import _run_driver
from test_r7f_findings import _AnswersOnlyAfter, _HangingLookup, _provider, _SlowConn
from test_real_check_dry import _valid_config, rrc

from demo_only.fake_smtp_tls import FAKE_PASSWORD
from lead_desk import netconnect
from lead_desk.contract import SendUnreachable
from lead_desk.imap_count import ImapConnectionError, ImapCountError, ImapSettingRefused, ImapSettings, counts_by_key
from lead_desk.netconnect import connect_bounded, resolve_bounded
from load_tools import load_driver

LOOKUP_REFUSED_TEXT = "the host name cannot be looked up"  # written out here: the test does not read the code's text

# names the look-up itself refuses with a UnicodeError (not a gaierror): label of more than 63 characters, empty label,
# lone surrogate. A trailing dot is one empty label only when it is doubled.
LABEL_64 = "a" * 64 + ".example.test"
LABEL_70 = "a" * 70 + ".example.test"
BAD_NAMES = [LABEL_64, LABEL_70, "a..example.test", "example.test..", "..", "\udcff.example.test", "a\udcffb.test"]


def _wait_lookup_threads() -> None:
    """The helper thread may still be ending when the call has returned: wait for it (a traceback is printed by it)."""
    for t in threading.enumerate():
        if t.name == "name-lookup":
            t.join(5)


# ---- M1: whatever the look-up raises, one fixed OSError, nothing on stderr, no IndexError ----


@pytest.mark.parametrize("name", BAD_NAMES)
def test_m1_a_name_the_lookup_refuses_gives_one_fixed_oserror_and_no_traceback(
    name: str, capfd: pytest.CaptureFixture[str]
) -> None:
    """FAILS on r7f (IndexError out of connect_bounded and a traceback of the helper thread on stderr)."""
    with pytest.raises(OSError) as e:
        connect_bounded(name, 9, 2.0)
    _wait_lookup_threads()
    assert type(e.value) is OSError and str(e.value) == LOOKUP_REFUSED_TEXT
    assert not isinstance(e.value, (IndexError, TimeoutError))
    assert capfd.readouterr().err == ""


class _Boom(BaseException):
    """Not an Exception: what `except Exception` does not catch."""


@pytest.mark.parametrize(
    "raised", [RuntimeError("x"), ValueError("x"), MemoryError(), _Boom("x"), SystemExit(3), KeyboardInterrupt()]
)
def test_m1_whatever_the_lookup_raises_the_caller_gets_the_fixed_oserror_and_stderr_stays_empty(
    raised: BaseException, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """FAILS on r7f for every case but none (IndexError and a traceback). Kills mutants N01 (`except BaseException`
    in the helper thread narrowed to Exception: the BaseException cases print a traceback)."""

    def boom(*_a: object, **_k: object) -> list[Any]:
        raise raised

    monkeypatch.setattr(socket, "getaddrinfo", boom)
    with pytest.raises(OSError) as e:
        resolve_bounded("name.example.test", 9, 2.0)
    _wait_lookup_threads()
    assert type(e.value) is OSError and str(e.value) == LOOKUP_REFUSED_TEXT
    assert capfd.readouterr().err == ""


def test_m1_an_empty_box_is_never_indexed(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7f (IndexError). Kills mutant N02 (`box[0] if box else None` replaced by `box[0]`)."""
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_a, **_k: (_ for _ in ()).throw(UnicodeError("label")))
    with pytest.raises(OSError, match=LOOKUP_REFUSED_TEXT):
        resolve_bounded("x.example.test", 9, 2.0)


def test_m1_a_gaierror_ends_as_the_one_fixed_text_and_a_lookup_that_works_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """r7h: a gaierror of the look-up is now the ONE fixed text too (r7g passed it on as it was, with the system's own
    words and error number); a result is returned as it is. Kills mutant N03 (the stored OSError is the raw error)."""

    def gone(*_a: object, **_k: object) -> list[Any]:
        raise socket.gaierror(-2, "Name or service not known")

    monkeypatch.setattr(socket, "getaddrinfo", gone)
    with pytest.raises(OSError, match=LOOKUP_REFUSED_TEXT) as e:
        resolve_bounded("x.example.test", 9, 2.0)
    assert str(e.value) == LOOKUP_REFUSED_TEXT and type(e.value) is OSError  # not a gaierror, no error number
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_a, **_k: [(2, 1, 6, "", ("127.0.0.1", 9))])
    assert resolve_bounded("x.example.test", 9, 2.0) == [(2, 1, 6, "", ("127.0.0.1", 9))]


@pytest.mark.parametrize("name", BAD_NAMES[:5] + ["\udcff.example.test"])
def test_m1_the_mailbox_read_with_a_bad_host_name_ends_in_one_fixed_line(
    name: str, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """FAILS on r7f (IndexError out of the mailbox read, traceback on stderr). The settings object refuses such a host
    (see the next test), so the host is forced in afterwards: this is the defence at the look-up itself."""
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    s = ImapSettings(
        "localhost", "reader-user", pw, port=993, folders=("INBOX",), timeout_seconds=2.0, total_seconds=3.0
    )
    object.__setattr__(s, "host", name)
    with pytest.raises(ImapConnectionError) as e:
        counts_by_key(s, "L")
    _wait_lookup_threads()
    assert str(e.value) == "the mailbox could not be read" and type(e.value) is ImapConnectionError
    assert capfd.readouterr().err == ""


@pytest.mark.parametrize("name", BAD_NAMES + ["", " ", "a b.test", "host\n", "a/b", "[::1]x", "a_b.test", "-a.test"])
def test_m1_the_mailbox_settings_refuse_a_bad_host_name(name: str, tmp_path: Path) -> None:
    """FAILS on r7f (no host check: the settings object is made). Kills mutant N04 (the host check removed)."""
    with pytest.raises(ImapSettingRefused) as e:
        ImapSettings(name, "reader-user", tmp_path / "p")
    assert str(e.value) == "the mailbox host must be a host name (letters, digits, hyphens and dots)"
    assert name.strip() == "" or name not in str(e.value)  # the typed value is never printed back
    assert isinstance(e.value, ImapCountError) and isinstance(e.value, ValueError)


@pytest.mark.parametrize(
    "name", ["h", "localhost", "127.0.0.1", "imap.example.test", "IMAP.Example.Test", "a" * 63 + ".t"]
)
def test_m1_the_mailbox_settings_still_take_a_plain_host_name(name: str, tmp_path: Path) -> None:
    """CONTROL (passes on r7f): the hosts the other tests and the real check use are not refused."""
    assert ImapSettings(name, "reader-user", tmp_path / "p").host == name


def test_m1_the_real_check_refuses_a_bad_mailbox_host_before_the_start_question(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FAILS on r7f (the bad host is accepted; the run goes on to the start question). On r7g: exit 2 (the refusal
    code of this script for every refusal at its start), ONE line, the typed host not printed, nothing real done."""
    bad = "a" * 70 + ".example.test"
    cfg = _valid_config(tmp_path, REAL_IMAP_1_HOST=bad)
    code = rrc.main(["--config", str(cfg)])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_REFUSED, (code, out[-300:])
    assert len([x for x in out.splitlines() if x.strip()]) == 1, out
    assert bad not in out and "Traceback" not in out


@pytest.mark.parametrize("name", ["a" * 70 + ".example.test", "a..example.test", "example.test.."])
def test_m1_the_mail_send_with_a_bad_host_name_is_one_unreachable_and_no_traceback(
    name: str, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """FAILS on r7f (the error carries the class name IndexError; a traceback on stderr). The settings object refuses
    such a host, so it is forced in afterwards (the defence at the look-up). One fixed refusal: SendUnreachable."""
    import ssl

    ctx = ssl.create_default_context()
    box = _provider(tmp_path, 9, ctx)
    object.__setattr__(box._s, "host", name)
    with pytest.raises(SendUnreachable) as e:
        box.send("K-1", "ada@example.test", "Hi", "Body", 1.0)
    _wait_lookup_threads()
    assert "IndexError" not in repr(e.value) and name not in repr(e.value)
    assert capfd.readouterr().err == ""


# ---- m1: each address its own slice, inside the total ----


class _FakeSock:
    """Wraps a real socket. The 'blackhole' address never answers: connect waits for the time-out it was given."""

    log: list[tuple[str, float | None]]
    closed: list[bool]
    BLACKHOLE = "127.0.0." + "2"  # a marker; nothing is ever connected to it

    def __init__(
        self, family: int, kind: int, proto: int, log: list[Any], closed: list[bool], error: BaseException | None
    ) -> None:
        self._s = socket.socket(family, kind, proto)
        self._error = error
        self._t: float | None = None
        self._log, self._closed = log, closed

    def settimeout(self, t: float | None) -> None:
        self._t = t
        self._s.settimeout(t)

    def connect(self, address: tuple[str, int]) -> None:
        self._log.append((address[0], self._t))
        if self._error is not None:
            raise self._error
        if address[0] == self.BLACKHOLE:
            time.sleep(self._t or 0.0)
            raise TimeoutError("timed out")
        self._s.connect(address)

    def close(self) -> None:
        self._closed.append(True)
        self._s.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._s, name)


def _shim(
    monkeypatch: pytest.MonkeyPatch, addresses: list[str], port: int, connect_error: BaseException | None = None
) -> tuple[list[tuple[str, float | None]], list[bool]]:
    log: list[tuple[str, float | None]] = []
    closed: list[bool] = []
    found = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, port)) for a in addresses]

    def make(family: int, kind: int, proto: int = 0) -> Any:
        return _FakeSock(family, kind, proto, log, closed, connect_error)

    shim = types.SimpleNamespace(
        getaddrinfo=lambda *_a, **_k: found, SOCK_STREAM=socket.SOCK_STREAM, socket=make, AF_INET=socket.AF_INET
    )
    monkeypatch.setattr(netconnect, "socket", shim)
    return log, closed


def test_m1_a_first_address_that_never_answers_does_not_use_the_whole_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7f (the first address waits the whole 3 s, the second is never tried: TimeoutError). Kills mutants
    A01 (the per-address cap removed: `own = left` for every address) and A02 (the cap applied to the LAST address
    too: the last gets min(cap, left))."""
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 0.5, raising=False)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    log, _ = _shim(monkeypatch, [_FakeSock.BLACKHOLE, "127.0.0.1"], srv.getsockname()[1])
    try:
        start = time.monotonic()
        conn = connect_bounded("name.example.test", srv.getsockname()[1], 3.0)
        took = time.monotonic() - start
        conn.close()
    finally:
        srv.close()
    assert [a for a, _ in log] == [_FakeSock.BLACKHOLE, "127.0.0.1"]
    assert 0.4 < took < 1.5, took  # the first address used its slice only
    first, second = log[0][1], log[1][1]
    assert first is not None and second is not None
    assert first == pytest.approx(0.5, abs=0.05)  # min(cap, left)
    assert 2.0 < second <= 2.6, second  # the last address gets all the time that is left, more than the cap


def test_m1_one_address_keeps_the_whole_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """CONTROL on r7f in effect (a single address always got the time left). Kills A02 (the cap on the last)."""
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 0.5, raising=False)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    log, _ = _shim(monkeypatch, ["127.0.0.1"], srv.getsockname()[1])
    try:
        connect_bounded("name.example.test", srv.getsockname()[1], 3.0).close()
    finally:
        srv.close()
    assert log[0][1] is not None and 2.5 < log[0][1] <= 3.0


def test_m1_the_total_limit_holds_over_many_silent_addresses(monkeypatch: pytest.MonkeyPatch) -> None:
    """The total deadline is kept: four silent addresses, cap 0.4, total 1.0 s: TimeoutError at about 1 s, and the
    address after the time is used is not tried. FAILS on r7f (the first address waits the whole second, one address is
    tried). Since r7h the four addresses get an even share (0.25 s) each and all are tried; the `left <= 0` check
    (mutant A03) is killed by test_m2_an_address_that_overruns_the_whole_limit in test_r7h_findings.py."""
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 0.4, raising=False)
    log, _ = _shim(monkeypatch, [_FakeSock.BLACKHOLE] * 4, 9)
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        connect_bounded("name.example.test", 9, 1.0)
    took = time.monotonic() - start
    assert took < 1.4, took
    assert len(log) == 4  # the even split (r7h): 0.25 each, all four tried; nothing is started after the time is gone
    assert all(t is not None and t <= 0.26 for _, t in log), log
    # r7k: the lower bound (0.24 <= t) was removed: it failed under machine load; the exact share is pinned by
    # test_m4 in test_r7j_findings.py with a fake clock


@pytest.mark.parametrize(
    "error", [RuntimeError("x"), KeyboardInterrupt(), ConnectionRefusedError("x"), TimeoutError("x")]
)
def test_n1_the_socket_is_closed_on_any_exception(error: BaseException, monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7f for RuntimeError and KeyboardInterrupt (the socket is left to the garbage collector). Kills mutant
    A04 (`except BaseException` narrowed to `except OSError`)."""
    _, closed = _shim(monkeypatch, ["127.0.0.1"], 9, connect_error=error)
    with pytest.raises(type(error)):
        connect_bounded("name.example.test", 9, 2.0)
    assert closed == [True]


def test_m1_a_connection_refused_on_every_address_raises_the_last_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """CONTROL (passes on r7f). Kills mutant A05 (the error of the last address replaced by the generic text)."""
    _shim(monkeypatch, ["127.0.0.1", "127.0.0." + "3"], 9, connect_error=ConnectionRefusedError("last"))
    with pytest.raises(ConnectionRefusedError, match="last"):
        connect_bounded("name.example.test", 9, 2.0)


# ---- the load driver's look for a listener goes through netconnect ----


def test_the_load_driver_listener_probe_is_bounded_when_the_name_look_up_hangs(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7f (socket.create_connection waits for the look-up: 30 s here). Kills mutant L01 (the probe goes back
    to socket.create_connection)."""
    monkeypatch.setattr(load_driver, "CONNECT_PROBE_SECONDS", 0.5)
    hang = _HangingLookup(monkeypatch)
    try:
        start = time.monotonic()
        assert load_driver.desk_listening("http://localhost:9") is False
        assert time.monotonic() - start < 2.5
    finally:
        hang.release.set()


def test_the_load_driver_listener_probe_still_finds_a_listener_and_refuses_a_bad_name() -> None:
    """CONTROL (passes on r7f)."""
    ls = socket.socket()
    ls.bind(("127.0.0.1", 0))
    ls.listen(1)
    try:
        assert load_driver.desk_listening(f"http://127.0.0.1:{ls.getsockname()[1]}") is True
    finally:
        ls.close()
    assert load_driver.desk_listening("http://" + "a" * 70 + ".test:9") is False
    assert load_driver.desk_listening("http://" + ":9") is False


# ---- M2: every request that the stop took out of the run is counted, in ONE place ----


class _FirstAnsweredLate(_AnswersOnlyAfter):
    QUIET = 2.0


def test_m2_a_request_given_up_by_the_stop_makes_the_run_end_with_exit_code_3(tmp_path: Path) -> None:
    """FAILS on r7f (rc 0, summary stopped 0, no ERROR line). The pattern of the r7f review: the first real request is
    answered 202 after 2 s, every other connection is closed; burst:2, 1 worker, 2 threads. The second request is
    already retrying when the stop is set, so it is logged gave_up 'stopped' with final status 'error' (not
    driver:stopped). Kills mutant D01 (stopped_count back to counting driver:stopped lines only)."""
    srv = _FirstAnsweredLate()
    try:
        log = tmp_path / "req.jsonl"
        done = _run_driver(
            f"http://127.0.0.1:{srv.port}", "burst:2", log, "--workers", "1", "--threads", "2", timeout=120
        )
    finally:
        srv.close()
    err = done.stderr.decode()
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    given_up = [d for d in lines if d["gave_up"] == "stopped" and d["final_status"] != "driver:stopped"]
    assert given_up and [d for d in lines if d["accepted"]], [(d["final_status"], d["gave_up"]) for d in lines]
    assert done.returncode == 3, (done.returncode, err[-300:])
    assert "1 of 2 requests were never sent or were given up" in err, err[-300:]
    assert "cannot be reached" not in err  # an answer did arrive, so that line would be false
    assert json.loads(done.stdout.decode())["stopped"] == 1


def test_m2_stopped_count_counts_both_kinds_and_nothing_else() -> None:
    """FAILS on r7f (no such function). Kills D01 (only `driver:stopped`) and D02 (only `gave_up == stopped` lines
    that have final status `error`)."""
    lines = [
        {"final_status": "driver:stopped", "gave_up": "stopped"},
        {"final_status": "error", "gave_up": "stopped"},
        {"final_status": 503, "gave_up": "stopped"},
        {"final_status": 503, "gave_up": "deadline"},
        {"final_status": "error", "gave_up": "deadline"},
        {"final_status": 202, "gave_up": None},
        {"final_status": "driver:error", "gave_up": "driver_error"},
    ]
    assert load_driver.stopped_count(lines) == 3
    assert load_driver.stopped_count([]) == 0


class _Only(_AnswersOnlyAfter):
    """A stand-in desk with a fixed pattern: `answer(n)` gives the status for the n-th request (None = close)."""

    QUIET = 0.0
    DROP_FROM, DROP_TO = 10**9, 10**9 + 1
    STATUS = 202

    def _one(self, conn: Any) -> None:
        conn2 = _SlowConn(conn, 0.0)
        with conn2:
            conn2.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                piece = conn2.recv(65536)
                if not piece:
                    return
                data += piece
            head, _, body = data.partition(b"\r\n\r\n")
            need = 0
            for h in head.split(b"\r\n")[1:]:
                k, _, v = h.partition(b":")
                if k.strip().lower() == b"content-length":
                    need = int(v.strip())
            while len(body) < need:
                body += conn2.recv(65536)
            raw = b'{"receipt_id": "r", "verdict": "accepted"}'
            out = f"HTTP/1.1 {self.STATUS} X\r\nContent-Length: {len(raw)}\r\nConnection: close\r\n\r\n".encode()
            conn2.sendall(out + raw)


@pytest.mark.parametrize("status", [202, 429])
def test_m2_a_desk_that_always_answers_ends_with_exit_code_0(status: int, tmp_path: Path) -> None:
    """CONTROL (passes on r7f, as the review found): only 202, only 429 are answers: no stop, rc 0, no ERROR line."""

    class Srv(_Only):
        STATUS = status

    srv = Srv()
    try:
        log = tmp_path / "req.jsonl"
        done = _run_driver(
            f"http://127.0.0.1:{srv.port}", "burst:4", log, "--workers", "1", "--threads", "2", timeout=120
        )
    finally:
        srv.close()
    assert done.returncode == 0, (done.returncode, done.stderr.decode()[-300:])
    assert "ERROR" not in done.stderr.decode()
    assert json.loads(done.stdout.decode())["stopped"] == 0
