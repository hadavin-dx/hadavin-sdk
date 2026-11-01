"""K5-core review round 5 (EGM design, readiness and codebase reviews). Each test names the finding it closes."""

from __future__ import annotations

import base64
import json
import shutil
import sys
import types
import urllib.error
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote

import pytest
import yaml
from pydantic import ValidationError

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli, evals
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import Reply, RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick as tick_mod
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from hadavin_sdk.sources.kubernetes import KubernetesSettings
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound
from tests.conftest import qualify
from tests.fixtures import k5_tools
from tests.k5_support import (
    BUNDLES,
    TOOL,
    ScriptLLM,
    build_runtime,
    handle,
    k5_cfg,
)
from tests.tls_support import FakeKube

S = RunState
SECRETS_PLUS = FakeSecretProvider(
    {"fixture-token": "t" * 8, "tool-key": "k-secret-value-123", "k8s-token": "kube-token-value-1"}
)


@pytest.fixture(autouse=True)
def _reset():
    k5_tools.RESULTS.clear()
    yield
    k5_tools.RESULTS.clear()


@pytest.fixture
def kube(tmp_path):
    server = FakeKube(tmp_path)
    yield server
    server.close()


def _source_cfg(tmp_path: Path, kube: FakeKube, **extra) -> Path:
    cfg = k5_cfg(
        tmp_path / "cfg",
        config={
            "sources": {
                "cluster": {
                    "kind": "kubernetes",
                    "settings": {"api_url": kube.url, "namespaces": ["prod"]},
                    "token_secret_name": "k8s-token",
                    "ca_file": "ca.pem",
                }
            },
            **extra,
        },
    )
    shutil.copy(kube.ca, cfg / "ca.pem")
    return cfg


# --- B1: the purge is scheduled by the real tick ---------------------------------------------------------------------


def test_b1_purge_evidence_is_due_again_through_the_real_tick(tmp_path):
    from tests.test_k5_tools import _age, _purge_app

    app = _purge_app(tmp_path, config={"retention": {"purge_every_s": 600}})
    t0 = now()
    first = app.runtime.handle("test-agent", "svc:test-agent", b"a 10.0.0.5")
    _age(app, first.run_id, 40)
    assert tick_mod.run_tick(app, now=t0) == 0
    assert app.store.list_tool_calls(first.run_id) == []
    for minute in (
        1,
        2,
        5,
    ):  # frequent ticks: the step is skipped and does NOT refresh its own clock
        assert tick_mod.run_tick(app, now=t0 + timedelta(minutes=minute)) == 0
    assert app.store.get_tick_state("purge_evidence").last_run_at == t0
    second = app.runtime.handle("test-agent", "svc:test-agent", b"b 10.0.0.6")
    _age(app, second.run_id, 40)
    tick_mod.run_tick(app, now=t0 + timedelta(minutes=11))  # past the interval
    assert app.store.list_tool_calls(second.run_id) == []


# --- M1 / readiness 1: configured sources are probed in production wiring, through the CLI too -------------------------


def test_m1_a_configured_source_is_probed_by_build(tmp_path, kube):
    cfg = _source_cfg(tmp_path, kube)
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(cfg, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]))
    assert app is not None
    review = [r for r in kube.requests if r["method"] == "POST"]
    assert review and review[0]["headers"]["Content-Type"] == "application/json"
    assert (
        review[0]["headers"]["Authorization"] == "Bearer kube-token-value-1"
    )  # from the secrets kind


def test_m1_a_write_capable_service_account_stops_start_up(tmp_path):
    server = FakeKube(tmp_path, rules=[{"verbs": ["get", "patch"], "resources": ["deployments"]}])
    try:
        cfg = _source_cfg(tmp_path, server)
        qualify(load_registry(load_config(cfg)))
        with pytest.raises(ConfigError, match="write verb patch"):
            app_mod.build(cfg, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]))
    finally:
        server.close()


def test_m1_the_cli_tick_path_refuses_a_write_capable_source(tmp_path, monkeypatch, capsys):
    """`hadavin-sdk tick` calls build(None, agents) with no sources argument: the configured source is still
    probed, and a failing probe means exit 2 (config error), not a running process."""
    server = FakeKube(tmp_path, rules=[{"verbs": ["create"], "resources": ["pods/exec"]}])
    try:
        cfg = _source_cfg(tmp_path, server)
        data = yaml.safe_load((cfg / "config.yaml").read_text(encoding="utf-8"))
        data["backends"]["secrets"] = {"kind": "env"}
        (cfg / "config.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
        monkeypatch.setenv("HADAVIN_SECRET_K8S_TOKEN", "kube-token-value-1")
        monkeypatch.setenv("HADAVIN_SECRET_FIXTURE_TOKEN", "t" * 8)
        monkeypatch.setenv("HADAVIN_SECRET_TOOL_KEY", "k-secret-value-123")
        assert cli.main(["--config", str(cfg), "tick"]) == 2
        err = capsys.readouterr().err
        assert "write verb create" in err and "access to pods/exec" in err
    finally:
        server.close()


def test_m1_the_cli_tick_path_runs_with_a_read_only_source(tmp_path, monkeypatch):
    server = FakeKube(tmp_path)
    try:
        cfg = _source_cfg(tmp_path, server)
        data = yaml.safe_load((cfg / "config.yaml").read_text(encoding="utf-8"))
        data["backends"]["secrets"] = {"kind": "env"}
        (cfg / "config.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
        monkeypatch.setenv("HADAVIN_SECRET_K8S_TOKEN", "kube-token-value-1")
        monkeypatch.setenv("HADAVIN_SECRET_FIXTURE_TOKEN", "t" * 8)
        monkeypatch.setenv("HADAVIN_SECRET_TOOL_KEY", "k-secret-value-123")
        assert cli.main(["--config", str(cfg), "tick"]) == 0
        assert any(r["method"] == "POST" for r in server.requests)
    finally:
        server.close()


K8S_TOOL = {
    **TOOL,
    "name": "read_logs",
    "operations": ["bundle.read"],
}


def test_m1_a_tool_that_reads_a_cluster_needs_a_probe_or_an_inventory_entry(tmp_path, monkeypatch):
    """A tool listing a `k8s.*` operation is covered by a probed source on one of its hosts or by an inventory entry
    `tool:<name>`; otherwise the process does not start."""
    monkeypatch.setitem(
        sys.modules,
        "k8s_ops",
        types.SimpleNamespace(
            READ_OPERATIONS={"k8s.list_events": ("GET", "/.*")}, read=lambda a, c: "x"
        ),
    )
    tool = {
        **TOOL,
        "function": "k8s_ops:read",
        "operations": ["k8s.list_events"],
        "hosts": ["kube.example.test"],
    }
    cfg = k5_cfg(tmp_path, tools=[tool], config={"tool_modules": ["k8s_ops"]})
    qualify(load_registry(load_config(cfg)))
    with pytest.raises(ConfigError, match="no probe vouches for"):
        app_mod.build(cfg, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]))
    ref = "data-readiness.md#kube sha256:" + "c" * 64
    ok = k5_cfg(
        tmp_path / "ok",
        tools=[tool],
        config={"tool_modules": ["k8s_ops"], "scope_inventory": {"tool:read_logs": ref}},
    )
    qualify(load_registry(load_config(ok)))
    app_mod.build(ok, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]))


# --- M2: the legacy callable path, and a toolbox without the proposal check --------------------------------------------


def test_m2_plain_callables_are_refused_in_pilot_and_prod(tmp_path):
    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(tmp_path)
    with pytest.raises(ConfigError, match="plain callables"):
        app_mod.build(root, ["ito-agent"], secrets=SECRETS_PLUS, tools={"echo": lambda a: "x"})


def test_m2_a_toolbox_without_a_proposal_check_is_refused(tmp_path):
    cfg = load_config(k5_cfg(tmp_path))
    reg = load_registry(cfg)
    store = MemoryStore()
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.guard import RegexDetector
    from hadavin_sdk.limits import Limits

    audit = LocalDirSink(cfg.backends.audit.dir)
    qualify(reg)
    with pytest.raises(ValueError, match="needs hooks.validate_proposal"):
        Runtime(
            reg, store, audit, ScriptLLM([]), RegexDetector(0.5), Limits(store, audit, reg),
            ["test-agent"], Hooks(toolbox=app_mod._toolbox(cfg, reg, SECRETS_PLUS)),
        )  # fmt: skip


# --- M3: a runaway return value is cut before redaction ------------------------------------------------------------------


def test_m3_a_multi_megabyte_return_is_cut_before_redaction():
    huge = "ERROR 10.0.0.5 retry\n" * 400_000  # about 8 MB
    started = __import__("time").monotonic()
    out = tools_mod.prepare_output(huge, {}, 16384, raw_cap=100_000)
    assert len(out.encode()) <= 16384 + len(tools_mod.TRUNCATED)
    assert __import__("time").monotonic() - started < 20


def test_m3_nul_bytes_are_replaced_so_the_store_can_keep_the_row():
    assert "\x00" not in tools_mod.prepare_output("a\x00b", {}, 100)


# --- M4 / M5: abstention, and a store fault is not a redaction fault ---------------------------------------------------------


def test_m4_redaction_error_is_an_abstention_not_a_catch():
    from hadavin_sdk.runtime import agent_loop

    # Round 6 (D1): K6 counts every non-null caught_by, so only a control that stopped a proposal sets one.
    for reason in ("redaction_error", "tool_error", "evidence_unavailable"):
        assert reason not in agent_loop.GUARD_STOP_REASONS
    assert {"ungrounded", "injection_suspected"} <= agent_loop.GUARD_STOP_REASONS


def test_m5_a_store_fault_on_the_map_is_evidence_unavailable_not_redaction_error(tmp_path):
    store = MemoryStore()
    rt, cards = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"noaction": True}]), store=store)

    def down(run_id, mapping):
        raise OSError("db down")

    store.put_redaction_map = down
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "evidence_unavailable")
    assert "redaction_error" not in cards[0].text


def test_m5_a_store_fault_on_a_tool_call_row_is_evidence_unavailable(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR 10.0.0.5"
    store = MemoryStore()

    def down(call):
        raise OSError("db down")

    store.add_tool_call = down
    rt, _ = build_runtime(
        k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}]), store=store
    )
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "evidence_unavailable")


# --- M6: the map is saved right after each redaction -----------------------------------------------------------------------


def test_m6_a_crash_after_a_tool_result_was_redacted_loses_no_placeholder(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.9 refused"
    store = MemoryStore()

    class Crash(BaseException):
        pass

    def crash(call):
        raise Crash

    store.add_tool_call = crash
    rt, _ = build_runtime(
        k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}]), store=store
    )
    with pytest.raises(Crash):
        handle(rt, b"alert at 10.0.0.5")
    (run_id,) = list(store._runs)
    assert set(store.get_redaction_map(run_id).values()) == {"10.0.0.5", "10.0.0.9"}


# --- M3 (design): a lookalike log naming another real target is NOT stopped by grounding ------------------------------------


def test_design_m3_grounding_is_not_an_injection_control(tmp_path):
    """A log line, with no instruction phrase, names a different real address as 'the culprit'. It is in the
    evidence, so the proposal is grounded and reaches the shadow card. Grounding proves a value was SEEN, not that
    the diagnosis is right or that the log is honest. The controls that remain are the card (shadow: not run),
    approval at suggest, and the injection screen where text matches its patterns."""
    bundle = json.loads(
        (BUNDLES.parent / "redteam_extra" / "08-other-real-target.json").read_text("utf-8")
    )
    k5_tools.RESULTS["app"] = bundle["results"]["app"]
    store = MemoryStore()
    rt, cards = build_runtime(k5_cfg(tmp_path), ScriptLLM(list(bundle["script"])), store=store)
    run = handle(rt, bundle["document"].encode())
    assert (run.state, run.reason_code) == (S.NO_ACTION, "shadow")  # reaches the card
    assert (
        store.get_redaction_map(run.run_id)["<IPV4_2>"] == "10.9.9.9"
    )  # the other target, not the alert's
    assert "not run" in cards[-1].text.lower() or "do not run" in cards[-1].text.lower()


# --- M5 design: a CA for a private endpoint --------------------------------------------------------------------------------------


def _ctx_with_ca(kube, **spec):
    import ssl

    base = {
        **TOOL,
        "hosts": ["localhost"],
        "ports": [kube.port],
        "operations": ["k8s.rules_review"],
        **spec,
    }
    return tools_mod.ToolContext(
        tools_mod.ToolSpec(**base),
        5.0,
        bindings={"k8s.rules_review": ("POST", "/apis/.*")},
        ssl_context=ssl.create_default_context(cadata=kube.ca.read_text()),
    )


def test_design_m5_a_pinned_ca_trusts_the_self_signed_endpoint_and_system_cas_do_not(kube):
    url = kube.url + "/apis/authorization.k8s.io/v1/selfsubjectrulesreviews"
    out = _ctx_with_ca(kube).fetch("POST", url, operation="k8s.rules_review", body=b"{}")
    assert "resourceRules" in out
    system = tools_mod.ToolContext(
        tools_mod.ToolSpec(
            **{
                **TOOL,
                "hosts": ["localhost"],
                "ports": [kube.port],
                "operations": ["k8s.rules_review"],
            }
        ),
        5.0,
        bindings={"k8s.rules_review": ("POST", "/apis/.*")},
    )
    with pytest.raises(urllib.error.URLError):
        system.fetch("POST", url, operation="k8s.rules_review", body=b"{}")


def test_design_m5_a_ca_from_a_named_secret_or_a_file_builds_a_context(tmp_path, kube):
    cfg = load_config(k5_cfg(tmp_path))
    pem = kube.ca.read_text()
    secrets = FakeSecretProvider({"ca-secret": pem})
    assert app_mod._tls_context(cfg, secrets, None, "ca-secret") is not None
    (cfg.root / "ca.pem").write_text(pem, encoding="utf-8")
    assert app_mod._tls_context(cfg, secrets, "ca.pem", None) is not None
    assert app_mod._tls_context(cfg, secrets, None, None) is None
    with pytest.raises(ConfigError, match="escapes"):
        app_mod._tls_context(cfg, secrets, "../outside.pem", None)


def test_design_m5_ca_settings_are_validated():
    spec = tools_mod.ToolSpec(**{**TOOL, "ca_file": "a.pem", "ca_secret_name": "s"})
    assert any("not both" in p for p in tools_mod.spec_problems(spec, ["tests.fixtures.k5_tools"]))
    plain = tools_mod.ToolSpec(
        **{**TOOL, "ca_file": "a.pem", "cluster_http": True, "hosts": ["a.svc"]}
    )
    assert any(
        "plain http" in p for p in tools_mod.spec_problems(plain, ["tests.fixtures.k5_tools"])
    )


# --- m1: handed-out secrets are scrubbed in their encoded forms too -----------------------------------------------------------------


@pytest.mark.parametrize(
    "form",
    [
        lambda s: s,
        lambda s: quote(s, safe=""),
        lambda s: base64.b64encode(s.encode()).decode(),
        lambda s: base64.b64encode(s.encode()).decode().rstrip("="),
        lambda s: base64.urlsafe_b64encode(s.encode()).decode(),
        lambda s: s[0] + "\u200b" + s[1:],  # an invisible character in the middle
    ],
)
def test_m1_a_handed_out_secret_is_scrubbed_in_every_form(form):
    secret = "p@ss/w0rd+Vl" + "u3=x"
    out = tools_mod.prepare_output(f"auth failed for {form(secret)} today", {}, 16384, [secret])
    assert form(secret) not in out and "<SECRET_REDACTED>" in out


def test_m1_a_very_short_secret_is_not_scrubbed_it_would_shred_text():
    assert tools_mod.prepare_output("the ab cat", {}, 100, ["ab"]) == "the ab cat"


# --- m2: manifest hosts that name no service -----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "10.0.0.5", "169.254.169.254", "::1", "[fe80::1]", "localhost", "foo.localhost",
     "metadata.google.internal", "metadata", "instance-data", "2130706433", "0x7f.1",
     "127.1", "017700000001"],
)  # fmt: skip
def test_m2_hosts_that_are_ip_literals_loopback_or_metadata_are_refused(host):
    spec = tools_mod.ToolSpec(**{**TOOL, "hosts": [host]})
    bad = [p for p in tools_mod.spec_problems(spec, ["tests.fixtures.k5_tools"]) if "host" in p]
    assert bad, host


def test_m2_an_ordinary_service_name_is_fine():
    spec = tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.test"]})
    assert tools_mod.spec_problems(spec, ["tests.fixtures.k5_tools"]) == []


# --- m3: per-run caps and the abandoned-thread ceiling ------------------------------------------------------------------------------


def test_m3_calls_per_run_are_capped(tmp_path):
    k5_tools.RESULTS["app"] = "ok"
    cfg = k5_cfg(tmp_path, config={"evidence": {"max_tool_calls_per_run": 2}})
    rt, _ = build_runtime(cfg, ScriptLLM([{"tool": "app"}] * 4))
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "tool_error")


def test_m3_bytes_sent_to_the_model_per_run_are_capped(tmp_path):
    k5_tools.RESULTS["app"] = "x " * 300
    cfg = k5_cfg(tmp_path, config={"evidence": {"max_tool_bytes_per_run": 1000}})
    llm = ScriptLLM([{"tool": "app"}] * 4)
    rt, _ = build_runtime(cfg, llm)
    run = handle(rt)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "tool_error") and len(llm.sent) == 2


def test_m3_too_many_abandoned_bodies_refuse_further_calls(tmp_path):
    cfg = k5_cfg(
        tmp_path,
        tools=[{**TOOL, "function": "tests.fixtures.k5_tools:slow"}],
        config={
            "tool_timeout_s": 0.2,
            "evidence": {"max_abandoned_tool_threads": 1, "max_tool_errors": 5},
        },
    )
    store = MemoryStore()
    rt, _ = build_runtime(
        cfg, ScriptLLM([{"tool": "a"}, {"tool": "b"}, {"noaction": True}]), store=store
    )
    run = handle(rt)
    outputs = [r.output for r in store.list_tool_calls(run.run_id)]
    assert outputs[0] == "ERROR: tool timed out"
    assert "still running past their deadline" in outputs[1]


# --- m4: the cited list excludes errored calls --------------------------------------------------------------------------------------------


def test_m4_an_errored_call_is_not_listed_as_cited(tmp_path):
    llm = ScriptLLM([{"tool": "boom"}, {"tool": "boom"}, {"tool": "boom"}])
    rt, cards = build_runtime(k5_cfg(tmp_path), llm)
    run = handle(rt)
    assert run.reason_code == "tool_error" and "- no calls were made" in cards[-1].text


# --- m5: in-cluster suffixes are config -----------------------------------------------------------------------------------------------------


def test_m5_cluster_suffixes_are_configurable():
    mine = tools_mod.ToolSpec(**{**TOOL, "cluster_http": True, "hosts": ["a.corp.cluster"]})
    assert tools_mod.spec_problems(mine, ["tests.fixtures.k5_tools"], (".corp.cluster",)) == []
    assert tools_mod.spec_problems(
        mine, ["tests.fixtures.k5_tools"]
    )  # the default suffixes refuse it
    with pytest.raises(ValidationError):
        load_config  # noqa: B018 - placeholder to keep the import used
        from hadavin_sdk.config import EvidenceSettings

        EvidenceSettings(cluster_suffixes=("svc",))


# --- m6: the URL the checks read is the URL the client uses ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.test\\@evil.example/x",
        "https://evil.example#@api.example.test/x",
        "https://api.example.test%2eevil.example/x",
        "https://api.example.test.evil.example/x",
        "https://api.example.test@evil.example/x",
        "https://api.example.test:443@evil.example/x",
        "https://api.example.test/x\n/y",
        "https://api.example.test/%2e%2e/x",
        "https://api.example.test/a/../x",
        "https://ａpi.example.test/x",  # full-width letter
    ],
)
def test_m6_parser_differentials_are_refused(url, monkeypatch):
    class Boom:
        def open(self, *a, **k):
            raise AssertionError("must be refused before any connection")

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Boom())
    ctx = tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.test"]}),
        3.0,
        bindings=k5_tools.READ_OPERATIONS,
    )
    with pytest.raises(tools_mod.ToolRefused):
        ctx.fetch("GET", url, operation="bundle.read")


# --- readiness ----------------------------------------------------------------------------------------------------------------------------------


def test_r1_hold_run_ids_is_wired_by_build_and_a_raising_hook_halts_purging(tmp_path):
    from tests.test_k5_tools import _age

    cfg = k5_cfg(tmp_path)
    qualify(load_registry(load_config(cfg)))
    k5_tools.RESULTS["app"] = "ERROR 10.0.0.5"
    held: set[str] = set()
    app = app_mod.build(
        cfg,
        ["test-agent"],
        secrets=SECRETS_PLUS,
        llm=ScriptLLM([{"tool": "app"}, {"noaction": True}] * 3),
        hold_run_ids=lambda: held,
    )
    keep = app.runtime.handle("test-agent", "svc:test-agent", b"a 10.0.0.5")
    held.add(keep.run_id)
    _age(app, keep.run_id, 40)
    tick_mod.run_tick(app, now=now())
    assert len(app.store.list_tool_calls(keep.run_id)) == 1  # held through the wired hook

    def broken():
        raise RuntimeError("hook down")

    app.runtime.hooks.hold_run_ids = broken
    other = app.runtime.handle("test-agent", "svc:test-agent", b"b 10.0.0.6")
    _age(app, other.run_id, 40)
    assert tick_mod.run_tick(app, now=now() + timedelta(days=2)) == 1  # the step failed, loudly
    assert len(app.store.list_tool_calls(other.run_id)) == 1  # and nothing was purged
    assert "hook down" in app.store.get_tick_state("purge_evidence").last_error


def test_r2_inputs_view_is_public_and_restores(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5; revision 17"
    store = MemoryStore()
    llm = ScriptLLM([{"tool": "app"}, {"propose": {"host": "<IPV4_1>", "revision": "17"}}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
    run = handle(rt)
    assert rt.inputs_view(run, store.get_plan(run.run_id)) == {"host": "10.0.0.5", "revision": "17"}


def test_r3_the_document_is_raw_and_the_map_belongs_to_it(tmp_path):
    store = MemoryStore()
    rt, _ = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"noaction": True}]), store=store)
    run = handle(rt, b"alert for 10.0.0.5", mapping={"<IPV4_1>": "10.0.0.5"})
    assert store.get_redaction_map(run.run_id) == {
        "<IPV4_1>": "10.0.0.5"
    }  # the intake placeholder is reused
    assert "RAW bytes" in Runtime.handle.__doc__
    # A document that already holds a placeholder-shaped literal is still raw text: the literal is escaped.
    store2 = MemoryStore()
    llm = ScriptLLM([{"noaction": True}])
    rt2, _ = build_runtime(k5_cfg(tmp_path / "b"), llm, store=store2)
    run2 = handle(rt2, b"already redacted <IPV4_1> text")
    assert b"\xe2\x80\xb9IPV4_1\xe2\x80\xba" in llm.sent[0]["documents"][0]
    assert store2.get_redaction_map(run2.run_id) == {}


def test_r5_held_maps_may_not_be_kept_for_less_time_than_ordinary_ones(tmp_path):
    with pytest.raises(ConfigError, match="held_maps_max_days must be at least"):
        load_config(
            k5_cfg(
                tmp_path,
                config={"retention": {"redaction_maps_days": 60, "held_maps_max_days": 30}},
            )
        )


# --- codebase nits ---------------------------------------------------------------------------------------------------------------------------------


def test_n3_a_tool_that_exits_is_a_failed_tool_not_a_dead_run(tmp_path):
    for body in ("SystemExit", "KeyboardInterrupt", "GeneratorExit"):
        spec = tools_mod.ToolSpec(**TOOL)

        def fn(args, ctx, body=body):
            raise {
                "SystemExit": SystemExit,
                "KeyboardInterrupt": KeyboardInterrupt,
                "GeneratorExit": GeneratorExit,
            }[body]()

        box = tools_mod.ToolBox({"read_logs": spec}, {"read_logs": fn}, timeout_s=2)
        out = box.invoke("read_logs", {"name": "x"}, {})
        assert out.error and body in out.text


def test_n3_the_deadline_state_is_snapshotted_under_a_lock():
    ctx = tools_mod.ToolContext(tools_mod.ToolSpec(**TOOL), 1.0, lambda n: "secret-value-1")
    ctx.handed_out.append("x")
    assert ctx.secrets_handed_out() == ["x"] and ctx.secrets_handed_out() is not ctx.handed_out


def test_n4_an_http_error_body_is_closed(monkeypatch):
    closed = []

    class Err(urllib.error.HTTPError):
        def close(self):
            closed.append(1)

    class Opener:
        def open(self, req, timeout=None):
            raise Err("https://api.example.test/x", 500, "boom", {}, None)

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    ctx = tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.test"]}),
        3.0,
        bindings=k5_tools.READ_OPERATIONS,
    )
    with pytest.raises(tools_mod.ToolRefused, match="HTTP 500"):
        ctx.fetch("GET", "https://api.example.test/x", operation="bundle.read")
    assert closed == [1]


def test_n5_text_is_kept_as_received_and_only_guarded_literals_change():
    text = "café 你好 \U0001f468‍\U0001f4bb Ａ <IPV4_9> ＜IPV4_8＞"
    out = runmap.escape_placeholders(text)
    assert out.startswith("café 你好 \U0001f468‍\U0001f4bb Ａ ")  # untouched, ZWJ kept
    assert "<IPV4_9>" not in out and "＜IPV4_8＞" not in out  # both look-alikes escaped


def test_n7_percent_and_dotdot_in_a_path_are_refused(monkeypatch):
    ctx = tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.test"]}),
        3.0,
        bindings=k5_tools.READ_OPERATIONS,
    )
    for url in ("https://api.example.test/a%2fb", "https://api.example.test/a/../b"):
        with pytest.raises(tools_mod.ToolRefused):
            ctx.fetch("GET", url, operation="bundle.read")


def test_n11_output_sha256_is_the_digest_of_the_fetched_bytes(monkeypatch):
    class Resp:
        def __init__(self):
            self.data = b"hello world"

        def read(self, n=-1):
            out, self.data = self.data[:n], self.data[n:]
            return out

        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False

    class Opener:
        def open(self, req, timeout=None):
            return Resp()

    import hashlib

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    ctx = tools_mod.ToolContext(
        tools_mod.ToolSpec(**{**TOOL, "hosts": ["api.example.test"]}),
        3.0,
        bindings=k5_tools.READ_OPERATIONS,
    )
    ctx.fetch("GET", "https://api.example.test/x", operation="bundle.read")
    assert ctx.digest() == hashlib.sha256(b"hello world").hexdigest()


# --- codebase minors ---------------------------------------------------------------------------------------------------------------------------------


def test_anchored_patterns_refuse_a_name_or_url_that_merely_contains_a_good_one():
    for name in ("Bad Name!x", "ok_name\nrm", "9lives"):
        with pytest.raises(ValidationError):
            tools_mod.ToolSpec(**{**TOOL, "name": name})
    assert tools_mod.ToolSpec(**{**TOOL, "name": "ok_name"})
    for url in (
        "ftp://x https://y",
        "https://a.example.test\nhttp://b",
        "x https://a.example.test",
    ):
        with pytest.raises(ValidationError):
            KubernetesSettings(api_url=url, namespaces=("prod",))
    assert KubernetesSettings(api_url="https://a.example.test:6443", namespaces=("prod",))


def test_the_executor_timeout_comes_from_config(tmp_path):
    cfg = k5_cfg(tmp_path, config={"executor_timeout_s": 3.5})
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(cfg, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]))
    assert app.executor.timeout_s == 3.5
    again = app_mod.build(
        cfg, ["test-agent"], secrets=SECRETS_PLUS, llm=ScriptLLM([]), timeout_s=1.5
    )
    assert again.executor.timeout_s == 1.5


def test_the_vault_provider_uses_the_shared_no_redirect_handler():
    from hadavin_sdk.actions import secrets_vault
    from hadavin_sdk.guard.http import NoRedirect

    assert secrets_vault.NoRedirect is NoRedirect and not hasattr(secrets_vault, "_NoRedirect")


def test_the_redirect_test_covers_the_shared_opener_too():
    handlers = [type(h).__name__ for h in tools_mod.http_guard.OPENER.handlers]
    assert "NoRedirect" in handlers and "HTTPRedirectHandler" not in handlers


def test_the_model_sees_its_own_call_arguments_in_later_steps(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5"
    llm = ScriptLLM([{"tool": "app"}, {"noaction": True}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm)
    handle(rt)
    assistant = [m["content"] for m in llm.sent[1]["messages"] if m["role"] == "assistant"]
    assert assistant == ['tool read_logs {"name": "app"}']
    assert "tool=read_logs" in json.dumps(llm.sent[1]["messages"])


# --- the gate offers what the runtime offers and matches by subset --------------------------------------------------------------------------------


def test_evals_matches_by_subset_and_offers_the_evidence_field(live_cfg_dir):
    assert evals.matches(
        {"action": "a", "inputs": {"x": 1, "opt": 2}}, {"action": "a", "inputs": {"x": 1}}
    )
    assert not evals.matches(
        {"action": "a", "inputs": {"x": 2}}, {"action": "a", "inputs": {"x": 1}}
    )
    assert not evals.matches({"action": "a", "inputs": {}}, {"action": "a", "inputs": {"x": 1}})
    assert not evals.matches(
        {"action": "b", "inputs": {"x": 1}}, {"action": "a", "inputs": {"x": 1}}
    )
    assert evals.matches({"action": None, "inputs": {}}, {"action": None, "inputs": {}})

    class Spy:
        def __init__(self):
            self.tools = []

        def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
            self.tools.append(tools)
            return Reply(model_id="fake-model")

    cfg = load_config(live_cfg_dir)
    reg = load_registry(cfg)
    spy = Spy()
    evals.gate(reg, spy, "test-agent")
    assert all(
        "evidence" not in t["input_schema"]["properties"] for t in spy.tools[0]
    )  # not tooled


def test_evals_gate_offers_evidence_to_a_tooled_agent(tmp_path):
    cfg = load_config(k5_cfg(tmp_path))
    reg = load_registry(cfg)
    inputs = cfg.inputs_dir
    (inputs / "x.txt").write_text("alert", encoding="utf-8")
    (cfg.golden_dir / "test-agent.jsonl").write_text(
        json.dumps({"id": "g1", "input_ref": "x.txt", "expected": {"action": None, "inputs": {}}})
        + "\n",
        encoding="utf-8",
    )

    class Spy:
        tools = None

        def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
            Spy.tools = tools
            return Reply(model_id="fake-model")

    evals.gate(reg, Spy(), "test-agent")
    undo = next(t for t in Spy.tools if t["name"] == "rollout_undo")
    assert "evidence" in undo["input_schema"]["required"]


# --- sources --------------------------------------------------------------------------------------------------------------------------------------------


def test_n9_an_evaluation_error_is_not_a_pass():
    from tests.contracts.sources import ks

    def fetch(method, url, *, operation, body=None, headers=None, max_bytes=None):
        return json.dumps({"status": {"evaluationError": "webhook down", "resourceRules": []}})

    assert any("evaluation error" in p for p in ks(fetch).probe_scope())


def test_n10_a_403_is_not_retried_and_a_limit_stop_is_marked():
    from tests.contracts.sources import ks

    calls = []

    class Refused(OSError):
        too_large = False

    def fetch(method, url, *, operation, body=None, headers=None, max_bytes=None):
        calls.append(url)
        raise Refused("HTTP 403")

    from hadavin_sdk.sources import SourceError

    with pytest.raises(SourceError):
        ks(fetch).recent_changes("prod", "2026-11-01T10:00:00Z", "2026-11-01T11:00:00Z")
    assert len(calls) == 1  # asking for a smaller page would not help

    lines = "".join(f"2026-11-01T10:00:0{i}Z line {i}\n" for i in range(5))
    rows = ks(lambda *a, **k: lines).query_logs(
        "prod/p", "2026-11-01T09:00:00Z", "2026-11-01T11:00:00Z", 2
    )
    assert rows[-1]["kind"] == "incomplete" and "limit of 2" in rows[-1]["note"]


def test_n10_timestamps_compare_as_instants():
    from hadavin_sdk.sources.kubernetes import _after, _within

    assert _within("2026-11-01T10:30:00+00:00", "2026-11-01T10:00:00Z", "2026-11-01T11:00:00Z")
    assert _within("2026-11-01T12:30:00+02:00", "2026-11-01T10:00:00Z", "2026-11-01T11:00:00Z")
    assert not _after("2026-11-01T10:30:00+00:00", "2026-11-01T11:00:00Z")
    assert _after("2026-11-01T11:30:00+00:00", "2026-11-01T11:00:00Z")


# --- tool modules are pinned by hash -----------------------------------------------------------------------------------------------------------------


def test_m1_design_tool_modules_must_be_pinned_in_pilot_and_prod(tmp_path):
    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(
        tmp_path / "a",
        agent={"tools_allowed": ["read_logs"]},
        config={"tool_modules": ["tests.fixtures.k5_tools"]},
    )
    (root / "tools").mkdir()
    (root / "tools" / "ito-agent.yaml").write_text(yaml.safe_dump([TOOL]), encoding="utf-8")
    with pytest.raises(ConfigError, match="no tool_module_hashes pin"):
        load_registry(load_config(root))


def test_m1_design_a_pin_that_does_not_match_the_source_is_refused(tmp_path):
    cfg = k5_cfg(tmp_path, config={"tool_module_hashes": {"tests.fixtures.k5_tools": "0" * 64}})
    with pytest.raises(ConfigError, match="the pin says"):
        load_registry(load_config(cfg))
    good = k5_cfg(
        tmp_path / "ok",
        config={
            "tool_module_hashes": {
                "tests.fixtures.k5_tools": tools_mod.module_sha256("tests.fixtures.k5_tools")
            }
        },
    )
    assert load_registry(load_config(good)).tools["test-agent"]


def test_notfound_is_the_specific_error_for_a_missing_plan(tmp_path):
    rt, _ = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"noaction": True}]))
    run = handle(rt)
    with pytest.raises(NotFound):
        rt.store.get_plan(run.run_id)
