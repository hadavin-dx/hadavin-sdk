"""The changelog states the days the dated lists start to fail, as the dated lists have them.

Kept apart from tests/test_policy_guard.py because that file is copied alone into the temporary folder the
mutation runner uses, and the changelog is not part of that copy."""

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
