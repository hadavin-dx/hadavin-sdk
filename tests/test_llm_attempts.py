"""`Reply.attempts` / `ProviderError.attempts`: how many requests a kind sent for one reply. A meter needs it,
because only the answered request reports usage (the class: spend recorded from the last attempt only)."""

from __future__ import annotations

import pytest

from hadavin_sdk.config import Route
from hadavin_sdk.llm.common import Answer, NetworkLLM, reply
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.llm.retry import with_retry

ROUTE = Route(model_id="m", input_usd_per_mtok="1", output_usd_per_mtok="1", max_tokens=10)


class Flaky(NetworkLLM):
    label = "flaky"
    retryable = staticmethod(lambda exc: isinstance(exc, ConnectionError))

    def __init__(self, failures: int, max_attempts: int = 3, fatal: bool = False) -> None:
        super().__init__({"r": ROUTE}, max_attempts, sleep=lambda _s: None)
        self.failures, self.fatal, self.calls = failures, fatal, 0

    def _chat(self, route, system, turns, specs, forced, output_schema):
        def once() -> Answer:
            self.calls += 1
            if self.calls <= self.failures:
                raise ValueError("bad request") if self.fatal else ConnectionError("reset")
            return Answer(text="ok", calls=[], tokens=(5, 5), stop="end_turn")

        got = self._retry(once)
        return reply(route, **vars(got), started=0.0, sent="x")


def test_a_reply_after_two_transient_failures_says_three_requests_were_sent():
    r = Flaky(failures=2).chat([{"role": "user", "content": "q"}], system="s", route="r")
    assert r.attempts == 3


def test_a_clean_reply_says_one():
    assert (
        Flaky(failures=0).chat([{"role": "user", "content": "q"}], system="s", route="r").attempts
        == 1
    )


def test_exhaustion_and_refusal_carry_the_count():
    with pytest.raises(ProviderExhausted) as spent:
        Flaky(failures=9).chat([{"role": "user", "content": "q"}], system="s", route="r")
    assert spent.value.attempts == 3
    with pytest.raises(ProviderError) as refused:
        Flaky(failures=1, fatal=True).chat(
            [{"role": "user", "content": "q"}], system="s", route="r"
        )
    assert refused.value.attempts == 1 and not isinstance(refused.value, ProviderExhausted)


def test_with_retry_marks_a_refusal_on_a_later_attempt():
    calls = iter([ConnectionError("x"), ConnectionError("y"), ValueError("no")])

    def call():
        raise next(calls)

    with pytest.raises(ProviderError) as err:
        with_retry(
            call,
            label="k",
            max_attempts=5,
            sleep=lambda _s: None,
            retryable=lambda e: isinstance(e, ConnectionError),
        )
    assert err.value.attempts == 3
