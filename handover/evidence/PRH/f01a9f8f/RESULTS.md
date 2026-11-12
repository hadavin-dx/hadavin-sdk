# EVIDENCE RUNNER results, PR H batch 9, head f01a9f8ff3e5174da61b1aad79572c1ee1eeb13a (tag PRHb9)

Record only. Nothing was fixed, judged or edited in the repository. Run 10:58 to about 11:45 UTC (16:28 to 17:15 IST). Raw logs: /home/user/build/evidence-raw/PRHb9-f01a9f8f/ (outside the repository); small excerpts and my scripts are in this folder. Detached worktrees: head (`git rev-parse HEAD` equals f01a9f8f, `git status --short` empty before and after), main 2a8c2aac, previous head ea6dbdaf. The ref origin/wip/cloud-prh-b9 tip is f01a9f8f as the lead said.

## What failed, deviated or was not run (first)
1. Nothing in the gated items failed. The one failure anywhere is `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` inside `pytest -m perf` (known flaky test, see item 9).
2. `uv sync --locked --no-build ...` fails for the project itself (first runner's log: "marked as --no-build but has no binary distribution"); the venv was built without `--no-build` (sync2.log). All runs use that venv.
3. The builder's fail-before numbers do not match mine. Builder: 33 failed, 2046 passed over five files, 170 tests that pass on old code. Mine, same five files copied from the head into ea6dbdaf: 33 failed, 2050 passed; the failed list is identical (33 names); tests that pass on old code in b7, b8, b9 and b9_docs: 174. The four extra rows are `test_b9_g1_mutant_31_the_scrub_returns_the_checked_result_not_the_first_scrubbed_reading` and three rows of `test_b9_g1_mutant_114_...` (in `tests/test_prh_b9.py`); they are missing from builder-evidence/passing-on-old-ea6dbdaf.txt. The builder's file has one row of mine's complement: none other. So the 170-row list is not complete; the real count is 174 (list: 5-tests-passing-on-old-code-174.txt).
4. Full pytest: 13170 passed, 1 skipped, 62 deselected; the builder wrote 13166 passed. Four more tests than the builder's number (same four as in 3, as far as I can tell; I did not prove the match).
5. Heavy jobs of other agents ran at the same time as mine (all three slots are shared); my own jobs ran one at a time, mutants first. Load average was 4 to 5 during the runs.
6. Not run: the builder's all-shapes perf script (65,536 and W row); only the official `--compare-main` tool (262,144 characters, rows S1 to S5 and H1 to H4) was run.
7. My own fuzz measures readable 8-character stretches and withheld texts; it does not judge. Leak counts are listed below (head still shows 321 texts with a readable stretch).

## Results table
| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1a | prh_mutants, root, one run, first | `python tests/prh_mutants.py` via heavy.sh (11:00 to 11:07) | 0 | 129 of 129 good; problems: [] |
| 1b | prh_mutants, user nobody (uid 65534, clean env, tree copy) | same via setpriv, heavy.sh (11:07 to 11:12) | 0 | 129 of 129 good; problems: [] |
| 2 | full pytest on own Postgres 16 (own socket and port) | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 0 | 13170 passed, 1 skipped, 62 deselected in 525.51s; skip: tests/contracts/test_llm.py:95 |
| 3 | stage_mutants | `python tests/stage_mutants.py` via heavy.sh | 0 | 37 of 37 good; problems: [] |
| 4a | `pytest -m perf -rs`, all 3 slots held | flock on the three slot files | 1 | 1 failed, 61 passed, 13171 deselected in 126.72s (the known flaky test) |
| 4b | perf compare to main | `tests/test_prh_perf.py --compare-main <main worktree>` alone | 0 | ratios below |
| 4c | perf compare to ea6dbdaf | same with the ea6dbdaf worktree | 0 | ratios below |
| 5 | fail-before (5 changed test files on ea6dbdaf src) | pytest -rA | 1 | 33 failed, 2050 passed in 54.46s |
| 6 | own fuzz, clean corpus, spaced rate | scripts in this folder | 0 | numbers below |
| 7a | ruff check src tests demos tools | `uv run --no-sync ruff check` | 0 | All checks passed! |
| 7b | ruff format --check | same | 0 | 338 files already formatted |
| 7c | bandit -q -r src demos tools -ll | `uv run --with bandit` | 0 | only warnings (nosec B102 at src/hadavin_sdk/tools.py:390 and two "Test in comment" warnings) |
| 7d | tools/scan_repo.py | | 0 | no findings printed |
| 7e | gitleaks git origin/main..HEAD | `gitleaks git --log-opts=origin/main..HEAD` | 0 | 29 commits scanned, no leaks found |
| 1x | files changed vs origin/main | `git diff --name-only origin/main...HEAD` | 0 | 101 files (1-difflist.txt) |
| 9 | known timing test alone | see item 9 | | see item 9 |

## Item 1: mutants
Both runs finished with every mutant killed for the planted reason (no survivor, no WRONG_REASON row). Files: 1-mutants-root.txt, 1-mutants-nobody.txt (129 `ok` rows each). My jobs: one mutant run at a time; other agents' jobs ran at the same time.

## Item 4: perf ratios (head / other, median CPU, 262,144 characters, one run, alone)
| shape | vs main 2a8c2aac | vs ea6dbdaf |
|---|---|---|
| S1 plain ASCII log | 1.04 | 1.04 |
| S2 tab table | 1.01 | 1.04 |
| S3 JSON lines | 1.09 | 1.03 |
| S4 Hindi | 1.02 | 1.02 |
| S5 Persian ZWNJ emoji | 1.01 | 0.99 |
| H1 coloured output | 2.90 | 1.02 |
| H2 colour inside a word | 3.39 | 1.02 |
| H3 sgr0 inside a word | 4.82 | 1.01 |
| H4 colourised log with sgr0 | 3.48 | 1.01 |
Head seconds: S1 0.406, S2 0.415, S3 0.433, S4 0.808, S5 1.407, H1 0.707, H2 1.089, H3 1.828, H4 1.076 (main run); the ea6dbdaf run gave the same within 0.03 s. No W row and no 65,536 rows (the tool does not print them).

## Item 5: fail-before
Five files (tests/test_prh_b7.py, b8, b9, b9_docs, test_prh_tools.py) plus tests/seeded.py copied from the head into a detached worktree of ea6dbdaf; `PYTHONPATH` put its `src` first (checked: `hadavin_sdk.__file__` pointed into that worktree). 33 failed, 2050 passed. The 33 failing names equal the builder's 33 (diff empty). Failing by test: b9 g5 (8 + 4 + 1 rows), b9 e3 (5), b9 g3 (3), b9 g9 (2), b9 e1 (2), b9 g8 (2), b9 g7 (1), b9 e2 (1), b8 i6 (1), b9_docs (3). Lists: 5-tests-failing-on-old-code-33.txt and 5-tests-passing-on-old-code-174.txt (b7, b8, b9, b9_docs only; test_prh_tools.py has 1876 passing rows, not listed).

## Item 6: own fuzz (own_fuzz_b9.py; made-up values built from parts; 5455 texts per tree; the readable-stretch test is any 8 characters of the planted secret still in the output of `tools.prepare_output`)
| tree | texts | texts with a readable stretch | withheld | errors (RedactionError) |
|---|---|---|---|---|
| main 2a8c2aac | 5455 | 3515 | 0 | 0 |
| ea6dbdaf | 5455 | 611 | 375 | 2 |
| head f01a9f8f | 5455 | 321 | 465 | 2 |
Head, readable by group: split 261, spaced_unknown 40 (an unknown value of no pattern shape, spaced out), opener_front 15, rand 3 (multi-cut: rand/566, 808, 1032), spaced 1 (hand/dash), spaced_esc 1 (hand/dash). Head groups with 0 readable stretches: hand, key, long, pw, opener (480 texts; 5 withheld). ea6dbdaf for the same groups: opener 120, spaced 24, spaced_esc 24, hand 14, key 12, long 21, pw 8, rand 63. My `opener_front` group is the secret's first six characters, then ` = `, then a string opener, then the rest (15 texts on every tree, readable on all three). Errors on head: rand/465 and rand/607 (same two on ea6dbdaf). Withheld on head by group: rand 307, pw 72, key 30, long 21, hand 14, split 10, opener 5, runcap 3, runcap_secret 3.
Run cap (texts built of N runs of 12 spaced single characters of 12 different letters, runs separated by the word `ok`): head shows 31 and 32 runs (output of 842 and 869 characters) and withholds 33, 40 and 100 runs (output of 29 characters, the withhold marker), with or without an example key in the text. main and ea6dbdaf show every text at every N.
Separators tried for the spaced-out secrets (new this batch): line break, zero-width joiner, word joiner plus space, tab plus no-break space, in addition to the earlier ones. Only the dash-with-spaces separator is readable on head (hand secret).
Clean corpus (one shared corpus for all trees: README, CHANGELOG, SECURITY, docs and src of the head; 7950 texts, with coloured and zero-width variants, a handed-out made-up value not in the text): withheld or error main 69 (0.87%), ea6dbdaf 128 (1.61%), head 126 (1.59%).
Spaced-run rule (`redact.spaced_unknown`): Python 3.13 standard library (4695 files, 1,933,591 lines): 71 lines hold a spaced run, 0 changed. Head repository including handover (494 files, 89,815 lines): 29 lines hold a spaced run, 11 changed; none of the 11 is outside `handover/` (they are lines of saved test-failure logs). Positive control: 1 run found.

## Item 9: the known timing test, alone
Head: failed, failed, failed (0.58 s, 0.58 s, 0.60 s). Main 2a8c2aac: see the addendum at the end of this file.

## Cleanup and counts
See the end of this file.
