"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from typing import Any, Protocol

from hadavin_sdk.models import Reply


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way.

    `refused_before_response` is the mark the model gate reads (`getattr(exc, "refused_before_response",
    False) is True`) to settle a spend reservation at 0. It is False unless `llm/retry.py` sets it on the
    instance: True only when it is certain that no response was produced and nothing was billed (see
    `REFUSED_STATUSES` and `never_sent` there). False means "unknown": the worst case stays booked."""

    refused_before_response: bool = False


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
