"""AK1-a: the pipeline step contract (`hadavin_sdk/pipeline/step.py`), rows S1 to S14 of the AK1 ticket plus the class tests
that go with them (ids, tenant, readers, `tenant_key`, the records, `run_step`).

Made-up data only; a canary is a made-up value that must never appear where text is not allowed. Fake sinks only.

On a base commit that has no `pipeline` package this file still COLLECTS (the import below is guarded) and every row fails by
assertion or by `AttributeError` on the missing module; row S8 (`tenant_key`) falls back to the naive `"/".join(...)` key so
that it fails by ASSERTION (the weak fail-before of the ticket). The mutants of this file are in `tests/ak1a_mutants.py`.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import logging
import random
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.audit.local_dir import LocalDirSink
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.models import AuditEvent, new_id

try:  # a base commit has no such module: the rows then fail, the file still collects
    from hadavin_sdk.pipeline import step as S
except ModuleNotFoundError:  # pragma: no cover - only on a base without the package
    S = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
CANARY = "canary-" + "9f3a7c"  # made-up value, built from parts
ITEM = "doc-" + "0" * 31 + "1"
READERS = frozenset({"person-1", "role:analyst"})


def naive_tenant_key(tenant, *parts):  # the old, ambiguous shape
    return "/".join((tenant, *parts))


def tenant_key_or_naive():
    return S.tenant_key if S is not None else naive_tenant_key


class Sink:
    """A fake audit sink: records every event in write order; can refuse the intent or break the outcome."""

    def __init__(self, fail_intent=False, break_outcome=False, intent_error=None):
        self.intents: list[AuditEvent] = []
        self.outcomes: list[AuditEvent] = []
        self.fail_intent = fail_intent
        self.break_outcome = break_outcome
        self.intent_error = intent_error or AuditUnavailable("down")
        self.lock = threading.Lock()

    def write_intent(self, event):
        if self.fail_intent:
            raise self.intent_error
        with self.lock:
            self.intents.append(event)
        return event.event_id

    def write_outcome(self, event):
        if self.break_outcome:
            raise RuntimeError("off contract: " + CANARY)
        with self.lock:
            self.outcomes.append(event)
        return event.event_id

    def reconcile(self):
        return 0

    def verify_object(self, key):
        return True

    def events(self, run_id=None):
        return [*self.intents, *self.outcomes]


class FnStep:
    """A step from a function; counts its calls."""

    def __init__(self, fn, name="probe_step"):
        self.name = name
        self.fn = fn
        self.calls = 0

    def run(self, inp):
        self.calls += 1
        return self.fn(inp)


def make_input(
    body="hello", readers=READERS, tenant="tenant-a", item=ITEM, run_id="run-1", agent="agent-1"
):
    return S.StepInput(item, tenant, readers, body, run_id, agent)


def out_for(inp, outcome=None, reason=None, body=None, **changes):
    outcome = outcome or S.Outcome.DONE
    fields = {
        "item_id": inp.item_id,
        "tenant": inp.tenant,
        "readers": inp.readers,
        "outcome": outcome,
        "reason": reason,
        "body": body,
        "run_id": inp.run_id,
        "agent_id": inp.agent_id,
    }
    fields.update(changes)
    return S.StepOutput(**fields)


def done(inp):
    return out_for(inp, body="result")


def run(fn, inp=None, sink=None, principal="trigger:probe"):
    inp = inp or make_input()
    sink = sink or Sink()
    step = FnStep(fn)
    return S.run_step(step, inp, audit=sink, principal=principal), sink, step


class Text(str):
    pass


# --- S1 tenant pattern ------------------------------------------------------------------------------------------------
def test_s1_tenant_pattern_accepts_and_refuses():
    for ok in ("tenant-a", "a", "0x", "a_b-c", "a" * 63):
        assert S.check_tenant(ok) == ok
    for bad in (
        "tenant-a\n",
        "Tenant-A",
        "",
        "a" * 64,
        Text("tenant-a"),
        b"tenant-a",
        "tenant-а",  # a Cyrillic look-alike of `a`
        "-a",
        "_a",
        "a b",
        "a/b",
        "a:b",
        None,
        1,
    ):
        with pytest.raises(ValueError, match="tenant"):
            S.check_tenant(bad)


def test_s1_the_constructor_and_tenant_key_refuse_a_bad_tenant_without_echoing_it():
    for bad in ("tenant-a\n", "Tenant-A", "", Text("tenant-a"), CANARY.upper()):
        with pytest.raises(ValueError) as caught:
            make_input(tenant=bad)
        assert "tenant" in str(caught.value) and CANARY not in str(caught.value).lower()
        with pytest.raises(ValueError):
            S.tenant_key(bad)


def test_s1_tenant_pattern_matches_a_reference_over_seeded_random_text():
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    alphabet = "abcXYZ019_-/: \nаé١"
    first_ok = set("abcdefghijklmnopqrstuvwxyz0123456789")
    rest_ok = first_ok | {"_", "-"}
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 70)))
        expected = 1 <= len(text) <= 63 and text[0] in first_ok and all(c in rest_ok for c in text)
        try:
            S.check_tenant(text)
            accepted = True
        except ValueError:
            accepted = False
        assert accepted == expected, "the tenant check disagrees with the reference"


# --- S2 readers -------------------------------------------------------------------------------------------------------
def test_s2_readers_refuse_the_bad_and_accept_the_limits():
    for bad in (
        frozenset(),
        frozenset({"*"}),
        frozenset({"a b"}),
        frozenset({"person-1\n"}),
        frozenset({"-x"}),
        frozenset({"x" * 129}),
        frozenset({1}),
        frozenset({b"person-1"}),
        frozenset({Text("person-1")}),
        {"person-1"},  # a plain set is not a frozenset
        ["person-1"],
        None,
        frozenset(f"r{i}" for i in range(1001)),
    ):
        with pytest.raises(ValueError, match="readers"):
            S.check_readers(bad)
    assert len(S.check_readers(frozenset({"r"}))) == 1
    assert len(S.check_readers(frozenset(f"r{i}" for i in range(1000)))) == 1000
    assert defaults.PIPELINE_MAX_READERS == 1000
    assert S.check_readers(frozenset({"a.b:c@d-e_f", "A" + "z" * 127})) is not None


def test_s2_a_frozenset_subclass_is_refused():
    class Fs(frozenset):
        pass

    with pytest.raises(ValueError, match="readers"):
        S.check_readers(Fs({"person-1"}))


def test_s2_the_input_and_the_output_refuse_empty_readers():
    inp = make_input()
    with pytest.raises(ValueError, match="readers"):
        make_input(readers=frozenset())
    with pytest.raises(ValueError, match="readers"):
        out_for(inp, readers=frozenset())


# --- S3 one final state -----------------------------------------------------------------------------------------------
def _behaviours():
    needs = sorted(S.REASONS[S.Outcome.NEEDS_PERSON])
    refused = sorted(S.REASONS[S.Outcome.REFUSED])
    table = [("done", lambda inp: done(inp))]
    table += [
        ("needs_" + r, lambda inp, r=r: out_for(inp, S.Outcome.NEEDS_PERSON, r)) for r in needs
    ]
    table += [
        ("refused_" + r, lambda inp, r=r: out_for(inp, S.Outcome.REFUSED, r)) for r in refused
    ]
    for exc in (ValueError, KeyError, RuntimeError, OSError):

        def boom(inp, exc=exc):
            raise exc(CANARY)

        table.append(("raise_" + exc.__name__, boom))
    table.append(("wrong_type_dict", lambda inp: {"outcome": "done"}))
    table.append(("wrong_type_str", lambda inp: "done"))
    table.append(("none", lambda inp: None))
    return table


def test_s3_exactly_one_final_state_over_500_seeded_behaviours():
    table = _behaviours()
    rng = random.Random(7771)  # noqa: S311 - a seeded test generator, not a secret
    seen = set()
    for _ in range(500):
        name, fn = rng.choice(table)
        seen.add(name)
        intent_fails = rng.random() < 0.1
        sink = Sink(fail_intent=intent_fails)
        step = FnStep(fn)
        out = S.run_step(step, make_input(), audit=sink, principal="trigger:probe")
        assert type(out) is S.StepOutput
        assert len(sink.intents) <= 1 and len(sink.outcomes) <= 1
        if intent_fails:
            assert (out.outcome, out.reason, out.body) == (
                S.Outcome.NEEDS_PERSON,
                "audit_unavailable",
                None,
            )
            assert sink.events() == [] and step.calls == 0
        else:
            assert len(sink.intents) == 1 and len(sink.outcomes) == 1 and step.calls == 1
            assert sink.outcomes[0].decision == out.outcome.value
            assert sink.outcomes[0].error_code == out.reason
    assert seen == {n for n, _ in table}, "the seeded draw must reach every behaviour"


def test_s3_a_sink_that_raises_another_error_on_the_intent_also_stops_the_step():
    sink = Sink(fail_intent=True, intent_error=RuntimeError("off contract " + CANARY))
    out, _, step = run(done, sink=sink)
    assert (out.outcome, out.reason) == (S.Outcome.NEEDS_PERSON, "audit_unavailable")
    assert step.calls == 0


# --- S4 closed reasons ------------------------------------------------------------------------------------------------
def test_s4_the_reason_sets_are_exactly_the_ticket_sets():
    assert S.REASONS[S.Outcome.DONE] == frozenset()
    assert S.REASONS[S.Outcome.NEEDS_PERSON] == frozenset(
        {
            "step_error",
            "low_quality",
            "unreadable",
            "over_budget",
            "meter_unavailable",
            "masking_refused",
            "outbound_refused",
            "audit_unavailable",
            "policy",
        }
    )
    assert S.REASONS[S.Outcome.REFUSED] == frozenset({"invalid_input", "forbidden", "duplicate"})
    assert set(S.REASONS) == set(S.Outcome)
    with pytest.raises(TypeError):
        S.REASONS[S.Outcome.DONE] = frozenset({"x"})  # type: ignore[index]


def test_s4_a_reason_outside_its_outcome_is_refused():
    inp = make_input()
    cases = [
        (S.Outcome.DONE, "step_error"),
        (S.Outcome.DONE, ""),
        (S.Outcome.NEEDS_PERSON, "duplicate"),
        (S.Outcome.NEEDS_PERSON, "step_error\n"),
        (S.Outcome.NEEDS_PERSON, None),
        (S.Outcome.NEEDS_PERSON, ""),
        (S.Outcome.REFUSED, "step_error"),
        (S.Outcome.REFUSED, None),
        (S.Outcome.REFUSED, Text("duplicate")),
    ]
    for outcome, reason in cases:
        with pytest.raises(ValueError, match="reason"):
            out_for(inp, outcome, reason)
    # every allowed pair builds
    for outcome, reasons in S.REASONS.items():
        for reason in reasons or {None}:
            assert out_for(inp, outcome, reason).reason == reason


def test_s4_the_outcome_must_be_an_outcome_and_only_done_carries_a_body():
    inp = make_input()
    with pytest.raises(ValueError, match="outcome"):
        out_for(inp, "done")  # an equal string is not an Outcome
    with pytest.raises(ValueError, match="body"):
        out_for(inp, S.Outcome.NEEDS_PERSON, "policy", body="text")
    with pytest.raises(ValueError, match="body"):
        out_for(inp, S.Outcome.REFUSED, "forbidden", body=b"x")
    assert out_for(inp, body=None).body is None  # done without a body is allowed
    assert out_for(inp, body=b"\xff\xfe").body == b"\xff\xfe"
    with pytest.raises(ValueError, match="UTF-8"):
        out_for(inp, body="\ud800")


def test_s4_every_runner_error_row_is_a_closed_needs_person_reason():
    assert S.REASON_BY_ERROR[AuditUnavailable] == "audit_unavailable"
    for exc, reason in S.REASON_BY_ERROR.items():
        assert issubclass(exc, BaseException)
        assert reason in S.REASONS[S.Outcome.NEEDS_PERSON], "a row would crash the runner"


# --- S5 a step cannot widen -------------------------------------------------------------------------------------------
def _widened(inp):
    return {
        "reader not in input": lambda: out_for(inp, readers=inp.readers | {"person-9"}),
        "other tenant": lambda: out_for(inp, tenant="tenant-b"),
        "other item": lambda: out_for(inp, item_id="doc-" + "0" * 31 + "2"),
        "other run id": lambda: out_for(inp, run_id="run-2"),
        "run id dropped": lambda: out_for(inp, run_id=None),
        "other agent": lambda: out_for(inp, agent_id="agent-2"),
    }


def test_s5_an_output_that_changes_identity_or_widens_is_a_step_error_with_no_body():
    inp = make_input()
    for label, build in _widened(inp).items():
        out, sink, _ = run(lambda _i, build=build: build(), inp=inp)
        assert (out.outcome, out.reason, out.body) == (
            S.Outcome.NEEDS_PERSON,
            "step_error",
            None,
        ), label
        assert (
            out.readers == inp.readers and out.tenant == inp.tenant and out.item_id == inp.item_id
        ), label
        assert sink.outcomes[0].error_code == "step_error", label


def test_s5_narrowing_and_keeping_the_readers_are_allowed():
    inp = make_input()
    for readers in (inp.readers, frozenset({"person-1"})):
        out, _, _ = run(lambda i, r=readers: out_for(i, readers=r, body="x"), inp=inp)
        assert out.outcome is S.Outcome.DONE and out.readers == readers and out.body == "x"


def test_s5_a_record_built_around_the_constructor_is_refused_by_the_runner():
    inp = make_input()

    def forged_reason(i):
        out = out_for(i, S.Outcome.NEEDS_PERSON, "policy")
        object.__setattr__(out, "reason", "bogus")
        return out

    def forged_body(i):
        out = out_for(i, S.Outcome.REFUSED, "forbidden")
        object.__setattr__(out, "body", "smuggled")
        return out

    def forged_readers(i):
        out = done(i)
        object.__setattr__(out, "readers", frozenset({"*"}))
        return out

    def empty_shell(i):
        return object.__new__(S.StepOutput)  # no attribute set at all

    class Sub(S.StepOutput):
        pass

    def subclass(i):
        return Sub(i.item_id, i.tenant, i.readers, S.Outcome.DONE, None, "x", i.run_id, i.agent_id)

    for build in (forged_reason, forged_body, forged_readers, empty_shell, subclass):
        out, _, _ = run(build, inp=inp)
        assert (out.outcome, out.reason, out.body) == (S.Outcome.NEEDS_PERSON, "step_error", None)


# --- S6 exceptions ----------------------------------------------------------------------------------------------------
def _everything_written(out, sink, caplog):
    parts = [repr(out), str(out), caplog.text]
    parts += [r.getMessage() + repr(r.args) for r in caplog.records]
    for event in sink.events():
        parts.append(event.model_dump_json())
    for field in ("item_id", "tenant", "outcome", "reason", "body", "run_id", "agent_id"):
        parts.append(repr(getattr(out, field)))
    return "\n".join(parts)


def test_s6_ordinary_exceptions_end_in_step_error_and_leave_no_text(caplog):
    for exc in (ValueError, KeyError, RuntimeError, OSError):
        caplog.clear()

        def boom(_i, exc=exc):
            try:
                raise exc(CANARY)
            except exc as inner:
                raise exc(CANARY + " again") from inner

        with caplog.at_level(logging.DEBUG):
            out, sink, _ = run(boom)
        assert (out.outcome, out.reason, out.body) == (S.Outcome.NEEDS_PERSON, "step_error", None)
        assert CANARY not in _everything_written(out, sink, caplog)


def test_s6_audit_unavailable_raised_by_the_step_gives_audit_unavailable(caplog):
    class DeeperDown(AuditUnavailable):
        pass

    for exc in (AuditUnavailable, DeeperDown):

        def boom(_i, exc=exc):
            raise exc(CANARY)

        with caplog.at_level(logging.DEBUG):
            out, sink, _ = run(boom)
        assert (out.outcome, out.reason) == (S.Outcome.NEEDS_PERSON, "audit_unavailable")
        assert CANARY not in _everything_written(out, sink, caplog)
        assert len(sink.intents) == 1 and len(sink.outcomes) == 1


def test_s6_the_log_names_the_error_class_only(caplog):
    with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.pipeline.step"):
        run(lambda _i: (_ for _ in ()).throw(KeyError(CANARY)))
    assert "KeyError" in caplog.text and CANARY not in caplog.text


# --- S7 stop requests -------------------------------------------------------------------------------------------------
class OtherStop(BaseException):
    pass


@pytest.mark.parametrize(
    "stop", [KeyboardInterrupt, SystemExit, GeneratorExit, asyncio.CancelledError, OtherStop]
)
def test_s7_stop_requests_propagate_unchanged_after_a_best_effort_outcome(stop):
    raised = stop(CANARY)

    def boom(_i):
        raise raised

    sink = Sink()
    with pytest.raises(stop) as caught:
        S.run_step(FnStep(boom), make_input(), audit=sink, principal="trigger:probe")
    assert caught.value is raised
    assert len(sink.intents) == 1 and len(sink.outcomes) == 1
    assert (sink.outcomes[0].decision, sink.outcomes[0].error_code) == (
        "needs_person",
        "step_error",
    )
    assert CANARY not in sink.outcomes[0].model_dump_json()


def test_s7_off_contract_a_sink_that_raises_does_not_replace_the_stop_request():
    # OFF CONTRACT on purpose: `write_outcome` never raises by contract (audit/protocol.py); this sink does.
    raised = KeyboardInterrupt()

    def boom(_i):
        raise raised

    with pytest.raises(KeyboardInterrupt) as caught:
        S.run_step(
            FnStep(boom), make_input(), audit=Sink(break_outcome=True), principal="trigger:probe"
        )
    assert caught.value is raised


def test_s7_off_contract_a_sink_that_raises_does_not_lose_the_output(caplog):
    with caplog.at_level(logging.DEBUG):
        out, _, _ = run(done, sink=Sink(break_outcome=True))
    assert out.outcome is S.Outcome.DONE and out.body == "result"
    assert CANARY not in caplog.text


# --- S8 tenant key one to one -----------------------------------------------------------------------------------------
def _decode(key):
    """A decoder written from the ticket's grammar; if it can read every key back, no two tuples share a key."""
    assert key.startswith("t")
    rest = key[1:]
    n, _, rest = rest.partition(":")
    parts = [rest[: int(n)]]
    rest = rest[int(n) :]
    while rest:
        assert rest[0] == "/"
        n, _, rest = rest[1:].partition(":")
        parts.append(rest[: int(n)])
        rest = rest[int(n) :]
    return tuple(parts)


def test_s8_tenant_key_is_one_to_one_over_2000_seeded_tuples():
    tenant_key = tenant_key_or_naive()
    rng = random.Random(4242)  # noqa: S311 - a seeded test generator, not a secret
    alphabet = "ab/:19 \né中"
    tuples = set()
    while len(tuples) < 2000:
        tenant = rng.choice(["tenant-a", "tenant-b", "t1", "a1", "a-1"])
        parts = tuple(
            "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
            for _ in range(rng.randint(0, 3))
        )
        tuples.add((tenant, *parts))
    keys = {t: tenant_key(*t) for t in tuples}
    assert len(set(keys.values())) == 2000, "two different argument lists gave one key"
    if S is not None:
        assert all(_decode(k) == t for t, k in keys.items())


def test_s8_the_two_ambiguous_tuples_differ():
    tenant_key = tenant_key_or_naive()
    assert tenant_key("tenant-a", "x/y") != tenant_key("tenant-a", "x", "y")
    assert tenant_key("tenant-a", "ab", "c") != tenant_key("tenant-a", "a", "bc")


def test_s8_the_key_has_the_ticket_shape():
    assert S.tenant_key("tenant-a") == "t8:tenant-a"
    assert S.tenant_key("tenant-a", "x/y") == "t8:tenant-a/3:x/y"
    assert S.tenant_key("tenant-a", "src", ITEM) == f"t8:tenant-a/3:src/{len(ITEM)}:{ITEM}"
    # tenant comes first, always; characters are counted, not bytes
    assert S.tenant_key("tenant-a", "é") == "t8:tenant-a/1:é"


def test_s8_a_bad_part_is_refused_without_echoing_it():
    limit = defaults.PIPELINE_KEY_PART_MAX_CHARS
    assert limit == 512
    assert S.tenant_key("tenant-a", "x" * limit)
    for bad in ("", "x" * (limit + 1), b"x", Text("x"), None, 1):
        with pytest.raises(ValueError) as caught:
            S.tenant_key("tenant-a", bad)
        assert "part" in str(caught.value)
    with pytest.raises(ValueError) as caught:
        S.tenant_key("tenant-a", CANARY * 100)
    assert CANARY not in str(caught.value)


# --- S9 no text in repr -----------------------------------------------------------------------------------------------
def test_s9_no_text_in_repr_str_format_or_log(caplog):
    reader = "reader-" + CANARY
    inp = make_input(body="body " + CANARY, readers=frozenset({reader}))
    out = out_for(inp, body="answer " + CANARY)
    for text in (
        repr(inp),
        str(inp),
        f"{inp}",
        f"{inp!r}",
        "%s" % (inp,),  # noqa: UP031 - the percent path must stay clean too
        format(inp),
        repr(out),
        str(out),
        f"{out}",
    ):
        assert CANARY not in text
    assert "readers=1" in repr(inp) and inp.item_id in repr(inp) and inp.tenant in repr(inp)
    assert inp.content_sha256 in repr(inp)
    assert "has_body=True" in repr(out)

    def writes_back(i):
        return out_for(i, body="answer " + CANARY)

    with caplog.at_level(logging.DEBUG):
        o, sink, _ = run(writes_back, inp=inp)
    log_text = caplog.text + "".join(r.getMessage() + repr(r.args) for r in caplog.records)
    assert CANARY not in log_text
    for event in sink.events():
        assert CANARY not in event.model_dump_json(), "audit holds hashes, counts and codes only"
    assert CANARY not in repr(o)


# --- S10 audit order --------------------------------------------------------------------------------------------------
def _check_audit_order(sink, events_of):
    inp = make_input()
    seen_by_step = []

    def step_fn(i):
        seen_by_step.extend(e.operation for e in events_of())
        return out_for(i, S.Outcome.NEEDS_PERSON, "low_quality")

    step = FnStep(step_fn, name="read_doc")
    out = S.run_step(step, inp, audit=sink, principal="trigger:probe")
    assert seen_by_step == ["read_doc"], "the intent event must exist before the step runs"
    events = events_of()
    assert len(events) == 2
    intent, outcome = events
    key = S.tenant_key(inp.tenant, inp.item_id)
    for event in events:
        assert (event.domain, event.operation, event.principal, event.source) == (
            "pipeline",
            "read_doc",
            "trigger:probe",
            "step",
        )
        assert event.object_ref == key and event.run_id == "run-1"
    assert intent.inputs_hash == inp.content_sha256 and intent.decision is None
    assert (outcome.decision, outcome.error_code) == (out.outcome.value, out.reason)
    assert outcome.decision == "needs_person" and outcome.error_code == "low_quality"
    assert outcome.result == f"readers={len(out.readers)}"


def test_s10_audit_order_on_the_recording_sink():
    sink = Sink()
    _check_audit_order(sink, sink.events)


def test_s10_audit_order_on_the_local_folder_sink(tmp_path):
    sink = LocalDirSink(tmp_path / "audit")
    _check_audit_order(sink, sink.events)


def test_s10_audit_order_on_the_chain_sink(tmp_path):
    from tests.contracts.kinds import (
        KINDS,
        audit_chain,  # noqa: F401 - registers the kinds
    )

    sink = KINDS["audit"]["chain"](tmp_path)
    _check_audit_order(sink, sink.events)


def test_s10_a_failed_intent_means_the_step_is_never_called():
    sink = Sink(fail_intent=True)
    out, _, step = run(done, sink=sink)
    assert step.calls == 0 and sink.events() == []
    assert (out.outcome, out.reason, out.body) == (
        S.Outcome.NEEDS_PERSON,
        "audit_unavailable",
        None,
    )


def test_s10_the_dash_stands_for_a_missing_run_id():
    sink = Sink()
    run(done, inp=make_input(run_id=None), sink=sink)
    assert {e.run_id for e in sink.events()} == {"-"}


# --- S11 runner threads -----------------------------------------------------------------------------------------------
def test_s11_eight_threads_one_shared_sink_each_gets_its_own_two_events():
    sink = Sink()
    barrier = threading.Barrier(8)
    results: dict[int, object] = {}
    errors: list[BaseException] = []

    def worker(n):
        try:
            item = f"doc-{n:032x}"
            inp = make_input(body=f"body {n}", item=item, readers=frozenset({f"person-{n}"}))

            def fn(i):
                barrier.wait(timeout=20)  # all eight steps run at the same moment
                return out_for(i, body=f"result {n}")

            results[n] = S.run_step(FnStep(fn), inp, audit=sink, principal=f"trigger:{n}")
        except BaseException as exc:  # noqa: BLE001 - reported on the main thread
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not errors and all(not t.is_alive() for t in threads)
    for n in range(8):
        key = S.tenant_key("tenant-a", f"doc-{n:032x}")
        mine = [e for e in sink.events() if e.object_ref == key]
        assert [e.decision for e in mine] == [None, "done"]
        assert {e.principal for e in mine} == {f"trigger:{n}"}
        assert results[n].body == f"result {n}" and results[n].readers == {f"person-{n}"}
    assert len(sink.intents) == 8 and len(sink.outcomes) == 8


# --- S12 item ids -----------------------------------------------------------------------------------------------------
def test_s12_item_ids():
    assert S.check_item_id(new_id("doc")) is not None
    assert S.check_item_id("a-" + "f" * 32)
    assert S.check_item_id("a" * 24 + "-" + "0" * 32)
    for bad in (
        "doc-person-1@example.invalid",
        "doc-" + "0" * 32 + "\n",
        "doc-" + "A" * 32,
        "doc-" + "0" * 31,
        "doc-" + "0" * 33,
        "a" * 25 + "-" + "0" * 32,
        Text("doc-" + "0" * 32),
        b"doc-" + b"0" * 32,
        "Doc-" + "0" * 32,
        "1doc-" + "0" * 32,
        "x" + "doc-" + "0" * 32 + "x",
        "",
        None,
    ):
        with pytest.raises(ValueError, match="item_id"):
            S.check_item_id(bad)
        with pytest.raises(ValueError, match="item_id"):
            make_input(item=bad)


# --- S13 first match by MRO -------------------------------------------------------------------------------------------
class BaseFailure(RuntimeError):
    pass


class SubFailure(BaseFailure):
    pass


def test_s13_the_first_class_of_the_mro_found_in_the_table_wins(monkeypatch):
    monkeypatch.setattr(S, "REASON_BY_ERROR", {BaseFailure: "policy", SubFailure: "step_error"})

    def raise_(exc):
        def fn(_i):
            raise exc("x")

        return fn

    assert run(raise_(SubFailure))[0].reason == "step_error"
    assert run(raise_(BaseFailure))[0].reason == "policy"
    assert run(raise_(ValueError))[0].reason == "step_error"  # no match: step_error


# --- S14 content hash and lone surrogates (BN-8) ----------------------------------------------------------------------
def test_s14_content_hash_and_strict_utf8():
    with pytest.raises(ValueError) as caught:
        make_input(body="\ud800" + CANARY)
    assert type(caught.value) is ValueError, (
        "a plain ValueError, not the UnicodeEncodeError behind it"
    )
    assert str(caught.value) == "body: not valid UTF-8" and caught.value.__suppress_context__
    assert CANARY not in str(caught.value)
    raw = b"\x00\xffbinary"
    assert make_input(body=raw).content_sha256 == hashlib.sha256(raw).hexdigest()
    assert make_input(body="ab").content_sha256 == make_input(body=b"ab").content_sha256
    assert make_input(body="hé").content_sha256 == hashlib.sha256("hé".encode()).hexdigest()
    sink = Sink()
    inp = make_input(body="ab")
    run(done, inp=inp, sink=sink)
    assert sink.intents[0].inputs_hash == inp.content_sha256 == hashlib.sha256(b"ab").hexdigest()


# --- records and the runner: argument checks (class tests) -------------------------------------------------------------
def test_the_input_refuses_a_wrong_type_everywhere():
    good = (ITEM, "tenant-a", READERS, "x", "run-1", "agent-1")
    S.StepInput(*good)
    for index, bad in (
        (3, bytearray(b"x")),
        (3, Text("x")),
        (3, 5),
        (3, None),
        (4, ""),
        (4, "run\n1"),
        (4, "r" * 257),
        (4, Text("run-1")),
        (5, ""),
        (5, None),
        (5, "agent\x00"),
        (5, Text("agent-1")),
    ):
        args = list(good)
        args[index] = bad
        with pytest.raises((ValueError, TypeError)):
            S.StepInput(*args)
    assert S.StepInput(ITEM, "tenant-a", READERS, b"", None, "agent-1").body == b""


def test_the_records_are_frozen_and_slotted():
    inp = make_input()
    out = done(inp)
    for record in (inp, out):
        with pytest.raises(AttributeError):
            record.tenant = "tenant-b"  # type: ignore[misc]
        assert not hasattr(record, "__dict__")


def test_run_step_refuses_bad_arguments_before_any_event():
    sink = Sink()
    good = FnStep(done)
    with pytest.raises(ValueError, match="step.name"):
        S.run_step(FnStep(done, name="Bad Name"), make_input(), audit=sink, principal="p")
    with pytest.raises(TypeError):
        S.run_step(good, "not an input", audit=sink, principal="p")  # type: ignore[arg-type]
    for principal in ("", "p\n", "x" * 257, None, Text("p")):
        with pytest.raises(ValueError, match="principal"):
            S.run_step(good, make_input(), audit=sink, principal=principal)  # type: ignore[arg-type]
    assert sink.events() == [] and good.calls == 0
    assert S.STEP_NAME_PATTERN == r"[a-z][a-z0-9_]{0,39}"


# --- imports: the module needs nothing outside core and sends nothing ------------------------------------------------------
def test_the_step_module_imports_only_what_the_ticket_allows():
    tree = ast.parse((ROOT / "src/hadavin_sdk/pipeline/step.py").read_text("utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{a.name}" for a in node.names)
    own = {m for m in imported if m.startswith("hadavin_sdk")}
    assert own <= {
        "hadavin_sdk",
        "hadavin_sdk.defaults",
        "hadavin_sdk.audit.protocol",
        "hadavin_sdk.audit.protocol.AuditSink",
        "hadavin_sdk.audit.protocol.AuditUnavailable",
        "hadavin_sdk.models",
        "hadavin_sdk.models.AuditEvent",
        "hadavin_sdk.defaults.defaults",
    }, own
    network = {"socket", "ssl", "urllib", "http", "requests", "subprocess", "boto3", "psycopg"}
    assert not {m.split(".")[0] for m in imported} & network
    assert not any("outbound" in m or "backends" in m for m in own)


@pytest.mark.parametrize("module", ["hadavin_sdk.pipeline", "hadavin_sdk.pipeline.step"])
def test_the_module_imports_first_in_a_fresh_interpreter(module):
    done_ = subprocess.run(  # noqa: S603 - a fixed argument list, no shell
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r}); import {module}",
        ],
        cwd=ROOT,
        env={"PATH": ""},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done_.returncode == 0, done_.stderr[-300:]


def test_the_package_exports_exactly_what_ak_g2_needs():
    import hadavin_sdk.pipeline as P

    for name in (
        "TENANT_PATTERN",
        "ITEM_ID_PATTERN",
        "Readers",
        "tenant_key",
        "StepInput",
        "StepOutput",
        "Outcome",
        "REASONS",
        "Step",
        "run_step",
        "check_tenant",
        "check_readers",
    ):
        assert hasattr(P, name) and name in P.__all__, name
