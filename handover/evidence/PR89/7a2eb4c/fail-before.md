# Fail-before: previous head b95b0ca7 (tool and src untouched) with the tests of head 7a2eb4c overlaid

| test | with manifest of the head overlaid | without manifest overlay | first assertion or error line (variant with manifest) |
|---|---|---|---|
| test_mutation_runner::test_the_manifest_pins_the_files_a_demo_copies | FAIL | PASS | `AssertionError: ('tools/mutation_runner.py', 'changed: re-sync the demos and update the manifest and the CHANGELOG')` |
| test_mutation_runner_keywords::test_the_descriptor_is_closed_when_no_file_object_can_take_it | FAIL | FAIL | `AssertionError: the lock folder and the lock file were not each opened once: [11]` |
| test_mutation_runner_keywords::test_the_lock_file_name_does_not_depend_on_the_password | FAIL | FAIL | `AssertionError: two databases behind one unix socket folder got one lock file name` |
| test_mutation_runner_keywords::test_the_lock_name_input_is_exactly_the_allowed_parts_or_unparsed | FAIL | FAIL | `AssertionError: a lock name input was not the expected one (row 2 of the table)` |
| test_mutation_runner_keywords::test_an_error_row_with_no_failing_test_names_the_exit_code_unless_it_is_one | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_Shown'` |
| test_mutation_runner_keywords::test_first_lines_has_an_entry_only_for_a_row_that_has_a_first_error_line | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_Shown'` |
| test_mutation_runner_keywords::test_the_runner_judges_through_judge_report | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_Shown'` |
| test_mutation_runner_keywords::test_the_lock_folder_is_made_private_and_reused | FAIL | FAIL | `AssertionError: the choice of the folder already made it` |
| test_mutation_runner_keywords::test_a_lock_folder_that_others_can_enter_or_that_is_not_the_users_is_refused | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_a_lock_folder_of_another_user_is_refused | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_a_symbolic_link_or_a_file_in_place_of_the_lock_folder_is_refused | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_what_was_opened_as_the_lock_folder_must_be_a_folder | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_a_lock_folder_that_cannot_be_made_is_a_clear_refusal | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_the_lock_folder_is_opened_as_a_folder_without_following_a_link_and_the_file_is_made_under_it | FAIL | FAIL | `ValueError: not enough values to unpack (expected 2, got 1)` |
| test_mutation_runner_keywords::test_the_lock_folder_prefers_the_runtime_folder_of_the_user_when_it_is_private | FAIL | FAIL | `AssertionError: a private XDG_RUNTIME_DIR of this user was not preferred` |
| test_mutation_runner_keywords::test_the_projection_shows_the_class_the_expect_word_and_the_callers_expect_only | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_a_class_name_is_shown_only_when_it_is_on_the_allowlist_of_the_call | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_the_address_of_ci_hides_no_ordinary_class_name_and_no_test_id_of_the_caller | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_a_test_id_is_shown_only_when_it_is_made_of_the_callers_own_text | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_the_projection_replaces_the_parameters_of_a_test_id | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_the_names_the_caller_wrote_on_a_mutant_are_its_only_test_and_its_pinned_function | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_own_names'` |
| test_mutation_runner_keywords::test_the_second_layer_masks_a_secret_that_is_also_caller_text | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_the_callers_expect_text_is_printed_as_given_and_the_docstring_says_so | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_shown_classes_takes_plain_class_names_only_and_is_checked_before_anything_runs | FAIL | FAIL | `TypeError: run_mutants() got an unexpected keyword argument 'shown_classes'` |
| test_mutation_runner_keywords::test_a_form_of_the_password_as_a_class_name_never_reaches_first_lines_in_a_real_run | FAIL | FAIL | `AssertionError: the password in the form 'reversed' was shown as the class name in first_lines` |
| test_mutation_runner_keywords::test_fuzz_every_output_field_holds_only_allowlisted_classes_and_caller_ids | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_the_fuzz_check_fails_when_the_class_or_the_id_allowlist_is_switched_off | FAIL | FAIL | `AttributeError: <module 'tools.mutation_runner' from '/home/user/build/EV-P89-fb-b95b0ca/tools/mutation_runner.py'> has no attribute '_shown_class'` |
| test_mutation_runner_keywords::test_a_row_with_no_passed_value_shows_the_line_and_the_id_as_before | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_Shown'` |
| test_mutation_runner_keywords::test_crash_type_is_checked_against_the_raw_line_also_when_the_class_is_not_shown | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_shown_for'. Did you mean: '_shown_id'?` |
| test_mutation_runner_keywords::test_each_hostile_address_of_the_probes_is_refused[a unix socket folder that is not listed] | FAIL | FAIL | `AssertionError: a hostile address was accepted (a unix socket folder that is not listed): nothing was raised` |
| test_mutation_runner_keywords::test_the_probes_that_are_accepted_stay_accepted_and_a_socket_folder_needs_its_exact_entry | FAIL | FAIL | `ValueError: throwaway_hosts holds exact host names or addresses only (letters, digits, '.', ':', '-'): no pattern, no path` |
| test_mutation_runner_keywords::test_the_address_check_accepts_a_local_address_and_the_address_of_ci[host=::1 port=5432 dbname=app] | FAIL | FAIL | `ValueError: HADAVIN_TEST_PG_DSN is refused: its address is not in a shape the runner can check (a postgresql:// URL with an optional login, a host, a port and ONE database name and nothing after it, or key=value words from host, h` |
| test_mutation_runner_keywords::test_the_address_check_refuses_a_host_that_is_not_on_the_allowlist | FAIL | FAIL | `AssertionError: a host that is not allowed was accepted ('host=/var/run/postgresql dbname=app'): nothing was raised` |
| test_mutation_runner_keywords::test_the_address_check_refuses_an_address_with_no_host | FAIL | FAIL | `AssertionError: an address with neither host nor hostaddr was accepted ('dbname=app'): nothing was raised` |
| test_mutation_runner_keywords::test_a_unix_socket_folder_is_accepted_only_as_an_exact_member_of_the_host_list | FAIL | FAIL | `AssertionError: a unix socket folder that is not listed was accepted: nothing was raised` |
| test_mutation_runner_keywords::test_no_key_of_a_key_value_address_may_be_written_twice | FAIL | FAIL | `AssertionError: a key of the allowlist has no sample here` |
| test_mutation_runner_keywords::test_every_allowed_key_has_a_reason_and_a_refused_sibling | FAIL | FAIL | `AssertionError: the key allowlist changed: every allowed key needs a refused sibling in this test` |
| test_mutation_runner_keywords::test_the_address_check_takes_an_exact_allowlist_and_nothing_wider | FAIL | FAIL | `AssertionError: Regex pattern did not match.` |
| test_mutation_runner_keywords::test_the_host_list_is_checked_for_every_call_also_when_no_variable_is_passed | FAIL | FAIL | `AssertionError: a host list with a pattern was accepted (keywords []): nothing was raised` |
| test_mutation_runner_keywords::test_the_address_check_message_never_shows_the_value | FAIL | FAIL | `Failed: DID NOT RAISE ValueError` |
| test_mutation_runner_keywords::test_run_mutants_refuses_an_address_before_any_folder_or_run | FAIL | FAIL | `AttributeError: module 'tools.mutation_runner' has no attribute '_open_lock_dir'` |
| test_mutation_runner_keywords::test_the_grammar_reads_the_parts_that_the_address_check_uses | FAIL | FAIL | `AssertionError: a unix socket folder was not read as written` |
| test_mutation_runner_keywords::test_one_run_goes_through_the_real_address_check_the_real_lock_folder_and_the_allowlist | FAIL | FAIL | `AssertionError: {'flip': 'LibraryError [expect found] scratch'}` |
| test_mutation_runner_keywords::test_the_three_cases_are_written_in_the_module_docstring | FAIL | FAIL | `AssertionError: the module docstring does not hold the table words: listed, variable absent` |
| test_mutation_runner_keywords::test_the_refusals_come_in_the_order_the_docstring_gives | FAIL | FAIL | `AssertionError: the docstring does not list the refusals in the order of the code: [-1, -1, -1, -1, -1, 10012, -1, -1, -1]` |
| test_mutation_runner_meta::test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets | FAIL | FAIL | `AssertionError: runner: run_mutants does not check the names before it starts: the search string occurs 0 times in tools/mutation_runner.py` |

Passing in both variants: 237 tests (names in the raw XML).
