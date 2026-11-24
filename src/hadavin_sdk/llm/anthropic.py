"""Claude through the ``anthropic`` SDK, on the Claude API, Google Vertex AI or Azure AI Foundry (``platform``).

Ports WARDEN ``AnthropicProvider`` (design 4.3): SDK retries off (``llm/retry.py`` decides), a socket timeout
(``call_timeout_s``, per socket operation, not a wall clock), an explicit base URL on every platform, the key read
on every call (a rotated key is picked up), and ``output_schema`` forced through one tool.
Needs ``hadavin-sdk[anthropic]``.

Three things this kind does to the whole process, for whoever runs it:

1. Before every attempt of every call it sets the loggers ``anthropic``, ``httpcore2`` and ``google.auth``, and
   every logger below them, to WARNING wherever a level below WARNING is set. DEBUG or INFO output of those three
   libraries cannot be switched on while this kind is in use, for other code in the process either.
2. With ``ANTHROPIC_LOG`` set to ``debug`` or ``info``, the HTTP client's logger (``httpx2``) writes one line
   per request: method, full URL, HTTP version, status. No key, header or body; on Vertex the URL holds the
   project id, the region and the model id, on Foundry the resource name.
3. Tracing by the SDK is fixed: spans carry no request or response content and the SDK adds no trace header to
   the request, so the host's trace context is not sent to the model provider. Neither can be changed by an
   environment variable.
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

# Loggers that can carry a request body, a header value or a credential at DEBUG, held at WARNING together with
# every logger below them, whatever level the host's root, the host's logging config or ANTHROPIC_LOG gives them
# (read in the installed sources on 2026-11-24). The logging is done by child loggers:
#   anthropic     anthropic._base_client (_base_client.py:133 in 2.1.0, :134 in 2.9.0) logs "Request options",
#                 body included (:598-613 in 2.1.0, :603-618 in 2.9.0); every SDK logger is below this name
#   httpcore2     httpcore2.http11 logs the response's header values (httpcore2 2.16.2 _sync/http11.py:27,
#                 :90-103); httpcore2.proxy and the other children are held with it
#   google.auth   google.auth.transport.requests logs the Vertex token request with its body and headers
#                 (google-auth 2.62.0 transport/requests.py:47, :272; _helpers.py:410-443)
# The google-auth lines are those of 2.62.0, the version in the lock; in 2.63.1 they are transport/requests.py
# :47, :286 and _helpers.py:410-434. httpx2 logs only the request line (method, URL, version, status) and is
# left alone.
QUIET_LOGGERS = ("anthropic", "httpcore2", "google.auth")

# Environment variables that reach the client whatever arguments we pass, refused on every platform:
# ANTHROPIC_CUSTOM_HEADERS adds its headers to every request of the API and Foundry clients (_client.py:250 in
# 2.1.0 and 2.9.0) and of the Vertex client from SDK 2.7.0 (lib/_env.py:9 in 2.9.0), and is read again on every
# call. Read in the installed sources of anthropic 2.1.0, 2.4.0 and 2.9.0 on 2026-11-24.
REFUSED_ENV = ("ANTHROPIC_CUSTOM_HEADERS",)

# Second net behind the explicit tracing option: the variable that makes the SDK add request and response
# content to trace spans (_tracing.py:111 in 2.1.0, :205 in 2.9.0). Any set value is refused (fail closed).
# ANTHROPIC_LOG is not refused. At import the SDK calls logging.basicConfig and sets the level of its own
# logger and of the HTTP client's, httpx2 (_utils/_logs.py:8-25). The guard undoes the first before every
# attempt; the second stays on (see the module docstring, point 2).
CONTENT_ENV = ("ANTHROPIC_OPEN_TELEMETRY_TRACES_CONTENT_MODE",)

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
# 2.9.0): spans, if the host has set tracing up, carry no request or response content, and the SDK adds no
# trace header to the request (propagation off: _base_client.py:1222, :1417-1419 in 2.1.0; :1227, :1239,
# :1428-1430 in 2.9.0). The host cannot change either by environment.
_NO_CONTENT_TRACES = {"propagation": False, "traces": {"content_mode": "metadata_only"}}


def _quiet() -> None:
    """No quiet logger, and no logger below one, logs under WARNING (a level a host sets on a child, such as
    anthropic._base_client, would win over the parent's). A level is written only where one below WARNING is
    set: a host that made a library stricter (ERROR) keeps that. Children made later are caught by the next
    run: this runs at import and before every attempt."""
    below = tuple(f"{name}." for name in QUIET_LOGGERS)
    # The manager's table, not Logger.getChildren: that one returns immediate children only (and needs Python
    # 3.12), and the loggers that log are deeper (google.auth.transport.requests).
    for name, logger in list(logging.root.manager.loggerDict.items()):
        if (
            name.startswith(below)
            and isinstance(logger, logging.Logger)
            and logging.NOTSET < logger.level < logging.WARNING
        ):
            logger.setLevel(logging.NOTSET)
    for name in QUIET_LOGGERS:
        if (logger := logging.getLogger(name)).level < logging.WARNING:
            logger.setLevel(logging.WARNING)


_quiet()  # at import: the loggers are quiet before anything can be sent


def _guard() -> None:
    """Before a client is built and before every attempt of every call (the SDK rebuilds its client, and re-reads
    the environment, on each one). Names only: a variable's value is never read."""
    _quiet()
    if stray := [name for name in (*REFUSED_ENV, *CONTENT_ENV) if name in os.environ]:
        raise ConfigError(
            f"backend llm 'anthropic': unset the environment variable(s) {', '.join(stray)}: they add headers "
            "to every request or write request and response content to traces. The endpoint, and on api and "
            "foundry the key, come from the configuration, except the host's proxy and certificate settings; "
            "on vertex the host's Google identity signs the request"
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
    gcloud user's file, else the machine's metadata server, which GCE_METADATA_HOST can point elsewhere), so
    whoever sets those variables chooses as whom the request is signed. The project, the region and the host it
    is sent to still come from the configuration.
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
        if settings.platform == "vertex":
            # No key: the workload's Google identity (see the docstring).
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


def detail(exc: BaseException) -> str:
    """The text of a ConfigError of this package raised inside an attempt, passed on in the ProviderError (today
    only the guard's refusal, which names variables and never values: keep any other ConfigError raised in an
    attempt free of values too). An SDK message is never passed on: it can quote the request."""
    return str(exc) if isinstance(exc, ConfigError) else ""


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
    detail = staticmethod(detail)

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
        """The client with today's key: the platform secret is read per call, so rotation needs no restart.
        Called inside every retried attempt. The key is fetched first, then the guard runs, then the copy is
        built and used: nothing the fetch does to a log level survives to the request. A refusal by the guard
        reaches the caller as ProviderError (not retried), the one class the run loops catch."""
        key = self._key() if self._key else None
        _guard()
        return self._client.with_options(api_key=key) if self._key else self._client

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
