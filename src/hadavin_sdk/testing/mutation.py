"""Judge one mutation-test run by the REASON for the kill, not only the exit code.

Harness contract (the runner is yours; this judges one run): revert one guard in a copy of the package, run the
targeted tests with ``pytest -x``, then call ``judge(returncode, test_id, first_line, expect=..., pinned=...)`` with the
FAILING TEST ID and the FIRST ``E `` line pytest printed (``first_failure(stdout)`` extracts both). Passing them
separately means a test id that contains `` | `` is never split.

Verdicts: SURVIVED (exit 0), NO_TESTS (exit 5), ERROR (any other exit code except 1), WRONG_REASON (``expect`` is not in the test id or
line), OTHER_TEST (not the test pinned in a reviewed baseline), CRASH (the first line is not an AssertionError, or it
matches a ``crash_markers`` pattern such as an executor's ``denied:internal_error``), KILLED (an AssertionError, the intended
way). Only an AssertionError first line is KILLED; anything else (KeyError, TypeError, an import error) is CRASH, so
a mutant that merely breaks the code is not counted as an assertion kill."""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum


class Verdict(StrEnum):
    SURVIVED = "SURVIVED"
    NO_TESTS = "NO_TESTS"
    ERROR = "ERROR"
    WRONG_REASON = "WRONG_REASON"
    OTHER_TEST = "OTHER_TEST"
    CRASH = "CRASH"
    KILLED = "KILLED"


_ASSERTION = re.compile(
    r"^E\s+(?:\w+\.)*AssertionError\b|^E\s+assert\b|^E\s+Failed: DID NOT RAISE\b"
)


def judge(
    rc: int,
    test_id: str,
    first_line: str,
    *,
    expect: str | None = None,
    pinned: str | None = None,
    crash_markers: Iterable[str | re.Pattern[str]] = (),
) -> Verdict:
    if rc == 0:
        return Verdict.SURVIVED
    if rc == 5:
        return Verdict.NO_TESTS
    if rc != 1:
        return Verdict.ERROR
    if expect and expect not in test_id and expect not in first_line:
        return Verdict.WRONG_REASON
    if pinned is not None and pinned != test_id:
        return Verdict.OTHER_TEST
    for m in crash_markers:
        if m.search(first_line) if isinstance(m, re.Pattern) else m in first_line:
            return Verdict.CRASH
    return Verdict.KILLED if _ASSERTION.search(first_line.strip()) else Verdict.CRASH


def first_failure(stdout: str) -> tuple[str, str]:
    """(failing test id, first ``E `` line) from ``pytest -q -x`` output; empty strings if there is none."""
    failed = next((ln for ln in stdout.splitlines() if ln.startswith("FAILED ")), "")
    test_id = failed.removeprefix("FAILED ").split(" - ")[0].strip()
    first = next((ln.strip() for ln in stdout.splitlines() if ln.startswith("E ")), "")
    return test_id, first
