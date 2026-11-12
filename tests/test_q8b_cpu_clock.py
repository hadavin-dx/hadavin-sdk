"""Q8b gate fix: a speed test of the Q8b files is decided by the CPU time of the test process, never by the wall clock.

Class: a LOAD-DEPENDENT KILL. A wall-clock reading counts the time the process waited for a free core, so on a busy machine a
mutant that is slow was sometimes not caught (M257 once) and a good rule was sometimes failed. `time.process_time()` counts only the
time the process ran, so a second job on the machine does not change it (measured with four busy-loop processes alongside: see the
Q8b gate note in CHANGELOG.md). This file fails when any Q8b test file reads a wall clock again.
"""

from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
WALL_CLOCK = frozenset(
    {"perf_counter", "perf_counter_ns", "time", "time_ns", "monotonic", "monotonic_ns"}
)


def wall_clock_reads(source: str) -> list[int]:
    """Line numbers where `time.<wall clock>` is used, or a wall-clock name is imported from `time`, or `timeit` is used."""
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "time"
            and node.attr in WALL_CLOCK
        ):
            lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module == "time":
            lines += [node.lineno for a in node.names if a.name in WALL_CLOCK]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + (
                [node.module] if isinstance(node, ast.ImportFrom) else []
            )
            if "timeit" in names:
                lines.append(node.lineno)
    return lines


def test_the_checker_finds_each_form_of_a_wall_clock_read():
    assert wall_clock_reads("import time\nx = time.perf_counter()") == [2]
    assert wall_clock_reads("import time\nx = time.monotonic_ns()") == [2]
    assert wall_clock_reads("import time\nx = time.time()") == [2]
    assert wall_clock_reads("from time import perf_counter as p") == [1]
    assert wall_clock_reads("import timeit") == [1]
    assert wall_clock_reads("import time\nx = time.process_time()\ntime.sleep(1)") == []


def test_no_q8b_test_file_reads_a_wall_clock():
    found = {
        path.name: wall_clock_reads(path.read_text(encoding="utf-8"))
        for path in sorted(HERE.glob("test_q8b_*.py"))
    }
    bad = {name: lines for name, lines in found.items() if lines}
    assert not bad, f"a Q8b test reads the wall clock (use time.process_time): {bad}"
