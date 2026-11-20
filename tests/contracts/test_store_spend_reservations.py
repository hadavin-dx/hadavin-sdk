"""Store suite, spend reservations: interface (i) version 2.1 as published by core-b (README section 1 and
i_store_spend.py), over every registered store kind. Written before the code exists: while `MemoryStore` has no
`reserve_spend`, every test here is skipped with the reason in `NOT_LANDED`; the minute step F lands they run.

Each test names the README section 1 table row it covers (S1.reserve, S1.settle, S1.expire, S1.purge) and quotes the
invariant phrase. The README says the invariants are numbered 1 to 12 in the F-store ticket but lists ten phrases, and
the ticket was not among this session's inputs, so the phrases are quoted and no number is invented.

Assumptions (also in handover/core-a/requests/003-interface-i-questions.md):
- A1. `SpendCapExceeded` is looked up at run time in `hadavin_sdk.store.protocol`, then `hadavin_sdk.models` (the
  interface file says "added to Store in protocol.py and to models.py" without saying which name goes where). When
  the methods exist and the name is in neither module, the test FAILS; it never skips.
- A2. The booking is visible through the existing `spend_totals` (the reservation sits on the same day and month
  counters as `add_spend`), and an amount already there counts towards the cap.
- A3. There is no read method for a reservation: a row is observed only through what `settle_spend` returns.
- A4. On a store that splits its identities (the postgres kind: runtime and purge role), the purge runs through the
  purge identity, found as the `_purge` attribute of the kind's wrapper.
- A5. `expire_spend_reservations(0)` expires every open row created before the call (after a short sleep).
- A6. Reserve does not touch the run's cost; only settle adds to it.
Not asserted because the interface does not say (questions in request 003): whether purge deletes an expired row that
was never settled; the status of an expired row after its settle; bad caps; an int amount; a run id with no run row.
"""

import importlib
import random
import threading
import time
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run, now
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound, StaleState

NOT_LANDED = "core-b step F not landed: Store.reserve_spend missing"
LANDED = hasattr(MemoryStore, "reserve_spend")  # detected once, on the in-package reference store
pytestmark = pytest.mark.skipif(not LANDED, reason=NOT_LANDED)

_HOMES = ("hadavin_sdk.store.protocol", "hadavin_sdk.models")
D1, D2 = date(2026, 3, 10), date(2026, 3, 11)  # two days of one month, both in the past
OTHER_MONTH = date(2026, 4, 2)
WIDE = Decimal(1000)  # a cap that is never reached


def _usd(text):
    return Decimal(text)


def _cap_error():
    """Assumption A1: the error type by name, from the modules the interface names."""
    for home in _HOMES:
        found = getattr(importlib.import_module(home), "SpendCapExceeded", None)
        if found is not None:
            return found
    pytest.fail(f"reserve_spend exists but SpendCapExceeded is in none of {_HOMES}")


def _rid():
    return "res-" + uuid.uuid4().hex


def _run(store, agent="a"):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run.run_id


def _reserve(store, usd, *, agent="a", day=D1, day_cap=WIDE, month_cap=WIDE, run_id=None, rid=None):
    rid = rid or _rid()
    store.reserve_spend(rid, agent, day, usd, day_cap=day_cap, month_cap=month_cap, run_id=run_id)
    return rid


def _expire_all(store):
    time.sleep(0.05)  # "older than": the row must be strictly older than the store's clock reading
    return store.expire_spend_reservations(0)


def _purge(store, before):
    """Assumption A4."""
    split = getattr(store, "_purge", None)
    target = split if hasattr(split, "purge_spend_reservations") else store
    return target.purge_spend_reservations(before)


HOSTILE = [
    pytest.param(Decimal("-0.01"), id="negative"),
    pytest.param(Decimal("NaN"), id="nan"),
    pytest.param(Decimal("sNaN"), id="signalling-nan"),
    pytest.param(Decimal("Infinity"), id="infinity"),
    pytest.param(Decimal("-Infinity"), id="minus-infinity"),
    pytest.param(1.5, id="float"),
    pytest.param(float("nan"), id="float-nan"),
    pytest.param(True, id="bool-true"),
    pytest.param(False, id="bool-false"),
    pytest.param("1.00", id="str"),
]


# --- S1.reserve: "books usd on day and month, or books nothing" -----------------------------------------------


def test_reserve_books_the_amount_on_the_day_and_the_month(store):
    """S1.reserve; invariant "day then month in one transaction"."""
    assert store.spend_totals("a", D1) == (Decimal(0), Decimal(0))
    _reserve(store, _usd("1.25"))
    assert store.spend_totals("a", D1) == (_usd("1.25"), _usd("1.25"))
    _reserve(store, _usd("0.50"), day=D2)
    assert store.spend_totals("a", D1) == (_usd("1.25"), _usd("1.75"))
    assert store.spend_totals("a", D2) == (_usd("0.50"), _usd("1.75"))
    assert store.spend_totals("a", OTHER_MONTH) == (Decimal(0), Decimal(0))
    assert store.spend_totals("b", D1) == (Decimal(0), Decimal(0))  # counters are per agent


def test_reserve_past_the_day_cap_is_refused_with_which_day_and_books_nothing(store):
    """S1.reserve; invariant "all or nothing". An amount that lands exactly on the cap passes."""
    cap = _usd("3.00")
    _reserve(store, _usd("2.00"), day_cap=cap)
    refused = _rid()
    with pytest.raises(_cap_error()) as caught:
        _reserve(store, _usd("1.01"), day_cap=cap, rid=refused)
    assert caught.value.which == "day"
    assert store.spend_totals("a", D1) == (_usd("2.00"), _usd("2.00"))
    with pytest.raises(NotFound):  # no row was kept for the refused reservation
        store.settle_spend(refused, Decimal(0))
    _reserve(store, _usd("1.00"), day_cap=cap)
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))
    with pytest.raises(_cap_error()):
        _reserve(store, _usd("0.01"), day_cap=cap)
    _reserve(store, _usd("3.00"), agent="b", day_cap=cap)  # another agent has its own counters


def test_reserve_past_the_month_cap_is_refused_with_which_month_and_the_day_stays_unbooked(store):
    """S1.reserve; invariants "all or nothing" and "day then month in one transaction": the day passes its own cap,
    the month does not, and the day counter of the refused day stays at zero."""
    _reserve(store, _usd("2.00"), day=D1, day_cap=_usd("5.00"), month_cap=_usd("3.00"))
    refused = _rid()
    with pytest.raises(_cap_error()) as caught:
        _reserve(
            store, _usd("1.50"), day=D2, day_cap=_usd("5.00"), month_cap=_usd("3.00"), rid=refused
        )
    assert caught.value.which == "month"
    assert store.spend_totals("a", D2) == (Decimal(0), _usd("2.00"))
    assert store.spend_totals("a", D1) == (_usd("2.00"), _usd("2.00"))
    with pytest.raises(NotFound):
        store.settle_spend(refused, Decimal(0))
    _reserve(store, _usd("1.00"), day=D2, day_cap=_usd("5.00"), month_cap=_usd("3.00"))
    assert store.spend_totals("a", D2) == (_usd("1.00"), _usd("3.00"))


def test_when_both_caps_would_be_passed_the_day_is_named(store):
    """S1.reserve: "day checked first"."""
    with pytest.raises(_cap_error()) as caught:
        _reserve(store, _usd("2.00"), day_cap=_usd("1.00"), month_cap=_usd("1.00"))
    assert caught.value.which == "day"
    assert isinstance(caught.value, RuntimeError)  # the published base class
    assert store.spend_totals("a", D1) == (Decimal(0), Decimal(0))


def test_spend_already_on_the_counters_counts_towards_the_cap(store):
    """S1.reserve, assumption A2: the reservation shares the counters `add_spend` writes."""
    store.add_spend("a", D1, _usd("2.50"))
    with pytest.raises(_cap_error()) as caught:
        _reserve(store, _usd("1.00"), day_cap=_usd("3.00"))
    assert caught.value.which == "day"
    _reserve(store, _usd("0.50"), day_cap=_usd("3.00"))
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))


def test_a_duplicate_reservation_id_is_stale_and_nothing_is_booked_twice(store):
    """S1.reserve: StaleState (id exists). The first row is left exactly as it was."""
    rid = _reserve(store, _usd("1.00"))
    with pytest.raises(StaleState):
        _reserve(store, _usd("1.00"), rid=rid)  # the very same call again
    with pytest.raises(StaleState):
        _reserve(store, _usd("0.25"), agent="b", day=D2, rid=rid)  # same id, other content
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))
    assert store.spend_totals("b", D2) == (Decimal(0), Decimal(0))
    row, applied = store.settle_spend(rid, _usd("1.00"))
    assert applied is True
    assert (row.agent_id, row.day, row.reserved_usd) == ("a", D1, _usd("1.00"))


@pytest.mark.parametrize("bad", HOSTILE)
def test_reserve_refuses_a_bad_amount_and_books_nothing(store, bad):
    """S1.reserve: ValueError; invariant "amounts are finite Decimals >= 0"."""
    refused = _rid()
    with pytest.raises(ValueError):
        _reserve(store, bad, rid=refused)
    assert store.spend_totals("a", D1) == (Decimal(0), Decimal(0))
    with pytest.raises(NotFound):
        store.settle_spend(refused, Decimal(0))
    _reserve(store, _usd("1.00"), rid=refused)  # the id was not used up by the refused call
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))


def test_zero_is_an_allowed_amount(store):
    """S1.reserve and S1.settle: ">= 0" includes zero, for the reservation and for the real cost."""
    rid = _reserve(store, Decimal(0), day_cap=_usd("3.00"), month_cap=_usd("3.00"))
    assert store.spend_totals("a", D1) == (Decimal(0), Decimal(0))
    row, applied = store.settle_spend(rid, Decimal(0))
    assert applied is True
    assert (row.reserved_usd, row.settled_usd) == (Decimal(0), Decimal(0))
    other = _reserve(store, _usd("1.00"))
    row, applied = store.settle_spend(other, Decimal(0))  # a call that cost nothing frees it all
    assert applied is True and row.settled_usd == Decimal(0)
    assert store.spend_totals("a", D1) == (Decimal(0), Decimal(0))


def test_nothing_is_rounded(store):
    """Invariant "nothing rounded": a long Decimal survives the counters, the row and the run's cost."""
    long_reserved, long_actual = (
        _usd("0.000000123456789012345"),
        _usd("0.00108225000000000001"),
    )
    run_id = _run(store)
    rid = _reserve(store, long_reserved, run_id=run_id)
    assert store.spend_totals("a", D1) == (long_reserved, long_reserved)
    row, applied = store.settle_spend(rid, long_actual)
    assert applied is True
    assert (row.reserved_usd, row.settled_usd) == (long_reserved, long_actual)
    assert store.spend_totals("a", D1) == (long_actual, long_actual)
    assert store.get_run(run_id).cost_usd == long_actual


# --- S1.settle: first call closes, later calls change nothing ---------------------------------------------------


def test_first_settle_closes_the_row_and_returns_it(store):
    """S1.settle: the returned row carries the nine columns of the published SpendReservation."""
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), run_id=run_id)
    row, applied = store.settle_spend(rid, _usd("0.40"))
    assert applied is True
    assert (row.reservation_id, row.agent_id, row.day, row.run_id) == (rid, "a", D1, run_id)
    assert (row.reserved_usd, row.settled_usd, row.status) == (
        _usd("1.00"),
        _usd("0.40"),
        "settled",
    )
    assert row.closed_at is not None and row.created_at <= row.closed_at
    assert abs(now() - row.created_at) < timedelta(minutes=5)  # a clock reading, not a default


def test_a_lower_actual_frees_headroom(store):
    """S1.settle: counters move by actual minus reserved, so the freed part can be reserved again."""
    cap = _usd("3.00")
    rid = _reserve(store, _usd("3.00"), day_cap=cap, month_cap=cap)
    with pytest.raises(_cap_error()):
        _reserve(store, _usd("0.50"), day_cap=cap, month_cap=cap)
    store.settle_spend(rid, _usd("0.75"))
    assert store.spend_totals("a", D1) == (_usd("0.75"), _usd("0.75"))
    _reserve(store, _usd("2.25"), day_cap=cap, month_cap=cap)
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))


def test_a_higher_actual_books_the_overshoot_in_full_even_past_the_cap(store):
    """S1.settle; invariant "overshoot booked in full": settle never refuses and never clips at the cap."""
    cap = _usd("3.00")
    rid = _reserve(store, _usd("3.00"), day_cap=cap, month_cap=cap)
    row, applied = store.settle_spend(rid, _usd("4.75"))
    assert applied is True and row.settled_usd == _usd("4.75")
    assert store.spend_totals("a", D1) == (_usd("4.75"), _usd("4.75"))
    with pytest.raises(_cap_error()) as caught:
        _reserve(store, _usd("0.01"), day_cap=cap, month_cap=cap)
    assert caught.value.which == "day"


def test_settle_moves_the_counters_of_the_rows_own_day_not_of_today(store):
    """S1.settle; invariant "the UTC day is fixed at reserve time". The row is reserved on a day that is over (the
    clock day has changed since); the settle must move that day and that month, and leave today untouched."""
    today = now().date()
    assert today not in (D1, D2) and (today.year, today.month) != (D1.year, D1.month)
    store.add_spend("a", today, _usd("0.30"))
    rid = _reserve(store, _usd("1.00"), day=D1)
    higher = _reserve(store, _usd("1.00"), day=D2)
    row, _ = store.settle_spend(rid, _usd("0.25"))
    assert row.day == D1
    assert store.spend_totals("a", D1) == (_usd("0.25"), _usd("1.25"))
    store.settle_spend(higher, _usd("1.50"))
    assert store.spend_totals("a", D2) == (_usd("1.50"), _usd("1.75"))
    assert store.spend_totals("a", today) == (_usd("0.30"), _usd("0.30"))
    assert store.spend_totals("a", now().date()) == (_usd("0.30"), _usd("0.30"))


def test_a_second_settle_returns_the_stored_row_with_false_and_changes_nothing(store):
    """S1.settle; invariant "idempotent settle": the first call wins, whatever the later amount is."""
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), run_id=run_id)
    first, applied = store.settle_spend(rid, _usd("0.40"))
    assert applied is True
    for later in (_usd("0.90"), Decimal(0), _usd("7.00"), _usd("0.40")):
        again, applied = store.settle_spend(rid, later)
        assert applied is False
        assert again == first
        assert again.settled_usd == _usd("0.40")
    assert store.spend_totals("a", D1) == (_usd("0.40"), _usd("0.40"))
    assert store.get_run(run_id).cost_usd == _usd("0.40")


def test_settle_of_an_unknown_id_is_not_found(store):
    """S1.settle: NotFound, and nothing moves."""
    _reserve(store, _usd("1.00"))
    with pytest.raises(NotFound):
        store.settle_spend(_rid(), _usd("0.10"))
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))


@pytest.mark.parametrize("bad", HOSTILE)
def test_settle_refuses_a_bad_amount_and_leaves_the_row_open(store, bad):
    """S1.settle: ValueError. The row is not claimed by the refused call: the next good settle still applies."""
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), run_id=run_id)
    with pytest.raises(ValueError):
        store.settle_spend(rid, bad)
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))
    assert store.get_run(run_id).cost_usd == Decimal(0)
    row, applied = store.settle_spend(rid, _usd("0.20"))
    assert applied is True and row.settled_usd == _usd("0.20")
    assert store.spend_totals("a", D1) == (_usd("0.20"), _usd("0.20"))


def test_settle_adds_the_actual_amount_to_the_runs_cost_once(store):
    """S1.settle (2.1): "adds the actual amount to the run's cost when the row has a run"; only the first call."""
    run_id, other_run = _run(store), _run(store)
    store.add_cost(run_id, _usd("0.10"))
    with_run = _reserve(store, _usd("1.00"), run_id=run_id)
    without_run = _reserve(store, _usd("1.00"))
    assert store.get_run(run_id).cost_usd == _usd("0.10")  # assumption A6: reserve adds nothing
    store.settle_spend(with_run, _usd("0.40"))
    assert store.get_run(run_id).cost_usd == _usd("0.50")
    _, applied = store.settle_spend(with_run, _usd("0.90"))
    assert applied is False
    assert store.get_run(run_id).cost_usd == _usd("0.50")
    row, _ = store.settle_spend(without_run, _usd("0.70"))
    assert row.run_id is None
    assert store.get_run(run_id).cost_usd == _usd("0.50")
    assert store.get_run(other_run).cost_usd == Decimal(0)
    over = _reserve(store, _usd("1.00"), run_id=other_run)
    store.settle_spend(over, _usd("2.50"))  # the whole actual amount, not only the overshoot
    assert store.get_run(other_run).cost_usd == _usd("2.50")


def test_two_threads_settling_one_row_exactly_one_applies(store):
    """Invariant "idempotent settle" under a race: one call applies, the other gets the stored row with False."""
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), run_id=run_id)
    amounts = [_usd("0.20"), _usd("0.60")]
    gate = threading.Barrier(2)
    results, problems = [], []

    def settle(amount):
        gate.wait()
        try:
            results.append((amount, *store.settle_spend(rid, amount)))
        except Exception as exc:  # noqa: BLE001 - anything raised is a failure, reported below
            problems.append(exc)

    threads = [threading.Thread(target=settle, args=(a,)) for a in amounts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not problems
    assert sorted(applied for _, _, applied in results) == [False, True]
    winner = next(amount for amount, _, applied in results if applied)
    assert all(row.settled_usd == winner for _, row, _ in results)
    assert store.spend_totals("a", D1) == (winner, winner)
    assert store.get_run(run_id).cost_usd == winner


# --- S1.expire: "open rows older than that become expired; counters do not move" -----------------------------


def test_expire_marks_old_open_rows_and_the_counters_do_not_move(store):
    """S1.expire; invariant "crash rule (worst case stays booked)". Settled rows are not counted or touched."""
    _reserve(store, _usd("1.00"))
    _reserve(store, _usd("0.50"))
    done = _reserve(store, _usd("0.25"))
    store.settle_spend(done, _usd("0.25"))
    before = store.spend_totals("a", D1)
    assert before == (_usd("1.75"), _usd("1.75"))
    assert store.expire_spend_reservations(3600) == 0  # nothing is an hour old
    assert _expire_all(store) == 2
    assert store.spend_totals("a", D1) == before
    assert _expire_all(store) == 0  # an expired row is not expired twice
    assert store.spend_totals("a", D1) == before
    again, applied = store.settle_spend(done, _usd("9.00"))
    assert applied is False and again.status == "settled"


def test_expire_takes_only_rows_older_than_the_bound(store):
    """S1.expire; invariant "expiry by database clock". Two rows, one more than a second older than the other: a bound
    of one second expires the older one only. Which one expired is read from how its settle behaves (an open row moves
    its counters down, an expired row does not)."""
    old = _reserve(store, _usd("1.00"), day=D1)
    time.sleep(1.3)
    fresh = _reserve(store, _usd("1.00"), day=D2)
    assert store.expire_spend_reservations(1) == 1
    store.settle_spend(fresh, _usd("0.25"))
    assert store.spend_totals("a", D2) == (_usd("0.25"), _usd("1.25"))  # still open: freed
    store.settle_spend(old, _usd("0.25"))
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.25"))  # expired: stays booked


def test_settle_after_expiry_with_a_lower_actual_moves_nothing_down(store):
    """S1.settle (2.1): "an expired row only upward". The first settle still claims the row and the run gets the
    actual amount; a second settle returns False."""
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), run_id=run_id)
    assert _expire_all(store) == 1
    row, applied = store.settle_spend(rid, _usd("0.40"))
    assert applied is True
    assert row.status in ("settled", "expired") and row.closed_at is not None
    assert (row.reserved_usd, row.settled_usd) == (_usd("1.00"), _usd("0.40"))
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))
    assert store.get_run(run_id).cost_usd == _usd("0.40")
    again, applied = store.settle_spend(rid, _usd("5.00"))
    assert applied is False and again == row
    assert store.spend_totals("a", D1) == (_usd("1.00"), _usd("1.00"))
    assert store.get_run(run_id).cost_usd == _usd("0.40")


def test_settle_after_expiry_with_a_higher_actual_books_the_difference(store):
    """S1.settle (2.1): an expired row moves upward by actual minus reserved, past the cap if need be."""
    cap = _usd("1.00")
    run_id = _run(store)
    rid = _reserve(store, _usd("1.00"), day_cap=cap, month_cap=cap, run_id=run_id)
    assert _expire_all(store) == 1
    row, applied = store.settle_spend(rid, _usd("1.75"))
    assert applied is True and row.settled_usd == _usd("1.75")
    assert store.spend_totals("a", D1) == (_usd("1.75"), _usd("1.75"))
    assert store.get_run(run_id).cost_usd == _usd("1.75")
    _, applied = store.settle_spend(rid, _usd("9.00"))
    assert applied is False
    assert store.spend_totals("a", D1) == (_usd("1.75"), _usd("1.75"))
    assert _expire_all(store) == 0  # a claimed row is closed for the sweep too


def test_an_expired_row_keeps_its_headroom_taken(store):
    """Invariant "crash rule": after the sweep the worst case still counts against the cap."""
    cap = _usd("3.00")
    for _ in range(3):
        _reserve(store, _usd("1.00"), day_cap=cap, month_cap=cap)
    assert _expire_all(store) == 3
    with pytest.raises(_cap_error()):
        _reserve(store, _usd("1.00"), day_cap=cap, month_cap=cap)
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))


# --- S1.purge: "deletes closed rows only" ------------------------------------------------------------------------


def test_purge_deletes_closed_rows_only_and_returns_the_count(store):
    """S1.purge; invariant "purge deletes closed rows only". Open and settled rows only: whether an expired row that
    nobody settled counts as closed is an open question (request 003). Counters never move on a purge."""
    kept_open = _reserve(store, _usd("1.00"))
    closed = [_reserve(store, _usd("0.50")) for _ in range(2)]
    for rid in closed:
        store.settle_spend(rid, _usd("0.25"))
    totals = store.spend_totals("a", D1)
    assert totals == (_usd("1.50"), _usd("1.50"))
    assert _purge(store, now() - timedelta(days=1)) == 0  # closed, but after the bound
    _, applied = store.settle_spend(closed[0], _usd("0.25"))
    assert applied is False  # still stored
    assert _purge(store, now() + timedelta(days=1)) == 2
    for rid in closed:
        with pytest.raises(NotFound):
            store.settle_spend(rid, _usd("0.25"))
    assert _purge(store, now() + timedelta(days=1)) == 0
    assert store.spend_totals("a", D1) == totals
    row, applied = store.settle_spend(kept_open, _usd("1.00"))  # the open row outlived both purges
    assert applied is True and row.status == "settled"


# --- invariant "atomic reserve": exactly floor(cap / amount) succeed ---------------------------------------------


@pytest.mark.parametrize("which", ["day", "month"])
def test_fifty_threads_against_a_cap_of_three_exactly_three_succeed(store, which):
    """Invariant "atomic reserve": cap 3.00, amount 1.00, 50 threads on ONE store object: exactly 3 are booked and 47
    raise SpendCapExceeded. Stated limit of the README: the memory store guarantees nothing across processes, so for
    that kind this is a statement about threads of one process only; separate connections are covered by
    tests/contracts/test_t1_reserve_cap.py."""
    cap_error = _cap_error()
    caps = {"day_cap": _usd("3.00"), "month_cap": WIDE}
    if which == "month":
        caps = {"day_cap": WIDE, "month_cap": _usd("3.00")}
    gate = threading.Barrier(50)
    granted, refused, other = [], [], []

    def go():
        rid = _rid()
        gate.wait()
        try:
            store.reserve_spend(rid, "a", D1, _usd("1.00"), **caps)
            granted.append(rid)
        except cap_error as exc:
            refused.append(exc.which)
        except Exception as exc:  # noqa: BLE001 - anything else is a failure, reported below
            other.append(exc)

    threads = [threading.Thread(target=go) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not other
    assert (len(granted), len(refused)) == (3, 47)
    assert set(refused) == {which}
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))
    for rid in granted:  # each granted id is a real open row
        _, applied = store.settle_spend(rid, _usd("1.00"))
        assert applied is True
    assert store.spend_totals("a", D1) == (_usd("3.00"), _usd("3.00"))


# --- all invariants together: a fixed-seed sequence ---------------------------------------------------------------


@pytest.mark.parametrize("seed", [20261120, 7, 4242])
def test_a_random_sequence_keeps_the_counters_equal_to_the_rows(store, seed):
    """A fixed-seed sequence of reserve, settle and expire, checked after every step: no counter is negative, and the
    day counter equals the sum over its rows of: the reserved amount while open or expired; the actual amount once an
    open row is settled; the larger of the two once an expired row is settled (only upward). The month counter is the
    sum of its days, and the run's cost is the sum of the first-settle amounts."""
    rng = random.Random(seed)  # noqa: S311 - a reproducible test sequence, not a secret
    days = [D1, D2, OTHER_MONTH]
    cap = _usd("6.00")
    month_cap = _usd("9.00")
    cap_error = _cap_error()
    run_id = _run(store)
    rows = {}  # rid -> [day, reserved, state, booked]
    run_cost = Decimal(0)

    def check():
        for day in days:
            day_total, month_total = store.spend_totals("a", day)
            booked = sum((r[3] for r in rows.values() if r[0] == day), Decimal(0))
            month = sum(
                (r[3] for r in rows.values() if (r[0].year, r[0].month) == (day.year, day.month)),
                Decimal(0),
            )
            assert day_total >= 0 and month_total >= 0
            assert day_total == booked, (seed, day)
            assert month_total == month, (seed, day)
        assert store.get_run(run_id).cost_usd == run_cost

    for _ in range(120):
        roll = rng.random()
        if roll < 0.45 or not rows:
            day = rng.choice(days)
            usd = Decimal(rng.randrange(1, 250)) / 100
            day_now, month_now = store.spend_totals("a", day)
            rid = _rid()
            try:
                store.reserve_spend(
                    rid, "a", day, usd, day_cap=cap, month_cap=month_cap, run_id=run_id
                )
            except cap_error as exc:
                over_day = day_now + usd > cap
                assert over_day or month_now + usd > month_cap  # a refusal has a reason
                assert exc.which == ("day" if over_day else "month")
            else:
                assert (
                    day_now + usd <= cap and month_now + usd <= month_cap
                )  # a grant fits both caps
                rows[rid] = [day, usd, "open", usd]
        elif roll < 0.9:
            rid = rng.choice(sorted(rows))
            day, reserved, state, _ = rows[rid]
            actual = Decimal(rng.randrange(0, 400)) / 100
            row, applied = store.settle_spend(rid, actual)
            assert applied is (state in ("open", "expired"))
            if state == "open":
                rows[rid] = [day, reserved, "closed", actual]
                run_cost += actual
            elif state == "expired":
                rows[rid] = [day, reserved, "closed", max(reserved, actual)]
                run_cost += actual
            assert row.reserved_usd == reserved
        else:
            open_ids = [rid for rid, r in rows.items() if r[2] == "open"]
            assert _expire_all(store) == len(open_ids)
            for rid in open_ids:
                rows[rid][2] = "expired"
        check()
    assert any(r[2] == "closed" for r in rows.values())  # the sequence did reach settle
