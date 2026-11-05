"""Mask kernel, round 5 (part A and B of bb6762c): gaps are read from the FOLDED text, groups are walked from a first token of up to 8 characters, a long
candidate beyond a hidden place is hidden whole, the date test is strict, and the phone split handles every slash. The class-level property test is in
tests/test_mask_iban_fuzz.py; this file holds the named rows."""

from __future__ import annotations

import pytest
from test_mask_kernel import m

from intake import mask

NB, THIN, EN, ZW, NL = chr(0xA0), chr(0x2009), chr(0x2013), chr(0x200B), chr(10)
GROUPS = ["DE89", "3704", "0044", "0532", "0130", "01"]


def digits_left(text: str) -> str:
    return "".join(c for c in text if c.isdigit())


# ---------------------------------------------------------------------------------------------------------------- MAJOR 1: folded gaps
@pytest.mark.parametrize("sep", [NB, THIN, EN, ZW, ".", ",", ";", ":", "|", "/", "   ", " / ", " | "])
def test_a_mistyped_iban_with_any_separator_is_hidden_whole(sep):
    out = m("Pay to " + sep.join(GROUPS)).text
    assert out == "Pay to <IBAN_1>", ascii(out)


@pytest.mark.parametrize(
    "text",
    [
        "GB29 NWBK 6016 1331 / 9268 11",
        "GB29 NWBK 6016 1331, 9268 11",
        "GB29 NWBK 6016 1331; 9268 11",
        "GB29 NWBK 6016 1331: 9268 11",
        "GB29 NWBK 6016 1331 | 9268 11",
        "| GB29 NWBK | 6016 1331 | 9268 11 |",
        "GB29 NWBK 6016 1331   9268 11",
        "GB29 NWBK 6016 1331" + NL + "    9268 11",
        "> GB29 NWBK 6016 1331" + NL + "> 9268 11",
    ],
)
def test_a_mistyped_gb_iban_in_every_layout_is_hidden(text):
    out = m(text).text
    assert digits_left(out.replace("<IBAN_1>", "")) == "" and "NWBK" not in out and "<IBAN_1>" in out, ascii(out)


# ---------------------------------------------------------------------------------------------------------------- MAJOR 2: first token up to 8 characters, long last group
@pytest.mark.parametrize("text", ["Pay to GB29NWBK 6016 1331 9268 11", "NL91ABNA 0417 1643 01", "GB29 NWBK 60161331 9268190"])
def test_bank_statement_forms_and_long_last_groups_are_hidden_whole(text):
    out = m(text).text
    assert digits_left(out.replace("<IBAN_1>", "")) == "", ascii(out)


def test_a_candidate_beyond_a_long_hidden_place_is_hidden_whole_but_a_dated_reference_keeps_its_date():
    assert digits_left(m("GB29 NWBK 6016 1331 9268 190").text.replace("<IBAN_1>", "")) == ""
    out = m("Ref DE2026110412345678 04.11.2026").text
    assert "04.11.2026" in out and "DE2026" not in out


# ---------------------------------------------------------------------------------------------------------------- MINOR 3: strict date test
@pytest.mark.parametrize("text", ["GB29-NWBK-6016-13-31926819", "GB29 NWBK 60-16-1331926819"])
def test_a_group_that_looks_like_part_of_a_date_but_is_not_one_does_not_cut_the_iban(text):
    assert m(text).text == "<IBAN_1>"


def test_a_real_date_after_the_iban_stays():
    out = m("GB29 NWBK 6016 1331 9268 10 2026-11-04").text
    assert out.endswith("2026-11-04") and "NWBK" not in out


# ---------------------------------------------------------------------------------------------------------------- MINOR 7: false hides
@pytest.mark.parametrize(
    "text",
    [
        "NO12 Pay now for the new job",
        "FI12 Date",
        "Ticket DK50 Open",
    ],
)
def test_words_after_a_short_code_are_not_joined_into_an_iban(text):
    assert m(text).text == text


def test_two_adjacent_mistyped_ibans_stay_two_places_and_an_amount_after_one_stays():
    assert m("GB29 NWBK 6016 1331 9268 11 GB29 NWBK 6016 1331 9268 12").text == "<IBAN_1> <IBAN_2>"
    assert m("GB29 NWBK 6016 1331 9268 11 1,500.00").text == "<IBAN_1> 1,500.00"
    assert m("GB29 NWBK 6016 1331 9268 11 EUR 1,500.00").text.endswith("EUR 1,500.00")


# ---------------------------------------------------------------------------------------------------------------- MINOR 5, 6
def test_the_phone_split_handles_every_slash_a_date_and_a_short_extension():
    assert m("Tel: 020 7946 0958 / 04.11.2026").text == "Tel: <PHONE_1> / 04.11.2026"
    assert m("Tel 020 7946 0958 / 0959").text == "Tel <PHONE_1> / <PHONE_2>"
    out = m("Tel 020 7946 0958 / 020 7946 0959 / 020 7946 0960").text
    assert out == "Tel <PHONE_1> / <PHONE_2> / <PHONE_3>"


# ---------------------------------------------------------------------------------------------------------------- the false-hide list, extended
def test_the_thirty_line_list_extended_with_odd_separators_glued_codes_and_mistyped_ibans():
    stays = [
        "PO SO20261015001", "Ref IT20261104", "Order NL12345678", "Ref GB123456789", "Case SE12345678", "Meet at 12:30", "Item IE12345", "Code CY12AB",
        "Form DK12 A", "Page LT12.", "NO12 Pay now for the new job", "Ticket DK50 Open",
    ]  # fmt: skip
    goes = [
        "Pay to GB29" + NB + "NWBK" + NB + "6016" + NB + "1331" + NB + "9268" + NB + "11", "DE89.3704.0044.0532.0130.01", "| GB29 NWBK | 6016 1331 | 9268 11 |",
        "Pay to GB29NWBK 6016 1331 9268 11", "GB29NWBK60161331926811", "VAT: GB123456789012", "PO: PL2026110212345", "Ref DE2026110412345678",
    ]  # fmt: skip
    assert [t for t in stays if m(t).text != t] == []
    assert [t for t in goes if m(t).text == t] == []
    print(f"REFLINES5 {len(stays)} stay-visible lines and {len(goes)} must-hide lines, none wrong")


def test_the_walk_helpers_exist_with_their_documented_limits():
    assert mask.IBAN_REF_MAX_LEN == 13 and mask._IBAN_MIN_BEYOND == 16


def test_an_amount_ends_the_walk_and_a_stray_gap_does_not_leave_a_tail():
    out = m("GB29 NWBK 6016 1331 9268 EUR 1,500.00").text
    assert out.endswith("EUR 1,500.00") and "NWBK" not in out
    out = m("GB29 NWBK 6016 1331 9268 ~ 11").text  # a gap the walk does not accept: the finder's candidate still hides the rest
    assert digits_left(out.replace("<IBAN_1>", "")) == "", ascii(out)


def test_word_without_a_digit_after_a_long_place_is_padding_and_walk_stops_at_an_amount():
    assert m("Ref DE2026110412345678 Date 02 Nov 2026").text == "Ref <IBAN_1> Date 02 Nov 2026"
    text = "GB29 NWBK 6016 1331 9268 1,500.00"
    spans = mask.detect(text).spans
    start = text.index("1,500.00")
    assert not any(s.start <= start < s.end for s in spans)  # the amount is not part of the account
    assert any(s.end == text.index(" 1,500.00") for s in spans)


def test_the_date_test_is_strict_about_month_day_and_a_following_digit():
    ahead = mask._IBAN_DATE_AHEAD
    assert ahead.match("2026-11-05") and ahead.match("05.11.2026") and ahead.match("5/1/2026")
    assert (
        not ahead.match("2026-13-05") and not ahead.match("35.11.2026") and not ahead.match("2026-11-051") and not ahead.match("60-16-1331")
    )
