"""K5-core review round 10 (two egm:* reviews of head 39d149d). Each test names the finding it closes."""

from __future__ import annotations

import ipaddress
import sys
import time
import urllib.error
import urllib.request

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import sources as sources_mod
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.actions.contract import schema_problems
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.egress import EgressRefused
from hadavin_sdk.models import RunState
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import evidence
from tests.fixtures import k5_tools
from tests.k5_support import SECRETS, TOOL, ScriptLLM, build_runtime, handle, k5_cfg

S = RunState


def _redact_module():
    return sys.modules["hadavin_sdk.guard.redact"]


# --- CODE B1: a tool whose source was switched off by the re-probe does not run ------------------------------------------------


def _box(tmp_path, tool, disabled, hosts=None):
    cfg = load_config(k5_cfg(tmp_path, tools=[tool]))
    box = app_mod._toolbox(
        cfg, load_registry(cfg), SECRETS, disabled_sources=disabled, source_hosts=hosts or {}
    )
    ran = []
    box._fns["read_logs"] = lambda args, ctx: ran.append(1) or "ok"
    return box, ran


def test_a_tool_reading_a_switched_off_source_is_refused_through_toolbox_invoke(tmp_path):
    disabled: set[str] = set()
    box, ran = _box(tmp_path, {**TOOL, "options": {"source": "cluster"}}, disabled)
    assert not box.invoke("read_logs", {"name": "a"}, {}).error and ran == [1]
    disabled.add("cluster")  # what the tick does when the re-probe finds a problem
    out = box.invoke("read_logs", {"name": "a"}, {})
    assert out.error and "switched off" in out.text and ran == [1]  # the body did not run again
    disabled.discard("cluster")  # and when a probe passes again
    assert not box.invoke("read_logs", {"name": "a"}, {}).error


def test_a_tool_on_a_switched_off_sources_host_is_refused_too(tmp_path):
    tool = {**TOOL, "hosts": ["kube.example.test"]}
    box, ran = _box(tmp_path, tool, {"cluster"}, hosts={"cluster": "kube.example.test"})
    out = box.invoke("read_logs", {"name": "a"}, {})
    assert out.error and "switched off" in out.text and ran == []


# --- M1: a live deployment on postgres must name the purge identity -----------------------------------------------------------------


def test_a_live_postgres_deployment_without_a_purge_dsn_does_not_start(tmp_path):
    import yaml

    from tests.test_k3_pilot_env import pilot_cfg

    cfg = pilot_cfg(tmp_path)
    path = cfg / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["backends"]["store"]["purge_dsn_secret_name"]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="purge_dsn_secret_name"):
        app_mod.build(cfg, ["ito-agent"], secrets=SECRETS, llm=ScriptLLM([]))


# --- M3: the restored-hash key must be real ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["", "short", "x" * 15])
def test_an_empty_or_short_restored_hash_key_is_refused(value):
    with pytest.raises(ConfigError, match="at least"):
        app_mod._restored_key(FakeSecretProvider({"k": value}), "k")


def test_a_sixteen_byte_key_is_accepted():
    assert app_mod._restored_key(FakeSecretProvider({"k": "k" * 16}), "k") == b"k" * 16


# --- M4: redaction cost does not grow with the map per string; a bigger map is refused ------------------------------------------


def test_the_redactor_is_built_once_per_map_change_not_once_per_string(monkeypatch):
    mod = _redact_module()
    builds: list[int] = []
    real = mod._Redactor._build
    monkeypatch.setattr(mod._Redactor, "_build", lambda self: (builds.append(1), real(self))[1])
    rmap = runmap.RunMap()
    runmap.redact_untrusted(" ".join(f"10.0.{i // 250}.{i % 250 + 1}" for i in range(500)), rmap)
    after_intake = len(builds)
    for i in range(100):  # 40 tool calls x 5 strings is 200: nothing new in them, so no rebuild
        runmap.redact_value({"a": f"x {i}", "b": "y"}, rmap)
    assert len(builds) == after_intake


def test_a_non_ascii_text_does_not_rebuild_for_each_of_its_passes(monkeypatch):
    mod = _redact_module()
    builds: list[int] = []
    real = mod._Redactor._build
    monkeypatch.setattr(mod._Redactor, "_build", lambda self: (builds.append(1), real(self))[1])
    rmap = runmap.RunMap()
    runmap.redact_untrusted("host 10.0.0.5 é mail ａ@example.com", rmap)
    assert (
        len(builds) <= 3
    )  # one per pass at most (pass one, the canonical view, the unescaped view)


def test_the_cpu_of_a_full_size_run_stays_in_budget():
    rmap = runmap.RunMap()
    doc = " ".join(f"10.{i // 60000}.{(i // 250) % 240}.{i % 250 + 1}" for i in range(1500))
    t0 = time.process_time()
    runmap.redact_untrusted(
        doc, rmap
    )  # intake: 1,500 distinct addresses (under the default cap of 2,000)
    for i in range(40):  # then 40 tool calls x 5 strings of arguments
        runmap.redact_value({f"k{j}": f"value {i} {j} 10.9.9.{j}" for j in range(5)}, rmap)
    assert (
        time.process_time() - t0 < 30
    )  # measured about 1 s; the old per-string rebuild took minutes


def test_a_document_with_too_many_distinct_values_is_refused_not_ground_through(tmp_path):
    cfg = k5_cfg(tmp_path, config={"evidence": {"max_map_entries": 20}})
    rt, _ = build_runtime(cfg, ScriptLLM([{"noaction": True}]))
    doc = " ".join(f"10.1.1.{i}" for i in range(1, 60)).encode()
    run = handle(rt, document=doc)
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "document_too_complex")
    assert all(e.caught_by is None for e in rt.audit.events(run.run_id))  # a refusal, not a catch


# --- M6: what the pin does and does not do ---------------------------------------------------------------------------------------


def _module(tmp_path, monkeypatch, name, body, extra=None):
    mods = tmp_path / "mods"
    mods.mkdir(exist_ok=True)
    (mods / f"{name}.py").write_text(body, encoding="utf-8")
    for other, text in (extra or {}).items():
        (mods / f"{other}.py").write_text(text, encoding="utf-8")
    monkeypatch.syspath_prepend(str(mods))
    for n in (name, *(extra or {})):
        monkeypatch.delitem(sys.modules, n, raising=False)
    return name


def test_an_absolute_import_of_an_unpinned_sibling_is_still_allowed_by_design(
    tmp_path, monkeypatch
):
    """The pin proves the reviewed text of ONE file is what runs. A sibling it imports by absolute name is not
    covered (a tool body is trusted code; the boundary is code review plus K7), and the README says so."""
    name = _module(
        tmp_path, monkeypatch, "r10_main", "import r10_helper\nVALUE = r10_helper.VALUE\n",
        extra={"r10_helper": "VALUE = 7\n"},
    )  # fmt: skip
    mod = tools_mod.load_tool_module(name, {name: tools_mod.module_sha256(name)})
    assert mod.VALUE == 7
    sys.modules.pop(name, None)
    sys.modules.pop("r10_helper", None)


def test_a_string_that_happens_to_say_exec_is_not_a_loader(tmp_path, monkeypatch):
    body = 'FIELDS = {"exec": "command", "eval": 1, "builtins": []}\nX = FIELDS["exec"]\n'
    name = _module(tmp_path, monkeypatch, "r10_fields", body)
    assert tools_mod.load_tool_module(name, {name: tools_mod.module_sha256(name)}).X == "command"
    sys.modules.pop(name, None)


def test_the_refusal_message_does_not_claim_a_boundary(tmp_path, monkeypatch):
    name = _module(tmp_path, monkeypatch, "r10_loader", "import runpy\n")
    with pytest.raises(ConfigError) as err:
        tools_mod.load_tool_module(name, {name: tools_mod.module_sha256(name)})
    assert "tripwire" in str(err.value) and "trusted code" in str(err.value)


# --- M8: an identifier that is not a string cannot be grounded ----------------------------------------------------------------------


def test_a_non_string_identifier_value_is_ungrounded(tmp_path):
    cfg = k5_cfg(
        tmp_path,
        action={
            "input_schema": {
                "type": "object",
                "required": ["name"],
                "additionalProperties": False,
                "properties": {"name": {"type": "string", "identifier": True}},
            }
        },
    )
    contract = load_registry(load_config(cfg)).contracts["rollout_undo"]
    assert not evidence.grounded(contract, {"name": 17}, ["pod 17"], {})
    assert not evidence.grounded(contract, {"name": ["pod"]}, ["pod"], {})
    assert evidence.grounded(
        contract, {}, ["pod"], {}
    )  # an input the model left out is the schema's business


@pytest.mark.parametrize(
    "schema",
    [
        {"identifier": True},
        {"type": "integer", "identifier": True},
        {"type": ["string", "null"], "identifier": True},
    ],
)
def test_identifier_true_needs_a_string_type_at_load(schema):
    assert schema_problems({"type": "object", "properties": {"n": schema}})


# --- redaction: every bound masks instead of letting text through; the disclosed limits are pinned ------------------------------------------


def test_a_command_flag_after_the_1024_character_gap_is_masked_to_the_end_of_the_line():
    out = runmap.redact_untrusted("mysql" + " " * 1100 + " -pHunter2xyz and more", {})
    assert "Hunter2xyz" not in out


def test_a_quoted_credential_over_255_characters_is_masked_whole():
    out = runmap.redact_untrusted('tool --password "' + "Sx9" * 100 + '" ok', {})
    assert "Sx9Sx9Sx9" not in out


def test_a_url_password_over_1024_characters_is_masked():
    out = runmap.redact_untrusted("postgres://app:" + "pq" * 600 + "@db.example.test/x", {})
    assert "pqpqpqpq" not in out


def test_an_email_with_a_local_part_over_254_characters_is_masked():
    out = runmap.redact_untrusted("to " + "a1" * 150 + "@example.com now", {})
    assert "a1a1a1a1" not in out and "example.com" not in out


def test_a_known_value_spelled_in_full_width_is_masked_by_the_second_pass():
    rmap = runmap.RunMap()
    runmap.redact_untrusted("first AKIAIOSFODNN7EXAMPLE seen", rmap)
    before = dict(rmap)
    # pass one cannot read this spelling, so the map does not grow; only the held count tells the second pass it won
    out = runmap.redact_untrusted("again ＡＫＩＡIOSFODNN7EXAMPLE seen", rmap)
    assert dict(rmap) == before
    assert "IOSFODNN7EXAMPLE" not in out and "ＡＫＩＡ" not in out


def test_originals_over_256_characters_are_masked_but_never_stored():
    rmap = runmap.RunMap()
    runmap.redact_untrusted("name: " + "Ab " * 120 + "x@example.com", rmap)
    assert runmap.storable(rmap) == {k: v for k, v in rmap.items() if len(v) <= 256}


# --- code nits ---------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("ip", ["168.63.129.16", "fd20:ce::254"])
def test_more_cloud_metadata_addresses_are_refused(ip):
    assert http_guard._refused(ipaddress.ip_address(ip))


def test_one_refused_answer_among_good_ones_refuses_the_whole_name(monkeypatch):
    answers = [(2, 1, 6, "", ("93.184.216.34", 443)), (2, 1, 6, "", ("169.254.169.254", 443))]
    monkeypatch.setattr(http_guard.socket, "getaddrinfo", lambda *a, **k: answers)
    monkeypatch.setattr(
        http_guard.socket, "create_connection", lambda *a, **k: pytest.fail("connected")
    )
    with pytest.raises(EgressRefused):
        http_guard.checked_connection(("mixed.example.test", 443))


def test_a_name_lookup_that_never_answers_is_refused(monkeypatch):
    monkeypatch.setattr(http_guard, "RESOLVE_TIMEOUT_S", 0.2)
    monkeypatch.setattr(http_guard.socket, "getaddrinfo", lambda *a, **k: time.sleep(3))
    with pytest.raises(OSError, match="name lookup"):
        http_guard.checked_connection(("slow.example.test", 443))


def test_an_environment_proxy_does_not_receive_the_connection(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.test:3128")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.test:3128")
    asked: list[str] = []

    def lookup(host, *a, **k):
        asked.append(host)
        raise OSError("no network in the test")

    monkeypatch.setattr(http_guard.socket, "getaddrinfo", lookup)
    with pytest.raises(urllib.error.URLError):
        http_guard.OPENER.open(urllib.request.Request("https://target.example.test/x"), timeout=2)
    assert asked == [
        "target.example.test"
    ]  # the target is looked up and checked here, not handed to a proxy


def test_source_reads_count_toward_the_same_request_cap(tmp_path, monkeypatch):
    class Resp:
        def __init__(self):
            self.chunks = [b'{"status": {"resourceRules": []}}', b""]

        def read(self, n=-1):
            return self.chunks.pop(0) if self.chunks else b""

        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False

    class Opener:
        def open(self, req, timeout=None):
            return Resp()

    monkeypatch.setattr(tools_mod.http_guard, "OPENER", Opener())
    source = {
        "cluster": {
            "kind": "kubernetes",
            "settings": {"api_url": "https://kube.example.test", "namespaces": ["prod"]},
            "token_secret_name": "tool-key",
        }
    }
    cfg = load_config(k5_cfg(tmp_path, config={"sources": source}))
    counter = tools_mod.FetchCounter(1)
    src = app_mod._build_source("cluster", cfg.sources["cluster"], cfg, SECRETS, set(), counter)
    assert src.probe_scope() == []
    with pytest.raises(sources_mod.SourceError):  # the second request in the minute is refused
        src.probe_scope()


def test_a_post_read_operation_needs_the_deployments_permission(tmp_path):
    tool = {**TOOL, "operations": ["bundle.post"]}
    with pytest.raises(ConfigError, match="post_read_operations"):
        load_registry(load_config(k5_cfg(tmp_path / "a", tools=[tool])))
    allowed = k5_cfg(
        tmp_path / "b", tools=[tool], config={"evidence": {"post_read_operations": ["bundle.post"]}}
    )
    assert load_registry(load_config(allowed)).tools["test-agent"]["read_logs"]


def test_a_thread_that_cannot_start_does_not_leak_the_slot(monkeypatch):
    spec = tools_mod.ToolSpec(**TOOL)
    box = tools_mod.ToolBox(
        {"read_logs": spec}, {"read_logs": lambda a, c: "ok"}, timeout_s=2, max_concurrent=1
    )

    class Broken:
        def __init__(self, *a, **k):
            raise RuntimeError("cannot start a thread")

    real = tools_mod.threading.Thread
    monkeypatch.setattr(tools_mod.threading, "Thread", Broken)
    assert box.invoke("read_logs", {"name": "x"}, {}).error
    monkeypatch.setattr(tools_mod.threading, "Thread", real)
    assert not box.invoke("read_logs", {"name": "x"}, {}).error  # the slot was released


def test_the_first_tool_call_still_works_with_the_shared_counter(tmp_path):
    k5_tools.RESULTS["app"] = "ok"
    cfg = load_config(k5_cfg(tmp_path))
    box = app_mod._toolbox(
        cfg, load_registry(cfg), SECRETS, fetch_counter=tools_mod.FetchCounter(5)
    )
    assert not box.invoke("read_logs", {"name": "app"}, {}).error
