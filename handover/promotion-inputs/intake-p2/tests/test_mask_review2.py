"""Mask kernel, review round 2 (reviews A and B of head a9a0267, errata 98 and 99). Every paper-attack input is run here."""

from __future__ import annotations

import base64

import pytest
from test_mask_kernel import KEY, held, m
from test_mask_review1 import BANK_LINES

from intake import invoicecheck, mask
from intake.selfcheck_codes import SelfCheckFailed

NBSP, EN, ZWJ = chr(0xA0), chr(0x2013), chr(0x200D)


# ---------------------------------------------------------------------------------------------------------------- A M1: copies the locator does not see
@pytest.mark.parametrize(
    "text",
    [
        "INV-12345678" + chr(10) + "Account No 1234&#53;678",  # the clean digits only as an id token
        "INV-12345678" + chr(10) + "Account No 12345678 and" + chr(10) + "Account No 1234&#53;678",  # clean copy beside the obfuscated one
        "Total 12345678.00" + chr(10) + "Account No 1234&#53;678",  # the clean digits only as an amount
    ],
)
def test_an_obfuscated_copy_is_never_excused_by_a_kept_occurrence(text):
    assert held(text) == "mask_residual"


def test_kept_places_and_hidden_places_leave_nothing_for_the_finder():
    out = m("INV-20261001 ref" + chr(10) + "Sort code 200000 total $200000.00")  # amounts and id tokens kept on purpose: no false hold-back
    assert "$200000.00" in out.text and "INV-20261001" in out.text


# ---------------------------------------------------------------------------------------------------------------- A M2: IBAN-shaped candidates
def test_a_mistyped_iban_of_the_right_length_is_still_hidden():
    out = m("Bank: NatWest GB29 NWBK 6016 1331 9268 10").text  # last digit transposed, no IBAN word
    assert "6016" not in out and "<IBAN_1>" in out


def test_short_references_are_left_alone_and_longer_ones_are_hidden():
    text = "PO SO20261015001" + chr(10) + "GB123456789"  # 13 and 11 characters
    assert m(text).text == text
    vat = "VAT: GB123456789012" + chr(10) + "Item   Qty   Unit cost   Amount"  # 14 characters: hidden, the next line stays
    assert "GB123456789012" not in m(vat).text and "Item   Qty" in m(vat).text


# ---------------------------------------------------------------------------------------------------------------- B MAJ-1: entity-encoded bank words
@pytest.mark.parametrize("line", ["&amp;#98;ank: ref-12345678", chr(0xFF06) + "#98;ank: ref-12345678", "&amp;amp;#97;ccount no 12345678"])
def test_the_stem_shortcut_never_skips_a_line_with_an_entity_or_a_non_ascii_character(line):
    assert invoicecheck.bank_word_in(line)
    assert mask._Lines(line).ctx == [True]  # the line is bank context


@pytest.mark.parametrize(
    "line", BANK_LINES + ["&amp;#98;ank: 12345678", chr(0xFF06) + "#98;ank: 12345678", "&amp;amp;#97;ccount no 12345678"]
)
def test_every_bank_word_line_is_context_whatever_the_encoding(line):
    assert mask._Lines(line).ctx == [invoicecheck.bank_word_in(line)]


@pytest.mark.parametrize("text", ["&amp;#98;ank: 12345678", chr(0xFF06) + "#98;ank: 12345678", "&amp;amp;#97;ccount no 12345678"])
def test_an_entity_encoded_bank_word_still_masks_the_number(text):
    assert "12345678" not in m(text).text


# ---------------------------------------------------------------------------------------------------------------- A1, A2: cards
@pytest.mark.parametrize(
    "text",
    [
        "card 4111" + NBSP + "1111" + NBSP + "1111" + NBSP + "1111",
        "card 4111" + EN + "1111" + EN + "1111" + EN + "1111",
        "card 4111  1111  1111  1111",
        "card 4111" + ZWJ + "1111" + ZWJ + "1111" + ZWJ + "1111",
        "Amex 3782" + NBSP + "822463" + NBSP + "10005",
        "Diners 3056 930902 5904",
        "Paid by card 4242424242424242",
        "visa card 4222222222222",  # 13 digits with a leading 4
        "credit card 5105105105102",  # 13 digits with a card word
    ],
)
def test_card_numbers_in_card_groupings_are_hidden_even_with_odd_spaces(text):
    out = m(text)
    assert out.counts["CARD"] == 1 and not any(c.isdigit() for c in out.text.replace("<CARD_1>", ""))


@pytest.mark.parametrize(
    "text",
    [
        "dates 2026-11-04 2026-12-04",
        "EAN 5901234123457 ok",  # 13 digits, no card word, no leading 4
        "sku 5901234123457",
        "ref 2026 1104 0012 345",  # not a card grouping
    ],
)
def test_ordinary_long_numbers_are_not_cards(text):
    assert m(text).text == text


# ---------------------------------------------------------------------------------------------------------------- A3, A4, A5: phones
@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("(555)123-4567 x", "123-4567"),
        ("Phone (landline): 020 7946 0958", "7946 0958"),
        ("call 1-800-555-0199", "555-0199"),
        ("fax 555-123-4567", "123-4567"),
    ],
)
def test_phone_formats_with_a_signal_are_hidden(text, value):
    assert value not in m(text).text


@pytest.mark.parametrize(
    "text",
    ["part 555-123-4567 bare", "Ref 555.123.4567", "qty 200 100 2000.00", "price +112500.00 end", "order 5551234567 shipped"],
)
def test_bare_numbers_without_a_phone_signal_stay_visible(text):
    assert m(text).text == text


def test_a_phone_number_stops_before_a_date():
    out = m("Tel 020 7946 0958 04/11/2026").text
    assert "04/11/2026" in out and "7946" not in out
    out = m("Mobile +44 20 7946 0958 2026-11-04").text
    assert "2026-11-04" in out and "7946" not in out


def test_no_phone_fragment_is_a_bare_plus_or_bracket():
    out = m("call +44 20 7946 0958")
    assert out.counts["PHONE"] == 1 and out.text == "call <PHONE_1>"  # the whole number is one mark, no sign left behind
    assert m("price +112500.00 end").spans == ()


# ---------------------------------------------------------------------------------------------------------------- A6: names
@pytest.mark.parametrize("text", ["Dear Shri Rao,", "Smt Rao wrote", "Mx Lee wrote", "Sri Kumar called"])
def test_indian_and_neutral_titles_are_name_contexts(text):
    out = m(text).text
    assert "Rao" not in out and "Lee" not in out and "Kumar" not in out


# ---------------------------------------------------------------------------------------------------------------- base64 blobs, gold hostile cases
def test_a_blob_next_to_the_clean_digits_is_hidden_whole():
    blob = base64.b64encode(b"Acct 87654321").decode()
    out = m("Remit to: BSB 012-345 Acct 12345678" + chr(10) + blob + chr(10) + "Item Qty").text
    assert blob not in out and "12345678" not in out and "87654321" not in out


def test_the_171_gold_hostile_blob_line_is_no_longer_a_hold_back():
    out = m("Remit to: BSB 012-345 Acct 12345678" + chr(10) + "QWNjdCA4NzY1NDMyMQ==" + chr(10) + "Item Qty Unit cost Amount")
    assert "QWNjdCA4" not in out.text


# ---------------------------------------------------------------------------------------------------------------- B minors
def test_check_model_text_of_a_non_masked_value_is_a_code():
    with pytest.raises(SelfCheckFailed):
        mask.check_model_text(None)  # type: ignore[arg-type]


def test_expected_errors_never_include_the_base_exception_class():
    assert Exception not in mask._EXPECTED_ERRORS and MemoryError not in mask._EXPECTED_ERRORS


def test_find_hidden_ignores_a_low_view_of_the_wrong_length():
    assert mask.find_hidden("xx JO@ACME.EXAMPLE.COM", "jo@acme.example.com", (), low="short")


def test_bank_check_outcome_for_a_detail_without_components():
    assert mask.bank_check_outcome("Acme Ltd" + chr(10) + "Account no 12345678", {"acme ltd": "x"})[0] == "no_details_on_file"


def test_fill_refuses_a_missing_value():
    from intake import phrases

    with pytest.raises(KeyError):
        phrases.fill("bank_changed", supplier="X", n=1)  # bank_words missing


def _core_secret_extra_examples() -> dict[str, str]:
    return {
        "cli_password": "tool --password hunter2hunter2 --user x",
        "cli_token": "tool --token abcdEFGH12345678 run",
        "json_password": '{"password": "hunter2hunter2", "user": "x"}',
        "query_token": "GET /api?token=abcdEFGH12345678&x=1",
        "curl_user": "curl -u admin:hunter2pass https://example.com/x",
        "session": "session_id=Zx9Qw3Lk8Vb2Nm5Hj7Gf4Dc1Sa6Rt0Py",
        "credential_quoted": "credential: 'hunter2hunter2'",
    }


@pytest.mark.parametrize("name", sorted(_core_secret_extra_examples()))
def test_more_core_secret_forms_pass_check_a2_when_masked(name):
    text = _core_secret_extra_examples()[name]
    out = m(text)
    if (
        out.counts["SECRET"] == 0
    ):  # the core rules do not mask this form (a later core PR): it must then pass through unchanged, never half-hidden
        assert out.text == text
        return
    mask.check_model_text(out)  # a hold-back here would be a false hold-back caused by the filler


def test_one_character_secret_on_long_lines_reaches_the_masked_cap_region():
    doc = "pwd='a'" + chr(10) + ("a " * 990 + chr(10)) * 3
    out = mask.mask(doc, KEY)
    assert out.counts["SECRET"] >= 1 and len(out.text) > 30000


def test_a_percent_encoded_run_that_spells_the_number_is_hidden_whole():  # the gold hostile cases h-162 and h-163
    out = m("Remit to: ZZ91TEST1234567890" + chr(10) + "Acct %38%37%36%35%34%33%32%31" + chr(10) + "Item Qty").text
    assert "%38" not in out and "87654321" not in out
    assert held("Acct " + "".join(f"{ord(c):02x}" for c in "Account number 12345678")) == "mask_residual"  # a hex form is still held back
