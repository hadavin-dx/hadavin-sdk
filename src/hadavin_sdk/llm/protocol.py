"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from typing import Any, Protocol

from hadavin_sdk.models import Reply


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way."""

    attempts = 1  # requests sent before this was raised (`llm/retry.py` sets it); a meter must not assume 0
    answered = 0  # of those, requests that came back with an answer and so were billed
    billed_usd = 0  # what those answers cost (a Decimal when set; the kind prices them)


class UnusableAnswer(ProviderError):
    """The provider answered (HTTP 200) but the body could not be used. The request was billed, so a meter charges it."""


class ProviderExhausted(ProviderError):
    """The provider throttled or failed after its retries."""


class LLM(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str,
        route: str,
        tools: list[dict[str, Any]] | None = None,
        documents: list[bytes] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Reply: ...
