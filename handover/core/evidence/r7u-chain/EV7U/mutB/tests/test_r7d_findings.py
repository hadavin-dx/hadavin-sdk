"""Round 7D: the r7c review findings on the money and mail path. Real loopback sockets, made-up data only.

N1  the live model key file is read (with the one secret reader) before the cost lines and before the Start question.
N2  the IMAP total time limit also covers the TCP connect and the TLS handshake; the two time settings are refused
    unless they are finite, above 0 and at most IMAP_SECONDS_MAX (one fixed line, no Python error text).
N3  the final line of an SMTP reply (and a bare code) counts toward the 65,536-byte cap: the cap is accepted, cap + 1
    is refused whole.
N4  the HubSpot probe prints only the status and a category from a fixed list for a refused call, never server text.
N5  the model fake reads its key file with the one secret reader.
M1  the load driver looks for a listener once before it starts any worker, and stops when nothing ever answers.
m3  reset.ps1 uses -LiteralPath everywhere; m4  start_all.ps1 turns a failed start into one fixed line and exit code 4
    (text-level tests: PowerShell itself was NOT run).

Every test here says in its docstring whether it FAILS on the r7c tree (a real fix test) or is a CONTROL (it passes on
r7c and pins behaviour that must stay); a CONTROL names the mutant that kills it."""

from __future__ import annotations

import io
import json
import math
import os
import re
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from support import REPO, free_port, popen_program, run_program, script_module, start_serving, stop_serving

from lead_desk import smtp_outbox
from lead_desk.constants import EXIT_UNREACHABLE, IMAP_SECONDS_MAX
from lead_desk.imap_count import ImapCountError, ImapSettingRefused, ImapSettings, counts_by_key

rrc = script_module("run_real_check")
hp = script_module("hubspot_probe")

# -- N1 -------------------------------------------------------------------------------------------------------------

LIVE_KEY_TEXT = "made-up-key-for-test-only"


def _live_config(tmp_path: Path, key_file: Path) -> Path:
    good = tmp_path / "ok.txt"
    good.write_text("pw-ok-12345678\n", encoding="utf-8")
    lines = [
        f"DESK_DB_PATH={tmp_path / 'run' / 'desk.db'}",
        f"DESK_HUBSPOT_KEY_FILE={good}",
        "DESK_HUBSPOT_MAX_CALLS=100",
        "REAL_HUBSPOT_READBACK_MAX_CALLS=50",
        "DESK_SMTPP_HOST=smtp.example.test",
        "DESK_SMTPP_USER=desk@example.test",
        f"DESK_SMTPP_PASSWORD_FILE={good}",
        "DESK_SMTPP_FROM=desk@example.test",
        "DESK_SMTPP_RECIPIENTS=a@example.test,b@example.test",
        "DESK_SMTPP_MAX_SENDS=50",
        "REAL_IMAP_1_USER=a@example.test",
        f"REAL_IMAP_1_PASSWORD_FILE={good}",
        "REAL_IMAP_2_USER=b@example.test",
        f"REAL_IMAP_2_PASSWORD_FILE={good}",
        "DESK_LIVE_MODEL=model-x",
        f"DESK_LIVE_KEY_FILE={key_file}",
        "DESK_LIVE_PRICE_IN_PER_MTOK=1",
        "DESK_LIVE_PRICE_OUT_PER_MTOK=5",
        "DESK_LIVE_PRICE_DATE=2026-01-01",
        "DESK_LIVE_CAP_RUN_USD=1.25",
        "DESK_LIVE_CAP_TOTAL_USD=3",
        f"DESK_LIVE_LEDGER_PATH={tmp_path / 'ledger'}",
        "DESK_LIVE_RUN_ID=r1",
    ]
    cfg = tmp_path / "live.env"
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cfg


@pytest.mark.parametrize("kind", ["missing", "two_lines", "too_short", "non_ascii", "empty"])
def test_n1_a_bad_live_key_file_is_refused_before_the_cost_lines_and_the_question(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAILS on r7c: the live key was first read after the question. Refused with the setting name and the
    refusal exit code (the review said "exit 1"; every refusal of this script is EXIT_REFUSED)."""
    key = tmp_path / "live-key.txt"
    if kind != "missing":
        key.write_bytes(
            {
                "two_lines": (LIVE_KEY_TEXT + "\nsecond-line-here\n").encode(),
                "too_short": b"abc\n",
                "non_ascii": (LIVE_KEY_TEXT + "\xc2\xa0x").encode("latin-1"),
                "empty": b"\n",
            }[kind]
        )
    asked: list[str] = []
    monkeypatch.setattr("builtins.input", lambda prompt="": (asked.append(prompt), "y")[1])
    out = io.StringIO()
    with redirect_stdout(out):
        rc = rrc.main(["--config", str(_live_config(tmp_path, key)), "--live-model"])
    text = out.getvalue()
    assert rc == rrc.EXIT_REFUSED  # the same exit code as every other refused setting of this script
    assert not asked, "the Start? question was reached with a bad live key file"
    assert "DESK_LIVE_KEY_FILE" in text and "worst case" not in text and "Start?" not in text
    assert str(tmp_path) not in text and "second-line" not in text and LIVE_KEY_TEXT not in text


def test_n1_control_a_good_live_key_file_reaches_the_question(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CONTROL (passes on r7c): a readable key reaches the question and the cost lines. Killed by the mutant that makes
    check_one_secret refuse every file."""
    key = tmp_path / "live-key.txt"
    key.write_text(LIVE_KEY_TEXT + "\n", encoding="utf-8")
    asked: list[str] = []
    monkeypatch.setattr("builtins.input", lambda prompt="": (asked.append(prompt), "n")[1])
    out = io.StringIO()
    with redirect_stdout(out):
        rc = rrc.main(["--config", str(_live_config(tmp_path, key)), "--live-model"])
    assert rc == rrc.EXIT_STOPPED and len(asked) == 1 and "worst case" in out.getvalue()


# -- N5 -------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content", [b"abc\n", b"first-line-12345\nsecond-line-12345\n", b"made-up-\xc3\xa9-key-123456\n"]
)
def test_n5_the_model_fake_reads_its_key_with_the_one_secret_reader(content: bytes, tmp_path: Path) -> None:
    """FAILS on r7c: a short, two-line or non-ASCII key started the fake."""
    key = tmp_path / "key.txt"
    key.write_bytes(content)
    done = run_program(
        [sys.executable, "-m", "demo_only.fake_model_server", "--port", "0", "--key-file", str(key)],
        cwd=REPO,
        env={
            "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LEAD_DESK_PATH_ROOTS": str(tmp_path),
        },
        capture_output=True,
        timeout=30,
    )
    text = done.stdout.decode() + done.stderr.decode()
    assert done.returncode == 4 and text.count("\n") == 1 and "refused: --key-file" in text, text
    assert "Traceback" not in text and str(tmp_path) not in text and "second-line" not in text


# -- N2 -------------------------------------------------------------------------------------------------------------

BAD_SECONDS: list[Any] = [
    float("nan"),
    float("inf"),
    float("-inf"),
    0,
    0.0,
    -1,
    -0.5,
    True,
    False,
    10**400,
    IMAP_SECONDS_MAX + 1,
    1e308,
    "5",
    None,
]


@pytest.mark.parametrize("field", ["timeout_seconds", "total_seconds"])
@pytest.mark.parametrize("value", BAD_SECONDS, ids=repr)
def test_n2_a_time_setting_that_is_not_finite_above_0_and_small_is_one_fixed_refusal(
    field: str, value: Any, tmp_path: Path
) -> None:
    """FAILS on r7c (nothing was checked). One fixed text, never a Python error text, never the value."""
    with pytest.raises(ImapSettingRefused) as e:
        ImapSettings("localhost", "u", tmp_path / "p", **{field: value})
    text = str(e.value)
    assert "must each be a number above 0" in text and "Error" not in text and "\n" not in text
    assert not isinstance(e.value, OverflowError)


@pytest.mark.parametrize("value", [0.001, 1, 30.0, float(IMAP_SECONDS_MAX), IMAP_SECONDS_MAX])
def test_n2_control_the_largest_allowed_value_and_small_values_are_accepted(value: float, tmp_path: Path) -> None:
    """CONTROL (passes on r7c). Killed by the mutant `<=` -> `<` in the check (the maximum itself is refused) and by
    the mutant that drops the lower bound."""
    s = ImapSettings("localhost", "u", tmp_path / "p", timeout_seconds=value, total_seconds=value)
    assert s.total_seconds == value and math.isfinite(s.timeout_seconds)


def _silent_server(stop: threading.Event, drip: bool = False) -> int:
    """Accepts one connection and sends nothing (or, with `drip`, the start of a TLS record and then one byte every
    0.2 s: a handshake that never ends and never goes quiet for a whole step)."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(2)

    def serve() -> None:
        try:
            c, _ = srv.accept()
            c.settimeout(0.2)
            if drip:
                c.sendall(b"\x16\x03\x03\x40\x00")  # a handshake record that claims 16,384 bytes
            t0 = time.monotonic()
            while not stop.is_set() and time.monotonic() - t0 < 12:
                if drip:
                    c.sendall(b"\x00")
                try:
                    c.recv(4096)
                except OSError:
                    pass
                time.sleep(0.2 if drip else 0.05)
            c.close()
        except OSError:
            return
        finally:
            srv.close()

    threading.Thread(target=serve, daemon=True).start()
    return int(srv.getsockname()[1])


@pytest.mark.parametrize("drip", [False, True], ids=["silent", "handshake-drip"])
def test_n2_the_total_time_limit_covers_the_tls_handshake(drip: bool, tmp_path: Path) -> None:
    """FAILS on r7c: the handshake waited for a whole step (30 s) against a 1.5 s total limit; a drip kept it alive
    even longer (the socket time-out restarts with each byte)."""
    pw = tmp_path / "pw.txt"
    pw.write_text("made-up-password-1\n", encoding="utf-8")
    stop = threading.Event()
    port = _silent_server(stop, drip)
    s = ImapSettings("127.0.0.1", "u", pw, port=port, folders=("INBOX",), timeout_seconds=30.0, total_seconds=1.5)
    t0 = time.monotonic()
    with pytest.raises(ImapCountError) as e:
        counts_by_key(s, "RUN1-")
    took = time.monotonic() - t0
    stop.set()
    assert took < 4.0, f"the call ran {took:.1f} s against a total limit of 1.5 s"
    assert "total time limit" in str(e.value) and str(port) not in str(e.value)


def test_n2_the_deadline_is_checked_before_the_connect_when_no_time_is_left() -> None:
    """FAILS on r7c (no such check in the connect): _create_socket with no time left opens nothing."""
    from lead_desk.imap_count import ImapTotalTimeout, _BoundedImap

    ctx = ssl.create_default_context()
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    srv.settimeout(0.5)
    port = srv.getsockname()[1]
    try:
        with pytest.raises(ImapTotalTimeout):
            _BoundedImap("127.0.0.1", port, ssl_context=ctx, timeout=5.0, deadline=time.monotonic() - 1)
        with pytest.raises(TimeoutError):  # nothing connected: accept finds no client
            srv.accept()
    finally:
        srv.close()


# -- N3 -------------------------------------------------------------------------------------------------------------


class _FakeSock:
    """Hands out the bytes of one scripted reply in pieces of `piece` bytes (recv never returns more)."""

    def __init__(self, data: bytes, piece: int) -> None:
        self.data, self.piece = data, piece

    def settimeout(self, _t: float | None) -> None:
        pass

    def recv(self, n: int) -> bytes:
        take = self.data[: min(n, self.piece)]
        self.data = self.data[len(take) :]
        return take


def _read(data: bytes, piece: int = 4096) -> int:
    sock: Any = _FakeSock(data, piece)
    return smtp_outbox._read_reply(sock, smtp_outbox._Budget(5.0), bytearray())


CAP = smtp_outbox._REPLY_MAX_BYTES


def _reply(kind: str, total: int) -> bytes:
    """A reply of exactly `total` bytes counting every CRLF. kinds: single (one line "250 xxx"), bare (lines "250-xxx"
    then the bare code "250"), multi (lines "250-xxx" then "250 ok")."""
    if kind == "single":
        return b"250 " + b"x" * (total - 6) + b"\r\n"
    last = b"250\r\n" if kind == "bare" else b"250 ok\r\n"
    body = total - len(last)
    out = b""
    while body > 0:
        n = min(body, 1000)
        if body - n and body - n < 8:  # leave room so that every line is at least "250-\r\n"
            n -= 8
        out += b"250-" + b"x" * (n - 6) + b"\r\n"
        body -= n
    return out + last


@pytest.mark.parametrize("kind", ["single", "bare", "multi"])
@pytest.mark.parametrize("piece", [4096, 1, 777])
def test_n3_the_cap_is_accepted_and_cap_plus_one_is_refused_whole(kind: str, piece: int) -> None:
    """The cap case is a CONTROL (passes on r7c; killed by the mutant `>` -> `>=` in the line check). The cap + 1 case
    FAILS on r7c for the single line and the bare code (the final line was not counted)."""
    if piece == 1 and kind != "single":
        piece = 509  # one byte per recv for 65 KB is slow: the boundary does not depend on the piece size
    assert len(_reply(kind, CAP)) == CAP and len(_reply(kind, CAP + 1)) == CAP + 1
    assert _read(_reply(kind, CAP), piece) == 250
    with pytest.raises(smtp_outbox._Closed, match="too long"):
        _read(_reply(kind, CAP + 1), piece)


def test_n3_a_short_reply_of_each_kind_still_reads() -> None:
    """CONTROL (passes on r7c). Killed by the mutant that refuses every line (`> 0`)."""
    for data in (b"250 ok\r\n", b"250\r\n", b"250-a\r\n250-b\r\n250 c\r\n", b"354 go\r\n"):
        assert _read(data) == int(data[:3])


# -- N4 -------------------------------------------------------------------------------------------------------------

TOKEN = "pat-" + "na1-" + "abcd1234-ef56-7890-abcd-ef1234567890"
ZW = "​"
ECHOES = {
    "truncated": TOKEN[:20],
    "upper": TOKEN.upper(),
    "percent": "".join(f"%{ord(c):02x}" for c in TOKEN),
    "zero_width": ZW.join(TOKEN),
    "plain": TOKEN,
}


@pytest.mark.parametrize("name", list(ECHOES))
def test_n4_no_text_of_the_server_message_is_printed(name: str) -> None:
    """FAILS on r7c for every echo but the plain one: it printed the first 100 characters of the message with an exact
    replace of the token. The plain echo is a CONTROL (killed by the mutant that prints the message)."""
    body = {"category": "INVALID_AUTHENTICATION", "message": f"Authentication failed for {ECHOES[name]} now"}
    out = hp._why(401, body)
    assert out == " [INVALID_AUTHENTICATION]"
    assert not any(piece in out for piece in (TOKEN[:6], TOKEN.upper()[:6], "%70", ZW))


def test_n4_a_category_that_is_not_on_the_fixed_list_is_not_printed() -> None:
    """FAILS on r7c: any upper-case word of 3 to 40 letters was printed (a server could put a token echo there)."""
    echo = "".join(c for c in TOKEN.upper() if c.isalpha() or c == "_")
    assert re.fullmatch(r"[A-Z_]{3,40}", echo[:40])
    assert hp._why(400, {"category": echo[:40], "message": "x"}) == ""
    assert hp._why(400, {"category": ["BAD_REQUEST"]}) == ""
    assert hp._why(400, "text") == ""
    assert hp._why(500, {"category": "BAD_REQUEST"}) == ""  # only a 4xx answer
    assert hp._why(404, {"category": "OBJECT_NOT_FOUND"}) == " [OBJECT_NOT_FOUND]"  # CONTROL: a listed word passes


# -- M1 -------------------------------------------------------------------------------------------------------------


def _run_driver(base_url: str, scenario: str, log: Path, *extra: str, timeout: float = 60) -> Any:
    """Runs the driver in its own process group; past `timeout` the whole group (the worker processes too) is killed,
    so a driver that never ends fails the test instead of stalling the run."""
    proc = popen_program(
        [
            sys.executable,
            "-m",
            "load_tools.load_driver",
            "--base-url",
            base_url,
            "--scenario",
            scenario,
            "--log",
            str(log),
            *extra,
        ],
        cwd=REPO,
        env={
            "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LEAD_DESK_PATH_ROOTS": str(log.parent),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        pytest.fail(f"the driver was still running after {timeout} s")
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def test_m1_a_burst_of_100000_on_a_closed_port_ends_at_once_with_one_line_and_exit_3(tmp_path: Path) -> None:
    """FAILS on r7c: it kept every request alive for its whole retry deadline (the run did not end within the limit)."""
    log = tmp_path / "req.jsonl"
    t0 = time.monotonic()
    done = _run_driver(f"http://127.0.0.1:{free_port()}", "burst:100000", log, timeout=30)
    took = time.monotonic() - t0
    err = done.stderr.decode().strip().splitlines()
    assert done.returncode == EXIT_UNREACHABLE == 3, (done.returncode, err[-3:])
    assert took < 5, f"took {took:.1f} s"
    assert len(err) == 1 and err[0].startswith("ERROR: the desk cannot be reached") and done.stdout == b""
    assert not [p for p in tmp_path.iterdir()], "a log or facts file was written although nothing was sent"


def test_m1_a_desk_that_accepts_and_hangs_up_stops_the_run_after_the_first_errors(tmp_path: Path) -> None:
    """FAILS on r7c (every request retried for its whole deadline). The listener exists (the probe passes) but never
    answers: after 2 x threads connection errors with no answer all workers stop, the rest is logged as stopped."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(64)
    srv.settimeout(0.2)
    stop = threading.Event()

    def hang_up() -> None:
        while not stop.is_set():
            try:
                c, _ = srv.accept()
            except OSError:
                continue
            c.close()

    th = threading.Thread(target=hang_up, daemon=True)
    th.start()
    try:
        log = tmp_path / "req.jsonl"
        t0 = time.monotonic()
        done = _run_driver(
            f"http://127.0.0.1:{srv.getsockname()[1]}", "burst:60", log, "--workers", "1", "--threads", "2", timeout=40
        )
        took = time.monotonic() - t0
    finally:
        stop.set()
        th.join(5)
        srv.close()
    err = done.stderr.decode().strip().splitlines()
    assert done.returncode == 3, (done.returncode, err[-3:], done.stdout[-300:])
    assert took < 25, f"took {took:.1f} s"
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 60 and all(not d["accepted"] for d in lines)
    assert sum(d["gave_up"] == "stopped" for d in lines) >= 50


class _Ok(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        raw = b'{"receipt_id": "r", "verdict": "accepted"}'
        self.send_response(202)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args: Any) -> None:
        pass


def test_m1_control_a_desk_that_answers_is_not_stopped(tmp_path: Path) -> None:
    """CONTROL (passes on r7c). Killed by the mutants that stop the run on the first attempt or make the probe refuse
    a live listener."""
    srv = HTTPServer(("127.0.0.1", 0), _Ok)
    th = start_serving(srv)
    try:
        log = tmp_path / "req.jsonl"
        done = _run_driver(f"http://127.0.0.1:{srv.server_port}", "burst:20", log, "--workers", "1", "--threads", "4")
    finally:
        stop_serving(srv, th)
    assert done.returncode == 0, (done.stdout[-300:], done.stderr[-300:])
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 20 and all(d["accepted"] and d["gave_up"] is None for d in lines)


# -- m3, m4 (text level: PowerShell was NOT run) ---------------------------------------------------------------------


def _ps1(name: str) -> str:
    raw = (REPO / "scripts" / name).read_bytes()
    assert raw.count(b"\r\n") == raw.count(b"\n") and raw.count(b"\r") == raw.count(b"\n"), f"{name} must keep CRLF"
    return raw.decode("utf-8").replace("\r\n", "\n")


PATH_CMDLETS = ("Remove-Item", "Test-Path", "Get-Item", "Get-Content", "Set-Content", "Select-String", "New-Item")


def test_m3_every_path_cmdlet_of_reset_ps1_takes_a_literal_path() -> None:
    """FAILS on r7c (Remove-Item $pidFile and Remove-Item -Force $f read [ ] * ? in a name as wildcards)."""
    text = _ps1("reset.ps1")
    seen = 0
    for no, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        for cmd in PATH_CMDLETS:
            if re.search(rf"\b{cmd}\b", code):
                seen += 1
                assert "-LiteralPath" in code, f"reset.ps1:{no}: {cmd} without -LiteralPath: {line.strip()}"
    assert seen >= 4


def test_m4_both_start_process_calls_and_the_settings_calls_are_inside_a_try_with_a_fixed_exit() -> None:
    """FAILS on r7c (a failed Start-Process ended with PowerShell's own error text and left the first program
    running; python missing printed a PowerShell error)."""
    text = _ps1("start_all.ps1")
    for needle in (
        "Start-Process python -ArgumentList '-m', 'demo_only.fakes_server'",
        "Start-Process python -ArgumentList '-m', 'lead_desk.server'",
    ):
        at = text.index(needle)
        before = text[:at]
        opened = before.rfind("try {")
        assert opened != -1 and "catch" not in before[opened:], f"{needle[-25:]} is not inside a try block"
    assert re.search(r"catch \{ Stop-Start 'the demo servers could not be started' 4 \}", text)
    assert re.search(r"catch \{ Stop-Start 'the desk could not be started' 4 \}", text)
    first_settings = text.index("$dataDir = Get-DeskSetting 'data-dir'")
    assert text[:first_settings].rstrip().endswith("try {")
    tail = text[first_settings:]
    assert "exit 4" in tail[: tail.index("New-Item")], "python missing must end with one fixed line and exit code 4"
    assert "Start-Process" not in text[:first_settings] and text.index("Get-DeskSetting 'port'") < text.index(
        "Start-Process"
    )
