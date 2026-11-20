"""Migration 0009 (stop state hardening, E12 Medium 3, Medium 4, Low 6) against a real PostgreSQL: the reset's own
record table is writable by the reset role only, a planted audit seq or a planted stop year is refused, the watermark
table and the stop index exist, and `migrate` applies the file on a fresh schema and on an upgrade from 0008.
Throwaway schema and roles with unique names, dropped after. Needs HADAVIN_TEST_PG_DSN; skipped without it."""

from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store.migrate import GRANTS, migrate

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

DENIED = errors.InsufficientPrivilege
FILE_0009 = migrate_mod.MIGRATIONS / "0009_stop_state_hardening.sql"
NEW_TABLES = (
    "kill_switch_resets",
    "hadavin_limits",
    "hadavin_caps",
)  # 0009 and 0011
ROW = "(seq, at, run_id, kind, body, prev, hash, event_id) VALUES (%s, 'a', 'r', 'k', 'b', 'p', 'h', %s)"


class World:
    def __init__(self):
        self.sfx = uuid.uuid4().hex[:10]
        self.dsn = os.environ["HADAVIN_TEST_PG_DSN"]
        self.schema = f"e7_s_{self.sfx}"
        self.runtime, self.portal, self.purge, self.reset = (
            f"e7_{n}_{self.sfx}" for n in ("rt", "po", "pu", "rs")
        )
        self.roles = [self.runtime, self.portal, self.purge, self.reset]
        self.scoped = make_conninfo(self.dsn, options=f"-c search_path={self.schema}")

    def migrate(self, **kw):
        return migrate(
            self.scoped,
            runtime_role=self.runtime,
            portal_role=self.portal,
            purge_role=self.purge,
            reset_role=self.reset,
            **kw,
        )

    def as_(self, role):
        return psycopg.connect(make_conninfo(self.scoped, user=role), autocommit=True)

    def admin(self):
        return psycopg.connect(self.scoped, autocommit=True)

    def run(self, statement, params=()):
        with self.admin() as db:
            return db.execute(statement, params).fetchall()

    def seq_row(self, role, seq):
        with self.as_(role) as db:
            db.execute(f"INSERT INTO audit_entries {ROW}", (seq, f"ev-{seq}-{uuid.uuid4().hex}"))


def make_world():
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    return w


def drop_world(w):
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


@pytest.fixture(name="w")
def world():
    w = make_world()
    try:
        w.migrate()
        yield w
    finally:
        drop_world(w)


def test_migration_file_is_numbered_0009_and_the_ledger_has_it(w):
    assert FILE_0009.exists()
    assert migrate_mod.check_ledger(migrate_mod._migration_files()) == []
    assert migrate_mod.check_grants(migrate_mod._migration_files()) == []
    assert ("0009_stop_state_hardening",) in w.run("SELECT version FROM schema_migrations")


def test_runtime_cannot_insert_into_the_reset_record_but_the_reset_role_can(w):
    with w.as_(w.runtime) as db:
        with pytest.raises(DENIED):
            db.execute("INSERT INTO kill_switch_resets (\"by\") VALUES ('rt')")
        with pytest.raises(DENIED):
            db.execute("SELECT * FROM kill_switch_resets")
    with w.as_(w.reset) as db:
        db.execute("INSERT INTO kill_switch_resets (\"by\", audit_seq) VALUES ('rs', 1)")
        assert db.execute("SELECT count(*) FROM kill_switch_resets").fetchone()[0] == 1
        with pytest.raises(DENIED):
            db.execute("UPDATE kill_switch_resets SET \"by\" = 'x'")
    with (
        pytest.raises(psycopg.errors.RaiseException),
        w.admin() as db,
    ):  # append-only even for the owner
        db.execute("DELETE FROM kill_switch_resets")


def test_grant_rows_say_the_same(w):
    assert GRANTS["kill_switch_resets"].runtime == ""
    assert GRANTS["kill_switch_resets"].reset == "SELECT, INSERT"
    assert "kill_switch_watermark" not in GRANTS


def test_there_is_no_watermark_table_and_no_guard_function(w):
    """Review N3: nothing read the watermark, so it is gone (and its trigger function with it)."""
    rel = w.run("SELECT to_regclass(%s)::text", (f"{w.schema}.kill_switch_watermark",))[0][0]
    fn = w.run(
        "SELECT count(*) FROM pg_proc WHERE proname = 'hadavin_watermark_guard' AND pronamespace = %s::regnamespace",
        (w.schema,),
    )[0][0]
    assert (rel, fn) == (None, 0)


STOP_YEAR_CONSTRAINTS = ["kill_switch_clears_ts_range", "kill_switch_stops_ts_range"]


def _validated(w):
    """The names of the stop-year constraints PostgreSQL itself calls validated (not our own helper)."""
    return sorted(
        r[0]
        for r in w.run(
            "SELECT k.conname FROM pg_constraint k JOIN pg_namespace n ON n.oid = k.connamespace "
            "WHERE k.conname = ANY(%s) AND k.convalidated AND n.nspname = %s",
            (STOP_YEAR_CONSTRAINTS, w.schema),
        )
    )


def test_migrate_warns_while_a_constraint_is_not_valid_and_the_validate_step_clears_it(w):
    notes: list[str] = []
    w.migrate(
        notes=notes
    )  # a second run on the migrated schema: nothing new, the warning is still there
    assert any(
        "NOT VALID" in n and "kill_switch_stops_ts_range" in n and "--validate-constraints" in n
        for n in notes
    ), notes
    assert _validated(w) == []
    done = migrate_mod.validate_stop_constraints(w.scoped)
    assert sorted(done) == STOP_YEAR_CONSTRAINTS
    assert _validated(w) == STOP_YEAR_CONSTRAINTS  # both really validated, read from pg_constraint
    again: list[str] = []
    w.migrate(notes=again)
    assert not any("NOT VALID" in n for n in again), again  # no warning once validated
    assert migrate_mod.validate_stop_constraints(w.scoped) == []  # idempotent


def test_the_validate_step_refuses_naming_the_constraint_while_a_planted_row_exists(w):
    # plant what an upgrade from before 0009 can hold: drop the check, add the row, put the check back NOT VALID
    with w.admin() as db:
        db.execute("ALTER TABLE kill_switch_stops DROP CONSTRAINT kill_switch_stops_ts_range")
        db.execute("INSERT INTO kill_switch_stops (ts) VALUES ('0100-01-01 BC')")
        db.execute(
            "ALTER TABLE kill_switch_stops ADD CONSTRAINT kill_switch_stops_ts_range "
            "CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID"
        )
    with pytest.raises(ConfigError, match="kill_switch_stops_ts_range"):
        migrate_mod.validate_stop_constraints(w.scoped)
    assert "kill_switch_stops_ts_range" not in _validated(w)


def test_the_open_stops_index_exists(w):
    rows = w.run(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = 'kill_switch_stops'",
        (w.schema,),
    )
    assert any("(ts)" in r[0] for r in rows), rows


def test_a_planted_audit_seq_is_refused_and_exact_next_is_accepted(w):
    for seq in (1, 2):
        w.seq_row(w.runtime, seq)
    for bad in (9007199254740993, 5, 2, 1, 0, -3):
        with pytest.raises(psycopg.errors.CheckViolation):
            w.seq_row(w.runtime, bad)
    w.seq_row(w.reset, 3)  # the reset role appends too
    assert [r[0] for r in w.run("SELECT seq FROM audit_entries ORDER BY seq")] == [1, 2, 3]


def test_the_first_audit_row_must_be_seq_1(w):
    with pytest.raises(psycopg.errors.CheckViolation):
        w.seq_row(w.runtime, 2)


@pytest.mark.parametrize("year", ["0100-01-01 BC", "20000-01-01", "1999-12-31", "2100-01-02"])
@pytest.mark.parametrize("table", ["kill_switch_stops", "kill_switch_clears"])
def test_planted_stop_years_are_refused(w, table, year):
    ts = f"{year}"
    if table == "kill_switch_stops":
        stmt, params = "INSERT INTO kill_switch_stops (ts) VALUES (%s)", (ts,)
    else:
        sid = uuid.uuid4()
        w.run("INSERT INTO kill_switch_stops (id) VALUES (%s) RETURNING id", (sid,))
        stmt, params = "INSERT INTO kill_switch_clears (stop_id, ts) VALUES (%s, %s)", (sid, ts)
    role = w.runtime if table == "kill_switch_stops" else w.reset
    with w.as_(role) as db, pytest.raises(psycopg.errors.CheckViolation):
        db.execute(stmt, params)


def test_a_normal_stop_still_works(w):
    with w.as_(w.runtime) as db:
        db.execute("INSERT INTO kill_switch_stops (\"by\") VALUES ('ops')")


def test_fresh_schema_and_upgrade_from_0008(w, monkeypatch):
    # fresh schema: the fixture already did it. Upgrade: a schema whose ledger stops at 0008, then migrate.
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
            m.setattr(  # the 0011 functions do not exist at 0008 either
                migrate_mod,
                "FUNCTION_GRANTS",
                {
                    k: v
                    for k, v in migrate_mod.FUNCTION_GRANTS.items()
                    if k not in migrate_mod.MONEY_FUNCTIONS
                },
            )
            up.migrate()
        assert not up.run("SELECT to_regclass('kill_switch_resets')")[0][0]
        up.migrate()
        assert up.run("SELECT to_regclass('kill_switch_resets') IS NOT NULL")[0][0]
        assert ("0009_stop_state_hardening",) in up.run("SELECT version FROM schema_migrations")
        up.seq_row(up.runtime, 1)
        with pytest.raises(psycopg.errors.CheckViolation):
            up.seq_row(up.runtime, 99)
    finally:
        drop_world(up)
