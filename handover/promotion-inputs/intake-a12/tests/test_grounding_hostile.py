"""Grounding round 1: hostile numbers (the int-digit limit), quantity tokens, money-token context, supplier phrase, date and invoice-number boundaries."""

from __future__ import annotations

import pytest
from test_grounding import TEXT, failing, line_rec, rec

from intake import extract, ground
from intake.ground import find_money, parse_money
from intake.model import ModelResult

BIG = "9" * 4400  # above the 4300-digit limit of int()


# ---- BLOCKER: absurd numbers never raise ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("tail", ["Total $" + BIG, "Total " + BIG + ".00", "Total $" + BIG + ".00", "Total (" + BIG + ")", BIG + "," + BIG])
def test_a_4400_digit_run_never_raises_and_never_grounds(tail):
    r = ground.ground(rec(), TEXT + tail + "\n")
    assert r.ok is True  # the real total is still there; the absurd token is simply not a number
    assert parse_money("$" + BIG) is None
    assert find_money(tail) is not None  # must return


def test_absurd_values_in_the_record_fail_instead_of_raising():
    assert "lines" in failing(line_rec(("Widget A", 10**5000, 1250, 2500)))
    assert "total_minor" in failing(rec(total_minor=10**5000))
    assert "adjustments" in failing(rec(adjustments=[{"label": "x", "amount_minor": 10**5000}]))
    assert ground.ground(rec(), None).failing_fields == ground.ORDER  # not even a string: everything fails


def test_extract_with_a_4400_digit_invoice_is_a_normal_result_not_a_traceback(tmp_path):
    from model_support import register

    from conftest import settings_for_tests
    from intake import reader

    s = settings_for_tests(tmp_path)
    data = (TEXT + "Total $" + BIG + "\n").encode()
    register(s, reader.read("x.txt", data).text)  # the in-extract data gate refuses a text that is not on the made-up list

    class M:
        def call(self, req, **kw):
            return ModelResult(fields=rec(), model_id="m", in_tok=1, out_tok=1, cost_micro=1, error=None)

    d = extract.extract("x.txt", data, M(), s)
    # the 4,400-character line is over the masking line cap: held back before any call, a normal result and not a traceback
    assert d.fields is None and d.selfcheck == "mask_too_large" and d.calls == () and d.cost_micro == 0


# ---- quantity tokens --------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Widget A  $1,250.00  $2,500.00",  # 250 is the tail of a grouped amount
        "Widget A  1,250.00  2,500.00",
        "Widget A  $ 250.00  $ 500.00",  # a space after the symbol does not exempt
        "Widget A  USD 250.00  USD 500.00",
        "Widget A  250.00%  500.00",
        "Widget A  x250  500.00",
        "Widget A  250kg  500.00",
        "Widget A  2026-250  500.00",
    ],
)
def test_quantity_must_be_a_whole_number_token(text):
    f = rec(lines=[{"description": "Widget A", "qty": 250, "unit_cost_minor": 25000, "amount_minor": 50000}])
    body = "INV-1001 Acme Ltd 2026-10-01 USD\n" + text + "\nTotal $500.00\n"
    assert "lines" in ground.ground(rec(lines=f["lines"], adjustments=[], total_minor=50000), body).failing_fields


def test_a_real_quantity_still_grounds():
    for qty_text in ("2", "2.00", "(2)"):
        t = f"INV-1001 Acme Ltd 2026-10-01 USD\nWidget A  {qty_text}  $12.50  $25.00\nTotal $25.00\n"
        assert ground.ground(line_rec(("Widget A", 2, 1250, 2500)), t).failing_fields == (), qty_text


# ---- money-token context ----------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["20.00%", "12.50kg", "ABC12345.67", "12.50USD", "3.00x", "x3.00"])
def test_numbers_with_a_percent_or_letters_around_them_are_not_money(text):
    assert find_money(text) == []


@pytest.mark.parametrize("text", ["$20.00", "20.00 ", "(20.00)", "-20.00", "A$20.00", "CA$20.00", "total:20.00", "20.00."])
def test_ordinary_money_still_counts(text):
    assert len(find_money(text)) == 1


def test_a_total_that_only_appears_as_a_percentage_fails():
    assert "total_minor" in failing(
        rec(total_minor=2000, adjustments=[]), TEXT.replace("$28.00", "20.00%").replace("$3.00", "").replace("$25.00", "")
    )


# ---- boundaries and folding ---------------------------------------------------------------------------------------------------------------------
def test_invoice_date_needs_boundaries():
    assert failing(rec(), TEXT.replace("2026-10-01", "12026-10-015")) == ("invoice_date",)
    assert failing(rec(), TEXT.replace("2026-10-01", "Date 2026-10-01.")) == ()
    assert failing(rec(invoice_date="26-10-01")) == ("invoice_date",)  # a tail of the real date is not the date


def test_po_ref_is_a_whole_run():
    assert failing(rec(po_ref="PO-12"), TEXT + "PO-123\n") == ("po_ref",)
    assert failing(rec(po_ref="PO-123"), TEXT + "PO-123\n") == ()


def test_invoice_numbers_are_nfkc_folded_then_compared_in_ascii():
    fullwidth = "".join(chr(ord(c) + 0xFEE0) if c.isalnum() else c for c in "INV-1001")
    assert failing(rec(), TEXT.replace("INV-1001", fullwidth)) == ()  # fullwidth text grounds the ASCII number
    assert failing(rec(invoice_no=fullwidth)) == ()  # and a fullwidth model value grounds too
    accented = "INV-" + chr(0xE9) + "1"  # non-ASCII after folding: never grounded (false-ungrounded; a person sees it)
    assert failing(rec(invoice_no=accented), TEXT.replace("INV-1001", accented)) == ("invoice_no",)
