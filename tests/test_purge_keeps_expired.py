"""E11 M3, lead verdict (a): the purge deletes only SETTLED rows (a settled row, and a row released by 0008, which
looks like a settled row at 0 with `closed_at` set) older than the bound. An EXPIRED hold nobody settled is kept: it
is still booked on the counters, and a late settle must still find it and count what the call really cost, above
the reserved amount too. Both stores; the PostgreSQL case runs through the real purge login."""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run, new_id, now
from hadavin_sdk.store.memory import MemoryStore

D = Decimal
AGENT = "agent-a"
DAY = date(now().year - 1, 1, 31)
BIG = D("1000")
FAR = timedelta(days=1)


def _status(rows, rid):
    return rows[rid].status, rows[rid].settled_usd


def test_memory_purge_keeps_an_expired_hold_and_a_late_settle_still_counts():
    s = MemoryStore()
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    s.create_run(run)
    settled, expired = new_id("res"), new_id("res")
    s.reserve_spend(settled, AGENT, DAY, D("1.00"), day_cap=BIG, month_cap=BIG)
    s.reserve_spend(expired, AGENT, DAY, D("2.00"), day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    s.settle_spend(settled, D("0.50"), agent_id=AGENT)
    with s._lock:  # age the open hold, then the real expire step
        r = s._reservations[expired]
        s._reservations[expired] = r.model_copy(update={"created_at": r.created_at - 2 * FAR})
    assert s.expire_spend_reservations(3600) == 1
    assert s.purge_spend_reservations(now() + FAR) == 1  # the settled row only
    assert set(s._reservations) == {expired}
    assert s.spend_totals(AGENT, DAY) == (D("2.50"), D("2.50"))
    row, first = s.settle_spend(
        expired, D("5.00"), agent_id=AGENT
    )  # a late settle above the reserved amount
    assert first is True and row.settled_usd == D("5.00")
    assert s.spend_totals(AGENT, DAY) == (D("5.50"), D("5.50"))
    assert s.get_run(run.run_id).cost_usd == D("5.00")
    assert s.purge_spend_reservations(now() + FAR) == 1  # settled now: purgeable


pg_dsn = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"), reason="HADAVIN_TEST_PG_DSN not set"
)

try:  # the fixture of the release tests (needs psycopg)
    from tests.test_release_expired_spend_pg import (  # noqa: F401
        _audit,
        _counters,
        _expire,
        _release,
        _reserve,
        release_world,
    )
    from tests.test_release_expired_spend_pg import (
        _status as _pg_status,
    )
except ImportError:  # pragma: no cover - psycopg missing
    release_world = None


@pg_dsn
def test_pg_purge_keeps_expired_deletes_settled_and_released_and_a_late_settle_counts(w):
    rt, purge = w.store(w.runtime), w.store(w.purge)
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    rt.create_run(run)
    settled = _reserve(rt, "1.00")
    rt.settle_spend(settled, D("0.50"), agent_id=AGENT)
    released = _reserve(rt, "2.00")
    late = new_id("res")
    rt.reserve_spend(late, AGENT, DAY, D("4.00"), day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    _expire(w, released, late)
    _release(w)  # releases every expired hold of the day, `late` included
    # a second, expired hold that stays unreleased
    keep = new_id("res")
    rt.reserve_spend(keep, AGENT, DAY, D("8.00"), day_cap=BIG, month_cap=BIG, run_id=run.run_id)
    _expire(w, keep)
    assert _pg_status(w, released) == ("settled", 0) and _pg_status(w, keep)[0] == "expired"
    before = _counters(w)
    assert purge.purge_spend_reservations(now() + FAR) == 3  # settled + the two released
    left = w.run("SELECT reservation_id, status FROM spend_reservations")
    assert left == [(keep, "expired")]
    assert _counters(w) == before  # a purge moves no counter
    row, first = rt.settle_spend(keep, D("20.00"), agent_id=AGENT)  # late, above the reserved 8.00
    assert first is True and row.settled_usd == D("20.00")
    assert _counters(w) == (before[0] + D("12.00"), before[1] + D("12.00"))
    assert rt.get_run(run.run_id).cost_usd == D("20.00")
    assert purge.purge_spend_reservations(now() + FAR) == 1
