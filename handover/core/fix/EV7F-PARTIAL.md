# EV7F-PARTIAL (evidence runner, raw numbers only, no verdicts)

Tree: /home/user/build/rr6/tree-EV7F (r7f; patch sha 7041492f9555a5601b2d89a80c5fa0aab9a8bf846ff59f69e377b58543394841 applied rc0). Raw files: /home/user/build/rr6/out/EV7F/ (clean/, mut/, hostile/, mut-results.tsv, clean-results.tsv, checkpoint.md).
Run 2026-11-14 04:52 to 05:34 UTC (10:22 to 11:04 IST).

## Machine state (header)
At start: `up 3 min` (container had restarted), load average 0.95 0.93 0.41, 4 cores, 16 GB (523 MB used), 5 python processes. Load stayed under 1 during my runs (the earlier ~95 load and the 4 stray spawn processes were gone after the restart). Other lanes ran pytest concurrently late in the run (pids not mine, left alone).

## Already done before this run (not repeated)
patch apply rc0, ruff check rc0 ("All checks passed!", ruff 0.17.1), ruff format check rc0 (218 files formatted), suppression lists (suppressions.txt, suppressions2.txt).

## Not run (and why)
- Full suite: superseded by r7g, by lead order. The earlier partial pytest-full.log is "cut by lead order, not a result".
- Per-file odd-file loop (perfile.sh): trimmed by lead order.
- Hung-name-lookup via loopback fake as a stand-alone driver: no such case exists in the HD7 driver list (cases: burst_url, check_invariants, fakes_bad, imap_user, log_target, n8n_api, output_target, portal_crm_size, scripts, slow_sender). Only the test-suite coverage exists (tests/test_r7f_findings.py inside the clean sets below).
- The brief's "r7c-era" wording for B02/C01/C05: specs7 was used for every id (table below). specs8 was run only as an extra for the 4 ids that exist in both files (T01 T02 C01 C05).
- Hostile table was not produced against the "EV7D-hostile-table.md" frozen-tree baseline; old = copy of tree-R7E (data/ removed from the copy), new = tree-EV7F. Cases without a row on one side are listed in hostile-table.md as "(no row)".

## Clean selector sets (run ALONE, no -x, inside unshare -n; selector = tests/test_r7f_findings.py + every tests/ file naming the module)
| module | rc | seconds | files | pytest summary line |
|---|---|---|---|---|
| crm_hubspot | 0 | 106s | 11 | 685 passed, 8 skipped, 6 warnings in 103.83s (0:01:43) |
| tls_trust | 0 | 54s | 7 | 440 passed, 10 warnings in 53.51s |
| smtp_outbox | 0 | 83s | 13 | 789 passed, 8 skipped, 2 warnings in 82.04s (0:01:22) |
| imap_count | 0 | 244s | 11 | 615 passed, 10 warnings in 243.70s (0:04:03) |
| smtp_provider | 0 | 238s | 17 | 1165 passed, 8 skipped, 10 warnings in 237.28s (0:03:57) |
| run_real_check | 0 | 433s | 21 | 1733 passed, 4 skipped, 4 warnings in 432.42s (0:07:12) |
| live_claude | 0 | 333s | 16 | 1505 passed, 9 skipped, 41 warnings in 332.12s (0:05:32) |

Logs: out/EV7F/clean/<module>.log (each ends in the pytest summary).

## Mutants (selector = same file set as the module's clean set, `-x`; limits: imap_count 390 s, smtp_provider 630 s, run_real_check 520 s, others 240 s)
| id (spec) | file | description | line | status | first failing test | restore | seconds |
|---|---|---|---|---|---|---|---|
| spec7 G03 | src/lead_desk/crm_hubspot.py | hubspot read: per-read arm removed | line 324 | KILLED | tests/test_r7f_findings.py::test_f5_every_hubspot_read_gets_only_the_time_that_is_left | restored-ok | 17s |
| spec7 T01 | src/lead_desk/tls_trust.py | BOM strip removed | line 41 | KILLED | tests/test_r7f_findings.py::test_f5_a_certificate_file_with_a_byte_order_mark_is_read | restored-ok | 16s |
| spec7 T02 | src/lead_desk/tls_trust.py | END line detection narrowed | line 48 | KILLED | tests/test_r7f_findings.py::test_f5_an_end_line_with_a_non_ascii_byte_is_refused_even_when_it_is_indented | restored-ok | 15s |
| spec7 B02 | src/lead_desk/smtp_outbox.py | reply cap: buffered bytes not counted with used | line 161 | KILLED | tests/test_r7f_findings.py::test_f4_a_reply_whose_earlier_lines_plus_the_waiting_bytes_pass_the_cap_is_cut_off | restored-ok | 14s |
| spec7 A01 | src/lead_desk/imap_count.py | deadline check in _fill removed | line 126 | KILLED | tests/test_r7f_findings.py::test_f4_a_read_after_the_total_deadline_ends_even_when_bytes_are_waiting | restored-ok | 13s |
| spec7 A02 | src/lead_desk/imap_count.py | _fill: socket timeout is the plain step (restarts per byte) | line 128 | KILLED | tests/test_r7f_findings.py::test_f1_a_server_that_is_silent_after_tls_ends_with_the_total_time_error | restored-ok | 7s |
| spec7 A04 | src/lead_desk/imap_count.py | readline: no limit stop (unbounded line) | line 153 | KILLED | tests/test_r7f_findings.py::test_f4_readline_with_a_limit_returns_at_the_limit_while_the_server_is_still_sending | restored-ok | 14s |
| spec7 A06 | src/lead_desk/imap_count.py | send: deadline check removed | line 220 | KILLED | tests/test_r7f_findings.py::test_f2_nothing_is_sent_after_the_total_deadline | restored-ok | 11s |
| spec7 A07 | src/lead_desk/imap_count.py | send: plain step timeout | line 223 | KILLED | tests/test_r7f_findings.py::test_f4_a_send_that_blocks_ends_at_the_total_deadline_not_at_the_step | restored-ok | 21s |
| spec7 A08 | src/lead_desk/imap_count.py | total deadline doubled | line 269 | KILLED | tests/test_r7f_findings.py::test_f2_a_connection_error_after_the_total_deadline_is_not_repeatable[1.3-ImapCountError] | restored-ok | 15s |
| spec7 A12 | src/lead_desk/imap_count.py | literal cap boundary >=  | line 227 | KILLED | tests/test_r7f_findings.py::test_f4_the_literal_cap_is_exact | restored-ok | 14s |
| spec7 A14 | src/lead_desk/imap_count.py | _DeadlineReader.read: short read (size 1) | line 140 | KILLED | tests/test_r7f_findings.py::test_f4_read_waits_for_all_the_bytes_it_was_asked_for | restored-ok | 14s |
| spec7 C01 | src/lead_desk/smtp_provider.py | STARTTLS: plaintext buffer not cleared after wrap | line 322 | KILLED | tests/test_r7f_findings.py::test_f2_bytes_that_arrive_with_the_starttls_reply_are_not_read_as_a_reply_after_tls | restored-ok | 5s |
| spec7 C05 | src/lead_desk/smtp_provider.py | send timeout finite check removed | line 242 | KILLED | tests/test_r7f_findings.py::test_f5_a_send_timeout_that_is_not_finite_is_refused_before_anything_else | restored-ok | 17s |
| spec7 E05 | scripts/run_real_check.py | scrub: min length 4 -> 400 | line 304 | KILLED | tests/test_r7f_findings.py::test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop | restored-ok | 15s |
| spec7 E06 | scripts/run_real_check.py | refusal text: ValueError message printed unscrubbed | line 1044 | KILLED | tests/test_r7f_findings.py::test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop | restored-ok | 13s |
| spec7 F02 | src/lead_desk/live_claude.py | live: redirect refused removed | line 376 | KILLED | tests/test_r7f_findings.py::test_f5_the_live_model_client_never_follows_a_redirect | restored-ok | 17s |
| spec8 (extra) T01 | src/lead_desk/tls_trust.py | minimum TLS 1.0 | line 99 | KILLED | tests/test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection[no_hostname-ssl] | restored-ok | 43s |
| spec8 (extra) T02 | src/lead_desk/tls_trust.py | empty CA file not refused | line 68 | KILLED | tests/test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[empty-trust] | restored-ok | 20s |
| spec8 (extra) C01 | scripts/run_real_check.py | live key not checked | line 1034 | KILLED | tests/test_r7d_findings.py::test_n1_a_bad_live_key_file_is_refused_before_the_cost_lines_and_the_question[missing] | restored-ok | 359s |
| spec8 (extra) C05 | scripts/run_real_check.py | scrub backstop removed | line 1044 | KILLED | tests/test_r7f_findings.py::test_f3_a_setting_value_inside_a_refusal_line_is_replaced_by_the_backstop | restored-ok | 14s |

SURVIVED: none. TIMEOUT: none. BADMUT: none. So the "re-run survivors on the full 22-file set" step had nothing to run.
Restore proof: after all mutants `diff -r -x __pycache__` of src/, scripts/, load_tools/ between tree-EV7F and tree-R7F: all three equal (rc 0). (Only difference in the whole trees: tree-R7F has a .ruff_cache folder; tree-EV7F has no data/ folder.) Every row above says restored-ok (sha of the file equal before and after).

## Hostile drivers (HD7 suite: out/HD7/run_hostile_r7.sh, 80 cases x 2 trees; raw: out/EV7F/hostile/results-r7.jsonl, table: out/EV7F/hostile/hostile-table.md)
Run 05:29:39 to 05:33:04 UTC, rc 0. Rows: old 139, new 139. Counts: traceback in output old 0 / new 0; hang (ran into case timeout) old 0 / new 0; escape character in output old 0 / new 0. Cases named in the brief that this suite holds: FIFO and folder as log/output target (log_target, output_target), huge file (check_invariants 300MB_NUL, 100000_real_shape_353MB), portal_crm_size (100MiB), closed port and slow senders. Symlink and closed-stdin cases: no case with those names in the suite (output_target cases include link variants; see table). Judgement of the rows is left to the reviewer.
