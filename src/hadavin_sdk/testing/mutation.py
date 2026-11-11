"""Judge one mutation-test run by the REASON for the kill, not only the exit code.

A *mutant* is one deliberate bug put into a copy of the code. It is *killed* when a test fails because of it. The harness that runs mutants is
``tools/mutation_runner.py`` (a developer tool, not shipped); this module judges one run of it.

How a harness uses this module: put one mutant into a copy of the package and run the targeted tests with a JUnit result file (the XML file
pytest writes). Read that file ONCE with ``read_junit(xml)``. Then call ``judge_report(returncode, report, expect=..., pinned=...)``. That
is the one call that judges a run correctly. A run whose first failing case is a fixture error (a failure in the setup or teardown of a test)
or a test file that could not be collected is ``ERROR``: no test ran as written, so it is never a kill.

Two lower-level helpers exist. ``judge(returncode, test_id, first_line, ...)`` judges the two plain values only. It cannot know about a
fixture or collection failure, so a harness that feeds it the output of ``first_failure_junit(xml)`` alone can count a fixture error as a
kill. ``first_failure_junit(xml)`` returns the id and the first line that starts with ``E `` of the first failing case (it copes with ids that
contain ``-``, ``|`` or ``[...]``). ``first_failure(stdout)`` reads the short failure list of pytest's ``-rf`` option and is safe only for ids
without `` - ``.

Verdicts:

- SURVIVED: exit code 0.
- NO_TESTS: exit code 5.
- ERROR: any other exit code except 1. Also exit code 1 when no failing test id is known (a failing run that names no test cannot have been
  killed by one).
- WRONG_REASON: ``expect`` is not in the first error line. The test id is NOT searched; ``pinned`` is what ties a kill to its test.
- OTHER_TEST: the failing test is not the test named in ``pinned`` (``Mutant.pinned`` in ``tools/mutation_runner.py``).
- CRASH: the first line is not an AssertionError, or it holds one of the ``crash_markers`` (texts or patterns the caller gives for failures
  that must count as a crash, for example ``denied:internal_error``).
- KILLED: the first line is an AssertionError, the intended way.

Only an AssertionError (or ``Failed: DID NOT RAISE``) first line is KILLED. Anything else (KeyError, TypeError, an import error,
``pytest.fail`` with another message) is CRASH, so a mutant that merely breaks the code is not counted as an assertion kill. A runner should
count CRASH as a failure unless the mutant says a crash is the intended reaction.

Limits: an ``assert`` inside the package code that a mutant trips looks like an assertion kill, because the judge sees only text.
``expect`` must be at least 4 characters (a one-letter fragment matches almost anything).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from enum import StrEnum
from typing import NamedTuple

MAX_JUNIT_CHARS = 8_000_000  # a JUnit file of one targeted pytest run is a few KB; this is a ceiling, not a target


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
    if not test_id:  # a failing run with no failing test id (an empty or unreadable JUnit file) names no test that killed
        return Verdict.ERROR
    if expect and expect not in first_line:
        return Verdict.WRONG_REASON
    if pinned is not None and pinned != test_id:
        return Verdict.OTHER_TEST
    for m in crash_markers:
        if m.search(first_line) if isinstance(m, re.Pattern) else m in first_line:
            return Verdict.CRASH
    return Verdict.KILLED if _ASSERTION.search(first_line.strip()) else Verdict.CRASH


def judge_report(
    rc: int,
    report: JunitReport,
    *,
    expect: str | None = None,
    pinned: str | None = None,
    crash_markers: Iterable[str | re.Pattern[str]] = (),
) -> Verdict:
    """``judge`` for a run read by ``read_junit``: ``ERROR`` when the run failed (exit 1) and its FIRST failing case is a fixture error or a test
    file that could not be collected (no test ran as written, so it is never a kill, whatever the first line says); every other run is judged
    by ``judge`` on ``report.test_id`` and ``report.first_line``. An exit code other than 1 is judged by ``judge`` alone (0 SURVIVED, 5 NO_TESTS)."""
    verdict = judge(
        rc,
        report.test_id,
        report.first_line,
        expect=expect,
        pinned=pinned,
        crash_markers=crash_markers,
    )
    return (
        Verdict.ERROR
        if rc == 1 and (report.fixture_failed or report.collection_failed)
        else verdict
    )


def first_failure(stdout: str) -> tuple[str, str]:
    """(failing test id, first ``E `` line) from ``pytest -q -rf`` output. The id is cut at the FIRST `` - `` of the FAILED line, so an
    id that contains `` - `` is truncated: use ``first_failure_junit`` for those."""
    failed = next((ln for ln in stdout.splitlines() if ln.startswith("FAILED ")), "")
    test_id = failed.removeprefix("FAILED ").split(" - ")[0].strip()
    first = next((ln.strip() for ln in stdout.splitlines() if ln.startswith("E ")), "")
    return test_id, first


def _parse_junit(xml_text: str) -> ET.Element:
    """The root of a JUnit file, after the three refusals (size ceiling, DOCTYPE, ENTITY): the one place where JUnit text is parsed."""
    # The file is written by our own pytest run, but the parser is shipped: a DOCTYPE or ENTITY declaration (the way an XML bomb or an
    # external entity is written) is refused before parsing, so only plain elements reach expat.
    if len(xml_text) > MAX_JUNIT_CHARS:
        raise ValueError("a JUnit file over MAX_JUNIT_CHARS is refused")
    low = xml_text.lower()
    if "<!doctype" in low or "<!entity" in low:
        raise ValueError("a JUnit file with a DOCTYPE or ENTITY declaration is refused")
    # The ONE documented exception to S314 and B314 in this file: the call is reached only after the three refusals above (size
    # ceiling, no DOCTYPE, no ENTITY), so no entity can be declared or expanded, and the text is written by our own pytest run.
    return ET.fromstring(xml_text)  # noqa: S314  # nosec B314


def _case_id(case: ET.Element) -> str:
    """The id of one JUnit test case, in the form ``Mutant.pinned`` uses: ``classname`` with ``.`` read as ``/``, then ``::name``."""
    return f"{case.get('classname', '').replace('.', '/')}::{case.get('name', '')}"


_FIXTURE_ERROR_STARTS = (
    "failed on setup",
    "failed on teardown",
)  # how pytest words the ``error`` of a fixture that failed


_COLLECTION_ERROR_START = "collection failure"  # how pytest words the ``error`` of a test file that could not be imported or collected


def _first_failure(root: ET.Element) -> tuple[str, str, str]:
    """(id, first ``E`` line, kind) of the first test case that holds a ``failure`` or an ``error``. ``kind`` is ``"fixture"`` for a setup or
    teardown error of a fixture, ``"collection"`` for a test file that could not be imported or collected (pytest gives that case a
    NON-empty id, ``::<dotted module>``, and runs no test), and ``""`` for a test body that failed."""
    for case in root.iter("testcase"):
        bad = case.find("failure")
        if bad is None:
            bad = case.find("error")
        if bad is None:
            continue
        body = (bad.text or "").splitlines()
        e_line = next(
            (ln.strip() for ln in body if ln.lstrip().startswith("E ")),
            (bad.get("message") or "").splitlines()[0] if bad.get("message") else "",
        )
        message = bad.get("message") or ""
        kind = ""
        if bad.tag == "error" and message.startswith(_FIXTURE_ERROR_STARTS):
            kind = "fixture"
        elif bad.tag == "error" and message.startswith(_COLLECTION_ERROR_START):
            kind = "collection"
        return _case_id(case), e_line, kind
    return "", "", ""


def _skipped(root: ET.Element) -> list[str]:
    return [_case_id(case) for case in root.iter("testcase") if case.find("skipped") is not None]


def _fixture_errors(root: ET.Element) -> list[str]:
    return [
        _case_id(case)
        for case in root.iter("testcase")
        for err in case.findall("error")
        if (err.get("message") or "").startswith(_FIXTURE_ERROR_STARTS)
    ]


class JunitReport(NamedTuple):
    """What one pass over a JUnit file found: the first failing case (``test_id``, ``first_line``), the skipped cases, every case with a
    fixture error (``fixture_errors``), and ``fixture_failed``: True when the FIRST failing case is itself a fixture error. A test body
    that failed and whose teardown then failed is NOT ``fixture_failed``: pytest writes the failure first, so the test ran as written.
    ``collection_failed``: True when the FIRST failing case is a test file that could not be imported or collected (an ``assert`` at import time
    is a plain ``AssertionError`` there), so no test ran."""

    test_id: str
    first_line: str
    skipped: list[str]
    fixture_errors: list[str]
    fixture_failed: bool
    collection_failed: bool = False


def read_junit(xml_text: str) -> JunitReport:
    """One parse of a pytest JUnit file for ``first_failure_junit``, ``skipped_tests`` and ``fixture_errors`` together (same refusals:
    ``ValueError`` for a DOCTYPE, an ENTITY or a text over ``MAX_JUNIT_CHARS``; a truncated file is a ``SyntaxError``)."""
    root = _parse_junit(xml_text)
    test_id, first, kind = _first_failure(root)
    return JunitReport(
        test_id,
        first,
        _skipped(root),
        _fixture_errors(root),
        kind == "fixture",
        kind == "collection",
    )


def first_failure_junit(xml_text: str) -> tuple[str, str]:
    """(failing test id, first assertion line of THAT test) from a pytest JUnit XML file. The id is ``classname`` with ``.`` read as ``/`` plus
    ``::name``: a path-like id (``tests/test_x::test_y``; a test in a class reads ``tests/test_x/TestC::test_y``), the form ``Mutant.pinned``
    must use. A DOCTYPE or ENTITY declaration, or a text over ``MAX_JUNIT_CHARS``, raises ``ValueError`` (the runner marks that mutant ERROR)."""
    return _first_failure(_parse_junit(xml_text))[:2]


def skipped_tests(xml_text: str) -> list[str]:
    """The ids (same form as ``first_failure_junit``) of the test cases a pytest JUnit file records as skipped, an expected failure
    (xfail) included. A run that selected a test which did not run proves nothing about it: a runner that forbids skips counts such a
    mutant run as an error and not as a kill. The same refusals as ``first_failure_junit`` (``ValueError``; a truncated file is a ``SyntaxError``)."""
    return _skipped(_parse_junit(xml_text))


def fixture_errors(xml_text: str) -> list[str]:
    """The ids (same form as ``first_failure_junit``) of the test cases whose ``error`` record is a setup or teardown failure of a fixture
    (pytest writes ``failed on setup with ...`` / ``failed on teardown with ...``). Such a test never ran as written, so a runner counts the
    mutant run as an error and not as a kill, even when the fixture failed with an ``AssertionError``. Note (confirmed by a real pytest 9.2.0 run: ``<testsuite errors="1" failures="1" tests="2">`` with ``<testcase classname="t.test_b" name="test_x">`` holding the ``<failure>`` first and a second ``<testcase>`` of the same classname and name holding ``<error message="failed on teardown with ...">``): when a test body fails and its
    teardown fails too, pytest writes TWO ``testcase`` elements of the same classname and name (the ``failure`` first, then the teardown ``error``), so that id is listed here as
    well; ``read_junit(...).fixture_failed`` tells whether the FIRST failing case is the fixture error. Same refusals as ``first_failure_junit``."""
    return _fixture_errors(_parse_junit(xml_text))
