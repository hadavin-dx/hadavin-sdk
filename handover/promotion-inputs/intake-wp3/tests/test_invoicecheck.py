import base64
import pathlib
import random
import re
import time

import pytest

from intake import invoicecheck as ic

FIX = pathlib.Path(__file__).parent / "fixtures" / "d10"
ON_IBAN = "GB82 WEST 1234 5698 7654 32"
ON_SC = "Sort 20-00-00 Acct 12345678"
ON_G = "GB29 NWBK 6016 1331 9268 19"
ON_UK = "Sort 40-11-58 Acct 12345678"
ON_BIC = "GB82 WEST 1234 5698 7654 32 BIC WESTGB2L"
ON_ABA2 = "ABA 111222333"
ON_IFSC = "IFSC HDFC0001234 acct 123456789012"
ON_CLEAR = "Clearing 123456"
ON_BLZ = "BLZ 37040044"
ON_LOOK = "Acct 12345O78"
ON_MT = "MT84 MALT 0110 0001 2345 MTLC AST 001 S"
ON_ZZ = "IBAN ZZ12 ABCD EFGH IJKL MNOP"
ON_NUM9 = "Acct 456789012"
ON_ABA = "routing 111222333 acct 123456789"

# fixture name -> (on-file detail, expected D10)
CASES = {
    "changed_account": (ON_SC, True),
    "changed_iban": (ON_IBAN, True),
    "iban_last_digit": (ON_IBAN, True),
    "iban_changed_then_words": (ON_IBAN, True),
    "iban_words_clean": (ON_IBAN, False),
    "prose_at_30_days": (ON_IBAN, False),
    "prose_no_12_elm": (ON_IBAN, False),
    "partial_account": (ON_SC, True),
    "iban_lowercase_clean": (ON_IBAN, False),
    "iban_dotted_clean": (ON_IBAN, False),
    "iban_nbsp_clean": (ON_IBAN, False),
    "iban_second_different": (ON_IBAN, True),
    "sort_code_space": (ON_SC, True),
    "acct_no_changed": (ON_SC, True),
    "sort_and_changed_account": ("20-00-00 12345678", True),
    "account_bare_changed": (ON_SC, True),
    "routing_changed": ("111222333 123456789", True),
    "vat_lookalike": (ON_IBAN, False),
    "vat_no_due": (ON_IBAN, False),
    "cubic": (ON_IBAN, False),
    "abacus": (ON_IBAN, False),
    "bicycle": (ON_IBAN, False),
    "swift_then_date": (ON_IBAN, False),
    "sort_acct_both_clean": ("20-00-00 12345678", False),
    "fullwidth_changed": (ON_SC, True),
    "fullwidth_clean": (ON_SC, False),
    "html_entity_changed": (ON_SC, True),
    "html_entity_clean": (ON_SC, False),
    "base64_changed": (ON_SC, True),
    "base64_clean": (ON_SC, False),
    "percent_changed": (ON_SC, True),
    "percent_clean": (ON_SC, True),  # raw text "%2012345678" forms a digit group: stated limit, a person decides
    "iban_next_line_changed": (ON_IBAN, True),
    "iban_next_line_clean": (ON_IBAN, False),
    "acct_next_line_changed": (ON_SC, True),
    "acct_next_line_clean": (ON_SC, False),
    "account_manager": (ON_SC, False),  # a phone-like number after `manager` is skipped for the bare words
    "account_2026_001": (ON_SC, False),
    "statement_of_account": (ON_SC, False),
    "invoice_date_line": (ON_IBAN, False),
    "po_long": (ON_IBAN, False),
    "layout1_clean": (ON_IBAN, False),
    "layout2_clean": (ON_SC, False),
    "layout3_clean": (ON_ABA, False),
    "no_candidates": (ON_SC, False),
    "raccoglitori_clean": (ON_SC, False),
    "accenture_clean": (ON_SC, False),
    "bankside_clean": (ON_SC, False),
    "accounts_payable_clean": (ON_SC, False),
    "accounts_email_above_phone_clean": (ON_SC, False),
    "accounts_email_above_telephone_clean": (ON_SC, False),
    "spaced_account_clean": (ON_NUM9, False),
    "spaced_account_changed": (ON_NUM9, True),
    "bank_label_with_number_changed": (ON_SC, True),
    "account_notes_weak": (ON_SC, False),  # round 7: 6-7 digits under a bare word are D12
    "date_day32_first_changed": (ON_SC, True),
    "date_dmy_1899_changed": (ON_SC, True),
    "lookalike_run_i_only_changed": (ON_SC, True),
    "lookalike_run_l_only_changed": (ON_SC, True),
    "lookalike_run_s_only_changed": (ON_SC, True),
    "lookalike_run_b_only_changed": (ON_SC, True),
    "lookalike_run_z_only_changed": (ON_SC, True),
    "lookalike_run_o_only_changed": (ON_SC, True),
    "iban_kw_two_fillers_clean": (ON_IBAN, False),
    "iban_kw_three_fillers_flagged": (ON_IBAN, True),
    "money_next_line_cents_changed": (ON_SC, True),
    "money_next_line_spaced_cents_changed": (ON_SC, True),
    "money_next_line_after_sort_changed": (ON_SC, True),
    "amount_word_next_line_clean": (ON_SC, False),
    "greek_capital_nu_changed": (ON_SC, True),
    "greek_capital_nu_clean": (ON_SC, False),
    "cyrillic_capital_ze_changed": (ON_SC, True),
    "hangul_filler_in_number_changed": (ON_SC, True),
    "hangul_filler_in_keyword_changed": (ON_SC, True),
    "halfwidth_hangul_filler_changed": (ON_SC, True),
    "hangul_choseong_filler_changed": (ON_SC, True),
    "hangul_jungseong_filler_changed": (ON_SC, True),
    "hangul_filler_clean": (ON_SC, False),
    "wrapped_digits_changed": (ON_SC, True),
    "wrapped_digits_clean": (ON_SC, False),
    "wrapped_digits_second_label_changed": (ON_SC, True),
    "wrapped_digits_second_label_clean": (ON_SC, False),
    "glued_upper_bankacct_changed": (ON_SC, True),
    "glued_lower_bankacct_changed": (ON_SC, True),
    "glued_bankacc_changed": (ON_SC, True),
    "lookalike_run_two_tokens_changed": (ON_SC, True),
    "lookalike_run_87o5_changed": (ON_SC, True),
    "iban_nokw_spaced_letters_changed": (ON_IBAN, True),
    "iban_nokw_spaced_letters_clean": (ON_IBAN, False),
    "iban_nokw_maltese_clean": (ON_MT, False),
    "iban_nokw_maltese_changed": (ON_MT, True),
    "account_manager_colon_clean": (ON_SC, False),
    "customer_contact_clean": (ON_SC, False),
    "bank_po_changed": (ON_SC, True),
    "iban_next_line_token_run_changed": (ON_IBAN, True),
    "iban_next_line_token_run_clean": (ON_ZZ, False),
    "number_on_line_above_changed": (ON_SC, True),
    "number_on_line_above_clean": (ON_SC, False),
    "filler_line_known_gap_clean": (ON_SC, False),
    "swift_address_next_line_changed": (ON_BIC, True),
    "swift_address_next_line_clean": (ON_BIC, False),
    "date_dec31_clean": (ON_SC, False),
    "date_dec32_changed": (ON_SC, True),
    "date_jan31_clean": (ON_SC, False),
    "date_month0_changed": (ON_SC, True),
    "date_day0_changed": (ON_SC, True),
    "date_1999_clean": (ON_SC, False),
    "date_dmy_2100_changed": (ON_SC, True),
    "date_dmy_1999_clean": (ON_SC, False),
    "camel_bic_changed": (ON_SC, True),
    "camel_aba_changed": (ON_ABA2, True),
    "camel_aba_clean": (ON_ABA2, False),
    "camel_ifsc_changed": (ON_IFSC, True),
    "iban_6_digits_changed": (ON_SC, True),
    "account_hash_6_changed": (ON_SC, True),
    "acct_hash_6_changed": (ON_SC, True),
    "blz_6_changed": (ON_BLZ, True),
    "account_num_6_changed": (ON_SC, True),
    "account_nr_6_changed": (ON_SC, True),
    "account_nbr_6_changed": (ON_SC, True),
    "account_id_6_changed": (ON_SC, True),
    "accrued_clean": (ON_SC, False),  # fixed class: acc/bank inside a word is not a label
    "riverbank_clean": (ON_SC, False),  # fixed class: acc/bank inside a word is not a label
    "bankruptcy_clean": (ON_SC, False),  # fixed class: acc/bank inside a word is not a label
    "iban_kw_filler_word_clean": (ON_IBAN, False),
    "date_ydm_reading_clean": (ON_SC, False),
    "lookalike_onfile_clean": (ON_LOOK, False),
    "lookalike_three_digits_not_read_clean": (ON_SC, False),
    "sep_spaced_hyphen_changed": (ON_SC, True),
    "sep_spaced_dot_changed": (ON_SC, True),
    "sep_spaced_hyphen_clean": (ON_SC, False),
    "sep_spaced_dot_clean": (ON_SC, False),
    "aba_changed": (ON_ABA2, True),
    "aba_clean": (ON_ABA2, False),
    "ifsc_changed": (ON_IFSC, True),
    "ifsc_clean": (ON_IFSC, False),
    "clearing_changed": (ON_CLEAR, True),
    "clearing_clean": (ON_CLEAR, False),
    "swift_digits_changed": (ON_SC, True),
    "bic_digits_changed": (ON_SC, True),
    "account_hash_changed": (ON_SC, True),
    "konto_changed": (ON_SC, True),
    "bare_account_changed": (ON_SC, True),
    "bare_acct_changed": (ON_SC, True),
    "bank_phone_ref_clean": (ON_SC, False),
    "account_no_tel_label_changed": (ON_SC, True),
    "bank_hotel_changed": (ON_SC, True),
    "iban_nokw_three_words_changed": (ON_SC, True),  # words with acc/bank inside: documented false D10
    "iban_nokw_two_words_changed": (ON_SC, True),
    "iban_nokw_five_letter_bank_code_not_found_clean": (ON_SC, False),
    "camel_bankaccountno_changed": (ON_SC, True),
    "camel_bankaccountno_glued_changed": (ON_SC, True),
    "camel_bankaccountno_clean": (ON_SC, False),
    "camel_myaccountnumber_changed": (ON_SC, True),
    "lower_glued_in_word_changed": (ON_SC, True),
    "number_before_label_changed": (ON_SC, True),
    "number_before_label_clean": (ON_SC, False),
    "number_before_bic_changed": (ON_SC, True),
    "header_group_then_value_changed": (ON_SC, True),
    "header_group_then_value_clean": (ON_SC, False),
    "label_then_blank_then_value_changed": (ON_SC, True),
    "keyword_alpha_variant_changed": (ON_SC, True),
    "keyword_alpha_variant_clean": (ON_SC, False),
    "iban_nokw_space_cc_changed": (ON_IBAN, True),
    "iban_nokw_space_cc_clean": (ON_IBAN, False),
    "iban_nokw_wrapped_changed": (ON_IBAN, True),
    "iban_nokw_wrapped_clean": (ON_IBAN, False),
    "iban_nokw_three_lines_changed": (ON_IBAN, True),
    "iban_nokw_three_lines_clean": (ON_IBAN, False),
    "iban_nokw_hyphen_changed": (ON_IBAN, True),
    "iban_nokw_hyphen_clean": (ON_IBAN, False),
    "iban_nokw_colon_changed": (ON_IBAN, True),
    "iban_nokw_slash_backslash_changed": (ON_IBAN, True),
    "iban_nokw_prose_at_30_days_clean": (ON_IBAN, False),
    "iban_nokw_no_12_elm_road_clean": (ON_IBAN, False),
    "iban_nokw_at_30_days_then_bank_line_clean": (ON_SC, False),
    "lookalike_o_extra_changed": (ON_SC, True),
    "lookalike_o_prefix_changed": (ON_SC, True),
    "lookalike_l_changed": (ON_SC, True),
    "lookalike_capital_i_changed": (ON_SC, True),
    "lookalike_s_changed": (ON_SC, True),
    "lookalike_b_changed": (ON_SC, True),
    "lookalike_z_changed": (ON_SC, True),
    "lookalike_o_in_middle_changed": (ON_SC, True),
    "lookalike_in_sort_code_changed": (ON_SC, True),
    "lookalike_plain_words_clean": (ON_SC, False),
    "sep_002f_changed": (ON_SC, True),
    "sep_002f_clean": (ON_SC, False),
    "sep_005c_changed": (ON_SC, True),
    "sep_005c_clean": (ON_SC, False),
    "sep_003a_changed": (ON_SC, True),
    "sep_003a_clean": (ON_SC, False),
    "sep_007c_changed": (ON_SC, True),
    "sep_007c_clean": (ON_SC, False),
    "sep_002a_changed": (ON_SC, True),
    "sep_002a_clean": (ON_SC, False),
    "sep_002b_changed": (ON_SC, True),
    "sep_002b_clean": (ON_SC, False),
    "sep_0060_changed": (ON_SC, True),
    "sep_0060_clean": (ON_SC, False),
    "sep_0027_changed": (ON_SC, True),
    "sep_0027_clean": (ON_SC, False),
    "sep_2032_changed": (ON_SC, True),
    "sep_2032_clean": (ON_SC, False),
    "sep_02bc_changed": (ON_SC, True),
    "sep_02bc_clean": (ON_SC, False),
    "sep_2019_changed": (ON_SC, True),
    "sep_2019_clean": (ON_SC, False),
    "sep_00b7_changed": (ON_SC, True),
    "sep_00b7_clean": (ON_SC, False),
    "sep_003b_changed": (ON_SC, True),
    "sep_003b_clean": (ON_SC, False),
    "sep_005f_changed": (ON_SC, True),
    "sep_005f_clean": (ON_SC, False),
    "sep_007e_changed": (ON_SC, True),
    "sep_007e_clean": (ON_SC, False),
    "sep_005e_changed": (ON_SC, True),
    "sep_005e_clean": (ON_SC, False),
    "sep_003d_changed": (ON_SC, True),
    "sep_003d_clean": (ON_SC, False),
    "sep_0023_changed": (ON_SC, True),
    "sep_0023_clean": (ON_SC, False),
    "sep_0040_changed": (ON_SC, True),
    "sep_0040_clean": (ON_SC, False),
    "sep_0026_changed": (ON_SC, True),
    "sep_0026_clean": (ON_SC, False),
    "sep_0021_changed": (ON_SC, True),
    "sep_0021_clean": (ON_SC, False),
    "sep_003f_changed": (ON_SC, True),
    "sep_003f_clean": (ON_SC, False),
    "sep_0028_changed": (ON_SC, True),
    "sep_0028_clean": (ON_SC, False),
    "sep_0029_changed": (ON_SC, True),
    "sep_0029_clean": (ON_SC, False),
    "sep_003c_changed": (ON_SC, True),
    "sep_003c_clean": (ON_SC, False),
    "sep_003e_changed": (ON_SC, True),
    "sep_003e_clean": (ON_SC, False),
    "sep_007b_changed": (ON_SC, True),
    "sep_007b_clean": (ON_SC, False),
    "sep_007d_changed": (ON_SC, True),
    "sep_007d_clean": (ON_SC, False),
    "sep_005b_changed": (ON_SC, True),
    "sep_005b_clean": (ON_SC, False),
    "sep_005d_changed": (ON_SC, True),
    "sep_005d_clean": (ON_SC, False),
    "sep_002c_changed": (ON_SC, True),
    "sep_002c_clean": (ON_SC, False),
    "sep_002e_changed": (ON_SC, True),
    "sep_002e_clean": (ON_SC, False),
    "sep_002d_changed": (ON_SC, True),
    "sep_002d_clean": (ON_SC, False),
    "sep_0020_changed": (ON_SC, True),
    "sep_0020_clean": (ON_SC, False),
    "sep_0025_changed": (ON_SC, True),
    "sep_0025_clean": (ON_SC, False),
    "sep_0024_changed": (ON_SC, True),
    "sep_0024_clean": (ON_SC, False),
    "sort_endash_changed": (ON_UK, True),
    "sort_endash_clean": (ON_UK, False),
    "sort_emdash_changed": (ON_UK, True),
    "sort_nbhyphen_changed": (ON_UK, True),
    "sort_minus_changed": (ON_UK, True),
    "sort_spaced_hyphen_changed": (ON_UK, True),
    "sort_spaced_hyphen_clean": (ON_UK, False),
    "iban_nbhyphen_changed": (ON_IBAN, True),
    "iban_nbhyphen_clean": (ON_IBAN, False),
    "iban_endash_nokw_changed": (ON_IBAN, True),
    "a_c_division_slash_changed": (ON_SC, True),
    "a_c_fraction_slash_changed": (ON_SC, True),
    "a_c_fullwidth_slash_changed": (ON_SC, True),
    "account_double_space_changed": (ON_SC, True),
    "account_double_space_clean": (ON_SC, False),
    "account_tab_changed": (ON_SC, True),
    "account_tab_clean": (ON_SC, False),
    "account_nbsp_changed": (ON_SC, True),
    "account_ideographic_space_changed": (ON_SC, True),
    "account_thousands_comma_changed": ("12345678", True),
    "account_thousands_comma_clean": ("12345678", False),
    "account_comma_changed": (ON_SC, True),
    "account_comma_space_changed": (ON_SC, True),
    "account_apostrophe_changed": (ON_SC, True),
    "account_underscore_changed": (ON_SC, True),
    "glued_accountno_changed": (ON_SC, True),
    "glued_account_changed": (ON_SC, True),
    "glued_ac_changed": (ON_SC, True),
    "acc_colon_changed": (ON_SC, True),
    "glued_accountno_clean": (ON_SC, False),
    "glued_account_clean": (ON_SC, False),
    "glued_ac_clean": (ON_SC, False),
    "armenian_seh_changed": (ON_SC, True),
    "armenian_seh_clean": (ON_SC, False),
    "cyrillic_ghe_routing_changed": (ON_ABA, True),
    "cyrillic_ghe_routing_clean": (ON_ABA, False),
    "cyrillic_soft_sign_bic_changed": (ON_SC, True),
    "small_caps_account_changed": (ON_SC, True),
    "small_caps_account_clean": (ON_SC, False),
    "greek_omicron_account_changed": (ON_SC, True),
    "iban_space_cc_due_clean": (ON_IBAN, False),
    "vat_gb_payable_30_days_clean": (ON_IBAN, False),
    "vat_de_amtsgericht_clean": (ON_IBAN, False),
    "bank_hsbc_tel_clean": (ON_SC, False),
    "bank_tel_then_account_changed": (ON_SC, True),
    "bic_changed": (ON_BIC, True),
    "bic_clean": (ON_BIC, False),
    "bic_branch_clean": (ON_BIC, False),
    "bic_ignored_without_onfile_bic": (ON_IBAN, False),
    "keyword_6_digits_changed": (ON_SC, True),
    "keyword_5_digits_clean": (ON_SC, False),
    "keyword_7_digits_changed": (ON_SC, True),
    "bare_7_digits_weak": (ON_SC, False),  # round 7: the same
    "bare_9_digits_changed": (ON_SC, True),
    "date_month13_changed": (ON_SC, True),
    "date_day32_changed": (ON_SC, True),
    "date_year1899_changed": (ON_SC, True),
    "date_year2100_changed": (ON_SC, True),
    "date_year1900_clean": (ON_SC, False),
    "date_year2099_clean": (ON_SC, False),
    "collide_extra_group_changed": ("12345678", True),
    "collide_three_groups_changed": ("12345678", True),
    "collide_sortcode_extended_changed": (ON_SC, True),
    "collide_short_onfile_changed": ("123456", True),
    "collide_days_false_d10": ("12345678", True),
    "iban_kw_space_cc_changed": (ON_IBAN, True),
    "iban_kw_space_cc_clean": (ON_IBAN, False),
    "iban_wrapped_changed": (ON_IBAN, True),
    "iban_wrapped_clean": (ON_IBAN, False),
    "iban_truncated_changed": (ON_IBAN, True),
    "iban_star_changed": (ON_IBAN, True),
    "iban_star_around_clean": (ON_IBAN, False),
    "iban_hash_changed": (ON_IBAN, True),
    "iban_short_truncated_floor_clean": (ON_IBAN, False),
    "bsb_changed": ("BSB 062-000 acct 12345678", True),
    "bsb_clean": ("BSB 062-000 acct 12345678", False),
    "blz_konto_changed": ("BLZ 37040044 Konto 532013000", True),
    "blz_konto_clean": ("BLZ 37040044 Konto 532013000", False),
    "konto_nummer_changed": (ON_SC, True),
    "account_nr_changed": (ON_SC, True),
    "account_id_changed": (ON_SC, True),
    "account_nbr_clean": (ON_SC, False),
    "branch_code_changed": (ON_SC, True),
    "clabe_changed": ("clabe 012345678901234567", True),
    "tel_total_do_not_hide_changed": (ON_SC, True),
    "account_year_like_changed": (ON_SC, True),
    "total_before_keyword_clean": (ON_SC, True),  # line scope: any 6+ digit run on a keyword line (documented false D10)
    "account_dateshaped_changed": (ON_SC, True),
    "account_dateshaped_sort_changed": (ON_SC, True),
    "account_spaced_changed": (ON_SC, True),
    "acct_spaced_changed": (ON_SC, True),
    "account_spaced_clean": (ON_SC, False),
    "acct_spaced_clean": (ON_SC, False),
    "acct_hash_changed": (ON_SC, True),
    "acct_hash_clean": (ON_SC, False),
    "alabama_clean": (ON_SC, False),
    "dotted_date_clean": (ON_SC, False),
    "glued_clean": ("20-00-00 12345678", False),
    "glued_changed": ("20-00-00 12345678", True),
    "iban_kw_slashes_clean": (ON_G, False),
    "iban_kw_slashes_changed": (ON_G, True),
    "iban_kw_tab_underscore_changed": (ON_G, True),
    "iban_kw_pipe_clean": (ON_G, False),
    "iban_kw_unknown_country_changed": (ON_G, True),
    "sort_code_underscore_clean": (ON_SC, False),
    "sort_code_underscore_changed": (ON_SC, True),
    "acct_no_equals_changed": (ON_SC, True),
    "acct_equals_changed": (ON_SC, True),
    "a_c_no_changed": (ON_SC, True),
    "a_c_changed": (ON_SC, True),
    "acc_no_changed": (ON_SC, True),
    "acc_dot_changed": (ON_SC, True),
    "bank_colon_changed": (ON_SC, True),
    "acct_next_line_blank_changed": (ON_SC, True),
    "acct_next_line_blank_clean": (ON_SC, False),
    "empty_onfile_quoted": ("", True),
    "empty_onfile_no_candidates": ("", False),
}


def _cands(text):
    return ic._candidates(ic._f(text), ic._f(ic._camel(text)))


def load(name):
    raw = (FIX / f"{name}.txt").read_bytes()
    assert b"\r" not in raw and raw.isascii()
    return re.sub(r"\\u([0-9a-f]{4})", lambda m: chr(int(m.group(1), 16)), raw.decode("ascii").replace("\\t", chr(9)))


def test_every_fixture_listed():
    assert {p.stem for p in FIX.glob("*.txt")} == set(CASES)


@pytest.mark.parametrize("name", sorted(CASES))
def test_fixture(name):
    on_file, want = CASES[name]
    assert ic.bank_detail_changed(load(name), on_file) is want


def test_iban_table_sane():
    assert (
        ic.IBAN_LENGTH["GB"] == 22
        and ic.IBAN_LENGTH["NO"] == 15
        and len(ic.IBAN_LENGTH) == 89
        and all(type(v) is int for v in ic.IBAN_LENGTH.values())
    )


# ---------------------------------------------------------------- D06 / L01 / check
def rec(**kw):
    r = {
        "invoice_no": "INV-1",
        "supplier_name": "Acme  Widgets LTD",
        "currency": "USD",
        "lines": [{"description": "x", "qty": 2, "unit_cost_minor": 500, "amount_minor": 1000}],
        "adjustments": [{"label": "tax", "amount_minor": 100}],
        "total_minor": 1100,
    }
    r.update(kw)
    return r


SUP = {"acme widgets ltd": ON_IBAN}


def test_check_clean():
    assert ic.check(rec(), "pay GB82 WEST 1234 5698 7654 32", SUP, backstop=False) == []


def test_d06_total_and_line():
    assert ic.check(rec(total_minor=1101), "", SUP, backstop=False) == ["D06"]
    bad = rec(lines=[{"description": "x", "qty": 2, "unit_cost_minor": 500, "amount_minor": 999}], total_minor=1099)
    assert ic.check(bad, "", SUP, backstop=False) == ["D06"]


def test_d06_runs_for_unknown_supplier_with_l01_only_no_d10():
    out = ic.check(rec(supplier_name="Nobody", total_minor=1), "Account: 99887766", SUP, backstop=False)
    assert out == ["D06", "L01"]


def test_d06_and_d10_together():
    assert ic.check(rec(total_minor=1), "Pay GB82 WEST 1234 5698 7654 33", SUP, backstop=False) == ["D06", "D10"]


def test_supplier_key_is_casefold_and_space_collapse_only():
    assert "L01" in ic.check(rec(supplier_name="Acme Widgets Ltd."), "", SUP)


def test_load_suppliers(tmp_path):
    p = tmp_path / "s.csv"
    p.write_bytes(b'supplier_name,bank_detail\r\n"Acme  Ltd","GB82 WEST 1234 5698 7654 32"\nOther,20-00-00 12345678\n')
    assert ic.load_suppliers(p) == {"acme ltd": ON_IBAN, "other": "20-00-00 12345678"}


def test_load_suppliers_bom(tmp_path):
    p = tmp_path / "s.csv"
    p.write_bytes(b"\xef\xbb\xbfsupplier_name,bank_detail\nAcme,12345678\n")
    assert ic.load_suppliers(p) == {"acme": "12345678"}


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"a,b\nx,y\n",
        b"supplier_name,bank_detail\nA,1\n",
        b"supplier_name,bank_detail\nA,GB82 WEST\n",
        b"supplier_name,bank_detail\nA,\n",
        b"supplier_name,bank_detail\nA,123456\na ,123456\n",
        b"supplier_name,bank_detail\n,123456\n",
        b"supplier_name,bank_detail\nA,123456,2\n",
        b"supplier_name,bank_detail\n\xff,123456\n",
    ],
)
def test_load_suppliers_invalid(tmp_path, data):
    p = tmp_path / "s.csv"
    p.write_bytes(data)
    with pytest.raises(ic.SuppliersInvalid):
        ic.load_suppliers(p)
    with pytest.raises(ic.SuppliersInvalid):
        ic.load_suppliers(tmp_path / "missing.csv")


# ---------------------------------------------------------------- property tests
def _forms_iban(rnd):
    n = "GB82WEST12345698765432"
    sep = rnd.choice([" ", ".", "-", "  "])
    spaced = sep.join(n[i : i + 4] for i in range(0, len(n), 4))
    return rnd.choice([n, spaced, n.lower(), spaced.lower(), spaced.replace(" ", chr(0xA0))])


def _forms_acct(rnd):
    return rnd.choice(["12345678", "1234-5678", "1234.5678", "".join(chr(0xFF10 + int(d)) for d in "12345678"), "1234 5678"])


def _wrap(rnd, quoted):
    if rnd.choice(["plain", "b64"]) == "b64":
        return base64.b64encode(quoted.encode()).decode()
    return quoted


NOISE = [
    "Thanks for your order",
    "Total 125.00",
    "Invoice INV-1001 date 2026-10-01",
    "Payable at 30 days",
    "PO-77",
    "",
]


def _doc(rnd, quoted):
    lines = [rnd.choice(NOISE) for _ in range(rnd.randint(0, 4))]
    lines.insert(rnd.randint(0, len(lines)), quoted)
    return "\n".join(lines) + "\n"


def test_property_verbatim_never_d10():
    rnd = random.Random(1)
    for _ in range(300):
        iban = _doc(rnd, "IBAN " + _forms_iban(rnd) + " Payment due")
        assert not ic.bank_detail_changed(iban, ON_IBAN), iban
        acct = _doc(rnd, "Sort Code 20-00-00 Account No " + _forms_acct(rnd))
        assert not ic.bank_detail_changed(acct, "20-00-00 12345678"), acct
    for _ in range(100):  # encoded blobs: plain quoted account, wrapped in base64
        q = _wrap(rnd, "Account No 12345678 thanks")
        assert not ic.bank_detail_changed("Ref " + q + "\n", "12345678"), q


def test_property_single_digit_mutation_always_d10():
    rnd = random.Random(2)
    for _ in range(300):
        iban = list("GB82WEST12345698765432")
        i = rnd.randrange(2, 22)
        if iban[i].isdigit():
            iban[i] = rnd.choice([d for d in "0123456789" if d != iban[i]])
        else:
            iban[i] = rnd.choice([c for c in "ABCDEFGHJK" if c != iban[i]])
        q = "".join(iban)
        assert ic.bank_detail_changed(_doc(rnd, "IBAN " + q + rnd.choice(["", " Payment due", " 2026-11-01"])), ON_IBAN), q
        acct = list("12345678")
        j = rnd.randrange(8)
        acct[j] = rnd.choice([d for d in "0123456789" if d != acct[j]])
        text = _doc(rnd, "Account No " + "".join(acct))
        assert ic.bank_detail_changed(text, "12345678"), text


def test_spaced_account_property():
    rnd = random.Random(3)
    for _ in range(200):
        a, b = rnd.randrange(1000, 10000), rnd.randrange(1000, 10000)
        on = f"{a}{b}"
        assert not ic.bank_detail_changed(_doc(rnd, f"Account No {a} {b}"), on)
        assert not ic.bank_detail_changed(_doc(rnd, f"Acct {a} {b}"), on)
        assert ic.bank_detail_changed(_doc(rnd, f"Account No {a} {b + 1 if b < 9999 else b - 1}"), on)


def test_adversarial_20000_chars_fast():
    for text in (
        "aba 1 " * 3300,
        "acct " * 4000,
        "sort code " + "1" * 19900,
        "gb12 " * 4000,
        "iban gb12 " * 2000,
        "1 " * 10000 + "account",
        chr(10) * 19990 + "swift",
    ):
        t0 = time.monotonic()
        ic.bank_detail_changed(text, ON_SC)
        assert time.monotonic() - t0 < 10.0, text[:20]


# ---------------------------------------------------------------- arithmetic robustness
@pytest.mark.parametrize(
    "mut",
    [
        {"total_minor": True},
        {"total_minor": 1100.0},
        {"total_minor": None},
        {"lines": [{"description": "x", "qty": 2.0, "unit_cost_minor": 500, "amount_minor": 1000}]},
        {"lines": [{"description": "x", "qty": 2, "unit_cost_minor": 500}]},
        {"lines": None},
        {"adjustments": [{"label": "t", "amount_minor": None}]},
        {"adjustments": [{"label": "t", "amount_minor": True}]},
    ],
)
def test_malformed_amounts_give_d06_not_crash(mut):
    assert "D06" in ic.check(rec(**mut), "", SUP)


# ---------------------------------------------------------------- pins and properties (round 3)
def test_property_extra_spaced_group_always_d10():
    rnd = random.Random(4)
    for _ in range(300):
        a, b, c = rnd.randrange(1000, 10000), rnd.randrange(1000, 10000), rnd.randrange(10, 100)
        on = f"{a}{b}"
        assert ic.bank_detail_changed(_doc(rnd, f"Account No {a} {b} {c}"), on)
        assert ic.bank_detail_changed(_doc(rnd, f"Acct No {on} {c}"), on)


def test_next_lines_window_pinned():
    assert ic.bank_detail_changed("Acct No:\n\n\n12345679\n", ON_SC)
    assert not ic.bank_detail_changed("Acct No:\n\n\n\n12345679\n", ON_SC)


def _kwib(text):
    return ic._iban_keyword([ic._f(text)], 0)


def test_iban_run_cap_and_floor_pinned():
    assert max(map(len, _kwib("iban xx12 " + "3456 " * 20))) == 34
    assert _kwib("iban xx12 3456 7890") == []
    assert len(_kwib("iban xx12 3456 7890 1234")[0]) == 16


def test_max_join_pinned():
    cands = _cands("account no " + "1 " * 20)
    assert "1" * 16 in cands and "1" * 17 not in cands


def test_tel_line_same_line_does_not_hide():
    assert ic.bank_detail_changed("Tel 0207123 4567 Account No 87654321", ON_SC)


# ---------------------------------------------------------------- round 4: class-level normalisation, findings, guards
def test_more_adversarial_inputs_linear():
    tab, nl, sp = chr(9), chr(10), " "
    inputs = [
        "gb12" + sp * 19990,
        "iban gb12" + nl * 1 + ("iban gb12" + nl) * 1500,
        "account no " + "1 " * 9000,
        "8765" + tab * 19990 + "4321",
        "sort code" + "-" * 19990,
        "bic " + "a" * 19990,
        "12," * 6600 + "account",
        ("acct " + "1" * 7 + nl) * 2500,
        "a/c" * 6600,
        chr(0x2013) * 19990 + "account no 1",
    ]
    for text in inputs:
        t0 = time.monotonic()
        ic.bank_detail_findings(text, ON_SC)
        assert time.monotonic() - t0 < 10.0, text[:20]


def test_cr_and_crlf_give_the_same_verdict_for_every_fixture():
    for name, (on_file, want) in CASES.items():
        text = load(name)
        for nl in (chr(13) + chr(10), chr(13)):
            assert ic.bank_detail_changed(text.replace(chr(10), nl), on_file) is want, (name, nl)


def test_separator_classes_never_change_the_verdict():
    dashes = [chr(c) for c in (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2212, 0xFE63, 0xFF0D)]
    spaces = [" ", "  ", chr(9), chr(0xA0), chr(0x2003), chr(0x3000), chr(0x202F)]
    rnd = random.Random(7)
    docs = [
        ("Sort Code: 40-11-58 Account No: 1234 5678", ON_UK + " 12345678"),
        ("IBAN: GB82 WEST 1234 5698 7654 32", ON_IBAN),
        ("Account No 8765 4321", ON_SC),
        ("Sort Code 20-00-00 Account 87654321", ON_SC),
    ]
    for text, on in docs:
        want = ic.bank_detail_changed(text, on)
        for _ in range(60):
            t = re.sub("-", lambda m: rnd.choice(dashes), text)
            t = re.sub(" ", lambda m: rnd.choice(spaces), t)
            assert ic.bank_detail_changed(t, on) is want, t


@pytest.mark.parametrize(
    "cp,ch", [(0x57D, "u"), (0x433, "r"), (0x44C, "b"), (0x458, "j"), (0x1D00, "a"), (0x299, "b"), (0x3B1, "a"), (0x585, "o")]
)
def test_homoglyph_table_maps_by_class(cp, ch):
    assert ic._f(chr(cp)) == ch


def test_findings_report_candidate_and_components():
    f = ic.bank_detail_findings("Account No 87654321", ON_SC)
    assert [(x.candidate, x.kind) for x in f] == [("87654321", "number")]
    assert "12345678" in f[0].components and f[0].on_file == ON_SC
    assert ic.bank_detail_findings("Account No 12345678", ON_SC) == []
    b = ic.bank_detail_findings("BIC WESTGB2M", ON_BIC)
    assert [(x.candidate, x.kind) for x in b] == [("westgb2m", "bic")]


def test_hex_encoded_changed_and_clean():
    hx = lambda t: t.encode().hex()  # noqa: E731
    assert ic.bank_detail_changed("Ref " + hx("Account No 87654321"), ON_SC)
    assert not ic.bank_detail_changed("Ref " + hx("Account No 12345678"), ON_SC)


def test_check_rejects_unnormalised_supplier_keys():
    with pytest.raises(ValueError):
        ic.check(rec(), "", {"Acme  Widgets LTD": ON_IBAN})


def test_check_takes_raw_text_and_flags_homoglyph_changed_number():
    text = "Acco" + chr(0x57D) + "nt No 87654321"
    assert ic.check(rec(), text, SUP_SC, backstop=False) == ["D10"]


SUP_SC = {"acme widgets ltd": ON_SC}


def test_dash_and_whitespace_tables_cover_the_unicode_classes():
    import unicodedata

    for cp in range(0x11000):
        if unicodedata.category(chr(cp)) == "Pd":
            assert ic._f("1" + chr(cp) + "2") == "1-2", hex(cp)
    for cp in (0x20, 9, 0xA0, 0x1680, 0x2000, 0x2009, 0x202F, 0x205F, 0x3000):
        assert ic._f("a" + chr(cp) * 3 + "b") == "a b", hex(cp)


def test_line_break_class_is_a_line_break_not_a_space():
    doc = "Acct No 8765{}4321"
    lf = ic.bank_detail_findings(doc.format(chr(10)), ON_SC)
    for br in (chr(13), chr(13) + chr(10), chr(0x0B), chr(0x0C), chr(0x85), chr(0x2028), chr(0x2029)):
        assert ic.bank_detail_findings(doc.format(br), ON_SC) == lf, hex(ord(br[0]))
    assert ic._f("a" + chr(13) + "b") == "a" + chr(10) + "b"
    assert ic._f("a" + chr(0x2028) + "b") == "a" + chr(10) + "b"


SEPARATOR_CODEPOINTS = [
    47,
    92,
    58,
    124,
    42,
    43,
    96,
    39,
    8242,
    700,
    8217,
    183,
    59,
    95,
    126,
    94,
    61,
    35,
    64,
    38,
    33,
    63,
    40,
    41,
    60,
    62,
    123,
    125,
    91,
    93,
    44,
    46,
    45,
    32,
    37,
    36,
]


# ---------------------------------------------------------------- round 5: pins, backstop, structure
PHONE_WORDS = ["tel", "phone", "fax", "mob", "mobile", "ph", "ref", "vat", "abn"]


@pytest.mark.parametrize("word", PHONE_WORDS)
def test_phone_word_suppresses_only_on_a_bank_only_line(word):
    if word in ("ref", "vat", "abn"):  # reference words skip any run
        assert not ic.bank_detail_changed(f"Bank: {word} 87654321", ON_SC)
    else:  # phone words skip a phone-shaped run only
        assert not ic.bank_detail_changed(f"Bank: {word} 020 7946 0958", ON_SC)
        assert not ic.bank_detail_changed(f"Bank: {word} +44 20 7946 0958", ON_SC)
        assert ic.bank_detail_changed(f"Bank: {word} 87654321", ON_SC)  # a plain 8-digit number after a phone word is still a candidate
    assert ic.bank_detail_changed(f"Account No: {word} 87654321", ON_SC)
    assert ic.bank_detail_changed(f"Bank: x{word} 87654321", ON_SC)


def test_bic_needs_a_bic_shape_and_an_on_file_bic():
    assert not ic.bank_detail_changed("Pay by SWIFT transfer", ON_BIC)
    assert ic.bank_detail_changed("SWIFT: WESTGB2M", ON_BIC)
    assert not ic.bank_detail_changed("SWIFT: WESTXX2M", ON_BIC)  # XX is not a country: not a BIC shape


def _hx(t, **kw):
    return t.encode().hex()


def test_hex_forms():
    raw = "Account No 87654321"
    h = raw.encode().hex()
    forms = {
        "plain": h,
        "spaced": " ".join(h[i : i + 2] for i in range(0, len(h), 2)),
        "0x": " ".join("0x" + h[i : i + 2] for i in range(0, len(h), 2)),
        "backslash-x": "".join(chr(92) + "x" + h[i : i + 2] for i in range(0, len(h), 2)),
        "odd offset": "f" + h,
        "comma": ",".join(h[i : i + 2] for i in range(0, len(h), 2)),
    }
    for name, form in forms.items():
        assert ic.bank_detail_changed("Ref " + form, ON_SC), name
    clean = b"Account No 12345678".hex()
    assert not ic.bank_detail_changed("Ref " + clean, ON_SC)


def test_hex_minimum_is_eight_bytes():
    assert ic._hex_extras("41" * 8) and not ic._hex_extras("41" * 7)


def test_backstop_unexplained_numbers():
    f = rec(invoice_no="INV-20261101", po_ref="PO-5551234", invoice_date="2026-11-01", total_minor=12345678)
    f["lines"] = [{"description": "x", "qty": 1, "unit_cost_minor": 12345678, "amount_minor": 12345678}]
    f["adjustments"] = []
    assert ic.unexplained_numbers(f, "Please ring 87654321 today", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(f, "Please ring 12345678 today", ON_SC) == []  # an on-file component
    assert ic.unexplained_numbers(f, "Total 123,456.78", ON_SC) == []  # the grounded total
    assert ic.unexplained_numbers(f, "Order INV-20261101", ON_SC) == []  # the invoice number
    assert ic.unexplained_numbers(f, "Tel 020 7946 0958", ON_SC) == []  # a phone-labelled, phone-shaped line
    assert ic.unexplained_numbers(f, "Mobile: +44 7700 900123", ON_SC) == []
    assert ic.unexplained_numbers(f, "Tel 87654321", ON_SC) == ["87654321"]  # a plain number after a phone word is not a phone number
    assert ic.unexplained_numbers(f, "Hotel 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(f, "Date 2026-11-01", ON_SC) == []
    assert ic.unexplained_numbers(f, "ref 8765432", ON_SC) == []  # 7 digits: below the minimum
    assert ic.unexplained_numbers(f, "ref 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(f, "ref 8765 4321", ON_SC) == ["87654321"]
    hexed = "Ref " + b"87654321".hex()
    assert "87654321" in ic.unexplained_numbers(f, hexed, ON_SC)


def test_backstop_flag_only_when_asked():
    sup = {"acme widgets ltd": ON_SC}
    text = "Thanks. Ring 87654321"
    assert ic.check(rec(), text, sup, backstop=False) == []
    assert ic.check(rec(), text, sup) == [ic.BACKSTOP_FLAG]
    assert ic.BACKSTOP_REASON == "unexplained_number"


def test_finding_is_folded_and_iban_length_is_read_only():
    f = ic.bank_detail_findings("ACCOUNT NO 8765 4321", ON_SC)
    assert f[0].candidate == "87654321"
    with pytest.raises(TypeError):
        ic.IBAN_LENGTH["GB"] = 1  # type: ignore[index]


def test_public_surface_and_importers():
    import ast

    assert all(not n.startswith("_") and hasattr(ic, n) for n in ic.__all__)
    src = pathlib.Path(ic.__file__).parent
    for p in src.glob("*.py"):
        if p.name in ("invoicecheck.py", "confusables_data.py"):
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] == "invoicecheck":
                assert {a.name for a in node.names} <= set(ic.__all__), (p.name, [a.name for a in node.names])
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "invoicecheck":
                assert node.attr in ic.__all__, (p.name, node.attr)


PD_CODE_POINTS = [
    0x2D,
    0x58A,
    0x5BE,
    0x1400,
    0x1806,
    0x2010,
    0x2011,
    0x2012,
    0x2013,
    0x2014,
    0x2015,
    0x2E17,
    0x2E1A,
    0x2E3A,
    0x2E3B,
    0x2E40,
    0x2E5D,
    0x301C,
    0x3030,
    0x30A0,
    0xFE31,
    0xFE32,
    0xFE58,
    0xFE63,
    0xFF0D,
    0x10EAD,
    0x2212,
]


def test_dash_class_fixed_code_points():
    for cp in PD_CODE_POINTS:
        assert ic._f("1" + chr(cp) + "2") == "1-2", hex(cp)


def test_thresholds_pinned_by_behaviour():
    assert ic.bank_detail_changed("Sort code 123456", ON_SC) and not ic.bank_detail_changed("Sort code 12345", ON_SC)
    assert not ic.bank_detail_changed("Account 1234567", ON_SC) and ic.bank_detail_changed(
        "Account 87654321", ON_SC
    )  # round 7: 6-7 digits are D12
    assert not ic.bank_detail_changed("Account 12345", ON_SC) and not ic.bank_detail_changed("Account 123456", ON_SC)
    assert ic.unexplained_numbers(rec(), "Account 1234567", ON_SC) == []  # (the weak candidate is a notice, not a D12 number)
    assert "short_account_number" in [n.code for n in ic.check_reasons(rec(), "Account 1234567", {"acme widgets ltd": ON_SC})[1]]
    assert not ic._iban_keyword([ic._f("iban xx12 3456 78901 23456")], 0)  # TOKEN_MAX 4: a 5-character token ends the run
    assert ic._ibans([ic._f("GB82 WESTX 1234 5698 7654 99")], 0) == []  # ALPHA_TOKEN_STOP 5
    assert ic._ibans([ic._f("GB82 WEST 1234 5698 7654 99")], 0)
    assert ic._ibans([ic._f("GB82 1234 a b c d e f g h i 5698 7654")], 0) == []  # ALPHA_TOKEN_MAX 8: nine one-letter words
    assert ic._ibans([ic._f("GB82 1234 a b c d e f g h 5698 7654")], 0)


def test_scaling_is_linear():
    nl, tab = chr(10), chr(9)
    makers = {
        "digits": lambda n: "account no " + "1 " * n,
        "gb12": lambda n: "gb12 " * n,
        "ibanlines": lambda n: ("iban gb12" + nl) * n,
        "ibanspaces": lambda n: "iban " * n,
        "tabs": lambda n: "8765" + tab * n + "4321",
        "slashes": lambda n: "a/c" * n,
        "dashes": lambda n: "1-" * n + "account",
        "hex": lambda n: "ab" * n,
        "hexonly": lambda n: "0123456789abcdef" * (n // 8),
        "keywordlines": lambda n: ("account no 1" + nl) * n,
        "camel": lambda n: "Ab" * n + "Account",
    }
    for name, mk in makers.items():
        times = []
        for n in (2000, 16000):
            text = mk(n)
            best = min(_timed(text) for _ in range(2))
            times.append(best)
        assert times[1] <= 24 * times[0] + 0.5, (name, times)  # 8x the input: quadratic would be about 64x


def _timed(text):
    t0 = time.perf_counter()
    ic.bank_detail_findings(text, ON_SC)
    ic.unexplained_numbers(rec(), text, ON_SC)
    return time.perf_counter() - t0


# ---------------------------------------------------------------- round 5b: survivors of the first mutant run
@pytest.mark.parametrize("label", ["Phone", "Fax:", "Mob", "Mobile", "Ph", "Tel"])
def test_backstop_skips_only_the_phone_labelled_group(label):
    assert ic.unexplained_numbers(rec(), f"{label} 020 7946 0958", ON_SC) == []
    assert ic.unexplained_numbers(rec(), f"{label} 87654321", ON_SC) == ["87654321"]  # not phone-shaped
    assert ic.unexplained_numbers(rec(), f"Hotel {label} x 020 7946 0958", ON_SC) == ["02079460958"]  # a word between: not a phone group
    assert ic.unexplained_numbers(rec(), f"{label} 020 7946 0958 ring 87654321", ON_SC) == [
        "87654321"
    ]  # a label elsewhere does not hide it
    assert ic.unexplained_numbers(rec(), f"Sphone 87654321", ON_SC) == ["87654321"]  # noqa: F541


def test_backstop_on_file_and_join_set():
    on = "Acct 1234567890"
    assert ic.unexplained_numbers(rec(), "Pay 1234567890 now", on) == []
    assert ic.unexplained_numbers(rec(), "Pay 1234567890 now", ON_SC) == ["1234567890"]
    assert ic.unexplained_numbers(rec(), "ref 8765,4321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "ref 8765/4321", ON_SC) == [
        "87654321"
    ]  # round 5: the backstop joins like D10 does (any non-alphanumeric)


def test_iban_fallback_length_bounds():
    assert len(_kwib("iban xx12 3456 7890 123")) == 1
    assert _kwib("iban xx12 3456 7890 12") == []


def test_findings_are_unique():
    blob = base64.b64encode(b"Account No 87654321").decode()
    f = ic.bank_detail_findings("Account No 87654321 Ref " + blob, ON_SC)
    assert [x.candidate for x in f] == ["87654321"]  # the same number in the text and in its decoded form: one finding


# ---------------------------------------------------------------- round 6
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import unicodedata  # noqa: E402

from intake import confusables_data as cd  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_flag_codes_are_defined_once():
    codes = json.loads((ROOT / "config" / "exceptions.json").read_text(encoding="utf-8"))
    raw = (ROOT / "config" / "exceptions.json").read_text(encoding="utf-8")
    assert len(codes) == len(set(codes)) and raw.count('"D11"') >= 1
    emitted = {"D06", "D10", "L01", ic.BACKSTOP_FLAG}
    assert len(emitted) == 4
    assert ic.BACKSTOP_FLAG == "D12" and ic.BACKSTOP_FLAG not in codes  # D11 is supplier_mismatch; D12 is new
    assert {"D06", "D10"} <= set(codes)  # these two mean what exceptions.json says they mean


def test_backstop_default_on_and_malformed_record_flags_d12():
    sup = {"acme widgets ltd": ON_SC}
    assert ic.check(rec(), "Thanks. Ring 87654321", sup) == ["D12"]
    assert ic.check(rec(), "Thanks. Ring 87654321", sup, backstop=False) == []
    bad = rec()
    del bad["total_minor"]
    assert ic.check(bad, "Thanks", sup) == ["D06", "D12"]  # never an exception; a person looks
    with pytest.raises(KeyError):
        ic.unexplained_numbers(bad, "x", None)


def test_backstop_exact_match_only_and_look_alikes():
    f = rec(invoice_no="INV-876543210")
    assert ic.unexplained_numbers(f, "Invoice INV-876543210 ring 87654321", ON_SC) == ["87654321"]  # a substring explains nothing
    assert ic.unexplained_numbers(f, "Invoice INV-876543210", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "ring 8765432l", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "ring 87O5 4321", ON_SC) == ["87054321"]
    assert ic.unexplained_numbers(rec(), "Cust" + chr(0x3164) + "omer pay 87654321", ON_SC) == ["87654321"]


def test_backstop_covers_countries_outside_the_iban_table():
    assert ic.unexplained_numbers(rec(), "Pay MA64 011 519 000 0012 0500 0534 921 today", ON_SC) == [
        "64011519000001205000534921"
    ]  # round 7: on a line with a payment verb two-digit groups count, so `64` of `MA64` joins
    assert ic.unexplained_numbers(rec(), "Pay DZ58 0002 1000 0111 3000 0005 70", ON_SC) == [
        "580002100001113000000570"
    ]  # (same: `58` of `DZ58` joins; the line says Pay)


@pytest.mark.parametrize("ch", [" ", "-", ".", ",", ";", "_", "'", chr(0x2019), chr(0xB7)])
def test_backstop_joins_each_listed_separator(ch):
    assert ic.unexplained_numbers(rec(), f"x 8765{ch}4321", ON_SC) == ["87654321"]


def test_backstop_joins_every_non_alphanumeric_like_d10_but_not_a_letter_or_line_break():
    for ch in "/:|*+[]()#\\":
        assert ic.unexplained_numbers(rec(), f"x 8765{ch}4321", ON_SC) == ["87654321"], ch
    assert ic.unexplained_numbers(rec(), "x 8765k4321", ON_SC) == []


def test_phone_gap_pinned():
    assert not ic.bank_detail_changed("Bank: Tel:- 020 7946 0958", ON_SC)  # three separator characters (the space counts)
    assert ic.bank_detail_changed("Bank: Tel:-- 020 7946 0958", ON_SC)  # four: not a phone group
    assert not ic.bank_detail_changed("Bank: Mobile - 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed("Account Manager: 0207 000 0000", ON_SC)
    assert not ic.bank_detail_changed("Account Contact: 0207 000 0000", ON_SC)
    assert not ic.bank_detail_changed("Account Customer 0207 000 0000", ON_SC)
    assert not ic.bank_detail_changed("Account Customer:- 0207 000 0000", ON_SC)  # the longest label plus a full gap
    assert ic.bank_detail_changed("Account Customer:-- 0207 000 0000", ON_SC)
    assert ic.bank_detail_changed("Account Sales 0207 000 0000", ON_SC)
    assert not ic.bank_detail_changed("Account Tel:- 020 7946 0958", ON_SC)  # bare class: gap of three
    assert ic.bank_detail_changed("Account Tel:-- 020 7946 0958", ON_SC)  # four: not a phone group


def test_kw_gap_pinned():
    assert ic.bank_detail_changed("Sort - Code 876543", ON_SC)  # three separator characters between the words
    assert not ic.bank_detail_changed("Sort ---- Code 876543", ON_SC)
    assert not ic.bank_detail_changed("Sort -- Code 876543", ON_SC)  # four separator characters: not the keyword


def test_money_and_amount_word():
    assert not ic.bank_detail_changed("Account No: 12345678\nTotal 876543.21", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678\nTotal 8765432", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678\nTotal 876543.2", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678\nTotal 876543.211", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678\nSubtotalx 876543.21", ON_SC)


ISO_PINNED = (
    "ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl bm bn bo bq br bs bt bv bw by bz ca cc cd cf cg ch ci ck "
    "cl cm cn co cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg eh er es et fi fj fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs "
    "gt gu gw gy hk hm hn hr ht hu id ie il im in io iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv "
    "ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm "
    "pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr ss st sv sx sy sz tc td tf tg th tj tk tl tm tn to tr "
    "tt tv tw tz ua ug um us uy uz va vc ve vg vi vn vu wf ws xk ye yt za zm zw"
).split()


@pytest.mark.parametrize("cc", ISO_PINNED)
def test_bic_accepts_every_iso_country(cc):
    assert ic._bics(f"swift: abcd{cc}2l") == [f"abcd{cc}2l"]


def test_bic_shapes_and_labels():
    assert ic._bics("bic westgb2l") == ["westgb2l"] and ic._bics("bic westgb2lxxx") == ["westgb2lxxx"]
    assert ic._bics("bic westgb2lxx") == [] and ic._bics("bic westgb2") == [] and ic._bics("bic westgb2l1") == []
    assert ic._bics("bic westxx2l") == [] and ic._bics("bic wes1gb2l") == []
    assert ic._bics("swift address: westgb2l") == ["westgb2l"] and ic._bics("swift code westgb2l") == ["westgb2l"]
    assert ic._bics("swift" + "-" * 6 + "westgb2l") == ["westgb2l"] and ic._bics("swift" + "-" * 7 + "westgb2l") == []
    assert ic._bics("swift transfer") == []
    for word in ("number", "no", "id"):
        assert ic._bics(f"swift {word} westgb2l") == ["westgb2l"], word


LOOKALIKE_PINNED = {
    0x44C: "b",
    0x433: "r",
    0x1D00: "a",
    0x299: "b",
    0x1D04: "c",
    0x1D05: "d",
    0x1D07: "e",
    0xA730: "f",
    0x262: "g",
    0x29C: "h",
    0x26A: "i",
    0x1D0A: "j",
    0x1D0B: "k",
    0x29F: "l",
    0x1D0D: "m",
    0x274: "n",
    0x1D0F: "o",
    0x1D18: "p",
    0x280: "r",
    0xA731: "s",
    0x1D1B: "t",
    0x1D1C: "u",
    0x1D20: "v",
    0x1D21: "w",
    0x28F: "y",
    0x1D22: "z",
}


def test_confusables_table_walk():
    for cp, target in cd.CONFUSABLES.items():  # the data module, not the table under test
        if unicodedata.normalize("NFKD", chr(cp)) != chr(cp):
            continue  # NFKD already turns it into something else (fullwidth digits, ligatures)
        expected = "i" if cp in ic._I_LIKE else target
        if cp in ic._SEPLIKE:
            expected = "|"  # round 7: a letter that looks like a bar is read as one
        if unicodedata.category(chr(cp)) == "Nd":
            expected = str(unicodedata.decimal(chr(cp)))  # round 7: digits become ASCII before the confusables
        assert ic._f(chr(cp)) == expected, hex(cp)  # exactly the data entry (round 6: the looser test let U+0AE6 -> o survive a mutant)
    for cp in cd.CONFUSABLES:
        for c in (chr(cp).upper(), chr(cp).lower()):  # upper-casing a source still maps to ASCII
            if len(c) == 1 and ord(c) > 127:
                out = ic._f(c)
                assert out and out.isascii(), hex(ord(c))
    for cp, ch in LOOKALIKE_PINNED.items():
        assert ic._f(chr(cp)) == ch, hex(cp)


def test_capital_i_look_alikes_read_as_i():
    for cp in ic._I_LIKE:
        assert ic._f(chr(cp)) == "i", hex(cp)


def test_capital_greek_and_cyrillic_map_before_lower_casing():
    assert ic._f("Accou" + chr(0x39D) + "t") == "account"  # capital Nu looks like N
    assert ic._f(chr(0x392) + "ank") == "bank" and ic._f("S" + chr(0x397) + "ORT") != ""
    assert ic._f(chr(0x417)) in ("3", "z")
    assert ic._f(chr(0x406)) == "i" and ic._f(chr(0x399)) == "i"


IGNORABLE_SAMPLE = [
    0xAD,
    0x34F,
    0x61C,
    0x115F,
    0x1160,
    0x17B4,
    0x180B,
    0x180E,
    0x200B,
    0x200D,
    0x202A,
    0x202E,
    0x2060,
    0x2064,
    0x206F,
    0x3164,
    0xFE00,
    0xFE0F,
    0xFEFF,
    0xFFA0,
    0xFFF0,
    0x1BCA0,
    0x1D173,
    0xE0100,
]


@pytest.mark.parametrize("cp", IGNORABLE_SAMPLE)
def test_default_ignorable_code_points_are_deleted(cp):
    assert ic._f("ac" + chr(cp) + "count") == "account"
    assert ic.bank_detail_changed("Account No 8765" + chr(cp) + "4321", ON_SC)


def test_no_default_ignorable_is_missing():
    # every code point Python knows as Cf, plus the Hangul fillers, must be gone after the choke point
    missing = [
        hex(c)
        for c in range(0x110000)
        if unicodedata.category(chr(c)) == "Cf"
        and c not in ic._DELETE
        and not 0xE0020 <= c <= 0xE007E
        and ic._f("a" + chr(c) + "b") != "ab"
    ]
    assert missing == [], missing[:10]


def test_dash_list_is_pinned_and_reports_drift():
    running = {c for c in range(0x11000) if unicodedata.category(chr(c)) == "Pd"}
    assert running <= set(ic._DASHES), sorted(hex(c) for c in running - set(ic._DASHES))
    assert ic._DASHES[0x2212] == "-" and len(ic._DASHES) == 27


def test_supplier_key_is_nfkc():
    composed, decomposed = "M" + chr(0xFC) + "ller", "Mu" + chr(0x308) + "ller"
    assert ic._key(composed) == ic._key(decomposed) == ic._key("  M" + chr(0xFC) + "LLER ")
    assert ic.check(rec(supplier_name=decomposed), "", {ic._key(composed): ON_SC}, backstop=False) == []


def test_core_copy_agrees_on_overlapping_confusables():
    from intake.core_copy import _confusables as core

    diff = sorted(cp for cp, t in core.TABLE.items() if cp in cd.CONFUSABLES and len(t) == 1 and t.lower() != ic._CONF[cp])
    assert diff == [], [hex(c) for c in diff]
    raw_diff = sorted(cp for cp, t in core.TABLE.items() if cp in cd.CONFUSABLES and len(t) == 1 and t.lower() != cd.CONFUSABLES[cp])
    assert raw_diff == sorted(ic._I_LIKE[:6] + (0x10CA5,)), [
        hex(c) for c in raw_diff
    ]  # the seven capital-I look-alikes read as l in the Unicode data
    assert core.DATA_SHA256 == cd.SOURCE_SHA256 and core.DATA_VERSION == cd.SOURCE_VERSION


def test_confusables_provenance():
    assert len(cd.SOURCE_SHA256) == 64 and cd.SOURCE_VERSION == "18.0.0" and cd.ENTRIES == len(cd.CONFUSABLES) == 1582
    assert "unicode.org" in cd.SOURCE_URL and "Unicode License" in (cd.__doc__ or "")
    spec = importlib.util.spec_from_file_location("gen_confusables_wp3", ROOT / "tools" / "gen_confusables_wp3.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    with pytest.raises(ValueError):
        gen.parse("# Version: 19.0.0\n")
    pairs, version, _ = gen.parse("# Version: 18.0.0\n# Date: x\n0251 ;\t0061 ;\tMA\t# x\n0041 ;\t0042 ;\tMA\n")
    assert pairs == {0x251: "a"} and version == "18.0.0"
    src = os.environ.get("INTAKE_CONFUSABLES_SOURCE")  # optional: the downloaded file; a stale module then fails here
    if src and pathlib.Path(src).exists():
        raw = pathlib.Path(src).read_bytes()
        table, _, _ = gen.parse(raw.decode("utf-8"))
        assert table == cd.CONFUSABLES and hashlib.sha256(raw).hexdigest() == cd.SOURCE_SHA256


def test_hex_forms_with_every_separator():
    raw = b"Account No 87654321".hex()
    for sep in (".", "/", "  ", chr(10), ":", ";", ",", "-"):
        form = sep.join(raw[i : i + 2] for i in range(0, len(raw), 2))
        assert ic.bank_detail_changed("Ref " + form, ON_SC), repr(sep)


def test_wrapped_digits_both_directions():
    assert ic.bank_detail_changed("Account No 8765" + chr(10) + "4321", ON_SC)
    assert not ic.bank_detail_changed("Account No 1234" + chr(10) + "5678", ON_SC)
    assert not ic.bank_detail_changed("Account No 12345678" + chr(10) + "Thanks", ON_SC)


def test_look_alike_digits_per_run():
    assert ic._digitise("account no 12o4 5o78") == "account no 1204 5078"
    assert ic._digitise("account no 87o5 4321") == "account no 8705 4321"
    assert ic._digitise("hello 8o7b6s") == "hello 8o7b6s"  # three digits only: not read
    assert ic._digitise("8o7b6s5") == "8078655"
    assert ic._digitise("1234 5678") == "1234 5678" and ic._digitise("o oil bill") == "o oil bill"
    assert ic._digitise("1234 oil 5678") == "1234 oil 5678"  # a piece without a digit is not part of the run


@pytest.mark.parametrize("ch", ["-", "."])
def test_backstop_joins_spaced_hyphen_and_dot(ch):
    assert ic.unexplained_numbers(rec(), f"x 8765 {ch} 4321", ON_SC) == ["87654321"]


# ---------------------------------------------------------------- round 6b: backstop blocks, phone groups, record numbers
def test_backstop_does_not_join_table_columns_or_small_blocks():
    assert ic.unexplained_numbers(rec(), "L100 72 2.75 198.00 L101 24 2.02 48.48 L102 132 8.01 1057.32", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "Qty 12 24 36 48 60 72", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "x 87 654 3210", ON_SC) == []  # a two-digit block never joins
    assert ic.unexplained_numbers(rec(), "x 876 543 210", ON_SC) == ["876543210"]  # three-digit blocks do
    assert ic.unexplained_numbers(rec(), "x 8765 432", ON_SC) == []  # seven digits


def test_backstop_phone_group_and_money():
    for text in ("Fax: +44 (0) 20 7946 0958", "Tel +61 2 9999 8888", "Phone: 0207-946-0958 ext 5"):
        assert ic.unexplained_numbers(rec(), text, ON_SC) == [], text
    assert ic.unexplained_numbers(rec(), "Tel 0207 946 0958 or ring 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Total 1234567.89 USD", ON_SC) == []  # an amount
    assert ic.unexplained_numbers(rec(), "Tel x87654321", ON_SC) == ["87654321"]  # the group ends at the first letter
    assert ic.unexplained_numbers(rec(), "Amount 87654321", ON_SC) == ["87654321"]  # no cents: not an amount


@pytest.mark.parametrize("key", ["invoice_no", "po_ref", "invoice_date"])
def test_backstop_record_text_fields_explain_their_digits(key):
    label = {"invoice_no": "Invoice", "po_ref": "PO", "invoice_date": "Date"}[key]
    assert ic.unexplained_numbers(rec(**{key: "Z-87654321"}), f"{label} 87654321", ON_SC) == []
    assert ic.unexplained_numbers(rec(**{key: "Z-87654322"}), f"{label} 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(**{key: "Z-87654321"}), "see 87654321", ON_SC) == [
        "87654321"
    ]  # round 5: no invoice / PO / date word on the line


def test_backstop_record_amounts_explain_their_digits():
    assert ic.unexplained_numbers(rec(total_minor=87654321), "Total 876,543.21", ON_SC) == []
    assert ic.unexplained_numbers(rec(total_minor=87654322), "Total 876,543.21 ref 87654321", ON_SC) == ["87654321"]
    line = {"description": "x", "qty": 1, "unit_cost_minor": 87654321, "amount_minor": 12345679}
    assert ic.unexplained_numbers(rec(lines=[line]), "unit 87654321 amount 12345679", ON_SC) == []
    line = {"description": "x", "qty": 1, "unit_cost_minor": 11111111, "amount_minor": 22222222}
    assert ic.unexplained_numbers(rec(lines=[line]), "unit 87654321 amount 12345679", ON_SC) == ["87654321", "12345679"]
    assert ic.unexplained_numbers(rec(adjustments=[{"label": "t", "amount_minor": 87654321}]), "tax 87654321", ON_SC) == []
    assert ic.unexplained_numbers(rec(adjustments=[{"label": "t", "amount_minor": 87654322}]), "tax 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(total_minor=-87654321), "x 87654321", ON_SC) == []  # a credit: the sign is dropped


@pytest.mark.parametrize("word", ["total", "subtotal", "amount", "balance", "due", "price", "sum", "vat", "tax"])
def test_each_amount_word_skips_an_amount_on_the_next_line(word):
    nl = chr(10)
    assert not ic.bank_detail_changed("Account No: 12345678" + nl + f"{word} 876543.21", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678" + nl + f"x{word} 876543.21", ON_SC)
    assert ic.bank_detail_changed("Account No: 12345678" + nl + f"{word}x 876543.21", ON_SC)


@pytest.mark.parametrize("label", ["Tel", "Phone", "Fax", "Mob", "Mobile", "Ph", "manager", "contact", "customer"])
def test_bare_class_skips_a_number_after_each_label(label):
    if label in ("manager", "contact", "customer"):  # contact words skip any run
        assert not ic.bank_detail_changed(f"Account {label} 87654321", ON_SC)
    else:
        assert not ic.bank_detail_changed(f"Account {label} 020 7946 0958", ON_SC)
        assert ic.bank_detail_changed(f"Account {label} 87654321", ON_SC)  # plain digits after a phone word: flagged
    assert ic.bank_detail_changed(f"Account No {label} 87654321", ON_SC)  # a bank-specific keyword is never skipped
    assert ic.bank_detail_changed(f"Account x{label} 87654321", ON_SC)


def test_iban_keyword_token_cap_and_number_only_line_above():
    assert len(_kwib("iban xx " + "1 " * 32)[0]) == 34
    assert ic.bank_detail_changed("87,654,321" + chr(10) + "Account No", ON_SC)
    assert not ic.bank_detail_changed("Total 87654321" + chr(10) + "Account No", ON_SC)


def test_wrap_needs_a_digit_on_both_sides_of_the_break():
    assert not ic.bank_detail_changed("Account No 8765 -" + chr(10) + "4321", ON_SC)
    assert not ic.bank_detail_changed("Account No 8765" + chr(10) + "- 4321", ON_SC)


def test_backstop_wrapped_digits():
    assert ic.unexplained_numbers(rec(), "x 8765" + chr(10) + "4321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "x 8765 -" + chr(10) + "4321", ON_SC) == [
        "87654321"
    ]  # round 5: the line-break-as-space copy joins it


DEFAULT_IGNORABLE_RANGES = [
    (0xAD, 0xAD), (0x34F, 0x34F), (0x61C, 0x61C), (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180F), (0x200B, 0x200F),
    (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
]  # fmt: skip


def test_every_default_ignorable_code_point_vanishes():
    for lo, hi in DEFAULT_IGNORABLE_RANGES:
        for cp in range(lo, hi + 1):
            if 0xE0020 <= cp <= 0xE007E:
                continue  # tag letters are turned into visible ASCII by fold on purpose
            assert ic._f("ac" + chr(cp) + "count") == "account", hex(cp)


# ---------------------------------------------------------------- documented limits (pin today's behaviour; a change here is a decision, not a fix)
def _both(text, on_file=ON_SC, fields=None):
    return ic.bank_detail_changed(text, on_file), ic.unexplained_numbers(fields or rec(), text, on_file)


def test_documented_limit_blocks_under_three_digits_without_keyword():
    assert _both("Ring 87 65 43 21 please") == (False, [])  # no payment verb on the line: groups under 3 digits do not join
    assert _both("Pay to 87 65 43 21 please")[0]  # round 5: `Pay to` is a payment-instruction word, so the line is read as a label


def test_documented_limit_number_split_over_three_lines():
    nl = chr(10)
    assert _both("Account No 12" + nl + "34" + nl + "56" + nl + "78") == (False, [])


def test_documented_limit_spelled_out_digits():
    assert _both("Account No eight seven six five four three two one") == (False, [])


def test_documented_limit_wallet_and_payment_link_handles():
    assert _both("Pay to wallet bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh") == (False, [])
    assert _both("Pay at https://pay.example.com/p/a1b2c3d4") == (False, [])


def test_documented_limit_wide_phone_span():
    assert ic.unexplained_numbers(rec(), "Tel 0207 123 4567 87654321", ON_SC) == []  # the forged number follows a real phone number


def test_documented_limit_manager_contact_customer_before_a_number():
    for word in ("manager", "contact", "customer"):
        assert not ic.bank_detail_changed(f"Account {word}: 87654321", ON_SC)


def test_documented_limit_amount_looking_number():
    assert ic.unexplained_numbers(rec(), "pay 87654321.00 now", ON_SC) == []
    assert ic.bank_detail_changed("Account No 87654321.00", ON_SC)  # on a keyword line it is still a candidate


def test_the_mutation_runner_reads_no_secret_and_no_environment():
    import ast

    tree = ast.parse((ROOT / "tests" / "mutation_runner" / "mutate_invoicecheck.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] != "secret_store" and a.name != "os" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert "secret_store" not in (node.module or "") and not any(
                a.name in ("secret_store", "environ", "getenv") for a in node.names
            )
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("environ", "getenv", "secret_store")
        if isinstance(node, ast.Name):
            assert node.id not in ("environ", "getenv", "secret_store")


# ---------------------------------------------------------------- reopen fix pass: false D10 / D12 on clean invoices
@pytest.mark.parametrize(
    "label",
    [
        "Telephone",
        "Telephone No",
        "Tel.",
        "Tel No",
        "Phone No",
        "Phone Number",
        "Mobile No",
        "Cell",
        "GSM",
        "WhatsApp",
        "Telefono",
        "Telefon",
        "Telefoon",
        "Telefone",
        "Handy",
        "Tlf",
        "Fax",
    ],
)
def test_phone_label_variants_before_an_international_number(label):
    assert ic.unexplained_numbers(rec(), f"{label}: +44 20 7946 0958", ON_SC) == [], label
    assert ic.unexplained_numbers(rec(), f"{label} x +44 20 7946 0958", ON_SC) == ["79460958"], label  # a word between: not a phone group


def test_labels_inside_other_words_are_not_phone_labels():
    assert ic.unexplained_numbers(rec(), "Hotelephone 87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Telephonex 87654321", ON_SC) == ["87654321"]


def test_single_spaced_account_against_the_on_file_number():
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901 2 now", "456789012") == []
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901 3 now", "456789012") == ["45678901"]  # a different last digit is still flagged
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901", "456789012") == ["45678901"]  # a piece of the number, not the number


def test_word_boundaries_keep_the_labels_and_drop_the_lookalikes():
    for text in (
        "Raccoglitori 87654321",
        "Accenture 87654321",
        "Bankside 87654321",
        "Riverbank 87654321",
        "Accrued 87654321",
        "Accounts Payable 87654321",
        "accounts@x.example.com 87654321",
    ):
        assert not ic.bank_detail_changed(text, ON_SC), text
    for text in (
        "Acc 87654321",
        "Acct 87654321",
        "A/C 87654321",
        "Account 87654321",
        "Bank 87654321",
        "Bank: 87654321",
        "BankAccount 87654321",
        "bankacct 87654321",
        "BANKACC 87654321",
        "My.Account 87654321",
        "(acc) 87654321",
        "acc:87654321",
    ):
        assert ic.bank_detail_changed(text, ON_SC), text


def test_documented_decision_accounts_and_bankside_are_not_labels():
    assert ic.bank_detail_changed("Accounts 87654321", ON_SC) and ic.bank_detail_changed("Accounts: 87654321", ON_SC)  # digits right after
    assert not ic.bank_detail_changed("Accounts Payable 87654321", ON_SC) and not ic.bank_detail_changed(
        "accounts@x.example.com 87654321", ON_SC
    )
    assert not ic.bank_detail_changed("Bankside 87654321", ON_SC)


def test_the_real_routing_number_is_not_in_the_tests():
    for p in [*(ROOT / "tests" / "fixtures" / "d10").glob("*.txt"), ROOT / "tests" / "test_invoicecheck.py"]:
        assert "0210" + "00021" not in p.read_text(encoding="utf-8"), p.name


def test_short_block_next_to_a_run_joins_the_comparison_only():
    on = "Acct 1234567890"
    assert ic.unexplained_numbers(rec(), "Ring 12 3456 7890", on) == []  # leading short block
    assert ic.unexplained_numbers(rec(), "Ring 13 3456 7890", on) == ["34567890"]
    assert ic.unexplained_numbers(rec(), "Ring 12 x 3456 7890", on) == ["34567890"]  # a word between: not a neighbour
    assert ic.unexplained_numbers(rec(), "Ring 3456 7890 12", on) == [
        "34567890"
    ]  # a trailing block that does not complete the on-file number
    assert ic.unexplained_numbers(rec(), "Ring 3456 7890 12", "Acct 3456789012") == []
    assert ic.unexplained_numbers(rec(), "Ring 12 3456 7890 34", "Acct 123456789034") == []  # both sides


def test_label_lookalikes_inside_other_words_do_not_make_a_keyword():
    assert not ic.bank_detail_changed("xaccno 876543", ON_SC)
    assert not ic.bank_detail_changed("xacc#876543", ON_SC)
    assert ic.bank_detail_changed("acc no 876543", ON_SC) and ic.bank_detail_changed("acc#876543", ON_SC)


def test_longest_phone_label_with_a_full_gap_in_the_bare_class():
    assert not ic.bank_detail_changed("Account Telephone:- 020 7946 0958", ON_SC)
    assert ic.bank_detail_changed("Account Telephone:-- 020 7946 0958", ON_SC)


@pytest.mark.parametrize("label", ["Tel Nr", "Tel Num", "Phone Nr", "Phone Num"])
def test_number_word_after_a_phone_label(label):
    assert ic.unexplained_numbers(rec(), f"{label}: +44 20 7946 0958", ON_SC) == []


NEW_LABELS = ["Telephone", "Telefone", "Telefono", "Telefoon", "Telefon", "WhatsApp", "Handy", "Cell", "GSM", "Tlf"]


@pytest.mark.parametrize("word", NEW_LABELS)
def test_new_phone_labels_in_the_bank_and_bare_classes(word):
    assert not ic.bank_detail_changed(f"Bank: {word} 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed(f"Account {word} 020 7946 0958", ON_SC)
    assert ic.bank_detail_changed(f"Bank: {word} 87654321", ON_SC) and ic.bank_detail_changed(f"Account {word} 87654321", ON_SC)
    assert ic.bank_detail_changed(f"Account No {word} 87654321", ON_SC)  # a bank-specific keyword is never skipped
    assert ic.bank_detail_changed(f"Bank: x{word} 87654321", ON_SC)


def test_a_word_ending_in_acc_is_not_a_label():
    assert not ic.bank_detail_changed("xacc 87654321", ON_SC) and not ic.bank_detail_changed("Subxacct 87654321", ON_SC)
    assert ic.bank_detail_changed("x acc 87654321", ON_SC)


# ---------------------------------------------------------------- fix pass round 2: whole-prefix labels, phone-shaped skips, number words
@pytest.mark.parametrize(
    "text",
    [
        "Our new banking details: 87654321",
        "Banking 87654321",
        "Bankverbindung 87654321",
        "bankverbindung: 87654321",
        "Bankleitzahl 37040044",
        "Bankgiro 87654321",
        "Bankdetails 87654321",
        "BANKDETAILS 87654321",
        "Bank details 87654321",
        "Bankdaten 87654321",
        "Bankname 87654321",
        "Bankinfo 87654321",
        "Bankinformation 87654321",
        "Bank information: 87654321",
        "Accountholder 87654321",
        "Account holder 87654321",
        "Accountname 87654321",
        "Accounts 87654321",
        "Accounts: 87654321",
        "ACCOUNTS - 87654321",
        "Accts 87654321",
        "A-C 87654321",
        "a-c: 87654321",
        "A/C 87654321",
    ],
)
def test_whole_prefix_labels_are_found(text):
    assert ic.bank_detail_changed(text, ON_SC), text


@pytest.mark.parametrize(
    "text",
    [
        "Raccoglitori 87654321",
        "Accenture 87654321",
        "Bankside 87654321",
        "Riverbank 87654321",
        "Accrued 87654321",
        "Accountant 87654321",
        "Accountability 87654321",
        "Accounts Payable 87654321",
        "Accounts Payable: 87654321",
        "accounts@x.example.com 87654321",
        "accounts@x.example.com",
        "Bankruptcy 87654321",
        "BA-C 87654321",
        "Banked 87654321",
        "Bankers 87654321",
    ],
)
def test_lookalike_words_are_not_labels(text):
    assert not ic.bank_detail_changed(text, ON_SC), text


def test_documented_limit_compound_bank_words_in_front_are_not_labels():
    assert not ic.bank_detail_changed("Hausbank 87654321", ON_SC)
    assert not ic.bank_detail_changed("Postbank 87654321", ON_SC)
    assert not ic.bank_detail_changed("Accounts 8765432", ON_SC)  # under eight digits after Accounts
    assert ic.bank_detail_changed("Accounts, 87654321", ON_SC)  # a comma and a space: up to three separator characters are allowed


def test_documented_limit_camelcase_company_names_with_bank_in_them():
    assert ic.bank_detail_changed(
        "RiverBank Ltd 87654321", ON_SC
    )  # false D10, accepted: the camel pass cannot tell RiverBank from SupplierBank
    assert ic.bank_detail_changed("BankSide Ltd 87654321", ON_SC)
    assert ic.bank_detail_changed("SupplierBank 87654321", ON_SC)


def test_a_phone_word_hides_only_a_phone_shaped_run():
    for text in (
        "Bank: Cell 87654321",
        "Bank: Ph 87654321",
        "Account Handy 87654321",
        "Bank: Mob 87654321",
        "Bank account (GSM) 87654321",
        "Account Tel 87654321",
    ):
        assert ic.bank_detail_changed(text, ON_SC), text
        assert ic.unexplained_numbers(rec(), text, ON_SC) == ["87654321"], text  # and D12 keeps it
    for text in (
        "Bank: Cell 020 7946 0958",
        "Account Handy +44 20 7946 0958",
        "Bank: Mob (020) 7946 0958",
        "Bank: Ph 0207946095",
        "Bank account (GSM) 07700 900123",
    ):
        assert not ic.bank_detail_changed(text, ON_SC), text
    assert ic.unexplained_numbers(rec(), "Cell 020 7946 0958", ON_SC) == []


def test_phone_shape_rules_one_by_one():
    assert not ic.bank_detail_changed("Bank: Tel 087654321", ON_SC)  # a leading 0
    assert ic.bank_detail_changed("Bank: Tel 07654321", ON_SC)  # eight digits are not a phone (round 4; the old hole is closed)
    assert not ic.bank_detail_changed("Bank: Tel +44 7700 900123", ON_SC)  # + with nine or more digits
    assert not ic.bank_detail_changed("Bank: Tel (020) 7946 0958", ON_SC)  # (digits) then more digits
    assert not ic.bank_detail_changed("Bank: Tel 212 555 0123", ON_SC)  # three groups, ten digits
    assert not ic.bank_detail_changed("Bank: Tel 1 800 555 0199", ON_SC)  # a one-digit first group
    assert ic.bank_detail_changed("Bank: Tel +87654321", ON_SC)  # + with eight digits
    assert ic.bank_detail_changed("Bank: Tel (87654321", ON_SC)
    assert ic.bank_detail_changed("Bank: Cell (87654321)", ON_SC)  # all digits inside the brackets
    assert ic.bank_detail_changed("Bank: Tel 8765 4321", ON_SC)  # two groups
    assert ic.bank_detail_changed("Bank: Tel 87654321", ON_SC)
    assert ic.bank_detail_changed("Bank: Mob 87654321 1 2", ON_SC)  # one-digit groups after the first
    assert ic.bank_detail_changed("Bank: Mob 8765 43 21", ON_SC)  # three groups but eight digits
    assert ic.bank_detail_changed("Account Cell 87 65 43 21", ON_SC)
    assert ic.bank_detail_changed("Account Cell 87654321 12345678901", ON_SC)  # sixteen digits in two groups is not a phone


def test_number_word_after_a_phone_word_in_the_bank_and_bare_classes():
    assert not ic.bank_detail_changed("Account Tel No: 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed("Account Dept Tel No: 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed("Account Tel Nr: +44 20 7946 0958", ON_SC)
    assert not ic.bank_detail_changed("Bank: Phone Number 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed("Bank: Mobile Num +44 20 7946 0958", ON_SC)
    assert ic.bank_detail_changed("Account Tel No: 87654321", ON_SC)
    assert ic.bank_detail_changed("Bank: Phone Number 87654321", ON_SC)
    assert ic.bank_detail_changed("Bank: Tel Nox 020 7946 0958", ON_SC)  # a word that only starts like a number word


def test_comparison_forms_need_a_single_space_and_no_quantity_word():
    on = "Acct 945678901"
    assert ic.unexplained_numbers(rec(), "Pay 9 45678901", on) == []  # documented hole: a lone leading block is read as part of the number
    assert ic.unexplained_numbers(rec(), "Qty 9 45678901", on) == ["45678901"]
    assert ic.unexplained_numbers(rec(), "9 x 45678901", on) == ["45678901"]
    assert ic.unexplained_numbers(rec(), "Pay 9-45678901", on) == []  # a hyphen inside the number: one block, the whole number
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901 2", "Acct 456789012") == []
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901-2", "Acct 456789012") == []  # the hyphen joins 8901-2 into one block
    assert ic.unexplained_numbers(rec(), "Pay 4567 8901,2", "Acct 456789012") == ["45678901"]  # a comma is not a single space


def test_aba_number_is_gone_from_the_test_sources_of_this_pass():
    real = "0210" + "00021"
    for p in [*(ROOT / "tests" / "fixtures" / "d10").glob("*.txt"), ROOT / "tests" / "test_invoicecheck.py"]:
        assert real not in p.read_text(encoding="utf-8"), p.name


def test_accounts_label_edges_and_singular_compounds():
    assert not ic.bank_detail_changed("Accounts 1234567 x 87654321", ON_SC)  # seven digits after Accounts: not the label
    assert ic.bank_detail_changed("Accounts - 87654321", ON_SC)  # three separator characters
    assert not ic.bank_detail_changed("Accounts -- 87654321", ON_SC)  # four
    assert ic.bank_detail_changed("A-C No 876543", ON_SC) and ic.bank_detail_changed("A/C No 876543", ON_SC)
    assert ic.bank_detail_changed("Bankdetail 87654321", ON_SC) and ic.bank_detail_changed("Bankdetails 87654321", ON_SC)


@pytest.mark.parametrize("numword", ["no", "nr", "num", "number"])
def test_every_number_word_after_a_phone_word_in_both_classes(numword):
    assert not ic.bank_detail_changed(f"Bank: Tel {numword}: 020 7946 0958", ON_SC)
    assert not ic.bank_detail_changed(f"Account Phone {numword} +44 20 7946 0958", ON_SC)
    assert ic.bank_detail_changed(f"Bank: Tel {numword}: 87654321", ON_SC)
    assert ic.bank_detail_changed(f"Account Phone {numword} 87654321", ON_SC)


def test_longest_label_number_word_and_both_gaps_still_reach_back():
    longest = "Account Telephone:- Number:- 020 7946 0958"  # 9 + 3 + 6 + 3 characters before the digits
    assert not ic.bank_detail_changed(longest, ON_SC)
    assert not ic.bank_detail_changed(longest.replace("Account", "Bank"), ON_SC)
    assert ic.bank_detail_changed("Account Telephone:-- Number:- 020 7946 0958", ON_SC)


@pytest.mark.parametrize("word", ["qty", "quantity", "pcs", "unit", "units", "menge", "stk", "cant", "x"])
def test_each_quantity_word_stops_a_leading_block_joining_the_comparison(word):
    on = "Acct 945678901"
    assert ic.unexplained_numbers(rec(), f"{word} 9 45678901", on) == ["45678901"], word
    assert ic.unexplained_numbers(rec(), f"{word}z 9 45678901", on) == [], word  # a longer word is not a quantity word


def test_phone_text_signs_in_the_second_warning():
    assert ic.unexplained_numbers(rec(), "Tel +44 20 7946 0958", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "Tel (020) 7946 0958", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "Tel 087654321", ON_SC) == []
    assert ic.unexplained_numbers(rec(), "Tel +87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Tel (87654321", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Bank: Cell (87654321)", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Bank: Mob 87654321 1 2", ON_SC) == ["87654321"]
    assert ic.unexplained_numbers(rec(), "Tel 020 7946 0958 x87654321", ON_SC) == [
        "87654321"
    ]  # starts right after the letter that ended the group


def test_a_comma_is_not_the_single_space_of_a_comparison_form():
    on = "Acct 945678901"
    assert ic.unexplained_numbers(rec(), "Pay 9,45678901", on) == ["45678901"]
    assert ic.unexplained_numbers(rec(), "Pay 9 45678901", on) == []


def test_phone_label_inside_a_word_or_after_a_letter_does_not_hide_a_phone_shaped_number():
    assert ic.unexplained_numbers(rec(), "Hotelephone 020 7946 0958", ON_SC) == ["02079460958"]
    assert ic.unexplained_numbers(rec(), "Tel x020 7946 0958", ON_SC) == ["02079460958"]  # the group ends at the first letter
    assert ic.unexplained_numbers(rec(), "Tel 020 7946 x87654321", ON_SC) == [
        "87654321"
    ]  # a number that starts right after the letter that ended the group
    assert ic.unexplained_numbers(rec(), "Tel 020 7946 0958", ON_SC) == []


# ---------------------------------------------------------------- round 3: one phone-shape predicate, grouped Accounts, more bank compounds
GENUINE_PHONES = [
    "020 7946 0958",
    "+44 20 7946 0958",
    "(020) 7946 0958",
    "+49 30 901820",
    "212 555 0123",
    "1 800 555 0199",
    "+1 (212) 555 0123",
    "07700 900123",
]
FAKE_PHONES = [
    "87654321",
    "87654321 1 2",
    "8765 43 21",
    "87 65 43 21",
    "+87654321",
    "(87654321)",
    "(87654321",
    "8765 4321",
    "87-65-43-21 1",
]


@pytest.mark.parametrize("label", ["Tel", "Phone", "Mob", "Mobile", "Cell", "GSM", "Handy", "WhatsApp", "Fax", "Telephone No", "Tel Nr"])
def test_one_phone_predicate_for_d10_and_d12(label):
    for phone in GENUINE_PHONES:
        assert not ic.bank_detail_changed(f"Bank: {label}: {phone}", ON_SC), (label, phone)
        assert not ic.bank_detail_changed(f"Account Dept {label}: {phone}", ON_SC), (label, phone)
        assert ic.unexplained_numbers(rec(), f"{label}: {phone}", ON_SC) == [], (label, phone)
    for fake in FAKE_PHONES:
        assert ic.bank_detail_changed(f"Bank: {label}: {fake}", ON_SC), (label, fake)
        assert ic.bank_detail_changed(f"Account {label} {fake}", ON_SC), (label, fake)


def test_phone_predicate_directly():
    for phone in GENUINE_PHONES:
        assert ic._phone_text("Tel " + phone), phone
    for fake in FAKE_PHONES:
        assert not ic._phone_text("Tel " + fake), fake
    assert not ic._phone_text("Tel") and not ic._phone_text("Tel +")
    assert ic._phone_text("Tel 0123456789012345")  # a leading 0 with one long group is a phone
    assert not ic._phone_text("Tel 0123456789012345 6")  # a one-digit group after it is not
    assert not ic._phone_text("Tel 123 4567 8901 23456")  # sixteen digits in four groups
    assert ic._phone_text("Tel 123 4567 8901 2345")  # fifteen
    assert not ic._phone_text("Tel 123 45 678")  # eight digits in three groups
    assert ic._phone_text("Tel 123 45 6789")  # nine


def test_documented_limit_two_digit_groups_are_invisible_to_the_second_warning():
    assert (
        ic.unexplained_numbers(rec(), "Bank: Mob 8765 43 21", ON_SC) == []
    )  # D10 flags it (see above); D12 ignores groups under three digits
    assert ic.unexplained_numbers(rec(), "Account Cell 87 65 43 21", ON_SC) == []


@pytest.mark.parametrize(
    "text",
    [
        "Accounts: 8765 4321",
        "Accounts 87-65-43-21",
        "Accounts: 87 65 43 21",
        "Accounts No: 87654321",
        "Accounts No 876543",
        "Account No 876543",
        "bankaccounts: 87654321",
        "banknumber 87654321",
        "bankcode: 87654321",
        "Bankno 87654321",
        "Banknr 87654321",
        "Bankverbindungen 87654321",
        "A / C 87654321",
        "A /C 87654321",
        "a - c 87654321",
    ],
)
def test_grouped_accounts_and_more_bank_compounds_are_found(text):
    assert ic.bank_detail_changed(text, ON_SC), text


@pytest.mark.parametrize(
    "text",
    [
        "Accounts Payable No 123456",
        "accounts@x.example.com 87654321",
        "Accounts Dept 8765 4321",
        "Accounts 8765 432",
        "Bankcodex 87654321",
        "Banknumbers 87654321",
        "BA C 87654321",
        "A 5 C 87654321",
    ],
)
def test_the_new_labels_keep_the_lookalikes_out(text):
    assert not ic.bank_detail_changed(text, ON_SC), text


def test_documented_limit_residual_spellings_have_no_end():
    assert not ic.bank_detail_changed("B A N K 87654321", ON_SC)  # spaced letters


def test_accounts_hash_and_plural_no_are_labels():
    assert ic.bank_detail_changed("Accounts #876543", ON_SC)
    assert ic.bank_detail_changed("Account #876543", ON_SC)
    assert ic.bank_detail_changed("Accounts No 876543", ON_SC)
    assert not ic.bank_detail_changed("Accounts Payable #876543", ON_SC)


def test_phone_shape_edges_for_brackets_plus_and_two_groups():
    assert ic.bank_detail_changed("Bank: Tel (876543215", ON_SC)  # ( without a closing bracket is not a phone
    assert not ic.bank_detail_changed("Bank: Tel (0) 876543215", ON_SC)
    assert not ic.bank_detail_changed("Bank: Tel +876543215", ON_SC)  # + with nine digits
    assert not ic.bank_detail_changed("Bank: Tel (87) 6543215", ON_SC)  # (digits) then more digits, nine in all
    assert ic.unexplained_numbers(rec(), "Tel (87) 6543215", ON_SC) == [] and ic.unexplained_numbers(rec(), "Tel +876543215", ON_SC) == []
    assert ic.bank_detail_changed("Bank: Tel 8765 43210", ON_SC)  # two groups, nine digits: not a phone
    assert ic.bank_detail_changed("Bank: Tel 87654321 123", ON_SC)
    assert ic.unexplained_numbers(rec(), "Tel 87654321 123", ON_SC) == ["87654321123"]


# ---------------------------------------------------------------- round 4: never silent next to a bank word; the first of 0-9 + ( decides
M1_INPUTS = ["Bank: Mob 87654321 (1)", "Bank: Tel 87654321 +1", "Account Cell 87654321 (5) 6", "Bank: Tel 8765 4321 (0)"]
PADDED = ["Bank: Tel 8765 4321 00", "Bank: Tel 87654321 00 00", "Bank: Tel 123 456 789", "Bank: Tel 0123 4567", "Bank: Tel 0 87654321"]


@pytest.mark.parametrize("text", M1_INPUTS + PADDED)
def test_sign_bracket_after_number_and_padding_are_not_phones(text):
    assert ic.bank_detail_changed(text, ON_SC), text
    assert "D10" in ic.check(rec(), text, SUP_SC), text


@pytest.mark.parametrize("text", ["Tel 0123 4567", "Tel 0 87654321", "Tel 8765 4321 00", "Tel 87654321 00 00"])
def test_padded_numbers_without_a_bank_word_reach_d12(text):
    assert ic.unexplained_numbers(rec(), text, ON_SC), text


def test_predicate_first_character_decides():
    assert not ic._phone_text("Tel 87654321 (1)") and not ic._phone_text("Tel 87654321 +1")
    assert not ic._phone_text("Tel 8765 4321 (0)") and not ic._phone_text("Tel 87654321 (5) 6")
    assert ic._phone_text("Tel +44 20 7946 0958") and ic._phone_text("Tel (0) 20 7946 0958") and ic._phone_text("Tel (+44) 20 7946 0958")
    assert not ic._phone_text("Tel (1) 87654321")


@pytest.mark.parametrize(
    "phone", ["020 7946 0958", "+44 20 7946 0958", "(020) 7946 0958", "212 555 0123", "1 800 555 0199", "07700 900123"]
)
@pytest.mark.parametrize("bank", ["Bank: Tel {}", "Account Dept Tel: {}", "Bank transfer only. Tel {}"])
def test_phone_next_to_a_bank_word_is_d12_never_silent(phone, bank):
    text = bank.format(phone)
    assert not ic.bank_detail_changed(text, ON_SC), text  # D10 still skips the phone
    assert ic.unexplained_numbers(rec(), text, ON_SC), text  # D12: a person looks
    assert "D12" in ic.check(rec(), text, SUP_SC) and "D10" not in ic.check(rec(), text, SUP_SC)


def test_phone_without_a_bank_word_stays_skipped():
    for phone in ["020 7946 0958", "+44 20 7946 0958", "212 555 0123", "07700 900123"]:
        assert ic.unexplained_numbers(rec(), f"Tel {phone}", ON_SC) == [], phone
        assert ic.unexplained_numbers(rec(), f"Customer service\nTel {phone}@Thank you", ON_SC) == [], phone


def test_bank_word_on_a_neighbour_line_counts():
    phone = "Tel 020 7946 0958"
    assert ic.unexplained_numbers(rec(), "Bank:\n" + phone, ON_SC)  # the line below the keyword line (D10 reads it)
    assert ic.unexplained_numbers(rec(), phone + "\nBank:", ON_SC)  # the line above
    assert ic.unexplained_numbers(rec(), "Bank:\n\n" + phone, ON_SC)  # a blank line between
    assert ic.unexplained_numbers(rec(), "Bank:\nx\nx\nx\n" + phone, ON_SC) == []  # too far for D10 too


def test_phone_label_on_the_previous_line_is_not_seen():
    assert ic.unexplained_numbers(rec(), "Tel:\n020 7946 0958", ON_SC) == ["02079460958"]  # documented: the label must be on the line
    assert ic.bank_detail_changed("Bank:\n87654321", ON_SC)


def test_round4_survivors_bracket_anchor_two_digit_lead_distance_and_camel():
    assert not ic._phone_text("Tel (1) 87654321 (+1)")  # only the bracket at the first position counts
    assert ic._phone_text("Tel 02 9999 8888") and not ic.bank_detail_changed("Bank: Tel 02 9999 8888", ON_SC)  # two-digit leading-0 group
    assert ic.unexplained_numbers(rec(), "Bank:\nx\nTel 020 7946 0958", ON_SC) == []  # two lines below: D10 does not read it either
    assert ic.unexplained_numbers(rec(), "SupplierBank: Tel 020 7946 0958", ON_SC)  # the CamelCase pass sees the bank word
    assert ic.unexplained_numbers(rec(), "IBAN see below. Tel 020 7946 0958", ON_SC)
