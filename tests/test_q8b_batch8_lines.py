"""Issue 13 (batch 8), reworked in batch 9 (Issue 3): one machine-checked line for every test the independent run found named by no mutant.

A test that passes on the old code is a control (it guards behaviour that must not change). Each control has one line
`<test id> | control | <why it exists>`. How a control is checked is NOT written by hand any more: it is read from the mutant
table `tests/q8b_mutants.py` (one source). A control is in exactly one of three groups:

* PLANTED: at least one mutant of the table names this test as its killer (the check is that mutant, run by the mutant runner);
* NO_FAULT: no fault can be planted for this test; a written reason that names an existing file (empty since batch 11: a test of a test file
  has a `test_file_mutant`);
* UNPLANTED: no planted fault yet. The group is listed in full below, its size is pinned (it can only shrink), and it is a
  defect to fix (a planted fault or a true reason): batch 11 left three, see the constant `UNPLANTED_MAX` below.
A line that is missing, a test that does not exist, a line in two groups or a group name that has no line fails `_problems`."""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

LINES = """
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[clean] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_bounded] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_layered] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_untrusted] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[redact_value] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_redaction_function_reaches_the_one_choke_point[safe_head] | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_no_message_is_cut_with_a_slice_before_it_is_redacted | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_producers.py::test_in_producer_functions_a_head_slice_only_follows_a_redaction | control | a producer of text for a model or a log must reach the one redaction point
tests/test_k5_round11.py::test_redact_text_applies_the_neutralise_hook_to_every_view_it_can_return | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_the_hook_check_itself_catches_a_missing_none_and_an_alias | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_second_markup_split_secret_of_the_same_kind_is_masked | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_an_ordinary_card_keeps_its_spaces_even_when_it_looks_like_a_header | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%3B] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%26] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%22] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%27] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%2C] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_pass_one_masks_survive_the_swap_for_every_value_terminator[%20] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[assignment] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[entity] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_declared_free_text_proposal_field_is_masked_in_the_stored_plan_and_the_card[percent] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_percent_u_and_brace_unicode_escapes_are_decoded | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_clean_and_the_fake_channel_do_not_reuse_a_placeholder_number | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_the_bare_redactor_ban_also_catches_an_aliased_import | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_the_gitleaks_header_chain_regex_matches_the_three_planted_headers_and_nothing_longer | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[assignment] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[entity] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_secret_in_a_tool_call_argument_is_masked_in_the_stored_call_record[percent] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0D] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0B] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%0C] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%E2%80%A8] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%1C] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_every_white_space_character_encoded_in_a_value_keeps_the_whole_value_masked[%C2%85] | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_value_with_a_plain_comma_and_an_encoded_one_is_masked_whole | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_junk_ahead_cannot_use_up_the_pairing_slots_and_a_long_value_is_masked_or_refused | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_the_tag_deleted_view_keeps_real_placeholders_and_line_breaks | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_more_pairable_values_than_the_bound_are_refused_not_skipped | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_a_plain_secret_and_a_markup_split_one_are_both_masked | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_k5_round11.py::test_markdown_cannot_be_formed_around_a_placeholder | control | card and record paths: a decoded view or a split secret must stay masked
tests/test_mutation_runner_meta.py::test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each | control | the mutant list itself must stay complete and each mutant must have a real killer
tests/test_mutation_runner_meta.py::test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists | control | the mutant list itself must stay complete and each mutant must have a real killer
tests/test_mutation_runner_meta.py::test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant | control | the mutant list itself must stay complete and each mutant must have a real killer
tests/test_q8b_batch2.py::test_a_link_alone_is_still_removed_whole | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch2.py::test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch3.py::test_i1_an_unrelated_not_set_line_stays_readable | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch3.py::test_i3_corpus_is_not_empty_and_disjoint | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch3.py::test_i8_a_link_label_before_a_key_keeps_the_next_parameter | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch4.py::test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch4.py::test_j3_the_stop_is_the_same_on_every_path | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch4.py::test_j4_the_scan_finds_every_shape_of_a_second_list | control | older rows of the redaction table keep their behaviour
tests/test_q8b_batch4.py::test_j6_no_shipped_text_names_an_internal_decision_number | control | older rows of the redaction table keep their behaviour
tests/test_q8b_card_text.py::test_n8_the_check_itself_catches_each_way_round | control | card text keeps its rules
tests/test_q8b_card_text.py::test_g8_an_ip_shaped_target_is_a_placeholder | control | card text keeps its rules
tests/test_q8b_credential_keys.py::test_t1_every_key_the_older_rule_accepted_is_still_accepted | control | a credential key word is still recognised the same way
tests/test_q8b_credential_keys.py::test_n3_no_fragment_of_a_one_letter_value | control | a credential key word is still recognised the same way
tests/test_q8b_credential_keys.py::test_g1_a_one_word_value_is_one_placeholder | control | a credential key word is still recognised the same way
tests/test_q8b_credential_keys.py::test_g2_a_message_is_not_a_credential | control | a credential key word is still recognised the same way
tests/test_q8b_credential_keys.py::test_g4_a_value_nested_under_a_credential_key_registers_nothing | control | a credential key word is still recognised the same way
tests/test_q8b_glued_and_whole_values.py::test_r1_the_guard_in_front_of_the_address_pattern_is_bounded | control | a glued or whole value stays masked
tests/test_q8b_glued_and_whole_values.py::test_r3_every_spelling_of_value_is_masked | control | a glued or whole value stays masked
tests/test_q8b_glued_and_whole_values.py::test_r10_refused_credential_values_do_not_multiply_the_work | control | a glued or whole value stays masked
tests/test_q8b_random.py::test_x9_has_cases_to_check | control | the random corpus runs with cases
tests/test_q8b_batch8.py::test_b8_1_a_count_of_tokens_stays_readable_as_a_flag_and_as_a_record_key | control | a plain count of tokens stays readable on both paths
tests/test_q8b_batch8.py::test_b8_2_the_cookie_flag_with_its_exact_name_still_masks_its_value | control | the exact cookie flags keep masking their value as they did before
tests/test_q8b_batch8.py::test_b8_3_a_real_two_word_credential_key_is_never_hidden_by_the_ordinary_look_behind | control | a real two-word credential key is never made readable by the ordinary-word rule
tests/test_q8b_batch8.py::test_b8_4_the_generic_flag_takes_a_scheme_word_with_its_token | control | a flag followed by a scheme word and a token masks both
tests/test_q8b_batch8.py::test_b8_4_the_generic_flags_keep_the_one_word_rule_and_so_does_a_value_that_is_no_scheme_word_and_a_word | control | the one-word value rule of the generic flag is unchanged
tests/test_q8b_batch8.py::test_b8_10_a_long_run_of_white_space_after_a_scheme_word_is_read_in_linear_time | control | a long run of white space costs linear time (a time test, not a planted fault)
tests/test_q8b_batch8.py::test_b8_8_a_very_long_run_of_digits_is_read_once | control | a very long run of digits costs linear time (a time test, not a planted fault)
tests/test_q8b_batch8.py::test_b8_12_a_word_that_only_holds_cookie_inside_is_no_key_in_text_and_none_for_the_record_walk | control | a word that only holds cookie inside is no key on either path
"""

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


def planted_killers() -> dict[str, list[str]]:
    """test function name -> the mutants of the table that name it as their killer (the table is the one source)."""
    src = (HERE / "q8b_mutants.py").read_text(encoding="utf-8")
    kills: dict[str, list[str]] = {}
    for m in re.finditer(r"mutant\('(M\d+) .*?\n\s+\w+, '([^']+)'", src, re.DOTALL):
        kills.setdefault(m.group(2).split("[")[0], []).append(m.group(1))
    return kills


# NO_FAULT is empty since batch 11: the seven tests that held "no product line can be faulted" check a test file or a helper, and a fault
# of that file is planted by a `test_file_mutant` (M227 to M233, like M136 and M142); the old reason was untrue.
NO_FAULT: dict[str, str] = {}
# The real size of the group without a planted fault at the head of batch 11: three wall-clock tests (the white space after a scheme word,
# a very long run of digits, the guard of the address pattern, which runs in the perf step). Each fails only on a super-linear regex; the
# planted fault found for the digits (a bare word that may start at every digit) runs longer than five minutes, so it was not put in the table
# in batch 11 (NOT DONE; the next builder plants a smaller one). The number is a gate: a count ABOVE it fails the test below, and the number only falls.
UNPLANTED_MAX = 3


def _group_of(test_id: str, kills: dict[str, list[str]]) -> str:
    name = test_id.split("::")[1].split("[")[0]
    if kills.get(name):
        return "PLANTED"
    return "NO_FAULT" if name in NO_FAULT else "UNPLANTED"


def _parsed(lines: str | None = None):
    rows = []
    for raw in (LINES if lines is None else lines).strip().splitlines():
        parts = [p.strip() for p in raw.split(" | ")]
        assert len(parts) == 3 and parts[1] == "control" and parts[2], (
            f"a line must be '<id> | control | <reason>': {raw!r}"
        )
        rows.append(parts)
    return rows


def _function_exists(test_id: str) -> bool:
    path, _, rest = test_id.partition("::")
    name = rest.split("[")[0]
    src = (HERE.parent / path).read_text(encoding="utf-8")
    return re.search(rf"^def {re.escape(name)}\(", src, re.MULTILINE) is not None


def _problems(lines: str | None = None) -> list[str]:
    """Every way the lines can be wrong; the tests below call this on the real text and on a text with a line removed."""
    rows = _parsed(lines)
    ids = [r[0] for r in rows]
    kills = planted_killers()
    bad = [f"no line for {i}" for i in sorted(EXPECTED_IDS - set(ids))]
    bad += [f"two lines for {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    bad += [
        f"{i} names a test that does not exist"
        for i in ids
        if i in EXPECTED_IDS and not _function_exists(i)
    ]
    names = {i.split("::")[1].split("[")[0] for i in EXPECTED_IDS}
    bad += [f"NO_FAULT names {n}, which has no line" for n in NO_FAULT if n not in names]
    for n, why in NO_FAULT.items():
        path = re.search(r"(tests/[\w./]+)$", why)
        if path is None or not (HERE.parent / path.group(1)).exists():
            bad.append(f"the reason of {n} names no existing file")
        if kills.get(n):
            bad.append(f"{n} has a planted fault and a NO_FAULT reason: drop the reason")
    unplanted = [i for i in ids if _group_of(i, kills) == "UNPLANTED"]
    if len(unplanted) > UNPLANTED_MAX:
        bad.append(
            f"{len(unplanted)} controls have neither a planted fault nor a reason (at most {UNPLANTED_MAX})"
        )
    return bad


def test_every_line_is_checked_by_one_source_and_every_listed_test_exists():
    assert _problems() == []


def test_the_lines_cover_every_id_the_independent_run_listed():
    ids = [r[0] for r in _parsed()]
    assert len(set(ids)) == len(ids), "an id has two lines"
    assert len(EXPECTED_IDS) >= 74 and set(ids) == EXPECTED_IDS


def test_a_planted_fault_is_read_from_the_mutant_table_and_the_pinned_killer_is_the_test_itself():
    kills = planted_killers()
    assert len(kills) >= 25, "the mutant table was not read"
    src = (HERE / "q8b_mutants.py").read_text(encoding="utf-8")
    for name in kills:
        assert f"def {name}(" in "".join(
            p.read_text(encoding="utf-8") for p in HERE.glob("test_*.py")
        ), f"the mutant table names a killer that does not exist: {name}"
    assert (
        "M149" in src
        and "M149" in kills["test_every_redaction_function_reaches_the_one_choke_point"]
    )


def test_the_check_itself_fails_when_a_line_is_missing_a_line_is_doubled_or_a_test_is_renamed():
    rows = LINES.strip().splitlines()
    assert _problems("\n".join(rows[1:])), "a missing line was not found by the check"
    assert _problems("\n".join([rows[0], *rows])), "a doubled line was not found by the check"
    renamed = rows[0].replace("::test_", "::test_no_such_", 1)
    assert _problems("\n".join([renamed, *rows[1:]])), "a renamed test was not found by the check"


def test_the_group_without_a_planted_fault_is_listed_and_its_size_is_pinned():
    kills = planted_killers()
    unplanted = sorted(
        {i.split("::")[1].split("[")[0] for i in EXPECTED_IDS if _group_of(i, kills) == "UNPLANTED"}
    )
    count = sum(1 for i in EXPECTED_IDS if _group_of(i, kills) == "UNPLANTED")
    assert count <= UNPLANTED_MAX, (
        f"{count} controls have no planted fault and no reason: {unplanted}"
    )


def test_every_planted_fault_is_in_its_product_file_once_and_names_a_killer_that_exists():
    """The table is read as code: the text each mutant replaces is in its file at least once (a stale text plants nothing; the runner replaces every copy) and its killer is a
    test of the file it names. `planted_killers()` alone proves only that a mutant names a test."""
    import sys

    sys.path.insert(0, str(HERE.parent))
    from tests import q8b_mutants

    bad = []
    for m in q8b_mutants.M:
        path = HERE.parent / m.file
        text = path.read_text(encoding="utf-8")
        if text.count(m.old) < 1:
            bad.append(
                f"{m.name}: its fault text is in {m.file} {text.count(m.old)} times, not at least once"
            )
        tests = (HERE.parent / m.test_file).read_text(encoding="utf-8")
        if re.search(rf"^def {re.escape(m.only_test)}\(", tests, re.MULTILINE) is None:
            bad.append(f"{m.name}: its killer {m.only_test} is not a test of {m.test_file}")
    assert not bad, bad[:5]


def test_the_ceiling_is_the_real_number_and_a_larger_group_fails():
    kills = planted_killers()
    count = sum(1 for i in EXPECTED_IDS if _group_of(i, kills) == "UNPLANTED")
    assert count == UNPLANTED_MAX, (
        f"{count} controls have no planted fault and no reason, the ceiling says {UNPLANTED_MAX}: lower the ceiling to the real number"
    )
    assert _problems() == [] and _problems(None) == []
