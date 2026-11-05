"""REGRESSION GUARDS, not pre-fix proof: these passed on the old source (1479888) too, because the old code was already linear or already correct on
these inputs. They pin that behaviour for the new regex and caps (several mutants of `gate_rules._PCT` are killed here). The per-test fail-before /
pass-after proof is `test_review1_behaviour.py` only (`mutation/prefix_proof.py`)."""

import pytest
from test_review1_behaviour import percent_pattern_in_child, within

from dealdesk import gate_rules as g


@pytest.mark.parametrize(
    "shape",
    ["a " * 25_000, "$1" * 25_000, "usd 1 " * 8_000, "1 % " * 12_000, "a" * 50_000, "1a" * 25_000, "-1" * 25_000, "1." * 25_000],
)
def test_traceability_stays_linear_on_other_hostile_runs_guard(shape):
    out, took = within(5, g.traceability, shape)
    assert out["status"] == "hand_back" and took < 2.0


@pytest.mark.parametrize("shape", ["a" * 300_000, "1a" * 150_000, "-1" * 100_000, "a1" * 100_000 + "x", "+" * 200_000])
def test_the_percent_pattern_stays_linear_on_letter_and_sign_runs_guard(shape):
    percent_pattern_in_child(shape)


def test_spelled_numbers_and_uptime_percentages_still_work_guard():
    assert g.traceability("Zephyr Works wants twenty five percent off")["discount_bps"] == 2500
    assert g.traceability("Zephyr Works wants 15% off, 99.95% uptime")["discount_bps"] == 1500
