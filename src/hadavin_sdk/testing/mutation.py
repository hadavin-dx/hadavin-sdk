"""Judge one mutation-test run by the REASON for the kill, not only the exit code.

Harness contract (the runner is ``testing.mutation_runner``; this judges one run): revert one guard in a copy of the package, run the
targeted tests, then call ``judge(returncode, test_id, first_line, expect=..., pinned=...)`` with the FAILING TEST ID and the FIRST
``E `` line of THAT test. ``first_failure_junit(xml)`` extracts both from a JUnit file (robust for ids that contain ``-``,
``|`` or ``[...]``); ``first_failure(stdout)`` parses ``-rf`` text and is only safe for ids without `` - ``.

Verdicts: SURVIVED (exit 0), NO_TESTS (exit 5), ERROR (any other exit code except 1), WRONG_REASON (``expect`` is not in the test id or
line), OTHER_TEST (not the test pinned in a reviewed baseline), CRASH (the first line is not an AssertionError, or it matches a
``crash_markers`` pattern such as an executor's ``denied:internal_error``), KILLED (an AssertionError, the intended way). Only an
AssertionError (or ``Failed: DID NOT RAISE``) first line is KILLED; anything else (KeyError, TypeError, an import error, ``pytest.fail``
with another message) is CRASH, so a mutant that merely breaks the code is not counted as an assertion kill. A runner should count CRASH
as a failure unless the mutant says a crash is the intended reaction.

Limits: an ``assert`` inside the package code that a mutant trips looks like an assertion kill; the judge sees only text. ``expect`` must
be at least 4 characters (a one-letter fragment matches almost anything).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
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
    r"^E?\s*(?:\w+\.)*AssertionError\b|^E?\s*assert\b|^E?\s*Failed: DID NOT RAISE\b"
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
    if expect is not None and len(expect) < 4:
        raise ValueError("expect must be at least 4 characters")
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
    """(failing test id, first ``E `` line) from ``pytest -q -rf`` output. The id is cut at the FIRST `` - `` of the FAILED line, so an
    id that contains `` - `` is truncated: use ``first_failure_junit`` for those."""
    failed = next((ln for ln in stdout.splitlines() if ln.startswith("FAILED ")), "")
    test_id = failed.removeprefix("FAILED ").split(" - ")[0].strip()
    first = next((ln.strip() for ln in stdout.splitlines() if ln.startswith("E ")), "")
    return test_id, first


def first_failure_junit(xml_text: str) -> tuple[str, str]:
    """(failing test id, first assertion line of THAT test) from a pytest JUnit XML file."""
    # the junit file is written by our own pytest run, not untrusted input
    root = ET.fromstring(xml_text)  # noqa: S314  # nosec B314
    for case in root.iter("testcase"):
        bad = case.find("failure")
        if bad is None:
            bad = case.find("error")
        if bad is None:
            continue
        test_id = f"{case.get('classname', '').replace('.', '/')}::{case.get('name', '')}"
        body = (bad.text or "").splitlines()
        e_line = next(
            (ln.strip() for ln in body if ln.lstrip().startswith("E ")),
            (bad.get("message") or "").splitlines()[0] if bad.get("message") else "",
        )
        return test_id, e_line
    return "", ""
