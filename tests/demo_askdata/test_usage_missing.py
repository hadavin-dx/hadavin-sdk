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
