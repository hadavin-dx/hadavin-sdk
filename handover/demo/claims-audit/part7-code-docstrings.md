# Part 7: promises in code docstrings and comments (src/, tools/, scripts/, load_tools/, demo_only/)

Repo: /tmp/claims-main (main c30c3737). Read-only. I ran NO tests (reading only); "BACKED-BY-TEST" means I read the assertion, not that I ran it.

## Greps run (all `grep -rniwE ... --include='*.py' src tools scripts load_tools demo_only`)
Hit lines (code lines and comment lines mixed, counted by line): never 233, always 20, guarantee 1, guarantees 0, proves 13, proof 2, safe 26, cannot 133, exactly 21, at most 52, at least 24, impossible 0, atomic 3, durable 0, idempotent 2, refuses 27, "is refused" 34, every 196, all 81, only 286.
- The first group (never ... "is refused") gave 563 distinct hit lines in 44 files (saved in /tmp/work/claims/p7-hits.txt). I read all 563 lines (one line each, trimmed to 220 chars), dropped hits that were code (print/raise strings, variable names, `quote(..., safe=...)`) and hits in obvious local loops. About 150 were promise-like; I AUDITED the ~55 below (module docstrings of src/lead_desk/*.py headers, tools/pathconfine.py, scripts/*.py headers, load_tools/*.py first, then the desk.py/constants.py/server.py promises a reader would rely on).
- "every / all / only" (563 lines): counted, NOT read line by line; triaged only through the other greps (most are descriptive). The remaining ~95 promise-like hits of the first group (mostly "never prints/never logs the key|value" repeated in per-function docstrings, and "cannot" meaning a Python limitation) were triaged as covered by the same tests as the module-level rows and NOT audited one by one.

Verdict key: KEEP / BACKED-BY-TEST / UNBACKED (see BRIEF).

## src/lead_desk/live_claude.py (module docstring)
| file:line | exact words | backing | verdict |
|---|---|---|---|
| live_claude.py:4 | "this proves the plumbing (valid answer, failures, cost), not the quality of the answer" | tests/test_live_claude.py::test_ok_label_and_cost_log, ::test_failure_modes_raise_classed_errors | BACKED-BY-TEST |
| live_claude.py:8 | "default 8 s, at most the desk's AI call budget of 9 s" | constants.py:176 LIVE_DEFAULT_TIMEOUT_SECONDS=8.0; constants.py:80 MODEL_CALL_BUDGET_SECONDS=9.0; config.py:160; tests/test_live_claude.py:199 (9.1 refused) | BACKED-BY-TEST |
| live_claude.py:8-12 | "one call = one TOTAL time limit ... network request is not started at all when the limit is already used up" | tests/test_live_claude.py::test_timeout_is_hard_and_short, ::test_slow_drip_hits_the_whole_call_deadline, ::test_header_trickle_hits_the_total_deadline; code live_claude.py:498-504 | BACKED-BY-TEST |
| live_claude.py:14 | "NO retry in here" | test_failure_modes_raise_classed_errors asserts model.state.calls == 1 | BACKED-BY-TEST |
| live_claude.py:17-18 | "the key ... is never an argument and never printed. Every error ... fixed text only (never the reply, never the key, never the key file path)" | test_key_never_leaks, test_failure_modes (FAKE_KEY not in str/repr), test_the_key_file_path_is_not_printed_with_the_settings. Tests check specific paths (401, missing file, 429/5xx), not every error | BACKED-BY-TEST |
| live_claude.py:20-22 | "WORST case cost ... reserved in a locked ledger file; the call is refused when the per-run or the plan total cap would be passed" | tests/test_live_claude.py::test_cap_survives_restart_and_counts_worst_case, ::test_ledger_concurrent_reserves_never_pass_the_cap, ::test_cap_holds_with_five_refusals | BACKED-BY-TEST |
| live_claude.py:22-25 | "A call that fails or crashes keeps its worst-case reserve ... This includes a 429 or a 5xx answer" | code live_claude.py:497-501 (no settle on a raise). Test only for the crash case (test_total_cap_spans_runs_and_crash_keeps_reserve). No test asserts the ledger after an r429/r5xx answer | UNBACKED: guarantee for 429/5xx has no test that reads the ledger after such an answer (code does enforce it) |
| live_claude.py:25 | "The ledger survives restarts." | test_cap_survives_restart_and_counts_worst_case | BACKED-BY-TEST |
| live_claude.py:26-27 | "if the cost cannot be recorded after a paid answer ... the answer is still returned and the worst-case reserve stays" | tests/test_ledger_and_bind_retry.py::test_bad_token_counts_keep_the_worst_case_reserve, ::test_settle_failure_does_not_discard_a_paid_answer | BACKED-BY-TEST |
| live_claude.py:28 | "there is no price or model name in this file" | grep of the file: none found by me, no test | KEEP |
| live_claude.py:61 | "Answer with exactly one word: hot, warm or cold" | it is the prompt text itself | KEEP |

## src/lead_desk/smtp_provider.py, imap_count.py, smtp_outbox.py
| file:line | exact words | backing | verdict |
|---|---|---|---|
| smtp_provider.py:4 | "certificate checked against that name, verification always ON" | tests/test_smtp_provider.py::test_certificate_not_trusted_is_unreachable_and_nothing_is_sent, ::test_certificate_for_another_name_is_unreachable; code :188,:268 | BACKED-BY-TEST |
| smtp_provider.py:6-7 | "password read from a FILE at every send (never an argument, never printed, never in an error text)" | test_bad_login_is_refused_without_the_password_in_the_error, test_password_file_missing_or_empty_is_refused_without_path_or_network, test_settings_do_not_print_addresses_or_paths | BACKED-BY-TEST |
| smtp_provider.py:7-10 | "the mail is NEVER sent to the lead's own address ... The made-up lead addresses can therefore never receive mail" | test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead; code :204-206 picks only from settings.recipients. (A configured recipient could in principle equal a lead address; the code does not check that.) | BACKED-BY-TEST |
| smtp_provider.py:11-13 | "Message-ID and X-Send-Attempt are a NEW random token for every attempt" | test_every_attempt_has_its_own_message_id_and_attempt_header_but_the_same_count_key | BACKED-BY-TEST |
| smtp_provider.py:152 / SECRET_FILE_MAX_BYTES | "At most SECRET_FILE_MAX_BYTES are read" (4096) | code smtp_provider.py:72,:159; test_password_file_formats_give_a_helpful_fixed_text | BACKED-BY-TEST |
| smtp_outbox.py:8,:10 | "A retry is safe" (nothing reached the server's data stage) | tests/test_smtp_outbox.py (error table) and test_smtp_provider.py::test_any_doubt_after_the_text_started_is_ambiguous | BACKED-BY-TEST |
| imap_count.py:7 | "a count for `L-001` never includes `L-0010`" | tests/test_smtp_provider.py:441-454 (L-001 vs L-0010 asserted) | BACKED-BY-TEST |
| imap_count.py:8-11 | "searches for each FULL key ... fallback scan (at most FALLBACK_SCAN_MAX) ... the LARGER of the two counts is kept" | imap_count.py:39 (=300), :174; tests test_a_key_the_search_misses_triggers_the_scan_and_the_larger_count_wins, test_the_larger_count_wins_and_a_scan_never_replaces_the_search_result | BACKED-BY-TEST |
| imap_count.py:18-19 | "The connection ALWAYS checks the certificate chain and the host name: no settings value can switch that off." | code :90 (create_default_context when none given); tests test_imap_default_trust_rejects_an_untrusted_certificate..., test_imap_certificate_for_another_name_is_rejected. A caller of the Python API can still pass its own `ssl_context` (imap_count.py:68), so "no settings value" is true for config files but not for code that builds ImapSettings itself | BACKED-BY-TEST (wording slightly absolute) |

## src/lead_desk/crm_hubspot.py
| file:line | exact words | backing | verdict |
|---|---|---|---|
| crm_hubspot.py:22 | "The key is read from a file at every call and never logged, never in an error text, never in the file path text." | tests/test_crm_hubspot.py (key-file tests), test_the_key_goes_only_to_hubspot_hosts_unless_overridden, :356 redirect test | BACKED-BY-TEST (I read the test names and the redirect/host tests; I did not read every key-leak assertion) |
| crm_hubspot.py:24-26 | "Every request is bounded as a WHOLE by a wall-clock budget ... a worker that outlives it is abandoned" | tests/test_hung_adapter_calls.py (hung CRM) | BACKED-BY-TEST |
| crm_hubspot.py:47 | "The copy may use at most floor(max_calls * MIRROR_CALL_SHARE) calls" (share 0.5) | code crm_hubspot.py:358 `int(max_calls * MIRROR_CALL_SHARE)`; tests/test_lead_crm_copy.py:425 and test_mirror_gate.py | BACKED-BY-TEST |
| crm_hubspot.py:88 | "this module never creates one" (the lead-id property) | no create-property call in the file (grep) | KEEP |
| crm_hubspot.py:407 | "the body is never read: a 200 already says the change was applied" | code line itself | KEEP |

## src/lead_desk/desk.py, gate.py, constants.py, server.py, others
| file:line | exact words | backing | verdict |
|---|---|---|---|
| desk.py:169 | "refuses to be built with a setting that would break its once-only guarantee ... exit code 4" | tests/test_hung_model_call.py:220 (14.9 s declared refused), tests/test_live_claude.py:616 (9 s yes, 9.1 s no), server.py:1113 | BACKED-BY-TEST |
| desk.py:206 | "A reminder is never sent again by the desk." (text shown to the user) | tests/test_reminder_email.py::test_reminder_once_over_many_passes, ::test_reminder_crash_gives_unknown, ::test_clock_set_back_no_resend, ::test_ten_racing_one_row | BACKED-BY-TEST |
| desk.py:624 | "two reapers never run a pass at the same time" | tests/test_reaper_start_stop.py::test_start_after_stop_waits_for_old, ::test_stop_start_stop_start_one_pass, ::test_simultaneous_starts_one_reaper | BACKED-BY-TEST |
| desk.py:884 | "at most NUDGES_PER_PASS claims inside NUDGE_PASS_SECONDS" (5 per pass, 2.5 s) | code desk.py:894-895; constants.py:153, gate.py:39. grep over tests/: the constant is never referenced, no test of the cap of 5 | UNBACKED: number (5 per pass / 2.5 s) enforced in code but no test checks it |
| desk.py:1317 | "At most INFLIGHT_MAX calls run at once" (32) | gate.py:19; tests/test_desk_edge_cases.py::test_inflight_limit_503_busy (asserts 32, call 33 gets 503 busy, no receipt) | BACKED-BY-TEST |
| desk.py:1476-1486 | "waits for it at most `budget` seconds ... the bound is exactly the cap ... a slot is reserved BEFORE the worker is started" | tests/test_hung_adapter_calls.py, test_hung_model_call.py | BACKED-BY-TEST |
| desk.py:1912 / 1915 | "an automatic driver can never take a `failed` row" | tests/test_claim_ownership.py, test_claim_checks_and_crm_mode.py (read by name only; I did not open the assertions) | BACKED-BY-TEST (by name; unchecked assertion) |
| desk.py:2204,:2222 | "409 in_progress, never 200, when the row is still `sending` afterwards" | tests/test_slow_sender.py / test_followup_edge_cases.py (by name search only) | UNBACKED: I could not find, within the timebox, a test I could read that asserts 409 vs 200 for this case (NONE found, not a guess) |
| desk.py:125 | "the lock is never held across a database write or a CRM call" | no test found | UNBACKED: absolute "never" about lock scope, no test (code reading only) |
| constants.py:58-77 | "9 s is accepted, 9.1 s is not"; grace "30 s with the defaults"; margin 15 s = 10 s + 5 s | arithmetic checked: gate.py:46 SENDING_GRACE_BUSY_WAITS=5, constants.py:45 BUSY_WAIT_SECONDS=5.0, constants.py:81 =15.0; tests/test_live_claude.py:616 | BACKED-BY-TEST |
| gate.py:30-35 | "10 + 27 + 18 = 55 s at the very worst" (reaper pass) | arithmetic matches (10 s pass + 3x9 s + 2x9 s); no test measures it | KEEP (arithmetic from the constants; not a measured result) |
| constants.py:86 / :248 | "FD_RESERVE = 96 ... at least the sum of FD_RESERVE_ITEMS" | items sum to 66 (1+1+4+1+2+16+1+16+24); tests/test_hung_adapter_calls.py:659 validate_descriptor_budget | BACKED-BY-TEST |
| constants.py:133 | "approver id; at most 32 characters (the table CHECK)" | schema.sql:73 `length(approver_id) BETWEEN 1 AND 32`; pattern {0,31}+1 | KEEP |
| constants.py:183 | "a bigger ledger file is refused (read whole on every reserve)" (8,000,000 bytes) | tests/test_ledger_amounts.py::test_oversize_file_refused_with_its_own_message, ::test_exactly_the_size_cap_is_allowed... | BACKED-BY-TEST |
| constants.py:236 | "Refused connections kept open ... at most this many at once" (16) | tests/test_stall_eviction.py:568-571 | BACKED-BY-TEST |
| constants.py:252 / server.py:223-224 | "connection stays at most DRAIN_TOTAL_SECONDS (1.0 s) ... at most DRAIN_MAX_BYTES are read" | tests/test_portal_api.py::test_trickle_is_cut_at_drain_deadline (time); no test found for the byte limit | UNBACKED: DRAIN_MAX_BYTES limit has no test I could find (time limit is tested) |
| constants.py:226 | "PORTAL_MAX_INFLIGHT = 8 portal JSON requests answered at once; more get 503 busy" | tests/test_model_stamp_and_reaper.py:251-269 uses the constant for fd counting only; no test that request 9 gets 503 found | UNBACKED: number 8 and "503 busy" for the portal not tested by name |
| constants.py:269 | "DUPLICATES_MAX 50 repeats listed for one lead (the total is always given)" | portal_api.py:482,:540 (duplicates_total); no test mentions the constant | UNBACKED: the cap of 50 has no test |
| server.py:732-733 | "DNS rebinding is refused. A present Origin must be exactly one of this server's own origins; `null` is refused ... Sec-Fetch-Site same-origin or none" | tests/test_later_approval.py::test_foreign_origin_decision_is_403, ::test_wrong_host_decision_is_403 (the `null` and Sec-Fetch-Site cases not read) | BACKED-BY-TEST (partly; `null`/Sec-Fetch-Site assertions not read) |
| server.py:1036 | "`main` refuses a public bind (`Config.public_bind_problem`)" | tests/test_bind_refusals.py | BACKED-BY-TEST |
| server.py:1215 | "the socket, the database and the lock are always released" | code: nested try/finally at server.py:1214-1228; tests/test_server_main_reaper.py::test_main_reaper_sends_and_frees_lock (one path) | BACKED-BY-TEST (nested finally by code; test covers the normal path only) |
| config.py:66 | "Fails closed: anything it cannot read is not loopback" | tests/test_bind_refusals.py::test_which_hosts_are_this_computer | BACKED-BY-TEST |
| gate.py:6 | "inside one desk process SQLite itself is never contended" | tests/test_stamp_locks_and_budget.py / test_desk_edge_cases.py (retry-locked tests exist, which show it CAN be contended by another process, as the next sentence says); no test proves "never" inside one process | UNBACKED: absolute "never contended" within a process, no test that shows no lock error under many writers was found |
| adapters.py:3 | "The opener has no proxy handler" | code adapters.py:44 uses `ProxyHandler({})` (an empty proxy map, so it does have a handler that disables proxies); tests/test_infra.py:73-77 | BACKED-BY-TEST (wording: "no proxy handler" is loosely stated; behaviour true) |
| run_stats.py:1 | "writes its counters there after every change (an atomic replace)" | code only; no test of atomicity (tests reference counters through test_live_claude/test_load_tools) | UNBACKED: "atomic" not tested (os.replace in code was not verified by me line by line) |
| trace.py:14-17 | "A trace line that cannot be written is counted and dropped; it never changes the result of the traced call" | tests/test_live_claude.py::test_trace_wrappers_and_hooks, ::test_trace_records_a_failure_and_reraises (failure path; write-failure path not seen) | UNBACKED: the write_failures path has no test I could find |
| db.py:134-137 | "A crash or an error anywhere rolls the whole thing back, so the book is never left with columns but no view" | tests/test_desk_http_edge_cases.py:681 repairs a book whose view was dropped; tests/test_migration_triggers.py repairs triggers. No test injects an error mid-migration and checks the rollback | UNBACKED: rollback-on-error guarantee not tested directly (repair after a half migration is) |
| loader.py:43 | "the burst and crash controls write leads, so they never load next to a real CRM" | contradicts demo_only/portal_demo.py:11 ("`state` and `crash` never touch the lead book"; crash only arms a flag file) ; code loader.py:44 gate is real | UNBACKED: STALE/loose wording: the crash control does not write leads, only the burst does |

## tools/pathconfine.py (module docstring)
| file:line | exact words | backing | verdict |
|---|---|---|---|
| pathconfine.py:8-17 | "uses ONLY the returned path afterwards, never the original text ... the text that gets opened is never the argument's text" | tests/test_path_confinement.py::test_the_listing_path_is_returned_not_the_argument_text, ::test_no_flagged_site_opens_a_raw_argument, ::test_each_flagged_function_calls_the_helper_itself... | BACKED-BY-TEST |
| pathconfine.py:20-24 | new names: only letters, digits . _ -; refused with trailing dot or Windows device names "on every operating system" | test_a_new_file_name_is_rebuilt_from_allowed_characters_only, test_v3_* (devices, trailing dot, list equals Python's reserved list) | BACKED-BY-TEST |
| pathconfine.py:41-47 | list of what is refused (NUL, control, too long, loops, folders, outside) | tests test_odd_input_is_refused, test_v2_*, test_c0_del_and_c1_controls..., test_a_link_loop..., test_a_path_that_names_an_allowed_folder_itself... | BACKED-BY-TEST |
| pathconfine.py:49-53 | "What this is NOT: a defence against a person or agent that controls the shell ... not a defence against a swap between check and open" | honest limitation statement | KEEP |
| pathconfine.py:55 | "a `?` or `#` in a file name cannot start a new option" | test_sqlite_uri_encodes_query_and_fragment_characters | BACKED-BY-TEST |
| pathconfine.py:70 | MAX_PATH_CHARS 4096 "the usual Linux limit; Windows allows less" | code line; general knowledge, no test of the Linux claim | KEEP |

## tools/scrub_n8n_export.py, tools/hygiene.py
| file:line | exact words | backing | verdict |
|---|---|---|---|
| scrub_n8n_export.py:3-4 | "a key that is not listed is dropped, so a field n8n adds later cannot leak. Never kept: ids, instance id, credentials, webhook ids, pinData, tags, project owner, timestamps." | tests/test_hygiene.py::test_scrub_canary (unknown keys at top/meta/node level, id, webhookId, pinData, tags, homeProject, createdAt all planted and asserted absent). Credentials key not planted | BACKED-BY-TEST (credentials not in the canary) |
| scrub_n8n_export.py:21-24 | "The webhook PATH is kept ... so a secret written inside a path stays" and the NOT-cleaned list | tests/test_scrub_n8n_export.py::test_limit_a_secret_inside_the_path_of_a_kept_address_stays and ::test_the_docs_and_the_module_text_carry_the_same_limit_phrases... | BACKED-BY-TEST |
| hygiene.py:94 | "the term itself is never returned" | tests/test_hygiene.py (not opened) | UNBACKED: not checked within the timebox (NONE found, not a guess) |

## scripts/
| file:line | exact words | backing | verdict |
|---|---|---|---|
| hubspot_probe.py:3 | "It makes at most 8 calls ... (two calls, so the table shows which one a free plan refuses)" | hubspot_probe.py:44 CALL_BUDGET=8, :47 PLANNED_CALLS=7; tests/test_hubspot_probe.py::test_429_retries_are_counted_and_the_budget_stops_the_run ("calls used: 8 of 8"), ::test_gdpr_429_forever_stays_inside_budget | BACKED-BY-TEST |
| hubspot_probe.py:4-5 | "then always deletes it (by id, or by email when the create answer was lost)" | tests test_cleanup_after_failure_at_each_step, test_unknown_create_outcome_deletes_by_email, test_both_deletes_fail_warns_and_fails (the last shows delete can fail: it then warns, so "always" means "always tries") | UNBACKED: "always deletes" is stronger than the code: it always TRIES; test_both_deletes_fail... shows it can fail and warns |
| hubspot_probe.py:6 | "first 100 characters of its message"; "never prints the token or a header" | hubspot_probe.py:168 `[:100]`, :159 token replaced by ***; tests test_token_echoed_in_a_4xx_message_is_masked, test_no_token_in_exception_text, test_token_pasted_as_env_name_is_never_echoed | BACKED-BY-TEST |
| hubspot_probe.py:14 | "number after --yes-spend-calls must equal the planned count" | test_refuses_wrong_count_missing_token_and_token_argument | BACKED-BY-TEST |
| n8n_api.py:6-17 | key "never printed"; "A redirect answer is never followed"; "proxy settings ... ignored for http to this computer"; key file one printable ASCII word of at most 4096 chars; "never a Python traceback" | tests/test_n8n_api_url.py (redirect, proxy, key-file, traceback tests, ~30 tests) | BACKED-BY-TEST |
| n8n_api.py:23 | "NOT covered (a traceback is possible): Ctrl-C, MemoryError, BrokenPipeError" | honest exception list | KEEP |
| run_live_check.py:2-3 | "~12 made-up leads, 3 runs ... Prints ONLY counts, cost, valid-label rate, flip rate and latency. Never prints the key or any reply text." | run_live_check.py:37-38 LEADS=12, RUNS=3; tests/test_live_claude.py::test_runner_prints_counts_only_and_asks_first | BACKED-BY-TEST |
| run_live_check.py:10-13 | "without caps, prices and a price date the script refuses to start ... waits for y/N before the first call ... any other address than the provider's or this computer is refused" | test_runner_refuses_without_caps_or_prices, test_runner_prints_counts_only_and_asks_first, test_the_key_goes_only_to_the_providers_host_or_this_computer | BACKED-BY-TEST |
| run_real_check.py:6-33 | defaults "REAL_PERSONS 12, REAL_DRAIN_SECONDS 150, REAL_MAIL_WAIT_SECONDS 90"; "refuses to start without every required name"; "asks y/N"; "It never prints a key, an address or a message text" | code run_real_check.py:102,:854,:873-874,:920; tests/test_real_check_dry.py (dry-run tests, incl. :821 default stays 150) | BACKED-BY-TEST |
| run_real_check.py:308-319 | checks F1-F6 (floors: "at least all but the crash window ended `sent`", "mails sent are at most leads + unknown leads") | tests/test_real_check_dry.py::test_the_desk_may_not_send_more_than_leads_plus_unknown_leads (F4); F1-F3, F5, F6 not read | BACKED-BY-TEST (F4 only read) |
| check_schema.py:3 | "fire every trigger and constraint once" (14 triggers in schema.sql, 46 expect_error calls) | script run in .github/workflows/lint.yml (no log in repo); tests/test_migration_triggers.py::test_the_trigger_list_is_every_trigger_of_schema_sql; all 14 trigger names appear in the script or that test | UNBACKED: result of the CI run is not stored in the repo; I did not check each of the 14 against the script |
| check_schema.py "never deleted"/"never changes" labels | e.g. "lead_state: owner never changes" | schema.sql triggers lead_state_owner_immutable etc. (14 `RAISE(ABORT` ) fired by the script | KEEP |
| http_guard.py:1 | "only http and https are allowed, never file:, ftp: or any other scheme" | tests/test_http_guard.py | BACKED-BY-TEST |
| reset_check.py:3,:28 | "a lock file that cannot be tested is a refusal" | tests/test_reset_scripts.py:246,:269 | BACKED-BY-TEST |

## load_tools/ and demo_only/
| file:line | exact words | backing | verdict |
|---|---|---|---|
| check_invariants.py:1-5 | "The seven checks ... Exit code 0 only when all seven checks hold; 1 when a check fails; 2 when an input file cannot be read" | CHECK_NAMES has 7 entries (:49-57); tests/test_load_tools.py::test_cli_exit_codes, ::test_clean_case_passes, ::test_planted_fault_fails_one_check | BACKED-BY-TEST |
| check_invariants.py:54 | check 3 "at most one message per send key; no message only for failed or unknown" | test_two_messages_to_one_address_fail_check_3..., test_planted_fault_fails_one_check, test_failed_after_an_unclear_end_may_have_a_message | BACKED-BY-TEST |
| check_invariants.py:229 | "an empty request log proves nothing: a run that sent nothing must not pass" | tests test_empty_request_log_fails, test_nothing_sent_fails_whatever_the_allowances | BACKED-BY-TEST |
| check_invariants.py:56 (header of load_tools) | followup subject pinned to the desk's text | tests/test_load_tools.py::test_the_checkers_followup_text_is_the_desks_text, ::test_the_checkers_subject_text_is_the_desks_text | BACKED-BY-TEST |
| load_driver.py:5-7 | "Open loop: each request has an INTENDED send time fixed before the run; a slow reply never moves a later request. ... lag are logged" | tests/test_load_tools.py::test_schedule_is_open_loop_and_fixed (schedule fixed); lag field load_driver.py:151,:176. No test that a slow reply leaves later send times unchanged | UNBACKED: "a slow reply never moves a later request" tested only through the fixed schedule, not with a slow reply |
| catcher.py:6-8 | "ONE line per accepted message ... A message that cannot be parsed still leaves a line {"unparseable": true}" | tests/test_load_tools.py::test_catcher_counts_a_message_it_cannot_parse | BACKED-BY-TEST |
| catcher.py:20-21 | "Handles hundreds of connections at once (asyncio, listen backlog 1024)" | code catcher.py:42 BACKLOG=1024; grep over tests: no concurrency test of the catcher | UNBACKED: "hundreds of connections" is not tested; only the backlog number is in code |
| catcher.py:43 | "one SMTP line (and one message) may be at most 1 MiB" | LINE_LIMIT = 1 << 20 | KEEP |
| demo_only/portal_demo.py:11-13 | "`state` and `crash` never touch the lead book. `burst` DOES write ... Every call except `state` is refused with 409 demo_not_wired unless the desk really runs on the made-up CRM" | tests/test_portal_demo.py (by name; BURST_BUDGET_REQUESTS patched at :1147); not read in detail | BACKED-BY-TEST (by name only) |
| portal_demo.py:79 | "the lead book grows by at most this many rows" (BURST_BUDGET_REQUESTS = 500) | tests/test_portal_demo.py:1147 patches the budget to 5 | BACKED-BY-TEST |
| fake_model_server.py:2,:18 | "Never receives a real key"; "the key itself is never stored or printed" | fake server code stores only a flag (:67 comment); tests/test_codeant_fakes.py (not read) | UNBACKED: "never receives a real key" cannot be enforced by a fake server; "never stored" checked by reading only |
| fake_hubspot.py:101 | "One lock covers the email check and the store: two creates cannot both succeed" | tests/test_codeant_fakes.py (_BarrierFields barrier test at :210-220, by name) | BACKED-BY-TEST (by name) |
| burst.py:56-57,:71 | "never more than BURST_BACKOFF_MAX_SECONDS and never past the deadline" | tests/test_burst_retry.py; tests/test_load_tools.py::test_backoff_doubles_and_is_capped | BACKED-BY-TEST |

## Counts (89 rows; verdict = the one that starts the last column)
- KEEP: 11
- BACKED-BY-TEST: 60 (several "by name only" or partly read, marked in the row)
- UNBACKED: 18 (of which 1 STALE wording: loader.py:43; 0 clearly FALSE)

## 10 most serious UNBACKED / STALE items
1. loader.py:43: STALE: says the "burst and crash controls write leads"; portal_demo.py:11 says crash never touches the lead book (only burst writes).
2. hubspot_probe.py:4-5: "always deletes it": the code always TRIES; test_both_deletes_fail_warns_and_fails shows the delete can fail (then it warns).
3. gate.py:6: "SQLite itself is never contended" inside one process: absolute, no test shows it.
4. db.py:134-137: "an error anywhere rolls the whole thing back, so the book is never left with columns but no view": only the repair after a half-finished migration is tested, not the rollback.
5. live_claude.py:22-25: "429 or 5xx keeps the worst-case reserve": enforced by code, no test reads the ledger after such an answer.
6. desk.py:125: "the lock is never held across a database write or a CRM call": absolute, no test.
7. desk.py:2204/2222: "409 in_progress, never 200, when the row is still `sending`": I found no test I could read that asserts it.
8. catcher.py:20: "Handles hundreds of connections at once": no concurrency test.
9. check_schema.py:3: "fire every trigger and constraint once": CI result not stored in the repo; I did not match all 14 triggers to the script.
10. desk.py:884 / constants.py:226,:252,:269: numbers 5 reminders per pass, 8 portal requests, 1 MiB drain limit, 50 duplicates have no test of their own value.
Also: run_stats.py:1 "atomic replace" and trace.py:14 "never changes the result" have no direct test; imap_count.py:18 "no settings value can switch that off" is true for the config path but a Python caller can pass its own `ssl_context`.

## What I did not cover
- The ~95 remaining promise-like hits of the first grep (repeated "never prints the key/value" in per-function docstrings, `cannot` as a Python limit): triaged as the same claim as the module rows, not audited one by one.
- The "every / all / only" grep (563 lines): counted only, not read line by line.
- desk.py (86 hits) and server.py (51 hits): I audited about 15 promises each; the rest (transition-table comments, reaper detail) not read.
- src/lead_desk/portal/ (JS/CSS), scripts/*.sh and *.ps1, tests/ files: out of scope (not Python docstrings under my five folders).
- I ran no test. Test names were read and, where marked "(by name)", the assertion was NOT read.
- Time: no hard timebox overrun, but several tests (test_claim_ownership, test_followup_edge_cases, test_portal_demo, test_codeant_fakes, test_hygiene beyond the scrub canary) were located by name only.
