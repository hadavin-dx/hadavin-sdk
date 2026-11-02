"""Release-reservation money path: a take-back removes the same amount from the day and the month counter
(min(amount, day total)), so month never drops below the sum of its days and Postgres agrees with the memory store."""

from __future__ import annotations

import datetime
import random
from decimal import Decimal

from hadavin_sdk.store.memory import MemoryStore
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_core_hardening_round2 import _pg_store

D = Decimal
DAYS = [
    datetime.date(2026, 3, 1),
    datetime.date(2026, 3, 9),
    datetime.date(2026, 3, 30),
    datetime.date(2026, 4, 2),
]


def test_a_take_back_larger_than_the_day_does_not_eat_other_days_month_headroom():
    # Day D holds 0.30 of a 40.00 month: taking back 1.00 may only remove the 0.30 that sits on D.
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            store.settle_spend([("a", datetime.date(2026, 3, 1), D("39.70"))])
            store.settle_spend([("a", datetime.date(2026, 3, 9), D("0.30"))])
            store.settle_spend([("a", datetime.date(2026, 3, 9), D("-1.00"))])
            assert store.spend_totals("a", datetime.date(2026, 3, 9)) == (D("0"), D("39.70"))
            assert store.spend_totals("a", datetime.date(2026, 3, 1))[0] == D("39.70")
        finally:
            store.close()


def test_a_take_back_for_a_day_with_no_row_changes_nothing():
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            store.settle_spend([("a", datetime.date(2026, 3, 1), D("5"))])
            store.settle_spend([("a", datetime.date(2026, 3, 20), D("-2"))])  # no row for that day
            assert store.spend_totals("a", datetime.date(2026, 3, 1)) == (D("5"), D("5"))
            assert store.spend_totals("a", datetime.date(2026, 3, 20)) == (D("0"), D("5"))
        finally:
            store.close()


def test_postgres_and_memory_agree_and_month_is_always_the_sum_of_its_days():
    rng = random.Random(48)  # noqa: S311 - a seeded test generator
    for dsn in pg_schema():
        pg, mem = _pg_store(dsn), MemoryStore()
        try:
            for _ in range(150):
                day = rng.choice(DAYS)
                amount = D(rng.randint(1, 900)) / 100
                delta = amount if rng.random() < 0.5 else -amount
                for s in (pg, mem):
                    s.settle_spend([("a", day, delta)])
                for d in DAYS:
                    assert pg.spend_totals("a", d) == mem.spend_totals("a", d)
                for month in (3, 4):
                    days = [d for d in DAYS if d.month == month]
                    assert pg.spend_totals("a", days[0])[1] == sum(
                        (pg.spend_totals("a", d)[0] for d in days), D(0)
                    )
        finally:
            pg.close()


def test_release_reservation_command_takes_the_same_from_both_counters():
    from psycopg import sql  # noqa: F401 - skip cleanly without the driver

    from hadavin_sdk.store.migrate import release_reservation

    for dsn in pg_schema():
        pg = _pg_store(dsn)
        try:
            pg.settle_spend([("a", datetime.date(2026, 3, 1), D("39.70"))])
            pg.settle_spend([("a", datetime.date(2026, 3, 9), D("0.30"))])
            before, after = release_reservation(dsn, "a", datetime.date(2026, 3, 9), D("1.00"))
            assert (before, after) == ((D("0.30"), D("40.00")), (D("0"), D("39.70")))
        finally:
            pg.close()


def test_a_nested_fallback_keeps_the_inner_carried_bill_when_the_outer_primary_lost_nothing():
    from hadavin_sdk.llm.protocol import ProviderExhausted
    from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
    from tests.test_pr48_review6 import FreshRaises, Stub, _fallback_reply

    def make_inner():  # a fresh breaker each time: an open circuit would send nothing and carry nothing
        return ResilientLLM(
            FreshRaises(ProviderExhausted, "read timeout"),  # unknown billing
            Stub(_fallback_reply()),
            CircuitBreaker(failures=1, reset_after_s=60.0),
            fallback_metered=True,
        )

    assert make_inner().chat([], system="", route="r").prior_unknown_requests == 1
    inner = make_inner()
    outer = ResilientLLM(
        FreshRaises(
            ProviderExhausted, "x", attempts=0, refused=0
        ),  # provably sent nothing: lost == 0
        inner,
        CircuitBreaker(failures=1, reset_after_s=60.0),
        fallback_metered=True,
    )
    assert outer.chat([], system="", route="r").prior_unknown_requests == 1


def test_driver_errors_are_typed_refusals_at_both_guards_with_distinct_messages():
    import psycopg
    import pytest

    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            # (a) the connector fails: the borrow guard says "cannot connect"
            def broken():
                raise psycopg.OperationalError("host=db.internal user=svc")

            store._connector, store._idle = broken, type(store._idle)()
            with pytest.raises(StoreUnavailable, match="cannot connect") as e:
                store.settle_spend([("a", DAYS[0], D("1"))])
            assert "db.internal" not in str(e.value)
        finally:
            store.close()
        store = _pg_store(dsn)
        try:
            # (b) a driver error inside the work of a healthy connection: the spend-tx guard says "operation failed"
            def work(conn):
                raise psycopg.OperationalError("host=db.internal user=svc")

            with pytest.raises(StoreUnavailable, match="spend operation failed") as e:
                store._spend_tx(work)
            assert "db.internal" not in str(e.value) and "svc" not in str(e.value)
        finally:
            store.close()
