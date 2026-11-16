"""Mask kernel, round 6 (review-p2-4 of 1090d39): IBAN-shaped places from a first token of any length, with the country code and the check digits apart,
and glued to a zero-width character; false hides of item codes, gate numbers and months; dates read on the FOLDED text; amounts beside a currency code.
The class-level property test (one assertion per layout dimension, on the detected spans and on the real output) is tests/test_mask_iban_fuzz.py; this
file holds the named rows, including the VAT numbers that are hidden as IBANs on purpose (a false hide, listed in the README limits)."""

from __future__ import annotations

import re

import pytest
from test_mask_kernel import m

NB, EN, ZW = chr(0xA0), chr(0x2013), chr(0x200B)
MARK = re.compile(r"<[A-Z]+_\d+>")


def plain(text: str) -> str:
    """What stays visible: the output with its marks cut out."""
    return MARK.sub("", text)


# ---------------------------------------------------------------------------------------------------------------- MAJOR 1: first tokens, apart, glued
def test_a_first_token_of_ten_characters_is_followed_by_its_groups():
    assert m("Pay to DE89370400 4405 3201 3000 1").text == "Pay to <IBAN_1> 1"  # one typed extra digit may stay, never a run of four


def test_a_first_token_of_twelve_characters_is_followed_by_a_last_group_of_any_length():
    assert m("GB29NWBK6016 1331 9268 11").text == "<IBAN_1>"
    assert m("Ref nl0377695923 23098 and").text == "Ref <IBAN_1> and"


@pytest.mark.parametrize("text", ["DE 88 3704 0044 0532 0130 00", "DE 89 3704 0044 0532 0130 00", "AT 61 1904 3002 3457 3201"])
def test_the_country_code_and_the_check_digits_as_two_tokens_are_hidden(text):
    assert not any(c.isdigit() for c in plain(m(text).text)), ascii(m(text).text)


def test_the_check_digits_stuck_to_a_zero_width_character_and_the_bank_code_are_one_token():
    text = "iban AL\n> 62" + ZW + "ZBGT\n  89455193,62748809\r\n  989\n2026-11-04"
    out = m(text).text
    assert "89455193" not in out and "62748809" not in out and out.endswith("2026-11-04"), ascii(out)


@pytest.mark.parametrize(
    "text",
    [
        "DE89370400440532013000",
        "DE89" + ZW + "3704" + ZW + "0044" + ZW + "0532" + ZW + "0130" + ZW + "00",
        "DE88\r\n\r\n3704\r\n\r\n0044\r\n\r\n0532\r\n\r\n0130\r\n\r\n00",
        "DE88\n\n3704\n\n0044\n\n0532\n\n0130\n\n00",
    ],
)
def test_one_piece_zero_width_and_double_break_layouts_are_hidden_whole(text):
    assert m(text).text == "<IBAN_1>"


@pytest.mark.parametrize("prefix", [ZW, ZW + " ", NB, "IBAN:", "IBAN" + ZW, "x " + ZW])
def test_a_zero_width_or_glued_prefix_does_not_hide_the_country_code(prefix):
    out = m(prefix + "GB29 NWBK 6016 1331 9268 04").text
    assert out == prefix + "<IBAN_1>", ascii(out)


def test_zero_width_characters_inside_a_bank_code_or_a_last_group():
    assert m("GB29 N" + ZW + "W" + ZW + "B" + ZW + "K 6016 1331 9268 04").text == "<IBAN_1>"
    assert m("GB29 NWBK 6016 1331 92" + ZW + "68 0" + ZW + "4").text == "<IBAN_1>"


# ---------------------------------------------------------------------------------------------------------------- MAJOR 2: false hides stay visible
@pytest.mark.parametrize(
    "text",
    [
        "Item IT10 Pen 2 pcs 4.50 EUR 9.00",
        "Gate NO12 is open from 9 to 5 on 1 Nov",
        "DE12 is the 1st of May 2026",
        "Pay IT10 Pen 2 pcs 4.50 EUR 9.00 now",
        "VAT DE123456789",
        "VAT FR12345678901",
        "Ref NO86 0111 1794",
        "GB29 NWBK 6016",
    ],
)
def test_item_codes_gate_numbers_months_and_short_references_stay_visible(text):
    assert m(text).text == text


@pytest.mark.parametrize("tail", [" 9.00 EUR", " EUR 9.00", "\nTotal 12.50 EUR"])
def test_a_decimal_amount_beside_a_currency_code_ends_the_walk(tail):
    assert m("GB29 NWBK 6016 1331 9268 04" + tail).text == "<IBAN_1>" + tail


def test_a_currency_code_does_not_complete_a_short_account():
    # three letters that would complete a mistyped account by length are a currency code, not part of it
    out = m("IBAN: LU77 DVVU 2006 6156 3 EUR 9.00").text
    assert out.endswith("EUR 9.00"), ascii(out)


# ---------------------------------------------------------------------------------------------------------------- MINOR 3-4: dates on folded text, CRLF
@pytest.mark.parametrize("date", ["04" + EN + "11" + EN + "2026", "04 11 2026", "04.11.2026", "04/11/2026"])
def test_a_date_after_a_mistyped_iban_is_read_on_the_folded_text(date):
    out = m("GB29 NWBK 6016 1331 9268 " + date).text
    assert out == "<IBAN_1> " + date, ascii(out)


def test_two_digit_year_dates_are_not_recognised_and_may_be_swallowed():
    # honest limit: only four-digit years count as a date (README limit); the account is hidden either way
    out = m("GB29 NWBK 6016 1331 9268 04 04.11.26").text
    assert out.startswith("<IBAN_1>")


def test_a_crlf_counts_as_two_line_breaks_and_a_date_after_it_stays():
    out = m("GB29 NWBK 6016 1331 9268 04\r\n\r\n11.11.2026").text
    assert out == "<IBAN_1>\r\n\r\n11.11.2026", ascii(out)


# ---------------------------------------------------------------------------------------------------------------- MINOR 5: VAT numbers (false hides, listed)
@pytest.mark.parametrize("text", ["VAT NL123456789B01", "VAT SE123456789001", "VAT NO123456789MVA", "VAT GB123456789012"])
def test_vat_numbers_longer_than_the_reference_limit_are_hidden_as_ibans_on_purpose(text):
    assert m(text).text == "VAT <IBAN_1>"  # a false hide, accepted and written in the README limits


# ---------------------------------------------------------------------------------------------------------------- MINOR 6: truncation
@pytest.mark.parametrize("cut", [2, 3, 4, 5, 6, 7, 8, 9])
def test_an_iban_cut_by_two_to_nine_characters_leaves_no_run_of_four(cut):
    full = "DE89 3704 0044 0532 0130 00"
    text = "Pay to " + full[:-cut]
    out = m(text).text
    left = re.sub(r"\D", "", plain(out))
    assert len(left) < 4, ascii(out)


def test_a_short_country_iban_cut_to_the_reference_limit_stays_visible():
    assert m("Ref NO86 0111 1794").text == "Ref NO86 0111 1794"  # 12 characters: a reference number by the one skip rule
    assert m("NO86 0111 1794 3").text == "<IBAN_1>"  # complete


# ---------------------------------------------------------------------------------------------------------------- walk limits
def test_a_short_account_before_an_amount_or_a_date_is_hidden_and_not_held_back():
    assert (
        m("GB29 NWBK 6016 1331 9268 0 9.00 EUR").text == "<IBAN_1> 9.00 EUR"
    )  # the finder pads the place with the amount: no residual copy
    assert m("Total GB29 NWBK 6016 1331 9268 0 04.11.2026").text == "Total <IBAN_1> 04.11.2026"


def test_at_most_two_bank_code_groups_belong_to_one_place():
    assert m("DE12 ABCD 1 EFGH 2 IJKL 3 MNOP 4").text == "<IBAN_1> IJKL 3 MNOP 4"


def test_reference_followed_by_a_word_and_a_number_or_by_another_reference_stays_two_things():
    assert m("VAT GB123456789 Date 02 Nov 2026").text == "VAT GB123456789 Date 02 Nov 2026"
    assert m("PO SO20261015001\nGB123456789").text == "PO SO20261015001\nGB123456789"


def test_a_tail_of_up_to_three_letters_completes_the_account_a_currency_code_up_to_three_does_not():
    assert m("NO29 1111 1111 ABC").text == "<IBAN_1>"
    assert m("IBAN: LU77 DVVU 2006 6156 3 USD 9.00").text.endswith("USD 9.00")


def test_a_bank_code_stuck_to_its_digits_by_a_zero_width_character_is_one_group():
    out = m("iban kz23:xgvk" + ZW + "67635504\n263 EUR 9.00").text
    assert out == "iban <IBAN_1> EUR 9.00", ascii(out)


def test_account_digits_that_look_like_the_start_of_a_date_do_not_end_the_walk():
    # "1970 04.11" would be a year, a month and a day, but ".2026" follows: it is account digits, and the real date after it stays
    assert m("GL;53" + EN + "FYJP\n  07342.1970 04.11.2026").text == "<IBAN_1> 04.11.2026"
    assert m("IBAN:BA48\n\n1474\n\n1915 04" + EN + "11" + EN + "2026").text == "IBAN:<IBAN_1> 04" + EN + "11" + EN + "2026"
    assert m("IBAN:VA03. 442\n 2095 02 9.00 EUR").text == "IBAN:<IBAN_1> 9.00 EUR"


def test_a_word_of_four_letters_after_a_code_is_no_bank_code_when_no_digits_follow_it():
    out = m("ES91 Late Fees 1234 5678 9012 3456").text
    assert out.startswith("ES91 Late Fees "), ascii(out)
    assert m("Item IT10 Pen 2 pcs 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1").text == "Item IT10 Pen 2 pcs 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1"


def test_the_country_code_and_check_digits_apart_with_a_bank_code_in_letters():
    assert m("GB 29 NWBK 6016 1331 9268 19").text == "<IBAN_1>"
    assert m("GB 29 NWBK 6016 1331 9268").text == "<IBAN_1>"


def test_an_amount_with_decimals_after_a_short_account_is_neither_swallowed_nor_a_hold_back():
    assert m("IBAN: so45vtom96148820545446 9.00 EUR").text == "IBAN: <IBAN_1> 9.00 EUR"
    assert m("GB29 NWBK 6016 1331 9268 9.00 EUR").text == "<IBAN_1> 9.00 EUR"


def test_a_word_of_four_letters_at_the_end_does_not_complete_the_account():
    assert m("Ref DE2026110412345678 Date 02 Nov 2026").text == "Ref <IBAN_1> Date 02 Nov 2026"
    assert m("Ref DE2026110412345678 Paid on 02 Nov 2026").text == "Ref <IBAN_1> Paid on 02 Nov 2026"
