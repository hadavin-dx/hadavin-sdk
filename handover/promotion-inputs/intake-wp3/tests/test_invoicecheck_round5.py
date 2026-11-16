"""Round 5 of the invoice checks: one runnable attack (PoC) per review finding BL-intake-wp3-r4-001..011. Each test was written to FAIL on
0cc3638 (the module before this round) and does; `check` is used wherever the finding is about what a person finally sees."""

import base64
import time

import forgeries2 as fg
import pytest

from intake import invoicecheck as ic

SC, IBAN = fg.SC, fg.IBAN
SUP_SC = {"acme widgets ltd": SC}
SUP = {"acme widgets ltd": SC}
SUP_IBAN = {"acme widgets ltd": IBAN}


def rec(**over):
    return fg._rec(over)


RLO, PDF, RLM = fg.RLO, fg.PDF, fg.RLM


def flags(text, onfile=SC, **over):
    return ic.check(rec(**over), text, {"acme widgets ltd": onfile})


# ---------------------------------------------------------------- 001 bidi controls
def test_bidi_on_the_candidate_line_of_the_right_number_is_d12_and_with_a_wrong_number_d10():
    # round 6 (C5): the stored number equals the one on file -> a person looks (D12); a wrong number is D10 anyway
    assert flags(f"Account No: {RLO}12345678{PDF}") == ["D12"]
    assert flags(f"Acct: 1234{RLM}5678") == ["D12"]
    assert "D10" in flags(f"Account No: {RLO}87654321{PDF}")
    f = ic.bank_detail_findings(f"Account No: {RLO}87654321{PDF}", SC)
    assert [(x.candidate, x.kind) for x in f] == [("87654321", "number")]
    assert "<U+202E>" in f[0].raw and "87654321" in f[0].raw  # the person sees the raw line and the control, next to the folded number


def test_bidi_elsewhere_in_a_document_with_a_payment_line_is_d12_only():
    text = f"Account No 12345678\nThank you{RLM}"
    assert flags(text) == ["D12"]
    n = ic.look_notices(rec(), text, SC)
    assert [x.code for x in n] == ["bidi_control"] and "direction" in n[0].message


def test_bidi_without_any_payment_word_or_number_is_clean():
    assert flags(f"Thank you{RLM} for your order{RLO}") == []


@pytest.mark.parametrize(
    "cp", [0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0x200E, 0x200F, 0x061C, 0x2060, 0x206A]
)
def test_every_bidi_and_format_control_is_flagged(cp):
    assert flags(f"Account No: 1234{chr(cp)}5678") == ["D12"]
    assert "D10" in flags(f"Account No: 8765{chr(cp)}4321")


def test_bidi_inside_an_entity_or_a_decoded_form_is_flagged_too():
    assert flags("Account No: 1234&#x200F;5678") == ["D12"]
    assert "D12" in flags("Ref " + base64.b64encode(f"Account No 1234{RLM}5678".encode()).decode())


# ---------------------------------------------------------------- 002 model-extracted identifiers
def test_invoice_no_equal_to_the_account_does_not_silence_the_other_occurrences():
    r = rec(invoice_no="87654321")
    assert ic.unexplained_numbers(r, "INVOICE 87654321\nSend funds to 87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "INVOICE 87654321", SC) == []  # all occurrences on invoice lines: explained
    assert ic.unexplained_numbers(r, "INVOICE 87654321\nNew transfer reference 87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "INVOICE 87654321\nPlease pay invoice 87654321 to account 87654321", SC) == [
        "87654321"
    ]  # a bank word on the line
    assert ic.unexplained_numbers(rec(po_ref="87654321"), "Your PO: 87654321\nPay 87654321", SC) == ["87654321"]


# ---------------------------------------------------------------- 003 unlisted payee words and change notices
@pytest.mark.parametrize(
    "lab",
    [
        "Beneficiary",
        "Payee",
        "Pay to",
        "Remit to",
        "Wire to",
        "Payment details",
        "Cuenta",
        "Compte",
        "Conto",
        "Hesap no",
        "Rekening",
        "Conta",
    ],
)
def test_payment_instruction_words_make_a_line_a_label(lab):
    assert ic.bank_detail_changed(f"{lab}: 87654321", SC)
    assert not ic.bank_detail_changed(f"{lab}: 12345678", SC)  # the number on file is clean


@pytest.mark.parametrize(
    "text",
    [
        "Please note our bank details have changed. Request the new account from us.",
        "NEW PAYMENT INFORMATION - see attached picture",
        "Nos coordonnees bancaires ont change, veuillez demander le nouveau compte.",
        "Nuestros datos bancarios han cambiado, solicite la nueva cuenta.",
        "Updated banking details enclosed",
    ],
)
def test_change_notice_phrases_need_a_person(text):
    assert flags(text) == ["D12"]
    assert "change_notice" in [x.code for x in ic.look_notices(rec(), text, SC)]


def test_payment_line_without_a_readable_number_needs_a_person_but_a_plain_text_does_not():
    assert flags("Pay by PayPal: ap-payments@evil.example") == ["D12"]
    assert [x.code for x in ic.look_notices(rec(), "Payment details: see the attached picture", SC)] == ["payment_line_no_number"]
    assert flags("Thank you for your order. Net 30 days.") == []  # no payment word at all: not a flag
    assert flags("Account No 12345678") == []  # the number on file is present: clean


def test_new_notice_texts_have_a_code_and_plain_words():
    assert set(ic.NOTICE_MESSAGES) == {
        "bidi_control", "change_notice", "payment_line_no_number", "iban_spans_lines", "opaque_blob", "line_mismatch",
        "bic_not_on_file", "ifsc_not_on_file", "check_failed", "hidden_text", "date_as_account", "short_account_number",
        "id_on_payment_line", "unexplained_number", "text_too_large", "quoted_payment_details",
    }  # fmt: skip
    assert all(len(m) > 30 and m.endswith(".") for m in ic.NOTICE_MESSAGES.values())


# ---------------------------------------------------------------- 004 IBAN, sort code and account over several lines
def test_iban_over_four_lines_is_seen():
    t = "IBAN\nGB82 WEST\n1234 5698\n7654 33"
    assert "D12" in flags(t, IBAN) or "D10" in flags(t, IBAN)
    t2 = "Settle by transfer\nGB82 WEST\n1234 5698\n7654\n33"
    assert "iban_spans_lines" in [x.code for x in ic.look_notices(rec(), t2, IBAN)]
    assert flags("Settle by transfer\nGB82 WEST\n1234 5698\n7654\n32", IBAN) == []  # the right one, spread over lines: clean


def test_account_number_split_over_lines_is_one_d12_run():
    assert ic.unexplained_numbers(rec(), "Sort code 20-00-00\nAccount\n8765\n4321", SC) == [
        "87654321"
    ]  # two pieces: the old wrap rule joined these
    # three pieces: only the line-break-as-space copy joins them
    assert ic.unexplained_numbers(rec(), "Sort code 20-00-00\nAccount\n876\n543\n210", SC) == ["876543210"]


# ---------------------------------------------------------------- 005 one joiner rule for D12 and D10
@pytest.mark.parametrize("sep", ["/", "|", ":", "*", "]", "[", "(", ")", "+", "#", "\\"])
def test_d12_joins_every_non_alphanumeric_except_a_line_break(sep):
    assert ic.unexplained_numbers(rec(), f"Transfer 8765{sep}4321", SC) == ["87654321"]


# ---------------------------------------------------------------- 006 6 and 7 digit accounts
def test_six_and_seven_digit_accounts_under_a_bare_word():
    # round 7 (decision 3): 6-7 digits under a bare word are a D12 notice (`short_account_number`), D10 stays for 8+ digits
    assert not ic.bank_detail_changed("Account: 765432", SC) and not ic.bank_detail_changed("Acc: 7654321", SC)
    assert "short_account_number" in [n.code for n in ic.check_reasons(rec(), "Account: 765432", SUP_SC)[1]]
    assert not ic.bank_detail_changed("Account: 76543", SC)  # five digits: still below every threshold
    assert not ic.bank_detail_changed("Account 2026-001", SC)
    assert not ic.bank_detail_changed("Account 12345678", SC)


# ---------------------------------------------------------------- 007 IFSC and BIC
IND = fg.IND


def test_ifsc_is_compared_with_the_one_on_file():
    assert ic.bank_detail_changed("IFSC: ICIC0009999 acct 123456789012", IND)
    assert not ic.bank_detail_changed("IFSC: HDFC0001234 acct 123456789012", IND)
    assert not ic.bank_detail_changed("IFSC: HDFC 0001234 acct 123456789012", IND)  # a space inside is tolerated
    assert "ifsc" in [x.kind for x in ic.bank_detail_findings("IFSC ICIC0009999", IND)]


def test_ifsc_on_the_invoice_when_none_is_on_file_needs_a_person():
    assert "ifsc_not_on_file" in [x.code for x in ic.look_notices(rec(), "Account 12345678 IFSC ICIC0009999", SC)]
    assert "D12" in flags("Account 12345678 IFSC ICIC0009999")


def test_bic_with_spaces_and_bic_when_none_is_on_file():
    assert ic.bank_detail_changed("IBAN GB82 WEST 1234 5698 7654 32\nBIC DEUT DE FF", fg.BICF)
    assert not ic.bank_detail_changed("IBAN GB82 WEST 1234 5698 7654 32\nBIC WEST GB 2L", fg.BICF)
    assert flags("IBAN GB82 WEST 1234 5698 7654 32\nSWIFT: DEUTDEFF", IBAN) == ["D12"]
    assert ic._bics("bic deut de ff") == ["deutdeff"]


# ---------------------------------------------------------------- 008 encodings
def test_base64_with_undecodable_bytes_is_still_read():
    blob = base64.b64encode(b"Account No 87654321\xff\xfe\xfd").decode()
    assert ic.bank_detail_changed("Ref " + blob, SC)


def test_long_opaque_base64_blob_needs_a_person():
    blob = base64.b64encode(bytes((i * 37 + 11) % 256 for i in range(60))).decode()
    assert flags("Ref " + blob) == ["D12"]
    assert [x.code for x in ic.look_notices(rec(), "Ref " + blob, SC)] == ["opaque_blob"]
    assert flags("Ref " + base64.b64encode(b"Thank you for your order, see you soon!").decode()) == []  # readable text
    assert flags("internationalization-and-localization-department") == []  # a long hyphenated word is not a blob


def test_quoted_printable_and_unicode_escapes_are_decoded():
    assert ic.bank_detail_changed("Account No =38=37=36=35=34=33=32=31", SC)
    assert ic.bank_detail_changed("Account No " + "".join(f"\\u00{ord(c):02x}" for c in "87654321"), SC)


# ---------------------------------------------------------------- 009 phone-shaped numbers with short groups next to a bank word
PHONES = [
    "Bank: Tel 876 54 3210",
    "Bank: Tel 8765 43 2100",
    "Account: Tel 08 76 54 32 10",
    "Bank: Tel +87 65 43 21 0",
    "Bank: Tel (0) 8 7 6 5 4 3 2 1",
]


@pytest.mark.parametrize("text", PHONES)
def test_phone_shape_with_short_groups_next_to_a_bank_word_is_a_d12(text):
    assert ic.unexplained_numbers(rec(), text, SC) != []
    assert "D12" in flags(text)


def test_a_real_phone_without_a_bank_word_stays_silent():
    assert ic.unexplained_numbers(rec(), "Tel +44 20 7946 0958", SC) == []


# ---------------------------------------------------------------- 010 minors
def test_check_fails_closed_when_the_scan_breaks(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(ic, "_candidates_at", boom)
    assert ic.bank_detail_changed("Account No 12345678", SC) is True
    assert "D10" in ic.check(rec(), "Account No 12345678", SUP)
    monkeypatch.setattr(ic, "_components", boom)
    assert "D12" in ic.check(rec(), "x", SUP)


def test_entities_are_resolved_once_in_one_function_until_stable():
    assert ic._unescape("&amp;amp;#10;") == "\n" and ic._unescape("a &lt; b") == "a < b"
    assert ic.bank_detail_changed("BankAccountNo&amp;amp;#10;87654321", SC)  # the CamelCase pass still runs
    assert ic.bank_detail_changed("Account No &amp;#56;7654321", SC)


@pytest.mark.parametrize("text", ["Account No 8765432e", "Account No 8765q321", "Account No 8t654321", "Account No 8765432E"])
def test_wider_look_alike_letters_are_read_as_digits(text):
    assert ic.bank_detail_changed(text, SC)
    assert not ic.bank_detail_changed("Account No ab12", SC)


def test_hex_like_words_are_not_read_as_numbers():
    assert ic.unexplained_numbers(rec(), "24{U+00A0}cases{U+00A0}L100", SC) == []


def test_findings_carry_the_raw_line_next_to_the_folded_number():
    f = ic.bank_detail_findings("Pay\u00a0to\u200b:\u00a0\uff18\uff17654321", SC)
    assert f and f[0].candidate == "87654321" and "87654321" not in f[0].raw and "U+FF18" not in f[0].raw  # shown as written (fullwidth)
    assert ic.bank_detail_findings("Account No 87654321", SC)[0].raw == "Account No 87654321"


# ---------------------------------------------------------------- 011 the second forgery set
def test_every_forgery_of_the_second_set_designed_to_be_caught_is_caught():
    missed = [name for cls, name, must, got in fg.results(ic) if must and not got]
    assert missed == []


def test_the_classes_documented_as_not_caught_are_not_caught():
    assert [name for cls, name, must, got in fg.results(ic) if cls == "uncaught" and name == "picture-only" and got] == []


# ---------------------------------------------------------------- fuzz and ReDoS bounds
def _timed(text):
    t0 = time.perf_counter()
    ic.check(rec(), text, SUP)
    return time.perf_counter() - t0


def test_large_inputs_stay_bounded():
    """Linear, not quadratic: 4 times the input may take at most 12 times as long (plus a second), measured on this machine at this
    moment, so a busy machine does not fail it; one absolute ceiling of two minutes remains for the largest input."""
    makers = {
        "digits": lambda n: "9" * (n * 10),
        "iban": lambda n: "iban " * n,
        "mixed": lambda n: "a1b2c3d4" * n,
        "hex": lambda n: bytes(range(256)).hex() * (n // 64),
        "keyword lines": lambda n: "Account No 12 " * n,
    }
    for name, mk in makers.items():
        small = _timed(mk(5_000 if name != "hex" else 6_400))
        big = _timed(mk(20_000 if name != "hex" else 25_600))
        assert big <= 12 * small + 1, (name, small, big)
        assert big < 120, (name, big)
    assert _timed("9" * 1_000_000) < 120  # the one-megabyte case from the review


def test_look_alike_g_is_read_both_ways_and_each_letter_individually():
    def cands(t):
        return ic._candidates(ic._f(t), ic._f(ic._camel(t)))

    assert {"67654321", "97654321"} <= set(cands("Account No G7654321"))  # capital G looks like 6, small g like 9
    for letter, digit in (("q", "9"), ("t", "7"), ("a", "4"), ("e", "3"), ("E", "3"), ("T", "7")):
        assert "8765" + digit + "321" in cands(f"Account No 8765{letter}321"), letter
    assert "87654321" not in cands("Account No 8765z321z")  # sanity: a letter that maps to another digit does not give this number
    assert not any(len(c) >= 8 for c in cands("Account No ab12 cd34"))  # too few digits: nothing is read as a number


def test_a_line_count_mismatch_between_the_two_readings_is_a_flag_not_a_silent_fallback(monkeypatch):
    monkeypatch.setattr(ic, "_camel", lambda s: s + "\n\n")
    assert "line_mismatch" in [n.code for n in ic.look_notices(rec(), "Thank you", SC)]
    assert flags("Thank you") == ["D12"]


def test_notice_raw_text_is_shown_with_controls_made_visible():
    n = ic.look_notices(rec(), f"Account No 12345678\nPay{RLM} now", SC)
    assert n[0].code == "bidi_control" and "<U+200F>" in n[0].raw
