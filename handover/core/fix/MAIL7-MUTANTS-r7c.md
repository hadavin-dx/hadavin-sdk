# Mail pass 7 mutants on r7c (EVIDENCE RUNNER, no judging)

**Not run / unresolved first:** 10 of 54 mutants hit the 300 s per-mutant limit without being killed and without finishing (CRASH/TIMEOUT: result unknown, NOT survived); they were not re-run with a longer limit. The whole run took about 105 minutes, not 40, because every surviving mutant needs the full test set (about 250 s).

What went wrong: the first detached start was stopped by the harness 30-minute background limit while mutants C08 (lane A) and B03 (lane B) were planted; both planted files were found, restored from tree-EV7C and verified identical (git diff empty); those mutants were re-run from the start. Final check below.

- Baseline on the restarted container (tree-M7R): 3 failed, 1104 passed, 1 skipped in 249 s. The same 3 [socket] cases of test_r7_no_replace_of_special.py fail; they were deselected in every mutant run (raw: /home/user/build/rr6/out/M7R/baseline.txt).
- Test set: the 22 files of setC.txt (it already contains test_r7c_mail_killers, test_r7c_mail6_killers, test_r7c_smtp_reply_total_cap, test_r7c_head_deadline_errors); CHANGELOG.md in that list is not a test and was dropped. pytest -x, 300 s limit, no network, 2 lanes (scratch copies tree-M7R, tree-M7R2).
- Killers (killers/test_m7_new.py, path-adjusted to tree-M7R): 8 failed, 0 passed on the clean tree (raw: /home/user/build/rr6/out/M7R/killers.txt).

Counts: 54 run; KILLED 32, SURVIVED 12, CRASH/TIMEOUT 10, BADMUT 0; restore mismatches 0.
Raw per-mutant logs: /home/user/build/rr6/out/M7R/raw-<id>.txt; table source results-A.tsv / results-B.tsv in the same folder.

| id | file | planted line | result | desc | seconds |
|---|---|---|---|---|---|
| A01 | src/lead_desk/imap_count.py | 114 | SURVIVED | deadline check in _fill removed | 242s |
| A02 | src/lead_desk/imap_count.py | 116 | SURVIVED | _fill: socket timeout is the plain step (restarts per byte) | 215s |
| A03 | src/lead_desk/imap_count.py | 120 | KILLED tests/test_smtp_provider.py::test_one_call_is_bounded_in_total_not_only_per_step | _fill: timeout-after-deadline no longer ImapTotalTimeout | 86s |
| A04 | src/lead_desk/imap_count.py | 141 | SURVIVED | readline: no limit stop (unbounded line) | 271s |
| A05 | src/lead_desk/imap_count.py | 169 | KILLED tests/test_r7c_mail_killers.py::test_m6_the_total_time_limit_holds_inside_one_slow_line_or_literal[greeting] | deadline set AFTER the greeting (super first) | 11s |
| A06 | src/lead_desk/imap_count.py | 178 | SURVIVED | send: deadline check removed | 273s |
| A07 | src/lead_desk/imap_count.py | 181 | SURVIVED | send: plain step timeout | 273s |
| A08 | src/lead_desk/imap_count.py | 227 | SURVIVED | total deadline doubled | 250s |
| A09 | src/lead_desk/imap_count.py | 238 | KILLED tests/test_real_check_dry.py::test_only_a_reset_after_a_good_login_is_repeated[<lambda>-False0] | login failure classed repeatable (logging_in never set) | 236s |
| A10 | src/lead_desk/imap_count.py | 237 | SURVIVED | _tick before login removed | 242s |
| A11 | src/lead_desk/imap_count.py | 216 | KILLED tests/test_smtp_provider.py::test_a_folder_name_the_program_cannot_send_is_a_clear_fixed_error[Spamf\xf6lder] | folder-name check in _session removed | 87s |
| A12 | src/lead_desk/imap_count.py | 185 | SURVIVED | literal cap boundary >=  | 210s |
| A13 | src/lead_desk/imap_count.py | 85 | KILLED tests/test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[a\nb] | ImapSettings user: printable check removed | 18s |
| A14 | src/lead_desk/imap_count.py | 128 | SURVIVED | _DeadlineReader.read: short read (size 1) | 214s |
| A15 | src/lead_desk/imap_count.py | 253 | KILLED tests/test_real_check_dry.py::test_only_a_reset_after_a_good_login_is_repeated[<lambda>-False1] | TimeoutError treated as repeatable | 182s |
| B01 | src/lead_desk/smtp_outbox.py | 154 | KILLED tests/test_r7c_smtp_reply_total_cap.py::test_a_multi_line_reply_over_the_cap_is_refused_whole | reply cap: continuation lines not counted | 8s |
| B02 | src/lead_desk/smtp_outbox.py | 161 | SURVIVED | reply cap: buffered bytes not counted with used | 187s |
| B03 | src/lead_desk/smtp_outbox.py | 59 | CRASH/TIMEOUT(300s) | reply cap x10 | 305s |
| B04 | src/lead_desk/smtp_outbox.py | 156 | SURVIVED | reply cap check after continuation removed | 245s |
| C01 | src/lead_desk/smtp_provider.py | 321 | SURVIVED | STARTTLS: plaintext buffer not cleared after wrap | 298s |
| C02 | src/lead_desk/smtp_provider.py | 325 | KILLED tests/test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | AUTH refusal ignored | 75s |
| C03 | src/lead_desk/smtp_provider.py | 225 | KILLED tests/test_r7c_head_deadline_errors.py::test_a_real_header_drip_prints_no_trace[hubspot] | recipient pick always the first | 14s |
| C04 | src/lead_desk/smtp_provider.py | 264 | KILLED tests/test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | RCPT goes to the offered address, not the test inbox | 73s |
| C05 | src/lead_desk/smtp_provider.py | 241 | CRASH/TIMEOUT(300s) | send timeout finite check removed | 303s |
| C06 | src/lead_desk/smtp_provider.py | 319 | KILLED tests/test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | STARTTLS refusal: any reply accepted | 72s |
| C07 | src/lead_desk/smtp_provider.py | 191 | KILLED tests/test_r6_refusals.py::test_context_and_ca_file_together_refused | ca_file + context check removed in context given | 23s |
| C08 | src/lead_desk/smtp_provider.py | 257 | KILLED tests/test_r7c_head_deadline_errors.py::test_a_real_header_drip_prints_no_trace[fakes] | send cap check removed | 16s |
| C09 | src/lead_desk/smtp_provider.py | 302 | KILLED tests/test_r7c_mail6_killers.py::test_m6_d11_a_connection_refused_for_its_tls_version_is_closed_at_once | wrap: modern-protocol result closes nothing, still refuses (conn.close removed) | 8s |
| C10 | src/lead_desk/smtp_provider.py | 173 | KILLED tests/test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | smtp password re-read removed: read_secret_file strict spaced off | 114s |
| D01 | src/lead_desk/regfile.py | 75 | KILLED tests/test_r6_refusals.py::test_secret_read_is_bounded | secret read: boundary max bytes | 22s |
| D02 | src/lead_desk/regfile.py | 102 | KILLED tests/test_r6_refusals.py::test_plain_ascii_key_accepted | secret min length boundary | 24s |
| D03 | src/lead_desk/regfile.py | 90 | KILLED tests/test_r7_mail_context.py::test_f2_spaced_mode_drops_only_space_and_tab | spaced: tabs not dropped | 22s |
| D04 | src/lead_desk/regfile.py | 31 | KILLED tests/test_r7c_head_deadline_errors.py::test_a_real_header_drip_prints_no_trace[hubspot] | open_regular: O_NONBLOCK removed (a FIFO open waits) | 14s |
| D05 | src/lead_desk/regfile.py | 77 | KILLED tests/test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key] | read_secret_line: OSError message not fixed (path leaks) | 31s |
| E01 | scripts/run_real_check.py | 661 | KILLED tests/test_r7c_mail_killers.py::test_m6_real_check_refuses_a_bad_secret_file_before_the_start_question | check_secret_files: hubspot key not checked | 8s |
| E02 | scripts/run_real_check.py | 664 | KILLED tests/test_r7c_mail_killers.py::test_m6_real_check_refuses_a_bad_secret_file_before_the_start_question | check_secret_files: mailbox files not checked | 8s |
| E03 | scripts/run_real_check.py | 661 | KILLED tests/test_crm_hubspot.py::test_timeout_after_create_then_retry_finds_it_and_does_not_double | check_secret_files: hubspot read in spaced mode | 200s |
| E04 | scripts/run_real_check.py | 1018 | KILLED tests/test_r7c_mail_killers.py::test_m6_real_check_refuses_a_bad_secret_file_before_the_start_question | check_secret_files: call removed from main | 8s |
| E05 | scripts/run_real_check.py | 304 | CRASH/TIMEOUT(300s) | scrub: min length 4 -> 400 | 306s |
| E06 | scripts/run_real_check.py | 1036 | CRASH/TIMEOUT(300s) | refusal text: ValueError message printed unscrubbed | 304s |
| E07 | scripts/run_live_check.py | 264 | KILLED tests/test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key] | live check: key file problem not checked before the cost line | 31s |
| F01 | src/lead_desk/live_claude.py | 448 | KILLED tests/test_live_claude.py::test_header_trickle_hits_the_total_deadline | live post: thread join without limit | 128s |
| F02 | src/lead_desk/live_claude.py | 376 | CRASH/TIMEOUT(300s) | live: redirect refused removed | 303s |
| F03 | src/lead_desk/live_claude.py | 431 | KILLED tests/test_live_claude.py::test_key_never_leaks | live key cache: error not fixed text | 109s |
| G01 | src/lead_desk/crm_hubspot.py | 258 | KILLED tests/test_crm_hubspot.py::test_key_file_missing_or_empty_is_a_classed_config_error_without_the_path[None] | hubspot key: error not fixed text | 167s |
| G02 | src/lead_desk/crm_hubspot.py | 170 | KILLED tests/test_crm_hubspot.py::test_the_key_goes_only_to_hubspot_hosts_unless_overridden[https://example.test] | hubspot vendor-domain check: any https | 180s |
| G03 | src/lead_desk/crm_hubspot.py | 324 | CRASH/TIMEOUT(300s) | hubspot read: per-read arm removed | 303s |
| T01 | src/lead_desk/tls_trust.py | 41 | CRASH/TIMEOUT(300s) | BOM strip removed | 303s |
| T02 | src/lead_desk/tls_trust.py | 48 | CRASH/TIMEOUT(300s) | END line detection narrowed | 303s |
| T03 | src/lead_desk/tls_trust.py | 30 | CRASH/TIMEOUT(300s) | weak cipher word anon dropped | 303s |
| T04 | src/lead_desk/tls_trust.py | 66 | KILLED tests/test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[over_cap-trust] | CA read errors: only OSError caught (too-big file escapes as FileRefused) | 65s |
| T05 | src/lead_desk/tls_trust.py | 68 | CRASH/TIMEOUT(300s) | empty-after-clean PEM not refused: 'raw.strip()' on cadata skipped | 303s |
| P01 | src/lead_desk/imap_count.py | 235 | KILLED tests/test_r7c_mail6_killers.py::test_m6_d05_a_mailbox_connection_refused_for_its_tls_version_gets_no_logout_either | (pass6 D05) refused TLS version: deadline not cut, LOGOUT sent | 9s |
| P02 | scripts/run_real_check.py | 695 | KILLED tests/test_r7c_mail6_killers.py::test_m6_d20_a_config_name_with_a_no_break_space_is_refused | (pass6 D20) load_env name check uses str.strip | 12s |
