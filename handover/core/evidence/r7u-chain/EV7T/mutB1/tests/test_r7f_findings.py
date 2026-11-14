"""Round 7F: the pass-8 mail-path review (minors and survivors). Real loopback sockets, made-up data only.

Every test says in its docstring which mutant it kills (a mutant really run, with the result in R7F-RESULTS.md) or
that it is a CONTROL (it passes on r7e and on the older trees as well, and names the mutant that was run)."""

from __future__ import annotations

import json
import socket
import ssl
import threading
import time
import warnings
from pathlib import Path
from typing import Any

import pytest
import support
from test_r7d_findings import _run_driver
from test_r7e_findings import _DropsSomeRequests

from demo_only.fake_imap import FakeImap
from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp, make_cert
from lead_desk.constants import HUBSPOT_HOST_SUFFIXES
from lead_desk.contract import SendRefused
from lead_desk.crm_hubspot import HubspotSettings
from lead_desk.envnum import SettingRefused
from lead_desk.imap_count import (
    ImapConnectionError,
    ImapCountError,
    ImapSettings,
    ImapTotalTimeout,
    _BoundedImap,
    _DeadlineReader,
    _session,
    counts_by_key,
)
from lead_desk.jsonread import JsonTooDeep, loads_bounded
from lead_desk.live_claude import LiveSettings, LiveTransport
from lead_desk.regfile import FileRefused, read_secret_line
from lead_desk.smtp_outbox import _REPLY_MAX_BYTES, _Budget, _Closed, _dot_stuff, _read_reply
from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox
from lead_desk.tls_trust import CaFileRefused, require_verifying
from load_tools import load_driver


def _imap_settings(tmp_path: Path, port: int, total: float, step: float) -> tuple[ImapSettings, Path, Path]:
    made = make_cert(tmp_path, "localhost")
    assert made is not None
    cert, key = made
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n")
    s = ImapSettings(
        "localhost",
        "reader-user",
        pw,
        port=port,
        folders=("INBOX",),
        timeout_seconds=step,
        total_seconds=total,
        ssl_context=ssl.create_default_context(cafile=str(cert)),
    )
    return s, cert, key


def test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step(tmp_path: Path) -> None:
    """Kills mutant I03 (imap_count._create_socket: the connect waits one plain step, not min(step, time left)):
    with a total of 1 s and a step of 10 s the mutant ends after about 10 s. Fails on the I03 mutant, passes on r7e.
    The server is a listener with backlog 0 and filler connections, so the next SYN is dropped and a connect hangs."""
    ls = socket.socket()
    ls.bind(("127.0.0.1", 0))
    ls.listen(0)
    port = ls.getsockname()[1]
    fillers = []
    try:
        for _ in range(3):
            c = socket.socket()
            c.setblocking(False)
            try:
                c.connect(("127.0.0.1", port))
            except BlockingIOError:
                pass
            fillers.append(c)
        probe = socket.socket()
        probe.settimeout(0.5)
        try:
            probe.connect(("127.0.0.1", port))
            pytest.skip("this system completes a connect to a full queue")
        except OSError:
            pass
        finally:
            probe.close()
        s, _, _ = _imap_settings(tmp_path, port, total=1.0, step=10.0)
        t0 = time.monotonic()
        with pytest.raises(ImapTotalTimeout):
            counts_by_key(s, "RUN1-")
        assert time.monotonic() - t0 < 3.0
    finally:
        for c in fillers:
            c.close()
        ls.close()


def test_f1_a_server_that_is_silent_after_tls_ends_with_the_total_time_error(tmp_path: Path) -> None:
    """Kills mutant I09 (imap_count._DeadlineReader._fill: a timeout past the deadline stays a plain timeout, so the
    caller sees ImapCountError instead of ImapTotalTimeout). Fails on the I09 mutant, passes on r7e. The fake server
    completes TLS and then says nothing; it keeps a reference to its TLS socket (a dropped one is closed)."""
    ss = socket.socket()
    ss.bind(("127.0.0.1", 0))
    ss.listen(2)
    port = ss.getsockname()[1]
    s, cert, key = _imap_settings(tmp_path, port, total=1.0, step=10.0)

    def serve() -> None:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(cert), str(key))
        c, _ = ss.accept()
        try:
            kept = ctx.wrap_socket(c, server_side=True)
            time.sleep(4)
            kept.close()
        except OSError:
            pass

    threading.Thread(target=serve, daemon=True).start()
    try:
        with pytest.raises(ImapTotalTimeout):
            counts_by_key(s, "RUN1-")
    finally:
        ss.close()


# ---- tls_trust.require_verifying: the three checks that guard a context handed in by other code ----


def test_f2_a_context_without_the_host_name_check_is_refused() -> None:
    """Kills mutant T03 (tls_trust.require_verifying: the host name check not required). Fails on T03, passes on r7e."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False  # the chain is still checked (CERT_REQUIRED), only the name is not
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


@pytest.mark.parametrize("floor", ["TLSv1", "TLSv1_1"])
def test_f2_a_context_that_allows_tls_below_1_2_is_refused(floor: str) -> None:
    """Kills mutant T04 (the floor test lowered to `< TLSv1`, so TLS 1.0 and 1.1 pass). Fails on T04 for both floors
    (TLS 1.1 passes the mutant, and TLS 1.0 is not below TLS 1.0), passes on r7e."""
    ctx = ssl.create_default_context()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        ctx.minimum_version = getattr(ssl.TLSVersion, floor)
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


@pytest.mark.parametrize("ciphers", ["NULL:@SECLEVEL=0", "aNULL:@SECLEVEL=0", "MD5:@SECLEVEL=0"])
def test_f2_a_context_that_offers_a_null_or_md5_cipher_is_refused(ciphers: str) -> None:
    """Kills mutant T08 (the weak-cipher test removed). Fails on T08, passes on r7e."""
    ctx = ssl.create_default_context()
    ctx.set_ciphers(ciphers)
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


@pytest.mark.parametrize("ciphers", ["ADH-AES256-GCM-SHA384:@SECLEVEL=0", "AECDH-AES256-SHA:@SECLEVEL=0"])
def test_f5_a_context_that_offers_an_anonymous_cipher_is_refused(ciphers: str) -> None:
    """FIX TEST (found while classifying mutant T03, MAIL7): the word list had "anon", which no OpenSSL cipher name
    contains, so ciphers without any server login (names starting ADH- or AECDH-) were accepted. FAILS on r7e (the
    context is accepted), passes on r7f; the mutant that drops the two new words fails it."""
    ctx = ssl.create_default_context()
    ctx.set_ciphers(ciphers)
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


# ---- smtp_provider: a context weakened after the object was built; STARTTLS must be a plain 220 ----


class _Certs:
    def __init__(self, tmp: Path) -> None:
        made = make_cert(tmp, "localhost")
        if made is None:
            support.skip_or_fail_without_openssl()
        self.cert, self.key = made

    def context(self) -> ssl.SSLContext:
        return ssl.create_default_context(cafile=str(self.cert))


def _provider(tmp_path: Path, port: int, ctx: ssl.SSLContext, **over: Any) -> SmtpProviderOutbox:
    pw = tmp_path / "smtp-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    kw: dict[str, Any] = {
        "host": "localhost",
        "port": port,
        "user": "sender-user",
        "password_file": pw,
        "mail_from": "sender@example.test",
        "recipients": ("inbox-a@example.test",),
        "max_sends": 5,
        "security": "starttls",
        "timeout_seconds": 2.0,
    }
    return SmtpProviderOutbox(ProviderSettings(**(kw | over)), ssl_context=ctx)


def test_f2_a_context_weakened_after_the_object_was_built_is_refused_before_any_connection(tmp_path: Path) -> None:
    """Kills mutants P03 (the re-check at the start of send removed: the connection is opened and the dialogue starts
    before _wrap refuses) and P07 (the re-check removed everywhere: the mail is sent). Fails on both, passes on r7e."""
    certs = _Certs(tmp_path)
    srv = FakeSmtp(certs.cert, certs.key, "localhost")
    try:
        ctx = certs.context()
        box = _provider(tmp_path, srv.port, ctx)
        ctx.check_hostname = False  # weakened AFTER the constructor checked it
        ctx.verify_mode = ssl.CERT_NONE
        with pytest.raises(SendRefused):
            box.send("RUN1-L-001", "ada@example.test", "Thanks", "Hi", 2.0)
        assert srv.commands == []  # nothing, not even EHLO, went to the server
        assert srv.messages == [] and box.sent == 0
    finally:
        srv.close()


def test_f2_a_blank_ca_file_setting_is_refused_not_read_as_unset() -> None:
    """Kills mutant P09 (a present but blank DESK_SMTPP_CA_FILE is treated as unset, so the system authorities would
    be trusted without a word). Fails on P09, passes on r7e."""
    env = {
        "DESK_SMTPP_HOST": "localhost",
        "DESK_SMTPP_USER": "sender-user",
        "DESK_SMTPP_PASSWORD_FILE": "pw.txt",
        "DESK_SMTPP_FROM": "sender@example.test",
        "DESK_SMTPP_RECIPIENTS": "inbox-a@example.test",
        "DESK_SMTPP_MAX_SENDS": "3",
    }
    assert ProviderSettings.from_env(env).ca_file is None
    for blank in ("", "   "):
        with pytest.raises(SettingRefused):
            ProviderSettings.from_env({**env, "DESK_SMTPP_CA_FILE": blank})


def test_f2_a_ca_file_and_a_context_together_are_refused(tmp_path: Path) -> None:
    """Kills mutant P08 (both a CA file and a context argument allowed: the file would be ignored without a word).
    Fails on P08, passes on r7e."""
    certs = _Certs(tmp_path)
    with pytest.raises(SettingRefused):
        _provider(tmp_path, 1, certs.context(), ca_file=certs.cert)


class _ScriptedStarttls:
    """A server written for this test: `after_starttls_reply` is what it answers to STARTTLS. With b"220..." it
    appends the bytes of an injected reply in the same send (a classic attack: text put in front of the handshake),
    then does the TLS handshake; with anything else it stays plain. `early` = what the client sent after the
    post-TLS EHLO before the server answered it (must stay empty), `plain_after_refusal` = bytes seen after a
    refusal."""

    def __init__(self, certs: _Certs, reply: bytes) -> None:
        self.reply, self.early, self.plain_after_refusal, self.lines = reply, b"", b"", []
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(str(certs.cert), str(certs.key))
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(2)
        self.port = self.srv.getsockname()[1]
        threading.Thread(target=self._run, daemon=True).start()

    def _line(self, f: Any) -> bytes:
        return f.readline(4096)

    def _run(self) -> None:
        try:
            c, _ = self.srv.accept()
            f = c.makefile("rwb", buffering=0)
            f.write(b"220 ready\r\n")
            self.lines.append(self._line(f))  # EHLO
            f.write(b"250-x\r\n250-STARTTLS\r\n250 AUTH PLAIN\r\n")
            self.lines.append(self._line(f))  # STARTTLS
            f.write(self.reply)
            if not self.reply.startswith(b"220"):
                c.settimeout(1.0)
                try:
                    self.plain_after_refusal = c.recv(64)
                except OSError:
                    pass
                return
            tls = self.ctx.wrap_socket(c, server_side=True)
            g = tls.makefile("rwb", buffering=0)
            self.lines.append(self._line(g))  # EHLO after TLS
            tls.settimeout(0.8)
            try:
                self.early = tls.recv(256)  # the client must wait for our answer
            except OSError:
                pass
            tls.settimeout(3.0)
            g.write(b"250 ok\r\n")
            self.lines.append(self._line(g))  # AUTH
            g.write(b"535 no\r\n")
        except OSError:
            pass

    def close(self) -> None:
        self.srv.close()


def test_f2_bytes_that_arrive_with_the_starttls_reply_are_not_read_as_a_reply_after_tls(tmp_path: Path) -> None:
    """Kills mutant P01 (the plaintext buffer kept after STARTTLS). The server adds `250 INJECTED` to the same send as
    `220`; the client must throw it away and wait for the real answer to its second EHLO. On the P01 mutant the
    injected line is taken as that answer and AUTH is sent at once (`early` is not empty). Fails on P01, passes on
    r7e."""
    certs = _Certs(tmp_path)
    srv = _ScriptedStarttls(certs, b"220 go\r\n250 INJECTED\r\n")
    try:
        box = _provider(tmp_path, srv.port, certs.context())
        with pytest.raises(SendRefused, match="login refused"):  # the scripted server refuses the login on purpose
            box.send("RUN1-L-001", "ada@example.test", "Thanks", "Hi", 2.0)
        assert srv.early == b""
        assert srv.lines[2].startswith(b"EHLO") and srv.lines[3].startswith(b"AUTH PLAIN")
    finally:
        srv.close()


@pytest.mark.parametrize("reply", [b"250 ok\r\n", b"200 ok\r\n", b"299 ok\r\n"])
def test_f2_only_a_220_answer_to_starttls_starts_the_handshake(tmp_path: Path, reply: bytes) -> None:
    """Kills mutant P04 (any 2xx accepted for STARTTLS: the client would start a TLS handshake on a server that did
    not agree, so the password could follow in the wrong mode). Fails on P04 (the client sends a handshake, the call
    ends later as SendUnreachable), passes on r7e (SendRefused, and no handshake byte arrives)."""
    certs = _Certs(tmp_path)
    srv = _ScriptedStarttls(certs, reply)
    try:
        box = _provider(tmp_path, srv.port, certs.context(), timeout_seconds=1.5)
        with pytest.raises(SendRefused, match="starttls refused"):
            box.send("RUN1-L-001", "ada@example.test", "Thanks", "Hi", 1.5)
        assert srv.plain_after_refusal == b""
    finally:
        srv.close()


# ---- imap_count: no context given means the verifying one ----


def test_f2_no_ssl_context_means_a_verified_connection_and_no_login_to_an_untrusted_server(tmp_path: Path) -> None:
    """Kills mutant I18 (imaplib's unverified default used when no context is given). The fake server's certificate is
    not trusted by the system store, so the call must end before any LOGIN. Fails on I18 (the login goes out and the
    call returns counts), passes on r7e."""
    certs = _Certs(tmp_path)
    srv = FakeImap(certs.cert, certs.key, "localhost", {"INBOX": ["RUN1-L-001"]})
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    try:
        s = ImapSettings(
            "localhost", "reader-user", pw, port=srv.port, folders=("INBOX",), timeout_seconds=2.0, total_seconds=5.0
        )
        assert s.ssl_context is None
        with pytest.raises(ImapCountError):
            counts_by_key(s, "RUN1-")
        assert srv.logins == [] and srv.login_lines == []
    finally:
        srv.close()


# ---- crm_hubspot: the vendor domain test is a whole-label test ----


@pytest.mark.parametrize("prefix", ["evil", "not", "x-"])
def test_f2_a_host_that_only_ends_with_a_vendor_name_is_not_a_vendor_host(prefix: str) -> None:
    """Kills mutant V03 (endswith(suffix) without the dot: a host that only ends with a vendor name would count as the
    vendor's and get the key). Fails on V03, passes on r7e."""
    for suffix in HUBSPOT_HOST_SUFFIXES:
        with pytest.raises(ValueError, match="vendor's own domains"):
            HubspotSettings(Path("k"), 1, base_url=f"https://{prefix}{suffix}")
        ok = f"https://{'a' + 'pi'}.{suffix}"  # a real label in front of the vendor domain stays allowed (CONTROL)
        assert HubspotSettings(Path("k"), 1, base_url=ok).base_url == ok


# ---- live_claude: the key-read refusal is a fixed text, not the class of the error ----


@pytest.mark.parametrize("shape", ["missing", "two lines", "empty"])
def test_f2_the_key_read_refusal_is_the_fixed_text_and_names_no_class(tmp_path: Path, shape: str) -> None:
    """Kills mutant V01 (LiveTransport(repr(e)): the text would start with the class name FileRefused and hold quotes
    and brackets). Fails on V01, passes on r7e."""
    key = tmp_path / "key.txt"
    if shape != "missing":
        key.write_bytes(b"made-up-key-aaaa\nsecond\n" if shape == "two lines" else b"")
    from decimal import Decimal

    from lead_desk.live_claude import LiveQualifier  # local import: the settings need a full set of money values

    s = LiveSettings(
        model="fake-model-1",
        key_file=key,
        price_in_per_mtok=Decimal("1"),
        price_out_per_mtok=Decimal("1"),
        price_date="2026-01-01",
        cap_run_usd=Decimal("1"),
        cap_total_usd=Decimal("3"),
        ledger_path=tmp_path / "ledger.jsonl",
        run_id="run-a",
        base_url="http://127.0.0.1:9",
        timeout_seconds=2.0,
    )
    with pytest.raises(LiveTransport) as info:
        LiveQualifier(s)._read_key()
    text = str(info.value)
    assert text.startswith("the key file ") and "Refused" not in text and "(" not in text and "'" not in text, text


# ---- load_driver: the look for a listener sends nothing ----


def test_f2_the_listener_probe_sends_no_byte_and_closes() -> None:
    """Kills mutant L03 (the probe sends an HTTP request on its connection). The listener records everything that
    arrives; the probe must give True and the connection must end with no byte at all. Fails on L03, passes on r7e."""
    ls = socket.socket()
    ls.bind(("127.0.0.1", 0))
    ls.listen(2)
    port = ls.getsockname()[1]
    got: list[bytes] = []

    def serve() -> None:
        c, _ = ls.accept()
        c.settimeout(2.0)
        try:
            got.append(c.recv(256))  # b"" means the client closed without sending anything
        except OSError:
            got.append(b"timeout")
        finally:
            c.close()

    th = threading.Thread(target=serve, daemon=True)
    th.start()
    try:
        assert load_driver.desk_listening(f"http://127.0.0.1:{port}") is True
        th.join(5)
        assert got == [b""]
    finally:
        ls.close()


# ---- load_driver (r7e review M1): a run that was stopped early is never a success ----


class _SlowConn:
    """Wraps a connection: the answer (sendall) leaves only `delay` seconds after the connection was made."""

    def __init__(self, conn: socket.socket, delay: float) -> None:
        self._c, self._due = conn, time.monotonic() + delay

    def __enter__(self) -> _SlowConn:
        return self

    def __exit__(self, *a: object) -> None:
        self._c.close()

    def settimeout(self, t: float) -> None:
        self._c.settimeout(t)

    def recv(self, n: int) -> bytes:
        return self._c.recv(n)

    def sendall(self, data: bytes) -> None:
        time.sleep(max(0.0, self._due - time.monotonic()))
        self._c.sendall(data)


class _AnswersOnlyAfter(_DropsSomeRequests):
    """The pattern of the r7e review: the FIRST request is answered 202 only after QUIET seconds, every other request
    that arrives is closed without an answer."""

    QUIET = 3.0
    DROP_FROM, DROP_TO = 1, 10**9

    def _one(self, conn: Any) -> None:
        super()._one(_SlowConn(conn, self.QUIET))


def test_m1_r7e_a_stopped_run_that_the_desk_answers_later_is_not_a_success(tmp_path: Path) -> None:
    """FAILS on r7e: rc 0, final_status {error 1, 202 1, driver:stopped 6}, empty stderr (six of eight requests never
    sent, exit code says success). On r7f: rc 3 and one true line that names how many were never sent."""
    srv = _AnswersOnlyAfter()
    try:
        log = tmp_path / "req.jsonl"
        done = _run_driver(
            f"http://127.0.0.1:{srv.port}", "burst:8", log, "--workers", "1", "--threads", "2", timeout=120
        )
    finally:
        srv.close()
    err = done.stderr.decode()
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    stopped = [d for d in lines if d["final_status"] == "driver:stopped"]
    answered = [d for d in lines if d["accepted"]]
    assert stopped and answered, [d["final_status"] for d in lines]  # the pattern of the review: stop, then an answer
    assert done.returncode == 3, (done.returncode, err[-300:])
    taken = [d for d in lines if d.get("gave_up") == "stopped"]  # r7g: never sent AND given up by the stop
    assert len(taken) >= len(stopped), (len(taken), len(stopped))
    assert f"{len(taken)} of 8 requests were never sent or were given up" in err, err[-300:]
    assert "cannot be reached" not in err  # an answer did arrive, so that line would be false
    assert json.loads(done.stdout.decode())["stopped"] == len(taken)  # the summary still says so


# ---- tests/support.py::book_folder_in_repo (r7e review m3): never write through a data link ----


def test_m3_book_folder_in_repo_refuses_a_data_link_and_writes_nothing_through_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAILS on r7e: the helper followed the link, made its fresh folder inside the link target and removed it again
    (no failure). On r7f it fails the test at once and the target stays empty. Also a link that points nowhere."""
    repo = tmp_path / "repo"
    repo.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (repo / "data").symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(support, "REPO", repo)
    with pytest.raises(pytest.fail.Exception), support.book_folder_in_repo("x-"):
        pytest.fail("the helper must not get this far")
    assert list(target.iterdir()) == []
    (repo / "data").unlink()
    (repo / "data").symlink_to(tmp_path / "nowhere")
    with pytest.raises(pytest.fail.Exception), support.book_folder_in_repo("x-"):
        pytest.fail("the helper must not get this far")
    assert not (tmp_path / "nowhere").exists()


def test_m3_book_folder_in_repo_leaves_the_repository_folder_as_it_found_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL (the r7e behaviour kept; passes on r7e; no mutant run): a plain data folder that did not exist is made
    and removed again, a data folder that held something is kept."""
    monkeypatch.setattr(support, "REPO", tmp_path)
    with support.book_folder_in_repo("x-") as f:
        assert f.parent == tmp_path / "data" and f.is_dir()
    assert not (tmp_path / "data").exists()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "keep.txt").write_text("x", encoding="utf-8")
    with support.book_folder_in_repo("x-"):
        pass
    assert (tmp_path / "data" / "keep.txt").exists()


# ---- regfile.read_secret_line: what is trimmed, what is one line, what is text ----

KEY = "made-up-key-0123456789"  # 22 printable ASCII characters


def _secret(tmp_path: Path, raw: bytes, **kw: Any) -> str:
    f = tmp_path / "secret.txt"
    f.write_bytes(raw)
    return read_secret_line(f, "key", "key", **kw)


@pytest.mark.parametrize("tail", ["\u00a0", "\u2003", "\x0b", "\x0c", "\u3000"])
def test_f2_only_ascii_space_is_trimmed_round_a_secret(tmp_path: Path, tail: str) -> None:
    """Kills mutant R02 (`.strip()` for every kind of space): a no-break space (or another non-ASCII or control space)
    after the key would be cut off and the key accepted; it must be refused. Fails on R02, passes on r7e. CONTROL part:
    ASCII space, tab and line ends round the key are trimmed (passes on both)."""
    assert _secret(tmp_path, (" \t" + KEY + " \r\n").encode()) == KEY
    with pytest.raises(FileRefused):
        _secret(tmp_path, (KEY + tail + "\n").encode("utf-8"))


@pytest.mark.parametrize("mid", [b"\r", b"\n", b"\r\n"])
def test_f2_a_line_end_inside_the_key_says_more_than_one_line(tmp_path: Path, mid: bytes) -> None:
    """Kills mutant R04 (a lone CR no longer counts as a line end: the file is still refused, but with the text 'holds
    no key', which sends the user to the wrong fix). Fails on R04 for the lone CR, passes on r7e."""
    with pytest.raises(FileRefused, match="more than one line"):
        _secret(tmp_path, KEY.encode() + mid + b"second-part-aaaaaaaa")


@pytest.mark.parametrize("bom", [b"\xff\xfe", b"\xfe\xff"])
def test_f2_utf16_text_of_either_byte_order_is_named_as_utf16(tmp_path: Path, bom: bytes) -> None:
    """Kills mutant R05 (the big-endian mark not recognised: refused as 'not UTF-8' instead of the helpful UTF-16
    text). Fails on R05 for the big-endian mark, passes on r7e."""
    with pytest.raises(FileRefused, match="UTF-16"):
        _secret(tmp_path, bom + KEY.encode("utf-16-le"))


def test_f2_spaced_drops_spaces_and_tabs_and_only_with_the_flag(tmp_path: Path) -> None:
    """Kills mutant R08 (spaced drops only spaces: a tab in a grouped app password stays and the file is refused).
    Fails on R08, passes on r7e. CONTROL part: without `spaced` a space or tab inside is refused (passes on both)."""
    grouped = b"abcd efgh\tijkl mnop"
    assert _secret(tmp_path, grouped, spaced=True) == "abcdefghijklmnop"
    with pytest.raises(FileRefused):
        _secret(tmp_path, grouped)


# ---- smtp_outbox: dot stuffing and the reply cap, without a network ----


def test_f2_a_message_that_starts_with_a_dot_is_dot_stuffed_on_its_first_line() -> None:
    """Kills mutant S06 (the first line is not doubled: a text that starts with a lone dot line could end the DATA part
    early). Fails on S06, passes on r7e."""
    assert _dot_stuff(b".\r\nrest\r\n") == b"..\r\nrest\r\n.\r\n"
    assert _dot_stuff(b".hidden\r\n.second\r\n") == b"..hidden\r\n..second\r\n.\r\n"
    assert _dot_stuff(b"plain\r\n") == b"plain\r\n.\r\n"  # CONTROL: passes on both


class _Chunks:
    """A socket stand-in that hands out `total` bytes of one endless line in chunks of 4096 and then ends."""

    def __init__(self, total: int) -> None:
        self.left, self.taken = total, 0

    def settimeout(self, t: float) -> None:
        pass

    def recv(self, n: int) -> bytes:
        piece = min(n, self.left)
        self.left -= piece
        self.taken += piece
        return b"x" * piece


def test_f2_a_reply_line_without_an_end_is_cut_off_at_the_cap_not_at_twice_the_cap() -> None:
    """Kills mutant S02 (the cap for an unfinished line doubled): the reader stops after about one cap of bytes and says
    'reply too long'; on S02 it keeps reading up to twice the cap and then ends as 'connection closed'. Fails on S02."""
    sock: Any = _Chunks(3 * _REPLY_MAX_BYTES)
    with pytest.raises(_Closed, match="reply too long"):
        _read_reply(sock, _Budget(5.0), bytearray())
    assert sock.taken <= _REPLY_MAX_BYTES + 4096


# ---- imap_count internals ----


class _Owner:
    def __init__(self, sock: socket.socket, deadline: float, step: float = 5.0) -> None:
        self.sock, self.deadline, self.step_seconds = sock, deadline, step


def test_f2_readline_never_returns_more_than_its_limit() -> None:
    """Kills mutant I16 (the limit of readline not applied: a reader that asks for at most 4 bytes gets the whole
    buffer). Fails on I16, passes on r7e."""
    a, b = socket.socketpair()
    try:
        b.sendall(b"abcdefghij")
        b.close()
        owner: Any = _Owner(a, time.monotonic() + 5)
        r = _DeadlineReader(owner)
        assert r.readline(4) == b"abcd"
        assert r.readline(4) == b"efgh"
        assert r.readline(-1) == b"ij"  # CONTROL: no limit means everything up to the end of the data
    finally:
        a.close()


def test_f2_nothing_is_sent_after_the_total_deadline() -> None:
    """Kills mutant I10 (send without the deadline check): a command written after the total time ran out would still
    leave. Fails on I10 (the bytes arrive and no error is raised), passes on r7e."""
    a, b = socket.socketpair()
    try:
        conn = object.__new__(_BoundedImap)
        conn.sock, conn.deadline, conn.step_seconds = a, time.monotonic() - 1.0, 5.0
        with pytest.raises(ImapTotalTimeout):
            conn.send(b"A1 NOOP\r\n")
        b.setblocking(False)
        with pytest.raises(BlockingIOError):
            b.recv(16)  # nothing arrived
    finally:
        a.close()
        b.close()


@pytest.mark.parametrize(("pause", "expected"), [(1.3, ImapCountError), (0.0, ImapConnectionError)])
def test_f2_a_connection_error_after_the_total_deadline_is_not_repeatable(
    tmp_path: Path, pause: float, expected: type[Exception]
) -> None:
    """Kills mutant I12 (the past-deadline error is the repeatable ImapConnectionError, so a caller would start a second
    whole call after the total time was used up). Fails on I12 for pause 1.3 (total 1 s). The pause 0.0 case is the
    CONTROL (a reset inside the time is repeatable: ImapConnectionError); it passes on both."""
    certs = _Certs(tmp_path)
    srv = FakeImap(certs.cert, certs.key, "localhost", {"INBOX": []})
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    ctx = ssl.create_default_context(cafile=str(certs.cert))
    try:
        s = ImapSettings(
            "localhost",
            "reader-user",
            pw,
            port=srv.port,
            folders=("INBOX",),
            timeout_seconds=5.0,
            total_seconds=1.0,
            ssl_context=ctx,
        )

        def work(m: Any) -> dict[str, dict[str, int]]:
            time.sleep(pause)
            raise ConnectionResetError

        with pytest.raises(expected) as info:
            _session(s, work)
        assert type(info.value) is expected  # ImapConnectionError is a subclass of ImapCountError: exact class
    finally:
        srv.close()


# ---- jsonread ----


def test_f2_a_json_text_nested_too_deeply_is_a_value_error_not_a_recursion_error() -> None:
    """Kills mutant V02 (RecursionError not mapped). Fails on V02, passes on r7e."""
    with pytest.raises(JsonTooDeep):
        loads_bounded("[" * 200_000)
    assert loads_bounded("[1, 2]") == [1, 2]  # CONTROL


# ---- load_driver: an answer protects the run from the stop (r7e L05) ----


def test_f2_connection_errors_after_an_answer_never_set_the_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills mutant L05 (`if reached:` without the answered check): after one answer, 2 x threads connection errors
    would stop the run. Fails on L05, passes on r7e. CONTROL part: with no answer the same errors do stop it."""
    import multiprocessing

    errors = multiprocessing.get_context("spawn").Value("i", 0)
    stop, answered = threading.Event(), threading.Event()
    monkeypatch.setattr(load_driver, "_STOP", stop)
    monkeypatch.setattr(load_driver, "_ANSWERED", answered)
    monkeypatch.setattr(load_driver, "_ERRORS", errors)
    monkeypatch.setattr(load_driver, "_STOP_LIMIT", 3)
    for _ in range(2):
        assert load_driver._note_attempt(None) is False
    answered.set()
    for _ in range(5):
        assert load_driver._note_attempt(None) is False
    assert not stop.is_set()
    answered.clear()
    errors.value = 0
    assert [load_driver._note_attempt(None) for _ in range(3)] == [False, False, True]
    assert stop.is_set()


# ---- run_real_check: every secret file is read before the Start question ----
# CONTROL for every test below: each passes on r7e (no code changed); the mutants named were really run and fail them.


def _secret_files(tmp_path: Path, **bad: str) -> Any:
    from types import SimpleNamespace

    def one(name: str, text: str) -> Path:
        p = tmp_path / name
        if name in bad:
            if bad[name] != "missing":
                p.write_text(bad[name], encoding="utf-8")
        else:
            p.write_text(text, encoding="utf-8")
        return p

    hs = SimpleNamespace(key_file=one("hs", "key-abcdefghij\n"))
    pr = SimpleNamespace(password_file=one("pw", "a made up pass word\n"))
    boxes = [
        SimpleNamespace(password_file=one("m1", "box one pass\n")),
        SimpleNamespace(password_file=one("m2", "box two pass\n")),
    ]
    return hs, pr, boxes


def test_f3_good_secret_files_pass_and_a_spaced_password_is_allowed(tmp_path: Path) -> None:
    """CONTROL: passes on r7e; mutant C03 (spaced ignored in the pre-check) fails it."""
    import run_real_check as rrc

    hs, pr, boxes = _secret_files(tmp_path)
    rrc.check_secret_files(hs, pr, boxes)


@pytest.mark.parametrize(
    ("which", "setting"),
    [
        ("hs", "DESK_HUBSPOT_KEY_FILE"),
        ("pw", "DESK_SMTPP_PASSWORD_FILE"),
        ("m1", "REAL_IMAP_1_PASSWORD_FILE"),
        ("m2", "REAL_IMAP_2_PASSWORD_FILE"),
    ],
)
@pytest.mark.parametrize("problem", ["missing", "", "two\nlines\n"])
def test_f3_a_bad_secret_file_is_refused_by_the_name_of_its_setting(
    tmp_path: Path, which: str, setting: str, problem: str
) -> None:
    """CONTROL: passes on r7e; mutants C02 (mailbox passwords), C06 (hubspot key), C07 (smtp password) fail it."""
    import run_real_check as rrc

    hs, pr, boxes = _secret_files(tmp_path, **{which: problem})
    with pytest.raises(ValueError, match=setting) as e:
        rrc.check_secret_files(hs, pr, boxes)
    assert str(tmp_path) not in str(e.value)


def test_f3_a_spaced_hubspot_key_is_refused(tmp_path: Path) -> None:
    """CONTROL: passes on r7e (a key is one plain word; a password may have spaces)."""
    import run_real_check as rrc

    hs, pr, boxes = _secret_files(tmp_path, hs="key abcdefghij\n")
    with pytest.raises(ValueError, match="DESK_HUBSPOT_KEY_FILE"):
        rrc.check_secret_files(hs, pr, boxes)


def test_f3_an_os_error_from_the_reader_is_a_refusal_naming_the_setting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL: passes on r7e; mutant C04 (OSError not mapped) fails it. The reader maps its own OSErrors, so this
    stands in for one it did not."""
    import run_real_check as rrc

    def boom(*_a: object, **_k: object) -> str:
        raise OSError("disk detail that must not be shown")

    monkeypatch.setattr(rrc, "read_secret_line", boom)
    with pytest.raises(ValueError, match="DESK_X_FILE") as e:
        rrc.check_one_secret("DESK_X_FILE", tmp_path / "x", "key", "key")
    assert "disk detail" not in str(e.value)


def test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CONTROL: passes on r7e; mutant C05 (scrub removed in main's refusal line) fails it."""
    import run_real_check as rrc

    seen: list[str] = []

    def leaky(hs: Any, _pr: Any, _boxes: Any) -> None:
        seen.append(str(hs.key_file))
        raise ValueError("odd failure " + str(hs.key_file))

    monkeypatch.setattr(rrc, "check_secret_files", leaky)
    rc = rrc.main(["--dry-fakes", "--assume-yes"])
    out = capsys.readouterr().out
    assert rc == rrc.EXIT_REFUSED and seen
    assert seen[0] not in out and "<value>" in out


# ---- imap_count and smtp_outbox: the rows of the pass 7 table (MAIL7-MUTANTS-r7c.md) that survived on r7c ----


def test_f4_a_read_after_the_total_deadline_ends_even_when_bytes_are_waiting() -> None:
    """Kills mutant A01 (an expired deadline still gets a 1 ms read: bytes already waiting would be taken). Fails on
    A01, passes on r7e."""
    a, b = socket.socketpair()
    try:
        b.sendall(b"* OK late\r\n")
        owner: Any = _Owner(a, time.monotonic() - 1.0)
        with pytest.raises(ImapTotalTimeout):
            _DeadlineReader(owner).readline()
    finally:
        a.close()
        b.close()


def test_f4_readline_with_a_limit_returns_at_the_limit_while_the_server_is_still_sending() -> None:
    """Kills mutant A04 (no stop at the limit: it keeps reading until a line end or the end of the data, so a line
    without an end grows without bound). The peer stays open and sends no line end: the right answer is the first 4
    bytes at once. Fails on A04 (it waits for the step time-out), passes on r7e."""
    a, b = socket.socketpair()
    try:
        b.sendall(b"abcdefghij")
        owner: Any = _Owner(a, time.monotonic() + 5, step=0.5)
        start = time.monotonic()
        assert _DeadlineReader(owner).readline(4) == b"abcd"
        assert time.monotonic() - start < 0.4
    finally:
        a.close()
        b.close()


def test_f4_read_waits_for_all_the_bytes_it_was_asked_for() -> None:
    """Kills mutant A14 (a read of N bytes returns after the first piece). The bytes arrive in two pieces. Fails on
    A14, passes on r7e."""
    a, b = socket.socketpair()

    def later() -> None:
        time.sleep(0.3)
        b.sendall(b"def")

    t = threading.Thread(target=later)
    try:
        b.sendall(b"abc")
        t.start()
        owner: Any = _Owner(a, time.monotonic() + 5)
        assert _DeadlineReader(owner).read(6) == b"abcdef"
    finally:
        t.join()
        a.close()
        b.close()


def test_f4_a_send_that_blocks_ends_at_the_total_deadline_not_at_the_step() -> None:
    """Kills mutant A07 (send uses the plain step as its time-out). The peer never reads, so a big write blocks; the
    total is 0.6 s and the step 6 s. Fails on A07 (it lasts about 6 s), passes on r7e."""
    a, b = socket.socketpair()
    try:
        conn = object.__new__(_BoundedImap)
        conn.sock, conn.deadline, conn.step_seconds = a, time.monotonic() + 0.6, 6.0
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            conn.send(b"x" * 50_000_000)
        assert time.monotonic() - start < 3.0
    finally:
        a.close()
        b.close()


def test_f4_the_literal_cap_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kills mutant A12 (the cap itself is refused: >= instead of >). A part of exactly the cap is read, one byte more
    is refused. Fails on A12, passes on r7e."""
    import lead_desk.imap_count as ic

    monkeypatch.setattr(ic, "IMAP_LITERAL_MAX_BYTES", 10)
    a, b = socket.socketpair()
    try:
        b.sendall(b"0123456789")
        conn = object.__new__(_BoundedImap)
        conn.sock, conn.deadline, conn.step_seconds = a, time.monotonic() + 5, 5.0
        conn.file = _DeadlineReader(conn)
        assert conn.read(10) == b"0123456789"
        with pytest.raises(ImapCountError, match="too long"):
            conn.read(11)
    finally:
        a.close()
        b.close()


def test_f4_a_reply_whose_earlier_lines_plus_the_waiting_bytes_pass_the_cap_is_cut_off() -> None:
    """Kills mutant B02 (the cap for waiting bytes ignores the lines already taken). The first line of a multi-line
    reply uses nearly the whole cap; then bytes without a line end arrive. Fails on B02 (it reads up to a whole cap
    more), passes on r7e."""
    sock: Any = _Chunks(3 * _REPLY_MAX_BYTES)
    buf = bytearray(b"250-" + b"y" * (_REPLY_MAX_BYTES - 300) + b"\r\n")
    with pytest.raises(_Closed, match="reply too long"):
        _read_reply(sock, _Budget(5.0), buf)
    assert sock.taken <= 2 * 4096


def test_f4_a_login_is_not_sent_when_the_total_time_ran_out_during_the_protocol_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROL for mutant A10 (the check before the login removed). A10 is EQUIVALENT: the send step has the same
    check, so with or without the first one nothing is sent and the error is the same. This test passes on r7e AND on
    A10 (run); it pins the observable behaviour."""
    import lead_desk.imap_count as ic

    certs = _Certs(tmp_path)
    srv = FakeImap(certs.cert, certs.key, "localhost", {"INBOX": []})
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    ctx = ssl.create_default_context(cafile=str(certs.cert))
    real = ic.require_modern_protocol

    def slow(sock: Any, name: str) -> None:
        real(sock, name)
        time.sleep(1.3)

    monkeypatch.setattr(ic, "require_modern_protocol", slow)
    try:
        s = ImapSettings(
            "localhost",
            "reader-user",
            pw,
            port=srv.port,
            folders=("INBOX",),
            timeout_seconds=5.0,
            total_seconds=1.0,
            ssl_context=ctx,
        )
        with pytest.raises(ImapTotalTimeout):
            _session(s, lambda m: {})
    finally:
        srv.close()


def test_f5_the_live_model_client_never_follows_a_redirect() -> None:
    """Kills mutant F02 (the redirect handler of live_claude hands back a new request: the key header would go to
    another host). Fails on F02, passes on r7e."""
    import urllib.request

    from lead_desk.live_claude import _NoRedirect

    req = urllib.request.Request("https://example.test/v1/x", headers={"x-api-key": "made-up-key-1234"})
    assert _NoRedirect().redirect_request(req, None, 302, "Found", {}, "https://example.test/other") is None


def test_f5_a_send_timeout_that_is_not_finite_is_refused_before_anything_else() -> None:
    """Kills mutant C05 (the finite check of the send timeout removed). The refusal is the first line of send, so an
    object that was never set up still gives the right error; on C05 the next line fails with another error.
    Fails on C05, passes on r7e."""
    box = object.__new__(SmtpProviderOutbox)
    for bad in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError, match="finite"):
            box.send("lead-key", "a@example.test", "subject", "body", bad)


def test_f5_every_hubspot_read_gets_only_the_time_that_is_left() -> None:
    """Kills mutant G03 (the per-read time-out is not set from the time left). Each read1 call must see a socket
    time-out no larger than the time left of the total. Fails on G03 (no time-out is set), passes on r7e."""
    from types import SimpleNamespace

    from lead_desk.crm_hubspot import HubspotCrm

    seen: list[float] = []
    chunks = [b'{"a":', b"1}", b""]

    sock = SimpleNamespace(settimeout=seen.append)
    response = SimpleNamespace(fp=SimpleNamespace(raw=SimpleNamespace(_sock=sock)), read1=lambda _n: chunks.pop(0))
    assert HubspotCrm._read(response, time.monotonic() + 7.0) == {"a": 1}
    assert len(seen) == 3 and all(0 < t <= 7.0 for t in seen)


def test_f5_a_certificate_file_with_a_byte_order_mark_is_read() -> None:
    """Kills mutant T01 (the byte-order mark is not removed: the BEGIN line then looks non-ASCII and the file is
    refused). Fails on T01, passes on r7e."""
    from lead_desk.tls_trust import _ascii_outside_blocks

    text = b"\xef\xbb\xbf-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n"
    assert _ascii_outside_blocks(text) is not None


def test_f5_an_end_line_with_a_non_ascii_byte_is_refused_even_when_it_is_indented() -> None:
    """Kills mutant T02 (an END line is found only at the start of the line). Fails on T02, passes on r7e."""
    from lead_desk.tls_trust import _ascii_outside_blocks

    assert _ascii_outside_blocks(b"  -----END CERTIFICATE-----\xff\n") is None
    assert _ascii_outside_blocks(b"# note \xff\n") == "# note \n"  # CONTROL: outside a block a stray byte is dropped


# ---- the look-up of a host name is inside the total time limit (lead_desk.netconnect) ----


class _HangingLookup:
    """Replaces socket.getaddrinfo with a look-up that does not return until released: a name server that is silent."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.release = threading.Event()
        monkeypatch.setattr(socket, "getaddrinfo", self._wait)

    def _wait(self, *_a: object, **_k: object) -> list[Any]:
        self.release.wait(30)
        return []


def test_f6_a_name_look_up_that_never_answers_ends_at_the_time_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """FIX TEST (coordinator item 2a): before r7f the look-up of the host name had no time limit (create_connection
    bounds only the connect). FAILS on r7e (the call waits for the look-up)."""
    from lead_desk.netconnect import connect_bounded

    hang = _HangingLookup(monkeypatch)
    try:
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            connect_bounded("name.example.test", 25, 0.5)
        assert time.monotonic() - start < 2.5
    finally:
        hang.release.set()


def test_f6_a_bounded_connect_reaches_a_listener_and_passes_a_lookup_error_on() -> None:
    """CONTROL: passes on r7e and r7f in effect (a plain connect works; a failed look-up is an OSError)."""
    from lead_desk.netconnect import connect_bounded

    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    try:
        conn = connect_bounded("127.0.0.1", srv.getsockname()[1], 2.0)
        conn.close()
    finally:
        srv.close()
    with pytest.raises(OSError):
        connect_bounded("no-such-name." + "inva" + "lid", 9, 2.0)


def test_f6_the_mailbox_read_ends_at_the_total_time_when_the_name_look_up_hangs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FIX TEST: the total is 1 s, the step 5 s; the look-up never answers. FAILS on r7e (waits for the look-up)."""
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    hang = _HangingLookup(monkeypatch)
    try:
        s = ImapSettings(
            "name.example.test",
            "reader-user",
            pw,
            port=993,
            folders=("INBOX",),
            timeout_seconds=5.0,
            total_seconds=1.0,
        )
        start = time.monotonic()
        with pytest.raises(ImapTotalTimeout):
            _session(s, lambda m: {})
        assert time.monotonic() - start < 3.5
    finally:
        hang.release.set()


def test_f6_a_mail_send_ends_at_its_time_limit_when_the_name_look_up_hangs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FIX TEST: send time limit 1 s, look-up silent: the send is refused as unreachable in time, nothing was sent.
    FAILS on r7e (waits for the look-up)."""
    from lead_desk.contract import SendUnreachable

    certs = _Certs(tmp_path)
    ctx = ssl.create_default_context(cafile=str(certs.cert))
    box = _provider(tmp_path, 587, ctx, host="name.example.test")
    hang = _HangingLookup(monkeypatch)
    try:
        start = time.monotonic()
        with pytest.raises(SendUnreachable):
            box.send("K-1", "ada@example.test", "Hi", "Body", 1.0)
        assert time.monotonic() - start < 3.5
    finally:
        hang.release.set()
