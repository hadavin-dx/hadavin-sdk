Status: fresh review of the E1 code (lead order); fixed by d-fix9 (e1-fix2). No Blocker; 4 Major, 2 test gaps, 2 nits.
| id | decision | action |
|---|---|---|
| M1 | FIXED | `_build_app`, `_recover`, `_prepare` close the Runner and the App's stores (`_close_app`) on every non-success path; tests `test_fix2_recover_closes_the_store_on_every_failed_try`, `test_fix2_build_app_closes_the_store_when_it_fails_after_build[make_app|check_tick]`, `test_fix2_prepare_closes_the_store_when_the_server_cannot_be_made` |
| M2 | FIXED | `Runner.health` assigns `_ping` after `thread.start()`; a start failure is a counted 503; `test_fix2_a_ping_thread_that_does_not_start_is_a_counted_503_and_the_next_call_works` |
| M3 | FIXED | conflict audit write on a daemon thread, 2 s wait (`AUDIT_WRITE_TIMEOUT_S`), one pending write, the rest counted and warned; `test_fix2_a_blocked_audit_write_costs_the_409_at_most_2_s_and_one_write_is_pending` |
| M4 | FIXED | 5 consecutive non-store re-check failures stop the worker, exit 3, WARNING with the class (`DEGRADED_FATAL_AFTER`); store-down retries forever; `test_fix2_five_non_store_failures_in_a_row_stop_the_worker_with_exit_3`, `test_fix2_store_down_failures_retry_forever_and_reset_the_count` |
| G5 | FIXED | `test_fix2_an_unsigned_or_wrongly_signed_conflicting_document_writes_no_event`; 401 step added to `test_e1_health_needs_no_signature_and_leaks_nothing` |
| G6 | FIXED | `test_fix2_the_cap_is_per_sender_and_the_window_dict_is_bounded_by_the_senders` |
| N1 | FIXED | degraded socket timeout = configured `ack_wait_s` + `SOCKET_SLACK_S` (`_ack_wait_of`); `test_fix2_the_degraded_socket_timeout_is_the_configured_ack_wait_plus_slack` |
| N2 | FIXED | `Runner` docstring: `store_failures` restarts after the swap; concurrent health callers on one hung ping each count a failure |
