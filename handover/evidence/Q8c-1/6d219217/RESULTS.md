# EVIDENCE RUNNER results: Q8c-1 batch 12, head 6d219217fdc55593a0df61018cd7807232d9ee7d
Run 2026-11-12 (UTC). Recorded only, no judgement. Raw logs: /home/user/build/evidence-raw/Q8c1b12-6d219217/

## Failed or deviating first
1. Full pytest: 1 failed, 10950 passed, 13 skipped, 28 deselected (rc 1). The one failure: tests/demo_askdata/test_validate_harm.py dblink-connect. Cause: my first Postgres was started without PGHOST/PGPORT in the SERVER's environment (dblink_connect used the default socket). After restarting the server with them set, tests/demo_askdata/test_validate_harm.py alone: 253 passed. I did not rerun the whole suite after the restart.
2. Fail-before on e4f1b2a4: 18 failed, 401 passed (builder said 17 failed, 401 passed; GATES.md says one more test failed in a separate late run, which would make 18; I did not check the builder's list).
3. `uv sync --locked --no-build` (as written in the brief and ci.yml) failed here (rc 2: the editable project has no binary distribution); I used `uv sync --locked` without --no-build (rc 0).
4. `git diff --stat origin/main..HEAD -- src` is NOT empty: 3 files, 536 insertions (src/hadavin_sdk/actions/secrets_vault.py, audit/signer_vault.py, sources/kubernetes.py). Against e4f1b2a4 the src diff is empty. Origin/main and merge-base are the same commit (2a8c2aac). I did not compare these files to any grant list.
5. Time: waited about 15 min in the heavy.sh queue for the full suite; policy_mutants runs also queued.

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| head | git rev-parse HEAD | - | 6d219217fdc55593a0df61018cd7807232d9ee7d, tree clean |
| changed files | git diff --name-only origin/main...HEAD | - | 80 files |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 326 files already formatted |
| bandit | bandit -q -r src demos tools -ll | 0 | only nosec warning (B102, src/hadavin_sdk/tools.py:389) |
| scan_repo | python tools/scan_repo.py | 0 | (empty) |
| policy page | python tools/policy_page.py --check | 0 | (empty) |
| gitleaks | git --redact ... origin/main..HEAD | 0 | no leaks found |
| stage mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| policy mutants, real clock | python tests/policy_mutants.py | 0 | 235 of 235 good; problems: []; weak 0 of 235 |
| policy mutants, 2026-12-11 | --day 2026-12-11 | 0 | 235 of 235 good; problems: [] |
| policy mutants, 2026-12-12 | --day 2026-12-12 | 0 | 234 of 234 good; B12 not run at that day (by design, as printed) |
| notes check vs e4f1b2a4 | tools/notes_lines_check.py --auto e4f1b2a4 | 0 | no output besides a uv warning |
| notes check vs origin/main | --auto origin/main | 0 | no output besides a uv warning |
| notes plant | new test with no row, committed on a detached copy, --auto <head> --head <plant> | 1 | reported: "the test test_plant_no_notes_row_zz is new or changed and has no row of its own in the notes" |
| full pytest | pytest -p no:cacheprovider -q -m "not live and not perf" -rs via heavy.sh, own Postgres 16.15 | 1 | 1 failed, 10950 passed, 13 skipped, 28 deselected in 271.94s |
| failing test rerun | test_validate_harm.py with PGHOST/PGPORT in server env | 0 | 253 passed |
| fail-before e4f1b2a4 | 4 test files + policy_mutants.py (5 changed files) copied to detached e4f1b2a4 | 1 | 18 failed, 401 passed |
| fail-before origin/main (extra) | same files on origin/main | 2 | 4 errors during collection |

Skips (13): tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape); tests/test_policy_engine.py lines 255, 263, 271, 285, 297, 310, 373, 386 (x2), 401, 413, 425 (needs a real Vault server, HADAVIN_TEST_VAULT_ADDR not set; 12 skips).

Not run: perf tests (ticket names none); the flaky timing test (not asked in this brief); no real Vault server.
Cleaned up: my Postgres stopped, its folder, venv and worktree removed. Nothing committed or pushed.
