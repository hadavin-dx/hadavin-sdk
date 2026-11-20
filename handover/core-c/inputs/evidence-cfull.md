# evidence-cfull: whole-suite evidence, core-c head (evidence runner; raw output only, no judgement)

- Head sha: 9aeedc22fe6ce63c479d9a5653d6526030b6edf8 (origin/cloud/core-c, "lead: laptop job 3 result ..."). Not 7c31dbc97 named in the request file; the head was used as instructed.
- Worktree (kept): C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\lead-cfull (detached).
- Run on a git-less copy under WSL ~/lead-cfull, 3 workers, UTC dates 2026-11-20. uv 0.10.2. Made-up data, no live calls, no push.
- Raw logs: egm\core-complete-2026-11-20\evidence-cfull\raw\

## Results
| Run | Command (+ `-n 3 --no-header -p no:cacheprovider`) | EXIT | Counts | Duration |
|---|---|---|---|---|
| a | `uv run --python 3.13 --all-extras --group test pytest -q -n 3 ...` (a-py313.log) | 1 | 8 failed, 14822 passed, 562 skipped, 53 xfailed, 0 xpassed | 1098.07 s (wall script 1161 s) |
| b | same with `--python 3.12` (b-py312.log) | 1 | 7 failed, 14823 passed, 562 skipped, 53 xfailed, 0 xpassed | 1251.75 s (script 1324 s) |
| c | PG 17 (postgres:17, container hvcfull17, 127.0.0.1 random port, trust auth, no password), py3.13, 19 files that use HADAVIN_TEST_PG_DSN/pg_schema/store_postgres + tests/contracts (c-pg-py313.log) | 0 | 623 passed, 341 skipped, 2 xfailed, 0 failed | 68.11 s |
| d1 | `ruff check src tests` | 0 | All checks passed | |
| d2 | `ruff format --check src tests tools` | 0 | 360 files already formatted | |
| d3 | `uvx bandit -q -r src -ll` | 0 | no findings printed; only warnings (nosec at src/hadavin_sdk/tools.py:389 with no failed test; comment "test" names) | |
| d4 | gitleaks 8.21.2 is installed in WSL (`/home/rakesh/bin/gitleaks`); `uvx gitleaks` not used | | see below | |

Suite has no postgres marker; markers are only `live` and `perf`. The perf tests ran in a and b (not deselected). Run c's skips (54 reported with -rs): 20 "migrate() has no reset_role", 19 "Store.reserve_spend missing", 12 "no spend_reservations row in migrate.GRANTS", 2 "install the PostgreSQL client or set PSQL" (no psql client in WSL), 1 Stubber.

## Failures (run a, python 3.13; first error line)
1. tests/test_ci_gitleaks_scope.py::test_the_gitleaks_config_has_only_narrow_path_allowlists : CalledProcessError `git ls-files` exit 128 (copy has no .git).
2. tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked : AssertionError: `handover/BRIEF-PREAMBLE.md: 'Port.io'`.
3. tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse : `hadavin_sdk.guard.runmap.InputTooLarge`, then `AssertionError: fdfa; assert 'fdfa' in {'devanagari lines', 'e-acute lines'}`.
4. tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[dots-redact_text] : 3.61 s, assert < 3.0.
5. tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[hex and dashes-redact] : 3.41 s, assert < 3.0.
6. tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[hex and dashes-redact_text] : 3.42 s, assert < 3.0.
7. tests/test_redact_settle_loop.py::test_the_work_of_the_scan_is_bounded_a_hostile_text_is_refused_not_walked_to_the_end : `assert (694.9994882 - 691.1039135) < 3.0` (thread_time).
8. tests/test_repo_rules.py::test_licences_are_proprietary : CalledProcessError `git ls-files` exit 128.

## Failures (run b, python 3.12)
Same ids as a for 1, 2, 3, 5 ("hex and dashes-redact" 3.57 s), 7 ((738.747569 - 735.3255078) < 3.0), 8; NOT failing on 3.12: the two other glued_patterns cases (4, 6). Extra on 3.12 only:
9. tests/test_textnorm_mixed_script_micro.py::test_a_code_point_newer_than_unicode_15_1_0_counts_as_neutral : `AssertionError: assert '15.0.0' >= '15.1.0'` where '15.0.0' = unicodedata.unidata_version (Python 3.12 ships Unicode 15.0.0).

## Extra isolation reruns (same copy, `-n 1`; raw e-rerun-isolated-perf.log, f-rerun-git-tests.log)
- e: test_redact_fold_budget (the one id) + test_redact_glued_rest.py + test_redact_settle_loop.py + test_textnorm_mixed_script_micro.py, py3.13: 1 failed, 584 passed, 43 xfailed, 213 s. The failing id is test_redact_fold_budget::test_hostile_1 again (reproduces without load); the glued-linear and settle-loop ids passed.
- f: after `git init && git add -A` in the throwaway copy, py3.13: test_ci_gitleaks_scope.py, test_no_reference_material.py, test_repo_rules.py::test_licences_are_proprietary: 1 failed, 91 passed. Failing: test_no_vendor_brand_string_is_tracked (`handover/BRIEF-PREAMBLE.md: 'Port.io'`, reproduces with git). The two git ls-files failures pass with a git repo.

## gitleaks (d4)
Run `gitleaks dir . --redact -c .gitleaks.toml` on the git-less copy (includes untracked `tests/__pycache__`, so not the CI scan mode): 46 findings, gitleaks exit 1 (d4b, d4c logs). By path/rule: tests/__pycache__ private-key 10 + aws-access-token 2; handover/core-c generic-api-key 6; tests/fixtures generic-api-key 6 + private-key 3; tests/test_textnorm_differential.py generic-api-key 4; tests/warden_port curl-auth-user 4, generic-api-key 4, slack-app-token 4, slack-webhook-url 2; tests/test_text_parts_together.py generic-api-key 1. Values not printed. The CI-equivalent scan (git history/tracked files only) was NOT run.

## Not run
CI-mode gitleaks (git scan); whole suite with HADAVIN_TEST_PG_DSN set (only the 19 PG files + tests/contracts); vault-service tests; mutation scripts (job 2); psql-client dependent tests (no psql in WSL).

## Cleanup
Container hvcfull17 removed (`docker ps -a --filter name=hvcfull` empty); WSL copy ~/lead-cfull removed; no leftover run processes; other containers untouched; worktree lead-cfull kept clean. Helper scripts are in _local\scratch\wt\cfull-scripts.
