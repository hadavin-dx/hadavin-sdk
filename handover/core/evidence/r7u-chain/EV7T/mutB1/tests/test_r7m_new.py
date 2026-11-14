"""REV7M: tests for what the round 7 review found (TLS floor on the real handshake, IMAP deadline against an endless
run of untagged lines). Real classes, real loopback sockets; look at what the SERVER saw. Made-up data only."""

from __future__ import annotations

import socket
import ssl
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from support import skip_or_fail_without_openssl

from demo_only.fake_imap import FakeImap
from demo_only.fake_smtp_tls import FAKE_PASSWORD, FakeSmtp, make_cert
from lead_desk.imap_count import ImapCountError, ImapSettings, ImapTotalTimeout, counts_by_key
from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox

HOST = "localhost"
INBOXES = ("inbox-a@example.test",)


@pytest.fixture
def cert(tmp_path: Path) -> tuple[Path, Path]:
    made = make_cert(tmp_path, HOST)
    if made is None:
        skip_or_fail_without_openssl()
    return made


@pytest.fixture
def pwfile(tmp_path: Path) -> Path:
    p = tmp_path / "pw.txt"
    p.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    return p


def _old_only(server_ctx: ssl.SSLContext) -> None:
    """Make a server context that speaks nothing newer than TLS 1.1 (skip when this OpenSSL cannot)."""
    try:
        server_ctx.minimum_version = ssl.TLSVersion.TLSv1
        server_ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        server_ctx.set_ciphers("ALL:@SECLEVEL=0")
    except (ValueError, ssl.SSLError):
        pytest.skip("this OpenSSL cannot make a TLS 1.1 only test server")


def _no_floor_client(cafile: Path) -> ssl.SSLContext:
    """A caller context that checks chain and name, names NO minimum version and lowers the security level: the
    library's own floor decides, and the security level cannot be read from a context."""
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    c.load_verify_locations(cafile=str(cafile))
    c.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
    try:
        c.set_ciphers("ALL:!aNULL:@SECLEVEL=0")
    except ssl.SSLError:
        pytest.skip("this OpenSSL does not accept the security level 0 cipher list")
    return c


@pytest.mark.parametrize("security", ["ssl", "starttls"])
def test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2(
    cert: tuple[Path, Path], pwfile: Path, security: str
) -> None:
    srv = FakeSmtp(cert[0], cert[1], HOST, implicit_tls=security == "ssl")
    try:
        _old_only(srv._ctx)
        s = ProviderSettings(
            HOST,
            srv.port,
            "sender-user",
            pwfile,
            "sender@example.test",
            INBOXES,
            5,
            security=security,
            timeout_seconds=3.0,
        )
        box = SmtpProviderOutbox(s, _no_floor_client(cert[0]))
        with pytest.raises(Exception):  # noqa: B017, PT011  (any refusal; the server log below is the proof)
            box.send("K-1", "ada@example.test", "Hi", "Body", 3.0)
        assert "AUTH" not in srv.commands and srv.messages == []
    finally:
        srv.close()


def test_f1_imap_login_never_goes_out_over_a_tls_version_below_1_2(cert: tuple[Path, Path], pwfile: Path) -> None:
    srv = FakeImap(cert[0], cert[1], HOST, {"INBOX": ["RUN1-L1"]})
    try:
        _old_only(srv._ctx)
        s = ImapSettings(
            HOST,
            srv.user,
            pwfile,
            port=srv.port,
            folders=("INBOX",),
            timeout_seconds=3.0,
            ssl_context=_no_floor_client(cert[0]),
        )
        with pytest.raises(ImapCountError):
            counts_by_key(s, "RUN1-")
        assert srv.login_lines == [] and "LOGIN" not in srv.commands
    finally:
        srv.close()


class Endless:
    """A TLS server that logs in and then answers EXAMINE with an endless run of short untagged lines (no literal)."""

    def __init__(self, cert: Path, key: Path) -> None:
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(str(cert), str(key))
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(4)
        self.port = int(self.srv.getsockname()[1])
        self.stop = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        while not self.stop.is_set():
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, c: socket.socket) -> None:
        try:
            f = self.ctx.wrap_socket(c, server_side=True).makefile("rwb", buffering=0)
            f.write(b"* OK ready\r\n")
            while not self.stop.is_set():
                tag, _, rest = f.readline(65536).decode().rstrip("\r\n").partition(" ")
                word = rest.split(" ", 1)[0].upper()
                if word == "CAPABILITY":
                    f.write(f"* CAPABILITY IMAP4rev1\r\n{tag} OK done\r\n".encode())
                elif word == "LOGIN":
                    f.write(f"{tag} OK login\r\n".encode())
                elif word in ("EXAMINE", "SELECT"):
                    end = time.monotonic() + 8
                    while not self.stop.is_set() and time.monotonic() < end:
                        f.write(b"* 1 EXISTS\r\n" * 2000)
                    return
                elif not word:
                    return
        except (OSError, ssl.SSLError, ValueError):
            return

    def close(self) -> None:
        self.stop.set()
        self.srv.close()


@pytest.fixture
def endless(cert: tuple[Path, Path]) -> Iterator[Endless]:
    e = Endless(cert[0], cert[1])
    yield e
    e.close()


def test_f2_an_endless_run_of_untagged_lines_ends_at_the_total_time_limit(
    cert: tuple[Path, Path], pwfile: Path, endless: Endless
) -> None:
    ctx = ssl.create_default_context(cafile=str(cert[0]))
    s = ImapSettings(
        HOST,
        "reader-user",
        pwfile,
        port=endless.port,
        folders=("INBOX",),
        timeout_seconds=3.0,
        total_seconds=1.0,
        ssl_context=ctx,
    )
    t0 = time.monotonic()
    with pytest.raises((ImapTotalTimeout, ImapCountError)):
        counts_by_key(s, "RUN1-")
    assert time.monotonic() - t0 < 4.0, "the call ran far past total_seconds"


def test_sibling_repr_of_settings_shows_no_path() -> None:
    from decimal import Decimal

    from lead_desk.config import LiveSettings
    from lead_desk.crm_hubspot import HubspotSettings

    h = repr(HubspotSettings(Path("/made/up/key"), 5, stats_file=Path("/made/up/stats")))
    ls = repr(
        LiveSettings(
            model="m",
            key_file=Path("/made/up/key"),
            price_in_per_mtok=Decimal(1),
            price_out_per_mtok=Decimal(1),
            price_date="2026-11-01",
            cap_run_usd=Decimal("0.1"),
            cap_total_usd=Decimal("0.1"),
            ledger_path=Path("/made/up/ledger"),
            run_id="r",
        )
    )
    assert "/made/up" not in h
    assert "/made/up" not in ls


def test_f3_a_blank_or_space_padded_smtp_user_is_refused_where_the_settings_are_made(pwfile: Path) -> None:
    from lead_desk.smtp_provider import SettingRefused

    for user in ("  ", " bob", "bob "):
        with pytest.raises(SettingRefused):
            ProviderSettings(HOST, 25, user, pwfile, "sender@example.test", INBOXES, 5)


def test_n8_the_one_context_maker_names_tls_1_2_itself_even_if_the_library_default_is_lower(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills the mutant that drops `ctx.minimum_version = TLSv1_2` from new_verifying_context. On this Python the
    library default is already TLS 1.2, so only a library whose default is lower (simulated here) shows the line."""
    from lead_desk import tls_trust

    real = ssl.create_default_context

    def low_default(*a: Any, **k: Any) -> ssl.SSLContext:
        ctx = real(*a, **k)
        ctx.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        return ctx

    monkeypatch.setattr(tls_trust.ssl, "create_default_context", low_default)
    ctx = tls_trust.new_verifying_context()
    assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname
