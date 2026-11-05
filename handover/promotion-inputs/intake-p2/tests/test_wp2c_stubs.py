"""Day-1 batch of WP2c: the closed vocabulary, the self-check codes, the phrases, the seam and the stub surfaces (design-v6.1 B3-B6)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from intake import coreredact, flags, invoicecheck, mask, phrases, selfcheck_codes, trace_vocab

MODULES = ("trace_vocab", "selfcheck_codes", "flags", "phrases", "mask", "tracelog", "coreredact")


def _imported_alone(module: str) -> set[str]:
    code = f"import sys, intake.{module}; print(' '.join(sorted(m for m in sys.modules if m.startswith('intake.'))))"
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    return set(out.split())


@pytest.mark.parametrize("module", MODULES)
def test_import_graph_has_no_cycle(module):
    assert f"intake.{module}" in _imported_alone(module)  # a cycle raises ImportError in the fresh interpreter, which fails check=True


def test_the_leaf_modules_import_nothing_beyond_their_stated_leaves():
    assert _imported_alone("trace_vocab") == {"intake.trace_vocab"}
    assert _imported_alone("selfcheck_codes") == {"intake.selfcheck_codes"}
    assert _imported_alone("phrases") == {"intake.phrases", "intake.flags", "intake.selfcheck_codes"}


def test_the_closed_set_of_self_check_codes():
    assert len(selfcheck_codes.SELFCHECK_CODES) == 12 and len(set(selfcheck_codes.SELFCHECK_CODES)) == 12
    assert "body_unsafe" not in selfcheck_codes.SELFCHECK_CODES  # a model error, not an item sub-reason
    assert set(selfcheck_codes.PLAIN) == set(selfcheck_codes.SELFCHECK_CODES)
    assert set(selfcheck_codes.FLAG_OF) == set(selfcheck_codes.SELFCHECK_CODES) - {"body_not_reproducible"}
    assert {c for c, f in selfcheck_codes.FLAG_OF.items() if f == "M02"} == {"mark_like_text", "forged_mark"}
    assert all(flags.is_reject_only(f) for f in selfcheck_codes.FLAG_OF.values())
    assert "doc_sha_mismatch" in selfcheck_codes.FLAG_OF and "mask_too_large" in selfcheck_codes.FLAG_OF


def test_self_check_failed_carries_the_code_only_and_refuses_an_unknown_one():
    e = selfcheck_codes.SelfCheckFailed("forged_mark")
    assert (e.code, e.args) == ("forged_mark", ("forged_mark",))
    with pytest.raises(ValueError):
        selfcheck_codes.SelfCheckFailed("body_unsafe")


def test_phrases_hold_the_flag_meanings_the_codes_and_the_fixed_sentences():
    ph = phrases.phrases()
    assert flags.FLAGS["M01"].meaning in phrases.texts() and flags.FLAGS["M02"].meaning in phrases.texts()
    assert all(selfcheck_codes.PLAIN[c] in phrases.texts() for c in selfcheck_codes.PLAIN)
    assert {"bank_ok", "bank_changed", "bank_none_found", "bank_no_details_on_file", "bank_not_run", "manual_path"} <= set(ph)
    assert len(phrases.texts()) == len(ph)  # no two keys share a sentence
    with pytest.raises(TypeError):
        ph["x"] = "y"  # type: ignore[index]


def test_the_trace_vocabulary_day_one_content():
    v = trace_vocab
    assert "trace_refused" in v.WARN_REASONS and "trace_refused" in v.REASON_WORDS and "trace_refused" not in v.RESULTS
    assert v.REASON_WORDS == v.WARN_REASONS + ("gate_refused", "selfcheck_failed", "approved", "rejected", "exported")
    assert set(v.DERIVED_STEPS) | set(v.LOG_ONLY_STEPS) <= set(v.STEPS)
    assert set(v.COUNT_KEYS) <= set(v.FIELDS) and set(v.FREE_TEXT_FIELDS) <= set(v.FIELDS)
    assert all(len(set(t)) == len(t) for t in (v.STEPS, v.EVENTS, v.COUNT_KEYS, v.FIELDS))
    assert {"digit8", "at_sign", "digit13_19", "mixed20"} <= set(v.COUNT_KEYS)


def test_the_masked_text_cap_is_a_complete_constant_and_the_stub_names_exist():
    assert (mask.MASKED_MAX_CHARS, mask.MASK_MAX_LINE_CHARS) == (40000, 2000)
    for name in ("detect", "neutralise", "find_hidden", "restore", "residual_warn", "spellings", "bank_check_outcome"):
        assert callable(getattr(mask, name))


@pytest.mark.parametrize(
    "line",
    [
        "Sort Code 20-00-00",
        "IBAN GB29",
        "Acct12345678",
        "BANKNAME: x",
        "Routing 021000021",
        "KONTO 12345678",
        "BankAccountNo 1",
        "Bank:",
        "BSB 062000",
    ],
)
def test_bank_word_in_is_the_d10_keyword_rule(line):
    assert invoicecheck.bank_word_in(line) and invoicecheck.bank_word_in("Invoice 1\n" + line + "\nTotal 5.00")


@pytest.mark.parametrize("text", ["", "Invoice INV-1001 total 33.00", "Postcode SW1A 1AA", "Invoice code 12345678", "Contoso Ltd"])
def test_bank_word_in_is_false_without_a_bank_word(text):
    assert not invoicecheck.bank_word_in(text)


def test_bank_word_in_sees_every_line_break_kind_and_the_folded_variants():
    assert invoicecheck.bank_word_in("a" + chr(0x2028) + "sort code 1")
    assert invoicecheck.bank_word_in("S" + chr(0x200B) + "ort code")  # zero-width character
    assert invoicecheck.bank_word_in("".join(chr(ord(c) + 0xFEE0) if c != " " else c for c in "IBAN"))  # fullwidth letters
    assert "bank_word_in" in invoicecheck.__all__


def test_the_core_redactor_seam_returns_kind_and_original():
    got = coreredact.find("Questions: jo@acme.example.com")
    assert ("EMAIL", "jo@acme.example.com") in got
    assert coreredact.find("nothing sensitive here") == []
