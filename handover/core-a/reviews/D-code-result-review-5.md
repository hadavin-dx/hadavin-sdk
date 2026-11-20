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

## Round 2 (fresh, egm-design): NO Blocker, 1 Major (arguable), 3 Nits. The 4 round-1 Majors are fixed; each new test fails on revert (the unsigned test is a regression guard).
| id | sev | finding | category | action |
|---|---|---|---|---|
| E1b-1 | Major (arguable) | _recover turns every failed ping into StoreUnavailable: a store that REFUSES (missing table/grant/schema) is counted as store-down, retried forever, cause logged only at DEBUG: M4 does not cover it | PROPOSE FIX | _Ping keeps the exception class; a non-connectivity cause re-raises and counts toward DEGRADED_FATAL_AFTER; the class is logged at WARNING |
| E1b-2 | Nit | _audit_pending set before _conflict_event(...) which is outside the try: if it raised the flag stays True | PROPOSE FIX | build the event first |
| E1b-3 | Nit | late runner.close(0) after a stop skips _close_app | PROPOSE FIX | close the app in the same branch |
| E1b-4 | Nit | closing the PG connection while a timed-out ping thread may be in get_run on it | DECLINE | psycopg behaviour not verified; the ping thread catches the error; process exiting anyway |
Fixes (e1-fix3) wait for mutant run 17 (it reads worker.py).

## Round 3 (fresh, codebase-details): NO Blocker, 1 arguable Major, nits; CHURN
| id | sev | finding | category | action |
|---|---|---|---|---|
| E1c-1 | Major (arguable) | `_is_store_down`/`main` inherit 'any OSError = connectivity': a typo'd secret/registry path (FileNotFoundError, PermissionError) is retried forever in degraded mode, never exit 3 | CHURN (see below) | resolved by deleting the fatal-after-5 machinery |
| E1c-2 | Nit | with_traceback(None) leaves __context__ chains; _ping_error unlocked | resolved by the same deletion (no stored cause) | |
| E1c-3 | Nit | a store down for hours shows only the /health counter | PROPOSE FIX | one WARNING (class name only) per 5 minutes while down |
| E1c-4..6 | Nit | ping thread per hung re-check; owned_app not closed on normal shutdown; stop_server thread | DECLINE | bounded; process exits |
Churn (EGM rule: a new finding is at the scope of an applied fix and reverting that fix would resolve it): rounds 2 and 3 both found problems INSIDE the 'fatal after 5 non-store failures -> exit 3' machinery that round 1 asked for (M4). The lead's verdict (E1b) asks only for '/health 503 plus a counter while the store is down; no exit 4'; the machinery is not in it (about 35 lines: DEGRADED_FATAL_AFTER, the `other` counter, _is_store_down, _Ping.cause, Runner._ping_error/ping_error, `raise cause` in _recover). DECISION (reversible, mine): delete it; `_watch` retries every error forever, logs the exception CLASS once per 5 minutes at WARNING, /health stays 503 + counter. Cost: a permanent schema/grant/path fault shows as /health 503 + the periodic WARNING, never as a process exit; the supervisor/operator reads /health. If the lead wants exit 3 back: say so, and the E1c-1 fix (not-store-down for FileNotFoundError/PermissionError/IsADirectoryError/NotADirectoryError, same helper in main) is the way.
