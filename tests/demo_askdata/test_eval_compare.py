"""Result comparison rules: scale, order, ties, extra columns, interpretations, second-seed agreement."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

from askdata import compare
from askdata.compare import Match, agrees, match, matches_interpretation, result_hash, tie_at_cut

GOLD = [("US", Decimal("10.50"), 3), ("UK", Decimal("7.25"), 2)]


def test_identical_results_match():
    assert match(GOLD, list(GOLD)).ok


def test_column_names_do_not_exist_and_column_order_is_ignored():
    swapped = [(3, "US", Decimal("10.50")), (2, "UK", Decimal("7.25"))]
    assert match(GOLD, swapped).ok


def test_row_order_is_ignored_unless_it_matters():
    rev = list(reversed(GOLD))
    assert match(GOLD, rev).ok
    m = match(GOLD, rev, order_matters=True)
    assert not m.ok and m.reason == "row_order"
    assert match(GOLD, list(GOLD), order_matters=True).ok


def test_numbers_are_rounded_half_even_to_the_scale():
    assert match([(Decimal("2.345"),)], [(2.34,)]).ok  # 2.345 -> 2.34 (half-even) and 2.34 -> 2.34
    assert match([(Decimal("2.355"),)], [(Decimal("2.36"),)]).ok
    assert not match([(Decimal("2.30"),)], [(Decimal("2.31"),)]).ok
    assert match([(Decimal("2.30"),)], [(Decimal("2.31"),)], scale=[1]).ok  # a coarser item scale
    assert not match([(Decimal("0.1234"),)], [(Decimal("0.1235"),)], scale=[4]).ok


def test_ints_floats_and_decimals_with_the_same_value_are_equal():
    assert match([(3,)], [(Decimal("3.00"),)]).ok and match([(3,)], [(3.0,)]).ok


def test_an_extra_or_missing_column_is_not_correct():
    m = match(GOLD, [(r[0], r[1], r[2], "x") for r in GOLD])
    assert not m.ok and m.reason == "column_count"
    assert match(GOLD, [(r[0], r[1]) for r in GOLD]).reason == "column_count"


def test_a_different_row_count_or_value_is_wrong():
    assert match(GOLD, GOLD[:1]).reason == "row_count"
    assert not match(GOLD, [("US", Decimal("10.50"), 3), ("UK", Decimal("7.25"), 9)]).ok


def test_duplicate_rows_count_as_a_multiset():
    assert match([(1,), (1,), (2,)], [(1,), (2,), (2,)]).ok is False
    assert match([(1,), (1,), (2,)], [(2,), (1,), (1,)]).ok


def test_null_equals_null_only():
    assert match([(None, 1)], [(None, 1)]).ok
    assert not match([(None, 1)], [("", 1)]).ok and not match([(None,)], [(0,)]).ok


def test_timestamps_compare_by_value_in_utc():
    ist = timezone(timedelta(hours=5, minutes=30))
    a = [(datetime(2026, 1, 1, 6, 30, tzinfo=UTC),)]
    b = [(datetime(2026, 1, 1, 12, 0, tzinfo=ist),)]
    assert match(a, b).ok and match([(date(2026, 1, 1),)], [(date(2026, 1, 1),)]).ok
    assert not match(a, [(datetime(2026, 1, 1, 6, 31, tzinfo=UTC),)]).ok


def test_empty_results_compare_by_width():
    assert match([], [], gold_width=2, cand_width=2).ok
    assert match([], [], gold_width=2, cand_width=3).reason == "column_count"
    assert match([], [(1, 2)], gold_width=2, cand_width=2).reason == "row_count"


def test_two_columns_with_equal_values_can_be_mapped_either_way():
    assert match([(1, 1), (2, 2)], [(1, 1), (2, 2)]).ok
    assert not match(
        [(1, 2), (2, 1)], [(1, 1), (2, 2)]
    ).ok  # same columns' values, different pairing


def test_agreement_needs_both_seed_databases():
    ok, bad = Match(True, "match"), Match(False, "row_count")
    assert agrees(ok, ok) and not agrees(ok, bad) and not agrees(bad, ok)


def test_tie_at_the_cut_is_detected():
    assert tie_at_cut([9, 8, 8, 5], 2) is True  # row 2 and row 3 both 8
    assert tie_at_cut([9, 8, 7, 5], 2) is False
    assert tie_at_cut([9, 8], 2) is False  # nothing past the cut
    assert tie_at_cut([Decimal("1.000001"), Decimal("1.000002")], 1) is False
    assert (
        tie_at_cut([Decimal("1.0000001"), Decimal("1.0000002")], 1) is True
    )  # equal at the comparison scale


def test_interpretations_match_one_of_several():
    interps = {"i1": [(5,)], "i2": [(9,)]}
    assert (
        matches_interpretation([(9,)], interps) == "i2"
        and matches_interpretation([(1,)], interps) is None
    )


def test_result_hash_is_stable_and_order_rules_hold():
    a = [(1, Decimal("2.50")), (2, None)]
    assert result_hash(a, ordered=True) == result_hash(
        [(1, Decimal("2.5")), (2, None)], ordered=True
    )
    assert result_hash(a, ordered=False) == result_hash(list(reversed(a)), ordered=False)
    assert result_hash(a, ordered=True) != result_hash(list(reversed(a)), ordered=True)
    assert result_hash([], ordered=False) == result_hash([], ordered=True)
    assert len(result_hash(a, ordered=True)) == 64 and compare.NULL not in str(
        result_hash(a, ordered=True)
    )


# ------------------------------------------------------------------ regression tests for the independent review


def test_oversized_model_text_never_loses_the_question(tmp_path):
    from askdata.fixtures import Step

    from tests.demo_askdata.kit import COUNT_ORDERS, Kit

    k = Kit(tmp_path)
    q = "How many orders are there"
    k.script(q, Step(sql=COUNT_ORDERS, assumptions=("x" * 301, "y" * 5) + ("z",) * 30))
    a = k.pipeline.ask(q)
    assert (
        a.outcome == "answered"
        and len(a.line.assumptions) == 20
        and max(map(len, a.line.assumptions)) <= 300
    )
    assert len(k.ledger.read().items) == 1
    ctl = chr(1) * 1500  # under 4000 raw, far over after being made visible
    k2 = Kit(tmp_path / "2")
    k2.script(q, Step(sql=f"SELECT 1 /* {ctl} */"), Step(sql=COUNT_ORDERS), Step(sql=COUNT_ORDERS))
    b = k2.pipeline.ask(q)
    assert len(k2.ledger.read().items) == 1 and b.query_id
    from askdata import audit

    assert audit.verify(k2.ledger, k2.sink).ok


def test_set_external_refuses_values_that_would_brick_the_meter(tmp_path):
    from decimal import Decimal

    import pytest
    from askdata.meter import Meter, MeterError

    m = Meter(tmp_path / "m.json")
    Meter.create(m.path, total_cap="10.00", reserve="1.00", demo_cap="8.00")
    for bad in (Decimal(-1), Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(MeterError):
            m.set_external(bad)
    assert m.snapshot()["external_usd"] == 0
    with pytest.raises(MeterError):
        Meter.create(tmp_path / "n.json", total_cap="10.00", reserve="1.00", demo_cap="9.50")


def test_compare_survives_huge_and_non_finite_numbers():
    from decimal import Decimal

    from askdata.compare import match

    assert match([(1e30,)], [(1e30,)]).ok
    assert match([(Decimal("Infinity"),)], [(Decimal("Infinity"),)]).ok
    assert not match([(1e30,)], [(1.0,)]).ok


def test_second_look_aborted_needs_an_aborted_first_run():
    from decimal import Decimal

    import pytest
    from askdata import evalrun
    from askdata.evalset import Lock, LockError

    done = Lock(files={}, test_runs=1, last_test_status="complete")
    with pytest.raises(LockError, match="did not abort"):
        evalrun.sealed_gate(done, Decimal(5), split="test", second_look="aborted")
    with pytest.raises(LockError, match="harness_defect_reason"):  # a completed run is NOT a defect
        evalrun.sealed_gate(done, Decimal(5), split="test", second_look="harness_defect")
    evalrun.sealed_gate(
        done.model_copy(update={"harness_defect_reason": "seed B drifted"}),
        Decimal(5),
        split="test",
        second_look="harness_defect",
    )
    evalrun.sealed_gate(
        done.model_copy(update={"last_test_status": "aborted"}),
        Decimal(5),
        split="test",
        second_look="aborted",
    )
