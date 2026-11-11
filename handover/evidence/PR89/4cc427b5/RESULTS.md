# EVIDENCE RUNNER record: PR89, round 23, head 4cc427b5bfbf1ff07beb8db03da80c9e59b44fc6 (tag pr89r23)

I ran things and recorded them. No verdict, nothing fixed. Times UTC (IST = UTC + 5:30): started 19:39, last run ended 20:37 UTC (01:09 to 02:07 IST). About 40 minutes of my own work plus about 35 minutes waiting for heavy slots that other sessions held.
Raw logs (not in git): `/home/user/build/evidence-raw/pr89r23-4cc427b5/`. Small copies and my probe scripts are in this folder.

## Failed, not run, odd (read first)
1. **Full suite: 1 failed, 10800 passed, 1 skipped, 28 deselected (481 s), exit 1.** The failure is `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: "connection to server on socket /var/run/postgresql/.s.PGSQL.5432 failed". The cause is MY setup slip: I started my own Postgres without `PGHOST` and `PGPORT` in the server's own environment (the brief says to set them), so the server's `dblink_connect('dbname=postgres')` looked at the default socket. I restarted the server with them set and re-ran that whole file alone through heavy.sh: 253 passed (`rerun-askdata.log`). I did NOT re-run the whole suite (not asked, no summary-line failure). So the full run on the head, as recorded, is 1 failed; the re-run of the file is the only evidence about that test.
2. **Leak probe: 2 of 498 cases SHOWN, the same 2 as at c2f98f49, unchanged.** Password = made-up value equal to a built-in error class name (`TimeoutError`) and the child raising that class (`BUILTIN_CLASS--exc_class_dynamic_plain`, `BUILTIN_CLASS--exc_class_literal`): `first_lines` is `probe mutant\nTimeoutError [expect found] value must be one` (plain form found). A per-case comparison of all 498 records against c2f98f49: no case changed its hits.
3. **Known flaky timing test** `test_the_timing_harness_flags_a_quadratic_stand_in`: FAILED 3 of 3 alone on the head and 3 of 3 alone on origin/main (see item 9). It did not fail in the full suite run.
4. **Fail-before on origin/main:** `tests/test_mutation_runner_keywords.py` (new file, 276 tests collected on the head) cannot even be imported on main's src (`ImportError: cannot import name 'PASS_ENV_ALLOWED'`), so none of its tests ran there. Details in item 7.
5. `uv sync --locked --no-build ...` as written in the common brief was REFUSED ("hadavin-sdk ... editable ... marked as --no-build but has no binary distribution"); I ran `uv sync --locked --all-extras --group test` (no `--no-build`) in all three worktree venvs. Same lock file, same extras.
6. bandit is not in the venv: run with `uv run --with bandit`. Output with `-q -ll` lists only warnings; exit 0 (no summary counts printed at `-q`).
7. Not run: Windows, macOS, perf-marked tests (the ticket names no perf item), mypy (not in this brief; c2f98f49 evidence had it). The Postgres test inputs were my own Postgres 16 (own folder, port 56873), stopped and deleted.
8. Machine was shared: other sessions ran heavy jobs the whole time. The mutant list ran while no other job of mine was running; I killed my own queued (not yet started) fail-before job to keep it so. I cannot say what other sessions ran at the same time.
9. I left no process of mine running. A folder `/tmp/hadavin_mutation_locks_102` was created by my lock probe (as the postgres user) and removed by me; `/tmp/hadavin_mutation_locks_0` is not mine and was there before.

## Results
| # | item | command (under `env -u AWS_ACCESS_KEY_ID ... -u VAULT_SECRET_ID`) | exit | last line |
|---|---|---|---|---|
| 5 | full suite | `heavy.sh uv run pytest -q -p no:cacheprovider -m "not live and not perf" -rfEs` | **1** | 1 failed, 10800 passed, 1 skipped, 28 deselected in 481.29s |
| 5 | the failed file re-run (server env fixed) | `heavy.sh uv run --no-sync pytest tests/demo_askdata/test_validate_harm.py` | 0 | 253 passed in 21.66s |
| 9 | flaky timing test, head, alone, 3 runs | `flock slot1 slot2 slot3 pytest <test>` | 1,1,1 | 1 failed in 0.57s (each) |
| 9 | flaky timing test, origin/main, alone, 3 runs | same, worktree of 2a8c2aac | 1,1,1 | 1 failed in 0.6s (each) |
| 1 | head | `git rev-parse HEAD` | 0 | 4cc427b5bfbf1ff07beb8db03da80c9e59b44fc6, tree clean (checked at start and after runs) |
| 1 | changed files (`origin/main...HEAD`, origin/main = 2a8c2aac) | `git diff --name-only` | 0 | 9 files: CHANGELOG.md, src/hadavin_sdk/testing/mutation.py, tests/conftest.py, tests/fixtures/mutation_manifest.json, tests/mutation_runner_mutants.py, tests/test_mutation_runner.py, tests/test_mutation_runner_keywords.py, tests/test_mutation_runner_meta.py, tools/mutation_runner.py |
| 2 | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 | ruff format | `ruff format --check src tests demos tools` | 0 | 319 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | warnings only (nosec notes) |
| 4 | scan_repo | `python tools/scan_repo.py` | 0 | no findings printed |
| 4 | stage_mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 | gitleaks | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 6 | whole mutant list (the CI file has no step for it; ticket step) | `heavy.sh uv run python tests/mutation_runner_mutants.py` | 0 | **299 of 299 good; problems: []** (19:48:17 to 19:55:39; 295 KILLED rows, 4 CRASH rows, all listed "ok") |
| 6 | pins | my own sha256 of the 4 files in `tests/fixtures/mutation_manifest.json` | | all 4 equal the manifest AND the CHANGELOG list (`pins.txt`) |
| 7 | fail-before on origin/main src | worktree of 2a8c2aac, the 5 changed test files of the diff overlaid (conftest, mutants file, 3 test files; manifest fixture NOT overlaid), `heavy.sh pytest --continue-on-collection-errors` of the 3 mutation-runner test files | 1 | 3 failed, 63 passed, 1 error (the keywords file cannot be imported). Run 1 without `--continue-on-collection-errors` stopped at the collection error (`fb-run1-collection-error.log`). |
| 7b | fail-before on the previous head (extra, same method) | worktree of c2f98f49 (src and tools of round 22), same overlay | 1 | 19 failed, 323 passed in 107 s |
| 8 | address probes (136 cases, `addr.py` of the c2f98f49 evidence) | | 0 | 25 accepted, 111 refused, 0 harness errors, 0 secret in any output, 0 refused-but-child-ran |
| 8 | lock probes (43 cases, root and postgres user) | | 0 | 23 REFUSED, 20 RAN (same as c2f98f49); per-case outcome and file changes identical to c2f98f49 |
| 8 | leak probes (498 calls) | | 0 | 2 SHOWN, 0 worker failures (see item 2 above) |

## Item 7: which tests pass or fail on old src
On origin/main src (2a8c2aac): failed = `test_mutation_runner.py::test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on`, `test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on`, `test_mutation_runner_meta.py::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets`; error: whole `test_mutation_runner_keywords.py` (not importable). The 63 passed are the old and changed tests of the two other files. List: `fb-failed-list.txt`.
On c2f98f49 src (round 22): 19 failed (list `fbprev-failed-list.txt`): 18 in the keywords file (private folder checks under umask 0 for temp, snapshot and settings folders, rebuild checks, the empty-folder helper, bare strings for `tests`, `extra_dirs`, `only`, port range and boundaries, lock folder inside the tree, junction check before any folder, docstring limits) and `test_g_...` in the meta file. Every other new test (the other 258 of the 276 in the keywords file) PASSED on the round 22 src; I do not judge whether that matters.

## Probes: what changed against c2f98f49 (the spec of this run)
- Leak: no case changed (498 of 498 same hits). Still 2 SHOWN (item 2).
- Address: `HOST=localhost` (upper-case key): REFUSED then and now (was ACCEPTED only at 7a2eb4cc). `POSTGRESQL://` scheme: REFUSED then and now. **Port `99999999999`: was ACCEPTED at c2f98f49, now REFUSED** (case "url port huge"); that is the only outcome that changed (26 accepted/110 refused before, 25/111 now). The refusal text of 48 refused cases changed in its wording (same start "its address is not in a shape the runner can check", a different tail); full rows in `address-table.md`.
- Lock: 43 cases, all outcomes and all created/changed/removed entries identical to c2f98f49.

## Files here
RESULTS.md, `*.log`, `*.out`, `*.time`, `*-failed-list.txt`, `pins.txt`, `flaky.txt`, `address-table.md`, `leak-table.md`, `lock-table.md`, `instruments/` (probe and run scripts, paths changed for this head). The JUnit files (`full.xml`, `fb.xml`) are NOT copied: they hold made-up secret-shaped strings. Not pushed.
