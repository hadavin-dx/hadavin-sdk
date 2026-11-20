"""Interface (ii), the Meter the model gate calls: reserve money for one model call before the call, settle the
real cost after it. Written by core-a as an independent reader (not the builder) from core-b's published text
at core-b commit 7f8481795: handover/core-b/interfaces/ii-meter.md (the ten points, cited here as "ii N"),
interfaces/README.md version 2.3 (the invariants of section 1, cited as "inv N") and tickets/F-install.md
(U5, U6, V2, W2 and W7 for the in-memory Budget).

Implementers under test, one shape:
- `limits-memory`: `Limits` on the memory store.
- `limits-postgres`: `Limits` on PostgreSQL with the runtime login (HADAVIN_TEST_PG_DSN and `pg_schema`).
- `budget`: the in-memory `Budget` of the eval and replay command lines. Until it has `reserve` and `settle`
  (it "arrives with step F-install", ii-meter.md header) its cases are skipped with the reason
  `BUDGET_NOT_BUILT`, and `test_both_implementers_have_the_meter_shape[budget]` is a strict expected failure,
  so the day it lands this file says so and its cases start to run. They are written from the ticket only.

The whole module is skipped with `NOT_LANDED` on a branch whose `Limits` has no `reserve`.

How "booked" is observed: for `Limits` through `store.spend_totals` (the day and month counters the store keeps),
for `Budget` through `spent` (settled plus held, ticket U6). The clock of `Limits` is the `now` name that
`hadavin_sdk.limits` reads; every case pins it, so a run across midnight cannot change a result.

A test marked xfail(strict) with a reason starting "FINDING Mn" is a defect of the code as built; the mark is
applied to the one implementer that has it (`_finding`).

Overlap with core-b's own tests (added to its branch after our store run): tests/test_limits_reserve.py covers
`Limits` on the memory store only (refusal reasons, hostile amounts, settle, the last microsecond of a day).
New here: the same points on PostgreSQL, threads and connections through `Limits`, concurrent settles, a stop
set between the read and the booking, a closed database connection, the tick step, one table of scenarios run
through every implementer, and the Budget cases.
"""

import inspect
import math
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk import limits as limits_mod
from hadavin_sdk.models import KillSwitch, Run
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound

NOT_LANDED = "core-b meter not on this branch yet"
BUDGET_NOT_BUILT = (
    "k1b Budget has no reserve/settle on this tree: the in-memory meter arrives with step F-install "
    "(ii-meter.md header); its cases are written from tickets/F-install.md and have never run"
)
Limits = limits_mod.Limits
LANDED = hasattr(Limits, "reserve") and hasattr(Limits, "settle")
pytestmark = pytest.mark.skipif(not LANDED, reason=NOT_LANDED)
SpendRefused = getattr(limits_mod, "SpendRefused", RuntimeError)


def _budget_class():
    """Ticket U6: Budget moves to hadavin_sdk.limits and k1b/loop.py keeps the name."""
    found = getattr(limits_mod, "Budget", None)
    if found is None:
        from hadavin_sdk.k1b import loop

        found = getattr(loop, "Budget", None)
    return found


BUDGET = _budget_class()
BUDGET_BUILT = BUDGET is not None and hasattr(BUDGET, "reserve") and hasattr(BUDGET, "settle")

D = Decimal
AGENT = "agent-m"
WIDE = D(1000)  # a cap that is never reached
SMALLEST = D("0.000000000001")  # 12 decimal places: the smallest amount above zero (inv 9)
REASONS = {  # ii-meter.md: "Allowlist all six"
    "kill_switch",
    "daily_budget",
    "monthly_budget",
    "limits_unavailable",
    "bad_amount",
    "usd_cap",
}
YEAR = datetime.now(UTC).year - 1  # every pinned day is in the past
NOON = datetime(YEAR, 3, 10, 12, 0, tzinfo=UTC)
CALLERS = 16
WAIT_S = 60

HOSTILE = [
    pytest.param(D("-0.01"), id="negative"),
    pytest.param(D("NaN"), id="nan"),
    pytest.param(D("sNaN"), id="signalling-nan"),
    pytest.param(D("Infinity"), id="infinity"),
    pytest.param(D("-Infinity"), id="minus-infinity"),
    pytest.param(1.5, id="float"),
    pytest.param(float("nan"), id="float-nan"),
    pytest.param(True, id="bool-true"),
    pytest.param(False, id="bool-false"),
    pytest.param(1, id="int"),
    pytest.param("1.00", id="str"),
    pytest.param(None, id="none"),
    pytest.param(D("0.0000000000001"), id="thirteen-decimal-places"),
    pytest.param(D("1E+9"), id="ten-to-the-ninth"),
    pytest.param(D(10**9), id="ten-to-the-ninth-as-integer-decimal"),
]


# --- stand-ins ----------------------------------------------------------------------------------------------------


class Sink:
    """An audit sink that keeps what it was asked to write."""

    def __init__(self):
        self.intents, self.outcomes = [], []

    def write_intent(self, event):
        self.intents.append(event)

    def write_outcome(self, event):
        self.outcomes.append(event)


class Inner:
    """The fake inner client: counts its calls and answers with a fixed cost. `seen` is what was booked at the
    moment of the call."""

    def __init__(self, cost, booked=None):
        self.cost, self.calls, self.seen, self._booked = cost, 0, [], booked

    def chat(self):
        self.calls += 1
        if self._booked is not None:
            self.seen.append(self._booked())
        return SimpleNamespace(cost_usd=self.cost)


def _gated(meter, inner, worst, run_id=None):
    """The three lines of README section 2, with ii 6: a settle that raises does not take the reply away."""
    rid = meter.reserve(AGENT, worst, run_id=run_id)
    reply = inner.chat()
    try:
        over = meter.settle(rid, reply.cost_usd)
    except Exception as exc:  # noqa: BLE001 - ii 6: return the reply anyway
        over = exc
    return rid, reply, over


class Spy:
    """Passes every call to the real store and keeps the names; `fail` makes one method raise instead."""

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


class StopAfterRead:
    """A store on which somebody sets the stop right after the meter's first stop-state read returned 'off'."""

    def __init__(self, real):
        self._real, self.done = real, False

    def __getattr__(self, name):
        return getattr(self._real, name)

    def get_kill_switch(self):
        seen = self._real.get_kill_switch()
        if not self.done:
            self.done = True
            self._real.set_kill_switch(KillSwitch(on=True, by="operator-" + uuid.uuid4().hex[:6]))
        return seen


def _registry(daily, monthly):
    budget = SimpleNamespace(daily=daily, monthly=monthly)
    return SimpleNamespace(agents={AGENT: SimpleNamespace(budget_usd=budget)})


def _pg_stores(request, count):
    """`count` stores of the runtime login on one fresh schema, one connection each (skips without the DSN)."""
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends.factory import make
    from hadavin_sdk.backends.table import PostgresSettings
    from tests.contracts.kinds.store_postgres import pg_schema

    schema = pg_schema(runtime=True)
    dsn = next(schema)
    stores = []

    def done():
        for s in stores:
            s._db.close()
        next(schema, None)

    request.addfinalizer(done)
    name = "pg" + "-dsn"
    settings = PostgresSettings(kind="postgres", dsn_secret_name=name)
    for _ in range(count):
        stores.append(make("store", settings, FakeSecretProvider({name: dsn})))
    return stores


class Rig:
    """One implementer with what a test needs to look at it from outside."""

    def __init__(self, name, meter, clock, store=None):
        self.name, self.meter, self.clock, self.store = name, meter, clock, store
        self.is_limits = store is not None
        self.cap_reason = "daily_budget" if self.is_limits else "usd_cap"

    def booked(self, at=None):
        """What is booked: the day counter of `Limits` (on the pinned day), `spent` of the Budget."""
        if not self.is_limits:
            return self.meter.spent
        return self.store.spend_totals(AGENT, (at or self.clock[0]).date())[0]

    def month(self, at=None):
        return self.store.spend_totals(AGENT, (at or self.clock[0]).date())[1]

    def run(self):
        """A run id the meter can carry: a stored run for `Limits`, a plain id for the Budget."""
        if not self.is_limits:
            return "run-" + uuid.uuid4().hex
        run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
        self.store.create_run(run)
        return run.run_id

    def run_cost(self, run_id):
        return self.store.get_run(run_id).cost_usd

    def sweep(self, run_id):
        """Close what nobody settled: the expiry of the store (ii 10) or `forfeit` of the Budget (ticket W2)."""
        if not self.is_limits:
            return self.meter.forfeit(run_id)
        time.sleep(0.05)  # the row must be strictly older than the store's clock reading
        return self.store.expire_spend_reservations(0)


def _builder(request, tmp_path, monkeypatch, name):
    """A function `build(cap=WIDE, monthly=WIDE, wrap=None) -> Rig` for one implementer."""
    clock = [NOON]
    monkeypatch.setattr(limits_mod, "now", lambda: clock[0])
    if name == "budget":
        if not BUDGET_BUILT:
            pytest.skip(BUDGET_NOT_BUILT)
        return lambda cap=WIDE, monthly=WIDE, wrap=None: Rig(name, BUDGET(min(cap, monthly)), clock)
    real = MemoryStore() if name == "limits-memory" else _pg_stores(request, 1)[0]

    def build(cap=WIDE, monthly=WIDE, wrap=None):
        store = wrap(real) if wrap else real
        rig = Rig(name, Limits(store, Sink(), _registry(cap, monthly)), clock, store=real)
        rig.seen_by_meter = store
        return rig

    return build


@pytest.fixture(params=["limits-memory", "limits-postgres", "budget"])
def rig(request, tmp_path, monkeypatch):
    """Both implementers (`Limits` on each store, and the Budget)."""
    return _builder(request, tmp_path, monkeypatch, request.param)


@pytest.fixture(params=["limits-memory", "limits-postgres"])
def lim(request, tmp_path, monkeypatch):
    """`Limits` only: points that the interface or the ticket states for the store-backed meter alone."""
    return _builder(request, tmp_path, monkeypatch, request.param)


def _finding(request, impl, reason):
    """Mark this test as a strict expected failure for ONE implementer (the others must still pass)."""
    params = request.node.callspec.params
    if impl in (params.get("rig"), params.get("lim")):
        request.applymarker(pytest.mark.xfail(strict=True, reason=reason))


def _refused(meter, worst, *, agent=AGENT, run_id=None):
    """Reserve must refuse: returns the reason, after checking the type and the allowlist."""
    with pytest.raises(SpendRefused) as caught:
        meter.reserve(agent, worst, run_id=run_id)
    assert isinstance(caught.value, RuntimeError)
    assert caught.value.reason in REASONS, f"reason {caught.value.reason!r} is not one of the six"
    assert str(caught.value) == caught.value.reason
    return caught.value.reason


def _together(count, work):
    """Run work(i) on `count` threads that start behind one barrier; returns the results in thread order."""
    gate, out = threading.Barrier(count), [None] * count

    def one(i):
        gate.wait(WAIT_S)
        try:
            out[i] = work(i)
        except BaseException as exc:  # noqa: BLE001 - handed to the test thread
            out[i] = exc

    threads = [threading.Thread(target=one, args=(i,), daemon=True) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(WAIT_S)
    assert not any(t.is_alive() for t in threads), "a caller did not finish"
    return out


# --- the shape ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        "limits",
        pytest.param(  # core-b built the Budget meter by d0cac9693; the old "NOT BUILT N1" xfail is gone
            "budget",
            marks=pytest.mark.skipif(not BUDGET_BUILT, reason=BUDGET_NOT_BUILT),
        ),
    ],
)
def test_both_implementers_have_the_meter_shape(impl):
    """README section 2 "Two implementers, one shape"; ticket F-install line 8: reserve(agent_id, worst_usd, *,
    run_id=None) -> str and settle(reservation_id, actual_usd) -> Decimal."""
    cls = Limits if impl == "limits" else BUDGET
    assert cls is not None
    reserve = inspect.signature(cls.reserve).parameters
    assert list(reserve) == ["self", "agent_id", "worst_usd", "run_id"]
    assert (
        reserve["run_id"].kind is inspect.Parameter.KEYWORD_ONLY
        and reserve["run_id"].default is None
    )
    assert list(inspect.signature(cls.settle).parameters) == [
        "self",
        "reservation_id",
        "actual_usd",
    ]


# --- ii 1: an id only after the booking; every refusal means no model call and nothing booked -----------------------


def test_reserve_returns_an_id_only_after_the_worst_case_is_booked(rig):
    """ii 1: "reserve returns a reservation id only after the worst case is booked". The fake inner client reads
    the booking at the moment it is called."""
    r = rig(cap=D("1.00"))
    assert r.booked() == 0
    inner = Inner(D("0.25"), booked=r.booked)
    rid, reply, over = _gated(r.meter, inner, D("0.60"))
    assert isinstance(rid, str) and rid
    assert inner.calls == 1 and inner.seen == [D("0.60")]
    assert reply.cost_usd == D("0.25") and over == 0
    assert r.booked() == D("0.25")
    other, _, _ = _gated(r.meter, inner, D("0.10"))
    assert other != rid


def test_a_reserve_past_the_cap_is_refused_with_the_cap_reason_and_books_nothing(rig):
    """ii 1 and inv 2: daily_budget from `Limits`, usd_cap from the Budget (ticket V2); no model call."""
    r = rig(cap=D("1.00"))
    r.meter.reserve(AGENT, D("0.60"))
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, D("0.41"))
    assert caught.value.reason == r.cap_reason
    assert inner.calls == 0
    assert r.booked() == D("0.60")
    assert (
        _refused(r.meter, D("0.41")) == r.cap_reason
    )  # a refusal does not use the budget up either
    r.meter.reserve(AGENT, D("0.40"))
    assert r.booked() == D("1.00")


def test_the_month_cap_refuses_with_monthly_budget_and_books_nothing(lim):
    """ii 1: reason monthly_budget; inv 2: neither the day nor the month counter moves."""
    r = lim(cap=WIDE, monthly=D("1.00"))
    r.meter.reserve(AGENT, D("0.60"))
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, D("0.41"))
    assert caught.value.reason == "monthly_budget" and inner.calls == 0
    assert (r.booked(), r.month()) == (D("0.60"), D("0.60"))


def test_the_day_is_checked_before_the_month(lim):
    """Interface (i) table: "day checked first"; inv 5. Both caps would be passed: the reason is the day."""
    r = lim(cap=D("0.50"), monthly=D("0.50"))
    assert _refused(r.meter, D("0.60")) == "daily_budget"
    assert (r.booked(), r.month()) == (0, 0)


def test_a_stop_set_before_reserve_refuses_with_kill_switch_and_books_nothing(lim):
    """ii 1 (reason kill_switch) and ii 9: the stop state is read before the booking."""
    r = lim(cap=D("1.00"))
    r.store.set_kill_switch(KillSwitch(on=True, by="operator-1"))
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, D("0.60"))
    assert caught.value.reason == "kill_switch" and inner.calls == 0
    assert (r.booked(), r.month()) == (0, 0)
    assert _refused(r.meter, D(0)) == "kill_switch"  # a free call is stopped too


def test_a_stop_set_between_the_read_and_the_booking_lets_one_call_through(lim):
    """ii 9: "A stop set between the stop-state read and the booking lets that one call through; it takes
    effect at the next reserve." The stop is set by the wrapped store right after the first read."""
    r = lim(cap=D("1.00"), wrap=StopAfterRead)
    inner = Inner(D("0.10"))
    rid, _, over = _gated(r.meter, inner, D("0.30"))
    assert isinstance(rid, str) and inner.calls == 1 and over == 0
    assert r.store.get_kill_switch().on is True
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, D("0.30"))
    assert caught.value.reason == "kill_switch" and inner.calls == 1
    assert r.booked() == D("0.10")


ERRORS = {
    "runtime-error": RuntimeError("down"),
    "os-error": OSError("down"),
    "timeout": TimeoutError("down"),
    "key-error": KeyError("x"),  # must not be read as "unknown agent"
    "not-found": NotFound("x"),
    "value-error": ValueError("x"),  # must not be read as "bad amount"
}


@pytest.mark.parametrize("method", ["get_kill_switch", "reserve_spend"])
@pytest.mark.parametrize("error", sorted(ERRORS))
def test_a_store_that_cannot_be_asked_refuses_with_limits_unavailable(lim, method, error):
    """ii 1 and inv 8 (fail closed): any exception from the store or the stop-state read inside reserve is
    SpendRefused("limits_unavailable"); no error path returns an id, and nothing is booked."""
    r = lim(cap=D("1.00"), wrap=lambda real: Spy(real, fail={method: ERRORS[error]}))
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, D("0.60"))
    assert caught.value.reason == "limits_unavailable" and inner.calls == 0
    assert (r.booked(), r.month()) == (0, 0)
    assert r.seen_by_meter.calls.count("reserve_spend") <= 1  # one try, no retry inside the meter


def test_a_closed_database_connection_at_reserve_is_limits_unavailable(request, monkeypatch):
    """inv 8 with a real failure (PostgreSQL only): the connection of the meter's store is closed; a second
    connection shows that nothing was booked."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    broken, reader = _pg_stores(request, 2)
    meter = Limits(broken, Sink(), _registry(D("1.00"), WIDE))
    broken._db.close()
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(meter, inner, D("0.60"))
    assert caught.value.reason == "limits_unavailable" and inner.calls == 0
    assert reader.spend_totals(AGENT, NOON.date()) == (0, 0)


@pytest.mark.parametrize("amount", HOSTILE)
def test_a_hostile_amount_at_reserve_is_bad_amount_and_books_nothing(rig, amount):
    """ii 2: "exactly a Decimal, finite, 0 or more and below 1000000000"; inv 9 adds at most 12 decimal
    places. Anything else is SpendRefused("bad_amount") from both meters (ticket V2)."""
    r = rig(cap=WIDE)
    inner = Inner(D("0.10"))
    with pytest.raises(SpendRefused) as caught:
        _gated(r.meter, inner, amount)
    assert caught.value.reason == "bad_amount" and inner.calls == 0
    assert r.booked() == 0


def test_an_unknown_agent_is_a_key_error_and_books_nothing(lim):
    """ii 1: "An unknown agent raises KeyError (still no call)". Not for the Budget (ticket W7: no registry)."""
    r = lim(cap=D("1.00"))
    stranger = "agent-" + uuid.uuid4().hex[:8]
    for stop in (False, True):
        if stop:
            r.store.set_kill_switch(KillSwitch(on=True, by="operator-1"))
        with pytest.raises(KeyError) as caught:
            r.meter.reserve(stranger, D("0.10"))
        assert not isinstance(caught.value, SpendRefused)
        assert r.store.spend_totals(stranger, NOON.date()) == (0, 0)
    assert r.booked() == 0


@pytest.mark.parametrize("run_id", [7, 1.5, ("run",)], ids=["int", "float", "tuple"])
def test_a_reserve_that_is_refused_for_any_reason_books_nothing(lim, request, run_id):
    """ii 1 and inv 2, inv 8: reserve either returns an id with the worst case booked, or raises with nothing
    booked. A run id that is not text is not fixed by the interface (a store may take it or refuse it); what
    is fixed is that a refusal leaves no booking behind."""
    _finding(
        request,
        "limits-memory",
        "FINDING M1: Limits on the memory store refuses a reserve whose run_id is not text with "
        "limits_unavailable, but the worst case stays on the day and month counters with no reservation "
        "to settle or expire (MemoryStore.reserve_spend books before it builds the row; our F1 of the "
        "store run, still there at 7f8481795, now reachable through the meter)",
    )
    r = lim(cap=D("1.00"))
    try:
        rid = r.meter.reserve(AGENT, D("0.60"), run_id=run_id)
    except SpendRefused as exc:
        assert exc.reason in REASONS
        assert (r.booked(), r.month()) == (0, 0), "a refused reserve left money booked"
    else:
        assert isinstance(rid, str)
        assert r.booked() == D("0.60")


# --- ii 3: settle returns the overshoot from the stored row; the first settle wins -----------------------------------


@pytest.mark.parametrize(
    ("actual", "over"),
    [
        ("0", "0"),
        ("0.25", "0"),
        ("0.60", "0"),
        ("0.600000000001", "0.000000000001"),
        ("0.85", "0.25"),
    ],
)
def test_settle_returns_the_overshoot_and_books_the_real_cost(rig, actual, over):
    """ii 3: "settle returns the overshoot, max(0, settled minus reserved)"; inv 7: an overshoot is booked in
    full with no cap check (the cap here is exactly the reserved amount)."""
    r = rig(cap=D("0.60"))
    rid = r.meter.reserve(AGENT, D("0.60"))
    result = r.meter.settle(rid, D(actual))
    assert type(result) is D and result == D(over)
    assert r.booked() == D(actual)


@pytest.mark.parametrize(
    ("first", "second", "over"),
    [("0.25", "0.90", "0"), ("0.90", "0.25", "0.30"), ("0", "0.60", "0"), ("0.60", "0", "0")],
)
def test_settle_twice_the_first_call_wins(rig, first, second, over):
    """ii 3: "the first settle wins; a repeat with another amount returns the first result and changes
    nothing"; inv 3."""
    r = rig(cap=WIDE)
    rid = r.meter.reserve(AGENT, D("0.60"))
    assert r.meter.settle(rid, D(first)) == D(over)
    for amount in (second, first, second):
        assert r.meter.settle(rid, D(amount)) == D(over)
        assert r.booked() == D(first)


def test_settle_with_zero_frees_the_whole_reservation(rig):
    """ii 5: "Cost known (also 0 for a request that was refused before sending): settle(rid, cost)". After a
    settle at 0 the full cap can be reserved again."""
    r = rig(cap=D("1.00"))
    rid = r.meter.reserve(AGENT, D("1.00"))
    assert _refused(r.meter, SMALLEST) == r.cap_reason
    assert r.meter.settle(rid, D(0)) == 0
    assert r.booked() == 0
    r.meter.reserve(AGENT, D("1.00"))
    assert r.booked() == D("1.00")


# --- ii 4: unknown id and bad amounts at settle ----------------------------------------------------------------------


def test_settle_with_an_unknown_id_is_not_found_from_both_meters(rig):
    """ii 4: "settle with an unknown reservation id raises NotFound (a KeyError subclass) from both meters"."""
    r = rig(cap=WIDE)
    rid = r.meter.reserve(AGENT, D("0.60"))
    for unknown in ("res-" + uuid.uuid4().hex, rid + "x", ""):
        with pytest.raises(NotFound) as caught:
            r.meter.settle(unknown, D("0.10"))
        assert isinstance(caught.value, KeyError)
    assert r.booked() == D("0.60")
    assert r.meter.settle(rid, D("0.10")) == 0  # the known one is untouched and still open


@pytest.mark.parametrize("amount", HOSTILE)
def test_a_hostile_amount_at_settle_is_a_value_error_and_the_worst_case_stays(rig, amount):
    """ii 4: "settle with a bad amount raises ValueError"; inv 2: a failed settle leaves the row and the
    counters unchanged, so a later good settle still wins."""
    r = rig(cap=WIDE)
    rid = r.meter.reserve(AGENT, D("0.60"))
    with pytest.raises(ValueError) as caught:
        r.meter.settle(rid, amount)
    assert not isinstance(caught.value, SpendRefused)
    assert r.booked() == D("0.60")
    assert r.meter.settle(rid, D("0.25")) == 0
    assert r.booked() == D("0.25")


# --- ii 5 and ii 10: no settle keeps the worst case, before and after the sweep -------------------------------------


def test_without_a_settle_the_worst_case_stays_booked_also_after_the_sweep(rig):
    """ii 5: "do not settle ... keep the worst case booked"; ii 10 and inv 4: the sweep closes the reservation
    at its worst case, the booked amount stays and still counts against the cap."""
    r = rig(cap=D("1.00"))
    run_id = r.run()
    inner = Inner(D("0.10"))
    r.meter.reserve(AGENT, D("0.60"), run_id=run_id)
    inner.chat()  # the call was made, the process died before settle
    assert r.booked() == D("0.60")
    r.sweep(run_id)
    assert r.booked() == D("0.60")
    assert _refused(r.meter, D("0.41"), run_id=run_id) == r.cap_reason
    r.sweep(run_id)  # a second sweep changes nothing
    assert r.booked() == D("0.60")


@pytest.mark.parametrize(
    ("actual", "over", "booked"),
    [("0", "0", "0.60"), ("0.10", "0", "0.60"), ("0.60", "0", "0.60"), ("0.85", "0.25", "0.85")],
)
def test_a_settle_after_the_sweep_can_only_raise_the_booked_amount(rig, actual, over, booked):
    """ii 10: "a later settle can only raise the booked amount, never lower it"; README 2.3: the first settle
    of an expired row sets settled_usd = max(actual, reserved) and the run gets the real cost."""
    r = rig(cap=WIDE)
    run_id = r.run()
    rid = r.meter.reserve(AGENT, D("0.60"), run_id=run_id)
    r.sweep(run_id)
    assert r.meter.settle(rid, D(actual)) == D(over)
    assert r.booked() == D(booked)
    assert r.meter.settle(rid, D("0.99")) == D(over)  # and that settle was the first: it wins
    assert r.booked() == D(booked)
    if r.is_limits:
        assert r.run_cost(run_id) == D(actual)


def test_the_tick_step_expires_by_age_and_leaves_the_counters_alone(lim, monkeypatch):
    """ii 10: the expiry age is "the larger of 3600 seconds and the stuck-run age", closed "by a tick step".
    With the real age a fresh reservation is not touched (a lower settle still lowers the booking); with the
    default age set to 0 the step closes it at its worst case."""
    from hadavin_sdk import defaults
    from hadavin_sdk.runtime import tick

    r = lim(cap=WIDE)
    app = SimpleNamespace(store=r.store, registry=SimpleNamespace(agents={}))
    ctx = SimpleNamespace(app=app, now=NOON, results={})
    assert tick.reservation_expire_s(app) == max(3600, defaults.RESERVATION_EXPIRE_S)
    assert "expire_reservations" in [step.name for step in tick.STEPS]
    fresh = r.meter.reserve(AGENT, D("0.60"))
    tick.expire_reservations(ctx)
    assert r.meter.settle(fresh, D("0.10")) == 0
    assert r.booked() == D("0.10")
    old = r.meter.reserve(AGENT, D("0.60"))
    time.sleep(0.05)
    monkeypatch.setattr(defaults, "RESERVATION_EXPIRE_S", 0)
    tick.expire_reservations(ctx)
    assert r.booked() == D("0.70")
    assert r.meter.settle(old, D("0.10")) == 0
    assert r.booked() == D("0.70")  # 0.10 settled plus the 0.60 that expired: never lower


# --- ii 6: the store is down at settle --------------------------------------------------------------------------------


@pytest.mark.parametrize("error", ["runtime-error", "os-error", "timeout"])
def test_a_store_that_is_down_at_settle_raises_and_the_worst_case_stays(lim, error):
    """ii 6: "If settle raises (store down after the call), return the reply anyway; the worst case stays
    booked. Never retry reserve." The interface names no exception type: the store's own error reaches the
    caller, it is not turned into a refusal or into NotFound, and the meter asks the store once."""
    down = ERRORS[error]
    r = lim(cap=D("1.00"), wrap=lambda real: Spy(real, fail={"settle_spend": down}))
    inner = Inner(D("0.10"))
    rid, reply, over = _gated(r.meter, inner, D("0.60"))
    assert reply.cost_usd == D("0.10") and inner.calls == 1
    assert over is down
    assert r.booked() == D("0.60")
    calls = r.seen_by_meter.calls
    assert calls.count("reserve_spend") == 1 and calls.count("settle_spend") == 1
    assert Limits(r.store, Sink(), _registry(WIDE, WIDE)).settle(rid, D("0.10")) == 0  # still open


def test_a_closed_database_connection_at_settle_raises_and_the_worst_case_stays(
    request, monkeypatch
):
    """ii 6 with a real failure (PostgreSQL only): the connection dies between the call and the settle. Seen
    from a second connection the worst case is still booked and the reservation is still open."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    broken, reader = _pg_stores(request, 2)
    meter = Limits(broken, Sink(), _registry(D("1.00"), WIDE))
    rid = meter.reserve(AGENT, D("0.60"))
    broken._db.close()
    with pytest.raises(Exception) as caught:
        meter.settle(rid, D("0.10"))
    assert not isinstance(caught.value, SpendRefused | KeyError | ValueError), type(caught.value)
    assert reader.spend_totals(AGENT, NOON.date()) == (D("0.60"), D("0.60"))
    assert Limits(reader, Sink(), _registry(WIDE, WIDE)).settle(rid, D("0.10")) == 0
    assert reader.spend_totals(AGENT, NOON.date()) == (D("0.10"), D("0.10"))


# --- ii 8: the settled cost goes to the run exactly once -------------------------------------------------------------


def test_the_settled_cost_is_added_to_the_run_exactly_once(lim):
    """ii 8 and inv 13: "The settled cost is added to the run's cost by the store (when run_id was given)":
    nothing at reserve, the real cost at the first settle (an overshoot in full), nothing at a repeat."""
    r = lim(cap=WIDE)
    run_id, other = r.run(), r.run()
    first = r.meter.reserve(AGENT, D("0.60"), run_id=run_id)
    second = r.meter.reserve(AGENT, D("0.60"), run_id=run_id)
    loose = r.meter.reserve(AGENT, D("0.60"))  # no run: only the counters move
    assert r.run_cost(run_id) == 0
    r.meter.settle(first, D("0.25"))
    assert r.run_cost(run_id) == D("0.25")
    r.meter.settle(first, D("0.50"))
    r.meter.settle(first, D("0.25"))
    assert r.run_cost(run_id) == D("0.25")
    assert r.meter.settle(second, D("0.85")) == D("0.25")
    r.meter.settle(loose, D("0.40"))
    assert r.run_cost(run_id) == D("1.10")
    assert r.run_cost(other) == 0
    assert r.booked() == D("1.50")


# --- caps: exact arithmetic, the edge, zero ---------------------------------------------------------------------------


def test_the_cap_is_exact_decimal_arithmetic(rig):
    """inv 9 "nothing is rounded" and inv 1: three times 0.1 fits a cap of 0.3 exactly (binary floats would
    refuse the third), the smallest amount above it does not."""
    r = rig(cap=D("0.3"))
    for _ in range(3):
        r.meter.reserve(AGENT, D("0.1"))
    assert r.booked() == D("0.3")
    assert _refused(r.meter, SMALLEST) == r.cap_reason
    assert r.booked() == D("0.3")


def test_twelve_decimal_places_are_booked_unrounded(rig):
    """inv 9: at most 12 decimal places, nothing is rounded."""
    r = rig(cap=D("1.00"))
    rid = r.meter.reserve(AGENT, SMALLEST)
    assert r.booked() == SMALLEST
    r.meter.reserve(AGENT, D("1.00") - SMALLEST)
    assert r.booked() == D("1.00")
    assert r.meter.settle(rid, SMALLEST * 3) == SMALLEST * 2
    assert r.booked() == D("1.00") + SMALLEST * 2


def test_a_cap_reached_exactly_refuses_even_a_zero_amount(lim):
    """README 2.3: "a zero amount at the cap is refused"; below the cap a zero amount is granted."""
    r = lim(cap=D("1.00"))
    free = r.meter.reserve(AGENT, D(0))
    assert isinstance(free, str)
    r.meter.reserve(AGENT, D("0.40"))
    r.meter.reserve(AGENT, D("0.60"))
    assert r.booked() == D("1.00")
    assert _refused(r.meter, D(0)) == "daily_budget"
    assert _refused(r.meter, SMALLEST) == "daily_budget"


@pytest.mark.parametrize(
    ("daily", "monthly", "reason"),
    [("0", "100", "daily_budget"), ("100", "0", "monthly_budget"), ("0", "0", "daily_budget")],
)
def test_a_cap_of_zero_refuses_every_call(lim, daily, monthly, reason):
    """README 2.3 (a zero amount at the cap is refused): a budget of zero grants nothing, not even a free
    call. Not for the Budget: its cap must be above zero (ticket W6)."""
    r = lim(cap=D(daily), monthly=D(monthly))
    for worst in (D(0), SMALLEST, D("0.10")):
        assert _refused(r.meter, worst) == reason
    assert (r.booked(), r.month()) == (0, 0)


def test_the_month_cap_holds_across_the_days_of_a_month_and_a_new_month_is_free(lim):
    """inv 5 and inv 6: the month counter is the month of the reserve day; the next month starts at zero."""
    r = lim(cap=D("1.00"), monthly=D("1.50"))
    r.meter.reserve(AGENT, D("1.00"))
    r.clock[0] = NOON + timedelta(days=1)
    assert r.booked() == 0  # a new day
    assert _refused(r.meter, D("0.60")) == "monthly_budget"
    r.meter.reserve(AGENT, D("0.50"))
    assert (r.booked(), r.month()) == (D("0.50"), D("1.50"))
    r.clock[0] = datetime(YEAR, 4, 1, 0, 0, tzinfo=UTC)
    r.meter.reserve(AGENT, D("1.00"))
    assert (r.booked(), r.month()) == (D("1.00"), D("1.00"))
    assert r.month(NOON) == D("1.50")


def test_the_day_is_fixed_at_reserve_time_and_a_settle_after_midnight_moves_that_day(lim):
    """inv 6 (midnight rule): "the day is the UTC date at reserve time, stored in the row; settle and expire
    act on that stored day and its month". Clock seam: the `now` name of hadavin_sdk.limits."""
    r = lim(cap=D("1.00"), monthly=D("1.00"))
    late = datetime(YEAR, 1, 31, 23, 59, 59, 999999, tzinfo=UTC)
    r.clock[0] = late
    run_id = r.run()
    rid = r.meter.reserve(AGENT, D("1.00"), run_id=run_id)
    after = late + timedelta(microseconds=1)
    r.clock[0] = after
    assert (after.month, after.day) == (2, 1)
    assert (r.booked(), r.month()) == (0, 0)  # the first of February starts empty
    held = r.meter.reserve(AGENT, D("0.70"))
    assert r.meter.settle(rid, D("0.25")) == 0
    assert (r.booked(late), r.month(late)) == (D("0.25"), D("0.25"))
    assert (r.booked(after), r.month(after)) == (D("0.70"), D("0.70"))
    assert r.run_cost(run_id) == D("0.25")
    r.clock[0] = late  # back on the old day the freed 0.75 can be reserved, and no more
    assert _refused(r.meter, D("0.76")) == "daily_budget"
    r.meter.reserve(AGENT, D("0.75"))
    r.clock[0] = after
    assert r.meter.settle(held, D("0.90")) == D("0.20")
    assert (r.booked(after), r.month(after)) == (D("0.90"), D("0.90"))


# --- concurrency: inv 1 through the meter ----------------------------------------------------------------------------


def _grants(outcomes, reason):
    ids = [o for o in outcomes if isinstance(o, str)]
    refused = [o for o in outcomes if isinstance(o, SpendRefused)]
    assert len(ids) + len(refused) == len(outcomes), [o for o in outcomes if o not in ids + refused]
    assert {o.reason for o in refused} <= {reason}
    assert len(set(ids)) == len(ids)
    return ids


def test_threads_through_one_limits_on_the_memory_store_get_exactly_three_grants(monkeypatch):
    """inv 1 through `Limits.reserve`: cap 3 x amount, 16 threads on one meter: exactly 3 ids, 13 refusals
    with daily_budget, and 3 x amount booked."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    store = MemoryStore()
    meter = Limits(store, Sink(), _registry(D("3.00"), WIDE))
    outcomes = _together(CALLERS, lambda i: meter.reserve(AGENT, D("1.00")))
    assert len(_grants(outcomes, "daily_budget")) == 3
    assert store.spend_totals(AGENT, NOON.date()) == (D("3.00"), D("3.00"))


@pytest.mark.parametrize(
    ("daily", "monthly", "reason"),
    [("3.00", "1000", "daily_budget"), ("1000", "3.00", "monthly_budget")],
)
def test_connections_through_limits_on_postgres_get_exactly_three_grants(
    request, monkeypatch, daily, monthly, reason
):
    """inv 1 through `Limits.reserve` on PostgreSQL: 16 meters on 16 connections of the runtime login, cap
    3 x amount: exactly 3 ids, the others refused with the reason of the cap that binds."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    stores = _pg_stores(request, CALLERS + 1)
    reader = stores.pop()
    pids = {s._db.execute("SELECT pg_backend_pid()").fetchone()[0] for s in stores}
    assert len(pids) == CALLERS, "the callers do not have a connection each"
    registry = _registry(D(daily), D(monthly))
    meters = [Limits(s, Sink(), registry) for s in stores]
    outcomes = _together(CALLERS, lambda i: meters[i].reserve(AGENT, D("1.00")))
    assert len(_grants(outcomes, reason)) == 3
    assert reader.spend_totals(AGENT, NOON.date()) == (D("3.00"), D("3.00"))


def test_threads_on_one_budget_get_exactly_floor_cap_over_amount_grants():
    """Ticket U6 "a lock" and its test E8: 16 threads on one Budget with cap 3.50 and amount 1.00: exactly
    floor(3.50 / 1.00) = 3 ids, the others refused with usd_cap, 3.00 held."""
    if not BUDGET_BUILT:
        pytest.skip(BUDGET_NOT_BUILT)
    meter = BUDGET(D("3.50"))
    amount = D("1.00")
    outcomes = _together(CALLERS, lambda i: meter.reserve(AGENT, amount))
    assert len(_grants(outcomes, "usd_cap")) == math.floor(D("3.50") / amount)
    assert meter.spent == D("3.00")


def _settle_race(meters, store, run_id, rid):
    amounts = [
        D("0.10") * (i + 1) for i in range(len(meters))
    ]  # 0.10 .. 1.60 against 0.60 reserved
    outcomes = _together(len(meters), lambda i: meters[i].settle(rid, amounts[i]))
    assert all(type(o) is D for o in outcomes), outcomes
    assert len(set(outcomes)) == 1, (
        f"settles of one reservation returned different results: {outcomes}"
    )
    winner = store.get_run(run_id).cost_usd
    assert winner in amounts
    assert outcomes[0] == max(D(0), winner - D("0.60"))
    assert store.spend_totals(AGENT, NOON.date()) == (winner, winner)


def test_threads_settling_one_reservation_on_the_memory_store_apply_it_once(monkeypatch):
    """ii 3 and inv 3 under threads: 16 settles of one reservation with 16 amounts: every caller gets the
    result of the one that won, the counters and the run's cost carry that one amount."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    store = MemoryStore()
    meter = Limits(store, Sink(), _registry(WIDE, WIDE))
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    rid = meter.reserve(AGENT, D("0.60"), run_id=run.run_id)
    _settle_race([meter] * CALLERS, store, run.run_id, rid)
    assert len(meter.audit.outcomes) <= 1  # an overshoot is audited once, by the winner


def test_connections_settling_one_reservation_on_postgres_apply_it_once(request, monkeypatch):
    """ii 3, ii 8 and inv 3 on PostgreSQL: 16 connections settle one reservation with 16 amounts."""
    monkeypatch.setattr(limits_mod, "now", lambda: NOON)
    stores = _pg_stores(request, CALLERS + 1)
    reader = stores.pop()
    registry = _registry(WIDE, WIDE)
    meters = [Limits(s, Sink(), registry) for s in stores]
    run = Run(agent_id=AGENT, principal_id="p", trigger_kind="event", trigger_ref="t")
    reader.create_run(run)
    rid = meters[0].reserve(AGENT, D("0.60"), run_id=run.run_id)
    _settle_race(meters, reader, run.run_id, rid)
    assert sum(len(m.audit.outcomes) for m in meters) <= 1


# --- the Budget and the stop state ------------------------------------------------------------------------------------


def test_the_budget_does_not_read_the_stop_state():
    """ii 9: "The Budget meter (command-line eval and replay) does not read the stop state." It is built from
    its cap alone (no store to read a stop from), and grants while a store nearby is stopped."""
    if not BUDGET_BUILT:
        pytest.skip(BUDGET_NOT_BUILT)
    required = [
        p.name
        for p in list(inspect.signature(BUDGET.__init__).parameters.values())[1:]
        if p.default is inspect.Parameter.empty
    ]
    assert len(required) == 1, f"the Budget needs more than its cap: {required}"
    store = MemoryStore()
    store.set_kill_switch(KillSwitch(on=True, by="operator-1"))
    meter = BUDGET(D("1.00"))
    assert not any(hasattr(meter, name) for name in ("store", "get_kill_switch", "registry"))
    rid = meter.reserve(AGENT, D("0.60"))
    assert isinstance(rid, str) and meter.settle(rid, D("0.25")) == 0


# --- one table of scenarios, the same for every implementer -----------------------------------------------------------

ID, CAP = "id", "refused:cap"
# Each step: (what, key, amount) -> (outcome, booked afterwards). The cap is 1.00 for every scenario.
SCENARIOS = {
    "grant-then-settle-lower": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("settle", "a", D("0.25")), (D(0), D("0.25"))),
    ],
    "overshoot-is-booked-in-full-and-counts-against-the-cap": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("settle", "a", D("0.85")), (D("0.25"), D("0.85"))),
        (("reserve", "b", D("0.20")), (CAP, D("0.85"))),
        (("reserve", "c", D("0.15")), (ID, D("1.00"))),
    ],
    "an-overshoot-past-the-cap-refuses-the-next-call": [
        (("reserve", "a", D("0.90")), (ID, D("0.90"))),
        (("settle", "a", D("1.50")), (D("0.60"), D("1.50"))),
        (("reserve", "b", D("0.10")), (CAP, D("1.50"))),
    ],
    "settle-twice-lower-then-higher": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("settle", "a", D("0.25")), (D(0), D("0.25"))),
        (("settle", "a", D("0.90")), (D(0), D("0.25"))),
    ],
    "settle-twice-higher-then-zero": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("settle", "a", D("0.90")), (D("0.30"), D("0.90"))),
        (("settle", "a", D(0)), (D("0.30"), D("0.90"))),
    ],
    "the-cap-reached-exactly": [
        (("reserve", "a", D("0.40")), (ID, D("0.40"))),
        (("reserve", "b", D("0.60")), (ID, D("1.00"))),
        (("reserve", "c", SMALLEST), (CAP, D("1.00"))),
    ],
    "refused-then-freed-by-a-settle-at-zero": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("reserve", "b", D("0.60")), (CAP, D("0.60"))),
        (("settle", "a", D(0)), (D(0), D(0))),
        (("reserve", "b", D("0.60")), (ID, D("0.60"))),
    ],
    "bad-amounts-change-nothing": [
        (("reserve", "a", D("-1")), ("refused:bad_amount", D(0))),
        (("reserve", "a", 0.5), ("refused:bad_amount", D(0))),
        (("reserve", "a", D("0.50")), (ID, D("0.50"))),
        (("settle", "a", D("NaN")), ("ValueError", D("0.50"))),
        (("settle", "a", True), ("ValueError", D("0.50"))),
        (("settle", "a", D("0.10")), (D(0), D("0.10"))),
    ],
    "an-unknown-id": [
        (("settle", "never-reserved", D("0.10")), ("NotFound", D(0))),
        (("reserve", "a", D("0.50")), (ID, D("0.50"))),
        (("settle", "never-reserved", D("0.10")), ("NotFound", D("0.50"))),
    ],
    "a-free-call-that-cost-something": [
        (("reserve", "a", D(0)), (ID, D(0))),
        (("settle", "a", D("0.30")), (D("0.30"), D("0.30"))),
    ],
    "swept-then-settled-lower": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("sweep", None, None), (None, D("0.60"))),
        (("settle", "a", D("0.10")), (D(0), D("0.60"))),
    ],
    "swept-then-settled-higher": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("sweep", None, None), (None, D("0.60"))),
        (("settle", "a", D("0.90")), (D("0.30"), D("0.90"))),
        (("settle", "a", D("0.10")), (D("0.30"), D("0.90"))),
    ],
    "swept-money-still-counts-against-the-cap": [
        (("reserve", "a", D("0.60")), (ID, D("0.60"))),
        (("sweep", None, None), (None, D("0.60"))),
        (("reserve", "b", D("0.60")), (CAP, D("0.60"))),
    ],
}


def _play(r, steps):
    """Run the steps through one implementer; outcomes are put in the words of the table."""
    run_id, ids, seen = r.run(), {}, []
    for what, key, amount in steps:
        outcome = None
        try:
            if what == "reserve":
                ids[key] = r.meter.reserve(AGENT, amount, run_id=run_id)
                outcome = ID if isinstance(ids[key], str) and ids[key] else repr(ids[key])
            elif what == "settle":
                outcome = r.meter.settle(ids.get(key, "res-" + key), amount)
            else:
                r.sweep(run_id)
        except SpendRefused as exc:
            caps = ("daily_budget", "monthly_budget", "usd_cap")
            outcome = CAP if exc.reason in caps else "refused:" + exc.reason
        except NotFound:
            outcome = "NotFound"
        except ValueError:
            outcome = "ValueError"
        seen.append((outcome, r.booked()))
    return seen


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_every_implementer_gives_the_outcomes_of_the_shared_table(rig, name):
    """README section 2: "one shape ... The gate takes the meter as a constructor argument and must not test
    which one it got." One list of scenarios with the outcome each step must have under ii 1 to ii 5, ii 10 and
    inv 7; every implementer is held to the same list, so two that pass agree with each other. The cap
    reasons (daily_budget, usd_cap) are one outcome here, the only difference the interface allows."""
    steps = SCENARIOS[name]
    seen = _play(rig(cap=D("1.00")), [step for step, _ in steps])
    assert seen == [expected for _, expected in steps]
