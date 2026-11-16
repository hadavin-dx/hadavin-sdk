"""The reset scripts delete the lead book, so they refuse a database path that is not inside the repository's data
folder. Made-up data only; each test creates only the files it names."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest
from support import (
    REPO,
    book_folder_in_repo,
    popen_program,
    run_program,
    run_python,
    start_standin,
    text_file,
    wait_until,
)

WINDOWS = sys.platform == "win32"


def _run(
    script: str,
    db: Path,
    *args: str,
    first_on_path: Path | None = None,
    shell: str = "bash",
    code: str | None = None,
    **extra: str,
) -> subprocess.CompletedProcess[str]:
    """first_on_path: a folder (holding a stand-in `python`) searched before this interpreter's folder; the
    desk's own DESK_LEADFLOW_FILE and DESK_NUDGE_TO of the calling shell are then left out of the environment.
    code: shell text run as a script file of its own instead of the script file (not on Windows)."""
    env = {**os.environ, "DESK_DB_PATH": str(db), **extra}
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    if first_on_path is not None:
        env["PATH"] = str(first_on_path) + os.pathsep + env["PATH"]
        for name in ("DESK_LEADFLOW_FILE", "DESK_NUDGE_TO"):
            if name not in extra:
                env.pop(name, None)
    if WINDOWS:
        powershell = shutil.which("powershell")
        if powershell is None:
            pytest.skip("Windows PowerShell is not installed")
        cmd = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(REPO / "scripts" / script)]
    else:
        cmd = [shell, text_file(code, ".sh")] if code is not None else [shell, str(REPO / "scripts" / script), *args]
    return run_program(cmd, cwd=REPO, env=env, capture_output=True, text=True, timeout=120, check=False)


SCRIPT = "reset.ps1" if WINDOWS else "reset.sh"


def test_reset_refuses_a_database_outside_the_data_folder(tmp_path: Path) -> None:
    db = tmp_path / "desk.sqlite3"
    log = tmp_path / "desk.log"
    for f in (db, log):
        f.write_text("keep me", encoding="utf-8")
    done = _run(SCRIPT, db)
    assert done.returncode == 2, (done.stdout, done.stderr)
    assert "refused" in done.stdout + done.stderr
    assert db.read_text(encoding="utf-8") == "keep me" and log.read_text(encoding="utf-8") == "keep me"


def test_reset_still_deletes_a_database_inside_the_data_folder() -> None:
    with book_folder_in_repo("reset-test-") as folder:
        db = folder / "desk.sqlite3"
        db.write_text("x", encoding="utf-8")
        done = _run(SCRIPT, db, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
        assert done.returncode == 0, (done.stdout, done.stderr)
        assert not db.exists()


# -- the reset never deletes the lead book while the desk may still be using it
@pytest.fixture
def book() -> Any:
    with book_folder_in_repo("reset-guard-") as folder:  # a fresh folder: nothing else is ever removed
        db = folder / "desk.sqlite3"
        db.write_text("keep me", encoding="utf-8")
        (folder / "desk.log").write_text("keep me", encoding="utf-8")
        yield db


def _kept(db: Path) -> bool:
    return db.read_text(encoding="utf-8") == "keep me" and (db.parent / "desk.log").exists()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_reset_refuses_when_something_answers_on_the_desk_port(book: Path) -> None:
    """A desk started by hand has no pid file: the port that still answers stops the reset."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        done = _run(SCRIPT, book, DESK_PORT=str(listener.getsockname()[1]), DESK_FAKES_PORT=str(_free_port()))
    assert done.returncode == 4 and "answers on port" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert _kept(book)


def test_reset_refuses_when_a_process_holds_the_database(book: Path) -> None:
    from lead_desk import lockfile

    handle = lockfile.acquire(book)
    try:
        done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    finally:
        handle.close()
    assert done.returncode == 3 and "holds the database" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert _kept(book)


def test_reset_refuses_a_pid_file_of_another_program(book: Path) -> None:
    pidfile = book.parent / "desk.pid"
    pidfile.write_text(str(os.getpid()), encoding="utf-8")  # this test process: not the desk
    done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    assert done.returncode == 6 and "not the desk" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert _kept(book) and pidfile.exists()


# CONTROL (r7e, old, body changed): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.skipif(WINDOWS, reason="Windows ends a process at once; the slow stop is a POSIX case")
def test_reset_sh_refuses_when_the_desk_does_not_stop(book: Path) -> None:
    ready = book.parent / "ready"
    code = (
        "import os, signal, sys, time; signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "open(os.environ['READY'], 'w').close(); time.sleep(60)"
    )
    slow = start_standin(Path(text_file("pass")).parent / "standin", "lead_desk.server", code, ready)
    try:
        wait_until(ready.exists, what="the child has installed its signal handler")
        (book.parent / "desk.pid").write_text(str(slow.pid), encoding="utf-8")
        done = _run(
            SCRIPT, book, RESET_STOP_WAIT_SECONDS="1", DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port())
        )
    finally:
        slow.kill()
        slow.wait()
    assert done.returncode == 5 and "did not stop" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert _kept(book)


# CONTROL (r7e, old, body changed): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.skipif(WINDOWS, reason="Windows ends a process at once; the slow stop is a POSIX case")
def test_reset_sh_waits_for_a_desk_that_needs_a_few_seconds_to_stop(book: Path) -> None:
    """A desk that takes about three seconds to finish after the stop signal: the reset waits for it, and only then
    deletes. (A reset that checked once and went on would delete under a live desk or give up too early.)"""
    code = (
        "import os, signal, sys, time\n"
        "def stop(*a):\n"
        "    time.sleep(3)\n"
        "    sys.exit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        "open(os.environ['READY'], 'w').close()\n"
        "time.sleep(60)\n"
    )
    ready = book.parent / "ready"
    slow = start_standin(Path(text_file("pass")).parent / "standin", "lead_desk.server", code, ready)
    try:
        wait_until(ready.exists, what="the child has installed its signal handler")
        (book.parent / "desk.pid").write_text(str(slow.pid), encoding="utf-8")
        done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
        alive_after = slow.poll() is None
    finally:
        slow.kill()
        slow.wait()
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert not alive_after and not book.exists() and not (book.parent / "desk.pid").exists()


@pytest.mark.skipif(WINDOWS, reason="reset.sh is the non-Windows script")
@pytest.mark.parametrize("name", ["desk.pid", "fakes.pid"])
def test_reset_sh_deletes_an_empty_pid_file(book: Path, name: str) -> None:
    """An empty pid file names no process: it is removed and the reset goes on (the check is -e, not -s)."""
    pidfile = book.parent / name
    pidfile.write_text("", encoding="utf-8")
    done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert not pidfile.exists() and not book.exists()


# CONTROL (r7e, old, body changed): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.skipif(WINDOWS, reason="a process that ended but is not collected yet is a POSIX state")
def test_reset_sh_treats_a_pid_file_of_an_ended_but_uncollected_process_as_gone(book: Path) -> None:
    ended = popen_program([sys.executable, text_file("pass")])

    def uncollected() -> bool:  # not waited for: the process stays a zombie of this test until it is collected
        out = run_program(
            ["ps", "-p", str(ended.pid), "-o", "stat="],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        return out.strip().startswith("Z")

    try:
        wait_until(uncollected, what="the child ended and was not collected")
        (book.parent / "desk.pid").write_text(str(ended.pid), encoding="utf-8")
        done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    finally:
        ended.wait()
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert not book.exists() and not (book.parent / "desk.pid").exists()


# CONTROL (r7e, old, body changed): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize(
    "value", ["1+1", "$(touch pwned)", "-3", "1.5", " ", "a", "abc", "08", "09", "0001", "1234", "99999999999999999999"]
)
def test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number(book: Path, value: str) -> None:
    """Both scripts: digits only, no leading zero (a shell reads 08 as a bad octal), at most three digits; the answer
    is exit 2 before a process is stopped or a file is deleted."""
    ready = book.parent / "ready"
    code = "import os, sys, time; open(os.environ['READY'], 'w').close(); time.sleep(60)"
    desk = start_standin(Path(text_file("pass")).parent / "standin", "lead_desk.server", code, ready)
    try:
        wait_until(ready.exists, what="the child is running")
        (book.parent / "desk.pid").write_text(str(desk.pid), encoding="utf-8")
        ports = {"DESK_PORT": str(_free_port()), "DESK_FAKES_PORT": str(_free_port())}
        done = _run(SCRIPT, book, RESET_STOP_WAIT_SECONDS=value, **ports)
        still_running = desk.poll() is None
    finally:
        desk.kill()
        desk.wait()
    assert done.returncode == 2 and "RESET_STOP_WAIT_SECONDS" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert still_running and (book.parent / "desk.pid").exists()  # nothing was stopped
    assert _kept(book) and not (REPO / "pwned").exists()


@pytest.mark.parametrize("value", ["0", "1", "10", "999"])
def test_reset_accepts_a_plain_whole_number_of_seconds(book: Path, value: str) -> None:
    done = _run(
        SCRIPT, book, RESET_STOP_WAIT_SECONDS=value, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port())
    )
    assert done.returncode == 0 and not book.exists(), (done.stdout, done.stderr)


def test_reset_check_answers_one_line_when_the_lock_file_cannot_be_looked_at(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], book: Path
) -> None:
    import importlib.util

    from lead_desk import lockfile

    spec = importlib.util.spec_from_file_location("reset_check_under_test", REPO / "scripts" / "reset_check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Unreadable:
        def exists(self) -> bool:
            raise PermissionError("no access")

    monkeypatch.setenv("DESK_DB_PATH", str(book))
    monkeypatch.setattr(lockfile, "lock_path", lambda _db: Unreadable())
    assert module.main() == 3
    out = capsys.readouterr().out.strip()
    assert out.startswith("refused:") and len(out.splitlines()) == 1 and "no access" not in out and _kept(book)


def test_reset_refuses_when_the_lock_file_cannot_be_tested_and_creates_none_on_a_refusal(book: Path) -> None:
    lock = Path(f"{book.resolve()}.lock")
    lock.mkdir()  # a lock file that cannot be opened: nothing says that no desk holds the book
    try:
        done = _run(SCRIPT, book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    finally:
        lock.rmdir()
    assert done.returncode == 3 and "cannot be tested" in done.stdout + done.stderr, (done.stdout, done.stderr)
    assert _kept(book)
    with socket.socket() as listener:  # a refusal for another reason leaves no lock file behind either
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        again = _run(SCRIPT, book, DESK_PORT=str(listener.getsockname()[1]), DESK_FAKES_PORT=str(_free_port()))
    assert again.returncode == 4 and not lock.exists(), (again.stdout, again.stderr)


# A stand-in `python` for scripts/start_all.sh: it answers the three helper calls `python scripts/desk_setting.py
# data-dir | fakes-port | port` (data folder, demo-server port, desk port) with fixed values, writes one line per
# `python -m <module>` launch (the desk stand-in stays up 2 seconds unless STUB_DESK_EXITS is set) with the
# DESK_LEADFLOW_FILE and DESK_NUDGE_TO it saw, and records every call, so the test sees what the shell [[ ]] tests
# decided without starting a server.
# server.
_STUB_PYTHON = """#!/usr/bin/env bash
echo "$*" >> "${STUB_DATA}/calls.log"
if [[ "$1" == "scripts/desk_setting.py" ]]; then
  case "$2" in
    data-dir) echo "${STUB_DATA}";;
    fakes-port) echo 1234;;
    port) echo "${STUB_DESK_PORT:-4321}";;
    start-tries) echo "${STUB_TRIES:-3}";;
    start-pause) echo 0.1;;
  esac
elif [[ "$1" == "-m" ]]; then
  echo "LEADFLOW=[${DESK_LEADFLOW_FILE-<unset>}] NUDGE=[${DESK_NUDGE_TO-<unset>}]" > "${STUB_DATA}/launch-$2.rec"
  # R7: a program that is "started" must own what the start check looks for. The demo-server stand-in prints the
  # line the real one prints and stays up; the desk stand-in is a real loopback HTTP server (STUB_DESK_HELPER)
  # that binds after
  # STUB_DESK_DELAY seconds, prints its line, answers GET /counts with 200 and ends after 8 seconds.
  # STUB_DESK_EXITS=1 is a desk that stops at once; STUB_DESK_NO_BIND=1 one that stays up but never takes the port.
  if [[ "$2" == "demo_only.fakes_server" ]]; then
    echo "fakes server stub on $$"; echo "$$" > "${STUB_DATA}/fakes-stub.pid"; exec sleep 8
  fi
  if [[ "$2" == "lead_desk.server" ]] && [[ -z "${STUB_DESK_EXITS-}" ]]; then
    echo "$$" > "${STUB_DATA}/desk-stub.pid"
    exec "${STUB_REAL_PY}" "${STUB_DESK_HELPER}"
  fi
fi
"""


_STUB_DESK_HELPER = """import http.server, os, sys, time
time.sleep(float(os.environ.get("STUB_DESK_DELAY", "0")))
if os.environ.get("STUB_DESK_NO_BIND"):
    time.sleep(8)
    sys.exit(0)
if os.environ.get("STUB_DESK_LIES"):  # prints the ready line but owns no port: a neighbour holds it
    print("desk listening on 127.0.0.1", flush=True)
    time.sleep(8)
    sys.exit(0)
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", int(os.environ["STUB_DESK_PORT"])), H)
if not os.environ.get("STUB_DESK_SILENT"):
    print("desk listening on 127.0.0.1", flush=True)
srv.timeout = 0.2
end = time.monotonic() + 8
while time.monotonic() < end:
    srv.handle_request()
"""


def _start_all(
    tmp_path: Path, *args: str, pid_file: str = "", fifo: str = "", **env: str
) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Run scripts/start_all.sh with the stub python first on PATH; returns the result and the stub's data folder."""
    data = tmp_path / "data"
    data.mkdir()
    helper = tmp_path / "stub_desk.py"
    helper.write_text(_STUB_DESK_HELPER, encoding="utf-8")
    env.setdefault("STUB_DESK_PORT", str(_free_port()))
    if pid_file:
        (data / pid_file).write_text("1\n", encoding="utf-8")
    if fifo:
        os.mkfifo(data / fifo)  # a pipe where a log file should be
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "python"
    stub.write_text(_STUB_PYTHON, encoding="utf-8")
    stub.chmod(0o755)
    done = _run(
        "start_all.sh",
        tmp_path / "unused.sqlite3",
        *args,
        first_on_path=bin_dir,
        STUB_DATA=str(data),
        STUB_REAL_PY=sys.executable,
        STUB_DESK_HELPER=str(helper),
        **env,
    )
    return done, data


def _launch(data: Path) -> str:
    """The env line the stub saw for the desk launch (a background process: wait, bounded, until it has written)."""
    rec = data / "launch-lead_desk.server.rec"
    wait_until(rec.exists, timeout=10, what="the stub python launched as the desk")
    return rec.read_text(encoding="utf-8").strip()


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, "LEADFLOW=[demo_only/leadflow.json] NUDGE=[reminder@example.test]"),  # default: on
        ({"DESK_LEADFLOW_FILE": "off"}, "LEADFLOW=[off] NUDGE=[<unset>]"),  # script line 12: != off
        ({"DESK_LEADFLOW_FILE": ""}, "LEADFLOW=[] NUDGE=[<unset>]"),  # script line 12: -n
        ({"DESK_LEADFLOW_FILE": "x.json"}, "LEADFLOW=[x.json] NUDGE=[reminder@example.test]"),
        ({"DESK_LEADFLOW_FILE": "of"}, "LEADFLOW=[of] NUDGE=[reminder@example.test]"),  # a near miss of "off" is a file
        ({"DESK_LEADFLOW_FILE": "*"}, "LEADFLOW=[*] NUDGE=[reminder@example.test]"),  # no pattern matching in [[ ]] rhs
        (
            {"DESK_LEADFLOW_FILE": "x.json", "DESK_NUDGE_TO": "me@example.test"},
            "LEADFLOW=[x.json] NUDGE=[me@example.test]",
        ),
        (
            {"DESK_LEADFLOW_FILE": "x.json", "DESK_NUDGE_TO": ""},
            "LEADFLOW=[x.json] NUDGE=[]",
        ),  # a set empty value is kept
    ],
)
def test_start_all_sh_turns_the_reminder_on_only_for_a_real_leadflow_file(
    tmp_path: Path, env: dict[str, str], expected: str
) -> None:
    """Runs the real scripts/start_all.sh (the [[ ]] test of its leadflow line, which SonarCloud shell:S7688 made
    us rewrite) with a stub `python`, and reads the environment the launched desk process would get."""
    done, data = _start_all(tmp_path, **env)
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert _launch(data) == expected


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
def test_start_all_sh_ends_with_exit_3_and_one_line_when_the_desk_stops_at_once(tmp_path: Path) -> None:
    """A desk that is gone right after the start is not "started": exactly one fixed line, exit code 3."""
    done, _data = _start_all(tmp_path, STUB_DESK_EXITS="1")
    assert done.returncode == 3, (done.stdout, done.stderr)
    assert done.stderr.strip() == (
        "the desk stopped right after it was started: the programs started here were stopped; "
        "read the log files in the data folder"
    )
    assert "started:" not in done.stdout


def _gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    try:  # a process that ended but is not yet collected still answers kill 0: read its state
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split(") ")[-1][:1] == "Z"
    except OSError:
        return True


class _Foreign:
    """A listener of ANOTHER program on a port of this computer: it answers every connection with `reply` and closes."""

    def __init__(self, reply: bytes) -> None:
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.sock.settimeout(0.1)
        self.port = int(self.sock.getsockname()[1])
        self.reply = reply
        self.stop = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self) -> None:
        while not self.stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            try:
                conn.sendall(self.reply)
            except OSError:
                pass
            conn.close()

    def close(self) -> None:
        self.stop = True
        self.thread.join(2)
        self.sock.close()


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
@pytest.mark.parametrize(
    ("reply", "extra"),
    [
        (b"HELLO, not http\r\n", {}),  # a foreign program on the port; the stand-in desk cannot bind and ends
        (b"HTTP/1.0 200 OK\r\n\r\n{}", {"STUB_DESK_NO_BIND": "1"}),  # the neighbour answers 200, the desk never binds
        (b"HTTP/1.0 200 OK\r\n\r\n{}", {"STUB_DESK_SILENT": "1"}),  # (binds nothing here) a desk with no ready line
        (b"HTTP/1.0 404 Not Found\r\n\r\n", {"STUB_DESK_LIES": "1"}),  # ready line printed, the port is a neighbour's
    ],
    ids=["desk-cannot-bind", "foreign-200-desk-never-binds", "foreign-200-desk-silent", "ready-line-but-foreign-404"],
)
def test_start_all_sh_does_not_call_a_neighbours_port_the_desk_and_stops_what_it_started(
    tmp_path: Path, reply: bytes, extra: dict[str, str]
) -> None:
    """F3: a program on the desk's port that is not the desk must never make start_all.sh say "started". A real
    foreign listener answers on the port (once even with a good 200); the script ends with exit 3, ONE fixed line,
    and the demo server it had started is gone and its pid file removed."""
    foreign = _Foreign(reply)
    try:
        done, data = _start_all(tmp_path, STUB_DESK_PORT=str(foreign.port), STUB_TRIES="12", **extra)
    finally:
        foreign.close()
    assert done.returncode == 3, (done.stdout, done.stderr)
    assert "started:" not in done.stdout and len(done.stderr.strip().splitlines()) == 1, done.stderr
    assert "the programs started here were stopped" in done.stderr
    fakes_pid = int((data / "fakes-stub.pid").read_text(encoding="utf-8"))
    wait_until(lambda: _gone(fakes_pid), timeout=10, what="the demo server stand-in stopped")
    assert not (data / "fakes.pid").exists() and not (data / "desk.pid").exists()


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
def test_start_all_sh_waits_for_a_desk_that_takes_two_seconds_to_start(tmp_path: Path) -> None:
    """F3: the look lasts longer than a slow start. A desk that binds after 2 s is "started" (exit 0)."""
    done, data = _start_all(tmp_path, STUB_DESK_DELAY="2", STUB_TRIES="80")
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert "started: demo servers" in done.stdout
    desk_pid = int((data / "desk-stub.pid").read_text(encoding="utf-8"))
    os.kill(desk_pid, 15)  # the stand-in ends at once; nothing of this test stays running
    fakes_pid = int((data / "fakes-stub.pid").read_text(encoding="utf-8"))
    os.kill(fakes_pid, 15)
    wait_until(lambda: _gone(desk_pid) and _gone(fakes_pid), timeout=10, what="both stand-ins stopped")


def test_start_poll_constants_cover_the_bind_retry_and_the_script_reads_them() -> None:
    """F3: behaviour, not only "positive": the look lasts longer than the desk's own bind retry by the margin, and the
    two helper words the shell scripts ask for answer with exactly these numbers."""
    from lead_desk import constants as c

    span = c.START_CHECK_TRIES * c.START_CHECK_PAUSE_SECONDS
    assert span > c.BIND_RETRY_SECONDS + c.START_CHECK_MARGIN_SECONDS - c.START_CHECK_PAUSE_SECONDS
    assert span >= c.BIND_RETRY_SECONDS + c.START_CHECK_MARGIN_SECONDS
    for word, want in (("start-tries", c.START_CHECK_TRIES), ("start-pause", c.START_CHECK_PAUSE_SECONDS)):
        done = run_python(
            [str(REPO / "scripts" / "desk_setting.py"), word],
            {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(REPO / "src")},
            timeout=30,
        )
        assert done.returncode == 0 and float(done.stdout) == want, (word, done.stdout, done.stderr)


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
@pytest.mark.parametrize("name", ["fakes.log", "desk.log"])  # a pid-file name that exists is refused earlier, with 2
def test_start_all_sh_refuses_a_pipe_in_place_of_a_log_or_process_number_file(tmp_path: Path, name: str) -> None:
    """Round 7B (review M6): a pipe named fakes.log used to let the script go on and end with exit code 0."""
    done, data = _start_all(tmp_path, fifo=name)
    assert done.returncode == 4, (done.returncode, done.stdout, done.stderr)
    assert done.stdout == "" and len(done.stderr.strip().splitlines()) == 1, (done.stdout, done.stderr)
    assert f"({name})" in done.stderr and "not a regular file" in done.stderr
    assert not list(data.glob("launch-*.rec")), "a server was launched although a log path was a pipe"


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
@pytest.mark.parametrize("pid_file", ["fakes.pid", "desk.pid"])
def test_start_all_sh_refuses_when_either_pid_file_exists_and_starts_nothing(tmp_path: Path, pid_file: str) -> None:
    """The pid-file check is the other rewritten [[ ]] test (two tests joined by ||): either file alone refuses."""
    done, data = _start_all(tmp_path, pid_file=pid_file)
    assert done.returncode == 2, (done.stdout, done.stderr)  # 2 = refused (7B; was 1, a failed check)
    assert done.stderr.strip() == "pid files exist: run scripts/reset.sh first", done.stderr
    assert not list(data.glob("launch-*.rec")), "a server was launched although a pid file existed"
    assert sorted(p.name for p in data.glob("*.pid")) == [pid_file]  # and the script wrote no pid file of its own


@pytest.mark.skipif(WINDOWS, reason="start_all.sh is the non-Windows script")
def test_start_all_sh_refuses_an_unknown_mode_before_it_calls_python(tmp_path: Path) -> None:
    """The mode check is a `case`, not a changed [[ ]] line; this test only guards that the early exit stays first."""
    done, data = _start_all(tmp_path, "sideways")
    assert done.returncode == 2, (done.stdout, done.stderr)  # bad usage is exit 2 (it was 1, the code of "failed")
    assert "mode must be keyed or blind" in done.stderr
    assert not (data / "calls.log").exists(), "python was called before the mode was checked"


@pytest.mark.skipif(WINDOWS or shutil.which("dash") is None, reason="needs dash (the sh of Debian and Ubuntu)")
@pytest.mark.parametrize("bash_version", [None, "5.2.0"], ids=["BASH_VERSION-unset", "BASH_VERSION-exported"])
@pytest.mark.parametrize("script", ["reset.sh", "start_all.sh"])
def test_the_shell_scripts_refuse_to_run_under_dash_and_delete_or_start_nothing(
    tmp_path: Path, script: str, bash_version: str | None
) -> None:
    """[[ ]] is not in dash: its `[[: not found` counts as a false test, which would skip reset.sh's refusal of a
    database outside ./data. The scripts therefore stop at once when the shell cannot run [[ ]]. The test is of the
    feature, not of the variable BASH_VERSION: dash takes that from the environment, so a name test is bypassed
    (the second case exports it with a made-up value)."""
    db = tmp_path / "desk.sqlite3"
    db.write_text("made-up lead book", encoding="utf-8")
    bin_dir = (
        tmp_path / "bin"
    )  # a stand-in python first on PATH, so that without the guard start_all.sh starts nothing real
    bin_dir.mkdir()
    (bin_dir / "python").write_text(_STUB_PYTHON, encoding="utf-8")
    (bin_dir / "python").chmod(0o755)
    stub = bin_dir if script == "start_all.sh" else None
    extra = {} if bash_version is None else {"BASH_VERSION": bash_version}
    done = _run(script, db, shell=shutil.which("dash") or "dash", first_on_path=stub, STUB_DATA=str(tmp_path), **extra)
    assert done.returncode == 2, (done.stdout, done.stderr)
    assert "run this script with bash" in done.stderr and "not bash" in done.stderr
    assert "not found" not in done.stderr, "a [[ line ran under dash"
    assert db.read_text(encoding="utf-8") == "made-up lead book"
    assert not (tmp_path / "calls.log").exists(), "the stand-in python was called"


@pytest.mark.skipif(WINDOWS or shutil.which("dash") is None, reason="needs dash (the sh of Debian and Ubuntu)")
@pytest.mark.parametrize("script", ["reset.sh", "start_all.sh"])
def test_the_guard_line_refuses_under_dash_even_without_set_e(tmp_path: Path, script: str) -> None:
    """The guard joins its probe and `echo bash` with `&&`. With `;` it would still print `bash` after the failed
    probe, and only the `set -e` of the script (which comes before the guard) would hide that. This runs the guard
    line alone, with no `set -e`, so the `&&` is pinned by itself."""
    lines = (REPO / "scripts" / script).read_text(encoding="utf-8").splitlines()
    guard = [line for line in lines if line.startswith('case "$( (eval ')]
    assert len(guard) == 1, "the guard line was not found exactly once"
    db = tmp_path / "unused.sqlite3"
    after = guard[0] + "\necho PAST-THE-GUARD"
    refused = _run(script, db, shell=shutil.which("dash") or "dash", code=after)
    assert refused.returncode == 2 and "PAST-THE-GUARD" not in refused.stdout, (refused.stdout, refused.stderr)
    passed = _run(script, db, code=after)
    assert passed.returncode == 0 and "PAST-THE-GUARD" in passed.stdout, (passed.stdout, passed.stderr)


# -- R4-07: a pid file that is a pipe, a folder, a link or a word (never read for ever, never a traceback) ----------


def _bad_pid_file(pidfile: Path, kind: str) -> None:
    if kind == "fifo":
        os.mkfifo(pidfile)
    elif kind == "folder":
        pidfile.mkdir()
    elif kind == "link":
        target = pidfile.parent / "elsewhere.txt"
        target.write_text("1", encoding="utf-8")
        pidfile.symlink_to(target)
    elif kind == "word":
        pidfile.write_text("abc", encoding="utf-8")
    elif kind == "zero":
        pidfile.write_text("0", encoding="utf-8")
    elif kind == "negative":
        pidfile.write_text("-1", encoding="utf-8")


@pytest.mark.skipif(WINDOWS or not hasattr(os, "mkfifo"), reason="reset.sh and named pipes are POSIX")
@pytest.mark.parametrize("kind", ["fifo", "folder", "link", "word", "zero", "negative"])
@pytest.mark.parametrize("name", ["desk.pid", "fakes.pid"])
def test_reset_sh_refuses_a_pid_file_that_is_not_a_plain_process_number_in_one_line(
    book: Path, name: str, kind: str
) -> None:
    pidfile = book.parent / name
    _bad_pid_file(pidfile, kind)
    try:
        done = _run_limited(book, DESK_PORT=str(_free_port()), DESK_FAKES_PORT=str(_free_port()))
    finally:
        if pidfile.is_dir() and not pidfile.is_symlink():
            pidfile.rmdir()
    assert done is not None, "reset.sh did not return in 8 seconds (it waits on a pipe)"
    assert done.returncode == 6, (done.returncode, done.stdout, done.stderr)
    lines = (done.stdout + done.stderr).strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith(f"refused: {name} "), lines
    assert "Traceback" not in done.stderr and "abc" not in done.stderr
    assert _kept(book)  # nothing was deleted


def _run_limited(db: Path, **extra: str) -> subprocess.CompletedProcess[str] | None:
    env = {**os.environ, "DESK_DB_PATH": str(db), **extra}
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    try:
        return run_program(
            ["bash", str(REPO / "scripts" / "reset.sh")],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=8,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None


def test_the_windows_reset_script_reads_a_pid_file_only_when_it_is_a_plain_file() -> None:
    """Text test (no PowerShell here): the script refuses a link or folder, reads one line, bounds it to a number."""
    text = (REPO / "scripts" / "reset.ps1").read_text(encoding="utf-8")
    assert "Get-Content -LiteralPath" in text and "Get-Item -LiteralPath" in text and "-TotalCount 1" in text
    assert "[1-9][0-9]{0,9}" in text and "2147483647" in text and "LinkType" in text and "PSIsContainer" in text
    assert "[int]$word" not in text and "[int64]$word" in text
