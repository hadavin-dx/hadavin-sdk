"""Mutation runner for src/intake/mask.py (WP2c P2). Breaks one rule at a time in the real file, runs the named test of tests/test_mask_kernel.py (then the
whole file if that did not fail), and restores the file in a ``finally``.

Run from the repository root:  python tests/mutation_runner/mutate_mask.py [--only NAME[|NAME...]] [--skip-baseline]
(runs tests/test_mask_kernel.py and test_mask_review1.py to test_mask_review4.py; a name list that matches no mutant exits 2)
  KILLED     name :: the named test failed        (the expected result)
  ELSEWHERE  name :: another test of the file failed (the named test is stale or weak: counts as a failure of the run)
  SURVIVED   name :: no test noticed               (a failure of the run)
  CRASH      name :: the pattern was not found     (proves nothing: fix the list)
Exit code 0 only when every mutant that ran is KILLED and at least one ran.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src" / "intake" / "mask.py"
TIMEOUT_S = 900  # one pytest run
TESTS = (
    "tests/test_mask_kernel.py",
    "tests/test_mask_review1.py",
    "tests/test_mask_review2.py",
    "tests/test_mask_review3.py",
    "tests/test_mask_review4.py",
    "tests/test_mask_review5.py",
    "tests/test_mask_review6.py",
    "tests/test_mask_iban_fuzz.py",
)

# (name, old text, new text, pytest -k expression naming the test that must kill it)
MUTANTS = [
    ("masker returns text unchanged", 'model_text = "".join(out)', "model_text = text", "bank_words or amount_with"),
    ("locator returns nothing", "if n == 0 or n > len(sk.chars):", "if True:", "bank_words or r1_unlocated"),
    (
        "end-neighbour rule removed",
        "if not ends or (_outside_ok(fp_, a, -1, sk.outside) and _outside_ok(fp_, b, 1, sk.outside)):",
        "if True:",
        "end_rule",
    ),
    (
        "gap rule widened to letters",
        "_DIGITS, None, _DIGITS, 1, True)",
        "_DIGITS, None, _DIGITS, 1, False)",
        "gap_rule",
    ),
    (
        "locator fold replaced by casefold only",
        'return _WS_RUN.sub(" ", t.replace("\\r\\n", "\\n").replace("\\r", "\\n"))',
        "return c.casefold()",
        "fold_matches or zero_width",
    ),
    ("R1b removed", "if any(len(p) >= 3 and p not in hidden_cands for p in pieces):", "if False:", "r1b"),
    ("money occurrence never recognised (R2 removed)", "m = _overlaps(money, *o)", "m = False", "amount_with_the_same_digits"),
    (
        "kept-visible drop uses overlap instead of containment (errata 88)",
        "if not any(a <= h[0] and h[1] <= b for a, b in kept)",
        "if not any(h[0] < b and a < h[1] for a, b in kept)",
        "next_to_a_kept_string",
    ),
    (
        "kept-visible list ignored (a1 sees the amount as a leak)",
        "if hidden_hits(h, vals, fresh.kept_visible_texts):",
        "if hidden_hits(h, vals):",
        "drops_hits_inside_kept",
    ),
    (
        "rule (iv) widened: bank-context line accepted as id occurrence",
        "is_id[o] = (not force) and (not lines.ctx[li]) and _id_shaped(text, *o)",
        "is_id[o] = (not force) and _id_shaped(text, *o)",
        "header_inv",
    ),
    (
        "next-line rule widened to every non-blank line of three",
        "self.ctx[j] = True\n                    break",
        "self.ctx[j] = True",
        "first_non_blank_line_after",
    ),
    ("line cap removed", 'any(len(ln) > MASK_MAX_LINE_CHARS for ln in text.split("\\n"))', "False", "line_over_cap"),
    ("mark-like check skipped (a0)", "if _MARK_LIKE.search(canonical(text)):", "if False:", "mark_like"),
    (
        "a2 skipped",
        "if det.unlocated or any(nt[sp.start : sp.end] != NEUTRAL for sp in det.spans):",
        "if det.unlocated:",
        "a2_and_a3_are_separate",
    ),
    (
        "a3 skipped",
        "if sorted(marks) != sorted(look) or any(m not in ok for m in marks) or len(set(marks)) != len(ok):",
        "if False:",
        "a2_and_a3_are_separate",
    ),
    (
        "neutralise skipped",
        "return _MARK.sub(lambda m: NEUTRAL if m.group(0) in ok else m.group(0), text)",
        "return text",
        "kept_visible_is_position_based",
    ),
    ("BodyCheck always passes", "return self._check(body)", "return None", "body_check"),
    ("BodyCheck text tie skipped", "        if not same:", "        if False:", "ties_text"),
    ("BodyCheck doc_sha tie removed", 'if data.get("doc_sha") != self._source_sha256:', "if False:", "ties_text"),
    (
        "(b) canonical-only",
        "if strict != look or any(m not in ok for m in strict):",
        "if any(m not in ok for m in strict):",
        "forged_marks",
    ),
    ("path built from AI keys", 'name = k if sub is not None else "other"', "name = k", "thousand_marks"),
    (
        "merge priority swapped",
        "kind = min(last.kind, s.kind, key=PRIORITY.index)",
        "kind = max(last.kind, s.kind, key=PRIORITY.index)",
        "merge_priority",
    ),
    (
        "spellings without base64 and hex",
        "for name in SPELLING_NAMES if len(value) >= 6 else _SHORT_NAMES:",
        'for name in tuple(n for n in SPELLING_NAMES if not n.startswith(("base64", "hex"))) if len(value) >= 6 else _SHORT_NAMES:',
        "spellings_always",
    ),
    ("field rule skipped", "if sp.kind not in _FREE_TEXT_KINDS or generic not in _FREE_TEXT_PATHS:", "if False:", "field_rule"),
    (
        "(c) recompute skipped",
        'if sig(fresh) != sig(masked) or left[0] or any(v[3] != "same" for v in items.values()):',
        "if left[0]:",
        "recompute",
    ),
    ("PHONE narrowing removed", '        return "narrowed_phone"', "        return None", "phone_needs"),
    (
        "call added as a phone word",
        "contact number)(?![a-z])|(?<![a-z])ph[.:]",
        "contact number|call)(?![a-z])|(?<![a-z])ph[.:]",
        "phone_needs",
    ),
    (
        "phone word boundary removed",
        'r"(?<![a-z])(?:telephone|tel|phone|mobile|mob|cell|whatsapp|fax|telefon|telefono|contact no|contact number)(?![a-z])|(?<![a-z])ph[.:]"',
        'r"(?:telephone|tel|phone|mobile|mob|cell|whatsapp|fax|telefon|telefono|contact no|contact number)(?![a-z])|(?<![a-z])ph[.:]"',
        "word_boundary",
    ),
    ("ph without dot or colon", "|(?<![a-z])ph[.:]", "|(?<![a-z])ph", "phone_needs"),
    ("ID narrowing removed", 'else "narrowed_id"', "else None", "id_numbers_need"),
    ("masked cap removed", "if len(model_text) > MASKED_MAX_CHARS:", "if False:", "masked_text_cap"),
    ("one mark per surface removed", "if surface not in marks:", "if True:", "one_mark_per_surface"),
    ("repr=False removed on Masked.text", "    text: str = field(repr=False)", "    text: str", "masked_repr"),
    ("BodyCheck repr shows the key", 'return "BodyCheck()"', 'return f"BodyCheck({self._key!r})"', "repr_holds"),
    (
        "short values searched as substrings",
        "        if len(value) < 6:" + chr(10) + "            for m in re.finditer(",
        "        if False:" + chr(10) + "            for m in re.finditer(",
        "short_values",
    ),
    ("fingerprint not keyed", "key=key, digest_size=4", "digest_size=4", "recompute_detects"),
    (
        "name reuse check removed",
        "ok = all(_DEAR_BEFORE.search(text[max(0, s - 40) : s].lower()) for s in starts)",
        "ok = True",
        "person_only",
    ),
    (
        "card needs no Luhn check",
        "            if not _luhn(digits):" + chr(10) + "                continue",
        "            if False:" + chr(10) + "                continue",
        "not_a_card",
    ),
    ("card pass removed", 'out.append(("CARD", start, owner[m.end() - 1] + 1))', "pass", "card_numbers_are_hidden"),
    ("North American phone pass removed", "for rx in (_NANP_BRACKET, _NANP_LEADING):", "for rx in ():", "common_formats"),
    ("plus-sign phone pass removed", "for m in _PHONE_PLUS.finditer(text):", "for m in ():", "common_formats"),
    ("labelled phone pass removed", "for m in _PHONE_LABELLED.finditer(text):", "for m in ():", "core_only_half_finds"),
    ("R1b accepts a single unlocated block", "if not any(d in pieces for d in located):", "if False:", "single_unlocated_block"),
    ("decoded-only candidates are located", "if cand in decoded_only and cand not in proven:", "if False:", "percent_encoded_run"),
    (
        "residual copies not checked",
        "unlocated += _residual_copies(text, spans, kept, place_left)",
        "pass",
        "obfuscated_second_copy",
    ),
    (
        "control characters allowed",
        '        unicodedata.category(c) == "Cc" and c not in _ALLOWED_CONTROLS for c in text',
        "        False for c in text",
        "control_characters",
    ),
    (
        "names found as substrings",
        'starts = _word_occurrences(text, original) if ck == "NAME" else _occurrences(text, original)',
        "starts = _occurrences(text, original)",
        "whole_word_only",
    ),
    (
        "own title and label names removed",
        'own_names = [("NAME", m.group(1)) for m in _NAME_FIND.finditer(text)]',
        "own_names = []",
        "titled_and_labelled",
    ),
    ("language words not bank context", "or bool(_LANG_WORD.search(f))", "", "bank_context_for_the_id_test"),
    ("language candidates not taken", "for c in _lang_candidates(text):", "for c in ():", "language_bank_words"),
    (
        "every <word_n> is a mark-like text",
        '_KINDS_RX = "|".join(PRIORITY)',
        '_KINDS_RX = "[A-Za-z][A-Za-z0-9]*"',
        "only_the_marks_this_module_issues",
    ),
    (
        "keyword-less on-file detail is no detail",
        "not invoicecheck.on_file_components(on_file)",
        'not invoicecheck.bank_detail_findings(on_file, "")',
        "keyword_less_on_file",
    ),
    (
        "field rule kind part removed",
        "if sp.kind not in _FREE_TEXT_KINDS or generic not in _FREE_TEXT_PATHS:",
        "if generic not in _FREE_TEXT_PATHS:",
        "kind_part",
    ),
    (
        "label path not free text",
        '_FREE_TEXT_PATHS = ("lines[].description", "adjustments[].label")',
        '_FREE_TEXT_PATHS = ("lines[].description",)',
        "free_text_paths",
    ),
    ("forged mark in a key not checked", "if isinstance(k, str) and _MARK_LIKE.search(canonical(k)):", "if False:", "dict_key"),
    (
        "JSON-escaped kept form dropped",
        "{t, json.dumps(t, ensure_ascii=True)[1:-1], json.dumps(t, ensure_ascii=False)[1:-1]}",
        "{t}",
        "json_escaped_form",
    ),
    ("forged key fingerprint empty", "fp(key_for_detail, k)", '""', "dict_key"),
    (
        "exception chained",
        "        pass  # the code is raised below",
        '        raise SelfCheckFailed("mask_failed") from None  # the code is raised below',
        "chained_exception_is_absent",
    ),
    (
        "lower case changes length",
        '    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)',
        "    return text.casefold()",
        "lowers_to_two",
    ),
    ("filler exemption removed", "any(nt[sp.start : sp.end] != NEUTRAL for sp in det.spans)", "det.spans", "every_core_secret_rule"),
    ("recursion guard removed", "    if depth > 64:", "    if False:", "deeply_nested"),
    (
        "last code kept after a pass",
        "        self.last_code = None\n        try:\n            return self._check(body)",
        "        try:\n            return self._check(body)",
        "last_code_is_reset",
    ),
    (
        "stem test makes every line a non-bank line",
        '(("&" in ln or not ln.isascii() or any(st in f for st in _BANK_STEMS)) and invoicecheck.bank_word_in(ln))',
        "False",
        "bank_words",
    ),
    (
        "locator uses only the 6-character index",
        "length = max(lv for lv in self.PREFIX_LEVELS if lv <= len(cand))",
        "length = 6",
        "share_one_list_of_positions",
    ),
    (
        "residual check ignores kept places",
        "[(sp.start, sp.end) for sp in spans] + [(k.start, k.end) for k in kept]",
        "[(sp.start, sp.end) for sp in spans]",
        "leave_nothing_for_the_finder",
    ),
    (
        "stem shortcut ignores entities",
        '(("&" in ln or not ln.isascii() or any(st in f for st in _BANK_STEMS)) and invoicecheck.bank_word_in(ln))',
        "(any(st in f for st in _BANK_STEMS) and invoicecheck.bank_word_in(ln))",
        "entity_or_a_non_ascii",
    ),
    (
        "13-digit run needs no card word",
        'if len(digits) == 13 and digits[0] != "4" and not _CARD_WORDS.search(',
        'if False and len(digits) == 13 and digits[0] != "4" and not _CARD_WORDS.search(',
        "ordinary_long_numbers",
    ),
    (
        "bare phone needs no word",
        "if _word_before(text, m.start(), _PHONE_WORD, 28, 12)]",
        "if True]",
        "bare_numbers_without_a_phone_signal",
    ),
    (
        "phone date cut removed",
        "    m = _DATEISH.search(num, 4)\n    if m and sum",
        "    m = None\n    if m and sum",
        "stops_before_a_date",
    ),
    (
        "title Shri removed",
        '_TITLES = r"(?:mr|mrs|ms|miss|dr|prof|shri|smt|sri|mx)"',
        '_TITLES = r"(?:mr|mrs|ms|miss|dr|prof)"',
        "name_contexts",
    ),
    (
        "bare plus fragment hidden",
        "if any(c.isdigit() for c in text[a:b]):  # a fragment with no digit",
        "if text[a:b].strip():  # a fragment with no digit",
        "no_phone_fragment",
    ),
    (
        "percent runs not hidden",
        "if cand.isdigit() and cand in digits:",
        "if False:",
        "percent_run_proves_the_number",
    ),
    (
        "base64 blobs not hidden",
        '            spans.append(Span(a_, b_, "BANK", detector=DETECTOR_VERSION))',
        "            pass",
        "blob_next_to_the_clean_digits",
    ),
    (
        "check a2 accepts a non-Masked",
        '    if not isinstance(masked, Masked):\n        raise SelfCheckFailed("mask_failed")\n    marks',
        "    marks",
        "non_masked_value_is_a_code",
    ),
    (
        "find_hidden trusts a wrong low view",
        "if low is None or len(low) != len(haystack) else low",
        "if low is None else low",
        "wrong_length",
    ),
    (
        "no-component detail still compared",
        "if not on_file.strip() or not invoicecheck.on_file_components(on_file):",
        "if not on_file.strip():",
        "without_components",
    ),
    (
        "restore_mismatch carries no items",
        "        bad.detail = tuple(items.values())  # (mark",
        "        bad.detail = ()  # (mark",
        "carries_the_items",
    ),
    ("proven copies not forced", "force = cand in proven", "force = False", "proves_the_number_and_every_plain_copy"),
    (
        "card right after a plus or a bracket",
        "            if start > 0 and len(digits) <= (",
        "            if False and len(digits) <= (",
        "luhn_valid_international_phone",
    ),
    ("weak leading one counts", "1[.-])[2-9]", "1[ .-])[2-9]", "weak_leading_one"),
    ("slash cut removed", 'if " / " in num and', 'if False and " / " in num and', "plus_number_stops_at_a_slash"),
    (
        "cheap fold for entity lines",
        '(invoicecheck.fold_text(ln) if ("&" in ln or not ln.isascii()) else _fold_str(ln))',
        "_fold_str(ln)",
        "read_the_way_the_finder_reads_it",
    ),
    ("prefix index has one level", "PREFIX_LEVELS = (6, 10, 16, 24)", "PREFIX_LEVELS = (6,)", "prefix_levels_give_shorter_lists"),
    (
        "IBAN places not hidden",
        'spans += [Span(a_, b_, "IBAN", detector=DETECTOR_VERSION) for a_, b_ in place_hidden]',
        "pass",
        "hidden_without_the_word_iban",
    ),
    ("reference rule has no length limit", "and len(place) <= IBAN_REF_MAX_LEN", "and True", "skip_rule_has_exactly_these_parts"),
    ("reference rule ignores the IBAN word", "(not iban_word)", "True", "skip_rule_has_exactly_these_parts"),
    ("walk crosses a date", "or date_ahead(pos):", ":", "does_not_join_a_grouped_iban"),
    (
        "left-alone places not excused in the residual check",
        "if rel and all(any(a_ <= o[0] < b_ for a_, b_ in left_alone) for o in rel):",
        "if False:",
        "short_reference_followed_by_words",
    ),
    ("blanking filler counts as a copy", 'if set(c) <= {"x"}:', "if False:", "after_the_word_iban"),
    (
        "walk stays on one line",
        r'{0,6}(?:\n" + _IBAN_SEP + "{0,6}){0,6}")',
        r'{0,6}(?:\n" + _IBAN_SEP + "{0,6}){0,0}")',
        "across_a_line_break",
    ),
    ("gaps read from the raw text", 'return "".join(fp_[idx[i] + 1 : idx[j]])', "return text[idx[i] + 1 : idx[j]]", "any_separator"),
    ("only space and hyphen separate groups", 'r"[ \\t\\-/.,;:|>]"', 'r"[ \\t-]"', "every_layout_is_hidden"),
    ("no slack for a long last group", "_IBAN_LAST_GROUP_SLACK = 3", "_IBAN_LAST_GROUP_SLACK = 0", "bank_statement_forms"),
    (
        "any group is plausible as a month",
        '_IBAN_MONTH, _IBAN_DAY, _IBAN_YEAR = r"(?:0?[1-9]|1[0-2])"',
        '_IBAN_MONTH, _IBAN_DAY, _IBAN_YEAR = r"[0-9]{1,2}"',
        "date_test_is_strict",
    ),
    (
        "a letters-only group needs no digit after it",
        "(count <= 8 or codes == 1) and next_has_digit(e + 1)",
        "(count <= 8 or codes == 1)",
        "word_of_four_letters_after_a_code",
    ),
    (
        "the walk ignores amounts",
        "            if stop_at(pos, e):\n                break\n",
        "            if False:\n                break\n",
        "walk_stops_at_an_amount",
    ),
    ("long places beyond-test off", "place_len[h] >= _IBAN_MIN_BEYOND and", "place_len[h] >= 9999 and", "stray_gap_does_not_leave_a_tail"),
    (
        "padding after a place is never padding",
        "    return not any(c.isdigit() for c in tail[i:j])",
        "    return False",
        "word_without_a_digit_after_a_long_place",
    ),
    ("a date after a slash is a phone number", "if i > 0 and _DATEISH.match(part):", "if False:", "split_handles_every_slash"),
    ("no short extension after a slash", "or (i > 0 and 3 <= digits <= 6", "or (False and 3 <= digits <= 6", "split_handles_every_slash"),
    (
        "a letters-only group may have any length up to four",
        "m == 4 and (count <= 8 or codes == 1)",
        "m <= 4 and (count <= 8 or codes == 1)",
        "no_bank_code_when_no_digits_follow",
    ),
    ("a third bank code", "(count <= 8 or codes == 1)", "(count <= 8 or codes >= 1)", "at_most_two_bank_code_groups"),
    ("a bank code far from the check digits", "(count <= 8 or codes == 1)", "True", "reference_followed_by_a_word"),
    (
        "a letter in a long group is no more of the account",
        "or (not _BANK_CODE_AND_DIGITS.fullmatch(chars[pos : e + 1]) and not chars[pos : e + 1].isdigit())",
        "or False",
        "reference_followed_by_a_word",
    ),
    (
        "a bank code stuck to digits is a mixed group",
        "not _BANK_CODE_AND_DIGITS.fullmatch(chars[pos : e + 1]) and ",
        "",
        "stuck_to_its_digits",
    ),
    ("no letter tail completes an account", "and m <= 3 and not _IBAN_CURRENCY.fullmatch(chars[pos : e + 1])", "and False", "letter_tail"),
    (
        "a currency code completes an account",
        " and not _IBAN_CURRENCY.fullmatch(chars[pos : e + 1])  # NO29",
        "  # NO29",
        "currency_code_up_to_three",
    ),
    (
        "a date may be followed by a separator and a digit",
        r"{_IBAN_DAY})(?![./\-]?\d)",
        r"{_IBAN_DAY})(?!\d)",
        "look_like_the_start_of_a_date",
    ),
    (
        "date read on the raw text",
        "return _IBAN_DATE_AHEAD.match(folded, fstart[idx[i]]) is not None",
        "return _IBAN_DATE_AHEAD.match(text, idx[i]) is not None",
        "date_after_a_mistyped_iban",
    ),
    (
        "zero-width characters split a token",
        'while i + 1 < n and gap(i, i + 1) == "":',
        "while i + 1 < n and idx[i + 1] - idx[i] <= 1:",
        "zero_width_characters_inside",
    ),
    ("no anchor for code and check digits apart", "first == k + 1", "first == -1", "check_digits_apart_with_a_bank_code"),
    (
        "a zero-width character before the code does not separate",
        '(idx[k] > 0 and fp_[idx[k] - 1] == "")',
        "False",
        "zero_width_or_glued_prefix",
    ),
    ("an amount after a place is no padding", " or _IBAN_AMOUNT_AHEAD.match(tail, i)", "", "amount_with_decimals_after_a_short_account"),
    (
        "the blanked place plus padding is a copy",
        "if rest and len(c) - len(rest) >= 8 and _padded_tail(text, [sp.end for sp in spans], rest):",
        "if False:",
        "amount_with_decimals_after_a_short_account",
    ),
    (
        "a decimal amount beside a currency does not stop the walk",
        "            stops.append((m_.start(), m_.end()))\n",
        "            pass\n",
        "amount_with_decimals_after_a_short_account",
    ),
]


def run_pytest(k: str | None) -> int:
    """pytest's exit code: 0 all passed, 1 a test failed (a kill), anything else (2 interrupted or import error, 4 usage, 5 nothing selected) proves nothing."""
    cmd = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *TESTS]
    if k:
        cmd += ["-k", k]
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_S).returncode  # noqa: S603
    except subprocess.TimeoutExpired:
        return 124  # a hang proves nothing


def main() -> int:
    only = None
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        if i + 1 >= len(sys.argv):
            print("usage: mutate_mask.py [--only NAME[|NAME...]] [--skip-baseline]")
            return 2
        only = [o for o in sys.argv[i + 1].split("|") if o]
        if not only:
            print("usage: --only needs at least one name")
            return 2
    original = SRC.read_bytes()
    text = original.decode("utf-8")
    bad = ran = 0
    if "--skip-baseline" not in sys.argv and run_pytest(None) != 0:  # an unrelated failing test would make every mutant look killed
        print("BASELINE   the unmutated suite does not pass: nothing was mutated", flush=True)
        return 2
    try:
        for name, old, new, k in MUTANTS:
            if only and not any(o in name for o in only):
                continue
            ran += 1
            if text.count(old) != 1:
                print(f"CRASH      {name} :: pattern found {text.count(old)} times", flush=True)
                bad += 1
                continue
            SRC.write_bytes(text.replace(old, new).encode("utf-8"))
            rc = run_pytest(k)
            if rc == 1:
                print(f"KILLED     {name} :: -k {k}", flush=True)
            elif rc != 0:
                print(f"CRASH      {name} :: pytest exit code {rc} for -k {k} (stale expression or import error)", flush=True)
                bad += 1
            elif run_pytest(None) == 1:
                print(f"ELSEWHERE  {name} :: -k {k} stayed green", flush=True)
                bad += 1
            else:
                print(f"SURVIVED   {name}", flush=True)
                bad += 1
    finally:
        SRC.write_bytes(original)
    print(
        f"restore proof: {'ok' if SRC.read_bytes() == original else 'FAILED'}; not killed by its named test: {bad} of {ran} run ({len(MUTANTS)} in the list)"
    )
    if ran == 0:
        print("no mutant matched the names: nothing was tested")
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
