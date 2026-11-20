"""Negative tests for the grants of migration 0007 (`spend_reservations`): what each database identity must NOT
be able to do with a reservation row.

Written by a test-writer that did not build the code under test (session core-c; the builder of the store, of
migration 0007 and of its `GRANTS` row is session core-b, commit 8db9c29). Style and helpers of
tests/test_grants_negative_roles.py (imported, not copied). Two layers:

(a) Pure Python, no database: the `GRANTS` row of the table compared with a hand-written second copy (`HELD`,
    from the interface README: "runtime SELECT, INSERT, UPDATE; purge DELETE plus SELECT on status and closed_at;
    portal and reset none"), and the migration file read for what it creates.
(b) PostgreSQL: a migrated schema, one fresh login role per identity (runtime, portal, purge, reset) plus a
    `stranger` that was never granted anything. Each role connects as itself and runs one statement per
    privilege: a cell `HELD` does not give must raise `psycopg.errors.InsufficientPrivilege`, a cell it gives
    must get past the privilege check. Then the column rights, the catalog, and statements on real rows.
    Needs HADAVIN_TEST_PG_DSN and is skipped without it, like the other database tests (`pg_schema`).

Skipped as a whole, with the reason, in a tree where migration 0007 does not exist yet. Where it exists and the
helper module is missing, the tests FAIL (they do not skip and the file still collects).
"""

from __future__ import annotations

import inspect
import os
import re
import uuid
from datetime import date
from decimal import Decimal

import pytest

from hadavin_sdk.store import migrate as mig
from tests.contracts.kinds.store_postgres import pg_schema

try:  # the helpers of the per-role file: a connection AS a role, the schema name, one statement per privilege
    from tests.test_grants_negative_roles import PRIVILEGES, _as, _schema, _statements
except ImportError:  # reported by `_needs_the_helpers`, so this file still collects
    PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
    _as = _schema = _statements = None

TABLE = "spend_reservations"
MIGRATION = "0007_spend_reservations.sql"
pytestmark = pytest.mark.skipif(
    TABLE not in mig.GRANTS,
    reason=f"migration 0007 not in this tree: no {TABLE} row in migrate.GRANTS",
)

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
# The reviewed second copy, written by hand from the interface README (version 2.1, section 1, "Grants").
HELD: dict[str, set[str]] = {
    "runtime": {"SELECT", "INSERT", "UPDATE"},
    "portal": set(),
    "purge": {"DELETE"},
    "reset": set(),
    "stranger": set(),
}
PURGE_READS = {"status", "closed_at"}  # the two columns the purge role's DELETE ... WHERE needs
COUNTERS = ("spend", "spend_month")  # what a reservation is booked on
DAY = date(2026, 3, 10)


def _split(privileges: str) -> set[str]:
    return {p.strip() for p in privileges.split(",") if p.strip()}


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


def test_the_identities_are_the_four_this_file_knows():
    """A new role keyword is a new identity: its denials on this table must be written here first."""
    assert _role_keywords() == set(HELD) - {"stranger"}


@pytest.mark.parametrize("role", sorted(HELD))
def test_the_grant_row_gives_each_role_what_the_interface_states_and_no_more(role):
    assert _map_gives(role) == HELD[role]


def test_the_grant_row_is_a_table_with_two_purge_columns_and_no_portal_read():
    grant = mig.GRANTS[TABLE]
    assert grant.kind == "table"
    assert grant.portal is False
    assert set(grant.purge_cols) == PURGE_READS
    assert PURGE_READS < set(COLUMNS)


def test_nobody_may_truncate_and_only_the_purge_role_may_delete():
    assert {role for role in HELD if "TRUNCATE" in _map_gives(role)} == set()
    assert {role for role in HELD if "DELETE" in _map_gives(role)} == {"purge"}
    assert {role for role in HELD if _map_gives(role) & {"INSERT", "UPDATE"}} == {"runtime"}


def test_migration_0007_creates_this_one_table_and_no_sequence():
    """A second relation or a serial column in 0007 would need its own row here and in `GRANTS`."""
    text = (mig.MIGRATIONS / MIGRATION).read_text(encoding="utf-8")
    sql_only = "\n".join(line.split("--")[0] for line in text.splitlines())
    created = re.findall(r"CREATE\s+(TABLE|VIEW|SEQUENCE)\s+(\w+)", sql_only, re.IGNORECASE)
    assert [(kind.upper(), name) for kind, name in created] == [("TABLE", TABLE)]
    assert not re.search(r"SERIAL|IDENTITY|\bGRANT\b", sql_only, re.IGNORECASE)
    assert mig.check_grants(mig._migration_files()) == []


# --- (b) PostgreSQL ----------------------------------------------------------------------------------


@pytest.fixture
def _needs_the_helpers():
    if os.environ.get("HADAVIN_TEST_PG_DSN") and _as is None:
        pytest.fail(
            "tests/test_grants_negative_roles.py (the helpers) is missing: nothing was tested"
        )


@pytest.fixture
def identities(_needs_the_helpers):
    """(owner DSN, {role: login role name}): a migrated schema and one fresh login role per identity, the
    grants applied in ONE migrate() call, plus a `stranger` role that was never granted anything."""
    import psycopg
    from psycopg import sql

    for dsn in pg_schema():
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
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd) VALUES (%s, 'a', %s, 1)",  # noqa: S608 - a constant table name
            (open_id, DAY),
        )
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "  # noqa: S608 - a constant table name
            "closed_at) VALUES (%s, 'a', %s, 1, 0.5, 'settled', clock_timestamp())",
            (closed_id, DAY),
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


@pytest.mark.parametrize("role", sorted(HELD))
def test_pg_each_role_is_refused_every_privilege_the_map_does_not_give(identities, role):
    """One real statement per privilege, connected AS the role, rolled back. Schema-qualified, so the stranger
    is refused at the schema and not by a search path that does not find the table."""
    import psycopg

    dsn, names = identities
    _seed(dsn)
    before = _all_rows(dsn)
    schema = _schema(dsn)
    refused = []
    with _as(dsn, names[role]) as db:
        for privilege, statement in _statements(schema, TABLE, COLUMNS[0]).items():
            if privilege in HELD[role]:
                try:
                    db.execute(statement)  # may stop later on a constraint: not our subject
                except psycopg.errors.InsufficientPrivilege:
                    pytest.fail(f"{role} was refused {privilege}, which the map gives")
                except psycopg.Error:
                    pass
                finally:
                    db.rollback()
            else:
                _refused(db, statement)
                refused.append(privilege)
    assert sorted(refused) == sorted(set(PRIVILEGES) - HELD[role])
    assert "TRUNCATE" in refused
    assert _all_rows(dsn) == before and len(before) == 2


@pytest.mark.parametrize("role", ["portal", "purge", "reset", "stranger"])
def test_pg_column_rights_only_the_purge_role_reads_and_only_two_columns(identities, role):
    """Per column: SELECT, UPDATE and INSERT as the role. The purge role reads `status` and `closed_at` and
    nothing else; nobody but the runtime role writes a single column."""
    from psycopg import sql

    dsn, names = identities
    _seed(dsn)
    table = sql.Identifier(_schema(dsn), TABLE)
    reads = PURGE_READS if role == "purge" else set()
    with _as(dsn, names[role]) as db:
        for column in COLUMNS:
            c = sql.Identifier(column)
            select = sql.SQL("SELECT {} FROM {}").format(c, table)
            if column in reads:
                assert len(db.execute(select).fetchall()) == 2
                db.rollback()
            else:
                _refused(db, select)
            _refused(db, sql.SQL("UPDATE {} SET {} = DEFAULT").format(table, c))
            _refused(db, sql.SQL("INSERT INTO {} ({}) VALUES (DEFAULT)").format(table, c))
        _refused(db, sql.SQL("SELECT * FROM {}").format(table))
        _refused(db, sql.SQL("SELECT status FROM {} FOR UPDATE").format(table))
        if not reads:
            _refused(db, sql.SQL("SELECT count(*) FROM {}").format(table))
            # PostgreSQL lets a role that holds DELETE take this lock, so the purge role is not in this line
            _refused(db, sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(table))


def test_pg_the_catalog_agrees_for_every_role_privilege_and_column(identities):
    """`has_table_privilege` and `has_column_privilege` (direct, inherited and PUBLIC grants), including
    REFERENCES and TRIGGER, which no statement above exercises."""
    import psycopg

    dsn, names = identities
    wrong = []
    with psycopg.connect(dsn, autocommit=True) as db:
        for role, name in names.items():
            held = {
                p
                for p in (*PRIVILEGES, "REFERENCES", "TRIGGER")
                if db.execute(
                    "SELECT has_table_privilege(%s, %s, %s)", (name, TABLE, p)
                ).fetchone()[0]
            }
            if held != HELD[role]:
                wrong.append(f"{role} on the table: {sorted(held)}")
            for column in COLUMNS:
                cols = {
                    p
                    for p in ("SELECT", "INSERT", "UPDATE", "REFERENCES")
                    if db.execute(
                        "SELECT has_column_privilege(%s, %s, %s, %s)", (name, TABLE, column, p)
                    ).fetchone()[0]
                }
                expected = HELD[role] & {"SELECT", "INSERT", "UPDATE"}
                if role == "purge" and column in PURGE_READS:
                    expected = {"SELECT"}
                if cols != expected:
                    wrong.append(f"{role} on column {column}: {sorted(cols)}")
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


def test_pg_the_purge_role_deletes_by_status_and_date_and_can_do_nothing_else(identities):
    """It cannot read an amount, an agent or a run, cannot return a deleted row, cannot change or add one. Its
    own statement (status and closed_at only) works, so the refusals above are about rights, not the login."""
    dsn, names = identities
    open_id, closed_id = _seed(dsn)
    before = _all_rows(dsn)
    with _as(dsn, names["purge"]) as db:
        for statement in (
            f"DELETE FROM {TABLE} WHERE reserved_usd >= 0",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE reservation_id = '{closed_id}'",  # noqa: S608 - an id built here
            f"DELETE FROM {TABLE} WHERE agent_id = 'a'",  # noqa: S608 - a constant table name
            f"DELETE FROM {TABLE} WHERE created_at < clock_timestamp()",  # noqa: S608 - a constant table name
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
        deleted = db.execute(
            f"DELETE FROM {TABLE} WHERE status <> 'open' AND closed_at < clock_timestamp()"  # noqa: S608 - a constant table name
        ).rowcount
        db.commit()
    assert deleted == 1
    assert [row[0] for row in _all_rows(dsn)] == [open_id]  # the open reservation is still there


@pytest.mark.parametrize("role", ["portal", "reset", "stranger"])
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
    role; reserve, settle and the sweep under the purge, the portal and the reset role."""
    import psycopg
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.models import now
    from hadavin_sdk.store.postgres import PostgresStore, connect

    dsn, names = identities
    open_id, _ = _seed(dsn)
    before = _all_rows(dsn)
    cap = Decimal(1000)

    def store_as(role):
        return PostgresStore(connect(make_conninfo(dsn, user=names[role])))

    runtime = store_as("runtime")
    try:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            runtime.purge_spend_reservations(now())
    finally:
        runtime._db.close()
    for role in ("purge", "portal", "reset"):
        store = store_as(role)
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.reserve_spend(
                    "res-" + uuid.uuid4().hex, "a", DAY, Decimal(1), day_cap=cap, month_cap=cap
                )
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.settle_spend(open_id, Decimal(0))
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                store.expire_spend_reservations(0)
            if role != "purge":
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    store.purge_spend_reservations(now())
        finally:
            store._db.close()
    assert _all_rows(dsn) == before
