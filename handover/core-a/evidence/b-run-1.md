# b-run-1: core-b tests on PG16 (evidence only, no diagnosis)
core-b sha at /tmp/ca-b-run: ad70e50bf506f9f9b4fbaffa446d2a0ec4a03f04 (NOT the lead's 7e1b9750d; head differs)
PG: PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), 127.0.0.1:55433, superuser DSN, no psql-gated skips analysis done. uv run, Python via uv sync.

## Run 1: PG-gated set
cmd: cd /tmp/ca-b-run && HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55433/postgres uv run --all-extras --group test pytest -q -n 3 -rfE --no-header -p no:cacheprovider -m 'not perf and not live' tests/test_money_*.py tests/test_audit*.py tests/test_spend*.py tests/test_stop_state*.py tests/test_store*.py tests/test_limits_reserve.py tests/test_migrations_0009_0010_round2.py tests/contracts
(extra files tests/test_limits_reserve.py and tests/test_migrations_0009_0010_round2.py added because the lead's evidence names them)
load start: 14:41:21 up  9:22,  0 user,  load average: 0.25, 0.11, 0.17 | Fri Nov 20 14:41:21 UTC 2026
load end:   EXIT=1 WALL=390s |  14:47:51 up  9:29,  0 user,  load average: 3.24, 2.03, 1.05 | Fri Nov 20 14:47:51 UTC 2026
last 5 lines:
FAILED tests/contracts/test_store_spend_model.py::test_a_random_sequence_matches_the_model_after_every_call[postgres-seed23]
FAILED tests/contracts/test_store_spend_model.py::test_the_same_seed_gives_the_same_outcomes_on_memory_and_postgres[seed23]
ERROR tests/test_spend_reservations_pg.py::test_the_purge_login_is_denied[SELECT run_id FROM spend_reservations]
ERROR tests/test_spend_reservations_pg.py::test_the_portal_and_the_reset_login_hold_no_right_at_all[SELECT 1 FROM spend_reservations-reset]
23 failed, 2074 passed, 11 skipped, 2 xfailed, 2 errors in 383.29s (0:06:23)
counts: 23 failed, 2074 passed, 11 skipped, 2 xfailed, 2 errors, 383.29s
Failing/erroring ids with first E line:
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[f_reserve_p_day_cap_check_removed]
    E       AssertionError: mutant pattern did not match in reserve: (IF )[^;]*?( THEN\s+RAISE EXCEPTION 'invalid argument: p_day_cap')
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[f_reserve_p_month_cap_check_removed]
    E       AssertionError: mutant pattern did not match in reserve: (IF )[^;]*?( THEN\s+RAISE EXCEPTION 'invalid argument: p_month_cap')
- FAILED tests/test_stop_state_roles.py::test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner
    E           AssertionError: Regex pattern did not match.
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_day_cap_weakened]
    E       AssertionError: mutant pattern did not match in reserve: s\.usd < p_day_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_month_cap_weakened]
    E       AssertionError: mutant pattern did not match in reserve: m\.usd < p_month_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_sum_check_dropped_on_the_day]
    E       AssertionError: mutant pattern did not match in reserve:  AND s\.usd \+ p_usd <= p_day_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_month_cap_ignored]
    E       AssertionError: mutant pattern did not match in reserve: AND m\.usd < p_month_cap AND m\.usd \+ p_usd <= p_month_cap
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_refuses_a_member_of_the_reset_role[LOGIN]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_roles_of_the_server_with_no_grant_on_these_relations_are_not_listed
    E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_32f831b639 can DELETE spend; role sb_wa_32f831b639 can 
- FAILED tests/test_stop_state_roles.py::test_s2_a_second_schema_with_its_own_stop_tables_and_roles_does_not_change_this_schemas_answer
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_a_grant_to_public_is_listed_as_public
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_spend]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_all_counters]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[release_owner_check_removed]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[oserror]
    E       AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_5875125bb2 (not named in this command) can
- FAILED tests/test_stop_state_roles.py::test_e7_a_flag_on_before_0006_stays_on_after_the_upgrade
    E           hadavin_sdk.errors.ConfigError: migrations are inconsistent: GRANTS names hadavin_caps, which no migration creates; GRANTS names hadavin_limits, which no migration creates; FUNCTION_GRANTS
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[closed]
    E       AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_b4f47a8d26 (not named in this command) can
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_prints_the_accepted_admin_roles_when_it_refuses_too
    E       AssertionError: assert ('sb_ac3_f809f44ffc' in 'the hadavin_* functions are owned by a superuser: allowed (test servers and some managed services), but a superuser owner is a wider key than a 
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_only_the_runtime_role_refuses_the_reset_role_of_an_earlier_call
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[portal_role]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[purge_role]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/contracts/test_store_spend_model.py::test_a_random_sequence_matches_the_model_after_every_call[postgres-seed23]
    E           AssertionError: seed=23 op=0 ('expire', (), 0): outcome store=('ValueError',) model=('count', 0)
- FAILED tests/contracts/test_store_spend_model.py::test_the_same_seed_gives_the_same_outcomes_on_memory_and_postgres[seed23]
    E           AssertionError: seed=23 op=0 ('expire', (), 0): outcome memory=('count', 0) postgres=('ValueError',)
- ERROR tests/test_spend_reservations_pg.py::test_the_purge_login_is_denied[SELECT run_id FROM spend_reservations]
    E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_member_417a62ca1c can DELETE spend; role sb_member_417a62c
- ERROR tests/test_spend_reservations_pg.py::test_the_portal_and_the_reset_login_hold_no_right_at_all[SELECT 1 FROM spend_reservations-reset]
    E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_32f831b639 can DELETE spend; role sb_wa_32f831b639 can 

## Run 2: whole suite
cmd: same flags, no file list.
load start: 14:48:01 up  9:29,  0 user,  load average: 2.74, 1.96, 1.04 | Fri Nov 20 14:48:01 UTC 2026
load end:   EXIT=1 WALL=536s |  14:56:57 up  9:38,  0 user,  load average: 2.16, 2.70, 1.90 | Fri Nov 20 14:56:57 UTC 2026
last 5 lines:
FAILED tests/warden_port/test_audit_chain.py::test_postgres_appends_from_many_threads_keep_one_whole_chain
FAILED tests/warden_port/test_audit_chain.py::test_the_runtime_role_writes_and_reads_the_chain_but_cannot_rewrite_it
FAILED tests/test_stop_state_roles.py::test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner
ERROR tests/test_step_b_e7_migration_0009.py::test_planted_stop_years_are_refused[kill_switch_clears-20000-01-01]
51 failed, 13742 passed, 12 skipped, 18 xfailed, 1 error in 535.42s (0:08:55)
counts: 51 failed, 13742 passed, 12 skipped, 18 xfailed, 1 error, 535.42s
Failing/erroring ids with first E line:
- FAILED tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]
    E           psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection
- FAILED tests/test_k1b_cli.py::test_end_to_end_replay_then_score
    E       AssertionError: assert ('H=2_Hne=1_M=2_S=2_ic=1_ha=0' == 'H=2;Hne=1;M=2;S=2;ic=1;ha=0'
- FAILED tests/contracts/test_store_spend_model.py::test_a_random_sequence_matches_the_model_after_every_call[postgres-seed23]
    E           AssertionError: seed=23 op=0 ('expire', (), 0): outcome store=('ValueError',) model=('count', 0)
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_spend]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_all_counters]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[release_owner_check_removed]
    E           psycopg.errors.CheckViolation: new row for relation "spend" violates check constraint "spend_usd_range"
- FAILED tests/contracts/test_store_spend_model.py::test_the_same_seed_gives_the_same_outcomes_on_memory_and_postgres[seed23]
    E           AssertionError: seed=23 op=0 ('expire', (), 0): outcome memory=('count', 0) postgres=('ValueError',)
- FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
    E       AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: 'Port.io'; handover/core-b/board-body.md: 'Port.io'; handover/core-b/STATUS-BOARD.md: 'Port.i
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[f_reserve_p_day_cap_check_removed]
    E       AssertionError: mutant pattern did not match in reserve: (IF )[^;]*?( THEN\s+RAISE EXCEPTION 'invalid argument: p_day_cap')
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[f_reserve_p_month_cap_check_removed]
    E       AssertionError: mutant pattern did not match in reserve: (IF )[^;]*?( THEN\s+RAISE EXCEPTION 'invalid argument: p_month_cap')
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_day_cap_weakened]
    E       AssertionError: mutant pattern did not match in reserve: s\.usd < p_day_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_month_cap_weakened]
    E       AssertionError: mutant pattern did not match in reserve: m\.usd < p_month_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_sum_check_dropped_on_the_day]
    E       AssertionError: mutant pattern did not match in reserve:  AND s\.usd \+ p_usd <= p_day_cap
- FAILED tests/test_money_definer_mutants.py::test_the_battery_kills_every_mutant[i_month_cap_ignored]
    E       AssertionError: mutant pattern did not match in reserve: AND m\.usd < p_month_cap AND m\.usd \+ p_usd <= p_month_cap
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_refuses_a_member_of_the_reset_role[LOGIN]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_roles_of_the_server_with_no_grant_on_these_relations_are_not_listed
    E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_248d1c6719 can DELETE spend; role sb_wa_248d1c6719 can 
- FAILED tests/test_stop_state_roles.py::test_s2_a_second_schema_with_its_own_stop_tables_and_roles_does_not_change_this_schemas_answer
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_a_grant_to_public_is_listed_as_public
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_p5p6_followups.py::test_the_shared_retry_helper_names_no_vendor
    E           AssertionError: anthropic
- FAILED tests/test_stop_state_roles.py::test_e7_a_flag_on_before_0006_stays_on_after_the_upgrade
    E           hadavin_sdk.errors.ConfigError: migrations are inconsistent: GRANTS names hadavin_caps, which no migration creates; GRANTS names hadavin_limits, which no migration creates; FUNCTION_GRANTS
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[oserror]
    E       AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_f9ee53475c (not named in this command) can
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[closed]
    E       AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_302ee1b19a (not named in this command) can
- FAILED tests/test_stop_state_roles.py::test_cli_migrate_prints_the_accepted_admin_roles_when_it_refuses_too
    E       AssertionError: assert ('sb_ac3_52a69bb752' in 'the hadavin_* functions are owned by a superuser: allowed (test servers and some managed services), but a superuser owner is a wider key than a 
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_only_the_runtime_role_refuses_the_reset_role_of_an_earlier_call
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[portal_role]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[purge_role]
    E       AssertionError: Regex pattern did not match.
- FAILED tests/warden_port/test_audit_chain.py::test_an_untouched_log_verifies_and_is_fully_signed
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_rows_cannot_be_updated_or_deleted_through_sql
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_an_edited_row_is_found
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_deleted_row_is_found
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_rewriting_a_row_and_recomputing_every_later_hash_is_caught_by_the_signature
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_checkpoint_signed_with_another_key_is_rejected
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_cutting_the_tail_but_keeping_its_checkpoint_is_found
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_rows_after_the_last_checkpoint_are_reported_as_unsigned
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_checkpoint_is_written_automatically_every_n_rows
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_damaged_database_is_a_finding_not_a_crash
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_audit_verify_exits_0_when_intact_and_1_when_tampered
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_history_rewritten_and_re_signed_with_the_key_is_caught_by_its_anchors
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_checkpoint_that_was_never_anchored_or_an_anchor_with_no_checkpoint_is_reported
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_checkpoints_are_signed_by_kms_and_verify_with_its_public_key
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_appends_and_reads_from_many_threads_keep_one_whole_chain
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_each_anchor_is_locked_dated_and_never_overwritten
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_deleted_tail_is_detected_against_the_anchor
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_checkpoint_that_cannot_be_signed_or_anchored_fails_open_and_is_retried
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_an_outcome_that_cannot_be_appended_waits_in_the_outbox
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_a_new_event_does_not_overtake_a_parked_outcome
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_an_unsigned_chain_still_verifies_its_links
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_postgres_chain_appends_verifies_and_refuses_update_delete_truncate
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_postgres_appends_from_many_threads_keep_one_whole_chain
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/warden_port/test_audit_chain.py::test_the_runtime_role_writes_and_reads_the_chain_but_cannot_rewrite_it
    E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AuditEvent
- FAILED tests/test_stop_state_roles.py::test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner
    E           AssertionError: Regex pattern did not match.
- ERROR tests/test_step_b_e7_migration_0009.py::test_planted_stop_years_are_refused[kill_switch_clears-20000-01-01]
    E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_248d1c6719 can DELETE spend; role sb_wa_248d1c6719 can 

## collected? tests/test_money_definer*.py
Lead's 'battery not collected' does NOT reproduce here: no collection error; test_money_definer_pg.py and test_money_definer_mutants.py are collected and run. `pytest --co` tail:
tests/test_money_definer_static.py::test_postgres_py_calls_the_money_functions_schema_qualified_and_writes_no_money_table_itself
tests/test_money_definer_static.py::test_postgres_py_has_no_unqualified_call_of_any_hadavin_function

212 tests collected in 0.34s
Neither run printed 'too many values to unpack'.

## Side-by-side
Lead's failing ids (evidence-bpg.md, PG17/PG15 at 7e1b9750d) vs this run (PG16):
- test_money_definer_pg.py / _mutants.py collection ValueError (too many values to unpack): does not occur here (both files collected; see collected? note).
- test_audit_drain.py (n1,e6,e7,cross_process x2,f6_pg x2): does not occur here (no test_audit_drain failure in either run).
- test_spend_reservations_pg.py (6 failures: step order, longer-age, failing store, runtime-login expiry): does not occur here as failures; 2 NEW ERRORS here at setup (purge_login_is_denied, portal_and_reset_login_hold_no_right).
- test_stop_state_roles.py: migrate_refuses_reset_role_member_of_owner, s2_member_of_reset_role[LOGIN], s2_naming_one_other_role[portal_role], [purge_role], s2_grant_to_public_listed_as_public, e7_flag_on_before_0006, cli_migrate_prints_accepted_admin_roles: MATCH (same ids fail here). New here: s2_roles_no_grant_not_listed, s2_second_schema, cli_broken_stdout[oserror], [closed], s2_naming_only_runtime_role (listed in lead's evidence only as BASELINE FAILS for the mutants script, not as pytest ids).
- tests/contracts/test_store_spend_ids_caps.py (3: out-of-window cap day/month, exponent zero amount): does not occur here. test_store_spend_model[postgres-seed137] (PG17 only): does not occur here; NEW here: test_store_spend_model[postgres-seed23] and [seed23 same outcomes memory/postgres] ('expire' op=0 ValueError vs count 0).
- test_limits_reserve refusal_log_line, test_money_definer_review_fixes m2 header, test_migrations_0009_0010_round2 planted_ts: do not occur here.
- test_no_reference_material.py::test_no_vendor_brand_string_is_tracked: MATCHES (fails here, full run; now also handover/core-b/board-body.md 'Port.io').
- NEW here (not in lead's list): test_money_definer_mutants 6 ids (mutant pattern did not match in reserve), test_money_guard_mutants 3 ids (CheckViolation spend_usd_range), test_step_b_e7_migration_0009 planted_stop_years[kill_switch_clears-20000-01-01] ERROR, and full-run only: warden_port/test_audit_chain.py 24 (pydantic ValidationError for AuditEvent), demo_askdata test_validate_harm dblink-connect, test_k1b_cli end_to_end_replay_then_score, test_p5p6_followups shared_retry_helper_names_no_vendor.

Notes: no non-superuser login/second-database failure (tests created roles sb_* with superuser DSN). Logs: raw/b-run-1.log (run 1), raw/b-run-1-full.log (run 2).
