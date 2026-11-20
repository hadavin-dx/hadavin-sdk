"""`Limits.reserve` and `Limits.settle` (step F-store, interface (ii): handover/core-b/interfaces/ii-meter.md).

Written by a different agent than the builder, from the ticket (R4, R5, R6 and Q4, Q9, Q10), not from the code.
No database and no conftest fixture: the store is the memory store (its own contract is
tests/contracts/test_store_spend.py), the registry and the audit sink are small stand-ins, and the clock is the
`now` name that `hadavin_sdk.limits` reads, patched where a test needs a certain time."""

import inspect
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk import limits as limits_mod
from hadavin_sdk.limits import Limits, Meter, SpendRefused
from hadavin_sdk.models import KillSwitch, Run, new_id, now
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, StoreUnavailable

try:
    from psycopg import OperationalError
except ImportError:  # no driver installed: any other connection error class stands in

    class OperationalError(Exception):  # type: ignore[no-redef]
        pass


D = Decimal
AGENT = "agent-a"
ZERO = (D(0), D(0))
REASONS = {"kill_switch", "daily_budget", "monthly_budget", "limits_unavailable", "bad_amount"}


class Sink:
    """An audit sink that records what it was asked to write."""

    def __init__(self):
        self.intents, self.outcomes = [], []

    def write_intent(self, event):
        self.intents.append(event)

    def write_outcome(self, event):
        self.outcomes.append(event)


class BrokenSink(Sink):
    def write_outcome(self, event):
        super().write_outcome(event)
        raise RuntimeError("audit down")


class Spy:
    """Passes every call to the real store and counts the calls by name; `fail` makes one method raise."""

    def __init__(self, real, fail=None):
        self._real, self._fail, self.calls = real, fail or {}, []

    def __getattr__(self, name):
        target = getattr(self._real, name)

        def call(*a, **k):
            self.calls.append(name)
            if name in self._fail:
                raise self._fail[name]
            return target(*a, **k)

        return call


def _registry(daily="1.00", monthly="100.00", agents=(AGENT,)):
    budget = SimpleNamespace(daily=D(daily), monthly=D(monthly))
    return SimpleNamespace(agents={a: SimpleNamespace(budget_usd=budget) for a in agents})


def _limits(store=None, sink=None, **caps):
    store = MemoryStore() if store is None else store
    return Limits(store, Sink() if sink is None else sink, _registry(**caps))


def _refused(limits, reason, worst="0.60", agent=AGENT, raw=False, **kw):
    """`worst` is text for a Decimal, or with `raw` the very object that is passed."""
    assert reason in REASONS
    with pytest.raises(SpendRefused) as caught:  # "DID NOT RAISE" means: an id without a booking
        limits.reserve(agent, worst if raw else D(worst), **kw)
    assert caught.value.reason == reason and str(caught.value) == reason
    return caught.value


def _today_totals(limits, agent=AGENT):
    return limits.store.spend_totals(agent, now().date())


def _nothing_booked(limits, agent=AGENT):
    return _today_totals(limits, agent) == ZERO and limits.store._reservations == {}


# --- reserve -------------------------------------------------------------------------------------------------------


def test_reserve_books_the_worst_case_and_returns_a_fresh_id():
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"), run_id="run-x")
    assert re.fullmatch(r"res-[0-9a-f]{32}", rid)
    row = limits.store._reservations[rid]
    assert (row.agent_id, row.reserved_usd, row.status, row.run_id) == (
        AGENT,
        D("0.60"),
        "open",
        "run-x",
    )
    assert row.day == now().date()
    assert _today_totals(limits) == (D("0.60"), D("0.60"))
    other = limits.reserve(AGENT, D("0.40"))  # reaches the cap exactly; run_id is optional
    assert other != rid and limits.store._reservations[other].run_id is None
    assert _today_totals(limits) == (D("1.00"), D("1.00"))
    assert (
        limits.audit.outcomes == [] and limits.audit.intents == []
    )  # a reserve writes no audit row


def test_reserve_passes_the_agents_own_caps_to_the_store():
    store = Spy(MemoryStore())
    seen = {}
    real = store._real.reserve_spend

    def reserve_spend(rid, agent_id, day, usd, **kw):
        seen.update(kw, rid=rid, agent_id=agent_id, day=day, usd=usd)
        return real(rid, agent_id, day, usd, **kw)

    store._real.reserve_spend = reserve_spend
    limits = _limits(store, daily="7.00", monthly="55.00")
    rid = limits.reserve(AGENT, D("0.25"), run_id="run-y")
    assert seen == {
        "rid": rid,
        "agent_id": AGENT,
        "day": now().date(),
        "usd": D("0.25"),
        "day_cap": D("7.00"),
        "month_cap": D("55.00"),
        "run_id": "run-y",
    }
    assert store.calls == ["get_kill_switch", "reserve_spend"]  # the stop state is read first


def test_the_stop_state_refuses_with_kill_switch_and_nothing_is_booked():
    limits = _limits(Spy(MemoryStore()))
    limits.store.set_kill_switch(KillSwitch(on=True, by="ops"))
    limits.store.calls.clear()
    _refused(limits, "kill_switch")
    _refused(limits, "kill_switch", worst="0")
    assert "reserve_spend" not in limits.store.calls
    assert _today_totals(limits) == ZERO and limits.store._real._reservations == {}
    limits.store.set_kill_switch(KillSwitch(on=False, by="admin"))
    assert limits.reserve(AGENT, D("0.60")).startswith(
        "res-"
    )  # it takes effect at the next reserve


def test_the_day_cap_refuses_with_daily_budget():
    limits = _limits()
    _refused(limits, "daily_budget", worst="1.000001")
    assert _nothing_booked(limits)
    limits.reserve(AGENT, D("0.60"))
    _refused(limits, "daily_budget", worst="0.400001")
    assert _today_totals(limits) == (D("0.60"), D("0.60")) and len(limits.store._reservations) == 1
    limits.reserve(AGENT, D("0.40"))
    _refused(limits, "daily_budget", worst="0")  # at the cap even a free call is refused


def test_the_month_cap_refuses_with_monthly_budget():
    limits = _limits(daily="5.00", monthly="1.00")
    _refused(limits, "monthly_budget", worst="1.000001")
    assert _nothing_booked(limits)
    limits.reserve(AGENT, D("1.00"))
    _refused(limits, "monthly_budget", worst="0")


def test_a_budget_of_zero_refuses_even_a_free_call():
    assert _refused(_limits(daily="0"), "daily_budget", worst="0")
    assert _refused(_limits(daily="5", monthly="0"), "monthly_budget", worst="0")


STORE_ERRORS = {
    "operational_error": OperationalError("connection lost"),
    "store_unavailable": StoreUnavailable("store postgres: cannot connect"),
    "runtime_error": RuntimeError("spend counter row missing"),
    "os_error": OSError("broken pipe"),
    "key_error": KeyError("not an agent"),
    "value_error": ValueError("bad"),
    "unknown_cap": SpendCapExceeded("week"),
}


@pytest.mark.parametrize("name", sorted(STORE_ERRORS))
def test_a_store_that_raises_in_reserve_spend_is_limits_unavailable(name):
    limits = _limits(Spy(MemoryStore(), fail={"reserve_spend": STORE_ERRORS[name]}))
    exc = _refused(limits, "limits_unavailable")
    assert exc.__cause__ is None  # the driver's message never travels with the refusal
    assert limits.store.calls == ["get_kill_switch", "reserve_spend"]  # and reserve is not retried
    assert limits.store._real._reservations == {}


@pytest.mark.parametrize("name", sorted(STORE_ERRORS))
def test_a_stop_state_read_that_raises_is_limits_unavailable(name):
    limits = _limits(Spy(MemoryStore(), fail={"get_kill_switch": STORE_ERRORS[name]}))
    _refused(limits, "limits_unavailable")
    assert limits.store.calls == ["get_kill_switch"]  # no booking was even tried
    assert limits.store._real._reservations == {}


def test_the_refusal_log_line_names_the_error_class_and_not_its_message(caplog):
    limits = _limits(Spy(MemoryStore(), fail={"reserve_spend": RuntimeError("host=db user=u")}))
    with caplog.at_level("WARNING", logger="hadavin_sdk.limits"):
        _refused(limits, "limits_unavailable")
    assert "RuntimeError" in caplog.text and "host=db" not in caplog.text


HOSTILE = {
    "nan": D("NaN"),
    "signalling_nan": D("sNaN"),
    "infinity": D("Infinity"),
    "minus_infinity": D("-Infinity"),
    "negative": D("-0.000001"),
    "float": 0.5,
    "bool": True,
    "int": 1,
    "none": None,
    "text": "0.50",
    "ten_to_the_ninth": D(10**9),
    "thirteen_decimals": D("0.0000000000001"),
    "huge_exponent_zero": D("0E+999999"),
    "huge_exponent": D("1E+10"),
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_a_hostile_amount_is_bad_amount_and_the_store_is_never_asked(name):
    limits = _limits(Spy(MemoryStore()), daily="5000000000", monthly="5000000000")
    exc = _refused(limits, "bad_amount", worst=HOSTILE[name], raw=True)
    assert not isinstance(exc, ValueError) and exc.__cause__ is None
    assert limits.store.calls == []  # the amount is checked first: no stop-state read, no booking
    assert limits.store._real._reservations == {}


def test_a_bad_amount_is_reported_before_an_unknown_agent():
    _refused(_limits(), "bad_amount", worst=D("NaN"), agent="nobody", raw=True)


def test_an_unknown_agent_is_a_key_error_even_while_the_stop_state_is_on():
    limits = _limits(Spy(MemoryStore()))
    with pytest.raises(KeyError) as caught:
        limits.reserve("nobody", D("0.10"))
    assert not isinstance(caught.value, SpendRefused)
    limits.store.set_kill_switch(KillSwitch(on=True, by="ops"))
    limits.store.calls.clear()
    with pytest.raises(KeyError):
        limits.reserve("nobody", D("0.10"))
    assert limits.store.calls == []  # the agent is looked up before the stop state is read
    assert limits.store._real._reservations == {}


def test_an_unknown_agent_is_a_key_error_even_when_the_store_is_down():
    limits = _limits(Spy(MemoryStore(), fail={"get_kill_switch": OperationalError("down")}))
    with pytest.raises(KeyError):
        limits.reserve("nobody", D("0.10"))


def test_no_error_path_of_reserve_returns_an_id():
    """Invariant 8, as one sweep: whatever goes wrong, reserve raises and never hands out an id."""
    broken = [{"reserve_spend": e} for e in STORE_ERRORS.values()]
    broken += [{"get_kill_switch": e} for e in STORE_ERRORS.values()]
    for fail in broken:
        limits = _limits(Spy(MemoryStore(), fail=fail))
        with pytest.raises(SpendRefused):
            limits.reserve(AGENT, D("0.10"))
        assert limits.store._real._reservations == {}, fail
    for amount in HOSTILE.values():
        with pytest.raises(SpendRefused):
            _limits().reserve(AGENT, amount)


def test_spend_refused_is_a_runtime_error_that_carries_its_reason():
    exc = SpendRefused("daily_budget")
    assert (
        isinstance(exc, RuntimeError)
        and exc.reason == "daily_budget"
        and exc.args == ("daily_budget",)
    )


def test_limits_has_the_two_methods_of_the_meter_with_the_agreed_signatures():
    for owner in (Limits, Meter):
        reserve = inspect.signature(owner.reserve).parameters
        assert list(reserve) == ["self", "agent_id", "worst_usd", "run_id"]
        assert reserve["run_id"].kind is inspect.Parameter.KEYWORD_ONLY
        assert reserve["run_id"].default is None
        assert list(inspect.signature(owner.settle).parameters) == [
            "self",
            "reservation_id",
            "actual_usd",
            "agent_id",  # keyword-only and required: no agent-less settle
        ]


# --- settle --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("actual", ["0", "0.25", "0.60"])
def test_settle_at_or_below_the_reserved_amount_returns_zero_and_writes_no_audit_row(actual):
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"))
    over = limits.settle(rid, D(actual), agent_id=AGENT)
    assert over == 0 and type(over) is Decimal
    assert _today_totals(limits) == (D(actual), D(actual))
    assert limits.audit.outcomes == [] and limits.audit.intents == []


def test_an_overshoot_is_booked_in_full_returned_and_audited_once():
    """Cap 1.00, month cap 100.00, reserve 0.60, settle 1.50."""
    limits = _limits(daily="1.00", monthly="100.00")
    rid = limits.reserve(AGENT, D("0.60"), run_id="run-x")
    over = limits.settle(rid, D("1.50"), agent_id=AGENT)
    assert over == D("0.90") and type(over) is Decimal
    assert _today_totals(limits) == (D("1.50"), D("1.50"))
    row = limits.store._reservations[rid]
    assert (row.status, row.settled_usd, row.reserved_usd) == ("settled", D("1.50"), D("0.60"))
    assert len(limits.audit.outcomes) == 1 and limits.audit.intents == []
    event = limits.audit.outcomes[0]
    assert (event.domain, event.operation, event.source) == ("limits", "overshoot", "meter")
    assert (event.principal, event.result, event.run_id) == (AGENT, "booked", "run-x")
    # a replay, also with another amount, returns the first result and writes NO second audit row
    for amount in ("1.50", "0.10", "9.00"):
        assert limits.settle(rid, D(amount), agent_id=AGENT) == D("0.90")
    assert len(limits.audit.outcomes) == 1
    assert _today_totals(limits) == (D("1.50"), D("1.50"))
    # every later reserve of that day is refused, also a free one
    _refused(limits, "daily_budget", worst="0.000001")
    _refused(limits, "daily_budget", worst="0")


def test_the_day_after_an_overshoot_is_free_again(monkeypatch):
    limits = _limits(daily="1.00", monthly="100.00")
    limits.settle(limits.reserve(AGENT, D("0.60")), D("1.50"), agent_id=AGENT)
    _refused(limits, "daily_budget", worst="0")
    start = now()
    monkeypatch.setattr(limits_mod, "now", lambda: start + timedelta(days=1))
    rid = limits.reserve(AGENT, D("1.00"))
    assert limits.store._reservations[rid].day == (start + timedelta(days=1)).date()
    assert limits.store.spend_totals(AGENT, start.date())[0] == D("1.50")


def test_the_overshoot_event_of_a_reservation_without_a_run_names_no_run():
    limits = _limits()
    assert limits.settle(limits.reserve(AGENT, D("0.10")), D("0.35"), agent_id=AGENT) == D("0.25")
    assert [e.run_id for e in limits.audit.outcomes] == ["-"]


def test_a_raising_audit_sink_does_not_make_settle_raise(caplog):
    limits = _limits(sink=BrokenSink())
    rid = limits.reserve(AGENT, D("0.60"))
    with caplog.at_level("WARNING", logger="hadavin_sdk.limits"):
        assert limits.settle(rid, D("1.50"), agent_id=AGENT) == D("0.90")
    assert len(limits.audit.outcomes) == 1  # it was tried once
    assert "RuntimeError" in caplog.text and "audit down" not in caplog.text
    assert _today_totals(limits) == (D("1.50"), D("1.50"))  # the booking stands
    assert (
        limits.settle(rid, D("1.50"), agent_id=AGENT) == D("0.90")
        and len(limits.audit.outcomes) == 1
    )


def test_settle_with_an_unknown_id_is_not_found():
    limits = _limits()
    limits.reserve(AGENT, D("0.60"))
    with pytest.raises(NotFound):
        limits.settle(new_id("res"), D("0.10"), agent_id=AGENT)
    with pytest.raises(KeyError):
        limits.settle("res-unknown", D("5.00"), agent_id=AGENT)
    assert _today_totals(limits) == (D("0.60"), D("0.60")) and limits.audit.outcomes == []


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_settle_with_a_bad_amount_is_a_value_error_and_the_worst_case_stays(name):
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"))
    with pytest.raises(ValueError):
        limits.settle(rid, HOSTILE[name], agent_id=AGENT)
    assert limits.store._reservations[rid].status == "open"
    assert _today_totals(limits) == (D("0.60"), D("0.60")) and limits.audit.outcomes == []


def test_a_store_that_raises_in_settle_reaches_the_caller_and_writes_no_audit_row():
    """Contract point 6: the gate catches it and returns the reply; settle itself does not hide the failure."""
    limits = _limits(Spy(MemoryStore(), fail={"settle_spend": OperationalError("gone")}))
    rid = limits.reserve(AGENT, D("0.60"))
    with pytest.raises(OperationalError):
        limits.settle(rid, D("1.50"), agent_id=AGENT)
    assert limits.audit.outcomes == []
    assert limits.store._real._reservations[rid].status == "open"


def test_settle_adds_the_real_cost_to_the_run():
    limits = _limits(daily="10")
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    limits.store.create_run(run)
    limits.settle(limits.reserve(AGENT, D("0.60"), run_id=run.run_id), D("0.25"), agent_id=AGENT)
    limits.settle(limits.reserve(AGENT, D("0.60"), run_id=run.run_id), D("0.75"), agent_id=AGENT)
    assert limits.store.get_run(run.run_id).cost_usd == D("1.00")


def test_expired_then_settled_lower_is_no_overshoot_and_no_audit_row():
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"))
    assert limits.store.expire_spend_reservations(0) == 1
    assert limits.settle(rid, D("0.10"), agent_id=AGENT) == 0
    assert limits.audit.outcomes == []
    assert _today_totals(limits) == (
        D("0.60"),
        D("0.60"),
    )  # after expiry the booking never goes down


def test_expired_then_settled_higher_is_an_overshoot_audited_once():
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"))
    assert limits.store.expire_spend_reservations(0) == 1
    assert limits.settle(rid, D("0.85"), agent_id=AGENT) == D("0.25")
    assert limits.settle(rid, D("0.10"), agent_id=AGENT) == D("0.25")
    assert len(limits.audit.outcomes) == 1
    assert _today_totals(limits) == (D("0.85"), D("0.85"))


# --- midnight ------------------------------------------------------------------------------------------------------


def test_a_reserve_in_the_last_microsecond_books_that_day_and_a_late_settle_moves_it(monkeypatch):
    day = now().date().replace(month=1, day=31)
    clock = [datetime(day.year, 1, 31, 23, 59, 59, 999999, tzinfo=UTC)]
    monkeypatch.setattr(limits_mod, "now", lambda: clock[0])
    limits = _limits()
    rid = limits.reserve(AGENT, D("0.60"))
    assert limits.store._reservations[rid].day == day
    assert limits.store.spend_totals(AGENT, day) == (D("0.60"), D("0.60"))
    clock[0] += timedelta(microseconds=1)  # 00:00:00 of February 1
    following = clock[0].date()
    assert (following.month, following.day) == (2, 1)
    assert limits.store.spend_totals(AGENT, following) == ZERO
    other = limits.reserve(AGENT, D("1.00"))  # a new day and a new month: the full cap is free
    assert limits.store._reservations[other].day == following
    assert limits.settle(rid, D("0.85"), agent_id=AGENT) == D(
        "0.25"
    )  # settled "tomorrow": January 31 moves
    assert limits.store.spend_totals(AGENT, day) == (D("0.85"), D("0.85"))
    assert limits.store.spend_totals(AGENT, following) == (D("1.00"), D("1.00"))
