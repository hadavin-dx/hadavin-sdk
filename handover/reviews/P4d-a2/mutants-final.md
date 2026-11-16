heavy slot 3
| mutant | result | killed by |
|---|---|---|
| w01 memory save_plan: plan_id check dropped | KILLED | tests/contracts/test_store_hostile.py::test_a_plan_id_used_by_another_run_is_stale_state_and_the_first_plan_stays[memory] |
| w02 map: UniqueViolation unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[23505-StaleState] |
| w03 map: ForeignKeyViolation unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[23503-NotFound] |
| w04 map: CheckViolation unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[23514-ValueError] |
| w04b map: DataError unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[22021-ValueError] |
| w04c map: ProgramLimitExceeded unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[54000-ValueError] |
| w05 map: QueryCanceled unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[57014-StoreBusy] |
| w05b map: LockNotAvailable unmapped | KILLED | tests/contracts/test_store_writes_pg.py::test_driver_errors_become_protocol_errors[55P03-StoreBusy] |
| w06 retry widened to 40003 | KILLED | tests/contracts/test_store_writes_pg.py::test_connection_schema_privilege_and_unknown_outcome_errors_pass_through_unchanged[40003] |
| w06b retry only 40P01 | KILLED | tests/contracts/test_store_writes_pg.py::test_a_deadlock_or_serialization_failure_is_retried_and_counted[40001-1] |
| w07 retry applied to keyless writes (attempts) | KILLED | tests/contracts/test_store_writes_pg.py::test_a_keyless_write_raises_store_busy_at_once_with_no_retry[40P01] |
| w07c four attempts | KILLED | tests/contracts/test_store_writes_pg.py::test_three_attempts_at_most_then_store_busy |
| w07d two attempts | KILLED | tests/contracts/test_store_writes_pg.py::test_a_deadlock_or_serialization_failure_is_retried_and_counted[40P01-2] |
| w08a lock_timeout not set | KILLED | tests/contracts/test_store_writes_pg.py::test_a_lock_that_is_never_released_gives_store_busy_for_three_kinds_of_write[T1-lock-timeout-100] |
| w08b statement_timeout not set | KILLED | tests/contracts/test_store_writes_pg.py::test_T3_both_timeouts_are_set_on_the_connection_and_shrink_on_a_retry |
| w08c remaining budget ignored | KILLED | tests/contracts/test_store_writes_pg.py::test_T3_both_timeouts_are_set_on_the_connection_and_shrink_on_a_retry |
| w08c2 statement_timeout not shrunk | KILLED | tests/contracts/test_store_writes_pg.py::test_T3_both_timeouts_are_set_on_the_connection_and_shrink_on_a_retry |
| w08d set_config given an int | KILLED | tests/contracts/test_store_writes_pg.py::test_a_lock_that_is_never_released_gives_store_busy_for_three_kinds_of_write[T1-lock-timeout-100] |
| w08e back-off sleep under the lock | KILLED | tests/contracts/test_store_writes_pg.py::test_the_retry_sleep_holds_neither_the_lock_nor_a_transaction |
| w08f budget check left < 0 | KILLED | tests/contracts/test_store_writes_pg.py::test_a_spent_budget_is_store_busy_before_anything_is_sent |
| w09 memory list_approvals tie-break lost | KILLED | tests/contracts/test_store_hostile.py::test_list_approvals_is_oldest_first_with_the_id_as_tie_break[memory] |
| w09b pg list_approvals tie-break lost | KILLED | tests/contracts/test_store_hostile.py::test_list_approvals_is_oldest_first_with_the_id_as_tie_break[postgres] |
| w10 check_text skips dict keys | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[memory-nul] |
| w10b check_text skips lists | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[memory-nul] |
| w10c check_text skips floats | KILLED | tests/contracts/test_store_hostile.py::test_non_finite_floats_in_nested_data_are_refused[memory] |
| w10d check_text skips surrogates | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[memory-lone-high-surrogate] |
| w10e check_text skips NUL | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[memory-nul] |
| w10f pg wrapper scans models only (no str args) | SURVIVED |  |
| w10h pg wrapper scans nothing | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[postgres-lone-high-surrogate] |
| w10g memory transition skips reason_code scan | KILLED | tests/contracts/test_store_hostile.py::test_nul_and_lone_surrogates_are_refused_in_any_text_field[memory-nul] |
| w13 RLock back to Lock | KILLED | tests/contracts/test_store_writes_pg.py::test_a_wrapped_write_called_from_inside_another_joins_its_transaction_and_budget |
| w14 deadline check removed from _exec | KILLED | tests/contracts/test_store_writes_pg.py::test_T4_a_statement_is_not_sent_after_the_budget_is_spent |
| w15 nested wrapped call opens its own transaction | KILLED | tests/contracts/test_store_writes_pg.py::test_a_wrapped_write_called_from_inside_another_joins_its_transaction_and_budget |
| w16b is_connectivity: sqlstates not excluded | KILLED | tests/contracts/test_store_writes_pg.py::test_sqlstates_of_an_answering_server_are_not_connectivity[40001] |
| w17 check_step_name uses re.match with $ | KILLED | tests/contracts/test_store_hostile.py::test_a_bad_tick_step_is_refused[memory-abc\n] |
| w18 memory tick step unchecked | KILLED | tests/contracts/test_store_hostile.py::test_a_bad_tick_step_is_refused[memory-abc\n] |
| w19 on_retry never called | KILLED | tests/contracts/test_store_writes_pg.py::test_a_deadlock_or_serialization_failure_is_retried_and_counted[40P01-1] |
| w20 on_retry given the wrong attempt | KILLED | tests/contracts/test_store_writes_pg.py::test_a_deadlock_or_serialization_failure_is_retried_and_counted[40P01-1] |
| w21 build ignores the settings | KILLED | tests/contracts/test_store_writes_pg.py::test_build_passes_the_settings_to_the_store |
| w22 deadline not cleared after an attempt | KILLED | tests/contracts/test_store_writes_pg.py::test_a_wrapped_write_called_from_inside_another_joins_its_transaction_and_budget |
| w23 retried 40001/40P01 exhausted passes the raw error | KILLED | tests/contracts/test_store_writes_pg.py::test_three_attempts_at_most_then_store_busy |
