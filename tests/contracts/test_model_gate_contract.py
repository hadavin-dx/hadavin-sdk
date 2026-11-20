"""Contract test for the model gate (`hadavin_sdk.guard.model_gate`), written by a reader who did not build it.

Sources, and nothing else: the gate ticket (handover/core-c/tickets/F-gate-wrapper-body.md: invariants I1 to I15
with Amendment 1), INTERFACE (ii) (handover/core-a/inputs/interfaces-from-core-b/README.md section 2: contract
points 1 to 10, and ii_meter.py) and the code review of the gate (inputs/review-code-F-gate-1: Majors M1 to M4).
Every test names the invariant, the contract point or the Major it stands for.

Overlap with the builder's own tests/test_model_gate.py, and where this file differs:
- Same ground: T1 (order), T2 (reply unchanged), T3 (settle amount), T12 (reserve raises), T13 and T14 (failed
  call not settled), T15 (threads), T17 (raising sink), T18 (no text in rows or logs), T19 (no `chat` unbound),
  the m5 cases (unusable cost) and `test_worst_case_is_computed_on_the_enforced_copies`.
- Different here: every test runs against TWO meter doubles of unrelated shape, and both doubles refuse a bad
  amount as a real meter must (the builder's double accepts anything); the order is one event log that also holds
  the worst-case step, and the inner client checks the open reservation from INSIDE its call; point 10 is tested
  with the formula of the interface text (bytes at the input price, max_tokens at the output price, times the
  attempts) under a Decimal context that traps every inexact step, against a client that bills at random within
  those limits; the thread test pairs each reservation id with the cost of ITS OWN call; the source guards walk
  the whole module tree (Major M1) and do not share a helper with the builder's guard.
- Not repeated here: the replace rules of `runmap.enforce_map` and their stated limits (T5 to T10, the b1 cases,
  tests/test_runmap_enforce_map.py), the audit row field list, and the mutant script itself.

The module does not exist on every branch yet: the file is skipped as a whole where it is missing. No network,
no database, no model call: the inner client is a double."""

from __future__ import annotations

import ast
import copy
import importlib
import inspect
import itertools
import json
import logging
import random
import threading
import time
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

model_gate = pytest.importorskip(
    "hadavin_sdk.guard.model_gate",
    reason="the model gate (step F) is not on this branch yet: hadavin_sdk.guard.model_gate is missing",
)

ModelGate = model_gate.ModelGate
Reply = model_gate.Reply
ProviderError = model_gate.ProviderError
ProviderExhausted = model_gate.ProviderExhausted
# core-c ORDER 017 item 1 (handover/core-c/requests/3-bind-mapping-required.md): `bind` has a REQUIRED keyword
# `mapping`; "no run map" is said with the constant NO_MAP (before: `mapping=None`, or left out). Older heads have
# no NO_MAP and take None, so the same cases run on both.
NO_MAP = getattr(model_gate, "NO_MAP", None)
# core-c ORDER 017 item 5 (same request file, section 3): every failure BEFORE the provider call that is not a
# SpendRefused is raised as `GateRefused` (a code and nothing else: no text, no cause, no context). Older heads let
# the original error through; `None` here means "this head has no GateRefused": the original error comes out.
GateRefused = getattr(model_gate, "GateRefused", None)


def _refusal_of(error: BaseException):
    """The exception the gate must raise for an error of the worst-case step or of `reserve`: the very same
    object where the head passes it on (a SpendRefused, a BaseException that is not an Exception, any error on a
    head without GateRefused), else a `GateRefused` that holds only its code."""
    if GateRefused is None or not isinstance(error, Exception) or hasattr(error, "reason"):
        return type(error)
    return GateRefused


def _assert_code_only(error: BaseException, code: str) -> None:
    """A GateRefused carries its code and nothing else: no text, no secret, no cause, no context."""
    assert isinstance(error, GateRefused)
    assert error.code == code and error.args == (code,)
    assert error.__cause__ is None and error.__context__ is None


REASONS = ("kill_switch", "daily_budget", "monthly_budget", "limits_unavailable", "bad_amount")
AGENT = "agent-" + "a1"
RUN = "run-" + "r1"
ROUTE = "main"
MODEL = "fake-" + "model"
WORST = Decimal("0.2500")
COST = Decimal("0.012345678901")
HELLO = [{"role": "user", "content": "say hello"}]
# marker texts, built from parts: none of them may show up in a log line, an audit row or a gate exception
PROMPT_TEXT = "prompt-" + "marker-" + "7Qx"
SYSTEM_TEXT = "system-" + "marker-" + "4Kd"
DOC_TEXT = "document-" + "marker-" + "9Zp"
REPLY_TEXT = "reply-" + "marker-" + "2Wm"
ERROR_TEXT = "error-" + "marker-" + "5Ht"
MARKERS = (PROMPT_TEXT, SYSTEM_TEXT, DOC_TEXT, REPLY_TEXT, ERROR_TEXT)
MILLION = Decimal(1_000_000)


def _spend_refused() -> type[Exception]:
    """The published `SpendRefused` once it has landed; until then a copy of ii_meter.py's signature."""
    try:
        found = getattr(importlib.import_module("hadavin_sdk.limits"), "SpendRefused", None)
    except ImportError:
        found = None
    if isinstance(found, type) and issubclass(found, Exception):
        return found

    class SpendRefused(RuntimeError):
        def __init__(self, reason: str) -> None:
            super().__init__(reason)
            self.reason = reason

    return SpendRefused


SpendRefused = _spend_refused()


def _bind(gate, agent, run, **kwargs):
    """`gate.bind` with the run map said in the call: a missing or None `mapping` means "no run map" (NO_MAP)."""
    if kwargs.get("mapping") is None:
        kwargs["mapping"] = NO_MAP
    return gate.bind(agent, run, **kwargs)


def good_amount(value: object) -> bool:
    """INTERFACE (i): an amount is a finite Decimal that is not negative. A bool, a float or an int is not."""
    return isinstance(value, Decimal) and value.is_finite() and value >= 0


# --- doubles ---------------------------------------------------------------------------------------------------


class _Recorder:
    """Any attribute a double does not have is written down when something asks for it (points 7 and 9)."""

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.probes: list[str] = []
        self.charged: list[tuple] = []

    def __getattr__(self, name: str):
        if not name.startswith("__"):
            self.__dict__.setdefault("probes", []).append(name)
        raise AttributeError(name)

    def charge(
        self, *args, **kwargs
    ):  # the old after-the-fact booking: the gate must never call it
        self.charged.append((args, kwargs))
        raise AssertionError("charge was called")


class _MeterDouble(_Recorder):
    """INTERFACE (ii): reserve books and returns an id; the first settle wins; bad amounts are refused."""

    def __init__(self, events: list[str]) -> None:
        super().__init__(events)
        self.reserve_raises: BaseException | None = None
        self.settle_raises: BaseException | None = None
        self.reserve_calls: list[tuple[str, object, str | None]] = []
        self.settle_calls: list[tuple[str, object]] = []
        self.booked: dict[str, Decimal] = {}
        self.closed: dict[str, Decimal] = {}
        self.overshoots: list[Decimal] = []
        self._lock = threading.Lock()
        self._count = itertools.count(1)

    def _new_id(self, number: int) -> str:
        raise NotImplementedError

    def reserve(self, agent_id, worst_usd, *, run_id=None):
        with self._lock:
            self.events.append("reserve")
            self.reserve_calls.append((agent_id, worst_usd, run_id))
            if self.reserve_raises is not None:
                raise self.reserve_raises
            if not good_amount(worst_usd):
                raise SpendRefused("bad_amount")
            rid = self._new_id(next(self._count))
            self.booked[rid] = worst_usd
            return rid

    def settle(self, reservation_id, actual_usd):
        with self._lock:
            self.events.append("settle")
            self.settle_calls.append((reservation_id, actual_usd))
            if self.settle_raises is not None:
                raise self.settle_raises
            if reservation_id not in self.booked:
                raise LookupError("unknown reservation")
            if not good_amount(actual_usd):
                raise ValueError("bad amount")
            self.closed.setdefault(reservation_id, actual_usd)
            over = max(Decimal(0), actual_usd - self.booked[reservation_id])
            self.overshoots.append(over)
            return over

    def open(self) -> set[str]:
        return set(self.booked) - set(self.closed)


class StoreStyleMeter(_MeterDouble):
    """Shaped like the store-backed implementer: long opaque ids, a `store` attribute, a stop-state read."""

    def __init__(self, events: list[str]) -> None:
        super().__init__(events)
        self.store = object()

    def _new_id(self, number: int) -> str:
        return "rsv_" + format(number * 2654435761 % 2**32, "08x") + format(number, "04x")

    def blocked(self, *args, **kwargs):
        self.charged.append(("blocked", args, kwargs))
        raise AssertionError("blocked was called")


class MemoryStyleMeter(_MeterDouble):
    """Shaped like the in-memory implementer: short counted ids, a running total, no stop state."""

    def __init__(self, events: list[str]) -> None:
        super().__init__(events)
        self.spent = Decimal(0)

    def _new_id(self, number: int) -> str:
        return str(number)


class Inner(_Recorder):
    """The inner model client: counts calls, records what it got, returns a reply, raises, or retries inside."""

    def __init__(self, events: list[str], *, reply=None, raises=None, attempts: int = 1) -> None:
        super().__init__(events)
        self.reply = (
            Reply(text=REPLY_TEXT, cost_usd=COST, model_id=MODEL) if reply is None else reply
        )
        self.raises, self.attempts = raises, attempts
        self.calls = 0
        self.requests = 0
        self.seen: list[dict] = []
        self.during: list = []  # hooks run inside the call

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.events.append("call")
        self.calls += 1
        self.seen.append(
            {
                "messages": messages,
                "system": system,
                "route": route,
                "tools": tools,
                "documents": documents,
                "output_schema": output_schema,
            }
        )
        for hook in self.during:
            hook()
        for _ in range(self.attempts):  # the client's own retries: one chat call, several requests
            self.requests += 1
        if self.raises is not None:
            raise self.raises
        return self.reply(self.seen[-1]) if callable(self.reply) else self.reply


class Sink(_Recorder):
    """Only `write_outcome`, the one method the ticket lets the gate use (I8)."""

    def __init__(self, events: list[str], raises: Exception | None = None) -> None:
        super().__init__(events)
        self.raises = raises
        self.rows: list = []

    def write_outcome(self, event):
        self.events.append("audit")
        self.rows.append(event)
        if self.raises is not None:
            raise self.raises
        return event.event_id

    def codes(self) -> list[tuple[str | None, str | None]]:
        return [(row.result, row.error_code) for row in self.rows]


class Rig:
    """One gate with its doubles, all writing to ONE ordered event log."""

    def __init__(
        self, meter_cls, *, inner=None, sink="default", worst_case=None, enforce=None, **bind
    ):
        self.events: list[str] = []
        self.meter = meter_cls(self.events)
        self.inner = Inner(self.events) if inner is None else inner
        self.inner.events = self.events
        self.sink = Sink(self.events) if sink == "default" else sink
        if self.sink is not None:
            self.sink.events = self.events
        self.worst_calls: list[tuple] = []

        def fixed(route, system, messages, tools, documents, output_schema):
            return WORST

        self._worst = fixed if worst_case is None else worst_case
        kwargs = {} if enforce is None else {"enforce": enforce}
        self.gate = ModelGate(
            self.inner, meter=self.meter, audit=self.sink, worst_case=self._worst_step, **kwargs
        )
        self.bound = _bind(self.gate, AGENT, RUN, **bind)

    def _worst_step(self, route, system, messages, tools, documents, output_schema):
        self.events.append("worst")
        self.worst_calls.append((route, system, messages, tools, documents, output_schema))
        return self._worst(route, system, messages, tools, documents, output_schema)

    def chat(self, messages=None, **kwargs):
        kwargs.setdefault("system", "be brief")
        kwargs.setdefault("route", ROUTE)
        return self.bound.chat(HELLO if messages is None else messages, **kwargs)


@pytest.fixture(params=[StoreStyleMeter, MemoryStyleMeter], ids=["store-style", "memory-style"])
def meter_cls(request):
    """Both implementer shapes: the gate takes the meter as an argument and must work the same with each."""
    return request.param


def gate_tree() -> ast.Module:
    return ast.parse(inspect.getsource(model_gate))


# --- point 1, I5: any exception from reserve means no model call ----------------------------------------------

RESERVE_ERRORS = [
    *(pytest.param(lambda r=reason: SpendRefused(r), id=reason) for reason in REASONS),
    pytest.param(lambda: KeyError(AGENT), id="unknown-agent-KeyError"),
    pytest.param(lambda: RuntimeError("store down"), id="RuntimeError"),
    pytest.param(lambda: OSError("no route"), id="OSError"),
    pytest.param(lambda: TimeoutError(), id="TimeoutError"),
    pytest.param(lambda: KeyboardInterrupt(), id="KeyboardInterrupt"),
]


@pytest.mark.parametrize("make", RESERVE_ERRORS)
def test_point1_any_exception_from_reserve_means_the_inner_client_is_not_called(meter_cls, make):
    """Contract point 1 and ticket I5: every listed reason, an unknown agent (KeyError), any other exception
    and a BaseException from reserve: zero inner calls, zero settles, ONE reserve (never retried). The caller
    gets the very same exception object for a SpendRefused and for a BaseException; since ORDER 017 item 5 any
    other error comes out as a code-only `GateRefused("reserve_refused")`."""
    rig, error = Rig(meter_cls), make()
    rig.meter.reserve_raises = error
    expected = _refusal_of(error)
    with pytest.raises(expected) as caught:
        rig.chat()
    if expected is GateRefused:  # ORDER 017 item 5: a code, not the error
        _assert_code_only(caught.value, "reserve_refused")
    else:  # a SpendRefused, or a BaseException that is no Exception: the very same object
        assert caught.value is error
    assert rig.inner.calls == 0 and rig.inner.requests == 0
    assert len(rig.meter.reserve_calls) == 1 and rig.meter.settle_calls == []
    assert "call" not in rig.events and "settle" not in rig.events


@pytest.mark.parametrize("reason", REASONS)
def test_point1_the_published_reason_is_the_audit_error_code(meter_cls, reason):
    """Contract point 1 ("SpendRefused.reason is the audit error code") and ticket I8: one refused row."""
    rig = Rig(meter_cls)
    rig.meter.reserve_raises = SpendRefused(reason)
    with pytest.raises(SpendRefused):
        rig.chat()
    assert rig.sink.codes() == [("refused", reason)]


def test_point1_an_unknown_agent_is_refused_with_a_code_and_never_with_its_text(meter_cls):
    """Contract point 1 (KeyError: still no call) and ticket I9: the row holds a code, not the exception text."""
    rig = Rig(meter_cls)
    rig.meter.reserve_raises = KeyError(ERROR_TEXT)
    with pytest.raises(
        _refusal_of(KeyError(AGENT))
    ) as caught:  # GateRefused since ORDER 017 item 5
        rig.chat()
    if GateRefused is not None:
        _assert_code_only(caught.value, "reserve_refused")
        assert ERROR_TEXT not in repr(caught.value) and ERROR_TEXT not in str(caught.value)
    assert rig.inner.calls == 0
    (row,) = rig.sink.rows
    assert row.result == "refused" and row.error_code and row.error_code not in REASONS
    assert ERROR_TEXT not in row.model_dump_json()


@pytest.mark.parametrize(
    "amount",
    [0.25, 1, True, Decimal("NaN"), Decimal("Infinity"), Decimal("-0.01"), None, "0.25"],
    ids=repr,
)
def test_point1_a_bad_worst_case_amount_refused_by_the_meter_means_no_call(meter_cls, amount):
    """Contract points 1 and 10 (bad_amount): a worst case that is not a finite Decimal >= 0 (a float, an int,
    a bool, NaN, Infinity, a negative, None, text) never books and the inner client is not called. Where the
    head has `GateRefused` (ORDER 017 item 5, request 3 section 3) the GATE refuses it first, as the code
    `worst_case_invalid`, and the meter is not asked; before, the meter refused it as `bad_amount`."""
    rig = Rig(meter_cls, worst_case=lambda *a: amount)
    if GateRefused is None:
        with pytest.raises(SpendRefused) as caught:
            rig.chat()
        assert caught.value.reason == "bad_amount"
        assert rig.sink.codes() == [("refused", "bad_amount")]
    else:
        with pytest.raises(GateRefused) as caught:
            rig.chat()
        _assert_code_only(caught.value, "worst_case_invalid")
        assert rig.sink.codes() == [("refused", "worst_case_invalid")]
    assert rig.inner.calls == 0 and rig.meter.booked == {} and rig.meter.settle_calls == []


def test_point1_a_worst_case_that_cannot_be_computed_means_no_reservation_and_no_call(meter_cls):
    """Contract point 1 read with point 10: with no worst case there is nothing to book, so nothing is called."""

    def broken(*args):
        raise ArithmeticError("no price")

    rig = Rig(meter_cls, worst_case=broken)
    with pytest.raises(_refusal_of(ArithmeticError("no price"))) as caught:
        rig.chat()
    if (
        GateRefused is not None
    ):  # its error is NOT passed on (it may carry text): the code `worst_case_failed`
        _assert_code_only(caught.value, "worst_case_failed")
    assert rig.meter.reserve_calls == [] and rig.inner.calls == 0 and rig.meter.settle_calls == []


# --- points 2 and 3, I7, I11: one settle with the real cost ---------------------------------------------------


def test_point2_3_settle_is_called_exactly_once_with_the_real_cost_of_the_reply(meter_cls):
    """Contract points 2 and 3, ticket I6, I7, I11: one reservation for the worst case under the bound agent
    and run; one settle for THAT reservation id with the reply's cost, digit for digit and still a Decimal;
    the reply object comes back unchanged."""
    rig = Rig(meter_cls)
    reply = rig.chat()
    assert reply is rig.inner.reply and reply.cost_usd == COST
    assert rig.meter.reserve_calls == [(AGENT, WORST, RUN)]
    (rid,) = rig.meter.booked
    assert len(rig.meter.settle_calls) == 1
    settled_id, settled = rig.meter.settle_calls[0]
    assert settled_id == rid
    assert type(settled) is Decimal and type(rig.meter.reserve_calls[0][1]) is Decimal
    assert settled.as_tuple() == COST.as_tuple(), "the cost was rounded or re-scaled on its way"
    assert rig.meter.open() == set()


def test_point3_a_zero_cost_refusal_reply_is_settled_once_at_zero(meter_cls):
    """Contract point 3: a model refusal that cost nothing has a KNOWN cost of 0: settle once with Decimal 0,
    so the worst case is released."""
    reply = Reply(text="", cost_usd=Decimal(0), model_id=MODEL, stop_reason="refusal")
    rig = Rig(meter_cls, inner=Inner([], reply=reply))
    assert rig.chat() is reply
    assert len(rig.meter.settle_calls) == 1
    amount = rig.meter.settle_calls[0][1]
    assert type(amount) is Decimal and amount == 0
    assert rig.meter.open() == set()


def test_point3_a_request_marked_refused_before_sending_is_settled_once_at_zero(meter_cls):
    """Contract point 3 ("refused before sending and cost nothing: settle(rid, Decimal(0))"): only an error
    the adapter MARKED as refused before any response is settled at 0, exactly once; it still comes out."""
    error = ProviderError("refused")
    error.refused_before_response = True
    rig = Rig(meter_cls, inner=Inner([], raises=error))
    with pytest.raises(ProviderError) as caught:
        rig.chat()
    assert caught.value is error
    assert len(rig.meter.settle_calls) == 1
    rid, amount = rig.meter.settle_calls[0]
    assert rid in rig.meter.booked and type(amount) is Decimal and amount == 0


def test_point2_two_calls_make_two_reservations_each_settled_with_its_own_cost(meter_cls):
    """Contract point 2 and ticket I7: settle exactly once PER reservation; the second call does not reuse or
    re-settle the first id."""
    costs = iter([Decimal("0.01"), Decimal("0.07")])
    rig = Rig(
        meter_cls,
        inner=Inner([], reply=lambda seen: Reply(text="x", cost_usd=next(costs), model_id=MODEL)),
    )
    rig.chat()
    rig.chat()
    first, second = list(rig.meter.booked)
    assert first != second
    assert rig.meter.settle_calls == [(first, Decimal("0.01")), (second, Decimal("0.07"))]


# --- point 4, Major M2: an unknown cost is never settled ------------------------------------------------------


class CallTimeout(Exception):
    """A client's own timeout type, unknown to the gate."""


def _marked(error: BaseException, mark: object = True) -> BaseException:
    error.refused_before_response = mark  # type: ignore[attr-defined]
    return error


FAILED_CALLS = [
    pytest.param(lambda: TimeoutError(ERROR_TEXT), id="TimeoutError"),
    pytest.param(lambda: CallTimeout(ERROR_TEXT), id="client-timeout"),
    pytest.param(lambda: ProviderError(ERROR_TEXT), id="plain-ProviderError-M2"),
    pytest.param(lambda: ProviderExhausted(ERROR_TEXT), id="ProviderExhausted"),
    pytest.param(lambda: ValueError(ERROR_TEXT), id="reply-failed-to-parse"),
    pytest.param(lambda: ConnectionResetError(ERROR_TEXT), id="connection-reset"),
    pytest.param(lambda: KeyboardInterrupt(), id="KeyboardInterrupt"),
    pytest.param(lambda: SystemExit(3), id="SystemExit"),
    pytest.param(lambda: _marked(ProviderExhausted(ERROR_TEXT)), id="mark-on-used-up-retries"),
    pytest.param(lambda: _marked(ValueError(ERROR_TEXT)), id="mark-on-a-foreign-error"),
    pytest.param(lambda: _marked(ProviderError(ERROR_TEXT), "yes"), id="mark-that-is-not-True"),
]


@pytest.mark.parametrize("make", FAILED_CALLS)
def test_point4_a_failed_or_timed_out_call_is_not_settled_and_its_error_passes_unchanged(
    meter_cls, make
):
    """Contract point 4 and Major M2 of the code review: when the inner call raises or times out the real cost
    is unknown (a plain ProviderError may be a billed reply that failed to parse), so settle is NOT called,
    the worst case stays booked, reserve is not repeated, and the original exception object comes out with
    its arguments, cause and context untouched."""
    error = make()
    args_before = error.args
    rig = Rig(meter_cls, inner=Inner([], raises=error))
    with pytest.raises(type(error)) as caught:
        rig.chat()
    assert caught.value is error and error.args == args_before
    assert error.__cause__ is None and error.__context__ is None
    assert rig.meter.settle_calls == [], (
        "a call of unknown cost was settled: the worst case is released"
    )
    assert len(rig.meter.reserve_calls) == 1 and rig.inner.calls == 1
    assert rig.meter.open() == set(rig.meter.booked) and len(rig.meter.booked) == 1
    assert rig.meter.booked[next(iter(rig.meter.booked))] == WORST
    assert all(ERROR_TEXT not in row.model_dump_json() for row in rig.sink.rows)


# --- point 5: settle raising never loses the reply and never repeats reserve ---------------------------------


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("store down"),
        ConnectionError("gone"),
        LookupError("unknown id"),
        ValueError("bad"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_point5_when_settle_raises_the_reply_is_still_returned_and_reserve_is_not_retried(
    meter_cls, error
):
    """Contract point 5: the store goes down after a paid call: the reply comes back as the same object, the
    worst case stays booked, the model is not called again and reserve is called exactly once."""
    rig = Rig(meter_cls)
    rig.meter.settle_raises = error
    reply = rig.chat()
    assert reply is rig.inner.reply
    assert len(rig.meter.reserve_calls) == 1 and rig.inner.calls == 1
    assert rig.meter.open() == set(rig.meter.booked)
    assert rig.events.count("reserve") == 1 and rig.events.count("call") == 1


# --- point 6, I6: one reserve per chat call ------------------------------------------------------------------


@pytest.mark.parametrize("attempts", [1, 3, 7])
def test_point6_one_reserve_covers_the_clients_own_internal_retries(meter_cls, attempts):
    """Contract point 6 and ticket I6: the inner client sends several requests inside ONE chat call; the gate
    makes one reservation and one settle for it, and calls the client once."""
    rig = Rig(meter_cls, inner=Inner([], attempts=attempts))
    rig.chat()
    assert rig.inner.requests == attempts and rig.inner.calls == 1
    assert len(rig.meter.reserve_calls) == 1 and len(rig.meter.settle_calls) == 1


def test_point6_a_gate_is_never_put_around_a_gate(meter_cls):
    """Contract point 6 (one booking per call): a client that is already a gate would reserve twice."""
    rig = Rig(meter_cls)
    for client in (rig.gate, rig.bound):
        with pytest.raises(TypeError):
            ModelGate(client, meter=rig.meter, audit=None, worst_case=lambda *a: WORST)


# --- points 7 and 9: no second booking, the run's cost is not added again -------------------------------------


def _all_paths(meter_cls):
    """One rig per outcome: paid, refused by the meter, failed call, settle down, cost unknown."""
    paid = Rig(meter_cls)
    refused = Rig(meter_cls)
    refused.meter.reserve_raises = SpendRefused(REASONS[1])
    failed = Rig(meter_cls, inner=Inner([], raises=ProviderExhausted(ERROR_TEXT)))
    down = Rig(meter_cls)
    down.meter.settle_raises = RuntimeError("store down")
    unknown = Rig(meter_cls, inner=Inner([], reply=SimpleNamespace(text=REPLY_TEXT)))
    rigs = [paid, refused, failed, down, unknown]
    for rig in rigs:
        try:
            rig.chat(
                [{"role": "user", "content": PROMPT_TEXT}],
                system=SYSTEM_TEXT,
                documents=[DOC_TEXT.encode()],
            )
        except (SpendRefused, ProviderError):
            pass
    return rigs


def test_point7_the_gate_makes_no_second_booking_on_anything_it_is_given(meter_cls):
    """Contract point 7: on every path nothing calls a charge method (or the stop-state read) of the meter,
    the client or the sink, and the gate asks none of them for any attribute but the published ones."""
    for rig in _all_paths(meter_cls):
        for part in (rig.meter, rig.inner, rig.sink):
            assert part.charged == [], f"{type(part).__name__} was charged"
            assert part.probes == [], f"{type(part).__name__} was asked for {part.probes}"


def test_point7_9_the_module_has_no_money_logic_of_its_own():
    """Contract points 7 and 9, ticket "holds no money logic": the module names no charge call and imports
    neither the limits, the store nor the k1b budget, so it has no handle to book a cost a second time or to
    add it to the run's cost."""
    tree = gate_tree()
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not attributes & {"charge", "add_spend", "add_cost", "settle_spend", "reserve_spend"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    banned = ("hadavin_sdk.limits", "hadavin_sdk.store", "hadavin_sdk.k1b", "hadavin_sdk.runtime")
    assert not [name for name in imported if name.startswith(banned)], sorted(imported)


def test_point9_the_cost_reaches_the_meter_once_and_nothing_else(meter_cls):
    """Contract point 9: the store adds the settled cost to the run's cost, so the gate must hand the cost
    over exactly once (the one settle) and to nobody else: the audit row carries no amount at all."""
    rig = Rig(meter_cls)
    rig.chat()
    assert [amount for _, amount in rig.meter.settle_calls] == [COST]
    assert rig.events.count("settle") == 1
    (row,) = rig.sink.rows
    dumped = row.model_dump()
    assert not [v for v in dumped.values() if isinstance(v, Decimal | float)]
    assert str(COST) not in row.model_dump_json() and str(WORST) not in row.model_dump_json()


# --- order: I1 and Amendment 1 item 8 -------------------------------------------------------------------------


def test_order_reserve_strictly_before_the_inner_call_and_settle_strictly_after(meter_cls):
    """Ticket I1 with Amendment 1 item 8 (enforce, reserve, call, settle, audit) and the three lines of
    INTERFACE (ii): one ordered event log; and seen from INSIDE the inner call the reservation is already
    booked and not yet settled."""
    enforced: list[str] = []

    def enforce(text, mapping):
        rig.events.append("enforce")
        enforced.append(text)
        return text

    rig = Rig(meter_cls, enforce=enforce, mapping={})
    inside: list[tuple[int, int]] = []
    rig.inner.during.append(
        lambda: inside.append((len(rig.meter.booked), len(rig.meter.settle_calls)))
    )
    rig.chat()
    assert rig.events == ["enforce", "worst", "reserve", "call", "settle", "audit"]
    assert inside == [(1, 0)]


def test_order_holds_on_every_path_no_call_before_a_reserve_no_settle_before_a_call(meter_cls):
    """Ticket I1: on every outcome each "call" has a "reserve" before it and each "settle" a "call" before
    it; a refused path holds neither."""
    for rig in _all_paths(meter_cls):
        log = rig.events
        if "call" in log:
            assert log.index("reserve") < log.index("call")
        if "settle" in log:
            assert log.index("call") < log.index("settle")
        assert log.count("reserve") == 1 and log.count("call") <= 1 and log.count("settle") <= 1


# --- point 10: the worst case covers everything sent ---------------------------------------------------------


def sent_bytes(system, messages, tools, documents, output_schema) -> int:
    """Everything that goes to the provider, in bytes: at most one token per byte (contract point 10)."""
    total = len(system.encode("utf-8"))
    for group in (messages, tools or []):
        total += sum(len(json.dumps(item, ensure_ascii=False).encode("utf-8")) for item in group)
    total += sum(len(document) for document in documents or [])
    if output_schema is not None:
        total += len(json.dumps(output_schema, ensure_ascii=False).encode("utf-8"))
    return total


def contract_worst_case(
    input_price: Decimal, output_price: Decimal, max_tokens: int, max_attempts: int
):
    """The formula of contract point 10 as an installer would hand it to the gate: (bytes sent at the input
    price + max_tokens at the output price) times max_attempts; prices are USD per million tokens. Every
    step runs with the Inexact trap on: a rounded result is an error, not a number."""

    def worst_case(route, system, messages, tools, documents, output_schema) -> Decimal:
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("max_attempts")
        with localcontext() as ctx:
            ctx.traps[Inexact] = True
            tokens_in = Decimal(sent_bytes(system, messages, tools, documents, output_schema))
            one = tokens_in * input_price + Decimal(max_tokens) * output_price
            return (one * max_attempts).scaleb(-6)

    return worst_case


class BillingInner(Inner):
    """A client that bills like a provider within the route's limits: per request at most one input token
    per byte it RECEIVED and at most max_tokens of output, for 1 to max_attempts requests."""

    def __init__(self, rng, input_price, output_price, max_tokens, max_attempts, extreme) -> None:
        super().__init__([])
        self.rng, self.prices = rng, (input_price, output_price)
        self.max_tokens, self.max_attempts, self.extreme = max_tokens, max_attempts, extreme
        self.reply = self._bill

    def _bill(self, seen) -> Reply:
        received = len(seen["system"].encode("utf-8"))
        for message in seen["messages"]:
            received += sum(len(str(v).encode("utf-8")) for v in message.values())
        received += sum(
            len(json.dumps(t, ensure_ascii=False).encode()) for t in seen["tools"] or []
        )
        received += sum(len(d) for d in seen["documents"] or [])
        if seen["output_schema"] is not None:
            received += len(json.dumps(seen["output_schema"], ensure_ascii=False).encode())
        requests = self.max_attempts if self.extreme else self.rng.randint(1, self.max_attempts)
        cost = Decimal(0)
        tokens_in = tokens_out = 0
        with localcontext() as ctx:
            ctx.traps[Inexact] = True
            for _ in range(requests):
                used_in = received if self.extreme else self.rng.randint(0, received)
                used_out = self.max_tokens if self.extreme else self.rng.randint(0, self.max_tokens)
                tokens_in, tokens_out = tokens_in + used_in, tokens_out + used_out
                cost += (used_in * self.prices[0] + used_out * self.prices[1]).scaleb(-6)
        self.requests = requests
        return Reply(
            text="ok",
            cost_usd=cost,
            model_id=MODEL,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
        )


ALPHABET = 'abc XYZ 0123 .,:{}"\\\n' + "é" + "ß" + "й" + "漢" + "字" + "\u200b" + "\U0001f600"


def _text(rng, limit: int) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, limit)))


def _case(rng):
    messages = [
        {"role": rng.choice(["user", "assistant"]), "content": _text(rng, 300)}
        for _ in range(rng.randint(0, 5))
    ]
    tools = (
        None
        if rng.random() < 0.3
        else [
            {
                "name": "tool_" + str(n),
                "description": _text(rng, 80),
                "input_schema": {"type": "object"},
            }
            for n in range(rng.randint(0, 3))
        ]
    )
    documents = (
        None
        if rng.random() < 0.3
        else [rng.randbytes(rng.randint(0, 2000)) for _ in range(rng.randint(0, 3))]
    )
    schema = None if rng.random() < 0.5 else {"type": "object", "title": _text(rng, 40)}
    return _text(rng, 200), messages, tools, documents, schema


def test_point10_the_reserved_worst_case_is_never_below_the_real_cost_of_any_reply(meter_cls):
    """Contract point 10, with the formula of the interface text handed to the gate as its worst-case step:
    300 fixed-seed random calls (system prompt, messages, tool schemas, documents, an output schema, ASCII
    and multi-byte text, random prices, max_tokens and max_attempts). The amount the gate RESERVED is never
    below the cost of the reply, so the meter never reports an overshoot; both amounts are Decimals, the
    reserved one equals an independent whole-number computation exactly, and no step was inexact."""
    rng = random.Random(20261120)  # noqa: S311 - a fixed seed for test data, not a secret
    for number in range(300):
        input_price = Decimal(rng.randint(1, 75_000)).scaleb(-3)
        output_price = Decimal(rng.randint(1, 150_000)).scaleb(-3)
        max_tokens, max_attempts = rng.randint(1, 8192), rng.randint(1, 5)
        inner = BillingInner(
            rng, input_price, output_price, max_tokens, max_attempts, extreme=number % 4 == 0
        )
        rig = Rig(
            meter_cls,
            inner=inner,
            worst_case=contract_worst_case(input_price, output_price, max_tokens, max_attempts),
        )
        system, messages, tools, documents, schema = _case(rng)
        reply = rig.chat(
            messages, system=system, tools=tools, documents=documents, output_schema=schema
        )
        ((_, reserved, _),) = rig.meter.reserve_calls
        ((_, settled),) = rig.meter.settle_calls
        assert type(reserved) is Decimal and type(settled) is Decimal
        assert settled == reply.cost_usd
        assert reserved >= reply.cost_usd, (
            f"case {number}: reserved {reserved} < cost {reply.cost_usd}"
        )
        assert rig.meter.overshoots == [Decimal(0)]
        whole = Fraction(
            (
                sent_bytes(system, messages, tools, documents, schema) * int(input_price.scaleb(3))
                + max_tokens * int(output_price.scaleb(3))
            )
            * max_attempts,
            10**9,
        )
        assert Fraction(reserved) == whole, f"case {number}: the reserved amount is not exact"


def test_point10_each_thing_sent_reaches_the_worst_case_step_and_raises_the_reservation(meter_cls):
    """Contract point 10 ("must cover everything sent: system prompt, messages, tool schemas, documents"):
    the gate hands ALL of them to its worst-case step and books what the step returns, so adding any one of
    them raises the reserved amount by exactly its bytes at the input price."""
    price = Decimal(3)
    worst_case = contract_worst_case(price, Decimal(15), 100, 2)

    def reserved_for(**sent) -> Decimal:
        call = {
            "system": "",
            "messages": [],
            "tools": None,
            "documents": None,
            "output_schema": None,
            **sent,
        }
        rig = Rig(meter_cls, worst_case=worst_case)
        rig.chat(call.pop("messages"), **call)
        return rig.meter.reserve_calls[0][1]

    base = reserved_for()
    assert base == (Decimal(100) * 15 * 2).scaleb(-6)
    tool = {"name": "lookup", "input_schema": {"type": "object"}}
    message = {"role": "user", "content": "x" * 50}
    grown = {
        "system": (reserved_for(system="s" * 40), 40),
        "messages": (reserved_for(messages=[message]), len(json.dumps(message))),
        "tools": (reserved_for(tools=[tool]), len(json.dumps(tool))),
        "documents": (reserved_for(documents=[b"d" * 70, b"e" * 30]), 100),
        "output_schema": (
            reserved_for(output_schema={"type": "object"}),
            len('{"type": "object"}'),
        ),
    }
    for name, (amount, size) in grown.items():
        assert amount - base == (Decimal(size) * price * 2).scaleb(-6), f"{name} is not covered"


def test_point10_multi_byte_text_counts_one_token_per_byte_not_per_character(meter_cls):
    """Contract point 10 ("at most one token per byte"): text outside ASCII is counted by its UTF-8 bytes
    in what the gate reserves, in the system prompt, in a message and in a document."""
    wide = ("漢" + "字" + "\U0001f600" + "é") * 25  # 100 characters, 300 bytes
    assert len(wide) == 100 and len(wide.encode("utf-8")) == 300
    worst_case = contract_worst_case(Decimal(1), Decimal(1), 0, 1)
    plain = Rig(meter_cls, worst_case=worst_case)
    plain.chat([{"role": "user", "content": "a" * 100}], system="b" * 100, documents=[b"c" * 100])
    rig = Rig(meter_cls, worst_case=worst_case)
    rig.chat([{"role": "user", "content": wide}], system=wide, documents=[wide.encode("utf-8")])
    extra = rig.meter.reserve_calls[0][1] - plain.meter.reserve_calls[0][1]
    assert extra == Decimal(3 * 200).scaleb(-6)
    assert rig.inner.seen[0]["messages"][0]["content"] == wide  # sent as written


def test_point10_the_worst_case_is_computed_on_what_is_really_sent(meter_cls):
    """Contract point 10 with Amendment 1 item 7: when the enforce step makes a text LONGER (a placeholder
    longer than the value it stands for), the reservation covers the longer text the client receives."""
    value, placeholder = "v" + "9k2", "<" + "LONG_PLACEHOLDER_NAME_" + "1" + ">"
    price = Decimal(2)

    def enforce(text, mapping):
        for token, original in mapping.items():
            text = text.replace(original, token)
        return text

    rig = Rig(
        meter_cls,
        worst_case=contract_worst_case(price, Decimal(0), 0, 1),
        enforce=enforce,
        mapping={placeholder: value},
    )
    messages = [{"role": "user", "content": " ".join([value] * 40)}]
    documents = [(value + "\n").encode() * 40]
    rig.chat(messages, system="", documents=documents)
    seen = rig.inner.seen[0]
    assert (
        value not in seen["messages"][0]["content"] and value.encode() not in seen["documents"][0]
    )
    received = sent_bytes("", seen["messages"], None, seen["documents"], None)
    assert received > sent_bytes("", messages, None, documents, None)
    assert rig.meter.reserve_calls[0][1] == (Decimal(received) * price).scaleb(-6)


@pytest.mark.parametrize("max_attempts", [0, -1, -5, True, 1.0, None], ids=repr)
def test_point10_max_attempts_zero_or_negative_books_nothing_and_calls_nothing(
    meter_cls, max_attempts
):
    """Contract point 10 ("times the client's max_attempts"): an attempt count of 0 or below (or one that is
    not a whole number) has no worst case. The gate must not fall back to booking 0 and calling: no
    reservation, no call, and the refusal of the worst-case step comes out (its ValueError on a head without
    `GateRefused`; since ORDER 017 item 5 the code-only `GateRefused("worst_case_failed")`, as the gate does not
    pass the error of that step on)."""
    rig = Rig(meter_cls, worst_case=contract_worst_case(Decimal(3), Decimal(15), 100, max_attempts))
    if GateRefused is None:
        with pytest.raises(ValueError, match="max_attempts"):
            rig.chat()
    else:
        with pytest.raises(GateRefused) as caught:
            rig.chat()
        _assert_code_only(caught.value, "worst_case_failed")
    assert rig.meter.reserve_calls == [] and rig.inner.calls == 0


def test_point10_a_shared_worst_case_formula_exists_on_this_branch():
    """Contract point 10 says the worst case is the gate's job, or a shared helper
    `llm.common.worst_case_usd(route, system, messages, *, tools, documents, requests)`. The gate under test
    takes the formula from its installer, so the formula itself can only be tested where one exists."""
    common = importlib.import_module("hadavin_sdk.llm.common")
    if not hasattr(common, "worst_case_usd") and not hasattr(model_gate, "worst_case_usd"):
        pytest.skip(
            "contract point 10: no worst-case formula on this branch (neither llm.common.worst_case_usd nor "
            "one in the gate); the tests above use the formula of the interface text, not shipped code"
        )
    pytest.xfail("a worst-case helper has landed: bind the point 10 property test above to it")


# --- hostile replies ------------------------------------------------------------------------------------------

UNUSABLE = [
    Decimal("-0.01"),
    Decimal("NaN"),
    Decimal("sNaN"),
    Decimal("Infinity"),
    Decimal("-Infinity"),
    True,
    False,
    None,
]


@pytest.mark.parametrize("cost", UNUSABLE, ids=repr)
def test_hostile_a_negative_nan_infinite_or_bool_cost_is_never_settled(meter_cls, cost):
    """Contract points 3 and 4: a cost that is negative, NaN, Infinity or a bool is not a known cost. The
    reply is returned (the call is paid), nothing is settled with the bad value, the worst case stays booked
    and reserve is not repeated."""
    reply = SimpleNamespace(text=REPLY_TEXT, cost_usd=cost, model_id=MODEL)
    rig = Rig(meter_cls, inner=Inner([], reply=reply))
    assert rig.chat() is reply
    assert rig.meter.settle_calls == []
    assert len(rig.meter.reserve_calls) == 1 and rig.meter.open() == set(rig.meter.booked)
    assert len(rig.sink.rows) == 1 and rig.sink.rows[0].result == "ok"


def test_hostile_a_reply_with_no_cost_field_is_returned_and_not_settled(meter_cls):
    """Contract point 4: no cost field at all means the cost is unknown: the reply is returned unchanged,
    there is no settle (never a settle at 0) and the worst case stays booked."""
    reply = SimpleNamespace(text=REPLY_TEXT)
    rig = Rig(meter_cls, inner=Inner([], reply=reply))
    assert rig.chat() is reply
    assert rig.meter.settle_calls == [] and rig.meter.open() == set(rig.meter.booked)


@pytest.mark.parametrize("cost", [0.1, 1, "0.5", b"1", [Decimal(1)]], ids=repr)
def test_hostile_a_cost_of_another_type_never_reaches_settle_as_anything_but_a_decimal(
    meter_cls, cost
):
    """Exact Decimal arithmetic (contract point 10, INTERFACE (i) "nothing rounded"): a float, an int or text
    as the cost must never be handed to settle as it is. Either it is not settled (the worst case stays
    booked) or what is settled is a finite Decimal that is not negative. The reply is returned either way."""
    reply = SimpleNamespace(text=REPLY_TEXT, cost_usd=cost)
    rig = Rig(meter_cls, inner=Inner([], reply=reply))
    assert rig.chat() is reply
    assert all(good_amount(amount) for _, amount in rig.meter.settle_calls)
    assert len(rig.meter.settle_calls) <= 1


def test_hostile_a_cost_above_the_reservation_is_settled_in_full(meter_cls):
    """Contract point 2 (the overshoot is the meter's answer) and INTERFACE (i) "overshoot booked in full":
    the gate does not cap the real cost at the reserved amount."""
    over = WORST * 3 + Decimal("0.000001")
    rig = Rig(meter_cls, inner=Inner([], reply=Reply(text="x", cost_usd=over, model_id=MODEL)))
    rig.chat()
    assert [amount for _, amount in rig.meter.settle_calls] == [over]
    assert rig.meter.overshoots == [over - WORST]


def test_hostile_a_huge_document_is_booked_in_full_and_sent_as_the_callers_own_bytes(meter_cls):
    """Contract point 10 (documents are covered) and ticket I15: a 6 MiB document is neither cut nor copied
    on a site with no run map, and the reservation covers every byte of it."""
    document = bytes(range(256)) * (6 * 4096)
    price = Decimal("0.25")
    rig = Rig(meter_cls, worst_case=contract_worst_case(price, Decimal(0), 0, 1))
    rig.chat([], system="", documents=[document])
    assert rig.inner.seen[0]["documents"][0] is document
    assert rig.meter.reserve_calls[0][1] == (Decimal(len(document)) * price).scaleb(-6)
    assert all(document[:64].hex() not in row.model_dump_json() for row in rig.sink.rows)


@pytest.mark.parametrize("mapping", [None, {}], ids=["no-map", "empty-map"])
def test_hostile_an_empty_message_list_is_still_one_reserve_one_call_one_settle(meter_cls, mapping):
    """Contract points 1 to 3 hold with nothing to send: an empty message list is not a way around the
    meter and not a crash."""
    rig = Rig(meter_cls, mapping=mapping)
    rig.chat([])
    assert rig.inner.seen[0]["messages"] == []
    assert rig.events == ["worst", "reserve", "call", "settle", "audit"]


@pytest.mark.parametrize("content", [None, 7, 0.5, b"bytes", ["a"], {"text": "a"}], ids=repr)
def test_hostile_a_content_that_is_not_text_means_no_reservation_and_no_call(meter_cls, content):
    """Ticket I2' and Amendment 1 item 3: a message content that is not `str` is refused before anything is
    booked: no reserve, no call, a gate refusal that carries a code and no text."""
    rig = Rig(meter_cls, mapping={})
    with pytest.raises(model_gate.GateRefused) as caught:
        rig.chat([{"role": "user", "content": content}])
    assert rig.meter.reserve_calls == [] and rig.inner.calls == 0
    assert caught.value.args == (caught.value.code,) and caught.value.__cause__ is None
    assert rig.sink.codes() == [("refused", caught.value.code)]


# --- the ticket's own invariants about the enforce step, the map and the audit row ---------------------------


@pytest.mark.parametrize(
    "error",
    [ValueError(ERROR_TEXT), RuntimeError(ERROR_TEXT), RecursionError(), MemoryError()],
    ids=lambda e: type(e).__name__,
)
def test_i2_a_failing_enforce_step_means_no_reservation_and_no_call(meter_cls, error):
    """Ticket I2' (enforce failure means no call) and I9: the caller gets `UnmaskedInput` with no text, no
    cause and no context; nothing is reserved; the client is not called; one refused row."""

    def enforce(text, mapping):
        raise error

    rig = Rig(meter_cls, enforce=enforce, mapping={})
    with pytest.raises(model_gate.UnmaskedInput) as caught:
        rig.chat([{"role": "user", "content": PROMPT_TEXT}])
    assert rig.meter.reserve_calls == [] and rig.inner.calls == 0 and rig.worst_calls == []
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert not any(marker in str(caught.value) for marker in MARKERS)
    assert rig.sink.codes() == [("refused", "mask_refused")]


def test_i3_i4_the_map_and_the_callers_objects_are_never_written_and_system_and_tools_are_not_enforced(
    meter_cls,
):
    """Ticket I3' and I4': the enforce step sees every message content and every document, never the system
    prompt or the tool schemas; the client gets the enforced copies; the caller's list, dicts, documents and
    map are equal to what they were."""
    value, placeholder = "kq7" + "zz81", "<" + "VALUE_" + "1" + ">"
    seen_by_enforce: list[str] = []

    def enforce(text, mapping):
        seen_by_enforce.append(text)
        return text.replace(value, placeholder)

    mapping = {placeholder: value}
    messages = [
        {"role": "user", "content": "first " + value, "name": "kept"},
        {"role": "assistant", "content": "clean"},
    ]
    documents = [("doc " + value).encode(), b"plain"]
    tools = [{"name": "t", "description": "tool " + value}]
    before = copy.deepcopy((messages, documents, tools, mapping))
    rig = Rig(meter_cls, enforce=enforce, mapping=mapping)
    rig.chat(messages, system="system " + value, tools=tools, documents=documents)
    assert (messages, documents, tools, mapping) == before
    assert seen_by_enforce == ["first " + value, "clean", "doc " + value, "plain"]
    seen = rig.inner.seen[0]
    assert seen["messages"][0] == {
        "role": "user",
        "content": "first " + placeholder,
        "name": "kept",
    }
    assert seen["documents"] == [("doc " + placeholder).encode(), b"plain"]
    assert seen["system"] == "system " + value and seen["tools"] is tools
    assert seen["messages"][1] is messages[1] and seen["documents"][1] is documents[1]


def test_i12_the_map_is_held_by_reference_a_value_added_later_is_enforced_on_the_next_call(
    meter_cls,
):
    """Ticket I12: the bound gate keeps the run's LIVE map, so a value the run masks after the first call is
    replaced in the same earlier message on the next call."""
    value, placeholder = "pw" + "x44" + "tk", "<" + "LATE_" + "1" + ">"

    def enforce(text, mapping):
        for token, original in mapping.items():
            text = text.replace(original, token)
        return text

    mapping: dict[str, str] = {}
    rig = Rig(meter_cls, enforce=enforce, mapping=mapping)
    messages = [{"role": "user", "content": "earlier " + value}]
    rig.chat(messages)
    mapping[placeholder] = value
    rig.chat(messages)
    first, second = (seen["messages"][0]["content"] for seen in rig.inner.seen)
    assert first == "earlier " + value and second == "earlier " + placeholder


def test_i13_i14_i15_the_shipped_enforce_step_on_a_real_run_map(meter_cls):
    """Ticket I13 to I15 with the DEFAULT enforce step and a map built by the producers' own redactor: text
    that is already masked is passed on as the caller's same objects (I15, byte-identical), its placeholders
    are untouched (I13), a raw copy of the known value never reaches the client, and enforcing twice equals
    once (I14)."""
    runmap = model_gate.runmap
    known = "AKIA" + "IOSFODNN7" + "EXAMPLE"  # the documented example key, built from parts
    mapping: dict[str, str] = {}
    masked = runmap.redact_text("the key is " + known + " today", mapping)
    assert known not in masked and known in mapping.values()
    before = dict(mapping)
    rig = Rig(meter_cls, mapping=mapping)
    clean = [{"role": "user", "content": masked}]
    documents = [masked.encode()]
    rig.chat(clean, documents=documents)
    assert (
        rig.inner.seen[0]["messages"][0] is clean[0]
        and rig.inner.seen[0]["documents"][0] is documents[0]
    )
    rig.chat([{"role": "user", "content": "raw again: " + known}], documents=[known.encode()])
    sent = rig.inner.seen[1]
    assert (
        known not in sent["messages"][0]["content"] and known.encode() not in sent["documents"][0]
    )
    once = runmap.enforce_map("raw again: " + known + " and " + masked, mapping)
    assert runmap.enforce_map(once, mapping) == once and masked in once
    assert mapping == before


def test_i8_exactly_one_audit_row_per_call_on_every_path_and_a_raising_sink_changes_nothing(
    meter_cls,
):
    """Ticket I8: one row per chat call whatever the outcome; a sink that raises never turns a paid call into
    an exception, never hides a refusal and never stops the settle; `audit=None` works on every path."""
    for rig in _all_paths(meter_cls):
        assert len(rig.sink.rows) == 1, rig.events
        assert rig.events[-1] == "audit"
    broken = Rig(meter_cls, sink=Sink([], raises=RuntimeError(ERROR_TEXT)))
    assert broken.chat() is broken.inner.reply
    assert len(broken.meter.settle_calls) == 1 and broken.meter.open() == set()
    refused = Rig(meter_cls, sink=Sink([], raises=RuntimeError(ERROR_TEXT)))
    refused.meter.reserve_raises = SpendRefused(REASONS[0])
    with pytest.raises(SpendRefused):
        refused.chat()
    silent = Rig(meter_cls, sink=None)
    assert silent.chat() is silent.inner.reply and len(silent.meter.settle_calls) == 1


def test_i10_an_unbound_gate_cannot_call_a_model_and_two_bound_gates_keep_their_own_agent_and_run(
    meter_cls,
):
    """Ticket I10: `ModelGate` has no `chat`; `bind` is per call site with no shared state: each bound gate
    reserves under its own agent and run, also when the calls alternate."""
    rig = Rig(meter_cls)
    assert not hasattr(rig.gate, "chat")
    other = _bind(rig.gate, "agent-" + "b2", "run-" + "r2")
    rig.chat()
    other.chat(HELLO, system="s", route=ROUTE)
    rig.chat()
    assert [(agent, run) for agent, _, run in rig.meter.reserve_calls] == [
        (AGENT, RUN),
        ("agent-" + "b2", "run-" + "r2"),
        (AGENT, RUN),
    ]
    assert [row.run_id for row in rig.sink.rows] == [RUN, "run-" + "r2", RUN]


# --- the meter is an argument: the gate never tests which implementer it got ---------------------------------


def test_the_gate_uses_only_reserve_and_settle_of_its_meter_and_never_tests_its_type():
    """INTERFACE (ii) "Two implementers, one shape: the gate ... must not test which one it got": in the whole
    module the only attributes read from the meter are `reserve` and `settle`, and the meter is never an
    argument of isinstance, issubclass, type, hasattr or getattr."""
    tree = gate_tree()

    def is_meter(node: ast.AST) -> bool:
        return (isinstance(node, ast.Attribute) and node.attr in {"_meter", "meter"}) or (
            isinstance(node, ast.Name) and node.id in {"meter", "_meter"}
        )

    used = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and is_meter(node.value)
        and isinstance(node.ctx, ast.Load)
    }
    assert used - {"_meter"} == {"reserve", "settle"}, used
    probes = [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"isinstance", "issubclass", "type", "hasattr", "getattr", "callable"}
        and any(is_meter(arg) for arg in node.args)
    ]
    assert probes == []


def test_both_meter_shapes_give_the_same_outcome_on_every_path():
    """INTERFACE (ii) "one shape": the event log and the audit codes of every path are the same for the
    store-shaped and the memory-shaped meter; only the reservation ids differ."""
    logs = {
        cls.__name__: [(rig.events, rig.sink.codes()) for rig in _all_paths(cls)]
        for cls in (StoreStyleMeter, MemoryStyleMeter)
    }
    assert logs["StoreStyleMeter"] == logs["MemoryStyleMeter"]
    ids = {
        cls.__name__: next(iter(_all_paths(cls)[0].meter.booked))
        for cls in (StoreStyleMeter, MemoryStyleMeter)
    }
    assert ids["StoreStyleMeter"] != ids["MemoryStyleMeter"]


# --- threads: ticket I10 and T15 ------------------------------------------------------------------------------

THREADS, ROUNDS = 12, 6


def test_threads_reserve_and_settle_counts_match_and_no_reservation_gets_another_calls_cost(
    meter_cls,
):
    """Ticket I10 and T15 (as far as the ticket claims: the gate has no state of its own, the meter and the
    client look after theirs): 12 threads, each with its own bound gate from ONE `ModelGate`, 6 calls each,
    plus 12 threads sharing ONE bound gate. Every call makes one reservation and one settle; each
    reservation id is settled with the cost of the call that reserved it, under the agent that made it."""
    events: list[str] = []
    meter = meter_cls(events)

    def number_of(messages) -> int:
        return int(messages[0]["content"].split("#")[1])

    def worst_case(route, system, messages, tools, documents, output_schema):
        return Decimal(1000 + number_of(messages))

    def reply(seen):
        time.sleep(0.0005)  # let other threads in between the reserve and the settle
        cost = Decimal(number_of(seen["messages"])).scaleb(-3)
        return Reply(text=seen["messages"][0]["content"], cost_usd=cost, model_id=MODEL)

    inner = Inner(events, reply=reply)
    gate = ModelGate(inner, meter=meter, audit=Sink(events), worst_case=worst_case)
    shared = _bind(gate, "agent-shared", "run-shared")
    barrier = threading.Barrier(2 * THREADS)
    problems: list[str] = []

    def work(thread: int, bound) -> None:
        barrier.wait()
        for step in range(ROUNDS):
            number = thread * 100 + step
            text = f"call #{number}"
            answer = bound.chat([{"role": "user", "content": text}], system="s", route=ROUTE)
            if answer.text != text:
                problems.append(f"thread {thread} got the reply of another call: {answer.text}")

    workers = [
        threading.Thread(target=work, args=(n, _bind(gate, f"agent-{n}", f"run-{n}")))
        for n in range(THREADS)
    ]
    workers += [threading.Thread(target=work, args=(THREADS + n, shared)) for n in range(THREADS)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=60)
    assert not any(worker.is_alive() for worker in workers) and problems == []
    total = 2 * THREADS * ROUNDS
    assert len(meter.reserve_calls) == total == len(meter.settle_calls) == inner.calls
    assert len(meter.booked) == total and meter.open() == set()
    assert len({rid for rid, _ in meter.settle_calls}) == total, "a reservation was settled twice"
    for rid, cost in meter.settle_calls:
        number = int(meter.booked[rid]) - 1000
        assert cost == Decimal(number).scaleb(-3), f"reservation {rid} got the cost of another call"
    for agent, worst, run in meter.reserve_calls:
        thread = (int(worst) - 1000) // 100
        expected = (
            ("agent-shared", "run-shared")
            if thread >= THREADS
            else (f"agent-{thread}", f"run-{thread}")
        )
        assert (agent, run) == expected


# --- nothing of the prompt, the document or the reply is logged: I9, Major M1 --------------------------------


def test_i9_no_prompt_document_reply_or_error_text_is_logged_printed_or_put_in_an_audit_row(
    meter_cls, caplog, capsys
):
    """Ticket I9: on every path (paid, refused, failed, settle down, cost unknown, mask refused) the gate
    writes NO log record at any level, prints nothing, and no marker text of the prompt, the system prompt,
    the document, the reply or the provider's error is in any audit row."""
    caplog.set_level(logging.DEBUG)
    rigs = _all_paths(meter_cls)
    masked = Rig(meter_cls, mapping={})
    with pytest.raises(model_gate.UnmaskedInput) as caught:
        masked.chat([{"role": "user", "content": [PROMPT_TEXT]}], documents=[DOC_TEXT.encode()])
    rigs.append(masked)
    assert [record for record in caplog.records if record.name.startswith("hadavin_sdk")] == []
    logged = "\n".join(record.getMessage() for record in caplog.records)
    out = capsys.readouterr()
    rows = "\n".join(row.model_dump_json() for rig in rigs for row in rig.sink.rows)
    assert len(rows) > 0
    for marker in MARKERS:
        assert marker not in logged and marker not in out.out and marker not in out.err
        assert marker not in rows
        assert marker not in str(caught.value) and marker not in repr(caught.value)


def test_m1_the_whole_module_has_no_logger_no_print_and_no_exception_text():
    """Major M1 of the code review (the builder's guard read only the top of the file): walk EVERY node of
    the module. No import of logging, warnings, traceback or sys; no call of print, str, repr or format on
    anything; no f-string; no `raise ... from`; and every `raise` is bare or raises a class or a call with
    constant arguments."""
    tree = gate_tree()
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert not imported & {"logging", "warnings", "traceback", "sys", "structlog"}, imported
    calls = [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert not {"print", "str", "repr", "format", "vars"} & set(calls)
    methods = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not methods & {"format", "format_exc", "with_traceback", "add_note", "warn", "write"}
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.JoinedStr)], "an f-string"
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert not attributes & {"args", "__cause__", "__context__", "__traceback__", "__notes__"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        assert node.cause is None, f"line {node.lineno}: raise ... from"
        raised = node.exc
        if raised is None or isinstance(raised, ast.Name):
            continue
        # ORDER 017 item 5: `raise GateRefused(failure)` hands over a failure CODE held in a local; it is allowed
        # only when every assignment to that local in the module is a CODE_* constant (or None), so no text of any
        # kind can reach the exception. Every other raise keeps the rule: constant arguments only.
        if (
            isinstance(raised, ast.Call)
            and getattr(raised.func, "id", "") == "GateRefused"
            and len(raised.args) == 1
            and isinstance(raised.args[0], ast.Name)
        ):
            local = raised.args[0].id
            sources = [
                n.value
                for n in ast.walk(tree)
                if isinstance(n, ast.Assign | ast.AnnAssign)
                and local in {t.id for t in ast.walk(n) if isinstance(t, ast.Name)}
                and n.value is not None
            ]
            assert sources, f"line {node.lineno}: a code with no assignment"
            for source in sources:
                assert (isinstance(source, ast.Name) and source.id.startswith("CODE_")) or (
                    isinstance(source, ast.Constant) and source.value is None
                ), f"line {node.lineno}: a GateRefused code that is not a CODE_ constant"
            continue
        assert isinstance(raised, ast.Call) and all(
            isinstance(arg, ast.Constant) for arg in raised.args
        ), f"line {node.lineno}: an exception built from a value"


def test_m1_the_module_keeps_no_state_between_calls():
    """Ticket I10 ("no ContextVar and no module-level state"): every module-level assignment is a constant,
    a frozenset of constants or a type alias; nothing at module level is a list, a dict, a set, a lock or a
    context variable."""
    tree = gate_tree()
    for node in tree.body:
        if isinstance(node, ast.Assign | ast.AnnAssign):
            value = node.value
            assert not isinstance(
                value, ast.List | ast.Dict | ast.Set | ast.ListComp | ast.DictComp | ast.SetComp
            ), f"line {node.lineno}: a mutable module-level value"
            if isinstance(value, ast.Call):
                name = getattr(value.func, "id", getattr(value.func, "attr", ""))
                # a compiled pattern (`re.compile`, since the framing rule of ORDER 017 item 6) is an immutable
                # constant, not state; any other call still is refused
                is_compile = (
                    name == "compile"
                    and isinstance(value.func, ast.Attribute)
                    and getattr(value.func.value, "id", "") == "re"
                )
                # the NO_MAP sentinel (ORDER 017 item 1): one instance of a class that has `__slots__ = ()` and
                # only methods, so it can hold no state
                stateless = [
                    c
                    for c in tree.body
                    if isinstance(c, ast.ClassDef)
                    and c.name == name
                    and any(
                        isinstance(b, ast.Assign)
                        and [getattr(t, "id", "") for t in b.targets] == ["__slots__"]
                        and isinstance(b.value, ast.Tuple)
                        and not b.value.elts
                        for b in c.body
                    )
                    and all(isinstance(b, ast.FunctionDef | ast.Assign | ast.Expr) for b in c.body)
                ]
                assert name == "frozenset" or is_compile or stateless, (
                    f"line {node.lineno}: module-level call of {name}"
                )
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert not names & {"ContextVar", "contextvars", "threading", "local", "lru_cache", "cache"}
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Global | ast.Nonlocal)]


# --- the other Majors of the code review ---------------------------------------------------------------------


def test_m3_the_mutant_script_for_the_gate_exists():
    """Major M3 of the code review: without tests/gate_mutants.py the three gate guarantees count as not
    run. Looked for beside the source tree the module was imported from."""
    root = Path(model_gate.__file__).resolve().parents[3]
    if not (root / "tests").is_dir():
        pytest.skip("the module is installed without its tests folder")
    assert (root / "tests" / "gate_mutants.py").is_file()


def test_m4_the_live_map_is_never_emptied_while_a_producer_continues_it():
    """Major M4 of the code review: the gate holds the run's map by reference, so `redact_text` must never
    clear it and fill it again (a gate call on another thread would read it empty and send a known value
    raw). The map is never cleared, never shrinks during the write, and keeps every earlier entry."""
    runmap = model_gate.runmap
    sizes: list[int] = []

    class Watched(dict):
        def clear(self):
            raise AssertionError("the live map was cleared")

        def update(self, *args, **kwargs):
            sizes.append(len(self))
            super().update(*args, **kwargs)
            sizes.append(len(self))

        def pop(self, *args):
            raise AssertionError("an entry was taken out of the live map")

        def __delitem__(self, key):
            raise AssertionError("an entry was deleted from the live map")

    mapping = Watched()
    first = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    second = "AKIA" + "J7QW2RT5KLP9" + "ZX4M"
    runmap.redact_text("one " + first, mapping)
    before = dict(mapping)
    assert first in before.values()
    out = runmap.redact_text("two " + second + " and one " + first, mapping)
    assert first not in out and second not in out
    assert before.items() <= mapping.items() and len(mapping) > len(before)
    assert sizes == sorted(sizes), "the live map shrank during a write"
