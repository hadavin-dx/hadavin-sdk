"""Round 7C, finding H: reset.sh and reset.ps1 stop a process only when its whole command line is the desk's or the demo
server's, not when the text `lead_desk.server` appears anywhere in it. Real stand-in processes on this machine; the
.ps1 is checked by its text only (it has not been run on Windows)."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from support import REPO, popen_program, run_program, start_standin, text_file, wait_until

SH = (REPO / "scripts" / "reset.sh").read_text(encoding="utf-8")
PS = (REPO / "scripts" / "reset.ps1").read_bytes().decode("utf-8")
WAIT = "import os, time; open(os.environ['READY'], 'w').close(); time.sleep(60)"
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="reset.sh is the non-Windows script")


def _is_ours(pid: int, ps_text: str = "") -> bool:
    """Run the is_ours function of reset.sh alone, in bash, with an EMPTY search path (so no `python` is needed)."""
    start = SH.index("is_ours() {")
    body = SH[start : SH.index("\nalive() {", start)]
    script = text_file(body + f'\nis_ours {pid} "$1"\n', ".sh")
    done = run_program(
        [shutil.which("bash") or "bash", script, ps_text],
        env={"PATH": "/nonexistent"},
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode == 0


def _start(tmp: Path, module: str, args: tuple[str, ...] = ()) -> Any:
    ready = tmp / "ready"
    proc = start_standin(tmp / "standin", module, WAIT, ready, args)
    wait_until(ready.exists, what="the stand-in runs")
    return proc


def test_the_exact_command_lines_are_accepted_and_the_look_alikes_are_not(tmp_path: Path) -> None:
    good = [("lead_desk.server", ()), ("demo_only.fakes_server", ("--outbox", "keyed", "--port", "8123"))]
    bad = [
        ("lead_desk.server", ("--extra",)),
        ("demo_only.fakes_server", ()),
        ("demo_only.fakes_server", ("--outbox", "other", "--port", "8123")),
        ("demo_only.fakes_server", ("--outbox", "blind", "--port", "x")),
    ]
    for module, args in good + bad:
        folder = tmp_path / (module + "-".join(args))
        folder.mkdir()
        proc = _start(folder, module, args)
        try:
            assert _is_ours(proc.pid) == ((module, args) in good), (module, args)
        finally:
            proc.kill()
            proc.wait()


def test_a_program_that_only_mentions_the_desk_is_not_the_desk(tmp_path: Path) -> None:
    ready = tmp_path / "r"
    # the old text search matched this: a python script whose arguments hold the words lead_desk.server
    proc = popen_program(
        [sys.executable, text_file(WAIT), "lead_desk.server", "demo_only.fakes_server"],
        env={**os.environ, "READY": str(ready)},
    )
    try:
        wait_until(ready.exists, what="the look-alike runs")
        assert _is_ours(proc.pid) is False
    finally:
        proc.kill()
        proc.wait()


def test_a_program_not_named_python_is_not_the_desk() -> None:
    assert _is_ours(0, "sleep -m lead_desk.server") is False  # no /proc entry for pid 0: the ps text is used
    assert _is_ours(0, "/usr" + "/bin/python3 -m lead_desk.server") is True
    assert _is_ours(0, "python -m lead_desk.server extra") is False
    assert _is_ours(0, "less lead_desk.server.log") is False


def test_the_script_does_not_search_the_command_line_for_text() -> None:
    assert "*lead_desk.server*" not in SH and "*demo_only.fakes_server*" not in SH
    assert not re.search(r"-match 'lead_desk", PS)
    assert "$ourCommandLine" in PS and "-imatch $ourCommandLine" in PS
    assert "python[0-9.]*" in PS and "--outbox (keyed|blind) --port [0-9]+" in PS
