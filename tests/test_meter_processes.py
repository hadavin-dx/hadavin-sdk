"""P4b1-a T5: the meter across real processes, on Postgres only (spawn context, the runtime login role).
A missing database is a FAILED row, never a skip: `require_backend` fails under HADAVIN_REQUIRE_PG."""

import multiprocessing
import os
import queue
import signal
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.meter import Caps, Meter, OverBudget
from hadavin_sdk.money import SpendMicro
from hadavin_sdk.store.protocol import NotFound
from tests.contracts.kinds.store_postgres import pg_schema

AG = "agproc"
WAIT_S = 60
WORKERS, ATTEMPTS, AMOUNT = 8, 6, 50_000  # cap 1.000000 -> floor(1_000_000 / 50_000) = 20 grants
CAP = Caps(day=Decimal("1.000000"), month=None, run=None)


def open_store(dsn):
    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    return make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))


def total(store):
    return store.spend_totals(AG, datetime.now(UTC).date())[0]


@pytest.fixture
def dsn():
    yield from pg_schema(runtime=True)


def worker_race(dsn, idx, attempts_done, go_settle, out):
    try:
        meter = Meter(open_store(dsn))
        holds, refused = [], 0
        attempts_done.wait(
            WAIT_S
        )  # barrier 1: everyone starts together (the parent is not a party)
        for _ in range(ATTEMPTS):
            try:
                holds.append(meter.reserve(AG, SpendMicro(AMOUNT), CAP))
            except OverBudget:
                refused += 1
        out.put(("answered", idx, len(holds), refused))
        go_settle.wait(
            WAIT_S
        )  # barrier 2: parent has read the counter; every attempt of every worker is answered
        for h in holds:
            meter.settle(h.reservation_id, SpendMicro(AMOUNT // 2))
        out.put(("settled", idx, len(holds)))
    except BaseException as exc:  # noqa: BLE001 - the parent reads this
        out.put(("error", idx, repr(exc)))


def get(out, n):
    return [out.get(timeout=WAIT_S) for _ in range(n)]


def test_t5_1_and_t5_2_eight_processes_grant_exactly_the_cap_and_settle_half(dsn):
    ctx = multiprocessing.get_context("spawn")
    start, go_settle, out = (
        ctx.Barrier(WORKERS, timeout=WAIT_S),
        ctx.Barrier(WORKERS + 1, timeout=WAIT_S),
        ctx.Queue(),
    )
    procs = [
        ctx.Process(target=worker_race, args=(dsn, i, start, go_settle, out))
        for i in range(WORKERS)
    ]
    for p in procs:
        p.start()
    try:
        answers = get(out, WORKERS)
        assert [a for a in answers if a[0] == "error"] == []
        granted = sum(a[2] for a in answers)
        refused = sum(a[3] for a in answers)
        store = open_store(dsn)
        assert granted + refused == WORKERS * ATTEMPTS
        assert granted == 1_000_000 // AMOUNT == 20  # exactly: a meter that always refuses fails
        assert total(store) == Decimal(granted * AMOUNT).scaleb(
            -6
        )  # refused amounts are not in the counter
        go_settle.wait(WAIT_S)
        settled = get(out, WORKERS)
        assert [s for s in settled if s[0] == "error"] == []
        assert total(store) == Decimal(granted * (AMOUNT // 2)).scaleb(-6)
        assert store.list_open_reservations(agent_id=AG) == []
    finally:
        for p in procs:
            p.join(WAIT_S)
            if p.is_alive():
                p.kill()
    assert [p.exitcode for p in procs] == [0] * WORKERS


def worker_crash(dsn, out, never):
    meter = Meter(open_store(dsn))
    with meter.hold(AG, SpendMicro(AMOUNT), CAP) as h:
        out.put(h.reservation_id)
        never.wait(WAIT_S)  # killed here, inside the with block


def test_t5_3_a_killed_process_leaves_its_worst_case_booked_and_another_closes_it_with_settle_none(
    dsn,
):
    ctx = multiprocessing.get_context("spawn")
    out, never = ctx.Queue(), ctx.Event()
    p = ctx.Process(target=worker_crash, args=(dsn, out, never))
    p.start()
    try:
        rid = out.get(timeout=WAIT_S)
        os.kill(p.pid, signal.SIGKILL)
        p.join(WAIT_S)
        store = open_store(dsn)
        assert [r.reservation_id for r in store.list_open_reservations(agent_id=AG)] == [rid]
        assert total(store) == Decimal("0.050000")  # fail safe: the worst case stays booked
        s = Meter(store).settle(rid, None)  # NOT release: the call may have been sent
        assert (s.applied, s.charged) == (True, SpendMicro(AMOUNT))
        assert (
            total(store) == Decimal("0.050000") and store.list_open_reservations(agent_id=AG) == []
        )
    finally:
        if p.is_alive():
            p.kill()
    assert p.exitcode == -signal.SIGKILL


class LostAck:
    """Test-only wrapper: the reserve commits, then the process 'dies' with SystemExit. `blind` makes the
    best-effort release see NotFound (the stated late-commit window)."""

    def __init__(self, inner, blind):
        self._inner, self._blind = inner, blind

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def reserve_spend(self, *a, **k):
        self._inner.reserve_spend(*a, **k)
        raise SystemExit(7)

    def release_spend(self, rid):
        if self._blind:
            raise NotFound(rid)
        return self._inner.release_spend(rid)


def worker_lost_ack(dsn, blind, out):
    meter = Meter(LostAck(open_store(dsn), blind))
    try:
        meter.reserve(AG, SpendMicro(AMOUNT), CAP)
    except SystemExit:
        out.put("exit")
    ids = [r.reservation_id for r in open_store(dsn).list_open_reservations(agent_id=AG)]
    out.put(ids)


@pytest.mark.parametrize("blind", [False, True])
def test_t5_4_lost_acknowledgement(dsn, blind):
    ctx = multiprocessing.get_context("spawn")
    out = ctx.Queue()
    p = ctx.Process(target=worker_lost_ack, args=(dsn, blind, out))
    p.start()
    p.join(WAIT_S)
    assert p.exitcode == 0
    assert out.get(timeout=WAIT_S) == "exit"
    open_ids = out.get(timeout=WAIT_S)
    store = open_store(dsn)
    if (
        blind
    ):  # the release saw NotFound: the row ends open at the worst case; nothing is under-booked
        assert len(open_ids) == 1 and total(store) == Decimal("0.050000")
    else:  # the best-effort release closed it: the books are back to zero
        assert open_ids == [] and total(store) == 0
    rows = store.list_open_reservations(agent_id=AG)
    # another process replays the SAME reservation id: no new booking, applied=False if the row is still open
    if rows:
        row = rows[0]
        again = store.reserve_spend(
            row.reservation_id,
            AG,
            row.day,
            row.reserved_usd,
            day_cap=CAP.day,
            month_cap=None,
            run_cap=None,
        )
        assert again.applied is False and total(store) == Decimal("0.050000")


def worker_settle(dsn, rid, amount, ready, out):
    try:
        meter = Meter(open_store(dsn))
        ready.wait(WAIT_S)
        s = meter.settle(rid, SpendMicro(amount))
        out.put((s.applied, s.status, s.charged.micro))
    except BaseException as exc:  # noqa: BLE001 - the parent reads this
        out.put(("error", repr(exc)))


def test_t5_5_two_processes_settle_one_reservation_id_once(dsn):
    store = open_store(dsn)
    rid = Meter(store).reserve(AG, SpendMicro(AMOUNT), CAP).reservation_id
    ctx = multiprocessing.get_context("spawn")
    ready, out = ctx.Barrier(2, timeout=WAIT_S), ctx.Queue()
    procs = [
        ctx.Process(target=worker_settle, args=(dsn, rid, amt, ready, out))
        for amt in (10_000, 30_000)
    ]
    for p in procs:
        p.start()
    results = get(out, 2)
    for p in procs:
        p.join(WAIT_S)
    assert [r for r in results if r[0] == "error"] == []
    assert sorted(r[0] for r in results) == [False, True]
    winner = next(r for r in results if r[0] is True)
    assert all(r[1:] == winner[1:] for r in results)  # both get the same settled result
    assert total(store) == Decimal(winner[2]).scaleb(-6)  # one settle in the counter
    with pytest.raises(queue.Empty):
        out.get(timeout=0.2)
