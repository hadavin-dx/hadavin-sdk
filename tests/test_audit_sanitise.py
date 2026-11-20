"""Outside text (provider stop reason, tool name/error, executor ref and code) never crashes a run on a refused
AuditEvent: it is sanitised first, and `_note` itself falls back instead of raising."""

from __future__ import annotations

import pytest

from hadavin_sdk.models import AUDIT_FIELD_MAX, AuditEvent, Reply, RunResult, RunState, audit_code
from hadavin_sdk.store import MemoryStore
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg
from tests.test_k5_tools import _events, _execute_runtime

S = RunState


class StopLLM:
    def __init__(self, stop_reason: str) -> None:
        self.stop_reason = stop_reason

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        return Reply(text="x", stop_reason=self.stop_reason, model_id="fake-model")


def test_audit_code_shapes():
    assert audit_code("weird reason\n<x>") == "weird reason__x_"
    assert len(audit_code("a" * 5000)) == AUDIT_FIELD_MAX
    assert audit_code("") == "unknown" and audit_code(None) == "unknown"
    AuditEvent(run_id="r", domain="d", operation="o", principal=audit_code("a\nb"), source="s")


@pytest.mark.parametrize("stop", ["weird reason\n<x>", "z" * 5000])
def test_hostile_stop_reason_is_audited_and_the_run_ends(tmp_path, stop):
    store = MemoryStore()
    rt, _ = build_runtime(k5_cfg(tmp_path), StopLLM(stop), store=store)
    run = handle(rt)
    assert run.state in (S.NO_ACTION, S.NEEDS_PERSON)
    rows = _events(rt, run)
    assert rows and all("\n" not in (e.error_code or "") for e in rows)
    # a stop reason that does stop the run reaches the row through the same helper
    for reason in ("max_tokens", "refusal"):
        run = handle(build_runtime(k5_cfg(tmp_path), StopLLM(reason))[0])
        assert run.state == S.NEEDS_PERSON


def test_hostile_tool_name_is_audited_and_the_run_ends(tmp_path):
    llm = ScriptLLM([{"tool": "boom"}], tool_name="bad name\n<x>" + "q" * 300)
    rt, _ = build_runtime(k5_cfg(tmp_path), llm)
    run = handle(rt)
    assert run.state == S.NEEDS_PERSON
    assert any(e.domain == "tool" or e.domain == "run" for e in _events(rt, run))


def test_executor_ref_and_code_with_spaces_and_newlines_are_audited(tmp_path):
    def execute(plan, decision, approval, inputs_view=None):
        return RunResult(
            outcome="failed", external_ref="id with\nspaces <x>", error_code="boom happened\n!!"
        )

    rt, store, run = _execute_runtime(tmp_path, execute)
    store.put_redaction_map(run.run_id, {"<NAME_1>": "rec-123"})
    done = rt.execute(run.run_id)
    assert done.state == S.NEEDS_PERSON
    row = [e for e in _events(rt, run) if e.operation == "result"][-1]
    assert row.error_code == "boom happened___" and row.object_ref.startswith("sha256:")


def test_note_never_raises_on_a_refused_event(tmp_path):
    rt, _ = build_runtime(k5_cfg(tmp_path), StopLLM("end_turn"))
    run = handle(rt)
    rt._note(run, "x", "y", result="r", object_ref=None, error_code="e", rule_id=5)  # type: ignore[arg-type]
    rt._note(run, "x", "y", bogus_field="z")
    assert [e for e in _events(rt, run) if e.error_code == "audit_event_refused"]


def test_mutant_raw_helper_is_killed(tmp_path, monkeypatch):
    """With a helper that returns the raw text, the hostile executor code does not come out sanitised: the
    executor test's assertion would fail, so the mutant is killed."""
    from hadavin_sdk.runtime import agent_loop

    monkeypatch.setattr(agent_loop, "audit_code", lambda text: text)
    with pytest.raises(AssertionError):
        test_executor_ref_and_code_with_spaces_and_newlines_are_audited(tmp_path)


@pytest.mark.parametrize("text", ["a²b", "½", "①", "é ü", "x\n", "٣"])
def test_audit_code_output_is_always_accepted_by_audit_event(text):
    out = audit_code(text)
    AuditEvent(run_id="r", domain="d", operation="o", principal=out, source="s", result=out)
    assert out.isascii()


def test_audit_ref_refuses_a_trailing_newline_as_a_token():
    from hadavin_sdk.models import audit_ref

    assert audit_ref("abc\n").startswith("sha256:")
    assert audit_ref("abc") == "abc"
