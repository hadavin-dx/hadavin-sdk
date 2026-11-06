"""P4b1-a T3: parity with Intake's spend guard. Each row names the Intake test it mirrors
(`intake-a12/tests/test_budget.py`, line numbers as in the ticket). Amounts are whole micro-dollars.

P4 (two processes) is T5.1 in test_meter_processes.py. Allowed differences: P5 (a second settle returns the first result instead of raising) and P10 (the Intake halt becomes
the cap refusal; no kill switch). Rows P7 (usage adapter), P9 (price at reserve) and P14 (`worst_case_micro`) are
completed only with P4b1-b and are BLOCKED here: they need the P4a names and `llm/metered.py`; P7 is covered for
`record(None)` only."""

import logging
import threading
from decimal import Decimal

import pytest

from hadavin_sdk.meter import Caps, Meter, MeterUnavailable, OverBudget
from hadavin_sdk.money import SpendMicro
from hadavin_sdk.store.memory import MemoryStore
from tests.meter_support import FakeMono

AG = "ag"


def caps(micro=1_000_000):
    return Caps(day=Decimal(micro).scaleb(-6), month=None, run=None)


def books(store):
    from datetime import UTC, datetime

    return store.spend_totals(AG, datetime.now(UTC).date())[0]


def fresh():
    store = MemoryStore()
    return store, Meter(store)


def test_p1_boundary_exact_passes_one_micro_over_refuses_writing_nothing():  # test_budget.py:56-63
    store, m = fresh()
    with pytest.raises(OverBudget):
        m.reserve(AG, SpendMicro(1_000_001), caps())
    assert books(store) == 0 and store.list_open_reservations(agent_id=AG) == []
    assert m.reserve(AG, SpendMicro(1_000_000), caps()).reserved == SpendMicro(1_000_000)


def test_p2_settled_plus_open_plus_worst_case():  # :66-76
    _store, m = fresh()
    a = m.reserve(AG, SpendMicro(400_010), caps())
    b = m.reserve(AG, SpendMicro(400_010), caps())
    with pytest.raises(OverBudget):
        m.reserve(AG, SpendMicro(400_010), caps())
    cost = SpendMicro.ceil_cost(5 * 1_000_000 + 5 * 1_000_000)
    assert cost == SpendMicro(10)
    m.settle(a.reservation_id, cost)
    m.reserve(AG, SpendMicro(400_010), caps())
    assert m.settle(b.reservation_id, None).charged == SpendMicro(400_010)


def test_p3_eight_threads_never_pass_the_cap():  # :79
    store, m = fresh()
    gate, granted, errors = threading.Barrier(8, timeout=20), [], []

    def go():
        try:
            gate.wait()
            for _ in range(5):
                try:
                    granted.append(m.reserve(AG, SpendMicro(100_000), caps()))
                except OverBudget:
                    pass
        except BaseException as exc:  # noqa: BLE001 - reported by the row
            errors.append(repr(exc))

    pool = [threading.Thread(target=go) for _ in range(8)]
    for t in pool:
        t.start()
    for t in pool:
        t.join(40)
    assert errors == [] and len(granted) == 10 and books(store) == Decimal("1.000000")


def test_p5_second_settle_changes_nothing_and_returns_the_first_result():  # :128-133 (deliberate difference)
    store, m = fresh()
    h = m.reserve(AG, SpendMicro(1_000), caps())
    first = m.settle(h.reservation_id, SpendMicro(10))
    second = m.settle(h.reservation_id, SpendMicro(900))
    assert (
        second.applied is False
        and second.charged == first.charged
        and books(store) == Decimal("0.000010")
    )


def test_p6_unknown_reservation_cannot_be_settled():  # :136
    _store, m = fresh()
    with pytest.raises(MeterUnavailable) as ei:
        m.settle("rsv-never-seen", SpendMicro(1))
    assert ei.value.code == "unknown_reservation"


def test_p7_record_none_settles_at_reserved():  # :148-159, -a part only
    store, m = fresh()
    with m.hold(AG, SpendMicro(777), caps()) as h:
        h.record(None)
    assert h.settled.charged == SpendMicro(777) and books(store) == Decimal("0.000777")


@pytest.mark.parametrize(
    ("prices", "usage", "cost"),
    [((333_333, 1), (1, 1), 1), ((1, 333_333), (1, 1), 1), ((1_000_000, 5_000_000), (3, 7), 38)],
)
def test_p8_cost_rounds_up_once(prices, usage, cost):  # :162-167
    numerator = prices[0] * usage[0] + prices[1] * usage[1]
    assert SpendMicro.ceil_cost(numerator) == SpendMicro(cost)


def test_p10_settle_above_reserved_books_actual_in_one_call_and_signals_once():  # :181-197
    store, m = fresh()
    seen = []
    m = Meter(store, on_overshoot=seen.append)
    with m.hold(AG, SpendMicro(20), caps(1_000)) as h:
        h.record(SpendMicro(2_000), measured=True)
    assert h.settled.charged == SpendMicro(2_000) and h.settled.overshoot == SpendMicro(1_980)
    assert len(seen) == 1 and books(store) == Decimal("0.002000")
    with pytest.raises(OverBudget):
        m.reserve(AG, SpendMicro(1), caps(1_000))
    assert store.get_kill_switch().on is False  # the Intake halt is the cap refusal here


def test_p11_open_reservations_count_and_the_orphan_age_policy():  # :199-221 (age policy only)
    mono = FakeMono()
    store = MemoryStore()
    m = Meter(store, monotonic=mono)
    h = m.reserve(AG, SpendMicro(400_000), caps())
    assert m.orphan_age_s() == 605 and h.age_s() == 0
    mono.t += 300
    assert h.age_s() == 300
    m.reserve(AG, SpendMicro(400_000), caps())
    with pytest.raises(OverBudget):
        m.reserve(AG, SpendMicro(400_000), caps())  # young and old open ones both count
    assert len(store.list_open_reservations(agent_id=AG)) == 2


class Boom(Exception):
    pass


@pytest.mark.parametrize(
    "exc", [Boom("x"), ValueError("v"), OSError("o"), RuntimeError("r"), KeyError("k")]
)
def test_p12_p13_every_failure_inside_the_body_settles_at_reserved(exc):  # :223-255
    store, m = fresh()
    with pytest.raises(type(exc)), m.hold(AG, SpendMicro(5_000), caps()):
        raise exc
    assert books(store) == Decimal("0.005000") and store.list_open_reservations(agent_id=AG) == []


@pytest.mark.parametrize("exc", [KeyboardInterrupt, SystemExit])
def test_p12_interrupts_also_settle_at_reserved(exc):
    store, m = fresh()
    with pytest.raises(exc), m.hold(AG, SpendMicro(5_000), caps()):
        raise exc()
    assert books(store) == Decimal("0.005000") and store.list_open_reservations(agent_id=AG) == []


def test_p12_a_logged_overshoot_line_exists_for_an_applied_overshoot(caplog):
    _store, m = fresh()
    with (
        caplog.at_level(logging.WARNING, logger="hadavin_sdk.meter"),
        m.hold(AG, SpendMicro(1), caps()) as h,
    ):
        h.record(SpendMicro(9))
    assert any(r.getMessage().startswith("overshoot") for r in caplog.records)
