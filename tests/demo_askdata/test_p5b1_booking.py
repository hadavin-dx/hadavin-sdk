"""R20: a retry decision that crashes keeps the reservation booked.

The askdata pipeline books a call's worst case before the request and keeps it booked when the failure is a ``ProviderExhausted``
(``billed``), releasing it only for a plain ``ProviderError``. A crash inside ``with_retry``'s decision used to escape RAW
(on the base the reservation also stays booked, because nothing releases it). After the provider-error change the crash is a ``ProviderExhausted``, so
the pipeline books the worst case and returns an answer. Either way the meter must fall by EXACTLY the call's ``worst``.
Inputs (1) to (5) are the five ways a retry decision can crash.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from askdata import llm_io
from askdata.meter import worst_case_usd

from hadavin_sdk.llm.retry import with_retry
from tests.demo_askdata.kit import PROMPT, ROUTE, Kit
from tests.provider_wire_helpers import RAW_ESCAPES

Q = "How many orders are there"


def _boom(self):
    raise RuntimeError("hostile")


def _hostile(kind: str):
    base = {"status_code": property(_boom)}
    if kind == "reason-raises":
        base = {"reason": property(_boom)}
    if kind == "reason-eq-raises":

        class R(Exception):
            def __eq__(self, other):
                raise RuntimeError("eq")

            __hash__ = Exception.__hash__

        exc = type("Hostile", (Exception,), {})()
        exc.reason = R()
        return exc
    if kind == "hook-raises":
        return type("Hostile", (Exception,), {"status_code": 429})()
    if kind == "headers-raise":
        return type("Hostile", (Exception,), {"status_code": 429, "headers": property(_boom)})()
    return type("Hostile", (Exception,), base)()


class RetryingLLM:
    """A model whose ``chat`` runs the real ``with_retry`` (no-op sleep, 3 attempts) on a hostile error."""

    def __init__(self, kind: str) -> None:
        self.kind, self.calls = kind, 0

    def chat(self, *a, **kw):
        def call():
            self.calls += 1
            raise _hostile(self.kind)

        def hook(exc):
            raise RuntimeError("hook")

        extra = {"retryable": hook} if self.kind == "hook-raises" else {}
        return with_retry(call, label="fake", max_attempts=3, sleep=lambda s: None, **extra)


INPUTS = ["status_code-raises", "reason-raises", "reason-eq-raises", "hook-raises", "headers-raise"]


@pytest.mark.parametrize("kind", INPUTS)
def test_a_crashed_decision_keeps_exactly_the_worst_case_booked(tmp_path, kind):
    k = Kit(tmp_path)
    llm = RetryingLLM(kind)
    k.pipeline.llm = llm
    messages = llm_io.build_messages(PROMPT.text, Q, None, None)
    worst = worst_case_usd(ROUTE, len(llm_io.SYSTEM) + len(messages[0]["content"]))
    before = k.meter.remaining()
    escaped = None
    answer = None
    try:
        answer = k.pipeline.ask(Q)
    except RAW_ESCAPES as exc:  # on the base the crash escapes raw; the booking must still hold
        escaped = exc
    after = k.meter.remaining()
    assert before - after == worst, (before, after, worst)
    assert llm.calls == 1  # a crashed decision sends no further request
    if escaped is None:
        assert (answer.reason, answer.outcome) == ("model_unavailable", "failed")
        assert Decimal(answer.line.cost_usd) == worst
