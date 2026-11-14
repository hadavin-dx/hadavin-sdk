"""Round 7, mail path: every check that stands between a mail login and a server must hold on the REAL path.

Each test goes through the real classes and a real loopback socket (a counting listener or a scripted TLS fake), and
looks at what the SERVER saw (commands, LOGIN lines, connection count), not only at the exception. The first line of
each test names the check it pins. Made-up data only; loopback only; fake secrets built from parts."""

from __future__ import annotations

import argparse
import ast
import os
import socket
import ssl
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from support import run_python, skip_or_fail_without_openssl  # placed with the other test helpers

from demo_only.fake_imap import FakeImap
from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp, make_cert
from lead_desk import imap_count
from lead_desk.constants import IMAP_LITERAL_MAX_BYTES, MAIL_SPAM_FOLDER
from lead_desk.contract import SendRefused
from lead_desk.imap_count import (
    ImapCountError,
    ImapSettingRefused,
    ImapSettings,
    ImapTotalTimeout,
    counts_by_key,
    quote_user,
)
from lead_desk.regfile import FileRefused, read_secret_line
from lead_desk.smtp_provider import ProviderSettings, SettingRefused, SmtpProviderOutbox, read_secret_file
from lead_desk.tls_trust import CaFileRefused, new_verifying_context, require_verifying

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
HOST = "localhost"  # the certificates name it; verification stays ON
INBOXES = ("inbox-a@example.test", "inbox-b@example.test")
LEAD, SUBJECT, BODY = "ada@example.test", "Thanks, Ada", "Hi Ada."
PW = FAKE_PASSWORD


class Certs:
    def __init__(self, tmp: Path, host: str = HOST) -> None:
        made = make_cert(tmp, host)
        if made is None:
            skip_or_fail_without_openssl()
        self.cert, self.key = made
        self.ctx = ssl.create_default_context(cafile=str(self.cert))  # trusts the test certificate; checks the name


@pytest.fixture
def certs(tmp_path: Path) -> Certs:
    return Certs(tmp_path)


@pytest.fixture
def wrong_name(tmp_path: Path) -> Certs:
    """A certificate that names other.test while the client connects to localhost; the client's context trusts it."""
    d = tmp_path / "other"
    d.mkdir()
    return Certs(d, "other.test")


@pytest.fixture
def pwfile(tmp_path: Path) -> Path:
    p = tmp_path / "pw.txt"
    p.write_text(PW + "\n", encoding="utf-8")
    return p


@pytest.fixture
def servers() -> Iterator[list[Any]]:
    made: list[Any] = []
    yield made
    for s in made:
        s.close()


class Counting:
    """A plain TCP listener on this computer that counts connections and closes each at once."""

    def __init__(self) -> None:
        self._s = socket.socket()
        self._s.bind(("127.0.0.1", 0))
        self._s.listen(8)
        self._s.settimeout(0.1)
        self.port = int(self._s.getsockname()[1])
        self.count = 0
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                c, _ = self._s.accept()
            except OSError:
                continue
            self.count += 1
            c.close()

    def close(self) -> None:
        self._stop.set()
        self._t.join(2)
        self._s.close()


@pytest.fixture
def counting() -> Iterator[Counting]:
    c = Counting()
    yield c
    c.close()


def weaken(ctx: ssl.SSLContext, how: str) -> None:
    if how == "no_hostname":
        ctx.check_hostname = False
    elif how == "none":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:  # "optional": the name check stays on, the chain check is weaker
        ctx.verify_mode = ssl.CERT_OPTIONAL


WEAKENINGS = ["no_hostname", "none", "optional"]


def provider(port: int, pwfile: Path, security: str, ctx: ssl.SSLContext, user: str = "sender-user") -> Any:
    s = ProviderSettings(
        HOST, port, user, pwfile, "sender@example.test", INBOXES, 5, security=security, timeout_seconds=3.0
    )
    return SmtpProviderOutbox(s, ctx)


# -- M04: a chain check that is only "optional" is refused even when the name check is on ---------------------------


def test_m04_optional_chain_check_with_name_check_on_is_refused() -> None:
    ctx = ssl.create_default_context()
    ctx.verify_mode = ssl.CERT_OPTIONAL
    assert ctx.check_hostname is True
    with pytest.raises(CaFileRefused):
        require_verifying(ctx, "ctx")


def test_m04_the_outbox_and_the_mailbox_reader_refuse_it_too(pwfile: Path, servers: list[Any]) -> None:
    ctx = ssl.create_default_context()
    ctx.verify_mode = ssl.CERT_OPTIONAL
    with pytest.raises(SettingRefused):
        provider(1, pwfile, "ssl", ctx)
    s = ImapSettings(HOST, "reader-user", pwfile, port=1, timeout_seconds=1.0, ssl_context=ctx)
    with pytest.raises(ImapCountError):
        counts_by_key(s, "RUN1-")


# -- M18a: SMTP send re-checks a context weakened after the object was built ---------------------------------------


@pytest.mark.parametrize("security", ["ssl", "starttls"])
@pytest.mark.parametrize("how", WEAKENINGS)
def test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection(
    pwfile: Path, counting: Counting, security: str, how: str
) -> None:
    ctx = new_verifying_context()
    ob = provider(counting.port, pwfile, security, ctx)
    weaken(ctx, how)
    with pytest.raises(SendRefused):
        ob.send("RUN1-L1", LEAD, SUBJECT, BODY, 3.0)
    assert (ob.attempts, ob.sent) == (0, 0)
    assert counting.count == 0  # no connection at all: a mail login never had a chance to leave


# -- M18b: _wrap re-checks, even when the context is weakened after send() looked at it -----------------------------


@pytest.mark.parametrize("security", ["ssl", "starttls"])
@pytest.mark.parametrize("how", WEAKENINGS)
def test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login(
    wrong_name: Certs, pwfile: Path, servers: list[Any], monkeypatch: pytest.MonkeyPatch, security: str, how: str
) -> None:
    srv = FakeSmtp(wrong_name.cert, wrong_name.key, HOST, "ok", security == "ssl")
    servers.append(srv)
    ctx = ssl.create_default_context(cafile=str(wrong_name.cert))  # the chain is trusted, the name is wrong
    ob = provider(srv.port, pwfile, security, ctx, srv.user)
    real_connect = ob._connect

    def connect_then_weaken(budget: Any) -> Any:
        sock = real_connect(budget)  # send() has already looked at the context: it was strong then
        weaken(ctx, how)
        return sock

    monkeypatch.setattr(ob, "_connect", connect_then_weaken)
    with pytest.raises(SendRefused):
        ob.send("RUN1-L2", LEAD, SUBJECT, BODY, 3.0)
    assert "AUTH" not in srv.commands and not srv.messages  # the wrong-name server never saw a login


def test_m18b_control_the_same_server_with_a_strong_context_is_refused_as_unreachable(
    wrong_name: Certs, pwfile: Path, servers: list[Any]
) -> None:
    """Without the weakening the wrong-name certificate is refused by the name check: so the test above would show a
    login if the re-check in _wrap were missing."""
    srv = FakeSmtp(wrong_name.cert, wrong_name.key, HOST, "ok", True)
    servers.append(srv)
    ob = provider(srv.port, pwfile, "ssl", ssl.create_default_context(cafile=str(wrong_name.cert)), srv.user)
    with pytest.raises(Exception):
        ob.send("RUN1-L3", LEAD, SUBJECT, BODY, 3.0)
    assert "AUTH" not in srv.commands


# -- the same re-check for the mailbox reader --------------------------------------------------------------------


@pytest.mark.parametrize("how", WEAKENINGS)
def test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login(
    wrong_name: Certs, pwfile: Path, servers: list[Any], how: str
) -> None:
    srv = FakeImap(wrong_name.cert, wrong_name.key, HOST, {"INBOX": ["RUN1-L1"]})
    servers.append(srv)
    ctx = ssl.create_default_context(cafile=str(wrong_name.cert))
    s = ImapSettings(HOST, srv.user, pwfile, port=srv.port, timeout_seconds=3.0, ssl_context=ctx)
    weaken(ctx, how)
    with pytest.raises(ImapCountError):
        counts_by_key(s, "RUN1-")
    assert srv.logins == [] and srv.login_lines == []  # no LOGIN line reached the wrong-name server


# -- M20, M23, M29, M30 --------------------------------------------------------------------------------------------


def _smtp_env(pwfile: Path) -> dict[str, str]:
    return {
        "DESK_SMTPP_HOST": HOST,
        "DESK_SMTPP_USER": "sender-user",
        "DESK_SMTPP_PASSWORD_FILE": str(pwfile),
        "DESK_SMTPP_FROM": "sender@example.test",
        "DESK_SMTPP_RECIPIENTS": ",".join(INBOXES),
        "DESK_SMTPP_MAX_SENDS": "5",
    }


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities(pwfile: Path, blank: str) -> None:
    env = _smtp_env(pwfile) | {"DESK_SMTPP_CA_FILE": blank}
    with pytest.raises(SettingRefused, match="DESK_SMTPP_CA_FILE is empty"):
        ProviderSettings.from_env(env)


@pytest.mark.parametrize("blank", ["", "  "])
def test_m23_a_blank_mailbox_ca_file_setting_is_refused(blank: str) -> None:
    import run_real_check as rrc

    env = {"REAL_IMAP_1_USER": "reader-user", "REAL_IMAP_1_PASSWORD_FILE": "/nowhere", "REAL_IMAP_1_CA_FILE": blank}
    with pytest.raises(ValueError, match="REAL_IMAP_1_CA_FILE is empty"):
        rrc.imap_settings(env)


def _probe(monkeypatch: pytest.MonkeyPatch, token: str, port: int) -> int:
    import hubspot_probe as hp

    monkeypatch.setenv("R7_PROBE_TOKEN", token)
    args = ["--yes-spend-calls", str(hp.PLANNED_CALLS), "--token-env", "R7_PROBE_TOKEN"]
    return int(hp.main([*args, "--dry-run", f"http://127.0.0.1:{port}"], sleep=lambda _: None))


def test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection(
    monkeypatch: pytest.MonkeyPatch, counting: Counting
) -> None:
    assert _probe(monkeypatch, "αβγ-abcdefgh", counting.port) == 2
    assert counting.count == 0


@pytest.mark.parametrize("tail", [" ", "\x0b", "\x0c", " "])
def test_f2_a_token_ending_in_a_non_ascii_space_or_vertical_tab_is_refused_with_no_connection(
    monkeypatch: pytest.MonkeyPatch, counting: Counting, tail: str
) -> None:
    assert _probe(monkeypatch, "pat-na1-0000-1111" + tail, counting.port) == 2
    assert counting.count == 0


@pytest.mark.parametrize("user", ["αβ@example.invalid", "sender x", "ü"])
def test_m30_a_non_ascii_smtp_user_is_refused_where_the_settings_are_made(pwfile: Path, user: str) -> None:
    with pytest.raises(SettingRefused):
        ProviderSettings(HOST, 25, user, pwfile, "sender@example.test", INBOXES, 5)


# -- F1: the mailbox user -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("user", ["", " ", "   ", " a", "a ", "a\nb", "a\x00b", "a\tb", "αβ", "a b"])
def test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made(pwfile: Path, user: str) -> None:
    with pytest.raises(ImapSettingRefused):
        ImapSettings(HOST, user, pwfile)


def test_f1_run_real_check_refuses_a_bad_user_before_any_connection(pwfile: Path) -> None:
    import run_real_check as rrc

    env = {"REAL_IMAP_1_USER": "a\nb", "REAL_IMAP_1_PASSWORD_FILE": str(pwfile)}
    with pytest.raises(ValueError, match="plain printable ASCII"):
        rrc.imap_settings(env)


@pytest.mark.parametrize("user", ["reader user", 'rea"der', "rea\\der", "rea{3}der", "(rea)der", "a b c"])
def test_f1_the_user_goes_to_the_server_as_one_quoted_word(
    certs: Certs, pwfile: Path, servers: list[Any], user: str
) -> None:
    srv = FakeImap(certs.cert, certs.key, HOST, {"INBOX": ["RUN1-L1"], MAIL_SPAM_FOLDER: []})
    srv.user = user
    servers.append(srv)
    s = ImapSettings(HOST, user, pwfile, port=srv.port, timeout_seconds=3.0, ssl_context=certs.ctx)
    assert counts_by_key(s, "RUN1-")["INBOX"] == {"RUN1-L1": 1}
    assert srv.logins == [(user, PW)]
    assert srv.login_lines[0].startswith("LOGIN " + quote_user(user) + " ")  # the raw line: quoted, one word


def test_f1_quote_user_escapes_backslash_and_quote() -> None:
    assert quote_user('a"b\\c d') == '"a\\"b\\\\c d"'


# -- F2: secret files and values drop ASCII white space only -------------------------------------------------------


@pytest.mark.parametrize("tail", [" ", "\x0b", "\x0c", " ", "\x85"])
def test_f2_the_smtp_password_file_with_a_trailing_odd_space_is_refused(tmp_path: Path, tail: str) -> None:
    p = tmp_path / "pw.txt"
    p.write_text(PW + tail + "\n", encoding="utf-8")
    with pytest.raises(SendRefused):
        read_secret_file(p)


@pytest.mark.parametrize("tail", [" ", "\x0b"])
def test_f2_the_n8n_key_file_with_a_trailing_odd_space_is_refused_with_exit_4(tmp_path: Path, tail: str) -> None:
    p = tmp_path / "key.txt"
    p.write_text("n8n-key-" + "abcdefgh" + tail + "\n", encoding="utf-8")
    env = {"PATH": os.environ.get("PATH", ""), "N8N_API_KEY_FILE": str(p), "PYTHONPATH": str(REPO / "src")}
    r = run_python([str(REPO / "scripts" / "n8n_api.py"), "list"], env, timeout=30)
    assert r.returncode == 4 and "holds no key" in r.stderr and r.stdout == ""


@pytest.mark.parametrize("tail", [" ", "\x0b"])
def test_f2_the_live_key_file_with_a_trailing_odd_space_is_refused_and_no_ledger_line_is_written(
    tmp_path: Path, tail: str
) -> None:
    import run_live_check as rlc

    key, ledger = tmp_path / "key.txt", tmp_path / "ledger.jsonl"
    key.write_text("sk-live-" + "abcdefghij" + tail + "\n", encoding="utf-8")
    problem = rlc.file_problem(argparse.Namespace(key_file=str(key), ledger=str(ledger)))
    assert problem is not None and "holds no key" in problem
    assert not ledger.exists()


def test_f2_ascii_white_space_around_a_key_is_still_dropped(tmp_path: Path) -> None:
    p = tmp_path / "k.txt"
    p.write_bytes(b"\xef\xbb\xbf  key-abcdefghij \t\r\n")
    assert read_secret_line(p, "key", "key") == "key-abcdefghij"


def test_f2_spaced_mode_drops_only_space_and_tab(tmp_path: Path) -> None:
    p = tmp_path / "k.txt"
    p.write_text("abcd efgh\tijkl\n", encoding="utf-8")
    assert read_secret_line(p, "pw", "password", spaced=True) == "abcdefghijkl"
    p.write_text("abcd efgh\n", encoding="utf-8")
    with pytest.raises(FileRefused):
        read_secret_line(p, "pw", "password", spaced=True)


# -- F3: the repr of the settings never shows a path --------------------------------------------------------------


def test_f3_the_settings_print_no_ca_or_stats_path(pwfile: Path) -> None:
    s = ProviderSettings(
        HOST,
        25,
        "sender-user",
        pwfile,
        "sender@example.test",
        INBOXES,
        5,
        ca_file=Path("/secret-place/ca.pem"),
        stats_file=Path("/secret-place/stats.json"),
    )
    assert "secret-place" not in repr(s) and "secret-place" not in str(s)


# -- F4: a context that allows an old TLS version or a null/export cipher is refused -----------------------------


def test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused() -> None:
    assert require_verifying(new_verifying_context(), "ctx")
    assert require_verifying(ssl.create_default_context(), "ctx")  # the library floor is not "below 1.2"
    ctx = ssl.create_default_context()
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    except (ValueError, ssl.SSLError):
        pytest.skip("this OpenSSL does not allow a minimum version of TLS 1.0")
    with pytest.raises(CaFileRefused, match="too weak"):
        require_verifying(ctx, "ctx")


def test_f4_a_context_with_a_security_level_zero_cipher_list_is_refused() -> None:
    ctx = ssl.create_default_context()
    try:
        ctx.set_ciphers("ALL:COMPLEMENTOFALL:@SECLEVEL=0")
    except ssl.SSLError:
        pytest.skip("this OpenSSL does not accept the security level 0 cipher list")
    with pytest.raises(CaFileRefused, match="too weak"):
        require_verifying(ctx, "ctx")


def test_f4_the_outbox_refuses_such_a_context_at_construction(pwfile: Path) -> None:
    ctx = ssl.create_default_context()
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    except (ValueError, ssl.SSLError):
        pytest.skip("this OpenSSL does not allow a minimum version of TLS 1.0")
    with pytest.raises(SettingRefused):
        provider(1, pwfile, "ssl", ctx)


# -- F5: a server-announced reply part above the cap ends the call, on the real path -----------------------------


def test_f5_a_five_megabyte_literal_is_refused_without_being_read(
    certs: Certs, pwfile: Path, servers: list[Any]
) -> None:
    srv = FakeImap(certs.cert, certs.key, HOST, {"INBOX": ["RUN1-L1"]})
    srv.literal_announce = 5 * 1024 * 1024
    servers.append(srv)
    s = ImapSettings(
        HOST, srv.user, pwfile, port=srv.port, folders=("INBOX",), timeout_seconds=3.0, ssl_context=certs.ctx
    )
    with pytest.raises(ImapCountError, match="too long"):
        counts_by_key(s, "RUN1-")
    assert IMAP_LITERAL_MAX_BYTES < srv.literal_announce


def test_f5_the_read_cap_and_the_deadline_hold_on_the_reader_class() -> None:
    m = object.__new__(imap_count._BoundedImap)
    with pytest.raises(ImapCountError, match="too long"):
        m.read(IMAP_LITERAL_MAX_BYTES + 1)
    assert m.deadline == float("-inf")  # the connection is treated as over: no LOGOUT is sent on it
    late = object.__new__(imap_count._BoundedImap)
    late.deadline = 0.0
    with pytest.raises(ImapTotalTimeout):
        late.read(10)


# -- F6: the fakes read bounded lines ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["fake_imap.py", "fake_smtp_tls.py"])
def test_f6_every_readline_in_the_tls_fakes_has_the_size_cap(name: str) -> None:
    tree = ast.parse((REPO / "demo_only" / name).read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "readline"]
    assert calls, name
    for c in calls:
        assert len(c.args) == 1 and ast.unparse(c.args[0]) == "FAKE_LINE_MAX", ast.unparse(c)
