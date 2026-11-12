# PR H batch 8 (round 7) builder notes

Branch core/prh-b8 from 5f9df48e; pushed to wip/cloud-prh-b8. Failures and not-run items are in the lead report first; this file holds the detail.

## What changed, per issue
| Issue | Fix | Where | Tests (tests/test_prh_b8.py unless named) | Mutants |
|---|---|---|---|---|
| 4 (9 readable stretches) | Class: several cuts in one value. Two new readings: `hidden.strip_keeping` (a lone ESC keeps the next byte) and `hidden.strip_mixed` (same, with an nF charset sequence removed whole); cut readings are searched with ignorable characters out; the tool scrub no longer returns the text as written when only the mixed reading holds a handed-out value | hidden.py, runmap.py (`add_readings`, `mixed_reading`), tools.py (`_scrub`) | `test_b8_i4_*` (runner rows, seeded multi-cut property run+tool, LCG 3096 texts, runner's exact 3096 texts, mixed reading, one key cut twice) | 102, 103, 104, 112, 113, 114 |
| 3 (direct redact) | `Redactor.find` folds the keeping reading and the faithful character reading as SOFT readings: a conflict withholds only when a window of the soft values stands in the output | redact.py | `test_b8_i3_*` | 105, 106 |
| 1 (spaced-out) | Known values of 12 or more characters: `spaced_spans` (sweep, direct), `_mask_spaced_out` (tool), run path. Unknown: collapsed spaced run as a soft view | redact.py, runmap.py, tools.py, defaults.py | `test_b8_i1_*` | 107 to 111 |
| 2 (dead call) | Removed `compare_readings` in `_consuming_wins` with evidence | runmap.py | `consuming_conflict_dead.py` (7413 calls: same 6307, second 1106, conflict 0) | existing mutants re-pointed |
| 5 | Property test that no decoded reading holds an ignorable character; the old "equivalent" claim is replaced by a runnable test | `test_b8_i5_*` | (property, no mutant) | none |
| 6 | b7 tests tightened to exact outputs; withheld-share bound; mutant numbers in docstrings fixed | test_prh_b7.py, `test_b8_i6_*` | | |
| 7 | Measured (below) | `mojibake_loss.py` | | |
| 8 | The two evidence-folder `noqa: S311` removed (the evidence folder is not linted); the test in b7 keeps its one with a stated reason; b8 uses a hand-written LCG, plus ONE `noqa: S311` to reproduce the runner's own seed exactly | | | |
| 9 | Nits fixed (six space-like C0 characters, annotation, compute once, escape for U+0301, docstring of `Readings`) | | | |

## Measurements
* Runner fuzz (3096 texts, runner_own_fuzz.py), readable-stretch leaks / withheld: head 0 / 235; previous head 5f9df48e 9 / 226; main 1607 / 0.
* Builder fuzz (3000 texts, fuzz_classify.py), readable / strict withheld: head 0 / 155; 5f9df48e 0 / 143; main 1408 / 0. Direct `redact()` withheld 22 of 3000.
* Withheld causes at head (builder fuzz): readings-or-other 105, piece 43, limit 7. The 7 limit texts are the same texts as the Issue 2 work-limit texts of 5f9df48e (same count, same cause); the limit is converted to a withheld note, it is not removed.
* Unknown spaced-out check: 0 of 83,589 ordinary lines changed; 1 of 1 planted control caught (`spaced_unknown_rate.py`).
* Issue 7: 32 made-up mojibake lines; 13 hold a C1 string opener and lose 546 characters beyond the opener. Lowercase-only text holds none.
* Issue 9 `check_only` (a value found only inside a swallowed unterminated string body withholds the whole text): NOT narrowed in this batch (no leak-free narrowing was found in the time box); pinned as it is by the withheld-share bound.

## Corrections to older notes
* b7 NOTES "583 texts made only of secrets" versus 527: the 527 is the final-tree column (the 583 counted texts before dedup).
* The b7 notes said two `noqa: S311`; there were three (two evidence files and one test). Now: one in tests/test_prh_b7.py (reason stated), one in tests/test_prh_b8.py (reason stated).

## Fail-before and the tests that pass on old code
Fail-before: failbefore-test_prh_b8.txt (clean detached worktree of 5f9df48e with only tests/test_prh_b8.py copied in): 17 failed, 29 passed, 0 collection errors. (The 17 include the keeping and mixed reading tests, which fail by a missing function or argument on the old code: the new API does not exist there.)
Why the other tests pass on old code (one line per group, including the 46 of b7):
* b7 i1 encoded escape rows (22 of the 46: the `entity`, `entity_hex`, `json`, `percent` rows): these spellings were already decoded correctly on 5f9df48e; they are controls for the class, killed by mutant 84 in the b7 set (rows `T`, `Z`, `a`, `q`, `7`, `A` with `percent`/`percent_up` are the ones that fail on c802cc0f).
* b7 i5 opener rows (`\x90`..`\x9f` never shows its tail, known value cut by an opener, bell-ended rows): controls of the 5f9df48e fix; killed by mutants 91 and 98.
* b7 i10 ignorable rows, clean corpus, a cut copy beside a masked copy, i12 h2 row, mutant 95 rows 5 and 6: controls for fixes made in b7; killed by mutants 95, 99 and 101 of the b7 set.
* b7 i8 plain ZWJ text, combining mark, i9 spaced-out secret: documented behaviour controls (no leak, no over-withholding); the spaced-out one now states what is and is not masked.
* b8 runner rows L1..G3 and direct rows mail_cut, mail_esc, ip: controls (these shapes were masked on 5f9df48e; the nine leaks were in the random multi-cut texts, which `test_b8_i4_*_generator_*` and the seeded property reproduce); b8 ordinary-text and short-value tests: no-over-masking controls; `test_b8_i3_a_soft_conflict_is_not_a_refusal` and `test_b8_i4_one_key_cut_twice_is_one_placeholder`: old code already gave this output; they are killed by mutants 106 and 104 (the mutant removes the new code and the output changes); `test_b8_i6_the_withheld_share_is_bounded`: a bound that old code also meets (155 and 22 are the head's numbers; old 143), it fails only for a redactor that withholds much more.

## The 16 files outside the ticket's allowed list (ticket 8.7 checked)
Covered by ticket 8.7 (rev 4 table): defaults.py, scrub_settings.py, tests/fixtures/prh_accidental_pairs.json, tests/fixtures/prh_main_passes.json, tests/test_k5_fixes3.py (5 files). Not on the 8.7 list, each with its reason: tests/test_prh_b7.py and tests/test_prh_b8.py (the new tests of batches 7 and 8: the ticket's expression names the older test files only; the lead should add them to 8.7), and the 10 files under handover/evidence/PRH/ (the evidence folder the brief allows for notes, scripts and logs). Nothing reverted.

## Mutants
New mutants 102 to 114 (101 was taken by batch 7). `python tests/prh_mutants.py` results are in the lead report (exit codes).

## Earlier notes of this batch

## Issue 7 measurement (made-up mojibake, mojibake_loss.py)
32 made-up lines (capitalised Russian and Greek words read as Latin-1). 13 hold a C1 string opener (U+0090, U+0098, U+009D, U+009E, U+009F) and lose 546 characters beyond the opener in total (all 13 lose more than 5). Lowercase-only text holds none. Outcome: the loss is real for mojibake that contains capital letters; it is the price of reading an unterminated opener as hidden text.
