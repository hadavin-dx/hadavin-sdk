"""Claude through the ``anthropic`` SDK, on the Claude API, Google Vertex AI or Azure AI Foundry (``platform``).

Ports WARDEN ``AnthropicProvider`` (design 4.3): SDK retries off (``llm/retry.py`` decides), a socket timeout
(``call_timeout_s``, per socket operation, not a wall clock), an explicit base URL on every platform, the key read
on every call (a rotated key is picked up), and ``output_schema`` forced through one tool.
Needs ``hadavin-sdk[anthropic]``.
"""

from __future__ import annotations

import json
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


def _vertex_base_url(region: str) -> str:
    """As the SDK derives it. Passed explicitly because, given none, the SDK reads ANTHROPIC_VERTEX_BASE_URL
    (and the API client ANTHROPIC_BASE_URL) and sends the credential wherever that names (WARDEN review)."""
    if region == "global":
        return "https://aiplatform.googleapis.com/v1"
    if region in ("us", "eu"):
        return f"https://aiplatform.{region}.rep.googleapis.com/v1"
    return f"https://{region}-aiplatform.googleapis.com/v1"


# Every environment variable the anthropic SDK reads for a client's endpoint or identity, per platform. The SDK's
# rule for "our argument or the variable" moved between releases (2.9.0 stopped refusing ANTHROPIC_FOUNDRY_RESOURCE
# beside a base URL and began to send ANTHROPIC_CUSTOM_HEADERS on Vertex), so the refusal is ours, not the SDK's.
# Read from the installed source of anthropic 2.1.0, 2.4.0 and 2.9.0 on 2026-11-24: _client.py,
# lib/credentials/_constants.py, lib/foundry.py, lib/vertex/_client.py, lib/_env.py. A newer SDK that reads a
# name missing here fails tests/test_p5_llm.py (the drift tests). Vertex identity is the workload's own Google
# identity (ADC, read by google-auth), which is the configured credential and is not listed.
_API_ENV = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_CUSTOM_HEADERS",  # sent on every request, in every version read
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
ENDPOINT_ENV: dict[str, tuple[str, ...]] = {
    "api": _API_ENV,
    "foundry": (  # the Foundry client is a subclass of the API client and runs its constructor too
        *_API_ENV,
        "ANTHROPIC_FOUNDRY_API_KEY",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_FOUNDRY_BASE_URL",
    ),
    "vertex": (
        "ANTHROPIC_VERTEX_BASE_URL",
        "ANTHROPIC_VERTEX_PROJECT_ID",
        "CLOUD_ML_REGION",
        "ANTHROPIC_CUSTOM_HEADERS",  # read on Vertex from 2.9.0
    ),
}

# Environment variables that make the anthropic SDK write request or response content (what a client sent, what
# the model answered) to the process log or to trace spans, on every platform. Any set value is refused, harmful
# or not (fail closed): ANTHROPIC_LOG=debug logs each request's options, body included (_utils/_logs.py:17-18 and
# _base_client.py:600 in 2.1.0, :605 in 2.9.0); ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE=content adds the
# content to spans (_tracing.py:111 in 2.1.0, :205 in 2.9.0). Read from the installed source on 2026-11-24.
CONTENT_ENV = ("ANTHROPIC_LOG", "ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE")


def client(settings: Any, key: str | None) -> Any:
    # Set at all is refused, whatever the value: the name is reported, the value is never read.
    if stray := [name for name in ENDPOINT_ENV[settings.platform] if name in os.environ]:
        raise ConfigError(
            f"backend llm 'anthropic' ({settings.platform}): unset the environment variable(s) "
            f"{', '.join(stray)}: the endpoint and the credential come from the configuration only"
        )
    if stray := [name for name in CONTENT_ENV if name in os.environ]:
        raise ConfigError(
            f"backend llm 'anthropic' ({settings.platform}): unset the environment variable(s) "
            f"{', '.join(stray)}: they can make the SDK write request or response content to logs or traces"
        )
    common = {"timeout": settings.call_timeout_s, "max_retries": 0}
    try:
        if (
            settings.platform == "vertex"
        ):  # Google credentials from the workload's identity (ADC), no key
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
    except (
        ValueError
    ) as exc:  # second net: the SDK's own refusals (the first is ENDPOINT_ENV above)
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
