"""Mask kernel, review round 3 (reviews A and B of head 1c7f99b, erratum 100). Every paper-attack input is run here."""

from __future__ import annotations

import base64

import pytest
from test_mask_kernel import KEY, Doc, live, m
from test_mask_review1 import BANK_LINES, _best_cpu

from intake import invoicecheck, mask, phrases
from intake.selfcheck_codes import SelfCheckFailed

FW = chr(0xFF06)  # fullwidth ampersand
NL = chr(10)


def mk_iban(country: str, bban: str) -> str:
    n = int("".join(str(int(c, 36)) for c in bban + country + "00"))
    return f"{country}{98 - n % 97:02d}{bban}"


def mistype(iban: str) -> str:
    """The same IBAN with one digit before the last five characters changed (so the check digits no longer fit)."""
    i = len(iban) - 6
    return iban[:i] + ("1" if iban[i] != "1" else "2") + iban[i + 1 :]


def spaced(iban: str) -> str:
    return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))


# ---------------------------------------------------------------------------------------------------------------- A1: mistyped IBANs
@pytest.mark.parametrize(
    ("country", "bban"),
    [
        ("MT", "MALT011000012345MTLCAST001S"),
        ("MU", "BOMM0101101030300200000MUR"),
        ("SC", "SSCB11010000000000001497USD"),
        ("GB", "NWBK60161331926819"),
    ],
)
def test_a_mistyped_iban_is_hidden_without_the_word_iban(country, bban):
    good = mk_iban(country, bban)
    assert mask._iban_valid(good.lower())
    for text in (mistype(good), "Bank: " + spaced(mistype(good))):
        out = m(text).text
        assert "<IBAN_" in out or "<CARD_" in out, text  # hidden (a card-shaped group may take it first)
        assert not any(c.isdigit() for c in out.replace("<IBAN_1>", "").replace("<CARD_1>", "")), out
    assert m(good).text == "<IBAN_1>"


@pytest.mark.parametrize(
    ("text", "hidden_part", "kept_part"),
    [
        ("VAT: GB123456789012" + NL + "04/11/2026 date", "GB123456789012", "04/11/2026"),
        ("PO: PL2026110212345" + NL + "2026-11-04", "PL2026110212345", "2026-11-04"),
        ("Ref DE2026110412345678 04.11.2026", "DE2026110412345678", "04.11.2026"),
    ],
)
def test_an_iban_shaped_reference_is_hidden_and_the_date_beside_it_stays(text, hidden_part, kept_part):
    out = m(text).text
    assert hidden_part not in out and kept_part in out and "<IBAN_1>" in out


def test_a_short_reference_is_left_alone():
    assert m("PO SO20261015001").text == "PO SO20261015001"  # 13 characters, far from the country's length, no checksum, no IBAN word


def test_iban_places_and_the_one_skip_rule():
    text = "Pay GB29 NWBK 6016" + NL + "1331 9268 10 and SO20261015001"
    fp_ = mask._fold_list(text)
    places = mask._iban_places(text, fp_, mask._skeletons(text, fp_)[2], [])
    assert [p[2] for p in places] == ["gb29nwbk60161331926810", "so20261015001"]
    assert not mask._iban_reference("gb29nwbk60161331926810", False) and mask._iban_reference("so20261015001", False)
    assert not mask._iban_reference("so20261015001", True)  # an IBAN word anywhere switches the skip off
    assert not mask._iban_reference(
        "gb82west12345698765432", False
    )  # 22 characters, the full length of a GB IBAN: far over the limit of 13
    assert not mask._iban_reference("gb123456789012345", False)  # 17 characters: over the limit of 13, so it is hidden
    assert mask.IBAN_REF_MAX_LEN == 13


# ---------------------------------------------------------------------------------------------------------------- B1: the finder's own fold for lines with an entity
@pytest.mark.parametrize(
    "text",
    [
        "Account No" + NL + FW + "nbsp;" + NL + "INV-12345678",
        "Account No" + NL + "&#xFF06;nbsp;" + NL + "INV-12345678",
        "c" + FW + "#111;mpte: ref-12345678",
        "Account No" + NL + "&amp;nbsp;" + NL + "INV-12345678",
    ],
)
def test_a_blank_or_entity_encoded_line_is_read_the_way_the_finder_reads_it(text):
    assert "12345678" not in m(text).text


@pytest.mark.parametrize("text", [FW + "#49;2345678" + NL + "Account No", "Account No" + NL + FW + "#49;2345678"])
def test_an_entity_encoded_number_next_to_a_bank_line_is_hidden_or_held_never_sent(text):
    try:
        out = m(text).text
    except SelfCheckFailed as e:
        assert e.code == "mask_residual"
        return
    assert "2345678" not in out


def test_lines_ctx_equals_the_finders_context_on_a_grid():
    above = ["Account No", FW + "#98;ank:", "&amp;#98;ank:", "plain words"]
    middle = ["", "&nbsp;", FW + "nbsp;", "&#xFF06;nbsp;", "x", "   ", "&amp;nbsp;"]
    for a in above:
        for b in middle:
            text = a + NL + b + NL + "INV-12345678"
            finder = bool(invoicecheck.bank_detail_findings(text, ""))
            if finder:
                assert mask._Lines(text).ctx[2], (a, b)


@pytest.mark.parametrize("line", BANK_LINES + ["c" + FW + "#111;mpte: 12345678"])
def test_context_of_a_single_line_matches_bank_word_in(line):
    assert mask._Lines(line).ctx == [invoicecheck.bank_word_in(line) or bool(mask._LANG_WORD.search(invoicecheck.fold_text(line)))]


# ---------------------------------------------------------------------------------------------------------------- B2 (erratum 100a): runs hide the plain copies too
def test_a_base64_run_proves_the_number_and_every_plain_copy_is_hidden():
    blob = base64.b64encode(b"Account No 12345678").decode()
    for text in (
        "INV-12345678 ref" + NL + blob,
        "Please quote 12345678 on payment" + NL + blob,
        "ref 12345678 and 12345678" + NL + blob,
    ):
        out = m(text).text
        assert "12345678" not in out and blob not in out, text


def test_a_percent_run_proves_the_number_and_every_plain_copy_is_hidden():
    run = "".join(f"%{ord(c):02x}" for c in "12345678")
    for text in (
        "INV-12345678 ref" + NL + "Acct " + run,
        "Please quote 12345678" + NL + "Acct " + run,
        "Acct 12345678 and" + NL + "Acct " + run,
    ):
        out = m(text).text
        assert "12345678" not in out and "%31" not in out, text


def test_a_money_copy_of_a_proven_number_stays_visible():
    blob = base64.b64encode(b"Account No 12345678").decode()
    out = m("Total $12345678.00" + NL + "ref 12345678" + NL + blob).text
    assert "$12345678.00" in out and "ref 12345678" not in out


# ---------------------------------------------------------------------------------------------------------------- A minors
def _luhn_valid(prefix: str) -> str:
    for d in range(10):
        if mask._luhn(prefix + str(d)):
            return prefix + str(d)
    raise AssertionError


def test_a_luhn_valid_international_phone_number_is_a_phone_not_a_card():
    num = _luhn_valid("447700900123")
    assert mask._luhn(num)  # the input really passes the check, unlike the one used before
    for text in ("call +" + num, "call (+" + num + ")"):
        out = m(text)
        assert out.counts["CARD"] == 0 and out.counts["PHONE"] == 1, text


def test_a_second_phone_number_after_a_slash_is_its_own_number():
    out = m("Phone: 07700 900123 / 07700 900456").text
    assert "07700" not in out and out.count("<PHONE_") == 2


def test_a_weak_leading_one_is_no_phone_signal():
    assert m("x 1 250 100 2500 y").text == "x 1 250 100 2500 y"
    assert m("call 1-250-100-2500").counts["PHONE"] == 1


# ---------------------------------------------------------------------------------------------------------------- B minors
def test_the_prefix_levels_give_shorter_lists_for_longer_candidates():
    lines = []
    for i in range(40):  # 40 lines share 6 digits, 20 share 10, 10 share 16, 5 share 24
        a = "123456"
        b = "7890" if i < 20 else f"{i:04d}"
        c = "123456" if i < 10 else f"{i:06d}"
        d = "12345678" if i < 5 else f"{i:08d}"
        lines.append("bank " + a + b + c + d + f"{i:02d}")
    text = NL.join(lines)
    raw, _look, _alnum = mask._skeletons(text, mask._fold_list(text))
    probe = "123456" + "7890" + "123456" + "12345678" + "00"  # 26 digits
    counts = [len(raw.starts_for(probe[:n] + "0" * (n - len(probe[:n])))) for n in (6, 10, 16, 24)]
    assert counts[0] >= counts[1] >= counts[2] >= counts[3] >= 1 and counts[0] > counts[3], counts


def test_candidates_sharing_24_characters_stay_fast():
    lines = [f"bank 123456789012345678901234{i:04d}" for i in range(520)]  # every candidate shares its first 24 digits
    lines += [""] * 3
    text = NL.join(lines)[:19000]
    n = text.count("bank ")
    assert len(mask.detect(text).spans) == n  # every one of them was located and hidden
    cpu, wall = _best_cpu(lambda: mask.check_model_text(mask.mask(text, KEY)))
    assert cpu < 2.0 and wall < 10.0


def test_fill_with_no_bank_words_gives_a_whole_sentence():
    out = phrases.fill("bank_changed", supplier="Acme", n=1, bank_words=())
    assert "after the words" not in out and "(1 found)" in out and ")" in out and "<" not in out


def test_the_locator_acceptance_document_really_masks():
    text = NL.join(f"bank 123456{i:04d}" for i in range(1400))[:20000]
    assert len(mask.mask(text, KEY).spans) >= 1240  # the document has about 1,250 candidates and the mask succeeded


def test_body_check_still_passes_on_a_hidden_run():
    blob = base64.b64encode(b"Account No 12345678").decode()
    doc = "INV-12345678 ref" + NL + blob
    masked = m(doc)
    assert mask.BodyCheck(Doc(doc), masked, KEY)(live(masked.text)) is None
