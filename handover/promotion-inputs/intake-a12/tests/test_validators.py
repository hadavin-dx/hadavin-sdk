"""validate_record (spec 6.2): schema rules, integers only, limits, control characters, unknown keys."""

from __future__ import annotations

import copy
import json

import pytest

from conftest import MINI
from intake import validators as v

GOOD = {
    "invoice_no": "INV-1",
    "supplier_name": "Acme Ltd",
    "po_ref": None,
    "currency": "USD",
    "invoice_date": None,
    "lines": [{"description": "Widget", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}],
    "adjustments": [{"label": "VAT", "amount_minor": -300}],
    "total_minor": 2200,
}


def bad(**over):
    d = copy.deepcopy(GOOD)
    d.update(over)
    return v.validate_record(d)


def test_good_record_and_optional_fields_may_be_absent():
    assert v.validate_record(GOOD) == []
    d = copy.deepcopy(GOOD)
    del d["po_ref"], d["invoice_date"]
    assert v.validate_record(d) == []


def test_every_fake_reply_validates():
    for key, val in json.loads((MINI / "fake_replies.json").read_text()).items():
        if isinstance(val, dict):
            assert v.validate_record(val["fields"]) == [], key


@pytest.mark.parametrize("name", list(v.REQUIRED))
def test_missing_required(name):
    d = copy.deepcopy(GOOD)
    del d[name]
    assert v.validate_record(d) == [name]


@pytest.mark.parametrize("value", [True, 1.0, 1.5, "12", None, [1], float("nan"), float("inf")])
def test_integer_fields_reject_non_integers_and_bool(value):
    assert bad(total_minor=value) == ["total_minor"]
    assert bad(lines=[{**GOOD["lines"][0], "qty": value}]) == ["lines"]
    assert bad(lines=[{**GOOD["lines"][0], "unit_cost_minor": value}]) == ["lines"]
    assert bad(adjustments=[{"label": "x", "amount_minor": value}]) == ["adjustments"]


def test_range_limits():
    big = 10**12
    assert bad(total_minor=big) == []
    assert bad(total_minor=big + 1) == ["total_minor"]
    assert bad(total_minor=-1) == ["total_minor"]
    assert bad(lines=[{**GOOD["lines"][0], "qty": -1}]) == ["lines"]
    assert bad(lines=[{**GOOD["lines"][0], "amount_minor": big + 1}]) == ["lines"]
    assert bad(adjustments=[{"label": "x", "amount_minor": -big}]) == []
    assert bad(adjustments=[{"label": "x", "amount_minor": -big - 1}]) == ["adjustments"]
    assert bad(adjustments=[{"label": "x", "amount_minor": big + 1}]) == ["adjustments"]


def test_line_and_adjustment_counts():
    line = GOOD["lines"][0]
    assert bad(lines=[line] * 25) == []
    assert bad(lines=[line] * 26) == ["lines"]
    assert bad(lines=[]) == ["lines"]
    assert bad(adjustments=[{"label": "x", "amount_minor": 1}] * 10) == []
    assert bad(adjustments=[{"label": "x", "amount_minor": 1}] * 11) == ["adjustments"]


@pytest.mark.parametrize("name", ["invoice_no", "supplier_name"])
@pytest.mark.parametrize("value", ["", "   ", "\t\n", None, 5])
def test_required_strings_non_empty_after_strip(name, value):
    assert bad(**{name: value}) == [name]


@pytest.mark.parametrize("ch", ["\x00", "\n", "\t", "\x1f", "\x7f", "\ud800"])
def test_control_characters_and_lone_surrogates_rejected(ch):
    assert bad(invoice_no="INV" + ch + "1") == ["invoice_no"]
    assert bad(po_ref="P" + ch) == ["po_ref"]
    assert bad(lines=[{**GOOD["lines"][0], "description": "a" + ch}]) == ["lines"]
    assert bad(adjustments=[{"label": "a" + ch, "amount_minor": 1}]) == ["adjustments"]


def test_currency_must_be_in_the_configured_list():
    assert bad(currency="EUR") == []
    for c in ("usd", "JPY", "", None, "USD ", 5):
        assert bad(currency=c) == ["currency"], c
    assert v.validate_record({**GOOD, "currency": "JPY"}, currencies=["JPY"]) == []


def test_unknown_and_extra_keys_never_echo_the_key():
    d = {**GOOD, "bank_detail": "x"}
    assert v.validate_record(d) == ["unknown_field"]
    assert v.validate_record({**GOOD, "lines": [{**GOOD["lines"][0], "extra": 1}]}) == ["lines"]
    assert v.validate_record({**GOOD, 5: "x"}) == ["unknown_field"]  # type: ignore[dict-item]


@pytest.mark.parametrize("not_a_dict", [None, [], "x", 5, ()])
def test_non_dict_record(not_a_dict):
    assert v.validate_record(not_a_dict) == ["record"]


def test_several_failures_come_back_in_schema_order_without_duplicates():
    assert bad(total_minor="x", invoice_no="", currency="zz", po_ref=3) == ["invoice_no", "currency", "total_minor", "po_ref"]


def test_schema_and_validator_agree_on_the_required_list():
    assert v.RECORD_SCHEMA["required"] == list(v.REQUIRED) and v.RECORD_SCHEMA["additionalProperties"] is False
    assert v.RECORD_SCHEMA["properties"]["lines"]["maxItems"] == 25
    json.dumps(v.RECORD_SCHEMA)  # serialisable as the tool input schema


@pytest.mark.parametrize("name,cap", [("invoice_no", 64), ("po_ref", 64), ("supplier_name", 200), ("invoice_date", 32)])
def test_character_caps(name, cap):
    assert bad(**{name: "a" * cap}) == []
    assert bad(**{name: "a" * (cap + 1)}) == [name]
    assert v.MAX_LEN[name] == cap and v.RECORD_SCHEMA["properties"][name]["maxLength"] == cap


def test_null_optional_fields_still_pass_the_caps():
    assert bad(po_ref=None, invoice_date=None) == []


def test_zero_width_only_required_strings_are_empty():
    zw = chr(0x200B) * 5
    assert bad(invoice_no=zw) == ["invoice_no"] and bad(supplier_name=zw + " ") == ["supplier_name"]
    assert bad(invoice_no=chr(0x2060) + "A") == ["invoice_no"]  # a format character (Cf) is refused even with visible text


def test_caps_are_measured_on_the_folded_text_too():
    fdfa = chr(0xFDFA)  # one character, three UTF-8 bytes, 18 characters after the fold
    from intake.textfold import fold_text

    assert len(fdfa) == 1 and len(fold_text(fdfa)) == 18
    assert bad(invoice_no=fdfa) == []
    assert bad(invoice_no=fdfa * 4) == ["invoice_no"]  # 4 characters, 72 after the fold: over the cap of 64
    assert bad(po_ref=fdfa * 4) == ["po_ref"]
    assert bad(supplier_name=fdfa * 11) == []  # 198 folded characters
    assert bad(supplier_name=fdfa * 12) == ["supplier_name"]  # 216 folded characters: over 200


def test_caps_on_utf8_bytes_and_on_line_strings():
    assert v.MAX_BYTES_PER_CHAR == 4
    assert bad(lines=[{**GOOD["lines"][0], "description": "d" * 200}]) == []
    assert bad(lines=[{**GOOD["lines"][0], "description": "d" * 201}]) == ["lines"]
    assert bad(lines=[{**GOOD["lines"][0], "description": chr(0xFDFA) * 12}]) == ["lines"]
    assert bad(adjustments=[{"label": "l" * 64, "amount_minor": 1}]) == []
    assert bad(adjustments=[{"label": "l" * 65, "amount_minor": 1}]) == ["adjustments"]
    assert bad(adjustments=[{"label": chr(0xFDFA) * 4, "amount_minor": 1}]) == ["adjustments"]
    props = v.RECORD_SCHEMA["properties"]
    assert props["lines"]["items"]["properties"]["description"]["maxLength"] == 200
    assert props["adjustments"]["items"]["properties"]["label"]["maxLength"] == 64


@pytest.mark.parametrize("cp", [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x202E, 0x202A, 0x2066, 0x2028, 0x2029, 0x00AD])
def test_format_line_and_paragraph_separators_are_refused_in_every_string(cp):
    ch = chr(cp)
    assert bad(invoice_no="A" + ch + "B") == ["invoice_no"]
    assert bad(supplier_name="Acme" + ch) == ["supplier_name"]
    assert bad(po_ref=ch) == ["po_ref"]
    assert bad(invoice_date="2026" + ch) == ["invoice_date"]
    assert bad(lines=[{**GOOD["lines"][0], "description": "d" + ch}]) == ["lines"]
    assert bad(adjustments=[{"label": "l" + ch, "amount_minor": 1}]) == ["adjustments"]


def test_the_length_is_checked_before_any_scan_or_fold(monkeypatch):
    calls = []

    def spy(text, **kw):
        calls.append(len(text))
        return text

    monkeypatch.setattr(v, "fold_text", spy)
    scans = []
    real_clean = v._clean_str

    def clean_spy(s):
        scans.append(len(s) if isinstance(s, str) else 0)
        return real_clean(s)

    monkeypatch.setattr(v, "_clean_str", clean_spy)
    huge = "x" * 5_000_000
    assert bad(invoice_no=huge) == ["invoice_no"] and bad(po_ref=huge) == ["po_ref"] and bad(supplier_name=huge) == ["supplier_name"]
    assert bad(lines=[{**GOOD["lines"][0], "description": huge}]) == ["lines"]
    assert not [n for n in calls if n > 1000], calls  # no fold ran on an over-long string
    assert not [n for n in scans if n > 1000], scans  # and no character scan either: the length check comes first


@pytest.mark.parametrize("value", ["25", True, False, 0, 101, -1, 25.0, None, [25], 10**9])
def test_max_lines_from_policy_refuses_bad_types_and_bounds(monkeypatch, value):
    from intake.codes import ConfigError

    monkeypatch.setattr(v.settings, "read_policy_value", lambda key: value)
    with pytest.raises(ConfigError) as ei:
        v._max_lines_from_policy()
    assert ei.value.code == "bad_config"


@pytest.mark.parametrize("value", [1, 25, 100])
def test_max_lines_from_policy_accepts_real_integers(monkeypatch, value):
    monkeypatch.setattr(v.settings, "read_policy_value", lambda key: value)
    assert v._max_lines_from_policy() == value
