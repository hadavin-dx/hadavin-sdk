# Q8b evidence, head 999ed05b541171b9f9fd1c74b74fab7a5e6d9a3c (EVIDENCE RUNNER: recorded, not judged)
Run 2026-11-12 UTC. Worktree detached at the head (`git rev-parse HEAD` = 999ed05b541171b9f9fd1c74b74fab7a5e6d9a3c, tree clean before and after). origin/main = 2a8c2aac. Raw logs: /home/user/build/evidence-raw/Q8b-999ed05b/ (outside the repo).

## Not run, or run differently (first)
- Venv: `uv sync --locked --no-build` FAILED (rc 2: editable project has no binary distribution); I ran `uv sync --locked --all-extras --group test` without `--no-build` (rc 0). Everything below used that venv.
- Not run: perf tests (`-m perf`; the ticket names no perf item), CI steps semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit, Windows runs, the Vault service.
- Hostile probe covers only the two public TEXT entry points (`guard.redact.redact(text).text` and `guard.runmap.redact_text(text, {})`). Not probed: the record walk (`k1b.redaction.redact_bundle`), cards (`approvals`). Both entry points gave the same answer in all 240 cases.
- Fail-before on origin/main: the delta test files alone cannot be collected there (import of `tests.test_q8b_card_text` etc. missing); I also copied every test file of the branch diff onto main (second run below).
- The three "origin/main" timing runs used a worktree on which I had already copied branch test files; `tests/test_migration_numbers.py` was not one of them.
- Non-root mutation run: run as user `nobody` (`runuser -u nobody -- env -C wt TMPDIR=<own dir> HOME=<own dir> venv/bin/python tests/mutation_runner_mutants.py`) through heavy.sh.
- heavy.sh queue wait: full pytest about 3 min, non-root mutation run about 12 min (other agents held the slots).

## Failures recorded
- Known flaky timing test: FAILED 6 of 6 (head 3 of 3, origin/main 3 of 3), each in about 0.6 s, assertion "a quadratic function must be flagged". Not flaky-pass in this run.
- Nothing else failed. No mutant survived anywhere (no survivor names to list).

## Table
| item | command | exit | last line |
|---|---|---|---|
| diff names | git diff --name-only origin/main...HEAD | 0 | 31 files, see diff-names.txt |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 329 files already formatted |
| bandit | bandit -q -r src demos tools -ll | 0 | only nosec warnings (tools.py:389 B102), no findings |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| stage_mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| gitleaks | gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD | 0 | no leaks found |
| full pytest | heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs (own Postgres 16, port 56381, HADAVIN_REQUIRE_PINNED_UNIDATA=1) | 0 (pytest's own) | 10766 passed, 1 skipped, 29 deselected, 16 xfailed in 359.09s; the skip: tests/contracts/test_llm.py:95 Stubber refuses a malformed Converse shape |
| q8b mutants | heavy.sh python tests/q8b_mutants.py | 0 | 75 of 75 good; problems: []; 0 survivors |
| mutation_runner_mutants, root | heavy.sh python tests/mutation_runner_mutants.py | 0 | 64 of 64 good; problems: [] |
| mutation_runner_mutants, non-root (nobody) | see above | 0 | 64 of 64 good; problems: [] |
| flaky timing test x3 head | pytest ...::test_the_timing_harness_flags_a_quadratic_stand_in | 1,1,1 | 1 failed in ~0.6s each |
| flaky timing test x3 origin/main | same | 1,1,1 | 1 failed in ~0.6s each |

## Fail-before (delta tests copied onto older src)
Delta files (git diff --name-only 4091f8b1 HEAD -- tests): mutation_runner_mutants.py, q8b_helpers.py, q8b_key_corpus.py, q8b_mutants.py, q8b_older_rule.py, test_mutation_runner.py, test_mutation_runner_meta.py, test_q8b_batch2.py, test_q8b_batch3.py, test_q8b_batch4.py.
- On src of 4091f8b1 (5 test_ files: batch2, batch3, batch4, test_mutation_runner, test_mutation_runner_meta): 23 failed, 113 passed. Failed by file: test_q8b_batch2 1, test_q8b_batch3 5, test_q8b_batch4 17 (rest of the 23: see failbefore-prev.log; test_mutation_runner/meta names in /home/user/build/evidence-raw/Q8b-999ed05b/fb-prev-failed.txt). The 8 batch4 tests that pass on 4091f8b1: j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value, j3_the_stop_is_the_same_on_every_path, j4_names_that_are_no_credential_stay_readable, j4_the_scan_finds_a_list_written_one_entry_per_line_and_a_plain_regex_string, j5_a_secret_split_by_a_tag_is_masked_on_a_card, j5_the_card_test_reads_the_one_list_of_secret_kinds, j6_the_comma_pin_matches_the_code, j6_the_whole_line_after_a_bearer_key_is_masked.
- On src of origin/main, delta files only: collection errors (2 errors, ModuleNotFoundError tests.test_q8b_card_text), rc 2, nothing ran.
- On src of origin/main, all branch test files (tests/test_q8b_*, test_mutation_runner*, test_k5_producers, test_k5_round11 plus helpers): 190 failed, 188 passed, 14 xfailed. Passing on old code by file: batch2 3, batch3 5, batch4 8, card_text 3, credential_keys 12, glued_and_whole_values 4, random 1 (full pass list in /home/user/build/evidence-raw/Q8b-999ed05b/fb-main-passed-names.txt). Failing: batch2 16, batch3 20, batch4 17, card_text 37, credential_keys 68, glued 22, random 6, plus mutation_runner tests.

## Hostile-input probe (made-up value built from parts, different per case; R = made-up value still readable in the output, m = masked; "main / head")
Entry points: guard.redact.redact and guard.runmap.redact_text, identical results. Styles: `KEY=v`, `KEY: v`, `"KEY": "v"` (text form), `--KEY v`.
On the head, readable rows: key newpass, oldpass, postgresauth, authorization, each in the `--KEY v` style only (counted per entry point and style: main readable 94 of 168 key cases, head readable 8 of 168). Benign words: readable 42 of 72 on both main and head; the other 30 are masked on both (bypass, compass, oauth, obsession in eq/colon/json; passed, passenger, sessions in json).

| group | key | `KEY=v` main / head | `KEY: v` main / head | `"KEY": "v"` main / head | `--KEY v` main / head |
|---|---|---|---|---|---|
| key | passcode | R / m | R / m | m / m | R / m |
| key | passkey | R / m | R / m | m / m | R / m |
| key | sessionkey | R / m | R / m | m / m | R / m |
| key | session_key | R / m | R / m | m / m | R / m |
| key | session_value | R / m | R / m | m / m | R / m |
| key | pass_code | R / m | R / m | m / m | R / m |
| key | pass_value | R / m | R / m | m / m | R / m |
| key | auth_value | R / m | R / m | R / m | R / m |
| key | bearer_value | R / m | R / m | R / m | R / m |
| key | key-data | m / m | m / m | m / m | R / m |
| key | cert-data | m / m | m / m | m / m | R / m |
| key | certificate-data | m / m | m / m | m / m | R / m |
| key | session_cookie | m / m | m / m | m / m | R / m |
| key | newpass | m / m | m / m | m / m | R / R |
| key | oldpass | m / m | m / m | m / m | R / R |
| key | postgresauth | m / m | m / m | m / m | R / R |
| key | signing_key | R / m | R / m | R / m | R / m |
| key | encryption_key | R / m | R / m | R / m | R / m |
| key | authorization | m / m | m / m | m / m | R / R |
| key | client_secret | m / m | m / m | m / m | R / m |
| key | api_key | m / m | m / m | m / m | R / m |
| benign | bypass | m / m | m / m | m / m | R / R |
| benign | compass | m / m | m / m | m / m | R / R |
| benign | oauth | m / m | m / m | m / m | R / R |
| benign | obsession | m / m | m / m | m / m | R / R |
| benign | author | R / R | R / R | R / R | R / R |
| benign | authority | R / R | R / R | R / R | R / R |
| benign | passed | R / R | R / R | m / m | R / R |
| benign | passenger | R / R | R / R | m / m | R / R |
| benign | sessions | R / R | R / R | m / m | R / R |
