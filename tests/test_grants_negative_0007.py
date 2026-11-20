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
# Columns of the table the purge login may read: none since step 4 (it only runs the purge function).
PURGE_READS: set[str] = set()
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


def test_the_identities_are_the_five_this_file_knows():
    """A new role keyword is a new identity: its denials on this table must be written here first."""
    assert _role_keywords() == set(HELD) - {"stranger"}


@pytest.mark.parametrize("role", sorted(HELD))
def test_the_grant_row_gives_each_role_what_the_interface_states_and_no_more(role):
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


def test_function_grants_say_who_may_execute_each_function():
    """Only the purge role purges, only the runtime books, settles, expires and adds, only the release role
    releases, the reset role sets caps and compares them (with the runtime)."""
    assert _execute_got() == EXECUTE_HELD


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
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.models import now
    from hadavin_sdk.store.postgres import PostgresStore, connect

    store = PostgresStore(connect(make_conninfo(dsn, user=names["purge"])))
    try:
        deleted = store.purge_spend_reservations(now())
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
                    "res-" + uuid.uuid4().hex, "a", DAY, Decimal(1), day_cap=cap, month_cap=cap
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
            oid = _function_oid(db, schema, signature)
            can = {
                who
                for who, name in askers.items()
                if db.execute(
                    "SELECT has_function_privilege(%s, %s, 'EXECUTE')", (name, oid)
                ).fetchone()[0]
            }
            if can != holders:
                wrong.append(f"{signature}: can execute {sorted(can)}, expected {sorted(holders)}")
            if can != {
                r
                for r in ("runtime", "portal", "purge", "reset", "release")
                if getattr(mig.FUNCTION_GRANTS[signature], r)
            }:
                wrong.append(f"{signature}: differs from migrate.FUNCTION_GRANTS")
    assert wrong == []


def test_pg_the_release_function_runs_under_the_release_role_and_is_refused_to_a_stranger(
    identities,
):
    """Positive: the release role releases one hold expired a day ago (0011 releases only holds older than the
    min_expiry_age limit) and the counters fall. Negative: a stranger (and the
    runtime) is refused the same call."""
    import psycopg

    dsn, names = identities
    schema = _schema(dsn)
    rid = "res-" + uuid.uuid4().hex
    month = DAY.replace(day=1)
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', %s, 1)", (DAY,))
        db.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('a', %s, 1)", (month,))
        db.execute(
            f"INSERT INTO {TABLE} (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "  # noqa: S608 - a constant table name
            "closed_at) VALUES (%s, 'a', %s, 1, 1, 'expired', clock_timestamp() - interval '1 day')",
            (rid, DAY),
        )
    call = f"SELECT reservations, released_usd, day_usd, month_usd FROM {schema}.hadavin_release_expired_spend('a', %s)"  # noqa: S608 - names built here
    for who in ("stranger", "runtime"):
        with _as(dsn, names[who]) as db:
            _refused(db, call, (DAY,))
    assert _all_rows(dsn) == [(rid, Decimal(1), Decimal(1), "expired")]
    with _as(dsn, names["release"]) as db:
        row = db.execute(call, (DAY,)).fetchone()
        db.commit()
    assert row == (1, Decimal(1), Decimal(0), Decimal(0))
    assert _all_rows(dsn) == [(rid, Decimal(1), Decimal(0), "settled")]
