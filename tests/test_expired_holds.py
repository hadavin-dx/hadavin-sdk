"""The alert on expired spend holds nobody released (ticket money-hostile-reread-2 M4): `expired_holds` on both stores
and the tick step `check_expired_holds`. The Postgres half runs through the RUNTIME login (no right on the table; the
read-only definer function `hadavin_expired_holds` of 0011 answers). Needs HADAVIN_TEST_PG_DSN for the pg tests."""

from __future__ import annotations

import logging
import os
import shutil
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.models import new_id, now
from hadavin_sdk.runtime import tick
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import EXPIRED_HOLDS_MAX_ROWS, ExpiredHolds, ExpiredHoldsReader

D = Decimal
AGENT = "agent-a"
DAY = date(now().year - 1, 1, 31)
OTHER_DAY = date(now().year - 1, 1, 30)
BIG = D("100000")
AFTER = defaults.EXPIRED_HOLD_ALERT_AFTER_S
needs_pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def test_the_threshold_is_six_hours_and_above_the_release_minimum():
    assert AFTER == 6 * 3600 and AFTER > defaults.MIN_EXPIRY_AGE_S


# --- memory store ----------------------------------------------------------------------------------------------


def _mem_hold(s, usd, *, agent=AGENT, day=DAY, closed_ago=AFTER + 60, status="expired"):
    rid = new_id("res")
    s.reserve_spend(rid, agent, day, D(usd), day_cap=BIG, month_cap=BIG)
    if status == "settled":
        s.settle_spend(rid, D(usd), agent_id=agent)
    elif status == "expired":
        with s._lock:
            r = s._reservations[rid]
            s._reservations[rid] = r.model_copy(
                update={"status": "expired", "settled_usd": r.reserved_usd, "closed_at": now()}
            )
    if status != "open":
        with s._lock:
            r = s._reservations[rid]
            s._reservations[rid] = r.model_copy(
                update={"closed_at": now() - timedelta(seconds=closed_ago)}
            )
    return rid


def test_memory_is_an_expired_holds_reader():
    assert callable(MemoryStore().expired_holds) and ExpiredHoldsReader.expired_holds


def test_memory_lists_expired_holds_grouped_by_agent_and_day():
    s = MemoryStore()
    _mem_hold(s, "1.00")
    _mem_hold(s, "2.50")
    _mem_hold(s, "8", day=OTHER_DAY)
    _mem_hold(s, "16", agent="agent-b")
    assert s.expired_holds(AFTER) == [
        ExpiredHolds(AGENT, OTHER_DAY, 1, D("8")),
        ExpiredHolds(AGENT, DAY, 1 + 1, D("3.50")),
        ExpiredHolds("agent-b", DAY, 1, D("16")),
    ]


def test_memory_leaves_out_open_settled_released_and_young_holds():
    s = MemoryStore()
    _mem_hold(s, "1", status="open")
    _mem_hold(s, "2", status="settled")  # settled, or released (settled at 0): not listed
    _mem_hold(s, "4", closed_ago=AFTER - 60)  # expired, but not yet past the threshold
    assert s.expired_holds(AFTER) == []
    assert [g.usd for g in s.expired_holds(AFTER - 120)] == [D("4")]


def test_memory_is_bounded_and_refuses_a_bad_age():
    s = MemoryStore()
    for i in range(EXPIRED_HOLDS_MAX_ROWS + 5):
        _mem_hold(s, "1", agent=f"agent-{i:05d}")
    assert len(s.expired_holds(AFTER)) == EXPIRED_HOLDS_MAX_ROWS
    for bad in (-1, True, 1.5, "1"):
        with pytest.raises(ValueError):
            s.expired_holds(bad)


# --- the tick step -----------------------------------------------------------------------------------------------


def _step():
    (step,) = [s for s in tick.STEPS if s.name == "check_expired_holds"]
    return step


def _app(store):
    return SimpleNamespace(store=store)


def test_the_step_is_registered_once_after_expire_reservations_and_runs_every_tick():
    names = [s.name for s in tick.STEPS]
    assert names.count("check_expired_holds") == 1
    assert names.index("check_expired_holds") > names.index("expire_reservations")
    assert _step().every_s == 0


def test_no_alert_when_there_are_no_expired_holds():
    tick.check_expired_holds(tick.TickContext(_app(MemoryStore()), now()))


def test_no_alert_for_a_hold_younger_than_the_threshold():
    s = MemoryStore()
    _mem_hold(s, "5", closed_ago=AFTER - 60)
    tick.check_expired_holds(tick.TickContext(_app(s), now()))


def test_a_store_without_the_method_has_nothing_to_check():
    tick.check_expired_holds(tick.TickContext(_app(SimpleNamespace()), now()))


def test_an_old_expired_hold_fails_loudly_naming_agent_day_count_amount_and_the_fix():
    s = MemoryStore()
    _mem_hold(s, "1.50")
    _mem_hold(s, "2.00")
    with pytest.raises(tick.ExpiredHoldsStale) as caught:
        tick.check_expired_holds(tick.TickContext(_app(s), now()))
    text = str(caught.value)
    assert AGENT in text and DAY.isoformat() in text and "2 holds" in text and "3.50" in text
    assert "hadavin-sdk release-expired" in text
    assert "res" not in text.replace("reserv", "").replace("release", "").replace("residual", "")


def test_run_tick_exits_1_logs_an_error_and_records_the_step(caplog):
    s = MemoryStore()
    _mem_hold(s, "7")
    app = SimpleNamespace(store=s)
    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        code = tick.run_tick(app, now=now(), steps=[_step()])
    assert code == 1
    assert any(
        "step=check_expired_holds" in r.getMessage() and AGENT in r.getMessage()
        for r in caplog.records
    )
    assert any(r.getMessage().startswith("check_expired_holds") for r in caplog.records)
    state = s.get_tick_state("check_expired_holds")
    assert state.last_error and AGENT in state.last_error
    with s._lock:  # released (settled at 0): the next tick is quiet and the error clears
        for k, r in list(s._reservations.items()):
            s._reservations[k] = r.model_copy(update={"status": "settled", "settled_usd": D(0)})
    assert tick.run_tick(app, now=now() + timedelta(seconds=30), steps=[_step()]) == 0
    assert s.get_tick_state("check_expired_holds").last_error is None


def test_a_store_error_names_the_step_and_exits_1(caplog):
    class Broken(MemoryStore):
        def expired_holds(self, older_than_s):
            raise RuntimeError("database says no")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        code = tick.run_tick(_app_with(Broken()), now=now(), steps=[_step()])
    assert code == 1
    assert any("step=check_expired_holds" in r.getMessage() for r in caplog.records)


def _app_with(store):
    return SimpleNamespace(store=store)


# --- postgres ------------------------------------------------------------------------------------------------------

try:
    from tests.test_release_expired_spend_pg import (
        _release,
        _reserve,
    )
    from tests.test_release_expired_spend_pg import release_world as w
except ImportError:  # no psycopg: the pg tests are skipped below
    w = None


def _age(w, rid, seconds):
    w.run(
        "UPDATE spend_reservations SET closed_at = clock_timestamp() - make_interval(secs => %s) "
        "WHERE reservation_id = %s RETURNING 1",
        (float(seconds), rid),
    )


def _expire_now(w, *rids):
    """Expire the holds (the real expire step) and back-date their expiry by `closed_ago` below."""
    for rid in rids:
        w.run(
            "UPDATE spend_reservations SET created_at = created_at - interval '2 hours' "
            "WHERE reservation_id = %s RETURNING 1",
            (rid,),
        )
    w.store(w.runtime).expire_spend_reservations(3600)


def pg_battery(w):
    """The contract on the runtime login: expired holds past the threshold are listed (grouped, summed), released,
    settled, open and young ones are not, the rows carry no id. Raises AssertionError on any difference."""
    rt = w.store(w.runtime)
    a, b = _reserve(rt, "1.00"), _reserve(rt, "2.50")
    other_day = _reserve(rt, "8", day=OTHER_DAY)
    other_agent = _reserve(rt, "16", agent="agent-b")
    young = _reserve(rt, "32", agent="agent-c")
    settled = _reserve(rt, "64", agent="agent-d")
    released = _reserve(rt, "128", agent="agent-e")
    still_open = _reserve(rt, "256", agent="agent-f")
    rt.settle_spend(settled, D("64"), agent_id="agent-d")
    _expire_now(w, a, b, other_day, other_agent, young, released)
    for rid in (a, b, other_day, other_agent, released):
        _age(w, rid, AFTER + 600)
    _age(w, young, AFTER - 600)
    assert _release(w, agent="agent-e").reservations == 1
    assert rt.expired_holds(AFTER) == [
        ExpiredHolds(AGENT, OTHER_DAY, 1, D("8")),
        ExpiredHolds(AGENT, DAY, 2, D("3.50")),
        ExpiredHolds("agent-b", DAY, 1, D("16")),
    ]
    assert still_open and young
    assert sorted((g.agent_id, g.holds) for g in rt.expired_holds(AFTER - 1200)) == [
        (AGENT, 1),
        (AGENT, 2),
        ("agent-b", 1),
        ("agent-c", 1),
    ]
    assert not hasattr(rt.expired_holds(AFTER)[0], "reservation_id")


@needs_pg
def test_pg_expired_holds_contract(w):
    pg_battery(w)


@needs_pg
def test_pg_is_bounded_and_refuses_a_bad_age(w):
    w.run(
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "
        "closed_at) SELECT 'bulk-' || g, 'agent-' || g, %s, 1, 1, 'expired', "
        "clock_timestamp() - interval '1 day' FROM generate_series(1, %s) g RETURNING 1",
        (DAY, EXPIRED_HOLDS_MAX_ROWS + 5),
    )
    rows = w.store(w.runtime).expired_holds(AFTER)
    assert len(rows) == EXPIRED_HOLDS_MAX_ROWS
    for bad in (-1, mig_max() + 1):
        with pytest.raises(Exception, match="invalid|older_than_s"):
            w.store(w.runtime).expired_holds(bad)


def mig_max():
    from hadavin_sdk.store.protocol import MAX_EXPIRY_AGE_S

    return MAX_EXPIRY_AGE_S


@needs_pg
def test_pg_only_the_runtime_role_may_run_it_and_it_gives_no_table_right(w):
    sig = "hadavin_expired_holds(integer)"
    assert mig.FUNCTION_GRANTS[sig].runtime is True
    for role, expected in (
        (w.runtime, True),
        (w.portal, False),
        (w.purge, False),
        (w.reset, False),
        (w.release, False),
    ):
        got = w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (role, sig))
        assert got == [(expected,)], role
    assert w.run("SELECT has_function_privilege('public', %s, 'EXECUTE')", (sig,)) == [(False,)]
    assert w.run(
        "SELECT has_table_privilege(%s, 'spend_reservations', 'SELECT')", (w.runtime,)
    ) == [(False,)]


@needs_pg
def test_pg_the_tick_step_alerts_and_is_quiet_again_after_the_release(w, caplog):
    rt = w.store(w.runtime)
    app = _app(rt)
    assert tick.run_tick(app, now=now(), steps=[_step()]) == 0
    rid = _reserve(rt, "3.25")
    _expire_now(w, rid)
    _age(w, rid, AFTER + 600)
    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        assert tick.run_tick(app, now=now() + timedelta(seconds=30), steps=[_step()]) == 1
    assert any(
        "step=check_expired_holds" in r.getMessage()
        and AGENT in r.getMessage()
        and "3.25" in r.getMessage()
        for r in caplog.records
    )
    assert _release(w).reservations == 1
    assert tick.run_tick(app, now=now() + timedelta(seconds=60), steps=[_step()]) == 0


# --- mutants of the SQL function: each must make `pg_battery` fail ------------------------------------------------

STATUS_LINE = "WHERE r.status = 'expired'\n"
AGE_LINE = "                          - pg_catalog.make_interval(secs => p_older_than_s::double precision)\n"
EXPIRED_HOLDS_MUTANTS = {
    "control": (lambda t: t, False),
    "M-eh1 every status is listed": (
        lambda t: _fn(t, lambda f: f.replace(STATUS_LINE, "WHERE true\n")),
        True,
    ),
    "M-eh2 settled counts too": (
        lambda t: _fn(
            t, lambda f: f.replace(STATUS_LINE, "WHERE r.status IN ('expired', 'settled')\n")
        ),
        True,
    ),
    "M-eh3 the threshold is ignored": (lambda t: _fn(t, lambda f: f.replace(AGE_LINE, "")), True),
    "M-eh4 the age counts from creation, not from the expiry": (
        lambda t: _fn(t, lambda f: f.replace("AND r.closed_at <=", "AND r.created_at <=")),
        True,
    ),
    "M-eh5 not grouped by day": (
        lambda t: _fn(
            t,
            lambda f: (
                f.replace(
                    "r.agent_id, r.day, pg_catalog.count",
                    "r.agent_id, MIN(r.day), pg_catalog.count",
                )
                .replace("GROUP BY r.agent_id, r.day", "GROUP BY r.agent_id")
                .replace("ORDER BY r.agent_id, r.day", "ORDER BY r.agent_id")
            ),
        ),
        True,
    ),
    "M-eh6 no row bound": (lambda t: _fn(t, lambda f: f.replace("LIMIT 1000", "")), True),
}


def _fn(text, edit):
    head, sep, tail = text.partition("CREATE OR REPLACE FUNCTION hadavin_expired_holds")
    assert sep
    return head + sep + edit(tail)


@needs_pg
@pytest.mark.parametrize("name", list(EXPIRED_HOLDS_MUTANTS))
def test_the_expired_holds_battery_kills_every_mutant(name, tmp_path, monkeypatch):
    """Each mutant is a copy of 0011 migrated into a throwaway schema (the fixture is built here, after the patch)."""
    import psycopg
    from psycopg import sql

    from tests.test_stop_state_roles import World

    mutate, killed = EXPIRED_HOLDS_MUTANTS[name]
    path = mig.MIGRATIONS / "0011_money_definer.sql"
    text = path.read_text(encoding="utf-8")
    mutated = mutate(text)
    assert (mutated != text) or name == "control", "the mutation did not change the SQL"
    folder = tmp_path / "migrations"
    shutil.copytree(mig.MIGRATIONS, folder)
    (folder / path.name).write_text(mutated, encoding="utf-8")
    real = mig._migration_files
    monkeypatch.setattr(mig, "_migration_files", lambda folder_=None: real(folder))
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    world.release = world.new_role("rl")
    try:
        world.migrate(release_role=world.release)
        if killed:
            with pytest.raises((AssertionError, pytest.fail.Exception)):
                _battery_with_bound(world)
        else:
            _battery_with_bound(world)
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _battery_with_bound(w):
    pg_battery(w)
    w.run(
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "
        "closed_at) SELECT 'bulk-' || g, 'zagent-' || g, %s, 1, 1, 'expired', "
        "clock_timestamp() - interval '1 day' FROM generate_series(1, %s) g RETURNING 1",
        (DAY, EXPIRED_HOLDS_MAX_ROWS + 5),
    )
    assert len(w.store(w.runtime).expired_holds(AFTER)) == EXPIRED_HOLDS_MAX_ROWS
