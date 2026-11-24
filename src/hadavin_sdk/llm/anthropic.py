"""Claude through the ``anthropic`` SDK, on the Claude API, Google Vertex AI or Azure AI Foundry (``platform``).

Ports WARDEN ``AnthropicProvider`` (design 4.3): SDK retries off (``llm/retry.py`` decides), a socket timeout
(``call_timeout_s``, per socket operation, not a wall clock), an explicit base URL on every platform, the key read
on every call (a rotated key is picked up), and ``output_schema`` forced through one tool.
Needs ``hadavin-sdk[anthropic]``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable
from typing import Any

import anthropic  # the extra: a missing install fails at start-up with the hint (backends.make)

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm.common import Answer, NetworkLLM, pinned, reply
from hadavin_sdk.models import Reply, ToolCall

API_BASE_URL = "https://api.anthropic.com"

# Loggers that can carry a request body, a header value or a credential at DEBUG, held at WARNING whatever the
# host's root level or ANTHROPIC_LOG says (read in the installed sources on 2026-11-24):
#   anthropic     the SDK logs "Request options", body included (_base_client.py:598-613 in 2.1.0, :603-617 in
#                 2.9.0); every SDK logger is a child of this one, and none has a level of its own
#   httpcore2     the HTTP library logs the response's header values (httpcore2 2.16.2 _sync/http11.py:90-103)
#   google.auth   the Vertex token request is logged with its body and headers (google-auth 2.62.0
#                 _helpers.py:410-443, called from transport/requests.py:272)
# httpx2 logs only the request line (method, URL, status) and is left alone.
QUIET_LOGGERS = ("anthropic", "httpcore2", "google.auth")

# Environment variables that reach the client whatever arguments we pass, refused on every platform:
# ANTHROPIC_CUSTOM_HEADERS adds its headers to every request of the API and Foundry clients (_client.py:250 in
# 2.1.0 and 2.9.0) and of the Vertex client from SDK 2.7.0 (lib/_env.py:9 in 2.9.0), and is read again on every
# call. Read in the installed sources of anthropic 2.1.0, 2.4.0 and 2.9.0 on 2026-11-24.
REFUSED_ENV = ("ANTHROPIC_CUSTOM_HEADERS",)

# Second net behind QUIET_LOGGERS and the explicit tracing option: variables that make the SDK write request or
# response content to the process log or to trace spans. Any set value is refused, harmful or not (fail closed):
# ANTHROPIC_LOG=debug (_utils/_logs.py:17-18) and ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE=content
# (_tracing.py:111 in 2.1.0, :205 in 2.9.0).
CONTENT_ENV = ("ANTHROPIC_LOG", "ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE")

# Environment variables the SDK reads for a client's endpoint or identity and that MUST NOT REACH THE CLIENT:
# every one loses to the argument we pass, in 2.1.0, 2.4.0 and 2.9.0. They are not refused (cloud run-times and
# other clients in the same process set them); tests/test_p5_llm.py sets each to a marker on each platform, makes
# one call and fails if the request differs from the configured one, which is what stops an SDK upgrade that
# changes the precedence. The SDK itself refuses ANTHROPIC_FOUNDRY_RESOURCE beside a base URL before 2.7.0.
_API_ENV = (
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
)
IGNORED_ENV: dict[str, tuple[str, ...]] = {
    "api": _API_ENV,
    "foundry": (  # the Foundry client is a subclass of the API client and runs its constructor too
        *_API_ENV,
        "ANTHROPIC_FOUNDRY_API_KEY",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_FOUNDRY_BASE_URL",
    ),
    "vertex": ("ANTHROPIC_VERTEX_BASE_URL", "ANTHROPIC_VERTEX_PROJECT_ID", "CLOUD_ML_REGION"),
}

# Given explicitly, so the SDK reads none of its tracing variables (_tracing.py:74-79 in 2.1.0, :168-173 in
# 2.9.0): spans, if the host has set tracing up, carry no request or response content.
_NO_CONTENT_TRACES = {"traces": {"content_mode": "metadata_only"}}


def _quiet() -> None:
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


_quiet()  # at import: the loggers are quiet before anything can be sent


def _guard() -> None:
    """Before a client is built and before every call (the SDK rebuilds its client, and re-reads the environment,
    on each call). Names only: a variable's value is never read."""
    _quiet()
    if stray := [name for name in (*REFUSED_ENV, *CONTENT_ENV) if name in os.environ]:
        raise ConfigError(
            f"backend llm 'anthropic': unset the environment variable(s) {', '.join(stray)}: they add headers "
            "to every request or write request and response content to logs or traces. The endpoint and the "
            "credential come from the configuration, except the host's proxy and certificate settings"
        )


def _vertex_base_url(region: str) -> str:
    """As the SDK derives it. Passed explicitly because, given none, the SDK reads ANTHROPIC_VERTEX_BASE_URL
    (and the API client ANTHROPIC_BASE_URL) and sends the credential wherever that names (WARDEN review)."""
    if region == "global":
        return "https://aiplatform.googleapis.com/v1"
    if region in ("us", "eu"):
        return f"https://aiplatform.{region}.rep.googleapis.com/v1"
    return f"https://{region}-aiplatform.googleapis.com/v1"


def client(settings: Any, key: str | None) -> Any:
    """The SDK client for ``settings.platform``, with every endpoint and credential argument given explicitly.

    What stays with the host by design: its proxy and certificate settings (HTTPS_PROXY, SSL_CERT_FILE and the
    like, as for every model client of this package), and on Vertex the identity: Google's application default
    credentials are chosen by the host environment (the file GOOGLE_APPLICATION_CREDENTIALS names, else the
    gcloud user's file, else the machine's metadata server), so whoever sets those variables chooses as whom the
    request is signed. The project, the region and the host it is sent to still come from the configuration.
    """
    _guard()
    if settings.platform not in IGNORED_ENV:
        raise ConfigError(f"backend llm 'anthropic': unknown platform {settings.platform!r}")
    common = {
        "timeout": settings.call_timeout_s,
        "max_retries": 0,
        "open_telemetry": _NO_CONTENT_TRACES,
    }
    try:
        if (
            settings.platform == "vertex"
        ):  # no key: the workload's Google identity (see the docstring)
            return anthropic.AnthropicVertex(
                region=settings.region,
                project_id=settings.project_id,
                base_url=_vertex_base_url(settings.region),
                **common,
            )
        if settings.platform == "foundry":
            return anthropic.AnthropicFoundry(
                api_key=key,
                base_url=f"https://{settings.resource}.services.ai.azure.com/anthropic/",
                **common,
            )
        return anthropic.Anthropic(api_key=key, base_url=API_BASE_URL, **common)
    except ValueError as exc:
        # Second net: the SDK's own refusals (before 2.7.0, ANTHROPIC_FOUNDRY_RESOURCE beside our base URL).
        raise ConfigError(f"backend llm 'anthropic' ({settings.platform}): {exc}") from exc


# Claude's moving aliases. Every Claude API id is a pinned snapshot (WARDEN, checked 2026-10-02), dated or not.
_ALIASES = re.compile(r"(?i)^(?:sonnet|opus|haiku|fable|default|best|opusplan)(?:\[1m\])?$")


def floating(model_id: str) -> bool:
    return bool(_ALIASES.match(model_id))


def retryable(exc: BaseException) -> bool | None:
    """The SDK's own network errors (a status error is decided by its `status_code`, generically)."""
    if isinstance(exc, anthropic.APIConnectionError):  # includes APITimeoutError
        return True
    try:  # Vertex refreshes a Google token through google-auth (installed with the vertex extra)
        from google.auth import exceptions as google_auth
    except ImportError:
        return None
    if isinstance(exc, google_auth.RefreshError):
        return False  # bad or missing credentials
    return True if isinstance(exc, google_auth.TransportError) else None


def make(settings: Any, deps: Any) -> AnthropicLLM:
    name = settings.api_key_secret_name if settings.platform != "vertex" else None
    key = (lambda: deps.resolve(name)) if name else None
    return AnthropicLLM(
        client(settings, key() if key else None),
        pinned(dict(deps.routes), floating),
        settings.max_attempts,
        key=key,
    )


class AnthropicLLM(NetworkLLM):
    label = "anthropic"
    retryable = staticmethod(retryable)

    def __init__(
        self,
        client: Any,
        routes: dict[str, Any],
        max_attempts: int,
        sleep: Callable[[float], None] = time.sleep,
        key: Callable[[], str] | None = None,
    ) -> None:
        super().__init__(routes, max_attempts, sleep)
        self._client, self._key = client, key

    def _chat(self, route, system, turns, specs, forced, output_schema) -> Reply:
        request: dict[str, Any] = {
            "model": route.model_id,
            "max_tokens": route.max_tokens,
            "messages": [
                {"role": role, "content": [{"type": "text", "text": t} for t in texts]}
                for role, texts in turns
            ],
        }
        if system:
            request["system"] = system
        if specs:
            request["tools"] = specs
        if forced:
            request["tool_choice"] = {"type": "tool", "name": forced}
        _guard()
        started = time.monotonic()
        got = self._retry(lambda: self._parse(self._current().messages.create(**request)))
        return reply(
            route,
            **vars(got),
            started=started,
            sent=system + json.dumps(request["messages"]),
        )

    def _current(self) -> Any:
        """The client with today's key: the platform secret is read per call, so rotation needs no restart."""
        return self._client.with_options(api_key=self._key()) if self._key else self._client

    @staticmethod
    def _parse(resp: Any) -> Answer:
        # Thinking blocks are the model's working, never its answer: only text and tool calls are read.
        return Answer(
            text="".join(b.text for b in resp.content if b.type == "text"),
            calls=[
                ToolCall(name=b.name, input=b.input) for b in resp.content if b.type == "tool_use"
            ],
            tokens=(resp.usage.input_tokens, resp.usage.output_tokens),
            stop=resp.stop_reason,
        )
