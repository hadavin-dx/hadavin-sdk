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


# ---- openai_compat asks again after an unusable round: one counter and the billed usage across both rounds
import io
import urllib.error
from decimal import Decimal
from unittest import mock

from hadavin_sdk.llm import openai_compat as oc
from hadavin_sdk.llm.protocol import UnusableAnswer

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}}}
PRICED = Route(
    model_id="gpt-x-1", input_usd_per_mtok="1", output_usd_per_mtok="10", max_tokens=1000
)


def _http(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(b"{}"))


def _text(txt="plain words", pt=1000, ct=1000):
    return {
        "choices": [{"message": {"content": txt}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": pt, "completion_tokens": ct},
    }


def _tool(pt=1000, ct=1000):
    call = {"function": {"name": "submit_answer", "arguments": '{"a":1}'}}
    return {
        "choices": [
            {"message": {"content": "", "tool_calls": [call]}, "finish_reason": "tool_calls"}
        ],
        "usage": {"prompt_tokens": pt, "completion_tokens": ct},
    }


def _oc_chat(seq, max_attempts=3, route=PRICED):
    llm = oc.OpenAICompatLLM(
        "https://api.example.com/v1",
        lambda: "k",
        {"sql_generate": route},
        30,
        max_attempts,
        sleep=lambda _s: None,
    )
    it = iter(seq)

    def post(url, body, headers, timeout):
        v = next(it)
        if isinstance(v, BaseException):
            raise v
        return v

    with mock.patch.object(oc, "post_json", side_effect=post):
        return llm, llm.chat(
            [{"role": "user", "content": "hi"}],
            system="s",
            route="sql_generate",
            output_schema=SCHEMA,
        )


BILLED_ONE_ROUND = Decimal(1000) * 1 / 1_000_000 + Decimal(1000) * 10 / 1_000_000


def test_a_billed_round_is_not_lost_when_the_next_round_is_refused():
    with pytest.raises(ProviderError) as err:
        _oc_chat([_text(), _http(400)])
    e = err.value
    assert (e.attempts, e.answered) == (2, 1) and e.billed_usd == BILLED_ONE_ROUND
    assert not isinstance(e, ProviderExhausted | UnusableAnswer)


def test_a_billed_round_is_not_lost_when_the_next_round_is_exhausted():
    with pytest.raises(ProviderExhausted) as err:
        _oc_chat([_text(), _http(500), _http(500), _http(500)])
    e = err.value
    assert (e.attempts, e.answered) == (4, 1) and e.billed_usd == BILLED_ONE_ROUND


def test_one_counter_covers_every_round_and_the_bound_is_twice_the_attempts():
    llm, r = _oc_chat([_text("a words"), _text("b words")], max_attempts=1)
    assert (r.attempts, r.answered) == (2, 2)  # two requests were sent, both billed
    assert r.cost_usd == 2 * BILLED_ONE_ROUND
    assert llm.max_requests == 2 and Flaky(failures=0, max_attempts=3).max_requests == 3
    _, r2 = _oc_chat([_text(), _http(503), _http(503), _tool()])
    assert r2.attempts == 4 and r2.answered == 2


def test_an_unusable_200_body_is_a_billed_error_but_an_http_refusal_is_not():
    class X(NetworkLLM):
        label = "x"

    x = X({"r": ROUTE}, 3, sleep=lambda _s: None)

    def _parse():  # the kinds name their response parser `_parse`: a failure in it means a request WAS answered
        raise ValueError("malformed body")

    def bad():
        return _parse()

    with pytest.raises(UnusableAnswer):
        x._retry(bad)

    def before_any_request():  # e.g. a secret read or building the body: nothing was sent, nothing is billed
        raise ValueError("no key")

    with pytest.raises(ProviderError) as unsent:
        x._retry(before_any_request)
    assert not isinstance(unsent.value, UnusableAnswer)

    def refused():
        raise _http(400)

    with pytest.raises(ProviderError) as err:
        x._retry(refused)
    assert not isinstance(err.value, UnusableAnswer)


def test_a_round_that_reports_no_usage_is_estimated_not_counted_as_zero():
    no_usage = {"choices": [{"message": {"content": "plain words"}, "finish_reason": "stop"}]}
    input_only = Route(
        model_id="gpt-x-1", input_usd_per_mtok="1000", output_usd_per_mtok="0", max_tokens=1000
    )
    with pytest.raises(ProviderError) as err:
        _oc_chat([no_usage, _http(400)], route=input_only)
    # priced on INPUT only: above 0 only if the answered round's input tokens were estimated, not counted as 0
    assert err.value.answered == 1 and err.value.billed_usd > 0
    _, r = _oc_chat([no_usage, no_usage], max_attempts=1)
    assert r.answered == 2 and r.cost_usd > 0


# ---- a 2xx whose body is cut short or is not JSON is an unusable answer and is BILLED (it used to be a free refusal)
import http.client

from hadavin_sdk.llm import common


class _Resp:
    def __init__(self, reader):
        self._reader = reader

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._reader()


def _opener_returning(reader):
    return type("Op", (), {"open": lambda self, req, timeout=None: _Resp(reader)})()


@pytest.mark.parametrize(
    "reader",
    [
        lambda: b'{"choices": [{"message": {"content": "cut sh',  # truncated JSON
        lambda: (_ for _ in ()).throw(
            http.client.IncompleteRead(b"abc", 100)
        ),  # connection dropped mid-body
        lambda: b"\xff\xfe not utf-8",  # undecodable bytes
        lambda: b"<html>gateway page</html>",  # not JSON at all
    ],
)
def test_a_200_with_an_unusable_body_is_a_billed_unusable_answer(reader, monkeypatch):
    monkeypatch.setattr(common, "_OPENER", _opener_returning(reader))
    llm = oc.OpenAICompatLLM(
        "https://api.example.com/v1",
        lambda: "k",
        {"sql_generate": PRICED},
        30,
        1,
        sleep=lambda _s: None,
    )
    with pytest.raises(UnusableAnswer) as err:
        llm.chat(
            [{"role": "user", "content": "hi"}],
            system="s",
            route="sql_generate",
            output_schema=SCHEMA,
        )
    e = err.value
    assert e.attempts == 1 and not isinstance(e, ProviderExhausted)
    # UnusableAnswer is the class the meter bills (a plain ProviderError is the free refusal)


def test_the_estimate_of_a_round_without_usage_counts_the_tool_definitions_too():
    no_usage = {"choices": [{"message": {"content": "plain words"}, "finish_reason": "stop"}]}
    input_only = Route(
        model_id="gpt-x-1", input_usd_per_mtok="1000", output_usd_per_mtok="0", max_tokens=1000
    )
    llm = oc.OpenAICompatLLM(
        "https://api.example.com/v1",
        lambda: "k",
        {"sql_generate": input_only},
        30,
        1,
        sleep=lambda _s: None,
    )

    def cost(description: str) -> Decimal:
        tool = {"name": "lookup", "description": description, "input_schema": SCHEMA}
        with mock.patch.object(oc, "post_json", side_effect=[no_usage]):
            reply = llm.chat(
                [{"role": "user", "content": "hi"}], system="s", route="sql_generate", tools=[tool]
            )
        return reply.cost_usd

    assert cost("x" * 3000) > cost("x")  # the long tool definition is billed input
