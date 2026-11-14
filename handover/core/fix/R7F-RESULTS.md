# R7F RESULTS (patch round r7f on r7e, money and mail path). Tree /home/user/build/rr6/tree-R7F. Base frozen 49d3c859.

All numbers below are builder-claimed. Made-up data, loopback only (every test run inside `unshare -n`), no spend, nothing pushed.

## OPEN ITEMS / NOT RUN / NOT DONE (first)

1. **Newline-named stray file (coordinator item 2b): NOT FOUND within the box.** I ran 29 test files on staged copies (batches b1, b2: raw/stage-b1.log, stage-b2.log) and the four files that mention a name with a line break (test_path_confinement, test_r4_refusals, test_smtp_outbox, test_later_messages; raw/hunt1.log), then listed untracked files with `git ls-files -o` afterwards: no file with a control character in its name appeared. The first all-files runs were killed by something outside my commands at about 04:00 UTC (raw/full-h1.log ends "Terminated", rc 143; full-h2.log "KeyboardInterrupt"); I restarted them as one process per test file (raw/perfile-1.txt, perfile-2.txt) and the result of the stray-file check on those is in section "Per-file full run" below (no file with a control character in its name appeared; see the end). Next step if still open: run the per-file loop with a `git ls-files -o` line after every file to name the writer.
2. **Full suite on the FINAL tree: not completed as one run.** See "Per-file full run" for what ran and what did not. The batches b1/b2 ran on the tree before the last two code changes (netconnect and the file-call-guard table), so the files that touch them were re-run (listed below) or are named as not re-run.
3. NOT RUN: PowerShell (no .ps1 changed), Python 3.13/3.14, real mail/HubSpot/model services, the hygiene scan history part on the real frozen clone (a fresh scratch git is used: the frozen clone has a known extra ref, see R7E item 5).
4. Mutants: pass-8 survivors I04 and I05 are NOT APPLICABLE as written (the r7e change removed the code the mutant edits, count 0). I ran two analogue mutants on the new code (I04a, I05a): both killed by existing tests. MAIL7 row B04 is NOT APPLICABLE (the line it edits no longer exists), T03 as written is not applicable (see below: the word it removes never matched anything; fixed).
5. Machine load average about 100 the whole time; mutants were run one at a time, test files `-x`. Lane timeouts were not an issue in the final runs.
6. Slips (mine): I typed a device path as an argument or redirect three times (once in the earlier part, twice later); each time the harness refused it and the command did not run. Written down in checkpoint.md.
7. `tree-R7E/data` (the stray empty folder, n2) was NOT touched: it is not mine and I must not edit tree-R7E. The r7f tree has no `data/` (checked), and the build removes `data` anyway.

## What changed in r7f (delta r7e to r7f: 16 files, 154 files vs frozen)

- scripts/hubspot_probe.py + docs/hubspot-probe.md: `_mask` is now the fixed words "(id hidden)"; the owners line says only a count. Old: "..." plus the last 4 characters of a value that can come from the server. Tests: happy-path test gets one extra assertion; new `test_no_part_of_a_server_supplied_id_is_printed_even_when_the_delete_fails`, `test_the_mask_is_a_fixed_word_for_any_value` (3 fail on the r7e mask, raw/hp-mutant-r7e-mask.log).
- load_tools/load_driver.py (r7e review M1): a run with any `driver:stopped` line ends rc 3 with one true line ("N of M requests were never sent"). New test `test_m1_r7e_a_stopped_run_that_the_desk_answers_later_is_not_a_success`: fails on r7e (rc 0), passes on r7f (raw/m1r7e-before.log, m1r7e-after.log). Closed port still rc 3 fast (raw/m1-regress.log: 31 passed).
- docs/real-services.md (m2): a damaged key file is refused; a file replaced by another valid key is used as it then is.
- docs/limits.md (n1): no total time limit for a whole run, stated plainly with the 62.7 s measurement; plus the new name look-up paragraph.
- tests/support.py (m3): `book_folder_in_repo` fails the test if `data` is a link; `made` from `os.path.lexists`. Tests: `test_m3_...refuses_a_data_link...` (fails on r7e), `...leaves_the_repository_folder_as_it_found_it` (CONTROL).
- labels (m1): the 10 pipe/link/folder cases of `test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once` are now labelled "FAILS on the frozen tree (fix test)"; `test_portal_demo.py::test_burst_keeps_every_answer[hang_up-error]` is labelled a fix test, the other two cases CONTROL. The test_hygiene and test_vendor_hosts labels were checked on a fresh scratch copy of the frozen tree: 30 passed (raw/labels-froz3.log), so "passes on the frozen tree" holds for them. (An earlier check failed only because my scratch git had my own overlay commits in its history: raw/labels-froz2.log.)
- **Real gap found while classifying MAIL7 T03 (fixed):** `src/lead_desk/tls_trust.py` `WEAK_CIPHER_WORDS` held the word "anon", which no OpenSSL cipher name contains (158 names checked), so a context that offered ciphers with no server login (ADH-..., AECDH-...) was accepted. Now the words are "ADH-" and "AECDH-". Fix tests `test_f5_a_context_that_offers_an_anonymous_cipher_is_refused` (2 cases) FAIL on r7e (raw/f5-on-r7e.log), pass on r7f; mutant "words dropped" killed. One existing test setup had to change: `tests/test_r7m_new.py` line 57, the client context list `"ALL:@SECLEVEL=0"` became `"ALL:!aNULL:@SECLEVEL=0"` (the test wants old TLS versions offered; it must not offer a cipher with no server login). Assertions unchanged (raw/r7m-after.log: 10 passed).
- **Name look-up (coordinator item 2a, fixed, not only proved):** new `src/lead_desk/netconnect.py` (`resolve_bounded`, `connect_bounded`): the look-up runs in a helper thread that is waited for at most the time given, then the connect uses the time left. Used by `imap_count._BoundedImap._create_socket` and `smtp_provider._connect` (replacing `imaplib.IMAP4._create_socket` and `socket.create_connection`). The desk's own SMTP outbox (`smtp_outbox.py`) connects to loopback addresses only and is unchanged; HubSpot already runs its request in a worker thread (crm_hubspot.py header). Tests `test_f6_*` (4): silent look-up ends at 0.5 s; the mailbox read with total 1 s ends in under 3.5 s with ImapTotalTimeout; a mail send with limit 1 s ends in time with SendUnreachable; a plain connect and a lookup error still work. On r7e the two end-to-end tests fail after about 60 s (raw/f6-on-r7e.log). `tests/test_file_call_guard.py`: the table of allowed calls changed: removed `imap_count imaplib.IMAP4` and `smtp_provider socket.create_connection`, added `netconnect socket.getaddrinfo` and `netconnect socket.socket`, each with a reason (the guard test passes: raw/guard2.log). A look-up thread that is still running after the time-out stays alive until the system answers (daemon thread, no connection, no secret): stated in docs/limits.md.
- data/ writers (coordinator message 3): the only writer in `tests/` was the `REPO / "data"` one in `tests/support.py` (fixed in r7e, link-safe now). grep of `tests tools scripts load_tools demo_only src` for mkdir/makedirs on a repo `data` path found no other; the others are under `tmp_path`. After the staged runs `data/` was absent in every stage copy (git ls-files -o empty). EV7F can start on a checkout with no `data/`: tree-R7F has none.

## D21 (EV7D, run_real_check `name.strip(" \t")` to `name.strip()` in `out[...]`)

**EQUIVALENT.** Line 700 requires `CONFIG_NAME.fullmatch(name.strip(" \t"))` with `CONFIG_NAME = [A-Z0-9_]+`; the same expression is the key on line 705. A string that fully matches that pattern has no white space at either end, so `strip()` on it changes nothing. D20 (the same replacement inside the fullmatch) is a different, real mutant; it is killed by existing tests per EV7D. No test can tell D21 from the original; I did not write one. Evidence: code lines 128, 700, 705 of scripts/run_real_check.py.

## Mutant table (every id of the pass-8 list, plus the MAIL7 survivor and timeout rows)

Status: KILLED-BY-EXISTING (an existing test of the r7e tree fails on the mutant, run on a snapshot without my new file), KILLED-BY-NEW-TEST (survived the existing relevant files, killed by a test in `tests/test_r7f_findings.py` or `test_hubspot_probe.py`), EQUIVALENT, NOT-APPLICABLE. No row is NOT-RUN. Raw rows: mut/results.tsv (existing tests), mut/results-new.tsv, mut/lane*.log.

| id | status | killer / reason |
|---|---|---|
| I03 | KILLED-BY-NEW-TEST | test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step |
| I04 | NOT-APPLICABLE | code removed in r7e; analogue I04a (handshake time-out = plain step) KILLED-BY-EXISTING test_r7d_findings::test_n2_...handshake[silent] |
| I05 | NOT-APPLICABLE | same; analogue I05a (handshake time-out never classed as total) KILLED-BY-EXISTING, same test |
| I09 | KILLED-BY-NEW-TEST | test_f1_a_server_that_is_silent_after_tls_ends_with_the_total_time_error |
| I10 | KILLED-BY-NEW-TEST | test_f2_nothing_is_sent_after_the_total_deadline |
| I12 | KILLED-BY-NEW-TEST | test_f2_a_connection_error_after_the_total_deadline_is_not_repeatable |
| I16 | KILLED-BY-NEW-TEST | test_f2_readline_never_returns_more_than_its_limit |
| I18 | KILLED-BY-EXISTING | test_smtp_provider::test_imap_default_trust_rejects_an_untrusted_certificate_and_sends_no_password (also new test_f2_no_ssl_context...) |
| S02 | KILLED-BY-NEW-TEST | test_f2_a_reply_line_without_an_end_is_cut_off_at_the_cap_not_at_twice_the_cap (survived 9 existing files) |
| S06 | KILLED-BY-NEW-TEST | test_f2_a_message_that_starts_with_a_dot_is_dot_stuffed_on_its_first_line (survived existing) |
| S08 | KILLED-BY-EXISTING | test_bind_refusals::test_which_hosts_are_this_computer[::ffff:10.0.0.1-False] |
| P01 | KILLED-BY-NEW-TEST | test_f2_bytes_that_arrive_with_the_starttls_reply_are_not_read_as_a_reply_after_tls (survived 15 existing files, 341 s) |
| P03 | KILLED-BY-EXISTING | test_r7_mail_context::test_m18a_a_context_weakened... (also new test) |
| P04 | KILLED-BY-NEW-TEST | test_f2_only_a_220_answer_to_starttls_is_accepted (survived 15 existing files) |
| P07 | KILLED-BY-EXISTING | test_ca_file_reads::test_a_non_ascii_character_inside_a_certificate... (also new test) |
| P08 | KILLED-BY-EXISTING | test_r6_refusals::test_context_and_ca_file_together_refused (also new) |
| P09 | KILLED-BY-EXISTING | test_ca_file_reads::test_an_empty_smtp_ca_file_setting... (also new) |
| T03 | KILLED-BY-EXISTING | test_r5_refusals::test_require_verifying_refuses_a_context_that_does_not_check_the_server... (also new) |
| T04 | KILLED-BY-EXISTING | test_r7_mail_context::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused (also new) |
| T08 | KILLED-BY-EXISTING | test_r7_mail_context::test_f4_a_context_with_a_security_level... (also new) |
| R02 | KILLED-BY-NEW-TEST | test_f2_only_ascii_space_is_trimmed_... |
| R04 | KILLED-BY-NEW-TEST | test_f2_a_line_end_inside_the_key_says_more_than_one_line[\r] (first run flagged the M1 test; re-run alone in laneC: the line-end test) |
| R05 | KILLED-BY-NEW-TEST | test_f2_utf16_text_of_either_byte_order_is_named_as_utf16 |
| R08 | KILLED-BY-NEW-TEST | test_f2_spaced_drops_spaces_and_tabs_and_only_with_the_flag |
| C02 | KILLED-BY-NEW-TEST | test_f3_a_bad_secret_file_is_refused_by_the_name_of_its_setting (REAL_IMAP_n) |
| C03 | KILLED-BY-NEW-TEST | test_f3_good_secret_files_pass_and_a_spaced_password_is_allowed |
| C04 | KILLED-BY-NEW-TEST | test_f3_an_os_error_from_the_reader_is_a_refusal_naming_the_setting (the reader maps its own errors, so the test stands in for one it did not; not equivalent) |
| C05 | KILLED-BY-NEW-TEST | test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop (runs `main --dry-fakes`) |
| C06 | KILLED-BY-NEW-TEST | test_f3_a_bad_secret_file... (DESK_HUBSPOT_KEY_FILE) |
| C07 | KILLED-BY-NEW-TEST | test_f3_a_bad_secret_file... (DESK_SMTPP_PASSWORD_FILE) |
| H03 | KILLED-BY-NEW-TEST | test_hubspot_probe::test_a_token_that_is_not_one_plain_word_is_refused_before_any_call |
| L03 | KILLED-BY-NEW-TEST | test_f2_the_listener_probe_sends_no_bytes (survived 12 existing files) |
| L05 | KILLED-BY-NEW-TEST | test_f2_connection_errors_after_an_answer_never_set_the_stop |
| V01 | KILLED-BY-NEW-TEST | test_f2_the_key_read_... (fixed text, no class name) |
| V02 | KILLED-BY-NEW-TEST | test_f2_a_json_text_nested_too_deeply_is_a_value_error_not_a_recursion_error |
| V03 | KILLED-BY-NEW-TEST | test_f2_a_host_that_... (vendor suffix needs the dot) |
| V05 | KILLED-BY-EXISTING | test_r5_refusals::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key] |
| D21 | EQUIVALENT | see above |
| MAIL7 A01 | KILLED-BY-NEW-TEST | test_f4_a_read_after_the_total_deadline_ends_even_when_bytes_are_waiting |
| A02 | KILLED-BY-NEW-TEST | test_f1_a_server_that_is_silent_after_tls_ends_with_the_total_time_error |
| A04 | KILLED-BY-NEW-TEST | test_f4_readline_with_a_limit_returns_at_the_limit_while_the_server_is_still_sending |
| A06 | KILLED-BY-NEW-TEST | test_f2_nothing_is_sent_after_the_total_deadline |
| A07 | KILLED-BY-NEW-TEST | test_f4_a_send_that_blocks_ends_at_the_total_deadline_not_at_the_step |
| A08 | KILLED-BY-NEW-TEST | test_f2_a_connection_error_after_the_total_deadline_is_not_repeatable[1.3] |
| A10 | EQUIVALENT | the send step has the same deadline check (`_BoundedImap.send`), so with the check before the login removed nothing is sent and the error is the same ImapTotalTimeout. CONTROL test `test_f4_a_login_is_not_sent_when_the_total_time_ran_out_during_the_protocol_check` passes on r7f and on the mutant (run: survived), and pins the behaviour |
| A12 | KILLED-BY-NEW-TEST | test_f4_the_literal_cap_is_exact |
| A14 | KILLED-BY-NEW-TEST | test_f4_read_waits_for_all_the_bytes_it_was_asked_for |
| B02 | KILLED-BY-NEW-TEST | test_f4_a_reply_whose_earlier_lines_plus_the_waiting_bytes_pass_the_cap_is_cut_off |
| B03 | KILLED-BY-EXISTING | test_r7d_findings::test_n3_the_cap_is_accepted_and_cap_plus_one_is_refused_whole (the r7c timeout is gone) |
| B04 | NOT-APPLICABLE | the checked line is not in the r7f code (count 0): `used` can never pass the cap, the line check before it refuses first |
| C01 | KILLED-BY-NEW-TEST | test_f2_bytes_that_arrive_with_the_starttls_reply_are_not_read_as_a_reply_after_tls |
| C05 | KILLED-BY-NEW-TEST | test_f5_a_send_timeout_that_is_not_finite_is_refused_before_anything_else |
| E05 | KILLED-BY-NEW-TEST | test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop |
| E06 | KILLED-BY-NEW-TEST | same |
| F02 | KILLED-BY-NEW-TEST | test_f5_the_live_model_client_never_follows_a_redirect |
| G03 | KILLED-BY-NEW-TEST | test_f5_every_hubspot_read_gets_only_the_time_that_is_left |
| T01 | KILLED-BY-NEW-TEST | test_f5_a_certificate_file_with_a_byte_order_mark_is_read |
| T02 | KILLED-BY-NEW-TEST | test_f5_an_end_line_with_a_non_ascii_byte_is_refused_even_when_it_is_indented |
| T03 (MAIL7) | fixed, not a mutant of working code | dead word "anon", see above; mutant T03b (new words dropped) KILLED-BY-NEW-TEST test_f5_a_context_that_offers_an_anonymous_cipher_is_refused |

"Also new" rows: the existing test killed the mutant first; my new test is a second killer. Existing-test rows came from `mut9.py` runs on a snapshot without the r7f file (lane A, lane B for I18 and S08; 15, 12 or 9 relevant existing files each, `-x`).

## Tests: which fail on r7e (fix tests) and which pass there (CONTROL)

`tests/test_r7f_findings.py` run on the r7e source (raw/r7f-file-on-r7e.log): 8 fail, 71 pass. The 8 that fail on r7e are fix tests: the M1 test, the m3 data-link test, 2 anonymous-cipher cases, 4 `test_f6_*` (one of them only because the module does not exist there). The other 71 pass on r7e, so they are CONTROLS: each docstring names the mutant that was really run and that it fails on. Fixing a label, not the test: nothing in the r7f file claims "fails on r7e" unless it is in the list above.

## Changed or deleted existing tests (old to new)

- tests/test_r7m_new.py line 57: cipher list for the client context `ALL:@SECLEVEL=0` to `ALL:!aNULL:@SECLEVEL=0` (setup only, assertions unchanged).
- tests/test_file_call_guard.py: table rows as listed above (no test body changed).
- tests/test_hubspot_probe.py: happy-path test: one assertion added (the owners line shows a count, not an id). Old assertions kept.
- tests/support.py: helper refuses a `data` link.
- tests/test_special_output_files.py, tests/test_portal_demo.py: labels only (comment lines).
- No test deleted. No assertion weakened.

## Numbers (builder-claimed)

- Ruff 0.17.1 `check .`: "All checks passed!"; `format --check .`: "218 files already formatted" (final tree).
- Suppressions (noqa / type: ignore / nosec / nosemgrep / S603), whole tree: frozen 250/121/12/32/52; r7e 175/126/8/32/7; r7f 175/126/8/32/7 (zero new; measured before the netconnect change, which adds none: it was written without any suppression).
- Staged batch b1 (18 files, before the last code changes): 784 passed, 1 failed (test_hygiene_scan_public: literal in my own test, fixed, re-run alone: 8 passed incl. the scan, raw/stage-hy2.log). Batch b2 (11 files): 435 passed, 3 failed, 1 skipped: test_r7m_new x2 (fixed, see above, raw/r7m-after.log) and one test_reset_scripts start_all test "the desk did not answer on its port in time" (the same load flake as r7e item 3; not re-run alone by me, so NOT proven a flake).
- hunt1 (4 files): 621 passed, 1 skipped.
- Hygiene + vendor files on the staged r7f copy: 30 passed (raw/stage2.log).
- Patches: 154 files touched vs frozen; delta 16 files. `build_patches.sh`: BYTE-FOR-BYTE-SAME (frozen + patch == tree, .git and data excluded), DELTA-ON-R7E-GIVES-R7F. apply-matrix-r7f.txt: `git apply --check` rc 0 on checkouts a (CRLF .ps1), b (CRLF .ps1; same bytes as a here) and c (LF .ps1 with the lf patch).

## Deliverables (out/R7F/)

core-fix-on-frozen-r7f.patch (CRLF hunks for reset.ps1, start_all.ps1), core-fix-on-frozen-r7f-lf.patch, core-fix-r7e-to-r7f-delta.patch, sha256-r7f.txt, apply-matrix-r7f.txt, build_patches.sh, apply_matrix.sh, mut9.py, t.sh, loopfiles.sh, checkpoint.md, raw/, mut/.

## Per-file full run (final tree)

- One pytest process per test file (loopfiles.sh; raw/perfile-1.txt, perfile-2.txt, perfile-3.txt, raw/pf-*.log). Together with batches b1, b2 and hunt1 (earlier, on the tree before netconnect), 118 of 140 test files ran (loop 1: 54, loop 2: 31, batches b1+b2+hunt1: 33; the last 16 re-run on the final tree); NOT RUN:
  - Loop 2 was stopped by me at about 04:12 (to free a slot for the reruns; I killed only pids I had started) after 31 of its 53 files; NOT RUN: tests/test_r7_exit_codes.py, test_r7_fake_slow_senders.py, test_r7_no_replace_of_special.py, test_r7b_guard_replant.py, test_r7b_program_helper.py, test_r7c_invariants_output_size.py, test_r7c_one_json_loader.py, test_r7c_program_helper_rejects.py, test_r7c_start_all_parity.py, test_reaper_start_stop.py, test_reminder_email.py, test_review_item_edge_cases.py, test_script_refusals_feed.py, test_server_hardening.py, test_server_stop_guard.py, test_slow_sender.py, test_sonar_p2_feed_optional.py, test_sonar_p2_regex_optional.py, test_stage_confirm_browser.py, test_stamp_locks_and_budget.py, test_tools_and_fakes_pipes.py, test_workflow_run_flags.py (22 files). Loop 1 ran all its 54 files (54 lines in raw/perfile-1.txt).
  - So there is NO full-suite pass of the final tree. Next step: run these 22 files (EV7F does the full suite).
- Result of the files that ran in the loops: 3855 passed in 101 files, one failing file: tests/test_hygiene.py (1 failed, 23 passed): `test_hygiene_scan_public` found a host-name literal in my new test (`tests/test_r7f_findings.py:1068`). FIXED (the literal is built from parts), then re-run on the final tree: raw/final-hy.log, 120 passed (test_hygiene, test_vendor_hosts, test_r7f_findings, test_file_call_guard). The files that touch the last code changes (smtp_provider, imap, tls, real_check, r7c..r7f findings, r5/r6 refusals, r7m, call guard) were re-run on the final tree (perfile-3.txt): all rc 0.
- Stray file with a line break in its name: after every staged run `git ls-files -o` listed no such file in any stage copy; the writer is not among the files run. NOT FOUND (open item 1).
- Why the first two all-files runs ended at 03:55:39 UTC (not 04:00): both logs stop in the same second, about 6 minutes after the start; h1 says Terminated (rc 143), h2 KeyboardInterrupt. My own timeout is 1500 s and my only pkill calls (03:23 and 03:28, patterns of my own mutant lanes) are earlier, so they are not the cause. An outside signal to both processes at once: cause NOT proven (not me by any command I can find). Per the lead rule, such a run is a harness event, not a result. I used `pkill -f` twice earlier against my own lanes: against the new rule, noted.
- Test processes: I ran at most 2 at once from 04:01; before that I briefly had 3 (mutant lanes A and C and V5 around 03:17-03:25).
- Housekeeping: no process of mine is left running (checked with pgrep at the end); mutants ran only on temp copies under tmp-R7F; tree-R7F has no leftover mutant (byte-for-byte check against frozen + patch passed).
