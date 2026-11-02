"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.models import Reply


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way.

    BILLING CONTRACT (one set of attributes, shared by every layer and by PR #43's ``UnusableAnswer``). A retry layer
    stamps the instance; a bare error keeps the class defaults, which mean "one request, refused":

    - ``attempts``   requests actually SENT before this was raised. 0 = provably nothing left this process.
    - ``answered``   of those, requests the provider answered AND billed (HTTP 2xx, even if the body was unusable).
    - ``refused``    of those, requests the provider explicitly refused (HTTP 4xx incl. 429): not processed, not billed.
    - ``billed_usd`` what the ``answered`` ones cost (a ``Decimal``; 0 when the kind does not price them).

    ``attempts - answered - refused`` is the number of requests whose billing is UNKNOWN (a timeout or reset after the
    request was sent, a 5xx). A meter settles with ``cost_to_settle(exc, reserved)``: nothing unknown and nothing
    answered = release; something unknown = keep the whole reservation; something answered = book what it cost, and
    never zero."""

    attempts = 1
    answered = 0
    refused = 1
    billed_usd: Any = 0


class ProviderExhausted(ProviderError):
    """The provider throttled or failed after its retries. The last attempt may have been processed (a read timeout
    after the request was sent, a 5xx after work), so the cost is UNKNOWN: a metered caller keeps the reserved worst
    case booked, unless the retry layer proved nothing was sent or every request was refused (see ``ProviderError``)."""

    refused = 0


class DeadlineExceeded(ProviderExhausted):
    """The call's wall-clock deadline passed with a request still running. That request may still complete and be
    billed, so its cost is UNKNOWN: a metered caller keeps the reserved worst case booked."""


class SpendLimitReached(ProviderError):
    """The provider's spend or quota cap is reached (for the Claude API: the monthly cap, a 429 with no
    ``retry-after``). Retrying fails until the cap resets, so it is never retried; callers map it to ``over_budget``."""


def cost_to_settle(exc: BaseException, reserved: Decimal) -> Decimal:
    """What a meter should settle a reservation to after ``exc`` (see the billing contract on ``ProviderError``)."""
    attempts = int(getattr(exc, "attempts", 1))
    answered = int(getattr(exc, "answered", 0))
    refused = int(getattr(exc, "refused", 0))
    if attempts - answered - refused > 0:
        return reserved  # unknown: the call may have been billed, keep the worst case booked
    if answered > 0:
        try:
            billed = Decimal(getattr(exc, "billed_usd", 0))
        except (ArithmeticError, TypeError, ValueError):
            return reserved
        return (
            billed if billed.is_finite() and billed > 0 else reserved
        )  # never settle a billed answer at zero
    return Decimal(0)


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
