"""T1, PostgreSQL only: the spend cap under 50 separate connections (interface (i) version 2.1, README section 1,
invariant "atomic reserve under N separate connections (exactly floor(cap / amount) succeed)", and README section 3).

Needs HADAVIN_TEST_PG_DSN (the convention of tests/contracts/kinds/store_postgres.py: a fresh migrated schema and
fresh roles per test, dropped afterwards). Written before the code exists: while `PostgresStore` has no
`reserve_spend`, every test is skipped with the reason in `NOT_LANDED`. Once the method exists the only skip left is
the unset variable; with the variable set nothing here skips, except the one test that names a role fixture this
repository does not have yet.

Assumptions (also in handover/core-a/requests/003-interface-i-questions.md):
- A1. `SpendCapExceeded` is looked up at run time in `hadavin_sdk.store.protocol`, then `hadavin_sdk.models`.
- A2. The reservation sits on the counters `spend_totals` reads.
- A7. One `PostgresStore` per connection is built as the package does it: `PostgresStore(connect(dsn))`, logged in as
  the runtime role of `pg_schema(runtime=True)`.
- A8. The table is named `spend_reservations` and its grants are the README's: runtime SELECT, INSERT, UPDATE; purge
  DELETE plus SELECT on status and closed_at; the portal role none. The portal role is made here through the public
  `migrate(..., portal_role=...)`, because the postgres kind has no fixture for it.
"""

import importlib
import os
import threading
import uuid
from datetime import date
from decimal import Decimal

import pytest

NOT_LANDED = "core-b step F not landed: Store.reserve_spend missing"
try:
    from hadavin_sdk.store.postgres import PostgresStore, connect
except ModuleNotFoundError:  # the pg extra is not installed: nothing to detect
    PostgresStore = connect = None
LANDED = hasattr(PostgresStore, "reserve_spend")  # detected once
pytestmark = pytest.mark.skipif(not LANDED, reason=NOT_LANDED)

_HOMES = ("hadavin_sdk.store.protocol", "hadavin_sdk.models")
THREADS = 50
DAY = date(2026, 3, 10)
CAP, WORST, WIDE = Decimal("3.00"), Decimal("1.00"), Decimal(1000)
TABLE = "spend_reservations"


def _cap_error():
    for home in _HOMES:
        found = getattr(importlib.import_module(home), "SpendCapExceeded", None)
        if found is not None:
            return found
    pytest.fail(f"reserve_spend exists but SpendCapExceeded is in none of {_HOMES}")


def _rid():
    return "res-" + uuid.uuid4().hex


@pytest.fixture
def runtime_dsn():
    from tests.contracts.kinds.store_postgres import pg_schema

    yield from pg_schema(runtime=True)


@pytest.fixture
def stores(runtime_dsn):
    """50 PostgresStore objects, each on its own connection, all logged in as the runtime role."""
    built = []
    try:
        for _ in range(THREADS):
            built.append(PostgresStore(connect(runtime_dsn)))
        yield built
    finally:
        for s in built:
            s._db.close()


def _in_threads(stores, work):
    """Run `work(store)` once per store, one thread each, released together. Returns (results, errors) in store
    order; every thread also reports the backend pid of its own connection."""
    gate = threading.Barrier(len(stores))
    results, errors, pids = [None] * len(stores), [None] * len(stores), [None] * len(stores)

    def go(i):
        store = stores[i]
        try:
            pids[i] = store._db.execute("SELECT pg_backend_pid()").fetchone()[0]
            gate.wait(timeout=60)
            results[i] = work(store)
        except Exception as exc:  # noqa: BLE001 - sorted by the caller: a cap refusal or a failure
            errors[i] = exc

    threads = [threading.Thread(target=go, args=(i,)) for i in range(len(stores))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results, errors, pids


def test_fifty_stores_are_fifty_backends(stores):
    """The premise of the cap test: 50 distinct pg_backend_pid() values, so no two threads share a connection."""
    _, errors, pids = _in_threads(stores, lambda store: None)
    assert not [e for e in errors if e is not None]
    assert len(stores) == THREADS
    assert len(set(pids)) == THREADS and None not in pids


@pytest.mark.parametrize("which", ["day", "month"])
def test_fifty_connections_against_a_cap_of_three_grant_exactly_three(stores, runtime_dsn, which):
    """Cap 3.00, worst case 1.00, 50 connections at once: exactly 3 granted, 47 SpendCapExceeded, counters at 3.00."""
    cap_error = _cap_error()
    caps = {"day_cap": CAP, "month_cap": WIDE} if which == "day" else {"day_cap": WIDE, "month_cap": CAP}
    ids = {id(s): _rid() for s in stores}

    def reserve(store):
        store.reserve_spend(ids[id(store)], "a", DAY, WORST, **caps)
        return ids[id(store)]

    results, errors, pids = _in_threads(stores, reserve)
    granted = [r for r in results if r is not None]
    refused = [e for e in errors if isinstance(e, cap_error)]
    unexpected = [e for e in errors if e is not None and not isinstance(e, cap_error)]
    assert not unexpected
    assert len(set(pids)) == THREADS
    assert (len(granted), len(refused)) == (3, THREADS - 3)
    assert {e.which for e in refused} == {which}
    reader = PostgresStore(connect(runtime_dsn))  # a 51st connection reads what was committed
    try:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        rows = reader._db.execute(
            "SELECT reservation_id, reserved_usd, status FROM spend_reservations ORDER BY 1"
        ).fetchall()
        assert [(r[0], Decimal(r[1]), r[2]) for r in rows] == [
            (rid, WORST, "open") for rid in sorted(granted)
        ]
        with pytest.raises(cap_error):  # and the cap is still shut afterwards
            reader.reserve_spend(_rid(), "a", DAY, WORST, **caps)
        for rid in granted:
            _, applied = reader.settle_spend(rid, WORST)
            assert applied is True
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
    finally:
        reader._db.close()


def test_control_the_old_check_then_add_pattern_admits_more_than_three(stores, runtime_dsn):
    """CONTROL: why the reservation is needed. The pattern it replaces reads the counter, compares with the cap and
    then calls `add_spend`: two statements with nothing holding the row between them. Here the 50 connections all do
    the read, meet at a barrier, and then all do the add. The barrier does not invent a schedule: it pins the one the
    database allows whenever 50 callers read before the first of them writes, so the result is the same on every run
    (all 50 admitted, 50.00 booked against a cap of 3.00). If a thread ever read a counter at the cap it would return
    without waiting and the barrier would time out as an error, so the assertion below cannot pass by accident."""
    between = threading.Barrier(len(stores))

    def check_then_add(store):
        day_total, _ = store.spend_totals("a", DAY)
        if day_total + WORST > CAP:
            return False
        between.wait(timeout=60)
        store.add_spend("a", DAY, WORST)
        return True

    results, errors, pids = _in_threads(stores, check_then_add)
    assert not [e for e in errors if e is not None]
    assert len(set(pids)) == THREADS
    admitted = sum(1 for r in results if r)
    assert admitted > 3
    reader = PostgresStore(connect(runtime_dsn))
    try:
        day_total, month_total = reader.spend_totals("a", DAY)
    finally:
        reader._db.close()
    assert day_total == month_total == WORST * admitted
    assert day_total > CAP


# --- per-role negative tests: the README's grants on spend_reservations ----------------------------------------


def _as(dsn):
    import psycopg

    return psycopg.connect(dsn, autocommit=True)


def test_the_runtime_role_may_not_delete_reservations(runtime_dsn):
    """Grants: runtime SELECT, INSERT, UPDATE. No DELETE, no TRUNCATE; the purge method fails for it too."""
    import psycopg

    store = PostgresStore(connect(runtime_dsn))
    try:
        rid = _rid()
        store.reserve_spend(rid, "a", DAY, WORST, day_cap=CAP, month_cap=CAP)
        store.settle_spend(rid, WORST)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            store.purge_spend_reservations(_far_future())
    finally:
        store._db.close()
    with _as(runtime_dsn) as db:
        assert db.execute("SELECT count(*) FROM spend_reservations").fetchone()[0] == 1
        for statement in ("DELETE FROM spend_reservations", "TRUNCATE spend_reservations"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
        assert db.execute("SELECT count(*) FROM spend_reservations").fetchone()[0] == 1


def test_the_purge_role_deletes_closed_rows_and_reads_only_status_and_closed_at(runtime_dsn):
    """Grants: purge DELETE plus SELECT on status and closed_at; nothing else on the table."""
    import psycopg

    from tests.contracts.kinds.store_postgres import PURGE_DSN

    purge_dsn = PURGE_DSN[runtime_dsn]
    runtime = PostgresStore(connect(runtime_dsn))
    purge = PostgresStore(connect(purge_dsn))
    try:
        closed, kept = _rid(), _rid()
        for rid in (closed, kept):
            runtime.reserve_spend(rid, "a", DAY, WORST, day_cap=CAP, month_cap=CAP)
        runtime.settle_spend(closed, WORST)
        assert purge.purge_spend_reservations(_far_future()) == 1
        _, applied = runtime.settle_spend(kept, WORST)  # the open row was not deleted
        assert applied is True
    finally:
        runtime._db.close()
        purge._db.close()
    with _as(purge_dsn) as db:
        db.execute("SELECT status, closed_at FROM spend_reservations").fetchall()
        for statement in (
            "SELECT reserved_usd FROM spend_reservations",
            "SELECT * FROM spend_reservations",
            "UPDATE spend_reservations SET status = 'open'",
            "INSERT INTO spend_reservations (reservation_id) VALUES ('res-x')",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


def test_the_portal_role_may_not_read_reservations():
    """Grants: portal none. The role is created here and given its rights by `migrate(portal_role=...)`, as the
    package does for a deployment; a relation it may read (`runs`) shows the login itself works."""
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate
    from tests.contracts.kinds.store_postgres import pg_schema

    for owner_dsn in pg_schema():
        portal = "pt_" + uuid.uuid4().hex[:12]
        base = os.environ["HADAVIN_TEST_PG_DSN"]
        with psycopg.connect(base, autocommit=True) as db:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(portal)))
        try:
            migrate(owner_dsn, portal_role=portal)
            with _as(owner_dsn) as db:  # the table exists, so the refusal below is about rights
                assert db.execute("SELECT count(*) FROM spend_reservations").fetchone()[0] == 0
            with _as(make_conninfo(owner_dsn, user=portal)) as db:
                assert db.execute("SELECT current_user").fetchone()[0] == portal
                db.execute("SELECT count(*) FROM runs").fetchone()
                for statement in (
                    "SELECT * FROM spend_reservations",
                    "SELECT status FROM spend_reservations",
                    "DELETE FROM spend_reservations",
                    "UPDATE spend_reservations SET status = 'open'",
                ):
                    with pytest.raises(psycopg.errors.InsufficientPrivilege):
                        db.execute(statement)
        finally:
            with psycopg.connect(base, autocommit=True) as db:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(portal)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(portal)))


def test_the_reset_role_may_not_read_reservations():
    """Grants: reset none. `migrate` knows three roles today (runtime, portal, purge) and the postgres kind builds two
    (runtime, purge): there is no reset role to log in as. The statements are written; the role is the missing part."""
    import inspect

    import psycopg

    from hadavin_sdk.store.migrate import migrate

    if "reset_role" not in inspect.signature(migrate).parameters:
        pytest.skip(
            "missing fixture: no reset role (migrate has no reset_role parameter and "
            "tests/contracts/kinds/store_postgres.pg_schema builds runtime and purge only); request 003"
        )
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from tests.contracts.kinds.store_postgres import pg_schema

    for owner_dsn in pg_schema():
        reset = "rs_" + uuid.uuid4().hex[:12]
        base = os.environ["HADAVIN_TEST_PG_DSN"]
        with psycopg.connect(base, autocommit=True) as db:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(reset)))
        try:
            migrate(owner_dsn, reset_role=reset)
            with _as(make_conninfo(owner_dsn, user=reset)) as db:
                assert db.execute("SELECT current_user").fetchone()[0] == reset
                for statement in (
                    "SELECT * FROM spend_reservations",
                    "DELETE FROM spend_reservations",
                ):
                    with pytest.raises(psycopg.errors.InsufficientPrivilege):
                        db.execute(statement)
        finally:
            with psycopg.connect(base, autocommit=True) as db:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(reset)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(reset)))


def _far_future():
    from datetime import timedelta

    from hadavin_sdk.models import now

    return now() + timedelta(days=1)
