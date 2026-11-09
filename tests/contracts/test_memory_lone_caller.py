"""P4d-b, B4b (c): a lone caller on a fresh `MemoryStore` finishes each reservation method. The store's lock is a
plain lock (ticket N9): no method may call a lock-taking method while holding it, so any future nesting shows here as
a hang. Today `reserve_spend` reads the run row and the kill switch (`_kill_on`) through helpers that do not lock."""

import threading
from decimal import Decimal

import pytest

from hadavin_sdk.models import KillSwitch, Run
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import KillSwitchOn, Store
from tests.contracts.store_support import utc_today

D = Decimal
METHODS = ["reserve_spend", "settle_spend", "release_spend", "sweep_spend_reservations"]
SIX = {*METHODS, "get_spend_reservation", "list_open_reservations"}


def test_the_list_of_methods_matches_the_protocol():
    in_protocol = {
        n
        for n, v in vars(Store).items()
        if callable(v)
        and ("reservation" in n or n in {"reserve_spend", "settle_spend", "release_spend"})
    }
    assert in_protocol == SIX  # a seventh reservation method must be added to the lone-caller rows


def _reserve(store, run):
    return store.reserve_spend(
        "lone-1",
        "ag",
        utc_today(store),
        D(1),
        day_cap=None,
        month_cap=None,
        run_id=run.run_id,
        run_cap=None,
    )


@pytest.mark.parametrize("method", METHODS)
def test_a_lone_caller_finishes_every_reservation_method(method):
    store = MemoryStore()  # fresh per row: a hang cannot poison a later row
    run = Run(agent_id="ag", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    calls = {
        "reserve_spend": lambda: _reserve(
            store, run
        ),  # with a run: reads the run row under the held lock
        "settle_spend": lambda: (_reserve(store, run), store.settle_spend("lone-1", D("0.5"))),
        "release_spend": lambda: (_reserve(store, run), store.release_spend("lone-1")),
        "sweep_spend_reservations": lambda: store.sweep_spend_reservations(60),
    }
    done = threading.Event()

    def target():
        calls[method]()
        done.set()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=10)
    assert done.is_set(), f"{method} did not finish within 10 s for a lone caller"


def test_reserve_and_get_kill_switch_read_the_switch_through_the_one_helper(monkeypatch):
    """Both reads go through `MemoryStore._kill_on`: replacing it moves both (a second, direct read of `_kill`
    would leave one of them behind)."""
    store = MemoryStore()
    monkeypatch.setattr(MemoryStore, "_kill_on", lambda self: KillSwitch(on=True, by="user:test"))
    assert store.get_kill_switch().on is True
    with pytest.raises(KillSwitchOn):
        store.reserve_spend(
            "ks-1", "ag", utc_today(store), D(1), day_cap=None, month_cap=None, run_cap=None
        )


def test_a_failure_while_building_the_row_leaves_no_counter_moved(monkeypatch):
    """The reservation row is built before any counter changes: if building it fails, nothing is half-booked."""
    store = MemoryStore()
    run = Run(agent_id="ag", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)

    def boom(**kwargs):
        raise RuntimeError("row could not be built")

    monkeypatch.setattr("hadavin_sdk.store.memory.SpendReservation", boom)
    with pytest.raises(RuntimeError):
        _reserve(store, run)
    assert store.spend_totals("ag", utc_today(store)) == (0, 0)
    assert store.get_run(run.run_id).cost_usd == 0
