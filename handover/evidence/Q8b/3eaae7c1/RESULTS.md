# Evidence results: Q8b batch 8, head 3eaae7c1b754d4c0e4f624d0d9fd1e6d0dde6a81 (round 8 evidence, redaction path)
Runner only records. Nothing was fixed or judged. Raw logs: /home/user/build/evidence-raw/Q8bb8-3eaae7c1/ (outside the repo). Date 2026-11-12 UTC. Worktree and venv are my own; origin main 2a8c2aac, previous head b7d7cd18.

## What failed, was not run, or differs from CI (first)
- `uv sync --locked --no-build --all-extras --group test` (the CI command) FAILED here: "hadavin-sdk==0.1.0 @ editable+. can't be installed because it is marked as --no-build but has no binary distribution". I installed with the same command minus `--no-build` (exit 0). All results below use that env (Python 3.13.18).
- Timing test `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, run ALONE (all three heavy slots held), failed 2 of 3 on head and 3 of 3 on main ("a quadratic function must be flagged"). See table.
- The perf step of ci.yml (`pytest -m perf`) was NOT run (not named in the Q8b ticket; the full pytest deselected 29 perf/live tests).
- The "120 cells readable on head, masked on main" list of the builder was NOT reproduced; my own probe has 118 cells (see below), the sets differ.
- Fail-before on b7d7cd18 and main: 18 of 72 delta tests failed on b7d7cd18; 54 passed on old code (list files below).
- Readable values on head in my probe (also readable on main and b7d7cd18 unless marked): bare `--tokens`/count tokens (intended), `AWS4-HMAC-SHA256` scheme value after `--authorization` or `Authorization:`, 7 prefix words before `password` flag (hyphen and underscore), 40 and 41 digits after `pass`/`password` before `=`, a second word after `--pass2`, `--password`, `--newpass`, `authorization=`. Full table: probe-table.md.

## Results table
| item | command | exit code | last line |
|---|---|---|---|
| 1 diff list | `git diff --name-only origin/main...HEAD` | 0 | 45 files (1-difflist.txt) |
| 2 ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 ruff format | `ruff format --check src tests demos tools` | 0 | 333 files already formatted |
| 3 bandit | `bandit -q -r src demos tools -ll` | 0 | only warnings: nosec B102 at tools.py:389 |
| 4 scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 4 gitleaks origin/main..HEAD | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 full pytest | `-p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh, own Postgres 16, HADAVIN_REQUIRE_PINNED_UNIDATA=1 | 0 | 10844 passed, 1 skipped, 29 deselected, 16 xfailed in 449.74s (skip: tests/contracts/test_llm.py:95) |
| 6 q8b mutants | `python tests/q8b_mutants.py` | 0 | 155 of 155 good; problems: [] |
| 6 stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 6 runner mutants (as user nobody, from `git archive HEAD`) | `python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good; problems: [] |
| 6 git status after mutants | `git status --short` | - | empty (no leftover mutation) |
| 7 fail-before b7d7cd18 | 4 delta test files copied into detached worktree of b7d7cd18 | 1 | 18 failed, 54 passed |
| 7 fail-before main | all 22 changed test/fixture files of the diff copied into worktree of main | 1 | 249 failed, 459 passed, 1 deselected, 14 xfailed |
| 8 probes | own script probe.py, 118 text cells, plus keys.py record-walk key rule, on head / b7d7cd18 / main | 0 | probe-table.md |
| 8 cost, 200 kB hostile text | cost.py, 15 shapes, 3 runs each x 3 passes, head and main, run alone (load about 1.0) | 0 | table below |
| 9 timing flake alone | head 3x, main 3x | see below | head: pass, fail, fail; main: fail, fail, fail |

## 7 fail-before details
- b7d7cd18 (files: test_q8b_batch6/7/8/8_lines.py): failed list 7-failbefore-old-failed.txt (18), passed list 7-failbefore-old-passed.txt (54). Of the batch 8 files, 12 tests pass on old code: b8_1, b8_2 (exact cookie name), b8_3, b8_4 (two), b8_10, b8_8, b8_12 (word holding cookie inside), and four tests in test_q8b_batch8_lines.py.
- main: 723 tests collected from the changed files on head; 336 ids do not exist on main's copies of those files (new). Of those new ids, 245 failed on main and 76 are in the passed list (7-new-pass-on-main.txt); the other 15 are in neither list (not examined further). Lists: 7-failbefore-main-failed.txt, 7-failbefore-main-passed.txt, 7-new-ids.txt, 7-new-pass-on-main.txt.

## 8 hostile inputs (own probe; R = made-up value readable, M = masked)
Counts of cells (118): readable on head 28; readable on head and masked on main: 2 (`possession_id=V`, `obsession_id=V`); masked on head and readable on main: 47; readable on b7d7cd18 and masked on head: 26 (apiTokens/accessTokens/refreshTokens/idTokens and lower-case plurals, cookie_name and cookie-policy in text, NTLM/Negotiate/OAuth/Splunk/Hawk scheme values, `Bearer 'V'`, Digest quoted, 4 to 6 joined prefix words, `--cloud-sql-proxy-db-password`, 10 and 11 digits after pass).
Readable on head and masked on b7d7cd18, readable on main (over-mask on b7d7cd18, now readable): wget `--no-cookies`, `--keep-session-cookies`, `--junk-session-cookies`, `--load-cookies`, `--save-cookies`, `--cookies` followed by a URL; `bypass_key`, `compass_code`, `bypass_code` (V readable); `Authorization: Digest` + newline + prose line.
Record-walk key rule (k1b sensitive): `possession_id`, `obsession_id`, `bypass_key`, `compass_code`, `bypass_code`, `maxTokens`, `max_tokens`, `input_tokens`, `audio_tokens` are not credential keys on head; the plural-token, cookie, `xbypass_key`, `bypasspass_key`, `pass2`, `newpass`, digits-suffixed keys are credential keys on head.

## 8 cost on 200 kB texts (seconds, 3 runs x 3 passes; min/median/max)
| shape | head | main | median ratio head/main |
|---|---|---|---|
| A letters only | 0.752/0.835/1.018 | 0.407/0.447/0.464 | 1.87 |
| B 40 letters + pass repeated | 0.782/0.859/0.988 | 0.413/0.470/0.535 | 1.83 |
| C 40 letters + password= value | 0.540/0.581/0.752 | 0.215/0.227/0.303 | 2.56 |
| D digits-letters glue + token: | 0.482/0.491/0.525 | 0.228/0.260/0.329 | 1.89 |
| E --a*39 pass flag | 0.831/0.881/1.113 | 0.250/0.253/0.308 | 3.48 |
| F 'a-' runs flag | 1.085/1.177/1.253 | 0.706/0.786/0.831 | 1.50 |
| G 'a_' runs flag | 0.733/0.809/0.929 | 0.416/0.490/0.614 | 1.65 |
| H digits after key word | 0.763/0.859/1.031 | 0.399/0.410/0.462 | 2.10 |
| I Digest + many spaces | 0.445/0.488/0.594 | 0.251/0.255/0.404 | 1.91 |
| J Digest + newlines | 0.547/0.583/0.824 | 0.254/0.274/0.330 | 2.13 |
| K word + many spaces | 0.561/0.574/0.682 | 0.261/0.298/0.429 | 1.93 |
| L cookie prefixes | 1.003/1.078/1.239 | 0.354/0.367/0.547 | 2.94 |
| M plural tokens glued | 0.866/0.881/1.004 | 0.292/0.306/0.414 | 2.88 |
| N pass words | 0.682/0.697/0.975 | 0.296/0.305/0.425 | 2.29 |
| O hostile hyphen words | 0.710/0.796/0.870 | 0.375/0.400/0.503 | 1.99 |
No call raised an error. Raw: 8-cost.txt.

## 9 timing flake (alone)
head: 1 passed in 0.61s / 1 failed / 1 failed. main: 1 failed / 1 failed / 1 failed. Failure line: "AssertionError: a quadratic function must be flagged". Raw: 9-flake-summary.txt.

## Not checked
The ticket's A1-A5 and X1-X9 acceptance rows were not run as separate commands (the full pytest and mutant runners include the tests that hold them). Windows and Python 3.12 runs: not done. CodeQL, SonarCloud, CodeRabbit: not looked at.
Files in this folder: probe.py, keys.py, cost.py (my scripts), probe-table.md, list files. EGM steps: none run by me (evidence runner).
