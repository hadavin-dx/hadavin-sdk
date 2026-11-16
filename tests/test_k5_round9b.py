"""K5-core review round 9, part two: majors M2 to M4 and the minors. Most of these fail on head bdb1f6f."""

from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import re
import sys
import threading
import urllib.request
from datetime import UTC, datetime
from html import escape as _unused  # noqa: F401  (kept out of the way of the secret literals below)
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import sources as sources_mod
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime import tick as tick_mod
from hadavin_sdk.sources.kubernetes import rules_problems
from tests.fixtures import k5_tools
from tests.k5_support import SECRETS, TOOL, ScriptLLM, build_runtime, handle, k5_cfg


def _redact_module():
    return sys.modules["hadavin_sdk.guard.redact"]


# --- M2: no client value reaches `re`'s process-wide compile cache ---------------------------------------------------------------


def _re_cache_text() -> str:
    caches = [getattr(re, n, {}) for n in ("_cache", "_cache2")]
    return " ".join(str(k) for c in caches for k in c)


def test_no_client_value_is_left_in_the_re_compile_cache(tmp_path):
    ip, mail, pod = "10.77.66.55", "bob.canary@acme-corp.example", "acme-billing-canary-9x"
    re.purge()
    runmap.redact_untrusted(f"upstream {ip} mail {mail} again {ip} {mail}", {})
    assert evidence.contains(f"pod {pod} up", pod)
    k5_tools.RESULTS["app"] = f"ERROR upstream {ip} refused; pod {pod}"
    rt, _ = build_runtime(k5_cfg(tmp_path), ScriptLLM([{"tool": "app"}, {"noaction": True}]))
    handle(rt, document=f"checkout 5xx from {ip}, {mail} {pod}".encode())
    cached = _re_cache_text()
    assert "10.77.66.55" not in cached.replace("\\", "") and "acme" not in cached
    assert "canary" not in cached


# --- M3: loader names in a pinned module are refused (a best-effort tripwire, not a boundary) ----------------------------------------------------------------------


def _module(tmp_path, monkeypatch, name, body):
    mods = tmp_path / "mods"
    mods.mkdir(exist_ok=True)
    (mods / f"{name}.py").write_text(body, encoding="utf-8")
    monkeypatch.syspath_prepend(str(mods))
    monkeypatch.delitem(sys.modules, name, raising=False)
    return name


_BYPASSES = [
    "m = __import__('x', globals(), level=1)\n",
    "m = __import__('x', globals(), locals(), [], 1)\n",
    "from importlib import import_module as im\nim('.x', __package__)\n",
    "import importlib\nim = importlib.import_module\n",
    "import importlib\ngetattr(importlib, 'import_module')('.x', __package__)\n",
    "import builtins\nbuiltins.__import__('x')\n",
    "exec('import os')\n",
    "x = eval('1')\n",
    "import runpy\nrunpy.run_path('x.py')\n",
    "from importlib.util import spec_from_file_location\n",
    "import importlib.util\n",
]


@pytest.mark.parametrize("body", _BYPASSES)
def test_loader_names_are_refused_as_a_best_effort_tripwire(tmp_path, monkeypatch, body):
    name = _module(tmp_path, monkeypatch, "r9_bypass", body)
    with pytest.raises(ConfigError, match="refused loader name"):
        tools_mod.load_tool_module(name, {name: tools_mod.module_sha256(name)})
    sys.modules.pop(name, None)


def test_an_ordinary_pinned_module_still_loads(tmp_path, monkeypatch):
    body = "import json\nimport re\nX = re.compile('a')\nY = json.dumps({})\n"
    name = _module(tmp_path, monkeypatch, "r9_plain", body)
    assert tools_mod.load_tool_module(name, {name: tools_mod.module_sha256(name)}).Y == "{}"
    sys.modules.pop(name, None)


# --- M4: the concurrency slot is held until the tool's thread ENDS ----------------------------------------------------------------


def test_a_timed_out_tool_keeps_its_slot_until_its_thread_ends():
    spec = tools_mod.ToolSpec(**TOOL)
    release, started = threading.Event(), threading.Event()

    def stuck(args, ctx):
        started.set()
        release.wait(10)
        return "late"

    box = tools_mod.ToolBox(
        {"read_logs": spec}, {"read_logs": stuck}, timeout_s=0.3, max_concurrent=1, max_abandoned=8
    )
    first = box.invoke("read_logs", {"name": "x"}, {})
    assert started.is_set() and first.error and "timed out" in first.text
    second = box.invoke("read_logs", {"name": "y"}, {})  # the first body is still running
    assert second.error and "at once" in second.text
    release.set()
    for _ in range(100):
        if box.abandoned() == 0:
            break
        threading.Event().wait(0.05)
    box._fns["read_logs"] = lambda a, c: "ok"
    assert not box.invoke("read_logs", {"name": "z"}, {}).error


def test_every_request_to_a_client_system_counts_toward_the_rate_cap(monkeypatch):
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
    spec = tools_mod.ToolSpec(
        **{**TOOL, "hosts": ["api.example.test"], "operations": ["bundle.read"]}
    )

    def two_fetches(args, ctx):
        for _ in range(2):
            ctx.fetch("GET", "https://api.example.test/x", operation="bundle.read")
        return "ok"

    box = tools_mod.ToolBox(
        {"read_logs": spec},
        {"read_logs": two_fetches},
        timeout_s=2,
        bindings={"bundle.read": ("GET", r"/.*")},
        max_per_minute=3,
    )
    assert not box.invoke("read_logs", {"name": "a"}, {}).error  # 2 fetches
    second = box.invoke("read_logs", {"name": "b"}, {})  # 1 more fetch fits, the next does not
    assert second.error and "request rate" in second.text


# --- m1: an environment proxy cannot skip the address check -------------------------------------------------------------------------


def test_tools_never_use_an_environment_proxy(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.test:3128")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.test:3128")
    import ssl

    for opener in (http_guard.OPENER, http_guard.opener_for(ssl.create_default_context())):
        proxy_handlers = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
        assert all(not h.proxies for h in proxy_handlers)  # none, or one with no proxies


# --- m2: metadata addresses and the IPv6 forms that carry them ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "ip",
    [
        "2002:a9fe:a9fe::1",  # 6to4 of 169.254.169.254
        "2001:0:a9fe:a9fe::1",  # Teredo server 169.254.169.254
        "64:ff9b::a9fe:a9fe",  # NAT64
        "fd00:ec2::254",  # the cloud metadata service over IPv6
        "100.100.100.200",
        "192.0.0.192",
        "198.18.0.7",
        "::ffff:7f00:1",
    ],
)
def test_metadata_addresses_and_the_forms_that_carry_them_are_refused(ip):
    assert http_guard._refused(ipaddress.ip_address(ip))


@pytest.mark.parametrize(
    "ip", ["10.0.0.5", "172.16.4.4", "93.184.216.34", "100.64.0.9", "2606:4700::1"]
)
def test_ordinary_private_and_public_addresses_are_allowed(ip):
    assert not http_guard._refused(ipaddress.ip_address(ip))


# --- m3: generated_suffix is a tiny language, so it cannot backtrack or match any longer name ---------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "(.*)*x",
        ".+",
        ".*",
        "[a-z]+",
        "a|b",
        "(x)",
        "[a-z]{1,99}",
        "[a-z]{5,2}",
        "x" * 201,
        "(?=x)y",
        "a?",
    ],
)
def test_a_catastrophic_or_over_broad_suffix_is_refused(bad):
    assert tools_mod.suffix_problem(bad)


def test_the_pod_hash_suffix_is_accepted():
    assert tools_mod.suffix_problem(r"-[0-9a-f]{5,10}-[a-z0-9]{5}") is None
    assert tools_mod.suffix_problem(r"\.v[0-9]{1,3}") is None


# --- m4: nothing escapes at a scanning bound ------------------------------------------------------------------------------------------


def test_a_long_token_whose_mix_of_cases_comes_late_is_still_masked():
    token = "a" * 140 + "Ab1" + "a" * 10
    out = runmap.redact_untrusted(f"blob {token} end", {})
    assert "aaaaaaaaaa" not in out


def test_a_jwt_with_huge_segments_is_masked_whole():
    jwt = "eyJ" + "a" * 6000 + "." + "b" * 6000 + "." + "c" * 6000
    out = runmap.redact_untrusted(f"Authorization: {jwt}", {})
    assert "aaaaaaaaaa" not in out and "bbbbbbbbbb" not in out and "cccccccccc" not in out


def test_a_very_long_url_password_is_masked():
    out = runmap.redact_untrusted("postgres://app:" + "p" * 600 + "@db.example.test/x", {})
    assert "pppppppppp" not in out


# --- m5: more encodings of a handed-out secret ----------------------------------------------------------------------------------------

_SECRET = "Zx9/" + "Qw+ab12=Pq"


def _more_layers():
    b64 = base64.b64encode(_SECRET.encode()).decode()
    return {
        "double percent": quote(quote(_SECRET, safe=""), safe=""),
        "base32": base64.b32encode(_SECRET.encode()).decode(),
        "base32 lower": base64.b32encode(_SECRET.encode()).decode().lower(),
        "triple base64": base64.b64encode(base64.b64encode(b64.encode())).decode(),
    }


@pytest.mark.parametrize("layer", list(_more_layers()))
def test_the_scrub_sees_these_encodings_too(layer):
    variant = _more_layers()[layer]
    out = tools_mod.prepare_output(f"key: {variant} end", {}, 4096, [_SECRET])
    assert variant not in out and "SECRET_REDACTED" in out


# --- m6: a failed re-probe switches the source off, and a malformed rule proves nothing ------------------------------------------------


@pytest.mark.parametrize(
    "rule",
    [
        {
            "verbs": "create",
            "apiGroups": ["authorization.k8s.io"],
            "resources": ["selfsubjectaccessreviews"],
        },
        {"verbs": ["get"], "resources": "pods"},
        {"verbs": ["get"], "apiGroups": [1], "resources": ["pods"]},
        "get pods",
    ],
)
def test_a_malformed_rule_is_not_proven_read_only(rule):
    assert rules_problems("prod", [rule])


def test_a_failed_reprobe_switches_the_source_off_until_a_probe_passes():
    class Src:
        def __init__(self):
            self.found: list[str] = []

        def probe_scope(self):
            return self.found

    src = Src()
    app = SimpleNamespace(
        sources={"c": src}, disabled_sources=set(), config=SimpleNamespace(scope_inventory={})
    )
    ctx = tick_mod.TickContext(app, datetime.now(UTC))
    src.found = ["namespace prod: write verb patch on ['deployments']"]
    with pytest.raises(RuntimeError):
        tick_mod.reprobe_sources(ctx)
    assert app.disabled_sources == {"c"}
    src.found = []
    tick_mod.reprobe_sources(ctx)
    assert app.disabled_sources == set()


def test_a_switched_off_source_refuses_reads_but_still_answers_the_probe(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        tools_mod.ToolContext,
        "fetch",
        lambda self, *a, **k: (
            calls.append(k.get("operation")) or '{"status": {"resourceRules": []}}'
        ),
    )
    source = {
        "cluster": {
            "kind": "kubernetes",
            "settings": {"api_url": "https://kube.example.test", "namespaces": ["prod"]},
            "token_secret_name": "tool-key",
        }
    }
    cfg = load_config(k5_cfg(tmp_path, config={"sources": source}))
    src = app_mod._build_source("cluster", cfg.sources["cluster"], cfg, SECRETS, {"cluster"})
    with pytest.raises(sources_mod.SourceError):
        src.probe_scope()
    assert calls == []  # switched off: nothing was sent
    token = sources_mod.PROBING.set(True)
    try:
        assert src.probe_scope() == []  # the probe itself still gets through
    finally:
        sources_mod.PROBING.reset(token)
    assert calls == ["k8s.rules_review"]


# --- m7: the restored-values hash is keyed ----------------------------------------------------------------------------------------------


def test_the_restored_hash_is_an_hmac_under_the_deployment_key(tmp_path):
    k5_tools.RESULTS["app"] = "ERROR upstream 10.0.0.5 refused; revision 17"
    llm = ScriptLLM([{"tool": "app"}, {"propose": {"host": "<IPV4_1>", "revision": "17"}}])
    rt, _ = build_runtime(k5_cfg(tmp_path), llm)
    rt.hooks.restored_key = b"deployment-key-0123456789"
    run = handle(rt)
    plain = hashlib.sha256(b'{"host":"10.0.0.5","revision":"17"}').hexdigest()
    decide = next(
        e for e in rt.audit.events(run.run_id) if e.domain == "gate" and e.operation == "decide"
    )
    keyed = hmac.new(rt.hooks.restored_key, b'{"host":"10.0.0.5","revision":"17"}', hashlib.sha256)
    assert (
        decide.restored_hash == keyed.hexdigest() != plain
    )  # a reader cannot confirm a guessed IP


def test_a_live_deployment_without_the_key_does_not_start(tmp_path):
    from tests.test_k3_pilot_env import pilot_cfg

    cfg = pilot_cfg(tmp_path, config={"evidence": {}})
    with pytest.raises(ConfigError, match="restored_hash_key_secret_name"):
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS, llm=ScriptLLM([]))


# --- m8: no credential-bearing header over plain http --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header", ["Proxy-Authorization", "X-Api-Key", "Cookie", "X-Auth-Token", "Authorization"]
)
def test_a_credential_header_is_refused_over_plain_http(header):
    spec = tools_mod.ToolSpec(
        **{**TOOL, "hosts": ["api.svc"], "cluster_http": True, "operations": ["bundle.read"]}
    )
    ctx = tools_mod.ToolContext(
        spec, 5.0, None, {"bundle.read": ("GET", r"/.*")}, cluster_suffixes=(".svc",)
    )
    with pytest.raises(tools_mod.ToolRefused, match="plain http"):
        ctx.fetch("GET", "http://api.svc/x", operation="bundle.read", headers={header: "abc"})


def _execute_with(tmp_path, restored):
    from hadavin_sdk.models import RunResult, RunState
    from tests.test_k5_tools import _execute_runtime

    ran = []

    def execute(plan, decision, approval, inputs_view=None):
        ran.append(inputs_view)
        return RunResult(outcome="succeeded", external_ref="r")

    rt, store, run = _execute_runtime(tmp_path, execute)
    store.put_redaction_map(run.run_id, {"<NAME_1>": restored})
    return rt, run, ran, RunState


def test_an_execution_on_values_other_than_the_approved_ones_is_stopped(tmp_path):
    rt, run, ran, state = _execute_with(
        tmp_path, "rec-124"
    )  # the helper's decide event says rec-123
    done = rt.execute(run.run_id)
    assert (done.state, done.reason_code) == (state.NEEDS_PERSON, "restored_changed")
    assert ran == []  # nothing was executed


def test_an_execution_with_no_recorded_hash_is_refused_not_skipped(tmp_path, monkeypatch):
    rt, run, ran, state = _execute_with(tmp_path, "rec-123")
    monkeypatch.setattr(rt.audit, "events", lambda run_id=None: [])
    done = rt.execute(run.run_id)
    assert (done.state, done.reason_code) == (state.NEEDS_PERSON, "restored_unbound")
    assert ran == []


def test_an_execution_on_the_approved_values_goes_through(tmp_path):
    rt, run, ran, state = _execute_with(tmp_path, "rec-123")
    assert rt.execute(run.run_id).state == state.SUCCEEDED and ran == [{"id": "rec-123"}]
