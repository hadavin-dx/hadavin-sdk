"""P4b1-a T1.8 to T1.32: the meter against a scripted store (memory underneath; errors raised on demand).

BLOCKED by P4d-a2-ii: the real `StoreBusy` does not exist yet. The rows that name it use `Busy`, a class defined in
THIS file and bound to the name `store.protocol.StoreBusy` for one test (`busy` fixture), so they prove the meter's
mapping and retry logic only; they say nothing about the real class. They are marked in the evidence file."""

import logging
import re
import time
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk import models
from hadavin_sdk.defaults import METER_MAX_HOLD_LIMIT_S, METER_SETTLE_RETRIES
from hadavin_sdk.meter import (
    CODES,
    REASON_BY_WHICH,
    Caps,
    Meter,
    MeterError,
    MeterUnavailable,
    OverBudget,
)
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.money import BusinessMoney, SpendMicro
from hadavin_sdk.store import protocol as sp
from hadavin_sdk.store.memory import MemoryStore
from tests.meter_support import (
    NO_CAPS,
    FakeMono,
    ScriptedStore,
    StepClock,
    make_run,
    new_meter,
    utc,
)

D = Decimal
S = SpendMicro


class Busy(RuntimeError):
    """Stand-in for P4d-a2-ii's `StoreBusy` (BLOCKED: the real class is not built)."""


@pytest.fixture
def busy(monkeypatch):
    monkeypatch.setattr(sp, "StoreBusy", Busy, raising=False)
    return Busy


def reserve_row(store, hold):
    return store.get_spend_reservation(hold.reservation_id)


# --- T1.8 fail closed ---------------------------------------------------------------------------------------------
STORE_ERRORS = [
    lambda: sp.KillSwitchOn("x"),
    lambda: sp.SpendCapExceeded("day", D(1), D(1), D(1)),
    lambda: sp.ReservationConflict("x"),
    lambda: sp.StaleState("x"),
    lambda: sp.NotFound("x"),
    lambda: sp.CounterDamaged("x"),
    lambda: ValueError("x"),
    lambda: RuntimeError("x"),
    lambda: OSError("x"),
    lambda: MemoryError(),
]


@pytest.mark.parametrize("make", STORE_ERRORS)
def test_t1_8_a_store_error_never_reaches_the_model_call(make):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(make())
    reached = []
    with pytest.raises(MeterError), meter.hold("ag", S(10), NO_CAPS):
        reached.append(1)
    assert reached == []


def test_t1_8_busy_store_never_reaches_the_model_call(busy):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(busy())
    reached = []
    with pytest.raises(MeterUnavailable), meter.hold("ag", S(10), NO_CAPS):
        reached.append(1)
    assert reached == []


# --- T1.9 error table -----------------------------------------------------------------------------------------------
RESERVE_TABLE = [
    (lambda: sp.CounterDamaged("x"), "counter_damaged"),
    (lambda: sp.ReservationConflict("x"), "conflict"),
    (lambda: sp.StaleState("x"), "conflict"),
    (lambda: sp.NotFound("x"), "unknown_run"),
    (lambda: ValueError("x"), "store_rejected"),
    (lambda: RuntimeError("x"), "store_unreachable"),
    (lambda: OSError("x"), "store_unreachable"),
    (lambda: MemoryError(), "store_unreachable"),
]


@pytest.mark.parametrize(("make", "code"), RESERVE_TABLE)
def test_t1_9_reserve_error_table(make, code):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(make())
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value.code == code and code in CODES


def test_t1_9_reserve_busy_and_overbudget_rows(busy):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(busy())
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value.code == "store_busy"
    store.raises["reserve_spend"].append(sp.KillSwitchOn("x"))
    with pytest.raises(OverBudget) as ob:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ob.value.reasons == ("kill_switch",)


SETTLE_TABLE = [
    (lambda: sp.NotFound("x"), "unknown_reservation"),
    (
        lambda: sp.StaleState("x"),
        "conflict",
    ),  # defensive row: P4d never raises it from settle (fake store only)
    (lambda: sp.CounterDamaged("x"), "counter_damaged"),
    (lambda: ValueError("x"), "store_rejected"),
    (lambda: OSError("x"), "store_unreachable"),
    (lambda: RuntimeError("x"), "store_unreachable"),
]


@pytest.mark.parametrize("method", ["settle_spend", "release_spend"])
@pytest.mark.parametrize(("make", "code"), SETTLE_TABLE)
def test_t1_9_settle_and_release_error_table(method, make, code):
    store, meter = new_meter()
    h = meter.reserve("ag", S(10), NO_CAPS)
    store.raises[method].append(make())
    with pytest.raises(MeterUnavailable) as ei:
        (
            meter.settle(h.reservation_id, S(5))
            if method == "settle_spend"
            else meter.release(h.reservation_id)
        )
    assert ei.value.code == code


@pytest.mark.parametrize("method", ["settle_spend", "release_spend"])
def test_t1_9_settle_and_release_busy_row(busy, method):
    store, meter = new_meter()
    h = meter.reserve("ag", S(10), NO_CAPS)
    store.raises[method].append(busy())
    with pytest.raises(MeterUnavailable) as ei:
        (
            meter.settle(h.reservation_id, S(5))
            if method == "settle_spend"
            else meter.release(h.reservation_id)
        )
    assert ei.value.code == "store_busy"


def test_t1_9_counter_damaged_is_never_store_rejected():
    store, meter = new_meter()
    store.raises["reserve_spend"].append(sp.CounterDamaged("x"))
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value.code != "store_rejected"
    assert not isinstance(ei.value, (OSError, ValueError))


def test_t1_9_the_unknown_id_is_unknown_reservation_on_the_real_store():  # T1.18
    _, meter = new_meter()
    for call in (
        lambda: meter.settle("rsv-nope", S(1)),
        lambda: meter.settle("rsv-nope", None),
        lambda: meter.release("rsv-nope"),
    ):
        with pytest.raises(MeterUnavailable) as ei:
            call()
        assert ei.value.code == "unknown_reservation"


# --- T1.10 / T1.11 OverBudget ---------------------------------------------------------------------------------------
def test_t1_10_overbudget_numbers_for_run_day_and_month():
    store, meter = new_meter()
    run = make_run(store)
    day = meter.spend_day()
    h = meter.reserve(
        "ag", S(600_000), Caps(day=D("1"), month=D("1"), run=D("1")), run_id=run.run_id
    )
    assert h.day == day
    cases = {
        "run": Caps(day=D("5"), month=D("5"), run=D("1")),
        "day": Caps(day=D("1"), month=D("5"), run=D("5")),
        "month": Caps(day=D("5"), month=D("1"), run=D("5")),
    }
    for which, caps in cases.items():
        with pytest.raises(OverBudget) as ei:
            meter.reserve("ag", S(500_000), caps, run_id=run.run_id)
        e = ei.value
        assert e.which == which and e.reasons == (REASON_BY_WHICH[which],)
        assert (e.cap, e.current, e.requested) == (D("1"), D("0.600000"), D("0.500000"))
        assert e.day == day and type(e.cap) is D
    store.raises["reserve_spend"].append(sp.KillSwitchOn("x"))
    with pytest.raises(OverBudget) as ei:
        meter.reserve("ag", S(1), NO_CAPS)
    e = ei.value
    assert (e.which, e.cap, e.current, e.requested) == (None, None, None, None) and e.day == day


def test_t1_11_reason_table():
    assert REASON_BY_WHICH == {
        "run": "run_budget",
        "day": "daily_budget",
        "month": "monthly_budget",
    }


# --- T1.12 / T1.13 lost acknowledgement and the release table --------------------------------------------------------
def test_t1_12_lost_acknowledgement_releases_exactly_once():
    store, meter = new_meter()
    store.after["reserve_spend"].append(OSError("lost"))
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value.code == "store_unreachable"
    reserved = next(a for m, a in store.calls if m == "reserve_spend")[0]
    assert [a for m, a in store.calls if m == "release_spend"] == [(reserved,)]
    assert store.get_spend_reservation(reserved).status == "released"


def test_t1_12_a_failing_release_is_swallowed():
    store, meter = new_meter()
    store.after["reserve_spend"].append(OSError("lost"))
    store.raises["release_spend"].append(RuntimeError("also down"))
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value.code == "store_unreachable"
    assert store.count("release_spend") == 1


@pytest.mark.parametrize("exc", [KeyboardInterrupt, SystemExit])
def test_t1_12_interrupts_release_and_re_raise_unchanged(exc):
    store, meter = new_meter()
    err = exc()
    store.raises["reserve_spend"].append(err)
    with pytest.raises(exc) as ei:
        meter.reserve("ag", S(10), NO_CAPS)
    assert ei.value is err
    assert store.count("release_spend") == 1


NO_RELEASE = [
    lambda: sp.KillSwitchOn("x"),
    lambda: sp.SpendCapExceeded("run", D(1), D(1), D(1)),
    lambda: sp.ReservationConflict("x"),
    lambda: sp.StaleState("x"),
    lambda: sp.NotFound("x"),
    lambda: sp.CounterDamaged("x"),
    lambda: ValueError("x"),
]
ONE_RELEASE = [
    lambda: OSError("x"),
    lambda: type("psycopg_OperationalError", (Exception,), {})("x"),  # a driver-shaped error
    lambda: MemoryError(),
    lambda: KeyboardInterrupt(),
    lambda: SystemExit(),
]


@pytest.mark.parametrize("make", NO_RELEASE)
def test_t1_13_no_release_when_the_store_answered(make):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(make())
    with pytest.raises(MeterError):
        meter.reserve("ag", S(10), NO_CAPS)
    assert store.count("release_spend") == 0


@pytest.mark.parametrize("make", ONE_RELEASE)
def test_t1_13_one_release_with_the_same_id_when_the_outcome_is_unknown(make):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(make())
    with pytest.raises((MeterError, KeyboardInterrupt, SystemExit)):
        meter.reserve("ag", S(10), NO_CAPS)
    sent = [a[0] for m, a in store.calls if m == "reserve_spend"]
    assert [a[0] for m, a in store.calls if m == "release_spend"] == sent


def test_t1_13_one_release_after_store_busy(busy):
    store, meter = new_meter()
    store.raises["reserve_spend"].append(busy())
    with pytest.raises(MeterUnavailable):
        meter.reserve("ag", S(10), NO_CAPS)
    assert store.count("release_spend") == 1


# --- T1.14 arguments --------------------------------------------------------------------------------------------------
def test_t1_14_arguments():
    store, meter = new_meter()
    with pytest.raises(TypeError):
        Caps(day=None, month=None)  # an omitted field
    with pytest.raises(TypeError):
        Caps(None, None, None)  # keyword-only
    with pytest.raises(ValueError):
        meter.reserve("ag", S(10), Caps(day=None, month=None, run=D("1")))
    assert store.count("reserve_spend") == 0
    run = make_run(store)
    meter.reserve("ag", S(10), NO_CAPS, run_id=run.run_id)
    assert store.get_run(run.run_id).cost_usd == D(
        "0.000010"
    )  # run_id reached the store with no run cap
    for bad in (5, 1.0, D(1), None, BusinessMoney(1, "USD")):
        with pytest.raises(TypeError):
            meter.reserve("ag", bad, NO_CAPS)
    with pytest.raises(ValueError):
        meter.reserve("ag", S(0), NO_CAPS)
    with pytest.raises(TypeError):
        meter.reserve("ag", S(1), None)
    for bad_id in ("", "a b", "x" * 201, 5):
        with pytest.raises(ValueError):
            meter.reserve(bad_id, S(1), NO_CAPS)
    with pytest.raises(ValueError):
        meter.reserve("ag", S(1), Caps(day=D("1.123456789"), month=None, run=None))
    assert store.count("reserve_spend") == 1


# --- T1.15 ids -----------------------------------------------------------------------------------------------------------
def test_t1_15_ids_are_unique_and_in_the_grammar():
    _store, meter = new_meter()
    ids = {meter.reserve("ag", S(1), NO_CAPS).reservation_id for _ in range(10_000)}
    assert len(ids) == 10_000
    assert all(re.fullmatch(r"rsv-[0-9a-f]{32}", i) for i in ids)
    assert all(uuid.UUID(i[4:]).hex == i[4:] for i in list(ids)[:50])


# --- T1.16 / T1.17 / T1.18 idempotent settle -------------------------------------------------------------------------
def test_t1_16_second_settle_returns_the_first_result():
    store, meter = new_meter()
    h = meter.reserve("ag", S(100), NO_CAPS)
    first = meter.settle(h.reservation_id, S(40))
    second = meter.settle(h.reservation_id, S(70))
    assert first.applied and not second.applied
    assert (second.charged, second.status) == (first.charged, "settled") == (S(40), "settled")
    day, _ = store.spend_totals("ag", h.day)
    assert day == D("0.000040")


def test_t1_17_release_after_settle_and_settle_after_release(caplog):
    store, meter = new_meter()
    a = meter.reserve("ag", S(100), NO_CAPS)
    meter.settle(a.reservation_id, S(40))
    r = meter.release(a.reservation_id)
    assert (r.status, r.applied, r.charged) == ("settled", False, S(40))
    b = meter.reserve("ag", S(100), NO_CAPS)
    rel = meter.release(b.reservation_id)
    assert (rel.status, rel.applied, rel.charged) == ("released", True, S(0))
    with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"):
        late = meter.settle(b.reservation_id, S(77))
    assert (late.status, late.applied) == ("released", False)
    lines = [r.getMessage() for r in caplog.records if "superseded" in r.getMessage()]
    assert len(lines) == 1 and b.reservation_id in lines[0] and "77" in lines[0]
    day, _ = store.spend_totals("ag", b.day)
    assert day == D("0.000040")


# --- T1.19 record rules ----------------------------------------------------------------------------------------------------
def test_t1_19_record_and_release_rules():
    store, meter = new_meter()
    h = meter.reserve("ag", S(100), NO_CAPS)
    with pytest.raises(ValueError):
        h.record(S(0))
    with pytest.raises(ValueError):
        meter.settle(h.reservation_id, S(0))
    with pytest.raises(TypeError):
        h.record(5)
    with pytest.raises(TypeError):
        h.record(S(1), measured=1)
    assert store.count("settle_spend") == 0
    # record(None): the worst case
    with meter.hold("ag", S(100), NO_CAPS) as a:
        a.record(S(7))
        a.record(None)
    assert a.settled.charged == S(100)
    # last wins: record twice, record then release, release then record
    with meter.hold("ag", S(100), NO_CAPS) as b:
        b.record(S(5))
        b.record(S(9))
    assert b.settled.charged == S(9)
    with meter.hold("ag", S(100), NO_CAPS) as c:
        c.record(S(5))
        c.release()
    assert c.settled.status == "released"
    with meter.hold("ag", S(100), NO_CAPS) as d:
        d.release()
        d.record(S(5))
    assert (d.settled.status, d.settled.charged) == ("settled", S(5))


# --- T1.20 Settled and overshoot -----------------------------------------------------------------------------------------------
def overshoot_lines(caplog):
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith("overshoot")]


@pytest.mark.parametrize("with_callback", [True, False])
@pytest.mark.parametrize("measured", [True, False])
def test_t1_20_overshoot_signal(caplog, with_callback, measured):
    seen = []
    _store, meter = new_meter(on_overshoot=seen.append if with_callback else None)
    with (
        caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"),
        meter.hold("ag", S(20), NO_CAPS) as h,
    ):
        h.record(S(2000), measured=measured)
    s = h.settled
    assert (s.applied, s.charged, s.overshoot) == (True, S(2000), S(1980))
    assert len(overshoot_lines(caplog)) == 1  # written with or without a callback, measured or not
    line = overshoot_lines(caplog)[0]
    assert h.reservation_id in line and "ag" in line and "20 " in line and "2000" in line
    assert len(seen) == (1 if with_callback and measured else 0)
    caplog.clear()
    again = meter.settle(h.reservation_id, S(3000))  # a replay: no signal, no line
    assert not again.applied and again.overshoot == S(1980)
    assert overshoot_lines(caplog) == [] and len(seen) == (1 if with_callback and measured else 0)


def test_t1_20_no_overshoot_when_the_cost_is_within_the_reservation(caplog):
    seen = []
    _, meter = new_meter(on_overshoot=seen.append)
    with (
        caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"),
        meter.hold("ag", S(20), NO_CAPS) as h,
    ):
        h.record(S(20))
    assert h.settled.overshoot == S(0) and seen == [] and overshoot_lines(caplog) == []


def test_t1_20_applied_maps_first_true_replay_false():
    _, meter = new_meter()
    h = meter.reserve("ag", S(20), NO_CAPS)
    assert meter.settle(h.reservation_id, S(5)).applied is True
    assert meter.settle(h.reservation_id, S(5)).applied is False


def test_t1_20_a_raising_callback_is_logged_by_class_and_does_not_escape(caplog):
    def boom(_):
        raise RuntimeError("SECRET-CALLBACK-TEXT")

    _store, meter = new_meter(on_overshoot=boom)
    with (
        caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"),
        meter.hold("ag", S(20), NO_CAPS) as h,
    ):
        h.record(S(30))
    assert h.settled.applied
    assert "RuntimeError" in caplog.text and "SECRET-CALLBACK-TEXT" not in caplog.text


def test_t1_20_a_standalone_settle_writes_the_line_but_never_calls_the_callback(caplog):
    seen = []
    _, meter = new_meter(on_overshoot=seen.append)
    h = meter.reserve("ag", S(20), NO_CAPS)
    with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"):
        s = meter.settle(h.reservation_id, S(50))
    assert s.overshoot == S(30) and seen == [] and len(overshoot_lines(caplog)) == 1


# --- T1.21 the context manager settles on every exit -----------------------------------------------------------------------------
@pytest.mark.parametrize("exc", [RuntimeError, KeyError, KeyboardInterrupt, SystemExit])
def test_t1_21_settles_when_the_body_raises(exc):
    store, meter = new_meter()
    holder = []
    with pytest.raises(exc), meter.hold("ag", S(100), NO_CAPS) as h:
        holder.append(h)
        h.record(S(30))
        raise exc()
    assert reserve_row(store, holder[0]).status == "settled"
    assert holder[0].settled.charged == S(30)


def test_t1_21_settles_on_return_release_and_default():
    store, meter = new_meter()
    with meter.hold("ag", S(100), NO_CAPS) as a:
        pass
    assert a.settled.charged == S(100) and a.settled.status == "settled"  # neither: the worst case
    with meter.hold("ag", S(100), NO_CAPS) as b:
        b.release()
    assert b.settled.status == "released"
    assert store.spend_totals("ag", a.day)[0] == D("0.000100")

    def f():
        with meter.hold("ag", S(100), NO_CAPS) as h:
            h.record(S(4))
            return h

    assert f().settled.charged == S(4)


# --- T1.22 exit failures -----------------------------------------------------------------------------------------------------------
def test_t1_22_the_bodys_exception_wins_over_a_failing_exit():
    failed = []
    store, meter = new_meter(on_settle_failed=failed.append)
    store.raises["settle_spend"].append(sp.CounterDamaged("x"))
    with pytest.raises(KeyError), meter.hold("ag", S(100), NO_CAPS) as h:
        raise KeyError("body")
    assert h.settle_failure.code == "counter_damaged" and failed == [h.settle_failure]


def test_t1_22_a_succeeded_body_with_a_failing_exit_returns_normally():
    failed = []
    store, meter = new_meter(on_settle_failed=failed.append)
    store.raises["settle_spend"].append(sp.CounterDamaged("x"))
    with meter.hold("ag", S(100), NO_CAPS) as h:
        h.record(S(40))
    assert h.settled is None and failed == [h.settle_failure]
    assert h.settle_failure.reservation_id == h.reservation_id
    assert reserve_row(store, h).status == "open"  # the reservation stays at its worst case
    assert store.spend_totals("ag", h.day)[0] == D("0.000100")


def test_t1_22b_a_planned_amount_above_the_reservation_is_carried(caplog):
    failed = []
    store, meter = new_meter(on_settle_failed=failed.append)
    store.raises["settle_spend"].append(sp.CounterDamaged("x"))
    with (
        caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"),
        meter.hold("ag", S(10), NO_CAPS) as h,
    ):
        h.record(S(30), measured=False)
    assert h.settle_failure.planned == S(30) and failed[0].planned == S(30)
    assert "planned 30 micro-dollars" in caplog.text
    assert reserve_row(store, h).status == "open" and reserve_row(store, h).reserved_usd == D(
        "0.000010"
    )
    assert store.count("release_spend") == 0
    s = meter.settle(h.reservation_id, S(30))  # the repair
    assert s.applied and store.spend_totals("ag", h.day)[0] == D("0.000030")


def test_t1_22_a_bug_inside_the_exit_never_replaces_the_body_outcome(monkeypatch):
    """Not a store error: the exit code itself raises (here the result reader). The body's exception still wins,
    a succeeded body still returns, and the failure is recorded with the closed code `store_unreachable`."""
    failed = []
    store, meter = new_meter(on_settle_failed=failed.append)

    def broken(_outcome):
        raise RuntimeError("bug in the exit")

    monkeypatch.setattr(Meter, "_settled", staticmethod(broken))
    with pytest.raises(KeyError), meter.hold("ag", S(100), NO_CAPS) as h:
        raise KeyError("body")
    assert h.settle_failure.code == "store_unreachable"
    with meter.hold("ag", S(100), NO_CAPS) as g:
        g.record(S(40))
    assert g.settle_failure.code == "store_unreachable" and len(failed) == 2


def test_t1_22_a_failing_callback_never_escapes(caplog):
    def boom(_):
        raise RuntimeError("x")

    store, meter = new_meter(on_settle_failed=boom)
    store.raises["settle_spend"].append(sp.CounterDamaged("x"))
    with meter.hold("ag", S(10), NO_CAPS):
        pass


# --- T1.23 retries ------------------------------------------------------------------------------------------------------------------------
def test_t1_23_busy_once_then_success(busy):
    store, meter = new_meter()
    store.raises["settle_spend"].append(busy())
    with meter.hold("ag", S(100), NO_CAPS) as h:
        h.record(S(30))
    assert h.settle_failure is None and h.settled.charged == S(30)
    calls = [a for m, a in store.calls if m == "settle_spend"]
    assert len(calls) == 2 and calls[0] == calls[1]


def test_t1_23_busy_every_time_gives_store_busy_after_exactly_the_retries(busy):
    store, meter = new_meter()
    store.raises["settle_spend"].extend(busy() for _ in range(5))
    with meter.hold("ag", S(100), NO_CAPS) as h:
        h.record(S(30))
    assert h.settle_failure.code == "store_busy" and h.settle_failure.planned == S(30)
    calls = [a for m, a in store.calls if m == "settle_spend"]
    assert len(calls) == 1 + METER_SETTLE_RETRIES == 3 and len(set(calls)) == 1
    assert store.count("release_spend") == 0


@pytest.mark.parametrize("make", [lambda: sp.CounterDamaged("x"), lambda: ValueError("x")])
def test_t1_23_counter_damaged_and_value_error_are_not_retried_and_never_release(make):
    store, meter = new_meter()
    store.raises["settle_spend"].append(make())
    with meter.hold("ag", S(100), NO_CAPS) as h:
        h.record(S(30))
    assert store.count("settle_spend") == 1 and store.count("release_spend") == 0
    assert h.settle_failure.code in ("counter_damaged", "store_rejected")


def test_t1_23_a_failing_release_plan_keeps_the_reservation():
    store, meter = new_meter()
    store.raises["release_spend"].append(sp.CounterDamaged("x"))
    with meter.hold("ag", S(100), NO_CAPS) as h:
        h.release()
    assert h.settle_failure.code == "counter_damaged" and h.settle_failure.planned is None


# --- T1.24 repair ---------------------------------------------------------------------------------------------------------------------------
def test_t1_24_repair_from_open_and_from_expired():
    clock = StepClock()
    store, meter = new_meter(ScriptedStore(MemoryStore(clock=clock)))
    h = meter.reserve("ag", S(100), NO_CAPS)
    store.raises["settle_spend"].append(sp.CounterDamaged("x"))
    with pytest.raises(MeterUnavailable):
        meter.settle(h.reservation_id, S(60))
    assert meter.settle(h.reservation_id, S(60)).applied  # from open
    g = meter.reserve("ag", S(100), NO_CAPS)
    clock.advance(1000)
    assert [r.reservation_id for r in store.sweep_spend_reservations(60)] == [g.reservation_id]
    assert reserve_row(store, g).status == "expired"
    assert meter.settle(g.reservation_id, S(60)).applied  # from expired (P4d PL12)
    assert reserve_row(store, g).status == "settled"


# --- T1.25 kill switch ------------------------------------------------------------------------------------------------------------------------
def test_t1_25_the_exit_settle_works_with_the_kill_switch_on():
    store, meter = new_meter()
    with meter.hold("ag", S(100), NO_CAPS) as h:
        store.set_kill_switch(KillSwitch(on=True, by="t"))
        h.record(S(30))
    assert h.settled.charged == S(30) and h.settle_failure is None
    with pytest.raises(OverBudget):
        meter.reserve("ag", S(1), NO_CAPS)


# --- T1.26 clocks and limits ------------------------------------------------------------------------------------------------------------------------
def test_t1_26_age_follows_the_injected_monotonic_clock(monkeypatch):
    mono = FakeMono()
    _, meter = new_meter(monotonic=mono)
    h = meter.reserve("ag", S(1), NO_CAPS)
    assert h.age_s() == 0
    mono.t += 42.5
    monkeypatch.setattr(
        models, "now", lambda: datetime.now(UTC) + timedelta(days=1)
    )  # wall clock jumps a day
    assert h.age_s() == 42.5


def test_t1_26_default_monotonic_is_resolved_at_call_time(monkeypatch):
    _, meter = new_meter()
    monkeypatch.setattr(time, "monotonic", lambda: 5.0)
    h = meter.reserve("ag", S(1), NO_CAPS)
    monkeypatch.setattr(time, "monotonic", lambda: 12.0)
    assert h.age_s() == 7.0


@pytest.mark.parametrize(
    ("hold_s", "orphan"), [(1, 600), (297, 600), (298, 601), (300, 605), (3600, 7205)]
)
def test_t1_26_orphan_age(hold_s, orphan):
    assert new_meter(max_hold_s=hold_s)[1].orphan_age_s() == orphan


def test_t1_26_default_hold_and_range():
    assert new_meter()[1].max_hold_s == 300
    for bad in (0, -1, METER_MAX_HOLD_LIMIT_S + 1, True, "5", 5.0):
        with pytest.raises(ValueError):
            new_meter(max_hold_s=bad)
    assert new_meter(max_hold_s=METER_MAX_HOLD_LIMIT_S)[1].max_hold_s == METER_MAX_HOLD_LIMIT_S


# --- T1.27 log content ------------------------------------------------------------------------------------------------------------------------------
def test_t1_27_logs_hold_only_ids_codes_and_amounts(caplog):
    store, meter = new_meter(
        on_overshoot=lambda s: None, max_hold_s=1, monotonic=(mono := FakeMono())
    )
    store.raises["reserve_spend"].append(OSError("SECRET-STORE-TEXT"))
    with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"):
        with pytest.raises(MeterUnavailable):
            meter.reserve("ag", S(1), NO_CAPS)
        store.after["reserve_spend"].append(OSError("SECRET-STORE-TEXT"))
        store.raises["release_spend"].append(RuntimeError("SECRET-RELEASE-TEXT"))
        with pytest.raises(MeterUnavailable):
            meter.reserve("ag", S(1), NO_CAPS)
        store.raises["settle_spend"].append(RuntimeError("SECRET-SETTLE-TEXT"))
        with meter.hold("ag", S(5), NO_CAPS) as h:
            h.record(S(9))
            mono.t += 100
        with meter.hold("ag", S(5), NO_CAPS) as g:
            g.record(S(9))
        r = meter.reserve("ag", S(5), NO_CAPS)
        meter.release(r.reservation_id)
        meter.settle(r.reservation_id, S(5))
    assert caplog.records
    for rec in caplog.records:
        assert rec.exc_info is None
        assert "SECRET" not in rec.getMessage()
    assert "SECRET" not in caplog.text


# --- T1.28 / T1.29 construction and names -------------------------------------------------------------------------------------------------------------
def test_t1_28_a_store_with_missing_methods_is_refused():
    class Partial:
        def reserve_spend(self):
            pass

    with pytest.raises(MeterError) as ei:
        Meter(Partial())
    assert "settle_spend" in str(ei.value) and "release_spend" in str(ei.value)


def test_t1_28_clock_none_resolves_models_now_at_call_time(monkeypatch):
    _, meter = new_meter()
    monkeypatch.setattr(models, "now", lambda: utc(2031, 3, 4, 5))
    assert meter.spend_day().isoformat() == "2031-03-04"


def test_t1_29_the_meter_has_no_sweep_prune_or_delete_name():
    names = [n for n in dir(Meter) if not n.startswith("_")]
    assert sorted(names) == ["hold", "orphan_age_s", "release", "reserve", "settle", "spend_day"]
    assert not [n for n in dir(Meter(MemoryStore())) if re.search("sweep|prune|delete|purge", n)]


# --- T1.30 the UTC day ---------------------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def kolkata(monkeypatch):
    assert hasattr(time, "tzset"), "this row needs time.tzset (Unix); it must not skip"
    monkeypatch.setenv("TZ", "Asia/Kolkata")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_t1_30_the_cap_day_is_utc_at_midnight_under_a_non_utc_zone(kolkata):
    today = datetime.now(UTC).date()
    assert time.localtime(0).tm_gmtoff == 19800  # the zone really is +05:30
    for stamp, expected in (
        (datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=UTC), today),
        (
            datetime(today.year, today.month, today.day, tzinfo=UTC) + timedelta(days=1),
            today + timedelta(days=1),
        ),
    ):
        meter = Meter(MemoryStore(), clock=lambda stamp=stamp: stamp)
        assert meter.spend_day() == expected
        assert meter.reserve("ag", S(1), NO_CAPS).day == expected


# --- T1.31 / T1.32 -----------------------------------------------------------------------------------------------------------------------------------------
def test_t1_31_an_old_hold_writes_exactly_one_line_at_exit(caplog):
    mono = FakeMono()
    _store, meter = new_meter(monotonic=mono, max_hold_s=60)
    with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.meter"):
        with meter.hold("ag", S(1), NO_CAPS) as young:
            mono.t += 60  # exactly max_hold_s: no line
        with meter.hold("ag", S(1), NO_CAPS) as old:
            mono.t += 61
    lines = [r.getMessage() for r in caplog.records if "stayed open" in r.getMessage()]
    assert len(lines) == 1 and old.reservation_id in lines[0] and "61" in lines[0]
    assert young.reservation_id not in caplog.text


def test_t1_32_a_far_day_refusal_is_store_rejected_without_release():
    store, meter = new_meter()
    store.raises["reserve_spend"].append(ValueError("day must be within one day of today (UTC)"))
    with pytest.raises(MeterUnavailable) as ei:
        meter.reserve("ag", S(1), NO_CAPS)
    assert ei.value.code == "store_rejected" and store.count("release_spend") == 0
