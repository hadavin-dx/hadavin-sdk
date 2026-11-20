"""Negative tests for the grants of migration 0007 (`spend_reservations`): what each database identity must NOT
be able to do with a reservation row.

Written by a test-writer that did not build the code under test (session core-c; the builder of the store, of
migration 0007 and of its `GRANTS` row is session core-b, commit 8db9c29). Style and helpers of
tests/test_grants_negative_roles.py (imported, not copied). Two layers:

(a) Pure Python, no database: the `GRANTS` row of the table compared with a hand-written second copy (`HELD`).
    Since step 4 of F-money-definer (migration 0011, core-b: "the runtime login holds only SELECT on `spend` and
    `spend_month` and nothing on `spend_reservations`; the purge login holds no table right (EXECUTE on the purge
    function only)") NO identity holds a table right on this table: every booking is a SECURITY DEFINER function,
    and `FUNCTION_GRANTS` says who may EXECUTE it (`EXECUTE_HELD`, the second copy of that map). The migration
    file is read for what it creates.
(b) PostgreSQL: a migrated schema, one fresh login role per identity (runtime, portal, purge, reset, release) plus a
    `stranger` that was never granted anything. Each role connects as itself and runs one statement per
    privilege: a cell `HELD` does not give must raise `psycopg.errors.InsufficientPrivilege`, a cell it gives
    must get past the privilege check. Then the column rights, the catalog, and statements on real rows.
    Needs HADAVIN_TEST_PG_DSN and is skipped without it, like the other database tests (`pg_schema`), UNLESS
    HADAVIN_REQUIRE_PG is 1, true or yes (parsed by the one reader, tests/triggers/conftest.py `strict`): then a
    missing DSN or driver is a FAILURE of every database test of this file.

Nothing in this file is skipped for a missing `spend_reservations` row of `GRANTS`: that is a FAILURE of every test
(pure and database). Where the helper module is missing, the database tests FAIL too (the file still collects).
Positive controls (`test_pg_control_*`) grant a right to a scratch role and prove the checking helpers SEE it.
"""

from __future__ import annotations

import inspect
import os
import re
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from decimal import Decimal

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.store import migrate as mig
from tests.contracts.kinds.store_postgres import pg_schema
from tests.triggers.conftest import strict  # the one reader of HADAVIN_REQUIRE_PG

try:  # the helpers of the per-role file: a connection AS a role, the schema name, one statement per privilege
    from tests.test_grants_negative_roles import PRIVILEGES, _as, _schema, _statements
except ImportError:  # reported by `_needs_the_helpers`, so this file still collects
    PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
    _as = _schema = _statements = None

TABLE = "spend_reservations"
MIGRATION = "0007_spend_reservations.sql"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def _the_grants_row_exists():
    """No skip: a deleted `spend_reservations` row of `GRANTS` fails every test of the file, pure ones included."""
    if TABLE not in mig.GRANTS:
        pytest.fail(f"no {TABLE} row in migrate.GRANTS: nothing of this file can be checked")


COLUMNS = (
    "reservation_id",
    "agent_id",
    "day",
    "run_id",
    "reserved_usd",
    "settled_usd",
    "status",
    "created_at",
    "closed_at",
)
# The reviewed second copy of the table rights: written by hand from migration 0011 (step 4: no identity holds a
# table right on `spend_reservations`) and from migrate.py `GRANTS`.
HELD: dict[str, set[str]] = {
    "runtime": set(),  # was SELECT, INSERT, UPDATE before step 4: it books through the functions now
    "portal": set(),
    "purge": set(),  # was DELETE plus two readable columns before step 4: it runs the purge function now
    "reset": set(),
    "release": set(),  # 0008: it runs the release function and appends to the audit, no money table
    "stranger": set(),
}
# The second copy of ALL of `FUNCTION_GRANTS` (signature -> the roles that may EXECUTE it; every other identity,
# PUBLIC included, may not). The five functions that touch `spend_reservations` come first; the last three are
# the counter and cap functions of 0011, also checked in tests/test_grants_negative_roles.py (FUNCTION_HOLDERS).
EXECUTE_HELD: dict[str, set[str]] = {
    "hadavin_reserve_spend(text, text, date, numeric, text)": {"runtime"},
    "hadavin_settle_spend(text, numeric, text)": {"runtime"},
    "hadavin_expire_spend_reservations(integer)": {"runtime"},
    "hadavin_purge_spend_reservations(timestamptz)": {"purge"},
    "hadavin_release_expired_spend(text, date)": {"release"},
    "hadavin_add_spend(text, date, numeric)": {"runtime"},
    "hadavin_set_cap(text, numeric, numeric, text)": {"reset"},
    "hadavin_cap_matches(text, numeric, numeric)": {"runtime", "reset"},
}
# The trigger functions (`EXCLUDED_FUNCTIONS`) that keep the default PUBLIC EXECUTE: 0010 revokes it from
# `hadavin_money_guard()` only, so every other one is open to everyone and the money guard to nobody (the owner
# is not an asker). A new trigger function needs its row here first.
TRIGGER_FUNCTIONS_OPEN_TO_PUBLIC = {
    "hadavin_audit_seq_guard()",
    "hadavin_audit_checkpoint_guard()",
    "hadavin_audit_append_only()",
    "hadavin_watermark_guard()",
}
COUNTERS = ("spend", "spend_month")  # what a reservation is booked on
# The booking day is NOT a constant: migration 0011 (`hadavin_reserve_spend`, `hadavin_add_spend`) refuses a day more
# than `hadavin_limits.max_day_skew` (= defaults.MAX_RESERVE_DAY_SKEW_DAYS = 1) days from the database's UTC date
# (`(clock_timestamp() AT TIME ZONE 'UTC')::date`), error 22023 "p_day window". Only the test-only wrapper of
# tests/money_caps_seed.py widens that window for the tests that book through the store; this file must not rely on
# that, so every day is read from the database clock of the very connection under test (`_db_today`).
DB_TODAY_SQL = "SELECT (clock_timestamp() AT TIME ZONE 'UTC')::date"
MARGIN_S = 600  # how much older than min_expiry_age a hold is seeded for the release test


def _split(privileges: str) -> set[str]:
    return {p.strip() for p in privileges.split(",") if p.strip()}


def _db_today(dsn: str):
    """The database's UTC date, the very day 0011 measures `max_day_skew` from. Never the Python clock."""
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute(DB_TODAY_SQL).fetchone()[0]


def _role_keywords() -> set[str]:
    return {p[:-5] for p in inspect.signature(mig.migrate).parameters if p.endswith("_role")}


def _map_gives(role: str) -> set[str]:
    """What `migrate()` grants the role on the table, read from the `GRANTS` row."""
    grant = mig.GRANTS[TABLE]
    if role == "portal":
        return {"SELECT"} if grant.portal else set()
    if role == "stranger":
        return set()
    return _split(getattr(grant, role))


# --- (a) pure Python ---------------------------------------------------------------------------------


def test_the_identities_are_the_five_this_file_knows():
    """A new role keyword is a new identity: its denials on this table must be written here first."""
    assert _role_keywords() == set(HELD) - {"stranger"}


@pytest.mark.parametrize("role", sorted(HELD))
def test_the_grant_row_gives_each_role_the_held_set_and_no_more(role):
    assert _map_gives(role) == HELD[role]


def test_the_grant_row_is_a_table_with_no_purge_column_and_no_portal_read():
    grant = mig.GRANTS[TABLE]
    assert grant.kind == "table"
    assert grant.portal is False
    assert set(grant.purge_cols) == set()  # the purge login reads no column
    assert grant.release == ""


def test_nobody_may_truncate_delete_insert_or_update_the_table_directly():
    assert {role for role in HELD if "TRUNCATE" in _map_gives(role)} == set()
    assert {role for role in HELD if "DELETE" in _map_gives(role)} == set()
    assert {role for role in HELD if _map_gives(role) & {"INSERT", "UPDATE", "SELECT"}} == set()


def _execute_got() -> dict[str, set[str]]:
    return {
        signature: {
            role
            for role in ("runtime", "portal", "purge", "reset", "release")
            if getattr(grant, role)
        }
        for signature, grant in mig.FUNCTION_GRANTS.items()
    }


def test_function_grants_key_set_is_the_one_this_file_knows():
    """A new function in `FUNCTION_GRANTS` (or one dropped) needs its holders written in `EXECUTE_HELD` first."""
    assert set(EXECUTE_HELD) == set(mig.FUNCTION_GRANTS)


def test_trigger_function_set_is_the_one_this_file_knows():
    """A new trigger function in `EXCLUDED_FUNCTIONS` needs its EXECUTE expectation written here first."""
    assert set(mig.EXCLUDED_FUNCTIONS) == TRIGGER_FUNCTIONS_OPEN_TO_PUBLIC | {
        mig.MONEY_GUARD_FUNCTION
    }


def test_function_grants_say_who_may_execute_each_function():
    """Only the purge role purges, only the runtime books, settles, expires and adds, only the release role
    releases, the reset role sets caps and compares them (with the runtime)."""
    assert _execute_got() == EXECUTE_HELD


_CREATE_RELATION = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:(?:UNLOGGED|TEMP|TEMPORARY)\s+)?(?:MATERIALIZED\s+)?"
    r"(TABLE|VIEW|SEQUENCE)\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?(\w+)\"?",
    re.IGNORECASE,
)
_BANNED = re.compile(r"SERIAL|IDENTITY|\bGRANT\b", re.IGNORECASE)


def _sql_only(text: str) -> str:
    """The SQL without `/* ... */` (also over several lines) and `-- ...` comments."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return "\n".join(line.split("--")[0] for line in text.splitlines())


def _created_relations(text: str) -> list[tuple[str, str]]:
    return [(kind.upper(), name) for kind, name in _CREATE_RELATION.findall(_sql_only(text))]


def test_the_catalog_helper_asks_for_maintain_only_from_postgresql_17():
    """MAINTAIN is a table right of PostgreSQL 17+; an older server would refuse the question itself."""
    assert "MAINTAIN" not in _table_rights_to_ask(160015)
    assert "MAINTAIN" not in _table_rights_to_ask(169999)
    assert "MAINTAIN" in _table_rights_to_ask(170000)
    assert "MAINTAIN" in _table_rights_to_ask(180001)
    for version in (160015, 170000):
        assert set(_table_rights_to_ask(version)) >= {*PRIVILEGES, "REFERENCES", "TRIGGER"}


def test_the_scan_reads_if_not_exists_and_ignores_comments():
    """Self-test of the scan on tiny strings: `IF NOT EXISTS` is not a table called IF, a commented-out CREATE or
    GRANT is not one, and a keyword shows through a comment-free line only."""
    assert _created_relations("CREATE TABLE IF NOT EXISTS x (a int);") == [("TABLE", "x")]
    assert _created_relations("create table if  not\nexists y(a int)") == [("TABLE", "y")]
    assert _created_relations("CREATE TABLE z (a int);") == [("TABLE", "z")]
    assert _created_relations("CREATE UNLOGGED TABLE u (a int); CREATE SEQUENCE s;") == [
        ("TABLE", "u"),
        ("SEQUENCE", "s"),
    ]
    assert _created_relations("/* CREATE TABLE gone (a int); */ CREATE TABLE kept (a int);") == [
        ("TABLE", "kept")
    ]
    assert _created_relations(
        "/* a\nCREATE TABLE gone2 (a int);\n*/\nCREATE VIEW v AS SELECT 1;"
    ) == [("VIEW", "v")]
    assert _created_relations("-- CREATE TABLE no (a int);\nSELECT 1;") == []
    assert _created_relations("CREATE FUNCTION f() RETURNS int AS $$ SELECT 1 $$;") == []
    assert not _BANNED.search(_sql_only("/* GRANT ALL ON t TO x; */ -- SERIAL\nSELECT 1;"))
    assert _BANNED.search(_sql_only("/* c */ GRANT SELECT ON t TO x;"))
    assert _BANNED.search(_sql_only("CREATE TABLE t (id BIGSERIAL);"))


def test_migration_0007_creates_this_one_table_and_no_sequence():
    """A second relation or a serial column in 0007 would need its own row here and in `GRANTS`."""
    sql_only = _sql_only((mig.MIGRATIONS / MIGRATION).read_text(encoding="utf-8"))
    assert _created_relations(sql_only) == [("TABLE", TABLE)]
    assert not _BANNED.search(sql_only)
    assert mig.check_grants(mig._migration_files()) == []


# every relation migrations 0007-0011 create (0008 and 0010 create none, 0009 the two stop-state tables, 0011 the
# limits and the caps). A new relation in one of these files needs a row here and in `GRANTS`.
CREATED_0007_TO_0011 = {
    ("TABLE", TABLE),
    ("TABLE", "kill_switch_resets"),
    ("TABLE", "kill_switch_watermark"),
    ("TABLE", "hadavin_limits"),
    ("TABLE", "hadavin_caps"),
}


def test_migrations_0007_to_0011_create_only_the_known_relations_and_grant_nothing():
    """The wall is built by `migrate` from `GRANTS`, never by a migration file: no GRANT, no serial column and no
    identity column in any of the files 0007-0011, and the relations they create are the known set."""
    files = [
        p for p in mig._migration_files() if p.name[:4].isdigit() and 7 <= int(p.name[:4]) <= 11
    ]
    assert sorted(p.name[:4] for p in files) == ["0007", "0008", "0009", "0010", "0011"]
    created: list[tuple[str, str]] = []
    for path in files:
        sql_only = _sql_only(path.read_text(encoding="utf-8"))
        assert not _BANNED.search(sql_only), f"{path.name}: GRANT, SERIAL or IDENTITY"
        created += _created_relations(sql_only)
    assert len(created) == len(set(created))
    assert set(created) == CREATED_0007_TO_0011


def test_the_grants_row_of_the_table_is_there():
    assert TABLE in mig.GRANTS


# --- (b) PostgreSQL ----------------------------------------------------------------------------------


def _pg_schema():
    """`pg_schema`, but with HADAVIN_REQUIRE_PG a missing DSN or driver FAILS instead of skipping."""
    if strict():
        if not os.environ.get("HADAVIN_TEST_PG_DSN"):
            pytest.fail(
                "HADAVIN_REQUIRE_PG is set but HADAVIN_TEST_PG_DSN is not: no PostgreSQL test ran"
            )
        try:
            import psycopg  # noqa: F401
        except ImportError:
            pytest.fail(
                "HADAVIN_REQUIRE_PG is set but psycopg is not installed: no PostgreSQL test ran"
            )
    yield from pg_schema()


@pytest.fixture
def _needs_the_helpers():
    if (os.environ.get("HADAVIN_TEST_PG_DSN") or strict()) and _as is None:
        pytest.fail(
            "tests/test_grants_negative_roles.py (the helpers) is missing: nothing was tested"
        )


@pytest.fixture
def identities(_needs_the_helpers):
    """(owner DSN, {role: login role name}): a migrated schema and one fresh login role per identity, the
    grants applied in ONE migrate() call, plus a `stranger` role that was never granted anything."""
    import psycopg
    from psycopg import sql

    for dsn in _pg_schema():
        names = {role: f"{role[:2]}_{uuid.uuid4().hex[:10]}" for role in HELD}
        with psycopg.connect(dsn, autocommit=True) as db:
            for name in names.values():
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
        try:
            mig.migrate(dsn, **{f"{role}_role": names[role] for role in HELD if role != "stranger"})
            yield dsn, names
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for name in names.values():
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def _seed(dsn: str) -> tuple[str, str]:
    """As the owner: one open and one settled reservation of 1.00. Returns (open id, settled id)."""
    import psycopg

    open_id, closed_id = "res-" + uuid.uuid4().hex, "res-" + uuid.uuid4().hex
    day = _db_today(dsn)
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd) VALUES (%s, 'a', %s, 1)",  # noqa: S608 - a constant table name
            (open_id, day),
        )
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "  # noqa: S608 - a constant table name
            "closed_at) VALUES (%s, 'a', %s, 1, 0.5, 'settled', clock_timestamp())",
            (closed_id, day),
        )
    return open_id, closed_id


def _all_rows(dsn: str) -> list[tuple]:
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute(
            f"SELECT reservation_id, reserved_usd, settled_usd, status FROM {TABLE} ORDER BY 1"  # noqa: S608 - a constant table name
        ).fetchall()


def _refused(db, statement, params=None) -> None:
    """The statement must be refused by the privilege check, and by nothing else."""
    import psycopg

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(statement, params)
    db.rollback()


def _probe_privileges(dsn: str, name: str, held: set[str], label: str) -> list[str]:
    """Connect AS `name`, one statement per privilege: a privilege in `held` must get past the privilege check
    (it may stop later on a constraint), every other one must be refused. Returns the refused privileges."""
    import psycopg

    schema = _schema(dsn)
    refused = []
    with _as(dsn, name) as db:
        for privilege, statement in _statements(schema, TABLE, COLUMNS[0]).items():
            if privilege in held:
                try:
                    db.execute(statement)  # may stop later on a constraint: not our subject
                except psycopg.errors.InsufficientPrivilege:
                    pytest.fail(f"{label} was refused {privilege}, which the map gives")
                except psycopg.Error:
                    pass
                finally:
                    db.rollback()
            else:
                _refused(db, statement)
                refused.append(privilege)
    return refused


@pytest.mark.parametrize("role", sorted(HELD))
def test_pg_each_role_is_refused_every_privilege_the_map_does_not_give(identities, role):
    """One real statement per privilege, connected AS the role, rolled back. Schema-qualified, so the stranger
    is refused at the schema and not by a search path that does not find the table."""
    dsn, names = identities
    _seed(dsn)
    before = _all_rows(dsn)
    refused = _probe_privileges(dsn, names[role], HELD[role], role)
    assert sorted(refused) == sorted(set(PRIVILEGES) - HELD[role])
    assert "TRUNCATE" in refused
    assert _all_rows(dsn) == before and len(before) == 2


@pytest.mark.parametrize("role", sorted(HELD))
def test_pg_column_rights_nobody_reads_or_writes_a_single_column(identities, role):
    """Per column: SELECT, UPDATE and INSERT as the role. Since step 4 no identity reads or writes any column
    of the table directly (the purge role used to read `status` and `closed_at`)."""
    from psycopg import sql

    dsn, names = identities
    _seed(dsn)
    table = sql.Identifier(_schema(dsn), TABLE)
    with _as(dsn, names[role]) as db:
        for column in COLUMNS:
            c = sql.Identifier(column)
            select = sql.SQL("SELECT {} FROM {}").format(c, table)
            _refused(db, select)
            _refused(db, sql.SQL("UPDATE {} SET {} = DEFAULT").format(table, c))
            _refused(db, sql.SQL("INSERT INTO {} ({}) VALUES (DEFAULT)").format(table, c))
        _refused(db, sql.SQL("SELECT * FROM {}").format(table))
        _refused(db, sql.SQL("SELECT status FROM {} FOR UPDATE").format(table))
        _refused(db, sql.SQL("SELECT count(*) FROM {}").format(table))
        # no role holds DELETE any more, so the lock is refused to every identity, the purge role included
        _refused(db, sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(table))


def _table_rights_to_ask(server_version_num: int) -> tuple[str, ...]:
    """Every table right the catalog is asked about. MAINTAIN (VACUUM, ANALYZE, REINDEX, CLUSTER, REFRESH, LOCK)
    exists from PostgreSQL 17 only: asking an older server is an error, so it is asked only from 170000 on."""
    rights = (*PRIVILEGES, "REFERENCES", "TRIGGER")
    return (*rights, "MAINTAIN") if server_version_num >= 170000 else rights


def _catalog_wrong(db, name: str, held: set[str], label: str) -> list[str]:
    """The catalog view of one role against the `held` set: has_table_privilege for every table right (REFERENCES
    and TRIGGER too, MAINTAIN on PostgreSQL 17+) and has_column_privilege per column. Returns the differences (empty when they agree)."""
    wrong = []
    version = int(db.execute("SHOW server_version_num").fetchone()[0])
    rights = {
        p
        for p in _table_rights_to_ask(version)
        if db.execute("SELECT has_table_privilege(%s, %s, %s)", (name, TABLE, p)).fetchone()[0]
    }
    if rights != held:
        wrong.append(f"{label} on the table: {sorted(rights)}")
    for column in COLUMNS:
        cols = {
            p
            for p in ("SELECT", "INSERT", "UPDATE", "REFERENCES")
            if db.execute(
                "SELECT has_column_privilege(%s, %s, %s, %s)", (name, TABLE, column, p)
            ).fetchone()[0]
        }
        if cols != held & {"SELECT", "INSERT", "UPDATE"}:
            wrong.append(f"{label} on column {column}: {sorted(cols)}")
    return wrong


def test_pg_columns_are_exactly_the_non_dropped_user_columns_of_the_table(identities):
    """`COLUMNS` drives every per-column probe: a column added to the table (or a dropped one) that is not written
    in it would escape them, so the set is compared with pg_attribute (no system column, no dropped column)."""
    import psycopg

    dsn, _ = identities
    with psycopg.connect(dsn, autocommit=True) as db:
        rows = db.execute(
            "SELECT attname FROM pg_attribute WHERE attrelid = %s::regclass AND attnum > 0 AND NOT attisdropped",
            (f"{_schema(dsn)}.{TABLE}",),
        ).fetchall()
    actual = [r[0] for r in rows]
    assert len(actual) == len(set(actual))
    assert set(actual) == set(COLUMNS), (
        f"columns in the table and not probed: {sorted(set(actual) - set(COLUMNS))}; "
        f"probed and not in the table: {sorted(set(COLUMNS) - set(actual))}"
    )


def test_pg_the_catalog_agrees_for_every_role_privilege_and_column(identities):
    """`has_table_privilege` and `has_column_privilege` (direct, inherited and PUBLIC grants), including
    REFERENCES and TRIGGER, which no statement above exercises."""
    import psycopg

    dsn, names = identities
    wrong = []
    with psycopg.connect(dsn, autocommit=True) as db:
        for role, name in names.items():
            wrong += _catalog_wrong(db, name, HELD[role], role)
        owner = db.execute(
            "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = %s::regclass", (TABLE,)
        ).fetchone()[0]
        assert owner not in names.values()  # none of the identities owns the table
    assert wrong == []


def test_pg_the_runtime_role_cannot_remove_a_reservation(identities):
    """It books and closes reservations; it must not be able to make one disappear (open or closed)."""
    dsn, names = identities
    open_id, closed_id = _seed(dsn)
    before = _all_rows(dsn)
    with _as(dsn, names["runtime"]) as db:
        for rid in (open_id, closed_id):
            _refused(db, f"DELETE FROM {TABLE} WHERE reservation_id = %s", (rid,))  # noqa: S608 - a constant table name
        _refused(db, f"DELETE FROM {TABLE} WHERE status <> 'open'")  # noqa: S608 - a constant table name
        _refused(db, f"TRUNCATE {TABLE}")
        _refused(db, f"DROP TABLE {TABLE}")
        _refused(db, f"ALTER TABLE {TABLE} DISABLE TRIGGER ALL")
        _refused(db, f"ALTER TABLE {TABLE} DROP CONSTRAINT spend_reservations_pkey")
    assert _all_rows(dsn) == before


def test_pg_the_purge_role_touches_the_table_only_through_its_function(identities):
    """Directly it can read nothing, return nothing, delete nothing, change or add nothing (every statement the
    old test tried is still refused, now including the DELETE that used to be its one right). Its own function
    works, so the refusals above are about rights, not the login."""
    dsn, names = identities
    open_id, closed_id = _seed(dsn)
    before = _all_rows(dsn)
    with _as(dsn, names["purge"]) as db:
        for statement in (
            f"DELETE FROM {TABLE} WHERE reserved_usd >= 0",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE reservation_id = '{closed_id}'",  # noqa: S608 - an id built here
            f"DELETE FROM {TABLE} WHERE agent_id = 'a'",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE created_at < clock_timestamp()",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE status <> 'open' AND closed_at < clock_timestamp()",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE status <> 'open' RETURNING *",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE status <> 'open' RETURNING reserved_usd",  # noqa: S608 - a constant table name
            f"UPDATE {TABLE} SET status = 'settled', settled_usd = 0, closed_at = clock_timestamp()",  # noqa: S608 - a constant table name
            f"UPDATE {TABLE} SET closed_at = NULL",  # noqa: S608 - a constant table name
            (
                f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd) "  # noqa: S608 - a constant table name
                "VALUES ('res-x', 'a', '2026-03-10', 1)"
            ),
            f"TRUNCATE {TABLE}",
            *(f"UPDATE {counter} SET usd = 0" for counter in COUNTERS),  # noqa: S608 - constant names
            *(f"SELECT usd FROM {counter}" for counter in COUNTERS),  # noqa: S608 - constant names
        ):
            _refused(db, statement)
        assert _all_rows(dsn) == before
    import psycopg
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.postgres import PostgresStore, connect

    # the cutoff is read from the DATABASE clock after the seeding (the settled row was closed at the database's
    # clock_timestamp() a moment ago), never from the Python clock: a database clock ahead of or behind this
    # process cannot change the count
    with psycopg.connect(dsn, autocommit=True) as db:
        cutoff = db.execute("SELECT clock_timestamp()").fetchone()[0]
    store = PostgresStore(connect(make_conninfo(dsn, user=names["purge"])))
    try:
        deleted = store.purge_spend_reservations(cutoff)
    finally:
        store._db.close()
    assert deleted == 1
    assert [row[0] for row in _all_rows(dsn)] == [open_id]  # the open reservation is still there


@pytest.mark.parametrize("role", ["portal", "reset", "release", "stranger"])
def test_pg_roles_with_no_grant_cannot_touch_a_reservation_or_its_counters(identities, role):
    """Real statements on real rows: no read of an amount, no closing or reopening, no removal; and no write on
    the day and month counters a reservation is booked on."""
    dsn, names = identities
    open_id, _ = _seed(dsn)
    before = _all_rows(dsn)
    schema = _schema(dsn)
    table = f"{schema}.{TABLE}"  # qualified: the stranger has no right on the schema and no search path into it
    counters = [f"{schema}.{counter}" for counter in COUNTERS]
    with _as(dsn, names[role]) as db:
        for statement in (
            f"SELECT reserved_usd, settled_usd FROM {table}",  # noqa: S608 - names built here
            f"SELECT status FROM {table}",  # noqa: S608 - names built here
            f"SELECT count(*) FROM {table}",  # noqa: S608 - names built here
            (
                f"UPDATE {table} SET status = 'settled', settled_usd = 0, closed_at = clock_timestamp() "  # noqa: S608 - an id built here
                f"WHERE reservation_id = '{open_id}'"
            ),
            f"UPDATE {table} SET reserved_usd = 0",  # noqa: S608 - names built here
            (
                f"INSERT INTO {table} (reservation_id, agent_id, day, reserved_usd) "  # noqa: S608 - names built here
                "VALUES ('res-x', 'a', '2026-03-10', 1)"
            ),
            f"DELETE FROM {table}",  # noqa: S608 - names built here
            f"DELETE FROM {table} WHERE status <> 'open'",  # noqa: S608 - names built here
            f"TRUNCATE {table}",
            *(f"UPDATE {counter} SET usd = 0" for counter in counters),  # noqa: S608 - names built here
            *(
                f"INSERT INTO {counter} VALUES ('a', '2026-03-01', 1)"  # noqa: S608 - names built here
                for counter in counters
            ),
            *(f"DELETE FROM {counter}" for counter in counters),  # noqa: S608 - names built here
        ):
            _refused(db, statement)
    assert _all_rows(dsn) == before


def test_pg_the_store_methods_are_refused_under_the_wrong_identity(identities):
    """The package's own calls, each under an identity that must not make them: the purge under the runtime
    role; reserve, settle and the sweep under the purge, the portal, the reset and the release role (a stranger cannot even open the store: the schema is closed to it)."""
    import psycopg
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.models import now
    from hadavin_sdk.store.postgres import PostgresStore, connect

    dsn, names = identities
    open_id, _ = _seed(dsn)
    before = _all_rows(dsn)
    cap = Decimal(1000)
    day = _db_today(dsn)

    def store_as(role):
        return PostgresStore(connect(make_conninfo(dsn, user=names[role])))

    runtime = store_as("runtime")
    try:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            runtime.purge_spend_reservations(now())
    finally:
        runtime._db.close()
    for role in ("purge", "portal", "reset", "release"):
        store = store_as(role)
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.reserve_spend(
                    "res-" + uuid.uuid4().hex, "a", day, Decimal(1), day_cap=cap, month_cap=cap
                )
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.settle_spend(open_id, Decimal(0), agent_id="a")
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.expire_spend_reservations(0)
            if role != "purge":
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    store.purge_spend_reservations(now())
        finally:
            store._db.close()
    assert _all_rows(dsn) == before


def _function_oid(db, schema: str, signature: str) -> int:
    row = db.execute("SELECT to_regprocedure(%s)::oid", (f"{schema}.{signature}",)).fetchone()
    assert row[0] is not None, f"{signature} does not exist in {schema}"
    return row[0]


def _execute_holders(db, schema: str, signature: str, askers: dict[str, str]) -> set[str]:
    """The askers (label -> role name or 'public') for whom has_function_privilege says EXECUTE."""
    oid = _function_oid(db, schema, signature)
    return {
        who
        for who, name in askers.items()
        if db.execute("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (name, oid)).fetchone()[0]
    }


def test_pg_execute_on_every_function_is_exactly_the_expected_set_for_every_identity(identities):
    """has_function_privilege (direct, inherited and PUBLIC grants) for every function of `FUNCTION_GRANTS` and
    every identity, the stranger and PUBLIC included, against the second copy `EXECUTE_HELD` AND the map."""
    import psycopg

    dsn, names = identities
    schema = _schema(dsn)
    askers = {**names, "PUBLIC": "public"}
    wrong = []
    with psycopg.connect(dsn, autocommit=True) as db:
        for signature, holders in EXECUTE_HELD.items():
            can = _execute_holders(db, schema, signature, askers)
            if can != holders:
                wrong.append(f"{signature}: can execute {sorted(can)}, expected {sorted(holders)}")
            if can != {
                r
                for r in ("runtime", "portal", "purge", "reset", "release")
                if getattr(mig.FUNCTION_GRANTS[signature], r)
            }:
                wrong.append(f"{signature}: differs from migrate.FUNCTION_GRANTS")
        for signature in mig.EXCLUDED_FUNCTIONS:
            # trigger functions: the trigger runs them. Only the money guard is closed to everyone (0010 REVOKEs it
            # from PUBLIC); the older guards keep the default PUBLIC EXECUTE (a trigger function cannot be called
            # directly), so each of those must show exactly PUBLIC plus every role: any other result is a change.
            can = _execute_holders(db, schema, signature, askers)
            expected = set(askers) if signature in TRIGGER_FUNCTIONS_OPEN_TO_PUBLIC else set()
            if can != expected:
                wrong.append(
                    f"{signature} (trigger function): can execute {sorted(can)}, expected {sorted(expected)}"
                )
    assert wrong == []


def test_pg_the_release_function_runs_under_the_release_role_and_is_refused_to_a_stranger(
    identities,
):
    """Positive: the release role releases one hold expired longer ago than the `min_expiry_age` limit (0011
    releases only holds older than that) and the counters fall. Negative: a stranger (and the runtime) is refused
    the same call. The age is taken from the database clock only: `clock_timestamp() - seed_age`."""
    import psycopg

    dsn, names = identities
    schema = _schema(dsn)
    rid = "res-" + uuid.uuid4().hex
    day = _db_today(dsn)
    month = day.replace(day=1)
    seed_age_s = defaults.MIN_EXPIRY_AGE_S + MARGIN_S
    with psycopg.connect(dsn, autocommit=True) as db:
        min_expiry_age = db.execute(
            "SELECT value FROM hadavin_limits WHERE name = 'min_expiry_age'"
        ).fetchone()[0]
        # the relation the seeding depends on: a change of the constant (or of what migrate writes) fails HERE, loudly,
        # and not as a release that happens not to find its hold
        assert seed_age_s > defaults.MIN_EXPIRY_AGE_S
        assert seed_age_s > min_expiry_age
        db.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', %s, 1)", (day,))
        db.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('a', %s, 1)", (month,))
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "  # noqa: S608 - a constant table name
            "closed_at) VALUES (%s, 'a', %s, 1, 1, 'expired', "
            "clock_timestamp() - make_interval(secs => %s))",
            (rid, day, seed_age_s),
        )
    call = f"SELECT reservations, released_usd, day_usd, month_usd FROM {schema}.hadavin_release_expired_spend('a', %s)"  # noqa: S608 - names built here
    for who in ("stranger", "runtime"):
        with _as(dsn, names[who]) as db:
            _refused(db, call, (day,))
    assert _all_rows(dsn) == [(rid, Decimal(1), Decimal(1), "expired")]
    with _as(dsn, names["release"]) as db:
        row = db.execute(call, (day,)).fetchone()
        db.commit()
    assert row == (1, Decimal(1), Decimal(0), Decimal(0))
    assert _all_rows(dsn) == [(rid, Decimal(1), Decimal(0), "settled")]


# --- positive controls: the harness must SEE a grant that is there ---------------------------------------


def _scratch_role(dsn: str):
    """A fresh login role with USAGE on the schema, dropped (with everything granted to it) by the caller."""
    import psycopg
    from psycopg import sql

    name = f"sc_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(_schema(dsn)), sql.Identifier(name)
            )
        )
    return name


def _drop_role(dsn: str, name: str) -> None:
    import psycopg
    from psycopg import sql

    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
        db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def test_pg_control_a_table_right_that_is_present_is_seen_by_every_checking_path(identities):
    """HELD is empty by design, so the 'role holds it' branches never run on the real roles. Here a scratch role is
    GRANTed SELECT on the table: the catalog helper, the column rights and the statement probe (the same functions
    the real tests call) must all report it as held, INSERT as still refused; after REVOKE they report none."""
    import psycopg
    from psycopg import sql

    dsn, _ = identities
    _seed(dsn)
    table = sql.Identifier(_schema(dsn), TABLE)
    name = _scratch_role(dsn)
    try:
        with psycopg.connect(dsn, autocommit=True) as db:
            assert _catalog_wrong(db, name, set(), "scratch") == []  # nothing yet
            db.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(table, sql.Identifier(name)))
            assert _catalog_wrong(db, name, {"SELECT"}, "scratch") == []  # seen as held
            assert (
                _catalog_wrong(db, name, set(), "scratch") != []
            )  # and the empty expectation now fails
            # the statement path: SELECT gets past the check, the other four are refused
            refused = _probe_privileges(dsn, name, {"SELECT"}, "scratch")
            assert sorted(refused) == sorted(set(PRIVILEGES) - {"SELECT"})
            db.execute(sql.SQL("REVOKE SELECT ON {} FROM {}").format(table, sql.Identifier(name)))
            assert _catalog_wrong(db, name, set(), "scratch") == []
            assert sorted(_probe_privileges(dsn, name, set(), "scratch")) == sorted(PRIVILEGES)
            # a single column grant is seen per column, and only there
            db.execute(
                sql.SQL("GRANT SELECT ({}) ON {} TO {}").format(
                    sql.Identifier("status"), table, sql.Identifier(name)
                )
            )
            got = db.execute(
                "SELECT has_column_privilege(%s, %s, 'status', 'SELECT'), "
                "has_column_privilege(%s, %s, 'agent_id', 'SELECT')",
                (name, TABLE, name, TABLE),
            ).fetchone()
            assert got == (True, False)
            assert _catalog_wrong(db, name, set(), "scratch") != []
    finally:
        _drop_role(dsn, name)


def test_pg_control_an_execute_grant_that_is_present_is_seen(identities):
    """The EXECUTE helper reports a scratch role granted the reserve function, and PUBLIC when it is granted to
    PUBLIC; after REVOKE it reports none."""
    import psycopg
    from psycopg import sql

    dsn, _ = identities
    schema = _schema(dsn)
    name = _scratch_role(dsn)
    signature = "hadavin_reserve_spend(text, text, date, numeric, text)"
    target = sql.SQL("{}.{}").format(sql.Identifier(schema), sql.SQL(signature))
    asker = {"scratch": name, "PUBLIC": "public"}
    try:
        with psycopg.connect(dsn, autocommit=True) as db:
            assert _execute_holders(db, schema, signature, asker) == set()
            db.execute(
                sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(target, sql.Identifier(name))
            )
            assert _execute_holders(db, schema, signature, asker) == {"scratch"}
            db.execute(
                sql.SQL("REVOKE EXECUTE ON FUNCTION {} FROM {}").format(
                    target, sql.Identifier(name)
                )
            )
            assert _execute_holders(db, schema, signature, asker) == set()
            db.execute(sql.SQL("GRANT EXECUTE ON FUNCTION {} TO PUBLIC").format(target))
            assert _execute_holders(db, schema, signature, asker) == {"scratch", "PUBLIC"}
            db.execute(sql.SQL("REVOKE EXECUTE ON FUNCTION {} FROM PUBLIC").format(target))
            assert _execute_holders(db, schema, signature, asker) == set()
    finally:
        _drop_role(dsn, name)


def test_pg_the_runtime_role_is_allowed_to_reserve_settle_and_expire_and_a_stranger_is_refused(
    identities,
):
    """Positive: the runtime role really calls the three booking functions (through the package's own store
    methods) and the rows move. Negative: a stranger is refused each of the same three calls."""
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.postgres import PostgresStore, connect

    dsn, names = identities
    schema = _schema(dsn)
    cap = Decimal(1000)
    rid = "res-" + uuid.uuid4().hex
    day = _db_today(dsn)
    store = PostgresStore(connect(make_conninfo(dsn, user=names["runtime"])))
    try:
        store.reserve_spend(rid, "a", day, Decimal(1), day_cap=cap, month_cap=cap)
        assert [row[:2] for row in _all_rows(dsn)] == [(rid, Decimal(1))]
        store.settle_spend(rid, Decimal("0.5"), agent_id="a")
        assert [row[3] for row in _all_rows(dsn)] == ["settled"]
        assert store.expire_spend_reservations(0) == 0  # allowed to call; nothing is open to expire
    finally:
        store._db.close()
    before = _all_rows(dsn)
    calls = (
        f"SELECT * FROM {schema}.hadavin_reserve_spend('res-x', 'a', %s::date, 1::numeric, 'k')",  # noqa: S608 - names built here
        f"SELECT * FROM {schema}.hadavin_settle_spend(%s, 0::numeric, 'a')",  # noqa: S608 - names built here
        f"SELECT {schema}.hadavin_expire_spend_reservations(0)",
    )
    with _as(dsn, names["stranger"]) as db:
        _refused(db, calls[0], (day,))
        _refused(db, calls[1], (rid,))
        _refused(db, calls[2])
    assert _all_rows(dsn) == before


# --- HADAVIN_REQUIRE_PG: a missing database fails the PostgreSQL tests, and without the flag they skip -----


def _pg_gated_test_names() -> set[str]:
    """By introspection: every test function of this module that takes the `identities` fixture (the only road to
    the database here). Not selected by a name pattern, so a differently named one cannot escape."""
    module = sys.modules[__name__]
    return {
        name
        for name, fn in vars(module).items()
        if name.startswith("test_")
        and inspect.isfunction(fn)
        and "identities" in inspect.signature(fn).parameters
    }


def _run_this_file_without_a_dsn(require: str | None, tmp_path) -> dict[str, str]:
    """This whole file in a child pytest with no DSN (and HADAVIN_REQUIRE_PG as given), minus the two meta tests
    (no recursion). Returns {test id: 'passed' | 'failed' | 'error' | 'skipped'} from the child's junit XML, and
    the child's text in the key ''."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("HADAVIN_TEST_PG_DSN", "HADAVIN_REQUIRE_PG")
    }
    assert "HADAVIN_GRANTS_0007_CHILD" not in os.environ, "the child ran a meta test: recursion"
    env["HADAVIN_GRANTS_0007_CHILD"] = (
        "1"  # a child that would start a child fails at once instead of forking on
    )
    if require is not None:
        env["HADAVIN_REQUIRE_PG"] = require
    report = tmp_path / "child.xml"
    me = os.path.abspath(__file__)
    done = subprocess.run(  # noqa: S603 - our own interpreter, constant arguments
        [
            sys.executable, "-m", "pytest", me, "-q", "-p", "no:cacheprovider", "-p", "no:randomly",
            "--no-header", "-rN", f"--junitxml={report}",
            "-k", "not test_with_require_pg_and_no_dsn and not test_without_require_pg_and_no_dsn",
        ],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=300, check=False,
    )  # fmt: skip
    outcomes: dict[str, str] = {"": done.stdout + done.stderr}
    for case in ET.parse(report).getroot().iter("testcase"):  # noqa: S314 - the junit file of our own child
        kinds = {child.tag for child in case}
        outcome = (
            "error" if "error" in kinds
            else "failed" if "failure" in kinds
            else "skipped" if "skipped" in kinds
            else "passed"
        )  # fmt: skip
        outcomes[case.get("name")] = outcome
    return outcomes


def _check_child(outcomes: dict[str, str], pg_outcomes: set[str]) -> None:
    pg = _pg_gated_test_names()
    assert pg, "no PostgreSQL-gated test found by introspection"
    assert {n for n in vars(sys.modules[__name__]) if n.startswith("test_pg_")} <= pg
    out = outcomes.pop("")
    seen_pg = 0
    for test_id, outcome in outcomes.items():
        base = test_id.split("[")[0]
        if base in pg:
            seen_pg += 1
            assert outcome in pg_outcomes, (
                f"{test_id} is {outcome}, expected one of {pg_outcomes}\n{out}"
            )
        else:  # the pure layer needs no database: it passes in every mode
            assert outcome == "passed", f"{test_id} (pure) is {outcome}\n{out}"
    assert {t.split("[")[0] for t in outcomes} >= pg, "a PostgreSQL test did not run in the child"
    assert seen_pg >= len(pg)


@pytest.mark.parametrize("word", ["1", "true", "YES"])
def test_with_require_pg_and_no_dsn_every_pg_test_fails_and_none_skips(word, tmp_path):
    outcomes = _run_this_file_without_a_dsn(word, tmp_path)
    assert "HADAVIN_REQUIRE_PG is set but HADAVIN_TEST_PG_DSN is not" in outcomes[""]
    # a failing fixture is counted as an error, a failing test body as a failure: either is not a skip
    _check_child(outcomes, {"failed", "error"})


@pytest.mark.parametrize("word", [None, "0", "no"])
def test_without_require_pg_and_no_dsn_every_pg_test_skips(word, tmp_path):
    outcomes = _run_this_file_without_a_dsn(word, tmp_path)
    _check_child(outcomes, {"skipped"})
