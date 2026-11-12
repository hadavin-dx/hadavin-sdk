"""The changelog gives the days the lists of kinds start to fail as the list has them, and writes no review day of
the names and claims as text.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

import re
from pathlib import Path

from tests.test_policy_guard import (
    PENDING_KINDS,
    changelog_entry,
    kinds_sentence,
    stray_days,
)

ROOT = Path(__file__).resolve().parents[1]


def test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail():
    # Structural pin only: the changelog holds the sentence built from the list, and the list has entries. No day
    # and no count is written here; they come from `PENDING_KINDS` (a renewal changes the list and this follows).
    assert PENDING_KINDS, "the list of pending kinds is empty"
    assert kinds_sentence() in changelog_entry(), (
        "the changelog does not give the days the kinds list starts to fail"
    )


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
