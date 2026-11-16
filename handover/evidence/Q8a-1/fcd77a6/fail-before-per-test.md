# Q8a-1 fail-before, head fcd77a68: every test, both bases untouched (EVIDENCE RUNNER record, no judgement)

## Base (a): origin/main 2a8c2aac + the head's five test files. `5 failed, 108 passed, 1 error`, exit 1

| test | result | first assertion or error (junit `message`, line breaks shown as ` / `, cut at 420 chars) |
|---|---|---|
| `::tests.test_q8a_live_overrides` | error | `collection failure` |
| `tests.test_k3_pilot_env::test_k3_pilot_config_loads` | passed |  |
| `tests.test_k3_pilot_env::test_k3_http_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_missing_level_refused` | passed |  |
| `tests.test_k3_pilot_env::test_k3_levels_must_cover_every_action_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_suggest_refused_without_evidence` | passed |  |
| `tests.test_k3_pilot_env::test_k3_missing_run_budget_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_confidential_agent_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_read_only_contract_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_request_tracker_key_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_pilot_app_has_no_executor` | passed |  |
| `tests.test_k5_round8_postgres::test_the_app_deletes_evidence_only_through_the_purge_identity` | passed |  |
| `tests.test_stage_names::test_the_stages_are_exactly_demo_pilot_prod` | passed |  |
| `tests.test_stage_names::test_dev_is_refused_with_the_rename` | passed |  |
| `tests.test_stage_names::test_values_are_compared_exactly_never_normalised` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[None]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[0]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[1.5]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[True]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[value4]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[value5]` | passed |  |
| `tests.test_stage_names::test_a_missing_stage_is_refused` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[~]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[null]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[Null]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[NULL]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[]` | passed |  |
| `tests.test_stage_names::test_demo_loads_and_pilot_and_prod_load_only_without_the_fakes` | passed |  |
| `tests.test_stage_names::test_demo_only_is_exactly_the_six_pairs` | passed |  |
| `tests.test_stage_names::test_demo_accepts_every_demo_only_kind` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_every_relaxed_kind` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair0]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair1]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair2]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair3]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair4]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair5]` | passed |  |
| `tests.test_stage_names::test_demo_is_not_live` | passed |  |
| `tests.test_stage_names::test_a_value_that_is_not_a_stage_is_live_for_every_guard` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_test_object_handed_to_build` | failure | `AssertionError: a live build took a test object ('pilot'): "secret 'pg-dsn' cannot be read at start-up" / assert "secret 'pg-d...d at start-up" == 'channel= is ...ilot and prod' / - channel= is for tests; configure backends.channel in pilot and prod / + secret 'pg-dsn' cannot be read at start-up` |
| `tests.test_stage_names::test_pilot_and_prod_refuse_sources_and_tools_handed_to_build` | failure | `AssertionError: a live build took sources= ('pilot', _FalsyDict of 1): "secret 'pg-dsn' cannot be read at start-up" / assert False / +  where False = <built-in method startswith of str object at 0x7fe7588a80f0>('sources= is for tests') / +    where <built-in method startswith of str object at 0x7fe7588a80f0> = "secret 'pg-dsn' cannot be read at start-up".startswith` |
| `tests.test_stage_names::test_demo_refuses_a_timeout_that_is_out_of_range` | failure | `AssertionError: demo took timeout_s=0: '' / assert '' == 'timeout_s= m...ded) and 3600' / - timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_static_vault_token` | failure | `AssertionError: a static Vault token was accepted for secrets (pilot, {}): "secret 'pg-dsn' cannot be read at start-up" / assert "secret 'pg-d...d at start-up" == 'environment ...uth: approle)' / - environment pilot: refused: secrets: vault auth token (the default; set auth: kubernetes (recommended) or auth: approle) / + secret 'pg-dsn' cannot be read at start-up` |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick` | failure | `AssertionError: a live tick took a time handed to it ('pilot'): '' / assert '' == 'now= is for ...ilot and prod' / - now= is for tests; it is refused in pilot and prod` |
| `tests.test_stage_names::test_a_value_that_is_not_a_stage_gets_the_prod_only_rules` | passed |  |
| `tests.test_stage_names::test_no_old_spelling_of_the_demo_only_flag_is_left` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[dev_only]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[demo_only]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[demo]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[dev]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[stage]` | passed |  |
| `tests.test_stage_names::test_both_spellings_of_the_stage_together_refuse_start` | passed |  |
| `tests.test_stage_names::test_the_old_stage_word_is_gone` | passed |  |
| `tests.test_stage_names::test_the_exemptions_have_no_stale_entry` | passed |  |
| `tests.test_stage_names::test_a_stage_shaped_line_in_a_file_that_holds_an_exempt_line_still_fails` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[environment: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[environment="{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word["environment": "{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[ENV={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[APP_ENV={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[docker run --env {w} app]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[      env: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[STAGE_{W}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[Environment.{W}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[tier: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[profile={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word["mode": "{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[x = {{"{w}": 1}}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[    case '{w}':]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[y = 1 if ok else '{w}']` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[    "{w}",]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[if env == "{w}":]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[x = {w}\|pilot\|prod]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[demo, {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[  - {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[{W}_ONLY = frozenset()]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[def {w}_cfg(tmp_path):]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[def test_x_outside_{w}(cfg):]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[kept in {w} for the tests]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[kinds allowed only in `{w}`.]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[a {w} executor]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[https://{w}.example.org/x]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[## Running in {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[\uff44\uff45\uff56]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[d\u0435v]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[D\u0435V]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[d\u200bev]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[a developer wrote this]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the device is on]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[stddev = 3]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[a real `vault server -dev` in CI]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the CI Vault dev server]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[dev split of the dataset]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[(?:com\|net\|io\|dev\|ai\|cloud)]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[[dependency-groups]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[dev = ["pytest"]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[Dev-tool constants]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[environment variable HADAVIN_X]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[environment: demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[for row in dev:]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[modern mode: developer]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[stage: demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the demo stage and the pilot stage]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[  - demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[default-groups = ["devx"]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[mode: develop]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[pytest.mark.parametrize("test")]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[env]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[environment]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[tier]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[stage]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[profile]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[mode]` | passed |  |
| `tests.test_stage_names::test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names` | passed |  |

## Base (b): f6fad26f + the five test files changed by the newest commit. `31 failed, 205 passed`, exit 1

| test | result | first assertion or error (junit `message`, line breaks shown as ` / `, cut at 420 chars) |
|---|---|---|
| `tests.test_k3_pilot_env::test_k3_pilot_config_loads` | passed |  |
| `tests.test_k3_pilot_env::test_k3_http_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_missing_level_refused` | passed |  |
| `tests.test_k3_pilot_env::test_k3_levels_must_cover_every_action_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_suggest_refused_without_evidence` | passed |  |
| `tests.test_k3_pilot_env::test_k3_missing_run_budget_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_confidential_agent_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_read_only_contract_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_request_tracker_key_refused_in_pilot` | passed |  |
| `tests.test_k3_pilot_env::test_k3_pilot_app_has_no_executor` | passed |  |
| `tests.test_k5_round8_postgres::test_the_app_deletes_evidence_only_through_the_purge_identity` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[secrets-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[secrets-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[channel-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[channel-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[detector-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[detector-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[llm-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[llm-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[clock-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[clock-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[timeout_s-pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_each_test_keyword_is_refused_in_pilot_and_prod[timeout_s-prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage[staging]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage[Demo]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage[demo ]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage[]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage[None]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_falsy_test_object_is_refused_in_pilot` | passed |  |
| `tests.test_q8a_live_overrides::test_a_zero_timeout_is_refused_in_pilot_as_a_test_keyword[0]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_zero_timeout_is_refused_in_pilot_as_a_test_keyword[0.0]` | passed |  |
| `tests.test_q8a_live_overrides::test_with_several_given_only_the_first_in_the_fixed_order_is_named[given0-secrets]` | passed |  |
| `tests.test_q8a_live_overrides::test_with_several_given_only_the_first_in_the_fixed_order_is_named[given1-channel]` | passed |  |
| `tests.test_q8a_live_overrides::test_with_several_given_only_the_first_in_the_fixed_order_is_named[given2-detector]` | passed |  |
| `tests.test_q8a_live_overrides::test_with_several_given_only_the_first_in_the_fixed_order_is_named[given3-llm]` | passed |  |
| `tests.test_q8a_live_overrides::test_with_several_given_only_the_first_in_the_fixed_order_is_named[given4-clock]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_earlier_refusals_still_come_first` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[staging]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[Demo]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[demo ]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused[None]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_falsy_sources_mapping_is_refused_in_pilot` | passed |  |
| `tests.test_q8a_live_overrides::test_a_falsy_tools_mapping_is_refused_in_pilot` | passed |  |
| `tests.test_q8a_live_overrides::test_an_empty_sources_or_tools_mapping_is_refused_in_pilot` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[secrets]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[channel]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[detector]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[llm]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[clock]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_each_test_keyword[timeout_s]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_falsy_test_object_instead_of_dropping_it` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_falsy_sources_or_tools_mapping_instead_of_dropping_it` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[0]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[0.0]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[-1]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[-0.5]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[True]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[False]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[nan]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[inf]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type['5']` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[[5]]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[Decimal('2.5]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[Fraction(5, ]` | failure | `AssertionError: / - timeout_s= must be greater than 0 / + timeout_s= must be an int or float between 0 (not included) and 3600` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[100000000000]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[3601]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type[3600.1]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[3]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[0.001]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[2.5]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[3600]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[3600.0]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[1e-09]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_uses_a_timeout_in_the_range_as_given[5e-324]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_factory_hands_a_falsy_secret_provider_to_the_backend` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[pilot]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[prod]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[staging]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[Demo]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[demo ]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_time_outside_demo[None]` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_accepts_a_given_time_in_demo` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[pilot-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[pilot-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[prod-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[prod-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[staging-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[staging-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[Demo-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[Demo-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[demo -one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[demo -empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[None-one-step]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo[None-empty-list]` | failure | `Failed: DID NOT RAISE ConfigError` |
| `tests.test_q8a_live_overrides::test_run_tick_names_now_first_when_both_are_given_outside_demo` | passed |  |
| `tests.test_q8a_live_overrides::test_run_tick_accepts_a_given_step_list_in_demo` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[pilot-secrets-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[pilot-secrets-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[pilot-signer-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[pilot-signer-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[prod-secrets-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[prod-secrets-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[prod-signer-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads[prod-signer-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage[staging]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage[Demo]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage[demo ]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage[]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage[None]` | passed |  |
| `tests.test_q8a_live_overrides::test_both_static_vault_tokens_are_named_in_one_refusal` | passed |  |
| `tests.test_q8a_live_overrides::test_a_new_kind_built_on_the_vault_settings_class_is_refused_too` | passed |  |
| `tests.test_q8a_live_overrides::test_every_kind_with_a_vault_sign_in_field_is_built_on_the_vault_settings_class` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-secrets-auth0]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-secrets-auth1]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-signer-auth0]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-signer-auth1]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-secrets-auth0]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-secrets-auth1]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-signer-auth0]` | passed |  |
| `tests.test_q8a_live_overrides::test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-signer-auth1]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_a_static_vault_token[secrets-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_a_static_vault_token[secrets-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_a_static_vault_token[signer-auth-written]` | passed |  |
| `tests.test_q8a_live_overrides::test_demo_accepts_a_static_vault_token[signer-auth-left-out]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_kill_switch_command_is_not_refused_for_a_static_vault_token[pilot-stop]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_kill_switch_command_is_not_refused_for_a_static_vault_token[pilot-reset]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_kill_switch_command_is_not_refused_for_a_static_vault_token[prod-stop]` | passed |  |
| `tests.test_q8a_live_overrides::test_the_kill_switch_command_is_not_refused_for_a_static_vault_token[prod-reset]` | passed |  |
| `tests.test_stage_names::test_the_stages_are_exactly_demo_pilot_prod` | passed |  |
| `tests.test_stage_names::test_dev_is_refused_with_the_rename` | passed |  |
| `tests.test_stage_names::test_values_are_compared_exactly_never_normalised` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[None]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[0]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[1.5]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[True]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[value4]` | passed |  |
| `tests.test_stage_names::test_a_stage_that_is_not_a_string_is_refused[value5]` | passed |  |
| `tests.test_stage_names::test_a_missing_stage_is_refused` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[~]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[null]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[Null]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[NULL]` | passed |  |
| `tests.test_stage_names::test_a_yaml_null_stage_is_refused[]` | passed |  |
| `tests.test_stage_names::test_demo_loads_and_pilot_and_prod_load_only_without_the_fakes` | passed |  |
| `tests.test_stage_names::test_demo_only_is_exactly_the_six_pairs` | passed |  |
| `tests.test_stage_names::test_demo_accepts_every_demo_only_kind` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_every_relaxed_kind` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair0]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair1]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair2]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair3]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair4]` | passed |  |
| `tests.test_stage_names::test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal[pair5]` | passed |  |
| `tests.test_stage_names::test_demo_is_not_live` | passed |  |
| `tests.test_stage_names::test_a_value_that_is_not_a_stage_is_live_for_every_guard` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_test_object_handed_to_build` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_sources_and_tools_handed_to_build` | passed |  |
| `tests.test_stage_names::test_demo_refuses_a_timeout_that_is_out_of_range` | failure | `AssertionError: demo took timeout_s=0: 'timeout_s= must be greater than 0' / assert 'timeout_s= m...reater than 0' == 'timeout_s= m...ded) and 3600' / - timeout_s= must be an int or float between 0 (not included) and 3600 / + timeout_s= must be greater than 0` |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_static_vault_token` | passed |  |
| `tests.test_stage_names::test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick` | failure | `AssertionError: a live tick took a step list handed to it ('pilot'): '', ran ['recorded'] / assert ('' == 'steps= is fo...ilot and prod' / - steps= is for tests; it is refused in pilot and prod)` |
| `tests.test_stage_names::test_a_value_that_is_not_a_stage_gets_the_prod_only_rules` | passed |  |
| `tests.test_stage_names::test_no_old_spelling_of_the_demo_only_flag_is_left` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[dev_only]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[demo_only]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[demo]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[dev]` | passed |  |
| `tests.test_stage_names::test_a_config_key_for_either_spelling_of_the_flag_refuses_start[stage]` | passed |  |
| `tests.test_stage_names::test_both_spellings_of_the_stage_together_refuse_start` | passed |  |
| `tests.test_stage_names::test_the_old_stage_word_is_gone` | passed |  |
| `tests.test_stage_names::test_the_exemptions_have_no_stale_entry` | passed |  |
| `tests.test_stage_names::test_a_stage_shaped_line_in_a_file_that_holds_an_exempt_line_still_fails` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[environment: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[environment="{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word["environment": "{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[ENV={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[APP_ENV={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[docker run --env {w} app]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[      env: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[STAGE_{W}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[Environment.{W}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[tier: {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[profile={w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word["mode": "{w}"]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[x = {{"{w}": 1}}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[    case '{w}':]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[y = 1 if ok else '{w}']` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[    "{w}",]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[if env == "{w}":]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[x = {w}\|pilot\|prod]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[demo, {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_shape_for_each_word[  - {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[{W}_ONLY = frozenset()]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[def {w}_cfg(tmp_path):]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[def test_x_outside_{w}(cfg):]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[kept in {w} for the tests]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[kinds allowed only in `{w}`.]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[a {w} executor]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[https://{w}.example.org/x]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_each_old_word_only_shape[## Running in {w}]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[\uff44\uff45\uff56]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[d\u0435v]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[D\u0435V]` | passed |  |
| `tests.test_stage_names::test_the_scanner_finds_the_word_spelled_with_look_alike_letters[d\u200bev]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[a developer wrote this]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the device is on]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[stddev = 3]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[a real `vault server -dev` in CI]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the CI Vault dev server]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[dev split of the dataset]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[(?:com\|net\|io\|dev\|ai\|cloud)]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[[dependency-groups]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[dev = ["pytest"]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[Dev-tool constants]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[environment variable HADAVIN_X]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[environment: demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[for row in dev:]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[modern mode: developer]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[stage: demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[the demo stage and the pilot stage]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[  - demo]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[default-groups = ["devx"]]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[mode: develop]` | passed |  |
| `tests.test_stage_names::test_the_scanner_ignores_words_that_are_not_stage_positions[pytest.mark.parametrize("test")]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[env]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[environment]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[tier]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[stage]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[profile]` | passed |  |
| `tests.test_stage_names::test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters[mode]` | passed |  |
| `tests.test_stage_names::test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names` | passed |  |
