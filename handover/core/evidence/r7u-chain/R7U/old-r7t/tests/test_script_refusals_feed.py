"""Class: a helper script that takes a number or a choice from the person (or talks to the desk) ends with ONE plain
line `refused: ...` and a fixed exit code, never with a Python traceback. Covers scripts/feed.py (a bad --index, a bad
setting, an unreadable canned file, a desk that is not running, does not answer, hangs up or answers rubbish),
scripts/reset_check.py, scripts/crash_desk.py and tools/scrub_n8n_export.py. Every script runs in its own process;
loopback only, made-up data only."""

from __future__ import annotations

import json
import os
import socket
import subprocess  # noqa: S404
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refusals import EXIT_REFUSED, EXIT_UNREACHABLE
from support import run_program

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"

CANNED_COUNT = len(json.loads((REPO / "demo_only" / "canned_leads.json").read_text(encoding="utf-8")))
LOOPBACK = "127.0.0.1"


def _run(args: list[str], cwd: Path = REPO, **env: str) -> tuple[int, str]:
    """Run a script in its own process; returns (exit code, standard output + standard error)."""
    base = {k: v for k, v in os.environ.items() if not k.startswith("DESK_")}
    base.update(PYTHONPATH=str(REPO / "src"), PYTHONDONTWRITEBYTECODE="1", **env)
    done = run_program(
        [sys.executable, *args], cwd=cwd, env=base, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL
    )
    return done.returncode, done.stdout + done.stderr


def _feed(*args: str, **env: str) -> tuple[int, str]:
    return _run([str(SCRIPTS / "feed.py"), *args], **env)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind((LOOPBACK, 0))
        return int(s.getsockname()[1])


def _assert_refusal(code: int, out: str, want_code: int, *, starts: str) -> None:
    assert "Traceback" not in out, out
    assert code == want_code, (code, out)
    lines = out.strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith("refused: " + starts), out


@contextmanager
def _fake_desk(behaviour: str) -> Iterator[int]:
    """A loopback listener that misbehaves: 'silent' takes the request and never answers, 'hangup' closes at once,
    'rubbish' answers bytes that are not a web reply."""
    server = socket.socket()
    server.bind((LOOPBACK, 0))
    server.listen(4)
    server.settimeout(0.2)
    stop = threading.Event()
    held: list[socket.socket] = []

    def serve() -> None:
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except OSError:
                continue
            if behaviour == "hangup":
                conn.close()
            elif behaviour == "rubbish":
                conn.recv(65536)
                conn.sendall(b"\x00\xff this is not http\r\n\r\n")
                conn.close()
            else:
                held.append(conn)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield int(server.getsockname()[1])
    finally:
        stop.set()
        thread.join(5)
        for c in held:
            c.close()
        server.close()


@pytest.mark.parametrize("index", ["0", "-1", str(CANNED_COUNT + 1), "9999", "99999999999999999999"])
def test_feed_index_out_of_range_is_one_refusal_line(index: str) -> None:
    code, out = _feed("--source", "form", "--index", index)
    _assert_refusal(code, out, EXIT_REFUSED, starts="--index: must be a whole number from 1 to ")
    assert out.strip().endswith(str(CANNED_COUNT))


@pytest.mark.parametrize("args", [["--source", "form"], ["--source", "form", "--index", "1", "--all"]])
def test_feed_needs_exactly_one_of_index_and_all_as_one_refusal_line(args: list[str]) -> None:
    # (the other wrong command lines are the shared refusing parser's job: builder F2)
    code, out = _feed(*args)
    _assert_refusal(code, out, EXIT_REFUSED, starts="--index, --all: give exactly one of them")


@pytest.mark.parametrize("value", ["abc", "70000", "-5"])
def test_feed_bad_desk_port_setting_is_one_refusal_line(value: str) -> None:
    code, out = _feed("--source", "form", "--index", "1", DESK_PORT=value)
    _assert_refusal(code, out, EXIT_REFUSED, starts="desk settings: DESK_PORT")
    assert value not in out.replace("DESK_PORT", "")


def test_feed_desk_not_running_says_so_and_how_to_start_it() -> None:
    port = str(_free_port())  # nothing listens there
    for args in (["--index", "1"], ["--all"]):
        code, out = _feed("--source", "form", *args, DESK_BIND=LOOPBACK, DESK_PORT=port)
        _assert_refusal(code, out, EXIT_UNREACHABLE, starts="the desk: the desk cannot be reached")
        assert "not running" in out and "scripts/start_all.sh" in out
        assert port not in out and LOOPBACK not in out  # the address is never printed


@pytest.mark.parametrize(
    ("behaviour", "words"),
    [("silent", "did not answer in time"), ("hangup", "not a web reply"), ("rubbish", "not a web reply")],
)
def test_feed_desk_that_hangs_hangs_up_or_answers_rubbish_is_one_refusal_line(behaviour: str, words: str) -> None:
    with _fake_desk(behaviour) as port:
        code, out = _feed(
            "--source",
            "webhook",
            "--index",
            "1",
            DESK_BIND=LOOPBACK,
            DESK_PORT=str(port),
            DESK_SEND_TIMEOUT_SECONDS="1",
        )
    _assert_refusal(code, out, EXIT_UNREACHABLE, starts="the desk: ")
    assert words in out and str(port) not in out


@pytest.mark.parametrize("canned", ["missing", "not-json", "not-a-list", "not-utf8", "empty-list", "list-of-numbers"])
def test_feed_unreadable_canned_file_is_one_refusal_line(tmp_path: Path, canned: str) -> None:
    folder = tmp_path / "demo_only"
    folder.mkdir()
    target = folder / "canned_leads.json"
    content = {
        "not-json": b"{bad",
        "not-a-list": b'{"a": 1}',
        "not-utf8": b"\xff\xfe\x00[]",
        "empty-list": b"[]",
        "list-of-numbers": b"[1, 2]",
    }
    if canned in content:
        target.write_bytes(content[canned])
    code, out = _run(
        [str(SCRIPTS / "feed.py"), "--source", "form", "--index", "1"], cwd=tmp_path, DESK_PORT=str(_free_port())
    )
    _assert_refusal(code, out, EXIT_REFUSED, starts="canned leads: demo_only/canned_leads.json cannot be read")
    assert "repository root" in out


# -- the siblings of the same class -----------------------------------------------------------------------------------


@pytest.mark.parametrize("script", ["reset_check.py", "crash_desk.py"])
def test_scripts_that_read_the_desk_settings_refuse_a_bad_setting_without_a_traceback(script: str) -> None:
    code, out = _run([str(SCRIPTS / script)], DESK_PORT="abc")
    assert "Traceback" not in out, out
    assert code == (EXIT_REFUSED if script == "reset_check.py" else 4), (code, out)
    assert len(out.strip().splitlines()) <= 2 and "DESK_PORT is not a number" in out


@pytest.mark.parametrize("content", [b"{bad", b"[1]", b'"text"', b"\xff\xfe\x00", b'{"nodes": 5}', b'{"nodes": [1]}'])
def test_scrub_refuses_a_file_that_is_not_a_workflow_without_a_traceback(tmp_path: Path, content: bytes) -> None:
    src = tmp_path / "in.json"
    src.write_bytes(content)
    code, out = _run(["-m", "tools.scrub_n8n_export", str(src), str(tmp_path / "out.json")], cwd=REPO)
    assert "Traceback" not in out, out
    assert code == EXIT_REFUSED and out.startswith("refused: in.json: "), (code, out)
    assert not (tmp_path / "out.json").exists()


def test_scrub_refuses_text_it_cannot_write_and_leaves_no_half_file(tmp_path: Path) -> None:
    src = tmp_path / "in.json"
    src.write_text('{"name": "\\ud800 lone half of a character", "nodes": []}', encoding="utf-8")
    code, out = _run(["-m", "tools.scrub_n8n_export", str(src), str(tmp_path / "out.json")], cwd=REPO)
    assert "Traceback" not in out, out
    assert code == EXIT_REFUSED and out.startswith("refused: out.json: "), (code, out)
    assert not (tmp_path / "out.json").exists()


@pytest.mark.parametrize("ca_file", ["not-a-certificate", "missing", "folder"])
def test_server_refuses_an_unusable_smtp_ca_file_without_a_traceback(tmp_path: Path, ca_file: str) -> None:
    password = tmp_path / "pw"
    password.write_text("made-up-" + "password", encoding="utf-8")
    ca = tmp_path / "ca.pem"
    if ca_file == "not-a-certificate":
        ca.write_text("this is not certificate text\n", encoding="utf-8")
    elif ca_file == "folder":
        ca.mkdir()
    code, out = _run(
        ["-m", "lead_desk.server"],
        DESK_DB_PATH=str(tmp_path / "d" / "desk.sqlite3"),
        DESK_PORT="0",
        DESK_OUTBOX="smtp_provider",
        DESK_SMTPP_HOST="mail.example.test",
        DESK_SMTPP_USER="u",
        DESK_SMTPP_PASSWORD_FILE=str(password),
        DESK_SMTPP_FROM="a@example.test",
        DESK_SMTPP_RECIPIENTS="b@example.test",
        DESK_SMTPP_MAX_SENDS="5",
        DESK_SMTPP_CA_FILE=str(ca),
    )
    assert "Traceback" not in out, out
    assert code == 4, (code, out)
    assert out.strip() == (
        "the desk refuses a setting: DESK_SMTPP_CA_FILE cannot be read as a file of trusted certificates"
    ), out
    assert "ca.pem" not in out and "SSL" not in out
