"""Round 7L: tests for the survivors of the r7i review (a mutant is a one-line change to the code; "survived" means the
whole test set stayed green, so the behaviour it changed was not checked). Made-up data only, loopback only; sockets
are fakes that record the time limit and the bytes they are given, or small real loopback pairs.

Header table (finding | mutant | what the test pins | why it matters). Every row is a PIN unless it says NEW CODE:
the code was already right, the test was missing; the proof is that each test FAILS on its mutant (R7L-RESULTS.md).
  F1  | X05 + sibling P-X05 | the reply to the message text must be 2xx: a 3xx (354, 334, 300), 1xx, 4xx or 5xx is
        "maybe sent" (SendAmbiguous "final reply N"), never SENT; outbox AND provider
        | a 354 after the text means the server is still waiting; reporting SENT would hide a lost mail
  F2  | X17 | the provider's stats file says attempts 1 BEFORE the connection is opened
        | a crash in the middle of a send must not lose the cap count on disk
  F3  | Y1, Y2, X14, X01/Y4, X02, X13 | every step (connect, handshake, reply read, every command, the text, QUIT)
        is given the time LEFT of the send budget; the tests use a budget of 0.5 s under an own limit of 2 s and
        sockets that start with an old 10 s limit, so "own full limit" and "older limit" both fail
        | a step that gets a longer limit than the time left can stretch a send past its budget
  F4  | V01, V02, V05, V06 (+ V03 is EQUIVALENT, pinned) | server.py: a client that never reads or never speaks cannot
        hold the accept loop (busy reply write and drain), the reply body write gets the time left, the finish drain
        waits only the quiet time
        | one blocked write or read on the accept loop stops the whole desk
  F4b | S2, S3, S4, S11, S12 | server.py: the reader sets the time left and restores the idle limit; the lingerer drops
        a silent connection at the time limit and one past the byte limit (desk socket stays non-blocking)
        | a slow client must not hold a connection or stretch the limit
  F4c | V03, S13 are EQUIVALENT (not killable) | _drain's own settimeout and total-limit check repeat what
        _DeadlineReader.readinto already arms at the top of _drain; a control pin covers the shared behaviour
        | stated here so nobody mistakes the survivors for a gap
  F5  | X03 | the HELO fallback fires only on a 5xx EHLO reply (outbox and provider) | 4xx means "try later"
  F7  | X20 | provider: the EHLO reply is checked BEFORE STARTTLS | no STARTTLS to a server that refused EHLO
  F8  | X21 | each word of WEAK_CIPHER_WORDS makes require_verifying refuse | one word removed = a weak cipher passes
  F9  | X27 | imap handshake: limit is min(step, time left) | step limit must hold inside a big total
  F10 | Y3 sibling | login accepted on exactly 235; 3xx and 4xx/5xx refused too (r7i i3 only tried 2xx)
  F13 | provider empty key | the refusal text is the key-pattern text, and an empty key never reaches the network
  G1  | X28 | imap: an OSError during the login line is never repeated (ImapCountError, not ImapConnectionError)
        | a repeat would be a second login attempt
  G2  | X30 | imap: a handshake that timed out at the TOTAL limit is ImapTotalTimeout, at the step limit TimeoutError
  G3  | X29 | imap send: the step limit caps each write
  G4  | guard | the secret readers: four adapters read a secret, each has an order test; a fifth fails this test
        | the reviewer's guard: a new adapter must not read a secret without the order test"""

from __future__ import annotations

import imaplib
import io
import json
import re
import socket
import ssl
import threading
import time
import types
from pathlib import Path
from typing import Any

import pytest
from test_r7f_findings import _Certs, _provider
from test_smtp_outbox import SUBJECT, TO

from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp
from lead_desk import imap_count, server, smtp_outbox, smtp_provider
from lead_desk.contract import SendAmbiguous, SendRefused, SendUnreachable
from lead_desk.smtp_outbox import SmtpOutbox, SmtpSettings, _Budget, _read_reply
from lead_desk.tls_trust import WEAK_CIPHER_WORDS, CaFileRefused, new_verifying_context, require_verifying

LOOP = "127.0.0." + "1"
WIRE = b"Subject: x\r\n\r\nhi\r\n.\r\n"
OLD_LIMIT = 10.0  # a socket starts with this limit: a step that forgets to set the time left would run with it


class _Rec:
    """A fake socket. Each recv answers with the next scripted reply (an empty script is a closed connection) and
    each call records (what, bytes, the limit the socket had at that moment)."""

    def __init__(self, replies: list[bytes], first: float | None = OLD_LIMIT) -> None:
        self.t = first
        self.replies = list(replies)
        self.log: list[tuple[str, bytes, float | None]] = []

    def settimeout(self, t: float | None) -> None:
        self.t = t

    def gettimeout(self) -> float | None:
        return self.t

    def sendall(self, data: bytes) -> None:
        self.log.append(("send", data, self.t))

    def recv(self, _n: int) -> bytes:
        self.log.append(("recv", b"", self.t))
        return self.replies.pop(0) if self.replies else b""

    def version(self) -> str:
        return "TLSv1.3"

    def close(self) -> None:
        pass

    def sent(self) -> list[bytes]:
        return [d for w, d, _ in self.log if w == "send"]


OUTBOX_OK = [b"220 ok\r\n", b"250 ok\r\n", b"250 ok\r\n", b"250 ok\r\n", b"354 go\r\n"]
SSL_OK = [b"220 ok\r\n", b"250 ok\r\n", b"235 ok\r\n", b"250 ok\r\n", b"250 ok\r\n", b"354 go\r\n"]
STARTTLS_OK = [
    b"220 ok\r\n",
    b"250 ok\r\n",
    b"220 go\r\n",
    b"250 ok\r\n",
    b"235 ok\r\n",
    b"250 ok\r\n",
    b"250 ok\r\n",
    b"354 go\r\n",
]


def _outbox(limit: float = 2.0) -> SmtpOutbox:
    return SmtpOutbox(SmtpSettings(host=LOOP, port=9, timeout_seconds=limit))


def _prov_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sock: Any, security: str, limit: float = 2.0
) -> smtp_provider.SmtpProviderOutbox:
    """A provider whose TLS wrap hands back `sock` (which answers like a TLS socket)."""
    ctx = ssl.create_default_context()
    monkeypatch.setattr(ctx, "wrap_socket", lambda s, server_hostname=None: sock)
    return _provider(tmp_path, 9, ctx, security=security, timeout_seconds=limit)


def _run_outbox(final: bytes | None, budget: float = 2.0, replies: list[bytes] | None = None) -> _Rec:
    sock = _Rec((replies if replies is not None else OUTBOX_OK) + ([final] if final is not None else []))
    _outbox()._dialogue(sock, _Budget(budget), TO, WIRE)
    return sock


def _run_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    security: str,
    final: bytes | None,
    budget: float = 2.0,
    replies: list[bytes] | None = None,
) -> _Rec:
    base = replies if replies is not None else (SSL_OK if security == "ssl" else STARTTLS_OK)
    sock = _Rec(base + ([final] if final is not None else []))
    box = _prov_on(tmp_path, monkeypatch, sock, security)
    box._dialogue(sock, _Budget(budget), FAKE_PASSWORD, "inbox-a@example.test", WIRE)
    return sock


# ---- F1: the reply to the message text must be a 2xx ----


@pytest.mark.parametrize("code", [354, 334, 300, 399, 100, 199, 421, 450, 550, 554])
def test_l1_outbox_a_final_reply_that_is_not_2xx_is_maybe_sent_never_sent(code: int) -> None:
    """Kills X05 (outbox: `code // 100 not in (2, 3)`: a 354 or 334 after the text counted as queued)."""
    with pytest.raises(SendAmbiguous) as e:
        _run_outbox(f"{code} text\r\n".encode())
    assert str(e.value) == f"final reply {code}"


@pytest.mark.parametrize("security", ["ssl", "starttls"])
@pytest.mark.parametrize("code", [354, 334, 300, 399, 100, 199, 421, 450, 550, 554])
def test_l1_provider_a_final_reply_that_is_not_2xx_is_maybe_sent_never_sent(
    code: int, security: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills the provider sibling of X05 (`code // 100 not in (2, 3)` at the end of smtp_provider._dialogue)."""
    with pytest.raises(SendAmbiguous) as e:
        _run_provider(tmp_path, monkeypatch, security, f"{code} text\r\n".encode())
    assert str(e.value) == f"final reply {code}"


@pytest.mark.parametrize("code", [200, 250, 299])
def test_l1_control_a_2xx_final_reply_is_sent_and_quit_follows(
    code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL (passes on every mutant): 2xx is the one good answer; the desk then says QUIT."""
    s1 = _run_outbox(f"{code} queued\r\n".encode())
    s2 = _run_provider(tmp_path, monkeypatch, "ssl", f"{code} queued\r\n".encode())
    assert s1.sent()[-1] == b"QUIT\r\n" and s2.sent()[-1] == b"QUIT\r\n"


# ---- F2: the stats file says attempts 1 before the connection is opened ----


def test_l2_the_stats_file_holds_the_attempt_before_the_connection_is_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X17 (the write_stats right after `attempts += 1` removed: a crash in the middle of the send would lose
    the cap count on disk, the later write after a success hides it). The fake connect reads the file."""
    stats = tmp_path / "stats.json"
    box = _provider(tmp_path, 9, ssl.create_default_context(), stats_file=stats)
    seen: list[dict[str, int]] = []

    def connect(_budget: Any) -> Any:
        seen.append(json.loads(stats.read_text(encoding="utf-8")))
        raise SendUnreachable("stop here: the file was read")

    monkeypatch.setattr(box, "_connect", connect)
    for _ in range(2):
        with pytest.raises(SendUnreachable):
            box.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0)
    assert seen == [{"attempts": 1, "sent": 0}, {"attempts": 2, "sent": 0}]


# ---- F3: every step is given the time LEFT (budget 0.5 s under an own limit of 2 s, old socket limit 10 s) ----


def _within(t: float | None, cap: float) -> bool:
    return t is not None and 0 < t <= cap


def test_l3_the_provider_handshake_gets_the_time_left_not_its_own_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills Y1 (`sock.settimeout(self._s.timeout_seconds)` before wrap_socket: the provider's own 2 s instead of the
    0.5 s that are left)."""
    ctx = ssl.create_default_context()
    seen: list[float | None] = []

    def wrap(sock: Any, server_hostname: str | None = None) -> Any:
        seen.append(sock.gettimeout())
        raise ssl.SSLError("stop here")

    monkeypatch.setattr(ctx, "wrap_socket", wrap)
    box = _provider(tmp_path, 9, ctx, timeout_seconds=2.0)
    with pytest.raises(ssl.SSLError):
        box._wrap(_Rec([]), _Budget(0.5))
    assert len(seen) == 1 and _within(seen[0], 0.5)


def test_l3_the_outbox_connect_gets_the_time_left_not_its_own_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills Y2 (`sock.settimeout(self._s.timeout_seconds)` before connect: the own 2 s, not the 0.5 s left)."""
    made: list[Any] = []

    class _Conn(_Rec):
        def connect(self, _address: Any) -> None:
            self.log.append(("connect", b"", self.t))
            raise ConnectionRefusedError("refused")

    def make(_family: int, _kind: int) -> Any:
        made.append(_Conn([], first=None))
        return made[-1]

    shim = types.SimpleNamespace(
        socket=make, AF_INET=socket.AF_INET, AF_INET6=socket.AF_INET6, SOCK_STREAM=socket.SOCK_STREAM
    )
    monkeypatch.setattr(smtp_outbox, "socket", shim)
    with pytest.raises(SendUnreachable):
        _outbox(2.0).send("K-3", TO, SUBJECT, "Hi", 0.5)
    ((what, _, limit),) = made[0].log
    assert what == "connect" and _within(limit, 0.5)


def test_l3_the_provider_connect_gets_the_time_left_not_its_own_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X14 (`connect_bounded(..., self._s.timeout_seconds)`: the provider's own 2 s for the connect)."""
    asked: list[float] = []

    def connect_bounded(_host: str, _port: int, seconds: float) -> Any:
        asked.append(seconds)
        raise OSError("refused")

    monkeypatch.setattr(smtp_provider, "connect_bounded", connect_bounded)
    box = _provider(tmp_path, 9, ssl.create_default_context(), timeout_seconds=2.0)
    with pytest.raises(SendUnreachable):
        box.send("RUN1-L-001", TO, SUBJECT, "Hi", 0.5)
    assert len(asked) == 1 and _within(asked[0], 0.5)


def test_l3_a_reply_is_read_with_the_time_left_not_an_older_limit() -> None:
    """Kills X01 / Y4 (the `sock.settimeout(budget.left())` before recv removed: the read ran with the old 10 s)."""
    sock = _Rec([b"250 ok\r\n"])
    assert _read_reply(sock, _Budget(0.5), bytearray()) == 250
    ((what, _, limit),) = sock.log
    assert what == "recv" and _within(limit, 0.5)


def test_l3_every_step_of_an_outbox_send_carries_at_most_the_time_left_and_quit_at_most_0_2() -> None:
    """Kills X02 (QUIT limit not capped at 0.2 s) and any step of the dialogue that is given a longer limit."""
    sock = _run_outbox(b"250 queued\r\n", budget=0.5)
    assert all(_within(t, 0.5) for _, _, t in sock.log)
    what, data, t = sock.log[-1]
    assert (what, data) == ("send", b"QUIT\r\n") and _within(t, 0.2)
    assert any(d == WIRE and _within(t2, 0.5) for _, d, t2 in sock.log)  # the text itself


@pytest.mark.parametrize("security", ["ssl", "starttls"])
def test_l3_every_step_of_a_provider_send_carries_at_most_the_time_left_and_quit_at_most_0_2(
    security: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X13 (QUIT limit not capped at 0.2 s) and any provider step given a longer limit."""
    sock = _run_provider(tmp_path, monkeypatch, security, b"250 queued\r\n", budget=0.5)
    assert all(_within(t, 0.5) for _, _, t in sock.log)
    what, data, t = sock.log[-1]
    assert (what, data) == ("send", b"QUIT\r\n") and _within(t, 0.2)
    assert any(d == WIRE and _within(t2, 0.5) for _, d, t2 in sock.log)


# ---- F5 / F7: the HELO fallback and the EHLO check before STARTTLS ----


@pytest.mark.parametrize("code", [421, 451, 354, 450])
def test_l5_an_ehlo_that_is_not_a_5xx_gets_no_helo_and_is_refused_outbox(code: int) -> None:
    """Kills X03 (`ehlo != 250`: the HELO fallback on any other reply)."""
    sock = _Rec([b"220 ok\r\n", f"{code} no\r\n".encode(), b"250 ok\r\n", b"250 ok\r\n"])
    with pytest.raises(SendRefused) as e:
        _outbox()._dialogue(sock, _Budget(2.0), TO, WIRE)
    assert str(e.value) == f"ehlo reply {code}"
    assert sock.sent() == [b"EHLO example.test\r\n"]


@pytest.mark.parametrize("code", [421, 451, 354, 450])
def test_l5_an_ehlo_that_is_not_a_5xx_gets_no_helo_and_is_refused_provider(
    code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills the provider sibling of X03."""
    sock = _Rec([b"220 ok\r\n", f"{code} no\r\n".encode(), b"250 ok\r\n", b"250 ok\r\n"])
    box = _prov_on(tmp_path, monkeypatch, sock, "starttls")
    with pytest.raises(SendRefused) as e:
        box._dialogue(sock, _Budget(2.0), FAKE_PASSWORD, "inbox-a@example.test", WIRE)
    assert str(e.value) == f"ehlo reply {code}"
    assert [d.split(b" ")[0].strip() for d in sock.sent()] == [b"EHLO"]


def test_l5_control_a_5xx_ehlo_reply_is_answered_with_helo_once() -> None:
    """CONTROL: an old server that does not know EHLO gets HELO, then the dialogue goes on."""
    sock = _run_outbox(b"250 queued\r\n", replies=[b"220 ok\r\n", b"500 what\r\n", b"250 ok\r\n"] + OUTBOX_OK[2:])
    assert [d.split(b" ")[0].strip() for d in sock.sent()][:2] == [b"EHLO", b"HELO"]


@pytest.mark.parametrize(
    ("code", "replies"),
    [
        (421, [b"220 ok\r\n", b"421 no\r\n", b"220 go\r\n", b"250 ok\r\n"]),
        (554, [b"220 ok\r\n", b"554 no\r\n", b"554 no\r\n", b"220 go\r\n", b"250 ok\r\n"]),  # HELO also refused
    ],
)
def test_l7_a_refused_ehlo_in_starttls_mode_is_refused_before_starttls(
    code: int, replies: list[bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X20 (`_expect(ehlo, "ehlo")` removed: STARTTLS was sent to a server that had refused EHLO)."""
    sock = _Rec(replies)
    box = _prov_on(tmp_path, monkeypatch, sock, "starttls")
    with pytest.raises(SendRefused) as e:
        box._dialogue(sock, _Budget(2.0), FAKE_PASSWORD, "inbox-a@example.test", WIRE)
    assert str(e.value) == f"ehlo reply {code}"
    assert b"STARTTLS\r\n" not in sock.sent()


# ---- F8: every weak cipher word is refused ----


@pytest.mark.parametrize(
    "word", ["NULL", "RC4", "EXPORT", "MD5", "ADH-", "AECDH-", "DES-CBC-"]
)  # written out: not read from the code
def test_l8_a_context_that_offers_a_cipher_with_a_weak_word_is_refused(
    word: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X21 (RC4 removed from the words) and the same for every other word: one cipher list per word."""
    ctx = new_verifying_context()
    monkeypatch.setattr(ctx, "get_ciphers", lambda: [{"name": "AES128-GCM-SHA256"}, {"name": f"X{word}Y"}])
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


def test_l8_control_the_words_are_the_seven_and_a_normal_context_passes() -> None:
    """CONTROL: a seventh word cannot be dropped without a change here; a normal context offers none of them."""
    assert set(WEAK_CIPHER_WORDS) == {"NULL", "RC4", "EXPORT", "MD5", "ADH-", "AECDH-", "DES-CBC-"}
    ctx = new_verifying_context()
    assert not any(w in c["name"] for c in ctx.get_ciphers() for w in WEAK_CIPHER_WORDS)
    assert require_verifying(ctx, "ctx") is ctx


# ---- F10: the login is exactly 235 (3xx, 4xx, 5xx too) ----


@pytest.mark.parametrize("code", [300, 334, 335, 399, 421, 535, 454])
def test_l10_a_login_reply_that_is_not_235_is_refused_and_nothing_goes_further(
    code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills the sibling of Y3 (`// 100 in (2, 3)`: a 334 or 335 counted as a login). r7i i3 tried 2xx codes only."""
    replies = SSL_OK[:2] + [f"{code} login\r\n".encode(), b"250 ok\r\n", b"250 ok\r\n", b"354 go\r\n"]
    sock = _Rec(replies)
    box = _prov_on(tmp_path, monkeypatch, sock, "ssl")
    with pytest.raises(SendRefused) as e:
        box._dialogue(sock, _Budget(2.0), FAKE_PASSWORD, "inbox-a@example.test", WIRE)
    assert str(e.value) == "login refused"
    assert not any(d.startswith(b"MAIL") for d in sock.sent())


# ---- F13: provider empty key ----


@pytest.mark.parametrize("key", ["", " ", "a b", "k" * 65])
def test_l13_a_send_key_outside_the_pattern_is_refused_with_its_text_before_the_network(
    key: str, tmp_path: Path
) -> None:
    """Kills the provider empty-key mutant (`{1,64}` -> `{0,64}`): the refusal has the key-pattern text, nothing is
    counted and nothing connects."""
    certs = _Certs(tmp_path)
    srv = FakeSmtp(certs.cert, certs.key, "localhost")
    try:
        box = _provider(tmp_path, srv.port, certs.context())
        with pytest.raises(SendRefused) as e:
            box.send(key, TO, SUBJECT, "Hi", 2.0)
        assert str(e.value) == "send key has characters outside the allowed set"
        assert srv.commands == [] and box.attempts == 0
    finally:
        srv.close()


# ---- F9 / G1 / G2 / G3: the mailbox reader ----


def _imap_box(step: float, total: float, wrap: Any, sock: Any) -> Any:
    box = object.__new__(imap_count._BoundedImap)
    box.host, box.port = "mail.example.test", 993
    box.ssl_context = types.SimpleNamespace(wrap_socket=wrap)
    box.deadline, box.step_seconds = time.monotonic() + total, step
    box.sock = sock
    return box


def test_l9_the_mailbox_handshake_is_given_at_most_one_step_even_inside_a_big_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills X27 (`min(step, time left)` -> the time left only: a step of 1 s inside a total of 20 s gave 20 s)."""
    seen: list[float | None] = []
    fake = _Rec([], first=OLD_LIMIT)
    monkeypatch.setattr(imap_count, "connect_bounded", lambda _h, _p, _s: fake)

    def wrap(sock: Any, server_hostname: str | None = None) -> str:
        seen.append(sock.gettimeout())
        return "wrapped"

    box = _imap_box(1.0, 20.0, wrap, fake)
    assert box._create_socket(10.0) == "wrapped"
    assert _within(seen[0], 1.0)


def test_l9_the_mailbox_handshake_is_given_the_time_left_when_that_is_shorter_than_a_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The other side of X27: a step of 10 s with 0.5 s of the total left gives at most 0.5 s."""
    seen: list[float | None] = []
    fake = _Rec([], first=OLD_LIMIT)
    monkeypatch.setattr(imap_count, "connect_bounded", lambda _h, _p, _s: fake)

    def wrap(sock: Any, server_hostname: str | None = None) -> str:
        seen.append(sock.gettimeout())
        return "wrapped"

    box = _imap_box(10.0, 0.5, wrap, fake)
    assert box._create_socket(10.0) == "wrapped"
    assert _within(seen[0], 0.5)


@pytest.mark.parametrize(
    ("step", "total", "expected"), [(10.0, 2.0, imap_count.ImapTotalTimeout), (1.0, 20.0, TimeoutError)]
)
def test_l9_a_handshake_that_times_out_is_the_total_error_only_when_the_total_was_the_limit(
    step: float, total: float, expected: type, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X30 (`handshake_limited_by_total = False`: a time-out at the total limit read as a step time-out)."""
    fake = _Rec([])
    monkeypatch.setattr(imap_count, "connect_bounded", lambda _h, _p, _s: fake)

    def wrap(_sock: Any, server_hostname: str | None = None) -> str:
        raise TimeoutError("handshake")

    box = _imap_box(step, total, wrap, fake)
    with pytest.raises(expected) as e:
        box._create_socket(10.0)
    assert type(e.value) is expected


def test_l9_every_write_to_the_mailbox_is_capped_at_one_step() -> None:
    """Kills X29 (`min(step, left)` -> left: a write inside a total of 20 s got 20 s although a step is 1 s)."""
    fake = _Rec([], first=OLD_LIMIT)
    box = _imap_box(1.0, 20.0, lambda *_a, **_k: None, fake)
    box.send(b"a1 NOOP\r\n")
    ((what, _, limit),) = fake.log
    assert what == "send" and _within(limit, 1.0)


class _LoginBox:
    """A mailbox connection whose login line fails with a network error; `work_error` fails the work after it."""

    def __init__(self, login_error: BaseException | None, work_error: BaseException | None = None) -> None:
        self.sock = _Rec([])
        self.deadline = float("inf")
        self.login_error, self.work_error = login_error, work_error

    def login(self, _user: str, _password: str) -> None:
        if self.login_error is not None:
            raise self.login_error

    def logout(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def _imap_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, box: _LoginBox) -> Any:
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    s = imap_count.ImapSettings(
        "mail.example.test", "reader-user", pw, ssl_context=new_verifying_context(), folders=("INBOX",)
    )
    monkeypatch.setattr(imap_count, "_BoundedImap", lambda *_a, **_k: box)

    def work(_m: Any) -> dict[str, dict[str, int]]:
        if box.work_error is not None:
            raise box.work_error
        return {}

    return imap_count._session(s, work)


@pytest.mark.parametrize("error", [ConnectionResetError("reset"), imaplib.IMAP4.abort("hung up"), OSError("boom")])
def test_g1_a_network_error_during_the_login_is_never_repeated(
    error: BaseException, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kills X28 (`logging_in or` removed: a failure during the login became a repeatable connection error, so a
    second login attempt was made)."""
    with pytest.raises(imap_count.ImapCountError) as e:
        _imap_session(tmp_path, monkeypatch, _LoginBox(error))
    assert type(e.value) is imap_count.ImapCountError


@pytest.mark.parametrize("error", [ConnectionResetError("reset"), imaplib.IMAP4.abort("hung up")])
def test_g1_control_a_network_error_after_the_login_is_a_connection_error_worth_one_repeat(
    error: BaseException, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL: the same error after the login is the repeatable class."""
    with pytest.raises(imap_count.ImapConnectionError):
        _imap_session(tmp_path, monkeypatch, _LoginBox(None, error))


# ---- F4: server.py, every blocking send and receive has a time limit ----


def _pair() -> tuple[socket.socket, socket.socket]:
    """(the desk's side, a client that never reads): a loopback pair with small buffers."""
    ls = socket.socket()
    ls.bind((LOOP, 0))
    ls.listen(1)
    client = socket.socket()
    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    client.connect(ls.getsockname())
    desk, _ = ls.accept()
    ls.close()
    desk.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    return desk, client


def _fill_send_buffer(desk: socket.socket) -> None:
    """Send until the desk's side cannot take another byte (the client never reads), then back to blocking."""
    desk.setblocking(False)
    try:
        while True:
            desk.send(b"x" * 65536)
    except BlockingIOError:
        pass
    desk.settimeout(None)


class _NoLinger:
    def add(self, _sock: Any) -> bool:
        return False  # no room: the loop must drain on its own


def _busy_self() -> Any:
    return types.SimpleNamespace(_linger=_NoLinger(), shutdown_request=lambda r: r.close())


def _run_busy(desk: socket.socket, seconds: float) -> bool:
    """Run `_refuse_busy` on a thread; True when it ended inside `seconds`."""
    th = threading.Thread(target=server._Server._refuse_busy, args=(_busy_self(), desk), daemon=True)
    th.start()
    th.join(seconds)
    return not th.is_alive()


def test_l4_a_client_that_never_reads_cannot_hold_the_accept_loop_in_the_busy_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills V01 (`request.settimeout(BUSY_WRITE_TIMEOUT_SECONDS)` removed: the 503 write on the accept loop waited
    for ever). The desk's send buffer is full and the client reads nothing."""
    monkeypatch.setattr(server, "BUSY_WRITE_TIMEOUT_SECONDS", 0.3)
    desk, client = _pair()
    try:
        _fill_send_buffer(desk)
        t0 = time.monotonic()
        assert _run_busy(desk, 3.0), "the busy reply write is not bounded"
        assert time.monotonic() - t0 < 2.0
    finally:
        client.close()
        desk.close()


def test_l4_a_client_that_never_speaks_cannot_hold_the_accept_loop_in_the_busy_drain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills V06 (`request.setblocking(False)` before the drain read removed: the read waited for the write limit).
    The client reads the reply and then says nothing and stays open; the lingerer is full."""
    monkeypatch.setattr(server, "BUSY_WRITE_TIMEOUT_SECONDS", 3.0)
    desk, client = _pair()
    try:
        t0 = time.monotonic()
        assert _run_busy(desk, 2.5), "the drain read is not bounded by the quiet time"
        assert time.monotonic() - t0 < 1.5
        assert client.recv(4096).startswith(b"HTTP/1.0 503")
    finally:
        client.close()
        desk.close()


class _Writer:
    """wfile of a handler: the headers take 0.4 s to write; the body write records the limit the connection had."""

    def __init__(self, conn: _Rec, header_seconds: float) -> None:
        self.conn, self.header_seconds = conn, header_seconds
        self.body_limit: float | None = None

    def write(self, data: bytes) -> None:
        if data.startswith(b"HTTP/"):
            time.sleep(self.header_seconds)
        else:
            self.body_limit = self.conn.gettimeout()

    def flush(self) -> None:
        pass


def test_l4_the_reply_body_is_written_with_the_time_left_of_the_reply_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills V02 (the `settimeout(left)` before the body write removed: the body got the full reply limit again
    although the headers had used 0.4 s of it)."""
    monkeypatch.setattr(server, "REPLY_WRITE_TIMEOUT_SECONDS", 1.0)
    h = object.__new__(server._Handler)
    h.request_version, h.command, h.requestline = "HTTP/1.0", "GET", "GET / HTTP/1.0"
    conn = _Rec([], first=OLD_LIMIT)
    h.connection = conn
    writer = _Writer(conn, 0.4)
    h.wfile = writer
    h.close_connection = False
    h._slot = types.SimpleNamespace(release=lambda: None)
    h._send_bytes(200, b"{}", "application/json")
    assert writer.body_limit is not None and 0 < writer.body_limit < 0.7


class _Fin:
    """connection of a handler at its end: nothing more arrives (recv times out); records the limit of each recv."""

    def __init__(self) -> None:
        self.t: float | None = OLD_LIMIT
        self.limits: list[float | None] = []

    def settimeout(self, t: float | None) -> None:
        self.t = t

    def shutdown(self, _how: int) -> None:
        pass

    def recv(self, _n: int) -> bytes:
        self.limits.append(self.t)
        raise TimeoutError("nothing is arriving")


def _finish(monkeypatch: pytest.MonkeyPatch, drain_total: float) -> list[float | None]:
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", drain_total)
    h = object.__new__(server._Handler)
    conn = _Fin()
    h.connection = conn
    h.wfile = types.SimpleNamespace(flush=lambda: None, close=lambda: None, closed=True)
    h.rfile = types.SimpleNamespace(close=lambda: None, closed=True)
    h.finish()
    return conn.limits


def test_l4_the_finish_drain_waits_only_the_quiet_time_for_a_silent_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills V05 (`min(QUIET_DRAIN_SECONDS, left)` -> the left of the whole drain: a silent client held the thread for
    the full DRAIN_TOTAL_SECONDS)."""
    (limit,) = _finish(monkeypatch, 5.0)
    assert limit is not None and 0 < limit <= server.QUIET_DRAIN_SECONDS


def test_l4_the_finish_drain_never_waits_longer_than_what_is_left_of_the_drain(monkeypatch: pytest.MonkeyPatch) -> None:
    """The other side of V05: with 0.01 s left of the drain the wait is at most that."""
    (limit,) = _finish(monkeypatch, 0.01)
    assert limit is not None and 0 < limit <= 0.01


def test_l4_control_a_drain_of_a_body_that_never_arrives_ends_at_the_drain_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PIN, passes on V03 by design: V03 (`self.connection.settimeout(budget)` in `_drain` removed) is EQUIVALENT,
    because `_DeadlineReader.readinto` sets the very same wall-clock limit (armed at the top of `_drain`) before every
    read. What is pinned is the behaviour both share: a reader that sends one byte per 0.1 s is dropped at the limit."""
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 0.5)
    desk, client = _pair()
    h = object.__new__(server._Handler)
    reader = server._DeadlineReader(desk, lambda: server.REQUEST_TIMEOUT_SECONDS, lambda: False)
    h._reader = reader
    h.rfile = io.BufferedReader(reader)
    h.connection = desk
    stop = threading.Event()

    def drip() -> None:
        while not stop.is_set():
            try:
                client.send(b"z")
            except OSError:
                return
            time.sleep(0.1)

    th = threading.Thread(target=drip, daemon=True)
    th.start()
    try:
        t0 = time.monotonic()
        h._drain(10_000)
        took = time.monotonic() - t0
        assert 0.3 < took < 2.0
    finally:
        stop.set()
        th.join(2)
        client.close()
        desk.close()


class _ReaderSock:
    """A socket for `_DeadlineReader`: recv_into answers at once and records the limit it had."""

    def __init__(self) -> None:
        self.t: float | None = OLD_LIMIT
        self.during: list[float | None] = []

    def settimeout(self, t: float | None) -> None:
        self.t = t

    def recv_into(self, b: Any) -> int:
        self.during.append(self.t)
        b[:1] = b"x"
        return 1


def test_l4_the_reader_sets_the_time_left_for_the_read_and_puts_the_idle_limit_back_after_it() -> None:
    """Kills S2 (`_restore_timeout` that never sets the idle limit: the socket kept the short deadline-limited limit
    after a read, and a later write on it would run on that stale value). Redundant with the reply write's own
    settimeout in the normal path, so this pins the reader's own promise (its docstring)."""
    sock = _ReaderSock()
    reader = server._DeadlineReader(sock, lambda: 30.0, lambda: False)
    reader.arm("body", 0.5)
    assert reader.readinto(bytearray(4)) == 1
    assert sock.during and _within(sock.during[0], 0.5)  # the read ran on the time left of the armed phase
    assert sock.t == 30.0  # and the normal per-read limit is back after it


def _closed_within(sock: socket.socket, seconds: float) -> bool:
    """True when the lingerer closed `sock` (its file number is gone) inside `seconds`."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if sock.fileno() < 0:
            return True
        time.sleep(0.02)
    return sock.fileno() < 0


def test_l4_the_lingerer_drops_a_silent_connection_at_the_time_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills S3 (`select.select(..., None)`: the lingerer waited for ever for a client that says nothing, so the time
    limit was never looked at), S11 (the time limit of a lingering socket removed) and S4 (the socket left blocking).
    The client stays open and silent; the time limit is 0.3 s."""
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 0.3)
    desk, client = _pair()
    linger = server._Lingerer()
    try:
        assert linger.add(desk) is True
        assert desk.gettimeout() == 0.0, "a socket the lingerer reads must not block"
        assert _closed_within(desk, 3.0), "a silent lingering connection was not dropped at its time limit"
    finally:
        linger.close_all()
        client.close()
        desk.close()


def test_l4_the_lingerer_drops_a_connection_that_sends_more_than_the_byte_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills S12 (the byte limit of a lingering socket removed). The time limit is long (30 s), the byte limit 1000;
    the client sends 20000 bytes and stays open."""
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 30.0)
    monkeypatch.setattr(server, "DRAIN_MAX_BYTES", 1000)
    desk, client = _pair()
    linger = server._Lingerer()
    try:
        assert linger.add(desk) is True
        client.sendall(b"y" * 20000)
        assert _closed_within(desk, 3.0), "a lingering connection was not dropped at its byte limit"
    finally:
        linger.close_all()
        client.close()
        desk.close()


# ---- G4: the guard: a new adapter that reads a secret needs an order test ----

SRC = Path(__file__).resolve().parent.parent / "src" / "lead_desk"
ORDER_TESTS = Path(__file__).resolve().parent / "test_r7h_findings.py"
READERS = {  # module -> the words its `test_order_*` test (in test_r7h_findings.py) has in its name
    "live_claude": "live_model",
    "crm_hubspot": "hubspot",
    "smtp_provider": "smtp",
    "imap_count": "mailbox",
}
_CALL = re.compile(r"(?<!def )\bread_secret_(?:line|file)\(")


def test_g4_only_the_four_known_adapters_read_a_secret_and_each_has_an_order_test() -> None:
    """The reviewer's guard. A module of src/lead_desk (other than regfile, the reader itself) that calls
    read_secret_line / read_secret_file must be listed in READERS and have a `test_order_<word>` test in
    test_r7h_findings.py (the order: the secret is read before any counter, reservation or connection). A fifth reader
    fails here until its order test is written and listed."""
    found = {p.stem for p in SRC.glob("*.py") if p.stem != "regfile" and _CALL.search(p.read_text(encoding="utf-8"))}
    assert found == set(READERS), f"a module reads a secret without an order test (or one was removed): {sorted(found)}"
    names = re.findall(r"^def (test_order_\w+)", ORDER_TESTS.read_text(encoding="utf-8"), re.M)
    for module, word in READERS.items():
        assert any(word in n for n in names), f"{module}: no test_order_* test with {word!r} in its name"
