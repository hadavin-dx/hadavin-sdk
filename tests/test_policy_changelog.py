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


def test_the_sixteen_pending_kinds_each_stand_on_the_day_they_were_decided():
    # `decided` is pinned apart from the tool's own date: moving that date to renew the names and claims must
    # not renew these kinds, and the 92-day cap compares `review_by` with `decided`.
    assert len(PENDING_KINDS) == 16, "the number of pending kinds is not 16"
    assert {p.decided for p in PENDING_KINDS.values()} == {date(2026, 11, 11)}, (
        "a pending kind has a `decided` day other than 2026-11-11"
    )
    assert max((p.review_by - p.decided).days for p in PENDING_KINDS.values()) <= 92, (
        "a pending kind is more than 92 days from its decision to its review day"
    )
