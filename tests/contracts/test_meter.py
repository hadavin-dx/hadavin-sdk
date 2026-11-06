"""P4b1-a T6: the meter on every store kind (`store`, `store_pair`). Each test uses its own agent id."""

import itertools
from decimal import Decimal

import pytest

from hadavin_sdk.meter import Caps, Meter, MeterUnavailable, OverBudget
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.money import SpendMicro
from tests.contracts.store_support import utc_today

D = Decimal
_n = itertools.count()


def agent():
    return f"mt{next(_n)}"


def day_cap(micro):
    return Caps(day=D(micro).scaleb(-6), month=None, run=None)


def total(store, who):
    return store.spend_totals(who, utc_today(store))[0]


def test_t6_1_round_trip(store):
    who, m = agent(), Meter(store)
    h = m.reserve(who, SpendMicro(400_000), day_cap(1_000_000))
    assert total(store, who) == D("0.400000")
    assert [r.reservation_id for r in store.list_open_reservations(agent_id=who)] == [
        h.reservation_id
    ]
    s = m.settle(h.reservation_id, SpendMicro(150_000))
    assert (s.applied, s.status, s.charged, s.overshoot) == (
        True,
        "settled",
        SpendMicro(150_000),
        SpendMicro(0),
    )
    assert total(store, who) == D("0.150000") and store.list_open_reservations(agent_id=who) == []
    r = m.reserve(who, SpendMicro(300_000), day_cap(1_000_000))
    rel = m.release(r.reservation_id)
    assert (rel.applied, rel.status, rel.charged) == (True, "released", SpendMicro(0))
    assert total(store, who) == D("0.150000")


def test_t6_2_settle_is_idempotent(store):
    who, m = agent(), Meter(store)
    h = m.reserve(who, SpendMicro(400_000), day_cap(1_000_000))
    first = m.settle(h.reservation_id, SpendMicro(100_000))
    again = m.settle(h.reservation_id, SpendMicro(390_000))
    assert again.applied is False and (again.charged, again.status) == (first.charged, first.status)
    assert total(store, who) == D("0.100000")


def test_t6_3_exact_boundary(store):
    who, m = agent(), Meter(store)
    caps = day_cap(1_000_000)
    m.reserve(who, SpendMicro(1_000_000), caps)
    with pytest.raises(OverBudget):
        m.reserve(who, SpendMicro(1), caps)
    assert total(store, who) == D("1.000000")
    other = agent()
    with pytest.raises(OverBudget):
        m.reserve(other, SpendMicro(1_000_001), caps)
    assert total(store, other) == D("0")


def test_t6_4_kill_switch(store):
    who, m = agent(), Meter(store)
    h = m.reserve(who, SpendMicro(10), day_cap(1_000_000))
    store.set_kill_switch(KillSwitch(on=True, by="t"))
    try:
        with pytest.raises(OverBudget) as ei:
            m.reserve(who, SpendMicro(10), day_cap(1_000_000))
        assert ei.value.reasons == ("kill_switch",)
        assert (
            m.settle(h.reservation_id, SpendMicro(5)).applied is True
        )  # an open hold still closes
    finally:
        store.set_kill_switch(KillSwitch(on=False, by="t"))


def test_t6_5_unknown_id(store):
    m = Meter(store)
    for call in (lambda: m.settle("rsv-nope", SpendMicro(1)), lambda: m.release("rsv-nope")):
        with pytest.raises(MeterUnavailable) as ei:
            call()
        assert ei.value.code == "unknown_reservation"


def test_t6_6_exit_and_exact_micro_round_trip(store):
    who, m = agent(), Meter(store)
    with m.hold(who, SpendMicro(999_999), day_cap(1_000_000)) as h:
        assert total(store, who) == D("0.999999")
        h.record(SpendMicro(123_457))
    assert h.settled.charged == SpendMicro(123_457) and total(store, who) == D("0.123457")
    with m.hold(who, SpendMicro(7), day_cap(1_000_000)):
        pass  # neither record nor release: the worst case stays booked
    assert total(store, who) == D("0.123464")
    with m.hold(who, SpendMicro(5), day_cap(1_000_000)) as g:
        g.release()
    assert total(store, who) == D("0.123464")


def test_t6_7_settle_from_a_second_meter_on_the_second_handle(store_pair):
    first, second = store_pair
    who = agent()
    h = Meter(first).reserve(who, SpendMicro(400_000), day_cap(1_000_000))
    s = Meter(second).settle(h.reservation_id, SpendMicro(100_000))
    assert s.applied is True and total(first, who) == total(second, who) == D("0.100000")
    assert Meter(first).settle(h.reservation_id, SpendMicro(1)).applied is False


def test_t6_8_a_settle_above_reserved_books_the_full_actual_once(store):
    who, m = agent(), Meter(store)
    h = m.reserve(who, SpendMicro(20), day_cap(1_000_000))
    s = m.settle(h.reservation_id, SpendMicro(2_000))
    assert (s.applied, s.charged, s.overshoot) == (True, SpendMicro(2_000), SpendMicro(1_980))
    assert total(store, who) == D("0.002000")
    assert m.settle(h.reservation_id, SpendMicro(2_000)).applied is False
    assert total(store, who) == D("0.002000")
