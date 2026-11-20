"""Round 4 review of the stop-year validation step (review-ts-watermark-4): one error mapping for the settle step and
`--validate-constraints`, the timeout path, the restore of the timeouts, schema-qualified lookups of our own
functions and tables, and the exit codes of the runbook. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest
import yaml

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as migrate_mod
from tests.test_step_b_e7_migration_0009 import (
    drop_world,
    make_not_valid,
    make_world,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

RUNBOOK = Path(__file__).resolve().parents[1] / "docs" / "stop-state-runbook.md"


@pytest.fixture(name="w")
def world():
    w = make_world()
    try:
        w.migrate()
        yield w
    finally:
        drop_world(w)


# --- M1: settle maps the errors exactly as validate does ---------------------------------------------------------


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (errors.CheckViolation("check constraint is violated by some row"), ConfigError),
        (errors.InsufficientPrivilege("must be owner of table kill_switch_stops"), ConfigError),
        (psycopg.OperationalError("server closed the connection"), migrate_mod.StopTablesBusy),
        (
            errors.QueryCanceled("canceling statement due to statement timeout"),
            migrate_mod.StopTablesBusy,
        ),
        (
            errors.LockNotAvailable("canceling statement due to lock timeout"),
            migrate_mod.StopTablesBusy,
        ),
    ],
)
@pytest.mark.parametrize("step", ["settle", "validate"])
def test_settle_and_validate_map_a_validation_error_the_same_way(
    w, monkeypatch, raised, expected, step
):
    make_not_valid(w, tables=("kill_switch_stops",))

    def boom(db, table, name):
        raise raised

    monkeypatch.setattr(migrate_mod, "_validate_one", boom)
    call = (
        migrate_mod.settle_stop_constraints
        if step == "settle"
        else migrate_mod.validate_constraints
    )
    with psycopg.connect(w.scoped) as db, db.transaction(), pytest.raises(expected) as err:
        call(db)
    assert (
        type(err.value) is expected
    )  # exactly that class: a refusal is not a retry and the reverse
    assert (
        not isinstance(err.value, migrate_mod.StopTablesBusy)
        or expected is migrate_mod.StopTablesBusy
    )


def test_settle_refuses_a_login_that_is_not_the_owner_with_a_real_privilege_error(w):
    """The runtime login holds no right on the stop tables: the real database refuses, and that is a ConfigError."""
    make_not_valid(w, tables=("kill_switch_stops",))
    with (
        w.as_(w.runtime) as db,
        pytest.raises(ConfigError, match="not the table owner"),
    ):
        db.execute("BEGIN")
        migrate_mod.settle_stop_constraints(db)


def test_settle_refuses_a_real_planted_row_that_the_precheck_missed_as_a_config_error(
    w, monkeypatch
):
    """The row set can change between the pre-check and the VALIDATE (or the session TimeZone differs): the real
    CheckViolation of VALIDATE is the same refusal as in `--validate-constraints` (exit 2), not a crash (exit 3)."""
    make_not_valid(w, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", lambda db: [])
    with (
        psycopg.connect(w.scoped) as db,
        db.transaction(),
        pytest.raises(ConfigError, match="kill_switch_stops_ts_range"),
    ):
        migrate_mod.settle_stop_constraints(db)


def _cli_cfg(cfg_dir):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_the_cli_exits_2_for_a_refusal_and_75_for_a_busy_table_in_both_places(
    w, cfg_dir, monkeypatch, capsys
):
    """End to end against the real database: the same refusal and the same retry code in `migrate` and in
    `migrate --validate-constraints`."""
    _cli_cfg(cfg_dir)
    make_not_valid(w, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.scoped)
    with (
        monkeypatch.context() as m
    ):  # the pre-check misses the planted row: VALIDATE refuses it (exit 2, not 3)
        m.setattr(migrate_mod, "planted_ts_rows", lambda db: [])
        assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 2
    assert "refused: cannot validate kill_switch_stops_ts_range" in capsys.readouterr().err
    monkeypatch.setenv(
        "HADAVIN_MIGRATE_DSN", make_conninfo(w.scoped, user=w.runtime)
    )  # not the owner
    assert cli.main(["--config", str(cfg_dir), "migrate", "--validate-constraints"]) == 2
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.scoped)
    with w.admin() as blocker:
        blocker.execute("SET idle_in_transaction_session_timeout = '40s'")
        blocker.execute("BEGIN")
        blocker.execute("LOCK TABLE kill_switch_stops IN ACCESS EXCLUSIVE MODE")
        assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 75
        assert cli.main(["--config", str(cfg_dir), "migrate", "--validate-constraints"]) == 75
        blocker.execute("ROLLBACK")


# --- m1: a connection that cannot be opened is exit 3 (the runbook says so) ---------------------------------------


def test_the_cli_exits_3_for_a_connection_that_cannot_be_opened_in_both_places(
    cfg_dir, monkeypatch
):
    _cli_cfg(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://u@127.0.0.1:1/x?connect_timeout=2")
    assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 3
    assert cli.main(["--config", str(cfg_dir), "migrate", "--validate-constraints"]) == 3


def test_the_runbook_states_the_numbers_the_code_uses():
    text = " ".join(RUNBOOK.read_text(encoding="utf-8").split())
    assert migrate_mod.VALIDATE_LOCK_TIMEOUT == "5s"
    assert migrate_mod.VALIDATE_STATEMENT_TIMEOUT == "60s"
    assert "5-second lock wait and 60-second statement limit" in text
    for exit_code in ("- 75 (retry later", "- 2 (refusal)", "- 3 (any other error", "- 0: done"):
        assert exit_code in RUNBOOK.read_text(encoding="utf-8")
    # m2: the lock lasts to commit, the wait has no limit, and why
    assert "holds that lock until the whole run commits" in text
    assert "stop the runtimes" in text
    assert "advisory lock" in text


# --- m3: the timeouts really are set during the step, and the statement timeout is a retry condition --------------


def test_the_validation_runs_under_the_two_timeouts_and_a_slow_scan_is_a_retry_condition(
    w, monkeypatch
):
    seen = []
    real = migrate_mod._validate_one

    def spy(db, table, name):
        seen.append(
            db.execute(
                "SELECT current_setting('lock_timeout'), current_setting('statement_timeout')"
            ).fetchone()
        )
        real(db, table, name)

    monkeypatch.setattr(migrate_mod, "_validate_one", spy)
    for call in (migrate_mod.settle_stop_constraints, migrate_mod.validate_constraints):
        make_not_valid(w, tables=("kill_switch_stops",))
        with psycopg.connect(w.scoped) as db, db.transaction():
            call(db)
    assert seen and set(seen) == {("5s", "1min")}  # PostgreSQL shows 60s as 1min
    monkeypatch.undo()

    # the slow part: the scan outlives the statement limit (pg_sleep inside the step), the error is the retry kind
    make_not_valid(w, tables=("kill_switch_clears",))
    monkeypatch.setattr(migrate_mod, "VALIDATE_STATEMENT_TIMEOUT", "100ms")
    first = migrate_mod.planted_ts_rows

    def slow(db):
        db.execute("SELECT pg_sleep(2)")
        return first(db)

    monkeypatch.setattr(migrate_mod, "planted_ts_rows", slow)
    with (
        psycopg.connect(w.scoped) as db,
        db.transaction(),
        pytest.raises(migrate_mod.StopTablesBusy, match="QueryCanceled"),
    ):
        migrate_mod.settle_stop_constraints(db)


# --- n1: the timeouts come back also when the step raises ----------------------------------------------------------


def test_the_timeouts_are_restored_when_the_step_raises_and_the_original_error_survives(w):
    show = "SELECT current_setting('lock_timeout'), current_setting('statement_timeout')"
    with psycopg.connect(w.scoped) as db, db.transaction():
        before = db.execute(show).fetchone()
        with (
            pytest.raises(KeyError),
            migrate_mod._stop_timeouts(db),
        ):  # a Python error: the restore must run
            assert db.execute(show).fetchone() != before
            raise KeyError("x")
        assert db.execute(show).fetchone() == before
    # a database error aborts the transaction: the original error survives, never InFailedSqlTransaction
    with (
        psycopg.connect(w.scoped) as db,
        db.transaction(force_rollback=True),
        pytest.raises(errors.DivisionByZero),
        migrate_mod._stop_timeouts(db),
    ):
        db.execute("SELECT 1/0")


# --- m5: our own functions and tables are looked up in current_schema(), never through the search path -------------


@pytest.fixture(name="decoy")
def decoy_world():
    """A mixed-case schema that holds nothing of ours (first in the search path) and a second schema, later in the
    path, that holds same-named functions and tables: a bare name would find those."""
    sfx = uuid.uuid4().hex[:10]
    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    mine, other = f"E7_Mine_{sfx}", f"e7_other_{sfx}"
    with psycopg.connect(dsn, autocommit=True) as db:
        for s in (mine, other):
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(s)))
        sigs = (
            *migrate_mod.TRIPWIRE_FUNCTIONS,
            *migrate_mod.MONEY_FUNCTIONS,
            migrate_mod.RELEASE_FUNCTION,
        )
        for sig in sigs:
            db.execute(
                sql.SQL("CREATE FUNCTION {}.{} RETURNS void LANGUAGE sql AS 'SELECT 1'").format(
                    sql.Identifier(other), sql.SQL(sig)
                )
            )
        for t in ("spend", "spend_month", "spend_reservations"):
            db.execute(
                sql.SQL("CREATE TABLE {}.{} (x int)").format(
                    sql.Identifier(other), sql.Identifier(t)
                )
            )
            db.execute(
                sql.SQL("GRANT INSERT ON {}.{} TO PUBLIC").format(
                    sql.Identifier(other), sql.Identifier(t)
                )
            )
        db.execute(
            sql.SQL("CREATE TABLE {}.hadavin_limits (name text PRIMARY KEY, value numeric)").format(
                sql.Identifier(other)
            )
        )
    conninfo = make_conninfo(dsn, options=f'-c search_path="{mine}",{other}')
    try:
        yield conninfo, mine, other, sigs
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            for s in (mine, other):
                db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(s)))


def test_the_pin_grant_and_check_steps_never_touch_another_schemas_objects(decoy):
    conninfo, mine, other, sigs = decoy
    with psycopg.connect(conninfo) as db, db.transaction():
        assert db.execute("SELECT current_schema()").fetchone()[0] == mine
        migrate_mod._pin_money_guard(db)
        migrate_mod._pin_money_functions(db)
        migrate_mod._apply_release_function(db, None, [])
        migrate_mod._apply_money_functions(db, {})
        assert (
            migrate_mod._unnamed_money_executors(db, []) == []
        )  # PUBLIC may run the other schema's, not ours
        assert (
            migrate_mod._money_table_writers(db) == []
        )  # PUBLIC may write the other schema's tables
        migrate_mod._seed_limits(db)
        configs = db.execute(
            "SELECT p.proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s",
            (other,),
        ).fetchall()
        assert len(configs) == len(sigs) and all(c[0] is None for c in configs), configs
        assert (
            db.execute(
                sql.SQL("SELECT count(*) FROM {}.hadavin_limits").format(sql.Identifier(other))
            ).fetchone()[0]
            == 0
        )


def test_the_validation_and_grant_statements_name_the_schema():
    """A bare table name in VALIDATE, the planted-row read and the GRANTs would follow the search path too."""
    w = make_world(mixed=True)
    try:
        w.migrate()
        make_not_valid(w, tables=("kill_switch_stops",))
        seen: list[str] = []

        class Spy:
            def __init__(self, db):
                self.db = db

            def execute(self, query, *args, **kw):
                seen.append(query.as_string(self.db) if hasattr(query, "as_string") else query)
                return self.db.execute(query, *args, **kw)

        with psycopg.connect(w.scoped) as db, db.transaction():
            spy = Spy(db)
            migrate_mod._validate_one(spy, "kill_switch_stops", "kill_switch_stops_ts_range")
            migrate_mod.planted_ts_rows(spy)
            migrate_mod._apply_grants(spy, w.runtime, lambda g: g.runtime)
        quoted = f'"{w.schema}".'
        for stmt in seen:
            if re.search(
                r"VALIDATE CONSTRAINT|FROM \"|REVOKE ALL ON|GRANT SELECT|GRANT (?!USAGE)", stmt
            ):
                assert quoted in stmt, stmt
        assert any("VALIDATE CONSTRAINT" in s for s in seen) and any(
            "REVOKE ALL ON" in s for s in seen
        )
    finally:
        drop_world(w)
