"""T1, PostgreSQL only: the spend cap under 50 separate connections (interface (i) version 2.1, README section 1,
invariant "atomic reserve under N separate connections (exactly floor(cap / amount) succeed)", and README section 3).

Two test writers, neither built the store (builder: session core-b, commit 8db9c29):
- First version, session core-a (written before the code existed): the 50 backends premise, the cap of three per
  counter, the control with the old check-then-add pattern, the four role tests.
- Extended by session core-c, run against core-b's pushed code (everything below the line "core-c additions"):
  caps that are not a multiple of the amount and a cap in cents; two agents on the same 50 connections; a month cap
  reached over two days; the 51st connection reads the granted sum BEFORE any settle and the refusals leave no row;
  settle (first of 50 wins, above the reserve books the actual amount, below it frees room for exactly that many
  new reservations); expiry (counters stay, the cap stays shut, a later settle only moves the counters upward,
  50 sweeps expire each row once, settle racing the sweep).

Needs HADAVIN_TEST_PG_DSN (the convention of tests/contracts/kinds/store_postgres.py: a fresh migrated schema and
fresh roles per test, dropped afterwards). Skips:
- the store protocol has no `reserve_spend` (a tree without step F): every test, with the reason in `NOT_LANDED`;
- the variable is not set: every test, with the reason of `pg_schema`.
With the methods there AND the variable set nothing here skips: a missing `psycopg` is then a failure
(`_no_silent_skip`), not a skip.

Assumptions (core-a's, from handover/core-a/requests/003-interface-i-questions.md; each is true on core-b 8db9c29):
- A1. `SpendCapExceeded` is looked up at run time in `hadavin_sdk.store.protocol`, then `hadavin_sdk.models`.
- A2. The reservation sits on the counters `spend_totals` reads.
- A7. One `PostgresStore` per connection is built as the package does it: `PostgresStore(connect(dsn))`, logged in as
  the runtime role of `pg_schema(runtime=True)`.
- A8. The table is named `spend_reservations` and its grants are the README's: runtime SELECT, INSERT, UPDATE; purge
  DELETE plus SELECT on status and closed_at; the portal role none. The portal role is made here through the public
  `migrate(..., portal_role=...)`, because the postgres kind has no fixture for it.
Not asserted, because the interface does not say it: the `status` word of an expired row after its settle.
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
from hadavin_sdk.store.protocol import Store

# Detected once, on the protocol: it needs no psycopg, so a missing driver cannot look like "not landed".
LANDED = hasattr(Store, "reserve_spend")
pytestmark = pytest.mark.skipif(not LANDED, reason=NOT_LANDED)

_HOMES = ("hadavin_sdk.store.protocol", "hadavin_sdk.models")
THREADS = 50
DAY = date(2026, 3, 10)
CAP, WORST, WIDE = Decimal("3.00"), Decimal("1.00"), Decimal(1000)


def _cap_error():
    for home in _HOMES:
        found = getattr(importlib.import_module(home), "SpendCapExceeded", None)
        if found is not None:
            return found
    pytest.fail(f"reserve_spend exists but SpendCapExceeded is in none of {_HOMES}")


def _rid():
    return "res-" + uuid.uuid4().hex


@pytest.fixture(autouse=True)
def _no_silent_skip():
    """The variable is set and the methods exist: this file must run. `pg_schema` would skip without the driver."""
    if os.environ.get("HADAVIN_TEST_PG_DSN") and connect is None:
        pytest.fail(
            "HADAVIN_TEST_PG_DSN is set but psycopg (the pg extra) is not installed: T1 did not run"
        )


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
    caps = (
        {"day_cap": CAP, "month_cap": WIDE}
        if which == "day"
        else {"day_cap": WIDE, "month_cap": CAP}
    )
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


# === core-c additions (session core-c, 2026-11-20; run against core-b 8db9c29) ==================================


class _Reader:
    """One more connection (the 51st), logged in as the runtime role; closed on exit."""

    def __init__(self, dsn):
        self.store = PostgresStore(connect(dsn))

    def __enter__(self):
        return self.store

    def __exit__(self, *exc):
        self.store._db.close()


def _split(errors, cap_error):
    """(cap refusals, anything else that was raised)."""
    refused = [e for e in errors if isinstance(e, cap_error)]
    return refused, [e for e in errors if e is not None and not isinstance(e, cap_error)]


def _rows(store):
    """Every reservation row as the runtime role sees it: {id: (reserved, settled, status, closed_at is set)}."""
    found = store._db.execute(
        "SELECT reservation_id, reserved_usd, settled_usd, status, closed_at FROM spend_reservations"
    ).fetchall()
    return {
        r[0]: (Decimal(r[1]), None if r[2] is None else Decimal(r[2]), r[3], r[4] is not None)
        for r in found
    }


def _reserve_all(stores, *, agent="a", day=DAY, usd=WORST, day_cap=CAP, month_cap=CAP):
    """Every store reserves once at the same moment. Returns (granted ids, errors, pids)."""
    ids = {id(s): _rid() for s in stores}

    def reserve(store):
        store.reserve_spend(ids[id(store)], agent, day, usd, day_cap=day_cap, month_cap=month_cap)
        return ids[id(store)]

    results, errors, pids = _in_threads(stores, reserve)
    return [r for r in results if r is not None], errors, pids


def _three_open(stores, runtime_dsn):
    """The starting point of the settle and expiry cases: 50 at once, 3 granted, read back from a 51st."""
    cap_error = _cap_error()
    granted, errors, pids = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert len(set(pids)) == THREADS
    assert (len(granted), len(refused)) == (3, THREADS - 3)
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
    return sorted(granted)


def test_the_fifty_first_connection_reads_the_granted_sum_before_any_settle(stores, runtime_dsn):
    """50 reserve at once; BEFORE any settle a connection that took no part reads the committed state: the day and
    the month counter are the sum of the granted reservations (3.00, not 50.00 and not 0), there is one open row per
    granted id and none for a refused one, and the reader's backend is a 51st pid."""
    cap_error = _cap_error()
    granted, errors, pids = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert (len(granted), len(refused)) == (3, 47)
    with _Reader(runtime_dsn) as reader:
        reader_pid = reader._db.execute("SELECT pg_backend_pid()").fetchone()[0]
        assert reader_pid not in pids and len({*pids, reader_pid}) == THREADS + 1
        rows = _rows(reader)
        assert rows == {rid: (WORST, None, "open", False) for rid in granted}
        granted_sum = sum(reserved for reserved, _, _, _ in rows.values())
        assert granted_sum == WORST * 3 == Decimal("3.00")
        assert reader.spend_totals("a", DAY) == (granted_sum, granted_sum)
        counters = reader._db.execute(
            "SELECT (SELECT count(*) FROM spend), (SELECT count(*) FROM spend_month)"
        ).fetchone()
        assert tuple(counters) == (1, 1)  # one day row, one month row: nothing else was booked


@pytest.mark.parametrize(
    ("cap", "worst", "expected"),
    [
        (Decimal("3.50"), Decimal("1.00"), 3),  # floor: the last 0.50 is not enough for a fourth
        (
            Decimal("0.07"),
            Decimal("0.01"),
            7,
        ),  # cents: nothing is rounded, the cap is reached exactly
        (Decimal("1.00"), Decimal("0.30"), 3),  # 0.90 booked, 0.10 left
        (Decimal("0.99"), Decimal("1.00"), 0),  # the cap is below one call: nobody is granted
        (Decimal("50.00"), Decimal("1.00"), 50),  # the cap fits all 50: nobody is refused
    ],
)
def test_exactly_floor_of_cap_over_worst_are_granted(stores, runtime_dsn, cap, worst, expected):
    """README invariant: "exactly floor(cap / amount) succeed", for caps that are not a multiple of the amount."""
    cap_error = _cap_error()
    assert expected == int(cap // worst)
    granted, errors, pids = _reserve_all(stores, usd=worst, day_cap=cap, month_cap=cap)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert len(set(pids)) == THREADS
    assert (len(granted), len(refused)) == (expected, THREADS - expected)
    assert {e.which for e in refused} <= {"day"}  # both caps are equal: the day is checked first
    with _Reader(runtime_dsn) as reader:
        total = worst * expected
        assert reader.spend_totals("a", DAY) == (total, total)
        assert total <= cap
        assert _rows(reader) == {rid: (worst, None, "open", False) for rid in granted}


def test_two_agents_on_the_same_fifty_connections_each_get_their_own_cap(stores, runtime_dsn):
    """25 connections reserve for one agent and 25 for another, all at once: 3 granted for each, never 6 for one."""
    cap_error = _cap_error()
    agent_of = {id(s): ("a" if i % 2 == 0 else "b") for i, s in enumerate(stores)}
    ids = {id(s): _rid() for s in stores}

    def reserve(store):
        store.reserve_spend(
            ids[id(store)], agent_of[id(store)], DAY, WORST, day_cap=CAP, month_cap=CAP
        )
        return agent_of[id(store)]

    results, errors, pids = _in_threads(stores, reserve)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert len(set(pids)) == THREADS
    assert sorted(r for r in results if r is not None) == ["a", "a", "a", "b", "b", "b"]
    assert len(refused) == THREADS - 6
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        assert reader.spend_totals("b", DAY) == (CAP, CAP)
        assert reader.spend_totals("c", DAY) == (Decimal(0), Decimal(0))


def test_a_month_cap_is_reached_by_fifty_connections_spread_over_two_days(stores, runtime_dsn):
    """Two day rows, one month row: 25 connections book day one and 25 day two of the same month. The month cap of
    3.00 grants exactly 3 in total, and a refused day booking is rolled back with its reservation row."""
    cap_error = _cap_error()
    other_day = date(2026, 3, 11)
    day_of = {id(s): (DAY if i % 2 == 0 else other_day) for i, s in enumerate(stores)}
    ids = {id(s): _rid() for s in stores}

    def reserve(store):
        store.reserve_spend(
            ids[id(store)], "a", day_of[id(store)], WORST, day_cap=WIDE, month_cap=CAP
        )
        return day_of[id(store)]

    results, errors, pids = _in_threads(stores, reserve)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert len(set(pids)) == THREADS
    days = [r for r in results if r is not None]
    assert (len(days), len(refused)) == (3, THREADS - 3)
    assert {e.which for e in refused} == {"month"}
    with _Reader(runtime_dsn) as reader:
        first, month = reader.spend_totals("a", DAY)
        second, month_again = reader.spend_totals("a", other_day)
        assert month == month_again == CAP
        assert first == WORST * days.count(DAY) and second == WORST * days.count(other_day)
        assert first + second == CAP  # no day counter kept a booking the month cap refused
        assert len(_rows(reader)) == 3


# --- settle -----------------------------------------------------------------------------------------------------


def test_fifty_connections_settle_one_reservation_and_the_first_wins(stores, runtime_dsn):
    """README: "first call closes the row ... later calls return the stored row with False and change nothing".
    50 connections settle the SAME reservation at once, each with its own amount: one is applied, all 50 get the
    same stored row, and the counters moved once, by the winner's amount."""
    with _Reader(runtime_dsn) as reader:
        rid = _rid()
        reader.reserve_spend(rid, "a", DAY, WORST, day_cap=CAP, month_cap=CAP)
        assert reader.spend_totals("a", DAY) == (WORST, WORST)
    amount_of = {
        id(s): Decimal(i + 1) / 100 for i, s in enumerate(stores)
    }  # 0.01 ... 0.50, all distinct

    def settle(store):
        row, applied = store.settle_spend(rid, amount_of[id(store)])
        return row, applied, amount_of[id(store)]

    results, errors, pids = _in_threads(stores, settle)
    assert not [e for e in errors if e is not None]
    assert len(set(pids)) == THREADS
    winners = [(row, amount) for row, applied, amount in results if applied is True]
    assert len(winners) == 1
    assert [applied for _, applied, _ in results].count(False) == THREADS - 1
    won_row, won_amount = winners[0]
    assert won_row.settled_usd == won_amount
    assert won_row.reserved_usd == WORST and won_row.closed_at is not None
    assert {row.model_dump_json() for row, _, _ in results} == {won_row.model_dump_json()}
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (won_amount, won_amount)
        assert _rows(reader) == {rid: (WORST, won_amount, "settled", True)}
        again, applied = reader.settle_spend(
            rid, Decimal("2.00")
        )  # a 51st, later, with a higher amount
        assert applied is False and again.settled_usd == won_amount
        assert reader.spend_totals("a", DAY) == (won_amount, won_amount)


def test_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap(stores, runtime_dsn):
    """README: "overshoot booked in full". The cap is full with three open reservations; one of them settles at
    2.50: the counters read 4.50 (above the cap of 3.00), nothing is clipped, and the cap stays shut for all 50."""
    cap_error = _cap_error()
    granted = _three_open(stores, runtime_dsn)
    with _Reader(runtime_dsn) as reader:
        row, applied = reader.settle_spend(granted[0], Decimal("2.50"))
        assert applied is True
        assert (row.reserved_usd, row.settled_usd) == (WORST, Decimal("2.50"))
        assert reader.spend_totals("a", DAY) == (Decimal("4.50"), Decimal("4.50"))
    more, errors, _ = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert (more, len(refused)) == ([], THREADS)
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (Decimal("4.50"), Decimal("4.50"))
        assert len(_rows(reader)) == 3  # the 50 refusals left no row


def test_settles_below_the_reserve_free_room_for_exactly_that_many_new_reservations(
    stores, runtime_dsn
):
    """Three reservations of 1.00 settle at 0.25, 0.25 and 0.50: 1.00 is booked, 2.00 is free. 50 connections
    reserve again at once: exactly 2 are granted, and the counters end at the cap."""
    cap_error = _cap_error()
    granted = _three_open(stores, runtime_dsn)
    with _Reader(runtime_dsn) as reader:
        for rid, actual in zip(granted, ("0.25", "0.25", "0.50"), strict=True):
            row, applied = reader.settle_spend(rid, Decimal(actual))
            assert applied is True and row.settled_usd == Decimal(actual)
        assert reader.spend_totals("a", DAY) == (Decimal("1.00"), Decimal("1.00"))
    more, errors, pids = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert len(set(pids)) == THREADS
    assert (len(more), len(refused)) == (2, THREADS - 2)
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        rows = _rows(reader)
        assert len(rows) == 5
        assert sorted(rid for rid, row in rows.items() if row[2] == "open") == sorted(more)


def test_a_settle_at_zero_gives_the_whole_reservation_back(stores, runtime_dsn):
    """Contract point 3 of the meter: a call that cost nothing settles at 0. All three settle at 0: the counters
    read 0 and the next 50 get exactly 3 again."""
    cap_error = _cap_error()
    granted = _three_open(stores, runtime_dsn)
    with _Reader(runtime_dsn) as reader:
        for rid in granted:
            assert reader.settle_spend(rid, Decimal(0))[1] is True
        assert reader.spend_totals("a", DAY) == (Decimal(0), Decimal(0))
    more, errors, _ = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert (len(more), len(refused)) == (3, THREADS - 3)
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)


# --- expiry -----------------------------------------------------------------------------------------------------


def test_expired_reservations_stay_booked_and_keep_the_cap_shut(stores, runtime_dsn):
    """README: "A reservation nobody closed ... is marked expired by a sweep and stays booked at the full amount"
    and "open rows older than that (database clock) become expired; counters do not move"."""
    cap_error = _cap_error()
    granted = _three_open(stores, runtime_dsn)
    with _Reader(runtime_dsn) as reader:
        assert reader.expire_spend_reservations(3600) == 0  # younger than an hour: not touched
        assert _rows(reader) == {rid: (WORST, None, "open", False) for rid in granted}
        assert reader.expire_spend_reservations(0) == 3
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        rows = _rows(reader)
        assert sorted(rows) == granted
        assert {(reserved, status, closed) for reserved, _, status, closed in rows.values()} == {
            (WORST, "expired", True)
        }
        assert reader.expire_spend_reservations(0) == 0  # an expired row is not expired twice
    more, errors, _ = _reserve_all(stores)
    refused, unexpected = _split(errors, cap_error)
    assert not unexpected
    assert (more, len(refused)) == ([], THREADS)
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        assert len(_rows(reader)) == 3


def test_fifty_sweeps_at_once_expire_each_reservation_once(stores, runtime_dsn):
    """50 connections run the sweep at the same moment over three open rows: the counts they return add up to 3."""
    granted = _three_open(stores, runtime_dsn)
    results, errors, pids = _in_threads(stores, lambda store: store.expire_spend_reservations(0))
    assert not [e for e in errors if e is not None]
    assert len(set(pids)) == THREADS
    assert sum(results) == 3
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        assert {row[2] for row in _rows(reader).values()} == {"expired"}
        assert sorted(_rows(reader)) == granted


def test_a_settle_after_expiry_never_lowers_the_counters(stores, runtime_dsn):
    """README: "an expired row is always claimed by its first settle and its counters only move upward".
    Of three expired reservations of 1.00: one settles at 0.25 (claimed, the counters stay), one at 1.75 (claimed,
    the counters rise by 0.75), one is left alone. A second settle of either changes nothing."""
    cap_error = _cap_error()
    low, high, untouched = _three_open(stores, runtime_dsn)
    with _Reader(runtime_dsn) as reader:
        assert reader.expire_spend_reservations(0) == 3
        row, applied = reader.settle_spend(low, Decimal("0.25"))
        assert applied is True  # claimed by its first settle
        assert row.reserved_usd == WORST and row.closed_at is not None
        assert row.settled_usd == WORST  # what stays booked: not the lower actual amount
        assert reader.spend_totals("a", DAY) == (CAP, CAP)
        row, applied = reader.settle_spend(high, Decimal("1.75"))
        assert applied is True
        assert row.settled_usd == Decimal("1.75")
        assert reader.spend_totals("a", DAY) == (Decimal("3.75"), Decimal("3.75"))
        for rid, later, stored in (
            (low, Decimal("5.00"), WORST),
            (high, Decimal(0), Decimal("1.75")),
        ):
            again, applied = reader.settle_spend(rid, later)
            assert applied is False and again.settled_usd == stored
        assert reader.spend_totals("a", DAY) == (Decimal("3.75"), Decimal("3.75"))
        assert _rows(reader)[untouched] == (WORST, WORST, "expired", True)
        assert reader.expire_spend_reservations(0) == 0  # the two claimed rows are closed, not open
        with pytest.raises(cap_error):
            reader.reserve_spend(_rid(), "a", DAY, WORST, day_cap=CAP, month_cap=CAP)


def test_settle_racing_the_sweep_ends_in_one_of_the_two_stated_results(stores, runtime_dsn):
    """25 connections settle one open reservation at 0.25 while 25 run the sweep, all at once. Whatever the order,
    one settle is applied and the counters equal what the row says is booked: 0.25 when the settle came first,
    the full 1.00 when the sweep came first (an expired row never goes down)."""
    with _Reader(runtime_dsn) as reader:
        rid = _rid()
        reader.reserve_spend(rid, "a", DAY, WORST, day_cap=CAP, month_cap=CAP)
    sweeps = {id(s) for s in stores[1::2]}
    actual = Decimal("0.25")

    def work(store):
        if id(store) in sweeps:
            return ("sweep", store.expire_spend_reservations(0))
        row, applied = store.settle_spend(rid, actual)
        return ("settle", (row, applied))

    results, errors, pids = _in_threads(stores, work)
    assert not [e for e in errors if e is not None]
    assert len(set(pids)) == THREADS
    expired = sum(value for kind, value in results if kind == "sweep")
    settles = [value for kind, value in results if kind == "settle"]
    assert len(settles) == THREADS // 2
    assert [applied for _, applied in settles].count(True) == 1
    assert expired in (0, 1)
    booked = WORST if expired else actual
    assert {row.settled_usd for row, _ in settles} == {booked}
    with _Reader(runtime_dsn) as reader:
        assert reader.spend_totals("a", DAY) == (booked, booked)
        assert _rows(reader)[rid][:2] == (WORST, booked)
        assert reader.expire_spend_reservations(0) == 0
