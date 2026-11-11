"""The mutants of the fold scan (P2d-1): 21 redactor mutants of core PR #50 (748849c), re-pointed, 21 new ones, the 16 of review round w3 and the 5 of round w4
(the views that drop spacing marks, the control-character gate, the block that grows over a second block, the line end of a withheld block).

``tools.mutation_runner`` replaces EVERY occurrence of a mutant's ``old`` text. Mutant 21 therefore removes both
``_deadline=started + defaults.REDACT_BUDGET_S`` arguments of ``runmap.redact_text`` (the first pass and the loop over the views), which is
what its name says ("the views get no shared deadline"); its killer fails on either one alone.

Each mutant reverts ONE guard in a temp copy of the package (``tools.mutation_runner``) and the named test must fail first, for the
reason in ``expect``. Not collected by pytest. Run from the repo root:

    uv run --all-extras --group test python tests/redact_mutants.py            # all mutants; exit 1 if any is not good
    uv run --all-extras --group test python tests/redact_mutants.py N8         # only mutants whose name contains the text

Good means KILLED, or CRASH with the declared exception class. Exit 1 if any mutant is not good, 2 if a filter selects none.
R2 ("the check after stage 1 is removed") is killed by BUDGET-1b (the spy counter is 1 instead of 0); it is not declared equivalent.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
S = "src/hadavin_sdk/"
RD, GM, DF = S + "guard/redact.py", S + "guard/runmap.py", S + "defaults.py"
TN = S + "guard/textnorm.py"
F1 = "tests/test_redact_fold.py"
FB = "tests/test_redact_fold_budget.py"
FS = "tests/test_redact_fold_seams.py"
FP = "tests/test_redact_fold_property.py"
FZ = "tests/test_k5_round12_fuzz.py"
FM = "tests/test_redact_marks.py"
PREFIX = {
    FM: "tests/test_redact_marks::",
    F1: "tests/test_redact_fold::",
    FB: "tests/test_redact_fold_budget::",
    FS: "tests/test_redact_fold_seams::",
    FP: "tests/test_redact_fold_property::",
    FZ: "tests/test_k5_round12_fuzz::",
}

CHECK = "if time.thread_time() > deadline:"
SLASH = 'c.isalnum() or c == "." or (c == "/" and "\\u2044" in f)'


def m(name, file, old, new, test_file, killer, expect, **kw):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=PREFIX[test_file] + killer,
        **kw,
    )


M = [
    # ---- the 21 existing redactor mutants (748849c tests/promoted_mutants.py), re-pointed ----
    m("1 the folded pass never runs", RD, "        if not _plain(out):\n", "        if False:\n", F1,
      "test_redact_masks_a_value_hidden_behind_look_alikes_on_the_line_and_leaves_other_text_alone", "ssert"),
    m("2 the folded line is emitted after a hit", RD, """        return f"{FOLD_NOTE} {' '.join""", """        return cur + eol if hits else line  # f"{FOLD_NOTE} {' '.join""", FP,
      "test_a_fold_on_hit_rewrite_never_emits_folded_text_so_nothing_goes_live_after_the_neutralising", "ssert"),
    m("3 a folded hit is dropped", RD, """        return f"{FOLD_NOTE}""", """        return line  # f"{FOLD_NOTE}""", F1,
      "test_redact_masks_a_value_hidden_behind_look_alikes_on_the_line_and_leaves_other_text_alone", "ssert"),
    m("4 every non-ASCII line gets the per-line check", RD,
      "suspects = {i for i, c in folded.items() if c - direct.get(i, Counter())}", "suspects = set(range(len(lines)))", FB,
      "test_many_short_non_ascii_lines_cost_no_per_line_pattern_runs", "ssert"),
    m("5 the fold scan has no time budget", RD, CHECK, "if False:", FB,
      "test_the_fold_scan_stops_at_the_time_budget_with_input_too_large", "DID NOT RAISE"),
    m("6 a value hidden behind look-alikes is masked in place", RD, "if any(any(alike[s:e]) for s, e, _, _ in claims):", "if False:", F1,
      "test_attacks_are_still_withheld_whole_and_never_emitted_folded", "ssert"),
    m("7 accented and other-script lines are withheld whole again", RD,
      'return (text, where, alike) if text == whole else None', "return None", F1,
      "test_benign_multilingual_corpus_has_a_zero_false_withhold_rate", "ssert"),
    m("8 a set compare hides a look-alike copy", RD, "if not any(self._dry_hits(f) - direct for f in folded):",
      "if all(set(self._dry_hits(f)) <= set(direct) for f in folded):", F1,
      "test_a_lookalike_copy_of_a_value_that_also_stands_in_clear_is_still_a_hit", "ssert"),
    m("9 the offset after a masked value is off by one", RD, "prev = where[e - 1] + 1", "prev = where[e - 1]", F1,
      "test_the_malformed_offset_is_caught_by_a_value_in_front_of_and_behind_other_text", "ssert"),
    m("10 the text before a masked value restarts at zero", RD, "out += [body[prev : where[s]], self._register_written(",
      "out += [body[: where[s]], self._register_written(", F1, "test_text_before_a_masked_value_is_kept_once_between_two_in_place_masks", "ssert"),
    m("11 the line scan asks for no budget", RD, "            self._over_budget(started)\n            for m in pattern.finditer(text):",
      "            for m in pattern.finditer(text):", FB, "test_line_hits_asks_for_the_budget_once_per_pattern", "ssert"),
    m("12 the rounds are not capped at four", RD, "MAX_FOLD_ROUNDS = 4  # rounds", "MAX_FOLD_ROUNDS = 40  # rounds", F1,
      "test_four_rounds_that_never_converge_fall_through_to_the_withhold", "ssert"),
    m("13 a multi-line fold value is left", RD, "if reach.get(i, i) > i:", "if False:", F1,
      "test_a_multi_line_value_that_only_the_fold_sees_is_replaced_not_left", "ssert"),
    m("14 the fold treatment ignores a bank word elsewhere", RD, "            self.bank_near = True", "            pass", F1,
      "test_an_account_number_below_an_accented_or_full_width_keyword_is_masked_when_a_bank_word_stands_elsewhere", "ssert"),
    m("15 a suspect line gets every pattern", RD, "ln = self._folded_line(ln, which.get(i))", "ln = self._folded_line(ln, None)", FB,
      "test_a_suspect_line_loops_only_the_patterns_that_matched_it", "ssert"),
    m("16 the pattern filter is off", RD, "if only is not None and n not in only and label not in _CONTEXT_LABELS:", "if False:", FB,
      "test_a_pattern_that_matched_nowhere_in_a_line_is_not_run_on_it", "ssert"),
    m("17 the budget is the wall clock again", RD, CHECK, "if time.monotonic() > deadline:", FB,
      "test_the_budget_is_cpu_time_of_the_thread_not_the_wall_clock", "ssert", allow_crash=True, crash_type="AssertionError"),
    m("18 a fraction slash is not mapped", RD, SLASH, 'c.isalnum() or c == "."', F1,
      "test_one_half_is_masked_around_but_a_full_width_slash_is_still_an_attack", "ssert"),
    m("19 any slash is allowed in a sign", RD, SLASH, 'c.isalnum() or c == "." or c == "/"', F1,
      "test_one_half_is_masked_around_but_a_full_width_slash_is_still_an_attack", "ssert"),
    m("20 the alignment never checks the budget", RD, "if not i & 4095:", "if False:", FB,
      "test_aligned_fold_checks_the_budget_every_4096_characters", "DID NOT RAISE"),
    m("21 the views get no shared deadline", GM, "_deadline=started + defaults.REDACT_BUDGET_S", "_deadline=None", FB,
      "test_one_deadline_covers_the_text_and_all_its_views", "ssert"),
    # ---- the 21 new mutants ----
    m("N1 U+2044 is no longer mapped to a slash", RD,
      '    if ch == "\\u2044":\n        return "/", 1  # a fraction slash spells a slash: masked around, never inside (SL-D)\n', "",
      F1, "test_d1_1_a_fraction_slash_beside_an_accented_address_is_masked_in_place", "ssert"),
    m("N4 find enters the scan for ASCII text", RD, "        if not _plain(out):\n", "        if True:\n", F1,
      "test_ascii_1_an_ascii_text_with_no_non_ascii_value_never_enters_the_fold_scan", "ssert"),
    m("N5 _over_budget never raises", RD, "runmap imports this module\n\n            raise InputTooLarge(\"InputTooLarge\")",
      "runmap imports this module\n\n            return", FB,
      "test_a_spent_budget_refuses_before_any_line_is_treated", "DID NOT RAISE"),
    m("N6 FOLD_NOTE text changed", RD, 'FOLD_NOTE = "[line withheld: look-alike text hid a protected value]"',
      'FOLD_NOTE = "[line withheld: look-alike text hid a value]"', F1, "test_fold_note_1_the_note_is_the_fixed_text", "ssert"),
    m("N7 the alike flag is always 0", RD, "alike.extend([flag] * len(f))", "alike.extend([0] * len(f))", F1,
      "test_attacks_are_still_withheld_whole_and_never_emitted_folded", "ssert"),
    m("N8 _dry_hits returns an empty Counter", RD, "        return found\n", "        return Counter()\n", F1,
      "test_attacks_are_still_withheld_whole_and_never_emitted_folded", "ssert"),
    m("N9 the map stores the folded spelling again", RD, "written = body[where[s] : where[e - 1] + 1]", "written = folded[s:e]", F1,
      "test_map_1_the_map_holds_the_written_spelling", "ssert"),
    m("N10 the reverse-map key is the folded value", RD, "self.reverse[full] if full in self.reverse else self._place(label, full, written)",
      "self.reverse[fold(full)] if fold(full) in self.reverse else self._place(label, full, written)", F1,
      "test_map_4_two_occurrences_get_two_placeholders_in_both_orders", "ssert"),
    m("N11 the mid-line check reads only index 0", RD, "if not i & 4095:", "if i == 0:", FB,
      "test_mid_1_the_budget_is_checked_in_the_middle_of_a_line", "DID NOT RAISE"),
    m("N12 the alignment comparison is always true", RD,
      'return (text, where, alike) if text == whole else None', "return (text, where, alike)", F1,
      "test_align_2_the_alignment_agrees_with_the_fold_or_steps_aside", "ssert"),
    m("N14 the slash replace is deleted from the alignment return", RD,
      'whole = fold_view(body, marks_dropped=marks, iota=iota).replace("\\u2044", "/")', "whole = fold_view(body, marks_dropped=marks, iota=iota)", F1,
      "test_d1_1_a_fraction_slash_beside_an_accented_address_is_masked_in_place", "ssert"),
    m("N15 the alias build asks for no budget", RD, "            if self._deadline is not None:\n                self._over_budget(self._deadline)\n", "", FB,
      "test_budget_3_the_alias_build_is_budgeted", "DID NOT RAISE"),
    m("R1 the budget is the wall clock in runmap", GM, "started = time.thread_time()", "started = time.monotonic()", FB,
      "test_the_budget_is_cpu_time_of_the_thread_not_the_wall_clock", "ssert", allow_crash=True, crash_type="AssertionError"),
    m("R2 the check after stage 1 is removed", GM, "if views and time.thread_time() - started > defaults.REDACT_BUDGET_S:", "if False:", FB,
      "test_budget_1b_the_check_after_stage_one_runs_before_any_decoded_mask", "ssert"),
    m("R3 the check in the loop over views is removed", GM,
      "                time.thread_time() - started > defaults.REDACT_BUDGET_S\n            ):  # a hostile text",
      "                False\n            ):  # a hostile text", FB, "test_budget_2_the_deadline_is_shared_by_every_view", "DID NOT RAISE"),
    m("DM-1 no check per stored original", GM,
      "        if deadline is not None and time.thread_time() > deadline:\n            raise InputTooLarge(\"InputTooLarge\")  # one check per stored original, before any skip\n", "",
      FB, "test_hostile_2_many_stored_originals_with_an_encoding_mark_stop_at_the_first_check", "ssert"),
    m("DM-1b the check sits after the skips", GM,
      "        if deadline is not None and time.thread_time() > deadline:\n            raise InputTooLarge(\"InputTooLarge\")  # one check per stored original, before any skip\n"
      "        if original.startswith(\"\\0seed\") or not (\n            any(c in original for c in _ENCODED_MARKS) or not original.isascii()\n        ):\n            continue\n",
      "        if original.startswith(\"\\0seed\") or not (\n            any(c in original for c in _ENCODED_MARKS) or not original.isascii()\n        ):\n            continue\n"
      "        if deadline is not None and time.thread_time() > deadline:\n            raise InputTooLarge(\"InputTooLarge\")\n",
      FB, "test_hostile_2b_the_check_sits_at_the_top_of_the_loop_before_any_skip", "ssert"),
    m("REG-M the rollback keeps the counters", RD, "        self.counters = counters\n", "        pass\n", F1,
      "test_reg_1b_non_converging_rounds_leave_no_orphan_placeholder", "ssert"),
    m("REG-M2 the journal is not rolled back for a withheld line", RD,
      "        # the line is withheld or left as it is: the registrations of its in-place rounds are discarded\n        self._rollback(counters)\n",
      "        self._journal = None\n", F1, "test_reg_1b_non_converging_rounds_leave_no_orphan_placeholder", "ssert"),
    m("AL-1 no sweep rules from the alias keys", RD,
      "[*self.mapping.items(), *((ph, k) for k, ph in alias.items() if k not in stored)],", "list(self.mapping.items()),", F1,
      "test_sweep_1_a_clear_copy_after_a_written_variant_gets_the_same_placeholder", "ssert"),
    m("AL-3 _mask_in_place registers through the alias", RD,
      "self.reverse[full] if full in self.reverse else self._place(label, full, written)",
      "self.reverse[full] if full in self.reverse else (self.alias.get(fold(full)) or self._place(label, full, written))", F1,
      "test_map_4_two_occurrences_get_two_placeholders_in_both_orders", "ssert"),
    # ---- review round w3: every view of a line is scanned (marks dropped, U+0345 dropped), control characters, grown blocks ----
    m("W1 no marks-dropped or iota view is scanned by _fold_scan", RD, "all_specs = list(dict.fromkeys(sp for one in specs_of for sp in one))", "all_specs = []", FM,
      "test_marks_1_the_four_review_inputs_leave_no_key", "ssert"),
    m("W2 _view_specs never offers the marks-dropped views", RD, "    has_marks = any(f[0] for f in flags)\n", "    has_marks = False\n", FM,
      "test_marks_1_the_four_review_inputs_leave_no_key", "ssert"),
    m("W3 _view_specs never offers the iota-dropped view", RD, "    has_iota = any(f[1] for f in flags)\n", "    has_iota = False\n", FM,
      "test_marks_4_a_greek_letter_with_the_subscript_iota_does_not_hide_a_key", "ssert"),
    m("W4 the in-place rounds read the primary view only", RD, "*reversed(_view_specs(cur)),\n                    _PRIMARY_VIEW,\n", "_PRIMARY_VIEW,\n", FM,
      "test_marks_1_the_four_review_inputs_leave_no_key", "ssert"),
    m("W5 the primary view masks before the marks-dropped ones", RD, "*reversed(_view_specs(cur)),\n                    _PRIMARY_VIEW,\n", "_PRIMARY_VIEW,\n                    *_view_specs(cur),\n", FM,
      "test_marks_1_the_four_review_inputs_leave_no_key", "ssert"),
    m("W6 the withhold check reads the primary view only", RD, "if not any(self._dry_hits(f) - direct for f in folded):", "if not (self._dry_hits(folded[0]) - direct):", FM,
      "test_marks_4_a_greek_letter_with_the_subscript_iota_does_not_hide_a_key", "ssert"),
    m("W7 a withheld line reports the first view only", RD, "        for cur in views:\n", "        for cur in views[:1]:\n", FM,
      "test_marks_4_a_greek_letter_with_the_subscript_iota_does_not_hide_a_key", "ssert"),
    m("W8 a block that starts inside another does not extend it", RD, "                        end = max(end, reach.get(j, j))", "                        end = end", FM,
      "test_marks_7_a_second_multi_line_value_that_starts_inside_the_first_is_withheld_to_its_end", "ssert"),
    m("W9 a withheld block loses its line end", RD, 'self._withhold(blocks, "".join(lines[i : end + 1]), eol)', 'self._withhold(blocks, "".join(lines[i : end + 1]))', FM,
      "test_marks_8_a_withheld_block_keeps_the_line_end_it_had", "ssert"),
    m("W10 an ASCII control character does not send the line to the fold", RD, "    return text.isascii() and _HIDDEN_ASCII.search(text) is None", "    return text.isascii()", FM,
      "test_marks_5_an_invisible_ascii_control_character_inside_a_value_is_masked", "ssert"),
    m("W11 the alias index holds the written fold only", RD, "    keys += [fold_view(value, marks_dropped=m, iota=i) for m, i in _view_specs(value)]\n", "", FM,
      "test_marks_6_a_clear_copy_of_a_value_masked_with_a_mark_inside_is_masked_too", "ssert"),
    m("W12 the alignment keeps the marks of a marks-dropped view", RD, "            if marks and _is_spacing(ch):\n", "            if False:\n", FM,
      "test_marks_1_the_four_review_inputs_leave_no_key", "ssert"),
    m("W13 runmap reads no view without the marks", GM, "        canonical(without_spacing_marks(text)),\n", "", FM,
      "test_marks_10_runmap_also_reads_the_text_without_its_marks", "ssert"),
    m("W14 the PEM pattern runs before the PuTTY one", RD, "    # Account-less (`arn:aws:s3:::bucket`)",
      "]\nPATTERNS[0], PATTERNS[1] = PATTERNS[1], PATTERNS[0]\nPATTERNS += [\n    # Account-less (`arn:aws:s3:::bucket`)", FM,
      "test_marks_7_a_second_multi_line_value_that_starts_inside_the_first_is_withheld_to_its_end", "ssert"),
    m("W15 the weight memo answers every long text with the first weight", TN, '    key = hashlib.sha256(text.encode("utf-8", "surrogatepass")).digest()\n', '    key = b"k"\n', FM,
      "test_marks_12_the_weight_of_a_long_text_is_remembered_by_digest_and_never_wrong", "ssert"),
    m("W16 the alignment ignores the view it is asked for", RD, "        marks, iota = spec\n", "        marks, iota = False, True\n", FM,
      "test_marks_14_the_alignment_of_every_view_agrees_with_that_view_of_the_fold_or_steps_aside", "ssert"),
    m("W17 the cut of a marks-dropped claim is not extended", RD, "marks=spec[0])", "marks=False)", FM,
      "test_marks_16_a_mark_beside_a_value_is_masked_with_it", "ssert"),
    m("W18 the cut is extended on the left only", RD, "                while stop < len(body) and _is_spacing(body[stop]):\n                    stop += 1\n", "", FM,
      "test_marks_16_a_mark_beside_a_value_is_masked_with_it", "ssert"),
    m("W19 the cut is extended on the right only", RD, "                while start > prev and _is_spacing(body[start - 1]):\n                    start -= 1\n", "", FM,
      "test_marks_16_a_mark_beside_a_value_is_masked_with_it", "ssert"),
    m("W20 the view without the iota keeps the letter plus an i", RD, "if own != f and own.isascii():", "if False:", FM,
      "test_marks_19_a_look_alike_letter_with_a_subscript_iota_does_not_withhold_the_line_beside_an_address", "ssert"),
    m("W21 the clock is not read before each view", RD, "                    self._over_budget(self._scan_deadline)  # one view", "                    pass  # one view", "tests/test_redact_fold_budget.py",
      "test_view_1_the_clock_is_read_before_each_view_of_a_line", "ssert"),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):  # one line per mutant, as soon as it finishes
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    first_lines: dict[str, str] = {}
    res = run_mutants(
        ROOT,
        M,
        [F1, FB, FS, FP, FZ, FM],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
