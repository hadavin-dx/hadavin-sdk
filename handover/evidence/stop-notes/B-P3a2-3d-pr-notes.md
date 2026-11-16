# P3a-2 commit 3d: fix batch for round 2 of commit 3c (Issues 1-20)

Start: wip/cloud-p3a2-3c at 11bd1260f83904242878f8de29d0d3195df4bb83. Branch core/p3a2-3d, pushed as wip/cloud-p3a2-3d (new ref, plain push).

## What is NOT done or only partly done (read first)
- Issue 2 (ticket 7.7 test, the empty-database test of what each role can really do): NOT BUILT. The ticket schedules it for commit 5. The docstring, the CHANGELOG and a test now say "NOT BUILT YET (planned for commit 5)". Next step: build it in commit 5.
- Issue 3 sentence, now in CHANGELOG and docstring: "Rows 1 and 2 of the promise table are not proven until commit 5 builds the empty-database test of what each role can really do."
- The PostgreSQL 17 branch of test_a_saved_transaction_timeout_stops_the_check_and_migrate_refuses_with_exit_2 is UNRUN: the only server here is PostgreSQL 16. On 16 the test pins that the server refuses the setting, and then runs migrate. Next step: the independent evidence run or CI on 17.
- Issue 19 deviates from the ticket on purpose: SQLSTATE 40003 (statement completion unknown) is classed "unknown" (exit 5) although the ticket F5 allowlists all of class 40 as refused. Needs a ticket line change or the lead's decision.
- Not decided here: q-p3a2-e1-extension-lockout and q-p3a2-o8-schema-owner (strict defaults stay). Not built: the 37x13 matrix, lock mutants, --list-batch (commits 4 and 5).
- tests/test_migration_numbers_perf.py (flaky timing test) was not touched.
- Ledger rows M1-M5, C1, C2 and the commit-5 matrix row stay OPEN until independent evidence exists.

## Issue by issue
1. Driver errors of verify before the commit (steps 2 and 6): new context manager `_check_could_not_run` gives ConfigError, exit 2, nothing kept. Mutants V67, V68.
2. See above.
3. See above.
4. CHANGELOG message forms rewritten to the real forms (`has {right}`, `can use it through the role {via}, {right}`, `To remove: {statement}`); test that every quoted form occurs in src (and a planted-fault test).
5. `_judge` tests for MAINTAIN and for unknown right words (not by prefix). Mutant V61.
6. REVOKE at step 4 goes through quote_identifier; the old skip of names with unusual characters (which left EXECUTE for everyone) is gone. Real-server test with 5 awkward names. Mutant V66. Siblings searched: no other hand-built identifier in migrate.py.
7. Retire count: all 29 ids of ticket 5.5 exist in tests/migrate_mutants.py at 4d328e3d and none exists at 11bd126 or at this head. So 29 retired, 0 "never existed" (the 17/12 split was wrong). Command: /tmp/claude-0/retire.py (git show REV:tests/migrate_mutants.py, regex of ids, for 4d328e3d, 11bd126, HEAD).
8. V-mutant labels corrected against ticket 3.3: V10 O2, V13 O7, V14 O2, V15 Q2 change (d), V16 O2, V17 O7, V18 O1, V19 O3, V20 O4, V21 O8, V22 S7, V23 E1, V25 D4, V26 D1, V27 D2, V28 D3.
9. Schema-owner exception docstring wording only.
10. Step numbering follows the ticket (0 to 8); migrate() docstring says a return means committed and checked.
11. Empty access list: the hole was real (verify returned nothing for a hostile empty-ACL SECURITY DEFINER function and for a foreign-owned map table). Q2 uses LEFT JOIN LATERAL, `_judge` skips the null right and still judges owner and definer. Mutants V62, V70.
12. SECURITY DEFINER wording: what `_judge` checks (reviewed list, owner, EXECUTE) and what it does not (body, search_path).
13. 1 ms statement-timeout test (V48), 57P01 asserted via `_commit_outcome` (V69), cancel at commit gives exit 2.
14. "postgres" no longer hard-coded: names from current_user.
15. Docstring sentence on login differing from the migration role.
16. Weak `A or any(...)` assertion made strict.
17. Dead constant removed, stale mutant ids in docstrings reworded (to "Guards: ... (no list mutant today)"), `problems_with_the_list` now also checks ids named in docstrings of killers and parametrize ids of killers; planted-fault test added (test_the_list_check_finds_a_mutant_id_...).
18. The branch that returned without running migrate: the PG16 branch of the transaction_timeout test now runs migrate before it returns; the prepared-transaction branch (max_prepared_transactions = 0) already ran migrate before its return, and now carries a comment saying why that return is not an early return.
19. 40003 as unknown (mutant V65).
20. See the table below.

## Issue 20: tests that pass on old code, and why
| test | passes on old code because / killed by |
|---|---|
| test_maintain_is_one_more_right_... | guards a rule that already held; killed by V61 |
| test_an_unknown_right_word_is_refused_whole_never_by_prefix | old code compared whole words; killed by V61 |
| test_an_item_with_no_right_is_never_read_as_a_right_for_everyone | new null row cannot occur on old Q2; killed by V62 |
| test_every_sentence_form_the_changelog_quotes_is_in_the_code... (+ planted fault) | old CHANGELOG forms were wrong only in text; the planted-fault test proves the check fails on a stale quote |
| test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog | V63, V64 |
| test_verify_gets_through_a_one_millisecond_statement_timeout... | V48 |
| test_a_lost_connection_at_commit_gives_exit_5 (57P01 form) | V69 |
| test_a_cancel_at_commit_gives_exit_2 | control for the refused class; passes on old code by design (V65 and V69 sit next to it) |
| PG16 branch of test_a_saved_transaction_timeout_... | passes on old code: nothing can be saved on 16; the 17 branch is killed by V67 and is UNRUN here |
| test_the_list_check_finds_a_mutant_id_... | tests the checker; no mutant; fails if `_stale_ids` is made to return [] |
| 40003 case of test_commit_outcome_classes_unknown_by_code | V65 |

## Fail-before (proven against 11bd126 src)
- test_an_object_whose_access_list_is_empty_is_still_judged_for_owner_and_definer: fails on old src.
- test_a_connection_lost_while_the_check_runs_before_the_commit_gives_exit_2 (step_2, step_6): fails on old migrate.py.
- test_step_4_takes_everyones_execute_off_functions_with_awkward_names: fails on old migrate.py.
- (3 failed, 1 passed in the selected set on old migrate.py; the one that passed is the PG16 transaction_timeout branch.)

## Gate results at head c7e0908 (code identical to fd3fee2 except the V62 test)
- ruff check 0; ruff format --check 0; bandit -ll -r src 0; tools/scan_repo.py 0; gitleaks no leaks; tests/stage_mutants.py 37 of 37 good (run at fd3fee2).
- Full pytest -m "not live and not perf" (fd3fee2): 1 failed, 11274 passed, 1 skipped. The failure is tests/demo_askdata/test_validate_harm.py::...[dblink-connect]: the Postgres SERVER process cannot open the default socket /var/run/postgresql/.s.PGSQL.5432 (my test server listens on TCP 57031 only). It touches no file of this diff; NOT yet shown to pass on a server with the default socket. Next step: the independent evidence run.
- Five migration test files at c7e0908: 581 passed.
- tests/migrate_mutants.py (fd3fee2): 352 of 353 killed; V62 was BROKEN (the mutant crashed the test instead of failing it by assertion). Test fixed in c7e0908; V62 re-run alone: 1 of 1 killed. The other 352 were not re-run at c7e0908 (the edit touches one test only).
- tests/migration_numbers_mutants.py: 40 of 40 good.
- Collision note: /tmp/claude-0/*.log names are shared with other builders; my logs are in /home/user/build/B-P3a2-3d-logs/.
