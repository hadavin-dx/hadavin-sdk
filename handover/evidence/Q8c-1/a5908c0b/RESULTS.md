# Evidence: Q8c-1 batch 17, head a5908c0b3404ee7159bc1f9076dff914c3866de6 (EVIDENCE RUNNER, records only, no judgement)

Clean detached worktree `/home/user/build/ER-q8c1b17` (`git rev-parse HEAD` equals the sha; `git status` clean). Own venv, own Postgres 16 on port 54917 (started as the `postgres` OS user, UTF8, `PGHOST`/`PGPORT` set in the server environment, `HADAVIN_TEST_PG_DSN` set). AWS_*, ANTHROPIC_*, GH_TOKEN, GITHUB_TOKEN unset. Raw logs outside the repo: `/home/user/build/evidence-raw/q8c1b17-runner/`.

## Not run / deviations (first)
- `tools/check-no-handover-files.sh` (or any file of that name) does not exist in this tree (`git ls-files | grep -i check-no-handover` is empty), so "the lane is refused by it" was NOT checked. The lane carries 62 commits over origin/main and 138 files under `handover/`.
- 13 skips in the full run, grouped by reason: 12 need a real Vault server (`HADAVIN_TEST_VAULT_ADDR` not set; all in `tests/test_policy_engine.py`: lines 255, 263, 271, 285, 297, 310, 373, 386 (2 tests), 401, 413, 425); 1 is `tests/contracts/test_llm.py:95` (Stubber refuses a malformed Converse shape). Those 12 were not run here (CI sets the Vault).
- The policy-mutant run was the DELTA run only (the full 466 was not repeated, per the once-per-PR rule): 25 B15 rows + 60 random rows (seed 17017, selection in `sel.json`/`sel.txt`) = 85 rows. Real clock only (day 2026-11-13); no `--day` runs of other days besides the ones the runner makes itself.
- The brief says the batch 17 code change is small. The range 37cd5157..a5908c0b is NOT small: it includes the whole commit 7010aa44 ("batch 17", 9 files, 2575 insertions, 111 deletions in tests/tools) and the fix commit 9c2c0742 (4 files). The fail-before below covers the full range 37cd5157..HEAD as asked.
- Plants (5 tests): see the plants row below (started when a slot looked free; status given there).
- Hostile-input probes: my first probe set used an empty text literal (`''`) for two cases (`empty_string_literal`, `loader_handed_on_as_value`); these are readable names (they name no module), so the check listing nothing is the expected answer, not a finding. I added three more probes with really unreadable names. The "control" column of the probe log is not meaningful for the unreadable cases (every test is then listed, and my control wrote one row only); only the plant exit is the answer.

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own PG) | 0 | `11032 passed, 13 skipped, 28 deselected in 1303.83s (0:21:43)` (wall 1307s including the slot wait) |
| 2a Policy mutants, delta (25 B15 rows + 60 sampled, seed 17017) | `heavy.sh python tests/policy_mutants.py <85 names>` | 0 | `85 of 85 good; problems: []`; 85 `ok  KILLED`, 0 `BAD`; weak-first-line `0 of 466`; changed sibling row `B15 notes check does not follow the text a run-time import name starts with` = `ok  KILLED` by `test_a_module_imported_by_a_name_built_at_run_time_lists_every_test_that_could_reach_it`; wall 641s incl. queue |
| 2b Search texts | `python tests/policy_mutants.py --snippets` | 0 | `all 466 search texts are found` |
| 3 Mutation runner mutants | `heavy.sh python tests/mutation_runner_mutants.py` | 0 | `67 of 67 good; problems: []` |
| 4a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b ruff format | `ruff format --check src tests demos tools` | 0 | `327 files already formatted` |
| 4c bandit | `bandit -q -r src tools -ll` | 0 | only warnings: `nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389` and `Test in comment: bytes is not a test name` |
| 4d policy page | `python tools/policy_page.py --check` | 0 | no output |
| 4e scan_repo | `python tools/scan_repo.py` | 0 | no problems printed |
| 4f gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts refs/remotes/origin/main..HEAD` | 0 | `62 commits scanned ... no leaks found` (covers all 62 commits of the lane) |
| 5 Fail-before | the changed test files (`test_mutation_runner.py`, `test_mutation_runner_meta.py`, `test_notes_lines_check.py`, `test_policy_renewal_copy.py`), `mutation_manifest.json`, `mutation_runner_mutants.py`, `policy_mutants.py` of the head copied into a detached worktree of 37cd5157 (old src and old tools; `hadavin_sdk` imported from the old src, checked: `/home/user/build/ER-q8c1b17-old/src/hadavin_sdk/__init__.py`) | 1 | `13 failed, 135 passed in 81.00s` |
| 6 Equivalence of the removed mutant | head copy with the removed `else` branch put back as `else: found |= set()` in `tools/notes_lines_check.py`; ran `tests/test_notes_lines_check.py tests/test_policy_renewal_copy.py tests/test_policy_docs.py tests/test_policy_changelog.py tests/test_policy_guard.py` | 0 | `493 passed in 959.91s`: NO test failed with the mutation in place |
| 7 Plants | `HADAVIN_POLICY_FULL_RENEWAL_RUN=1 heavy.sh pytest tests/test_policy_changelog.py -k plant` | PLANTS_RC | PLANTS_LAST |

## Fail-before detail (item 5)
Test functions with a changed or added `def` line in 37cd5157..HEAD in the four test files: 15 (list in `added-tests.txt`).
- 10 of the 15 FAIL on old code (`test_mutation_runner.py` 1, `test_notes_lines_check.py` 9).
- 5 of the 15 PASS on old code: `test_notes_lines_check.py::test_a_fixture_named_in_the_short_forms_the_keyword_forms_and_by_alias_is_followed`, `::test_a_walrus_in_every_part_of_a_definition_header_binds_a_module_name`, and the three of `test_policy_renewal_copy.py` (`test_the_asked_row_count_must_be_within_the_tolerance_of_the_printed_figure`, `test_the_assertion_helper_reads_the_printed_figure_of_its_own_mode`, `test_the_printed_row_figure_is_read_once_per_renewal_and_a_missing_or_doubled_one_is_refused`).
- 3 further failing tests were not in the added list (older tests in changed files): `test_mutation_runner.py::test_a_file_named_in_extra_files_is_in_every_copy_and_a_missing_or_outside_one_is_not`, `::test_the_manifest_pins_the_files_a_demo_copies`, `test_mutation_runner_meta.py::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets`.
- Total 13 failed = 10 + 3. Full id list: `fb-failed.txt`.

## Hostile inputs on `tools/notes_lines_check.py` (item 6, unreadable or empty run-time import name)
Method: a throwaway local clone of the head; commit 1 adds a test (`tests/test_probe_u.py`) and a helper (`tests/probe_h.py`); commit 2 changes the helper and has an empty notes table; `python tools/notes_lines_check.py --auto HEAD~1 --head HEAD`. "Plant exit" 1 means the check listed tests.
| Probe | Plant exit | Check output (start) |
|---|---|---|
| `import_module('')` (empty literal) | 0 | nothing listed (the name is readable and names no module) |
| `import_module('   ')` (blank literal) | 0 | nothing listed (same) |
| `import_module()` (no argument) | 1 | `every test is listed because the check cannot read part of the tests tree: ...: an import call with no module name` |
| `import_module(*a)` | 1 | `...a module name that starts with a value` |
| `import_module(os.environ.get('X',''))` | 1 | same text |
| `import_module(str(0).strip())` | 1 | same text |
| `__import__(''.join([]))` | 1 | same text |
| `import_module('.probe_h', package='tests')` | 1 | `a relative module name written as one text (starts with a dot)` |
| `f = import_module; f(n)` with `n` unreadable | 1 | listed |
| `import_module(name=n)` with `n` unreadable | 1 | listed |
| `import_module(f'{n}')` with `n` unreadable | 1 | listed |
| `import_module(n + 'probe_h')` with `n` unreadable | 1 | listed |
| `f = import_module; f('')` (handed on, empty literal) | 0 | nothing listed (readable empty name) |
Raw: `probes.log`, `probes2.log`, `probes3.log`. Not tested: other loader forms, symlinked tests, non-UTF8 files.

## Housekeeping
Helpers started by me (Postgres 54917, throwaway worktrees `ER-q8c1b17`, `-old`, `-equiv`, clone `-probe`) are stopped or removed at the end; see the final line of this file.
