"""The one flag table (spec 6.5). The reject-only list is pinned: a change here is a change to what a person may approve."""

from __future__ import annotations

import pytest

from intake import flags

REJECT_ONLY = ("D10", "L01", "L02", "X10", "X18", "X28")


def test_reject_only_codes_are_exactly_the_spec_list():
    assert flags.reject_only_codes() == REJECT_ONLY  # sorted tuple
    assert {c for c in flags.FLAGS if not flags.is_reject_only(c)} == {"D06", "D12"}


def test_every_flag_sends_the_item_to_a_person():
    assert all(flags.is_blocking(c) for c in flags.FLAGS)


@pytest.mark.parametrize("bad", ["", "d10", "D11", "X", None, 10, "D10 ", ["D10"]])
def test_unknown_codes_raise(bad):
    for fn in (flags.is_blocking, flags.is_reject_only):
        with pytest.raises(flags.UnknownFlag):
            fn(bad)


def test_sorted_codes_union_and_unknown():
    assert flags.sorted_codes(["L01", "D06", "D06"]) == ["D06", "L01"]
    assert flags.sorted_codes([]) == []
    with pytest.raises(flags.UnknownFlag):
        flags.sorted_codes(["D06", "Z99"])


@pytest.mark.parametrize("bad", [[["D06"]], [{"a": 1}], ["D06", 5], ["D06", None], [[]], [{}, "D06"]])
def test_sorted_codes_rejects_unhashable_and_mixed_elements_with_unknownflag(bad):
    with pytest.raises(flags.UnknownFlag):
        flags.sorted_codes(bad)


def test_approvable_on_plain_dict_items():
    items = [{"flags": ["D06"]}, {"flags": []}, {"flags": ["D06", "D10"]}, {"flags": ["L01", "D06"]}, {"flags": ["X10"]}]
    assert [flags.approvable(i["flags"]) for i in items] == [True, True, False, False, False]


def test_flag_table_matches_the_exceptions_file_codes_it_shares():
    import json

    from conftest import ROOT

    exc = json.loads((ROOT / "config" / "exceptions.json").read_text(encoding="utf-8"))
    assert {"D06", "D10"} <= set(exc) and {"D06", "D10"} <= set(flags.FLAGS)


def test_flag_table_is_total_and_d12_is_approvable_with_a_reason():
    assert set(flags.FLAGS) == {"D06", "D10", "D12", "L01", "L02", "X10", "X18", "X28"}
    assert all(f.meaning and f.needs_person for f in flags.FLAGS.values())
    assert flags.reject_only_codes() == REJECT_ONLY  # D12 does not join the reject-only list
    assert not flags.is_reject_only("D12") and flags.is_blocking("D12")
    assert {c for c, f in flags.FLAGS.items() if f.needs_reason} == {"D06", "D12"}
    with pytest.raises(flags.UnknownFlag):
        flags.is_reject_only("D11")  # D11 is the order-flow supplier_mismatch of exceptions.json, not an invoice-service flag


def test_the_approval_inputs_for_d12_on_plain_dicts():
    items = [{"flags": ["D12"]}, {"flags": ["D06", "D12"]}, {"flags": ["D12", "D10"]}, {"flags": ["D12", "L01"]}, {"flags": []}]
    assert [flags.approvable(i["flags"]) for i in items] == [True, True, False, False, True]
    assert [flags.reason_required(i["flags"]) for i in items] == [
        True,
        True,
        True,
        True,
        False,
    ]  # a valid reason is required before approving D12
    assert flags.sorted_codes(["D12", "D06"]) == ["D06", "D12"]


# ---- no code is defined twice with two meanings across flags.py, codes.py and config/exceptions.json (class test for the D11 collision) -----------------
SHARED_SAME_MEANING = {
    "D06",
    "D10",
    "X10",
    "X18",
    "X28",
}  # the invoice service deliberately reuses these order-flow codes with the same meaning


def _exceptions():
    import json

    from conftest import ROOT

    return json.loads((ROOT / "config" / "exceptions.json").read_text(encoding="utf-8"))


def test_no_code_is_defined_twice_across_flags_codes_and_exceptions():
    from intake import codes

    exc = _exceptions()
    f, e, r = set(flags.FLAGS), set(exc), {c.upper() for c in codes.CODES}
    assert f & e == SHARED_SAME_MEANING, f & e  # a new overlap needs a decision recorded here, never an accident
    assert not (f & r) and not (e & r)  # reason codes collide with neither
    # the sum of the three sets equals the union plus the deliberate overlap: nothing is hidden in a pair
    assert len(f) + len(e) + len(r) == len(f | e | r) + len(f & e)
    assert "D12" not in exc and "D11" in exc and exc["D11"]["name"] == "supplier_mismatch"  # exceptions.json is untouched (errata 40b)
    assert not set(codes.CODES) & {v["name"] for v in exc.values()}, "a reason code equals an exceptions.json name"
    assert len(codes.CODES) == len(set(codes.CODES)) and "unexplained_number" in codes.CODES and "D12" not in codes.CODES


def test_the_shared_codes_keep_one_meaning_in_both_tables():
    exc = _exceptions()
    words = {  # (a word the flag's OWN meaning must hold, a word the exceptions.json name must hold)
        "D06": ("add up", "total"),
        "D10": ("bank detail", "bank"),
        "X10": ("not found", "cross_check"),
        "X18": ("unreadable", "unreadable"),
        "X28": ("over 20000", "too_large"),
    }
    assert set(words) == SHARED_SAME_MEANING
    for code, (in_flag, in_exc) in words.items():
        assert in_flag in flags.FLAGS[code].meaning.lower(), (code, flags.FLAGS[code].meaning)
        assert in_exc in exc[code]["name"], (code, exc[code]["name"])


@pytest.mark.parametrize(
    "codes,reason_ok,expected",
    [
        ([], False, None),
        (["D06"], True, None),
        (["D06"], False, "invalid_reason"),
        (["D12"], True, None),
        (["D12"], False, "invalid_reason"),
        (["D06", "D12"], False, "invalid_reason"),
        (["D10"], True, "reject_only"),
        (["D12", "D10"], True, "reject_only"),
        (["D12", "L01"], True, "reject_only"),
        (["X10"], False, "reject_only"),
    ],
)
def test_approval_blocker_is_the_single_decision(codes, reason_ok, expected):
    assert flags.approval_blocker(codes, reason_ok) == expected


def test_approval_blocker_rejects_unknown_codes_and_the_docstring_points_to_it():
    with pytest.raises(flags.UnknownFlag):
        flags.approval_blocker(["D11"], True)
    assert "approval_blocker" in flags.approvable.__doc__
