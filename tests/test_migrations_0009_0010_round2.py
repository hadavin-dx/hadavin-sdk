"""Review round 2 of migrations 0009 and 0010 (tickets/migrations-0009-0010-review-1.md), real PostgreSQL.

Fixed in place (0009/0010 are unreleased): H3 the seq guard cannot be fooled by a temp table, M1 the stop-year
CHECKs are NOT VALID so an upgrade never fails on a planted row, M2 audit_checkpoints has a seq guard, M3 the
(agent_id, day) index of the money guard. The
former bypass pins (H1, H2 twice, L2) were xfail(strict) while the money guard was a tripwire; since F-money-definer
step 4 the runtime login holds no write right on the money tables, so each is a plain test: the attack is refused
with insufficient_privilege and nothing changes. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg

from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store.migrate import FUNCTION_GRANTS, GRANTS
from tests.test_step_b_e7_migration_0009 import NEW_TABLES, ROW, drop_world, make_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

ROOT = Path(__file__).resolve().parent.parent
HANDOVER = ROOT / "handover" / "core-b"


@pytest.fixture(name="w")
def world():
    w = make_world()
    try:
        w.migrate()
        yield w
    finally:
        drop_world(w)


def _pins(w, name):
    return w.run(
        "SELECT proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE p.proname = %s AND n.nspname = %s",
        (name, w.schema),
    )[0][0]


# --- H3: the seq guard and the checkpoint guard are search-path safe -----------------------------------------------


@pytest.mark.parametrize("fn", ["hadavin_audit_seq_guard", "hadavin_audit_checkpoint_guard"])
def test_guard_functions_pin_catalog_schema_temp_last(w, fn):
    assert _pins(w, fn) == [f"search_path=pg_catalog, {w.schema}, pg_temp"]


def test_a_temp_table_named_audit_entries_cannot_stand_in_for_the_seq_guard(w):
    with w.as_(w.runtime) as db:
        db.execute("CREATE TEMP TABLE audit_entries (seq bigint)")
        db.execute("INSERT INTO pg_temp.audit_entries VALUES (3999999999999999999)")
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute(
                f"INSERT INTO {w.schema}.audit_entries {ROW}", (4000000000000000000, "x-temp")
            )
    assert w.run("SELECT count(*) FROM audit_entries")[0][0] == 0


def test_a_temp_table_cannot_stand_in_for_the_checkpoint_guard(w):
    w.seq_row(w.runtime, 1)
    with w.as_(w.runtime) as db:
        db.execute("CREATE TEMP TABLE audit_entries (seq bigint, hash text)")
        db.execute("INSERT INTO pg_temp.audit_entries VALUES (4000000000000000000, 'h')")
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute(
                f"INSERT INTO {w.schema}.audit_checkpoints (seq, hash, signature) "  # noqa: S608
                "VALUES (4000000000000000000, 'h', 's')"
            )


def test_a_hand_run_create_or_replace_is_repinned_on_the_next_migrate(w):
    with w.admin() as db:
        db.execute("ALTER FUNCTION hadavin_audit_seq_guard() SET search_path = pg_catalog")
        db.execute("ALTER FUNCTION hadavin_audit_checkpoint_guard() SET search_path = pg_catalog")
    w.migrate()
    for fn in ("hadavin_audit_seq_guard", "hadavin_audit_checkpoint_guard"):
        assert _pins(w, fn) == [f"search_path=pg_catalog, {w.schema}, pg_temp"]


# --- M2: audit_checkpoints seq guard -------------------------------------------------------------------------------


def test_a_planted_checkpoint_seq_is_refused_and_a_real_one_accepted(w):
    w.seq_row(w.runtime, 1)
    w.seq_row(w.runtime, 2)
    ins = "INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (%s, %s, 's')"
    with w.as_(w.runtime) as db:
        for seq, h in ((4000000000000000000, "h"), (3, "h"), (0, "h"), (-1, "h"), (2, "wrong")):
            with pytest.raises(psycopg.errors.CheckViolation):
                db.execute(ins, (seq, h))
        db.execute(ins, (2, "h"))  # the head, with the hash of that row
    assert [r[0] for r in w.run("SELECT seq FROM audit_checkpoints")] == [2]


# --- M3: the index of the money guard's scans ----------------------------------------------------------------------


def test_spend_reservations_has_an_agent_day_index(w):
    rows = w.run(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = 'spend_reservations'",
        (w.schema,),
    )
    assert any("(agent_id, day)" in r[0] for r in rows), rows


# --- M1: the stop-year CHECKs are NOT VALID: an upgrade holding a planted ts succeeds -----------------------------


def test_upgrade_from_0008_with_a_planted_ts_succeeds_and_new_plants_are_refused(monkeypatch):
    up = make_world()
    try:
        real, grants = migrate_mod._migration_files, dict(GRANTS)
        with monkeypatch.context() as m:
            m.setattr(
                migrate_mod,
                "_migration_files",
                lambda *a, **k: [p for p in real(*a, **k) if p.name < "0009"],
            )
            m.setattr(
                migrate_mod, "GRANTS", {k: v for k, v in grants.items() if k not in NEW_TABLES}
            )
            m.setattr(  # the money functions of 0011 do not exist yet in this old schema
                migrate_mod,
                "FUNCTION_GRANTS",
                {migrate_mod.RELEASE_FUNCTION: FUNCTION_GRANTS[migrate_mod.RELEASE_FUNCTION]},
            )
            m.setattr(migrate_mod, "MONEY_FUNCTIONS", ())
            up.migrate()
        # the owner plants a year the 0006 isfinite check lets through (append-only: no one can delete it later)
        sid = uuid.uuid4()
        up.run(
            "INSERT INTO kill_switch_stops (id, ts) VALUES (%s, '0100-01-01 BC') RETURNING 1",
            (sid,),
        )
        up.run(
            "INSERT INTO kill_switch_clears (stop_id, ts) VALUES (%s, '0100-01-01 BC') RETURNING 1",
            (sid,),
        )
        up.migrate()  # must not raise CheckViolation
        assert ("0010_money_guard",) in up.run("SELECT version FROM schema_migrations")
        for table in ("kill_switch_stops", "kill_switch_clears"):
            name = f"{table}_ts_range"
            assert up.run(
                "SELECT convalidated FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace "
                "WHERE c.conname = %s AND n.nspname = %s",
                (name, up.schema),
            ) == [(False,)]
        with up.as_(up.runtime) as db, pytest.raises(psycopg.errors.CheckViolation):
            db.execute("INSERT INTO kill_switch_stops (ts) VALUES ('0100-01-01 BC')")
        # the documented later step: VALIDATE fails while the planted row exists (the operator fixes it first)
        with up.admin() as db, pytest.raises(psycopg.errors.CheckViolation):
            db.execute(
                "ALTER TABLE kill_switch_stops VALIDATE CONSTRAINT kill_switch_stops_ts_range"
            )
    finally:
        drop_world(up)


def test_validate_constraint_works_on_a_clean_database(w):
    with w.admin() as db:
        db.execute("ALTER TABLE kill_switch_stops VALIDATE CONSTRAINT kill_switch_stops_ts_range")
        db.execute("ALTER TABLE kill_switch_clears VALIDATE CONSTRAINT kill_switch_clears_ts_range")


# --- the documentation says what the guard does (H1, H2, L1, L2) ---------------------------------------------------


def _read(path):
    return path.read_text()


def test_0008_and_0010_headers_do_not_promise_an_unbreakable_guard():
    mig = ROOT / "src/hadavin_sdk/store/migrations"
    h8 = _read(mig / "0008_release_expired_spend.sql")
    h10 = _read(mig / "0010_money_guard.sql")
    assert "ONLY way" not in h8
    assert "no further" not in h10
    for text in (h8, h10):
        assert "tripwire" in text.lower()
    assert "NOT VALID" in _read(mig / "0009_stop_state_hardening.sql")
    assert "VALIDATE CONSTRAINT" in _read(mig / "0009_stop_state_hardening.sql")


def test_runbook_and_tickets_state_the_limits_and_the_emergency_disable():
    book = _read(ROOT / "docs/stop-state-runbook.md")
    assert "DISABLE TRIGGER" in book and "ENABLE TRIGGER" in book
    assert "VALIDATE CONSTRAINT" in book
    for path in (
        ROOT / "docs/stop-state-runbook.md",
        HANDOVER / "tickets/B-stop-state.md",
        HANDOVER / "tickets/F-store.md",
    ):
        text = _read(path)
        assert "tripwire" in text.lower(), path
        assert not re.search(r"pinned FROM CURRENT", text), path
    assert "definer" in _read(HANDOVER / "tickets/F-store.md").lower()


# --- the former bypasses, now refused (F-money-definer step 4: the runtime login holds no write right) --------------


def _seed_money(w):
    """Counter 100 (90 of it a plain charge, a 10 hold open) for agent ag on a day of the month."""
    w.run("INSERT INTO spend (agent_id, day, usd) VALUES ('ag', '2026-11-10', 100) RETURNING 1")
    w.run(
        "INSERT INTO spend_month (agent_id, month, usd) VALUES ('ag', '2026-11-01', 100) RETURNING 1"
    )
    w.run(
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd) "
        "VALUES ('h1', 'ag', '2026-11-10', 10) RETURNING 1"
    )


def _counter(w):
    return w.run("SELECT usd FROM spend WHERE agent_id = 'ag'")[0][0]


def _refused_each(db, statements):
    """Run each statement in a transaction of its own; every one must be refused with insufficient_privilege."""
    for stmt in statements:
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute(stmt)


SETTLE = (
    "UPDATE spend_reservations SET status = 'settled', settled_usd = 0, closed_at = clock_timestamp() "
    "WHERE reservation_id = 'h1'"
)
LOWER10 = "UPDATE spend SET usd = usd - 10 WHERE agent_id = 'ag'"


def test_a_plain_lowering_update_is_refused(w):
    _seed_money(w)
    with w.as_(w.runtime) as db, pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id = 'ag'")
    assert _counter(w) == 100


def test_H1_one_settle_then_repeated_lowering_is_refused(w):
    _seed_money(w)
    with w.as_(w.runtime) as db:
        _refused_each(db, [SETTLE, LOWER10, LOWER10, LOWER10])
    assert _counter(w) == 100  # the charge of the other 90 stays


def test_H2_forged_settled_hold_by_insert_is_refused(w):
    _seed_money(w)
    fake = (
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "
        "closed_at) VALUES ('fake', 'ag', '2026-11-10', 90, 0, 'settled', now())"
    )
    with w.as_(w.runtime) as db:
        _refused_each(db, [fake, "UPDATE spend SET usd = 10 WHERE agent_id = 'ag'"])
    assert _counter(w) == 100
    assert w.run("SELECT count(*) FROM spend_reservations WHERE reservation_id = 'fake'") == [(0,)]


def test_H2_inflating_reserved_usd_after_a_settle_is_refused(w):
    _seed_money(w)
    inflate = "UPDATE spend_reservations SET reserved_usd = 1000 WHERE reservation_id = 'h1'"
    with w.as_(w.runtime) as db:
        _refused_each(db, [SETTLE, inflate, "UPDATE spend SET usd = 0 WHERE agent_id = 'ag'"])
    assert _counter(w) == 100
    assert w.run(
        "SELECT reserved_usd, status FROM spend_reservations WHERE reservation_id = 'h1'"
    ) == [(10, "open")]


def test_L2_the_runtime_login_is_not_the_function_owner_and_is_refused(w):
    """The old pin was a login shared with the migration owner. The runtime login now has no write right at all
    (the owner of the functions is a different login), so the lowering UPDATE is refused by the missing GRANT."""
    _seed_money(w)
    owner = w.run(
        "SELECT proowner::regrole::text FROM pg_proc WHERE proname = 'hadavin_settle_spend'"
    )[0][0]
    assert owner.strip('"') != w.runtime
    with w.as_(w.runtime) as db:
        _refused_each(db, ["UPDATE spend SET usd = usd - 1 WHERE agent_id = 'ag'"])
    assert _counter(w) == 100
