"""PR 43 result review 1 (money path): the cost contract between the core retry loop and the demo meter.

M4: every `ProviderError` raised by `with_retry` carries `.attempts` equal to the requests actually sent, a retried-then-
failed call is billed per attempt and an `UnusableAnswer` is billed. A merge that swaps `llm/retry.py` for a version
that raises bare errors makes these fail instead of silently under-billing. The pins at the end record CURRENT behaviour
that PR #48 changes (marked `PIN`): flip them in the #48 rebase.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from askdata.evalset import LockError
from askdata.meter import MeterError, _dec, call_cost, error_cost, worst_case_usd
from askdata.sealed import unchained_runs, verify_reports
from askdata.settings import Sealed
from pydantic import ValidationError

from hadavin_sdk.config import Money, Route
from hadavin_sdk.llm import common
from hadavin_sdk.llm import openai_compat as oc
from hadavin_sdk.llm.common import parse_stage
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted, UnusableAnswer
from hadavin_sdk.llm.retry import with_retry

PER = Decimal("0.01")
BIG = PER * 10  # a reservation that does not cap the charge, so the per-attempt count shows


class Net(Exception):
    pass


def _run(steps, *, max_attempts=3):
    """Run `with_retry` over a script of outcomes; return (the raised error, requests actually sent)."""
    sent = {"n": 0}
    it = iter(steps)

    def call():
        sent["n"] += 1
        step = next(it)
        if isinstance(step, BaseException):
            raise step
        return step

    with pytest.raises(ProviderError) as err:
        with_retry(
            call,
            label="k",
            max_attempts=max_attempts,
            sleep=lambda _s: None,
            retryable=lambda e: isinstance(e, Net),
        )
    return err.value, sent["n"]


def _unusable():
    try:
        parse_stage(lambda d: d["missing"], {})
    except UnusableAnswer as e:
        return e
    raise AssertionError("parse_stage did not raise")


CASES = {
    "plain refusal first request": ([ValueError("bad")], ProviderError, 1),
    "plain refusal after two transient": ([Net(), Net(), ValueError("bad")], ProviderError, 3),
    "exhausted": ([Net(), Net(), Net()], ProviderExhausted, 3),
    "unusable first request": ([_unusable()], UnusableAnswer, 1),
    "unusable after a transient": ([Net(), _unusable()], UnusableAnswer, 2),
}


@pytest.mark.parametrize("name", CASES)
def test_every_raised_provider_error_carries_the_requests_actually_sent(name):
    steps, cls, expected = CASES[name]
    err, sent = _run(list(steps))
    assert type(err) is cls and sent == expected
    assert err.attempts == sent  # not the class default of 1


def test_a_retried_then_failed_call_is_billed_per_attempt():
    err, sent = _run([Net(), Net(), Net()])
    assert sent == 3 and error_cost(err, PER, BIG, 3) == PER * 3
    err, sent = _run(
        [Net(), Net(), ValueError("bad")]
    )  # two billed-or-timed-out tries, then a free 4xx
    assert error_cost(err, PER, BIG, 3) == PER * 2


def test_an_unusable_answer_is_billed_and_a_plain_refusal_is_not():
    err, _ = _run([_unusable()])
    assert error_cost(err, PER, BIG, 3) == PER
    refused, _ = _run([ValueError("bad")])
    assert error_cost(refused, PER, BIG, 3) == 0


def test_an_error_that_is_not_a_provider_error_is_charged_for_the_configured_attempts():
    assert error_cost(TimeoutError(), PER, BIG, 3) == PER * 3


def test_a_provider_error_built_without_the_contract_charges_at_least_one_request():
    # what a bare `raise ProviderExhausted(...)` (no attempts set) costs: the class default, never zero
    assert ProviderExhausted("x").attempts == 1
    assert error_cost(ProviderExhausted("x"), PER, BIG, 3) >= PER
    assert isinstance(ProviderError.billed_usd, Decimal)


# ---- m1: the reply branch of call_cost is clamped; Money is finite and not negative
def test_call_cost_never_goes_negative_or_non_finite_with_a_reply():
    assert call_cost(PER, BIG, sent=1, reply_cost=Decimal(-1)) == 0
    assert call_cost(PER, BIG, sent=2, reply_cost=Decimal(-1)) == PER
    assert call_cost(PER, BIG, sent=1, reply_cost=Decimal("NaN")) == BIG
    assert call_cost(PER, BIG, sent=1, reply_cost=Decimal("Infinity")) == BIG


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "-1", "-0.0001"])
def test_money_is_finite_and_not_negative(bad):
    with pytest.raises(ValidationError):
        Route(model_id="m", input_usd_per_mtok=bad, output_usd_per_mtok="1", max_tokens=1)
    assert Money is not None
    ok = Route(model_id="m", input_usd_per_mtok="0", output_usd_per_mtok="1.5", max_tokens=1)
    assert ok.input_usd_per_mtok == 0


# ---- m6: a meter amount is ASCII and not astronomically large
@pytest.mark.parametrize("bad", ["١٢", "1e999999", "1E13", "9" * 40, "NaN", "-1"])
def test_meter_amounts_refuse_unicode_digits_and_huge_exponents(bad):
    with pytest.raises(MeterError):
        _dec(bad, "x")


def test_meter_amounts_accept_plain_numbers():
    assert (
        _dec("10.00", "x") == Decimal("10.00") and _dec(0, "x") == 0 and _dec("1e5", "x") == 100000
    )


# ---- m3: a validly signed but malformed chain entry is a LockError, not a KeyError or TypeError
@pytest.mark.parametrize(
    "entry",
    [
        {"kind": "report"},
        {"kind": "report", "data": None},
        {"kind": "report", "data": {}},
        {"kind": "report", "data": "x"},
    ],
)
def test_a_malformed_chain_entry_is_a_lock_error(entry, tmp_path):
    with pytest.raises(LockError):
        verify_reports([entry], tmp_path)
    with pytest.raises(LockError):
        unchained_runs([{**entry, "kind": "sealed_run"}], tmp_path)


# ---- m7: a bool is not a count
def test_max_second_looks_is_a_real_integer():
    with pytest.raises(ValidationError):
        Sealed(max_second_looks=True)
    assert Sealed(max_second_looks=3).max_second_looks == 3


# ---- PINS of behaviour PR #48 changes (flip these in the #48 rebase) -----------------------------------------------
SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}}}
ROUTE = Route(model_id="gpt-x-1", input_usd_per_mtok="1", output_usd_per_mtok="10", max_tokens=100)


def test_pin_m2_deep_json_in_a_forced_answer_missing_round_is_a_raw_recursion_error(monkeypatch):
    """PIN (#48 bounds `json_in_text`; after the rebase this must be an UnusableAnswer, billed): today the scan runs
    OUTSIDE `parse_stage`, so a deeply nested object in the text of a round with no forced tool call escapes as a raw
    RecursionError after a billed round. The demo survives it (`pipeline` books the worst case)."""
    deep = '{"a":' + "[" * 100_000 + "]" * 100_000
    body = {
        "choices": [{"message": {"content": deep}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10},
    }
    monkeypatch.setattr(
        common,
        "_OPENER",
        type(
            "Op",
            (),
            {
                "open": lambda self, req, timeout=None: type(
                    "R",
                    (),
                    {
                        "__enter__": lambda s: s,
                        "__exit__": lambda s, *a: False,
                        "read": lambda s: json.dumps(body).encode(),
                    },
                )()
            },
        )(),
    )
    llm = oc.OpenAICompatLLM(
        "https://api.example.com/v1", lambda: "k", {"r": ROUTE}, 30, 1, sleep=lambda _s: None
    )
    with pytest.raises(RecursionError):
        llm.chat([{"role": "user", "content": "hi"}], system="s", route="r", output_schema=SCHEMA)


def test_pin_m4_zero_attempts_is_an_assertion_error_not_a_config_error():
    """PIN (#48 owns `NetworkLLM.__init__`; after the rebase a ValueError at construction)."""
    with pytest.raises(AssertionError):
        with_retry(lambda: 1, label="k", max_attempts=0)


def test_pin_m5_worst_case_usd_prices_the_bytes_through_the_core_estimate():
    """PIN (the follow-up adds a core `estimate_tokens_bytes(n)` so no n-byte string is built): the value stays."""
    r = Route(model_id="m", input_usd_per_mtok="3", output_usd_per_mtok="15", max_tokens=1000)
    assert worst_case_usd(r, 3000) == (Decimal(1000) * 3 + Decimal(1000) * 15) / 1_000_000


def test_what_earlier_answered_requests_cost_travels_on_the_error():
    err = ProviderError("refused on the second request")
    err.attempts, err.answered, err.billed_usd = 2, 1, Decimal("0.02")
    assert error_cost(err, PER, BIG, 3) == Decimal(
        "0.02"
    )  # the 4xx is free, the answered first request is not
