# evidence-mutants-19-run5 (facts only)
Tree: lead-mut19d (core-a a8e864606 + G33d anchor edit `now - last_warned` -> `at - last_warned`). WSL Ubuntu, CPython 3.13.12. Exit codes read from a script file (`echo EXIT=$?`).
1. Baseline `tests/endpoint_mutants.py G33d`: EXIT=0, 0 Traceback; `ok KILLED G33d ...`, `1 killed, 0 crash-accepted (), 0 known survivors`, `1 of 1 run are as expected; problems: []`.
   tests/test_mutants_anchors.py: `1 failed, 111 passed`: test_every_mutant_anchor_occurs_exactly_once[G33d] = `[XPASS(strict)] G33d anchor line 1255 pending the owner: now -> at` (the xfail(strict) marker for G33d now xpasses because of the lead's edit).
2. FULL script (12:17:55 to 12:21:48 UTC, 3 min 53 s): EXIT=1, 0 Traceback.
   `107 killed, 3 crash-accepted (G20j, G31, G32e), 0 known survivors`
   `110 of 111 run are as expected; problems: ['G15d the stalled-client refusal needs no request_version default']`
   Not as expected (1): `BAD SURVIVED G15d the stalled-client refusal needs no request_version default` (first line: empty).
   Exit code is 1 when the script reports a problem.
Cleanup: no container; WSL copy and temp logs removed; no processes left.
Last 25 lines of the full log and everything else: raw/run5.log.

## last 25 lines of the full log
```
ok  KILLED       G29b check_senders does not refuse a principal that is unknown  [test_d2_check_senders_refuses_a_bad_agent_or_principal[unknown-princip]
ok  KILLED       G29c check_senders does not refuse a principal that is not of kind service  [test_d2_check_senders_refuses_a_bad_agent_or_principal[principal-not-s]
ok  KILLED       G32a the per-minute cap of the 409 audit events is never reached  [test_e1_the_11th_conflict_in_a_minute_writes_no_event_but_is_still_409]
ok  KILLED       G32b the conflict event result carries the payload text  [test_e1_a_409_writes_one_audit_event_with_exactly_ids_and_both_hashes]
ok  KILLED       G32c the stored hash of the conflict event is taken from the new request  [test_e1_a_409_writes_one_audit_event_with_exactly_ids_and_both_hashes]
ok  KILLED       G32d the /health body gets an extra key  [test_e1_start_with_the_store_down_starts_and_health_is_503[StoreUnavai]
ok  CRASH        G32e /health is answered with no health callable (the path is not an ordinary 404)  [test_e1_without_a_health_callable_the_path_is_an_ordinary_404]
ok  KILLED       G32f the degraded worker never starts its re-check thread  [test_e1fix_a_worker_started_with_the_store_down_recovers_in_the_same_p]
ok  KILLED       G32g the recovery does not ping the store before it takes the real app  [test_e1fix_a_worker_started_with_the_store_down_recovers_in_the_same_p]
ok  KILLED       G32h Runner.health starts a new ping thread on every call  [test_e1fix_the_health_ping_is_bounded_and_never_leaks_more_than_one_th]
ok  KILLED       G32i Runner.health never times the ping out (a hung store reads as up)  [test_e1fix_the_health_ping_is_bounded_and_never_leaks_more_than_one_th]
ok  KILLED       G32j _prepare does not warn that the App has no audit  [test_e1fix_main_warns_once_when_the_app_has_no_audit_and_make_app_does]
ok  KILLED       G33a _recover does not close the App's store after a failed try  [test_fix2_recover_closes_the_store_on_every_failed_try]
ok  KILLED       G33b Runner.health puts the ping in place before its thread has started  [test_fix2_a_ping_thread_that_does_not_start_is_a_counted_503_and_the_n]
ok  KILLED       G33c the conflict audit write is waited for 30 s, not 2 s  [test_fix2_a_blocked_audit_write_costs_the_409_at_most_2_s_and_one_writ]
ok  KILLED       G33d a degraded worker logs its re-check failure at every try, not once per 5 minutes  [test_fix2_the_recheck_warning_is_once_per_5_minutes_and_again_when_the]
ok  KILLED       G33e the 409 event cap uses one shared key for all senders  [test_fix2_the_cap_is_per_sender_and_the_window_dict_is_bounded_by_the_]
ok  KILLED       G33f an unsigned request is taken as the first configured sender  [test_fix2_an_unsigned_or_wrongly_signed_conflicting_document_writes_no]
ok  KILLED       G34 QuietWSGIHandler._write sends at once (the answer is four writes again)  [test_every_answer_is_one_write[202]]
ok  KILLED       G35 finish_response does not mark the headers as sent after a failing final send (handle_error builds a page from environ=None)  [test_a_timeout_on_the_final_send_is_logged_once_by_cl
107 killed, 3 crash-accepted (G20j, G31, G32e), 0 known survivors
KNOWN SURVIVORS (missing test): the mutant is not killed by any test; listed, not a pass
  - (none: every mutant of the list has a killer test)
110 of 111 run are as expected; problems: ['G15d the stalled-client refusal needs no request_version default']
EXIT=1
```
