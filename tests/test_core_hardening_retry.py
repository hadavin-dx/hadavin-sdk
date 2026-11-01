"""G-05: the Claude monthly spend-cap 429 is never retried; other 429s are; a wall-clock deadline; breaker and
fallback. Body shape from platform.claude.com/docs/en/api/rate-limits (read 2026-11-01)."""

from __future__ import annotations

import pytest

from hadavin_sdk.llm.anthropic import spend_limit
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted, SpendLimitReached
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.models import Reply

CAP_BODY = {
    "type": "error",
    "error": {
        "type": "rate_limit_error",
        "message": "You have reached your API usage limits: your organization has crossed its monthly API usage"
        " threshold. You will regain access on 2026-09-01 at 00:00 UTC.",
        "details": {"error_code": "enforced_spend_limit_reached"},
    },
    "request_id": "req_x",
}
THROTTLE_BODY = {
    "type": "error",
    "error": {"type": "rate_limit_error", "message": "Number of requests exceeded"},
}


class StatusError(Exception):
    """What the SDK's status errors expose to llm/retry.py and to the kind: status_code, body, headers."""

    def __init__(self, status_code: int, body: dict | None, headers: dict | None = None) -> None:
        super().__init__(f"Error code: {status_code}")
        self.status_code, self.body, self.headers = status_code, body, headers or {}


def _err(body: dict, headers: dict | None = None) -> StatusError:
    return StatusError(
        429, body.get("error"), headers
    )  # the SDK unwraps the "error" object into .body


def _run(excs, **kw):
    calls = []

    def call():
        calls.append(1)
        if len(calls) <= len(excs):
            raise excs[len(calls) - 1]
        return "ok"

    waits: list[float] = []
    return (
        calls,
        waits,
        lambda: with_retry(call, label="t", max_attempts=4, sleep=waits.append, **kw),
    )


def test_spend_cap_429_is_one_attempt_and_typed():
    calls, _, go = _run([_err(CAP_BODY)] * 4, spend_limit=spend_limit)
    with pytest.raises(SpendLimitReached):
        go()
    assert len(calls) == 1


def test_spend_cap_detected_with_sdk_body_unwrapped_or_whole():
    assert spend_limit(_err(CAP_BODY))
    e = _err(CAP_BODY)
    e.body = CAP_BODY  # some SDK versions keep the whole JSON
    assert spend_limit(e)


def test_throttle_429_with_retry_after_is_retried_with_that_floor():
    calls, waits, go = _run([_err(THROTTLE_BODY, {"retry-after": "3"})], spend_limit=spend_limit)
    assert go() == "ok" and len(calls) == 2 and waits[0] >= 3


def test_throttle_429_without_retry_after_is_still_retried():
    # Docs: "Not every 429 carries it" (acceleration limits), so only the error code marks the spend cap.
    calls, _, go = _run([_err(THROTTLE_BODY)], spend_limit=spend_limit)
    assert go() == "ok" and len(calls) == 2


def test_other_error_code_is_not_a_spend_cap():
    body = {
        "error": {
            "type": "rate_limit_error",
            "message": "x",
            "details": {"error_code": "something_else"},
        }
    }
    assert not spend_limit(_err(body))


def test_non_429_is_not_a_spend_cap():
    assert not spend_limit(StatusError(500, CAP_BODY["error"]))


def test_deadline_stops_retrying():
    now = [0.0]
    calls: list[int] = []

    def call():
        calls.append(1)
        raise _err(THROTTLE_BODY, {"retry-after": "5"})

    def sleep(s):
        now[0] += s

    with pytest.raises(ProviderExhausted, match="deadline"):
        with_retry(
            call, label="t", max_attempts=4, sleep=sleep, deadline_s=6.0, clock=lambda: now[0]
        )
    assert len(calls) == 2  # one 5s sleep fits in 6s; a second would pass the deadline


class Stub:
    call_timeout_s = 7

    def __init__(self, *outcomes):
        self.outcomes, self.n = list(outcomes), 0

    def chat(self, *a, **k):
        self.n += 1
        o = self.outcomes[min(self.n, len(self.outcomes)) - 1]
        if isinstance(o, BaseException):
            raise o
        return o


OK = Reply(text="ok", model_id="m")


def test_breaker_opens_then_falls_back_then_probes():
    now = [0.0]
    primary = Stub(*[ProviderExhausted("down")] * 2, OK)
    backup = Stub(OK)
    llm = ResilientLLM(primary, backup, CircuitBreaker(2, 30.0, clock=lambda: now[0]))
    assert (
        llm.chat().text == "ok" and llm.chat().text == "ok"
    )  # two failures, both served by the fallback
    assert primary.n == 2
    llm.chat()
    assert primary.n == 2  # open: the primary is not called
    now[0] = 31
    llm.chat()
    assert primary.n == 3  # one probe, it succeeded
    llm.chat()
    assert primary.n == 4  # closed again
    assert llm.call_timeout_s == 7


def test_spend_limit_trips_and_without_fallback_raises_the_original():
    llm = ResilientLLM(Stub(SpendLimitReached("cap")), None, CircuitBreaker(1, 30.0))
    with pytest.raises(SpendLimitReached):
        llm.chat()
    with pytest.raises(ProviderExhausted, match="circuit open"):
        llm.chat()


def test_caller_error_neither_trips_nor_falls_back():
    primary = Stub(*[ProviderError("bad request")] * 5)
    llm = ResilientLLM(primary, Stub(OK), CircuitBreaker(1, 30.0))
    for _ in range(3):
        with pytest.raises(ProviderError):
            llm.chat()
    assert primary.n == 3
