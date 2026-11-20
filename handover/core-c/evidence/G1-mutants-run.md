# G1 mutants run: textnorm mutant list on HEAD (ORDER 022 Q9)

Run by evidence runner tnmut, 2026-11-20 08:55Z to about 09:05Z (runner) plus about 15 minutes of diagnosis. Worktree `/tmp/core-c-tnmut`, branch `wip-tnmut` cut from HEAD bf729a9 (cloud/core-c). Nothing pushed, nothing committed, main tree untouched. The runner copies the tree to a temp folder and mutates only that copy.

## 1. Baseline

Command: `uv run python tests/textnorm_mutants.py` (Python 3.13.18). The runner first runs the UNMUTATED copy with the nine killer files (`TESTS` of the list: test_textnorm.py, _generator, _scan, _siblings, _fixbatch, _order137, _round1, _round2, _differential) and refuses to go on unless it is green (`RuntimeError: the unmutated copy does not pass its tests`). It went on and ran all 240 mutants, so THE BASELINE IS GREEN ON HEAD. (The M16 failure of G1-fold.md section 2 is closed: G-text-deltas Amendment 1 item 2 changed that clause; the runner confirms it.)

## 2. Raw summary of the full run

First line: `240 mutants: 228 change behaviour, 12 change only words`. Final line:

```
233 of 240 good; problems: ["mixed: a mark of the word's own script flags", 'runmap: the composed view is not listed', 'injection: the pieces do not overlap', 'injection: the new piece ignores the letters it holds', 'injection: a boundary with too few letters passes', 'injection: the settings are not checked', 'injection: the second half of a halved piece starts at the halfway point']
```

233 lines `ok  KILLED`, 7 lines `BAD`, 0 CRASHED (no mutant is declared CRASH). Raw output kept at `/tmp/tnmut.copy` in the worktree box (and the 7 BAD lines are below; the 233 KILLED lines list name and killer test). Exit code of the runner is 1 (a problem exists).

| mutant | verdict | killer named | first line |
|---|---|---|---|
| mixed: a mark of the word's own script flags | BAD WRONG_REASON | test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a_mark_of_the_words_own_script_does_not_flag | AssertionError: a mark of the word's own script group flags ['U+0061 U+1CE9 U+1CE1'] |
| runmap: the composed view is not listed | BAD SURVIVED | test_redact_text_masks_a_decomposed_copy_of_a_known_name (FB) | (passes) |
| injection: the pieces do not overlap | BAD SURVIVED | test_m4_a_steering_phrase_anywhere_in_a_text_over_the_size_rule_is_found (RO) | (passes) |
| injection: the new piece ignores the letters it holds | BAD SURVIVED | test_a_phrase_padded_across_a_piece_boundary_is_found_whatever_the_padding (R2) | (passes, 3 params) |
| injection: a boundary with too few letters passes | BAD WRONG_REASON | test_a_pad_longer_than_the_largest_overlap_is_flagged_never_passed (R2) | AssertionError: injection_suspected |
| injection: the settings are not checked | BAD WRONG_REASON | test_the_settings_of_the_chunked_read_are_checked (R2) | TextTooLong: the 8192 characters before a piece boundary ... hold too few letters |
| injection: the second half of a halved piece starts at the halfway point | BAD SURVIVED | test_a_phrase_padded_across_the_halving_point_of_a_heavy_piece_is_found (R2) | (passes) |

## 3. The 7 problems, one by one

I re-ran each in a scratch copy (`/tmp/diag_tn`, same replace, the named killer only) to confirm the verdict; the survivors do pass on the mutant.

1. `mixed: a mark of the word's own script flags` (WRONG_REASON): the mutant IS caught by its named killer, but the first failing line is "a mark of the word's own script group flags [...]" and the list expects the fragment `is flagged`, which is not in that message. Tooling/pinning problem (the `expect` fragment of the mutant does not match the assertion message), not a test gap. Fix: `expect` = "own script group flags". Not equivalent.
2. `runmap: the composed view is not listed` (SURVIVED): the mutant removes three lines (`composed(text)`, `composed(unescaped)`, `composed(undone)`). The fold's G3 view list also holds `composed(unmarked)`; for a text with no spacing mark `unmarked == text`, so `composed(unmarked)` equals `composed(text)`: the killer (a plain decomposed name) cannot tell. So for the `composed(text)` line the mutant is equivalent on the killer's input (proof: `without_spacing_marks(text) == text` when the text has no Mc/Lm/Sk character, then `composed(unmarked) == composed(text)`). It is NOT equivalent in general: the `composed(unescaped)` and `composed(undone)` lines are not covered by `composed(unmarked)`. TEST GAP: missing test = a decomposed known name that appears only after a JSON `\uXXXX` unescape or a percent/entity undo (so only `composed(unescaped)` / `composed(undone)` finds it) must be masked by `runmap.redact_text`. Alternative: split the mutant into three.
3. `injection: the pieces do not overlap` (SURVIVED): the mutant changes `if back >= low and _holds(...)` to `if back >= 1`. The two differ only when the first window (`low` = 1,024 characters before the boundary) fails `_holds`, i.e. when padding sits there. The named killer (M4, plain steering phrase, no padding) never has that, so it cannot tell. TEST GAP in the pinned killer: the mutant needs the padded-boundary test (R2) as killer, but see 4.
4. `injection: the new piece ignores the letters it holds` (SURVIVED): the same edit family (`back >= low` without `_holds`) and the R2 killer `test_a_phrase_padded_across_a_piece_boundary_is_found_whatever_the_padding` (zero-width space, space, han; pad 3,000 centred 500 before the boundary) passes on the mutant (3 passed). By its docstring the test "FAILS before ONLY BY NAME / by behaviour" on older code; on the fold with the mutant the phrase is still found, so the test does not exercise the `_holds` loop as intended (I did not find out which other path finds the phrase; the pad reaches 2,000 characters before the boundary, so the first 1,024-character window is pure padding and `_holds` should have moved it back). TEST GAP: missing test = a text over the size rule where the 1,024 characters before the first boundary are padding only and the phrase halves lie on both sides, so that only the moved-back start (`_holds`) finds it; and `_start_of_next` unit test with a pad window that must return `end - back` with `back > low`. Not proven equivalent; I did not prove or disprove that another path makes it equivalent.
5. `injection: a boundary with too few letters passes` (WRONG_REASON): the named killer fails on the mutant at line 113 (`assert verdict.reason_code == "guard_unavailable"`, got `injection_suspected`), so the mutant is killed in substance, but that assert has no message, so the `expect` fragment `HOSTILE-LONG-PAD` is not in the first line. Tooling/pinning: add the message to the assert (a test edit) or change `expect` to `injection_suspected`. Not a gap.
6. `injection: the settings are not checked` (WRONG_REASON): killed in substance (the killer raises `TextTooLong` out of the check instead of reaching the `GEOMETRY-UNCHECKED` assert); `expect` does not match that line. Tooling/pinning problem, not a gap.
7. `injection: the second half of a halved piece starts at the halfway point` (SURVIVED): `piece[cut:]` instead of `piece[second:]`; the killer (pad 300 across the halving point of a heavy piece) passes on the mutant. Its docstring says "FAILS before ONLY BY NAME", i.e. it never discriminated by behaviour. TEST GAP: missing test = a pad on the halving point long enough that `piece[cut:]` leaves too few letters of the first phrase half in the second part while `piece[:cut]` loses the second half (pad of more than the first half's width); not proven equivalent.

## 4. Q9: the 30 changed code points

What I found: the 30 code points are NOT in the textnorm data (`_confusables.py`, the fold table) diff; they are the 30 code points whose `redact._char_class` class differs from P2d-1 after the G3 adaptation (QUESTIONS item 9; `evidence/G3-p2d-port.md` section 6, which lists exactly 30). G-text-deltas.md Amendment for Q9 does not list them (the amendment text I found there does not name them; the list is in G3-p2d-port.md section 6). Exactly 30 identified: 25 dashes/minus/quotes now ASCII with flag 0 (ordinary typography), 3 slash look-alikes now refused (None), U+FFFD now dropped, U+10EAD.

Mutant search: `tests/textnorm_mutants.py` (240) and `tests/redact_mutants.py` (63) hold NO mutant on the typed-punctuation branch of `_char_class` (`_TYPED_PUNCT`, `_TYPED_CATEGORIES`, the U+2212 clause, the U+FFFD drop) and `tests/test_redact_g3_port.py` (the tests of these 30) is in the test list of neither runner. So the answer for every code point is MISSING. I did not add a mutant (told to write one file only).

Extra evidence (a probe, NOT a mutant of the list): for each code point I patched `_char_class` in process so that this one character keeps its P2d-1 class (itself, flag 0) and ran `tests/test_redact_g3_port.py` + `tests/test_redact_fold.py`; the last column lists the tests that failed. "none" = no existing test notices the change of that code point.

| code point | name | port (fold5) class | killer mutant | probe: tests that fail when this one char reverts to P2d-1 |
|---|---|---|---|---|
| U+058A | ARMENIAN HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+05BE | HEBREW PUNCTUATION MAQAF | `["-", 0]` | MISSING | none (no test fails) |
| U+1400 | CANADIAN SYLLABICS HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+1806 | MONGOLIAN TODO SOFT HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+2010 | HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+2012 | FIGURE DASH | `["-", 0]` | MISSING | none (no test fails) |
| U+2013 | EN DASH | `["-", 0]` | MISSING | fold5_a_value_written_with_typographic_dashes_is_masked_in_p |
| U+2014 | EM DASH | `["-", 0]` | MISSING | fold5_a_dash_or_a_typographic_quote_on_a_line_does_not_withh; typography_an_em_dash_is_ordinary_the_value_beside_it_is_mas; withhold_rate_on_lines_with_signs_is_measured_and_pinned |
| U+2015 | HORIZONTAL BAR | `["-", 0]` | MISSING | none (no test fails) |
| U+2018 | LEFT SINGLE QUOTATION MARK | `["'", 0]` | MISSING | typography_a_curly_quote_is_ordinary_the_value_inside_the_qu |
| U+2019 | RIGHT SINGLE QUOTATION MARK | `["'", 0]` | MISSING | typography_a_curly_quote_is_ordinary_the_value_inside_the_qu |
| U+201B | SINGLE HIGH-REVERSED-9 QUOTATION MARK | `["'", 0]` | MISSING | none (no test fails) |
| U+201C | LEFT DOUBLE QUOTATION MARK | `["\"", 0]` | MISSING | fold5_a_dash_or_a_typographic_quote_on_a_line_does_not_withh |
| U+201D | RIGHT DOUBLE QUOTATION MARK | `["\"", 0]` | MISSING | fold5_a_dash_or_a_typographic_quote_on_a_line_does_not_withh |
| U+201F | DOUBLE HIGH-REVERSED-9 QUOTATION MARK | `["\"", 0]` | MISSING | none (no test fails) |
| U+2212 | MINUS SIGN | `["-", 0]` | MISSING | fold5_a_dash_or_a_typographic_quote_on_a_line_does_not_withh |
| U+2215 | DIVISION SLASH | `null` | MISSING | fold5_the_class_of_every_dash_quote_and_slash_of_the_fold_ta |
| U+2571 | BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT | `null` | MISSING | fold5_the_class_of_every_dash_quote_and_slash_of_the_fold_ta |
| U+29F8 | BIG SOLIDUS | `null` | MISSING | fold5_the_class_of_every_dash_quote_and_slash_of_the_fold_ta |
| U+2E17 | DOUBLE OBLIQUE HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+2E1A | HYPHEN WITH DIAERESIS | `["-", 0]` | MISSING | none (no test fails) |
| U+2E3A | TWO-EM DASH | `["-", 0]` | MISSING | none (no test fails) |
| U+2E3B | THREE-EM DASH | `["-", 0]` | MISSING | none (no test fails) |
| U+2E40 | DOUBLE HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+2E5D | OBLIQUE HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+301C | WAVE DASH | `["-", 0]` | MISSING | none (no test fails) |
| U+3030 | WAVY DASH | `["-", 0]` | MISSING | none (no test fails) |
| U+30A0 | KATAKANA-HIRAGANA DOUBLE HYPHEN | `["-", 0]` | MISSING | none (no test fails) |
| U+FFFD | REPLACEMENT CHARACTER | `["", 0]` | MISSING | none (no test fails) |
| U+10EAD | YEZIDI HYPHENATION MARK | `["-", 0]` | MISSING | none (no test fails) |

Summary of the probe: tests notice 10 of the 30 (U+2013, U+2014, U+2018, U+2019, U+201C, U+201D, U+2212 by a behaviour test; U+2215, U+2571, U+29F8 only by the aggregate class-pin test). 20 code points are pinned by no test at all: U+058A, U+05BE, U+1400, U+1806, U+2010, U+2012, U+2015, U+201B, U+201F, U+2E17, U+2E1A, U+2E3A, U+2E3B, U+2E40, U+2E5D, U+301C, U+3030, U+30A0, U+FFFD, U+10EAD. Note the aggregate test `test_fold5_the_class_of_every_dash_quote_and_slash_of_the_fold_table_is_pinned` asserts only the flag (0) and the count 26 of the plain class, not the folded text, so it cannot see a revert to (char, 0) for a dash or quote. The three slash look-alikes have per-character behaviour tests (`test_typography_the_division_slash_u2215...` and the two like it) but those still passed under my probe (the aggregate test failed alone); reason not investigated.

## 5. What I could not do

- Did not write or run new mutants (one-file rule), so the MISSING rows are not closed.
- Causes of survivors 4 and 7 (which other path finds the phrase) not traced.
- The probe is an in-process patch, not the mutation runner; it is evidence of test sensitivity, not a list result.
- Amendment for Q9 in G-text-deltas.md: no list of 30 found there; used G3-p2d-port.md section 6.


## Round 2 (ORDER 022 Q9 and ORDER 023 E12), worktree `/tmp/core-c-q9`, branch `wip-q9`

Run on the worktree copy with `PYTHONPATH=/tmp/core-c-q9/src`, one runner at a time, load below 4. Nothing pushed.

### R2.1 `tests/textnorm_mutants.py`: raw SUMMARY lines and the 7 former problems

```
240 mutants: 228 change behaviour, 12 change only words
240 of 240 good; problems: []
```

The 7 problems of section 3, now (raw lines):

```
ok  KILLED       mixed: a mark of the word's own script flags  [test_a_spacing_mark_or_symbol_cannot_hide_a_mixed_word_and_a]
ok  KILLED       runmap: the composed view is not listed  [test_q9_a_decomposed_name_behind_a_json_escape_is_masked_by_]
ok  KILLED       injection: the pieces do not overlap  [test_q9_a_padded_window_before_a_boundary_moves_the_start_of]
ok  KILLED       injection: the new piece ignores the letters it holds  [test_q9_a_look_alike_phrase_padded_across_a_piece_boundary_i]
ok  KILLED       injection: a boundary with too few letters passes  [test_a_pad_longer_than_the_largest_overlap_is_flagged_never_]
ok  KILLED       injection: the settings are not checked  [test_the_settings_of_the_chunked_read_are_checked]
ok  KILLED       injection: the second half of a halved piece starts at the halfway point  [test_q9_a_look_alike_phrase_padded_across_the_halving_point_]
```

How each was closed:
- WRONG_REASON x3: `mixed: a mark of the word's own script flags` expects `own script group flags` (the assertion's real text); `injection: a boundary with too few letters passes` (`test_a_pad_longer_than_the_largest_overlap_is_flagged_never_passed`) now has a message `HOSTILE-LONG-PAD: the text was read to the end (...)` on the reason-code assert; `injection: the settings are not checked` (`test_the_settings_of_the_chunked_read_are_checked`) no longer lets a TextTooLong escape out of `pytest.raises`: any other failure of the read on a bad setting is turned into `GEOMETRY-UNCHECKED: ...`.
- SURVIVED x4, new killers in `tests/test_textnorm_q9.py`: (a) `runmap: the composed view is not listed`: a name with a literal `&amp;` (or `%25`) stored, written with JSON escapes (letter, U+200B, accent): `undone` decodes the `&amp;`, `canonical(unescaped)` composes nothing, only `composed(unescaped)` holds the stored name. `composed(undone)` alone is EQUIVALENT to `undone` (200,000 seeded texts, never different: `undo` ends at a fixed point of the whole text NFKC that drops invisible characters), so the mutant that removes all three lines is killed by the `composed(unescaped)` line and no separate killer for `composed(undone)` exists. (b) the two overlap mutants: an ASCII phrase padded by invisible, digit or Han characters is ALSO found by the raw squash of the whole text (`_SQUASH` keeps only a-z), whatever the pieces hold, which is why the old killers passed on the mutants; the new ones write the phrase with Cyrillic look-alike letters (not in the raw squash, only found by the views of a piece): `test_q9_a_padded_window_before_a_boundary_moves_the_start_of_the_next_piece_back` (a 300 character pad before the boundary: `_start_of_next` must start before it) and `test_q9_a_look_alike_phrase_padded_across_a_piece_boundary_is_found_only_by_the_moved_back_start` [300] (pads 300, 450, 600). (c) the halved piece started at the halfway point: `test_q9_a_look_alike_phrase_padded_across_the_halving_point_of_a_heavy_piece_is_found_by_value` (look-alike phrase, 300 pad on the halving point, a heavy piece), fails by value (flag missing).
- The mutant count stays 240 (replaced killers, no new textnorm mutant): the pins in `tests/test_textnorm_meta.py` and the changelog count (`len(mm.M) == 240`) are unchanged. `Q9` was added to the killer file list `TESTS` and a parametrized killer may pin one parameter id (`param=`).

### R2.2 `tests/redact_mutants.py`: raw SUMMARY line

```
88 of 93 good; problems: ['8 a set compare hides a look-alike copy', 'N1 U+2044 is no longer mapped to a slash', 'N14 the slash replace is deleted from the alignment return', 'N15 the alias build asks for no budget', 'DM-1 no check per stored original']
```

93 = 63 of before + 30 new `Q9 U+XXXX` mutants; `tests/test_redact_g3_port.py` is now in the killer list (prefix `tests/test_redact_g3_port::`). All 30 Q9 mutants KILLED. Raw non-Q9 BAD lines of that run (the first run, with N15 not yet re-expected):

```
BAD SURVIVED     8 a set compare hides a look-alike copy  []
      first line: 
BAD SURVIVED     N1 U+2044 is no longer mapped to a slash  []
      first line: 
BAD SURVIVED     N14 the slash replace is deleted from the alignment return  []
      first line: 
BAD WRONG_REASON N15 the alias build asks for no budget  [test_budget_3_the_alias_build_is_budgeted]
      first line: E       AssertionError: 300
BAD SURVIVED     DM-1 no check per stored original  []
      first line: 
```

N15 (E12): its `old` snippet is re-pointed at the budget check that is now inside `_build` (`if deadline is not None:\n self._over_budget(deadline)\n for key in _alias_keys(original):`; G7 rounds 3 to 6 made it a local `deadline`); the killer `test_budget_3_the_alias_build_is_budgeted` now has the assertion message `N15-ALIAS-BUDGET: ...` (the first line was `AssertionError: 300`, WRONG_REASON against `DID NOT RAISE`). Re-run `python tests/redact_mutants.py N15`:

```
ok  KILLED       N15 the alias build asks for no budget  [test_budget_3_the_alias_build_is_budgeted]
1 of 1 good; problems: []
```

So the full list is 88 of 93 on the raw first run, 89 of 93 with N15 fixed (the raw N15 line above is the re-run): 4 problems left that are not in this order (see ESCALATIONS.md E13): `8 a set compare hides a look-alike copy`, `N1 U+2044 ...`, `N14 the slash replace ...`, `DM-1 no check per stored original`, all SURVIVED.

### R2.3 The three slashes (U+2215, U+2571, U+29F8)

The probe of section 4 gave "no test fails" for them because with the P2d-1 class `(itself, 0)` the primary view's alignment finds `"a" + c + "b" != fold("a"+c+"b") == "a/b"` and steps aside (`None`), the very same outcome as the port's refused class `None`, so `redact` withholds the line either way and every typography test (which asserts the line is withheld) is satisfied. Only the views that drop a subscript iota differ (they read the character through `fold_view` as a live `/`). The new test `test_q9_a_slash_lookalike_is_refused_by_every_view_of_the_alignment` calls `_Redactor._aligned_fold` for all four view specs directly and fails by value (`Q9-SLASH-VIEW`).

### R2.4 The 30 code points: killer mutant and test

| code point | name | killer mutant | killer test (id) | result |
|---|---|---|---|---|
| U+058A | ARMENIAN HYPHEN | Q9 U+058A ARMENIAN HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+058A]) | KILLED |
| U+05BE | HEBREW PUNCTUATION MAQAF | Q9 U+05BE HEBREW PUNCTUATION MAQAF is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+05BE]) | KILLED |
| U+1400 | CANADIAN SYLLABICS HYPHEN | Q9 U+1400 CANADIAN SYLLABICS HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+1400]) | KILLED |
| U+1806 | MONGOLIAN TODO SOFT HYPHEN | Q9 U+1806 MONGOLIAN TODO SOFT HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+1806]) | KILLED |
| U+2010 | HYPHEN | Q9 U+2010 HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2010]) | KILLED |
| U+2012 | FIGURE DASH | Q9 U+2012 FIGURE DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2012]) | KILLED |
| U+2013 | EN DASH | Q9 U+2013 EN DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2013]) | KILLED |
| U+2014 | EM DASH | Q9 U+2014 EM DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2014]) | KILLED |
| U+2015 | HORIZONTAL BAR | Q9 U+2015 HORIZONTAL BAR is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2015]) | KILLED |
| U+2018 | LEFT SINGLE QUOTATION MARK | Q9 U+2018 LEFT SINGLE QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+2018]) | KILLED |
| U+2019 | RIGHT SINGLE QUOTATION MARK | Q9 U+2019 RIGHT SINGLE QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+2019]) | KILLED |
| U+201B | SINGLE HIGH-REVERSED-9 QUOTATION MARK | Q9 U+201B SINGLE HIGH-REVERSED-9 QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+201B]) | KILLED |
| U+201C | LEFT DOUBLE QUOTATION MARK | Q9 U+201C LEFT DOUBLE QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+201C]) | KILLED |
| U+201D | RIGHT DOUBLE QUOTATION MARK | Q9 U+201D RIGHT DOUBLE QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+201D]) | KILLED |
| U+201F | DOUBLE HIGH-REVERSED-9 QUOTATION MARK | Q9 U+201F DOUBLE HIGH-REVERSED-9 QUOTATION MARK is given back its P2d-1 class | test_q9_a_typographic_quote_is_ordinary_typography_beside_a_fold_hit (tests/test_redact_g3_port.py, id [U+201F]) | KILLED |
| U+2212 | MINUS SIGN | Q9 U+2212 MINUS SIGN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2212]) | KILLED |
| U+2215 | DIVISION SLASH | Q9 U+2215 DIVISION SLASH is given back its P2d-1 class | test_q9_a_slash_lookalike_is_refused_by_every_view_of_the_alignment (tests/test_redact_g3_port.py, id [U+2215]) | KILLED |
| U+2571 | BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT | Q9 U+2571 BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT is given back its P2d-1 class | test_q9_a_slash_lookalike_is_refused_by_every_view_of_the_alignment (tests/test_redact_g3_port.py, id [U+2571]) | KILLED |
| U+29F8 | BIG SOLIDUS | Q9 U+29F8 BIG SOLIDUS is given back its P2d-1 class | test_q9_a_slash_lookalike_is_refused_by_every_view_of_the_alignment (tests/test_redact_g3_port.py, id [U+29F8]) | KILLED |
| U+2E17 | DOUBLE OBLIQUE HYPHEN | Q9 U+2E17 DOUBLE OBLIQUE HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E17]) | KILLED |
| U+2E1A | HYPHEN WITH DIAERESIS | Q9 U+2E1A HYPHEN WITH DIAERESIS is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E1A]) | KILLED |
| U+2E3A | TWO-EM DASH | Q9 U+2E3A TWO-EM DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E3A]) | KILLED |
| U+2E3B | THREE-EM DASH | Q9 U+2E3B THREE-EM DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E3B]) | KILLED |
| U+2E40 | DOUBLE HYPHEN | Q9 U+2E40 DOUBLE HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E40]) | KILLED |
| U+2E5D | OBLIQUE HYPHEN | Q9 U+2E5D OBLIQUE HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+2E5D]) | KILLED |
| U+301C | WAVE DASH | Q9 U+301C WAVE DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+301C]) | KILLED |
| U+3030 | WAVY DASH | Q9 U+3030 WAVY DASH is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+3030]) | KILLED |
| U+30A0 | KATAKANA-HIRAGANA DOUBLE HYPHEN | Q9 U+30A0 KATAKANA-HIRAGANA DOUBLE HYPHEN is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+30A0]) | KILLED |
| U+FFFD | REPLACEMENT CHARACTER | Q9 U+FFFD REPLACEMENT CHARACTER is given back its P2d-1 class | test_q9_the_replacement_character_is_dropped_by_the_fold_and_is_ordina (tests/test_redact_g3_port.py, id [U+FFFD]) | KILLED |
| U+10EAD | YEZIDI HYPHENATION MARK | Q9 U+10EAD YEZIDI HYPHENATION MARK is given back its P2d-1 class | test_q9_a_dash_or_minus_is_ordinary_typography_beside_a_fold_hit_and_i (tests/test_redact_g3_port.py, id [U+10EAD]) | KILLED |
