"""The spend-connection gate: FIFO fairness, bounded wait, and the measured hot-key ceiling (never over the cap)."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from hadavin_sdk.limits import OverBudget
from hadavin_sdk.store.postgres import _FairSlots
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_core_hardening_round2 import DAY, _limits, _pg_store, clock  # noqa: F401 - fixture

D = Decimal


def test_fair_slots_are_first_in_first_out_and_hand_the_slot_straight_over():
    g = _FairSlots(1)
    assert g.acquire(0.1)
    order, started = [], []

    def waiter(i):
        started.append(i)
        assert g.acquire(5)
        order.append(i)

    def until(cond, what):  # a handshake on state, never a sleep that must be long enough
        deadline = time.monotonic() + 60
        while not cond():
            assert time.monotonic() < deadline, what
            time.sleep(0.001)

    threads = []
    for i in range(5):
        t = threading.Thread(target=waiter, args=(i,))
        t.start()
        threads.append(t)
        until(
            lambda i=i: len(g._q) > i, f"waiter {i} never queued"
        )  # arrival order is fixed: queued, then the next
    for n in range(5):
        g.release()
        until(lambda n=n: len(order) > n, f"waiter {n} was not handed the slot")
    for t in threads:
        t.join(60)
    assert order == [0, 1, 2, 3, 4]
    g.release()  # the last holder
    with pytest.raises(ValueError):
        g.release()  # more releases than slots


def test_fair_slots_time_out_without_losing_a_slot():
    g = _FairSlots(1)
    assert g.acquire(0.1)
    assert g.acquire(0.05) is False  # nobody released: the wait ends, the caller fails
    g.release()
    assert g.acquire(0.1)  # the timed-out waiter did not swallow the slot
    g.release()


def test_fair_slots_a_hammer_never_exceeds_the_capacity():
    g, inside, peak, lock = _FairSlots(3), [0], [0], threading.Lock()

    def work(_):
        if not g.acquire(5):
            return
        with lock:
            inside[0] += 1
            peak[0] = max(peak[0], inside[0])
        time.sleep(0.0005)
        with lock:
            inside[0] -= 1
        g.release()

    with ThreadPoolExecutor(32) as ex:
        list(ex.map(work, range(400)))
    assert peak[0] <= 3 and inside[0] == 0


def _burst(lim, n):
    tally, lock = {"ok": 0, "err": 0}, threading.Lock()

    def one(_):
        try:
            lim.reserve("a", D("0.001"))
            key = "ok"
        except StoreUnavailable:
            key = "err"
        with lock:
            tally[key] += 1

    with ThreadPoolExecutor(n) as ex:
        list(ex.map(one, range(n)))
    return tally["ok"], tally["err"]


def test_a_hot_key_burst_on_postgres_books_exactly_what_it_admitted(clock):  # noqa: F811
    # SAFETY only (no wall-clock admission count, which depends on the machine): 300 simultaneous callers on ONE agent
    # counter, with a long and a 50 ms wait. Every caller gets a booking or a typed fail-closed StoreUnavailable (any
    # other exception fails the test), booked == admitted x amount exactly, the cap still binds, and no permit leaks.
    for dsn in pg_schema():
        for wait in (60.0, 0.05):
            store = _pg_store(dsn, POOL_WAIT_S=wait)
            try:
                ok, err = _burst(_limits(store, daily="1000"), 300)
                assert ok + err == 300
                assert (
                    store.spend_totals("a", DAY)[0] == D("0.001") * ok
                )  # booked == admitted, exactly
                with pytest.raises(OverBudget):  # the cap still binds afterwards
                    _limits(store, daily="0.0000001").reserve("a", D("1"))
                assert (
                    store._slots._free == store.POOL_SIZE and not store._slots._q
                )  # no permit leaked
            finally:
                store.close()
                with __import__("psycopg").connect(dsn, autocommit=True) as db:
                    db.execute("DELETE FROM spend")
                    db.execute("DELETE FROM spend_month")


def test_a_driver_error_on_the_spend_path_is_a_typed_refusal_never_a_raw_error(clock):  # noqa: F811
    import psycopg

    from hadavin_sdk.store.postgres import PostgresStore

    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:

            def broken():
                raise psycopg.OperationalError("connection refused: host=db.internal user=svc")

            store._connector = broken
            store._idle = type(store._idle)()  # no pooled connection: the next borrow must connect
            with pytest.raises(StoreUnavailable) as e:
                _limits(store, daily="1").reserve("a", D("0.001"))
            assert "db.internal" not in str(e.value) and "svc" not in str(
                e.value
            )  # class name only
            assert store._slots._free == store.POOL_SIZE  # the failed borrow returned its permit
        finally:
            PostgresStore.close(store)


@pytest.mark.perf
def test_perf_a_generous_wait_admits_every_caller_of_a_150_burst(clock):  # noqa: F811
    # THROUGHPUT floor, machine-relative: with a wait far longer than the burst needs, no caller may be dropped. Run with
    # -m perf on a quiet machine; the bound is generous (120 s) and says nothing about capacity.
    for dsn in pg_schema():
        store = _pg_store(dsn, POOL_WAIT_S=120.0)
        try:
            ok, err = _burst(_limits(store, daily="1000"), 150)
            assert (ok, err) == (150, 0)
        finally:
            store.close()


def test_the_pool_settings_are_validated_and_reach_the_store():
    from hadavin_sdk.backends.table import PostgresSettings

    base = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}  # a secret NAME, not a secret
    with pytest.raises(ValueError):
        PostgresSettings(**base, spend_pool_size=0)
    with pytest.raises(ValueError):
        PostgresSettings(**base, spend_pool_wait_s=0)
    s = PostgresSettings(**base, spend_pool_size=4, spend_pool_wait_s=2)
    assert (s.spend_pool_size, s.spend_pool_wait_s) == (4, 2)


def test_build_passes_the_pool_settings_to_the_store():
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        base = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}  # a secret NAME, not a secret
        settings = PostgresSettings(**base, spend_pool_size=3, spend_pool_wait_s=1.5)
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        try:
            assert (store.POOL_SIZE, store.POOL_WAIT_S) == (3, 1.5)
        finally:
            store.close()


def _interrupting_event(before_raise):
    class Boom(BaseException):
        pass

    class Ev(threading.Event):
        def wait(self, timeout=None):
            before_raise()  # e.g. the holder releases: the slot is handed to this very waiter, then the interrupt lands
            raise Boom()

    return Boom, Ev


@pytest.mark.parametrize("handed_over", [False, True])
def test_an_interrupt_during_the_wait_loses_no_slot(monkeypatch, handed_over):
    from types import SimpleNamespace

    from hadavin_sdk.store import postgres as pg

    g = _FairSlots(1)
    boom, ev_cls = _interrupting_event(g.release if handed_over else (lambda: None))
    assert g.acquire(0.1)  # the only slot is taken
    monkeypatch.setattr(pg, "threading", SimpleNamespace(Lock=threading.Lock, Event=ev_cls))
    with pytest.raises(boom):
        g.acquire(5)  # queued, then interrupted while waiting
    monkeypatch.undo()
    assert not g._q  # no dead event is left in the queue
    if not handed_over:
        g.release()  # the holder gives the slot back: it must be usable, not handed to a dead waiter
    assert g.acquire(0.1)  # the permit is not lost
    g.release()
    with pytest.raises(ValueError):
        g.release()  # exactly one permit exists
