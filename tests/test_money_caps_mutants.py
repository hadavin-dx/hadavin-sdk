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

from hadavin_sdk.config import ConfigError
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.protocol import SpendCapExceeded
from tests.test_money_caps_reserve_pg import caps_battery
from tests.test_money_h1_pg import (
    check_b3_day_window,
    check_m1_min_expiry_age,
    check_n1_counters_refuse_bad_usd,
)
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

# What a mutant that changes behaviour looks like in the battery: a failed assertion, a missed `pytest.raises`, or the
# store refusing a reserve the battery expects to pass. NOT a bare Exception (a broken SQL would count as "killed").
BEHAVIOUR_FAILURES = (AssertionError, pytest.fail.Exception, SpendCapExceeded, ConfigError)

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
    "M-z drop the day `usd < cap` leg (a zero amount at the cap passes)": (
        lambda t: t.replace("AND s.usd < v_day_cap AND s.usd + p_usd", "AND s.usd + p_usd"),
        True,
    ),
    "M-z drop the month `usd < cap` leg": (
        lambda t: t.replace("AND m.usd < v_month_cap AND m.usd + p_usd", "AND m.usd + p_usd"),
        True,
    ),
    "M-z month boundary `<=` becomes `<`": (
        lambda t: t.replace("m.usd + p_usd <= v_month_cap", "m.usd + p_usd < v_month_cap"),
        True,
    ),
    "M-z a zero cap means unlimited": (
        lambda t: t.replace(
            "IF NOT FOUND THEN RAISE EXCEPTION 'caps' USING ERRCODE = 'HD005'; END IF;",
            "IF NOT FOUND THEN RAISE EXCEPTION 'caps' USING ERRCODE = 'HD005'; END IF;"
            " IF v_day_cap = 0 THEN v_day_cap := 1E+30; END IF;",
            1,
        ),
        True,
    ),
    "M-cm cap_matches says same when only the day cap matches": (
        lambda t: t.replace(
            "rec.day_cap = p_day_cap AND rec.month_cap = p_month_cap", "rec.day_cap = p_day_cap"
        ),
        True,
    ),
    "M-cm cap_matches says same when either cap matches": (
        lambda t: t.replace(
            "rec.day_cap = p_day_cap AND rec.month_cap = p_month_cap",
            "rec.day_cap = p_day_cap OR rec.month_cap = p_month_cap",
        ),
        True,
    ),
    "M-cm cap_matches says same for a missing row": (
        lambda t: t.replace("IF NOT FOUND THEN RETURN 'missing'; END IF;", ""),
        True,
    ),
    "M-sc set_cap does not overwrite the month cap": (
        lambda t: t.replace(
            "SET day_cap = EXCLUDED.day_cap, month_cap = EXCLUDED.month_cap, set_by",
            "SET day_cap = EXCLUDED.day_cap, set_by",
        ),
        True,
    ),
    "M-sc set_cap writes the month cap into the day cap": (
        lambda t: t.replace(
            "VALUES (p_agent, p_day_cap, p_month_cap, p_by",
            "VALUES (p_agent, p_month_cap, p_month_cap, p_by",
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
        with pytest.raises(BEHAVIOUR_FAILURES):
            caps_battery(scratch)
    else:
        caps_battery(scratch)


# --- builder H1 (lead review xr-money-lead-1): the day window, the minimum expiry age, the counter CHECKs ------------
B3_WINDOW = "IF p_day < v_today - v_skew::integer OR p_day > v_today + v_skew::integer THEN"
H1_MUTANTS = {
    "control": (lambda t: t, check_b3_day_window, False),
    "M-B3a the day window check is removed": (
        lambda t: t.replace(B3_WINDOW, "IF false THEN"),
        check_b3_day_window,
        True,
    ),
    "M-B3b only a past day is refused, a future day passes": (
        lambda t: t.replace(B3_WINDOW, "IF p_day < v_today - v_skew::integer THEN"),
        check_b3_day_window,
        True,
    ),
    "M-B3c only a future day is refused, a past day passes": (
        lambda t: t.replace(B3_WINDOW, "IF p_day > v_today + v_skew::integer THEN"),
        check_b3_day_window,
        True,
    ),
    "M-B3d the window is a literal, the table row is ignored": (
        lambda t: t.replace("v_skew::integer", "1"),
        check_b3_day_window,
        True,
    ),
    "M-B3e the window is wide (a literal 100000 days)": (
        lambda t: t.replace("v_skew::integer", "100000"),
        check_b3_day_window,
        True,
    ),
    "M-M1a expire takes any age (no minimum)": (
        lambda t: t.replace("p_age_s < v_min_age OR ", ""),
        check_m1_min_expiry_age,
        True,
    ),
    "M-M1b the minimum is a literal 0": (
        lambda t: t.replace("p_age_s < v_min_age OR ", "p_age_s < 0 OR "),
        check_m1_min_expiry_age,
        True,
    ),
    "M-M1c release lowers a hold expired just now": (
        lambda t: t.replace(
            "AND closed_at <= pg_catalog.clock_timestamp()\n"
            "                            - pg_catalog.make_interval(secs => v_min_age::double precision)",
            "",
        ),
        check_m1_min_expiry_age,
        True,
    ),
    "M-M1d release measures the age from creation, not from the expiry": (
        lambda t: t.replace(
            "AND closed_at <= pg_catalog.clock_timestamp()\n"
            "                            - pg_catalog.make_interval",
            "AND created_at <= pg_catalog.clock_timestamp()\n"
            "                            - pg_catalog.make_interval",
        ),
        check_m1_min_expiry_age,
        True,
    ),
    "M-N1a no CHECK on spend": (
        lambda t: t.replace(
            "ALTER TABLE spend ADD CONSTRAINT spend_usd_range CHECK (usd >= 0 AND usd < 'Infinity'::numeric) NOT VALID;\n"
            "ALTER TABLE spend VALIDATE CONSTRAINT spend_usd_range;\n",
            "",
        ),
        check_n1_counters_refuse_bad_usd,
        True,
    ),
    "M-N1b no CHECK on spend_month": (
        lambda t: t.replace(
            "ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_range CHECK (usd >= 0 AND usd < 'Infinity'::numeric) NOT VALID;\n"
            "ALTER TABLE spend_month VALIDATE CONSTRAINT spend_month_usd_range;\n",
            "",
        ),
        check_n1_counters_refuse_bad_usd,
        True,
    ),
    "M-N1c the CHECK is left NOT VALID": (
        lambda t: t.replace("ALTER TABLE spend VALIDATE CONSTRAINT spend_usd_range;\n", ""),
        check_n1_counters_refuse_bad_usd,
        True,
    ),
    "M-N1d the CHECK lets a negative amount through": (
        lambda t: t.replace(
            "CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "CHECK (usd < 'Infinity'::numeric)"
        ),
        check_n1_counters_refuse_bad_usd,
        True,
    ),
    "M-N1e the CHECK lets Infinity through": (
        lambda t: t.replace("CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "CHECK (usd >= 0)"),
        check_n1_counters_refuse_bad_usd,
        True,
    ),
}


@pytest.mark.parametrize("name", list(H1_MUTANTS))
def test_the_h1_checks_kill_every_mutant(name, scratch, tmp_path, monkeypatch):
    mutate, check, killed = H1_MUTANTS[name]
    text = SQL_FILE.read_text(encoding="utf-8")
    mutated = mutate(text)
    assert (mutated != text) or name == "control", "the mutation did not change the SQL"
    folder = tmp_path / "migrations"
    shutil.copytree(mig.MIGRATIONS, folder)
    (folder / SQL_FILE.name).write_text(mutated, encoding="utf-8")
    real = mig._migration_files
    monkeypatch.setattr(mig, "_migration_files", lambda folder_=None: real(folder))
    scratch.migrate()
    if killed:
        with pytest.raises((AssertionError, Exception, pytest.fail.Exception)):
            check(scratch)
    else:
        check(scratch)
