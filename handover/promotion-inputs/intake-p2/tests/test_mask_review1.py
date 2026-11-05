"""Mask kernel, review round 1 (reviews A and B of head 5e1b0a9, errata 94 and 95). Every paper-attack input of review A is run here: a leak is a test that
the value is not in ``Masked.text``; a false hold-back is pinned by the code it gives and listed in the README limits."""

from __future__ import annotations

import base64
import json
import time

import pytest
from test_mask_kernel import KEY, START, Doc, held, live, m

from intake import coreredact, flags, invoicecheck, mask, phrases
from intake.selfcheck_codes import SelfCheckFailed

ESC = chr(27)


# ---------------------------------------------------------------------------------------------------------------- A M1: card numbers
@pytest.mark.parametrize(
    "text",
    [
        "Paid by card 4242424242424242",
        "Card: 4111111111111111",
        "Amex 3782 822463 10005",
        "card 4111-1111-1111-1111 ok",
        "Diners 30569309025904",
    ],
)
def test_card_numbers_are_hidden_contiguous_or_grouped(text):
    out = m(text)
    digits = "".join(c for c in text if c.isdigit())
    assert digits not in "".join(c for c in out.text if c.isdigit()) and out.counts["CARD"] == 1


def test_a_long_number_that_fails_the_luhn_check_is_not_a_card():
    assert "1234567812345678" in m("ref 1234567812345678 end").text


# ---------------------------------------------------------------------------------------------------------------- A M2: phone numbers
@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("Telephone: 020 7946 0958", "020 7946 0958"),
        ("call +44 (0) 20 7946 0958 now", "20 7946 0958"),
        ("(555) 123 4567 end", "123 4567"),
        ("(555) 123-4567 end", "123-4567"),
        ("+1 (555) 123 4567 x", "123 4567"),
        ("fax 555-123-4567", "123-4567"),
        ("1-800-555-0199 free", "555-0199"),
        ("cell 07700 900123", "900123"),
        ("whatsapp +49 151 23456789", "23456789"),
        ("Contact no 020 7946 0958", "7946 0958"),
    ],
)
def test_phone_numbers_in_common_formats_are_hidden(text, value):
    assert value not in m(text).text and m(text).counts["PHONE"] >= 1


def test_the_extra_phone_pass_is_this_modules_own_and_the_core_copy_is_unchanged():
    assert coreredact.find("(555) 123 4567 end") == []  # the core copy does not see it: the pass lives in mask.py
    assert not mask.detect("order 5551234567 shipped").spans  # contiguous digits without a signal are not a phone number
    assert "INV-555-123-4567" in m("ref INV-555-123-4567 ok").text  # an id token is not a phone number


# ---------------------------------------------------------------------------------------------------------------- A M3, M4: located per value and per copy
def test_r1b_needs_a_located_block_of_the_joined_whole():
    assert held("Sort code 345678\nAccount No 1234&#53;678") == "mask_residual"  # a single unlocated block never counts as joined


def test_an_obfuscated_second_copy_of_a_hidden_value_holds_the_item_back():
    assert held("Account No 12345678 pay\nlater Acct 1234&#53;678") == "mask_residual"


def test_a_base64_blob_with_a_bank_detail_is_hidden_whole_not_held_back():
    blob = base64.b64encode(b"Account No 12345678").decode()
    for text in (
        "INV-12345678 ref" + chr(10) + blob,
        "Acct 12345678 and" + chr(10) + blob,
        "Remit to: BSB 012-345 Acct 12345678" + chr(10) + "QWNjdCA4NzY1NDMyMQ==",
    ):
        out = m(text).text
        assert blob not in out and "QWNjdCA4NzY1NDMyMQ==" not in out and "<BANK_" in out, text
    assert (
        held("Account no %31%32%33%34%35%36%37%38 " + "".join(f"{ord(c):02x}" for c in "Account number 12345678")) == "mask_residual"
    )  # percent and hex stay held


# ---------------------------------------------------------------------------------------------------------------- A minors
def test_control_characters_other_than_white_space_hold_the_text_back():
    assert held("Account No 1234" + ESC + "[0m5678") == "mask_residual"
    assert held("plain" + chr(7) + "text") == "mask_residual"
    assert m("tab" + chr(9) + "and" + chr(11) + "vt\nfine").text  # tab, line breaks and form feeds are allowed


def test_a_name_is_found_as_a_whole_word_only():
    out = m("Dear Mark,\nMarketing services").text
    assert "Marketing" in out and "Mark," not in out


@pytest.mark.parametrize(
    "text",
    ["Contact name: Jane Doe", "Cardholder name: Jane Doe", "Mr Smith called", "Attn: Jane Doe", "Dear Dr Jane Doe", "Mrs Jane Doe wrote"],
)
def test_titled_and_labelled_names_are_hidden_like_dear(text):
    out = m(text).text
    assert "Jane" not in out and "Smith" not in out and out.count("<PERSON_1>") == 1


def test_a_titled_name_that_is_also_used_elsewhere_stays_visible():
    assert "Smith" in m("Mr Smith called Smith & Sons Ltd").text


def test_line_context_unescapes_html_like_the_finder():
    assert "12345678" not in m("Account No\n&nbsp;\nINV-12345678").text


@pytest.mark.parametrize(
    "text",
    [
        "Cuenta: 0049 1500 05 1234567892",
        "Numero de cuenta 0049150005",
        "Compte: 30004 00828 00010412345 76",
        "Conto corrente 000012345678",
        "Rekening 123456789",
        "Banco 12345678",
        "Banque 12345678 x",
        "RIB 12345678901",
    ],
)
def test_masking_only_language_bank_words_make_a_line_bank_context(text):
    out = m(text).text
    assert not any(c.isdigit() for c in out.replace("<BANK_1>", "")), out
    assert "<BANK_1>" in out


def test_the_language_words_do_not_change_the_d10_keyword_rule():
    assert not invoicecheck.bank_word_in("Cuenta: 0049 1500 05 1234567892")  # D10 is untouched (errata 94 b)


def test_a_language_word_inside_another_word_is_no_bank_word():
    assert "12345678" in m("Contour 12345678 here").text and "12345678" in m("Contoso 12345678").text


def test_only_the_marks_this_module_issues_count_as_mark_like_text():
    assert m("<INV_2026> ok").text == "<INV_2026> ok"
    assert held("<BANK_2> ok") == "mark_like_text" and held("< person _ 1 >") == "mark_like_text"


# ---------------------------------------------------------------------------------------------------------------- B m1: the filler matches no core secret rule
def _secret_examples() -> dict[str, str]:
    jwt = "eyJ" + "hbGciOiJIUzI1NiJ9" + ".eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    pem = "RSA PRIVATE" + " KEY"
    return {
        "privkey": "-----BEGIN " + pem + "-----\nMIIEowIBAAKCAQEA1234567890abcdef\n-----END " + pem + "-----",
        "jwt": "token " + jwt,
        "apikey": "key sk-" + "abcdefghijklmnopqrstuvwxyz123456",
        "aws": "AKIA" + "IOSFODNN7EXAMPLE",
        "gcp": "ya29." + "a0AfH6SMBabcdefghijklmnopqrstuvwxyz0123456789",
        "azure": "https://acct.blob.core.windows.net/c?sv=2020-08-04&ss=b&sig=abcdefghij1234567890ABCDEFGH%3D",
        "webhook": "https://hooks.slack.com/services/" + "T00000000/B00000000/" + "XXXXXXXXXXXXXXXXXXXXXXXX",
        "urlcred": "postgres://admin:hunter2pass@db.example.com/x",
        "bearer": "Authorization: Bearer abcdef1234567890abcdef",
        "basic": "Authorization: Basic dXNlcjpwYXNzd29yZA==",
        "password": "password=hunter2hunter2",
        "secret": "client_secret: s3cr3tValue123",
        "token": "api_token=abcdEFGH12345678",
    }


@pytest.mark.parametrize("name", sorted(_secret_examples()))
def test_check_a2_passes_on_a_masked_example_of_every_core_secret_rule(name):
    out = m(_secret_examples()[name])
    assert out.counts["SECRET"] >= 1
    mask.check_model_text(out)  # the filler word must not make the core rules fire again


def test_the_filler_is_short_and_not_a_bank_word():
    assert len(mask.NEUTRAL) <= 7 and not invoicecheck.bank_word_in(mask.NEUTRAL)


# ---------------------------------------------------------------------------------------------------------------- B M1: bank check with a keyword-less on-file string
def test_a_keyword_less_on_file_detail_still_gives_changed():
    sup = {"acme ltd": "20-00-00 12345678"}  # load_suppliers accepts this: no bank word needed
    out = mask.bank_check_outcome("Acme Ltd\nAccount no 87654321", sup)
    assert out[0] == "changed" and out[1] == "acme ltd"
    assert mask.bank_check_outcome("Acme Ltd\nAccount no 12345678", sup)[0] == "ok"


# ---------------------------------------------------------------------------------------------------------------- B M2: restore field rule, forged key, kept text
DOC = "Acme Ltd\nAccount no 12345678 sort code 20-00-00\nTotal $33.00\njo@acme.example.com Tel: +44 20 7946 0958 Dear Jane Doe"


def _fields(description="plain", label="plain", **top):
    f = {
        "invoice_no": "INV-1",
        "supplier_name": "Acme Ltd",
        "po_ref": None,
        "currency": "USD",
        "invoice_date": None,
        "lines": [{"description": description, "qty": 1, "unit_cost_minor": 3300, "amount_minor": 3300}],
        "adjustments": [{"label": label, "amount_minor": 0}],
        "total_minor": 3300,
    }
    f.update(top)
    return f


def test_the_field_rule_kind_part_refuses_a_bank_class_mark_even_in_a_free_text_field():
    masked = m(DOC)
    for mark in ("<BANK_1>", "<ROUTING_1>"):
        with pytest.raises(SelfCheckFailed) as e:
            mask.restore(_fields(description="see " + mark), masked, KEY, DOC)
        assert e.value.code == "hidden_value_in_field" and len(e.value.detail) == 3  # path, length, fingerprint only
        assert e.value.detail[0] == "lines[0].description" and len(e.value.detail[2]) == 8
        assert "12345678" not in repr(e.value.detail)
    for kind_mark in ("<CARD_1>", "<SECRET_1>", "<ID_1>", "<IBAN_1>"):
        assert kind_mark not in masked.text  # these kinds are not in this document: a forged mark


def test_the_free_text_paths_are_description_and_label_only():
    masked = m(DOC)
    ok = mask.restore(_fields(description="mail <EMAIL_1>", label="call <PHONE_1> ask <PERSON_1>"), masked, KEY, DOC)
    assert (
        ok.restored == 3
        and "jo@acme.example.com" in ok.fields["lines"][0]["description"]
        and "Jane Doe" in ok.fields["adjustments"][0]["label"]
    )
    for field, value in (("invoice_no", "<PHONE_1>"), ("supplier_name", "<PERSON_1>"), ("currency", "<EMAIL_1>"), ("po_ref", "<PHONE_1>")):
        with pytest.raises(SelfCheckFailed) as e:
            mask.restore(_fields(**{field: value}), masked, KEY, DOC)
        assert e.value.code == "hidden_value_in_field" and e.value.detail[0] == field


def test_a_forged_mark_in_a_dict_key_is_refused_with_a_keyed_fingerprint():
    masked = m(DOC)
    f = _fields()
    f["<EMAIL_1>"] = "x"
    with pytest.raises(SelfCheckFailed) as e:
        mask.restore(f, masked, KEY, DOC)
    assert e.value.code == "forged_mark" and e.value.detail == ("other", len("<EMAIL_1>"), mask.fp(KEY, "<EMAIL_1>"))
    g = _fields(description="x <EMAIL_9>")
    with pytest.raises(SelfCheckFailed) as e:
        mask.restore(g, masked, KEY, DOC)
    assert e.value.detail == ("lines[0].description", len("x <EMAIL_9>"), mask.fp(KEY, "x <EMAIL_9>"))


def test_restore_mismatch_carries_the_items_for_the_trace():
    masked = m(DOC)
    with pytest.raises(SelfCheckFailed) as e:
        mask.restore(_fields(description="mail <EMAIL_1>"), masked, bytes(32), DOC)
    assert e.value.code == "restore_mismatch" and isinstance(e.value.detail, tuple)
    assert e.value.detail and e.value.detail[0][0] == "<EMAIL_1>" and e.value.detail[0][3] == "MISMATCH"


def test_a_deeply_nested_answer_is_a_code_not_a_recursion_error():
    masked = m(DOC)
    deep: dict = {}
    cur = deep
    for _ in range(200):
        cur["x"] = {}
        cur = cur["x"]
    with pytest.raises(SelfCheckFailed):
        mask.restore(deep, masked, KEY, DOC)


def test_kept_text_is_found_in_both_json_forms_in_a_real_body():
    d = "Sort code 200000\nTotal " + chr(0xFF04) + "200000.00"  # a fullwidth dollar sign inside the kept amount
    masked = m(d)
    body = json.dumps({"messages": [{"role": "user", "content": START + masked.text + mask.BODY_END}]}).encode()
    assert mask.BodyCheck(Doc(d), masked, KEY)(body) is None


def test_last_code_is_reset_by_a_passing_call():
    masked = m(DOC)
    bc = mask.BodyCheck(Doc(DOC), masked, KEY)
    assert bc(live(masked.text + " extra")) == "body_unsafe" and bc.last_code == "mask_failed"
    assert bc(live(masked.text)) is None and bc.last_code is None


# ---------------------------------------------------------------------------------------------------------------- B minors
def test_the_two_catch_sites_chain_no_exception(monkeypatch):
    monkeypatch.setattr(mask.coreredact, "find", lambda t: (_ for _ in ()).throw(RuntimeError("PLANTED-VALUE-123")))
    for call in (lambda: mask.mask("Account no 12345678", KEY), lambda: mask.detect("x")):
        with pytest.raises(SelfCheckFailed) as e:
            call()
        assert e.value.__context__ is None and e.value.__cause__ is None
        assert "PLANTED" not in repr(e.value)


def test_named_spellings_of_a_lone_surrogate_do_not_raise():
    v = "ab" + chr(0xD800) + "cdefg"
    assert mask.named_spellings(v) and mask.find_hidden("clean text", v) == ()


def test_find_hidden_keeps_case_insensitive_matching_when_a_character_lowers_to_two():
    ss = chr(0xDF)
    hay = ss + " JO@ACME.EXAMPLE.COM"
    assert mask.find_hidden(hay, "jo@acme.example.com")
    assert (
        mask.find_hidden(hay, "jo@acme.example.com", ("JO@ACME.EXAMPLE.COM",)) == ()
    )  # positions stay exact, the kept occurrence contains the hit


def test_the_expected_error_tuple_covers_recursion_overflow_and_pattern_errors():
    for cls in (RecursionError, OverflowError, RuntimeError, re_error(), KeyError, IndexError):
        assert issubclass(cls, mask._EXPECTED_ERRORS)


def re_error():
    import re

    return re.error


def test_fill_replaces_in_one_pass_and_joins_a_tuple():
    out = phrases.fill("bank_changed", supplier="Acme <n> Ltd", n=2, bank_words=("account no", "iban"))
    assert "Acme <n> Ltd" in out and "(2 found, after the words account no, iban)" in out
    assert phrases.fill("bank_ok", supplier="X").startswith("Not a verification.")


def test_phrases_still_exposes_flags_and_selfcheck_sentences():
    assert flags.FLAGS["M01"].meaning in phrases.texts()


# ---------------------------------------------------------------------------------------------------------------- B m2: the timing gaps (CPU time, best of 5)
CPU_LIMIT_S = 2.0
WALL_GUARD_S = 10.0


def _best_cpu(fn):
    best, wall = float("inf"), 0.0
    for _ in range(5):
        c0, w0 = time.process_time(), time.perf_counter()
        fn()
        best = min(best, time.process_time() - c0)
        wall = max(wall, time.perf_counter() - w0)
    return best, wall


def test_a_one_character_secret_on_long_lines_just_under_the_masked_cap_is_fast():
    doc = "pwd='a'\n" + ("a " * 990 + "\n") * 3  # about 32,000 characters of marks after masking
    assert len(doc) < mask.MASK_MAX_DOC_CHARS

    def run():
        mask.check_model_text(mask.mask(doc, KEY))

    cpu, wall = _best_cpu(run)
    assert cpu < CPU_LIMIT_S and wall < WALL_GUARD_S


def test_body_check_and_restore_on_the_about_1250_candidate_document_are_fast():
    doc = "\n".join(f"bank 12345{i:03d}0" for i in range(1400))[:19000] + "\njo@acme.example.com"
    masked = m(doc)
    body = live(masked.text)
    bc = mask.BodyCheck(Doc(doc), masked, KEY)
    cpu, wall = _best_cpu(lambda: bc(body))
    assert bc(body) is None and cpu < CPU_LIMIT_S and wall < WALL_GUARD_S
    f = _fields(description="mail <EMAIL_1>")
    cpu, wall = _best_cpu(lambda: mask.restore(f, masked, KEY, doc))
    assert cpu < CPU_LIMIT_S and wall < WALL_GUARD_S


# ---------------------------------------------------------------------------------------------------------------- tests added after the first mutant run of this pass
def test_a_phone_number_the_core_only_half_finds_is_hidden_whole():
    out = m("mobile 0044 20 7946 0958").text
    assert "0958" not in out and "7946" not in out  # the core pattern stops early; the labelled pass takes the whole number


def test_a_single_unlocated_block_is_not_a_joined_whole():
    det = mask.detect("Sort code 345678\nAccount No 1234&#53;678")
    assert det.notes["joined_unlocated"] == 0 and det.unlocated  # R1, not R1b


def test_a_language_bank_word_line_is_bank_context_for_the_id_test():
    assert "12345678" not in m("Cuenta ref INV-12345678").text  # hidden: the line is bank context, so the id token is no excuse


def test_a_hit_inside_the_json_escaped_form_of_kept_text_is_dropped():
    kept = ("12" + chr(0xE9) + "34",)
    escaped = json.dumps(kept[0])[1:-1]  # 12é34
    assert escaped != kept[0]
    assert mask.find_hidden("x " + escaped + " y", "00e934", kept) == ()
    assert mask.find_hidden("x " + escaped + " y", "00e934", ()) != ()


def test_the_chained_exception_is_absent_for_an_unexpected_error_type(monkeypatch):
    def boom(_):
        raise OSError("PLANTED-VALUE-123")  # not in the expected tuple: it reaches the catch in mask()

    monkeypatch.setattr(mask.coreredact, "find", boom)
    with pytest.raises(SelfCheckFailed) as e:
        mask.mask("Account no 12345678", KEY)
    assert e.value.code == "mask_failed" and e.value.__context__ is None and e.value.__cause__ is None


def test_an_iban_shaped_place_is_hidden_unless_it_is_a_short_reference():  # mi6, measured on the 397 demo texts
    assert "GB123456789012" not in m("VAT: GB123456789012" + chr(10) + "Item   Qty   Unit cost   Amount").text
    assert "GB82WEST12345698765432" not in m("Pay GB82WEST12345698765432 today").text  # a valid IBAN needs no word
    assert mask._iban_valid("gb82west12345698765432") and not mask._iban_valid("gb123456789012itemqtyu")
    assert "SO20261015001" in m("PO SO20261015001").text  # too short and invalid: left alone


# ---------------------------------------------------------------------------------------------------------------- cost: the cheap stem test before bank_word_in
BANK_LINES = [
    "Sort Code 20-00-00", "routing 021000021", "SWIFT ABCDGB2L", "clearing 123", "KONTO 12345678", "Branch Code 12", "IBAN GB29", "Account No 1",
    "account num 1", "ACCOUNT NUMBER 1", "account nr 1", "account nbr 1", "account id 1", "account # 1", "acct no 1", "acc # 1", "a/c no 1", "ABA 1",
    "BIC X", "BSB 062000", "BLZ 37040044", "IFSC SBIN0000001", "CLABE 0123", "Bankside", "BankAccountNo 1", "Acct12345678", "A/C-12345678",
    "&#97;ccount no 1", "&#66;ank:", "Acc" + chr(0x200B) + "ount no 1", "".join(chr(ord(c) + 0xFEE0) for c in "IBAN"), "Sort" + chr(0x2010) + "Code 1",
]  # fmt: skip


@pytest.mark.parametrize("line", BANK_LINES)
def test_the_stem_test_never_misses_a_line_bank_word_in_accepts(line):
    if invoicecheck.bank_word_in(line):
        folded = (
            invoicecheck.fold_text(line) if ("&" in line or not line.isascii()) else mask._fold_str(line)
        )  # the fold the masker uses for this line
        assert any(st in folded for st in mask._BANK_STEMS), line


def test_the_second_finder_pass_is_skipped_only_for_check_a2():
    text = "Account No 12345678 pay\nlater Acct 1234&#53;678"
    assert mask.detect(text).unlocated and not mask.detect(text, residual=False).unlocated


# ---------------------------------------------------------------------------------------------------------------- errata 98 (d): the prefix index
def test_locator_cost_with_about_1250_distinct_candidates():  # the acceptance test of P6 (about 1,250 candidates fit in 20,000 characters), copied here
    text = "\n".join(f"bank 123456{i:04d}" for i in range(1400))[:20000]
    cpu, wall = _best_cpu(lambda: _mask_and_a2_quiet(text))
    assert cpu < CPU_LIMIT_S and wall < WALL_GUARD_S


def _mask_and_a2_quiet(text):
    mask.check_model_text(mask.mask(text, KEY))  # must succeed: a hold-back would make the timing meaningless


def test_candidates_sharing_a_prefix_do_not_share_one_list_of_positions():
    text = "\n".join(f"bank 123456{i:04d}" for i in range(1400))[:20000]
    raw, _look, _alnum = mask._skeletons(text, mask._fold_list(text))
    assert (
        len(raw.starts_for("1234560007")) == 1 and len(raw.starts_for("123456")) >= 1000
    )  # a 6-digit candidate still uses the short index
    assert len(raw.starts_for("12345600071234567890")) <= 1  # longer candidates use longer prefixes
