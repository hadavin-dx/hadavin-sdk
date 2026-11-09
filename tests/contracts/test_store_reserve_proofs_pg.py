"""P4d-b, Postgres only (review round 1 of PR 75, blocker B-2): the proofs that need two real connections or a
login with exact rights.

1. The lock order run, day, month is proved from outside: while a second login holds the LAST counter row, the
   reserving call is stopped at it, and the earlier rows are already locked by that call (a `NOWAIT` probe fails on
   them). An inverted order would leave them free. Probes on the run row use `FOR NO KEY UPDATE`, never
   `FOR UPDATE`: the reservation's foreign key holds `FOR KEY SHARE` on the run row, and `FOR UPDATE` conflicts with
   that in both orders (ticket P4d, B4(vii)).
2. `reserve_spend`, `settle_spend` and `release_spend` run on a login that can only SELECT from `kill_switch`.
3. Races on two or more real connections: the same id, the same settle, and a mixed load with no deadlock.
"""

import contextlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

import pytest

from hadavin_sdk.models import KillSwitch, Run
from hadavin_sdk.store.postgres import PostgresStore
from hadavin_sdk.store.protocol import SpendOutcome, StoreBusy
from tests.contracts.kinds.store_postgres import pg_driver, pg_schema
from tests.contracts.store_support import utc_today

drv = pg_driver(module_level=True)
D = Decimal
AGENT = "ag-proof"


@pytest.fixture
def dsn():
    yield from pg_schema(runtime=True)


@pytest.fixture
def make(dsn):
    opened = []

    def build(**kw):
        conn = drv.connect_runtime(dsn)
        opened.append(conn)
        # N7: every race row uses the longest timeouts, so a slow runner cannot turn a wait into StoreBusy
        return PostgresStore(conn, lock_timeout_ms=60000, call_budget_ms=60000, **kw)

    yield build
    for conn in opened:
        conn.close()


@pytest.fixture
def admin(dsn):
    with drv.connect_admin(dsn, autocommit=False) as conn:
        yield conn


def _run(store):
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def _reserve(store, rid, amount="1", *, run=None, day=None):
    return store.reserve_spend(
        rid,
        AGENT,
        day or utc_today(store),
        D(amount),
        day_cap=None,
        month_cap=None,
        run_id=run.run_id if run else None,
        run_cap=None,
    )


# --- 1. the lock order, from outside ------------------------------------------------------------------------------


def _month_of(day: date) -> date:
    return day.replace(day=1)


def _wait_until_blocked(dsn, needle, seconds=15):
    """Poll `pg_stat_activity` until a backend waits on a lock in a statement that contains `needle`. The poll
    uses its own autocommit login: inside a transaction the activity view is a snapshot that never changes."""
    end = time.monotonic() + seconds
    with drv.connect_admin(dsn, autocommit=True) as poll:
        while time.monotonic() < end:
            rows = drv.execute(
                poll,
                "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
                "AND state = 'active' AND query ILIKE %s",
                (f"%{needle}%",),
            )
            if rows[0][0] >= 1:
                return True
            time.sleep(0.05)
    return False


def _probe_fails(dsn, statement, params):
    """A third login asks for the row with NOWAIT; True when the row is locked (55P03)."""
    with drv.connect_admin(dsn, autocommit=True) as probe:
        try:
            drv.execute(probe, statement, params)
        except Exception as exc:
            if drv.sqlstate(exc) == "55P03":
                return True
            raise
        return False


def _locks_held_at_the_month_counter(dsn, make, admin, call, *, run, day):
    """Hold the month counter row, start `call` on a store, wait until the call is stopped at that row, and report
    whether the run row and the day counter row are already locked by the stopped call."""
    store = make()
    drv.execute(
        admin,
        "SELECT 1 FROM spend_month WHERE agent_id = %s AND month = %s FOR NO KEY UPDATE",
        (AGENT, _month_of(day)),
    )
    result = {}
    thread = threading.Thread(target=lambda: result.update(out=call(store)), daemon=True)
    thread.start()
    blocked = _wait_until_blocked(dsn, "spend_month")
    locked = {}
    if blocked:
        locked["day"] = _probe_fails(
            dsn,
            "SELECT 1 FROM spend WHERE agent_id = %s AND day = %s FOR NO KEY UPDATE NOWAIT",
            (AGENT, day),
        )
        if run is not None:
            locked["run"] = _probe_fails(
                dsn,
                "SELECT 1 FROM runs WHERE run_id = %s FOR NO KEY UPDATE NOWAIT",
                (run.run_id,),
            )
    admin.rollback()  # let the stopped call go on
    thread.join(30)
    assert not thread.is_alive()
    return blocked, locked, result.get("out")


def _prepared(make, dsn):
    """A run, an open reservation with a run, and the counter rows (made by the reservation)."""
    store = make()
    day = utc_today(store)
    run = _run(store)
    _reserve(store, "res-open", "2", run=run, day=day)
    return store, run, day


def test_reserve_locks_run_then_day_before_it_waits_for_the_month_counter(dsn, make, admin):
    _, run, day = _prepared(make, dsn)
    blocked, locked, out = _locks_held_at_the_month_counter(
        dsn,
        make,
        admin,
        lambda s: _reserve(s, "res-second", "1", run=run, day=day),
        run=run,
        day=day,
    )
    assert blocked, "the call never waited on the month counter row"
    assert locked == {"day": True, "run": True}
    assert isinstance(out, SpendOutcome) and out.applied is True


@pytest.mark.parametrize("closer", ["settle", "release"])
def test_settle_and_release_lock_run_then_day_before_they_wait_for_the_month_counter(
    dsn, make, admin, closer
):
    _, run, day = _prepared(make, dsn)
    call = (
        (lambda s: s.settle_spend("res-open", D("0.5")))
        if closer == "settle"
        else (lambda s: s.release_spend("res-open"))
    )
    blocked, locked, out = _locks_held_at_the_month_counter(
        dsn, make, admin, call, run=run, day=day
    )
    assert blocked, "the call never waited on the month counter row"
    assert locked == {"day": True, "run": True}
    assert out.applied is True


def test_the_probe_can_tell_an_inverted_order_apart(dsn, make, admin):
    """The probe itself: a call that has NOT yet touched the run row leaves it free. Here the holder keeps the DAY
    row, so the call stops at the day counter (after the run row, in the right order): the run row is locked and
    the month row is free. A call written month-first would show the opposite."""
    _, run, day = _prepared(make, dsn)
    store = make()
    drv.execute(
        admin,
        "SELECT 1 FROM spend WHERE agent_id = %s AND day = %s FOR NO KEY UPDATE",
        (AGENT, day),
    )
    thread = threading.Thread(
        target=lambda: _reserve(store, "res-third", "1", run=run, day=day), daemon=True
    )
    thread.start()
    assert _wait_until_blocked(dsn, "UPDATE spend SET")
    run_locked = _probe_fails(
        dsn, "SELECT 1 FROM runs WHERE run_id = %s FOR NO KEY UPDATE NOWAIT", (run.run_id,)
    )
    month_locked = _probe_fails(
        dsn,
        "SELECT 1 FROM spend_month WHERE agent_id = %s AND month = %s FOR NO KEY UPDATE NOWAIT",
        (AGENT, _month_of(day)),
    )
    admin.rollback()
    thread.join(30)
    assert (run_locked, month_locked) == (True, False)


# --- 2. a login that can only SELECT from kill_switch -------------------------------------------------------------


RIGHTS = [
    ("SELECT", "kill_switch"),
    ("SELECT", "runs"),
    ("UPDATE", "runs"),
    ("SELECT", "spend"),
    ("INSERT", "spend"),
    ("UPDATE", "spend"),
    ("SELECT", "spend_month"),
    ("INSERT", "spend_month"),
    ("UPDATE", "spend_month"),
    ("SELECT", "spend_reservations"),
    ("INSERT", "spend_reservations"),
    ("UPDATE", "spend_reservations"),
]


def test_reserve_settle_and_release_work_on_a_login_with_select_only_on_the_kill_switch(dsn):
    with drv.connect_role(dsn, grants=RIGHTS) as conn:
        who = drv.execute(
            conn, "SELECT current_user, rolsuper FROM pg_roles WHERE rolname = current_user"
        )
        assert who[0][1] is False
        with pytest.raises(
            Exception
        ) as caught:  # the premise: this login cannot write the kill switch
            drv.execute(conn, 'UPDATE kill_switch SET "on" = "on"')
        assert drv.sqlstate(caught.value) == "42501"
        store = PostgresStore(conn)
        day = utc_today(store)
        out = store.reserve_spend(
            "res-ro", AGENT, day, D(1), day_cap=D(5), month_cap=D(5), run_cap=None
        )
        assert out.applied is True
        assert store.settle_spend("res-ro", D("0.25")).applied is True
        store.reserve_spend("res-ro2", AGENT, day, D(1), day_cap=D(5), month_cap=D(5), run_cap=None)
        assert store.release_spend("res-ro2").applied is True
        assert store.spend_totals(AGENT, day) == (D("0.25"), D("0.25"))


def test_the_kill_switch_read_takes_no_row_lock(dsn, make, admin):
    """The read is a plain SELECT: a login that holds the kill switch row with FOR UPDATE does not stop it."""
    store = make()
    drv.execute(admin, "SELECT 1 FROM kill_switch WHERE id = 1 FOR UPDATE")
    result = {}
    thread = threading.Thread(target=lambda: result.update(ks=store.get_kill_switch()), daemon=True)
    thread.start()
    thread.join(10)
    admin.rollback()
    assert not thread.is_alive() and result["ks"].on is False


# --- 3. races on real connections ---------------------------------------------------------------------------------


def _deadlocks(admin):
    admin.rollback()
    return drv.execute(
        admin, "SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()"
    )[0][0]


def _in_parallel(jobs):
    """Run each callable on its own thread, all released together; returns their results in order and raises the
    first error a job raised (so a failed job fails the test with its own error)."""
    start = threading.Barrier(len(jobs))

    def wrapped(job):
        start.wait()
        return job()

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(wrapped, job) for job in jobs]
        return [f.result(timeout=120) for f in futures]


def test_eight_stores_reserving_the_same_id_book_it_once(dsn, make):
    base = make()
    day = utc_today(base)
    run = _run(base)
    stores = [make() for _ in range(8)]
    results = _in_parallel(
        [lambda s=s: _reserve(s, "same-id", "1.5", run=run, day=day) for s in stores]
    )
    assert sorted(r.applied for r in results) == [False] * 7 + [True]
    assert base.spend_totals(AGENT, day) == (D("1.5"), D("1.5"))
    assert base.get_run(run.run_id).cost_usd == D("1.5")


def test_eight_stores_settling_the_same_reservation_with_different_amounts_book_one_of_them(
    dsn, make
):
    base = make()
    day = utc_today(base)
    run = _run(base)
    _reserve(base, "settle-race", "1", run=run, day=day)
    stores = [make() for _ in range(8)]
    amounts = [D(f"0.{n}") for n in range(1, 9)]
    outcomes = _in_parallel(
        [
            lambda s=s, a=a: s.settle_spend("settle-race", a)
            for s, a in zip(stores, amounts, strict=True)
        ]
    )
    winners = [(a, o) for a, o in zip(amounts, outcomes, strict=True) if o.applied]
    assert len(winners) == 1
    won = winners[0][0]
    assert {o.reservation.settled_usd for o in outcomes} == {
        won
    }  # every caller sees the first result
    assert base.spend_totals(AGENT, day) == (won, won)
    assert base.get_run(run.run_id).cost_usd == won


def test_a_mixed_load_on_shared_counters_has_no_deadlock_and_ends_exact(dsn, make, admin):
    base = make()
    day = utc_today(base)
    run = _run(base)
    before = _deadlocks(admin)
    workers, per_worker = 8, 12
    stores = [make() for _ in range(workers)]

    def work(n, store):
        for i in range(per_worker):
            rid = f"mix-{n}-{i}"
            _reserve(store, rid, "1", run=run, day=day)
            if i % 3 == 0:
                store.release_spend(rid)
            elif i % 3 == 1:
                store.settle_spend(rid, D("0.5"))

    _in_parallel([lambda n=n, s=s: work(n, s) for n, s in enumerate(stores)])
    settled = workers * 4  # i % 3 == 1 for i in 0..11
    still_open = workers * 4  # i % 3 == 2
    want = D("0.5") * settled + D(1) * still_open  # the released ones (i % 3 == 0) are back to zero
    assert base.spend_totals(AGENT, day) == (want, want)
    assert base.get_run(run.run_id).cost_usd == want
    assert len(base.list_open_reservations(AGENT, limit=1000)) == still_open
    assert _deadlocks(admin) == before


def test_a_held_counter_row_makes_a_reserve_store_busy_and_books_nothing(dsn, admin):
    conn = drv.connect_runtime(dsn)
    try:
        store = PostgresStore(conn, lock_timeout_ms=100, call_budget_ms=2000)
        day = utc_today(store)
        _reserve(store, "seed", "1", day=day)
        drv.execute(
            admin,
            "SELECT 1 FROM spend WHERE agent_id = %s AND day = %s FOR NO KEY UPDATE",
            (AGENT, day),
        )
        with pytest.raises(StoreBusy):
            _reserve(store, "res-busy", "1", day=day)
        admin.rollback()
        assert store.spend_totals(AGENT, day) == (D(1), D(1))
        assert store.list_open_reservations(AGENT) != []
        with contextlib.suppress(Exception):
            store.get_spend_reservation("res-busy")
    finally:
        conn.close()


def test_the_kill_switch_stops_a_reserve_on_real_connections(dsn, make):
    store = make()
    store.set_kill_switch(KillSwitch(on=True, by="user:test"))
    from hadavin_sdk.store.protocol import KillSwitchOn

    with pytest.raises(KillSwitchOn):
        _reserve(store, "res-ks")
