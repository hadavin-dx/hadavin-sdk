"""Round 6 of the invoice checks: one runnable attack (PoC) per finding of the two reviews of 8c13865 (C1-C5, A1-A6). Written to FAIL on 8c13865."""

import re
import time

import forgeries3 as f3
import pytest

from intake import invoicecheck as ic

SC = "Sort 20-00-00 Acct 12345678"
RLO, PDF = chr(0x202E), chr(0x202C)


def rec(**over):
    r = {
        "invoice_no": "INV-1",
        "supplier_name": "Acme  Widgets LTD",
        "currency": "USD",
        "lines": [{"description": "x", "qty": 2, "unit_cost_minor": 500, "amount_minor": 1000}],
        "adjustments": [{"label": "tax", "amount_minor": 100}],
        "total_minor": 1100,
    }
    r.update(over)
    return r


def flags(text, onfile=SC, **over):
    return ic.check(rec(**over), text, {"acme widgets ltd": onfile})


def codes(text, onfile=SC, **over):
    return [n.code for n in ic.look_notices(rec(**over), text, onfile)]


# ---------------------------------------------------------------- C1 / C2 identifier laundering
def test_c1_payment_verbs_not_in_the_lexicon_do_not_launder_the_invoice_number():
    r = rec(invoice_no="87654321")
    for t in (
        "Please pay into 87654321 quoting invoice number",
        "Kindly settle 87654321 quoting invoice number",
        "Send funds: 87654321 (invoice number below)",
        "Standing order / Invoice ref 87654321",
        "Please credit 87654321 today",
    ):
        assert ic.unexplained_numbers(r, t, SC) == ["87654321"], t
    assert ic.unexplained_numbers(r, "Invoice number 87654321", SC) == []
    assert ic.unexplained_numbers(r, "Please quote invoice number 87654321 when writing", SC) == []
    assert ic.unexplained_numbers(r, "Please quote invoice number 87654321 when you pay", SC) == [
        "87654321"
    ]  # round 7: a payment verb on the line


def test_c2_cross_line_run_is_judged_like_a_per_line_run():
    r = rec(invoice_no="876543210")
    # three pieces: only the line-break-as-space copy sees the run, and it must not borrow the invoice line's label
    assert ic.unexplained_numbers(r, "Invoice No 876543210\nPay to\n876\n543\n210", SC) == ["876543210"]
    assert ic.unexplained_numbers(r, "Invoice No 876543210", SC) == []
    assert ic.unexplained_numbers(rec(invoice_no="87654321"), "Invoice No 87654321\nPay to\n8765\n4321", SC) == ["87654321"]


@pytest.mark.parametrize("t", ["Account: 765 4321", "Account: 765-4321", "Acct 123 456", "Bank 765 432"])
def test_c3_spaced_short_accounts_are_candidates(t):
    # round 7 (decision 3): spaced or hyphenated 6-7 digit hits are the D12 notice `short_account_number`, never D10
    assert not ic.bank_detail_changed(t, SC)
    assert "short_account_number" in codes(t)


@pytest.mark.parametrize("t", ["Account 2026-001", "Account 2026 001"])
def test_c3_year_shaped_numbers_are_not(t):
    assert not ic.bank_detail_changed(t, SC)


# ---------------------------------------------------------------- C4 false D10 widening
@pytest.mark.parametrize(
    "t",
    [
        "Remit to: Acme, Mumbai 400001",
        "Remittance advice PO 123456",
        "Beneficiary PO Box 123456",
        "Payment details\nInvoice 4500123",
        "Account:\n765432",
    ],
)
def test_c4_postcodes_references_and_next_lines_are_not_rejected(t):
    assert not ic.bank_detail_changed(t, SC), t


def test_c4_record_numbers_on_their_own_lines_are_skipped_for_d10_but_not_after_a_payment_verb():
    assert "D10" not in flags("Payment details\nInvoice 4500123", invoice_no="4500123")
    assert flags("Payment by bank transfer, quote invoice 20260345", invoice_no="20260345") == [
        "D12"
    ]  # A5, round 7: never explained on a bank line, never a hard reject
    assert flags("Bank account 20260345 payable", invoice_no="20260345") == [
        "D12"
    ]  # round 7: the record's own number on a payment line is D12
    assert flags("Please pay into account 87654321 quoting invoice number", invoice_no="87654321") == [
        "D12"
    ]  # round 7: D12, never explained
    assert ic.bank_detail_changed("Sort code 123456", SC)  # strong keywords keep 6


# ---------------------------------------------------------------- C5
def test_c5_bidi_on_the_right_number_is_d12_and_on_a_wrong_one_d10():
    assert flags(f"Account No: {RLO}12345678{PDF}") == ["D12"]
    assert "D10" in flags(f"Account No: {RLO}87654321{PDF}")


def test_c5_check_failed_is_emitted_and_pinned(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(ic, "_components", boom)
    flg, notes = ic.check_reasons(rec(), "x", {"acme widgets ltd": SC})
    assert "D10" in flg and "check_failed" in [n.code for n in notes]


def test_c5_change_notice_regex_is_fast():
    for t in ("new bank details " * 20000, "bank details new " * 20000, "new " * 80000 + "bank", "bank details " * 30000):
        t0 = time.perf_counter()
        ic.look_notices(rec(), t, SC)
        assert time.perf_counter() - t0 < 6, t[:20]


def test_c5_documented_uncaught_classes_are_really_uncaught_and_catch_alls_say_so():
    assert flags("Thanks, as agreed. [image001.png]") == []
    assert flags("Ring 87 65 43 21") == []
    assert "payment_line_no_number" in codes("Beneficiary\n87\n65\n43\n21")
    assert "payment_line_no_number" in codes("UPI ID acme@okbank")  # alternative rails are never compared: always a person


# ---------------------------------------------------------------- A1 per-line payment-line notice
@pytest.mark.parametrize(
    "t",
    [
        SC + "\nAccount No:\n87\n65\n43\n21",
        SC + "\nPayPal: ap@evil.example",
        SC + "\nPayments now go to a different account, email us for details",
        SC + "\nPlease note: our new bank\ndetails are attached.",
        SC + "\nWe have changed banks. Ask us.",
        SC + "\nOur bank has changed, see the portal.",
    ],
)
def test_a1_a_second_payment_line_without_a_number_is_a_notice_even_with_the_genuine_line_present(t):
    assert flags(t) == ["D12"], t


def test_a1_clean_invoice_with_the_genuine_line_only_stays_clean():
    assert flags("Sort 20-00-00 Acct 12345678\nThank you") == []


# ---------------------------------------------------------------- A2 markdown tables
def test_a2_markdown_table_row_below_a_separator_row_is_read():
    t = "| Bank | Sort code | Account |\n|---|---|---|\n| Barclays | 12-34-56 | 87654321 |"
    assert ic.bank_detail_changed(t, SC)
    assert ic.bank_detail_changed("| Account |\n| --- |\n| 87654321 |", SC)


# ---------------------------------------------------------------- A3 lexicon and phones
@pytest.mark.parametrize(
    "lab",
    [
        "Transfer funds to", "Payment to", "Payments to", "Pay into", "Deposit to", "Payable to", "Numer konta", "Rachunek", "账号",
        "口座", "р/с", "M-Pesa", "Mobile money", "Credit to", "Send payment to", "Remit", "Ac count",
    ],
)  # fmt: skip
def test_a3_more_payment_instruction_words(lab):
    assert ic.bank_detail_changed(f"{lab}: 87654321", SC), lab


@pytest.mark.parametrize("t", ["Send payment to our mobile 0803 123 4567", "Mobile Money (M-Pesa): +254 712 345678"])
def test_a3_phone_shaped_numbers_after_a_payment_verb_are_not_silent(t):
    assert "D12" in flags(t)
    assert "payment_line_no_number" in codes(t) or ic.unexplained_numbers(rec(), t, SC)


def test_a3_reference_words_do_not_skip_a_short_run_after_a_bank_word():
    assert "short_account_number" in codes("Bank ref: 7654321")  # round 7: D12, no longer a hard reject
    assert not ic.bank_detail_changed("Bank VAT 123456789012", SC)


# ---------------------------------------------------------------- A4 slash dates
@pytest.mark.parametrize(
    "t",
    [
        "Payment by bank transfer by 15/12/2026",
        "Payment by bank transfer by 05/11/2026",
        "Payment by bank transfer by 5/11/2026",
        "Payment by bank transfer by 11/15/2026",
        "Payment by bank transfer by 15/12/26",
        "Bank details:\nDate: 05/11/2026",
    ],
)
def test_a4_slash_dates_are_not_candidates(t):
    assert not ic.bank_detail_changed(t, SC), t
    assert ic.unexplained_numbers(rec(), t, SC) == [], t


def test_a4_a_date_shaped_account_is_not_read_as_a_number_but_the_label_without_a_number_goes_to_a_person():
    assert not ic.bank_detail_changed("Account 12/05/2024", SC)
    assert "date_as_account" in codes("Account 12/05/2024")


# ---------------------------------------------------------------- A5 company names
@pytest.mark.parametrize("t", ["Swift Logistics Ltd, Company No 12345678", "Clearing House Services 20260345", "Swift Couriers 20260345"])
def test_a5_company_names_with_label_stems_are_not_labels(t):
    assert not ic.bank_detail_changed(t, SC), t


@pytest.mark.parametrize("t", ["SWIFT: 87654321", "Swift code 87654321", "Clearing 876543", "Clearing no 876543", "Clearing: 876543"])
def test_a5_real_labels_still_count(t):
    assert ic.bank_detail_changed(t, SC), t


# ---------------------------------------------------------------- A6 model-controlled explanations and the third list
def test_a6_fake_adjustment_equal_to_the_account_does_not_explain_a_payment_line():
    r = rec(adjustments=[{"label": "x", "amount_minor": 87654321}])
    assert ic.unexplained_numbers(r, "Wire transfer 87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "Adjustment 87654321", SC) == []  # a line with no payment word: still explained


def test_third_list_every_entry_meant_to_be_caught_is_caught():
    missed = [n for cls, n, must, got in f3.results(ic) if must and not got]
    assert missed == []
    for _cls, n, must, got in f3.results(ic):
        if not must:
            assert got == [], n  # a documented miss must really be a miss (this fails when the class gets fixed, then move it)


def test_a3_standing_order_is_a_payment_verb_but_not_a_label():
    # 13 of the 111 correct demo invoices say `Payment ref: standing order`; as a label it would send each to a person
    assert flags("Payment ref: standing order") == []
    assert ic.unexplained_numbers(rec(invoice_no="87654321"), "Standing order 87654321", SC) == ["87654321"]


def test_mutant_survivor_acct_no_is_a_strong_keyword_on_the_next_line_too():
    # strong keywords keep 6 digits on the line below; the bare class would need 8
    assert ic.bank_detail_changed("Acct No:\n765432", SC)
    assert ic.bank_detail_changed("Acc no:\n765432", SC)
    assert not ic.bank_detail_changed("Account:\n765432", SC)


@pytest.mark.parametrize(
    "label",
    [
        "Acct #",
        "Acc #",
        "A/C Nr",
        "A-C No",
        "Acct Nbr",
        "BSB",
        "BIC",
        "ABA",
        "BLZ",
        "CLABE",
        "Acct Nr",
        "IFSC",
        "Swift code",
        "SWIFT:",
        "Clearing no",
        "Routing",
        "Sort code",
    ],
)
def test_mutant_survivors_strong_labels_keep_six_digits_on_the_line_below(label):
    # a strong keyword reads 6 digits on the next line; the bare class (account, bank) needs 8 there
    assert ic.bank_detail_changed(f"{label}:\n765432", SC), label


def test_mutant_survivor_number_word_needs_its_right_boundary():
    assert not ic.bank_detail_changed("Account Notes:\n765432", SC)
    assert not ic.bank_detail_changed("Acct Nrs:\n765432", SC)


def test_mutant_survivor_look_alike_i_is_read_as_one():
    cands = ic._candidates(ic._f("Account No 8765432i"), ic._f(ic._camel("Account No 8765432i")))
    assert "87654321" in cands


# ---- survivors of the first full mutation run (each test names the mutant it kills)
LEXICON_SAMPLES = [
    "Beneficiary", "Beneficiario", "Beneficiaire", "Begunstigde", "Begunstigter", "Empfanger", "Payee", "Pay to", "Pay into", "Remit",
    "Remittance", "Payments to", "Transfer funds to", "Deposit to", "Payable to", "Credit to", "M-Pesa", "Mobile money", "Numer konta",
    "Rachunek", "\u8d26\u53f7", "\u53e3\u5ea7", "p/c", "Ac count", "Wire to", "Wire transfer", "Payment details", "UPI", "VPA", "PIX",
    "Zelle", "PayID", "PayPal", "Venmo", "CashApp", "Cuenta", "Compte", "Conto", "Conta", "Agencia", "Hesap", "RIB",
    "Datos bancarios", "Coordonnees bancaires", "Dati bancari", "Transfer to", "Bankrekeningnummer", "Zahlungsempf\u00e4nger",
    "Bitcoin", "BTC", "USDT", "USDC", "Ethereum", "ETH", "Wallet", "Crypto", "Binance", "Revolut", "Wise", "Payoneer",
    "Alipay", "WeChat", "Payment link", "Pay online", "\u0916\u093e\u0924\u093e",
    "\u062d\u0633\u0627\u0628", "\u5e10\u53f7", "\u8cec\u865f", "\u8d26\u6237", "\u5e33\u6236", "\u0421\u0447\u0451\u0442", "\u0421\u0447\u0435\u0442",
    "\uacc4\uc88c", "\u0e1a\u0e31\u0e0d\u0e0a\u0e35", "\u039b\u03bf\u03b3\u03b1\u03c1\u03b9\u03b1\u03c3\u03bc\u03bf\u03c2",
]  # fmt: skip


def test_lexicon_has_one_sample_per_entry_and_each_is_a_label():
    assert len(LEXICON_SAMPLES) == len(ic.PAYMENT_LEXICON)  # adding an entry forces a sample here
    for entry, sample in zip(ic.PAYMENT_LEXICON, LEXICON_SAMPLES, strict=True):
        assert ic.bank_detail_changed(f"{sample}: 87654321", SC), sample
        assert re.search("(?<![a-z])(?:" + ic._lex_entry(entry) + ")(?![a-z])", ic._f(sample)), (
            sample
        )  # the entry itself matches its sample


def test_survivor_each_payment_verb_makes_a_fake_adjustment_amount_unexplained():
    r = rec(adjustments=[{"label": "x", "amount_minor": 87654321}])
    for v in (
        "pay",
        "pays",
        "paid",
        "paying",
        "payment",
        "payments",
        "transfer",
        "transfers",
        "send",
        "sent",
        "deposit",
        "settle",
        "wire",
        "credit",
        "into",
        "standing",
    ):
        assert ic.unexplained_numbers(r, f"Please {v} 87654321", SC) == ["87654321"], v


def test_survivor_phone_with_a_payment_verb_is_not_silent_but_without_one_it_is():
    assert ic.unexplained_numbers(rec(), "Settle by phone: Tel 020 7946 0958", SC) != []
    assert ic.unexplained_numbers(rec(), "Call Tel 020 7946 0958", SC) == []


def test_survivor_phone_span_adds_a_run_only_when_no_run_covers_it():
    assert ic.unexplained_numbers(rec(), "Bank: Fax +44 (0) 20 7946 0958", SC) == ["79460958"]


def test_survivor_bic_and_ifsc_not_on_file_have_their_own_notice():
    assert "bic_not_on_file" in codes("IBAN GB82 WEST 1234 5698 7654 32\nBIC DEUTDEFF", "GB82 WEST 1234 5698 7654 32")
    assert "ifsc_not_on_file" in codes("Account 12345678 IFSC ICIC0009999")


@pytest.mark.parametrize(
    "t",
    [
        "Our bank details changed",
        "Our bank details have changed",
        "bank details are new",
        "Updated bank details",
        "The banking information was revised",
    ],
)
def test_survivor_change_notice_words(t):
    assert "change_notice" in codes(t), t


def test_survivor_check_failed_for_the_second_scan(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(ic, "_unexplained", boom)
    flg, notes = ic.check_reasons(rec(), "x", {"acme widgets ltd": SC})
    assert "D12" in flg and [(n.code, n.flag) for n in notes] == [("check_failed", "D12")]


def test_survivor_opaque_blob_limits():
    short = "Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qq9Rr"  # 29 characters, mixed, not text
    assert ic._opaque_blobs(short) == []
    assert ic._opaque_blobs("Ab1" * 11) != []  # 33 characters: cannot be decoded at all (incorrect padding)
    assert ic._opaque_blobs("abcdefghijklmnopqrstuvwxyzabcdefgh==") != []  # padded counts without mixed case


def test_survivor_quoted_printable_hides_the_label():
    assert ic.bank_detail_changed("=41ccount No 87654321", SC)
    assert not ic.bank_detail_changed("Rerouting 87654321", SC)  # routing is a label only as a word of its own


@pytest.mark.parametrize(
    "t", ["Payment by bank transfer by 5/1/2026", "Payment by bank transfer by 1/12/2026", "Payment by bank transfer by 31/1/26"]
)
def test_survivor_single_digit_slash_dates(t):
    assert not ic.bank_detail_changed(t, SC), t


def test_survivor_only_real_dates_are_masked():
    assert ic.bank_detail_changed("Account 45/67/2026", SC)


@pytest.mark.parametrize("t", ["Account 1999-001", "Account 1999 001", "Account 2026001"])
def test_survivor_year_start_rule(t):
    assert not ic.bank_detail_changed(t, SC)  # round 7: 6-7 digits are D12 whatever they start with
    assert "short_account_number" in codes(t)


@pytest.mark.parametrize("label", ["Account Nr", "Account Nbr", "Account Num", "Account Id", "Account #", "Accounts #"])
def test_survivor_account_number_words_are_strong_on_the_next_line(label):
    assert ic.bank_detail_changed(f"{label}:\n765432", SC), label


@pytest.mark.parametrize(
    ("letter", "digit"),
    [("o", "0"), ("i", "1"), ("l", "1"), ("s", "5"), ("b", "8"), ("z", "2"), ("q", "9"), ("t", "7"), ("a", "4"), ("e", "3")],
)
def test_survivor_every_look_alike_letter_gives_its_digit(letter, digit):
    text = f"Account No 8765432{letter}"
    cands = ic._candidates(ic._f(text), ic._f(ic._camel(text)))
    assert "8765432" + digit in cands, letter
    assert "87654326" in ic._candidates(ic._f("Account No 8765432g"), ic._f("Account No 8765432g"))  # g read as 6
    assert "87654329" in ic._candidates(ic._f("Account No 8765432g"), ic._f("Account No 8765432g"))  # and as 9


@pytest.mark.parametrize(("letter", "digit"), [("o", "0"), ("i", "1"), ("l", "1"), ("s", "5"), ("b", "8"), ("z", "2")])
def test_survivor_narrow_look_alikes_work_with_six_digits_where_the_wide_table_does_not_apply(letter, digit):
    text = f"Sort code 12345{letter}"
    assert "12345" + digit in ic._candidates(ic._f(text), ic._f(ic._camel(text))), letter


def test_survivor_percent_encoding_hides_the_label():
    assert ic.bank_detail_changed("%41ccount No 87654321", SC)


def test_survivor_every_direction_and_format_control_code_point_is_flagged():
    cps = [*range(0x202A, 0x202F), *range(0x2060, 0x2070), 0x200E, 0x200F, 0x061C]  # written out here, not read from the module
    assert len(cps) == 5 + 16 + 3
    for cp in cps:
        assert flags(f"Account No: 1234{chr(cp)}5678") == ["D12"], hex(cp)


def test_survivor_wide_look_alikes_each_have_their_own_digit():
    for letter, digit in (("g", "9"), ("g", "6"), ("q", "9"), ("t", "7"), ("a", "4"), ("e", "3")):
        text = f"Account No 8765432{letter}"
        assert "8765432" + digit in ic._candidates(ic._f(text), ic._f(text)), (letter, digit)


def test_survivor_check_reasons_returns_the_notices():
    flg, notes = ic.check_reasons(rec(), "Our bank details have changed", {"acme widgets ltd": SC})
    assert "D12" in flg and "change_notice" in [n.code for n in notes]


def test_survivor_bidi_notice_with_a_label_but_no_number():
    assert "bidi_control" in codes("Bank details attached\u200f")


def test_survivor_a_payment_line_next_to_a_good_one_is_not_excused_by_it():
    assert "payment_line_no_number" in codes("Account No: 12345678\nPayPal: ap@evil.example")
    assert "payment_line_no_number" not in codes("Account No: 12345678\nThank you")


@pytest.mark.parametrize(
    "t",
    [
        "Please use our different payment details",
        "Different remittance instructions attached",
        "Our bank has changed",
        "The banks have changed",
    ],
)
def test_survivor_more_change_phrases(t):
    assert "change_notice" in codes(t), t


def test_survivor_phone_span_run_for_a_payment_verb_without_a_bank_word():
    assert ic.unexplained_numbers(rec(), "Settle by Tel 876 54 3210", SC) == ["876543210"]


def test_survivor_id_explained_needs_a_seen_occurrence():
    assert ic._id_explained("87654321", ["nothing here"], {0}, frozenset({"87654321"})) is False
    assert ic._id_explained("87654321", ["invoice 87654321"], {0}, frozenset({"87654321"})) is True


def test_survivor_check_failed_of_the_first_scan_is_exactly_one_notice(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(ic, "_scan", boom)
    flg, notes = ic.check_reasons(rec(), "x", {"acme widgets ltd": SC})
    assert "D10" in flg and ("check_failed", "D10") in [(x.code, x.flag) for x in notes]


def test_survivor_bidi_notice_with_a_number_but_no_label():
    assert "bidi_control" in codes("Pay GB82 WEST 1234 5698 7654 32\u200f", "GB82 WEST 1234 5698 7654 32")


@pytest.mark.parametrize("t", ["Transfers go to another bank now", "Changed bank details attached"])
def test_survivor_other_change_phrases(t):
    assert "change_notice" in codes(t), t


def test_survivor_single_line_wrong_iban_is_not_reported_as_spanning_lines():
    assert "iban_spans_lines" not in codes("IBAN GB82 WEST 1234 5698 7654 33", "GB82 WEST 1234 5698 7654 32")


def test_survivor_a_label_followed_by_another_label_with_its_own_value_is_served():
    assert "payment_line_no_number" not in codes("Acct No:" + chr(10) + "PayPal 765432")
