"""Round 7 of the invoice checks: one exact-input test per finding of the two round-6 reviews of 1968b21 (ledger rows 001-020) and the
owner-level decisions: bidi stays D12 with the raw line shown; the payment-line notice is served only by a value that belongs to THAT
label; 6-7 digit hits under bare words are D12 (D10 stays for 8+ digits, strong labels and checksum-valid codes); `standing order` is a
payment verb but not a label."""

import base64
import re
import time

import forgeries3 as f3
import pytest

from intake import invoicecheck as ic

SC = "Sort 20-00-00 Acct 12345678"
IBAN = "GB82 WEST 1234 5698 7654 32"
NL = chr(10)


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
    return [n.code for n in ic.check_reasons(rec(**over), text, {"acme widgets ltd": onfile})[1]]


def flagged(text, onfile=SC, **over):
    return bool(set(flags(text, onfile, **over)) & {"D10", "D12"})


# ---------------------------------------------------------------- B1 / C-M4: an identifier never explains a number on a payment line
@pytest.mark.parametrize(
    ("text", "over"),
    [
        ("Invoice No: 87654321" + NL + "Bank account, invoice no 87654321", {"invoice_no": "87654321"}),
        ("Invoice No: 87654321" + NL + "Pay into account invoice 87654321", {"invoice_no": "87654321"}),
        ("Invoice No: 87654321" + NL + "Remit to the order of PO 87654321", {"invoice_no": "87654321", "po_ref": "87654321"}),
        ("Bank account / Order 87654321", {"po_ref": "87654321"}),
        ("Payment by bank transfer, quote invoice 20260345", {"invoice_no": "20260345"}),
    ],
)
def test_b1_identifier_equal_to_the_account_never_explains_a_payment_line(text, over):
    f = flags(text, **over)
    assert "D12" in f or "D10" in f, text
    assert "D10" not in f or "D12" in f
    assert flags(text.replace("87654321", "12345678").replace("20260345", "12345678"), **over) in (
        [],
        ["D12"],
    )  # the number on file is fine


def test_b1_identifier_still_explains_a_label_free_line():
    r = rec(invoice_no="87654321")
    assert ic.unexplained_numbers(r, "Invoice No: 87654321", SC) == []
    assert ic.unexplained_numbers(r, "Invoice No: 87654321" + NL + "Bank account, invoice no 87654321", SC) == ["87654321"]


# ---------------------------------------------------------------- B2 hidden or split by markup
@pytest.mark.parametrize(
    "t",
    [
        "Account number 8765<i></i>4321",
        'Account number 8765<span style="display:none">x</span>4321',
        "Account number 8<b>7</b>6<b>5</b>4321",
        "Account number 8765<!-- a comment -->4321",
        "Account number 8765&nbsp;4321",
        'Account number 8765<span style="font-size:0">9</span>4321',
        "Account number 8765<br>4321",
    ],
)
def test_b2_markup_cannot_split_a_number(t):
    assert ic.bank_detail_changed(t, SC), t


def test_b2_hidden_elements_are_a_notice_and_the_visible_text_is_scanned():
    t = 'Account number 8765<span style="display:none">x</span>4321'
    assert "hidden_text" in codes(t)
    assert "hidden_text" in codes("Pay <div hidden>secret</div> now")
    assert "hidden_text" in codes('<p style="visibility:hidden">Account 12345678</p>')
    assert "hidden_text" not in codes("<p>Thank you</p>")


# ---------------------------------------------------------------- B3 look-alike separators
@pytest.mark.parametrize("sep", ["ǀ", "ǁ", "ǂ", "ǃ", "׀", "∣"])
def test_b3_letter_look_alike_of_a_separator_joins_digit_blocks(sep):
    assert ic.bank_detail_changed(f"Account 8765 {sep} 4321", SC), hex(ord(sep))
    assert ic.unexplained_numbers(rec(), f"Ref 8765 {sep} 4321", SC) == ["87654321"], hex(ord(sep))


# ---------------------------------------------------------------- M1 / C-M7 served only by the value of that label
def test_m1_cells_one_per_line_after_a_label_with_a_genuine_sort_code_on_the_line():
    t = "Sort code 20-40-60 Account number" + NL + "87" + NL + "65" + NL + "43" + NL + "21"
    assert "payment_line_no_number" in codes(t) and "D12" in flags(t)


def test_m1_honest_layouts_are_not_flagged():
    assert flags("Bank: Barclays" + NL + "Sort code 20-00-00" + NL + "Account 12345678") == []
    assert flags("Payment by bank transfer by 30 days") == []
    assert flags("Sort 20-00-00 Acct 12345678" + NL + "Thank you") == []


def test_m1_a_label_with_a_value_further_down_within_three_lines_is_served():
    assert flags("Account number" + NL + NL + "Branch: Leeds" + NL + "12345678") == []


# ---------------------------------------------------------------- C-M1 date-shaped account next to a genuine sort code
@pytest.mark.parametrize("val", ["12/05/2024", "12.05.2024", "2024-05-12", "5/12/2024"])
def test_cm1_a_date_shaped_value_after_a_label_is_a_notice(val):
    t = "Sort 12-34-56 Acct " + val
    f = flags(t, "Sort 12-34-56 Acct 12345678")
    assert "D12" in f and "date_as_account" in codes(t, "Sort 12-34-56 Acct 12345678"), val


def test_cm1_a_date_in_prose_next_to_the_word_bank_is_still_fine():
    assert flags("Payment by bank transfer by 15/12/2026") == []


# ---------------------------------------------------------------- C-M2 / M8 grounded amount and a label on the previous line
def test_cm2_amount_does_not_launder_a_number_after_a_label_on_the_previous_line():
    r = rec(total_minor=87654321)
    assert ic.unexplained_numbers(r, "Please send funds to:" + NL + "87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "Send funds to" + NL + "8765" + NL + "4321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "Total due 87654321", SC) == []
    assert ic.unexplained_numbers(r, "Total payable 87654321", SC) == []  # C-m6: `payable` is not a payment verb on its own


# ---------------------------------------------------------------- M2 labels in other languages
LANG = [
    "खाता संख्या: 87654321",
    "رقم الحساب: ٨٧٦٥٤٣٢١",
    "账号: 87654321",
    "帐号: 87654321",
    "賬號: 87654321",
    "Счёт: 87654321",
    "р/с 87654321",
    "Bankrekeningnummer: 87654321",
    "Rekeningnummer 87654321",
    "계좌: 87654321",
    "บัญชี 87654321",
    "Kontonummer 87654321",
    "Número de cuenta 87654321",
    "Numéro de compte 87654321",
    "Número da conta 87654321",
    "Numero di conto 87654321",
    "Hesap numarası 87654321",
    "Λογαριασμός: 87654321",
]  # fmt: skip


@pytest.mark.parametrize("t", LANG)
def test_m2_account_labels_in_other_languages_give_d10_for_a_different_number(t):
    assert ic.bank_detail_changed(t, SC), ascii(t)


def test_m2_the_number_on_file_in_another_language_is_clean():
    assert not ic.bank_detail_changed("账号: 12345678", SC)
    assert not ic.bank_detail_changed("Rekeningnummer 12345678", SC)


# ---------------------------------------------------------------- M3 / C-M6 6-7 digit accounts are D12, 8+ and strong labels D10
@pytest.mark.parametrize(
    "t",
    [
        "Beneficiary account:" + NL + "1234567",
        "Bank: Westpac" + NL + "1234567",
        "Remit to: 1234567",
        "Account: 765432",
        "Acc: 7654321",
        "Account: 2026 45",
        "Bank ref 123456",
    ],
)
def test_m3_short_account_under_a_bare_label_is_d12_not_d10(t):
    f = flags(t)
    assert "D12" in f and "D10" not in f, (t, f)
    assert not ic.bank_detail_changed(t, SC)


@pytest.mark.parametrize("t", ["Pay by bank transfer, ref 4500123", "Bank: HSBC  PO 123456"])
def test_m3_honest_phrases_are_never_a_hard_reject(t):
    assert "D10" not in flags(t)


def test_m3_strong_labels_and_eight_digits_stay_d10():
    assert "D10" in flags("Sort code 123456")
    assert "D10" in flags("Account: 87654321")
    assert "D10" in flags("Beneficiary: 87654321")


# ---------------------------------------------------------------- M4 / M5 MIME
def test_m4_base64_split_across_a_wrap_boundary_is_rejoined():
    data = b"x" * (57 - len(b"Account No 876")) + b"Account No 87654321 thanks"
    wrapped = base64.encodebytes(data).decode()
    assert NL in wrapped.strip()
    assert ic.bank_detail_changed("Ref" + NL + wrapped, SC)


def test_m5_quoted_printable_soft_breaks_are_removed_even_without_other_escapes():
    assert ic.bank_detail_changed("Account No: 87=" + NL + "65=" + NL + "43=" + NL + "21", SC)
    assert ic.bank_detail_changed("Account No: 87=" + chr(13) + chr(10) + "654321", SC)


# ---------------------------------------------------------------- M6 digit forms
def test_m6_dingbat_and_cjk_digits_are_digits():
    dingbat = "".join(chr(c) for c in (0x277D, 0x277C, 0x277B, 0x277A, 0x2779, 0x2778, 0x2777, 0x2776))
    assert ic.bank_detail_changed("Account No " + dingbat, SC)
    assert ic.bank_detail_changed("Account No 八七六五四三二一", SC)
    assert ic._f("〇零一二") == "0012" or ic._f("〇零一二") == "0012"
    assert flags("一个月内付款") == []  # ordinary Chinese prose is not turned into numbers
    assert ic._f(chr(0x2780) + chr(0x2789)) == "110"


# ---------------------------------------------------------------- M7 the D12 reason
def test_m7_unexplained_number_is_a_notice_with_the_digits_and_the_raw_line():
    flg, notes = ic.check_reasons(rec(), "Thanks" + NL + "Reference 87654321 please", {"acme widgets ltd": SC})
    n = [x for x in notes if x.code == "unexplained_number"]
    assert flg == ["D12"] and len(n) == 1 and n[0].detail == "87654321" and n[0].raw == "Reference 87654321 please"
    assert "number" in n[0].message


def test_decision1_raw_lines_are_never_trimmed():
    line = "Account No 12345678 " + "x" * 400 + chr(0x202E)
    n = ic.check_reasons(rec(), line, {"acme widgets ltd": SC})[1]
    b = [x for x in n if x.code == "bidi_control"][0]
    assert b.raw.endswith("<U+202E>") and len(b.raw) > 400
    f = ic.bank_detail_findings("Account No 87654321 " + "y" * 400 + chr(0x202E), SC)
    assert f[0].raw.endswith("<U+202E>") and len(f[0].raw) > 400


# ---------------------------------------------------------------- C-M3 rails without digits
@pytest.mark.parametrize(
    "t",
    [
        "Pay in USDT to wallet 0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        "Bitcoin address bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "Revolut: @acme", "Wise transfer details attached", "Payoneer ID acme", "Alipay: acme@example.com", "WeChat Pay acme",
        "Payment link https://pay.example/x", "Pay online at the portal", "Zahlungsempfänger: Acme GmbH",
    ],
)  # fmt: skip
def test_cm3_rails_without_digits_need_a_person(t):
    assert flags(t) == ["D12"], t


# ---------------------------------------------------------------- minors
def test_cm2_text_over_the_limit_is_refused_with_a_closed_code_not_scanned():
    t0 = time.perf_counter()
    flg, notes = ic.check_reasons(rec(), "9" * (ic.MAX_TEXT_CHARS + 1), {"acme widgets ltd": SC})
    assert time.perf_counter() - t0 < 3
    assert flg == ["D12"] and [n.code for n in notes] == ["text_too_large"]


def test_cm3_label_driven_entries_of_the_third_list_have_the_right_class():
    res = {n: got for cls, n, must, got in f3.results(ic)}
    for n, got in res.items():
        if n.startswith("label-") and n not in ("label-m-pesa", "label-standing-order"):
            assert "D10" in got, (n, got)


def test_cm4_unexplained_numbers_without_the_bank_class_still_work():
    assert ic.unexplained_numbers(rec(), "Please pay into 87654321 today", SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Please pay into 12345678 today", SC) == []


def test_cm5_transfer_to_is_a_label_and_two_digit_groups_count_on_a_verb_line():
    assert ic.bank_detail_changed("Transfer to: 87654321", SC)
    assert ic.bank_detail_changed("Transfer to 87 65 43 21", SC)
    assert ic.unexplained_numbers(rec(), "Please send 87 65 43 21", SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Qty 87 65 43 21", SC) == []


def test_cm1_look_alike_mapping_layers():
    assert ic._f("ʀ") == "r" and ic._f("ь") == "b"


def test_adv_m1_uk_sort_code_and_account_against_an_iban_only_record():
    onf = "GB29 NWBK 6016 1331 9268 19"
    assert not ic.bank_detail_changed("Sort code 60-16-13 Account 31926819", onf)
    assert ic.bank_detail_changed("Sort code 60-16-13 Account 31926810", onf)


def test_adv_m3_a_comma_ends_a_phone_span():
    # the phone span ends at the comma, so the run that continues past it is not silent (it is one run: both numbers)
    assert ic.unexplained_numbers(rec(), "Tel: +44 20 7946 0958, 87654321", SC) == ["7946095887654321"]


def test_adv_m4_quoted_older_message_with_payment_details_is_a_notice():
    assert "quoted_payment_details" in codes("Thanks" + NL + "> Account No 12345678")
    assert "quoted_payment_details" not in codes("Thanks" + NL + "Account No 12345678")


def test_tables_each_entry_is_mapped_by_its_layer():
    """Proof for the mutants the runner calls unobservable: every table entry gives its documented result through `_f`."""
    from intake import confusables_data as cd  # noqa: PLC0415

    for cp, target in cd.CONFUSABLES.items():
        c = chr(cp)
        import unicodedata  # noqa: PLC0415

        if unicodedata.normalize("NFKD", c) == c:
            expected = "|" if cp in ic._SEPLIKE else "i" if cp in ic._I_LIKE else target
            if unicodedata.category(c) == "Nd":
                expected = str(unicodedata.decimal(c))  # digits become ASCII before the confusables
            assert ic._f(c) == expected, hex(cp)
    for cp in ic._DASHES:
        assert ic._f("1" + chr(cp) + "2") == "1-2", hex(cp)
    for cp in ic._DELETE:
        assert ic._f("a" + chr(cp) + "b") == "ab", hex(cp)


def test_large_inputs_have_a_growth_bound():
    def timed(text):
        t0 = time.perf_counter()
        ic.check(rec(), text, {"acme widgets ltd": SC})
        return time.perf_counter() - t0

    for mk in (lambda n: "9" * (n * 10), lambda n: "iban " * n, lambda n: "<b>7</b> " * n):
        small, big = timed(mk(4000)), timed(mk(16000))
        assert big <= 12 * small + 1, (small, big)
    assert re.search("MAX_TEXT_CHARS", open(ic.__file__, encoding="utf-8").read())


# ---- tests added for the mutants of round 7 (names in the runner's round7() say which branch each one kills)
def test_b1_the_records_own_number_on_a_payment_line_is_exactly_d12():
    assert flags("Bank account, invoice no 87654321", invoice_no="87654321") == ["D12"]
    assert [
        n.code
        for n in ic.check_reasons(rec(invoice_no="87654321"), "Bank account, invoice no 87654321", {"acme widgets ltd": SC})[1]
        if n.code != "unexplained_number"
    ] == ["id_on_payment_line"]


@pytest.mark.parametrize("sep", ["\u01c0", "\u01c1", "\u01c2", "\u01c3", "\u05c0", "\u05c3", "\u2223", "\u2502", "\u23d0", "\uff5c"])
def test_b3_every_separator_look_alike(sep):
    assert ic._f("1" + sep + "2") == "1|2"


def test_m6_every_circled_digit_and_numeral_in_a_four_run():
    expected = {}
    for base in (0x2776, 0x2780, 0x278A):
        for k in range(10):
            expected[base + k] = str(k + 1) if k < 9 else "10"
    for cp, want in expected.items():
        assert ic._f(chr(cp)) == want, hex(cp)
    for ch, want in zip("\u3007\u96f6\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d", "00123456789", strict=True):
        assert ic._f(ch * 4) == want * 4, ch
    assert ic._f("\u516b\u4e03\u516d") == "\u516b\u4e03\u516d"  # three numerals in a row are text
    assert ic._f("\u516b\u4e03\u516d\u4e94") == "8765"


def test_taxlabel_identifiers_on_non_payment_lines_are_not_a_d12():
    r = rec()
    for t in ("ABN 51 824 753 556", "VAT: GB123456789012", "GST No 123456789", "Company No 12345678"):
        assert ic.unexplained_numbers(r, t, SC) == [], t
    assert ic.unexplained_numbers(r, "Bank VAT 87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "Please remit VAT 87654321", SC) == ["87654321"]
    assert ic.unexplained_numbers(r, "Reference 87654321", SC) == ["87654321"]


def test_html_views_directly():
    assert ic._html_views("plain text") == []
    assert ic._html_views("a<br>b") == ["a" + chr(10) + "b"]
    assert ic._html_views("1<b>2</b>3")[0] == "123"
    assert ic._html_views("1<!-- x -->2")[0] == "12"
    assert "12" in ic._html_views('1<span style="display:none">9</span>2')
    assert any("192" in v for v in ic._html_views('1<span style="display:none">9</span>2'))


def test_unserved_value_window_is_three_non_blank_lines():
    base = "Account number"
    assert flags(base + "\nBranch: A\nBranch: B\n12345678") == []
    assert flags(base + "\nBranch: A\nBranch: B\nBranch: C\n12345678") == ["D12"]
    assert flags("12345678\nAccount number") == []  # the number alone on the line above


def test_unserved_amount_rows_and_shape_and_each_label_class():
    row = "G302 132 4.31 568.92"
    assert "payment_line_no_number" in codes("Please remit via pay@evil.example.net" + chr(10) + "Item Qty" + chr(10) + row)
    for t in ("Sort code", "Account:", "Bank details:", "PayPal: x@y.example", "Beneficiary"):
        assert "payment_line_no_number" in codes(t), t
    assert "payment_line_no_number" not in codes("Bank transfer accepted")  # prose, not a label


def test_size_limit_boundary_and_raw_limit_boundary(monkeypatch):
    monkeypatch.setattr(ic, "MAX_TEXT_CHARS", 100)
    assert [n.code for n in ic.check_reasons(rec(), "a" * 100, {"acme widgets ltd": SC})[1]] == []
    assert [n.code for n in ic.check_reasons(rec(), "a" * 101, {"acme widgets ltd": SC})[1]] == ["text_too_large"]
    monkeypatch.setattr(ic, "RAW_MAX", 10)
    assert ic._visible_controls("a" * 10) == "a" * 10
    assert ic._visible_controls("a" * 10 + chr(0x202E)).endswith("controls: U+202E]")


def test_verb_lines_read_two_digit_groups_but_not_one_digit_groups():
    assert ic.unexplained_numbers(rec(), "Please send 8 7 6 5 4 3 2 1", SC) == []
    assert ic.unexplained_numbers(rec(), "Please send 87 65 43 21", SC) == ["87654321"]


def test_non_latin_context_needs_eight_digits():
    greek = "\u0393\u03b5\u03b9\u03b1"
    assert "short_account_number" not in codes(greek + " 123456")
    assert not ic.bank_detail_changed(greek + " 1234567", SC)
    assert ic.bank_detail_changed(greek + " 87654321", SC)
    assert flags("\u4f60\u597d \u4e16\u754c thanks") == []


def test_phone_span_stops_at_the_comma_and_must_contain_the_run():
    assert ic.unexplained_numbers(rec(), "Tel: +44 20 7946 0958", SC) == []
    assert ic.unexplained_numbers(rec(), "Tel: +44 20 7946 0958 and 87654321", SC) != []
