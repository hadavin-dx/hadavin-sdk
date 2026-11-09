"""PEEL-run-id: `Runtime.handle(..., run_id=...)` starts a run with a caller-chosen id (ticket PEEL-run-id)."""

import inspect
import re
import threading
from datetime import timedelta

import pytest

from hadavin_sdk import models
from hadavin_sdk.models import Run, RunState, now
from hadavin_sdk.runtime import agent_loop
from hadavin_sdk.runtime.agent_loop import Runtime
from hadavin_sdk.store.protocol import NotFound, StaleState
from tests.test_s5_runtime import _doc, build

# ORACLE is written out here on purpose: the tests must not use the pattern under test to judge itself.
# `InvalidRunId` is looked up by name so that on the base commit (which has none) the tests FAIL when they run,
# not at collection.
ORACLE = re.compile(r"run-[0-9a-f]{32}")
InvalidRunId = getattr(agent_loop, "InvalidRunId", type("InvalidRunId", (ValueError,), {}))

AGENT, PRINCIPAL = "test-agent", "svc:test-agent"
GOOD = "run-" + "0123456789abcdef" * 2
# A shape a door may derive from a message id: "run-" + 28 hex + 4 hex = 36 characters.
DOOR_SHAPE = "run-" + "a1b2c3d" * 4 + format(7, "04x")


def _count_rows(rt, run_id):
    return len(rt.audit.events(run_id))


def test_t1_given_id_is_the_run_id(cfg_dir):
    rt, cfg = build(cfg_dir)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=GOOD)
    assert run.run_id == GOOD
    assert rt.store.get_run(GOOD).run_id == GOOD


class ForwardingStore:
    """Forwards every attribute to the real store; subclasses change one method. The tests judge the outcome (run
    rows, audit rows, model calls), not which store methods ran in which order."""

    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)


class SpyLimits:
    """Counts the budget and kill-switch calls (the base has no fake meter, so this stands for the meter hold)."""

    def __init__(self, inner):
        self._inner, self.calls = inner, []

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append(name)
            return attr(*args, **kwargs)

        return call


def _all_runs(store):
    """Every run in the store, through the public listing, whatever its state."""
    later = now() + timedelta(days=1)
    return [r for st in RunState for r in store.list_runs(st, later, limit=1000)]


def _foreign(rt, **diff):
    """Store a run with id GOOD that differs from the call (AGENT, PRINCIPAL, trigger_ref 'm-1') in `diff`."""
    kw = {
        "agent_id": AGENT,
        "principal_id": PRINCIPAL,
        "trigger_kind": "event",
        "trigger_ref": "m-1",
    }
    kw.update(diff)
    run = Run(run_id=GOOD, **kw)
    rt.store.create_run(run)
    return run


def test_d0_one_run_per_message_at_the_choke_point(cfg_dir):
    """Fails BY ASSERTION on the base (no `run_id` parameter there: the call is made without it, so two run rows
    exist) and on the first peel head (the second call raised StaleState). `run_id` is passed only when the parameter
    exists. The document stops before the model, so the result does not depend on the recording."""
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "injected.txt")
    kw = {"run_id": GOOD} if "run_id" in inspect.signature(Runtime.handle).parameters else {}
    first = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", **kw)
    second, refused = None, None
    try:
        second = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", **kw)
    except StaleState as exc:  # turned into an assertion below, so the row fails by assertion
        refused = exc
    assert refused is None, f"the second call for the same message raised {type(refused).__name__}"
    assert len(_all_runs(rt.store)) == 1  # the base has two
    assert isinstance(second, Run) and second.run_id == first.run_id


def test_d2_same_message_twice_returns_the_existing_run(cfg_dir):
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "chat.txt")
    first = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    assert first.run_id == GOOD and first.state == RunState.NO_ACTION
    calls, notes = len(rt.llm.calls), _count_rows(rt, GOOD)
    assert calls == 1 and notes > 0
    rt.limits = SpyLimits(rt.limits)
    second = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    assert isinstance(second, Run) and ORACLE.fullmatch(second.run_id)
    assert second.run_id == GOOD
    assert second.state == RunState.NO_ACTION  # the stored run, not a new one
    assert len(rt.llm.calls) == calls  # no second model call, so no second spend
    assert _count_rows(rt, GOOD) == notes  # no second "received" note
    assert rt.limits.calls == []  # no limits check, no meter hold
    assert len(_all_runs(rt.store)) == 1


@pytest.mark.parametrize(
    "diff",
    [
        {"agent_id": "other-agent"},
        {"principal_id": "svc:other"},
        {"trigger_ref": "m-2"},
    ],
    ids=["foreign-agent", "foreign-principal", "foreign-trigger-ref"],
)
def test_d2b_direct_a_foreign_run_is_never_returned(cfg_dir, diff):
    rt, cfg = build(cfg_dir)
    stored = _foreign(rt, **diff)
    rt.limits = SpyLimits(rt.limits)
    with pytest.raises(StaleState):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=GOOD)
    assert rt.llm.calls == []
    assert rt.audit.events() == []  # no note of any run
    assert rt.limits.calls == []
    assert rt.store.get_run(GOOD) == stored  # untouched
    assert len(_all_runs(rt.store)) == 1


def test_d2c_direct_a_foreign_run_created_inside_create_run(cfg_dir):
    """Another writer stores a run with this id after the caller built its own and just before `create_run` runs:
    `create_run` refuses, the stored run is not the caller's, so `StaleState` and nothing else is written."""
    rt, cfg = build(cfg_dir)

    class RacingStore(ForwardingStore):
        def create_run(self, run):
            self._inner.create_run(run.model_copy(update={"agent_id": "other-agent"}))
            return self._inner.create_run(run)

    rt.store, rt.limits = RacingStore(rt.store), SpyLimits(rt.limits)
    with pytest.raises(StaleState):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=GOOD)
    assert rt.llm.calls == []
    assert rt.audit.events() == []
    assert rt.limits.calls == []
    assert rt.store.get_run(GOOD).agent_id == "other-agent"
    assert rt.store.get_run(GOOD).state == RunState.RECEIVED
    assert len(_all_runs(rt.store)) == 1


def test_d2d_direct_the_existing_run_vanished_is_still_stale(cfg_dir):
    """`create_run` says the id exists but `get_run` finds nothing (it was removed in between): the typed refusal
    `StaleState` is raised, not `NotFound`, and nothing else is written."""
    rt, cfg = build(cfg_dir)

    class VanishingStore(ForwardingStore):
        def create_run(self, run):
            raise StaleState(f"run exists: {run.run_id}")

    rt.store = VanishingStore(rt.store)
    with pytest.raises(StaleState):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=GOOD)
    assert rt.llm.calls == [] and rt.audit.events() == []


def _race_once(cfg_dir, rid):
    """Two threads handle one message with one id; both reach `create_run` together. Returns what they got."""
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "chat.txt")
    gate = threading.Barrier(2)

    class GatedStore(ForwardingStore):
        def create_run(self, run):
            gate.wait(timeout=10)
            return self._inner.create_run(run)

    rt.store = GatedStore(rt.store)
    got, errors = [], []

    def go():
        try:
            got.append(rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=rid))
        except Exception as exc:  # noqa: BLE001 - reported by the caller's assertion
            errors.append(exc)

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return rt, got, errors


def test_race_two_threads_same_message_one_run(cfg_dir):
    """One thread creates the run and works, the other gets the same run back: one run, one model call, no error."""
    for n in range(10):
        rid = "run-" + format(n, "032x")
        rt, got, errors = _race_once(cfg_dir, rid)
        assert not errors, errors
        assert [r.run_id for r in got] == [rid, rid]  # the loser's run id is the winner's
        assert all(r.state in set(RunState) for r in got)  # a valid state, maybe still in progress
        assert rt.store.get_run(rid).state == RunState.NO_ACTION
        assert len(_all_runs(rt.store)) == 1
        assert len(rt.llm.calls) == 1


def test_t3_without_run_id_ids_are_fresh_and_well_formed(cfg_dir):
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "injected.txt")  # stops before the model, so the recording is not used up
    a = rt.handle(AGENT, PRINCIPAL, doc)
    b = rt.handle(AGENT, PRINCIPAL, doc, run_id=None)
    assert a.run_id != b.run_id
    assert ORACLE.fullmatch(a.run_id) and ORACLE.fullmatch(b.run_id)


HOSTILE = [
    "",
    "run-",
    "run-" + "a" * 31,
    "run-" + "a" * 33,
    "run-" + "A" * 32,
    "run-" + "g" * 32,
    "../" + "a" * 33,
    GOOD + "\n",
    "\n" + GOOD,
    GOOD + " ",
    "run-" + "a" * 31 + "\x00",
    "run-" + "a" * 31 + chr(0x661),  # Arabic-Indic digit one
    GOOD + ":1",
    "a" * 36,
    "ru-" + "a" * 33,
    "run_" + "a" * 32,
    123,
    GOOD.encode(),
    ["x"],
]


@pytest.mark.parametrize("bad", HOSTILE, ids=[repr(h)[:30] for h in HOSTILE])
def test_t4_hostile_ids_are_refused_before_any_write(cfg_dir, bad):
    rt, cfg = build(cfg_dir)
    with pytest.raises(InvalidRunId):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=bad)
    assert rt.llm.calls == []
    assert rt.audit.events() == []  # no note of any run: nothing was written
    if isinstance(bad, str):
        with pytest.raises(NotFound):
            rt.store.get_run(bad)


def test_t5_accepts_exactly_the_pattern(cfg_dir):
    """Every one-character damage (replace, insert, cut) of a valid id, at every position, with an awkward alphabet."""
    alphabet = "0123456789abcdefABCDEFg-_:/. \n\x00" + chr(0x661)
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "injected.txt")  # stops before the model, so the recording is not used up
    cases = {GOOD}
    for k in range(len(GOOD) + 1):
        cases.add(GOOD[:k] + GOOD[k + 1 :])
        for c in alphabet:
            cases.add(GOOD[:k] + c + GOOD[k + 1 :])
            cases.add(GOOD[:k] + c + GOOD[k:])
    ok = bad = 0
    for text in sorted(cases):
        if ORACLE.fullmatch(text):
            assert rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=text).run_id == text
            ok += 1
        else:
            with pytest.raises(InvalidRunId):
                rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=text)
            bad += 1
    assert ok > 5 and bad > 500  # both branches were really exercised


def test_t6_a_derived_id_shape_is_accepted(cfg_dir):
    rt, cfg = build(cfg_dir)
    assert len(DOOR_SHAPE) == 36
    assert (
        rt.handle(
            AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), trigger_ref="m-1", run_id=DOOR_SHAPE
        ).run_id
        == DOOR_SHAPE
    )


def test_t7_run_id_is_keyword_only_with_default_none():
    p = inspect.signature(Runtime.handle).parameters["run_id"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None


def test_t8_model_pattern_is_the_written_out_oracle():
    assert hasattr(models, "RUN_ID_PATTERN")  # fails by assertion on the base
    assert models.RUN_ID_PATTERN.pattern == ORACLE.pattern
    for _ in range(50):  # the id maker and the pattern agree
        assert models.RUN_ID_PATTERN.fullmatch(models.new_id("run"))


def test_t9_order_unqualified_first_then_invalid_run_id(cfg_dir):
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "chat.txt")
    with pytest.raises(
        agent_loop.Unqualified
    ):  # unknown agent AND a bad id: the agent is judged first
        rt.handle("no-such-agent", PRINCIPAL, doc, trigger_ref="m-1", run_id="bad")
    with pytest.raises(InvalidRunId):  # known agent, bad id
        rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id="bad")
    assert not issubclass(agent_loop.Unqualified, ValueError)  # so the two are told apart by type


@pytest.mark.parametrize(
    "ref", ["-", "", " ", "\t\n", " - "], ids=["dash", "empty", "space", "tab-nl", "padded-dash"]
)
def test_t10_run_id_with_a_trigger_ref_that_names_no_message_is_refused(cfg_dir, ref):
    """Squatting: with the default trigger_ref "-" every caller of one agent and principal is "the same message", so
    a caller that guesses an id would be handed the run another caller started. Refused before any write."""
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "chat.txt")
    with pytest.raises(InvalidRunId):
        rt.handle(AGENT, PRINCIPAL, doc, trigger_ref=ref, run_id=GOOD)
    assert rt.llm.calls == [] and rt.audit.events() == []
    assert _all_runs(rt.store) == []
    with pytest.raises(InvalidRunId):  # the default trigger_ref is the same refusal
        rt.handle(AGENT, PRINCIPAL, doc, run_id=GOOD) if ref == "-" else rt.handle(
            AGENT, PRINCIPAL, doc, trigger_ref=ref, run_id=GOOD
        )


def test_t10b_a_run_stored_under_the_dash_is_never_returned_to_a_squatter(cfg_dir):
    rt, cfg = build(cfg_dir)
    stored = _foreign(rt, trigger_ref="-")  # same agent, principal, kind: only the ref is the dash
    with pytest.raises(InvalidRunId):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), run_id=GOOD)
    assert rt.store.get_run(GOOD) == stored and rt.llm.calls == []


def test_t10c_without_run_id_the_dash_still_works(cfg_dir):
    rt, cfg = build(cfg_dir)
    assert rt.handle(AGENT, PRINCIPAL, _doc(cfg, "injected.txt")).trigger_ref == "-"
    assert rt.handle(AGENT, PRINCIPAL, _doc(cfg, "injected.txt"), run_id=None).trigger_ref == "-"


@pytest.fixture
def pg_store(tmp_path):
    """The Postgres store kind (skips without HADAVIN_TEST_PG_DSN)."""
    from tests.contracts.kinds import (
        KINDS,
        store_postgres,  # noqa: F401 - registers the kind
    )

    made = KINDS["store"]["postgres"](tmp_path)
    store = next(made)
    yield store
    next(made, None)


def test_d2_on_postgres_same_message_twice_returns_the_existing_run(cfg_dir, pg_store):
    rt, cfg = build(cfg_dir)
    rt.store = pg_store  # the runs live in the database; limits keep their own memory store
    doc = _doc(cfg, "chat.txt")
    first = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    calls, notes = len(rt.llm.calls), _count_rows(rt, GOOD)
    second = rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    assert second.run_id == first.run_id == GOOD and second.state == RunState.NO_ACTION
    assert len(rt.llm.calls) == calls and _count_rows(rt, GOOD) == notes
    _foreign_args = {"agent_id": AGENT, "principal_id": PRINCIPAL, "trigger_ref": "m-2"}
    assert {k: getattr(rt.store.get_run(GOOD), k) for k in _foreign_args} != _foreign_args
    with pytest.raises(StaleState):  # same id, another message
        rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-2", run_id=GOOD)
    assert len(rt.llm.calls) == calls
