# FB7 evidence: fail-before table for patch r7b (EVIDENCE RUNNER, no judging)

Patch: handover/core/fix/core-fix-on-frozen-r7b.patch. OLD = frozen 49d3c859 copy; NEW = frozen + r7b. Run per test file, `unshare -n`, per-test alarm. Times are container clock (UTC; IST = +5:30). The container restarted about 00:54 on 2026-11-14 and killed the previous runner mid-run; this run resumed at 00:57 and finished about 01:05 UTC (06:35 IST).

## What failed or was not run (first)
1. NEW tree: 1 test FAILS: `tests/test_hygiene.py::test_hygiene_scan_public` (hardcoded-literal scan flags lines in tests/test_file_call_guard.py:838,847,850,869,958,973 and tests/test_r4_refusals.py:87, among others; raw: raw3/test_hygiene.NEW.log). It passes on OLD (24 passed, raw4/test_hygiene.OLD.log) because OLD lacks the new test files. This is a defect in the patch's tests; not fixed here (runner never edits).
2. 4 tests SKIPPED on NEW (permission or fifo cases, probably running as root): test_book_folder_refusals::test_a_book_without_read_permission_is_refused; test_n8n_api_url::test_a_key_file_without_read_permission_is_a_clean_message_with_the_reason_only; test_r7b_fake_deep_and_head::test_the_model_fake_answers_a_deep_message_body_too[fakes] and [hubspot]. Their fail-before result is a skip, so no evidence.
3. HANG on OLD (killed by the 150 s per-test alarm, recorded as HANG, not a pass): tests/test_r4_refusals.py::test_run_real_check_config_refusals_have_the_exact_fixed_text and tests/test_reset_scripts.py::test_start_all_sh_refuses_an_unknown_mode_before_it_calls_python. test_reset_scripts OLD log holds 4 alarm markers but my parser matched 2 test ids; the other FAILED rows of that file (incl. the fifo pid-file cases, ~150 s each) may also be alarm kills. Not re-split by hand.
4. 938 ids have no real test result on OLD: ERROR-ON-OLD because the file cannot be imported on OLD (new module or name missing). That counts as "fails before" only in the sense that collection fails; they never executed.
5. Not run: 0 ids lack a result. Not checked: flakiness (each side run once); the NEW run was the pass-2 run (raw3), the OLD run is raw3 except 8 files rerun in raw4 with a 150 s alarm.
6. The 3 setup slips earlier in this task (first pass lacked .git in the work trees; TMPDIR too long for AF_UNIX) were fixed before the numbers below.

## Counts (1439 test ids over the files the patch changes or adds)
| OLD result | ids |
|---|---|
| FAILS on old (assertion/exception), incl. the HANGs below | 343 |
| of which HANG (alarm) | 2 |
| ERROR on old (file cannot be imported, test never ran) | 938 |
| PASSES on old | 158 |
| no result | 0 |

| NEW result | ids |
|---|---|
| PASS | 1434 |
| FAIL | 1 (test_hygiene_scan_public) |
| SKIPPED | 4 |

## Closure
Of the 1182 ids that had no result in the first pass (table-unchecked-1182.tsv), 1182 now have a result on both trees: OLD 938 error + 185 fail + 59 pass; NEW 1178 pass + 4 skipped. Full table: /home/user/build/rr6/out/FB7/table-all-1439.tsv (columns id, old, new, group).

## Tests that PASS on OLD and need a CONTROL label (158)
None of them has the word CONTROL on the line above the def or above its first decorator (checked by script: CONTROL-in-line-above=YES count 0 in both lists). 90 are new ids, 68 are changed existing tests.
Details with file:line: /home/user/build/rr6/out/FB7/passes-on-old-newids.tsv and passes-on-old-changed.tsv.

### New ids (90)
- tests/test_file_call_guard.py::test_at_least_forty_round_six_shapes_are_planted_and_all_are_found
- tests/test_file_call_guard.py::test_the_seventeen_round_seven_shapes_and_the_bare_read_are_planted_and_found
- tests/test_file_call_guard.py::test_a_read_with_a_size_is_not_a_hit_by_itself
- tests/test_file_call_guard.py::test_the_guard_finds_each_planted_shape_on_its_own
- tests/test_file_call_guard.py::test_the_guard_leaves_alone_what_is_not_a_file_call
- tests/test_file_call_guard.py::test_an_import_of_a_denied_module_needs_a_reason_per_file
- tests/test_file_call_guard.py::test_a_listed_reason_that_matches_nothing_is_a_failure
- tests/test_file_call_guard.py::test_a_planted_call_in_every_guarded_folder_is_found
- tests/test_file_call_guard.py::test_a_tls_loader_is_refused_outside_the_two_demo_fakes
- tests/test_r4_refusals.py::test_a_good_number_is_not_refused_by_the_parser[live --max-tokens-100]
- tests/test_r4_refusals.py::test_a_good_number_is_not_refused_by_the_parser[load --seed--5]
- tests/test_r4_refusals.py::test_a_good_number_is_not_refused_by_the_parser[inv --max-503-rate-0.5]
- tests/test_r4_refusals.py::test_a_good_number_is_not_refused_by_the_parser[live --timeout-2.5]
- tests/test_r4_refusals.py::test_check_invariants_never_echoes_the_base_name_of_an_existing_file
- tests/test_r7b_guard_replant.py::test_the_count_of_replanted_shapes_is_pinned
- tests/test_r7b_guard_replant.py::test_every_replanted_shape_is_found
- tests/test_r7b_guard_replant.py::test_a_type_name_in_a_signature_is_no_call
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-c print(1)]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-I -c print(1)]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-Ic print(1)]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-m http.server]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-m pip]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-m lead_desk.server; id]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-m ]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-m]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-X dev x.py]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[-W ignore x.py]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[--command print(1)]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[nothing]
- tests/test_r7b_program_helper.py::test_python_is_refused_with_text_to_run_a_foreign_module_or_no_script[no_such_script.py]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[-e]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[--eval]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[-p]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[--print]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[-r]
- tests/test_r7b_program_helper.py::test_node_and_other_interpreters_are_refused_with_text_to_run[-c]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[sh]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[bash]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[dash]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[zsh]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[ksh]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[cmd]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[powershell]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[pwsh]
- tests/test_r7b_program_helper.py::test_a_shell_name_is_refused_without_a_script_file[/bin/sh]
- tests/test_r7b_program_helper.py::test_a_shell_is_refused_with_an_option_before_a_real_script
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused['a string, not a list']
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[b'bytes']
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[None]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[[]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[()]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['/home/user/build/rr6/venv-br/bin/python', 5]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['/home/user/build/rr6/venv-br/bin/python', None]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['/home/user/build/rr6/venv-br/bin/python', b'x.py']]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['/home/user/build/rr6/venv-br/bin/python', PosixPath('x.py')]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[[PosixPath('/home/user/build/rr6/venv-br/bin/python')]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['/home/user/build/rr6/venv-br/bin/python', 'a\\x00b']]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[['git', ['nested']]]
- tests/test_r7b_program_helper.py::test_a_command_line_that_is_not_a_literal_list_of_plain_strings_is_refused[[<object object at 0x7f1917e977b0>]]
- tests/test_r7b_program_helper.py::test_an_element_that_is_a_str_subclass_is_refused
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[curl http://127.0.0.1/]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[rm -rf x]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[sudo id]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[env id]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[xargs id]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[/usr/bin/python3-not-ours x.py]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[python3 x.py]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[git -c core.sshCommand=id status]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[git -c alias.x=!id x]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[unshare -n -c id]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[unshare --mount true]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[unshare -n sh -c id]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[unshare -n curl x]
- tests/test_r7b_program_helper.py::test_a_program_that_is_not_on_the_short_list_or_is_given_a_loader_option_is_refused[unshare -n]
- tests/test_r7b_program_helper.py::test_the_shapes_the_tests_use_are_accepted
- tests/test_r7b_program_helper.py::test_a_refused_line_starts_nothing
- tests/test_r7b_program_helper.py::test_run_program_runs_a_script_file_and_text_goes_through_a_file
- tests/test_r7b_program_helper.py::test_text_file_is_content_addressed_and_read_back_exactly
- tests/test_r7b_program_helper.py::test_this_repository_paths_exist_for_the_accepted_shapes
- tests/test_special_files_and_plain_text.py::test_bind_still_accepts_every_plain_spelling
- tests/test_special_files_and_plain_text.py::test_hubspot_base_url_plain_text_still_works
- tests/test_special_files_and_plain_text.py::test_a_number_with_a_trailing_line_end_stays_accepted_on_purpose
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-append-pipe]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-append-link-to-pipe]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-append-folder]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-lock-pipe]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-lock-link-to-pipe]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-lock-folder]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[stats-folder]
- tests/test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[trace-folder]

### Changed existing tests (68)
- tests/test_codeant_demo_only.py::test_the_burst_summary_counts_slots_that_got_no_http_answer
- tests/test_codeant_hygiene.py::test_a_desk_setting_in_the_shell_does_not_reach_a_test
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[A]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[A2]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[B]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[D1]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[D2]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[L]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[C0]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[C1]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[D1b]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[D3]
- tests/test_crash_points.py::test_flag_file_hooks_kill_at_every_named_point[N1]
- tests/test_crm_hubspot.py::test_read_back_list_search_lag_and_archive
- tests/test_followup_b.py::test_n8n_api_puts_src_ahead_of_the_repository_folder
- tests/test_hygiene.py::test_hygiene_scan_public
- tests/test_hygiene.py::test_sh_blobs_no_cr
- tests/test_hygiene.py::test_every_cure_in_the_message_works[crlf-unstaged]
- tests/test_hygiene.py::test_every_cure_in_the_message_works[crlf-staged]
- tests/test_hygiene.py::test_every_cure_in_the_message_works[lone-cr-unstaged]
- tests/test_hygiene.py::test_every_cure_in_the_message_works[lone-cr-staged]
- tests/test_hygiene.py::test_a_gitleaks_that_crashes_on_either_copy_fails_the_premise[clean-copy]
- tests/test_hygiene.py::test_a_gitleaks_that_crashes_on_either_copy_fails_the_premise[crlf-copy]
- tests/test_hygiene.py::test_lock_file_hashes_are_allowed_only_at_the_root
- tests/test_ledger_amounts.py::test_a_bad_setting_value_stops_the_desk_with_a_plain_message_not_a_traceback
- tests/test_mode_safety.py::test_reset_sh_refuses_when_ps_is_missing
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[clean]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[exit 2 then clean]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[exit 2 then findings]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[exit 2 three times]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[exit 2 twice then clean]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[findings are never retried]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[unreadable file]
- tests/test_nosemgrep_form.py::test_scan_step_retries_only_exit_2[unreadable rule file]
- tests/test_portal_demo.py::test_burst_keeps_every_answer[cut_body-201]
- tests/test_portal_demo.py::test_burst_keeps_every_answer[cut_error_body-409]
- tests/test_portal_mode.py::test_the_show_all_button_opens_a_grouped_run_of_repeats_and_it_stays_open
- tests/test_reset_scripts.py::test_reset_sh_refuses_when_the_desk_does_not_stop
- tests/test_reset_scripts.py::test_reset_sh_waits_for_a_desk_that_needs_a_few_seconds_to_stop
- tests/test_reset_scripts.py::test_reset_sh_treats_a_pid_file_of_an_ended_but_uncollected_process_as_gone
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[1+1]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[$(touch pwned)]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[-3]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[1.5]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[ ]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[a]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[abc]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[08]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[09]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[0001]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[1234]
- tests/test_reset_scripts.py::test_reset_refuses_a_stop_wait_that_is_not_a_plain_whole_number[99999999999999999999]
- tests/test_review_item_edge_cases.py::test_backfill_classes[pending-internal:CrmError-None-2]
- tests/test_review_item_edge_cases.py::test_backfill_classes[failed-internal:CrmError-hot-2]
- tests/test_review_item_edge_cases.py::test_backfill_classes[pending-internal:CrmNothingStored-None-0]
- tests/test_review_item_edge_cases.py::test_backfill_classes[pending-internal:KeyError-None-0]
- tests/test_review_item_edge_cases.py::test_backfill_classes[pending-refused-hot-1]
- tests/test_review_item_edge_cases.py::test_backfill_classes[unknown-crash_while_sending-hot-1]
- tests/test_review_item_edge_cases.py::test_backfill_classes[unknown-ambiguous-None-1]
- tests/test_review_item_edge_cases.py::test_backfill_classes[pending-unreachable-None-1]
- tests/test_review_item_edge_cases.py::test_backfill_classes[sending-None-None-2]
- tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[URL]
- tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[MAIL]
- tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[ACTIVE_LINK]
- tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[_LOCAL_BROKEN]
- tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[_clean]
- tests/test_vendor_hosts.py::test_root_files_are_the_tracked_ones_not_an_untracked_scratch_file
- tests/test_vendor_hosts.py::test_root_files_fall_back_to_every_file_when_git_is_there_but_the_folder_is_not_a_repository

Raw logs: /home/user/build/rr6/out/FB7/raw3 (pass 2), raw4 (pass 3, 150 s alarm; test_reset_scripts partial kill kept as raw4/test_reset_scripts.OLD.killed-partial.log.txt). Per-file counts: counts-per-file.txt.
