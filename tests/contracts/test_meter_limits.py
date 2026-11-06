"""P4b1-a T2: the meter shares ONE counter with `Limits` (memory and Postgres through the `store` fixture).

This file sits under `tests/contracts/` because the `store` fixture is defined only in `tests/contracts/conftest.py`.
Its module-level imports are only modules that exist on `ce70eb5` (before the meter): the new names come in through
`_new(...)` inside the tests, so the fail-before copy of this file collects there and fails on an ASSERTION
(`test_t2_8_check_then_spend_race`). All amounts are `Decimal` (build note 19)."""

import contextlib
import importlib
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch, Run
from hadavin_sdk.registry import Budget

D = Decimal
WAIT_S = 20  # every wait has a timeout that FAILS the row, so nothing can deadlock


def _new(name):
    return importlib.import_module(f"hadavin_sdk.{name}")


def S(micro):
    return _new("money").SpendMicro(micro)


def usd(text):
    return _new("money").SpendMicro.from_usd(D(text))


def make_limits(store, daily="1.00", monthly="100", max_run=None, agent="ag"):
    record = SimpleNamespace(
        budget_usd=Budget(daily=D(daily), monthly=D(monthly)),
        max_run_usd=None if max_run is None else D(max_run),
    )
    return Limits(store, None, SimpleNamespace(agents={agent: record}))


def make_run(store, agent="ag"):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


class Spy:
    """Forwards to the store, counts calls, and can fail the next call of a method."""

    def __init__(self, inner):
        self._inner, self.calls, self.fail = inner, [], {}

    def count(self, name):
        return sum(1 for c in self.calls if c == name)

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if name.startswith("_") or not callable(attr):
            return attr

        def call(*a, **k):
            self.calls.append(name)
            if self.fail.get(name):
                raise self.fail[name].pop(0)
            return attr(*a, **k)

        return call


def totals(store, day=None):
    day = day or datetime.now(UTC).date()
    return store.spend_totals("ag", day)


# --- T2.1 to T2.5 -----------------------------------------------------------------------------------------------
def test_t2_1_a_hold_after_a_charge_is_refused_by_the_daily_cap(store):
    limits = make_limits(store)
    limits.charge("ag", D("0.60"))
    before = totals(store)
    with pytest.raises(_new("meter").OverBudget) as ei, limits.hold("ag", usd("0.50")):
        pytest.fail("the body must not run")
    assert ei.value.reasons == ("daily_budget",)
    assert totals(store) == before == (D("0.60"), D("0.60"))


def test_t2_2_blocked_reads_an_open_hold(store):
    limits = make_limits(store, daily="0.50")
    assert limits.blocked("ag") == []
    with limits.hold("ag", usd("0.50")):
        assert limits.blocked("ag") == [
            "daily_budget"
        ]  # the day total includes the open reservation
    assert limits.blocked("ag") == ["daily_budget"]  # settled at the worst case: still 0.50


def test_t2_3_exactly_at_the_cap_passes_one_micro_over_is_refused_and_writes_nothing(store):
    limits = make_limits(store)
    meter = _new("meter")
    with limits.hold("ag", usd("1.000000")) as h:
        assert totals(store)[0] == D("1.000000")
        h.release()
    assert totals(store)[0] == D("0.000000")
    with pytest.raises(meter.OverBudget), limits.hold("ag", S(1_000_001)):
        pytest.fail("the body must not run")
    assert totals(store) == (D("0"), D("0"))
    limits.charge("ag", D("0.999999"))
    with limits.hold("ag", S(1)):
        pass
    with pytest.raises(meter.OverBudget), limits.hold("ag", S(1)):
        pass
    assert totals(store)[0] == D("1.000000")


def test_t2_4_month_and_run_caps_each_refuse_alone_and_the_order_is_run_day_month(store):
    meter = _new("meter")
    limits = make_limits(store, daily="5", monthly="1", max_run="5")
    run = make_run(store)
    with limits.hold("ag", usd("0.60"), run_id=run.run_id):
        pass
    with pytest.raises(meter.OverBudget) as ei, limits.hold("ag", usd("0.50"), run_id=run.run_id):
        pass
    assert (ei.value.which, ei.value.reasons) == ("month", ("monthly_budget",))
    limits = make_limits(store, daily="5", monthly="5", max_run="1")
    with pytest.raises(meter.OverBudget) as ei, limits.hold("ag", usd("0.50"), run_id=run.run_id):
        pass
    assert (ei.value.which, ei.value.reasons) == ("run", ("run_budget",))
    limits = make_limits(
        store, daily="1", monthly="1", max_run="1"
    )  # all three fail: the run is named first
    with pytest.raises(meter.OverBudget) as ei, limits.hold("ag", usd("0.50"), run_id=run.run_id):
        pass
    assert ei.value.which == "run"
    limits = make_limits(
        store, daily="1", monthly="1", max_run="5"
    )  # day and month fail: day first
    with pytest.raises(meter.OverBudget) as ei, limits.hold("ag", usd("0.50"), run_id=run.run_id):
        pass
    assert ei.value.which == "day"


def test_t2_5_kill_switch_on_or_missing_row_refuses_and_the_exit_settle_still_works(store):
    meter = _new("meter")
    limits = make_limits(store)
    with limits.hold("ag", usd("0.50")) as h:
        store.set_kill_switch(KillSwitch(on=True, by="t"))
        h.record(S(100))
    assert h.settled.charged == S(100) and h.settle_failure is None
    with pytest.raises(meter.OverBudget) as ei, limits.hold("ag", S(1)):
        pass
    assert ei.value.reasons == ("kill_switch",) and ei.value.which is None
    assert "kill_switch" in limits.blocked("ag")


# --- T2.6 shared day ---------------------------------------------------------------------------------------------
@pytest.fixture
def kolkata(monkeypatch):
    assert hasattr(time, "tzset"), "this row needs time.tzset (Unix); it must not skip"
    monkeypatch.setenv("TZ", "Asia/Kolkata")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_t2_6_charge_blocked_and_hold_read_the_same_day_at_midnight(store, kolkata, monkeypatch):
    limits_mod = importlib.import_module("hadavin_sdk.limits")
    day0 = datetime.now(
        UTC
    ).date()  # read once; never a fixed past date (the store refuses a far day)
    limits = make_limits(store, daily="0.50")
    for stamp, day in (
        (datetime(day0.year, day0.month, day0.day, 23, 59, 59, tzinfo=UTC), day0),
        (
            datetime(day0.year, day0.month, day0.day, tzinfo=UTC) + timedelta(days=1),
            day0 + timedelta(days=1),
        ),
    ):
        monkeypatch.setattr(
            limits_mod, "now", lambda stamp=stamp: stamp
        )  # ONLY limits' own binding
        assert limits.blocked("ag") == []
        limits.charge("ag", D("0.10"))
        with limits.hold("ag", usd("0.20")):
            assert store.spend_totals("ag", day)[0] == D("0.30")
            assert limits.blocked("ag") == []
        with pytest.raises(_new("meter").OverBudget) as ei, limits.hold("ag", usd("0.30")):
            pass
        assert ei.value.day == day
        assert store.spend_totals("ag", day)[0] == D("0.30")


# --- T2.7 uncapped run -------------------------------------------------------------------------------------------
def test_t2_7_an_uncapped_run_still_follows_its_settles(store):
    limits = make_limits(store, max_run=None)
    run = make_run(store)
    with limits.hold("ag", usd("0.50"), run_id=run.run_id) as h:
        assert store.get_run(run.run_id).cost_usd == D("0.500000")
        h.record(S(120_000))
    with limits.hold("ag", usd("0.10"), run_id=run.run_id) as h2:
        h2.record(S(30_000))
    assert store.get_run(run.run_id).cost_usd == D("0.150000")


# --- T2.8 the check-then-spend race (FAIL-BEFORE on ce70eb5) --------------------------------------------------------
RACE_AMOUNT = D("0.40")


def _race(limits, threads=8, amount=RACE_AMOUNT):
    """8 threads: barrier 1 before the reserve; each thread counts itself once its reserve (or old-path check) is
    answered; the 8th answer sets an Event; granted threads wait for it inside the hold and only then settle."""
    meter = _new("meter") if hasattr(limits, "hold") else None
    barrier = threading.Barrier(threads, timeout=WAIT_S)
    answered_n, lock, all_answered = [0], threading.Lock(), threading.Event()
    granted, errors = [], []

    def answered():
        with lock:
            answered_n[0] += 1
            if answered_n[0] == threads:
                all_answered.set()

    def wait_for_everyone():
        if not all_answered.wait(WAIT_S):
            raise TimeoutError("the other threads never answered")

    def spend():
        try:
            barrier.wait()
            if meter is not None:
                try:
                    with limits.hold("ag", _new("money").SpendMicro.from_usd(amount)):
                        answered()
                        wait_for_everyone()
                        granted.append(1)
                except meter.OverBudget:
                    answered()
            else:  # the old path on ce70eb5: check, then charge after the call
                if limits.blocked("ag"):
                    answered()
                    return
                answered()
                wait_for_everyone()
                limits.charge("ag", amount)
                granted.append(1)
        except BaseException as exc:  # noqa: BLE001 - reported by the row
            errors.append(repr(exc))

    pool = [threading.Thread(target=spend) for _ in range(threads)]
    for t in pool:
        t.start()
    for t in pool:
        t.join(WAIT_S * 2)
    assert not any(t.is_alive() for t in pool), "a thread is stuck"
    assert errors == []
    return len(granted)


def test_t2_8_check_then_spend_race(store):
    limits = make_limits(store, daily="1.00")
    granted = _race(limits)
    total = store.spend_totals("ag", datetime.now(UTC).date())[0]
    assert total <= D("1.00"), f"day total {total} passed the 1.00 cap"
    assert granted == 2 and total == D(
        "0.80"
    )  # floor(1.00 / 0.40) x 0.40; a meter that always refuses fails


# --- T2.9 caps -------------------------------------------------------------------------------------------------------
def test_t2_9_caps_from_the_registry_rounded_down(store):
    meter = _new("meter")
    limits = make_limits(store, daily="1.123456789", monthly="20", max_run="0.999999999")
    assert limits.caps("ag") == meter.Caps(
        day=D("1.12345678"), month=D("20.00000000"), run=D("0.99999999")
    )
    assert make_limits(store).caps("ag") == meter.Caps(day=D("1.00"), month=D("100"), run=None)
    with pytest.raises(meter.MeterError):
        limits.caps("nobody")
    with pytest.raises(meter.MeterError), limits.hold("nobody", S(1)):
        pass


# --- T2.10 one Meter on first use ---------------------------------------------------------------------------------------
def test_t2_10_eight_threads_on_first_use_build_one_meter(store, monkeypatch):
    limits_mod = importlib.import_module("hadavin_sdk.limits")
    real = limits_mod.Meter
    built = []

    class Slow(real):
        def __init__(self, *a, **k):
            time.sleep(0.2)
            super().__init__(*a, **k)
            built.append(self)

    monkeypatch.setattr(limits_mod, "Meter", Slow)  # Limits.hold must look the name up at call time
    limits = make_limits(store)
    barrier = threading.Barrier(8, timeout=WAIT_S)
    errors = []

    def go():
        try:
            barrier.wait()
            with limits.hold("ag", S(1)):
                pass
        except BaseException as exc:  # noqa: BLE001 - reported by the row
            errors.append(repr(exc))

    pool = [threading.Thread(target=go) for _ in range(8)]
    for t in pool:
        t.start()
    for t in pool:
        t.join(WAIT_S)
    assert errors == [] and len(built) == 1 and limits._meter is built[0]
    assert store.spend_totals("ag", datetime.now(UTC).date())[0] == D("0.000008")


# --- T2.11 charge ---------------------------------------------------------------------------------------------------------
def test_t2_11a_charge_with_a_decimal_still_books(store):
    limits = make_limits(store)
    limits.charge("ag", D("0.25"))
    assert totals(store)[0] == D("0.25")  # regression pin


def test_t2_11b_charge_with_spend_micro_books_the_same_row_and_business_money_is_refused(store):
    limits = make_limits(store)
    limits.charge("ag", D("0.25"))
    limits.charge("ag", S(250_000))
    assert totals(store)[0] == D("0.50")
    with pytest.raises(TypeError):
        limits.charge("ag", _new("money").BusinessMoney(5, "USD"))
    assert totals(store)[0] == D("0.50")


# --- T2.12 overshoot through Limits ---------------------------------------------------------------------------------------------
def test_t2_12_a_settle_above_the_reservation_books_the_full_actual_once(store):
    meter = _new("meter")
    spy = Spy(store)
    limits = make_limits(spy, max_run="5")
    run = make_run(store)
    seen = []
    limits.on_overshoot = seen.append
    with limits.hold("ag", usd("0.50"), run_id=run.run_id) as h:
        h.record(usd("1.20"), measured=True)
    assert (h.settled.applied, h.settled.overshoot) == (True, usd("0.70"))
    assert totals(store) == (D("1.20"), D("1.20")) and store.get_run(run.run_id).cost_usd == D(
        "1.20"
    )
    assert (
        spy.count("settle_spend") == 1
        and spy.count("add_spend") == 0
        and spy.count("add_cost") == 0
    )
    assert [s.overshoot for s in seen] == [usd("0.70")]
    with pytest.raises(meter.OverBudget), limits.hold("ag", S(1), run_id=run.run_id):
        pass
    assert store.get_kill_switch().on is False


# --- T2.13 callbacks set after the Meter was built ---------------------------------------------------------------------------------
def test_t2_13_callbacks_set_later_are_still_called(store):
    spy = Spy(store)
    limits = make_limits(spy)
    with limits.hold("ag", S(10)):
        pass  # the Meter exists now, built with no callbacks set
    over, failed = [], []
    limits.on_overshoot, limits.on_settle_failed = over.append, failed.append
    with limits.hold("ag", S(10)) as h:
        h.record(S(50))
    assert [s.charged for s in over] == [S(50)]
    spy.fail["settle_spend"] = [_new("store.protocol").CounterDamaged("x")]
    with limits.hold("ag", S(10)) as g:
        g.record(S(20))
    assert [f.code for f in failed] == ["counter_damaged"] and failed[0].planned == S(20)


# --- T2.14 counter above the store ceiling (pins whatever P4d gives) -----------------------------------------------------------------
def test_t2_14_a_counter_above_the_store_ceiling(store):
    meter_mod = _new("meter")
    top = _new("defaults").MAX_USD
    ceiling = _new("store.protocol").MAX_COUNTER_USD
    limits = make_limits(store)
    m = meter_mod.Meter(store)
    no_caps = meter_mod.Caps(day=None, month=None, run=None)
    with contextlib.ExitStack() as stack:
        for _ in range((ceiling // top) + 1):  # all rows OPEN first, then all settled
            stack.enter_context(m.hold("ag", S(1), no_caps)).record(S(top * 1_000_000))
    day_total = store.spend_totals("ag", datetime.now(UTC).date())[0]
    assert day_total > ceiling
    assert "daily_budget" in limits.blocked("ag")  # no exception
    reached = []
    with pytest.raises(meter_mod.MeterError) as ei, m.hold("ag", S(1), no_caps):
        reached.append(1)
    assert reached == []
    pinned = (type(ei.value).__name__, getattr(ei.value, "code", None))
    print("P4d answer above the ceiling:", pinned)
    assert pinned in {("MeterUnavailable", "store_rejected"), ("OverBudget", None)}


# --- T2.15 unknown run ------------------------------------------------------------------------------------------------------------------
def test_t2_15_an_unknown_run_is_refused_without_a_trace(store):
    meter = _new("meter")
    spy = Spy(store)
    limits = make_limits(spy)
    before = totals(store)
    with (
        pytest.raises(meter.MeterUnavailable) as ei,
        limits.hold("ag", S(5), run_id="run-does-not-exist"),
    ):
        pass
    assert ei.value.code == "unknown_run"
    assert store.list_open_reservations(agent_id="ag") == []
    assert totals(store) == before and spy.count("release_spend") == 0
