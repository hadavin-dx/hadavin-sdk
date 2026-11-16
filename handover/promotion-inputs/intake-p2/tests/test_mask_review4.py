"""Mask kernel, review round 4 (part A and B of head 1b4dba0): IBAN-shaped places are found PER PLACE and hidden, with one skip rule for short
references. Every input is run both ways (a leak is a test that the value is not in ``Masked.text``; a reference that must stay is asserted unchanged)."""

from __future__ import annotations

import pytest
from test_mask_kernel import m
from test_mask_review3 import mistype, mk_iban, spaced

from intake import invoicecheck, mask, phrases
from intake.selfcheck_codes import SelfCheckFailed

NL = chr(10)
EN = chr(0x2013)


def digits_left(text: str) -> str:
    return "".join(c for c in text if c.isdigit())


# ---------------------------------------------------------------------------------------------------------------- A1-1: wrapped IBANs, per place
def test_a_mistyped_iban_across_a_line_break_is_hidden_without_the_word_iban():
    text = "Pay to GB29 NWBK 6016" + NL + "1331 9268 10"
    out = m(text).text
    assert digits_left(out.replace("<IBAN_1>", "")) == "" and "<IBAN_1>" in out


def test_a_wrapped_copy_does_not_excuse_the_clean_copy_of_the_same_iban():
    text = "Pay to GB29 NWBK 6016" + NL + "1331 9268 10" + NL + "also GB29NWBK60161331926810 please"
    out = m(text).text
    assert "NWBK" not in out and digits_left(out.replace("<IBAN_1>", "").replace("<IBAN_2>", "")) == ""


def test_the_clean_copy_alone_and_the_wrapped_copy_alone_are_both_hidden():
    assert m("GB29NWBK60161331926810").text == "<IBAN_1>"
    assert m("GB29 NWBK 6016" + NL + "1331 9268 10").text == "<IBAN_1>"
    assert m("GB29 NWBK 6016" + NL + NL + "1331 9268 10").text == "<IBAN_1>"  # a blank line in between


# ---------------------------------------------------------------------------------------------------------------- A1-2: groups of one or two digits
@pytest.mark.parametrize(
    "text", ["GB29-NWBK-60-16-13-31-92-68-10", "GB29 NWBK 60-16-13 31926810", "GB29 NWBK 6016 13 3192 6810", "GB29 NWBK 6016 1331 9268 10"]
)
def test_an_iban_written_in_odd_groups_is_hidden_whole(text):
    assert m(text).text == "<IBAN_1>"


# ---------------------------------------------------------------------------------------------------------------- A1-3: no availability regression
@pytest.mark.parametrize(
    "text",
    [
        "VAT GB123456789 Date 02 Nov 2026",
        "PO FR12345678901 Qty 55 Amt",
        "Ref NL12345678 Date 2026",
        "VAT DE123456789 Qty",
    ],
)
def test_a_short_reference_followed_by_words_is_left_alone_and_not_held_back(text):
    assert m(text).text == text


# ---------------------------------------------------------------------------------------------------------------- A1-4: one character short
def test_an_iban_that_is_one_character_short_or_long_is_hidden():
    good = "GB29NWBK60161331926810"
    for text in ("Pay to " + good[:-1] + ".", "Pay to " + good + "1.", "Pay to " + good[:-2] + ","):
        out = m(text).text
        assert "NWBK" not in out and out.startswith("Pay to <"), (
            text
        )  # hidden as an IBAN, or as a card where a digit grouping passes Luhn first


# ---------------------------------------------------------------------------------------------------------------- A1-5: every registry country, a letter tail
def test_a_mistyped_iban_of_every_registry_country_is_hidden_even_with_a_letter_tail():
    bad = []
    for cc, length in invoicecheck.IBAN_LENGTH.items():
        iban = cc + "29" + "1" * (length - 4 - 3) + "ABC"
        for text in (iban, spaced(iban), "Bank: " + iban + "."):
            out = m(text).text
            if "<IBAN_" not in out and "<CARD_" not in out:
                bad.append((cc, text))
    assert not bad, bad[:5]


def test_a_valid_iban_of_a_currency_tail_country_and_a_mistyped_one_are_both_hidden():
    for cc, bban in (("MU", "BOMM0101101030300200000MUR"), ("SC", "SSCB11010000000000001497USD"), ("MT", "MALT011000012345MTLCAST001S")):
        good = mk_iban(cc, bban)
        assert m(good).text == "<IBAN_1>" and m(mistype(good)).text == "<IBAN_1>"


# ---------------------------------------------------------------------------------------------------------------- the date stays, the reference goes
def test_a_date_beside_an_iban_shaped_reference_is_never_swallowed():
    for text, ref, date in (
        ("VAT: GB123456789012" + NL + "04/11/2026", "GB123456789012", "04/11/2026"),
        ("PO: PL2026110212345" + NL + "2026-11-04", "PL2026110212345", "2026-11-04"),
        ("Ref DE2026110412345678 04.11.2026", "DE2026110412345678", "04.11.2026"),
        ("GB29 NWBK 6016 1331 9268 10 04.11.2026", "NWBK", "04.11.2026"),
    ):
        out = m(text).text
        assert ref not in out and date in out, text


# ---------------------------------------------------------------------------------------------------------------- the one skip rule
def test_the_skip_rule_has_exactly_these_parts():
    ref = mask._iban_reference
    assert ref("so20261015001", False)  # short, far from its country's length, bad checksum, no IBAN word
    assert not ref("so20261015001", True)  # an IBAN word anywhere
    assert not ref("gb82west12345698765432", False)  # 22 characters: the full length of a GB IBAN
    assert not ref("gb123456789012", False)  # 14 characters: over the limit of 13
    assert not ref("gb29nwbk6016133192681", False)  # within two of the country's length
    assert not ref("gb29nwbk601613319268", False) and not ref("gb29nwbk6016133192681020", False)
    assert mask.IBAN_REF_MAX_LEN == 13


def test_extra_hides_over_a_set_of_thirty_made_up_reference_lines():
    lines = [  # (text, stays visible)
        ("PO SO20261015001", True),
        ("PO ES12345678", True),
        ("Ref AT123456789", True),
        ("Ref IT20261104", True),
        ("Order NL12345678", True),
        ("Inv BE20261104", True),
        ("Ref GB123456789", True),
        ("Customer FR12345678901", True),
        ("Ticket PL2026110212", True),
        ("Case SE12345678", True),
        ("VAT: GB123456789012", False),
        ("PO: PL2026110212345", False),
        ("Ref DE2026110412345678", False),
        ("Ref FR20261104123456", False),
        ("VAT: NL123456789B01", False),
        ("Order IT20261104123456", False),
        ("Acct ES2026110412345678", False),
        ("Ref GB2026110412345", False),
        ("Ref BE2026110412345", False),
        ("Ref AT202611041234567", False),
        ("Phone at12:30 today", True),
        ("Meet at 12:30", True),
        ("Tel no12345", True),
        ("Item IE12345", True),
        ("Code CY12AB", True),
        ("Form DK12 A", True),
        ("Type FI12", True),
        ("Id LV12ZZ", True),
        ("Plan SK12-B", True),
        ("Page LT12.", True),
    ]
    hidden_when_it_should_stay = [t for t, stay in lines if stay and m(t).text != t]
    visible_when_it_should_go = [t for t, stay in lines if not stay and m(t).text == t]
    print(
        f"REFLINES 30 made-up lines: extra hides {len(hidden_when_it_should_stay)}, visible by the 13-character rule {len(visible_when_it_should_go)}"
    )
    assert not hidden_when_it_should_stay and not visible_when_it_should_go


# ---------------------------------------------------------------------------------------------------------------- minors
@pytest.mark.parametrize(
    "text",
    [
        "Visa (4111" + EN + "1111" + EN + "1111" + EN + "1111)",
        "Amex (3782 822463 10005)",
        "+4111 1111 1111 1111",
        "Visa (4111" + chr(0xA0) + "1111" + chr(0xA0) + "1111" + chr(0xA0) + "1111)",
    ],
)
def test_a_card_number_after_a_bracket_or_a_plus_is_hidden_when_it_is_too_long_for_a_phone_number(text):
    out = m(text)
    assert out.counts["CARD"] == 1 and digits_left(out.text.replace("<CARD_1>", "")) == ""


def test_two_phone_numbers_with_a_slash_are_two_phone_marks():
    out = m("Tel: 020 7946 0958 / 020 7946 0959")
    assert out.text == "Tel: <PHONE_1> / <PHONE_2>"


# ---------------------------------------------------------------------------------------------------------------- B: grid, both directions
def test_context_grid_covers_numbers_above_entities_inside_a_line_and_non_ascii_words():
    fw = "".join(chr(ord(c) + 0xFEE0) for c in "Account")
    bank_lines = ["Account No", fw + " No", "&#65;ccount No", "&amp;#98;ank:"]
    others = ["", "&nbsp;", "12345678", "&#10;", "x &#10; y"]
    for bank in bank_lines:
        for o1 in others:
            for o2 in others:
                for order in ("below", "above"):
                    text = (o1 + NL + o2 + NL + bank) if order == "above" else (bank + NL + o1 + NL + o2)
                    finder = bool(invoicecheck.bank_detail_findings(text, ""))
                    if finder:  # the masker sees a bank context somewhere (the finder's own rule)
                        assert any(mask._Lines(text).ctx), (bank, o1, o2, order)
                    try:
                        out = m(text).text
                    except SelfCheckFailed:
                        continue  # held back: nothing is sent
                    assert not (finder and "12345678" in out), (bank, o1, o2, order)


# ---------------------------------------------------------------------------------------------------------------- B5
def test_fill_with_an_explicit_none_raises_like_a_missing_value():
    with pytest.raises(KeyError):
        phrases.fill("bank_changed", supplier="X", n=1, bank_words=None)
    with pytest.raises(KeyError):
        phrases.fill("bank_changed", supplier="X", n=None, bank_words=("a",))
    assert "(1 found)" in phrases.fill("bank_changed", supplier="X", n=1, bank_words=())


def test_a_valid_iban_with_an_odd_separator_is_hidden_whole():
    out = m("Pay GB82 WEST / 1234 5698 7654 32 now").text
    assert digits_left(out.replace("<IBAN_1>", "")) == "" and "WEST" not in out


def test_an_iban_after_the_word_iban_is_hidden_and_the_item_is_not_held_back():
    assert m("IBAN GB82WEST12345698765432").text == "IBAN <IBAN_1>"
    assert m("IBAN: GB82 WEST 1234 5698 7654 32").text == "IBAN: <IBAN_1>"


def test_a_plus_number_stops_at_a_slash_and_a_date_does_not_join_a_grouped_iban():
    out = m("+44 20 7946 0958 / 07700 900123").text
    assert out.startswith("<PHONE_1> / ") and out.endswith("07700 900123")
    out = m("GB29 NWBK 6016 1331 9268 04.11.2026").text
    assert "04.11.2026" in out and "NWBK" not in out
