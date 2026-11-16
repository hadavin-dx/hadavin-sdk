"""Gaps found by the integration mutation sample (budget.py and ground.py): each test fails against the named mutant."""

from __future__ import annotations

import pytest
from model_support import live_settings

from intake import budget
from intake.codes import Refused
from intake.ground import MAX_INT_DIGITS, parse_money


def _body() -> bytes:
    return b'{"x":1}'


def test_money_digit_limit_is_exact():  # ground.py: ``>`` mutated to ``>=``
    assert parse_money("1" * MAX_INT_DIGITS) == int("1" * MAX_INT_DIGITS) * 100
    assert parse_money("1" * (MAX_INT_DIGITS + 1)) is None


def test_halt_state_of_an_unreadable_ledger_is_not_halted(tmp_path):  # budget.py: ``return False, ""`` mutated to True
    s = live_settings(tmp_path)
    budget.reserve(s, "a" * 64, "read", _body())  # the ledger exists
    budget.ledger_path(s).write_bytes(b"this is not a sqlite file" * 40)
    assert budget.halt_state(s) == (False, "")


@pytest.mark.parametrize("tier,body", [("read", b""), ("read", "text"), ("read", None), ("nope", _body())])
def test_reserve_refuses_a_bad_tier_or_body(tmp_path, tier, body):  # budget.py: ``or`` mutated to ``and``
    s = live_settings(tmp_path)
    with pytest.raises(Refused) as e:
        budget.reserve(s, "a" * 64, tier, body)
    assert e.value.code == "bad_config"


def test_settle_retries_once_after_a_missing_ledger_and_then_succeeds(
    tmp_path, monkeypatch
):  # budget.py: ``attempt == 2`` mutated to ``!=``
    s = live_settings(tmp_path)
    res = budget.reserve(s, "b" * 64, "read", _body())
    real, n = budget._settle_once, []

    def flaky(*a, **k):
        n.append(1)
        if len(n) == 1:
            raise Refused("ledger_missing", "gone for a moment")
        return real(*a, **k)

    monkeypatch.setattr(budget, "_settle_once", flaky)
    assert budget.settle(res, (1, 1)) >= 1 and len(n) == 2
