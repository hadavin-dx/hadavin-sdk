"""ground.py: money-token vectors of spec 6.3, field rules, currency symbols, line windows, and the three mini layouts (grounded) plus perturbed records
(each must fail on the right field)."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from conftest import MINI
from intake import ground, reader
from intake.ground import find_money, parse_money

POUND, EURO = chr(0xA3), chr(0x20AC)


# ---- money tokens ---------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "tokens"),
    [
        ("1234.50", ["1234.50"]),
        ("1,234.50", ["1,234.50"]),
        ("$1,234.50, due", ["$1,234.50"]),
        ("Total: 12.50.", ["12.50"]),
        ("12", []),
        ("12.5", []),
        ("(500.00)", ["(500.00)"]),
        ("-45.00", ["-45.00"]),
        ("$3.00", ["$3.00"]),
        ("CA$3.00", ["$3.00"]),
        ("A$3.00", ["$3.00"]),
        ("AUD 3.00", ["3.00"]),
        ("1.234,56", []),
        ("12.50|25.00", ["12.50", "25.00"]),
        ("12.50,250.00", []),  # comma-delimited tables are not supported (spec 6.3)
        ("$3", ["$3"]),
        ("2026-10-01", []),
        ("1.23.45", []),
    ],
)
def test_find_money_vectors(text, tokens):
    assert find_money(text) == tokens


@pytest.mark.parametrize(
    ("token", "minor"),
    [("$3", 300), ("(500.00)", 50000), ("-45.00", 4500), ("1,234.50", 123450), ("$1,234.50", 123450), ("12", 1200), ("abc", None)],
)
def test_parse_money(token, minor):
    assert parse_money(token) == minor


def test_find_money_is_linear_on_hostile_input():
    for text in ("1," * 20000, "(" * 20000, "$" * 20000 + "1", "1" * 50000 + ".", "0.0" * 20000):
        find_money(text)  # must simply return (a catastrophic pattern would hang here)


# ---- record builders -------------------------------------------------------------------------------------------------------------------------
def rec(**kw):
    base = {
        "invoice_no": "INV-1001",
        "supplier_name": "Acme Ltd",
        "po_ref": None,
        "currency": "USD",
        "invoice_date": "2026-10-01",
        "lines": [{"description": "Widget A", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}],
        "adjustments": [{"label": "VAT", "amount_minor": 300}],
        "total_minor": 2800,
    }
    base.update(kw)
    return base


TEXT = "INVOICE\nSupplier: Acme Ltd\nInvoice No: INV-1001\nDate: 2026-10-01\nWidget A  2  $12.50  $25.00\nVAT $3.00\nTotal due $28.00\n"


def failing(fields, text=TEXT):
    return ground.ground(fields, text).failing_fields


def test_the_base_record_is_grounded():
    assert ground.ground(rec(), TEXT) == ground.GroundResult(True, ())


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"invoice_no": "INV-1002"}, "invoice_no"),
        ({"invoice_no": "INV-100"}, "invoice_no"),  # a whole word-run only: not a prefix
        ({"supplier_name": "Acme Holdings"}, "supplier_name"),
        ({"po_ref": "PO-1"}, "po_ref"),
        ({"po_ref": ""}, "po_ref"),
        ({"invoice_date": "2026-10-02"}, "invoice_date"),
        ({"invoice_date": ""}, "invoice_date"),
        ({"currency": "GBP"}, "currency"),
        ({"total_minor": 2900}, "total_minor"),
        ({"adjustments": [{"label": "VAT", "amount_minor": 400}]}, "adjustments"),
        ({"lines": [{"description": "Widget B", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}]}, "lines"),
        ({"lines": [{"description": "Widget A", "qty": 3, "unit_cost_minor": 1250, "amount_minor": 2500}]}, "lines"),
        ({"lines": [{"description": "Widget A", "qty": 2, "unit_cost_minor": 1260, "amount_minor": 2500}]}, "lines"),
        ({"lines": [{"description": "Widget A", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2600}]}, "lines"),
        ({"lines": [{"description": "", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}]}, "lines"),
    ],
)
def test_each_field_is_checked_on_its_own(change, field):
    assert failing(rec(**change)) == (field,)


def test_failing_names_come_in_schema_order_and_are_all_listed():
    assert failing(rec(total_minor=1, invoice_no="X-1", currency="EUR")) == ("invoice_no", "currency", "total_minor")


def test_invoice_no_ignores_a_trailing_full_stop_and_case():
    assert failing(rec(), "Invoice INV-1001.\nAcme Ltd Widget A 2 12.50 25.00 VAT 3.00 28.00 2026-10-01 $") == ()
    assert failing(rec(invoice_no="inv-1001"), TEXT) == ()
    assert failing(rec(), TEXT.replace("INV-1001", "INV-1001-B")) == ("invoice_no",)  # INV-1001 inside INV-1001-B is not a whole run


def test_supplier_words_must_form_an_ordered_phrase_on_one_line():
    assert failing(rec(supplier_name="Ltd. Acme")) == ("supplier_name",)  # any-position matching was too weak
    assert failing(rec(supplier_name="Acme, Ltd.")) == ()
    assert failing(rec(supplier_name="Acme & Ltd")) == ()
    assert failing(rec(supplier_name="ACME LTD")) == ()
    two_lines = TEXT.replace("Supplier: Acme Ltd", "Supplier: Acme\nLtd")
    assert failing(rec(), two_lines) == ("supplier_name",)  # a phrase does not span lines
    # the name of another company on the invoice does not ground "Acme Ltd"
    assert failing(rec(), TEXT.replace("Supplier: Acme Ltd", "Supplier: Globex Ltd Acme Holdings")) == ("supplier_name",)
    assert failing(rec(supplier_name="Acme Ltd Co")) == ("supplier_name",)  # one missing word fails
    assert failing(rec(supplier_name=".,&")) == ("supplier_name",)  # no words at all


def test_nfc_and_whitespace_collapse_apply_to_text_and_values():
    text = TEXT.replace("Acme Ltd", "Acme \t  Ltd").replace("Widget A", "Widget   A")
    assert failing(rec(), text) == ()
    decomposed, composed = "Mu" + chr(0x308) + "ller", "M" + chr(0xFC) + "ller"
    assert failing(rec(supplier_name=decomposed), TEXT + composed + "\n") == ()


# ---- currency -------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("code", "text", "ok"),
    [
        ("USD", "pay $3.00", True),
        ("USD", "pay USD 3.00", True),
        ("USD", "pay usd", True),
        ("USD", "CA$3.00", False),
        ("USD", "A$3.00", False),
        ("USD", "US$3.00", False),  # a letter before $ and no code: X10 by design
        ("USD", "USD1250.00", False),  # code glued to digits fails by design
        ("CAD", "CA$3.00", True),
        ("CAD", "A$3.00", False),
        ("CAD", "$3.00", False),
        ("CAD", "CAD 3.00", True),
        ("CAD", "CADENCE 3.00", False),  # not a whole word-run
        ("AUD", "A$3.00", True),
        ("AUD", "CA$3.00", False),
        ("AUD", "AUD 3.00", True),
        ("GBP", POUND + "3.00", True),
        ("GBP", "3.00 GBP.", True),
        ("EUR", EURO + "3.00", True),
        ("EUR", "3.00 eur", True),
        ("EUR", "$3.00", False),
        ("GBP", "$3.00", False),
    ],
)
def test_currency(code, text, ok):
    f = rec(
        currency=code, lines=[{"description": "x", "qty": 1, "unit_cost_minor": 300, "amount_minor": 300}], adjustments=[], total_minor=300
    )
    got = ground.ground(f, f"Invoice INV-1001 Acme Ltd 2026-10-01\nx 1 3.00 3.00\nTotal 3.00 {text}\n")
    assert ("currency" not in got.failing_fields) is ok


# ---- line windows -----------------------------------------------------------------------------------------------------------------------------
def line_rec(*lines):
    ls = [{"description": d, "qty": q, "unit_cost_minor": u, "amount_minor": a} for d, q, u, a in lines]
    return rec(lines=ls, adjustments=[], total_minor=sum(a for *_, a in lines))


def test_numbers_must_be_in_the_line_window_not_elsewhere():
    head = "INV-1001 Acme Ltd 2026-10-01 USD\n"
    near = head + "Widget A 2 $12.50 $25.00\nGadget B 1 $7.00 $7.00\nTotal $32.00\n"
    assert failing(line_rec(("Widget A", 2, 1250, 2500), ("Gadget B", 1, 700, 700)), near) == ()
    swapped = line_rec(("Widget A", 2, 700, 2500), ("Gadget B", 1, 700, 700))
    assert failing(swapped, near) == ()  # 7.00 IS on the next physical line: the window rule allows it (documented weakness)
    far = head + "Widget A 2 $12.50 $25.00\nfiller\nGadget B 1 $7.00 $7.00\nTotal $32.00\n"
    assert failing(swapped, far) == ("lines",)


def test_repeated_descriptions_use_their_own_occurrence():
    text = "INV-1001 Acme Ltd 2026-10-01 USD\nBolt 1 $1.00 $1.00\nfiller\nBolt 4 $2.00 $8.00\nTotal $9.00\n"
    assert failing(line_rec(("Bolt", 1, 100, 100), ("Bolt", 4, 200, 800)), text) == ()
    assert failing(line_rec(("Bolt", 4, 200, 800), ("Bolt", 1, 100, 100)), text) == ("lines",)  # occurrences are taken in order
    three = line_rec(("Bolt", 1, 100, 100), ("Bolt", 1, 100, 100), ("Bolt", 1, 100, 100))
    assert "lines" in failing(three, text)  # more lines than occurrences


def test_qty_is_an_integer_word_run_or_a_decimal_ending_00():
    base = "INV-1001 Acme Ltd 2026-10-01 USD\nPart {} $5.00 $10.00\nTotal $10.00\n"
    assert failing(line_rec(("Part", 2, 500, 1000)), base.format("2")) == ()
    assert failing(line_rec(("Part", 2, 500, 1000)), base.format("2.00")) == ()
    assert failing(line_rec(("Part", 2, 500, 1000)), base.format("2.50")) == ("lines",)
    assert failing(line_rec(("Part", 2, 500, 1000)), base.format("12")) == ("lines",)  # 2 is not inside 12
    assert failing(line_rec(("Part", 2, 500, 1000)), base.format("x2")) == ("lines",)


def test_a_symbol_prefixed_amount_is_not_a_quantity():
    # qty 3 must not be grounded by the "3.00" of "$3.00" on the next physical line (found by the perturbation sweep)
    assert failing(rec(lines=[{"description": "Widget A", "qty": 3, "unit_cost_minor": 1250, "amount_minor": 2500}])) == ("lines",)


def test_a_bare_number_never_grounds_an_amount():
    text = "INV-1001 Acme Ltd 2026-10-01 USD\nPart 2 5 10\nTotal 10.00\n"
    assert failing(line_rec(("Part", 2, 500, 1000)), text) == ("lines",)


def test_signs_are_not_grounded():
    f = rec(adjustments=[{"label": "Discount", "amount_minor": -300}])
    assert failing(f, TEXT.replace("VAT $3.00", "Discount (3.00)")) == ()
    assert failing(f, TEXT.replace("VAT $3.00", "Discount -3.00")) == ()


def test_european_numbers_fail():
    text = TEXT.replace("$28.00", "28,00 USD").replace("$3.00", "3,00")
    assert "total_minor" in failing(rec(), text)


def test_grounding_never_raises_on_a_malformed_record():
    for bad in ({}, {"invoice_no": 5}, {"lines": [{}]}, {"lines": [5]}, rec(adjustments=[None]), rec(lines=None), rec(total_minor="x")):
        r = ground.ground(bad, TEXT)
        assert r.ok is False and r.failing_fields


# ---- the three mini layouts and the perturbation sweep ------------------------------------------------------------------------------------
REPLIES = json.loads((MINI / "fake_replies.json").read_text(encoding="utf-8"))
_SHA = {
    n: hashlib.sha256((MINI / f"{n}.txt").read_bytes()).hexdigest()[:8] for n in ("inv-A", "inv-B", "inv-C")
}  # fixtures may be regenerated
DOCS = dict(_SHA)


def _doc(name):
    return reader.read(f"{name}.txt", (MINI / f"{name}.txt").read_bytes())


def _reply(prefix):
    return next(v for k, v in REPLIES.items() if k.startswith(prefix) and k.endswith(":read"))["fields"]


@pytest.mark.parametrize("name", DOCS)
def test_the_mini_invoices_ground_against_their_layouts(name):
    assert ground.ground(_reply(DOCS[name]), _doc(name).text) == ground.GroundResult(True, ())


@pytest.mark.parametrize("name", DOCS)
def test_every_perturbed_value_of_a_mini_reply_fails(name):
    text, fields = _doc(name).text, _reply(DOCS[name])
    perturb = [
        ("invoice_no", lambda f: f.update(invoice_no=f["invoice_no"] + "9")),
        ("supplier_name", lambda f: f.update(supplier_name="Zed Corp")),
        ("total_minor", lambda f: f.update(total_minor=f["total_minor"] + 1)),
        ("currency", lambda f: f.update(currency="EUR")),
    ]
    if fields["invoice_date"] is not None:
        perturb.append(("invoice_date", lambda f: f.update(invoice_date="1999-01-01")))
    for i in range(len(fields["lines"])):
        for key in ("qty", "unit_cost_minor", "amount_minor"):
            perturb.append(("lines", lambda f, i=i, key=key: f["lines"][i].__setitem__(key, f["lines"][i][key] + 7777)))
        perturb.append(("lines", lambda f, i=i: f["lines"][i].__setitem__("description", "Nonexistent item")))
    for i in range(len(fields["adjustments"])):
        perturb.append(
            ("adjustments", lambda f, i=i: f["adjustments"][i].__setitem__("amount_minor", f["adjustments"][i]["amount_minor"] + 7777))
        )
    for field, apply in perturb:
        f = copy.deepcopy(fields)
        apply(f)
        got = ground.ground(f, text).failing_fields
        assert field in got, (name, field, got)
