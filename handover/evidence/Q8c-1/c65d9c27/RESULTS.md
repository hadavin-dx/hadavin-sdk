# Evidence: Q8c-1 batch 13, head c65d9c27ccf757cf9210bafa7b15d610b3e09e37

EVIDENCE RUNNER: results are recorded, not judged. Nothing was fixed, committed on the branch or pushed.
Tag Q8c1-b13, previous reviewed head 6d219217. Run 2026-11-12 10:40 to about 11:20 UTC (16:10 to 16:50 IST).
Raw logs: /home/user/build/evidence-raw/Q8c1-b13-c65d9c27/ (outside the repository). Small excerpts: `excerpts/` here.

## What failed or was not run (first)

1. `uv sync --locked --no-build` (the CI command) fails on this machine: "hadavin-sdk==0.1.0 @ editable+. ... marked as
   --no-build but has no binary distribution". I re-ran `uv sync --locked --all-extras --group test` (without `--no-build`);
   it succeeded. Everything below ran in venvs made that way.
2. `bandit` is not in the project venv (`uv run --no-sync bandit` exit 2, "Failed to spawn"). Run instead with
   `uv run --with bandit bandit -q -r src demos tools -ll`: exit 0 (only "nosec ... no failed test" warnings).
3. Rehearsal of the first renewal (item 6): NOT green after following the printed steps literally. Details in item 6.
4. Item 6 mutants on the renewed copy: 268 of 269 good at both 2026-12-12 and 2026-12-13, one SURVIVED (item 6).
5. Item 3 plants: two cases were NOT flagged (b3, b5 helper changes reached through another helper module; d3 a
   row for a mutant that does not exist in the unit cell). Details in item 3.
6. Not run: CI perf step (`pytest -m perf`), the Python 3.12 job, semgrep, zizmor, the CI Vault service (the 13 skips
   need a real Vault server), the flaky `test_the_timing_harness_flags_a_quadratic_stand_in` (no perf item in this
   brief; it was not run on head or main). The CI step "notes check" is the `--auto` run in item 3.
7. Own Postgres 16.15 was used (unix socket, own folder). The Postgres, folders and worktrees were removed at the end.

## Table

| Item | Command (all on the exact head, `git rev-parse HEAD` = c65d9c27..., tree clean) | Exit | Last line |
|---|---|---|---|
| 1 | `git diff --name-only origin/main...HEAD` | 0 | 96 files (excerpts/item1-files.txt); non-handover: ci.yml, CHANGELOG.md, README.md, docs/declared-permissions.md, 3 src files, fixture, 6 tests/tools files |
| 2 | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 | `ruff format --check src tests demos tools` | 0 | 326 files already formatted |
| 3 | `bandit -q -r src demos tools -ll` (via `--with bandit`) | 0 | nosec warnings only |
| 4 | `python tools/scan_repo.py` | 0 | no output |
| 4 | `python tools/policy_page.py --check` | 0 | no output |
| 4 | `gitleaks git --redact ... --log-opts="origin/main..HEAD"` | 0 | no leaks found |
| 2/4 | `python tests/stage_mutants.py` (head, via heavy.sh) | 0 | 37 of 37 good; problems: [] |
| 2 | `python tests/policy_mutants.py` (real clock 2026-11-12) | 0 | 269 of 269 good; weak 0 of 269; 269 killed lines |
| 2 | `python tests/policy_mutants.py --day 2026-12-11` | 0 | 269 of 269 good; weak 0 of 269 |
| 2 | `python tests/policy_mutants.py --day 2026-12-12` | 0 | 268 of 268 good; weak 0 of 269; "not run at 2026-12-12: B12 an overdue unchecked claim is reported one day late (its killer is a date test that is red on that day)" |
| 3 | `notes_lines_check.py --auto 6d219217` | 0 | no output |
| 3 | `notes_lines_check.py --auto origin/main` | 0 | no output |
| 4 | full `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (heavy.sh, own Postgres 16.15) | 0 | 10968 passed, 13 skipped, 28 deselected in 426.76s |
| 5 | fail-before (below) | 1 | 19 failed, 417 passed |
| 6 | rehearsal (below) | see below | |
| 7 | `git diff --stat origin/main..HEAD -- src` | 0 | 3 files, 536 insertions (below) |

Mutant counts: with a killer 269 (real clock, 12-11); 268 (12-12, one not run by design). Weak mutants 0 in all three runs.
"Killed only by a test that reads the clock function": 6 of 269 in each run.

## Item 4: the 13 skips (all from `-rs`, excerpts/item-skips)

1 in tests/contracts/test_llm.py:95 ("Stubber refuses a malformed Converse shape before the kind sees it"); 12 in
tests/test_policy_engine.py (lines 255, 263, 271, 285, 297, 310, 373, 386 (2 tests), 401, 413, 425), each
"needs a real Vault server (HADAVIN_TEST_VAULT_ADDR is not set)". Full text: excerpts/i5-skips.txt.

## Item 3: plants on a scratch clone (excerpts/i3-plants.log, verbatim)

Each plant was one commit on top of c65d9c27 in a scratch clone, checked with `--auto origin/main` (and for a, b1, b2, b3 also `--auto 6d219217`).

| Plant | Result | First line printed |
|---|---|---|
| a: new test file, no notes row | exit 1 (both bases) | tests/test_zz_plant_a.py: the test test_plant_a_new_test_without_row is new or changed and has no row of its own in the notes |
| b1: only a NEW unused function added to tests/k1b_support.py | exit 0 | no output |
| b2: only a value used by many tests changed in tests/k1b_support.py (`"severity": "page"` to `"ticket"`) | exit 1, 108 lines (both bases) | tests/test_k1b_bundle.py: the test test_alert_time_constant_is_a_valid_timestamp is new or changed and has no row of its own in the notes (and the rest of the tests of the importing files) |
| b3: only the body of `azure_secret_client` in tests/contracts/http_fake.py changed (reached by tests only through tests/contracts/kinds/secrets_neutral.py, then tests/contracts/test_secrets.py) | exit 0 (both bases) | no output (excerpts/i3-b3-importers.txt lists the importers) |
| b4: only the body of `gcp_secret_client` in http_fake.py changed (imported by name inside a function of tests/test_p4b_secrets.py) | exit 1 | tests/test_p4b_secrets.py: the test test_gcp_fetch_is_bounded_with_no_retry is new or changed and has no row of its own in the notes |
| b5: only the body of `_azure` in tests/contracts/kinds/secrets_neutral.py changed (a helper module under tests/contracts/kinds used by tests/contracts/test_secrets.py) | exit 0 | no output |
| c1: module-level `pytestmark = pytest.mark.skip(...)` in tests/test_p4b_secrets.py | exit 1, 22 lines | tests/test_p4b_secrets.py: the test test_a_fifo_in_the_mounted_folder_is_refused_without_hanging is new or changed and has no row of its own in the notes (all tests of the file) |
| c2: `pytest_collection_modifyitems` skip hook added to tests/conftest.py | exit 1 | tests/conftest.py: the test pytest_collection_modifyitems is new or changed and has no row of its own in the notes |
| c3: autouse fixture that calls `pytest.skip` added to tests/conftest.py | exit 1, 9 lines | tests/conftest.py: the test FIXTURES is new or changed ... (also _ISOLATED, _plant_skip, cfg_dir, fake_system and more) |
| c4: xfail hook added to tests/contracts/conftest.py | exit 1 | tests/contracts/conftest.py: the test pytest_collection_modifyitems is new or changed and has no row of its own in the notes |
| d: the unit cell of the B10 row in b13 NOTES.md changed to `B99 no such mutant exists here` (the same B10 mutant is also covered by another row) | exit 0 | no output |
| d2: reason cell names `test_no_such_test_anywhere` | exit 1 | tests/policy_mutants.py: the mutant B10 ... has a row whose reason points at nothing: the test test_no_such_test_anywhere is in no test file |
| d3: an extra row whose unit cell is `B99 no such mutant exists here` (valid-form reason) | exit 0 | no output |
| d4: reason cell names backticked `B99 no such mutant exists here` | exit 1 | ... has a row whose reason points at nothing: the mutant `B99 no such mutant exists here` is in no mutant file |
| e: new mutant `B11 notes check ignores` (a substring of another row's cell, no row of its own) | exit 1 | tests/policy_mutants.py: the mutant B11 notes check ignores is new or changed and has no row of its own in the notes |

## Item 5: fail-before

Clean detached worktree of 6d219217 (src and tools of the old commit), with ONLY these changed test files copied from
the head: tests/test_notes_lines_check.py, tests/test_policy_changelog.py, tests/test_policy_guard.py; tests/test_policy_docs.py
is unchanged since 6d219217 and was run with them. Command: `pytest -p no:cacheprovider -q -rf` on the four files, through heavy.sh.
Result: **19 failed, 417 passed** (436 tests; same as the builder's numbers). A run of only the three copied files gave 19 failed, 406 passed.
Failed test ids (19): excerpts/i5-failed-ids.txt. Test ids in the four files: 419 on the old files, 436 on the head files, so 17 new ids; 12 of
the new ids fail on the old code and **5 new tests PASS on the old code** (excerpts/i5-new-pass-on-old.txt):

- tests/test_policy_guard.py::test_more_written_forms_of_a_day_are_found_and_an_ordinary_word_is_not_a_day
- tests/test_policy_guard.py::test_no_test_writes_a_day_of_the_renewal_window_as_a_literal_inside_a_function
- tests/test_policy_guard.py::test_plant_a_written_day_in_a_function_is_found_and_a_derived_day_a_top_level_day_and_the_pin_are_not
- tests/test_policy_guard.py::test_the_changelog_entry_ends_at_a_numbered_item_and_at_a_horizontal_rule
- tests/test_policy_guard.py::test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it

7 of the 19 failing ids are tests that existed before (changed tests). I did not check by hand which failures are for the right reason; the failures listed are
mostly `AttributeError: module 'tools.policy_page' has no attribute 'KINDS_RENEWAL_RULE'` and the like.

## Item 6: first-renewal rehearsal (scratch clone, clock set with `HADAVIN_POLICY_FIXED_DAY=2026-12-12` and `HADAVIN_POLICY_MUTANT_RUN=1`, the mechanism of `--day`)

At 2026-12-12 on the unchanged head, the four policy test files (436 tests): **3 failed, 433 passed**:
test_every_kind_is_declared_pending_or_holds_no_identity, test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves,
test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue. The full text a person reads, for the three lists, is in
excerpts/i6-messages-1212.txt (PENDING_NAMES 6 problems, PENDING_CLAIMS 7 problems, PENDING_KINDS 7 problems). Each starts "... is overdue (review_by 2026-12-11): ... What to do: finish that work and delete the entry; or, if it cannot be finished now, decide again: set `decided` ... at most 92 days after it. Renew all or none: ..." followed by the numbered steps.

I applied the steps literally, with new decision day 2026-12-12 and new review day 2027-01-11 (30 days, as the old pair). Edits, all listed in
excerpts/i6-renewal-edits.diff: tools/policy_page.py (DECIDED and the three `review_by` days); tests/test_policy_guard.py (the pin of `pp.DECIDED`,
`KINDS_DECIDED`, `_PR2`, the day in test_the_sixteen_kinds...); tests/test_policy_changelog.py (`KINDS_GROUPS`, `KINDS_LITERAL`); CHANGELOG.md (the kinds sentence);
page rewritten with `tools/policy_page.py --write` (this needs `today` 2026-12-12, so I called `pp.main(['--write'], today=date(2026,12,12))`:
the real clock 2026-11-12 refuses, "decided 2026-12-12 is in the future"; `--check` exit 0 the same way). I did NOT change the nine kinds with `review_by` 2027-01-31
(still within 92 days of the new decision day); that is my reading of "(the groups of days are kept apart on purpose)".

Result after that renewal, at the fixed days 2026-12-12 and 2026-12-13: **1 failed, 435 passed** in both:
`tests/test_policy_changelog.py::test_plant_a_full_renewal_done_as_the_overdue_messages_list_it_keeps_the_tests_the_page_and_the_mutants_green`, message
"the renewal step does not apply: '7 kinds that fail from 2027-01-12 and 9' is not in tests/test_policy_changelog.py". Cause seen in the file: line 38 of
tests/test_policy_changelog.py (the message text of `_kinds_pin_problem`) carries the day "2026-12-12" as written text; no printed step names it
(step 2 names only `KINDS_LITERAL` and `KINDS_GROUPS`). **A day the steps did not name that still failed: tests/test_policy_changelog.py line 38.**

I then also changed that line to 2027-01-12 and ran again: still **1 failed, 435 passed** at both days; the same test now fails inside its own nested renewal copy:
"after the renewal the tests are red: _names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder()" with, in the nested copy, 5 red tests:
test_the_kinds_pin_refuses_a_moved_kind_another_built_sentence_and_an_entry_without_it, test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail,
test_plant_a_moved_or_regrouped_kinds_list_or_a_changelog_that_follows_it_is_refused, test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list,
test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder (message: "the changelog entry hard-codes a day (not the kinds list's)"). That test renews
the already-renewed tree a second time, +31 days; in that nested copy the group of 7 kinds (review 2027-02-11, failing from 2027-02-12) comes after the group of 9 (review 2027-01-31, failing from 2027-02-01)
while `KINDS_GROUPS` lists 7 first. I did not look for further causes. Excerpts: renewed-guard-tests-1212-first.log (before the line 38 edit), renewed-guard-tests-1212-after-line38-edit.log.
The notes check on the renewed copy (`--auto origin/main`): exit 0, no output.
Mutants on the renewed copy (step 6), `python tests/policy_mutants.py --day 2026-12-12` and `--day 2026-12-13`: both exit 1, **268 of 269 good, 1 SURVIVED**:
`B13 a test of the policy files writes a day of the renewal window as a literal`. Its plant text writes `date(2026, 12, 10)`, a day that is no longer inside the renewal window after the renewal; I did not run the
real-clock mutant run on the renewed copy, since the real clock (2026-11-12) is before the new decision day. After a renewal of both groups, I did NOT edit tests/policy_mutants.py, as the step says.

## Item 7

`git diff --stat origin/main..HEAD -- src`: 3 files (src/hadavin_sdk/actions/secrets_vault.py 137, src/hadavin_sdk/audit/signer_vault.py 156, src/hadavin_sdk/sources/kubernetes.py 243; 536 insertions, no deletions).
These three were already on the branch before 6d219217: `git diff --stat 6d219217..HEAD -- src tools/mutation_runner.py` prints nothing (no change under src/ in this batch, tools/mutation_runner.py unchanged).
`git diff --stat origin/main..HEAD -- tools/mutation_runner.py` prints nothing. "No grant widened" was NOT checked by me beyond that the src diff since 6d219217 is empty; the three files above
vs main were not read for grant changes.

## Not verified / limits

- Builder numbers repeated here are mine: 37/37, 269/269, 269/269, 268/268, 10968 passed 13 skipped 28 deselected, 19 failed 417 passed. All match.
- Heavy runs waited in the heavy.sh queue (other agents held the slots) about 10 to 15 minutes in total; the fail-before run and the renewed-copy mutants waited most.
- Timing/perf tests did not run alone; the full suite ran in parallel with the stage and policy mutant runs on other worktrees.
