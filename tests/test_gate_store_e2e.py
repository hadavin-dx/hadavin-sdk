"""Gate end to end with the REAL store: `ModelGate` (guard/model_gate.py, core-c) -> `Limits` (limits.py) ->
`PostgresStore` reserve/settle (core-b, migration 0007) on a real PostgreSQL. Written on the scratch merge of
origin/cloud/core-b and origin/cloud/core-c (branch wip/cloud-core-c/p3-scratch). Needs HADAVIN_TEST_PG_DSN; skipped
without it. Findings F1 and F2 are in handover/core-c/evidence/P3-notes.md; the strict xfails below name them."""

from __future__ import annotations

import os
import threading
from decimal import Decimal
from types import SimpleNamespace

import psycopg
import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.model_gate import SPEND_REASONS, ModelGate
from hadavin_sdk.limits import Budget, Limits, SpendRefused
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.models import KillSwitch, Reply, now
from tests.contracts.kinds.store_postgres import pg_schema

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
D = Decimal
AGENT = "agent-e2e"
WORST = D("0.40")
SECRET = "password=Zx9qPlantedSecret77"  # noqa: S105 - a planted test value


class Sink:
    def __init__(self):
        self.rows = []
        self._lock = threading.Lock()

    def write_intent(self, event):
        pass

    def write_outcome(self, event):
        with self._lock:
            self.rows.append(event)


class Provider:
    def __init__(self, reply=None, exc=None):
        self.reply, self.exc, self.calls = reply, exc, 0

    def chat(self, messages, **kw):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.reply


def reply(cost="0.12", text="ok"):
    return Reply(text=text, cost_usd=D(cost), model_id="m")


class ForGate:
    """What the gate's `Meter` protocol calls (`settle(id, usd)`), mapped onto the real `Limits.settle_for`."""

    def __init__(self, limits):
        self.limits = limits

    def reserve(self, agent_id, worst, *, run_id=None):
        return self.limits.reserve(agent_id, worst, run_id=run_id)

    def settle(self, rid, usd):
        return self.limits.settle_for(AGENT, rid, usd)


def registry(daily="1.00", monthly="100.00"):
    budget = SimpleNamespace(daily=D(daily), monthly=D(monthly))
    return SimpleNamespace(agents={AGENT: SimpleNamespace(budget_usd=budget)})


class World:
    def __init__(self, dsn, daily="1.00", monthly="100.00"):
        self.dsn = dsn
        self.stores = []
        self.sink = Sink()
        self.registry = registry(daily, monthly)
        self.store = self.new_store()
        self.limits = Limits(self.store, self.sink, self.registry)

    def new_store(self):
        store = make(
            "store",
            PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"),  # noqa: S106 - a name
            FakeSecretProvider({"pg-dsn": self.dsn}),
        )
        self.stores.append(store)
        return store

    def gate(self, llm, meter=None, worst=WORST, limits=None, sink=None):
        meter = meter if meter is not None else ForGate(limits or self.limits)
        gate = ModelGate(
            llm, meter=meter, audit=sink or self.sink, worst_case=lambda *a: worst
        )
        return gate.bind(AGENT, "run-e2e", mapping=runmap.RunMap())

    def rows(self):
        with psycopg.connect(self.dsn, autocommit=True) as db:
            return db.execute(
                "SELECT status, reserved_usd, settled_usd FROM spend_reservations ORDER BY created_at"
            ).fetchall()

    def day(self):
        return self.store.spend_totals(AGENT, now().date())[0]

    def codes(self):
        return [(r.result, r.error_code) for r in self.sink.rows]


@pytest.fixture(name="w")
def world():
    for dsn in pg_schema():
        w = World(dsn)
        try:
            yield w
        finally:
            for s in w.stores:
                s._db.close()


def call(gate):
    return gate.chat([{"role": "user", "content": "hello"}], system="s", route="r")


def test_normal_call_reserves_then_settles_at_the_real_cost(w):
    out = call(w.gate(Provider(reply("0.12"))))
    assert out.cost_usd == D("0.12")
    assert [(s, D(r), D(x)) for s, r, x in w.rows()] == [("settled", WORST, D("0.12"))]
    assert w.day() == D("0.12")
    assert w.codes() == [("ok", None)]


@pytest.mark.xfail(
    strict=True,
    reason="F1: the gate calls meter.settle(id, usd) but Limits.settle needs agent_id (TypeError, caught as "
    "settle_failed); the real Limits cannot be the gate's meter as built",
)
def test_real_limits_as_the_meter_settles(w):
    call(w.gate(Provider(reply("0.12")), meter=w.limits))
    assert [s for s, _, _ in w.rows()] == ["settled"]
    assert w.day() == D("0.12")


def test_real_limits_as_the_meter_keeps_the_worst_case_booked_not_lost(w):
    """The F1 failure is at least safe: the reply is returned and the worst case stays booked (no under-count)."""
    out = call(w.gate(Provider(reply("0.12")), meter=w.limits))
    assert out.cost_usd == D("0.12")
    assert [s for s, _, _ in w.rows()] == ["open"]
    assert w.day() == WORST
    assert w.codes() == [("ok", "settle_failed")]


def test_refused_before_response_exhausted_settles_at_zero(w):
    exc = ProviderExhausted("all refused")
    exc.refused_before_response = True
    with pytest.raises(ProviderExhausted):
        call(w.gate(Provider(exc=exc)))
    assert [(s, D(x)) for s, _, x in w.rows()] == [("settled", D(0))]
    assert w.day() == D(0)
    assert w.codes() == [("failed", "provider_refused")]


def test_unmarked_exhausted_keeps_the_worst_case_booked(w):
    with pytest.raises(ProviderExhausted):
        call(w.gate(Provider(exc=ProviderExhausted("throttled"))))
    assert [s for s, _, _ in w.rows()] == ["open"]  # closed later by the sweep, at the worst case
    assert w.day() == WORST  # never under-counted
    assert w.codes() == [("failed", "provider_exhausted")]


def test_unmarked_provider_error_keeps_the_worst_case_booked(w):
    with pytest.raises(ProviderError):
        call(w.gate(Provider(exc=ProviderError("bad key"))))
    assert w.day() == WORST and [s for s, _, _ in w.rows()] == ["open"]


class Down:
    """A store whose reserve is unreachable."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        if name == "reserve_spend":

            def boom(*a, **k):
                raise psycopg.OperationalError("down")

            return boom
        return getattr(self._real, name)


def _refusal_case(w, reason):
    """(meter, worst) that makes the real stack refuse with `reason`."""
    worst = WORST
    if reason == "kill_switch":
        w.store.set_kill_switch(KillSwitch(on=True, by="t"))
    elif reason == "daily_budget":
        w.limits.charge(AGENT, D("0.90"))
    elif reason == "monthly_budget":
        w2 = World(w.dsn, daily="50.00", monthly="0.50")
        w.stores.extend(w2.stores)
        w.limits = w2.limits
        w.limits.charge(AGENT, D("0.30"))
    elif reason == "limits_unavailable":
        w.limits = Limits(Down(w.store), w.sink, w.registry)
    elif reason == "bad_amount":
        worst = D("0.0000000000001")  # 13 decimals: a usable amount for the gate, refused by the store's rule
    elif reason == "usd_cap":
        return ForBudget(Budget(D("0.10"))), worst
    return ForGate(w.limits), worst


class ForBudget:
    def __init__(self, budget):
        self.budget = budget

    def reserve(self, agent_id, worst, *, run_id=None):
        return self.budget.reserve(agent_id, worst, run_id=run_id)

    def settle(self, rid, usd):
        return self.budget.settle(rid, usd, agent_id=AGENT)


@pytest.mark.parametrize("reason", sorted(SPEND_REASONS))
def test_spend_refusal_is_audited_with_its_reason_and_leaves_no_reservation(w, reason):
    meter, worst = _refusal_case(w, reason)
    provider = Provider(reply())
    before = w.day()
    with pytest.raises(SpendRefused) as err:
        call(w.gate(provider, meter=meter, worst=worst))
    assert err.value.reason == reason
    assert provider.calls == 0
    assert w.codes() == [("refused", reason)]
    assert [s for s, _, _ in w.rows() if s == "open"] == []  # no open reservation
    assert w.rows() == []  # and no row at all
    assert w.day() == before


def test_all_reasons_are_covered():
    assert SPEND_REASONS == {
        "kill_switch",
        "daily_budget",
        "monthly_budget",
        "limits_unavailable",
        "bad_amount",
        "usd_cap",
    }


def test_reply_with_a_planted_secret_is_not_stored_and_the_reservation_is_settled(w):
    out = call(w.gate(Provider(reply("0.05", text=f"use {SECRET} now"))))
    assert out.cost_usd == D("0.05")
    assert [s for s, _, _ in w.rows()] == ["settled"] and w.day() == D("0.05")
    everything = repr([r.model_dump() for r in w.sink.rows]) + repr(w.rows())
    assert "Zx9qPlantedSecret77" not in everything
    with psycopg.connect(w.dsn, autocommit=True) as db:  # nor in any table the call touched
        for table in ("spend_reservations", "spend", "spend_month"):
            assert "Zx9qPlantedSecret77" not in repr(db.execute(f"SELECT * FROM {table}").fetchall())  # noqa: S608


@pytest.mark.xfail(
    strict=True,
    reason="F2: the gate masks what it SENDS, not what the model returns; the reply comes back as the client "
    "gave it (the run's own redaction, runmap.redact_text, is the caller's step)",
)
def test_reply_with_a_planted_secret_is_not_returned_unmasked(w):
    out = call(w.gate(Provider(reply("0.05", text=f"use {SECRET} now"))))
    assert "Zx9qPlantedSecret77" not in out.text


def test_concurrent_calls_cannot_overspend_the_budget(w):
    n = 8  # 8 x 0.40 against a 1.00 day cap: at most two may be admitted
    workers = [w.new_store() for _ in range(n)]
    results, lock = [], threading.Lock()
    start = threading.Barrier(n)

    def run(store):
        gate = w.gate(Provider(reply("0.40")), limits=Limits(store, w.sink, w.registry))
        start.wait()
        try:
            call(gate)
            outcome = "ok"
        except SpendRefused as exc:
            outcome = exc.reason
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=run, args=(s,)) for s in workers]
    [t.start() for t in threads]
    [t.join(60) for t in threads]
    assert len(results) == n
    assert results.count("ok") == 2 and results.count("daily_budget") == n - 2
    assert w.day() == D("0.80") <= D("1.00")
    assert [s for s, _, _ in w.rows()] == ["settled", "settled"]


@pytest.mark.parametrize("exc", [KeyboardInterrupt(), SystemExit(1), GeneratorExit()])
def test_interrupt_in_the_provider_leaves_the_worst_case_booked(w, exc):
    with pytest.raises(type(exc)):
        call(w.gate(Provider(exc=exc)))
    assert [s for s, _, _ in w.rows()] == ["open"]  # swept later at the worst case, never released
    assert w.day() == WORST
    assert w.codes() == [("failed", "call_interrupted")]
