"""An invalid cost can never be built into a Reply or a Verdict (F-store review 6, Major-1)."""

from decimal import Decimal

import pytest

from hadavin_sdk.models import Reply, Verdict

BAD = [
    Decimal("-0.5"),
    Decimal("NaN"),
    Decimal("sNaN"),
    Decimal("Infinity"),
    Decimal("-Infinity"),
    Decimal("0.0000000000001"),  # 13 places
    Decimal(1) / Decimal(3),
    Decimal(10) ** 9,
    1,
    True,
    0.5,
    "0.5",
]


def _reply(cost: object) -> Reply:
    return Reply(model_id="m", cost_usd=cost)  # type: ignore[arg-type]


def _verdict(cost: object) -> Verdict:
    return Verdict(flagged=False, score=0.0, backend="b", cost_usd=cost)  # type: ignore[arg-type]


@pytest.mark.parametrize("cost", BAD, ids=repr)
def test_reply_refuses_bad_cost(cost: object) -> None:
    with pytest.raises(ValueError):
        _reply(cost)


@pytest.mark.parametrize("cost", BAD, ids=repr)
def test_verdict_refuses_bad_cost(cost: object) -> None:
    with pytest.raises(ValueError):
        _verdict(cost)


def test_reply_accepts_none_and_zero_and_twelve_places() -> None:
    assert _reply(None).cost_usd is None
    assert _reply(Decimal(0)).cost_usd == 0
    assert _reply(Decimal("0.000000000001")).cost_usd == Decimal("0.000000000001")


def test_verdict_accepts_zero_but_not_none() -> None:
    assert _verdict(Decimal(0)).cost_usd == 0
    assert Verdict(flagged=False, score=0.0, backend="b").cost_usd == 0
    with pytest.raises(ValueError):
        _verdict(None)
