# Evidence: Q8c-1 batch 15, head ccb630218c4e12ee26be6a8ab52cc0ee8e721362 (EVIDENCE RUNNER, no judgement)

Head checked out in a clean detached worktree (`git rev-parse HEAD` equals the sha above, `git status` clean).
Own Postgres 16.15 on a private port. Raw logs: `/home/user/build/evidence-raw/Q8c1b15-ccb63021/` (outside the repo).

## Not run / deviations (first)
- 12 tests skipped in the full run need a real Vault server (`HADAVIN_TEST_VAULT_ADDR` not set here; CI sets it). Not run here. One more skip: `tests/contracts/test_llm.py:95` (Stubber).
- `uv sync --locked --no-build` fails (`hadavin-sdk` editable has no binary distribution); I used `uv sync --locked` without `--no-build` (exit 0).
- policy_mutants was run with the real clock only. The `--day 2026-12-11/12-12/12-13` runs and the "B15 set" run were NOT run (brief item 2 asks real clock only).
- Postgres cannot run as root here: I started it as the `postgres` OS user from my own folder.
- Fail-before: the first attempt used the head `src` by mistake (venv editable install points at the head); I stopped it and reran with `PYTHONPATH` = old `src`. Only the rerun is recorded.

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own PG) | 0 | `11000 passed, 13 skipped, 28 deselected in 1078.35s` |
| 2a Stage mutants | `python tests/stage_mutants.py` (heavy.sh) | 0 | `37 of 37 good; problems: []` |
| 2b Policy mutants (real clock) | `python tests/policy_mutants.py` (heavy.sh) | 0 | `350 of 350 good; problems: []`; weak-first-line count 0; every row `ok  KILLED` |
| 3 Fail-before | 9 changed test files + `mutation_manifest.json` + `policy_mutants.py` of the head copied into a detached worktree of a50d5b2e, old `src` | 1 | `41 failed, 574 passed` (see below) |
| 4a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b ruff format | `ruff format --check src tests demos tools` | 0 | `327 files already formatted` |
| 4c bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only a "nosec but no failed test" warning for `src/hadavin_sdk/tools.py:389` |
| 4d scan_repo | `python tools/scan_repo.py` | 0 | no output problems |
| 4e policy page | `python tools/policy_page.py --check` | 0 | no problems printed |
| 4f gitleaks | `gitleaks git --redact --log-opts origin/main..HEAD` | 0 | `no leaks found` |
| 5 Notes check | `python tools/notes_lines_check.py --auto a50d5b2e --head HEAD` | 0 | no problem lines |

## Fail-before detail (item 3)
Added test functions in the delta a50d5b2e..HEAD: 17 (list from `git diff a50d5b2e HEAD`). On old code (a50d5b2e src):
- 13 of the 17 FAIL: `test_k1b_cli.py` 1, `test_mutation_runner.py` 1, `test_notes_lines_check.py` 7 (all 7), `test_policy_guard.py` 4.
- 4 of the 17 PASS on old code: the four tests of `tests/test_policy_renewal_copy.py` (`..full_renewal_plant..`, `..kinds_alone_plant..`, `..names_and_claims_alone_plant..`, `..notes_check_of_a_renewed_copy..`).
- 28 further, older or parametrized tests in the changed files also fail on old code (the file `failbefore-failed-on-old-code.txt` lists all 41 failed ids; note: three plants tests in `test_policy_changelog.py`, `test_mutation_runner.py::test_the_manifest_pins_the_files_a_demo_copies` and many `test_policy_guard.py` plants/parametrized ids are among them).
- Lines `35 failed, 424 passed` in the raw log come from a test that runs pytest as a child process; the outer total is `41 failed, 574 passed`.

## Notes-check hostile probes (item 6)
Method: throwaway detached worktree (never on the branch, nothing pushed); commit 1 adds a test with a row, commit 2 changes the thing the test reads and replaces the notes file with a table that has no row for the test; `--auto <commit1> --head <commit2>`. Control: same, with a valid row added.
| Probe | Plant (no row) | Control (row added) |
|---|---|---|
| walrus `W = (X := n)`, test reads `X` | exit 1, `test_p is new or changed and has no row` | exit 0 |
| `@pytest.mark.usefixtures("fx")`, `fx` return value changed | exit 1, same message | exit 0 |
| `from tests.probe_helper_s import *`, helper constant changed | exit 1, same message | exit 0 |
| `importlib.import_module(name)` with a name held in a variable, helper changed | exit 1, same message | exit 0 |
Raw: `notes-check-probes.txt`. Each planted change was listed by the check; I did not test further variants (e.g. `getfixturevalue`, `pytest_plugins`, `-p` in `addopts`, unittest `setUp`).
