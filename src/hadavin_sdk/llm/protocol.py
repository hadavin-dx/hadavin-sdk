"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.models import Reply

_LOG = logging.getLogger("hadavin_sdk.llm.protocol")


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
    never zero. The counts must be plain ints (0..10**6, ``answered + refused <= attempts``); anything else, or an
    attribute that raises, is UNKNOWN.
    - ``prior_unknown_requests`` (added in PR #48; default 0 keeps every existing raiser unchanged) failed PRIMARIES of
      unknown billing that a fallback layer saw before this error: one mark per failed primary, nested fallbacks add up.
      A SUCCESSFUL call carries the same count on ``Reply.prior_unknown_requests``. Both paths settle through one helper
      (``book_marks``): the call's own settlement PLUS one reservation per mark. A non-int or negative mark counts as 0
      (it never raises)."""

    attempts = 1
    answered = 0
    refused = 1
    billed_usd: Any = 0
    prior_unknown_requests: int = 0


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


def _counts(exc: BaseException) -> tuple[int, int, int]:
    """(attempts, answered, refused) as non-negative ints. Raises ValueError/TypeError/OverflowError on a garbage,
    negative or inconsistent set (answered + refused above attempts): callers keep the reservation."""
    # a property that raises propagates: every caller below catches Exception and treats it as unknown
    vals = [getattr(exc, n, d) for n, d in (("attempts", 1), ("answered", 0), ("refused", 0))]
    for v in vals:
        # a real count is a plain int: a bool, a float (1.5), a string, None or nan is garbage, never coerced
        if type(v) is not int or v < 0 or v > _MAX_COUNT:
            raise ValueError("garbage billing count")
    attempts, answered, refused = vals
    if answered + refused > attempts:
        raise ValueError("inconsistent billing counts")
    return attempts, answered, refused


_MAX_COUNT = 10**6


def counts_valid(exc: BaseException) -> bool:
    """True if ``attempts``/``answered``/``refused`` are a sane, consistent set (garbage counts as unknown)."""
    try:
        _counts(exc)
    except Exception:  # noqa: BLE001 - anything unreadable is unknown
        return False
    return True


def unknown_requests(exc: BaseException) -> int:
    """Requests whose billing is unknown (``attempts - answered - refused``); a garbage attribute counts as 1."""
    try:
        attempts, answered, refused = _counts(exc)
    except Exception:  # noqa: BLE001 - anything unreadable is unknown
        return 1
    return attempts - answered - refused


MAX_MARKS = 16  # a fallback chain is never deeper than this; a larger count is clamped (fail safe), not trusted


def prior_marks(obj: Any) -> int:
    """``prior_unknown_requests`` of an error, reply or verdict as a safe count: anything but a plain int is 0, a
    negative is 0, and a count above ``MAX_MARKS`` (a chain cannot be that deep) is clamped to it, so one bad number can
    never book a million reservations and lock an agent."""
    try:
        v = getattr(obj, "prior_unknown_requests", 0)
    except Exception:  # noqa: BLE001 - a property that raises counts as no mark, never an exception
        return 0
    return min(v, MAX_MARKS) if type(v) is int and v > 0 else 0


def book_marks(own: Decimal, reserved: Decimal, obj: Any) -> Decimal:
    """The ONE place marks are priced, for the error path and the reply path alike: ``own`` plus one reservation per
    mark of ``obj`` (``own`` alone when there is none)."""
    marks = prior_marks(obj)
    return own + reserved * marks if marks > 0 else own


def cost_to_settle(
    exc: BaseException, reserved: Decimal, *, agent: str = "", route: str = ""
) -> Decimal:
    """What a meter should settle a reservation to after ``exc`` (see the billing contract on ``ProviderError``).
    The error's own part never exceeds ``reserved`` (a provider-reported ``billed_usd`` above the worst case is a bad
    number, not a bill); each ``prior_unknown_requests`` mark adds one more reservation (``book_marks``). Never raises:
    anything it cannot read keeps the whole reservation (the fail-safe direction)."""
    marks = prior_marks(exc)  # first: a failure to read the counts below must not lose the marks
    try:
        own = _own_cost(exc, reserved, agent, route)
    except Exception:  # noqa: BLE001 - never raises: the reservation is kept
        own = reserved
    try:
        return own + reserved * marks
    except Exception:  # noqa: BLE001 - a reservation that is not a number: nothing more can be said
        return reserved


def _own_cost(exc: BaseException, reserved: Decimal, agent: str, route: str) -> Decimal:
    attempts, answered, refused = _counts(exc)
    if attempts - answered - refused > 0:
        return reserved  # unknown: the call may have been billed, keep the worst case booked
    if answered > 0:
        billed = Decimal(getattr(exc, "billed_usd", 0))
        if not billed.is_finite() or billed <= 0:
            return reserved  # never settle a billed answer at zero
        if billed > reserved:
            _LOG.warning(
                "billed_usd above the reservation: settling at the reservation (agent=%s route=%s)",
                agent,
                route,
            )
            return reserved
        return billed
    return Decimal(0)


def reply_cost_to_settle(reply: Any, reserved: Decimal) -> Decimal:
    """What a meter settles after a SUCCESSFUL call: the reply's own cost, plus (if a fallback served it after a primary
    whose billing is unknown) one reservation per failed primary (``book_marks``, shared with ``cost_to_settle``), so no
    bill is lost. Never raises on a bad mark count (it counts as 0)."""
    return book_marks(reply.cost_usd, reserved, reply)


class UnusableAnswer(ProviderError):
    """The provider answered (HTTP 2xx, billed) but the body was unusable (empty, cut off, not the asked shape). It was
    BILLED: ``answered = 1``, ``refused = 0``. ``billed_usd`` stays 0 (unpriced) unless the kind that raises it sets the real
    cost; an unpriced billed answer keeps the whole reservation (``cost_to_settle``). Defined here, not in a kind, so no
    layer can default it to "refused" and have a meter release a call that was paid for."""

    answered = 1
    refused = 0


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
