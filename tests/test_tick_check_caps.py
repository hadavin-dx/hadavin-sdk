"""F-money-definer step 6, the tick step `check_caps`: the caps of the registry are compared with the caps table
through `hadavin_cap_matches` under the RUNTIME login. Any difference or missing row fails the step loudly (the
tick exits 1, the failure names agent ids and states, never a cap value). Quiet when everything matches; a retired
agent is neither checked nor reported; a store without a cap table (memory) has nothing to check.
Real PostgreSQL 16, a throwaway schema and real logins with unique names, dropped after. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.models import now
from hadavin_sdk.runtime import tick
from hadavin_sdk.store.memory import MemoryStore
from tests.test_stop_state_roles import World

D = Decimal
needs_pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _agent(agent_id, daily, monthly, status="live"):
    return SimpleNamespace(
        id=agent_id, status=status, budget_usd=SimpleNamespace(daily=D(daily), monthly=D(monthly))
    )


def _app(store, *agents):
    return SimpleNamespace(store=store, registry=SimpleNamespace(agents={a.id: a for a in agents}))


def _step():
    (step,) = [s for s in tick.STEPS if s.name == "check_caps"]
    return step


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


def _seed(w, agent, daily, monthly):
    w.store(w.reset).set_cap(agent, D(daily), D(monthly), "user:op")


def test_the_step_is_registered_once_and_runs_every_tick():
    assert [s.name for s in tick.STEPS].count("check_caps") == 1
    assert _step().every_s == 0  # every tick: a drift is loud within one tick period


def test_a_store_without_a_cap_table_has_nothing_to_check():
    app = _app(MemoryStore(), _agent("a", "1", "10"))
    tick.check_caps(tick.TickContext(app, now()))  # no exception


@needs_pg
def test_quiet_when_every_agent_matches(w):
    _seed(w, "a", "1.00", "10.00")
    _seed(w, "b", "2", "20")
    app = _app(w.store(w.runtime), _agent("a", "1.00", "10.00"), _agent("b", "2", "20"))
    tick.check_caps(tick.TickContext(app, now()))


@needs_pg
def test_a_lowered_registry_cap_is_a_loud_failure_naming_the_agent_only(w):
    _seed(w, "a", "1.00", "10.00")  # the table still holds the old, higher day cap
    _seed(w, "b", "2", "20")
    app = _app(w.store(w.runtime), _agent("a", "0.50", "10.00"), _agent("b", "2", "20"))
    with pytest.raises(tick.CapsDrift) as caught:
        tick.check_caps(tick.TickContext(app, now()))
    text = str(caught.value)
    assert "a:differs" in text and "b:" not in text  # b matches: not named
    assert "0.50" not in text and "1.00" not in text and "10.00" not in text  # no value


@needs_pg
def test_a_raised_registry_cap_alerts_too_documented_divergence_from_t13(w):
    """`cap_matches` answers same/differs/missing and the runtime has no table right, so the direction is unknown:
    a RAISED registry cap (safe: the table is stricter) is reported like a lowered one until `sync-caps` runs."""
    _seed(w, "a", "1.00", "10.00")
    app = _app(w.store(w.runtime), _agent("a", "2.00", "10.00"))  # raised above the table
    with pytest.raises(tick.CapsDrift, match="a:differs"):
        tick.check_caps(tick.TickContext(app, now()))


@needs_pg
def test_a_database_error_for_one_agent_names_it_and_the_others_are_still_checked(w):
    _seed(w, "a", "1", "10")
    bad_id = (
        "x" * 5000
    )  # check_store_id refuses it in Python; the message carries only 64 characters of it
    app = _app(w.store(w.runtime), _agent("a", "9", "10"), _agent(bad_id, "1", "10"))
    with pytest.raises(tick.CapsDrift) as caught:
        tick.check_caps(tick.TickContext(app, now()))
    text = str(caught.value)
    assert "a:differs" in text and f"{bad_id[:64]}:error" in text and bad_id not in text


@needs_pg
def test_a_missing_row_is_a_loud_failure(w):
    _seed(w, "a", "1", "10")
    app = _app(w.store(w.runtime), _agent("a", "1", "10"), _agent("new-agent", "3", "30"))
    with pytest.raises(tick.CapsDrift, match="new-agent:missing"):
        tick.check_caps(tick.TickContext(app, now()))


@needs_pg
def test_every_difference_is_named_not_only_the_first(w):
    _seed(w, "a", "1", "10")
    app = _app(w.store(w.runtime), _agent("a", "9", "10"), _agent("z", "3", "30"))
    with pytest.raises(tick.CapsDrift) as caught:
        tick.check_caps(tick.TickContext(app, now()))
    assert "a:differs" in str(caught.value) and "z:missing" in str(caught.value)


@needs_pg
def test_a_retired_agent_is_neither_checked_nor_reported(w):
    _seed(w, "a", "1", "10")
    app = _app(
        w.store(w.runtime),
        _agent("a", "1", "10"),
        _agent("old", "4", "40", status="retired"),  # no row, never synced: no alert
    )
    tick.check_caps(tick.TickContext(app, now()))


@needs_pg
def test_a_draft_agent_is_checked(w):
    app = _app(w.store(w.runtime), _agent("d", "1", "10", status="draft"))
    with pytest.raises(tick.CapsDrift, match="d:missing"):
        tick.check_caps(tick.TickContext(app, now()))


@needs_pg
def test_run_tick_exits_1_logs_an_error_and_records_the_step(w, caplog):
    store = w.store(w.runtime)
    app = _app(store, _agent("a", "1", "10"))
    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        code = tick.run_tick(app, now=now(), steps=[_step()])
    assert code == 1
    assert any(
        "step=check_caps" in r.getMessage() and "a:missing" in r.getMessage()
        for r in caplog.records
    )
    state = store.get_tick_state("check_caps")
    assert state.last_error and "a:missing" in state.last_error
    _seed(w, "a", "1", "10")  # synced: the next tick is quiet again
    assert tick.run_tick(app, now=now() + timedelta(seconds=30), steps=[_step()]) == 0
    assert store.get_tick_state("check_caps").last_error is None
