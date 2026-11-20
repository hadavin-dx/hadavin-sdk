"""Killing tests for step 6, second half (mutants M-q and M-t): each mutant is a COPY of 0011 applied in a scratch
schema; `caps_battery` (tests/test_money_caps_reserve_pg.py) must fail on every mutant and pass on the control.
M-q: the cap is taken from somewhere other than the table row (a fixed huge cap; day and month swapped). M-t: an
overload of `hadavin_reserve_spend` WITH cap arguments survives next to the five-argument one."""

from __future__ import annotations

import os
import shutil

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.store import migrate as mig
from tests.test_money_caps_reserve_pg import caps_battery
from tests.test_stop_state_roles import World

pytestmark = [
    pytest.mark.no_cap_seed,
    pytest.mark.skipif(
        not os.environ.get("HADAVIN_TEST_PG_DSN"),
        reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
    ),
]
SQL_FILE = mig.MIGRATIONS / "0011_money_definer.sql"
TABLE_READ = "SELECT c.day_cap, c.month_cap INTO v_day_cap, v_month_cap FROM hadavin_caps c WHERE c.agent_id = p_agent;"
OVERLOAD = """
CREATE OR REPLACE FUNCTION hadavin_reserve_spend(
    p_id TEXT, p_agent TEXT, p_day DATE, p_usd NUMERIC, p_day_cap NUMERIC, p_month_cap NUMERIC, p_run_id TEXT
) RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $f$ SELECT hadavin_reserve_spend(p_id, p_agent, p_day, p_usd, p_run_id) $f$;
"""

MUTANTS = {
    "control": (lambda t: t, False),
    "M-q cap is a fixed huge value, the table row is ignored": (
        lambda t: t.replace(
            TABLE_READ, "v_day_cap := 1E+30; v_month_cap := 1E+30; PERFORM 1 FROM hadavin_caps;"
        ).replace("IF NOT FOUND THEN RAISE EXCEPTION 'caps' USING ERRCODE = 'HD005'; END IF;", ""),
        True,
    ),
    "M-q day and month caps swapped": (
        lambda t: t.replace("INTO v_day_cap, v_month_cap", "INTO v_month_cap, v_day_cap"),
        True,
    ),
    "M-l a missing row is unlimited": (
        lambda t: t.replace(
            "IF NOT FOUND THEN RAISE EXCEPTION 'caps' USING ERRCODE = 'HD005'; END IF;",
            "IF NOT FOUND THEN v_day_cap := 1E+30; v_month_cap := 1E+30; END IF;",
        ),
        True,
    ),
    "M-t an overload with cap arguments survives": (
        lambda t: t.replace("-- hadavin_settle_spend:", OVERLOAD + "\n-- hadavin_settle_spend:", 1),
        True,
    ),
}


@pytest.fixture(name="scratch")
def scratch_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
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


@pytest.mark.parametrize("name", list(MUTANTS))
def test_the_caps_battery_kills_every_mutant(name, scratch, tmp_path, monkeypatch):
    mutate, killed = MUTANTS[name]
    text = SQL_FILE.read_text(encoding="utf-8")
    mutated = mutate(text)
    assert (mutated != text) or name == "control", "the mutation did not change the SQL"
    folder = tmp_path / "migrations"
    shutil.copytree(mig.MIGRATIONS, folder)
    (folder / SQL_FILE.name).write_text(mutated, encoding="utf-8")
    real = mig._migration_files
    monkeypatch.setattr(mig, "_migration_files", lambda folder_=None: real(folder))
    try:
        scratch.migrate()
    except Exception:  # noqa: BLE001 - migrate refusing an unmapped overload also kills the mutant
        assert killed, "the control must migrate"
        return
    if killed:
        with pytest.raises((AssertionError, Exception, pytest.fail.Exception)):
            caps_battery(scratch)
    else:
        caps_battery(scratch)
