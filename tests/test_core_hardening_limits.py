"""G-04 / R214: reserve-then-settle never overshoots a cap under concurrency (threads on one store; separate
connections on Postgres, which needs HADAVIN_TEST_PG_DSN and is skipped without it), plus the old check-then-charge
overshoot shown for contrast."""

from __future__ import annotations

import threading
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.config import Route
from hadavin_sdk.limits import Limits, OverBudget, worst_case_usd
from hadavin_sdk.models import KillSwitch, now
from hadavin_sdk.store.memory import MemoryStore

D = Decimal


def _limits(store, daily="1.00", monthly="10.00", max_run=None):
    agent = SimpleNamespace(
        budget_usd=SimpleNamespace(daily=D(daily), monthly=D(monthly)),
        max_run_usd=None if max_run is None else D(max_run),
    )
    return Limits(store, None, SimpleNamespace(agents={"a": agent}))  # type: ignore[arg-type]


def _hammer(limits, n, cost, run_id=None):
    gate, won, lost = threading.Barrier(n), [], []

    def one(i):
        gate.wait()
        try:
            won.append(limits.reserve("a", cost, run_id=run_id))
        except OverBudget as e:
            lost.append(e)

    ts = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return won, lost


def test_concurrent_reserve_never_exceeds_the_daily_cap():
    store = MemoryStore()
    limits = _limits(store, daily="1.00")
    won, lost = _hammer(limits, 64, D("0.10"))  # room for exactly 10
    assert len(won) == 10 and len(lost) == 54
    assert store.spend_totals("a", now().date())[0] == D("1.00")
    assert all(e.reasons == ["daily_budget"] for e in lost)


def test_monthly_cap_binds_and_names_itself():
    store = MemoryStore()
    limits = _limits(store, daily="100", monthly="0.30")
    won, lost = _hammer(limits, 16, D("0.10"))
    assert len(won) == 3 and lost[0].reasons == ["monthly_budget"]


def test_per_run_cap_and_its_rollback():
    store = MemoryStore()
    limits = _limits(store, daily="100", monthly="100", max_run="0.50")
    won, lost = _hammer(limits, 20, D("0.10"), run_id="r1")
    assert len(won) == 5 and lost[0].reasons == ["run_budget"]
    assert store.spend_totals("a", now().date())[0] == D(
        "0.50"
    )  # refused calls booked nothing anywhere
    limits.reserve("a", D("0.10"))  # a call outside any run is not under the run cap


def test_run_share_is_returned_when_the_agent_cap_refuses():
    store = MemoryStore()
    limits = _limits(store, daily="0.05", max_run="1.00")
    with pytest.raises(OverBudget):
        limits.reserve("a", D("0.10"), run_id="r2")
    limits.reserve("a", D("0.05"), run_id="r2")
    assert store.spend_totals("run:r2", date(1970, 1, 1))[0] == D("0.05")


def test_settle_replaces_the_reservation_with_the_real_cost_and_frees_room():
    store = MemoryStore()
    limits = _limits(store, daily="1.00")
    res = limits.reserve("a", D("0.90"))
    with pytest.raises(OverBudget):
        limits.reserve("a", D("0.20"))
    limits.settle(res, D("0.10"))
    assert store.spend_totals("a", now().date())[0] == D("0.10")
    limits.reserve("a", D("0.80"))
    with pytest.raises(ValueError, match="already settled"):
        limits.settle(res, D("0.10"))


def test_cost_above_the_reservation_is_recorded_not_refused():
    store = MemoryStore()
    limits = _limits(store)
    limits.settle(limits.reserve("a", D("0.10")), D("0.30"))
    assert store.spend_totals("a", now().date())[0] == D("0.30")


def test_release_returns_everything():
    store = MemoryStore()
    limits = _limits(store, max_run="1")
    limits.release(limits.reserve("a", D("0.40"), run_id="r"))
    assert store.spend_totals("a", now().date()) == (0, 0)


def test_kill_switch_refuses_reserve():
    store = MemoryStore()
    store.set_kill_switch(KillSwitch(on=True, by="t"))
    with pytest.raises(OverBudget) as e:
        _limits(store).reserve("a", D("0.01"))
    assert e.value.reasons == ["kill_switch"]


def test_reserve_is_month_aware_across_days():
    store = MemoryStore()
    yesterday = now().date() - timedelta(days=1)
    if yesterday.month != now().date().month:
        pytest.skip("first of the month")
    store.add_spend("a", yesterday, D("9.95"))
    limits = _limits(store, daily="5", monthly="10")
    with pytest.raises(OverBudget) as e:
        limits.reserve("a", D("0.10"))
    assert e.value.reasons == ["monthly_budget"]


def test_old_check_then_charge_overshoots_under_concurrency():
    """The contrast (why reserve exists): every thread passes `blocked` before any charges."""
    store = MemoryStore()
    limits = _limits(store, daily="1.00")
    n, gate, passed = 32, threading.Barrier(32), []

    def old_way():
        ok = not limits.blocked("a")
        gate.wait()  # all have checked; none has charged
        if ok:
            passed.append(1)
            limits.charge("a", D("0.10"))

    ts = [threading.Thread(target=old_way) for _ in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert store.spend_totals("a", now().date())[0] == D("3.20") > D("1.00")


def test_worst_case_usd():
    r = Route(model_id="m", input_usd_per_mtok=D("3"), output_usd_per_mtok=D("15"), max_tokens=1000)
    assert worst_case_usd(r, 3000) == (D(1000) * 3 + D(1000) * 15) / D(1_000_000)


def test_postgres_separate_connections_never_exceed_the_cap():
    from tests.contracts.kinds.store_postgres import pg_schema

    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        stores = [make("store", settings, FakeSecretProvider({"pg-dsn": dsn})) for _ in range(4)]
        limitses = [_limits(s, daily="1.00", max_run="5") for s in stores]
        n, gate, won, lost = 40, threading.Barrier(40), [], []

        def one(i, limitses=limitses, gate=gate, won=won, lost=lost):
            gate.wait()
            try:
                won.append(limitses[i % 4].reserve("a", D("0.10"), run_id="r"))
            except OverBudget as e:
                lost.append(e)

        ts = [threading.Thread(target=one, args=(i,)) for i in range(n)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        assert len(won) == 10 and len(lost) == 30
        assert stores[0].spend_totals("a", now().date()) == (D("1.00"), D("1.00"))
        limitses[0].settle(won[0], D(0))
        assert stores[1].spend_totals("a", now().date())[0] == D("0.90")
        for s in stores:
            s._db.close()
