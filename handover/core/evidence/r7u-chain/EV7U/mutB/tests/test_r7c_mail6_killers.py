"""Round 7C, mail pass 6, findings D05, D11, D20 (made-up data, loopback sockets only). D05: a mailbox connection
refused for its TLS version gets no LOGOUT and no LOGIN. D11: an SMTP connection refused for its TLS version is closed
at once. D20: a settings name holding a no-break space is refused."""

from __future__ import annotations

import socket
import ssl
import time
from pathlib import Path

import pytest
from support import script_module, skip_or_fail_without_openssl

from demo_only.fake_imap import FakeImap
from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp, make_cert
from lead_desk import smtp_provider as sp
from lead_desk.contract import SendRefused
from lead_desk.imap_count import ImapCountError as Err
from lead_desk.imap_count import ImapSettings, counts_by_key
from lead_desk.smtp_outbox import _Budget
from lead_desk.tls_trust import CaFileRefused

HOST = "localhost"


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# no close after a refused TLS version, or a no-break space accepted.
def test_m6_d11_a_connection_refused_for_its_tls_version_is_closed_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    made = make_cert(tmp_path, HOST)
    if made is None:
        skip_or_fail_without_openssl()
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    srv = FakeSmtp(made[0], made[1], HOST, implicit_tls=True)
    closed: list[bool] = []
    real_close = ssl.SSLSocket.close

    def spy(self: ssl.SSLSocket) -> None:
        closed.append(True)
        real_close(self)

    def refuse(conn: ssl.SSLSocket, name: str) -> None:
        raise CaFileRefused("forced")

    try:
        s = sp.ProviderSettings(
            HOST,
            srv.port,
            "sender-user",
            pw,
            "sender@example.test",
            ("a@example.test",),
            5,
            security="ssl",
            timeout_seconds=3.0,
        )
        box = sp.SmtpProviderOutbox(s, ssl.create_default_context(cafile=str(made[0])))
        monkeypatch.setattr(sp, "require_modern_protocol", refuse)
        monkeypatch.setattr(ssl.SSLSocket, "close", spy)
        sock = socket.create_connection((HOST, srv.port), timeout=3)
        with pytest.raises(SendRefused):
            box._wrap(sock, _Budget(3.0))
        assert closed, "the refused TLS connection was left open"
    finally:
        srv.close()


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# no close after a refused TLS version, or a no-break space accepted.
def test_m6_d20_a_config_name_with_a_no_break_space_is_refused(tmp_path: Path) -> None:
    rrc = script_module("run_real_check")

    cfg = tmp_path / "c.env"
    cfg.write_text("REAL_PERSONS\xa0=8\n", encoding="utf-8")
    with pytest.raises(ValueError, match="config line 1"):
        rrc.load_env(cfg)


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# no close after a refused TLS version, or a no-break space accepted.
def test_m6_d05_a_mailbox_connection_refused_for_its_tls_version_gets_no_logout_either(tmp_path: Path) -> None:

    made = make_cert(tmp_path, HOST)
    if made is None:
        skip_or_fail_without_openssl()
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    srv = FakeImap(made[0], made[1], HOST, {"INBOX": ["RUN1-L1"]})
    try:
        try:
            srv._ctx.minimum_version = ssl.TLSVersion.TLSv1
            srv._ctx.maximum_version = ssl.TLSVersion.TLSv1_1
            srv._ctx.set_ciphers("ALL:@SECLEVEL=0")
        except (ValueError, ssl.SSLError):
            pytest.skip("this OpenSSL cannot make a TLS 1.1 only test server")
        c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        c.load_verify_locations(cafile=str(made[0]))
        c.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        c.set_ciphers("ALL:@SECLEVEL=0")
        s = ImapSettings(HOST, srv.user, pw, port=srv.port, folders=("INBOX",), timeout_seconds=3.0, ssl_context=c)
        with pytest.raises(Err):
            counts_by_key(s, "RUN1-")
        time.sleep(0.3)
        assert "LOGOUT" not in srv.commands and "LOGIN" not in srv.commands, srv.commands
    finally:
        srv.close()
