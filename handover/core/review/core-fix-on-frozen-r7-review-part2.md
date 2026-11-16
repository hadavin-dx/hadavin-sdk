# REV7B review, PART 2, round 7 (fallback reviewer, egm-codebase-details persona)
Subject: frozen 49d3c859 + core-fix-on-frozen-r7.patch (tree-REV7B). Date 2026-11-13, 21:54 to about 22:15 UTC (03:24 to 03:45 IST on the 14th).

## NOT CHECKED (read first)
- Mail path (TLS, IMAP, SMTP, secrets): skipped as ordered. F1-F4 not re-run.
- 5 r7 test files cannot be collected on r6 (their modules do not exist there): test_r7_mail_context, test_r7_no_replace_of_special and 3 others. Only test_r7_exit_codes and test_r7_inputs_and_replies were run on r6 (40 FAILED). The other 3 files were run on r7 only (215 pass there).
- The "15 tests fail on r6" list below comes from that run. I did NOT re-plant a mutation in r7 code to see each test fail (no mutation matrix).
- IPv6 listeners and TIME_WAIT in start_all.sh: reasoned from code, not run.
- F12 and the second half of F13: only partly read. F6 (streaming) and F7 (cap) closed by code read, not by a huge-file run.
- Changed old tests: I read the diffs of test_book_folder_refusals, test_load_tools, test_n8n_api_url, test_r6_refusals, test_script_number_limits, test_reset_scripts, test_file_call_guard (removed lines). I did NOT read test_r4_refusals.py, test_path_confinement.py or the second half of r5-to-r6-test-diff.txt line by line.
- The sandbox /dev/null is a regular file; I did not touch it.
- out/R7/RESULTS.md was not used to form findings.

## Closure table (r6 findings)
| Id | Result | Evidence |
|---|---|---|
| F2 | closed | real hostile run; only known N1 (recursion) remains |
| F5a-c | closed | real run, 23 call shapes, one line, fixed exit codes |
| F6 | closed (code read) | read_jsonl streams with readline, check_invariants.py:183-225 |
| F7 | closed (code read) | row_cap and byte cap; portal view see M2 |
| F8 | closed (real) | nit: trailing space in one line |
| F9 | partly | 143 call shapes planted, 96 caught, 47 missed (see M3) |
| F10 | closed in tree | guard matches only `type(x).__name__` shape (see M3) |
| F11 | closed except one stale sentence | 10 doc sentences tested; M4 |
| F12, F13 | not fully checked | see not-checked |
| F14 | closed (real) | |

## New findings
No Blocker, no Major found.
- M1 Minor: load_tools/load_driver.py:554 (also catcher.py:232-234, demo_only/fake_model_server.py:295-297): a refused path (PathRefused) exits 2; the exit-code scheme says 4 for a bad setting or path. Failing input: `--log <a directory or FIFO>`. Fix: return EXIT_BAD_SETTING_OR_PATH in those three places and adjust test.
- M2 Minor: demo_only/portal_demo.py `_read_capped`: a CRM view larger than 4 MiB (about 20k rows) is refused; confirm the cap fits the largest burst or raise it by a named constant.
- M3 Minor (guard gap): tests/test_file_call_guard.py does not catch getaddrinfo/gethostbyname, ctx.Pool, loop.sock_connect, getattr with a literal name, ssl.SSLContext (47 of 143 planted shapes missed). Fix: add these to HIT_QUALIFIED/METHOD_NAMES and PLANTED_R7.
- M4 Minor (stale doc): docs/settings.md:164 says "the name of the error type"; r7 removed class names from output. Fix wording.
- M5 Minor: start_all.sh when pid files already exist exits 1 (the scheme says one of 2..7); fix: exit 2 or 6 with one line.
- M6 Minor: start_all.sh with a FIFO as fakes.log returns 0 and does not refuse; regfile check should be applied to the log path.
- N5 Nit: scripts/n8n_api.py list prints workflow names with ESC/newline raw; escape them.
- Known and not re-reported: N1-N4.

## 15 r7 tests that FAIL on r6 (real run)
test_a_bad_n8n_address_is_exit_4[ftp://127.0.0.1]; test_a_body_that_cannot_be_encoded_is_exit_4; test_a_key_file_that_is_not_one_plain_word_is_exit_4[short]; test_a_missing_key_setting_is_exit_4; test_a_name_that_matches_none_or_two_workflows_is_exit_2[data0]; test_a_workflow_file_that_is_missing_or_not_json_is_exit_4; test_an_unusable_answer_from_n8n_is_exit_3[http-401]; test_burst_refuses_a_far_address_before_any_lookup_or_connect[http://evil.example:9/leads]; test_n8n_refusing_an_import_is_exit_1; test_a_byte_order_mark_in_front_of_the_first_row_is_dropped; test_a_path_that_cannot_be_used_ends_the_checker_with_4_and_a_bad_file_with_2; test_a_reply_of_6200_rows_is_read_whole; test_reset_check_refuses_a_book_that_is_a_named_pipe_with_exit_4; test_the_exit_constants_have_one_meaning_each_and_the_documented_values; test_the_model_log_has_its_own_cap_and_main_passes_it. (40 FAILED in total.)
Tests that pass on both r6 and r7 (22 seen in the r6 run, e.g. test_announced_length_text[lines9-want9], test_the_full_body_is_read_and_a_short_one_is_408): they are controls for behaviour that did not change; I did not write a reason for each one. Honest gap.

## Changed old tests
No weaker assertion found in the diffs read, except known N4. test_reset_scripts.py got stricter (real stand-in desk, four foreign-listener cases, pid and process-gone checks).

## Verdict
No Blocker, no Major. 6 Minor findings (M1-M6) and 1 Nit, plus gaps listed above. Not a clean round: M1, M3 and M4 should be fixed in the same push, then no new review round is needed for them.
