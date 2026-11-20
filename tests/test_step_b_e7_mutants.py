"""Mutants of migration 0009: each one is applied (as a scratch copy of the SQL, in a scratch schema) and a test of
tests/test_step_b_e7_migration_0009.py must fail. A mutant that survives means the test is blind. Needs
HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk.store import migrate as migrate_mod
from tests import test_step_b_e7_migration_0009 as real
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
    return _cut(t, "ALTER TABLE kill_switch_stops ADD CONSTRAINT", "$do$;")


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


def test_a_migrate_that_never_warns_is_killed(mw, monkeypatch):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", lambda db: [])
    with pytest.raises(AssertionError):
        real.test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(mw)


def test_a_migrate_that_warns_on_every_not_valid_constraint_is_killed(mw, monkeypatch):
    mw.migrate()
    monkeypatch.setattr(migrate_mod, "planted_ts_rows", migrate_mod.not_valid_constraints)
    with pytest.raises(AssertionError):
        real.test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(mw)


def test_an_unconditional_validate_inside_0009_is_killed():
    always = SOURCE.replace(
        "IF NOT EXISTS (SELECT 1 FROM kill_switch_stops WHERE",
        "IF TRUE OR EXISTS (SELECT 1 FROM kill_switch_stops WHERE",
    )
    assert always != SOURCE
    with pytest.raises(BaseException) as err:  # VALIDATE fails the upgrade on the planted row
        real.check_real_0009_validates_clean_and_upgrades_planted(source=always)
    assert not isinstance(err.value, KeyboardInterrupt)


def test_a_0009_that_never_validates_is_killed():
    never = _cut(SOURCE, "DO $do$", "$do$;")
    assert never != SOURCE
    with pytest.raises(AssertionError):
        real.check_real_0009_validates_clean_and_upgrades_planted(source=never)
