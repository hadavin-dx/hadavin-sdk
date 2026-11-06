"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from typing import Any, Protocol

from hadavin_sdk import defaults
from hadavin_sdk.models import Reply, Usage


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way."""


class ProviderExhausted(ProviderError):
    """The provider throttled or failed after its retries."""


# The reasons a provider's usage cannot be priced, and the only field names an error may carry. Closed lists: an error
# message is built only from these, never from a reply (a provider reply can quote a document).
USAGE_REASONS = ("absent", "invalid", "implausible_zero", "unpriced_class")
USAGE_FIELDS = (
    "usage",
    "input_tokens",
    "output_tokens",
    "cache_write_tokens",
    "cache_read_tokens",
    "service_tier",
    "speed",
)


class UsageMissing(ProviderError):
    """The provider answered (so it may have billed) but the cost cannot be known or priced: no usable count, a
    count that cannot be real, or a class this core does not price. Refuse; nothing is estimated and nothing is
    retried. Not `ProviderExhausted`. The message is fixed text built from closed names."""

    def __init__(self, reason: str, field: str = "") -> None:
        if reason not in USAGE_REASONS:
            raise ValueError("unknown usage reason")
        if field and field not in USAGE_FIELDS:
            raise ValueError("unknown usage field")
        self.reason = reason
        self.field = field
        super().__init__(
            f"usage missing: {reason} ({field})" if field else f"usage missing: {reason}"
        )

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (self.reason, self.field), self.__dict__)


class UnpricedUsage(UsageMissing):
    """A usage class (a cache count) or a pricing word this core does not price. Reason is always `unpriced_class`."""

    def __init__(self, field: str) -> None:
        super().__init__("unpriced_class", field)

    def __reduce__(self) -> tuple[Any, ...]:
        return (type(self), (self.field,), self.__dict__)


def checked_count(value: Any, field: str) -> int:
    """One provider count, or a typed refusal. `None` is absent; anything that is not a plain `int` (a `bool`, a
    float, a string), a negative, or a value above the cap is invalid. Exactly the cap is accepted."""
    if value is None:
        raise UsageMissing("absent", field)
    if type(value) is not int:
        raise UsageMissing("invalid", field)
    if value < 0:
        raise UsageMissing("invalid", field)
    if value > defaults.MAX_USAGE_TOKENS_PER_CLASS:
        raise UsageMissing("invalid", field)
    return value


def build_usage(
    input_tokens: Any,
    output_tokens: Any,
    *,
    cache_write_tokens: Any = None,
    cache_read_tokens: Any = None,
) -> Usage:
    """The one way a kind turns provider counts into a `Usage`. Input and output are required. A cache class a
    kind passes as `None` means the provider leaves that field out and counts 0; a present value is checked."""
    inp = checked_count(input_tokens, "input_tokens")
    out = checked_count(output_tokens, "output_tokens")
    cw = (
        0 if cache_write_tokens is None else checked_count(cache_write_tokens, "cache_write_tokens")
    )
    cr = 0 if cache_read_tokens is None else checked_count(cache_read_tokens, "cache_read_tokens")
    return Usage(inp, out, cw, cr)


def add_usage(a: Usage, b: Usage) -> Usage:
    """The sum of two calls' usage, refused (`invalid`, field named) if any class sum is above the cap."""
    sums = {
        "input_tokens": a.input_tokens + b.input_tokens,
        "output_tokens": a.output_tokens + b.output_tokens,
        "cache_write_tokens": a.cache_write_tokens + b.cache_write_tokens,
        "cache_read_tokens": a.cache_read_tokens + b.cache_read_tokens,
    }
    for name, total in sums.items():
        if total > defaults.MAX_USAGE_TOKENS_PER_CLASS:
            raise UsageMissing("invalid", name)
    return Usage(**sums)


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
