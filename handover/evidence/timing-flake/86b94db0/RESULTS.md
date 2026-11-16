# Evidence: timing flake batch 3, head 86b94db0e2a6572d2dfd40efcc29ce01d7a0456d (EVIDENCE RUNNER, no judgement; saved condensed by the lead)
Clean worktree at the sha, own Postgres 16 UTF8 (PGHOST/PGPORT in the server env). Raw logs outside the repo: /home/user/build/evidence-raw/timing-b3/.

## Not run / read carefully (first)
- Load test did NOT reproduce a flake at the OLD head a3c94be5 either (0 of 10 failures under 4 busy loops plus the fixture's own load), so the busy-load contrast shows no difference; the evidence that the harness is sound is the mutants and fail-before, not a red-to-green flip.
- Machine shared with other agents (load average up to about 9).
- Bandit last line is a nosec warning (B102, tools.py:389), not a finding.

## Results
| Item | Exit / result |
|---|---|
| Full pytest -m "not live and not perf" | 0: 10645 passed, 1 skipped, 30 deselected in 254.20s (skip: tests/contracts/test_llm.py:95) |
| Perf group (timing_fixture, k5_perf, migration_numbers, -m perf) | 0: 12 passed, 159 deselected in 51.02s (builder measured 57.97s; the group is about 51 to 58 s, not 30 s) |
| Busy-load, new head, flag test and pass test | 0 failures of 30 each |
| Busy-load, old head a3c94be5 | 0 failures of 10 each |
| Six hand mutants (best_of to median, PER_SIZE 3 to 30, no block loop, same text every call, no handshake, floor MIN_SMALL_S 4 ms) | all 6 KILLED |
| tests/migration_numbers_mutants.py (whole table) | 0: 37 of 37 good; problems: [] |
| ruff check, ruff format --check, bandit -ll, gitleaks origin/main..HEAD, scan_repo, check-no-handover-files | all exit 0 |
| Fail-before (new timing tests with old timing.py) | 1: 13 failed, 17 passed |
| Timing files alone x5 | 0 failures of 5 |

## Lead note
After this run the lead pushed 21893cbc (tests only): the last E731 lambda at tests/test_migration_numbers.py:849 is a def, the perf figure (51 s and 58 s) is written into tests/fixtures/timing.py, two comments reworded. Checked: ruff check and format on tests, 163 passed in the two edited test files (rc 0), gitleaks and handover-files check exit 0. The full suite was not rerun on 21893cbc (comment, docstring and one def change only).
