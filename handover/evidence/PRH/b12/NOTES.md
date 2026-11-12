# Batch 12 (round 11 review, issues 1 to 11 and 13): notes

## What failed or was not run (read this first)
- NOT RUN: the final-head gates that need a heavy slot. The four jobs (one full `pytest -m "not live and not perf" -rs` with my own
  Postgres 16, `tests/prh_mutants.py` as root, the same as user nobody, and `tests/stage_mutants.py`) were queued behind other
  builders' jobs for about 20 minutes (3 slots machine-wide, all busy) and had not started when the 90 minute box ended; I stopped
  my own queued jobs. So there is NO full-run result, NO `-rs` skip table (issue 5 is not met: the skip table by reason and file
  does not exist), and NO mutant result for the head as a whole. `numbers.txt` has no lines for them. The lead's evidence runner must
  run them. What was run on mutants: every new or re-pointed mutant (186 to 201, 120, 174, 190, 198 to 200) was run and killed with its
  declared reason before the last commit; mutant 202 (new, `error_reason`) was checked by hand (the mutated line planted, the killer
  test `test_b11_g4_error_reason_lets_a_crash_pass_and_notes_a_refusal` failed, the file restored); `check_applies()` returns `[]`.
  The full set of 200 mutants has not been run on this head.
- NOT BUILT: issue 10 (stop later drops after a limit). It is stated in SECURITY.md as "(e)" with its next step: a design of what a
  limit may drop. Not closed.
- OWNER-ONLY: issue 12. Not fixed, not reported closed.
- Issue 13 is partly done: the explanation is written (below). Not done: a fail-before run of the whole delta set with its data files
  in one tree, a raising stand-in probe for every catcher (the issue 1 tests do this for the catchers they cover), a sibling probe for held
  identifiers, glued-mark shapes in the runner fuzz, and the timing test run alone on an idle machine (I did not touch that test).
- Issue 4: the docs tests are rewritten (figure test, planted-wrong-figure test, numbers-file-is-what-the-raw-files-give test) and pass
  (7 passed in `tests/test_prh_b9_docs.py`). The old test `test_b10_the_numbers_in_security_are_the_recorded_evidence` was REPLACED by
  them (it compared SECURITY.md with the batch 11 files and could not hold for a rewritten paragraph); its helpers were removed with it.
  The test that checks "30 percent" was made exact (`0.30 percent` contains the text `30 percent`; the withdrawn figure is still refused).
  Mutant for `error_reason` added (202). The ghost mutant numbers in the CHANGELOG were corrected.
- Load: the shared machine had load average 4 to 9 during the measurements (`perf-load.txt`), other builders' jobs were running. The perf
  rows are CPU time of the thread, so load moves them less than wall time, but the perf compare was NOT run alone.
- Docs test runs, ruff, bandit and the figure tests ran while other jobs ran. A `uv run` in a second copy of the tree re-pointed the shared
  editable install for about a minute; I restored it before any job of mine had started (nothing of mine was running).

## Gates that were run (head 8a4b70d5, exit codes)
- `ruff check src tests demos tools`: rc 0. `ruff format --check src tests demos tools`: rc 0 (341 files). `bandit -ll -r src`: rc 0.
- `python tools/scan_repo.py`: rc 0. `gitleaks git ... origin/main..HEAD`: rc 0, "no leaks found", 42 commits.
- `pytest tests/test_prh_b9_docs.py`: 7 passed.
- `pytest -m perf`: 62 passed, 1 skipped (a Postgres test of `tests/demo_askdata`, no DSN in that run; not a `tests/test_prh_*` skip), rc 0.
- `tests/test_prh_perf.py --compare-main`: rc 0, `perf-compare.txt`. The rows that matter against the 6 second budget (CPU seconds at
  262,144 characters): H3 1.843 on this head, 0.366 on main (ratio 5.04); P5 1.827 and 0.415 (4.40). Both are under the budget; the ratios are
  the cost of the batch 8 to 12 rules and are stated in SECURITY.md only through the clean-corpus withheld rates, not as speed.

## Per issue (code and tests; fail-before in `failbefore-b12-new-and-changed-tests-on-242dfd66.txt`: 68 failed, 163 passed)
1. Crash rule at every catcher: approvals/requests.py, evals.py, agent_loop.py (3), tick.py, injection.py; 8 tests; mutants 186 to 191 and 202.
2. Backslash-e glued in a word: glued rule, chain, 12-after and 6/6 rules, Windows path words; a grid of 63 cells; mutants 182, 192 to 194.
3. A piece of a held identifier counts as new (`_has_novel_value` at both sites); mutants 195, 196. Cost: +5 withheld on fuzz set 2 (161 against 156).
6. Gap characters glued to a spaced run; mutant 197. Glued letters, digits and accents: not changed, no count measured (stated in SECURITY.md).
7. Held-value search by interval merge, check every 4096 hits; mutants 199, 200.
8. CPU-time budget (`time.thread_time`); mutant 201.
9. The batch 11 fail-before file was regenerated with no readable values (`--tb=no`): 45 failed, 29 passed.
11. CJK Extension J letters (range up to U+3347F); mutant 198. Class-scan cost 0.043 s.
- Reasons for the new tests that pass on old code: `passing-on-old-reasons.md`.

## Issue 13 explanation
`test_b10_g5_the_wrapper_list_is_the_one_in_the_code` fails on 5c430b6a by design: that tree still has `_WRAPPERS` and no `_WORD_BODY`, and the
test asserts `not hasattr(redact_mod, "_WRAPPERS")`. The three b9_docs failures in the old run were a runner artefact (a missing copied file).

## Other changes to existing tests (all stated, none weakened)
- `tests/test_prh_b8.py`: withheld bound 156 to 161 (issue 3's cost, isolated to `_has_novel_value`; the remnant experiment and redact.py were checked and are not the cause).
- `tests/test_prh_b11.py`: rows flipped for the glued-mark rule, docstring and message fixes (mutant numbers).
- Mutant 185 removed (unreachable after the glued rule), 182 re-pointed to the chain test.
