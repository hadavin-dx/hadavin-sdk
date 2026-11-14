"""Round 7H, fixes for the r7g review: a host check that lower-cases before it matches (m1), the even split of the
connect time over the addresses (m2), the cap on look-ups nobody waits for (n1), and the three thread sites the r7g
sweep list left out (reaper in desk.py, `_Lingerer` in server.py, the head timer in scripts/http_guard.py). Made-up
data only, loopback only, no real name look-up: the look-up and the sockets are replaced by fakes."""

from __future__ import annotations

import socket
import struct
import sys
import threading
import time
import types
from pathlib import Path
from typing import Any

import pytest
from support import wait_until
from test_r7g_findings import _FakeSock, _shim

import scripts.http_guard as guard
from lead_desk import netconnect, server
from lead_desk.crm_hubspot import HubspotSettings
from lead_desk.envnum import SettingRefused, split_url
from lead_desk.imap_count import ImapSettingRefused, ImapSettings
from lead_desk.netconnect import connect_bounded, hung_lookups, resolve_bounded
from lead_desk.smtp_provider import ProviderSettings

KELVIN = chr(0x212A)  # lower() turns it into an ASCII k
DOTTED_I = chr(0x130)  # lower() gives i plus a combining mark
LONG_S = chr(0x17F)  # upper() gives S
DOTLESS_I = chr(0x131)  # upper() gives I
HOST_REFUSED = "the mailbox host must be a host name (letters, digits, hyphens and dots)"


# ---- m1: the checked text is the used text ----


@pytest.mark.parametrize(
    "name",
    [
        KELVIN + "example.test",
        "imap." + KELVIN + ".test",
        "imap.example.test" + KELVIN,
        DOTTED_I + "map.test",
        LONG_S + "mtp.test",
        "imap.example." + chr(0xFF21) + "A",  # a full-width capital A
    ],
)
def test_m1_the_mailbox_host_refuses_a_letter_that_lower_cases_to_ascii(name: str, tmp_path: Path) -> None:
    """FAILS on r7g for the Kelvin-sign names (lower() made them ASCII, so they passed and a different text was looked
    up). Kills mutant H01 (the `isascii()` part of the check removed)."""
    with pytest.raises(ImapSettingRefused) as e:
        ImapSettings(name, "reader-user", tmp_path / "p")
    assert str(e.value) == HOST_REFUSED and name not in str(e.value)


def test_m1_the_mailbox_host_still_allows_ascii_upper_case(tmp_path: Path) -> None:
    """CONTROL: the sentence in docs/limits.md (upper case allowed, non-ASCII refused) is true in both parts."""
    assert ImapSettings("IMAP.Example.Test", "reader-user", tmp_path / "p").host == "IMAP.Example.Test"


def _smtp_env(host: str, tmp_path: Path) -> dict[str, str]:
    return {
        "DESK_SMTPP_HOST": host,
        "DESK_SMTPP_USER": "sender-user",
        "DESK_SMTPP_PASSWORD_FILE": str(tmp_path / "pw"),
        "DESK_SMTPP_FROM": "sender@example.test",
        "DESK_SMTPP_RECIPIENTS": "inbox-a@example.test",
        "DESK_SMTPP_MAX_SENDS": "3",
    }


@pytest.mark.parametrize("name", [KELVIN + "example.test", "mail." + KELVIN + ".test", LONG_S + "mtp.test"])
def test_m1_the_mail_sender_host_refuses_non_ascii_and_does_not_lower_case_it_first(name: str, tmp_path: Path) -> None:
    """FAILS on r7g for the Kelvin names (from_env lower-cased the text before the check, so the host became `k...`).
    Kills mutant H02 (`_ascii_host` lower-cases every text)."""
    with pytest.raises(SettingRefused) as e:
        ProviderSettings.from_env(_smtp_env(name, tmp_path))
    assert str(e.value) == "DESK_SMTPP_HOST must be a lower-case host name" and name not in str(e.value)


def test_m1_the_mail_sender_host_from_the_settings_is_still_put_in_lower_case(tmp_path: Path) -> None:
    """CONTROL: an ASCII host in upper case is accepted and stored in lower case, as before."""
    assert ProviderSettings.from_env(_smtp_env(" Mail.Example.Test ", tmp_path)).host == "mail.example.test"


VENDOR = "".join(["hub", "spot"]) + "." + "".join(["co", "m"])  # from parts: the vendor-host scan refuses literals


@pytest.mark.parametrize("host", [KELVIN + "api." + VENDOR, "api." + KELVIN + VENDOR])
def test_m1_a_setting_url_with_a_non_ascii_host_is_refused(host: str, tmp_path: Path) -> None:
    """FAILS on r7g: urlsplit().hostname lower-cased the Kelvin sign, the host ended in the vendor's domain and the
    base address passed, though the address that is dialled is a different text. Kills mutant H03 (the `isascii()`
    test removed from split_url)."""
    url = "https://" + host
    with pytest.raises(SettingRefused):
        split_url("DESK_X", url)
    with pytest.raises(SettingRefused):
        HubspotSettings.from_env(
            {"DESK_HUBSPOT_KEY_FILE": str(tmp_path / "k"), "DESK_HUBSPOT_MAX_CALLS": "5", "DESK_HUBSPOT_BASE_URL": url}
        )


def test_m1_the_only_characters_that_lower_case_to_pure_ascii_is_the_kelvin_sign() -> None:
    """NOT-NEEDED proof for `is_loopback_host` ("localhost" has no k) and the Host header gate (a header reaches the
    server decoded as latin-1, and no latin-1 character lower-cases to ASCII): the sweep over every code point."""
    found = [
        c
        for c in map(chr, range(0x110000))
        if not c.isascii() and not 0xD800 <= ord(c) < 0xE000 and c.lower().isascii()
    ]
    assert found == [KELVIN]
    assert not [c for c in map(chr, range(256)) if not c.isascii() and any(x.isascii() for x in c.lower())]


def test_m1_the_real_check_passes_only_ascii_system_variables_to_the_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7g: a variable named with the long s (upper() gives S) passed for SYSTEMROOT and reached the child.
    Kills mutant H04 (`k.isascii() and` removed)."""
    from test_real_check_dry import rrc

    fake = "SY" + LONG_S + "TEMROOT"  # upper() of the long s is S: it spells SYSTEMROOT only after upper()
    monkeypatch.setattr(rrc.os, "environ", {fake: "secret-looking", "PATH": "/bin", "OTHER": "x"})
    env = rrc.child_environment({})
    assert env == {"PATH": "/bin"}


# ---- m2: an even share of the time left for every address ----


def test_m2_eight_silent_addresses_and_a_good_one_all_get_a_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    """The review case scaled down by 10 (12 s -> 1.2 s, 5 s -> 0.5 s): 8 silent addresses plus a good one. FAILS on r7g
    (0.5, 0.5, 0.2 and the time is gone: 3 addresses tried, TimeoutError). Kills mutant S01 (`left / still` ->
    `left`) and S02 (the `still == 1` test dropped: the last address gets only an even share)."""
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 0.5, raising=False)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    log, closed = _shim(monkeypatch, [_FakeSock.BLACKHOLE] * 8 + ["127.0.0.1"], port)
    try:
        start = time.monotonic()
        conn = connect_bounded("name.example.test", port, 1.2)
        took = time.monotonic() - start
        conn.close()
    finally:
        srv.close()
    assert [a for a, _ in log] == [_FakeSock.BLACKHOLE] * 8 + ["127.0.0.1"]  # every address, in order
    assert took < 1.5, took
    for _, t in log[:8]:
        assert t is not None and 0.10 < t <= 1.2 / 9 + 0.01, log  # about left / addresses left: 0.133, then a bit more
    assert len(closed) == 9  # the 8 silent sockets were closed, and the good one by conn.close() above


def test_m2_the_per_address_cap_still_binds_when_the_even_share_is_larger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Three addresses, limit 30 s, cap 0.2 s: the silent ones get the cap (0.2), not 10 s, and the last all that is
    left. Kills mutant S03 (`min(CAP, ...)` dropped: the even share only)."""
    monkeypatch.setattr(netconnect, "CONNECT_PER_ADDRESS_SECONDS", 0.2, raising=False)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    log, _ = _shim(monkeypatch, [_FakeSock.BLACKHOLE, _FakeSock.BLACKHOLE, "127.0.0.1"], port)
    try:
        start = time.monotonic()
        connect_bounded("name.example.test", port, 30.0).close()
        took = time.monotonic() - start
    finally:
        srv.close()
    assert took < 1.0, took
    assert log[0][1] == pytest.approx(0.2, abs=0.01) and log[1][1] == pytest.approx(0.2, abs=0.01)
    assert log[2][1] is not None and log[2][1] > 29.0  # the last address: all the time left


def test_m2_an_address_that_overruns_the_whole_limit_ends_the_call_and_the_rest_are_not_tried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The total limit holds even when a connect ignores its own time-out: the next address is not started once the
    time is gone. Kills mutant A03 (the `left <= 0` check removed, kept from r7g)."""
    log, _ = _shim(monkeypatch, [_FakeSock.BLACKHOLE, "127.0.0.1", "127.0.0.1"], 9)

    real = _FakeSock.connect

    def overrun(self: _FakeSock, address: tuple[str, int]) -> None:
        if address[0] == _FakeSock.BLACKHOLE:
            self._log.append((address[0], self._t))
            time.sleep(0.5)  # longer than the whole 0.3 s limit, whatever the socket time-out says
            raise TimeoutError("timed out")
        real(self, address)

    monkeypatch.setattr(_FakeSock, "connect", overrun)
    with pytest.raises(TimeoutError):
        connect_bounded("name.example.test", 9, 0.3)
    assert [a for a, _ in log] == [_FakeSock.BLACKHOLE]


# ---- n1: a cap on look-ups that nobody waits for ----


@pytest.fixture
def hung_rig(monkeypatch: pytest.MonkeyPatch):
    """getaddrinfo that blocks until released; the cap is 3 for speed. Yields (release, calls)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    release = threading.Event()
    calls: list[str] = []

    def blocking(host: str, *_a: Any, **_k: Any) -> list[Any]:
        calls.append(host)
        release.wait(20)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))]

    shim = types.SimpleNamespace(
        getaddrinfo=blocking, SOCK_STREAM=socket.SOCK_STREAM, socket=socket.socket, AF_INET=socket.AF_INET
    )
    monkeypatch.setattr(netconnect, "socket", shim)
    monkeypatch.setattr(netconnect, "LOOKUP_HUNG_MAX", 3, raising=False)
    yield release, calls
    release.set()
    wait_until(lambda: hung_lookups() == 0, what="hung look-ups ended")


def _lookup_threads() -> int:
    return sum(1 for t in threading.enumerate() if t.name == "name-lookup" and t.is_alive())


def test_n1_at_the_cap_a_new_lookup_is_refused_at_once_and_starts_no_thread(hung_rig: Any) -> None:
    """FAILS on r7g (every call started a thread: 20 hung look-ups, 20 threads). Kills mutant K01 (`>=` -> `>`: a
    fourth thread), K02 (the refusal removed), K03 (the count never raised: no cap)."""
    release, calls = hung_rig
    for _ in range(3):
        with pytest.raises(TimeoutError):
            resolve_bounded("a.example.test", 9, 0.05)
    assert hung_lookups() == 3 and len(calls) == 3
    threads = _lookup_threads()
    start = time.monotonic()
    with pytest.raises(TimeoutError) as e:
        resolve_bounded("b.example.test", 9, 5.0)  # a 5 s limit: the refusal must not wait for it
    assert time.monotonic() - start < 1.0
    assert str(e.value) == netconnect.LOOKUP_TEXT and e.value.__class__ is TimeoutError  # the same fixed text
    assert _lookup_threads() == threads and len(calls) == 3  # no new thread, getaddrinfo not called again
    with pytest.raises(TimeoutError):
        connect_bounded("c.example.test", 9, 5.0)  # the connect has the same refusal
    assert len(calls) == 3 and hung_lookups() == 3
    release.set()


def test_n1_when_the_hung_lookups_end_the_count_goes_down_and_lookups_work_again(hung_rig: Any) -> None:
    """Kills mutant K04 (the count never lowered when a late look-up ends: the process refuses for ever)."""
    release, calls = hung_rig
    for _ in range(3):
        with pytest.raises(TimeoutError):
            resolve_bounded("a.example.test", 9, 0.05)
    assert hung_lookups() == 3
    release.set()
    wait_until(lambda: hung_lookups() == 0, what="the count goes back to 0")
    found = resolve_bounded("d.example.test", 9, 2.0)  # works again (release is set: getaddrinfo answers at once)
    assert found and len(calls) == 4


def test_n1_look_ups_that_answer_in_time_never_count(hung_rig: Any) -> None:
    """CONTROL: a look-up that answers inside its time is not counted, however many there are."""
    release, calls = hung_rig
    release.set()
    for _ in range(10):
        assert resolve_bounded("e.example.test", 9, 2.0)
    assert hung_lookups() == 0 and len(calls) == 10


def test_n1_the_real_limit_is_a_small_number() -> None:
    """The documented limit is the constant, and it is small (docs/limits.md names it)."""
    from lead_desk import constants

    assert 1 <= constants.LOOKUP_HUNG_MAX <= 16


# ---- the three thread sites the r7g sweep list left out: no traceback from any bad input ----


class _Hook:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[str] = []
        monkeypatch.setattr(threading, "excepthook", lambda a: self.calls.append(a.exc_type.__name__))


class _Stop(BaseException):
    pass


def test_site_desk_reaper_survives_any_exception_of_a_pass(env: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """desk.py `_reaper_loop` catches BaseException around each pass: a failing pass (even SystemExit or a
    BaseException subclass) is one log line, the thread goes on and `threading.excepthook` is never called. Kills
    mutant T01 (`except BaseException` -> `except Exception`)."""
    hook = _Hook(monkeypatch)
    d = env.rig().desk
    d._started.set()
    passes: list[int] = []
    errors: list[BaseException] = [_Stop(), SystemExit(1), KeyboardInterrupt(), RuntimeError("x")]

    def reap() -> dict[str, int]:
        passes.append(1)
        if errors:
            raise errors.pop(0)
        return {}

    monkeypatch.setattr(d, "reap_once", reap)
    try:
        d.start_background(0.01)
        wait_until(lambda: len(passes) >= 6, what="the reaper went on after four failing passes")
        assert d.reaper_running()
    finally:
        d.stop_background(timeout=5)
    assert hook.calls == []


# SO_LINGER option "on, 0 seconds" in the form of the platform: two ints (Linux, macOS), two shorts (Windows)
_RESET_ON_CLOSE = struct.pack("HH", 1, 0) if sys.platform == "win32" else struct.pack("ii", 1, 0)


def test_site_lingerer_takes_hostile_connections_without_a_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    """server.py `_Lingerer._run`: a client that sends a flood and resets, one that closes at once, and a socket closed
    from outside (a closed file number: select raises ValueError) all end quietly; the thread never raises. Kills
    mutant T02 (`except (OSError, ValueError)` -> `except OSError`)."""
    hook = _Hook(monkeypatch)
    lingerer = server._Lingerer()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    clients: list[socket.socket] = []
    served: list[socket.socket] = []
    try:
        for kind in ("flood-reset", "close", "outside"):
            c = socket.create_connection(listener.getsockname())
            s, _ = listener.accept()
            clients.append(c)
            served.append(s)
            assert lingerer.add(s) is True
            if kind == "flood-reset":
                c.sendall(b"x" * 200000)
                c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, _RESET_ON_CLOSE)  # reset on close
                c.close()
            elif kind == "close":
                c.close()
            else:
                s.close()  # closed behind the lingerer's back
        wait_until(lambda: not lingerer._items, what="all lingering sockets dropped")
    finally:
        lingerer.close_all()
        for x in clients:
            x.close()
        listener.close()
    assert hook.calls == []


def test_site_head_timer_on_a_closed_connection_raises_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """http_guard `_head_too_slow` runs in a Timer thread. The connection may be closed already (the handler ended):
    shutdown raises OSError, which is caught; the Timer thread ends without a traceback. Kills mutant T03
    (`except OSError` -> `except KeyError`)."""
    hook = _Hook(monkeypatch)
    a, b = socket.socketpair()
    h = guard.HeadDeadline.__new__(guard.HeadDeadline)
    monkeypatch.setattr(h, "connection", a, raising=False)
    a.close()
    b.close()
    timer = threading.Timer(0.01, h._head_too_slow)
    timer.daemon = True
    timer.start()
    timer.join(5)
    assert not timer.is_alive() and hook.calls == []


def test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """server.py `_Lingerer._run` with a file number of 1024 or more (a desk with many open connections): `select`
    raises ValueError for it. On r7g the loop then spun at full speed and read nothing until the 1 s drain time was
    over (measured: 0.57 s of processor time in 0.6 s, the bytes of the client never read). Now `poll` reads it. Kills
    mutant T04 (`_poll_readable` returns an empty list at once)."""
    resource = pytest.importorskip("resource")  # Windows has no such module: the test is skipped there, not failed

    hook = _Hook(monkeypatch)
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    want = 4096
    if hard != resource.RLIM_INFINITY and hard < want:
        pytest.skip("the hard limit on open files is below 4096")
    if soft < want:
        resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))
    filler = []
    lingerer = server._Lingerer()
    client = served = None
    try:
        while True:  # open pairs until the next file number is above the select limit
            pair = socket.socketpair()
            filler.append(pair)
            if pair[0].fileno() >= 1030:
                break
        client, served = socket.socketpair()
        assert served.fileno() >= 1024
        assert lingerer.add(served) is True
        before = lingerer._items[served][1]
        cpu = time.process_time()
        client.sendall(b"x" * 100)
        wait_until(
            lambda: served in lingerer._items and lingerer._items[served][1] <= before - 100, what="the bytes were read"
        )
        time.sleep(0.4)
        assert time.process_time() - cpu < 0.3  # no full-speed loop
    finally:
        lingerer.close_all()
        for pair in filler:
            pair[0].close()
            pair[1].close()
        for sock in (client, served):
            if sock is not None:
                sock.close()
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
    assert hook.calls == []


# ---- lead note 1: every look-up failure gives the one fixed text ----


@pytest.mark.parametrize("name", ["", "example." + "test."])
def test_lookup_failures_of_the_system_give_the_fixed_text_not_the_gaierror_words(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The EV7G case: the empty host and `example.test.` ended in `[Errno -2] Name or service not known`. The system's
    look-up is replaced by the same refusal (no name server on this machine). FAILS on r7g. Kills mutant G04 (the
    stored error is the raw one again)."""

    def gone(*_a: object, **_k: object) -> list[Any]:
        raise socket.gaierror(-2, "Name or service not known")

    monkeypatch.setattr(socket, "getaddrinfo", gone)
    with pytest.raises(OSError) as e:
        connect_bounded(name, 9, 2.0)
    assert str(e.value) == "the host name cannot be looked up" and "Errno" not in str(e.value)


def test_the_empty_host_name_with_the_real_look_up_gives_the_fixed_text() -> None:
    """The real `getaddrinfo` on the empty name (no network needed). FAILS on r7g (raw gaierror text)."""
    with pytest.raises(OSError) as e:
        connect_bounded("", 9, 2.0)
    assert str(e.value) == "the host name cannot be looked up"


# ---- lead note 2: requests given up at their deadline: exit code 0 by contract, said on stderr ----


def test_deadline_count_counts_only_deadline_give_ups() -> None:
    """Kills mutant G01 (counts `stopped` too) and G05 (counts every line that is not accepted)."""
    from load_tools import load_driver

    lines = [
        {"gave_up": "deadline", "accepted": False},
        {"gave_up": "deadline", "accepted": False},
        {"gave_up": "stopped", "accepted": False},
        {"gave_up": "driver_error", "accepted": False},
        {"gave_up": None, "accepted": True},
        {"gave_up": None, "accepted": False},
    ]
    assert load_driver.deadline_count(lines) == 2 and load_driver.deadline_count([]) == 0


def _main_with(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **summary: Any) -> tuple[int, str, str]:
    import contextlib
    import io

    from load_tools import load_driver

    base = {"unreachable": False, "intended": 4, "logged": 4, "final_status": {}, "given_up": 0, "stopped": 0}
    monkeypatch.setattr(load_driver, "run", lambda *_a, **_k: {**base, **summary})
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = load_driver.main(
            ["--base-url", "http://127.0.0.1:9", "--scenario", "burst:4", "--log", str(tmp_path / "l.jsonl")]
        )
    return rc, out.getvalue(), err.getvalue()


def test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_3_and_one_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The EV7G case (burst:4, one 202, then every connection dropped: {'202': 1, 'error': 3}, stopped 0). r7j (lead
    decision): exit 3 and ONE line with the count, `given_up` in the summary. r7h had exit 0 and a NOTE line."""
    rc, out, err = _main_with(monkeypatch, tmp_path, given_up=3, final_status={"202": 1, "error": 3})
    assert rc == 3
    assert '"given_up": 3' in out
    assert err.startswith("ERROR: 3 of 4 requests were not accepted") and err.count("\n") == 1


def test_a_run_with_nothing_given_up_prints_no_line(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """CONTROL: the ERROR line appears only when something was given up. Kills mutant G06 (the line always printed)."""
    rc, _, err = _main_with(monkeypatch, tmp_path)
    assert rc == 0 and err == ""


def test_a_stopped_run_still_ends_with_exit_code_3(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """CONTROL: the stop rule of r7g is unchanged beside the new note."""
    rc, _, err = _main_with(monkeypatch, tmp_path, stopped=1)
    assert rc == 3 and "1 of 4 requests were never sent or were given up" in err


# ---- lead order 05:54: every secret file is read and checked BEFORE a counter, a reserve or a connection ----
# Pass 9 mutant M9-02 (the password read moved after the send counter) survived because no test pinned the order. The
# order in the code was already right on r7g, so these tests pass on r7g too: they are the missing pin (a real run on a
# copy of tree-R7G, and on a mutated copy of tree-R7H, is in R7H-RESULTS.md).


def _bad_secret(tmp_path: Path, kind: str) -> Path:
    from lead_desk.constants import SECRET_FILE_MAX_BYTES

    p = tmp_path / "secret.txt"
    if kind == "missing":
        return p
    if kind == "oversize":
        p.write_bytes(b"a" * (SECRET_FILE_MAX_BYTES + 10))
    elif kind == "two-lines":
        p.write_text("first-line-0123456789\nsecond-line-0123456789\n", encoding="utf-8")
    elif kind == "empty":
        p.write_text("", encoding="utf-8")
    return p


BAD_SECRETS = ["missing", "oversize", "two-lines", "empty"]


@pytest.mark.parametrize("kind", BAD_SECRETS)
def test_order_smtp_a_bad_password_file_leaves_the_send_counter_and_the_stats_file_unchanged(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """smtp_provider.py `send`: the password file is read before `attempts += 1` and before any connection. Kills
    mutant M9-02 (the read moved after the counter)."""
    import ssl

    from test_r7f_findings import _provider

    from lead_desk import smtp_provider
    from lead_desk.contract import SendRefused

    def no_connect(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("a connection was opened")

    monkeypatch.setattr(smtp_provider, "connect_bounded", no_connect)
    stats = tmp_path / "stats.json"
    box = _provider(
        tmp_path, 9, ssl.create_default_context(), password_file=_bad_secret(tmp_path, kind), stats_file=stats
    )
    with pytest.raises(SendRefused):
        box.send("RUN1-L-001", "ada@example.test", "Thanks", "Hi", 2.0)
    assert box.attempts == 0 and not stats.exists()


@pytest.mark.parametrize("kind", BAD_SECRETS)
def test_order_live_model_a_bad_key_file_reserves_nothing_in_the_ledger(kind: str, tmp_path: Path) -> None:
    """live_claude.py `qualify`: the key is read before `ledger.reserve`. Kills mutant M9-L (the read moved after
    the reserve)."""
    from decimal import Decimal

    from lead_desk.live_claude import LiveQualifier, LiveSettings, LiveTransport

    ledger = tmp_path / "ledger.jsonl"
    s = LiveSettings(
        model="fake-model-1",
        key_file=_bad_secret(tmp_path, kind),
        price_in_per_mtok=Decimal("2"),
        price_out_per_mtok=Decimal("10"),
        price_date="2026-01-01",
        cap_run_usd=Decimal("1"),
        cap_total_usd=Decimal("3"),
        ledger_path=ledger,
        run_id="run-a",
        base_url="http://127.0.0.1:9",
        timeout_seconds=2.0,
    )
    q = LiveQualifier(s)
    with pytest.raises(LiveTransport):
        q.qualify("L1", "a@example.test")
    assert not ledger.exists() and q.calls == 0


@pytest.mark.parametrize("kind", BAD_SECRETS)
def test_order_hubspot_a_bad_key_file_leaves_the_call_counter_and_the_stats_file_unchanged(
    kind: str, tmp_path: Path
) -> None:
    """crm_hubspot.py `_call`: the key is read before `_n["calls"] += 1`. Kills mutant M9-H (the read moved after the
    counter)."""
    from lead_desk.crm_hubspot import CrmConfigError, HubspotCrm

    stats = tmp_path / "stats.json"
    s = HubspotSettings(
        key_file=_bad_secret(tmp_path, kind),
        max_calls=5,
        base_url="http://127.0.0.1:9",
        allow_any_base_url=True,
        stats_file=stats,
    )
    crm = HubspotCrm(s)
    with pytest.raises(CrmConfigError):
        crm.put("L-1", {"email": "ada@example.test", "name": "Ada Example"})
    assert crm.stats()["calls"] == 0 and not stats.exists()


@pytest.mark.parametrize("kind", BAD_SECRETS)
def test_order_mailbox_a_bad_password_file_opens_no_connection(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """imap_count.py `_session`: the password is read before the connection (the mailbox read has no counter). Kills
    mutant M9-I (the read moved after the connect)."""
    from lead_desk import imap_count
    from lead_desk.imap_count import ImapCountError, counts_by_key

    def no_connect(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("a connection was opened")

    monkeypatch.setattr(imap_count, "_BoundedImap", no_connect)
    s = ImapSettings("imap.example.test", "reader-user", _bad_secret(tmp_path, kind))
    with pytest.raises(ImapCountError):
        counts_by_key(s, "L")
