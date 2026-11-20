"""Pins for mutants of llm/retry.py (the mark), limits.py (`Budget`) and runtime/tick.py that the existing tests
let survive (mutation check by a different agent than the builder). Each test names the mutant it kills."""

from decimal import Decimal

import pytest

from hadavin_sdk.limits import Budget, SpendRefused
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.llm.retry import never_sent, with_retry


class _Status(Exception):
    def __init__(self, code):
        super().__init__(f"status {code}")
        self.status_code = code


def _caused_by_refusal(code):
    """An SDK error that carries an HTTP status and was caused by a refused connection."""
    exc = _Status(code)
    exc.__cause__ = ConnectionRefusedError(111, "refused")
    return exc


def _raises(exc, attempts):
    def call():
        raise exc

    with pytest.raises(ProviderError) as caught:
        with_retry(call, label="t", max_attempts=attempts, sleep=lambda _s: None)
    return caught.value


@pytest.mark.parametrize("code", [429, 500, 503])
def test_never_sent_is_false_when_anything_in_the_chain_carries_a_status(code):
    # mutant: never_sent stops treating "carries an HTTP status" as proof that a response came
    assert never_sent(_caused_by_refusal(code)) is False


def test_a_status_answer_over_a_refused_connection_is_not_marked_when_retries_run_out():
    # mutant: never_sent ignores statuses -> a 500 that wraps a refusal would be marked "never answered"
    error = _raises(_caused_by_refusal(500), attempts=2)
    assert type(error) is ProviderExhausted
    assert error.refused_before_response is False


def test_a_status_answer_over_a_refused_connection_is_not_marked_when_not_retried():
    # a 409 is not retried and is not on the refused list; with a refusal in its chain it still counts as answered
    error = _raises(_caused_by_refusal(409), attempts=3)
    assert type(error) is ProviderError
    assert error.refused_before_response is False


def test_budget_accepts_a_booking_that_exactly_reaches_the_cap():
    # mutant: `spent + worst > limit` -> `>=`
    budget = Budget(Decimal("1.00"))
    budget.reserve("a", Decimal("0.60"))
    budget.reserve("a", Decimal("0.40"))
    assert budget.spent == Decimal("1.00")
    with pytest.raises(SpendRefused) as caught:
        budget.reserve("a", Decimal("0.000001"))
    assert caught.value.reason == "usd_cap"


def test_budget_refuses_a_reserve_for_a_run_closed_by_forfeit_even_with_room_left():
    # mutant: the `run_id in self._closed` test is dropped
    budget = Budget(Decimal(100))
    budget.reserve("a", Decimal(1), run_id="run-1")
    budget.forfeit("run-1")
    with pytest.raises(SpendRefused) as caught:
        budget.reserve("a", Decimal(1), run_id="run-1")
    assert caught.value.reason == "usd_cap"
    budget.reserve("a", Decimal(1), run_id="run-2")  # another run is not touched
    budget.reserve("a", Decimal(1))  # a hold with no run id is never closed


def test_budget_late_settle_after_forfeit_can_only_raise_the_booking():
    # mutant: the forfeited branch books `actual` even when it is below what stayed booked
    budget = Budget(Decimal(100))
    rid = budget.reserve("a", Decimal(5), run_id="run-1")
    budget.forfeit("run-1")
    assert budget.settle(rid, Decimal(1), agent_id="a") == Decimal(0)
    assert budget.spent == Decimal(5)  # the worst case stays
    rid2 = budget.reserve("a", Decimal(5), run_id="run-2")
    budget.forfeit("run-2")
    assert budget.settle(rid2, Decimal(7), agent_id="a") == Decimal(2)
    assert budget.spent == Decimal(12)
