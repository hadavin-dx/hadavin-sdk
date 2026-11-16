# EVIDENCE RUNNER results: Q8b batch 12, head a148bda6126aa0fcd59e350d41656651a34d139e (round 12 evidence, REDACTION path)

Recorded, not judged; nothing was fixed. Head confirmed by `git rev-parse HEAD` in a detached worktree, tree clean. Compared trees: head, 2153ad85 (previous reviewed head), origin/main 2a8c2aac. Raw logs live outside the repository: /home/user/build/evidence-raw/Q8bb12-a148bda6/. Probe values are never written here (cells are named only); the held files with readable probe text stay in the raw folder (`*-held-readable-head-masked-main.txt`).

## What failed or did not run (first)
1. `pytest -m perf` (the CI performance step, run alone with all three slots held): exit 1, 1 failed, 28 passed. The one failure is the known `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (assertion at line 836). See the flaky rows below for the 3 and 3 runs.
2. Probe groups, readable on head and masked on main: 16 cells in `probe` (bare compass, overpass, encompass, bypass with eq, colon, json, quoted forms) and 75 cells in `probe12` (all of them the 15 bare ordinary words in five forms: eq, colon, json, quoted, upper-case json; the flag form is masked on both). 0 in `probe_extra` (pairs, wrapped headers, capitals cookie). Cell names in the two `*-head-readable-main-masked-cells.txt` files.
3. Not run: pip-audit, semgrep, zizmor, trivy, Python 3.12 (not available here, as in earlier rounds); the ticket's own acceptance commands beyond the lead's items 1 to 8. `uv sync --locked --no-build` fails here (editable package has no binary build: "Distribution hadavin-sdk==0.1.0 @ editable+. ... marked as --no-build"); used `uv sync --locked --all-extras --group test` (exit 0).
4. Builder claims that differ from what I measured: cost ratios (builder 1.50/1.36, 1.23/1.24, 1.57/1.31, 1.34/1.04; measured table below). Everything else I checked equals the builder's number (241 of 241 twice, 11147 passed, 15 failed/15 passed, 16 failed/75 passed, 4 controls: see item 8 for my count of 3 and 7).
5. Queue waits (heavy.sh and the all-slot lock were busy with other agents): full pytest about 10 minutes, q8b root about 35 minutes, cost and perf about 17 minutes. Fail-before, probes, fuzz and lint ran outside the queue.

## Table
| # | Item | Command (short) | Exit | Result |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 66 files (`item1-changed-files.txt`); 26 commits origin/main..HEAD |
| 2a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | ruff format | `ruff format --check src tests demos tools` | 0 | 337 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no issues; only nosec warnings (tools.py:389) |
| 4a | repo scan | `python tools/scan_repo.py` | 0 | no findings printed |
| 4b | gitleaks | `gitleaks git --log-opts=origin/main..HEAD` | 0 | 26 commits scanned, no leaks found |
| 5 | full pytest | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, own Postgres 16 (PGHOST, PGPORT, PGUSER in the server environment) | 0 | 11147 passed, 1 skipped (tests/contracts/test_llm.py:95), 29 deselected, 16 xfailed in 504.46s |
| 6a | Q8b mutants, root | `heavy.sh python tests/q8b_mutants.py` | 0 | 241 of 241 good; 240 rows KILLED and 1 row `ok CRASH` (M226, shown as good by the runner); no SURVIVED, SNIPPET NOT FOUND, WRONG_REASON, OTHER_TEST; M195 absent; M234 to M246 present |
| 6b | Q8b mutants, nobody | same, via `setpriv --reuid=65534` | 0 | 241 of 241 good, same rows as root (`q8b-mutants-*-full-table.txt`) |
| 6c | stage mutants (nobody) | `python tests/stage_mutants.py` | 0 | 37 of 37 good |
| 6d | mutation runner mutants (nobody) | `python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good |
| 6e | CI perf step | `pytest -q -m perf -rs` alone | 1 | 1 failed (known timing test), 28 passed |
| 7 | fail-before | 7 test files of DELTA-FILES copied into a detached worktree of 2153ad85 (its own src; import path printed as the worktree's src) | 1 | 31 failed, 317 passed, 15 xfailed. Per file (failed/passed): batch12 15/15, batch10 15/52, batch8 1/23, batch11 0/103, batch2 0/19, batch8_lines 0/7, credential_keys 0/98 (+15 xfailed). batch10+batch8: 16 failed, 75 passed. |
| 8 | unplanted controls | own script `unplanted.py` and a wall-clock listing | - | `UNPLANTED_MAX = 3`, `NO_FAULT` empty; 74 controls in the lines table, 71 named by a killer, 3 not named (list below). Wall-clock tests in the q8b test files whose name appears nowhere in `tests/q8b_mutants.py`: 7 (list below) |

Fail-before: the 15 batch-12 tests that pass on 2153ad85 are the same 15 ids as the builder's `b12-passed-on-old.txt` (`diff` empty). Lists: `failbefore-failed-on-2153ad85.txt` (31 ids), `failbefore-passed-on-2153ad85-b12-b10-b8.txt` (90 ids, includes unchanged tests of those files).

Item 8 lists. Controls with no mutant killer (lines table): `test_r1_the_guard_in_front_of_the_address_pattern_is_bounded`, `test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time`, `test_b8_8_a_very_long_run_of_digits_is_read_once`. Other wall-clock tests whose name is not in `q8b_mutants.py` (the builder counts the first only): `test_b11_8_a_long_run_of_folded_lines_is_read_in_linear_time`, `test_b8_5_the_timing_of_the_flag_rule_on_hostile_text_is_bounded_and_close_to_the_old_bound`, `test_b10_1_a_long_run_of_line_breaks_after_a_scheme_word_is_read_in_linear_time`, `test_b10_2_a_long_run_of_digest_fold_lines_is_read_in_linear_time`, plus the three above (`wallclock-controls.txt`).

## Flaky timing test (alone, all three slots held)
`tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` run alone, 3 times each (all three heavy slots held, each tree's own src on the path): head a148bda6 failed, passed, failed (1 of 3 passed); origin/main failed 3 of 3. Also failed once inside the CI perf step (row 6e). Raw: `flaky.out` in the raw folder (copied here).

## Cost: clean() (`approvals.channel.clean`), median of 3, seconds, run alone with all three slots held
| text | size | head | main | 2153ad85 | head/main | 2153ad85/main |
|---|---|---|---|---|---|---|
| hostile | 30,000 | 0.081 | 0.072 | 0.144 | 1.13 | 2.00 |
| hostile | 60,000 | 0.182 | 0.162 | 0.295 | 1.12 | 1.82 |
| hostile | 120,000 | 0.359 | 0.303 | 0.600 | 1.18 | 1.98 |
| hostile | 262,144 | 0.910 | 0.661 | 1.380 | 1.38 | 2.09 |
| prose | 30,000 | 0.074 | 0.067 | 0.151 | 1.10 | 2.25 |
| prose | 60,000 | 0.146 | 0.136 | 0.301 | 1.07 | 2.21 |
| prose | 120,000 | 0.298 | 0.266 | 0.645 | 1.12 | 2.42 |
| prose | 262,144 | 0.653 | 0.581 | 1.391 | 1.12 | 2.39 |
Raw: `cost-raw.txt`. Builder claims (hostile/prose) 1.50/1.36, 1.23/1.24, 1.57/1.31, 1.34/1.04 for the four sizes. Hostile and prose texts are my own generators (`cost_clean.py`, seeded, the same as the round-11 evidence).

## Hostile probes (own scripts: `probe.py`, `probe_extra.py`, `probe12.py`, `fuzz2.py`, `fuzz3.py`, `compare3.py`)
Readable = any 8-character piece of the made-up secret survives in the output (secrets are random letters made at run time). Counts are readable cells / cells.
| group | cells | head | 2153ad85 | main | readable on head, masked on main |
|---|---|---|---|---|---|
| `hdr` bare/header table (3 prefixes x 6 schemes x 14 gaps) | 9072 | 2323 | 3207 | 3207 | 0 |
| `fold` folded Authorization 2 to 4 lines, 5 schemes | 90 | 0 | 0 | 90 | 0 |
| `word` ordinary word + value, 5 forms | 120 | 32 | 32 | 53 | 16 (compass, overpass, encompass, bypass; eq, colon, json, quoted) |
| `wordshort` | 24 | 24 | 24 | 24 | 0 |
| `recordsens` record-key check of those words | 24 | 6 | 6 | 18 | 0 |
| `wrap` wrapped header by shape, 4 names x 5 schemes | 660 | 348 | 348 | 660 | 0 |
| `nameBreak` | 44 | 0 | 0 | 0 | 0 |
| `pair` ordinary word + credential word, joiners and digits, 4 forms | 4160 | 1858 | 2198 | 2402 | 0 |
| `pairrec` record check of the same names | 1040 | 478 | 478 | 824 | 0 |
| `cap` capitals cookie forms (NFKC, fullwidth, zero width) text/json | 38 | 18 | 18 | 38 | 0 |
| `caprec` capitals cookie, record check | 19 | 7 | 7 | 19 | 0 |
| `pair12` 15 ordinary words x 10 credential words x 14 joiners x 7 forms (eq, quoted, json, json with spaces, flag, single quotes, upper case) | 14700 | 2372 | 4156 | 3426 | 0 |
| `pair12rec` record check of those names | 2100 | 416 | 416 | 1350 | 0 |
| `bare15` the 15 bare ordinary words x 6 forms (owner decision: stay shown) | 90 | 90 | 90 | 15 | 75 |
| `bare15rec` | 15 | 15 | 15 | 15 | 0 |
| `shapeA` secret cut on the same line, 14 scheme words or none, 3 names | 336 | 312 | 312 | 336 | 0 (Digest 0 of 24; every other scheme and no scheme 24 of 24) |
| `fold12` folded header, scheme word or none (14), 11 break characters, 4 indents, 0 to 4 extra first-line words | 9240 | 3945 | 8517 | 9240 | 0 |

`fold12` split on head: shape B (indented) 1755 of 6930; shape C (no indent) 2190 of 2310. By break: lf, crlf, cr 210 of 840 each; U+2028, U+2029, VT, FF, U+0085 195 of 840 each; FS, GS, RS (not among the five new ones) 780 of 840 each. By scheme: Digest 45 of 660; every other scheme and no scheme 300 of 660 each. By extra first-line words (0 to 4): 789 of 1848 each (equal). Tables: `compare3-table.txt`.

Random fuzz (made-up secret cut in 2 to 5 pieces, 3000 texts each; readable / total):
| fuzz | shape | head | 2153ad85 | main |
|---|---|---|---|---|
| `fuzz2` seed 1 (5 schemes, same generator as round 11) | A same line | 273 / 979 | 273 / 979 | 852 / 979 |
| | B indented | 0 / 1042 | 0 / 1042 | 879 / 1042 |
| | C no indent | 807 / 979 | 807 / 979 | 852 / 979 |
| `fuzz3` seed 1 (12 scheme words or none, 8 break characters, 0 to 4 extra first-line words) | A | 340 / 998 | 348 / 998 | 863 / 998 |
| | B | 294 / 1017 | 791 / 1017 | 885 / 1017 |
| | C | 803 / 985 | 807 / 985 | 873 / 985 |
`fuzz-counts.txt` holds all counts including per scheme. In `fuzz3` on head, shape B is readable in 294 texts; fuzz2 (the round-11 generator) shows 0, so the two generators differ in what they cut.

## Files in this folder
`RESULTS.md`, `item1-changed-files.txt`, `q8b-mutants-root-full-table.txt`, `q8b-mutants-nobody-full-table.txt`, `failbefore-*.txt`, `*-head-readable-main-masked-cells.txt` (cell name and a short hash of the input), `compare3-table.txt`, `fuzz-counts.txt`, `cost-table.txt`, `cost-raw.txt`, `unplanted-list.txt`, `wallclock-controls.txt`, and the probe, fuzz, cost and compare scripts (`probe.py`, `probe_extra.py`, `probe12.py`, `fuzz2.py`, `fuzz3.py`, `cost_clean.py`, `cost.py`, `unplanted.py`, `compare2.py`, `compare3.py`).

R-numbers used: R368 to R373 and R448 read via the preamble only; I did not open the studio bible (it is not in this checkout). EVIDENCE RUNNER: no judgments, no fixes, no push, no commit. Tokens: about 60,000 input and 25,000 output of my own, estimated.
