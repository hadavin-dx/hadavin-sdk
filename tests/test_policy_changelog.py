"""The changelog gives the days the lists of kinds start to fail as the list has them, and writes no review day of
the names and claims as text.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

import re
from datetime import date
from pathlib import Path

from tests.test_policy_guard import PENDING_KINDS

ROOT = Path(__file__).resolve().parents[1]


def test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail():
    by_date: dict[date, int] = {}
    for p in PENDING_KINDS.values():
        by_date[p.review_by] = by_date.get(p.review_by, 0) + 1
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split())
    first, second = sorted(by_date)
    assert (by_date[first], by_date[second]) == (7, 9) and (first, second) == (
        date(2026, 12, 11),
        date(2027, 1, 31),
    )
    assert "7 of them from 2026-12-12 and the other 9 from 2027-02-01" in changelog, (
        "the changelog does not give the days the kinds list starts to fail"
    )


def test_the_changelog_entry_for_the_page_names_no_review_by_day_as_text():
    # The review day of the names and claims is built by the tool (`review_date()`) and shown on the page; a day
    # written into the changelog entry would stay after a renewal. The entry says "the earliest review date".
    # (The days the kinds list starts to fail are checked above against the dated list itself.)
    text = " ".join((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split())
    start = text.index("**Declared permissions for three backend kinds**")
    entry = text[start : text.find("- **", start + 1)]
    stray = re.findall(r"review by \d{4}-\d{2}-\d{2}", entry)
    assert not stray, f"the changelog entry writes a review day as text: {stray}"
    assert "review by the earliest review date" in entry, (
        "the changelog entry does not name the review day by rule"
    )
