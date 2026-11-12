"""The changelog gives the days the lists of kinds start to fail as the list has them, and writes no review day of
the names and claims as text.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from tests.test_policy_guard import (
    PENDING_KINDS,
    changelog_entry,
    kinds_sentence,
    stray_days,
)

ROOT = Path(__file__).resolve().parents[1]


KINDS_GROUPS = [(7, "2026-12-12"), (9, "2027-02-01")]
KINDS_LITERAL = "7 of them from 2026-12-12 and the other 9 from 2027-02-01"


def _kinds_pin_problem(pending: dict, built: str, entry: str) -> str:
    """The pin of the kinds days, for any list, built sentence and changelog entry: '' when all three agree with
    the groups and the sentence written out above. Two pins that do not follow the list: a change of either (a
    kind added or removed, a renewal of the kinds list) must change this file and the changelog together."""
    groups = sorted(Counter(p.review_by for p in pending.values()).items())
    if [(n, (d + timedelta(days=1)).isoformat()) for d, n in groups] != KINDS_GROUPS:
        return (
            "the pending kinds list no longer holds 7 kinds that fail from 2026-12-12 and 9 from 2027-02-01: "
            "change this pin and the changelog sentence together"
        )
    if built != KINDS_LITERAL:
        return "the sentence built from the kinds list is not the one written in this pin"
    if KINDS_LITERAL not in entry:
        return "the changelog does not give the days the kinds list starts to fail"
    return ""


def test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail():
    problem = _kinds_pin_problem(PENDING_KINDS, kinds_sentence(), changelog_entry())
    assert not problem, problem


def test_plant_a_moved_or_regrouped_kinds_list_or_a_changelog_that_follows_it_is_refused():
    from dataclasses import replace

    first = next(iter(PENDING_KINDS))
    earliest = min(p.review_by for p in PENDING_KINDS.values())
    latest = max(p.review_by for p in PENDING_KINDS.values())
    moved = {
        **PENDING_KINDS,
        first: replace(PENDING_KINDS[first], review_by=earliest - timedelta(days=1)),
    }
    regrouped = {k: replace(p, review_by=latest) for k, p in PENDING_KINDS.items()}
    entry = f"text {KINDS_LITERAL} text"
    assert _kinds_pin_problem(PENDING_KINDS, KINDS_LITERAL, entry) == "", (
        "the right list was refused"
    )
    assert "no longer holds 7 kinds" in _kinds_pin_problem(moved, kinds_sentence(moved), entry), (
        "a kind moved to another day was accepted (a changelog that follows the list)"
    )
    assert "no longer holds 7 kinds" in _kinds_pin_problem(
        regrouped, kinds_sentence(regrouped), entry
    ), "a list of one group was accepted"
    assert "not the one written in this pin" in _kinds_pin_problem(
        PENDING_KINDS,
        KINDS_LITERAL[:-1] + "2",
        entry,  # the last day of the sentence moved by one
    ), "a built sentence with another day was accepted"
    assert "does not give the days" in _kinds_pin_problem(
        PENDING_KINDS, KINDS_LITERAL, "text with no sentence"
    ), "a changelog without the sentence was accepted"


def test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list():
    stray = stray_days(changelog_entry(), kinds_sentence())
    assert not stray, (
        f"the changelog entry writes a day as text that is not the kinds list's: {stray}"
    )
    assert kinds_sentence() in changelog_entry(), (
        "the changelog entry does not hold the kinds sentence built from the list"
    )
    assert "review by the earliest review date" in changelog_entry(), (
        "the changelog entry does not name the review day by rule"
    )


def test_plant_changelog_rows_that_write_a_day_are_refused():
    sentence = kinds_sentence()
    good = f"fails for {sentence}, unless renewed"
    assert stray_days(good, sentence) == [], "the allowed sentence alone is flagged"
    for said, row in (
        ("a review date", good + " (review date 2026-12-11)"),
        ("a review by day", good + " (review by 2026-12-11)"),
        ("a start day of the names list", good + " and the names list fails from 2026-12-12"),
        ("a day of another entry (a stale docstring day)", good + " the tool says 2027-03-03"),
        ("a day written with slashes", good + " and from 2026/12/12"),
        ("a day written with the month in words", good + " and from 12 December 2026"),
        ("a day written as month and number", good + " and from Dec 12"),
    ):
        assert stray_days(row, sentence), f"{said} written in the entry is not flagged"


def test_the_changelog_entry_for_the_page_names_no_review_by_day_as_text():
    # The review day of the names and claims is built by the tool (`review_date()`) and shown on the page; a day
    # written into the changelog entry would stay after a renewal. The entry says "the earliest review date".
    # (The days the kinds list starts to fail are checked above against the dated list itself.)
    entry = changelog_entry()
    stray = re.findall(r"review by \d{4}-\d{2}-\d{2}", entry)
    assert not stray, f"the changelog entry writes a review day as text: {stray}"
    assert "review by the earliest review date" in entry, (
        "the changelog entry does not name the review day by rule"
    )


def test_the_changelog_says_what_a_renewal_renews_in_the_words_of_the_code_and_not_the_old_one_list_wording():
    # the code and the guard tests require BOTH lists of names and claims to carry one `decided` day, and the 16
    # kinds a day of their own; "every entry of the same list is renewed with it" said the wrong thing
    from tools import policy_page as pp

    flat = (
        changelog_entry()
    )  # the entry of this work, whitespace folded (the renewal bullet is nested in it)
    assert pp.RENEWAL_RULE in flat, (
        "the changelog does not hold the renewal rule of the names and claims word for word"
    )
    assert pp.KINDS_RENEWAL_RULE in flat, (
        "the changelog does not hold the renewal rule of the kinds word for word"
    )
    assert "every entry of the same list is renewed with it" not in flat, (
        "the changelog still says that every entry of the same list is renewed (both lists must be)"
    )


def _renewal_edits(old_decided: date, new_decided: date) -> list[tuple[str, str, str]]:
    """The edits of a full renewal of both dated groups, written the way the renewal list of the tool says (steps
    1 to 3 of each list), built from the LIVE days: (file, text now, text after). The names and claims move to
    `new_decided` and a `review_by` 30 days later; the 16 kinds move to `new_decided`, and the kinds that fail first
    get a `review_by` 30 days after it (the other kinds keep their day, which is inside the 92 days)."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    def call(d: date) -> str:
        return f"date({d.year}, {d.month}, {d.day})"

    new_review = new_decided + timedelta(days=30)
    old_reviews = {p.review_by for p in (*pp.PENDING_NAMES.values(), *pp.PENDING_CLAIMS.values())}
    first_kinds = min(p.review_by for p in PENDING_KINDS.values())
    old_first_fail, new_first_fail = first_kinds + timedelta(days=1), new_review + timedelta(days=1)
    guard, tool = "tests/test_policy_guard.py", "tools/policy_page.py"
    edits = [(tool, f"DECIDED = {call(old_decided)}", f"DECIDED = {call(new_decided)}")]
    edits += [
        (tool, f"    {call(d)},\n", f"    {call(new_review)},\n") for d in sorted(old_reviews)
    ]
    edits += [
        (
            guard,
            f"assert pp.DECIDED == {call(old_decided)}",
            f"assert pp.DECIDED == {call(new_decided)}",
        ),
        (guard, f"KINDS_DECIDED = {call(KINDS_DECIDED)}", f"KINDS_DECIDED = {call(new_decided)}"),
        (guard, f"{{{call(KINDS_DECIDED)}}}", f"{{{call(new_decided)}}}"),
        (guard, f'"Q8c PR 2", {call(first_kinds)})', f'"Q8c PR 2", {call(new_review)})'),
        (guard, f"on the literal day {KINDS_DECIDED}", f"on the literal day {new_decided}"),
        (
            "tests/test_policy_changelog.py",
            f'(7, "{old_first_fail}")',
            f'(7, "{new_first_fail}")',
        ),
        (
            "tests/test_policy_changelog.py",
            f"7 of them from {old_first_fail} and the other 9",
            f"7 of them from {new_first_fail} and the other 9",
        ),
        (
            "tests/test_policy_changelog.py",
            f"7 kinds that fail from {old_first_fail} and 9",
            f"7 kinds that fail from {new_first_fail} and 9",
        ),
    ]
    return edits


def test_plant_a_full_renewal_done_as_the_overdue_messages_list_it_keeps_the_tests_the_page_and_the_mutants_green():
    """The whole renewal of both dated groups on a temporary copy, by the lists of the overdue messages and nothing
    else: the guard, changelog, docs and notes tests, the page check and the mutant search texts must all pass on
    the new decision day, and a sample of the mutants that build their texts from the live days must still be
    killed. The steps the lists name and this plant are the same steps; a step that is missing from the list shows
    here as a red test of the copy, not as a surprise on the first overdue day."""
    from tests.test_policy_guard import pp

    root = Path(__file__).resolve().parents[1]
    new_decided = pp.DECIDED + timedelta(days=31)
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "renewed"
        copy.mkdir()
        for name in ("src", "tests", "tools", "docs", ".github"):
            shutil.copytree(
                root / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
        for name in ("CHANGELOG.md", "pyproject.toml", "README.md"):
            shutil.copy(root / name, copy / name)
        for rel, old, new in _renewal_edits(pp.DECIDED, new_decided):
            text = (copy / rel).read_text(encoding="utf-8")
            assert old in text, f"the renewal step does not apply: {old!r} is not in {rel}"
            (copy / rel).write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        # the changelog sentence that gives the days the kinds fail (CHANGELOG.md; the text may wrap)
        first = min(p.review_by for p in PENDING_KINDS.values()) + timedelta(days=1)
        text = (copy / "CHANGELOG.md").read_text(encoding="utf-8")
        moved, n = re.subn(
            rf"7 of them from {first}(\s+and\s+the other 9)",
            f"7 of them from {new_decided + timedelta(days=31)}\\1",
            text,
        )
        assert n == 1, "the changelog sentence of the kinds days was not found exactly once"
        (copy / "CHANGELOG.md").write_text(moved, encoding="utf-8", newline="\n")
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}
        env.update(
            PYTHONPATH=os.pathsep.join([str(copy / "src"), str(copy)]),
            PYTHONNOUSERSITE="1",
            HADAVIN_POLICY_FIXED_DAY=str(new_decided),
            HADAVIN_POLICY_MUTANT_RUN="1",
        )

        def run(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(  # noqa: S603  (argv list of this test, a temporary copy, no shell)
                [sys.executable, *args],
                cwd=copy,
                env=env,
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
            )

        write = run(
            "-c",
            "import sys; from datetime import date; from tools import policy_page as p; "
            f"sys.exit(p.main(['--write'], today=date.fromisoformat('{new_decided}')))",
        )
        assert write.returncode == 0, f"the page was not rewritten: {write.stderr[-600:]}"
        tests = run(
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "tests/test_policy_guard.py",
            "tests/test_policy_changelog.py",
            "tests/test_policy_docs.py",
            "tests/test_notes_lines_check.py",
            "--deselect",
            f"tests/test_policy_changelog.py::{sys._getframe().f_code.co_name}",
        )
        assert tests.returncode == 0, f"after the renewal the tests are red: {tests.stdout[-1500:]}"
        snippets = run("tests/policy_mutants.py", "--snippets")
        assert snippets.returncode == 0, (
            f"a mutant text no longer matches: {snippets.stdout[-800:]}"
        )
        sample = run("tests/policy_mutants.py", "--day", str(new_decided), "B8", "B9")
        assert sample.returncode == 0, (
            f"the mutants that take their days from the live lists are not killed after the renewal: "
            f"{sample.stdout[-1500:]}"
        )
