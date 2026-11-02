"""G-04 / R214: reserve-then-settle never overshoots a cap under concurrency (many threads released by a barrier on
one store; separate connections on Postgres, which needs HADAVIN_TEST_PG_DSN and is skipped without it); the
kill switch is read inside the same step as the booking; settle is atomic, once, and retryable."""

# ruff: noqa: B023
from __future__ import annotations

import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk import limits as limits_mod
from hadavin_sdk.config import Route
from hadavin_sdk.limits import (
    Limits,
    OverBudget,
    StoreLacksReserve,
    prompt_bytes,
    worst_case_usd,
)
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store.memory import MemoryStore

D = Decimal
MID_MONTH = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _fixed_clock(monkeypatch):
    """Mid-month, always: the month-aware tests never depend on the day the suite runs (and never skip)."""
    monkeypatch.setattr(limits_mod, "now", lambda: MID_MONTH)


@contextmanager
def fast_switching() -> Iterator[None]:
    """Make the interpreter switch threads every microsecond, so a missing lock shows up in a short test."""
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        yield
    finally:
        sys.setswitchinterval(old)


def _limits(store, daily="1.00", monthly="10.00", max_run=None):
    agent = SimpleNamespace(
        budget_usd=SimpleNamespace(daily=D(daily), monthly=D(monthly)),
        max_run_usd=None if max_run is None else D(max_run),
    )
    return Limits(store, None, SimpleNamespace(agents={"a": agent, "b": agent}))  # type: ignore[arg-type]


def _hammer(limitses, n, cost, run_id=None):
    """n threads released together by a barrier, each reserving once (round-robin over ``limitses``)."""
    gate, won, lost = threading.Barrier(n), [], []
    lock = threading.Lock()

    def one(i):
        gate.wait()
        try:
            r = limitses[i % len(limitses)].reserve("a", cost, run_id=run_id)
            with lock:
                won.append(r)
        except OverBudget as e:
            with lock:
                lost.append(e)

    ts = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return won, lost


class RacyStore(MemoryStore):
    """Check, yield, then add: the check-then-act bug in miniature. The harness must catch it."""

    def reserve_spend(self, agent_id, day, usd, daily_cap, monthly_cap, **kw):
        total = self.spend_totals(agent_id, day)[0]
        if total + usd > daily_cap:
            return ["daily_budget"]
        time.sleep(0.001)  # the window every concurrent caller falls through
        self.add_spend(agent_id, day, usd)
        return []


def test_the_harness_catches_a_racy_reserve():
    store = RacyStore()
    won, _ = _hammer([_limits(store, daily="1.00")], 32, D("0.10"))
    assert len(won) > 10 and store.spend_totals("a", MID_MONTH.date())[0] > D("1.00")


def test_concurrent_reserve_never_exceeds_the_daily_cap():
    with fast_switching():
        for _round in range(30):  # many rounds: a lock removed from the store fails within a few
            store = MemoryStore()
            won, lost = _hammer([_limits(store, daily="1.00")], 64, D("0.10"))
            assert len(won) == 10 and len(lost) == 54
            assert store.spend_totals("a", MID_MONTH.date())[0] == D("1.00")
            assert all(e.reasons == ["daily_budget"] for e in lost)


def test_monthly_cap_binds_and_names_itself():
    store = MemoryStore()
    won, lost = _hammer([_limits(store, daily="100", monthly="0.30")], 16, D("0.10"))
    assert len(won) == 3 and lost[0].reasons == ["monthly_budget"]


def test_month_total_counts_earlier_days_of_the_same_month_only():
    store = MemoryStore()
    store.add_spend("a", date(2026, 3, 14), D("9.95"))
    store.add_spend("a", date(2026, 2, 28), D("50"))  # last month: not counted
    limits = _limits(store, daily="5", monthly="10")
    with pytest.raises(OverBudget) as e:
        limits.reserve("a", D("0.10"))
    assert e.value.reasons == ["monthly_budget"]
    limits.reserve("a", D("0.05"))


def test_per_run_cap_is_atomic_with_the_agent_cap():
    store = MemoryStore()
    limits = _limits(store, daily="100", monthly="100", max_run="0.50")
    with fast_switching():
        won, lost = _hammer([limits], 40, D("0.10"), run_id="r1")
    assert len(won) == 5 and lost[0].reasons == ["run_budget"]
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.50")  # refused calls booked nothing
    limits.reserve("a", D("0.10"))  # a call outside any run is not under the run cap


def test_a_refusal_by_the_agent_cap_books_nothing_for_the_run_and_never_touches_add_spend():
    class Spy(MemoryStore):
        adds = 0

        def add_spend(self, *a, **k):
            Spy.adds += 1
            return super().add_spend(*a, **k)

    store = Spy()
    limits = _limits(store, daily="0.05", max_run="1.00")
    with pytest.raises(OverBudget):
        limits.reserve("a", D("0.10"), run_id="r2")
    assert store.spend_totals("run:r2", MID_MONTH.date()) == (0, 0) and Spy.adds == 0
    limits.reserve("a", D("0.05"), run_id="r2")
    assert store.spend_totals("run:r2", MID_MONTH.date())[0] == D("0.05")


def test_old_run_counters_are_pruned_and_recent_ones_kept():
    store = MemoryStore()
    limits = _limits(store, max_run="1")
    limits.reserve("a", D("0.1"), run_id="old", run_day=MID_MONTH.date() - timedelta(days=30))
    limits.reserve("a", D("0.1"), run_id="new")
    assert limits.prune_runs(keep_days=7) == 1
    assert store.spend_totals("run:old", MID_MONTH.date() - timedelta(days=30)) == (0, 0)
    assert store.spend_totals("run:new", MID_MONTH.date())[0] == D("0.1")
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.2")  # agent totals are never pruned


def test_settle_replaces_the_reservation_with_the_real_cost_and_frees_room():
    store = MemoryStore()
    limits = _limits(store, daily="1.00")
    res = limits.reserve("a", D("0.90"))
    with pytest.raises(OverBudget):
        limits.reserve("a", D("0.20"))
    limits.settle(res, D("0.10"))
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.10")
    limits.reserve("a", D("0.80"))


def test_cost_above_the_reservation_is_recorded_not_refused():
    store = MemoryStore()
    limits = _limits(store)
    limits.settle(limits.reserve("a", D("0.10")), D("0.30"))
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.30")


def test_release_returns_everything_and_release_after_settle_is_refused():
    store = MemoryStore()
    limits = _limits(store, max_run="1")
    res = limits.reserve("a", D("0.40"), run_id="r")
    limits.release(res)
    assert store.spend_totals("a", MID_MONTH.date()) == (0, 0)
    assert store.spend_totals("run:r", MID_MONTH.date()) == (0, 0)
    with pytest.raises(ValueError, match="already settled"):
        limits.release(res)
    done = limits.reserve("a", D("0.40"))
    limits.settle(done, D("0.10"))
    with pytest.raises(ValueError, match="already settled"):
        limits.release(done)
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.10")


def test_concurrent_double_settle_applies_exactly_once():
    store = MemoryStore()
    limits = _limits(store, daily="5")
    with fast_switching():
        for _ in range(20):
            res = limits.reserve("a", D("0.50"))
            gate, ok, bad = threading.Barrier(16), [], []

            def one(res=res, gate=gate, ok=ok, bad=bad):
                gate.wait()
                try:
                    limits.settle(res, D("0.20"))
                    ok.append(1)
                except ValueError:
                    bad.append(1)

            ts = [threading.Thread(target=one) for _ in range(16)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            assert (len(ok), len(bad)) == (1, 15)
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.20") * 20


def test_settle_after_a_store_failure_can_be_retried_and_the_cost_is_not_lost():
    class Flaky(MemoryStore):
        fail = True

        def settle_spend(self, deltas):
            if Flaky.fail:
                raise OSError("store down")
            super().settle_spend(deltas)

    store = Flaky()
    limits = _limits(store, max_run="5")
    res = limits.reserve("a", D("0.10"), run_id="r")
    with pytest.raises(OSError):
        limits.settle(res, D("0.35"))  # the real cost is above the reservation
    assert not res.settled and not res.settling
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.10")  # nothing half-applied
    Flaky.fail = False
    limits.settle(res, D("0.35"))
    assert store.spend_totals("a", MID_MONTH.date())[0] == D("0.35")
    assert store.spend_totals("run:r", MID_MONTH.date())[0] == D("0.35")
    with pytest.raises(ValueError, match="already settled"):
        limits.settle(res, D("0.35"))


def test_the_kill_switch_is_read_in_the_same_step_as_the_booking():
    """A store whose separate switch read is stale (always off) must still refuse: Limits no longer asks it."""

    class StaleRead(MemoryStore):
        def get_kill_switch(self):
            return KillSwitch(on=False, by="stale")

    store = StaleRead()
    store.set_kill_switch(KillSwitch(on=True, by="t"))
    with pytest.raises(OverBudget) as e:
        _limits(store).reserve("a", D("0.01"))
    assert e.value.reasons == ["kill_switch"]
    assert store.spend_totals("a", MID_MONTH.date()) == (0, 0)


def test_no_reservation_starts_after_the_switch_returned():
    store = MemoryStore()
    limits = _limits(store, daily="1e9", monthly="1e9")
    log, stop, lock = [], threading.Event(), threading.Lock()

    def worker():
        while not stop.is_set():
            began = time.monotonic()
            try:
                limits.reserve("a", D("0.01"))
                ok = True
            except OverBudget:
                ok = False
            with lock:
                log.append((began, ok))

    ts = [threading.Thread(target=worker) for _ in range(8)]
    with fast_switching():
        for t in ts:
            t.start()
        time.sleep(0.05)
        store.set_kill_switch(KillSwitch(on=True, by="t"))
        flipped = time.monotonic()
        time.sleep(0.05)
        stop.set()
        for t in ts:
            t.join()
    assert any(ok for _, ok in log)
    assert not [b for b, ok in log if ok and b > flipped]


def test_a_store_without_reserve_is_a_typed_error_at_construction():
    class Old:  # a custom store written before R214
        def get_kill_switch(self): ...
        def add_spend(self, *a): ...
        def spend_totals(self, *a): ...

    with pytest.raises(StoreLacksReserve, match="reserve_spend, settle_spend, prune_spend"):
        Limits(Old(), None, SimpleNamespace(agents={}))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad", [D("NaN"), D("Infinity"), D("-Infinity"), D("-0.01"), 0.1, "1", None]
)
def test_money_inputs_are_checked_the_same_way_everywhere(bad):
    limits = _limits(MemoryStore())
    res = limits.reserve("a", D("0.10"))
    with pytest.raises(ValueError):
        limits.reserve("a", bad)
    with pytest.raises(ValueError):
        limits.settle(res, bad)
    with pytest.raises(ValueError):
        limits.charge("a", bad)
    assert not res.settled and not res.settling  # a rejected settle leaves it settle-able
    limits.settle(res, D("0.05"))


# --- the worst case is an upper bound -------------------------------------------------------------------------


def _route(per_token="1"):  # noqa: S107 - a ratio, not a password
    return Route(
        model_id="m",
        input_usd_per_mtok=D("3"),
        output_usd_per_mtok=D("15"),
        max_tokens=1000,
        prompt_bytes_per_token=D(per_token),
    )


def test_prompt_bytes_counts_system_documents_tools_schema_and_messages():
    base = prompt_bytes([{"role": "user", "content": "hi"}])
    assert prompt_bytes([{"role": "user", "content": "hi"}], system="s" * 100) == base + 100
    assert prompt_bytes([{"role": "user", "content": "hi"}], documents=[b"x" * 50]) == base + 150
    with_tools = prompt_bytes([{"role": "user", "content": "hi"}], tools=[{"name": "t" * 200}])
    assert with_tools > base + 200
    assert (
        prompt_bytes([{"role": "user", "content": "hi"}], output_schema={"a": "b" * 300})
        > base + 300
    )
    assert (
        prompt_bytes([{"role": "user", "content": "é"}]) == base - 2 + 2 + 0
    )  # utf-8 bytes, not characters


def test_a_document_of_invalid_bytes_is_priced_as_replacement_characters():
    bad = b"\xff" * 1000  # decoded with "replace" each becomes U+FFFD, 3 bytes
    sent = len(bad.decode("utf-8", "replace").encode("utf-8"))
    assert prompt_bytes([], documents=[bad]) >= sent


def test_worst_case_is_the_input_bound_plus_max_tokens_and_the_ratio_is_config():
    r = _route("1")
    assert worst_case_usd(r, 3000) == (D(3000) * 3 + D(1000) * 15) / D(1_000_000)
    assert worst_case_usd(_route("4"), 4001) == (D(1001) * 3 + D(1000) * 15) / D(
        1_000_000
    )  # ceiling: 4001 / 4 -> 1001
    with pytest.raises(ValueError):
        worst_case_usd(r, -1)


def test_worst_case_builds_no_giant_string(monkeypatch):
    import tracemalloc

    tracemalloc.start()
    worst_case_usd(_route(), 500_000_000)  # half a gigabyte of prompt, as a number
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert peak < 100_000


def test_postgres_separate_connections_hold_every_cap():
    from tests.contracts.kinds.store_postgres import pg_schema

    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        stores = [make("store", settings, FakeSecretProvider({"pg-dsn": dsn})) for _ in range(4)]
        try:
            # daily cap binds: 10 of 40
            limitses = [_limits(s, daily="1.00", max_run="50") for s in stores]
            won, lost = _hammer(limitses, 40, D("0.10"), run_id="r")
            assert len(won) == 10 and len(lost) == 30
            assert stores[0].spend_totals("a", MID_MONTH.date()) == (D("1.00"), D("1.00"))
            limitses[0].settle(won[0], D(0))
            assert stores[1].spend_totals("a", MID_MONTH.date())[0] == D("0.90")
            assert stores[2].spend_totals("run:r", MID_MONTH.date())[0] == D("0.90")

            # max_run binds across connections: 5 of 40, and the agent got exactly those 5
            run_limits = [_limits(s, daily="100", monthly="100", max_run="0.50") for s in stores]
            for s in stores:
                s.add_spend("b", MID_MONTH.date(), D(0))
            won, lost = _hammer_agent("b", run_limits, 40, D("0.10"), run_id="rb")
            assert len(won) == 5 and all(e.reasons == ["run_budget"] for e in lost)
            assert stores[3].spend_totals("b", MID_MONTH.date())[0] == D("0.50")

            # a double settle across connections applies once
            res = won[0]
            outcomes = []

            def settle(i, res=res, outcomes=outcomes):
                try:
                    run_limits[i % 4].settle(res, D("0.05"))
                    outcomes.append("ok")
                except ValueError:
                    outcomes.append("dup")

            ts = [threading.Thread(target=settle, args=(i,)) for i in range(8)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            assert outcomes.count("ok") == 1
            assert stores[0].spend_totals("b", MID_MONTH.date())[0] == D("0.50") - D("0.05")
        finally:
            for s in stores:
                s.close()


def _hammer_agent(agent, limitses, n, cost, run_id):
    gate, won, lost, lock = threading.Barrier(n), [], [], threading.Lock()

    def one(i):
        gate.wait()
        try:
            r = limitses[i % len(limitses)].reserve(agent, cost, run_id=run_id)
            with lock:
                won.append(r)
        except OverBudget as e:
            with lock:
                lost.append(e)

    ts = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return won, lost


def test_postgres_kill_switch_flip_is_seen_by_every_later_reserve():
    from tests.contracts.kinds.store_postgres import pg_schema

    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        stores = [make("store", settings, FakeSecretProvider({"pg-dsn": dsn})) for _ in range(4)]
        try:
            lims = [_limits(s, daily="1e6", monthly="1e6") for s in stores]
            log, stop, lock = [], threading.Event(), threading.Lock()

            def worker(i):
                while not stop.is_set():
                    began = time.monotonic()
                    try:
                        lims[i % 4].reserve("a", D("0.01"))
                        ok = True
                    except OverBudget:
                        ok = False
                    with lock:
                        log.append((began, ok))

            ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
            for t in ts:
                t.start()
            time.sleep(0.5)
            stores[0].set_kill_switch(KillSwitch(on=True, by="t"))
            flipped = time.monotonic()
            time.sleep(0.5)
            stop.set()
            for t in ts:
                t.join()
            assert any(ok for _, ok in log)
            assert not [b for b, ok in log if ok and b > flipped]
            assert [1 for _, ok in log if not ok]  # and some were refused after the flip
        finally:
            for s in stores:
                s.close()


def test_postgres_lock_wait_is_bounded_retried_and_does_not_hold_the_process_lock():
    from tests.contracts.kinds.store_postgres import pg_schema

    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        store.LOCK_TIMEOUT_MS, store.RESERVE_ATTEMPTS = 200, 2
        lims = _limits(store)
        lims.reserve("a", D("0.01"))  # creates the counter rows
        holder = psycopg.connect(dsn, autocommit=False)
        try:
            holder.execute(
                "SELECT usd FROM spend WHERE agent_id = 'a' FOR UPDATE"
            )  # a stuck writer
            result = []

            def blocked():
                t0 = time.monotonic()
                try:
                    lims.reserve("a", D("0.01"))
                except Exception as e:  # noqa: BLE001 - recorded, asserted below
                    result.append((time.monotonic() - t0, f"{type(e).__name__}: {e}"))

            t = threading.Thread(target=blocked)
            t.start()
            time.sleep(0.3)  # the reserve is now waiting on the row lock
            t0 = time.monotonic()
            store.get_kill_switch()  # takes the process lock: must not queue behind the row-lock wait
            assert time.monotonic() - t0 < 0.1
            t.join(60)
            elapsed, msg = result[0]
            assert 0.3 < elapsed < 5 and "busy" in msg  # 2 attempts of ~200 ms, then fail closed
        finally:
            holder.rollback()
            holder.close()
            store.close()


def test_postgres_serialization_failures_are_retried_a_bounded_number_of_times():
    from tests.contracts.kinds.store_postgres import pg_schema

    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        try:
            calls = []

            def flaky(conn, fail_times):
                calls.append(1)
                if len(calls) <= fail_times:
                    raise psycopg.errors.SerializationFailure()
                return "done"

            assert store._spend_tx(lambda c: flaky(c, 2)) == "done" and len(calls) == 3
            calls.clear()
            with pytest.raises(StoreUnavailable, match="busy"):
                store._spend_tx(lambda c: flaky(c, 99))
            assert len(calls) == store.RESERVE_ATTEMPTS
        finally:
            store.close()
