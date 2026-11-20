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


def make_not_valid(w, plant=None, tables=("kill_switch_stops", "kill_switch_clears")):
    """What an upgrade from before 0009 can leave: the check dropped, an optional planted stop ts, the check back
    NOT VALID."""
    with w.admin() as db:
        for table in tables:
            db.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_ts_range")
        if plant:
            db.execute("INSERT INTO kill_switch_stops (ts) VALUES (%s)", (plant,))
        for table in tables:
            db.execute(
                f"ALTER TABLE {table} ADD CONSTRAINT {table}_ts_range "
                "CHECK (ts BETWEEN '2000-01-01' AND '2100-01-01') NOT VALID"
            )


def test_a_clean_database_ends_validated_and_migrate_is_silent(w):
    notes: list[str] = []
    w.migrate(notes=notes)
    assert (
        _validated(w) == STOP_YEAR_CONSTRAINTS
    )  # the real 0009 validated both, read from pg_constraint
    assert not any("NOT VALID" in n for n in notes), notes


def test_migrate_warns_while_a_planted_row_blocks_validation_and_is_silent_without_one(w):
    make_not_valid(w, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    notes: list[str] = []
    w.migrate(notes=notes)
    warned = [n for n in notes if "NOT VALID" in n]
    assert len(warned) == 1 and "kill_switch_stops_ts_range" in warned[0], notes
    assert "kill_switch_clears_ts_range" not in warned[0]  # that table has no planted row
    assert "--validate-constraints" in warned[0]
    with (
        w.admin() as db
    ):  # the owner here is a superuser, which can remove what the append-only trigger guards
        db.execute("ALTER TABLE kill_switch_stops DISABLE TRIGGER USER")
        db.execute("DELETE FROM kill_switch_stops WHERE ts < '2000-01-01'")
        db.execute("ALTER TABLE kill_switch_stops ENABLE TRIGGER USER")
    again: list[str] = []
    w.migrate(notes=again)  # still NOT VALID, no bad row any more: silent
    assert not any("NOT VALID" in n for n in again), again
    assert "kill_switch_stops_ts_range" not in _validated(w)


def test_the_validate_step_validates_what_is_not_valid(w):
    make_not_valid(w)
    assert _validated(w) == []
    done = migrate_mod.validate_stop_constraints(w.scoped)
    assert sorted(done) == STOP_YEAR_CONSTRAINTS
    assert _validated(w) == STOP_YEAR_CONSTRAINTS  # read from pg_constraint, not from our helper
    assert migrate_mod.validate_stop_constraints(w.scoped) == []  # idempotent


def test_the_validate_step_refuses_naming_the_constraint_while_a_planted_row_exists(w):
    make_not_valid(w, plant="0100-01-01 BC", tables=("kill_switch_stops",))
    with pytest.raises(ConfigError, match="kill_switch_stops_ts_range"):
        migrate_mod.validate_stop_constraints(w.scoped)
    assert "kill_switch_stops_ts_range" not in _validated(w)


def test_the_validate_step_gives_up_on_a_locked_table_as_a_config_error(w):
    make_not_valid(w, tables=("kill_switch_stops",))
    with w.admin() as blocker:
        blocker.execute("BEGIN")
        blocker.execute("LOCK TABLE kill_switch_stops IN ACCESS EXCLUSIVE MODE")
        with pytest.raises(ConfigError, match="locked"):
            migrate_mod.validate_stop_constraints(w.scoped)
        blocker.execute("ROLLBACK")


def test_migrate_refuses_a_database_that_ran_an_earlier_unreleased_0009(w):
    with w.admin() as db:
        db.execute("CREATE TABLE kill_switch_watermark (id BOOLEAN PRIMARY KEY DEFAULT TRUE)")
    with pytest.raises(ConfigError, match="earlier unreleased 0009.*kill_switch_watermark"):
        w.migrate()
    with w.admin() as db:
        db.execute("DROP TABLE kill_switch_watermark")
        db.execute(
            "CREATE FUNCTION hadavin_watermark_guard() RETURNS trigger LANGUAGE plpgsql "
            "AS $f$ BEGIN RETURN NEW; END $f$"
        )
    with pytest.raises(ConfigError, match="hadavin_watermark_guard"):
        w.migrate()


def raw_0009_world(plant_stop=False, source=None):
    """A scratch schema holding 0001-0008 run raw (no migrate, no roles), then the REAL 0009 text (or `source`)."""
    schema = f"e7_r_{uuid.uuid4().hex[:10]}"
    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    conn = psycopg.connect(make_conninfo(dsn, options=f"-c search_path={schema}"), autocommit=True)
    try:
        for path in migrate_mod._migration_files():
            if path.name < "0009":
                conn.execute(path.read_text(encoding="utf-8"))
        if plant_stop:  # the year check of 0006 lets this through (isfinite only)
            conn.execute("INSERT INTO kill_switch_stops (ts) VALUES ('0100-01-01 BC')")
        conn.execute(source if source is not None else FILE_0009.read_text(encoding="utf-8"))
        return conn, schema
    except BaseException:
        conn.close()
        drop_raw(schema)
        raise


def drop_raw(schema):
    with psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"], autocommit=True) as db:
        db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def _validated_in(conn):
    rows = conn.execute(
        "SELECT conname FROM pg_constraint WHERE conname = ANY(%s) AND convalidated",
        (STOP_YEAR_CONSTRAINTS,),
    ).fetchall()
    return sorted(r[0] for r in rows)


def check_real_0009_validates_clean_and_upgrades_planted(source=None):
    """The real 0009 SQL: a clean database ends validated; a database with a planted stop ts still upgrades, the
    constraint on the planted table stays NOT VALID and the other table's is validated."""
    conn, schema = raw_0009_world(source=source)
    try:
        assert _validated_in(conn) == STOP_YEAR_CONSTRAINTS
    finally:
        conn.close()
        drop_raw(schema)
    conn, schema = raw_0009_world(plant_stop=True, source=source)  # must not raise
    try:
        assert _validated_in(conn) == ["kill_switch_clears_ts_range"]
        assert migrate_mod.planted_ts_rows(conn) == [
            ("kill_switch_stops", "kill_switch_stops_ts_range")
        ]
    finally:
        conn.close()
        drop_raw(schema)


def test_the_real_0009_validates_a_clean_database_and_survives_a_planted_row():
    check_real_0009_validates_clean_and_upgrades_planted()


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
