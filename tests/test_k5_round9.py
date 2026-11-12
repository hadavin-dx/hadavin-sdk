"""Round 9 (security path): every row of the producer registry, driven through its REAL producer function, with three
spellings of a secret (percent-encoded, entity-encoded, assignment-encoded). The needle must be absent AND a placeholder
must be present (a refusal text or an empty string is not a pass). Then the post-redaction transforms of a card."""

from __future__ import annotations

import json
import re

import pytest

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.judge import JudgeDetector
from hadavin_sdk.guard.producers import PRODUCERS
from hadavin_sdk.models import Plan, Reply, Target, ToolCall
from hadavin_sdk.runtime import tick as tick_mod
from tests.fixtures import k5_tools
from tests.k1b_support import ScriptedLLM, submit_not_sure, text_reply
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg
from tests.test_k1b_redaction_layers import _bundle, _log
from tests.test_k1b_replay import env  # noqa: F401  (a fixture)

SPELLINGS = {
    "percent": "%41KIA" + "IOSFODNN7EXAMPLE",
    "entity": "&#65;KIA" + "IOSFODNN7EXAMPLE",
    "assignment": "password%3Dhunter2",
}
NEEDLES = ("IOSFODNN7EXAMPLE", "hunter2")
# a placeholder that does NOT come from the IP address every runtime document carries: it can only come from the secret
PLACEHOLDER = re.compile(r"<(?!IPV4_)[A-Z][A-Z0-9]*_\d+>")


def _plan(inputs):
    return Plan(
        run_id="run-1",
        agent_id="test-agent",
        action_id="create_draft_record",
        action_version=1,
        risk_class="reversible",
        inputs=inputs,
        target=Target(system="fixture-records", ref=None),
        idempotency_key="run-1:create_draft_record",
        expected_outcome="x",
    )


def _judge(s, rq):
    seen = {}

    class LLM:
        def chat(self, messages, **kw):
            seen["doc"] = kw["documents"][0].decode()
            raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        JudgeDetector(LLM(), "r", 0.5).check(f"a {s} b", "t")
    return seen["doc"]


def _guardrail(s, rq):
    from hadavin_sdk.guard.bedrock_guardrail import GuardrailDetector

    seen = {}

    class Client:
        def apply_guardrail(self, **kw):
            seen["text"] = kw["content"][0]["text"]["text"]
            return {"action": "NONE", "assessments": []}

    GuardrailDetector(Client(), "g", "1", 0.5).check(f"a {s} b", "t")
    return seen["text"]


def _extract(s, rq):
    from pydantic import BaseModel

    from hadavin_sdk.extract import extract

    class Out(BaseModel):
        need: int

    sent = []

    class LLM:
        def chat(self, messages, **kw):
            sent.append(
                messages[-1]["content"]
            )  # the feedback the run adds (the model's own reply is its own text)
            return Reply(text=json.dumps({"other": f"a {s} b"}), model_id="fake")

    extract(LLM(), b"doc", Out, run_id="r", route="x")
    return " ".join(sent[1:])


def _runtime(s, rq, *, doc=None, reason=None, host="<IPV4_1>"):
    tmp_path = rq.getfixturevalue("tmp_path")
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; rollout revision 17 failed"
    llm = ScriptLLM(
        [{"tool": "app"}, {"propose": {"host": host, "revision": "17"}, "reason": reason}]
    )
    rt, cards = build_runtime(k5_cfg(tmp_path), llm)
    handle(rt, (doc or f"checkout 5xx from 10.0.0.5 {s} revision 17").encode())
    return llm.everything_sent() + " ".join(c.text for c in cards)


def _grounding(s, rq):
    """`grounded` compares the identifier the model typed, redacted, with the evidence, redacted: with the layered decode
    both read the same secret into the same placeholder (the value is grounded); without it the typed value stays raw
    and does not match. Returns the placeholders in the map, and fails if the value was not grounded."""
    from hadavin_sdk.runtime import evidence

    tmp_path = rq.getfixturevalue("tmp_path")
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused"
    rt, _ = build_runtime(k5_cfg(tmp_path), ScriptLLM([]))
    contract = rt.registry.contracts["rollout_undo"]
    mapping = runmap.RunMap()
    texts = [runmap.redact_text(f"host {s} down", mapping)]
    ok = evidence.grounded(contract, {"host": s}, texts, mapping)
    # an assignment-shaped identifier (`password=...`) is not an identifier the contract grounds; the other two must be
    assert ok or "password" in s, (
        "the layered identifier was not read as the secret in the evidence"
    )
    return " ".join(mapping)


def _k1b_raw(s, rq):
    e = rq.getfixturevalue("env")
    e.run(ScriptedLLM([text_reply("word " + s), submit_not_sure()]))
    return e.case()["raw"]


def _gate(s, rq):
    from hadavin_sdk import evals
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    cfg = load_config(rq.getfixturevalue("live_cfg_dir"))
    gp = cfg.golden_dir / "test-agent.jsonl"
    case = json.loads(gp.read_text(encoding="utf-8").splitlines()[0])
    (cfg.inputs_dir / "r9.txt").write_text(f"checkout down {s} again", encoding="utf-8")
    case["input_ref"] = "r9.txt"
    gp.write_text(json.dumps(case) + "\n", encoding="utf-8")
    docs = []

    class Echo:
        def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
            docs.append(documents[0].decode())
            exp = case["expected"]
            return Reply(
                tool_calls=[
                    ToolCall(name=exp["action"], input={**exp["inputs"], "evidence": ["x"]})
                ],
                model_id="fake",
            )

    evals.gate(load_registry(cfg), Echo(), "test-agent")
    return docs[0]


DRIVERS = {
    "tool result": lambda s, rq: tools_mod.prepare_output(f"a {s} b", {}, 16384, []),
    "tool result, redaction step": lambda s, rq: tools_mod.redact_layered(f"a {s} b", {}),
    "tool error reason": lambda s, rq: tools_mod.error_reason(ValueError(f"a {s} b"), []),
    "k1b case bundle": lambda s, rq: repr(
        __import__("hadavin_sdk.k1b.redaction", fromlist=["x"])
        .redact_bundle(_bundle(**_log(f"x {s} y")))[0]
        .logs
    ),
    "k1b stored raw model output": _k1b_raw,
    "evidence grounding": lambda s, rq: _grounding(s, rq),
    "evidence proposal inputs": lambda s, rq: _runtime(s, rq, reason=s),
    "document and model-written arguments": lambda s, rq: _runtime(
        s, rq, doc=f"checkout 5xx at host-a {s} revision 17"
    ),
    "judge input": _judge,
    "vendor guardrail input": _guardrail,
    "extract validation errors": _extract,
    "tick error message": lambda s, rq: tick_mod._message(tick_mod.ConfigError(f"a {s} b")),
    "approval card text": lambda s, rq: channel_mod.clean(f"a {s} b"),
    "approval summary": lambda s, rq: summary(_plan({"note": f"a {s} b"})),
    "eval case document": _gate,
}


def test_there_is_a_driver_for_every_registry_row():
    assert set(DRIVERS) == {r[0] for r in PRODUCERS}, (
        "a registry row without a driver (or the reverse)"
    )


@pytest.mark.parametrize("row", sorted(n for n, d in DRIVERS.items() if d is not None))
@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_every_registry_row_masks_every_spelling_through_its_real_function(row, spelling, request):
    out = DRIVERS[row](SPELLINGS[spelling], request)
    assert not any(n in out for n in NEEDLES), (row, spelling, out[:200])
    assert PLACEHOLDER.search(out), (
        row,
        spelling,
        "no placeholder: a refusal or an empty text is not a pass",
        out[:200],
    )


@pytest.mark.parametrize("encoded", ["%31%30.0.0.5", "&#49;0.0.0.5", "10&#46;0.0.5"])
def test_evidence_grounding_leaks_no_clear_identifier_for_an_encoded_one(encoded, tmp_path):
    """The executor would receive the identifier exactly as the model typed it, so an encoded address is either refused as
    ungrounded or redacted to the placeholder first (a layered entity): no clear address reaches the card."""
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; rollout revision 17 failed"
    llm = ScriptLLM([{"tool": "app"}, {"propose": {"host": encoded, "revision": "17"}}])
    rt, cards = build_runtime(k5_cfg(tmp_path), llm)
    handle(rt, b"checkout 5xx from 10.0.0.5, revision 17")
    shown = " ".join(c.text for c in cards)
    assert (
        "10.0.0.5" not in shown
    )  # refused as ungrounded, or redacted to its placeholder: never the clear address


# ---- A: what happens to a card text AFTER the first redaction ---------------------------------------------------------------------------


@pytest.mark.parametrize("filler", ["<b></b>", "\u200b", "⁠", "<!-- x -->", "<span></span>"])
@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_clean_redacts_again_what_sanitising_joined(filler, spelling):
    """`%41KIA<b></b>IOS...`: pass one cannot read it; sanitising removes the tag and JOINS the pieces into a layered
    spelling; the second pass must be the layered choke point, not the bare redactor."""
    s = SPELLINGS[spelling]
    cut = len(s) // 2
    out = channel_mod.clean(f"note {s[:cut]}{filler}{s[cut:]} end")
    assert not any(n in out for n in NEEDLES), (filler, spelling, out)


def test_the_slack_summary_with_a_withheld_command_and_a_layered_secret_shows_neither():
    """`withhold_commands` replaces a command by a note (it never joins what surrounds it), so the join case cannot be
    built there; this pins that a command AND a layered secret in one summary are both gone from the block."""
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(
        summary="run `kubectl delete pod web` then " + SPELLINGS["percent"],
        current_step=0,
        steps=[1],
        approval_id="a1",
        status="PENDING",
    )
    shown = ch._blocks(req, None)[0]["text"]["text"]
    assert "kubectl delete" not in shown and "IOSFODNN7EXAMPLE" not in shown


def test_the_slack_re_redaction_never_reuses_a_placeholder_number():
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(
        summary="host <IPV4_1> and 10.0.0.9",
        current_step=0,
        steps=[1],
        approval_id="a1",
        status="PENDING",
    )
    shown = ch._blocks(req, None)[0]["text"]["text"]
    assert shown.count("<IPV4_1>") == 1 and "<IPV4_2>" in shown and "10.0.0.9" not in shown


def test_the_slack_summary_is_redacted_once_more_after_commands_are_withheld():
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(
        summary=f"ok {SPELLINGS['percent']} fine",
        current_step=0,
        steps=[1],
        approval_id="a1",
        status="PENDING",
    )
    blocks = ch._blocks(req, None)
    assert "IOSFODNN7EXAMPLE" not in blocks[0]["text"]["text"]


def test_the_slack_card_never_cuts_a_summary_silently_and_the_block_builder_runs():
    from datetime import UTC, datetime

    from hadavin_sdk.approvals.slack_channel import SlackChannel
    from hadavin_sdk.models import ApprovalRequest, ChainStep

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 100
    ch.name = "slack"
    req = ApprovalRequest(
        run_id="r",
        plan_hash="h" * 64,
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["slack:U1"], timeout_s=60)],
        step_expires_at=datetime.now(UTC),
        requested_by="u",
        summary="word " * 200,
    )
    blocks = ch._blocks(req, ["slack:U1"])
    shown = blocks[0]["text"]["text"]
    assert "too long to show" in shown and "word word" not in shown


# ---- minors ---------------------------------------------------------------------------------------------------------------------------


def test_error_reason_with_an_expanding_message_is_a_fixed_note_not_an_exception():
    assert tools_mod.error_reason(ValueError("ﷺ" * 87000), []).endswith(runmap.SAFE_HEAD_NOTE)


def test_the_margin_follows_a_cut_made_after_the_scrub_grew_the_text():
    """A short handed-out secret becomes the longer marker, the grown text is cut again at the cap, and the end of THAT
    cut loses its margin too (a pattern token straddling it leaves no fragment)."""
    secret = "Zk3#" + "9q"  # 6 characters: the shortest handed-out secret (built from parts)
    cap = tools_mod.defaults.MAX_REDACT_CHARS
    raw = (secret + " ") * ((cap - 400) // 7) + "tail"
    out = tools_mod.prepare_output(raw, {}, cap, [secret])
    assert out.endswith(tools_mod.TRUNCATED)
    assert len(out) <= cap - tools_mod.defaults.CUT_MARGIN + len(tools_mod.TRUNCATED) + 20


def test_backslash_x_escapes_are_decoded():
    """One escaped character is enough to hide a key from the pattern (the plain test of the whole key passes without
    the decoder, because the redactor reads a fully escaped key by other means)."""
    bs = chr(92)
    for spelled in (bs + "x41KIA" + "IOSFODNN7EXAMPLE", "password" + bs + "x3dhunter2"):
        out = runmap.redact_text(f"k {spelled} z", {})
        assert not any(n in out for n in NEEDLES) and PLACEHOLDER.search(out), (spelled, out)


# ---- round 10: M-3, N-2, N-1 -------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "password%<i> </i>3Dhunter2 end",  # the input of round 9: markup that became a space between key and value
        "password%<b></b>3Dhunter2 end",
        "password<span> </span>=hunter2 end",
    ],
)
def test_a_key_and_value_split_by_markup_are_masked_in_a_card(text):
    out = channel_mod.clean("note " + text)
    assert "hunter2" not in out, out


def test_clean_keeps_placeholders_and_is_stable_on_ordinary_text():
    assert channel_mod.clean("host <IPV4_1> down <b>x</b>") == "host <IPV4_1> down x"
    assert channel_mod.clean("a b c 1 2 3 words") == "a b c 1 2 3 words"


def test_the_swap_to_a_decoded_view_keeps_what_pass_one_masked():
    """`password=p%40ss%20word` is masked whole in pass one; another secret makes the decoded view replace the text; the
    view reads `password=p@ss word` and used to leave ` word` behind."""
    text = "password=p%40ss%20word and " + SPELLINGS["percent"]
    out = runmap.redact_text(text, {})
    assert " word" not in out and "p@ss" not in out and "IOSFODNN7EXAMPLE" not in out, out
    out2 = tools_mod.prepare_output(text, {}, 4096, ["p%40ss%20word", "Zk3#" + "9qWd"])
    assert " word" not in out2 and "p@ss" not in out2, out2


def test_unicode_and_octal_escapes_are_decoded_and_the_rest_listed():
    bs = chr(92)
    assert runmap.undo(bs + "U00000041") == "A"
    assert runmap.undo(bs + "101") == "A"
    for kept in (
        bs + "41",
        bs + "7",
    ):  # a one- or two-digit octal escape: documented as not decoded
        assert runmap.undo(kept) == kept


def test_a_rsa_8192_key_straddling_the_cut_leaves_no_fragment():
    import base64

    body = "".join(
        base64.b64encode(bytes((i * 11 + j) % 256 for j in range(48))).decode() + "\n"
        for i in range(110)
    )
    pem = "-----BEGIN " + "PRIVATE KEY-----\n" + body + "-----END " + "PRIVATE KEY-----"
    cap = tools_mod.defaults.MAX_REDACT_CHARS
    for back in (200, 1200, 3000, 5000):
        raw = "word " * ((cap - back) // 5) + pem + "tail " * 400
        out = tools_mod.prepare_output(raw, {}, cap, [])
        flat = body.replace("\n", "")
        assert not any(
            flat[i : i + 24] in out.replace("\n", "") for i in range(0, len(flat) - 24, 8)
        ), back
    assert tools_mod.defaults.CUT_MARGIN >= 8192


def test_the_work_budget_refuses_a_text_that_costs_more_than_it_allows(monkeypatch):
    monkeypatch.setattr(tools_mod.defaults, "REDACT_BUDGET_S", 0.0)
    with pytest.raises(runmap.InputTooLarge):
        runmap.redact_text("%63url -u " * 20000, {})
