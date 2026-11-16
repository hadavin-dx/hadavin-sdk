# EVIDENCE RUNNER results, PR H batch 8, code head ea6dbdaf66345b9e6ffe25fc5bc842f1dbca0beb (tag PRHb8)

Record only. Nothing was fixed, judged or edited in the repository. Run 08:19 to about 09:18 UTC (13:49 to 14:48 IST); queue waits for heavy slots were long (other agents held all three). Raw logs: /home/user/build/evidence-raw/PRHb8-ea6dbdaf/ (outside the repository). Small excerpts and my scripts are in this folder.
Own detached worktrees: head ea6dbdaf (`git rev-parse HEAD` equals it, `git status --short` empty), 5f9df48e, main 2a8c2aac. Ref origin/wip/cloud-prh-b8 = b8fbf659 was fetched; I tested the code head ea6dbdaf as the brief says, not b8fbf659.

## What failed, deviated or was not run (first)
1. `uv sync --locked --no-build --all-extras --group test` FAILED (exit 2: the project itself "is marked as --no-build but has no binary distribution"). I ran the same command without `--no-build`; it succeeded. All runs use that venv.
2. prh_mutants as user nobody on ea6dbdaf: 109 of 114 good, exit 1. Survivors / not good: 54 (SURVIVED), 59 (WRONG_REASON), 84 (SURVIVED), 93 (SURVIVED), 111 (SURVIVED). Same list as root. See item 1 below.
3. Mutant 111 survived in 4 of 4 runs of mine (3 alone, 1 inside the full run); I did not see it killed. The builder's run 1 on another head killed it; I did not reproduce a kill, so I cannot say what made it flip.
4. `tests/test_prh_b8.py` of the head cannot be collected on 5f9df48e: `ImportError: cannot import name 'spaced_unknown'`. The builder's "17 failed, 29 passed" cannot be reproduced as written. With a shim (the import wrapped so a missing function raises when called; in a scratch copy of the test file only), result is 19 failed, 29 passed (the 29 are the builder's 29; 17 became 19 because the shim makes the two `spaced_unknown` tests fail by name).
5. `pytest -m perf`: exit 1, `1 failed, 61 passed`; the single failure is the known flaky `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (also failed 3 of 3 alone on the head and 3 of 3 alone on main 2a8c2aac).
6. My own fuzz (item 6) found readable 8-character stretches and unmasked spaced-out values on the head; counts below. These are measurements, no judgment.
7. Not run: the builder's `tests/record_prh_main.py` based clean corpus (I used my own corpus), the full mutation run was not run on the throwaway tree more than once. The per-test split of the other four changed test files between "new" and "old" tests was not made (I ran whole files).

## Results table
| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1a | prh_mutants, user nobody, run 1 (08:22 to 08:30) | `setpriv --reuid=65534 ... python tests/prh_mutants.py` via heavy.sh | 1 | 109 of 114 good; problems: 54, 59, 84, 93, 111 |
| 1b | prh_mutants, root | same as root | 1 | 109 of 114 good; same five |
| 1c | mutant 111 alone, nobody, 3 runs | `... prh_mutants.py "may refuse a text on its own"` | 1,1,1 | 0 of 1 good (SURVIVED) each |
| 2a | throwaway copy, `folded.append((fj, fs))` replaced by `pass`: `pytest tests/test_prh_*.py` | pytest | 0 | 2616 passed in 201.59s |
| 2b | same copy, prh_mutants (root) | python tests/prh_mutants.py | 1 | 109 of 114 good, same five survivors |
| 2c | control, unmodified head, same tests | pytest | 0 | 2616 passed in 204.15s |
| 3 | full pytest on own Postgres 16 (heavy.sh) | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 0 | 13106 passed, 1 skipped, 62 deselected in 497.29s; skip: tests/contracts/test_llm.py:95 |
| 4a | stage_mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| 4b | perf, all 3 slots held | pytest -m perf -rs | 1 | 1 failed, 61 passed, 13107 deselected in 132.59s (the flaky test) |
| 4c | perf compare to main | python tests/test_prh_perf.py --compare-main <main worktree> | 0 | prints S1-S5 and H1-H4 at 262,144 only; see below |
| 4d | builder's all-shapes compare (handover/evidence/PRH/b8/perf_compare_b8.py) | all 3 slots held | 0 | see below |
| 5a | head's test_prh_b8.py on 5f9df48e src | pytest | 2 | collection error ImportError spaced_unknown |
| 5b | same file with the import shim | pytest -rA | 1 | 19 failed, 29 passed in 19.63s |
| 5c | other four changed test files (b7, hidden_unit, steps, tools) on 5f9df48e src | pytest -rA | 1 | 4 failed, 2077 passed in 22.58s |
| 6 | own fuzz, spaced rate, clean corpus | scripts in this folder | 0 | see below |
| 7a | ruff check src tests demos tools | uv run --no-sync ruff check | 0 | All checks passed! |
| 7b | ruff format --check | | 0 | 335 files already formatted |
| 7c | bandit -q -r src demos tools -ll | uv run --with bandit | 0 | only two "nosec encountered (B102)" warnings for src/hadavin_sdk/tools.py:390 |
| 7d | tools/scan_repo.py | | 0 | no findings printed (only a uv warning about UV_NATIVE_TLS) |
| 7e | gitleaks git origin/main..HEAD | gitleaks git --log-opts="origin/main..HEAD" | 0 | 26 commits scanned, no leaks found |
| 1x | files changed vs origin/main (merge base 2a8c2aac) | git diff --name-only origin/main...HEAD | - | 65 files (1-difflist.txt) |

## Item 1: mutant survivors (runner's reason)
All five not-good rows (files 1-mutants-*.txt):
* 54 the scrub does not search the consuming reading: SURVIVED (no failing test)
* 59 the character reading is a result although the text holds a control sequence: WRONG_REASON, killer `test_scrub_character_reading_with_a_sequence_is_withheld` failed with `AssertionError: the secret stood, or a sequence body was shown: 'a <SECRET_REDACTED> ; INFO user[0m<SECRET_REDACTED>'` (the runner pins another fragment)
* 84 the scrub's decoded readings lack the character reading (batch 7): SURVIVED
* 93 direct redact() does not read the ignorable characters (batch 7): SURVIVED
* 111 the collapsed spaced run may refuse a text on its own (no soft rule): SURVIVED (4 of 4 of my runs)
The root run finished (about 5 minutes) with the same result as nobody.

## Item 2: disabling the `(fj, fs)` append in Redactor.find
Scratch copy of the head (tar copy without .git, never the snapshot or the checkout); the only change: lines `folded.append((fj, fs))` replaced by `pass`. `diff` against the head showed exactly that line. `tools.__file__` of the run pointed into the copy.
Result: all tests/test_prh_*.py pass (2616 passed); prh_mutants gives 109 of 114 with the same five survivors, no additional failing test or mutant. (A scratch run of the whole suite was not made, only the PRH test files and mutants.)

## Item 4: perf ratios (head / main, median CPU, one run alone)
Official tool (262,144 chars): S1 1.01, S2 1.00, S3 1.01, S4 1.01, S5 1.04; H1 2.88, H2 3.36, H3 4.85, H4 3.34. It prints no W row and no 65,536 rows.
Builder's all-shapes script (65,536 / 262,144): S1 0.99/0.91, S2 1.00/0.95, S3 1.02/0.92, S4 0.94/0.93, S5 1.00/1.03; H1 2.90/2.89, H2 3.40/3.35, H3 4.49/4.90, H4 3.68/3.71; W 2.23/2.21 (head 0.846 s and 3.509 s at 65,536 and 262,144 chars).

## Item 6: own fuzz (my scripts own_fuzz.py, spaced_rate.py, clean_corpus_own.py)
Fuzz: 4691 texts per tree, handed-out made-up secrets built from parts (two handed out, a made-up key shape and a password shape matched by patterns), 39 hidden-control kinds (C0, C1 openers, ESC alone, ESC before a charset sequence, zero-width, bidirectional, variation selector, tag, encoded ESC in 9 spellings), secret cut once at every position, 1500 random multi-cut texts, 300 split texts (two parts apart), spaced-out secrets with 7 separators, 40 unknown spaced-out values. "Readable" = an 8-character stretch of the secret (for spaced-out: of its spaced form) stands in the output of `tools.prepare_output`.
| tree | texts | readable leaks | withheld | errors |
|---|---|---|---|---|
| main 2a8c2aac | 4691 | 2999 | 0 | 0 |
| 5f9df48e | 4691 | 477 | 371 | 2 |
| head ea6dbdaf | 4691 | 458 | 375 | 2 |
Head leaks by group: hand 14, key 12, long 21, pw 8 (all 55 are the `\e[0m` spelling, a backslash and the letter e), rand 63 (mixed controls; not broken down), split 270 (two halves apart, no hidden character between; 270 on 5f9df48e and 277 on main), spaced 15 and spaced_esc 15 (of 21 each; leaks are the separators tab, no-break space, zero-width plus space, space plus tab, dash with spaces, and for the key also two spaces; the single-space form is masked at head, leaked 7 of 7 on 5f9df48e), spaced_unknown 40 of 40 (an unknown 17-character value that matches no pattern, written with single spaces, is not masked on any tree; `spaced_unknown` finds 0 runs for it, and the key written with tabs is not masked at head). Full list: 6-fuzz-head-leak-list-no-split.txt.
Clean corpus (the head's README, CHANGELOG, SECURITY, docs and src, 7896 texts incl. coloured and zero-width variants, a handed-out secret not in the text): withheld or error: main 57 (0.72%), 5f9df48e 121 (1.53%), head 121 (1.53%); one shared corpus for all three trees.
Spaced-run rule after the 6-distinct-character rule, `redact.spaced_unknown`: repository text of the head (README, CHANGELOG, SECURITY, docs, src, tests, tools, demos, handover; 434 files): 83,184 lines, 2 hold a spaced run at all, 0 changed. Python 3.13 standard library (4,695 files): 1,933,591 lines, 64 hold a spaced run, 0 changed. Positive control (example key spaced out): found 1 run. Seven ordinary spaced texts (alphabet, digits, repeated letter `a` x12, and others): 0 changed.
(The builder's 83,589-line count is from another tree state; mine is 83,184 on this head, with handover included.)

## Item 5: tests that pass on the old code (b8 file, shimmed import) - 29, list in 5-b8-tests-passing-on-old-code-29.txt
20 are the `test_b8_i4_runner_rows_leave_no_readable_stretch[...]` rows (G1-G3, L1-L3, L8-L11, each run and tool), 3 `test_b8_i3_direct_redact_masks_or_withholds_every_copy[ip|mail_cut|mail_esc]`, and `test_b8_i1_short_known_value_with_spaces_is_not_touched`, `test_b8_i1_ordinary_spaced_text_is_unchanged`, `test_b8_i3_a_soft_conflict_is_not_a_refusal`, `test_b8_i4_one_key_cut_twice_is_one_placeholder`, `test_b8_i4_a_handed_out_value_cut_by_a_charset_sequence_and_a_kept_letter`, `test_b8_i6_the_withheld_share_is_bounded`. The 19 failing are in 5-b8-tests-failing-on-old-code-19.txt. The four failing tests of the other files on old code: test_prh_hidden_unit.py::test_readings_are_the_same_set_everywhere, test_prh_steps.py::test_pass_bound_holds_for_a_seeded_search, test_prh_steps.py::test_every_regression_row_needs_at_most_eight_passes, test_prh_tools.py::test_scrub_character_reading_with_a_sequence_is_withheld.

## Item 9: the known timing test, alone
Head: failed, failed, failed (0.70 s, 0.65 s, 0.66 s). Main 2a8c2aac: failed, failed, failed (0.66 s, 0.71 s, 0.68 s). Assertion: `is_superlinear(quadratic, ...)` is False.

## Cleanup and counts
Own Postgres stopped and its folder deleted; own worktrees and scratch copy removed; background shells of mine ended.
