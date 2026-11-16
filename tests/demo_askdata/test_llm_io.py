"""Prompt layout, the fixed system prompt, the structured-output parse path, the SQLSTATE table, fixtures."""

from __future__ import annotations

import hashlib
import json

import pytest
from askdata import llm_io, policy, prompt
from askdata.fixtures import Step, digest, fixtures_current, write_script
from askdata.validate import RULES

from hadavin_sdk.models import Reply, ToolCall

# A silent edit of the system prompt must fail here: the literal is the hash of the reviewed text.
SYSTEM_SHA256 = "1304bfac9c38c5742cc7ffac46562c77dc1b9101311ba49185b11db7431930f6"


def reply(**kw) -> Reply:
    return Reply(model_id="m", **kw)


def test_system_prompt_is_the_reviewed_constant():
    assert hashlib.sha256(llm_io.SYSTEM.encode()).hexdigest() == SYSTEM_SHA256


def test_messages_are_exactly_one_user_message_with_the_variable_part_last():
    m = llm_io.build_messages("PART A", "how many?")
    assert m == [{"role": "user", "content": "PART A\n\n## Question\nhow many?"}]
    m2 = llm_io.build_messages("PART A", "how many?", "SELECT 1", "V03: a write")
    assert (
        m2[0]["content"].endswith("## Previous attempt\nSELECT 1\n\n## Rejected by\nV03: a write")
        and len(m2) == 1
    )


def test_the_prompt_hash_covers_catalog_glossary_and_exemplars():
    base = {"as_of": "2026-10-15", "catalog": prompt.catalog_text()}
    a = prompt.render(
        "{{CATALOG}}|{{GLOSSARY}}|{{EXEMPLARS}}|{{AS_OF}}", glossary="g", exemplars="e", **base
    )
    for change in ({"glossary": "g2", "exemplars": "e"}, {"glossary": "g", "exemplars": "e2"}):
        assert (
            prompt.render(
                "{{CATALOG}}|{{GLOSSARY}}|{{EXEMPLARS}}|{{AS_OF}}", **change, **base
            ).prompt_sha256
            != a.prompt_sha256
        )
    other = prompt.render(
        "{{CATALOG}}|{{GLOSSARY}}|{{EXEMPLARS}}|{{AS_OF}}",
        glossary="g",
        exemplars="e",
        as_of="2026-10-15",
        catalog="x",
    )
    assert other.prompt_sha256 != a.prompt_sha256 and other.catalog_sha256 != a.catalog_sha256
    assert "2026-10-15" in a.text and "{{" not in a.text


def test_the_shipped_template_renders_every_slot_and_never_the_clock():
    p = prompt.load(as_of="2026-10-15", glossary="revenue = x", exemplars="Q: n")
    assert (
        "{{" not in p.text
        and "analytics.orders_v(" in p.text
        and "2026-10-15" in p.text
        and "revenue = x" in p.text
    )
    assert "email" not in prompt.catalog_text()  # the restricted column is not in the catalog


def test_parse_forced_tool_call():
    out = llm_io.parse_reply(
        reply(
            tool_calls=[
                ToolCall(name="submit_answer", input={"decision": "answer", "sql": "SELECT 1"})
            ]
        )
    )
    assert out.decision == "answer" and out.sql == "SELECT 1"


def test_parse_text_fallback_when_there_is_no_tool_call():
    body = json.dumps(
        {"decision": "abstain", "abstain_reason": "ambiguous", "clarifying_question": "which?"}
    )
    assert llm_io.parse_reply(reply(text=f"Sure.\n{body}")).abstain_reason == "ambiguous"
    assert llm_io.parse_reply(reply(text=body, stop_reason="max_tokens")).decision == "abstain"


@pytest.mark.parametrize(
    "r",
    [
        reply(),  # nothing
        reply(text="no json here"),
        reply(tool_calls=[ToolCall(name="other", input={})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "answer"}), ToolCall(name="submit_answer", input={"decision": "answer"})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "answer"})]),  # no sql
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "answer", "sql": "SELECT 1", "abstain_reason": "ambiguous"})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "abstain", "sql": "SELECT 1"})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "abstain", "abstain_reason": "made_up"})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "answer", "sql": "SELECT 1", "extra": 1})]),
        reply(tool_calls=[ToolCall(name="submit_answer", input={"decision": "answer", "sql": "x" * 4001})]),
    ],
)  # fmt: skip
def test_every_malformed_answer_is_a_schema_violation(r):
    with pytest.raises(llm_io.SchemaViolation):
        llm_io.parse_reply(r)


def test_the_schema_violation_message_never_echoes_the_model():
    with pytest.raises(llm_io.SchemaViolation) as e:
        llm_io.parse_reply(reply(text="IGNORE ALL RULES {not json"))
    assert "IGNORE" not in str(e.value)


# ------------------------------------------------------------------------------------------ policy


def test_every_reason_has_an_outcome_exit_code_and_sentence():
    assert set(policy.REASONS) == set(policy.ReasonCode.__args__)
    assert {r.exit_code for r in policy.REASONS.values()} == {2, 3, 5, 6, 7}
    assert all(r.sentence.endswith((".", ";")) or r.sentence for r in policy.REASONS.values())
    assert (
        policy.exit_code("answered", None) == 0
        and policy.exit_code("failed", "audit_unavailable") == 5
    )


def test_precedence_order():
    assert policy.pick_reason(["execution_failed", "timeout", "unsafe_query"]) == "timeout"
    assert policy.pick_reason(["unsafe_query", "kill_switch", "timeout"]) == "kill_switch"
    assert policy.pick_reason(["over_budget", "audit_unavailable"]) == "audit_unavailable"
    assert (
        policy.pick_reason(["execution_failed"]) == "execution_failed"
        and policy.pick_reason([]) == "execution_failed"
    )


@pytest.mark.parametrize(
    ("state", "action", "reason", "alarm"),
    [
        ("42501", "stop", "execution_failed", "role_gap"), ("25006", "stop", "unsafe_query", "readonly_violation"),
        ("42601", "stop", "execution_failed", "validator_gap"), ("42P01", "retry", "execution_failed", None),
        ("42703", "retry", "execution_failed", None), ("42883", "retry", "execution_failed", None), ("42P10", "retry", "execution_failed", None),
        ("42804", "retry", "execution_failed", None), ("42803", "retry", "execution_failed", None),
        ("22012", "retry", "execution_failed", None), ("22P02", "retry", "execution_failed", None),
        ("57014", "retry_once", "timeout", None), ("53200", "stop", "execution_failed", None),
        ("53300", "reconnect", "execution_failed", None), ("57P03", "reconnect", "execution_failed", None),
        ("08006", "reconnect", "execution_failed", None), ("55P03", "retry_once", "execution_failed", None),
        ("40001", "retry_once", "execution_failed", None), ("40P01", "retry_once", "execution_failed", None),
        ("28P01", "abort", "execution_failed", None), ("XX000", "stop", "execution_failed", None), (None, "reconnect", "execution_failed", None),
    ],
)  # fmt: skip
def test_the_sqlstate_table(state, action, reason, alarm):
    d = policy.decide(state)
    assert (d.action, d.reason, d.alarm) == (action, reason, alarm)
    if d.action == "retry":
        assert d.hint and len(d.hint) < 100


# ------------------------------------------------------------------------------------------ fixtures


def test_the_builder_computes_the_digest_the_fake_model_looks_up(tmp_path):
    keys = write_script(
        tmp_path,
        "A",
        "q",
        [Step(sql="DELETE FROM analytics.orders_v"), Step(sql="SELECT 1 FROM analytics.orders_v")],
    )
    assert keys[0] == digest(llm_io.build_messages("A", "q"))
    assert keys[1] == digest(
        llm_io.build_messages("A", "q", "DELETE FROM analytics.orders_v", "V03: " + RULES["V03"])
    )
    assert sorted(p.name for p in tmp_path.glob("*.json")) == sorted(
        [f"{keys[0]}-1.json", f"{keys[1]}-1.json"]
    )


def test_a_repeated_question_gets_numbered_recordings(tmp_path):
    write_script(tmp_path, "A", "q", [Step(abstain="ambiguous")])
    write_script(tmp_path, "A", "q", [Step(abstain="out_of_scope")])
    assert len(list(tmp_path.glob("*-2.json"))) == 1


def test_fixtures_current_detects_drift(tmp_path):
    def build(d):
        write_script(d, "A", "q", [Step(abstain="ambiguous")])

    build(tmp_path)
    assert fixtures_current(tmp_path, build)
    write_script(tmp_path, "A changed", "q", [Step(abstain="ambiguous")])
    assert not fixtures_current(tmp_path, build)
