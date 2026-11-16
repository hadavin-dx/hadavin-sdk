# Q8b batch 7 - PR notes (builder)

Branch `core/q8b-b7` (from `origin/wip/cloud-q8b-b6` at 8e8ccbef), pushed to `wip/cloud-q8b-b7` only. No PR, no merge.

## What each round-7 issue became (one class, fixed at the shared rules in `guard/redact.py`; the record walk in `k1b/redaction.py` stays the source the card rules must match)

| Issue | Class | Fix |
|---|---|---|
| 1 | digits glued behind a credential word (`pass2`, `--auth0-key`, `oauth2`) | the bare words (`pass`, `auth`, `session`, `bearer`) take up to 9 digits before `=`/`:`; flag names end with `[0-9]*`; the `auth0`/`oauth2` exceptions are deleted and their pins now say "masked" |
| 2 | plural of a credential word as a flag (`--secrets`, `--api_tokens`) | one optional plural `s` after each flag word, except `tokens` after a count word (`max_tokens`), which stays a count; the drift test now counts the keys it compared and pins a floor of 210, and skips only by last word (a stated list) |
| 3 | `Cookie` / `COOKIE` / `Set-Cookie` as a key, any letter case, five paths | `cookie`/`cookies` are credential words of the record walk and flag words of the card rules; the curl cookie rule is case-insensitive and takes up to two prefix words; the assignment rule also takes a word glued behind `;` (`Cookie=a;b`) |
| 4 | `Authorization` scheme word + token (`Bearer`, `Basic`, `Token`, `Digest`, `ApiKey`) in flag, `=` and `:` forms | the scheme word is part of the value after a credential flag; a Digest header is masked to the end of the line. The generic second word after a credential flag stays masked-as-value by design: this is a stated design choice (LIMITS and CHANGELOG say so) |
| 5 | over-masking: `bypass`, `compass`, `obsession`, `author` readable in every form; real keys (`bypasspass`, `compassword`, `xbypass`) stay masked | one look-behind per ordinary word that must start a word, in all key-value, quoted and flag rules; both directions are probed (`tests/test_q8b_batch7.py`, `q8b_key_corpus.py`) |
| 6 | prefix groups / comments / CHANGELOG wording | third flag prefix group (`{0,3}`), cost named in LIMITS and CHANGELOG as "up to 40 letters or digits glued in front"; the comments at `tests/test_q8b_batch6.py` (drift test) and `k1b/redaction.py:148-153` are corrected |
| 11 | tests that pass on old main | the table below |

## Issue 11: one line per test that passes on old main code

Source list: `handover/evidence/Q8b/8e8ccbef/failbefore-main-passed-on-old.txt` (139 test ids, 120 distinct test functions; a parametrized function is one line with its count in the third column).
"Killed by mutant" means a mutant in `tests/*_mutants.py` makes that test fail first (so the test can fail for the case it names). "control" means the test guards a behaviour that already holds on old main; the reason is given. I read the names and the first lines of the controls; I did not mutate the controls marked "no mutant run".
The two path-hygiene tests pass on old main because the fix lives in `tests/`, not in `src`; they now each have a mutant (M111, M112) that puts the fault back in `tests/demo_askdata/corpus.py`. Controls of the batch-7 tests that also passed on 8e8ccbef got M113-M115.

| file | test function | ids | reason |
|---|---|---|---|
| test_k5_producers.py | `test_every_redaction_function_reaches_the_one_choke_point` | 6 | control: a call-graph scan of src that already held on 8e8ccbef; it fails only if a redaction function stops routing to the one choke point (code shape, not text); this batch changes no routing |
| test_k5_producers.py | `test_every_module_that_calls_a_model_is_registered` | 1 | control: a scan of src for model callers vs the registry; already true on 8e8ccbef; this batch adds no model caller |
| test_k5_producers.py | `test_no_message_is_cut_with_a_slice_before_it_is_redacted` | 1 | control: a source scan (no head slice before redaction); already true on 8e8ccbef |
| test_k5_producers.py | `test_in_producer_functions_a_head_slice_only_follows_a_redaction` | 1 | control: a source scan, same class as the line above; already true on 8e8ccbef |
| test_k5_round11.py | `test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_the_hook_check_itself_catches_a_missing_none_and_an_alias` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_only_clean_and_the_slack_block_call_the_card_sanitisers` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_a_second_markup_split_secret_of_the_same_kind_is_masked` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_pass_one_masks_survive_the_swap_for_every_value_terminator` | 6 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card` | 3 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_percent_u_and_brace_unicode_escapes_are_decoded` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_the_bare_redactor_ban_also_catches_an_aliased_import` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record` | 3 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked` | 6 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_more_pairable_values_than_the_bound_are_refused_not_skipped` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_a_plain_secret_and_a_markup_split_one_are_both_masked` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_k5_round11.py | `test_markdown_cannot_be_formed_around_a_placeholder` | 1 | control: an existing K5 round-11 test of redaction behaviour that main already had (it passes on old main by design); batch 7 changes only the key, flag, cookie and authorization rules, not the markup, unicode, pairing or hook rules this test reads (it must still pass in the full run on the final head); no mutant run for it in this batch |
| test_mutation_runner.py | `test_mutation_judge_verdicts` | 1 | killed by mutant judge:@mutation_runner |
| test_mutation_runner.py | `test_the_runner_kills_a_mutant_of_a_tiny_package` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_mutant_path_that_is_absolute_or_names_a_drive_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_mutant_path_with_a_dotdot_part_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_mutant_path_with_a_stream_name_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_mutant_with_a_short_expect_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_inside_refuses_a_path_through_a_link_out_of_the_tree` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_inside_refuses_the_tree_itself` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_locate_does_not_list_a_file_link_out_of_the_tree` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_locate_does_not_list_a_file_through_a_folder_link_out_of_the_tree` | 1 | control: runner path-safety test of tools/mutation_runner.py; the runner is not changed here, so it passes on old and new code (the file tools/mutation_runner.py is not changed in batch 7) |
| test_mutation_runner.py | `test_the_runner_checks_a_forged_mutant_path_again` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree` | 1 | control: runner path-safety test (tools/mutation_runner.py is not changed in batch 7) |
| test_mutation_runner.py | `test_the_runner_children_see_an_allowlisted_environment_only` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_path_that_starts_with_a_dash_is_refused_in_both_grammars_and_dot_slash_is_the_way_out` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_path_that_starts_with_an_at_sign_is_refused_because_pytest_reads_it_as_an_argument_file` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_failing_tree_kill_still_kills_the_child` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_baseline_run_gets_its_own_timeout` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_baseline_timeout_of_zero_is_not_unset` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_timeout_kills_the_whole_process_tree_not_only_pytest` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_an_interrupt_while_waiting_kills_the_run_and_is_not_swallowed` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_background_process_left_by_a_finished_run_is_killed_too` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_pytest_ini_planted_in_a_parent_folder_is_not_picked_up` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_runner_keeps_a_symlink_a_link` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_junit_with_a_doctype_or_entity_is_refused_not_parsed` | 1 | killed by mutant fix:@mutation_runner |
| test_mutation_runner.py | `test_the_runner_wires_pinned_so_another_failing_test_is_other_test` | 1 | killed by mutant fix:@mutation_runner |
| test_mutation_runner.py | `test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on` | 1 | killed by mutant b2:@mutation_runner |
| test_mutation_runner.py | `test_a_junit_text_over_the_ceiling_is_refused` | 1 | killed by mutant b2:@mutation_runner |
| test_mutation_runner.py | `test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one` | 1 | killed by mutant b3:@mutation_runner, runner:@mutation_runner |
| test_mutation_runner.py | `test_the_leading_class_of_an_error_line_is_parsed_not_searched` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_allow_crash_without_a_crash_type_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_taskkill_is_resolved_under_system_root` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_termination_signal_cleans_up_the_run` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_signal_handlers_are_restored_and_an_ignored_sighup_stays_ignored` | 1 | control: runner signal test (tools/mutation_runner.py is not changed in batch 7) |
| test_mutation_runner.py | `test_a_signal_during_the_cleanup_does_not_cut_the_cleanup_short` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_second_signal_cannot_cut_short_the_cleanup_of_the_first` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_signal_while_the_child_is_being_started_still_kills_the_child` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_signal_while_the_temp_folders_are_removed_leaves_none` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_process_group_is_killed_while_its_leader_is_not_yet_reaped` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_pytest_run_writes_no_file_into_its_working_folder_and_leaves_no_temp_folder` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_refused_run_leaves_no_temp_folder` | 1 | control: runner clean-up test (tools/mutation_runner.py is not changed in batch 7) |
| test_mutation_runner.py | `test_the_first_lines_of_an_earlier_run_do_not_leak_into_the_next` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_finished_run_does_not_kill_the_tree_on_windows` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_leader_reaped_by_someone_else_is_known_as_ended_so_its_group_is_not_signalled` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_run_mutants_is_not_re_entrant_and_a_nested_call_leaves_the_outer_one_alone` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_relative_link_that_points_out_of_the_tree_is_refused_at_snapshot_time` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_junction_under_src_or_a_fixture_folder_is_refused_before_the_copy` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_the_colon_refusal_says_a_path_may_not_contain_a_colon_and_the_docstring_states_it` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_child_reaped_by_someone_else_is_an_error_result_not_exit_code_zero` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_reaped_child_is_an_error_row_for_a_mutant` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_reaped_baseline_is_refused_as_reaped_not_as_a_failing_baseline` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner.py | `test_a_junction_as_the_folder_itself_or_a_part_of_its_path_is_refused` | 1 | killed by mutant runner:@mutation_runner |
| test_mutation_runner_meta.py | `test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each` | 1 | control: a guard on the layout of the manifest test files; fails if a manifest test is lost or doubled |
| test_mutation_runner_meta.py | `test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists` | 1 | control: a guard on the manifests (each mutant names an existing killer test); meaningful for the new M93-M115 because it fails if one names a missing test (it caught one missing killer in this batch before I added it) |
| test_mutation_runner_meta.py | `test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant` | 1 | control: exit-code guard of the mutants script |
| test_q8b_batch2.py | `test_the_plan_line_survives_a_masked_value_at_the_end_of_the_text` | 1 | killed by mutant M50@q8b |
| test_q8b_batch2.py | `test_a_link_alone_is_still_removed_whole` | 1 | control: guards that the card link rule still removes a bare link; the batch-2 change was around it and left it alone |
| test_q8b_batch2.py | `test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept` | 1 | control: guards the simple case that must keep working under the batch-7 scheme-word change (the old code and the new code both mask it) |
| test_q8b_batch3.py | `test_i1_an_unrelated_not_set_line_stays_readable` | 1 | control: over-masking guard for a line with no credential word |
| test_q8b_batch3.py | `test_i3_corpus_is_not_empty_and_disjoint` | 1 | control: checks the size and disjointness of the corpus lists themselves (data, no product code); batch 7 adds rows and this keeps them counted |
| test_q8b_batch3.py | `test_i7_a_flag_or_a_key_ends_the_value` | 1 | killed by mutant M62@q8b |
| test_q8b_batch3.py | `test_i8_a_link_label_before_a_key_keeps_the_next_parameter` | 1 | control: over-masking guard (the next parameter after a link label stays readable); already held on old code |
| test_q8b_batch4.py | `test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked` | 1 | control of a test helper: shows the older-rule comparison itself reports a half-masked value (it tests the checker, not src) |
| test_q8b_batch4.py | `test_j1_every_cookie_key_the_older_cookie_rule_masked_is_still_masked_with_its_jar` | 1 | killed by mutant M77@q8b |
| test_q8b_batch4.py | `test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked` | 1 | killed by mutant M54@q8b, M55@q8b, M64@q8b |
| test_q8b_batch4.py | `test_j2_ordinary_words_stay_readable_in_a_record` | 1 | killed by mutant M60@q8b |
| test_q8b_batch4.py | `test_j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value` | 1 | killed by mutant M70@q8b |
| test_q8b_batch4.py | `test_j3_the_stop_is_the_same_on_every_path` | 1 | control: the value stop characters agree on the five paths; already true on old code, and batch 7 changes none of them |
| test_q8b_batch4.py | `test_j4_names_that_are_no_credential_stay_readable` | 1 | killed by mutant M85@q8b |
| test_q8b_batch4.py | `test_j4_the_scan_finds_every_shape_of_a_second_list` | 1 | control of a test helper: the scan of the repo for a second copy of a word list (tests the scan, not src) |
| test_q8b_batch4.py | `test_j6_no_shipped_text_names_an_internal_decision_number` | 1 | control: a scan of shipped text for internal decision numbers; true on old code and new code |
| test_q8b_batch6.py | `test_d6_a_flag_with_an_ordinary_word_stays_readable` | 1 | killed by mutant M91@q8b |
| test_q8b_batch6.py | `test_no_test_names_a_fixed_path_in_the_shared_temporary_folder` | 1 | mutant M112 (new this batch: puts the fault back in the corpus file; the fix lives in tests/, so old src cannot fail it) |
| test_q8b_batch6.py | `test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file` | 1 | mutant M111 (new this batch: puts the fault back in the corpus file; the fix lives in tests/, so old src cannot fail it) |
| test_q8b_card_text.py | `test_n6_f6b_a_domain_outside_code_is_bracketed` | 1 | killed by mutant M18@q8b, M45@q8b |
| test_q8b_card_text.py | `test_n8_the_check_itself_catches_each_way_round` | 1 | control of a test helper (the check catches both directions); no src involved |
| test_q8b_card_text.py | `test_g8_an_ip_shaped_target_is_a_placeholder` | 1 | control: an address-shaped target already became a placeholder on old code; batch 7 does not touch the address rules |
| test_q8b_credential_keys.py | `test_s4_two_placeholders_are_accepted` | 1 | killed by mutant M5@q8b |
| test_q8b_credential_keys.py | `test_s7_a_quoted_attempt_without_quotes_is_refused` | 1 | killed by mutant M4@q8b |
| test_q8b_credential_keys.py | `test_t1_every_key_the_older_rule_accepted_is_still_accepted` | 1 | control by design: the superset guard (no key the older rule masked becomes readable); it passes on old and new code and fails only if a key is lost |
| test_q8b_credential_keys.py | `test_n1_a_list_under_a_setting_key` | 1 | killed by mutant M16@q8b |
| test_q8b_credential_keys.py | `test_n3_no_fragment_of_a_one_letter_value` | 1 | control: a one-letter value registers no fragments; the registry code is not changed by this batch |
| test_q8b_credential_keys.py | `test_g1_a_one_word_value_is_one_placeholder` | 1 | control: placeholder numbering for one word; unchanged code |
| test_q8b_credential_keys.py | `test_g2_a_message_is_not_a_credential` | 1 | control: over-masking guard for message text; unchanged code |
| test_q8b_credential_keys.py | `test_g4_a_value_nested_under_a_credential_key_registers_nothing` | 1 | control: nesting rule of the registry; unchanged code |
| test_q8b_glued_and_whole_values.py | `test_r1_the_guard_in_front_of_the_address_pattern_is_bounded` | 1 | control: a bound/timing guard on the address pattern; unchanged by this batch |
| test_q8b_glued_and_whole_values.py | `test_r3_every_spelling_of_value_is_masked` | 1 | control: every spelling of the word value stays masked; batch 7 keeps it (it passes on old and new code) |
| test_q8b_glued_and_whole_values.py | `test_r4_a_number_or_one_word_in_a_secret_is_not_registered` | 1 | killed by mutant M41@q8b |
| test_q8b_glued_and_whole_values.py | `test_r10_refused_credential_values_do_not_multiply_the_work` | 1 | control: a work-bound guard on refused values; unchanged code |
| test_q8b_random.py | `test_x9_has_cases_to_check` | 1 | control: the random run checked at least 100 cases (a guard that the run is not empty) |

## Gates on the final head b7d7cd18 (exit codes)
ruff check rc=0 (All checks passed); ruff format --check rc=0 (337 files formatted); bandit -ll -r src demos tools rc=0; tools/scan_repo.py rc=0; tests/q8b_mutants.py 115 of 115 good (first run 113/115, two wrong-reason rows M99/M104 fixed, then 2/2); tests/stage_mutants.py 37 of 37 good rc=0; tests/mutation_runner_mutants.py 64 of 64 good rc=0; full pytest `-m "not live and not perf"` rc=0: 10815 passed, 1 skipped, 29 deselected, 16 xfailed. The first full run (07:07) failed 149+30 because my Postgres was set up wrong (SQL_ASCII encoding, server env without PGHOST); fixed the Postgres, re-ran the one full run on the same head. The timing test `test_the_timing_harness_flags_a_quadratic_stand_in` passed this time; it is a known flake (fix on `core/fix-timing-harness-flake`), not touched.
Fail-before: with 8e8ccbef src and the new tests, 27 of 43 tests in test_q8b_batch7.py + test_q8b_batch6.py fail; the 16 that pass are listed in the report as controls or earlier-batch tests.
