# Q8c-1 batch 8 PR notes (branch core/q8c1-b8, pushed to wip/cloud-q8c1-b8; base ad588599)

Raw logs: /home/user/build/b8-logs/ (outside the repo).

## What each fix is (class, siblings)
- Issue 1 (F1). Class: a default that no test reaches (every call passed `today=`). Siblings searched: `datetime.now` appears once in tools/policy_page.py (line 850); `today=` default only in `data_problems` and `main`. Fix: a test that patches `pp.datetime` with a fixed-clock subclass and calls `pp.main(["--check"])` with no `today`; CI step `python tools/policy_page.py --check` right after the policy mutants.
- Issue 2 (B7 class: mutant result depends on the real date or on a generic assertion text). Fix: the one test that served write and check is split in two, each assertion has its own message, the two "ignores the day" mutants now judge against a FIXED day (`DECIDED`) instead of the real clock, and all killers pass `today=`.
- Issue 3 (N1). Class: one date serving two purposes. `PENDING_KINDS` has its own literal `KINDS_DECIDED = date(2026, 11, 11)`; the plant tests keep `today=pp.DECIDED`; 16 `decided` values pinned in two tests.
- Issue 4 (N3). Class: a date literal in prose that goes false after a renewal. Docstring and CHANGELOG say "from the day after the earliest `review_by`"; a test checks the docstring holds no date that is not in the dated lists.
- Issue 5. One CHANGELOG sentence (also in the tool docstring): the date guard is a reminder, not a check that anyone re-read the names.

## Issue 6: one line per new or changed test (head vs ad588599)
Command for the fail-before runs: the head's three policy test files copied onto a clean checkout of ad588599 (old tools, old CI file, old CHANGELOG), `pytest -q -p no:cacheprovider tests/test_policy_guard.py tests/test_policy_changelog.py tests/test_policy_docs.py`. Output (b8-logs/failbefore-real.log): `3 failed, 350 passed`. Same result with the clock faked to 2026-12-12 (b8-logs/fake-old.log).

| test | status on old head | proof |
|---|---|---|
| test_the_tool_docstring_holds_no_date_that_is_not_in_the_dated_lists | FAILS on old head | docstring holds 2026-12-12 |
| test_ci_runs_the_policy_page_check_right_after_the_policy_mutants | FAILS on old head | old ci.yml has no such step |
| test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder | FAILS on old head | old CHANGELOG text |
| test_the_check_command_uses_the_tools_own_clock_when_no_day_is_given | control (the old tool already uses the real clock: it is a guard) | killed by mutant "B8 the default clock of the data check is a fixed day" |
| test_from_the_review_date_the_write_command_stops_and_writes_nothing | control (split of the old test) | killed by mutants "B7 write command writes the page although overdue" and "B7 the write command judges the data against a fixed day" |
| test_from_the_review_date_the_check_command_stops | control (split of the old test) | killed by mutant "B7 the check command judges the data against a fixed day" |
| test_the_sixteen_kinds_keep_a_decision_day_of_their_own_not_the_tools_date | control (values equal today) | killed by mutant "B8 the pending kinds take another decision day than their own literal" |
| test_the_sixteen_pending_kinds_each_stand_on_the_day_they_were_decided (changelog file) | control (same reason) | not run by the mutant runner (it copies only test_policy_guard.py); the same pin sits in the guard file above, which a mutant kills |
| test_plant_d1_a_wildcard_resource_with_no_bound_is_caught, test_plant_d3_an_empty_reason_is_caught, test_plant_d7_unknown_keys_platform_and_never_type_are_refused | control (messages only) | the mutants D1, D3, D7 now expect the call's own `what` text |

Tests changed in batch 7 (d598d967..ad588599): 13 fail on d598d967 with the clock faked to 2026-12-12 (names in handover/evidence/Q8c-1/ad588599/pol3-fake-old-failed.txt, the independent evidence). I did not re-run them and did not individually classify the other changed tests of batch 7; the review names two kinds that pass on the old tool (`any(...)` and `startswith`) as controls by design. This part of Issue 6 is therefore only as complete as that evidence.

## Ticket 6.4 "must fail on origin/main" list, run once (b8-logs/mustfail-main.log)
Method: origin/main (2a8c2aac) src untouched; overlaid tools/policy_page.py, tests/test_policy_guard.py, tests/test_policy_engine.py, tests/test_policy_changelog.py, tests/test_policy_docs.py and the sources fixture; the docs page and the CI file are NOT overlaid. Command: `pytest -q -p no:cacheprovider` on the four policy test files. Output: `239 failed, 122 passed, 12 skipped`. F1: `E Left contains one more item: 'no POLICY in src/hadavin_sdk/actions/secrets_vault.py'` (and audit/signer_vault.py, sources/kubernetes.py); F2: `test_the_committed_page_equals_what_the_data_gives` FAILED; F3 (Vault engine): the 12 engine tests skip here (no server), so F3 on Vault is not shown; the moto part is PR 2 (not in this branch).

## Weak `expect` fragments (scan of all mutants)
Scan (script in scratchpad, reads tests/policy_mutants.py): fragments of 6 characters or fewer: ONE, "== 1" of the old B7 mutant (replaced). Mutants whose killer asserts through `same()`: 40 of 111; the runner's own classifier still prints 40 because it cannot see the new `what` argument. Strengthened (which guard grants/rules): D1 wildcard resource with no bound (expect "holds a wildcard" appeared in both calls), D3 empty reason (both calls), D7 unknown key (three calls): each call has its own `what`. Not changed: the other 37, because their killer has a single `same()` call whose expected text is unique to that assertion (checked by counting `same()` calls per killer). Not strengthened by design: nothing that guards a line or the date guard was left weak.

## Not done / open
- Issue 7 (Vault engine tests in CI, ENGINE_RUN) untouched, needs a CI run with HADAVIN_REQUIRE_VAULT_ENGINE=1 before 2026-12-11.
- Mutant "moves the tool's DECIDED" (Issue 3 wording): such a move cannot make a test red, because the kinds no longer read it; the mutant I added moves the kinds' own literal instead.

## Gates on head 208a47d5 (exit codes; logs in b8-logs)
ruff check 0; ruff format --check 0 (324 files); bandit -ll 0; scan_repo 0; policy_page --check 0; policy mutants 111 of 111 good exit 0; stage mutants 37 of 37 good exit 0; three policy files: real clock 353 passed, clock faked to 2026-12-12 353 passed; gitleaks staged 0 and range 0; full pytest: 1 failed, 10884 passed, 13 skipped (12 Vault engine + 1 llm), 28 deselected; the 1 failure is tests/demo_askdata/test_validate_harm.py writing the shared path /tmp/askdata_p2_copy.csv that another session's Postgres (user postgres) had created: file alone re-run as the same user: 253 passed.
