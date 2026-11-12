# Round 17: new or changed tests that PASS on 140a1268, one line each (reason or killing mutant)

Run: clean detached worktree of 140a1268 with only the four changed test files copied in, PYTHONPATH on that worktree's src, own PostgreSQL 16.15.
Raw output: new-tests-on-140a1268.txt (7 failed, 37 passed, 0 collection errors, 1529 deselected by -k).
The 7 that fail on the old code: 2 sign-in refusal tests and 2 address-without-host-or-user tests (tests/test_migration_verify.py), the close-hides-first-error test (verify), and the sign-in-at-start test and the unreachable-address test (tests/test_migration_verify_pg.py).

Why the rest pass on the old code: these tests check helper code that lives in the test file itself (the reason builder, the probes, the wording checks), so the old src cannot change their result. Each is shown to fail when its helper is broken, by a mutant.

- test_c10_every_effect_with_a_statement_is_in_one_set...: tests the set tables inside the test file; the added lines use `_expected_outcome` on the C10 sets. Killing mutant: none new; true reason: the rule it reads (the matrix table) is unchanged by this round, the added asserts pin it.
- test_the_matrix_has_exactly_the_planned_cells: the new numbers (6/6 and 8/4) are computed from the test file's own lists; old src cannot change them. Not mutant-killed; true reason: a count test of the table.
- test_every_empty_pair_has_a_probe_and_its_reason_carries_...: killed by V127.
- test_a_reason_or_a_probe_that_is_edited_to_a_wrong_fact_is_found: pure weaken-and-fail of the checker; the checker is in the same file. True reason: it plants wrong facts in copies of the tables and asserts the checker finds each.
- test_every_empty_reason_is_the_answer_of_a_real_server: killed by V128 (and fails if a server answer differs).
- test_the_real_server_check_of_a_probe_reports_a_wrong_state_...: weaken-and-fail on a real server; helper in the same file.
- test_c13_the_function_of_the_map_moved_...[no-roles] and [with-roles]: the behaviour (trigger rule) did not change; the no-roles reading is new coverage (before, only with-roles ran). True reason: measured on 16.15, both end at the trigger rule.
- test_the_o8_wording_check_* (all params): helper `states_its_condition` is in the test file. Killed by V129 (the old half-condition restored: the "must not change owner during the run" form is accepted again).
- test_the_postgresql_17_wording_check_finds_each_new_form...: helper in the test file; killed by V126 (window cut to nothing).
- test_the_postgresql_17_wording_check_leaves_the_honest_sentences_alone: honest sentences must stay unflagged; passes on old and new by design (guards against over-flagging).
- test_connect_with_the_iam_sign_in_runs_one_statement_and_adds_only_the_password: unchanged behaviour; killed by V120 (re-pointed to the new line).
- test_a_session_ended_by_the_idle_in_transaction_timeout_while_a_file_runs_...: only the timing margin changed (1 s limit, 6 s wait); the behaviour is the same on old code.
- test_the_refusal_names_the_sqlstate_of_a_session_ending_error[25P03] and [25P04]: the old code already printed the code; the test pins it. Killed by V124 (class name printed instead).
