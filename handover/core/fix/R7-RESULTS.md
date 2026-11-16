# R7 results (TASK R7, lead ORDER 268)

Tree: /home/user/build/rr6/tree-R7 (tree-R6 plus the round 7 changes, uncommitted). Nothing committed, nothing pushed.

## 1. What failed, was not run, or is still open (read this first)

1. NOT RUN: the full test suite. I ran affected batches only (list in section 9). The time box (75 minutes, ended about 21:36 UTC) was passed; I used about 15 more minutes for the lead's two late messages (special output files, apply matrix).
2. NOT RUN: `check_invariants` with 100,000 short rows (EV6 item 4: expect exit 1 and 161 lines). Next step: run `python scripts/check_invariants.py` on a book with 100,000 short rows in a temp folder and count lines.
3. NOT DONE (impossible now, no PowerShell here): the `start_all.ps1` check that the program that answers on the port is the one we started. `start_all.sh` has it. Next step: add the same three checks to `start_all.ps1`, pin its text in `tests/test_reset_scripts.py`, and run it on a Windows machine.
4. NOT DONE: the S603 ruling "ONE inline marker on the helper line". r7 has 68 lines mentioning S603 (frozen 52, r6 66). I added `tests/support.py::run_python` (one marker) and used it in all new tests and in `test_reset_scripts.py` (one old site converted), but about 60 older sites in tests still carry their own marker. Next step: convert them to `run_python` / one `popen_python` helper, one batch, then count again (target: 2 markers in support.py).
5. Not verified: the 24 r6 tests that pass on the old frozen code (out/AM/rf-required.txt). The triage agent owns them (out/TRI). I did not touch them and did not classify them.
6. Not verified: `SECLEVEL=0` with no weak cipher left is not detectable from a context (documented in the `require_verifying` docstring). Only weak cipher names and old minimum versions are refused.
7. Tests that use /dev/null (not changed; the box's /dev/null was damaged by a probe, per the lead): tests/test_r4_refusals.py, test_reset_scripts.py, test_book_folder_refusals.py, test_script_refusals_feed.py, test_shell_single_bracket.py, test_cli_refusals.py, test_script_number_limits.py, test_r5_refusals.py, test_file_reader_refusals.py, test_nosemgrep_form.py, test_no_terminal_questions.py; and scripts/start_all.sh, scripts/reset.sh, src/lead_desk/desk.py. Batch B (which holds several of them) passed before the lead's message; I did not re-run them on a repaired /dev/null. My new tests never touch a /dev path.
8. EV6 (1) to (6): (1) done, (2) done, (3) done, (4) NOT RUN (item 2), (5) done (one table row in docs still over 120 characters is a Markdown table, left whole), (6) partly (item 4).

Builder-claimed versus measured: every "killed" below is a measured run of the mutant against the named test (mutate*.py in tmp-R7, removed at the end; the mutation lines are copied in section 8). The suite of the whole repository was not measured.

## 2. Measured gates (final tree)

- `ruff check .`: All checks passed. `ruff format --check .`: 192 files already formatted. `bandit -ll -r src tools scripts -c pyproject.toml`: rc 0, no Medium or High issue.
- Batch B (guard, regfile, cli refusals, hubspot probe, n8n url, book folder, r6 refusals, no-terminal, all test_r7_*): rc 0.
- Batch C (desk edge cases, stamp locks, ai after claim, reminder, review item, portal api, follow-up edge cases): rc 0 after the fixes in section 6.
- Batch D (load, portal demo, portal a*, live claude, crm hubspot): one failure (test_live_claude exit 1 vs 6), fixed, `test_live_claude.py` re-run rc 0. The rest of batch D ran to the end in the first run with that one failure.
- Batch E (the 128-test remainder: tests not in the batches above, e.g. test_smtp_provider, test_ca_file_reads) NOT RUN in this tree after the last edits.
- Apply matrix: `sh out/AM/apply_matrix.sh --check <crlf> <lf>` rc 0, "APPLY MATRIX: OK (every recommended cell passes)"; 104 files touched in both patches; output in out/R7/apply-matrix-r7.txt. Delta patch: `git apply --check` on a copy of tree-R6, rc 0.
- Suppressions (final tree, my count with grep over *.py; EV6's tool may count differently): noqa 248 (frozen 250, r6 246 by EV6; r6 247 by my count), type: ignore 126 (121, 127), nosec 11 (12, 11), lines with S603 68 (52, 66 by EV6; r6 66 by my count).

## 3. Per-finding table (fix, test, fail before)

Fail before = new test files copied onto a clean copy of tree-R6 and run (out/R7 logs are removed with tmp-R7; numbers below are from those runs).

| Id | Fix location | Test | Fail before (r6) |
|---|---|---|---|
| F1 ImapCountError at run_real_check main | scripts/run_real_check.py main | test_r7_mail_context.py::test_f1_* | file cannot be collected on r6 (import of a new constant); the same tests were mutated: F1MAIN 1 failed, F1user 11, F1quote 6 |
| F2 bad body or query answers 400 | demo_only/bad_request.py (AnswersBadRequests), fakes | test_r7_fake_bad_requests.py (52) | cannot be collected on r6 (module missing) |
| F2 (slow or no length sender) | scripts/http_guard.py read_request_body, constants FAKE_BODY_DEADLINE_SECONDS | test_r7_fake_slow_senders.py (7), test_r7_inputs_and_replies.py | slow_senders: not collectable on r6; inputs_and_replies: 15 failed, 15 passed |
| F3 start_all.sh port identity | scripts/start_all.sh fail_start | test_reset_scripts.py (liar stub, STARTID/STARTID2 mutants) | test_reset_scripts: 6 failed, 59 passed on r6 |
| F4 n8n_api exit codes | scripts/n8n_api.py | test_r7_exit_codes.py (28 + burst) | 25 failed, 7 passed |
| BURST --url loopback only, before resolve or connect | scripts/burst (url check) | test_r7_exit_codes.py burst tests (4 far URLs, socket counter) | 4 of 4 failed on r6 |
| F5 to F14, S1 | check_invariants, load_driver, portal_demo, announced length, file-call guard, class names (src/lead_desk/errcode.py), docs, reader | test_r7_inputs_and_replies.py, test_r7_class_names.py, test_file_call_guard.py (PLANTED 201: 81 r6, 17 r7, plus bare read) | class_names: not collectable on r6 (errcode missing) |
| Late: special output files (replace of a pipe or socket) | src/lead_desk/regfile.py `refuse_replacing_special`; called in run_stats.write_stats and demo_only/portal_demo.py _write_flag | test_r7_no_replace_of_special.py (15 tests: fifo, socket, folder, link to fifo, stubbed char device, control, NUL) | probe on a copy of tree-R6: write_stats and _write_flag turned a FIFO and a socket into a regular file (4 of 6 cases replaced); on r7 all 6 untouched. The test file itself cannot be collected on r6 (new function). No real device was used. |

CONTROL labels (new tests that pass on old code, kept as controls, with reason):
- test_r7_exit_codes.py: `test_bad_usage_is_exit_2_before_the_key_or_the_address_is_looked_at[args0..4]`, `test_nothing_listening_is_exit_3`, `test_n8n_refusing_an_activation_is_exit_1` (pin the numbers that did not change, so a renumbering is caught).
- test_r7_inputs_and_replies.py: `test_a_byte_order_mark_in_the_middle_is_not_json`, `test_a_row_ends_at_a_line_feed_...`, `test_a_reply_over_the_cap_is_refused_whole_not_cut`, `test_announced_length_text[lines0,3,4,7,8,9,10,11,12]`, `test_a_slow_sender_that_stops_midway_is_answered_408`, `test_the_full_body_is_read_and_a_short_one_is_408`, `test_a_chunked_body_is_411_and_the_body_is_not_read` (behaviour that already held; they pin it against the new reader).
- test_r7_no_replace_of_special.py::test_a_missing_or_plain_target_is_still_written (control: the normal case keeps working).

Not measured: fail-before of the tests of test_r7_mail_context.py and test_r7_fake_bad_requests.py one by one (the files cannot be collected on r6). Their kill power is shown by the mutants in section 8.

## 4. Special output files (lead message, late)

Class: a name swapped with `os.replace` (the replace changes the name, so it turns a device, pipe or socket into a plain file). Choke point: `regfile.refuse_replacing_special(path)` (stat follows links; a missing path is fine; NUL refused), called before the replace in `write_stats` and in the portal demo flag writer (the only two `os.replace` sites in src, scripts, demo_only, tools: checked by grep). `open_output` already refuses non-regular targets by `fstat` after opening (kept; test covers fifo, socket, folder, link). Ledger, lock, trace and pid files go through `open_output` (not through a replace). Honest gap: `write_stats` swallows OSError, so a refused counters path is silent (the counters file is optional and must never break a send); the proof is that the target is untouched.

## 5. Exit-code pairs (decided with evidence)

Reset family numbers (3 desk running, 4 port or book, 5, 6) are read by shell scripts and pinned by tests/test_reset_scripts.py, so they were not renumbered. 4 means both "port answers" and "book path refused" (documented in docs/limits.md). Script family: 0 ok, 1 check failed, 2 refused or bad usage, 3 unreachable, 4 bad setting or path, 6 stopped by a person (a "no" answer now exits 6, not 1), 7 adapters unreachable. Evidence: tests/test_script_number_limits.py, test_r6_refusals.py::test_shared_exit_code_pairs_are_pinned, test_r7_exit_codes.py.

## 6. Changed tests (old assertion, new assertion, why not weaker)

R7 changes (full text in changed-tests-notes.txt, same folder):
- test_n8n_api_url.py::_message and 2 direct asserts: code was the message string; now an int status plus str(e.value) as the message.
- test_load_tools.py::test_cli_exit_codes: EXIT_INPUT 2 to EXIT_BAD_SETTING_OR_PATH 4 (missing catcher or facts file).
- test_load_driver_facts.py: also patches iter_regular_lines.
- test_r6_refusals.py: imap user text (+ isinstance ValueError); shared exit-code pairs now all distinct; `_H` stub gains `connection`.
- test_r4_refusals.py::ADDRESS_TEXT[burst] (8 tests): new text "must be an http address on this computer".
- test_path_confinement.py (6 asserts): EXIT_INPUT 2 to 4, same text, stricter.
- test_script_number_limits.py: EXIT_STOPPED 1 to 6; EXIT_CHECK_FAILED 1 and EXIT_BAD_SETTING_OR_PATH 4 added.
- test_reset_scripts.py: stand-in desk is a real loopback HTTP server; start_all liar variant and message; one S603 site to run_python.
- test_no_terminal_questions.py (2 tests): exit 1 to 6.
- test_book_folder_refusals.py: regex over the wrapped ps1 and sh text.
- internal:<class> tests: test_review_item_edge_cases.py, test_followup_edge_cases.py:333,391, test_mutation_guards.py:380, test_hung_model_call.py:191, test_stamp_locks_and_budget.py (3), test_ai_after_claim.py:83, test_reminder_email.py:287, test_desk_http_edge_cases.py:890,900: class name to "data" or "error" (error_code); same state and counts asserted; test_r7_class_names pins the mapping.
- test_live_claude.py::test_runner_prints_counts_only_and_asks_first: `returncode == 1` to `== EXIT_STOPPED`; same stdout checks.
Why not weaker: each keeps the same inputs and the same exact comparisons; only the number or word the code is now meant to give changed, and the new value is pinned by a test that fails on r6.

R5 to R6 reconstruction (`diff -ru tree-R5/tests tree-R6/tests`, raw in r5-to-r6-test-diff.txt, 658 lines): 18 files changed, 1 new (test_r6_refusals.py): test_burst_retry (lag 0.6 to 2.0, wait 5 to 15: slower, not weaker), test_cli_refusals, test_crm_hubspot (lag/wait larger), test_except_clause_hierarchy (one tuple split in two), test_file_call_guard (more denied modules and 81 planted shapes: stricter), test_file_reader_refusals (pytest.raises(Exception) to the exact ValueError with match: stricter), test_live_claude (error text "model service error", "driver:error"), test_load_tools (REPLY_MAX_BYTES renamed, type-ignore removed), test_n8n_api_url (fixed texts and exit 3 and "no class name"), test_portal_demo (burst "error" word instead of class names), test_r4/r5_refusals, test_regfile_limits_in_constants, test_reset_scripts (stub desk), test_script_refusals_feed, test_scrub_n8n_export (read(size) stub), test_sonar_p2_feed_optional (process_time instead of perf_counter: not weaker), test_special_output_files. The reasons are the R6 builder's; I did not re-judge each line. The lead's list of 24 r6 tests passing on old code is out/AM/rf-required.txt (triage agent).

## 7. Suppression table (S1)

Counts in section 2. New markers in r7: tests/support.py `run_python` (S603, one marker: our own interpreter, arguments made by the test) and tests/support.py:555 (S603 on a Popen helper: our interpreter and this repository's script). All other S603 markers are older sites (open item 4). tests/test_r7_*.py carry no noqa, no type: ignore and no nosec (removed; ruff and mypy only check the listed rules/paths). One `type: ignore` was removed in test_r7_no_replace_of_special.py before it was kept.

## 8. The 31 mutant rows and the killing test (mail path pass 4)

Rows M01 to M28 and M29, M30 were already killed in r6 by the tests listed in the review; the 7 survivors are now killed by tests in tests/test_r7_mail_context.py (measured, failed counts in brackets):
- M04 (verify_mode test removed): test_m04_optional_chain_check_with_name_check_on_is_refused, test_m04_the_outbox_and_the_mailbox_reader_refuse_it_too [2].
- M18a (no re-check in send): test_m18a_a_context_weakened_after_construction_is_refused_before_any_connection [6].
- M18b (no re-check in _wrap): test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login (control: test_m18b_control_...) [6]; plus test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login for the IMAP side [2].
- M20 (blank DESK_SMTPP_CA_FILE falls back): test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities [3].
- M23 (run_real_check blank REAL_IMAP_n_CA_FILE falls back): test_m23_a_blank_mailbox_ca_file_setting_is_refused [2] (r6 row was a 120 s time-out; this test returns at once).
- M29 (hubspot token weak check): test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection, test_f2_a_token_ending_in_a_non_ascii_space_or_vertical_tab_... [1 + 4].
- M30 (smtp user non-ASCII check removed): test_m30_a_non_ascii_smtp_user_is_refused_where_the_settings_are_made [3].
Other rows, kill list as in REV6M-partial.md: M01 test_ca_file_reads::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[empty-trust]; M02 test_the_context_trusts_only_the_file_and_checks_the_name; M03 test_r5_refusals::test_require_verifying_refuses_a_context_that_does_not_check_the_server[no-name]; M05 test_a_valid_ca_file_still_works[trust]; M06 test_a_non_ascii_character_inside_a_certificate_block_is_refused; M07 ..._fixed_text[text-trust]; M08 test_r5_refusals::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[ledger]; M09 ..._fixed_text[fifo-trust]; M10, M11 test_r6_refusals::test_secret_read_is_bounded; M12, M13 test_smtp_provider::test_password_file_formats_give_a_helpful_fixed_text; M14, M15 test_r6_refusals::test_non_ascii_or_control_key_refused; M16 test_r5_refusals BOM test; M17 test_the_mail_sender_refuses_a_context_that_does_not_check_the_server[none]; M19 test_context_and_ca_file_together_refused; M21 test_the_mailbox_counter_refuses_a_context_...[none]; M22 test_imap_default_trust_rejects_an_untrusted_certificate_and_sends_no_password; M24 test_imap_user_control_character_refused; M25 test_live_claude::test_a_bad_key_file_is_refused_before_the_ledger_and_the_call[UTF-16]; M26 test_r5_refusals ...[key]; M27 test_n8n_api_url::test_a_missing_or_unreadable_key_file_is_a_clean_message; M28 test_file_reader_refusals::test_the_one_reader_refuses_every_bad_content_with_one_error_type. I did not re-run M01 to M03, M05 to M17, M19, M21, M22, M24 to M28 in r7 (they were killed in the r6 review run; r7 changes did not touch their lines except the error text of M27/M10, whose tests I re-ran in batch B).
Extra mutants run in r7 (all killed): STARTID 2 failed, STARTID2 1, F3repr 1, ZEROS 2, DUPCL 2, CAPPLUS1 1, BOOKCHK 1, MODELCAP 1, ERRCODE 6, BOM 1, N8NURL several, F1MAIN 1, DEADLINE 3, BURSTCOUNT 4, IMAPctx 2, F2strip 7, F2hub 4, F4tls 2, F4cipher 1, F5cap 2, F6 1, F2shield, BOUND, DUPNAME, BURSTHOST.

## 9. Test batches run (each under 8 minutes, at most 2 at once)

A (desk, load, portal, 830 tests): timed out at 460 s at 71 percent with two early failures; the failures were from a file being edited during the run (ImportError of the new helper) and one real one (old ConnectionError class name, fixed). Re-run in pieces: batch C and D above. B and C rc 0, D one fix and re-run. The first run of A was never completed as one run. Processes started by me are stopped.

## 10. Output files

core-fix-on-frozen-r7.patch (CRLF kept for the two .ps1 files), core-fix-on-frozen-r7-lf.patch, core-fix-r6-to-r7-delta.patch, apply-matrix-r7.txt, changed-tests-notes.txt, r5-to-r6-test-diff.txt, checkpoint.md, this file.
