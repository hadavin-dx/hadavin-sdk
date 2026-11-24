# Batch 12: full-suite evidence run on the F-install integration branch

Evidence only. No code was changed, nothing was fixed, nothing was committed.

- Branch: `origin/wip/cloud-core-b/F-install`
- Commit (short): `8c5569fad` ("docs F-install: status, SECURITY.md spend-limits sentence follows the install")
- Run worktree: `/tmp/core-b-wt/EV12` (detached HEAD, removed after the run)
- Database: `hadavin_test_ev12` on `127.0.0.1:55439` (dropped after the run)
- Log: `/tmp/claude-0/ev12.log`

## Exact command

```
cd /tmp/core-b-wt/EV12 && PYTHONPATH=/tmp/core-b-wt/EV12/src HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test_ev12 /home/user/hadavin-sdk/.venv/bin/python -m pytest -q -p no:cacheprovider -n 2 --ignore=tests/demo_askdata
```

## Result

Final pytest line: `60 failed, 18589 passed, 14 skipped, 64 xfailed, 2 errors in 1539.09s (0:25:39)`

| Outcome | Count |
|---|---|
| passed | 18589 |
| failed | 60 |
| errors | 2 |
| skipped | 14 |
| xfailed | 64 |

## Failures and errors

Test ids are from the pytest short summary. The last error line is copied from each failure block in the log. Where the last `E` line is pytest's own truncation hint (`Use -v to get more diff`, `Full output truncated`), that text is copied as is and the real assertion is not in the log at this verbosity.

Known and expected failures per the brief: `tests/test_model_gate.py::test_no_error_the_adapters_raise_today_carries_the_mark` (core-c F3) and `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` (lead's files). Both appear in the table below.

| Outcome | Test id | Last error line |
|---|---|---|
| FAILED | `tests/test_model_cost_validation.py::test_reply_accepts_zero_and_twelve_places_and_refuses_none` | `E       Failed: DID NOT RAISE Exception` |
| FAILED | `tests/test_model_gate.py::test_no_error_the_adapters_raise_today_carries_the_mark` | `E        +    where ProviderError('x') = ProviderError('x')` |
| FAILED | `tests/test_money_context_everywhere.py::test_k1b_worst_case_usd` | `E       AttributeError: module 'hadavin_sdk.k1b.loop' has no attribute 'worst_case_usd'` |
| FAILED | `tests/test_money_context_everywhere.py::test_budget_spent_sum_and_settle_overshoot` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_context_everywhere.py::test_evals_cost_sum_and_division` | `E               hadavin_sdk.limits.SpendRefused: usd_cap` |
| FAILED | `tests/test_money_context_round5.py::test_k1b_worst_case_overflow_is_value_error` | `E           AttributeError: module 'hadavin_sdk.k1b.loop' has no attribute 'worst_case_usd'` |
| FAILED | `tests/test_money_context_round5.py::test_k1b_unpriceable_timeout_books_the_whole_cap` | `E           AttributeError: module 'hadavin_sdk.k1b.loop' has no attribute 'worst_case_usd'` |
| FAILED | `tests/test_grants_negative_0007.py::test_the_identities_are_the_four_this_file_knows` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_the_grant_row_gives_each_role_what_the_interface_states_and_no_more[purge]` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_the_grant_row_gives_each_role_what_the_interface_states_and_no_more[runtime]` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_the_grant_row_is_a_table_with_two_purge_columns_and_no_portal_read` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_nobody_may_truncate_and_only_the_purge_role_may_delete` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_each_role_is_refused_every_privilege_the_map_does_not_give[purge]` | `E                       Failed: purge was refused DELETE, which the map gives` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_each_role_is_refused_every_privilege_the_map_does_not_give[runtime]` | `E                       Failed: runtime was refused SELECT, which the map gives` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_column_rights_only_the_purge_role_reads_and_only_two_columns[purge]` | `E           psycopg.errors.InsufficientPrivilege: permission denied for table spend_reservations` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_the_catalog_agrees_for_every_role_privilege_and_column` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_the_purge_role_deletes_by_status_and_date_and_can_do_nothing_else` | `E           psycopg.errors.InsufficientPrivilege: permission denied for table spend_reservations` |
| FAILED | `tests/test_grants_negative_0007.py::test_pg_the_store_methods_are_refused_under_the_wrong_identity` | `E                   TypeError: PostgresStore.settle_spend() missing 1 required keyword-only argument: 'agent_id'` |
| FAILED | `tests/test_grants_negative_roles.py::test_the_identities_are_the_ones_this_file_knows` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_every_write_privilege_is_on_the_reviewed_list` | `E         ...Full output truncated, use '-vv' to show` |
| FAILED | `tests/test_grants_negative_roles.py::test_only_the_reviewed_roles_hold_anything_on_the_stop_state` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_delete_is_held_only_on_the_outbox_and_the_purged_tables` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_the_purge_role_holds_delete_only_and_no_whole_table_read` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_case10_the_released_manifest_names_every_migration_file` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_case2_the_reset_identity_holds_exactly_the_reviewed_cells` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_reset_writes_the_audit_intent_before_it_touches_the_switch` | `E       AttributeError: '_Recorder' object has no attribute 'open_stops'` |
| FAILED | `tests/test_grants_negative_roles.py::test_reset_leaves_the_switch_alone_when_the_audit_intent_fails` | `E       AttributeError: '_Recorder' object has no attribute 'open_stops'` |
| FAILED | `tests/test_grants_negative_roles.py::test_case8_a_reset_the_store_refuses_is_audited_as_reset_failed` | `E       AttributeError: '_Recorder' object has no attribute 'open_stops'` |
| FAILED | `tests/test_grants_negative_roles.py::test_case7_limits_reset_builds_its_store_and_audit_from_the_reset_dsn_only` | `E        +  where 2 = _limits_reset(PosixPath('/tmp/pytest-of-root/pytest-1911/popen-gw0/test_case7_limits_reset_builds0/pilot'), 'user:op')` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case2_the_reset_role_is_refused_everything_outside_its_reviewed_cells` | `E         Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case4_the_reset_role_switches_the_stop_off_and_the_runtime_role_can_stop_again` | `E               hadavin_sdk.errors.ConfigError: store postgres: this login holds rights on the stop tables that only the reset role may hold (UPDATE on kill_switch; INSERT on kill_switch_clears). A login that can write there can clear a stop. Revoke them from the login and from the roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login (it resets the grants and refuses what stays)` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case5_the_reset_role_appends_its_audit_intent_and_can_change_no_audit_row` | `E               hadavin_sdk.errors.ConfigError: store postgres: this login holds rights on the stop tables that only the reset role may hold (UPDATE on kill_switch; INSERT on kill_switch_clears). A login that can write there can clear a stop. Revoke them from the login and from the roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login (it resets the grants and refuses what stays)` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case8_reset_with_the_audit_intent_refused_leaves_the_stop_on` | `E               hadavin_sdk.errors.ConfigError: store postgres: this login holds rights on the stop tables that only the reset role may hold (UPDATE on kill_switch; INSERT on kill_switch_clears). A login that can write there can clear a stop. Revoke them from the login and from the roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login (it resets the grants and refuses what stays)` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case11_migrate_again_takes_back_what_was_granted_by_hand_to_the_reset_role` | `E             Use -v to get more diff` |
| FAILED | `tests/test_grants_negative_roles.py::test_pg_case12_a_reset_cannot_turn_a_missing_stop_row_into_off` | `E               hadavin_sdk.errors.ConfigError: store postgres: this login holds rights on the stop tables that only the reset role may hold (UPDATE on kill_switch; INSERT on kill_switch_clears). A login that can write there can clear a stop. Revoke them from the login and from the roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login (it resets the grants and refuses what stays)` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('-100')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('-0.000001')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('NaN')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('Infinity')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('-Infinity')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[Decimal('1E+9')]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[5]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount[0.5]` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_limits_charge_refuses_bad_amount['1']` | `E           AttributeError: 'Limits' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('-100')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('-0.000001')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('NaN')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('Infinity')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('-Infinity')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[Decimal('1E+9')]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[5]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount[0.5]` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_budget_charge_refuses_bad_amount['1']` | `E       AttributeError: 'Budget' object has no attribute 'charge'` |
| FAILED | `tests/test_money_store_round6.py::test_reply_missing_or_zero_tokens_still_estimated` | `E       TypeError: '>=' not supported between instances of 'NoneType' and 'int'` |
| FAILED | `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` | `E       assert not ["handover/BRIEF-PREAMBLE.md: 'Port.io'", "handover/core-b/inputs/evidence-bpg.md: 'Port.io'", "handover/core-b/inputs/evidence-bpg-first-error-lines.txt: 'Port.io'"]` |
| FAILED | `tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse` | `E               assert 'cyrillic a' in {'devanagari lines', 'e-acute lines'}` |
| FAILED | `tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[hex and dashes-redact]` | `E        +  where 0.25170269700004155 = max(0.25170269700004155, 0.001)` |
| FAILED | `tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[hex and dashes-redact_text]` | `E        +  where 0.29706638200002544 = max(0.29706638200002544, 0.001)` |
| FAILED | `tests/test_repo_rules.py::test_k5_no_transitive_import_of_actions_from_tools` | `E         Use -v to get more diff` |
| FAILED | `tests/test_textnorm_siblings.py::test_every_place_in_src_that_normalises_or_case_folds_text_is_recorded` | `E         Use -v to get more diff` |
| ERROR | `tests/contracts/test_store_spend.py::test_a_retry_with_the_same_arguments_succeeds_and_books_nothing_more[postgres]` | `E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_37ac664edc can DELETE spend; role sb_wa_37ac664edc can INSERT spend; role sb_wa_37ac664edc can UPDATE spend; role sb_wa_37ac664edc can DELETE spend_month; role sb_wa_37ac664edc can INSERT spend_month; role sb_wa_37ac664edc can UPDATE spend_month; role sb_wa_37ac664edc can DELETE spend_reservations; role sb_wa_37ac664edc can INSERT spend_reservations; role sb_wa_37ac664edc can UPDATE spend_reservations` |
| ERROR | `tests/test_money_definer_migrate.py::test_a_named_role_that_owns_the_functions_is_refused[reset]` | `E               hadavin_sdk.errors.ConfigError: a role other than the owner can write a money table (only the definer functions may): role sb_wa_3f0edc88a7 can DELETE spend; role sb_wa_3f0edc88a7 can INSERT spend; role sb_wa_3f0edc88a7 can UPDATE spend; role sb_wa_3f0edc88a7 can DELETE spend_month; role sb_wa_3f0edc88a7 can INSERT spend_month; role sb_wa_3f0edc88a7 can UPDATE spend_month; role sb_wa_3f0edc88a7 can DELETE spend_reservations; role sb_wa_3f0edc88a7 can INSERT spend_reservations; role sb_wa_3f0edc88a7 can UPDATE spend_reservations` |
