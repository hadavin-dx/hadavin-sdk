"""Mutants of migration 0009: each one is applied (as a scratch copy of the SQL, in a scratch schema) and a test of
tests/test_step_b_e7_migration_0009.py must fail. A mutant that survives means the test is blind. Needs
HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import contextlib
import inspect
import os

import psycopg
import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as migrate_mod
from tests import test_step_b_e7_migration_0009 as real
from tests import test_step_b_e7_round6 as r6
from tests.test_step_b_e7_migration_0009 import (
    FILE_0009,
    drop_world,
    make_world,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

SOURCE = FILE_0009.read_text()


def _cut(text, start, end):
    i = text.index(start)
    j = text.index(end, i) + len(end)
    return text[:i] + text[j:]


def no_seq_guard(t):
    return _cut(
        t, "CREATE OR REPLACE TRIGGER audit_entries_seq_guard", "hadavin_audit_seq_guard();"
    )


def no_ts_check(t):
    t = _cut(t, "ALTER TABLE kill_switch_stops ADD CONSTRAINT", "NOT VALID;")
    return _cut(t, "ALTER TABLE kill_switch_clears ADD CONSTRAINT", "NOT VALID;")


def no_index(t):
    return t.replace("CREATE INDEX kill_switch_stops_by_ts ON kill_switch_stops (ts);", "")


def mutants():
    return {
        "seq guard removed": no_seq_guard,
        "ts check removed": no_ts_check,
        "index removed": no_index,
    }


def _build(mutated, tmp_path, monkeypatch):
    d = tmp_path / "m"
    d.mkdir()
    for p in migrate_mod._migration_files():
        (d / p.name).write_text(mutated if p == FILE_0009 else p.read_text())
    files = sorted(d.glob("*.sql"))
    monkeypatch.setattr(migrate_mod, "_migration_files", lambda *a, **k: files)
    return files


@pytest.fixture(name="mw")
def mutant_world():
    w = make_world()
    yield w
    drop_world(w)


def test_mutations_really_change_the_file():
    for name, f in mutants().items():
        assert f(SOURCE) != SOURCE, name


def _run_killing(mw, tmp_path, monkeypatch, mutated, calls, grants=None):
    """Apply the mutated SQL in a scratch schema, then run the REAL test bodies against it: every one of `calls`
    must fail (an assertion, a pytest.fail or an unexpected database error), or the mutant survived."""
    _build(mutated, tmp_path, monkeypatch)
    if grants is not None:
        monkeypatch.setattr(migrate_mod, "GRANTS", grants)
    mw.migrate()
    for fn, args in calls:
        with pytest.raises(BaseException) as err:
            fn(mw, *args)
        assert not isinstance(err.value, KeyboardInterrupt)


def test_removing_the_seq_guard_is_killed(mw, tmp_path, monkeypatch):
    _run_killing(
        mw,
        tmp_path,
        monkeypatch,
        no_seq_guard(SOURCE),
        [
            (real.test_a_planted_audit_seq_is_refused_and_exact_next_is_accepted, ()),
            (real.test_the_first_audit_row_must_be_seq_1, ()),
        ],
    )


@pytest.mark.parametrize("table", ["kill_switch_stops", "kill_switch_clears"])
def test_removing_the_ts_check_is_killed(mw, tmp_path, monkeypatch, table):
    _run_killing(
        mw,
        tmp_path,
        monkeypatch,
        no_ts_check(SOURCE),
        [(real.test_planted_stop_years_are_refused, (table, "20000-01-01"))],
    )


def test_removing_the_index_is_killed(mw, tmp_path, monkeypatch):
    _run_killing(
        mw, tmp_path, monkeypatch, no_index(SOURCE), [(real.test_the_open_stops_index_exists, ())]
    )


def test_granting_insert_to_runtime_is_killed(mw, tmp_path, monkeypatch):
    g = dict(migrate_mod.GRANTS)
    g["kill_switch_resets"] = migrate_mod.Grant("table", "INSERT", reset="SELECT, INSERT")
    _run_killing(
        mw,
        tmp_path,
        monkeypatch,
        SOURCE,
        [
            (real.test_runtime_cannot_insert_into_the_reset_record_but_the_reset_role_can, ()),
        ],
        grants=g,
    )


# --- the validate step (review N2): a validate that leaves a constraint NOT VALID must be killed ------------------


def _validate_nothing(db):
    return [n for _, n in migrate_mod.not_valid_constraints(db)]  # claims the names, validates none


def _validate_first_only(db):
    table, name = migrate_mod.not_valid_constraints(db)[0]
    db.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")
    return [name]


@pytest.mark.parametrize("mutant", [_validate_nothing, _validate_first_only])
def test_a_validate_step_that_leaves_a_constraint_not_valid_is_killed(mw, monkeypatch, mutant):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "validate_constraints", mutant)
    with pytest.raises(AssertionError):
        real.test_the_validate_step_validates_what_is_not_valid(mw)


def test_a_settle_step_that_misses_the_planted_row_is_refused_not_a_crash(mw, monkeypatch):
    """Not the warning mutant: a pre-check that sees no planted row sends VALIDATE at it, and since round 4 that
    CheckViolation is the refusal (ConfigError, exit 2), the same as `--validate-constraints`."""
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", lambda db: [])
    with pytest.raises(ConfigError):
        real.test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(mw)


def test_a_migrate_with_its_warn_block_deleted_is_killed(mw, monkeypatch):
    """The block in `migrate()` that logs and appends the NOT VALID warning is cut out of its source."""
    src = inspect.getsource(migrate_mod.migrate)
    block = (
        '            _LOG.warning("migrate: %s", warn)\n'
        "            if notes is not None:\n"
        "                notes.append(warn)\n"
    )
    cut = src.replace(block, "            pass\n")
    assert cut != src and "notes.append(warn)" not in cut
    ns = dict(vars(migrate_mod))
    exec(compile(cut, "<mutant migrate>", "exec"), ns)  # noqa: S102 - our own source, cut in a test
    mw.migrate()
    monkeypatch.setattr(real, "migrate", ns["migrate"])
    with pytest.raises(AssertionError):  # no note names the planted row: the warning test sees it
        real.test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(mw)


def test_a_migrate_that_warns_on_every_not_valid_constraint_is_killed(mw, monkeypatch):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", migrate_mod.not_valid_constraints)
    with pytest.raises(AssertionError):
        real.test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(mw)


def test_a_0009_that_validates_unconditionally_is_killed():
    always = (
        SOURCE + "\nALTER TABLE kill_switch_stops VALIDATE CONSTRAINT kill_switch_stops_ts_range;\n"
    )
    with pytest.raises(
        psycopg.errors.CheckViolation
    ):  # VALIDATE fails the upgrade on the planted row
        real.raw_0009_world(plant_stop=True, source=always)
    with pytest.raises(
        AssertionError
    ):  # and on a clean database it validates early: the real check sees it
        real.check_real_0009_then_settle(source=always)


def test_a_settle_step_that_never_validates_is_killed(mw, monkeypatch):
    monkeypatch.setattr(migrate_mod, "settle_stop_constraints", migrate_mod.planted_ts_rows)
    with pytest.raises(AssertionError):
        real.test_a_clean_database_ends_validated_and_migrate_is_silent(mw)


def test_a_settle_step_that_validates_a_planted_row_too_is_killed(mw, monkeypatch):
    def everything(db):
        for pair in migrate_mod.not_valid_constraints(db):
            migrate_mod._validate_one(db, *pair)
        return []

    mw.migrate()
    real.make_not_valid(mw, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    monkeypatch.setattr(migrate_mod, "settle_stop_constraints", everything)
    with pytest.raises(
        psycopg.errors.CheckViolation
    ) as err:  # the upgrade fails on the planted row
        mw.migrate()
    assert not isinstance(err.value, KeyboardInterrupt)


# --- review round 3 ----------------------------------------------------------------------------------------------


def test_a_settle_step_without_timeouts_is_killed(mw, monkeypatch):
    @contextlib.contextmanager
    def no_timeouts(db):
        yield

    mw.migrate()
    monkeypatch.setattr(migrate_mod, "_stop_timeouts", no_timeouts)
    # Round 7: inside a plain `migrate` the lock limit of the whole transaction still ends such a wait (so the
    # locked-table test of `migrate` no longer sees this mutant, on purpose); the step's OWN limits are seen where
    # no other limit exists (`--validate-constraints`), and in the limits a real `migrate` sets for the step.
    with pytest.raises(
        pytest.fail.Exception
    ):  # it waits for the blocker instead of giving up: DID NOT RAISE
        real.test_the_validate_step_gives_up_on_a_locked_table_as_a_retry_condition(mw)
    with pytest.raises(AssertionError):  # the limits of the step are never set
        r6.limits_inside_migrate_scenario(monkeypatch)


def test_a_settle_step_that_leaves_its_timeouts_behind_is_killed(mw, monkeypatch):
    @contextlib.contextmanager
    def leaky(db):
        db.execute(
            "SELECT set_config('lock_timeout', '5s', true), set_config('statement_timeout', '60s', true)"
        )
        yield

    mw.migrate()
    monkeypatch.setattr(migrate_mod, "_stop_timeouts", leaky)
    with pytest.raises(AssertionError):
        real.test_the_settle_step_puts_the_transaction_timeouts_back(mw)


def test_a_validate_step_that_calls_a_lost_connection_a_refusal_is_killed(mw, monkeypatch):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "_busy", lambda exc, what: ConfigError(what))
    with pytest.raises(ConfigError):  # the real test expects StopTablesBusy for this case
        real.test_the_validate_step_separates_a_lost_connection_from_a_refusal(mw, monkeypatch)


def test_a_catalog_lookup_that_reparses_the_schema_name_is_killed(monkeypatch):
    def reparsing(db):
        rows = db.execute(
            "SELECT c.relname, k.conname FROM pg_catalog.pg_constraint k "
            "JOIN pg_catalog.pg_class c ON c.oid = k.conrelid "
            "WHERE c.relnamespace = pg_catalog.to_regnamespace(pg_catalog.current_schema()) "
            "AND NOT k.convalidated"
        ).fetchall()
        return [p for p in migrate_mod.NOT_VALID_BY_DESIGN if tuple(p) in {tuple(r) for r in rows}]

    monkeypatch.setattr(migrate_mod, "not_valid_constraints", reparsing)
    with pytest.raises(AssertionError):
        real.test_a_mixed_case_schema_is_found_by_the_validate_step_and_the_leftover_check()


# --- review round 4: every new line of logic has a killed mutant -------------------------------------------------

from tests import test_step_b_e7_round4 as r4
from tests.test_step_b_e7_round4 import decoy_world  # noqa: F401  (the `decoy` fixture)


def test_a_settle_step_without_the_shared_error_mapping_is_killed(mw, monkeypatch):
    """The pre-round-4 settle: VALIDATE's CheckViolation escapes raw (exit 3 instead of 2)."""
    mw.migrate()
    real.make_not_valid(mw, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", lambda db: [])
    monkeypatch.setattr(migrate_mod, "_validate_mapped", migrate_mod._validate_one)
    with (
        pytest.raises(psycopg.errors.CheckViolation),
        psycopg.connect(mw.scoped) as db,
        db.transaction(),
    ):
        migrate_mod.settle_stop_constraints(db)
    with pytest.raises(
        psycopg.errors.CheckViolation
    ):  # and the r4 test, which wants ConfigError, sees it
        r4.test_settle_refuses_a_real_planted_row_that_the_precheck_missed_as_a_config_error(
            mw, monkeypatch
        )


def test_a_mapping_that_calls_a_privilege_error_a_retry_is_killed(mw, monkeypatch):
    mw.migrate()
    real.make_not_valid(mw, tables=("kill_switch_stops",))

    def swapped(db, table, name):
        try:
            migrate_mod._validate_one(db, table, name)
        except psycopg.errors.InsufficientPrivilege as exc:
            raise migrate_mod.StopTablesBusy(str(exc)) from None

    monkeypatch.setattr(migrate_mod, "_validate_mapped", swapped)
    with pytest.raises(
        migrate_mod.StopTablesBusy
    ):  # the real test wants ConfigError, and fails on this
        r4.test_settle_refuses_a_login_that_is_not_the_owner_with_a_real_privilege_error(mw)


def test_a_mapping_that_calls_a_lost_connection_a_refusal_in_settle_is_killed(mw, monkeypatch):
    mw.migrate()
    real.make_not_valid(mw, tables=("kill_switch_stops",))
    monkeypatch.setattr(migrate_mod, "_busy", lambda exc, what: ConfigError(what))
    monkeypatch.setattr(
        migrate_mod,
        "_validate_one",
        lambda *a: (_ for _ in ()).throw(psycopg.OperationalError("x")),
    )
    with psycopg.connect(mw.scoped) as db, db.transaction(), pytest.raises(ConfigError):
        migrate_mod.settle_stop_constraints(
            db
        )  # wrong class; the injected-error test expects StopTablesBusy
    with pytest.raises(BaseException) as err:
        r4.test_settle_and_validate_map_a_validation_error_the_same_way(
            mw, monkeypatch, psycopg.OperationalError("x"), migrate_mod.StopTablesBusy, "settle"
        )
    assert not isinstance(err.value, KeyboardInterrupt)


def _one_timeout(which):
    @contextlib.contextmanager
    def cm(db):
        name, value = (
            ("lock_timeout", "5s") if which == "lock" else ("statement_timeout", "60s")
        )  # sets only one of the two
        db.execute("SELECT set_config(%s, %s, true)", (name, value))
        yield

    return cm


@pytest.mark.parametrize("which", ["lock", "statement"])
def test_a_step_that_sets_only_one_timeout_is_killed(mw, monkeypatch, which):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "_stop_timeouts", _one_timeout(which))
    with pytest.raises(AssertionError):
        r4.test_the_validation_runs_under_the_two_timeouts_and_a_slow_scan_is_a_retry_condition(
            mw, monkeypatch
        )


def test_a_step_with_no_statement_limit_is_killed(mw, monkeypatch):
    monkeypatch.setattr(
        migrate_mod, "VALIDATE_STATEMENT_TIMEOUT", "0"
    )  # the slow scan is not cut short
    with pytest.raises(BaseException) as err:
        r4.test_the_validation_runs_under_the_two_timeouts_and_a_slow_scan_is_a_retry_condition(
            mw, monkeypatch
        )
    assert not isinstance(err.value, KeyboardInterrupt)


@pytest.mark.parametrize(
    ("name", "value"), [("VALIDATE_LOCK_TIMEOUT", "1s"), ("VALIDATE_STATEMENT_TIMEOUT", "30s")]
)
def test_changed_timeout_constants_are_killed(monkeypatch, name, value):
    monkeypatch.setattr(migrate_mod, name, value)
    with pytest.raises(AssertionError):
        r4.test_the_runbook_states_the_numbers_the_code_uses()


def test_a_step_that_never_restores_on_error_is_killed(mw, monkeypatch):
    @contextlib.contextmanager
    def no_finally(db):
        db.execute("SELECT set_config('lock_timeout', '5s', true)")
        yield
        db.execute("SELECT set_config('lock_timeout', '0', true)")

    monkeypatch.setattr(migrate_mod, "_stop_timeouts", no_finally)
    with pytest.raises(AssertionError):
        r4.test_the_timeouts_are_restored_when_the_step_raises_and_the_original_error_survives(mw)


def test_a_step_that_restores_in_an_aborted_transaction_is_killed(mw, monkeypatch):
    @contextlib.contextmanager
    def always(db):
        db.execute("SELECT set_config('lock_timeout', '5s', true)")
        try:
            yield
        finally:  # no transaction-state check: on a database error the original error is replaced
            db.execute("SELECT set_config('lock_timeout', '0', true)")

    monkeypatch.setattr(migrate_mod, "_stop_timeouts", always)
    with pytest.raises(BaseException) as err:
        r4.test_the_timeouts_are_restored_when_the_step_raises_and_the_original_error_survives(mw)
    assert isinstance(err.value, psycopg.errors.InFailedSqlTransaction)


def test_a_bare_name_lookup_is_killed(decoy, monkeypatch):
    monkeypatch.setattr(migrate_mod, "_qualified", lambda db, name: name)
    with pytest.raises(AssertionError):
        r4.test_the_pin_grant_and_check_steps_never_touch_another_schemas_objects(decoy)


def test_a_bare_table_in_the_validate_and_grant_statements_is_killed(monkeypatch):
    monkeypatch.setattr(migrate_mod, "_in_schema", lambda db, table: psycopg.sql.Identifier(table))
    with pytest.raises(AssertionError):
        r4.test_the_validation_and_grant_statements_name_the_schema()


def test_grants_on_a_bare_table_name_are_killed(monkeypatch):
    src = inspect.getsource(migrate_mod._apply_grants)
    cut = src.replace(
        'sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(name))',
        "sql.Identifier(name)",
    )
    assert cut != src
    ns = dict(vars(migrate_mod))
    exec(compile(cut, "<mutant _apply_grants>", "exec"), ns)  # noqa: S102 - our own source, cut in a test
    monkeypatch.setattr(migrate_mod, "_apply_grants", ns["_apply_grants"])
    with pytest.raises(AssertionError):
        r4.test_the_validation_and_grant_statements_name_the_schema()
