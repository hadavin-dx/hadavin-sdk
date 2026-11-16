# EVIDENCE RUNNER results: Q8b batch 11, head 2153ad85375c97ff942c194ad849af883b0880bd (round 12, REDACTION path)

Recorded, not judged. Raw logs: /home/user/build/evidence-raw/Q8bb11-2153ad85/ (outside the repo). Probe values are never written here; cells are named. The held file with readable probe values is /home/user/build/evidence-raw/Q8bb11-held/probe_extra-head-readable-main-masked.txt.

## What failed or did not run (first)
1. `python tests/q8b_mutants.py` on the head: exit 1, **212 of 229 good, 17 not good** (rows in `q8b_mutants-bad-rows.txt`; the baseline is green: full pytest below passed). Not good: 3 SURVIVED (M159, M163, M190), 6 WRONG_REASON (M192, M198, M199, M200, M215, M216), CRASH 1 (M226), OTHER_TEST 7 (M193, M196, M197, M203, M223, M224, M225). Exact text of each row is in the file; no SNIPPET NOT FOUND row. First failing lines are in the raw log (not copied: they hold made-up values).
2. Not run: pip-audit, semgrep, zizmor, trivy, tests-py312, perf step (`pytest -m perf`; the ticket names no perf item). Ticket acceptance commands beyond the lead's items were not run.
3. `uv sync --locked --no-build` fails here (editable package has no binary build): "Distribution hadavin-sdk==0.1.0 @ editable+. ... marked as --no-build". Used `uv sync --locked --all-extras --group test` (rc 0). Deviation recorded.
4. Fail-before against origin/main is impossible: main has no `tests/test_q8b_batch7.py`, so 3 of the 5 test files fail to collect there (`failbefore-main.log`). Fail-before was done against 166d1313 as the brief says.
5. The known timing flake failed 2 of 3 on head and 3 of 3 on main (shared machine; see table).

## Table
| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 48 files (list in raw dir `item1-files.txt`); delta vs 166d1313: 10 files |
| 2a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | ruff format | `ruff format --check ...` | 0 | 336 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only warnings about nosec at tools.py:389 |
| 4a | repo scan | `python tools/scan_repo.py` | 0 | no output lines |
| 4b | gitleaks | `gitleaks git --log-opts=origin/main..HEAD` (24 commits) | 0 | no leaks found |
| 4c | stage mutants (as nobody) | `python tests/stage_mutants.py` | 0 | 37 of 37 good |
| 5 | full pytest | `heavy.sh ... pytest -p no:cacheprovider -q -m "not live and not perf" -rs` own Postgres 16.15, PGUSER/PGHOST/PGPORT in server env | 0 | 11117 passed, 1 skipped, 29 deselected, 16 xfailed in 597.01s (one skip: tests/contracts/test_llm.py:95) |
| 6a | Q8b mutants | `heavy.sh python tests/q8b_mutants.py` | 1 | 212 of 229 good (see above) |
| 6b | mutation runner mutants (as nobody) | `python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good |
| 7 | fail-before on 166d1313 | 5 test files copied from head | 1 | 57 failed, 169 passed (batch11 file: 53 failed, 50 passed; other 4 files: 4 failed, 119 passed). Same files on head: 226 passed. |
| 8 | unplanted controls | own count (`unplanted.py`) | - | 74 controls, 71 named by a mutant killer, 3 not named; `UNPLANTED_MAX = 3`, `NO_FAULT` empty; the three: test_r1_the_guard_in_front_of_the_address_pattern_is_bounded, test_b8_10_..._linear_time, test_b8_8_a_very_long_run_of_digits_is_read_once (`unplanted-list.txt`) |

Wait in the heavy.sh queue: about 12 minutes for the mutants, about 25 minutes for the cost run (needs all three slots).

## Fail-before detail
Tests of batch 11 that PASS on 166d1313 (50, names in `batch11-passed-on-166d1313.txt`): groups of parametrised ids: b11_3 record path 16, text path 13, flag path 9; b11_8 second word on same line 4; b11_8 first word under 8 characters 2; b11_3 flag authorization next line 2; one each of b11_8 long run of folded lines, no-indent line ends header, repeated headers linear time, b11_4 bare scheme rules. Four tests of the older files that FAIL on 166d1313: `other-files-failed-on-166d1313.txt`.

## Hostile probes (own: `probe.py`, `probe_extra.py`, `fuzz2.py`; probe.py and cost.py were reused from the earlier evidence of 166d1313, extended)
Readable = any 8-character piece of the made-up secret survives in the output. head vs 166d1313 vs main.
| group | cells | readable head | readable 166d1313 | readable main | readable on head, masked on main |
|---|---|---|---|---|---|
| bare/header table (`hdr`: 3 prefixes x 6 schemes x 14 gaps x lengths) | 9072 | 3207 | 3207 | 3207 | 0 |
| folded Authorization over 2-4 lines, 5 schemes | 90 | 0 | 72 | 90 | 0 |
| ordinary word + value (`word`, 5 forms) | 120 | 32 | 32 | 53 | 16 (compass, overpass, encompass, bypass; eq, colon, json, quoted) |
| ordinary word pairs with `` _ - . digits`` between (`pair`, 4 forms: key=value, flag, flag=value, json) | 4160 | 2198 | 2474 | 2402 | 340 (all json form; names in `probe_extra-head-readable-main-masked-cells.txt`) |
| same pairs, record-key check | 1040 | 478 | 478 | 824 | 0 |
| wrapped header by shape (`wrap`: 4 header names x 5 schemes x 11 separators x 2-4 pieces) | 660 | 348 | 552 | 660 | 0 |
| header name, break, scheme, break, token (`nameBreak`) | 44 | 0 | 0 | 0 | 0 |
| capitals cookie in text/json (`cap`, NFKC forms, fullwidth, zero width) | 38 | 18 | 18 | 38 | 0 |
| capitals cookie, record check (`caprec`) | 19 | 7 | 9 | 19 | 0 |

Key finding: cells readable on head and masked on main: 16 in `probe` and 340 in `probe_extra` (all in the json form of an ordinary-word pair or a bare ordinary word). Cell names: `probe-head-readable-main-masked-cells.txt` (16) and `probe_extra-head-readable-main-masked-cells.txt` (340, with input length and a hash); readable values are in the held file named at the top.

Random fuzz, 3000 texts, seed 1, wrapped header with a made-up secret cut into 2-5 pieces (shape A same line, B indented continuation, C no-indent break): readable texts / total.
| shape | head | 166d1313 | main |
|---|---|---|---|
| A (same line) | 273 / 979 | 289 / 979 | 852 / 979 |
| B (indented continuation) | 0 / 1042 | 778 / 1042 | 879 / 1042 |
| C (no indent) | 807 / 979 | 808 / 979 | 852 / 979 |
Head, shape A by scheme: ApiKey 79, Basic 75, Bearer 59, Digest 3, Token 57. Head, shape C by scheme: ApiKey 170, Basic 163, Bearer 165, Digest 148, Token 161.

## Cost, clean() on 60,000 characters, median of 3, run alone (all three slots held)
| text | head | 166d1313 | main | head/main | 166d1313/main |
|---|---|---|---|---|---|
| hostile | 0.302 s | 0.245 s | 0.146 s | 2.07x | 1.68x |
| prose | 0.310 s | 0.239 s | 0.154 s | 2.01x | 1.55x |
Builder's figure was 0.446 s and 0.340 s (2.69x and 2.45x); this run measured lower. Raw: `cost-and-flake.txt`.

## Known timing flake `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, alone
Head: failed, failed, passed. origin/main: failed, failed, failed.

## Setup notes
Own Postgres 16.15 on 127.0.0.1:56731 run as user nobody, PGUSER/PGHOST/PGPORT set in the server environment (the dblink test that failed in the earlier evidence passed in the full run). Python 3.13.18, venv at /home/user/build/EV-Q8bb11-2153ad85/venv. Fixed nothing, edited no src or tests of the head. Scripts here: probe.py, probe_extra.py, fuzz2.py, compare2.py, cost.py, cost_clean.py, unplanted.py.
