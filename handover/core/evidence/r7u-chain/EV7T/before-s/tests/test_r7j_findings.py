"""Round 7J, fixes for the r7h review (core-fix-on-frozen-r7h-review.md). Made-up data only, loopback only; the name
look-up and the sockets are replaced by fakes. Header table: finding, mutant, what the test pins, result on a copy of
r7i (FAILS = new behaviour, fails before the fix; PIN = pure pin of code that was already right, passes by design).

  finding | mutant   | what is pinned                                                      | on r7i
  ------- | -------- | --------------------------------------------------------------- | ---------
  m1      | J01      | the socket is made inside the try: a family the machine lacks       | FAILS
          |          | (errno 97) fails that address only, the next address is tried       |
  m2      | J02,J02b | the cap counts every look-up thread from the reservation (under the | FAILS (20 threads)
          | J02c     | lock, before the thread starts); the place goes back when it ends   |
  m2      | J03      | a thread that cannot start gives its reserved place back            | PIN (r7i had none)
  m3      | J04-J04f | an IP address in digits and `localhost` never need a thread and are | FAILS (refused)
          |          | never refused by the cap; zone names and other names go the normal  |
          |          | way (J04b: equivalent, see R7J-RESULTS.md)                          |
  m4      | O4       | the even share is EXACTLY time left / addresses not yet tried       | PIN (O4 survived)
  m5      | O8, O9   | `_poll_readable`: the no-`poll` branch and the poll time-out unit   | PIN (survived)
  m6      | O5, O6   | the real driver run puts the true count into `given_up`; the line  | FAILS (exit code
          |          | shows `intended`, not `logged`                                      | changed by m7)
  m7      | J08-J11  | exit 3 and ONE line when given-up or stopped is above 0, same count | FAILS
  m7/O20  | O20      | a run with both kinds names both numbers in the one line            | FAILS
  n1      | J05      | a look-up with no address ends with the ONE fixed text              | FAILS
  n2      | J06,J07  | `archive` takes ASCII digits only; a returned email with a          | FAILS
          |          | non-ASCII letter is not "the same email"                            |
  n3      | O1       | the look-up that ends just after the time-out returns its result    | PIN (O1 survived)
"""

from __future__ import annotations

import contextlib
import io
import json
import socket
import threading
import time
import types
from pathlib import Path
from typing import Any

import pytest
from support import wait_until

from lead_desk import netconnect, server
from lead_desk.netconnect import connect_bounded, hung_lookups, resolve_bounded

FIXED = "the look-up of the host name took longer than the time limit"
REFUSED = "the host name cannot be looked up"
_ORIG_THREAD = threading.Thread
_ORIG_EVENT = threading.Event
KELVIN = chr(0x212A)


def _lookup_threads() -> int:
    return sum(1 for t in threading.enumerate() if t.name == "name-lookup" and t.is_alive())


def _shim(getaddrinfo: Any, make: Any = socket.socket) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        getaddrinfo=getaddrinfo, SOCK_STREAM=socket.SOCK_STREAM, socket=make, AF_INET=socket.AF_INET
    )


@pytest.fixture
def stuck(monkeypatch: pytest.MonkeyPatch):
    """getaddrinfo that blocks until released; the cap is 3 for speed. Yields (release, calls)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    release = threading.Event()
    calls: list[str] = []

    def blocking(host: str, *_a: Any, **_k: Any) -> list[Any]:
        calls.append(host)
        release.wait(20)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))]

    monkeypatch.setattr(netconnect, "socket", _shim(blocking))
    monkeypatch.setattr(netconnect, "LOOKUP_HUNG_MAX", 3, raising=False)
    yield release, calls
    release.set()
    wait_until(lambda: hung_lookups() == 0, what="stuck look-ups ended")


# ---- m1: an address family the machine does not have fails that address only ----


def test_m1_an_unavailable_address_family_does_not_stop_the_next_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """The review case: the look-up gives an IPv6 address first and an IPv4 one second; the machine has no IPv6 (the
    socket constructor raises OSError errno 97). FAILS on r7i (OSError 97 aborts the call, IPv4 never tried). Kills
    mutant J01 (the socket made before the `try` again)."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    made: list[int] = []

    def make(family: int, kind: int, proto: int = 0) -> socket.socket:
        made.append(family)
        if family == socket.AF_INET6:
            raise OSError(97, "Address family not supported by protocol")
        return socket.socket(family, kind, proto)

    found = [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
    ]
    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: found, make))
    try:
        conn = connect_bounded("name.example.test", port, 2.0)
        conn.close()
    finally:
        srv.close()
    assert made == [socket.AF_INET6, socket.AF_INET]


def test_m1_when_every_family_is_unavailable_the_last_error_is_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    """CONTROL for J01: with no usable address the error of the last one is raised (not a generic text)."""
    errors = [OSError(97, "first"), OSError(97, "second")]

    def make(*_a: Any) -> socket.socket:
        raise errors.pop(0)

    found = [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 9, 0, 0))] * 2
    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: found, make))
    with pytest.raises(OSError) as e:
        connect_bounded("name.example.test", 9, 2.0)
    assert e.value.errno == 97 and "second" in str(e.value)


def test_m1_a_socket_constructor_error_that_is_not_an_os_error_is_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only an OSError means 'try the next address'; anything else ends the call (as for a failing connect)."""

    def make(*_a: Any) -> socket.socket:
        raise RuntimeError("odd")

    found = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))] * 2
    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: found, make))
    with pytest.raises(RuntimeError):
        connect_bounded("name.example.test", 9, 2.0)


# ---- m2: the cap is true under concurrent callers ----


def test_m2_twenty_concurrent_callers_never_run_more_than_the_cap_of_look_up_threads(
    stuck: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The review probe: 20 callers at the same moment, a stuck resolver, cap 3. FAILS on r7i (20 look-ups started, 20
    threads). Starting a thread is made slow (0.15 s) so that a check made BEFORE the place is reserved lets every
    caller through. Kills mutant J02 (the place reserved after the thread start, or the check outside the lock)."""
    release, calls = stuck

    class SlowStart(_ORIG_THREAD):
        def start(self) -> None:
            time.sleep(0.15)
            super().start()

    monkeypatch.setattr(
        netconnect, "threading", types.SimpleNamespace(Lock=threading.Lock, Event=_ORIG_EVENT, Thread=SlowStart)
    )
    barrier = threading.Barrier(20)
    outcomes: list[str] = []
    peak = [0]

    def call(i: int) -> None:
        barrier.wait()
        try:
            resolve_bounded(f"h{i}.example.test", 9, 0.5)
            outcomes.append("answer")
        except TimeoutError as e:
            outcomes.append(str(e))
        peak[0] = max(peak[0], _lookup_threads())

    workers = [_ORIG_THREAD(target=call, args=(i,)) for i in range(20)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(30)
    assert outcomes == [FIXED] * 20  # three timed out, seventeen were refused at once: the same text
    assert len(calls) == 3 and peak[0] <= 3, (len(calls), peak[0])
    assert hung_lookups() == 3
    release.set()
    wait_until(lambda: hung_lookups() == 0, what="count back to 0")


def test_m2_the_count_includes_look_ups_that_are_still_waited_for(stuck: Any) -> None:
    """Two callers wait at once for the stuck resolver: both are counted while they wait (r7i counted only after the
    give-up). Kills mutant J02 in its other form (count raised only on the abandon path)."""
    release, calls = stuck
    seen: list[int] = []

    def call() -> None:
        with contextlib.suppress(TimeoutError):
            resolve_bounded("w.example.test", 9, 1.0)

    ts = [_ORIG_THREAD(target=call) for _ in range(2)]
    for t in ts:
        t.start()
    wait_until(lambda: len(calls) == 2, what="both look-ups started")
    seen.append(hung_lookups())
    release.set()
    for t in ts:
        t.join(10)
    assert seen == [2]


def test_m2_a_thread_that_cannot_start_gives_its_place_back(stuck: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """The reserved place goes back when `Thread.start` raises (no process-wide limit on threads, say). Kills mutant J03
    (no release on that path: five failures would close the cap of 3 for ever)."""
    _, calls = stuck

    class NoStart(_ORIG_THREAD):
        def start(self) -> None:
            raise RuntimeError("can't start new thread")

    monkeypatch.setattr(
        netconnect, "threading", types.SimpleNamespace(Lock=threading.Lock, Event=_ORIG_EVENT, Thread=NoStart)
    )
    for _ in range(5):
        with pytest.raises(RuntimeError):
            resolve_bounded("n.example.test", 9, 1.0)
    assert hung_lookups() == 0 and calls == []


# ---- m3: an IP address in digits and localhost never need a look-up and are never refused by the cap ----


def _fill_cap(release: Any, calls: list[str]) -> None:
    for i in range(3):
        with pytest.raises(TimeoutError):
            resolve_bounded(f"f{i}.example.test", 9, 0.05)
    assert hung_lookups() == 3 and len(calls) == 3


@pytest.mark.parametrize(
    ("host", "first"),
    [
        ("127.0.0.1", (socket.AF_INET, ("127.0.0.1", 9))),
        ("10.20" + ".30.40", (socket.AF_INET, ("10.20" + ".30.40", 9))),
        ("::1", (socket.AF_INET6, ("::1", 9, 0, 0))),
        ("2001:db8::7", (socket.AF_INET6, ("2001:db8::7", 9, 0, 0))),
        ("localhost", (socket.AF_INET, ("127.0.0.1", 9))),
        ("LocalHost", (socket.AF_INET, ("127.0.0.1", 9))),
    ],
)
def test_m3_literals_and_localhost_are_answered_at_once_while_the_cap_is_full(
    host: str, first: tuple[int, tuple[Any, ...]], stuck: Any
) -> None:
    """FAILS on r7i (refused with the look-up text: no look-up ran). Kills mutant J04 (the cap checked before the
    literal test)."""
    release, calls = stuck
    _fill_cap(release, calls)
    threads = _lookup_threads()
    start = time.monotonic()
    found = resolve_bounded(host, 9, 5.0)
    assert time.monotonic() - start < 1.0
    assert found[0][0] == first[0] and found[0][4] == first[1] and found[0][1] == socket.SOCK_STREAM
    assert len(calls) == 3 and _lookup_threads() == threads and hung_lookups() == 3  # no look-up, no thread, no count


def test_m3_localhost_gives_the_one_ipv4_loopback_address(stuck: Any) -> None:
    """r7k (review M1): `::1` is no longer invented for localhost; the answer is 127.0.0.1 only."""
    found = resolve_bounded("localhost", 7, 1.0)
    assert [a[4][0] for a in found] == ["127.0.0.1"] and found[0][0] == socket.AF_INET


def test_m3_a_connect_to_a_literal_works_while_the_cap_is_full(stuck: Any) -> None:
    release, calls = stuck
    _fill_cap(release, calls)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    try:
        connect_bounded("127.0.0.1", srv.getsockname()[1], 2.0).close()
    finally:
        srv.close()


@pytest.mark.parametrize(
    "name",
    ["fe80::1%lo", "example.test", "１２７.0.0.1", "local" + "host.example.test"],
)
def test_m3_everything_else_still_needs_a_look_up_and_is_refused_at_the_cap(name: str, stuck: Any) -> None:
    """CONTROL: a zone name, full-width digits and other names go the normal way (and the cap refuses
    them, with the one fixed text). Kills a literal test that is too wide (J04 variant: `host.isascii()` dropped)."""
    release, calls = stuck
    _fill_cap(release, calls)
    with pytest.raises(TimeoutError) as e:
        resolve_bounded(name, 9, 5.0)
    assert str(e.value) == FIXED and len(calls) == 3


# ---- m4: the even share is exactly time left / addresses not yet tried (fake clock, no sleeping) ----


class _Clock:
    now = 1000.0

    @classmethod
    def monotonic(cls) -> float:
        return cls.now


def test_m4_every_address_gets_exactly_the_even_share_of_the_time_left(monkeypatch: pytest.MonkeyPatch) -> None:
    """Four addresses, limit 1.0, a clock that only the fake connects move. A: refused after 0.1 s; B and C: silent (use
    their whole share); D: good. Shares must be 1.0/4 = 0.25 (A), 0.9/3 = 0.3 (B), 0.6/2 = 0.3 (C), and D gets all that
    is left, 0.3. Pins the exact value from both sides: kills mutant O4 (`left / (still + 1)`, which the one-sided r7h
    test accepted) and any `left / still` variant, and (by D) the rule 'the last address gets all that is left'."""
    _Clock.now = 1000.0
    seen: list[tuple[str, float]] = []
    parts = {"a": "192.0.2." + "1", "b": "192.0.2." + "2", "c": "192.0.2." + "3", "d": "192.0.2." + "4"}

    class Fake:
        def __init__(self, *_a: Any) -> None:
            self.t = 0.0

        def settimeout(self, t: float) -> None:
            self.t = t

        def connect(self, address: tuple[str, int]) -> None:
            seen.append((address[0], self.t))
            if address[0] == parts["a"]:
                _Clock.now += 0.1
                raise ConnectionRefusedError("refused")
            if address[0] in (parts["b"], parts["c"]):
                _Clock.now += self.t
                raise TimeoutError("timed out")

        def close(self) -> None:
            pass

    found = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (parts[k], 9)) for k in "abcd"]
    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: found, Fake))
    monkeypatch.setattr(netconnect, "time", types.SimpleNamespace(monotonic=_Clock.monotonic))
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 5.0, raising=False)
    conn = connect_bounded("name.example.test", 9, 1.0)
    assert isinstance(conn, Fake)
    assert [a for a, _ in seen] == [parts[k] for k in "abcd"]
    assert [t for _, t in seen] == pytest.approx([0.25, 0.3, 0.3, 0.3], abs=1e-9)


# ---- m5: the poll helper of the lingerer, both platform branches and the unit of the time-out ----


class _Poller:
    def __init__(self, events: list[tuple[int, int]] | BaseException) -> None:
        self.events, self.registered, self.timeouts = events, [], []

    def register(self, fd: int, mask: int) -> None:
        self.registered.append((fd, mask))

    def poll(self, timeout: float) -> list[tuple[int, int]]:
        self.timeouts.append(timeout)
        if isinstance(self.events, BaseException):
            raise self.events
        return self.events


class _Sock:
    def __init__(self, fd: int) -> None:
        self.fd = fd

    def fileno(self) -> int:
        return self.fd


def _select_with(poller: _Poller) -> types.SimpleNamespace:
    return types.SimpleNamespace(POLLIN=1, poll=lambda: poller)


def test_m5_without_poll_the_helper_waits_the_quiet_time_and_reports_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Windows branch (no `select.poll`), run here with a stand-in that has no `poll`. Kills mutant O9 (that branch
    returns every socket instead of none) and the removal of the wait (a spinning loop)."""
    slept: list[float] = []
    monkeypatch.setattr(server, "select", types.SimpleNamespace())  # no `poll` attribute at all
    monkeypatch.setattr(server, "time", types.SimpleNamespace(sleep=slept.append))
    socks: Any = [_Sock(5), _Sock(6)]
    assert server._poll_readable(socks) == []
    assert slept == [server.QUIET_DRAIN_SECONDS]


def test_m5_the_poll_time_out_is_given_in_milliseconds(monkeypatch: pytest.MonkeyPatch) -> None:
    """`poll` takes milliseconds (`select` takes seconds). Kills mutant O8 (`poll(QUIET_DRAIN_SECONDS)`: 1 ms wake-ups)
    and checks that the sockets with an event come back and the others do not."""
    a, b, c = _Sock(7), _Sock(8), _Sock(9)
    poller = _Poller([(8, 1), (99, 1)])  # fd 99 is not ours: ignored
    monkeypatch.setattr(server, "select", _select_with(poller))
    socks: Any = [a, b, c]
    assert server._poll_readable(socks) == [b]
    assert poller.timeouts == [server.QUIET_DRAIN_SECONDS * 1000]
    assert [fd for fd, _ in poller.registered] == [7, 8, 9]


def test_m5_a_poll_error_waits_and_reports_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr(server, "select", _select_with(_Poller(OSError("bad"))))
    monkeypatch.setattr(server, "time", types.SimpleNamespace(sleep=slept.append))
    socks: Any = [_Sock(5)]
    assert server._poll_readable(socks) == [] and slept == [server.QUIET_DRAIN_SECONDS]


# ---- m6: the real driver run puts the true count into `given_up`; the NOTE prints `intended` ----


def test_m6_a_real_run_where_every_request_is_refused_busy_counts_them_as_given_up(tmp_path: Path) -> None:
    """A stand-in desk that always answers 503 (retried until the retry time is over, 30 s): burst:3, so all three are
    given up with `gave_up: deadline`. Runs the real driver in its own process. Kills mutant O5 (`"given_up": 0`), J08
    (exit 0) and O6 in the real path (the line shows the wrong total). Slow by nature (the retry time is a
    constant of the code)."""
    from test_r7d_findings import _run_driver
    from test_r7g_findings import _Only

    class Busy(_Only):
        STATUS = 503

    srv = Busy()
    try:
        log = tmp_path / "req.jsonl"
        done = _run_driver(
            f"http://127.0.0.1:{srv.port}", "burst:3", log, "--workers", "1", "--threads", "2", timeout=150
        )
    finally:
        srv.close()
    err = done.stderr.decode()
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert [d["gave_up"] for d in lines] == ["deadline"] * 3, [(d["final_status"], d["gave_up"]) for d in lines]
    summary = json.loads(done.stdout.decode())
    assert summary["given_up"] == 3 and summary["intended"] == summary["logged"] == 3 and summary["stopped"] == 0
    assert done.returncode == 3 and err.startswith("ERROR: 3 of 3 requests were not accepted"), (
        done.returncode,
        err[-300:],
    )
    assert err.count("\n") == 1


def _main_summary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **summary: Any) -> tuple[int, str]:
    from load_tools import load_driver

    base = {"unreachable": False, "intended": 7, "logged": 5, "final_status": {}, "given_up": 0, "stopped": 0}
    monkeypatch.setattr(load_driver, "run", lambda *_a, **_k: {**base, **summary})
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        rc = load_driver.main(
            ["--base-url", "http://127.0.0.1:9", "--scenario", "burst:7", "--log", str(tmp_path / "l.jsonl")]
        )
    return rc, err.getvalue()


def test_m6_the_line_shows_the_intended_total_not_the_logged_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The r7h fake had intended == logged == 4, so O6 (`logged`) survived. Here intended 7, logged 5. Kills O6."""
    rc, err = _main_summary(monkeypatch, tmp_path, given_up=2)
    assert rc == 3 and err.startswith("ERROR: 2 of 7 requests were not accepted")


@pytest.mark.parametrize(
    ("given_up", "stopped", "code"),
    [(0, 0, 0), (1, 0, 3), (0, 1, 3), (2, 3, 3), (5, 0, 3)],
)
def test_m7_exit_code_3_whenever_given_up_or_stopped_is_above_zero_and_the_line_has_the_same_count(
    given_up: int, stopped: int, code: int, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lead decision: exit 3 for given-up OR stopped requests; ONE line, same count as the decision. Kills J08 (exit 0
    for given-up requests), J09 (only `given_up` decides), J10 (only `stopped` decides), J11 (count in the line is one
    kind only) and O20 (the stopped run printing no line for the given-up requests: the mixed row names both)."""
    # r7k: the exit-0 row has logged == intended (a run with lines missing prints one WARNING line, see test_k15_*)
    logged = 7 if code == 0 else 5
    rc, err = _main_summary(monkeypatch, tmp_path, given_up=given_up, stopped=stopped, logged=logged)
    assert rc == code
    if code == 0:
        assert err == ""
        return
    assert err.count("\n") == 1 and err.startswith("ERROR: ")
    if given_up:
        n = given_up + stopped
        assert f" {n} of 7 requests were not accepted" in err
        assert f"{given_up} until their retry time was over" in err and f"{stopped} because the run was stopped" in err
    else:
        assert f" {stopped} of 7 requests were never sent or were given up" in err


# ---- n1: one fixed text for every look-up that fails ----


def test_n1_a_look_up_with_no_address_ends_with_the_one_fixed_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7i (a second text, 'no address for the host name'). Kills mutant J05 (the second text back)."""
    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: []))
    with pytest.raises(OSError) as e:
        connect_bounded("name.example.test", 9, 1.0)
    assert str(e.value) == REFUSED and type(e.value) is OSError


# ---- n3: the look-up that ends just after the time-out ----


def test_n3_a_look_up_that_ends_just_after_the_time_out_returns_its_answer_and_counts_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The race branch: the wait says 'time is up' but the thread has already finished. The answer is used, no
    TimeoutError, nothing counted. Kills mutant O1 (`if not state["finished"]:` -> `if True:`: a TimeoutError although
    the answer is there)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    found = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))]

    class LateEvent(_ORIG_EVENT):
        def wait(self, timeout: float | None = None) -> bool:
            super().wait(5)  # the thread ends first ...
            return False  # ... and then the wait reports 'time is up'

    monkeypatch.setattr(netconnect, "socket", _shim(lambda *_a, **_k: found))
    monkeypatch.setattr(
        netconnect, "threading", types.SimpleNamespace(Lock=threading.Lock, Event=LateEvent, Thread=_ORIG_THREAD)
    )
    assert resolve_bounded("late.example.test", 9, 0.01) == found
    assert hung_lookups() == 0


# ---- n2: ASCII only where a value reaches a URL ----


@pytest.fixture
def hubspot_rig(tmp_path: Path):
    from test_crm_hubspot import Rig

    rig = Rig(tmp_path)
    yield rig
    rig.stop()


@pytest.mark.parametrize("bad", ["²", "٣", "１２", "12a", "", "1 2", "-1"])
def test_n2_archive_refuses_a_contact_id_that_is_not_ascii_digits(bad: str, hubspot_rig: Any) -> None:
    """FAILS on r7i for the superscript two (`isdigit()` is True and the text went into the URL path). Kills mutant J06
    (the `isascii()` part removed: the Arabic-Indic three passes `isdecimal()` too)."""
    from lead_desk.crm_hubspot import CrmRefused

    with pytest.raises(CrmRefused):
        hubspot_rig.crm().archive(bad)
    assert not hubspot_rig.state.calls  # nothing was sent


def test_n2_archive_still_accepts_ascii_digits(hubspot_rig: Any) -> None:
    c = hubspot_rig.crm()
    c.put(
        "L-1", {"name": "Ada Example", "email": "Ada@Example.test", "company": "x", "source": "form", "ai_label": "hot"}
    )
    cid = c.rows_with_prefix("L-")[0][1]
    c.archive(cid)  # an ASCII number: goes through


def test_n2_a_returned_email_with_a_non_ascii_letter_is_not_the_same_email(
    hubspot_rig: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAILS on r7i (the Kelvin sign lower-cases to k, so the returned text matched the ASCII email). Kills mutant J07
    (the `isascii()` check on the returned email removed)."""
    from lead_desk import crm_hubspot as mod
    from lead_desk.crm_hubspot import CrmEmailTaken

    c = hubspot_rig.crm()
    kelvin = {"properties": {"hadavin_lead_id": "L-1", "email": KELVIN + "im@example.test"}}
    monkeypatch.setattr(c, "_call", lambda *a, **k: mod._Reply(200, kelvin, None))
    with pytest.raises(CrmEmailTaken):
        c._confirm_existing("L-1", "kim@example.test", {"message": "Existing ID: 7"}, time.monotonic() + 5)
    same = {"properties": {"hadavin_lead_id": "L-1", "email": " KIM@example.test"}}
    monkeypatch.setattr(c, "_call", lambda *a, **k: mod._Reply(200, same, None))
    assert c._confirm_existing("L-1", "kim@example.test", {}, time.monotonic() + 5) == "ALREADY_PRESENT"
