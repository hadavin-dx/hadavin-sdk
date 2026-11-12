# EVIDENCE RUNNER results: P3a-2 batch 7 (round 17), head aac26d60

Head `aac26d60c18c8ea50071918f2eba540aa5535e7c` (equals `origin/wip/cloud-p3a2-b7`), detached worktree; previous reviewed head `140a1268`. Raw logs: `/home/user/build/evidence-raw/P3a2-7-aac26d60/`. Times UTC (IST = UTC + 5:30): runs 13:46 to 14:21 UTC (19:16 to 19:51 IST).

How this file came about (plain statement): the first runner finished every run but never wrote this file. This file was written afterwards by a second runner that only READ the saved logs, exit-code files and start/end time files. It did not re-run any test. I record only; nothing was fixed or judged.

## FAILED or NOT RUN (read first)

1. **Nothing failed in the runs that count.** Every saved exit code is 0 except the fail-before run (item 3 below), which is expected to fail: it runs the new tests against the old code (its shell exit code 123 comes from `xargs`, which returns 123 when the pytest it launched exited 1; pytest's own result line is `7 failed, 25 passed in 1.42s`).
2. **Not run (impossible now, as the brief says):** the PostgreSQL 17 tests (3 skipped by name below), Python 3.12, semgrep, zizmor, trivy, pip-audit.
3. **The timing test was deselected, not run.** The full run used `-m "not live and not perf"` (29 deselected). The brief said not to touch the timing test; no run of it exists in these logs, so its result is unknown.
4. **Four tests skipped in the full run (by name):**
   - `tests/contracts/test_llm.py:95` "Stubber refuses a malformed Converse shape before the kind sees it"
   - `tests/test_migration_verify_pg.py:848`, `:901`, `:1084`: "UNRUN: PostgreSQL 17 only (`transaction_timeout` does not exist below 17)"
5. **`uv sync --locked --no-build` was not used** (it fails here); `uv sync` without `--no-build` was used, as the brief allows (`sync.log`).
6. **Not checked by me:** the 21-line `handover/evidence/P3a-2/b7/passes-on-old-code.md` (the brief asks whether it names a reason per test): I read only its first lines (it gives a reason or killing mutant per test); I did not compare it line by line with the 25 tests that passed on old code. Also not checked: whether the 2 test ids removed from head compared with the old tree (`ids-removed.txt`, below) are covered elsewhere; the review report `goldfish_review_report-r17.md`; builder notes file (none exists for batch 7 under `/home/user/build/*P3a2*b7*notes*`; the claims below come from the evidence brief `/home/user/build/EV-P3a2-7-brief.md`, which quotes the builder).
7. **Two logs show a slip risk, stated so a reader can decide:** the fail-before run copied the changed tests into the old-code tree `wt-old` and put `wt-old/src` first on the import path (`fb-import.txt` prints `.../wt-old/src/hadavin_sdk/__init__.py`, so the old code was really used). The second fail-before run (`fb-k.log`, a name filter) shows `32 passed, 1541 deselected`, rc 0: it selected tests that all pass on old code; it is not a second count of failing tests.

## Builder claim versus measured

| Builder claim (from the brief) | Measured |
|---|---|
| full pytest: 1 failed (dblink-connect, fixed socket path), 12438 passed, 4 skipped | **0 failed, 12439 passed, 4 skipped, 29 deselected in 759.80 s (0:12:39), exit 0**, own Postgres 16 on 127.0.0.1:56871. The dblink test passed here (own server) |
| migrate mutants batches 129, 88, 98, 97 all killed | 129 of 129, 88 of 88, 98 of 98, 97 of 97 killed; `not killed: []` in each |
| `migration_numbers_mutants` 40 of 40, rc 0 | `40 of 40 good; problems: []`, exit 0 |
| `stage_mutants` 37, rc 0 | `37 of 37 good; problems: []`, exit 0 |
| fail-before on 140a1268, four changed test files: 7 failed, 37 passed | the 32 NEW test ids only (`ids-new.txt`, 32 lines): 7 failed, 25 passed. Different test set, so the totals differ; the 7 failures are the same classes the builder names (sign-in refusal 2, address without host or user 2, close hides first error 1, sign-in at start 1, unreachable address 1) |
| tests that pass on old code are listed with a reason | 25 passed on old code: 5 in `test_migration_matrix.py`, 18 in `test_migration_rules.py`, 2 in `test_migration_verify_pg.py` (see item 6) |
| counts 580 cells, 30 empty, 550 built, 32 step-0, 518, 525, 25, 871 | printed by `tests/test_migration_matrix.py::test_the_matrix_has_exactly_the_planned_cells` (`1 passed in 0.59s`): 580 = 29 x 10 x 2; empty by logic 30; generated 550; ended at step 0 by the text rules 32; reach the data checks 518; expected refused 525; expected to return 25; total cells and controls 871. All eight equal the claim |

The same matrix log also prints these lines (copied, not judged): "NOT BUILT, E21 under variant (C)" and "NOT BUILT, E19-E21 under variants (T) and (U)" (no trusted-language extension on this server), and "DEVIATION FROM THE TICKET, E28-schema, owner outside the family ... ACCEPTED while the switch is OFF ... the choice is the lead's question q-p3a2-o8-schema-owner".

## Table

| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1 | changed files | `diff-names.txt` | n/a | 42 paths (src 9, tests 32, `ci.yml`, `CHANGELOG.md`, `pyproject.toml`) |
| 2 | ruff check | `uv run ruff check` | 0 | `All checks passed!` |
| 3 | ruff format | `ruff format --check` | 0 | `334 files already formatted` |
| 4 | bandit | `uv run --with bandit bandit -ll` | 0 | only warnings (`nosec` B608 at `demos/ask-your-data/db/lumen.py:723`, `nosec` B102 at `src/hadavin_sdk/tools.py:389`, both with no finding) |
| 5 | repo scan | `tools/scan_repo.py` | 0 | no output |
| 6 | gitleaks, `origin/main..HEAD` | `gitleaks git` | 0 | `76 commits scanned ... no leaks found` |
| 7 | full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 0 | `12439 passed, 4 skipped, 29 deselected in 759.80s (0:12:39)` (13:47:03 to 14:19:47 UTC) |
| 8 | matrix counts | `pytest -s ...test_the_matrix_has_exactly_the_planned_cells` | 0 | `1 passed in 0.59s` |
| 9 | migrate mutants batch 1 | `tests/migrate_mutants.py` (ids of batch 1) | 0 | `129 of 129 killed` (13:48 to 14:01) |
| 10 | migrate mutants batch 2 | same, batch 2 | 0 | `88 of 88 killed` (14:01 to 14:12) |
| 11 | migrate mutants batch 3 | same, batch 3 | 0 | `98 of 98 killed` (14:12 to 14:17) |
| 12 | migrate mutants batch 4 | same, batch 4 | 0 | `97 of 97 killed` (14:17 to 14:20) |
| 13 | migration numbers mutants | `tests/migration_numbers_mutants.py` | 0 | `40 of 40 good; problems: []` |
| 14 | stage mutants (CI command) | `tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 15 | fail-before, 32 new ids on old src (140a1268) | `PYTHONPATH=wt-old/src pytest ... <ids>` via xargs | 123 (pytest 1) | `7 failed, 25 passed in 1.42s` |
| 16 | filter run on old src (name filter) | `pytest -k "c10_every_effect or ... wording_check"` | 0 | `32 passed, 1541 deselected in 6.93s` |
| 17 | old-code import check | `python -c "import hadavin_sdk; print(file)"` | 0 | path under `wt-old/src` |

Fail-before test ids that FAILED on old code (`fb-new.log`):
- `tests/test_migration_verify.py::test_a_close_that_fails_after_a_failed_setup_statement_does_not_hide_the_first_error`
- `...::test_a_failed_cloud_sign_in_is_a_plain_refusal_that_prints_none_of_the_sdks_words[no-credentials]` and `[refused-request]`
- `...::test_an_iam_dsn_without_a_host_or_a_user_is_the_same_plain_refusal` (2 cases)
- `tests/test_migration_verify_pg.py::test_a_failed_cloud_sign_in_at_the_start_is_refused_with_exit_2_and_keeps_nothing`
- `...::test_an_address_that_cannot_be_reached_is_refused_with_exit_2_with_a_real_driver_error`

Test ids: head has 1573, old tree 1543, new 32, removed 2 (`test_c13_the_function_of_the_map_moved_is_refused_by_the_trigger_rule_before_any_right_is_judged` and `test_every_empty_pair_has_a_probe_and_its_reason_carries_the_measured_text`; the matrix log shows the replacement `..._state_text_and_version_of_it` passing).

## Environment

Three own PostgreSQL 16 servers (ports 56871 for the full run, 56872 and 56873 for the mutant and count runs), each with a data folder under `/home/user/build/EV-P3a2-7-aac26d60/`. Own venv. Worktrees `wt` (head), `wt-mut` (head), `wt-old` and `wt-old2` (140a1268). No cloud, model or token variables in the environment file. No secret-shaped value is quoted here.

Cleanup by the second runner: stopped the three servers (their process ids and data folders matched this runner's folder), removed worktrees `wt`, `wt-mut`, `wt-old2` and the temporary run scripts. Worktree `wt-old` was NOT removed: it holds the copied test files (modified and untracked), and `git worktree remove` without force refuses; it stays for the lead to remove. The data folders `pg`, `pg2`, `pg3` and the venv are left on disk.
