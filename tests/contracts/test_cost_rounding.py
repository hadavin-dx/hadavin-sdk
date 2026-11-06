"""P4d-a2-i: a model call's cost is rounded UP to 8 decimals at the model and at both producers (memory store, fake
model, no Postgres). Every row computes its exact value with `fractions.Fraction`."""

from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from hadavin_sdk.config import Route
from hadavin_sdk.models import Reply, Verdict

D = Decimal
MAX_USD = D(10**12)

# (name, input tokens, input price per million tokens, expected cost); the output price is 0 in every row
ROWS = [
    ("a1", 1231, "0.001", "0.00000124"),
    ("a2", 1234, "0.001", "0.00000124"),
    ("a3", 1236, "0.001", "0.00000124"),
    ("a4", 1239, "0.001", "0.00000124"),
    ("a5", 1235, "0.075", "0.00009263"),
    ("a6", 1230, "0.001", "0.00000123"),
    ("a7", 1, "0.000001", "0.00000001"),
    ("a8", 1000, "0", "0"),
]


def _route(price):
    return Route(model_id="m", input_usd_per_mtok=D(price), output_usd_per_mtok=D(0), max_tokens=10)


def _exact(n, price):
    return Fraction(n) * Fraction(D(price)) / 1_000_000


def _round_up_fraction(x: Fraction) -> Decimal:
    scaled = x * 10**8
    whole = scaled.numerator // scaled.denominator
    if whole * scaled.denominator != scaled.numerator:
        whole += 1
    return D(whole).scaleb(-8)


@pytest.mark.parametrize(("name", "n", "price", "want"), ROWS, ids=[r[0] for r in ROWS])
def test_reply_rounds_the_cost_up(name, n, price, want):
    from hadavin_sdk.llm.common import reply

    got = reply(
        _route(price), text="x", calls=[], tokens=(n, 5), stop="end_turn", started=0.0, sent="s"
    )
    assert got.cost_usd == D(want)
    assert got.cost_usd == _round_up_fraction(_exact(n, price))
    assert got.cost_usd.as_tuple().exponent >= -8


@pytest.mark.parametrize(("name", "n", "price", "want"), ROWS, ids=[r[0] for r in ROWS])
def test_fake_model_rounds_the_cost_up(name, n, price, want, tmp_path):
    import hashlib
    import json

    from hadavin_sdk.llm.fake import FakeLLM

    messages = [{"role": "user", "content": name}]
    digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
    (tmp_path / f"{digest}-1.json").write_text(
        json.dumps({"text": "x", "input_tokens": n, "output_tokens": 5}), encoding="utf-8"
    )
    fake = FakeLLM(tmp_path, {"r": _route(price)})
    assert fake.chat(messages, system="", route="r").cost_usd == D(want)


def test_helper_keeps_the_last_digit_of_a_29_digit_value():
    from hadavin_sdk.models import round_cost_up

    assert round_cost_up(D("1." + "0" * 27 + "1")) == D("1.00000001")


@pytest.mark.parametrize(
    "bad",
    [
        D("NaN"),
        D("sNaN"),
        D("Infinity"),
        D("-Infinity"),
        D("-1"),
        D("-0"),
        D("1E+30"),
        MAX_USD + D("0.00000001"),
    ],
)
def test_helper_refuses_what_the_store_would_refuse(bad):
    from hadavin_sdk.models import round_cost_up

    with pytest.raises(ValueError):
        round_cost_up(bad)


def test_helper_accepts_the_bound_and_zero():
    from hadavin_sdk.models import round_cost_up

    assert round_cost_up(MAX_USD) == MAX_USD
    assert round_cost_up(D(0)) == 0


def test_a_route_that_skipped_validation_gives_value_error():
    from hadavin_sdk.llm.common import reply

    bad = _route("1").model_copy(update={"input_usd_per_mtok": D("NaN")})
    with pytest.raises(ValueError):
        reply(bad, text="x", calls=[], tokens=(5, 5), stop=None, started=0.0, sent="s")


def test_exactness_at_the_price_bound():
    from hadavin_sdk.llm.common import reply

    for price in ("1000000", "999999.999999"):
        got = reply(
            _route(price), text="x", calls=[], tokens=(10**9, 5), stop=None, started=0.0, sent="s"
        )
        assert got.cost_usd == _round_up_fraction(_exact(10**9, price))


@pytest.mark.parametrize("cls", [Reply, Verdict])
def test_the_model_rounds_up_at_construction(cls):
    kw = {"model_id": "m"} if cls is Reply else {"flagged": False, "score": 0.0, "backend": "b"}
    assert cls(cost_usd=D("0.123456789"), **kw).cost_usd == D("0.12345679")
    for bad in (D("-1"), D("-0"), D("1E+30"), MAX_USD + D("0.00000001"), D("NaN")):
        with pytest.raises(ValidationError):
            cls(cost_usd=bad, **kw)


def test_a_loop_run_books_the_rounded_cost_and_nothing_escapes():
    """v3/d2: a reply with a 9-decimal cost, run through the memory store the way the loop books it."""
    from datetime import UTC, datetime

    from hadavin_sdk.models import Run
    from hadavin_sdk.store.memory import MemoryStore

    store = MemoryStore()
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    r = Reply(model_id="m", cost_usd=D("0.123456789"))
    store.add_cost(run.run_id, r.cost_usd)
    store.add_spend("a", datetime.now(UTC).date(), r.cost_usd)
    assert store.get_run(run.run_id).cost_usd == D("0.12345679")
    assert store.spend_totals("a", datetime.now(UTC).date())[0] == D("0.12345679")
