# P3a-2 evidence (builder, Sonnet 5.5). Head SHA: 659f9e301440bc1b8e268db89d31537850445f51 on branch core/P3a-2 (base core/P3a = 7155fb4, PR 68 head)

Run on Linux, PostgreSQL 16 (own throwaway server, port 55437, three databases p3a_2 / p3a_2b / p3a_2m). PostgreSQL 17 NOT run. No model call, no spend.

## What failed or was not run (first)
- Full suite py3.13 at the head: 1 failed, 10273 passed, 1 skipped. py3.12: 1 failed, 10273 passed, 1 skipped. The 1 failure is tests/demo_askdata/test_validate_harm.py::...[dblink-connect]: my throwaway server has no server-side default socket and port 5432, so the attack's dblink_connect('dbname=postgres') cannot connect and the test cannot show harm. The same test fails on the BASE commit 7155fb4 with the same server (command below). Not caused by this change; NOT proven green here. The 1 skip is tests/contracts/test_llm.py:95 (stubber), also on base.
- An earlier full run (kept as pytest-first-run-py312-default-env.txt) was py3.12 by mistake (uv default) and had 2 failures: the dblink one and one COPY ... TO PROGRAM 'Broken pipe' in the same file; the second did not recur in 3 later runs, so it looks like a flake of my server; unexplained.
- Not built (not this PR): the layer 1 previous-release comparer (P3a-3, CUT-TO-CONFIG+GLUE by BN-20), the recipe and CHANGELOG runbook cases (deferred by order 74(b), P3a-1 fix1), the real psql test, CI changes (lead), PostgreSQL 17 run. The downgrade-read test is my reading of the ticket (see BN.md item 4).
- Ticket mutants M63, M72-M86 (lexer/recipe), M99-M100 are not in this PR; the ticket count (124) is not reproduced; my table has 36 mutants.
- Perf-marked tests (-m perf) were NOT run (the ticket runs the timing test alone in command 3b; it belongs to P3a-1).

## Commands and output tails
```
$ uv run --all-extras --group test ruff check src tests
All checks passed!
ruff check rc=0
$ uv run --all-extras --group test ruff format --check src tests
277 files already formatted
ruff format rc=0
$ uvx bandit -ll -q -r src   (only nosec warnings, no Issue lines)
bandit -ll rc=0
Issue lines: 0
$ python tools/scan_repo.py

rc=0
$ HADAVIN_TEST_PG_DSN=.../p3a_2 <build-dir> uv run --python 3.13 --all-extras --group test pytest -q -m "not live and not perf" -p no:cacheprovider -rs
=========================== short test summary info ============================
SKIPPED [1] tests/contracts/test_llm.py:95: Stubber refuses a malformed Converse shape before the kind sees it
1 failed, 10273 passed, 1 skipped, 28 deselected in 367.02s (0:06:07)
$ HADAVIN_TEST_PG_DSN=.../p3a_2b <build-dir> uv run --python 3.12 --all-extras --group test pytest -q -m "not live and not perf" -p no:cacheprovider -rs
=========================== short test summary info ============================
SKIPPED [1] tests/contracts/test_llm.py:95: Stubber refuses a malformed Converse shape before the kind sees it
1 failed, 10273 passed, 1 skipped, 28 deselected in 274.73s (0:04:34)
```

## New tests (counts at the head)
```
........................................................................ [ 76%]
..................................................................       [100%]
282 passed in 9.15s
```
No skip in the new files (the -rs line above would list it).

## FAIL-BEFORE (new tests copied onto base 7155fb4 and run there; full output: fail-before.txt)
```
$ (in a worktree at 7155fb4 with the new test files and the one-line test_k2 edit) pytest -q -m "not live and not perf" tests/test_migration_wiring.py tests/test_migration_manifest.py tests/test_migration_postgres.py tests/test_migration_numbers.py tests/test_k2_migrations.py
47 failed, 189 passed, 2 deselected in 6.06s
47
```
Ticket FAIL-BEFORE items on the base: 1 test_late_number_is_refused (DID NOT RAISE), 2 test_unicode_digit_names_are_refused, 3 test_uppercase_extension_is_refused, 4a test_directory_named_like_a_migration_is_refused, 4b test_dangling_link_is_refused, 5 test_commit_in_a_file_is_refused_before_connecting, 6 test_newer_database_message, 7 test_number_zero_is_refused, 8 test_scan_comment_ends_at_cr, 9 test_scan_double_dash_in_string: all in the FAILED list of fail-before.txt. Pin test test_scan_sees_create_inside_bodies_and_strings and the manifest tests pass on the base (by design: they pin old behaviour or are new).

FAILED list on base:
```
FAILED tests/test_migration_wiring.py::test_migrate_uses_the_one_implementation_of_each_rule
FAILED tests/test_migration_wiring.py::test_unicode_digit_names_are_refused
FAILED tests/test_migration_wiring.py::test_uppercase_extension_is_refused - ...
FAILED tests/test_migration_wiring.py::test_number_zero_is_refused - Assertio...
FAILED tests/test_migration_wiring.py::test_dangling_link_is_refused - Assert...
FAILED tests/test_migration_wiring.py::test_directory_named_like_a_migration_is_refused
FAILED tests/test_migration_wiring.py::test_commit_in_a_file_is_refused_before_connecting
FAILED tests/test_migration_wiring.py::test_migrate_executes_the_text_it_scanned
FAILED tests/test_migration_wiring.py::test_late_file_is_refused_and_nothing_runs
FAILED tests/test_migration_wiring.py::test_gone_name_is_refused_with_the_old_phrase
FAILED tests/test_migration_wiring.py::test_clean_run_reads_before_each_file_insert
FAILED tests/test_migration_wiring.py::test_nothing_to_apply_reads_nothing - ...
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[current_user]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[session_user]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[session_replication_role]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[search_path]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[standard_conforming_strings]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[backslash_quote]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[client_encoding]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[transaction_timestamp]
FAILED tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[txid_current]
FAILED tests/test_migration_wiring.py::test_session_authorization_names_both_users
FAILED tests/test_migration_wiring.py::test_saved_users_that_differ_are_not_a_refusal
FAILED tests/test_migration_wiring.py::test_start_value_of_standard_conforming_strings_must_be_on
FAILED tests/test_migration_wiring.py::test_a_disabled_trigger_is_refused - A...
FAILED tests/test_migration_wiring.py::test_a_trigger_that_was_disabled_at_the_start_is_not_a_refusal
FAILED tests/test_migration_wiring.py::test_a_dropped_trigger_is_refused - At...
FAILED tests/test_migration_wiring.py::test_a_new_trigger_is_not_a_refusal_and_is_watched_from_then_on
FAILED tests/test_migration_wiring.py::test_trigger_query_reads_only_the_migration_schema
FAILED tests/test_migration_wiring.py::test_the_message_has_no_connection_string_and_escapes_names
FAILED tests/test_migration_postgres.py::test_late_number_is_refused - Failed...
FAILED tests/test_migration_postgres.py::test_newer_database_message - Assert...
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[backslash_quote]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[disable_trigger]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[drop_trigger]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[encoding]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[replica_trigger]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[replication_role]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[scs]
FAILED tests/test_migration_postgres.py::test_h11_the_read_back_refuses_a_planted_file[search_path]
FAILED tests/test_migration_postgres.py::test_h11_a_role_switched_inside_a_file_is_refused
FAILED tests/test_migration_postgres.py::test_h11_same_run_a_drop_in_the_first_run_leaves_no_ledger
FAILED tests/test_migration_postgres.py::test_a_hidden_commit_is_found_by_the_transaction_backstop
FAILED tests/test_migration_postgres.py::test_a_session_that_reads_strings_the_old_way_is_refused_before_any_file
FAILED tests/test_migration_numbers.py::test_scan_comment_ends_at_cr - Assert...
FAILED tests/test_migration_numbers.py::test_scan_double_dash_in_string - Ass...
FAILED tests/test_migration_numbers.py::test_scan_reads_the_given_text_not_the_file
```

## Base-failure proof for the one remaining full-suite failure
```
$ (worktree at 7155fb4) HADAVIN_TEST_PG_DSN=.../p3a_2 uv run --all-extras --group test pytest -q tests/demo_askdata/test_validate_harm.py
1 failed, 252 passed   (FAILED ...[dblink-connect])
```

## Mutation run (mutants.py; one text change at a time on a copy of the tree at the head; targeted files: wiring, postgres, manifest, numbers, k2, k5_fixes1, k5_fixes2)
36 mutants, 36 KILLED, 0 survived, 0 not applied. Baseline 279 passed. (A first run at e6ddf18 showed 2 problems, both fixed in the tests: MW3 survived until the directory test asserted MigrationNumberError; MW9 text did not match after the formatter changed the f-string. The run below is the single run at the head.)
```
heavy slot 3
BASELINE rc=0 279 passed, 3 deselected in 9.57s
M61 | read-back removed from migrate() | KILLED | 1 failed, 10 passed, 3 deselected in 0.39s
M62 | search_path not compared | KILLED | 1 failed, 15 passed, 3 deselected in 0.45s
M64 | read-back after the ledger INSERT | KILLED | 1 failed, 10 passed, 3 deselected in 0.50s
M65 | current_user compared with session_user | KILLED | 1 failed, 22 passed, 3 deselected in 0.41s
M66 | message omits the file name | KILLED | 1 failed, 12 passed, 3 deselected in 0.40s
M67 | read-back only after the last file | KILLED | 1 failed, 10 passed, 3 deselected in 0.45s
M70 | session_replication_role not compared | KILLED | 1 failed, 14 passed, 3 deselected in 0.42s
M71 | current_user not compared | KILLED | 1 failed, 12 passed, 3 deselected in 0.43s
M94 | session_user not compared | KILLED | 1 failed, 13 passed, 3 deselected in 0.40s
M91 | standard_conforming_strings not compared | KILLED | 1 failed, 16 passed, 3 deselected in 0.42s
M92 | backslash_quote not compared | KILLED | 1 failed, 17 passed, 3 deselected in 0.45s
M93 | client_encoding not compared | KILLED | 1 failed, 18 passed, 3 deselected in 0.41s
MB1 | transaction_timestamp not compared | KILLED | 1 failed, 19 passed, 3 deselected in 0.47s
MB2 | txid_current not compared | KILLED | 1 failed, 20 passed, 3 deselected in 0.49s
M88 | trigger state D/R check removed | KILLED | 1 failed, 24 passed, 3 deselected in 0.43s
M88b | trigger state: a trigger already D passes the same check wrongly (before None only) | KILLED | 1 failed, 24 passed, 3 deselected in 0.45s
M89 | saved trigger still exists: check removed | KILLED | 1 failed, 26 passed, 3 deselected in 0.54s
M90 | start check of standard_conforming_strings removed | KILLED | 1 failed, 23 passed, 3 deselected in 0.45s
M95 | saved values read after the first file | KILLED | 1 failed, 10 passed, 3 deselected in 0.47s
M101 | trigger baseline not refreshed | KILLED | 1 failed, 27 passed, 3 deselected in 0.45s
M102 | trigger query has no schema filter | KILLED | 1 failed, 28 passed, 3 deselected in 0.47s
M68 | _scan strips with the old regexes | KILLED | 1 failed, 188 passed, 3 deselected in 2.09s
M69 | _scan ignores the lexer problem | KILLED | 1 failed, 187 passed, 3 deselected in 1.95s
M87 | _scan reads the view with emptied quotes | KILLED | 1 failed, 189 passed, 3 deselected in 1.94s
MW1 | refusal list not applied in _scan | KILLED | 1 failed, 6 passed, 3 deselected in 0.56s
MW2 | migrate() reads the file again instead of the scanned text | KILLED | 1 failed, 7 passed, 3 deselected in 0.48s
MW3 | number problems raised as a plain ConfigError | KILLED | 1 failed, 5 passed, 3 deselected in 0.60s
MW4 | gone-name check removed | KILLED | 1 failed, 9 passed, 3 deselected in 0.44s
MW5 | late-file check removed | KILLED | 1 failed, 8 passed, 3 deselected in 0.46s
MW6 | check_grants scans without the shared text | KILLED | 1 failed, 7 passed, 3 deselected in 0.43s
MW7 | _migration_files uses the case-sensitive glob again | KILLED | 1 failed, 2 passed, 3 deselected in 0.41s
MW8 | lock key differs from the module constant | KILLED | 1 failed, 3 deselected in 0.39s
MW9 | no read-back message escapes (ESC survives) | KILLED | 1 failed, 12 passed, 3 deselected in 0.46s
MM1 | manifest: edited file not detected | KILLED | 1 failed, 52 passed, 3 deselected in 1.49s
MM2 | manifest: missing file not detected | KILLED | 1 failed, 53 passed, 3 deselected in 1.53s
MM3 | manifest: new file below released not detected | KILLED | 1 failed, 55 passed, 3 deselected in 1.58s
```

Killer per mutant group: M61/M62/M64-M67/M70/M71/M91-M94/MB1/MB2/M95: tests/test_migration_wiring.py stub cases (each value, order of reads vs INSERT, read before first file); M88/M88b/M89/M101/M102: trigger stub cases; M90: start-value case; M68/M69/M87: tests/test_migration_numbers.py scan tests; MW1-MW9: wiring tests; MM1-MM3: tests/test_migration_manifest.py. The timing/perf mutant M86 is not part of this PR.

## Rung table
See the PR body (KEEP-CODE rows only built: read-back after each file; wiring of the existing runner; manifest test is thin glue over hashlib).

## Load
Load average seen: 7.41 peak (other builders' jobs share the 4 cores); heavy slots were full for ~25 minutes, so wall-clock of the full runs includes queueing.

## Mutants and killers (head 66a5710, log mutants-final3.txt; baseline 346 passed)

36 mutants, 36 killed.

| id | mutation | status | killing test |
|---|---|---|---|
| M61 | read-back removed from migrate() | KILLED | tests/test_migration_wiring.py::test_clean_run_reads_before_each_file_insert |
| M62 | search_path not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[search_path] |
| M64 | read-back after the ledger INSERT | KILLED | tests/test_migration_wiring.py::test_clean_run_reads_before_each_file_insert |
| M65 | current_user compared with session_user | KILLED | tests/test_migration_wiring.py::test_saved_users_that_differ_are_not_a_refusal |
| M66 | message omits the file name | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[current_user] |
| M67 | read-back only after the last file | KILLED | tests/test_migration_wiring.py::test_clean_run_reads_before_each_file_insert |
| M70 | session_replication_role not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[session_replication_role] |
| M71 | current_user not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[current_user] |
| M94 | session_user not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[session_user] |
| M91 | standard_conforming_strings not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[standard_conforming_strings] |
| M92 | backslash_quote not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[backslash_quote] |
| M93 | client_encoding not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[client_encoding] |
| MB1 | transaction_timestamp not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[transaction_timestamp] |
| MB2 | txid_current not compared | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[txid_current] |
| M88 | trigger state D/R check removed | KILLED | tests/test_migration_wiring.py::test_a_disabled_trigger_is_refused |
| M88b | trigger state: a trigger already D passes the same check wrongly (before None only) | KILLED | tests/test_migration_wiring.py::test_a_disabled_trigger_is_refused |
| M89 | saved trigger still exists: check removed | KILLED | tests/test_migration_wiring.py::test_a_dropped_trigger_is_refused |
| M90 | start check of standard_conforming_strings removed | KILLED | tests/test_migration_wiring.py::test_start_value_of_standard_conforming_strings_must_be_on |
| M95 | saved values read after the first file | KILLED | tests/test_migration_wiring.py::test_clean_run_reads_before_each_file_insert |
| M101 | trigger baseline not refreshed | KILLED | tests/test_migration_wiring.py::test_a_new_trigger_is_not_a_refusal_and_is_watched_from_then_on |
| M102 | trigger query has no schema filter | KILLED | tests/test_migration_wiring.py::test_trigger_query_reads_only_the_migration_schema |
| M68 | _scan strips with the old regexes | KILLED | tests/test_migration_numbers.py::test_scan_double_dash_in_string |
| M69 | _scan ignores the lexer problem | KILLED | tests/test_migration_numbers.py::test_scan_comment_ends_at_cr |
| M87 | _scan reads the view with emptied quotes | KILLED | tests/test_migration_numbers.py::test_scan_sees_create_inside_bodies_and_strings |
| MW1 | refusal list not applied in _scan | KILLED | tests/test_migration_wiring.py::test_commit_in_a_file_is_refused_before_connecting |
| MW2 | migrate() reads the file again instead of the scanned text | KILLED | tests/test_migration_wiring.py::test_migrate_executes_the_text_it_scanned |
| MW3 | number problems raised as a plain ConfigError | KILLED | tests/test_migration_wiring.py::test_directory_named_like_a_migration_is_refused |
| MW4 | gone-name check removed | KILLED | tests/test_migration_wiring.py::test_gone_name_is_refused_with_the_old_phrase |
| MW5 | late-file check removed | KILLED | tests/test_migration_wiring.py::test_late_file_is_refused_and_nothing_runs |
| MW6 | check_grants scans without the shared text | KILLED | tests/test_migration_wiring.py::test_migrate_executes_the_text_it_scanned |
| MW7 | _migration_files uses the case-sensitive glob again | KILLED | tests/test_migration_wiring.py::test_uppercase_extension_is_refused |
| MW8 | lock key differs from the module constant | KILLED | tests/test_migration_wiring.py::test_migrate_uses_the_one_implementation_of_each_rule |
| MW9 | no read-back message escapes (ESC survives) | KILLED | tests/test_migration_wiring.py::test_each_value_is_compared_with_its_own_saved_value[current_user] |
| MM1 | manifest: edited file not detected | KILLED | tests/test_migration_numbers_fix1.py::test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number |
| MM2 | manifest: missing file not detected | KILLED | tests/test_migration_numbers_fix1.py::test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number |
| MM3 | manifest: new file below released not detected | KILLED | tests/test_migration_numbers_fix1.py::test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number |

Full suite py3.13 at 66a5710 (pytest-313-final2.txt, DSN set): 10341 passed, 1 skipped, 28 deselected, RC=0. Py3.12: first queue timed out (RC=99); requeued once as pytest-312-final3.txt.
Py3.12 at 66a5710 (pytest-312-final3.txt, DSN set): 10341 passed, 1 skipped, 28 deselected, RC=0.

Final at 967d5a1 (merge of core/P3a 606a9fe): py3.13 10438 passed 1 skipped RC=0 (pytest-313-final4.txt); py3.12 10438 passed 1 skipped RC=0 (pytest-312-final4.txt); mutants 36/36 killed RC=0 (mutants-final4.txt); bandit rc 0 (bandit-merge2.txt); ruff check + format clean, stage_names + stage_mutants 37/37 (targeted-merge2.txt).
