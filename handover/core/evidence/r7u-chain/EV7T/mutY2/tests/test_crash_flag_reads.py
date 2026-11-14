"""Class: the one-shot crash flag file is read through regfile with a small cap. A flag file that is not UTF-8 text, or
is bigger than any point name could be, is no flag: the reader returns, it does not raise and it does not crash the
process. Each case runs in a child process (a wrongly accepted flag would end the child with the crash exit code).
Made-up data only."""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from queue import Empty
from typing import Any

import pytest

from lead_desk.constants import EXIT_SIMULATED_KILL, FLAG_FILE_MAX_BYTES
from lead_desk.hooks import ALL_HOOK_POINTS
from lead_desk.trace import WINDOWS

POINT = sorted(ALL_HOOK_POINTS)[0]
WINDOW = sorted(WINDOWS)[0]


def _child(flag: str, point: str, window: str, queue: Any) -> None:
    """Runs in a child process: call both flag readers; a flag taken as real ends this process with the crash code."""
    from lead_desk.hooks import FlagFileHooks
    from lead_desk.trace import CrashWindows

    FlagFileHooks(Path(flag)).crash_point(point, None)
    CrashWindows(Path(flag)).hit(window)
    queue.put("returned")


def _run(flag: Path) -> tuple[int | None, str]:
    """(exit code of the child, what it put on the queue: "" when it ended before it could)."""
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_child, args=(str(flag), POINT, WINDOW, queue))
    child.start()
    child.join(30)
    if child.is_alive():
        child.terminate()
        pytest.fail("the flag reader did not end within 30 seconds")
    try:
        return child.exitcode, str(queue.get(timeout=2))
    except Empty:
        return child.exitcode, ""


@pytest.mark.parametrize(
    "content",
    [
        b"\x00" * (1024 * 1024),  # a megabyte of NUL: no flag
        b"\xff",  # not UTF-8 text: no flag, and no UnicodeDecodeError
        POINT.encode() + b" " * (FLAG_FILE_MAX_BYTES + 10),  # the right word but far longer than any flag file
        WINDOW.encode() + b" " * (FLAG_FILE_MAX_BYTES + 10),
    ],
    ids=["nul-megabyte", "not-utf8", "point-oversize", "window-oversize"],
)
def test_a_bad_flag_file_is_no_flag(tmp_path: Path, content: bytes) -> None:
    flag = tmp_path / "flag"
    flag.write_bytes(content)
    code, said = _run(flag)
    assert (code, said) == (0, "returned")
    assert flag.exists()  # the file was not taken as a flag, so it was not deleted


def test_a_good_flag_file_still_crashes_the_process(tmp_path: Path) -> None:
    flag = tmp_path / "flag"
    flag.write_text(POINT, encoding="utf-8")
    code, said = _run(flag)
    assert code == EXIT_SIMULATED_KILL and said == ""  # the process ended by itself at the crash point
    assert not flag.exists()
