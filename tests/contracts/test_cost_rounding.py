"""P4d-a2-i: a model call's cost is rounded UP to 8 decimals at the model and at both producers (memory store, fake
model, no Postgres). Every row computes its exact value with `fractions.Fraction`."""

from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from hadavin_sdk.config import Route
from hadavin_sdk.models import Reply, Usage, Verdict

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

    got = reply(_route(price), text="x", calls=[], usage=Usage(n, 5), stop="end_turn", started=0.0)
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
        reply(bad, text="x", calls=[], usage=Usage(5, 5), stop=None, started=0.0)


def test_exactness_at_the_price_bound():
    from hadavin_sdk.llm.common import reply

    for price in ("1000000", "999999.999999"):
        got = reply(
            _route(price), text="x", calls=[], usage=Usage(10**9, 5), stop=None, started=0.0
        )
        assert got.cost_usd == _round_up_fraction(_exact(10**9, price))


@pytest.mark.parametrize("cls", [Reply, Verdict])
def test_the_model_rounds_up_at_construction(cls):
    kw = {"model_id": "m"} if cls is Reply else {"flagged": False, "score": 0.0, "backend": "b"}
    assert cls(cost_usd=D("0.123456789"), **kw).cost_usd == D("0.12345679")
    for bad in (D("-1"), D("-0"), D("1E+30"), MAX_USD + D("0.00000001"), D("NaN")):
        with pytest.raises(ValidationError):
            cls(cost_usd=bad, **kw)


class _PricedLLM:
    """Plays one 'nothing to do' reply through `llm.common.reply` (the producer all real models use), or hands
    back a reply built directly. The agent loop is the real `Runtime`, wired as `app.build` wires it."""

    def __init__(self, *, route=None, tokens=None, direct=None):
        self.route, self.tokens, self.direct = route, tokens, direct

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        if self.direct is not None:
            return self.direct
        from hadavin_sdk.llm.common import reply
        from hadavin_sdk.llm.protocol import build_usage

        return reply(
            self.route,
            text="Nothing to do.",
            calls=[],
            usage=build_usage(*self.tokens),
            stop="end_turn",
            started=0.0,
            sent="s",
        )


def _run_through_the_loop(tmp_path, llm):
    from datetime import UTC, datetime

    from hadavin_sdk.store.memory import MemoryStore
    from tests.k5_support import build_runtime, handle, k5_cfg

    # One fixed clock for the meter (`limits.now`) and for the read below: a run that crosses midnight UTC cannot
    # book on one day and be read on the next.
    fixed = datetime.now(UTC)
    store = MemoryStore()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("hadavin_sdk.limits.now", lambda: fixed)
        rt, _cards = build_runtime(k5_cfg(tmp_path), llm, store=store)
        result = handle(rt)  # an exception that escapes the loop fails the test here
    run = store.get_run(result.run_id)
    return run.cost_usd, store.spend_totals("test-agent", fixed.date())[0]


def test_d_the_loop_books_the_producer_rounded_cost(tmp_path):
    """Row (d): the route of a5 (1235 tokens at 0.075) costs exactly 0.000092625. Run counter and day counter both
    equal the round-up 0.00009263. On the old code the loop booked 0.000092625."""
    llm = _PricedLLM(route=_route("0.075"), tokens=(1235, 5))
    assert _run_through_the_loop(tmp_path, llm) == (D("0.00009263"), D("0.00009263"))


def test_d2_an_unrounded_producer_cannot_raise_inside_the_loop(tmp_path):
    """Row (d2): the same run ends without an exception (the stores refuse 9 decimals, so a producer that did not
    round would raise after the paid call). Killed together with a1-a5 by the 'no rounding anywhere' mutant."""
    llm = _PricedLLM(route=_route("0.075"), tokens=(1235, 5))
    cost, day = _run_through_the_loop(tmp_path, llm)
    assert cost.as_tuple().exponent >= -8 and day.as_tuple().exponent >= -8


def test_v3_a_reply_with_a_nine_decimal_cost_is_booked_rounded_up(tmp_path):
    """Row (v3): a stub reply built directly with cost 0.123456789: the run completes and both counters equal
    0.12345679 (the old code booked 0.123456789)."""
    llm = _PricedLLM(direct=Reply(model_id="m", cost_usd=D("0.123456789")))
    assert _run_through_the_loop(tmp_path, llm) == (D("0.12345679"), D("0.12345679"))


def test_v4_a_reply_with_a_nan_cost_fails_before_the_loop_starts():
    """Row (v4): the object cannot be built, so no loop ever sees it."""
    with pytest.raises(ValidationError):
        Reply(model_id="m", cost_usd=D("NaN"))


def test_pricing_refuses_every_decimal_error_as_a_closed_refusal():
    """A route that skipped validation (`model_copy(update=...)`) can carry a price that overflows or is not a
    number: `cost_usd` (P4a-1 replaced `price_cost` as the one choke point of `reply` and the fake model) refuses
    with a closed `UsageMissing` or `ValueError` (the cost rounding), never `decimal.Overflow`."""
    from hadavin_sdk.llm.pricing import cost_usd
    from hadavin_sdk.llm.protocol import UsageMissing, build_usage
    from hadavin_sdk.models import round_cost_up

    for bad in (D("1E+999999"), D("NaN"), D("sNaN"), D("Infinity")):
        route = _route("1").model_copy(update={"input_usd_per_mtok": bad})
        with pytest.raises((UsageMissing, ValueError)):
            round_cost_up(cost_usd(build_usage(10, 5), route))


def test_the_fake_model_prices_through_cost_usd_and_refuses_a_bad_price(tmp_path):
    import hashlib
    import json

    from hadavin_sdk.llm.fake import FakeLLM

    messages = [{"role": "user", "content": "bad-price"}]
    digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
    (tmp_path / f"{digest}-1.json").write_text(
        json.dumps({"text": "x", "input_tokens": 10, "output_tokens": 5}), encoding="utf-8"
    )
    from hadavin_sdk.llm.protocol import UsageMissing

    route = _route("1").model_copy(update={"input_usd_per_mtok": D("1E+999999")})
    with pytest.raises((UsageMissing, ValueError)):
        FakeLLM(tmp_path, {"r": route}).chat(messages, system="", route="r")
