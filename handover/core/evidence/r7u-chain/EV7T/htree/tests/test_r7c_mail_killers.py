"""Round 7C, mail findings M-1 and M-2 (from the mail pass). Real loopback sockets, made-up data only.

M-1: the IMAP total time limit must hold INSIDE one slow greeting, one reply line and one literal (a server that sends
one byte every 0.3 s used to keep the call for 9 to 12 s against a 3 s limit).
M-2: a bad secret file is refused before the Start question, before any connection and before any spend is reserved."""

from __future__ import annotations

import io
import socket
import ssl
import threading
import time
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from support import script_module, skip_or_fail_without_openssl

from demo_only.fake_smtp_tls import FAKE_PASSWORD, make_cert
from lead_desk.imap_count import ImapCountError, ImapSettings, counts_by_key

HOST = "localhost"
TOTAL = 2.0
SLACK = 4.0  # the call must end within total + slack even though the server drips for 10 s


def _drip_server(cert: Path, key: Path, mode: str, stop: threading.Event) -> int:
    sctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    sctx.load_cert_chain(str(cert), str(key))
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(2)

    def serve() -> None:
        try:
            c, _ = srv.accept()
            t = sctx.wrap_socket(c, server_side=True)
            f = t.makefile("rwb", buffering=0)
            if mode == "greeting":  # one byte every 0.3 s, never a line end
                t0 = time.monotonic()
                while not stop.is_set() and time.monotonic() - t0 < 10:
                    f.write(b"*")
                    time.sleep(0.3)
                return
            f.write(b"* OK ready\r\n")
            while not stop.is_set():
                line = f.readline(65536).decode().rstrip("\r\n")
                if not line:
                    return
                tag, _, rest = line.partition(" ")
                word = rest.split(" ", 1)[0].upper()
                if word == "CAPABILITY":
                    f.write(f"* CAPABILITY IMAP4rev1\r\n{tag} OK done\r\n".encode())
                elif word == "LOGIN":
                    f.write(f"{tag} OK login\r\n".encode())
                elif word in ("EXAMINE", "SELECT"):
                    t0 = time.monotonic()
                    if mode == "line":  # one reply line that never ends
                        while not stop.is_set() and time.monotonic() - t0 < 10:
                            f.write(b"*")
                            time.sleep(0.3)
                    else:  # "literal": announces 2000 bytes and delivers 1 byte per 0.3 s
                        f.write(b"* 1 FETCH (BODY[] {2000}\r\n")
                        while not stop.is_set() and time.monotonic() - t0 < 10:
                            f.write(b"x")
                            time.sleep(0.3)
                    return
        except (OSError, ssl.SSLError, ValueError):
            return

    threading.Thread(target=serve, daemon=True).start()
    return int(srv.getsockname()[1])


@pytest.mark.parametrize("mode", ["greeting", "line", "literal"])
def test_m6_the_total_time_limit_holds_inside_one_slow_line_or_literal(mode: str, tmp_path: Path) -> None:
    made = make_cert(tmp_path, HOST)
    if made is None:
        skip_or_fail_without_openssl()
    cert, key = made
    pw = tmp_path / "pw.txt"
    pw.write_text(FAKE_PASSWORD + "\n", encoding="utf-8")
    stop = threading.Event()
    port = _drip_server(cert, key, mode, stop)
    ctx = ssl.create_default_context(cafile=str(cert))
    s = ImapSettings(
        HOST,
        "reader-user",
        pw,
        port=port,
        folders=("INBOX",),
        timeout_seconds=3.0,
        total_seconds=TOTAL,
        ssl_context=ctx,
    )
    t0 = time.monotonic()
    with pytest.raises(ImapCountError):
        counts_by_key(s, "RUN1-")
    took = time.monotonic() - t0
    stop.set()
    assert took < TOTAL + SLACK, f"the call ran {took:.1f} s against a total limit of {TOTAL} s"


def test_m6_real_check_refuses_a_bad_secret_file_before_the_start_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rrc = script_module("run_real_check")

    good = tmp_path / "ok.txt"
    good.write_text("pw-ok-12345678\n", encoding="utf-8")
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"pw-bad-\xc2\xa0-xx12\n")
    for which in ("hs", "smtp", "imap"):
        files = {"hs": good, "smtp": good, "imap": good}
        files[which] = bad
        cfg = tmp_path / f"{which}.env"
        cfg.write_text(
            "\n".join(
                [
                    f"DESK_DB_PATH={tmp_path / ('run-' + which) / 'desk.db'}",
                    f"DESK_HUBSPOT_KEY_FILE={files['hs']}",
                    "DESK_HUBSPOT_MAX_CALLS=100",
                    "REAL_HUBSPOT_READBACK_MAX_CALLS=50",
                    "DESK_SMTPP_HOST=smtp.example.test",
                    "DESK_SMTPP_USER=desk@example.test",
                    f"DESK_SMTPP_PASSWORD_FILE={files['smtp']}",
                    "DESK_SMTPP_FROM=desk@example.test",
                    "DESK_SMTPP_RECIPIENTS=a@example.test,b@example.test",
                    "DESK_SMTPP_MAX_SENDS=50",
                    "REAL_IMAP_1_USER=a@example.test",
                    f"REAL_IMAP_1_PASSWORD_FILE={files['imap']}",
                    "REAL_IMAP_2_USER=b@example.test",
                    f"REAL_IMAP_2_PASSWORD_FILE={files['imap']}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        asked: list[str] = []
        out = io.StringIO()
        monkeypatch.setattr("builtins.input", lambda prompt="": (asked.append(prompt), "n")[1])
        with redirect_stdout(out):
            rc = rrc.main(["--config", str(cfg)])
        assert not asked, f"{which}: the Start? question was reached with a bad secret file"
        assert rc == rrc.EXIT_REFUSED
        assert "\xa0" not in out.getvalue() and "xx12" not in out.getvalue()
