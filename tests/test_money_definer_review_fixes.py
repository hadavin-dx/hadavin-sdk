"""F-money-definer: fixes for the hostile review of 0011 (M1, M2, M3, m4-m7, m9, m10 and the limits seeding). Static
checks run without a database; the rest need HADAVIN_TEST_PG_DSN (real PostgreSQL 16, throwaway schema and logins with
unique names, dropped after)."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from psycopg import errors, sql

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from tests.test_stop_state_roles import World

D = Decimal
NEEDS_PG = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
SQL_FILE = Path(mig.__file__).parent / "migrations" / "0011_money_definer.sql"
DAY = date(2026, 1, 15)
TEN = D("10")
RESERVE = "hadavin_reserve_spend(%s, %s, %s, %s, %s, %s, %s)"
SETTLE = "SELECT * FROM hadavin_settle_spend(%s, %s, %s)"


# --- header (M1, M2) -----------------------------------------------------------------------------------------------


def test_m1_the_header_does_not_claim_the_runtime_already_lost_its_write_rights():
    head = SQL_FILE.read_text(encoding="utf-8")[:3000]
    assert "After this migration the ONLY writers" not in head
    assert "step 4" in head


def test_m2_the_header_states_the_expire_then_release_residual():
    head = SQL_FILE.read_text(encoding="utf-8")[:6000].lower()
    assert "release" in head and "late settle" in head
    assert "safe (holds stay booked" not in head


# --- static checks (m4, m5, limits) -------------------------------------------------------------------------------


def _plant(tmp_path: Path, body: str) -> list[Path]:
    (tmp_path / "0001_a.sql").write_text(body, encoding="utf-8")
    return [tmp_path / "0001_a.sql"]


def test_m5_a_double_dash_inside_a_literal_does_not_hide_the_next_function(tmp_path):
    files = _plant(
        tmp_path,
        "CREATE OR REPLACE FUNCTION hadavin_ok() RETURNS void LANGUAGE sql AS $$select '--'; $$; "
        "CREATE OR REPLACE FUNCTION hadavin_hidden() RETURNS void LANGUAGE sql AS $$ select 1 $$;",
    )
    problems = mig.check_grants(files)
    assert any("hadavin_hidden" in p for p in problems)
    assert any("hadavin_ok" in p for p in problems)


@pytest.mark.parametrize(
    "name", ['"hadavin_quoted"', "public.hadavin_qualified", 'public."hadavin_both"']
)
def test_m5_quoted_and_qualified_function_names_are_seen(tmp_path, name):
    files = _plant(
        tmp_path, f"CREATE FUNCTION {name}() RETURNS void LANGUAGE sql AS $$ select 1 $$;"
    )
    assert any(name.split(".")[-1].strip('"') in p for p in mig.check_grants(files))


def test_m5_a_real_comment_after_code_is_still_stripped(tmp_path):
    files = _plant(tmp_path, "SELECT 1; -- CREATE FUNCTION hadavin_ghost() ...\n")
    assert not any("hadavin_ghost" in p for p in mig.check_grants(files))


def test_m4_an_overload_of_a_mapped_name_is_unmapped_statically(tmp_path):
    files = _plant(
        tmp_path,
        "CREATE OR REPLACE FUNCTION hadavin_add_spend(a text, d date, u numeric) RETURNS void LANGUAGE sql AS $$ select 1 $$;"
        "CREATE OR REPLACE FUNCTION hadavin_add_spend(a text) RETURNS void LANGUAGE sql AS $$ select 1 $$;",
    )
    assert any(
        "hadavin_add_spend(text)" in p and "FUNCTION_GRANTS" in p for p in mig.check_grants(files)
    )


def test_the_real_migrations_pass_the_signature_check():
    assert not any("function" in p for p in mig.check_grants(mig._migration_files()))


def test_max_exponent_is_not_seeded_because_nothing_reads_it():
    assert "max_exponent" not in mig.money_limits()


# --- the database -------------------------------------------------------------------------------------------------


@pytest.fixture(name="w")
def review_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    world.release = world.new_role("rl")
    try:
        world.migrate(release_role=world.release)
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


def _reserve(db, rid="r1", agent="A", day=DAY, usd=TEN, run=None):
    db.execute(f"SELECT {RESERVE}", (rid, agent, day, usd, D("1000"), D("1000"), run))


@NEEDS_PG
def test_m3_an_unnamed_role_with_a_direct_execute_is_refused_by_name(w):
    other = w.new_role("stranger", "NOLOGIN")
    w.grant("GRANT EXECUTE ON FUNCTION hadavin_purge_spend_reservations(timestamptz) TO {}", other)
    with pytest.raises(ConfigError, match=other):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_m3_a_member_of_the_purge_role_is_refused(w):
    other = w.new_role("member", "LOGIN")
    w.grant("GRANT {} TO {}", w.purge, other)
    with pytest.raises(ConfigError, match=other):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_m3_a_default_privilege_for_future_functions_is_refused(w):
    other = w.new_role("deflt", "NOLOGIN")
    w.do(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{w.schema}" GRANT EXECUTE ON FUNCTIONS TO "{other}"')
    with pytest.raises(ConfigError, match="default"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_m3_the_check_does_not_fire_on_the_normal_setup(w):
    assert w.migrate(release_role=w.release) == []


@NEEDS_PG
def test_m4_an_overload_in_the_schema_is_refused_as_unmapped(w):
    w.do("CREATE FUNCTION hadavin_add_spend(text) RETURNS void LANGUAGE sql AS $$ select 1 $$")
    with pytest.raises(ConfigError, match=r"hadavin_add_spend\(text\)"):
        w.migrate(release_role=w.release)


@NEEDS_PG
def test_m6_the_functions_work_with_standard_conforming_strings_off(w):
    with w.as_(w.runtime) as db:
        db.execute("SET standard_conforming_strings = off")
        row = db.execute("SELECT * FROM hadavin_add_spend('A', %s, 1)", (DAY,)).fetchone()
        assert row == (D("1"), D("1"))
        _reserve(db, "r6")


@NEEDS_PG
@pytest.mark.parametrize("day", ["5874897-12-31", "294277-01-01", "0001-01-01"])
def test_m7_an_out_of_range_day_is_22023(w, day):
    with w.as_(w.runtime) as db:
        with pytest.raises(errors.InvalidParameterValue, match="p_day"):
            db.execute("SELECT * FROM hadavin_add_spend('A', %s::date, 1)", (day,))
        with pytest.raises(errors.InvalidParameterValue, match="p_day"):
            db.execute(f"SELECT {RESERVE}", ("r7", "A", day, D("1"), D("9"), D("9"), None))


@NEEDS_PG
def test_m9_a_foreign_run_id_still_raises_the_run_cost_residual_parity_with_the_other_stores(w):
    # Review m9 wanted settle to ignore a run of another agent. The contract tests (core-a) and the memory store add the
    # run cost regardless of the run's agent (the model test books runs of one agent against holds of several): parity
    # wins; a hostile runtime login can inflate any run's cost (stated residual).
    w.do(
        "INSERT INTO runs (run_id, schema_version, agent_id, principal_id, trigger_kind, trigger_ref, state, "
        "cost_usd, created_at, updated_at) VALUES ('run-b', 1, 'B', 'p', 'user', 't', 'WORKING', 0, now(), now()), "
        "('run-a', 1, 'A', 'p', 'user', 't', 'WORKING', 0, now(), now())"
    )
    with w.as_(w.runtime) as db:
        _reserve(db, "r9", "A", run="run-b")
        db.execute(SETTLE, ("r9", D("90"), "A"))
        _reserve(db, "r9b", "A", run="run-a")
        db.execute(SETTLE, ("r9b", D("3"), "A"))
    assert w.run("SELECT run_id, cost_usd FROM runs ORDER BY 1") == [
        ("run-a", D("3")),
        ("run-b", D("90")),
    ]


@NEEDS_PG
def test_m10_settle_refuses_to_push_a_counter_below_zero_and_the_hold_stays_open(w):
    with w.as_(w.runtime) as db:
        _reserve(db, "r10", "A", usd=D("10"))
    w.do("UPDATE spend SET usd = 0")  # a repair that left the counter below its open hold
    with w.as_(w.runtime) as db, pytest.raises(psycopg.Error) as exc:
        db.execute(SETTLE, ("r10", D("0"), "A"))
    assert exc.value.sqlstate == "HD003"
    assert w.run("SELECT status FROM spend_reservations WHERE reservation_id = 'r10'") == [
        ("open",)
    ]
    assert w.run("SELECT usd FROM spend") == [(D("0"),)]


@NEEDS_PG
def test_limits_rows_nobody_reads_are_removed_at_migrate(w):
    w.do("INSERT INTO hadavin_limits VALUES ('bogus', 1), ('max_exponent', 5)")
    w.migrate(release_role=w.release)
    assert {r[0] for r in w.run("SELECT name FROM hadavin_limits")} == set(mig.money_limits())
