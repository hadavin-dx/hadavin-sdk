"""Killing tests for the money guard of 0010: each mutant is a COPY of the SQL (never the repo file) applied in a
scratch schema of its own; the attack battery of `test_money_guard_pg` must get through on every mutant that
weakens the guard, and the release must break on the mutant that over-tightens it. The control (the real SQL) is
refused, so the battery is proven to be able to tell."""

from __future__ import annotations

import os
import shutil

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.store import migrate as mig
from tests.test_money_guard_pg import lowering_attacks, seed, trigger_role
from tests.test_release_expired_spend_pg import (
    _expire,
    _release,
    _reserve,
)
from tests.test_stop_state_roles import World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

SQL = mig.MIGRATIONS / "0010_money_guard.sql"
OWNER_CHECK = "IF release_owner IS NULL OR current_user::name IS DISTINCT FROM release_owner THEN"

MUTANTS = {
    "control": (lambda t: t, False),
    "trigger_removed_spend": (
        lambda t: t.replace(
            "CREATE TRIGGER spend_money_guard BEFORE UPDATE ON spend\n",
            "-- gone\nCREATE TRIGGER x_unused BEFORE DELETE ON spend\n",
        ),
        True,
    ),
    "trigger_removed_all_counters": (
        lambda t: t.replace("BEFORE UPDATE ON spend_month", "BEFORE DELETE ON spend_month").replace(
            "BEFORE UPDATE ON spend\n", "BEFORE DELETE ON spend\n"
        ),
        True,
    ),
    "trigger_removed_reservations": (
        lambda t: t.replace(
            "BEFORE UPDATE ON spend_reservations", "BEFORE DELETE ON spend_reservations"
        ),
        True,
    ),
    "release_owner_check_removed": (lambda t: t.replace(OWNER_CHECK, "IF false THEN"), True),
    "release_owner_check_is_a_plain_switch": (
        lambda t: t.replace(
            OWNER_CHECK,
            "IF pg_catalog.current_setting('hadavin.release', true) IS DISTINCT FROM 'on' THEN",
        ),
        True,
    ),
    "release_owner_not_let_through": (
        lambda t: t.replace(OWNER_CHECK, "IF true THEN"),
        "release breaks",
    ),
}


def _world_with(tmp_path, monkeypatch, mutate):
    text = SQL.read_text(encoding="utf-8")
    mutated = mutate(text)
    folder = tmp_path / "migrations"
    shutil.copytree(mig.MIGRATIONS, folder)
    (folder / SQL.name).write_text(mutated, encoding="utf-8")
    real = mig._migration_files
    monkeypatch.setattr(mig, "_migration_files", lambda folder_=None: real(folder))
    return mutated != text


@pytest.fixture(name="scratch")
def scratch_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    world.release = world.new_role("rl")
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
def test_the_attack_battery_kills_every_mutant_of_the_guard(name, scratch, tmp_path, monkeypatch):
    mutate, expect = MUTANTS[name]
    changed = _world_with(tmp_path, monkeypatch, mutate)
    assert changed or name == "control", (
        "the mutation did not change the SQL: it would prove nothing"
    )
    w = scratch
    w.migrate(release_role=w.release)
    if expect == "release breaks":
        rt = w.store(w.runtime)
        rid = _reserve(rt, "1.00")
        _expire(w, rid)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            _release(w)
        return
    opened, settled = seed(w)
    # the battery runs as a login that holds the table rights, so the trigger (not the missing GRANT) decides
    went_through = lowering_attacks(w, opened, settled, role=trigger_role(w))
    assert bool(went_through) is expect, f"{name}: {went_through}"
