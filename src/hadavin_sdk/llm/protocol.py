"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from typing import Any, Protocol

from hadavin_sdk.models import Reply


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way."""


class ProviderExhausted(ProviderError):
    """The provider throttled or failed after its retries. The last attempt may have been processed (a read timeout
    after the request was sent, a 5xx after work), so the cost is UNKNOWN: a metered caller keeps the reserved worst
    case booked. Only ``ProviderError`` itself (a refused request: 4xx) and ``SpendLimitReached`` are known unbilled."""


class DeadlineExceeded(ProviderExhausted):
    """The call's wall-clock deadline passed with a request still running. That request may still complete and be
    billed, so its cost is UNKNOWN: a metered caller keeps the reserved worst case booked."""


class SpendLimitReached(ProviderError):
    """The provider's spend or quota cap is reached (for the Claude API: the monthly cap, a 429 with no
    ``retry-after``). Retrying fails until the cap resets, so it is never retried; callers map it to ``over_budget``."""


class QuotaReached(SpendLimitReached):
    """A per-period request or token QUOTA is used up (for example a Gemini per-day quota). It is not a money cap: the
    provider refused the request, nothing is billed, and the quota returns at its reset time."""


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
