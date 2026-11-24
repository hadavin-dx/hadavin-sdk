"""Slice 2 P5: the llm kinds' wiring outside the contract suite (design 4.3, 12.10)."""

import json
import re
import ssl
import urllib.error
from email.message import Message
from pathlib import Path
from urllib.request import ProxyHandler

import pytest
import yaml

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import AnthropicSettings, OpenAICompatSettings
from hadavin_sdk.config import load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm import ProviderError, ProviderExhausted
from hadavin_sdk.llm.common import ANSWER_TOOL, stop_reason
from hadavin_sdk.llm.retry import MAX_DELAY_S, transient, with_retry
from hadavin_sdk.models import Reply, RunState, ToolCall
from hadavin_sdk.registry import load_registry
from tests.contracts.kinds.builtin import ROUTES
from tests.contracts.kinds.llm_wire import KEY, AnthropicWire, GeminiWire, OpenAICompatWire
from tests.contracts.test_llm import CALL, SCHEMA
from tests.test_s5_runtime import build


def _llm(cfg_dir, entry):
    path = cfg_dir / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["backends"]["llm"] = entry
    raw["made_up_data_only"] = True  # a real llm kind in demo
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return load_registry(load_config(cfg_dir)).config_hash("test-agent")


def test_where_the_model_runs_is_in_the_config_hash(cfg_dir):
    """A backend swap needs a new gate run, and so does a platform or host swap with the same model id."""
    api = _llm(cfg_dir, {"kind": "anthropic", "api_key_secret_name": "a", "platform": "api"})
    vertex = _llm(
        cfg_dir, {"kind": "anthropic", "platform": "vertex", "project_id": "p", "region": "global"}
    )
    local = _llm(cfg_dir, {"kind": "openai_compat", "base_url": "http://localhost:11434/v1"})
    other = _llm(cfg_dir, {"kind": "openai_compat", "base_url": "https://llm.example/v1"})
    assert len({api, vertex, local, other}) == 4
    # Retry settings say how the call is made, not which model answers: no new gate run.
    tuned = {"kind": "anthropic", "api_key_secret_name": "a", "platform": "api", "max_attempts": 5}
    assert _llm(cfg_dir, tuned) == api


def test_a_refused_provider_needs_a_person(cfg_dir):
    rt, cfg = build(cfg_dir)

    def refused(*a, **k):
        raise ProviderError("anthropic: AuthenticationError 401")

    rt.llm.chat = refused
    run = rt.handle("test-agent", "svc:test-agent", (cfg.inputs_dir / "create.txt").read_bytes())
    assert (run.state, run.reason_code) == (RunState.NEEDS_PERSON, "provider_error")


class _Status(Exception):
    def __init__(self, status):
        super().__init__(status)
        self.status_code = status


def test_backoff_is_exponential_with_jitter_and_bounded():
    waits = []
    calls = iter([_Status(529), _Status(503), _Status(429), _Status(500)])

    def call():
        raise next(calls)

    with pytest.raises(ProviderExhausted):
        with_retry(call, label="t", max_attempts=4, sleep=waits.append)
    assert len(waits) == 3  # none after the last attempt
    assert all(0 <= w <= ceiling for w, ceiling in zip(waits, (0.5, 1.0, 2.0), strict=True))
    assert max(waits) <= MAX_DELAY_S


@pytest.mark.parametrize("exc", [TimeoutError(), ConnectionResetError(), _Status(502)])
def test_network_failures_and_5xx_are_retried(exc):
    seen = []

    def call():
        seen.append(1)
        if len(seen) == 1:
            raise exc
        return "ok"

    assert with_retry(call, label="t", max_attempts=2, sleep=lambda s: None) == "ok"


@pytest.mark.parametrize(
    "exc", [_Status(400), _Status(403), KeyError("bug"), ValueError("bad json")]
)
def test_anything_else_fails_at_once(exc):
    seen = []

    def call():
        seen.append(1)
        raise exc

    with pytest.raises(ProviderError) as err:
        with_retry(call, label="t", max_attempts=3, sleep=lambda s: None)
    assert not isinstance(err.value, ProviderExhausted) and len(seen) == 1


def test_a_certificate_failure_is_not_retried_and_408_is():
    wrapped = urllib.error.URLError(ssl.SSLCertVerificationError("bad certificate"))
    assert not transient(wrapped)
    assert transient(_Status(408))
    assert transient(urllib.error.URLError(ssl.SSLEOFError("peer closed")))  # a dropped connection


def test_a_malformed_gemini_function_call_is_a_provider_error():
    wire = GeminiWire()
    try:
        fx = wire.scenario("text")
        fx["body"]["candidates"][0]["finishReason"] = "MALFORMED_FUNCTION_CALL"
        with pytest.raises(ProviderError):
            wire.serve(fx).chat(**CALL)
    finally:
        wire.close()


def test_retry_after_is_honoured_up_to_the_cap():
    headers = Message()
    headers["Retry-After"] = "5"
    throttled = urllib.error.HTTPError("https://x.example", 429, "slow down", headers, None)
    calls, waits = iter([throttled, "ok"]), []

    def call():
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return item

    assert with_retry(call, label="t", max_attempts=2, sleep=waits.append) == "ok"
    assert waits == [5.0]


# --- why an answer ended ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, want",
    [
        ("max_tokens", "max_tokens"),
        ("length", "max_tokens"),
        ("MAX_TOKENS", "max_tokens"),
        ("model_context_window_exceeded", "max_tokens"),
        ("refusal", "refusal"),
        ("content_filter", "refusal"),
        ("guardrail_intervened", "refusal"),
        ("SAFETY", "refusal"),
        ("STOP", "end_turn"),
        (None, "end_turn"),
    ],
)
def test_every_providers_stop_reason_is_folded(raw, want):
    assert stop_reason(raw, []) == want


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
def test_a_cut_off_or_declined_answer_needs_a_person(cfg_dir, stop):
    rt, cfg = build(cfg_dir)
    rt.llm.chat = lambda *a, **k: Reply(model_id="m", stop_reason=stop)
    run = rt.handle("test-agent", "svc:test-agent", (cfg.inputs_dir / "create.txt").read_bytes())
    assert (run.state, run.reason_code) == (RunState.NEEDS_PERSON, f"llm_{stop}")


# --- openai_compat: tool_choice ignored (design 4.3) -----------------------------------------------


@pytest.fixture
def openai_wire():
    w = OpenAICompatWire()
    yield w
    w.close()


def _text(wire, content, usage=True):
    fx = wire.scenario("text")
    fx["body"]["choices"][0]["message"]["content"] = content
    if not usage:
        del fx["body"]["usage"]
    return fx


def test_a_server_ignoring_tool_choice_is_read_as_json_in_text(openai_wire):
    llm = openai_wire.serve(_text(openai_wire, 'Sure: {"total": "249.00"}'))
    reply = llm.chat(**CALL, output_schema=SCHEMA)
    assert reply.tool_calls == [ToolCall(name=ANSWER_TOOL, input={"total": "249.00"})]
    sent = openai_wire.requests[0]
    assert (
        json.dumps(SCHEMA, sort_keys=True) in sent["messages"][0]["content"]
    )  # schema in the prompt
    assert len(openai_wire.requests) == 1


def test_no_json_in_text_asks_once_more_and_charges_both(openai_wire):
    llm = openai_wire.serve(_text(openai_wire, "no idea"), _text(openai_wire, "still none"))
    reply = llm.chat(**CALL, output_schema=SCHEMA)
    assert len(openai_wire.requests) == 2 and reply.tool_calls == []
    assert (reply.input_tokens, reply.output_tokens) == (600, 14)


@pytest.mark.parametrize("finish", ["length", "content_filter"])
def test_a_cut_off_or_refused_answer_is_not_asked_again(openai_wire, finish):
    fx = _text(openai_wire, "partial")
    fx["body"]["choices"][0]["finish_reason"] = finish
    reply = openai_wire.serve(fx, _text(openai_wire, '{"total": "1"}')).chat(
        **CALL, output_schema=SCHEMA
    )
    assert len(openai_wire.requests) == 1 and reply.tool_calls == []


def test_a_loopback_model_is_reached_without_a_proxy():
    from hadavin_sdk.llm import common

    # An empty ProxyHandler replaces the environment one and registers no proxy route at all.
    assert not any(isinstance(h, ProxyHandler) for h in common._LOCAL_OPENER.handlers)


def test_reasoning_models_get_max_completion_tokens(openai_wire):
    settings = OpenAICompatSettings(
        kind="openai_compat", base_url="http://localhost:1/v1", max_completion_tokens=True
    )
    llm = make("llm", settings, routes=ROUTES)
    llm.url = openai_wire.replay.url + "/v1/chat/completions"
    openai_wire.replay.queue.append(openai_wire.scenario("text"))
    llm.chat(**CALL)
    sent = openai_wire.requests[0]
    assert (
        sent["max_completion_tokens"] == ROUTES["default"].max_tokens and "max_tokens" not in sent
    )


# --- keys: read per call, sent only where configured ------------------------------------------------


def test_a_rotated_key_is_used_without_a_restart():
    keys, wire = [KEY], GeminiWire()
    try:
        from hadavin_sdk.llm.gemini import GeminiLLM

        llm = GeminiLLM(lambda: keys[-1], ROUTES, 5.0, 1)
        llm.base_url = wire.replay.url
        wire.replay.queue += [wire.scenario("text"), wire.scenario("text")]
        llm.chat(**CALL)
        keys.append(KEY + "-rotated")
        llm.chat(**CALL)
        sent = [r["headers"]["x-goog-api-key"] for r in wire.replay.requests]
        assert sent == [KEY, KEY + "-rotated"]
    finally:
        wire.close()


def test_gemini_thinking_tokens_are_charged_as_output():
    wire = GeminiWire()
    try:
        fx = wire.scenario("text")
        fx["body"]["usageMetadata"]["thoughtsTokenCount"] = 93
        reply = wire.serve(fx).chat(**CALL)
        assert reply.output_tokens == 7 + 93
    finally:
        wire.close()


@pytest.mark.parametrize(
    "platform, suffix",
    [
        ("api", "/v1/messages"),
        ("vertex", "/publishers/anthropic/models/contract.model-1:1:rawPredict"),
        ("foundry", "/anthropic/v1/messages"),
    ],
)
def test_each_anthropic_platform_calls_its_own_path_with_its_key(platform, suffix):
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    wire = AnthropicWire(platform)
    try:
        wire.serve(wire.scenario("text")).chat(**CALL)
        sent = wire.replay.requests[0]
        assert sent["path"].split("?")[0].endswith(suffix)
        assert any(KEY in v for v in sent["headers"].values())  # the SDK picks the header name
    finally:
        wire.close()


def test_a_foundry_resource_in_the_environment_is_a_config_error(monkeypatch):
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_RESOURCE", "elsewhere")
    settings = AnthropicSettings(
        kind="anthropic",
        platform="foundry",
        resource="acme",
        api_key_secret_name="a",  # noqa: S106 - a name
    )
    with pytest.raises(ConfigError, match="foundry"):
        make("llm", settings, FakeSecretProvider({"a": KEY}), routes=ROUTES)


# --- the endpoint and the identity come from the configuration, never from the environment ----------

_PLATFORMS = {
    "api": {"api_key_secret_name": "a"},
    "vertex": {"project_id": "p-1", "region": "global"},
    "foundry": {"api_key_secret_name": "a", "resource": "acme"},
}
_API_REFUSED = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_PROFILE",
    "ANTHROPIC_CONFIG_DIR",
    "ANTHROPIC_IDENTITY_TOKEN",
    "ANTHROPIC_IDENTITY_TOKEN_FILE",
    "ANTHROPIC_FEDERATION_RULE_ID",
    "ANTHROPIC_ORGANIZATION_ID",
    "ANTHROPIC_SERVICE_ACCOUNT_ID",
    "ANTHROPIC_WORKSPACE_ID",
    "ANTHROPIC_SCOPE",
]
_FOUNDRY_REFUSED = [
    *_API_REFUSED,
    "ANTHROPIC_FOUNDRY_API_KEY",
    "ANTHROPIC_FOUNDRY_RESOURCE",
    "ANTHROPIC_FOUNDRY_BASE_URL",
]
_VERTEX_REFUSED = [
    "ANTHROPIC_VERTEX_BASE_URL",
    "ANTHROPIC_VERTEX_PROJECT_ID",
    "CLOUD_ML_REGION",
    "ANTHROPIC_CUSTOM_HEADERS",
]
# Written out here, not read from the table in llm/anthropic.py: an entry dropped from the table fails a case.
REFUSED = [
    *(("api", n) for n in _API_REFUSED),
    *(("foundry", n) for n in _FOUNDRY_REFUSED),
    *(("vertex", n) for n in _VERTEX_REFUSED),
]
# Names in the SDK's source that are no endpoint or identity of the three clients we build, with the reason.
_NOT_OURS = {
    "ANTHROPIC_API_VERSION": "a constant in the SDK, not an environment variable",
    "ANTHROPIC_WEBHOOK_SIGNING_KEY": "checks webhooks we do not receive; sent nowhere",
    "ANTHROPIC_OPEN_TELEMETRY": "tracing: only the value false is read, and it turns spans off",
    "ANTHROPIC_OPEN_TELEMETRY_PROPAGATION": "tracing: only false is read, and it stops the trace header",
    "ANTHROPIC_OPEN_TELEMETRY_TRACES_MAX_CONTENT_BYTES": "tracing: a size cap, no content without content mode",
    "DEFER_PYDANTIC_BUILD": "model build timing",
    "APPDATA": "where a profile file is looked for; ANTHROPIC_PROFILE and ANTHROPIC_CONFIG_DIR are refused",
    **dict.fromkeys(
        [
            "ANTHROPIC_AWS_API_KEY",
            "ANTHROPIC_AWS_BASE_URL",
            "ANTHROPIC_AWS_WORKSPACE_ID",
            "ANTHROPIC_BEDROCK_BASE_URL",
            "ANTHROPIC_BEDROCK_MANTLE_BASE_URL",
            "AWS_BEARER_TOKEN_BEDROCK",
            "AWS_DEFAULT_REGION",
            "AWS_REGION",
            "ANTHROPIC_GOOGLE_CLOUD_BASE_URL",
            "ANTHROPIC_GOOGLE_CLOUD_LOCATION",
            "ANTHROPIC_GOOGLE_CLOUD_PROJECT",
            "ANTHROPIC_GOOGLE_CLOUD_WORKSPACE_ID",
            "GOOGLE_CLOUD_PROJECT",
            "ANTHROPIC_ENVIRONMENT_ID",
            "ANTHROPIC_ENVIRONMENT_KEY",
            "ANTHROPIC_SESSION_ID",
            "ANTHROPIC_WORK_ID",
            "ANTHROPIC_WORK_SECRET",
        ],
        "read only by SDK clients llm/anthropic.py never builds (AWS, Bedrock, Google Cloud, environments)",
    ),
}
# Variables that make the SDK write request or response content to logs or traces: refused on every platform.
CONTENT_REFUSED = ["ANTHROPIC_LOG", "ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE"]
_STRAY = "x-stray: stray-marker"  # reads as a header line, and shows in a URL, key or project if one is taken


@pytest.fixture
def no_endpoint_env(monkeypatch):
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    for name in [*(n for _, n in REFUSED), *CONTENT_REFUSED]:
        monkeypatch.delenv(name, raising=False)


def _anthropic_llm(platform):
    settings = AnthropicSettings(kind="anthropic", platform=platform, **_PLATFORMS[platform])
    return make("llm", settings, FakeSecretProvider({"a": KEY}), routes=ROUTES)


def _reached(client):
    """Everything about a built client that says where it sends and as whom."""
    names = ("base_url", "default_headers", "_custom_headers", "auth_headers")
    names += ("api_key", "auth_token", "credentials", "project_id", "region")
    return " ".join(repr(getattr(client, n, None)) for n in names)


def test_the_refused_list_is_the_table():
    mod = pytest.importorskip("hadavin_sdk.llm.anthropic", reason="needs extra anthropic")
    table = sorted((p, n) for p, names in mod.ENDPOINT_ENV.items() for n in names)
    assert table == sorted(REFUSED)
    assert sorted(mod.CONTENT_ENV) == sorted(CONTENT_REFUSED)


@pytest.mark.parametrize("platform, name", REFUSED)
@pytest.mark.parametrize("value", [_STRAY, ""])
def test_an_endpoint_or_identity_variable_in_the_environment_is_refused(
    no_endpoint_env, monkeypatch, platform, name, value
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError) as refused:
        _anthropic_llm(platform)
    message = str(refused.value)
    assert (
        name in message and platform in message and "stray" not in message
    )  # the name, never the value


@pytest.mark.parametrize("platform", list(_PLATFORMS))
@pytest.mark.parametrize("name", CONTENT_REFUSED)
@pytest.mark.parametrize("value", ["debug", "content", "stray-off", ""])
def test_a_variable_that_puts_content_in_logs_or_traces_is_refused(
    no_endpoint_env, monkeypatch, platform, name, value
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError) as refused:
        _anthropic_llm(platform)
    message = str(refused.value)
    assert (
        name in message and platform in message and "stray" not in message
    )  # any value, never shown


@pytest.mark.parametrize(
    "platform, name",
    [
        ("api", "CLOUD_ML_REGION"),
        ("vertex", "ANTHROPIC_OPEN_TELEMETRY_TRACES_MAX_CONTENT_BYTES"),
        ("vertex", "ANTHROPIC_FOUNDRY_RESOURCE"),
        ("foundry", "ANTHROPIC_VERTEX_BASE_URL"),
        ("api", "HADAVIN_UNRELATED"),
    ],
)
def test_a_variable_the_platform_does_not_read_is_fine(
    no_endpoint_env, monkeypatch, platform, name
):
    monkeypatch.setenv(name, _STRAY)
    assert "stray" not in _reached(_anthropic_llm(platform)._client)


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_no_variable_outside_a_platforms_list_reaches_its_client(
    no_endpoint_env, monkeypatch, platform
):
    """Drift, by behaviour: the SDK began to read a variable on a platform whose list does not have it
    (2.9.0 did so with ANTHROPIC_CUSTOM_HEADERS on Vertex)."""
    listed = {n for p, n in REFUSED if p == platform}
    for name in sorted({n for _, n in REFUSED} - listed):
        with monkeypatch.context() as env:
            env.setenv(name, _STRAY)
            assert "stray" not in _reached(_anthropic_llm(platform)._client), (
                f"the anthropic SDK now uses {name} on platform {platform}: "
                "add it to ENDPOINT_ENV in src/hadavin_sdk/llm/anthropic.py and to REFUSED here"
            )


def test_the_sdk_names_no_variable_the_table_does_not_know():
    """Drift, by source: every ANTHROPIC_ name, and every name read from the environment, in the installed SDK."""
    anthropic = pytest.importorskip("anthropic", reason="needs extra anthropic")
    patterns = [
        r"\bANTHROPIC_[A-Z0-9_]*[A-Z0-9]\b",
        r"(?:environ(?:\.get)?|getenv)\s*[\(\[]\s*[\"'](\w+)[\"']",
        r"\bENV_\w+\s*=\s*[\"'](\w+)[\"']",  # a name held in a constant and read through it
    ]
    found = set()
    for path in Path(anthropic.__file__).parent.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for pattern in patterns:
            found.update(re.findall(pattern, source))
    assert len(found) > 20  # the scan found the SDK's source
    unknown = sorted(found - {n for _, n in REFUSED} - set(CONTENT_REFUSED) - set(_NOT_OURS))
    assert not unknown, (
        f"anthropic {anthropic.__version__} names {unknown}, unknown to ENDPOINT_ENV in "
        "src/hadavin_sdk/llm/anthropic.py: read what each does in the SDK, then add it to ENDPOINT_ENV and "
        "REFUSED (endpoint or identity of api, vertex or foundry), to CONTENT_ENV and CONTENT_REFUSED (a logging "
        "or tracing switch that can write request or response content), or to _NOT_OURS with the reason"
    )
