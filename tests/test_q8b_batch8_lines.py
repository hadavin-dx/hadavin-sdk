"""Issue 13 (batch 8): one machine-checked line for every test the independent run found named by no mutant.

A test that passes on the old code is a control (it guards behaviour that must not change). Each control has one line
`<test id> | control | <why it exists> | <how it is checked>`. The check is either `mutant Mnnn` (a planted fault in
tests/q8b_mutants.py that this test, or one of its cases, is the pinned killer of) or `pytest <the test id>` (no planted
fault yet: the test is run by id; that is weaker and is counted by `test_the_lines_say_how_many_controls_have_a_planted_fault`).
The first check below FAILS if an id in EXPECTED_IDS has no line, if a line names a test that does not exist, or if a
`mutant` line names a mutant that is missing or whose killer is another test."""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

LINES = """
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[clean] | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[clean]
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_bounded] | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_bounded]
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_layered] | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_layered]
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_untrusted] | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_untrusted]
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_value] | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_value]
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[safe_head] | control | a producer of text for a model or a log must reach the one redaction point | mutant M149
tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered
tests/test_k5_producers.py::test_no_message_is_cut_with_a_slice_before_it_is_redacted | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_no_message_is_cut_with_a_slice_before_it_is_redacted
tests/test_k5_producers.py::test_in_producer_functions_a_head_slice_only_follows_a_redaction | control | a producer of text for a model or a log must reach the one redaction point | pytest tests/test_k5_producers.py::test_in_producer_functions_a_head_slice_only_follows_a_redaction
tests/test_k5_round11.py::test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return | control | card and record paths: a decoded view or a split secret must stay masked | mutant M156
tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook
tests/test_k5_round11.py::test_the_hook_check_itself_catches_a_missing_none_and_an_alias | control | card and record paths: a decoded view or a split secret must stay masked | mutant M136
tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers
tests/test_k5_round11.py::test_a_second_markup_split_secret_of_the_same_kind_is_masked | control | card and record paths: a decoded view or a split secret must stay masked | mutant M144
tests/test_k5_round11.py::test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header | control | card and record paths: a decoded view or a split secret must stay masked | mutant M147
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%3B] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%26] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%22] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%27] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%2C] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%20] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M154
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[assignment] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[assignment]
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[entity] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[entity]
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[percent] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[percent]
tests/test_k5_round11.py::test_percent_u_and_brace_unicode_escapes_are_decoded | control | card and record paths: a decoded view or a split secret must stay masked | mutant M155
tests/test_k5_round11.py::test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number | control | card and record paths: a decoded view or a split secret must stay masked | mutant M148
tests/test_k5_round11.py::test_the_bare_redactor_ban_also_catches_an_aliased_import | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_the_bare_redactor_ban_also_catches_an_aliased_import
tests/test_k5_round11.py::test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer | control | card and record paths: a decoded view or a split secret must stay masked | mutant M140
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[assignment] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M141
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[entity] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M141
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[percent] | control | card and record paths: a decoded view or a split secret must stay masked | mutant M141
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0D] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0D]
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0B] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0B]
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0C] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0C]
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%E2%80%A8] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%E2%80%A8]
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%1C] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%1C]
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%C2%85] | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%C2%85]
tests/test_k5_round11.py::test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole | control | card and record paths: a decoded view or a split secret must stay masked | mutant M146
tests/test_k5_round11.py::test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused | control | card and record paths: a decoded view or a split secret must stay masked | pytest tests/test_k5_round11.py::test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused
tests/test_k5_round11.py::test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks | control | card and record paths: a decoded view or a split secret must stay masked | mutant M157
tests/test_k5_round11.py::test_more_pairable_values_than_the_bound_are_refused_not_skipped | control | card and record paths: a decoded view or a split secret must stay masked | mutant M153
tests/test_k5_round11.py::test_a_plain_secret_and_a_markup_split_one_are_both_masked | control | card and record paths: a decoded view or a split secret must stay masked | mutant M143
tests/test_k5_round11.py::test_markdown_cannot_be_formed_around_a_placeholder | control | card and record paths: a decoded view or a split secret must stay masked | mutant M152
tests/test_mutation_runner_meta.py::test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each | control | the mutant list itself must stay complete and each mutant must have a real killer | pytest tests/test_mutation_runner_meta.py::test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each
tests/test_mutation_runner_meta.py::test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists | control | the mutant list itself must stay complete and each mutant must have a real killer | pytest tests/test_mutation_runner_meta.py::test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists
tests/test_mutation_runner_meta.py::test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant | control | the mutant list itself must stay complete and each mutant must have a real killer | mutant M142
tests/test_q8b_batch2.py::test_a_link_alone_is_still_removed_whole | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch2.py::test_a_link_alone_is_still_removed_whole
tests/test_q8b_batch2.py::test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch2.py::test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept
tests/test_q8b_batch3.py::test_i1_an_unrelated_not_set_line_stays_readable | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch3.py::test_i1_an_unrelated_not_set_line_stays_readable
tests/test_q8b_batch3.py::test_i3_corpus_is_not_empty_and_disjoint | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch3.py::test_i3_corpus_is_not_empty_and_disjoint
tests/test_q8b_batch3.py::test_i8_a_link_label_before_a_key_keeps_the_next_parameter | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch3.py::test_i8_a_link_label_before_a_key_keeps_the_next_parameter
tests/test_q8b_batch4.py::test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch4.py::test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked
tests/test_q8b_batch4.py::test_j3_the_stop_is_the_same_on_every_path | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch4.py::test_j3_the_stop_is_the_same_on_every_path
tests/test_q8b_batch4.py::test_j4_the_scan_finds_every_shape_of_a_second_list | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch4.py::test_j4_the_scan_finds_every_shape_of_a_second_list
tests/test_q8b_batch4.py::test_j6_no_shipped_text_names_an_internal_decision_number | control | older rows of the redaction table keep their behaviour | pytest tests/test_q8b_batch4.py::test_j6_no_shipped_text_names_an_internal_decision_number
tests/test_q8b_card_text.py::test_n8_the_check_itself_catches_each_way_round | control | card text keeps its rules | pytest tests/test_q8b_card_text.py::test_n8_the_check_itself_catches_each_way_round
tests/test_q8b_card_text.py::test_g8_an_ip_shaped_target_is_a_placeholder | control | card text keeps its rules | pytest tests/test_q8b_card_text.py::test_g8_an_ip_shaped_target_is_a_placeholder
tests/test_q8b_credential_keys.py::test_t1_every_key_the_older_rule_accepted_is_still_accepted | control | a credential key word is still recognised the same way | pytest tests/test_q8b_credential_keys.py::test_t1_every_key_the_older_rule_accepted_is_still_accepted
tests/test_q8b_credential_keys.py::test_n3_no_fragment_of_a_one_letter_value | control | a credential key word is still recognised the same way | pytest tests/test_q8b_credential_keys.py::test_n3_no_fragment_of_a_one_letter_value
tests/test_q8b_credential_keys.py::test_g1_a_one_word_value_is_one_placeholder | control | a credential key word is still recognised the same way | pytest tests/test_q8b_credential_keys.py::test_g1_a_one_word_value_is_one_placeholder
tests/test_q8b_credential_keys.py::test_g2_a_message_is_not_a_credential | control | a credential key word is still recognised the same way | pytest tests/test_q8b_credential_keys.py::test_g2_a_message_is_not_a_credential
tests/test_q8b_credential_keys.py::test_g4_a_value_nested_under_a_credential_key_registers_nothing | control | a credential key word is still recognised the same way | pytest tests/test_q8b_credential_keys.py::test_g4_a_value_nested_under_a_credential_key_registers_nothing
tests/test_q8b_glued_and_whole_values.py::test_r1_the_guard_in_front_of_the_address_pattern_is_bounded | control | a glued or whole value stays masked | pytest tests/test_q8b_glued_and_whole_values.py::test_r1_the_guard_in_front_of_the_address_pattern_is_bounded
tests/test_q8b_glued_and_whole_values.py::test_r3_every_spelling_of_value_is_masked | control | a glued or whole value stays masked | pytest tests/test_q8b_glued_and_whole_values.py::test_r3_every_spelling_of_value_is_masked
tests/test_q8b_glued_and_whole_values.py::test_r10_refused_credential_values_do_not_multiply_the_work | control | a glued or whole value stays masked | pytest tests/test_q8b_glued_and_whole_values.py::test_r10_refused_credential_values_do_not_multiply_the_work
tests/test_q8b_random.py::test_x9_has_cases_to_check | control | the random corpus runs with cases | pytest tests/test_q8b_random.py::test_x9_has_cases_to_check
tests/test_q8b_batch8.py::test_b8_1_a_count_of_tokens_stays_readable_as_a_flag_and_as_a_record_key | control | a plain count of tokens stays readable on both paths | mutant M117
tests/test_q8b_batch8.py::test_b8_2_the_cookie_flag_with_its_exact_name_still_masks_its_value | control | the exact cookie flags keep masking their value as they did before | mutant M158
tests/test_q8b_batch8.py::test_b8_3_a_real_two_word_credential_key_is_never_hidden_by_the_ordinary_look_behind | control | a real two-word credential key is never made readable by the ordinary-word rule | mutant M132
tests/test_q8b_batch8.py::test_b8_4_the_generic_flag_takes_a_scheme_word_with_its_token | control | a flag followed by a scheme word and a token masks both | mutant M104
tests/test_q8b_batch8.py::test_b8_4_the_generic_flags_keep_the_one_word_rule_and_so_does_a_value_that_is_no_scheme_word_and_a_word | control | the one-word value rule of the generic flag is unchanged | pytest tests/test_q8b_batch8.py::test_b8_4_the_generic_flags_keep_the_one_word_rule_and_so_does_a_value_that_is_no_scheme_word_and_a_word
tests/test_q8b_batch8.py::test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time | control | a long run of white space costs linear time (a time test, not a planted fault) | pytest tests/test_q8b_batch8.py::test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time
tests/test_q8b_batch8.py::test_b8_8_a_very_long_run_of_digits_is_read_once | control | a very long run of digits costs linear time (a time test, not a planted fault) | pytest tests/test_q8b_batch8.py::test_b8_8_a_very_long_run_of_digits_is_read_once
tests/test_q8b_batch8.py::test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk | control | a word that only holds cookie inside is no key on either path | pytest tests/test_q8b_batch8.py::test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk
"""

# Written out in full on purpose: the check must fail when a line is deleted from LINES above.
EXPECTED_IDS = {
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[clean]",
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_bounded]",
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_layered]",
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_untrusted]",
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_value]",
    "tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[safe_head]",
    "tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered",
    "tests/test_k5_producers.py::test_no_message_is_cut_with_a_slice_before_it_is_redacted",
    "tests/test_k5_producers.py::test_in_producer_functions_a_head_slice_only_follows_a_redaction",
    "tests/test_k5_round11.py::test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return",
    "tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook",
    "tests/test_k5_round11.py::test_the_hook_check_itself_catches_a_missing_none_and_an_alias",
    "tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers",
    "tests/test_k5_round11.py::test_a_second_markup_split_secret_of_the_same_kind_is_masked",
    "tests/test_k5_round11.py::test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%3B]",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%26]",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%22]",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%27]",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%2C]",
    "tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%20]",
    "tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[assignment]",
    "tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[entity]",
    "tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[percent]",
    "tests/test_k5_round11.py::test_percent_u_and_brace_unicode_escapes_are_decoded",
    "tests/test_k5_round11.py::test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number",
    "tests/test_k5_round11.py::test_the_bare_redactor_ban_also_catches_an_aliased_import",
    "tests/test_k5_round11.py::test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer",
    "tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[assignment]",
    "tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[entity]",
    "tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[percent]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0D]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0B]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0C]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%E2%80%A8]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%1C]",
    "tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%C2%85]",
    "tests/test_k5_round11.py::test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole",
    "tests/test_k5_round11.py::test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused",
    "tests/test_k5_round11.py::test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks",
    "tests/test_k5_round11.py::test_more_pairable_values_than_the_bound_are_refused_not_skipped",
    "tests/test_k5_round11.py::test_a_plain_secret_and_a_markup_split_one_are_both_masked",
    "tests/test_k5_round11.py::test_markdown_cannot_be_formed_around_a_placeholder",
    "tests/test_mutation_runner_meta.py::test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each",
    "tests/test_mutation_runner_meta.py::test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists",
    "tests/test_mutation_runner_meta.py::test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant",
    "tests/test_q8b_batch2.py::test_a_link_alone_is_still_removed_whole",
    "tests/test_q8b_batch2.py::test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept",
    "tests/test_q8b_batch3.py::test_i1_an_unrelated_not_set_line_stays_readable",
    "tests/test_q8b_batch3.py::test_i3_corpus_is_not_empty_and_disjoint",
    "tests/test_q8b_batch3.py::test_i8_a_link_label_before_a_key_keeps_the_next_parameter",
    "tests/test_q8b_batch4.py::test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked",
    "tests/test_q8b_batch4.py::test_j3_the_stop_is_the_same_on_every_path",
    "tests/test_q8b_batch4.py::test_j4_the_scan_finds_every_shape_of_a_second_list",
    "tests/test_q8b_batch4.py::test_j6_no_shipped_text_names_an_internal_decision_number",
    "tests/test_q8b_card_text.py::test_n8_the_check_itself_catches_each_way_round",
    "tests/test_q8b_card_text.py::test_g8_an_ip_shaped_target_is_a_placeholder",
    "tests/test_q8b_credential_keys.py::test_t1_every_key_the_older_rule_accepted_is_still_accepted",
    "tests/test_q8b_credential_keys.py::test_n3_no_fragment_of_a_one_letter_value",
    "tests/test_q8b_credential_keys.py::test_g1_a_one_word_value_is_one_placeholder",
    "tests/test_q8b_credential_keys.py::test_g2_a_message_is_not_a_credential",
    "tests/test_q8b_credential_keys.py::test_g4_a_value_nested_under_a_credential_key_registers_nothing",
    "tests/test_q8b_glued_and_whole_values.py::test_r1_the_guard_in_front_of_the_address_pattern_is_bounded",
    "tests/test_q8b_glued_and_whole_values.py::test_r3_every_spelling_of_value_is_masked",
    "tests/test_q8b_glued_and_whole_values.py::test_r10_refused_credential_values_do_not_multiply_the_work",
    "tests/test_q8b_random.py::test_x9_has_cases_to_check",
    "tests/test_q8b_batch8.py::test_b8_1_a_count_of_tokens_stays_readable_as_a_flag_and_as_a_record_key",
    "tests/test_q8b_batch8.py::test_b8_2_the_cookie_flag_with_its_exact_name_still_masks_its_value",
    "tests/test_q8b_batch8.py::test_b8_3_a_real_two_word_credential_key_is_never_hidden_by_the_ordinary_look_behind",
    "tests/test_q8b_batch8.py::test_b8_4_the_generic_flag_takes_a_scheme_word_with_its_token",
    "tests/test_q8b_batch8.py::test_b8_4_the_generic_flags_keep_the_one_word_rule_and_so_does_a_value_that_is_no_scheme_word_and_a_word",
    "tests/test_q8b_batch8.py::test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time",
    "tests/test_q8b_batch8.py::test_b8_8_a_very_long_run_of_digits_is_read_once",
    "tests/test_q8b_batch8.py::test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk",
}


def _parsed():
    rows = []
    for raw in LINES.strip().splitlines():
        parts = [p.strip() for p in raw.split(" | ")]
        assert len(parts) == 4 and parts[1] == "control" and parts[2], (
            f"a line must be '<id> | control | <reason> | <check>': {raw!r}"
        )
        rows.append(parts)
    return rows


def _function_exists(test_id: str) -> bool:
    path, _, rest = test_id.partition("::")
    name = rest.split("[")[0]
    src = (HERE.parent / path).read_text(encoding="utf-8")
    return re.search(rf"^def {re.escape(name)}\(", src, re.MULTILINE) is not None


def test_every_listed_test_exists_and_every_line_has_a_reason_and_a_check():
    missing = [r[0] for r in _parsed() if not _function_exists(r[0])]
    assert not missing, f"a line names a test that does not exist: {missing}"


def test_the_lines_cover_every_id_the_independent_run_listed():
    from_run = {r[0] for r in _parsed()}
    assert len(from_run) == len(_parsed()), "an id has two lines"
    lacking = sorted(EXPECTED_IDS - from_run)
    assert not lacking, f"an id has no line: {lacking}"
    assert len(EXPECTED_IDS) >= 74


def test_a_line_that_names_a_mutant_names_one_that_exists_with_that_test_as_its_killer():
    src = (HERE / "q8b_mutants.py").read_text(encoding="utf-8")
    bad = []
    for test_id, _, _, how in _parsed():
        if how.startswith("mutant "):
            mid = how.split()[1]
            name = test_id.split("::")[1].split("[")[0]
            block = re.search(rf"mutant\('{mid} .*?\n\s+\w+, '([^']+)'", src, re.DOTALL)
            if block is None or block.group(1).split("[")[0] != name:
                bad.append((test_id, how))
        else:
            if how != f"pytest {test_id}":
                bad.append((test_id, how))
    assert not bad, f"a check does not match its test: {bad}"


def test_the_check_itself_fails_when_a_line_is_missing(monkeypatch):
    dropped = LINES.strip().splitlines()[1:]
    monkeypatch.setattr("tests.test_q8b_batch8_lines.LINES", "\n".join(dropped))
    lacking = sorted(EXPECTED_IDS - {r[0] for r in _parsed()})
    assert lacking, "dropping a line must leave an id without a line"


def test_the_lines_say_how_many_controls_have_a_planted_fault():
    rows = _parsed()
    planted = sum(1 for r in rows if r[3].startswith("mutant "))
    assert planted >= 27, f"only {planted} of {len(rows)} controls have a planted fault"
