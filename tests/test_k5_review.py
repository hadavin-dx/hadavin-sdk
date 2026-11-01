"""K5-core independent-review fixes: each test fails without its fix. Secrets in fixtures are built from parts."""

from __future__ import annotations

import json
import sys
import time
from datetime import timedelta

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime import tick as tick_mod
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound
from tests.fixtures import k5_tools
from tests.k5_support import (
    BUNDLES,
    SECRETS,
    TOOL,
    ScriptLLM,
    build_runtime,
    handle,
    k5_cfg,
)

S = RunState
TOKEN = "s3cr3t" + "VALUE9xQ2"  # built from parts


@pytest.fixture(autouse=True)
def _reset():
    k5_tools.RESULTS.clear()
    yield
    k5_tools.RESULTS.clear()


# --- bug 1: a secret beside an identifier must never be stored --------------------------------------------------


def test_review_arn_pattern_stops_at_the_query_string():
    mapping: dict[str, str] = {}
    text = runmap.redact_untrusted(
        f"ran arn:aws:lambda:us-east-1:123456789012:function:billing?token={TOKEN}", mapping
    )
    assert TOKEN not in text
    assert mapping["<ARN_1>"] == "arn:aws:lambda:us-east-1:123456789012:function:billing"


def test_review_storable_drops_an_original_that_carries_a_secret():
    swallowed = f"arn:aws:lambda:us-east-1:123456789012:function:billing?token={TOKEN}"
    assert runmap.storable({"<ARN_1>": swallowed, "<IPV4_1>": "10.0.0.5"}) == {
        "<IPV4_1>": "10.0.0.5"
    }
    url = f"https://svc.example.com/x?api_key={TOKEN}"
    assert runmap.storable({"<NAME_1>": url}) == {}


@pytest.mark.parametrize(
    "line",
    [
        "job ran arn:aws:lambda:us-east-1:123456789012:function:billing?token={t}",
        "see https://svc.example.com/path?token={t} from 10.0.0.5",
    ],
)
def test_review_no_secret_reaches_the_stored_map_or_the_model(tmp_path, line):
    k5_tools.RESULTS["app"] = line.format(t=TOKEN)
    store, llm = MemoryStore(), ScriptLLM([{"tool": "app"}, {"noaction": True}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt)
    assert all(TOKEN not in v for v in store.get_redaction_map(run.run_id).values())
    assert TOKEN not in llm.everything_sent()
    assert all(TOKEN not in c.output for c in store.list_tool_calls(run.run_id))


# --- bug 2: a literal placeholder in untrusted text -------------------------------------------------------------


def test_review_literal_placeholders_are_escaped_before_redaction():
    mapping: dict[str, str] = {}
    out = runmap.redact_untrusted("host <IPV4_2> and 10.0.0.5 and 10.9.9.9", mapping)
    assert "<IPV4_2>" in out and out.count("<IPV4_2>") == 1  # only the issued one
    out2 = runmap.redact_untrusted("literal <IPV4_7>", {})
    assert "<IPV4_7>" not in out2 and "‹IPV4_7›" in out2
    # What the model writes is meant to be a placeholder: redact_text leaves it alone.
    assert runmap.redact_text("<IPV4_1>", {"<IPV4_1>": "10.0.0.5"}) == "<IPV4_1>"


def test_review_a_literal_placeholder_in_a_log_is_not_evidence(tmp_path):
    bundle = json.loads(
        (BUNDLES.parent / "redteam_extra" / "07-literal-placeholder.json").read_text("utf-8")
    )
    k5_tools.RESULTS["app"] = bundle["results"]["app"]
    store, llm = MemoryStore(), ScriptLLM(list(bundle["script"]))
    rt, cards = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt, bundle["document"].encode())
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "ungrounded")
    with pytest.raises(NotFound):  # no plan row of any kind
        store.get_plan(run.run_id)
    assert cards and "upstream ‹IPV4_2› refused" in json.dumps(
        llm.sent[1]["messages"], ensure_ascii=False
    )
    # The forged name is the one the redactor issued to 10.0.0.5; only the escaped literal and it exist.
    assert store.get_redaction_map(run.run_id) == {"<IPV4_1>": "10.0.0.5"}


@pytest.mark.parametrize("literal", ["<ipv4_2>", "<Ipv4_2>", "＜IPV4＿2＞", "<IPV4\u200b_2>"])
def test_review_round3_a_look_alike_literal_in_a_log_is_not_evidence(tmp_path, literal):
    """Case, full-width and zero-width spellings of the placeholder are escaped, not left to ground the real one."""
    k5_tools.RESULTS["app"] = f"ERROR upstream {literal} refused; seen from 10.0.0.5"
    store = MemoryStore()
    llm = ScriptLLM([{"tool": "app"}, {"propose": {"host": "<IPV4_2>", "revision": "17"}}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt, b"alert after rollout")
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "ungrounded")


def test_config_evidence_limits_have_documented_defaults_and_validate(tmp_path):
    from hadavin_sdk import defaults

    cfg = load_config(k5_cfg(tmp_path))
    ev = cfg.evidence
    assert (
        ev.max_tool_errors == defaults.MAX_TOOL_ERRORS
        and ev.fetch_ceiling_bytes == defaults.FETCH_CEILING_BYTES
    )
    assert (
        set(ev.stored_kinds) == set(defaults.STORED_KINDS) and cfg.retention.purge_every_s == 86400
    )
    for bad in (
        {"stored_kinds": ["APIKEY"]},  # a secret kind can never be stored
        {"stored_kinds": ["NOPE"]},
        {"max_tool_errors": 0},
        {"cluster_ports": [70000]},
    ):
        with pytest.raises(ConfigError):
            load_config(k5_cfg(tmp_path / "bad", config={"evidence": bad}))


def test_config_max_tool_errors_is_applied(tmp_path):
    llm = ScriptLLM([{"tool": "boom"}, {"tool": "boom"}, {"noaction": True}])
    cfg = k5_cfg(tmp_path, config={"evidence": {"max_tool_errors": 2}})
    rt, _ = build_runtime(cfg, llm)
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "tool_error") and len(llm.sent) == 2


def test_config_stored_kinds_can_narrow_what_is_stored_and_restored(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5; mail ops@example.test; revision 17"
    store = MemoryStore()
    cfg = k5_cfg(tmp_path, config={"evidence": {"stored_kinds": ["IPV4"]}})
    rt, _ = build_runtime(cfg, ScriptLLM([{"tool": "app"}, {"noaction": True}]), store=store)
    run = handle(rt)
    assert store.get_redaction_map(run.run_id) == {
        "<IPV4_1>": "10.0.0.5"
    }  # the e-mail is not stored


def test_config_fetch_limits_reach_the_tool_context(monkeypatch):
    spec = tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.com"], "max_output_bytes": 100})
    ctx = tools_mod.ToolContext(
        spec, 3.0, bindings=k5_tools.READ_OPERATIONS, fetch_ceiling=10, https_ports=(8443,)
    )

    class Resp:
        def __init__(self):
            self.n = 0

        def read(self, n=-1):
            self.n += 1
            return (b"x " * n)[:n] if self.n < 3 else b""

        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False

    class Opener:
        def open(self, req, timeout=None):
            return Resp()

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    with pytest.raises(tools_mod.ToolRefused, match="port 443 is not allowed"):
        ctx.fetch("GET", "https://api.example.com/x", operation="bundle.read")
    out = ctx.fetch("GET", "https://api.example.com:8443/x", operation="bundle.read")
    assert out == "x " * 5 + tools_mod.TRUNCATED  # the configured ceiling, not the manifest's 100


def test_review_a_real_placeholder_still_grounds(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; revision 17"
    llm = ScriptLLM([{"tool": "app"}, {"propose": {"host": "<IPV4_1>", "revision": "17"}}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm)
    assert handle(rt).reason_code == "shadow"


def test_review_the_frozen_set_is_still_six_and_bundle_seven_is_separate():
    assert len(list(BUNDLES.glob("*.json"))) == 6
    assert (BUNDLES.parent / "redteam_extra" / "07-literal-placeholder.json").is_file()


# --- risk: grounding is a whole-token match ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "value", "found"),
    [
        ("revision 17 failed", "17", True),
        ("REVISION 17.", "17", True),
        ("rolled to rev 17 today", "17", True),
        ("rolled to v17 today", "17", True),
        ("upstream 10.0.0.17 refused", "17", False),
        ("deploy-17 started", "17", False),
        ("rollout 1.17 done", "17", False),
        ("build 170 done", "17", False),
        ("ran on production cluster", "prod", False),
        ("service-api-7 is down", "api", False),
        ("path /var/prod/x", "prod", False),
        ("mail prod@example.test", "prod", False),
        ("namespace prod is down", "prod", True),
        ("host <ipv4_1> down", "<IPV4_1>", True),
        ("host <ipv4_10> down", "<IPV4_1>", False),
        ("CAFÉ open", "café", True),
    ],
)
def test_review_grounding_matches_whole_tokens_only(text, value, found):
    assert evidence.contains(text, value) is found


# --- risk: an ERROR result is not evidence ----------------------------------------------------------------------


def test_review_citing_an_error_result_is_uncited(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5; revision 17"
    llm = ScriptLLM(
        [
            {"tool": "boom"},
            {"tool": "app"},
            {"propose": {"host": "<IPV4_1>", "revision": "17"}, "evidence": ["$ERR"]},
        ]
    )
    store = MemoryStore()
    rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
    real_chat = llm.chat

    def chat(messages, **kw):
        reply = real_chat(messages, **kw)
        for c in reply.tool_calls:
            if c.input.get("evidence") == ["$ERR"]:
                first = store.list_tool_calls(next(iter(store._runs)))[0]
                c.input["evidence"] = [first.call_id]
        return reply

    llm.chat = chat
    run = handle(rt)
    rows = store.list_tool_calls(run.run_id)
    assert [r.error for r in rows] == [True, False]
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "uncited")


# --- risk: tool-less agents strip and ground too ------------------------------------------------------------------


def _toolless(tmp_path):
    return k5_cfg(tmp_path, tools=[], tools_allowed=[])


def test_review_toolless_agent_strips_evidence_and_grounds_against_the_document(tmp_path):
    store = MemoryStore()
    llm = ScriptLLM([{"propose": {"host": "10.0.0.5", "revision": "17"}, "evidence": ["x"]}])
    rt, _ = build_runtime(_toolless(tmp_path), llm, store=store)
    run = handle(rt, b"checkout 5xx from 10.0.0.5, revision 17")
    assert (run.state, run.reason_code) == (S.NO_ACTION, "shadow")
    assert store.get_plan(run.run_id).inputs == {"host": "<IPV4_1>", "revision": "17"}


def test_review_toolless_agent_with_an_ungrounded_identifier_abstains(tmp_path):
    llm = ScriptLLM([{"propose": {"host": "10.9.9.9", "revision": "17"}, "evidence": []}])
    rt, _ = build_runtime(_toolless(tmp_path), llm)
    run = handle(rt, b"checkout 5xx from 10.0.0.5, revision 17")
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "ungrounded")


# --- risk: raw model-typed values are redacted before the plan ---------------------------------------------------


def test_review_a_raw_value_the_model_typed_never_reaches_the_plan_or_the_card(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5; revision 17"
    llm = ScriptLLM(
        [
            {"tool": "app"},
            {"propose": {"host": "10.0.0.5", "revision": "17"}, "reason": "ops@example.test"},
        ]
    )
    store = MemoryStore()
    rt, cards = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt)
    inputs = store.get_plan(run.run_id).inputs
    assert inputs["host"] == "<IPV4_1>" and inputs["reason"].startswith("<EMAIL_")
    assert "10.0.0.5" not in cards[-1].text and "ops@example.test" not in cards[-1].text


# --- risk: the tool body and the fetch share one deadline ---------------------------------------------------------


def test_review_a_tool_body_that_hangs_is_abandoned_at_the_total_deadline(tmp_path):
    cfg = k5_cfg(
        tmp_path,
        tools=[{**TOOL, "function": "tests.fixtures.k5_tools:slow"}],
        config={"tool_timeout_s": 0.3},
    )
    store = MemoryStore()
    started = time.monotonic()
    rt, _ = build_runtime(cfg, ScriptLLM([{"tool": "app"}, {"noaction": True}]), store=store)
    run = handle(rt)
    assert time.monotonic() - started < 3
    (row,) = store.list_tool_calls(run.run_id)
    assert row.error and row.output == "ERROR: tool timed out"


def test_review_fetch_stops_a_slow_body_at_the_deadline(monkeypatch):
    class Slow:
        def __init__(self):
            self.at = 0

        def read(self, n=-1):
            time.sleep(0.15)
            self.at += 1
            return b"x" * 10

        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False

    class Opener:
        def open(self, req, timeout=None):
            return Slow()

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    spec = tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.com"], "max_output_bytes": 100000})
    ctx = tools_mod.ToolContext(spec, 0.4, bindings=k5_tools.READ_OPERATIONS)
    with pytest.raises(tools_mod.ToolRefused, match="timed out"):
        ctx.fetch("GET", "https://api.example.com/x", operation="bundle.read")


def test_review_the_secret_resolver_is_not_reachable_from_the_context():
    ctx = tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**TOOL, "secret_names": ["tool-key"]}), 3.0, SECRETS.get
    )
    assert not hasattr(ctx, "secret_resolver") and not hasattr(ctx, "_secret_resolver")
    with pytest.raises(tools_mod.ToolRefused, match="not named in the manifest"):
        ctx.secret("fixture-token")
    assert ctx.secret("tool-key") == "k-secret-value-123"


# --- risk: an operation id is bound to a method and a path ---------------------------------------------------------


def _ctx(**spec):
    base = {**TOOL, "hosts": ["api.example.com"], "operations": ["bundle.read", "bundle.other"]}
    return tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**base, **spec}), 3.0, bindings=k5_tools.READ_OPERATIONS
    )


def test_review_operation_is_bound_to_its_method(monkeypatch):
    ctx = _ctx()
    with pytest.raises(tools_mod.ToolRefused, match="not the one bound"):
        ctx.fetch("POST", "https://api.example.com/x", operation="bundle.read")


def test_review_operation_is_bound_to_its_path():
    with pytest.raises(tools_mod.ToolRefused, match="path is not the one bound"):
        _ctx().fetch("GET", "https://api.example.com/x", operation="bundle.other")


def test_review_an_operation_with_no_binding_is_refused():
    ctx = tools_mod.ToolContext(tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.com"]}), 3.0)
    with pytest.raises(tools_mod.ToolRefused, match="no bound method"):
        ctx.fetch("GET", "https://api.example.com/x", operation="bundle.read")


def test_review_read_operations_must_be_bound_in_code(monkeypatch):
    import types

    monkeypatch.setitem(
        sys.modules,
        "tests.fixtures.k5_unbound",
        types.SimpleNamespace(READ_OPERATIONS=frozenset({"a"})),
    )
    with pytest.raises(ConfigError, match="must map each operation id"):
        tools_mod.read_operations(["tests.fixtures.k5_unbound"])


# --- risk: cluster_http and ports ---------------------------------------------------------------------------------


def test_review_cluster_http_with_a_mixed_host_list_is_refused_at_load(tmp_path):
    cfg = k5_cfg(
        tmp_path, tools=[{**TOOL, "cluster_http": True, "hosts": ["prom.mon.svc", "example.com"]}]
    )
    with pytest.raises(ConfigError, match="cluster_http needs every host"):
        load_registry(load_config(cfg))


def test_review_a_port_outside_the_allowlist_is_refused(monkeypatch):
    class Opener:
        def open(self, req, timeout=None):
            raise AssertionError("must be refused before any connection")

    monkeypatch.setattr(tools_mod.http_guard, "LOCAL_OPENER", Opener())
    ctx = _ctx(cluster_http=True, hosts=["prom.mon.svc"])
    with pytest.raises(tools_mod.ToolRefused, match="port 22 is not allowed"):
        ctx.fetch("GET", "http://prom.mon.svc:22/x", operation="bundle.read")
    with pytest.raises(tools_mod.ToolRefused, match="port 8443 is not allowed"):
        _ctx().fetch("GET", "https://api.example.com:8443/x", operation="bundle.read")


def test_review_a_manifest_port_list_widens_the_allowlist(monkeypatch):
    class Resp:
        def read(self, n=-1):
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False

    class Opener:
        def open(self, req, timeout=None):
            return Resp()

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    assert (
        _ctx(ports=[8443]).fetch("GET", "https://api.example.com:8443/x", operation="bundle.read")
        == ""
    )
    cfg_problems = tools_mod.spec_problems(
        tools_mod.ToolSpec(**{**TOOL, "ports": [0, 70000]}), ["tests.fixtures.k5_tools"]
    )
    assert any("not valid" in p for p in cfg_problems)


# --- risk: a tool's own credential needs a signed inventory ---------------------------------------------------------


def test_review_a_tool_secret_needs_a_scope_inventory_reference(tmp_path):
    cfg = k5_cfg(tmp_path, tools=[{**TOOL, "secret_names": ["tool-key"]}])
    from tests.conftest import qualify

    qualify(load_registry(load_config(cfg)))
    with pytest.raises(ConfigError, match="no probe vouches for"):
        app_mod.build(cfg, ["test-agent"], secrets=SECRETS, llm=ScriptLLM([]))
    ref = "data-readiness.md#read-logs sha256:" + "b" * 64
    signed = k5_cfg(
        tmp_path / "ok",
        tools=[{**TOOL, "secret_names": ["tool-key"]}],
        config={"scope_inventory": {"tool:read_logs": ref}},
    )
    qualify(load_registry(load_config(signed)))
    app_mod.build(signed, ["test-agent"], secrets=SECRETS, llm=ScriptLLM([]))


# --- risk: maps of open runs survive the purge --------------------------------------------------------------------


def _store_with_run(state, age_days):
    from hadavin_sdk.models import Run

    store = MemoryStore()
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    if state is not S.RECEIVED:
        store.transition(run.run_id, S.RECEIVED, state)
    store.put_redaction_map(run.run_id, {"<IPV4_1>": "10.0.0.5"})
    old = now() - timedelta(days=age_days)
    store._runs[run.run_id] = store._runs[run.run_id].model_copy(update={"updated_at": old})
    store._maps[run.run_id] = (store._maps[run.run_id][0], old)
    return store, run.run_id


@pytest.mark.parametrize("state", [S.WAITING_FOR_APPROVAL, S.WORKING, S.EXECUTING])
def test_review_the_map_of_an_open_run_is_kept(state):
    store, run_id = _store_with_run(state, 40)
    cutoff = now() - timedelta(days=30)
    assert store.purge_redaction_maps(cutoff, keep_run_ids=frozenset()) == 0
    assert store.get_redaction_map(run_id) is not None


def test_review_the_map_of_a_finished_run_ages_from_when_it_finished():
    store, run_id = _store_with_run(S.NO_ACTION, 40)
    store._maps[run_id] = (store._maps[run_id][0], now())  # a recent write does not save it
    assert store.purge_redaction_maps(now() - timedelta(days=30), keep_run_ids=frozenset()) == 1


def test_review_the_400_day_ceiling_removes_even_an_open_run_map():
    store, _run_id = _store_with_run(S.WAITING_FOR_APPROVAL, 401)
    cutoff = now() - timedelta(days=400)
    assert store.purge_redaction_maps(cutoff, keep_run_ids=frozenset()) == 0
    assert store.purge_redaction_maps(cutoff, keep_run_ids=frozenset(), keep_open=False) == 1


def test_review_purge_evidence_applies_the_ceiling_to_open_runs(tmp_path):
    from tests.conftest import qualify

    cfg = k5_cfg(tmp_path)
    qualify(load_registry(load_config(cfg)))
    k5_tools.RESULTS["app"] = "ERROR 10.0.0.5"
    app = app_mod.build(cfg, ["test-agent"], secrets=SECRETS, llm=ScriptLLM([{"tool": "app"}] * 6))
    run = app.runtime.handle("test-agent", "svc:test-agent", b"a 10.0.0.5")
    assert app.store.get_run(run.run_id).state == S.NEEDS_PERSON  # parked: max_steps
    old = now() - timedelta(days=45)
    app.store._runs[run.run_id] = app.store._runs[run.run_id].model_copy(update={"updated_at": old})
    app.store._maps[run.run_id] = (app.store._maps[run.run_id][0], old)
    tick_mod.purge_evidence(tick_mod.TickContext(app, now()))
    # Round 6: NEEDS_PERSON has no way out, so the map of a run parked there ages like a finished run's.
    assert app.store.get_redaction_map(run.run_id) is None


def test_review_yaml_manifest_ports_round_trip(tmp_path):
    cfg = k5_cfg(tmp_path, tools=[{**TOOL, "ports": [8443], "hosts": ["api.example.com"]}])
    reg = load_registry(load_config(cfg))
    assert reg.tools["test-agent"]["read_logs"].ports == (8443,)
    assert yaml.safe_load((cfg / "tools" / "test-agent.yaml").read_text())[0]["ports"] == [8443]
