"""Slice 2 P5: the llm kinds' wiring outside the contract suite (design 4.3, 12.10)."""

import json
import logging
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
from tests.fixtures.http_fake import fixture
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


def test_a_foundry_resource_in_the_environment_never_moves_the_request(monkeypatch):
    """Exactly two outcomes: the SDK refuses the variable beside our base URL (before 2.7.0), or it ignores the
    variable and the request goes to the configured resource (2.7.0 and later)."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_RESOURCE", "elsewhere")
    try:
        llm = _anthropic_llm("foundry")
    except ConfigError as refused:
        assert "foundry" in str(refused) and "resource" in str(refused)
        assert "elsewhere" not in str(refused)
    else:
        sent = _call(llm, "foundry")
        assert sent.url.host == "acme.services.ai.azure.com" and "elsewhere" not in str(sent.url)


# --- the endpoint and the identity come from the configuration, never from the environment ----------

_PLATFORMS = {
    "api": {"api_key_secret_name": "a"},
    "vertex": {"project_id": "p-1", "region": "global"},
    "foundry": {"api_key_secret_name": "a", "resource": "acme"},
}
_HOSTS = {
    "api": "api.anthropic.com",
    "vertex": "aiplatform.googleapis.com",
    "foundry": "acme.services.ai.azure.com",
}
# The three lists are written out here, not read from llm/anthropic.py: an entry dropped there fails a case.
# Refused at start and on every call, on every platform: they reach the client whatever we pass.
REFUSED = ["ANTHROPIC_CUSTOM_HEADERS"]
# Refused too (second net): they make the SDK write request or response content to logs or traces.
CONTENT_REFUSED = ["ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE"]
# Loggers held quiet, and for each the children that log a body, a header value or a token request.
QUIET = {
    "anthropic": ["anthropic._base_client"],
    "httpcore2": ["httpcore2.http11", "httpcore2.proxy"],
    "google.auth": ["google.auth.transport.requests"],
}
# Not refused, and must not reach the client: the SDK reads them, our arguments win.
_API_IGNORED = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
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
MUST_NOT_REACH = {
    "api": _API_IGNORED,
    "foundry": [
        *_API_IGNORED,
        "ANTHROPIC_FOUNDRY_API_KEY",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_FOUNDRY_BASE_URL",
    ],
    "vertex": ["ANTHROPIC_VERTEX_BASE_URL", "ANTHROPIC_VERTEX_PROJECT_ID", "CLOUD_ML_REGION"],
}
_IGNORED_NAMES = sorted({n for names in MUST_NOT_REACH.values() for n in names})
# Names in the SDK's source that are no endpoint or identity of the three clients we build, with the reason.
_NOT_OURS = {
    "ANTHROPIC_API_VERSION": "a constant in the SDK, not an environment variable",
    "ANTHROPIC_WEBHOOK_SIGNING_KEY": "checks webhooks we do not receive; sent nowhere",
    "DEFER_PYDANTIC_BUILD": "model build timing",
    "ANTHROPIC_LOG": "the SDK log switch: not refused, the loggers it turns on are held quiet (tested)",
    "APPDATA": "where a profile file is looked for; a profile is never used when a credential is passed",
    **dict.fromkeys(
        [
            "ANTHROPIC_OPEN_TELEMETRY",
            "ANTHROPIC_OPEN_TELEMETRY_PROPAGATION",
            "ANTHROPIC_OPEN_TELEMETRY_TRACES_MAX_CONTENT_BYTES",
        ],
        "tracing: not read at all, because llm/anthropic.py passes the tracing option explicitly",
    ),
    **dict.fromkeys(
        ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR"],
        "the host's proxy and certificate settings stay the host's, as for every model client of this "
        "package (guard/http.py); read by the HTTP library, not by the SDK",
    ),
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
_STRAY = "x-stray: stray-marker"  # a well-formed header line, for the headers variable


def _marker(name):
    """A well-formed value for the kind of variable: a URL for a base URL, a plain word otherwise."""
    return "https://stray-marker.example/" if name.endswith("BASE_URL") else "stray-marker"


_BASELINE: dict[str, tuple] = {}


def _anthropic_llm(platform):
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    settings = AnthropicSettings(kind="anthropic", platform=platform, **_PLATFORMS[platform])
    return make("llm", settings, FakeSecretProvider({"a": KEY}), routes=ROUTES)


def _call(llm, platform, call=CALL, sent=None):
    """One call of an llm built by make(): the request the SDK would put on the wire is caught at the HTTP
    library's transport and answered from the recorded fixture, so the real, configured host is in it."""
    httpx2 = pytest.importorskip("httpx2", reason="needs extra anthropic")
    sent = [] if sent is None else sent

    def answer(request):
        sent.append(request)
        return httpx2.Response(200, json=fixture("anthropic", "text")["body"])

    http = httpx2.Client(transport=httpx2.MockTransport(answer))
    llm._client = llm._client.with_options(http_client=http)
    if platform == "vertex":
        llm._client.access_token = KEY  # the tests have no Google identity
    llm.chat(**call)
    return sent[0]


def _wire(request):
    """What decides where a request goes and as whom: URL, every header, body."""
    return str(request.url), sorted(request.headers.items()), request.content


def test_the_lists_are_the_tables():
    mod = pytest.importorskip("hadavin_sdk.llm.anthropic", reason="needs extra anthropic")
    assert sorted(mod.REFUSED_ENV) == sorted(REFUSED)
    assert sorted(mod.CONTENT_ENV) == sorted(CONTENT_REFUSED)
    assert sorted(mod.QUIET_LOGGERS) == sorted(QUIET)
    assert {p: sorted(n) for p, n in mod.IGNORED_ENV.items()} == {
        p: sorted(n) for p, n in MUST_NOT_REACH.items()
    }


@pytest.mark.parametrize("platform", list(_PLATFORMS))
@pytest.mark.parametrize("name", [*REFUSED, *CONTENT_REFUSED])
@pytest.mark.parametrize("value", [_STRAY, "debug", "content", ""])
def test_a_variable_that_reaches_the_client_or_the_logs_is_refused(
    monkeypatch, platform, name, value
):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError) as refused:
        _anthropic_llm(platform)
    assert name in str(refused.value) and "stray" not in str(
        refused.value
    )  # the name, never the value


def test_one_error_names_every_refused_variable_and_what_stays_with_the_host(monkeypatch):
    for name in [*REFUSED, *CONTENT_REFUSED]:
        monkeypatch.setenv(name, _STRAY)
    with pytest.raises(ConfigError) as refused:
        _anthropic_llm("api")
    message = str(refused.value)
    assert all(name in message for name in [*REFUSED, *CONTENT_REFUSED])
    assert "except the host's proxy and certificate settings" in message and "stray" not in message
    # No overclaim: on Vertex the credential is the host's Google identity, not a configured key.
    assert "credential come from the configuration" not in message and "on vertex" in message


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_a_headers_variable_set_after_start_is_refused_on_the_next_call(monkeypatch, platform):
    llm, sent = _anthropic_llm(platform), []
    _call(llm, platform, sent=sent)
    monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", _STRAY)
    with pytest.raises(ConfigError, match="ANTHROPIC_CUSTOM_HEADERS"):
        llm.chat(**CALL)
    assert len(sent) == 1  # the second call sent nothing


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_a_headers_variable_set_during_a_call_stops_the_next_attempt(monkeypatch, platform):
    """The check runs inside each retried attempt, not once before the retries."""
    httpx2 = pytest.importorskip("httpx2", reason="needs extra anthropic")
    llm, sent = _anthropic_llm(platform), []

    def drop(
        request,
    ):  # the first attempt fails in a retryable way, and the variable appears meanwhile
        sent.append(request)
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", _STRAY)
        raise httpx2.ConnectError("connection dropped", request=request)

    http = httpx2.Client(transport=httpx2.MockTransport(drop))
    llm._client = llm._client.with_options(http_client=http)
    if platform == "vertex":
        llm._client.access_token = KEY
    llm._sleep = lambda seconds: None
    assert llm.max_attempts > 1
    with pytest.raises((ConfigError, ProviderError), match="ANTHROPIC_CUSTOM_HEADERS") as refused:
        llm.chat(**CALL)
    assert len(sent) == 1 and "stray" not in str(refused.value)  # no second attempt was sent


def test_a_platform_without_a_table_row_is_a_config_error():
    mod = pytest.importorskip("hadavin_sdk.llm.anthropic", reason="needs extra anthropic")
    settings = AnthropicSettings(kind="anthropic", platform="api", **_PLATFORMS["api"])
    with pytest.raises(ConfigError, match="unknown platform"):
        mod.client(settings.model_copy(update={"platform": "elsewhere"}), KEY)


@pytest.mark.parametrize("platform", list(_PLATFORMS))
@pytest.mark.parametrize("name", [*_IGNORED_NAMES, "HADAVIN_UNRELATED"])
def test_a_variable_the_sdk_reads_never_reaches_the_request(monkeypatch, platform, name):
    """Drift, by behaviour: each endpoint or identity variable set to a marker, on each platform, and one call.
    The request is the configured one: same URL, same headers, same body as with a clean environment. An SDK
    upgrade that lets a variable win over our argument fails here."""
    if platform not in _BASELINE:
        _BASELINE[platform] = _wire(_call(_anthropic_llm(platform), platform))
    monkeypatch.setenv(name, _marker(name))
    try:
        llm = _anthropic_llm(platform)
    except ConfigError as refused:
        # The one refusal the SDK itself makes (before 2.7.0), mapped by llm/anthropic.py: nothing is sent.
        assert (platform, name) == ("foundry", "ANTHROPIC_FOUNDRY_RESOURCE")
        assert "stray" not in str(refused)
        return
    sent = _call(llm, platform)
    hint = f"the anthropic SDK now lets {name} change the {platform} request: see IGNORED_ENV in llm/anthropic.py"
    assert "stray" not in repr(_wire(sent)), hint
    assert _wire(sent) == _BASELINE[platform], hint
    assert sent.url.scheme == "https" and sent.url.host == _HOSTS[platform], hint
    assert any(KEY in value for value in sent.headers.values()), (
        hint
    )  # the SDK picks the header name


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_traces_carry_no_content_and_no_trace_header_whatever_the_environment_says(
    monkeypatch, platform
):
    """The tracing option is passed explicitly, so the SDK reads none of its tracing variables: no content in
    spans, and the host's trace context is not sent to the model provider. Our own refusal of the content-mode
    variable is switched off here to show the first net alone."""
    mod = pytest.importorskip("hadavin_sdk.llm.anthropic", reason="needs extra anthropic")
    monkeypatch.setattr(mod, "CONTENT_ENV", ())
    monkeypatch.setenv("ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE", "content")
    monkeypatch.setenv("ANTHROPIC_OPEN_TELEMETRY_PROPAGATION", "true")
    client = _anthropic_llm(platform)._client
    for built in (client, client.with_options(timeout=3.0)):  # a call uses such a copy
        assert built._open_telemetry["traces"]["content_mode"] == "metadata_only"
        assert built._open_telemetry["propagation"] is False


def _logged(caplog):
    return " ".join(r.getMessage() + repr(vars(r)) for r in caplog.records)


def _prompt_call(llm, platform):
    prompt = "prompt-marker-" + "7f3a"
    _call(llm, platform, call={**CALL, "messages": [{"role": "user", "content": prompt}]})
    return prompt


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_a_prompt_or_a_key_never_reaches_a_log_at_debug(caplog, platform):
    """A host that logs everything at DEBUG and, after start, sets the libraries' loggers to DEBUG too: the
    parents and the children that do the logging (the SDK logs bodies on anthropic._base_client)."""
    caplog.set_level(logging.DEBUG)  # the root logger
    llm = _anthropic_llm(platform)
    names = [*QUIET, *(child for children in QUIET.values() for child in children)]
    for name in names:
        logging.getLogger(name).setLevel(logging.DEBUG)
    prompt = _prompt_call(llm, platform)
    assert prompt not in _logged(caplog) and KEY not in _logged(caplog)
    assert all(logging.getLogger(n).getEffectiveLevel() >= logging.WARNING for n in names)


@pytest.mark.parametrize(
    "pinned, child", [(pinned, child) for pinned, children in QUIET.items() for child in children]
)
def test_a_debug_record_on_a_child_of_each_quiet_logger_is_dropped(pinned, child):
    """Per library, with the handler on the logger itself: a level a host sets on the child must not win."""
    mod = pytest.importorskip("hadavin_sdk.llm.anthropic", reason="needs extra anthropic")
    seen, logger = [], logging.getLogger(child)
    handler = logging.Handler(level=logging.DEBUG)
    handler.emit = seen.append
    logger.addHandler(handler)
    try:
        logger.setLevel(logging.DEBUG)
        logger.debug("a body, a header value or a token request")
        assert len(seen) == 1  # the control: without the guard the record is written
        mod._guard()
        logger.debug("a body, a header value or a token request")
        assert len(seen) == 1, f"{child} still logs at DEBUG: {pinned} must be in QUIET_LOGGERS"
    finally:
        logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)


@pytest.mark.parametrize("platform", list(_PLATFORMS))
def test_the_sdks_own_log_switch_puts_no_prompt_in_a_log(caplog, monkeypatch, platform):
    """ANTHROPIC_LOG=debug is not refused: what the SDK does with it at import is undone by the guard."""
    anthropic_logs = pytest.importorskip("anthropic._utils._logs", reason="needs extra anthropic")
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("ANTHROPIC_LOG", "debug")
    try:
        anthropic_logs.setup_logging()  # what importing the SDK does with the variable
        assert logging.getLogger("anthropic").level == logging.DEBUG  # the control
        llm = _anthropic_llm(platform)  # not refused
        prompt = _prompt_call(llm, platform)
        assert prompt not in _logged(caplog) and KEY not in _logged(caplog)
    finally:
        logging.getLogger("httpx2").setLevel(logging.NOTSET)


def test_the_sdk_names_no_variable_the_tables_do_not_know():
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
    listed = {*REFUSED, *CONTENT_REFUSED, *_IGNORED_NAMES}
    assert listed <= found, f"listed here but named nowhere in the SDK: {sorted(listed - found)}"
    unknown = sorted(found - listed - set(_NOT_OURS))
    assert not unknown, (
        f"anthropic {anthropic.__version__} names {unknown}, unknown to src/hadavin_sdk/llm/anthropic.py: read "
        "what each does in the SDK, then add it to REFUSED_ENV (reaches the client whatever we pass), to "
        "CONTENT_ENV (a tracing switch that can write request or response content), to IGNORED_ENV "
        "(an endpoint or identity name that loses to our argument) and to the same list here, or to _NOT_OURS "
        "with the reason"
    )
