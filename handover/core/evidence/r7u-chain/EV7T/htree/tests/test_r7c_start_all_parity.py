"""Round 7C, finding G: scripts/start_all.ps1 does what scripts/start_all.sh does. The .ps1 cannot run on this machine
(no PowerShell, not Windows), so its text is pinned step by step against the .sh; it has NOT been run on Windows."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PS = (REPO / "scripts" / "start_all.ps1").read_bytes().decode("utf-8")
SH = (REPO / "scripts" / "start_all.sh").read_text(encoding="utf-8")


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# ps1 saved with LF, or sh saved with CRLF.
def test_the_ps1_keeps_windows_line_ends_and_the_sh_does_not() -> None:
    assert PS.count("\r\n") == PS.count("\n") > 40
    assert "\r" not in SH


def test_both_look_for_the_same_three_signs_before_they_say_started() -> None:
    for text in (PS, SH):
        assert "^fakes server " in text and "^desk listening on " in text and "/counts" in text
        assert "start-tries" in text and "start-pause" in text
    # the order: the demo servers are looked at before the desk is started; "started:" is printed last
    assert PS.index("^fakes server ") < PS.index("-m', 'lead_desk.server'") < PS.index("^desk listening on ")
    assert PS.index("^desk listening on ") < PS.index("started: demo servers")
    assert SH.index("^fakes server ") < SH.index("python -m lead_desk.server") < SH.index("^desk listening on ")


def test_a_start_that_does_not_work_stops_what_was_started_and_ends_with_exit_3() -> None:
    # r7d: the PowerShell function ends with `exit $Code`, whose default is 3 (a program that could not even be started
    # passes 4); the shell script ends with exit 3 itself
    assert "[int]$Code = 3" in PS and "exit $Code" in PS and "exit 3" in SH
    assert "Stop-Process" in PS and "Remove-Item -LiteralPath" in PS and "fakes.pid" in PS and "desk.pid" in PS
    for phrase in (
        "the demo servers stopped right after they were started",
        "the demo servers did not report that they accept requests",
        "the desk stopped right after it was started",
        "the desk did not answer on its port in time",
        "the programs started here were stopped; read the log files in the data folder",
    ):
        assert phrase in PS and phrase in SH, phrase


def test_a_log_or_process_file_that_is_not_a_regular_file_is_refused_with_exit_4() -> None:
    line = "the desk refuses to start: a log or process-number file in the data folder is not a regular file"
    assert line in PS and line in SH
    for name in ("fakes.log", "desk.log", "fakes.pid", "desk.pid", "fakes.err.log", "desk.err.log"):
        assert f"'{name}'" in PS, name
    assert "ReparsePoint" in PS and "PSIsContainer" in PS and "LinkType" in PS
    assert PS.index("ReparsePoint") < PS.index("exit 4", PS.index("ReparsePoint"))


def test_every_path_test_in_the_ps1_is_literal() -> None:
    """A path with [ ] or * would be read as a pattern by Test-Path, Get-Item, Select-String or Set-Content."""
    for cmd in ("Test-Path", "Get-Item", "Select-String", "Set-Content", "Remove-Item"):
        for m in re.finditer(rf"{cmd}\b[^\r\n]*", PS):  # also the lines of the head comment: none names a command
            assert "-LiteralPath" in m.group(0), m.group(0)
