# Evidence batch 11: full suite on cloud/core-b

- Head sha: `763d71c42` (`git rev-parse --short HEAD` after `git pull origin cloud/core-b`, which reported "Already up to date.")
- Branch: `cloud/core-b`
- Database: `hadavin_test_ev11` on `127.0.0.1:55439` (created fresh for this run)
- Command (run once, in background, output to `/tmp/claude-0/ev11.log`):

```
HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test_ev11 uv run --all-extras --group test pytest -q -p no:cacheprovider -n 2 --ignore=tests/demo_askdata
```

- Pytest summary line (verbatim): `43 failed, 12593 passed, 12 skipped, 2 xfailed, 2 errors in 888.96s (0:14:48)`

| Outcome | Count |
|---|---|
| passed | 12593 |
| failed | 43 |
| skipped | 12 |
| xfailed | 2 |
| errors | 2 |

Failure and error entries below: test id from the log's short summary; the last `E` line copied verbatim from that test's section of the log.

## Failures and errors

- FAILED `tests/test_k1b_cli.py::test_end_to_end_replay_then_score`

  ```text
  E         ?    ^     ^   ^   ^    ^)
  ```

- FAILED `tests/test_p5p6_followups.py::test_the_shared_retry_helper_names_no_vendor`

  ```text
  E             ...Full output truncated, use '-vv' to show
  ```

- FAILED `tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_spend]`

  ```text
  E           DETAIL:  Failing row contains (agent-a, 2025-01-31, -0.5).
  ```

- FAILED `tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[trigger_removed_all_counters]`

  ```text
  E           DETAIL:  Failing row contains (agent-a, 2025-01-31, -0.5).
  ```

- FAILED `tests/test_money_guard_mutants.py::test_the_attack_battery_kills_every_mutant_of_the_guard[release_owner_check_removed]`

  ```text
  E           DETAIL:  Failing row contains (agent-a, 2025-01-31, -0.5).
  ```

- FAILED `tests/test_stop_state_roles.py::test_e7_a_flag_on_before_0006_stays_on_after_the_upgrade`

  ```text
  E           hadavin_sdk.errors.ConfigError: migrations are inconsistent: GRANTS names hadavin_caps, which no migration creates; GRANTS names hadavin_limits, which no migration creates; FUNCTION_GRANTS names hadavin_add_spend(text, date, numeric), which no migration creates; FUNCTION_GRANTS names hadavin_cap_matches(text, numeric, numeric), which no migration creates; FUNCTION_GRANTS names hadavin_expire_spend_reservations(integer), which no migration creates; FUNCTION_GRANTS names hadavin_purge_spend_reservations(timestamptz), which no migration creates; FUNCTION_GRANTS names hadavin_release_expired_spend(text, date), which no migration creates; FUNCTION_GRANTS names hadavin_reserve_spend(text, text, date, numeric, text), which no migration creates; FUNCTION_GRANTS names hadavin_set_cap(text, numeric, numeric, text), which no migration creates; FUNCTION_GRANTS names hadavin_settle_spend(text, numeric, text), which no migration creates
  ```

- FAILED `tests/test_stop_state_roles.py::test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner`

  ```text
  E         Actual message: 'sb_mo_62ce275702 is a member of postgres, the owner of the hadavin_* functions: remove the membership'
  ```

- FAILED `tests/test_stop_state_roles.py::test_e9_a_stop_state_that_turns_unreadable_at_any_later_read_means_no_card_and_no_action`

  ```text
  E             Use -v to get more diff
  ```

- FAILED `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`

  ```text
  E       assert not ["handover/BRIEF-PREAMBLE.md: '[vendor string]'", "handover/core-b/board-body.md: '[vendor string]'", "handover/core-b/STATUS-BOARD.md...over/core-b/inputs/evidence-bpg.md: '[vendor string]'", "handover/core-b/inputs/evidence-bpg-first-error-lines.txt: '[vendor string]'"]
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_migrate_refuses_a_member_of_the_reset_role[LOGIN]`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_mb_45ac804451 (not named in this command) can run hadavin_set_cap(text, numeric, numeric, text); role sb_mb_45ac804451 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_roles_of_the_server_with_no_grant_on_these_relations_are_not_listed`

  ```text
  E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_4021700989 can DELETE spend; role sb_wa_4021700989 can INSERT spend; role sb_wa_4021700989 can UPDATE spend; role sb_wa_4021700989 can DELETE spend_month; role sb_wa_4021700989 can INSERT spend_month; role sb_wa_4021700989 can UPDATE spend_month; role sb_wa_4021700989 can DELETE spend_reservations; role sb_wa_4021700989 can INSERT spend_reservations; role sb_wa_4021700989 can UPDATE spend_reservations
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_a_second_schema_with_its_own_stop_tables_and_roles_does_not_change_this_schemas_answer`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_y5_7349ea052d (not named in this command) can run hadavin_set_cap(text, numeric, numeric, text); role sb_y5_7349ea052d (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_a_grant_to_public_is_listed_as_public`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_rt_db1af1ca4e (not named in this command) can run hadavin_reserve_spend(text, text, date, numeric, text); role sb_rt_db1af1ca4e (not named in this command) can run hadavin_settle_spend(text, numeric, text); role sb_rt_db1af1ca4e (not named in this command) can run hadavin_expire_spend_reservations(integer); role sb_pu_db1af1ca4e (not named in this command) can run hadavin_purge_spend_reservations(timestamptz); role sb_rt_db1af1ca4e (not named in this command) can run hadavin_add_spend(text, date, numeric); role sb_rt_db1af1ca4e (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_an_untouched_log_verifies_and_is_fully_signed`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_rows_cannot_be_updated_or_deleted_through_sql`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_an_edited_row_is_found`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_deleted_row_is_found`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_rewriting_a_row_and_recomputing_every_later_hash_is_caught_by_the_signature`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_checkpoint_signed_with_another_key_is_rejected`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_cutting_the_tail_but_keeping_its_checkpoint_is_found`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_rows_after_the_last_checkpoint_are_reported_as_unsigned`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_checkpoint_is_written_automatically_every_n_rows`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_damaged_database_is_a_finding_not_a_crash`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_audit_verify_exits_0_when_intact_and_1_when_tampered`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_history_rewritten_and_re_signed_with_the_key_is_caught_by_its_anchors`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_checkpoint_that_was_never_anchored_or_an_anchor_with_no_checkpoint_is_reported`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_checkpoints_are_signed_by_kms_and_verify_with_its_public_key`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_appends_and_reads_from_many_threads_keep_one_whole_chain`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_each_anchor_is_locked_dated_and_never_overwritten`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_deleted_tail_is_detected_against_the_anchor`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_checkpoint_that_cannot_be_signed_or_anchored_fails_open_and_is_retried`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_an_outcome_that_cannot_be_appended_waits_in_the_outbox`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_a_new_event_does_not_overtake_a_parked_outcome`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_an_unsigned_chain_still_verifies_its_links`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_postgres_chain_appends_verifies_and_refuses_update_delete_truncate`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_postgres_appends_from_many_threads_keep_one_whole_chain`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/warden_port/test_audit_chain.py::test_the_runtime_role_writes_and_reads_the_chain_but_cannot_rewrite_it`

  ```text
  E           For further information visit https://errors.pydantic.dev/2.14/v/string_pattern_mismatch
  ```

- FAILED `tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[oserror]`

  ```text
  E   AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_9d9d4f766f (not named in this command) can run hadavin_purge_spend_reservations(timestamptz)\n' and 'sb_x4_9d9d4f766f' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_9d9d4f766f (not named in this command) can run hadavin_purge_spend_reservations(timestamptz)\n')
  ```

- FAILED `tests/test_stop_state_roles.py::test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[closed]`

  ```text
  E   AssertionError: assert ('refused:' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_144f29162a (not named in this command) can run hadavin_purge_spend_reservations(timestamptz)\n' and 'sb_x4_144f29162a' in 'refused: roles not named in this command can run the money functions, or will for future functions: role sb_pu_144f29162a (not named in this command) can run hadavin_purge_spend_reservations(timestamptz)\n')
  ```

- FAILED `tests/test_stop_state_roles.py::test_cli_migrate_prints_the_accepted_admin_roles_when_it_refuses_too`

  ```text
  E        +  where 'the hadavin_* functions are owned by a superuser: allowed (test servers and some managed services), but a superuser owner is a wider key than a plain owner role\n' = CaptureResult(out='the hadavin_* functions are owned by a superuser: allowed (test servers and some managed services),... functions: role sb_pu_38f713e2b4 (not named in this command) can run hadavin_purge_spend_reservations(timestamptz)\n').out
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_migrate_naming_only_the_runtime_role_refuses_the_reset_role_of_an_earlier_call`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_pu_aa459132e6 (not named in this command) can run hadavin_purge_spend_reservations(timestamptz); role sb_rs_aa459132e6 (not named in this command) can run hadavin_set_cap(text, numeric, numeric, text); role sb_rs_aa459132e6 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[portal_role]`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_rt_e006e6eba5 (not named in this command) can run hadavin_reserve_spend(text, text, date, numeric, text); role sb_rt_e006e6eba5 (not named in this command) can run hadavin_settle_spend(text, numeric, text); role sb_rt_e006e6eba5 (not named in this command) can run hadavin_expire_spend_reservations(integer); role sb_pu_e006e6eba5 (not named in this command) can run hadavin_purge_spend_reservations(timestamptz); role sb_rt_e006e6eba5 (not named in this command) can run hadavin_add_spend(text, date, numeric); role sb_rs_e006e6eba5 (not named in this command) can run hadavin_set_cap(text, numeric, numeric, text); role sb_rs_e006e6eba5 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric); role sb_rt_e006e6eba5 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- FAILED `tests/test_stop_state_roles.py::test_s2_migrate_naming_one_other_role_runs_the_same_check[purge_role]`

  ```text
  E     Actual message: 'roles not named in this command can run the money functions, or will for future functions: role sb_rt_5a7ac8c123 (not named in this command) can run hadavin_reserve_spend(text, text, date, numeric, text); role sb_rt_5a7ac8c123 (not named in this command) can run hadavin_settle_spend(text, numeric, text); role sb_rt_5a7ac8c123 (not named in this command) can run hadavin_expire_spend_reservations(integer); role sb_rt_5a7ac8c123 (not named in this command) can run hadavin_add_spend(text, date, numeric); role sb_rs_5a7ac8c123 (not named in this command) can run hadavin_set_cap(text, numeric, numeric, text); role sb_rs_5a7ac8c123 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric); role sb_rt_5a7ac8c123 (not named in this command) can run hadavin_cap_matches(text, numeric, numeric)'
  ```

- ERROR `tests/contracts/test_store.py::test_redaction_map_upserts_and_a_missing_map_is_none[postgres]`

  ```text
  E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_537e2e1870 can DELETE spend; role sb_wa_537e2e1870 can INSERT spend; role sb_wa_537e2e1870 can UPDATE spend; role sb_wa_537e2e1870 can DELETE spend_month; role sb_wa_537e2e1870 can INSERT spend_month; role sb_wa_537e2e1870 can UPDATE spend_month; role sb_wa_537e2e1870 can DELETE spend_reservations; role sb_wa_537e2e1870 can INSERT spend_reservations; role sb_wa_537e2e1870 can UPDATE spend_reservations
  ```

- ERROR `tests/contracts/test_store_spend_ids_caps.py::test_limits_reserve_keeps_the_key_error_of_an_unknown_hashable_agent[postgres-b'x']`

  ```text
  E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_86b0b63b21 can DELETE spend; role sb_wa_86b0b63b21 can INSERT spend; role sb_wa_86b0b63b21 can UPDATE spend; role sb_wa_86b0b63b21 can DELETE spend_month; role sb_wa_86b0b63b21 can INSERT spend_month; role sb_wa_86b0b63b21 can UPDATE spend_month; role sb_wa_86b0b63b21 can DELETE spend_reservations; role sb_wa_86b0b63b21 can INSERT spend_reservations; role sb_wa_86b0b63b21 can UPDATE spend_reservations
  ```
