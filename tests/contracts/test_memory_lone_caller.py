"""P4d-b, B4b (c): a lone caller on a fresh `MemoryStore` finishes each reservation method (no self-deadlock on the
store's lock, also on the path that calls a lock-taking helper: the run pre-check)."""

import threading
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import Store
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
        ),  # with a run: takes the run pre-check helper's lock
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
