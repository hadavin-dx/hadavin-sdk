"""F-money-definer step 6, second half: `hadavin_reserve_spend` has five arguments and reads the caps of the agent from
`hadavin_caps`. These tests run WITHOUT the test hook that seeds the table (marker `no_cap_seed`): T3/T6 a runtime login
reserving for an agent with no row is refused (HD005, fail closed), T9a a table value that differs from the argument
wins, T4 day and month are distinct values, T11 no overload with cap arguments exists. `caps_battery` is shared with
the mutant file. Real PostgreSQL 16, real logins. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import psycopg
import pytest
from psycopg import sql

from hadavin_sdk.config import ConfigError
from hadavin_sdk.models import new_id
from hadavin_sdk.store.protocol import SpendCapExceeded
from tests.money_caps_seed import seed_caps
from tests.test_stop_state_roles import World

D = Decimal
DAY = date(2026, 1, 15)
AGENT = "agent-caps"
HUGE = D(10) ** 30
pytestmark = [
    pytest.mark.no_cap_seed,
    pytest.mark.skipif(
        not os.environ.get("HADAVIN_TEST_PG_DSN"),
        reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
    ),
]
FIVE_ARGS = "p_id text, p_agent text, p_day date, p_usd numeric, p_run_id text"


@pytest.fixture(name="w")
def caps_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        world.migrate()
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _seed(w, agent, day_cap, month_cap):
    seed_caps(w.scoped, w.schema, agent, day_cap, month_cap)


def _reserve(store, agent, usd, *, arg_day=HUGE, arg_month=HUGE):
    store.reserve_spend(new_id("res"), agent, DAY, D(usd), day_cap=arg_day, month_cap=arg_month)


def _refused_by(store, agent, usd, which, **args):
    with pytest.raises(SpendCapExceeded) as err:
        _reserve(store, agent, usd, **args)
    assert str(err.value).startswith(which) or which in str(err.value)


def caps_battery(w):
    """Every behaviour of the table read; raises on the first one that is wrong. Used by the mutant file."""
    rt = w.store(w.runtime)
    # T11: exactly one function of that name, with the five arguments
    found = w.run(
        "SELECT pg_get_function_identity_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s AND p.proname = 'hadavin_reserve_spend'",
        (w.schema,),
    )
    assert found == [(FIVE_ARGS,)], found
    # T3/T6: no row: refused, nothing booked
    with pytest.raises(ConfigError, match="no cap for this agent"):
        _reserve(rt, "no-row", "1")
    assert w.run("SELECT count(*) FROM spend WHERE agent_id = 'no-row'") == [(0,)]
    # T9a: the table wins over the argument, both directions; T4: day and month are distinct values
    _seed(w, "low-day", D("1"), HUGE)
    _refused_by(rt, "low-day", "2", "day", arg_day=HUGE, arg_month=HUGE)
    _seed(w, "low-month", HUGE, D("3"))
    _refused_by(rt, "low-month", "4", "month")
    _seed(w, "high", HUGE, HUGE)
    _reserve(rt, "high", "2", arg_day=D("1"), arg_month=D("1"))  # the argument is ignored
    _seed(w, "exact", D("5"), D("50"))
    _reserve(rt, "exact", "5")  # up to the cap is allowed
    _refused_by(rt, "exact", "0.000001", "day")  # one micro-dollar over the day cap
    _refused_by(
        rt, "exact", "0", "day"
    )  # M10: a zero amount at the cap is refused too (usd < cap leg)
    # the month cap exactly, day cap far above it (day above month): the month leg and its boundary
    _seed(w, "exm", HUGE, D("7"))
    _reserve(rt, "exm", "7")  # up to the month cap is allowed (<=, not <)
    _refused_by(rt, "exm", "0", "month")  # zero amount at the month cap: refused (m.usd < cap leg)
    _refused_by(rt, "exm", "0.000001", "month")
    # a ZERO cap is a cap of zero, never "unlimited" (M10)
    _seed(w, "zero", D("0"), HUGE)
    _refused_by(rt, "zero", "1", "day")
    _refused_by(rt, "zero", "0", "day")
    _seed(w, "zero-m", HUGE, D("0"))
    _refused_by(rt, "zero-m", "1", "month")
    _cap_function_battery(w)


def _cap_function_battery(w):
    """`hadavin_set_cap` (an upsert that overwrites BOTH caps) and `hadavin_cap_matches` (same only when BOTH caps
    are equal, differs otherwise, missing without a row)."""
    rs, rt = w.store(w.reset), w.store(w.runtime)
    assert rt.cap_matches("cm-agent", D("3"), D("30")) == "missing"
    rs.set_cap("cm-agent", D("3"), D("30"), "user:op")
    assert rt.cap_matches("cm-agent", D("3"), D("30")) == "same"
    assert rt.cap_matches("cm-agent", D("3"), D("31")) == "differs"  # only the day cap matches
    assert rt.cap_matches("cm-agent", D("4"), D("30")) == "differs"  # only the month cap matches
    assert rt.cap_matches("cm-agent", D("4"), D("31")) == "differs"
    rs.set_cap("cm-agent", D("5"), D("50"), "user:op2")  # the upsert replaces both caps
    assert rt.cap_matches("cm-agent", D("5"), D("50")) == "same"
    assert rt.cap_matches("cm-agent", D("3"), D("30")) == "differs"
    assert rt.cap_matches("cm-agent", D("5"), D("30")) == "differs"
    assert rt.cap_matches("cm-agent", D("3"), D("50")) == "differs"


@pytest.mark.no_cap_seed
def test_a_missing_cap_row_through_limits_refuses_with_the_sync_caps_hint(w, caplog):
    """End to end on Postgres (no seeding hook): `Limits.reserve` for an agent with no cap row is refused as
    `limits_unavailable`, the log tells the operator to run sync-caps, and no counter row exists."""
    import logging

    from hadavin_sdk.limits import Limits, SpendRefused

    store = w.store(w.runtime)
    agent = SimpleNamespace(
        id=AGENT, status="live", budget_usd=SimpleNamespace(daily=D("5"), monthly=D("50"))
    )
    registry = SimpleNamespace(agents={AGENT: agent})
    limits = Limits(store, SimpleNamespace(), registry)
    with caplog.at_level(logging.WARNING), pytest.raises(SpendRefused) as err:
        limits.reserve(AGENT, D("1"))
    assert "limits_unavailable" in str(err.value)
    assert any("sync-caps" in r.getMessage() for r in caplog.records)
    assert w.run("SELECT count(*) FROM spend") == [(0,)]


def test_t6_a_runtime_login_with_no_cap_row_is_refused_fail_closed(w):
    rt = w.store(w.runtime)
    with pytest.raises(ConfigError, match="no cap for this agent: run limits sync-caps"):
        _reserve(rt, AGENT, "1")
    assert w.run("SELECT count(*) FROM spend_reservations") == [(0,)]
    with w.as_(w.runtime) as db, pytest.raises(psycopg.Error) as err:
        db.execute("SELECT hadavin_reserve_spend('r1', %s, %s, 1, NULL)", (AGENT, DAY))
    assert err.value.sqlstate == "HD005"


def test_t9a_the_table_cap_wins_over_the_argument_in_both_directions(w):
    rt = w.store(w.runtime)
    _seed(w, AGENT, D("1"), D("100"))
    _refused_by(rt, AGENT, "2", "day", arg_day=HUGE, arg_month=HUGE)
    _seed(w, "other", HUGE, HUGE)
    _reserve(rt, "other", "2", arg_day=D("1"), arg_month=D("1"))


def test_t4_day_and_month_caps_are_distinct_values_and_not_swapped(w):
    rt = w.store(w.runtime)
    _seed(w, "d", D("3"), D("100"))
    _refused_by(rt, "d", "4", "day")
    _seed(w, "m", D("100"), D("3"))
    _refused_by(rt, "m", "4", "month")


def test_t4_a_cap_changed_by_the_owner_takes_effect_on_the_next_reserve(w):
    rt = w.store(w.runtime)
    _seed(w, AGENT, D("10"), D("10"))
    _reserve(rt, AGENT, "6")
    _seed(w, AGENT, D("5"), D("10"))  # lowered below the booked total
    _refused_by(rt, AGENT, "0", "day")  # even a zero amount is refused when usd >= cap
    assert w.run("SELECT usd FROM spend WHERE agent_id = %s", (AGENT,)) == [(D("6"),)]
    _seed(w, AGENT, D("20"), D("20"))
    _reserve(rt, AGENT, "6")


def test_t11_no_overload_with_cap_arguments_exists(w):
    assert w.run(
        "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s AND p.proname = 'hadavin_reserve_spend'",
        (w.schema,),
    ) == [(1,)]
    assert w.run(
        "SELECT pg_get_function_identity_arguments(p.oid) FROM pg_proc p WHERE p.oid = "
        "to_regprocedure('hadavin_reserve_spend(text, text, date, numeric, text)')"
    ) == [(FIVE_ARGS,)]


def test_the_whole_battery_passes_on_the_real_sql(w):
    caps_battery(w)
