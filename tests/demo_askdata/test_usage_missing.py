"""P4a-1 row U6 (temporary demo edit): an answered call with no usable token count is charged the reserved amount, the
same as a call the provider billed but did not answer. It lives here, not in `tests/test_usage_refuse.py`, because the
demo package is importable only under this folder's conftest."""

from decimal import Decimal
from fractions import Fraction

from hadavin_sdk.llm import protocol
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from tests.demo_askdata.kit import Kit
from tests.demo_askdata.test_pipeline import Q

UsageMissing = getattr(protocol, "UsageMissing", None) or type("UsageMissing", (ProviderError,), {})


def _spent_when(tmp_path, error):
    k = Kit(tmp_path)

    class Boom:
        def chat(self, *a, **kw):
            raise error

    k.pipeline.llm = Boom()
    answer = k.pipeline.ask(Q)
    return answer, k.meter.snapshot()["askdata_spent"]


def test_usage_missing_is_charged_exactly_what_a_billed_failure_is(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    err = (
        UsageMissing("absent", "usage") if hasattr(protocol, "UsageMissing") else UsageMissing("x")
    )
    answer, missing = _spent_when(tmp_path / "a", err)
    _, exhausted = _spent_when(tmp_path / "b", ProviderExhausted("5xx"))
    assert missing == exhausted  # equality: a double charge or a missing charge fails
    assert Decimal(answer.line.cost_usd) == missing
    floor = Fraction(
        1024 * 10, 10**6
    )  # max_tokens times the demo route's output price (10 per million)
    assert Fraction(missing) >= floor


def test_a_plain_refusal_is_still_free(tmp_path):
    _, spent = _spent_when(tmp_path, ProviderError("bad key"))
    assert spent == 0


def _spent_with_wire(tmp_path, failures):
    """The pipeline driven by a real OpenAI-compatible kind whose request 1 was answered (300 in, 7 out, no answer)
    and whose request 2 failed in the way `failures` serves."""
    from tests.contracts.kinds.llm_wire import OpenAICompatWire
    from tests.demo_askdata.kit import ROUTE

    wire = OpenAICompatWire()
    try:
        k = Kit(tmp_path)
        first = wire.scenario("text")
        first["body"]["choices"][0]["message"]["content"] = "no idea"
        wire.set_tokens(first, 300, 7)
        k.pipeline.llm = wire.serve(first, *failures(wire), routes={k.pipeline.s.route: ROUTE})
        answer = k.pipeline.ask(Q)
        return answer, k.meter.snapshot()["askdata_spent"], len(wire.requests)
    finally:
        wire.close()


def test_c16a_a_failed_request_two_after_an_answered_request_one_is_booked_not_free(tmp_path):
    cases = {
        "exhausted": lambda w: [w.scenario("throttle")] * 3,
        "http_400": lambda w: [{"status": 400, "body": {"error": {"message": "x", "code": "c"}}}],
        "unparsable": lambda w: [{"status": 200, "body": {"choices": []}}],
    }
    for name, failures in cases.items():
        (tmp_path / name).mkdir()
        answer, spent, requests = _spent_with_wire(tmp_path / name, failures)
        assert requests >= 2
        assert (
            spent > 0
        )  # the temporary demo edit books the reserved amount, never less than a refusal's zero
        assert Decimal(answer.line.cost_usd) == spent
