# Evidence: Q8c-1 batch 16, round 16, code head 43be04debcda1600928c2f5eaa3dc4d0f4a8b7bc (EVIDENCE RUNNER, no judgement)

Clean detached worktree (`git rev-parse HEAD` = the sha above, `git status` clean before and after). Own Postgres 16 on private port, database encoding UTF8.
Raw logs: `/home/user/build/evidence-raw/Q8c1b16-43be04de/` (outside the repo). The branch tip 37cd5157 only adds files under handover/.

## Not run / deviations (first)
- Item 1, full suite: exit 1, `1 failed, 11016 passed, 13 skipped, 28 deselected in 1112.87s`. The one failure is `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: `could not establish connection ... socket "/var/run/postgresql/.s.PGSQL.5432"`. Cause (my setup slip): I started my Postgres without PGHOST/PGPORT in the server's own environment, so the server's dblink looked at the default socket. I restarted the server with PGHOST/PGPORT set and re-ran the whole `tests/demo_askdata` folder: `1212 passed, 2 deselected in 47.75s`, exit 0. I did NOT repeat the whole suite a second time (one full run only, per the rule). So there is no single full run with exit 0.
- 12 tests need a real Vault server (`HADAVIN_TEST_VAULT_ADDR` not set): not run (tests/test_policy_engine.py lines 255, 263, 271, 285, 297, 310, 373, 386 x2, 401, 413, 425). One more skip: `tests/contracts/test_llm.py:95` (Stubber).
- The 3 renewal plants (`HADAVIN_POLICY_FULL_RENEWAL_RUN=1`, `tests/test_policy_changelog.py -k plant`, about 42 min): NOT run (per the brief; the builder reports rc 0).
- Item 3 "delta rows one by one": I ran the whole policy run once (375 of 375) and the delta rows as one named run (each row prints its own line, 27 lines); I did not start 27 separate processes.
- Item 5 fail-before: the copied files were the 9 files the delta changes (`tests/test_k1b_cli.py`, `test_mutation_runner.py`, `test_mutation_runner_meta.py`, `test_notes_lines_check.py`, `test_policy_changelog.py`, `test_policy_renewal_copy.py`, `tests/mutation_runner_mutants.py`, `tests/policy_mutants.py`, `tests/fixtures/mutation_manifest.json`) onto a detached worktree of ccb63021 (src, tools, CHANGELOG old; checked `hadavin_sdk` and `tools.mutation_runner` import from the old tree). Only the 6 changed test files were run; the unchanged `tests/test_policy_guard.py` etc. were not. The three plant tests ran without the full-renewal variable, so they failed on old code for that reason as well as for any code reason (see list).
- Item 7: `--auto origin/main --head HEAD` at the code head 43be04de exits 1 (the notes file `handover/evidence/Q8c-1/b16/NOTES.md` exists only at the branch tip). I also ran it with `--head 37cd5157`: exit 0, no output.
- Item 8: only the existing unit test was run (plus the 3 extra_files mutants inside the runner-mutant run); I wrote no new hostile link probe.
- Bandit prints a "nosec but no failed test" warning for `src/hadavin_sdk/tools.py:389` (same as the previous round). Gitleaks was not on PATH; I used the copy at `/tmp/claude-0/.../scratchpad/glbin/gitleaks` (8.30.1).

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 1 | `1 failed, 11016 passed, 13 skipped, 28 deselected in 1112.87s` (failure = my Postgres setup, see above) |
| 1b Re-run of the failed folder | same flags, `tests/demo_askdata` | 0 | `1212 passed, 2 deselected in 47.75s` |
| 2 Stage mutants | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 3 Policy mutants, real clock, whole run | `python tests/policy_mutants.py` | 0 | `375 of 375 good; problems: []`; every row `ok  KILLED`, 0 `BAD`; weak first-line count `0 of 375` |
| 4a B16 set + the 2 changed B15 rows | `python tests/policy_mutants.py 'B16 ' 'B15 ...unreadable run-time import name'` and `'B15 ...follows/starts with'` | 0, 0 | `26 of 26 good` (25 B16 rows + 1 B15 row) and `1 of 1 good` (second B15 row); all `ok  KILLED` |
| 4b Runner mutants | `python tests/mutation_runner_mutants.py` | 0 | `65 of 65 good; problems: []` |
| 5 Fail-before | 6 changed test files, old src of ccb63021, own `heavy.sh` | 1 | `16 failed, 152 passed in 162.51s` (ids in `5-failed-ids.txt`) |
| 6a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 6b ruff format | `ruff format --check src tests demos tools` | 0 | `327 files already formatted` |
| 6c bandit | `bandit -q -r src demos tools -ll` | 0 | only the nosec warning above |
| 6d scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 6e policy page | `python tools/policy_page.py --check` | 0 | no output |
| 6f gitleaks | `gitleaks git --redact --log-opts origin/main..43be04de` | 0 | `no leaks found` (scanned ~2.47 MB) |
| 7a Notes check at code head | `python tools/notes_lines_check.py --auto origin/main --head 43be04de` | 1 | 41 lines, each "has no row" (notes file not on this commit) |
| 7a2 Notes check at branch tip | `... --auto origin/main --head 37cd5157` | 0 | no output |
| 7b Hostile probes | throwaway detached worktree, plant (no row) and control (row) | see below | all plants exit 1, all controls exit 0 |
| 8 extra_files | `pytest tests/test_mutation_runner.py -k extra_files` | 0 | `1 passed, 59 deselected` |

## Fail-before detail (item 5)
14 test functions were added in the delta ccb63021..43be04de (list in `5-added-defs.txt`).
- Failed on old code (9 of 14): the notes-check tests (`..package_of_tests`, `..keyword_name..`, `..package_is_reached..`, `..another_name_of_import_module..`, `..fixture_registered_under_an_alias..`, `..fixture_named_by_a_text_that_cannot_be_read..`, `..lazy_fixture_or_by_parametrize_indirect..`), `..walrus_in_a_definition_header..`, `..limits_of_the_notes_check_are_stated..`.
- PASSED on old code (5 of 14): `test_every_other_command_that_loads_the_config_also_refuses_an_empty_vault_path_prefix_with_exit_2` (4 ids), `test_a_name_built_at_run_time_with_a_percent_format_or_through_dunder_import_is_read_like_the_others`, `test_the_name_of_a_fixture_that_the_call_getfuncargvalue_names_lists_the_test`, `test_a_plugin_is_followed_through_the_attached_p_option_and_through_each_settings_file_and_an_annotated_list`, `test_a_star_import_is_followed_in_its_relative_form_and_through_a_module_that_only_re_exports` (confirmed with `-v`, log `5b-passing-on-old.log`). The B16 mutants for getfuncargvalue, percent format, `-p`, star import are all KILLED (4a), so those tests are pinned by a mutant; the vault-prefix test has no mutant row that I checked.
- Other failed ids on old code (7): `test_mutation_runner.py::test_a_file_named_in_extra_files_...`, `::test_the_manifest_pins_the_files_a_demo_copies`, `test_mutation_runner_meta.py::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets`, the 3 `test_policy_changelog.py::test_plant_*` (see deviation above), `test_policy_renewal_copy.py::test_the_notes_check_of_a_renewed_copy_asks_for_rows_that_can_be_written_and_then_passes`.

## Hostile probes (item 7b)
Method: throwaway detached worktree at 43be04de (removed afterwards, nothing pushed). Commit 1 adds the probe test(s); commit 2 changes the helper/fixture and adds a notes file with no row (plant) or with a row for each listed unit (control); `--auto <commit1> --head <commit2>`. Raw: `7b-probes.log`.
| Probe | Plant | Control |
|---|---|---|
| `from tests.x import y` plus `import_module(name)` (name in a variable), helper read by name changed | exit 1, `test_p ... no row` | exit 0 |
| same, the other helper (the `from` import) changed | exit 1 | exit 0 |
| `import_module(name=f"tests.probe_pkg.{n}")`, package file changed | exit 1 | exit 0 |
| `for m in MODS: import_module(m)` | exit 1 | exit 0 |
| `request.getfuncargvalue("fx")`, fixture in same file | exit 1 | exit 0 |
| same, fixture in a conftest | exit 1 (fixture and test listed) | exit 0 |
| `@pytest.fixture(name="alias")` in a conftest | exit 1 | exit 0 |
| same, in the same file | exit 1 | exit 0 |
| `parametrize("data", [1], indirect=True)`, fixture in conftest | exit 1 | exit 0 |
| `pytest.lazy_fixture("fx")`, fixture in conftest | exit 1 | exit 0 |
Not tried: other variants beyond this list.

## Cleanup
Postgres stopped; the three worktrees I made (evidence, probe, old-src) removed after the runs (evidence worktree was clean at 43be04de); my Postgres data folder `/home/user/build/ER-q8c1b16-pg` is left on disk, server stopped. Nothing committed or pushed.
