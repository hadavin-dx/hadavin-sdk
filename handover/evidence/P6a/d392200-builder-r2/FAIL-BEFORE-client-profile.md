# Fail-before table: tests/test_client_profile.py copied onto the base of the pull request (0dabf1f), source of the base only

Command: COLUMNS=300 PYTHONPATH=<base>/src python -m pytest tests/test_client_profile.py -q -rA --tb=no  (no Postgres, no cloud setting)

| row | result on the base | first words of the failure |
|---|---|---|
| test_the_prod_fixture_loads | PASS (pin: also true on the base) |  |
| test_secrets_env_is_refused_in_a_client_profile[pilot] | PASS (pin: also true on the base) |  |
| test_secrets_env_is_refused_in_a_client_profile[prod] | PASS (pin: also true on the base) |  |
| test_a_pilot_config_that_omits_store_is_refused | PASS (pin: also true on the base) |  |
| test_a_demo_anchor_only_failure_does_not_advise_the_field | PASS (pin: also true on the base) |  |
| test_demo_only_is_exactly_the_six_pairs | PASS (pin: also true on the base) |  |
| test_every_pair_is_decided_with_a_reason | PASS (pin: also true on the base) |  |
| test_planted_kind_in_neither_set_is_reported | PASS (pin: also true on the base) |  |
| test_planted_pair_in_both_sets_is_reported | PASS (pin: also true on the base) |  |
| test_planted_empty_reason_is_reported | PASS (pin: also true on the base) |  |
| test_sources_keeps_its_own_refusal | PASS (pin: also true on the base) |  |
| test_tools_keeps_its_own_refusal | PASS (pin: also true on the base) |  |
| test_no_door_in_src_or_demos | PASS (pin: also true on the base) |  |
| test_planted_doors_are_reported[direct] | PASS (pin: also true on the base) |  |
| test_planted_doors_are_reported[partial] | PASS (pin: also true on the base) |  |
| test_planted_doors_are_reported[double_star] | PASS (pin: also true on the base) |  |
| test_no_override_passes_the_check[pilot] | PASS (pin: also true on the base) |  |
| test_no_override_passes_the_check[prod] | PASS (pin: also true on the base) |  |
| test_the_live_hooks_need_no_switch[hold_run_ids] | PASS (pin: also true on the base) |  |
| test_the_live_hooks_need_no_switch[timeout_s] | PASS (pin: also true on the base) |  |
| test_every_refused_keyword_has_a_sample | PASS (pin: also true on the base) |  |
| test_the_facts_stated_in_the_reasons_are_true | FAIL by ImportError | ImportError: cannot import name '_sends_text_out' from 'hadavin_sdk.config' (/home/user/build/B-P6a- |
| test_each_test_double_is_refused_alone[secrets-pilot] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[secrets-prod] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[channel-pilot] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[channel-prod] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[detector-pilot] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[detector-prod] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[llm-pilot] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[llm-prod] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[clock-pilot] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_each_test_double_is_refused_alone[clock-prod] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_all_at_once_names_all_in_signature_order | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_a_falsy_double_is_refused | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_a_refusal_builds_nothing_first | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_a_keyword_added_later_is_refused_by_default | FAIL by AttributeError | AttributeError: module 'hadavin_sdk.app' has no attribute '_test_doubles_given' |
| test_any_environment_that_is_not_demo_is_live[Demo] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_any_environment_that_is_not_demo_is_live[uat] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_any_environment_that_is_not_demo_is_live[] | FAIL by tests.test_client_profile._Reached | tests.test_client_profile._Reached: signer |
| test_only_the_value_true_is_the_switch[no] | FAIL by TypeError | TypeError: build() got an unexpected keyword argument 'allow_test_doubles' |
| test_only_the_value_true_is_the_switch[yes] | FAIL by TypeError | TypeError: build() got an unexpected keyword argument 'allow_test_doubles' |
| test_only_the_value_true_is_the_switch[one] | FAIL by TypeError | TypeError: build() got an unexpected keyword argument 'allow_test_doubles' |
| test_only_the_value_true_is_the_switch[list] | FAIL by TypeError | TypeError: build() got an unexpected keyword argument 'allow_test_doubles' |
| test_the_switch_lets_a_test_double_through | FAIL by TypeError | TypeError: build() got an unexpected keyword argument 'allow_test_doubles' |
| test_the_live_hooks_are_exactly_two_parameters_of_build | FAIL by AttributeError | AttributeError: module 'hadavin_sdk.app' has no attribute '_LIVE_HOOKS' |
| test_a_real_llm_kind_in_demo_needs_the_field[anthropic] | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_a_real_llm_kind_in_demo_needs_the_field[bedrock] | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_a_real_llm_kind_in_demo_needs_the_field[gemini] | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_a_real_llm_kind_in_demo_needs_the_field[openai_compat] | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_the_vendor_detector_in_demo_needs_the_field | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_every_detector_kind_is_local_or_refused_in_demo | FAIL by ImportError | ImportError: cannot import name 'LOCAL_DETECTORS' from 'hadavin_sdk.backends.table' (/home/user/buil |
| test_a_detector_kind_nobody_reviewed_is_treated_as_sending_text_out | FAIL by ImportError | ImportError: cannot import name '_sends_text_out' from 'hadavin_sdk.config' (/home/user/build/B-P6a- |
| test_the_local_detector_list_is_exactly_regex_and_llm_judge | FAIL by ImportError | ImportError: cannot import name 'LOCAL_DETECTORS' from 'hadavin_sdk.backends.table' (/home/user/buil |
| test_a_real_channel_kind_in_demo_needs_the_field | FAIL by assertion (did not raise) | Failed: DID NOT RAISE ConfigError |
| test_with_the_field_a_real_llm_kind_loads_in_demo | FAIL by hadavin_sdk.errors.ConfigError | hadavin_sdk.errors.ConfigError: 1 validation error for Config |
| test_three_refusals_come_in_one_error | FAIL by assertion | AssertionError: Regex pattern did not match. |
| test_the_field_is_refused_in_pilot_and_prod | FAIL by assertion | AssertionError: assert 'demo configs only' in '1 validation error for Config\nmade_up_data_only\n  E |
| test_the_field_is_refused_in_any_environment_that_is_not_demo[Demo] | FAIL by assertion | AssertionError: Regex pattern did not match. |
| test_the_field_is_refused_in_any_environment_that_is_not_demo[uat] | FAIL by assertion | AssertionError: Regex pattern did not match. |
| test_the_field_is_refused_in_any_environment_that_is_not_demo[] | FAIL by assertion | AssertionError: Regex pattern did not match. |
| test_the_field_still_loads_in_demo | FAIL by hadavin_sdk.errors.ConfigError | hadavin_sdk.errors.ConfigError: 1 validation error for Config |
| test_a_loose_yes_does_not_switch_the_field_on[yes] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_loose_yes_does_not_switch_the_field_on[1] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_loose_yes_does_not_switch_the_field_on[true] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_loose_yes_does_not_switch_the_field_on[on] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_value_that_is_not_a_bool_is_refused_at_load[word] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_value_that_is_not_a_bool_is_refused_at_load[null] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_a_value_that_is_not_a_bool_is_refused_at_load[list] | FAIL by assertion | AssertionError: assert 'valid boolean' in '1 validation error for Config\nmade_up_data_only\n  Extra |
| test_an_unquoted_yes_in_the_file_is_the_yaml_true | FAIL by hadavin_sdk.errors.ConfigError | hadavin_sdk.errors.ConfigError: 1 validation error for Config |

Totals: 69 rows; PASS (pin: also true on the base): 21; FAIL by ImportError: 4; FAIL by tests.test_client_profile._Reached: 16; FAIL by AttributeError: 2; FAIL by TypeError: 5; FAIL by assertion (did not raise): 6; FAIL by hadavin_sdk.errors.ConfigError: 3; FAIL by assertion: 12

Every row that fails does so on its own: the whole file is collected on the base (no collection error), because LOCAL_DETECTORS, _sends_text_out and the other names that exist only with the change are read inside the row bodies.
