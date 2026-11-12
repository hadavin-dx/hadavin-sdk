"""The changelog gives the days the lists of kinds start to fail as the list has them, and writes no review day of
the names and claims as text.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

import re
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
    moved = {**PENDING_KINDS, first: replace(PENDING_KINDS[first], review_by=date(2026, 12, 10))}
    regrouped = {k: replace(p, review_by=date(2027, 1, 31)) for k, p in PENDING_KINDS.items()}
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
        PENDING_KINDS, "7 of them from 2026-12-12 and the other 9 from 2027-02-02", entry
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
