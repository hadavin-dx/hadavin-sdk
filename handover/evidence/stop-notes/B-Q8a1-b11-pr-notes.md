# Q8a-1 fix batch 11 (round 10 findings) - PR notes

Branch `core/q8a1-b11`, pushed as `wip/cloud-q8a1-b11`. Base: `wip/cloud-q8a1-b10` head f4acee28.

## Read this first: what is not finished or not proven
- The question q-q8a1-hide-ids (a `ConfigName` type that hides every configured name) is the owner's to decide. It is NOT built and NOT decided here.
- The allowed list of the widened guard (about 100 new entries) was judged by me by reading each site, in groups, with a reason per group. It was not tested entry by entry; a reviewer should spot-check the groups.
- The guard does not see: a configured value copied into another variable first (`x = name`, then `x` in a message), and the text of a library error (`f"{exc}"`). Both are stated in the CHANGELOG.
- `tests/test_migration_numbers.py` timing test: NOT touched (its fix is on `core/fix-timing-harness-flake`).

## Issue 2: the eleven f-string places, traced one by one
Marker: a made-up word built from parts at run time. Tests: `tests/test_q8a1_f_string_trace.py`.

| # | Place | What the value is and where it comes from | Reaches a message, log, exception or traceback? | Test | Result on the old head f4acee28 |
|---|---|---|---|---|---|
| 1 | `secrets_gcp.py:39` | `projects/{project_id}/secrets/{name}/versions/latest`: configured project id and secret name, sent to the cloud API | YES, through the cloud library's own error text (it quotes the resource path). Fixed at the shared base `CachedSecrets.get` (also closes AWS and Azure): fixed sentence with the error class, cause dropped | `test_a_cloud_error_that_quotes_the_secret_path_is_never_passed_on`, `test_the_aws_and_azure_kinds_say_the_class_of_a_library_error_only` | FAIL (marker shown) |
| 2 | `llm/anthropic.py:32` | Vertex base URL with the configured region | YES, through the client library's `ValueError` text. Fixed: fixed sentence with the error class, cause dropped | `test_a_client_library_error_that_quotes_the_base_url_is_not_passed_on` | FAIL |
| 3 | `llm/anthropic.py:33` | Foundry base URL with the configured resource | same as 2 (real library checked with the environment variable that makes it refuse) | same test, and `test_the_real_client_library_does_not_quote_the_resource_in_its_refusal` (control) | FAIL / control |
| 4 | `sources/kubernetes.py:237` | API path with the asked namespace | Only the request path. A transport error that quotes the path is already reduced to `kubernetes: <class>` | `test_a_fetch_error_that_quotes_the_api_path_never_shows_the_namespace` | control (passes on old code: already clean) |
| 5 | `sources/kubernetes.py:251` | same, for the logs call | same | same test | control |
| 6 | `store/migration_numbers.py:251` | `SET search_path TO "{schema}"`: the schema is `current_schema()` read from the database, printed in a recipe for a database administrator | Only in the returned recipe, and only for a plain lower-case name; any other name is refused by a fixed sentence without it | `test_the_hand_recipe_prints_only_a_plain_schema_name_and_refuses_any_other_with_a_fixed_sentence` | control |
| 7 | `store/migrate.py:212` | `{role}: can CREATE in schema {schema}`: role from the command line, schema from the database | Printed only after the role passed the plain-name pattern. A role that failed it was echoed with `!r`: FIXED, now the option name is said and the text is not | `test_a_database_role_option_that_is_not_a_plain_name_is_refused_by_option_never_by_text` | FAIL |
| 8-11 | `backends/table.py:367, 379, 380, 394` | region and bucket put in a host name of the suggested `egress.yaml` list | A returned value (the list the operator asked for), never a message. Region and bucket are pattern-checked at load; a bad value is refused by a fixed sentence | `test_a_region_or_bucket_is_in_the_suggested_host_list_and_in_no_error_text` | control |

Row 7 covers the three role options (`runtime_role`, `portal_role`, `purge_role`) in one test.
The new guard reads all of these files (a test pins that every module under `src/hadavin_sdk` except the two exempt places is read).

## Issue 10: one line per test that passes on old code or on main (2 named + 63)
Killers named Y3, Y4, Y5 were run as planted mutants in a scratch copy (scripts /tmp/b11/m2.py, m3.py), not added to tests/stage_mutants.py. M-numbers are in tests/stage_mutants.py (181 mutants, all killed in the final run).

- `test_the_platform_secret_probe_names_a_secret_by_position_and_never_by_name`: KILLED by M17u (a secret name is shown again at start-up)
- `test_every_secret_provider_says_no_name_for_a_plain_word_and_imports_no_name_filter`: KILLED by M19c and M19d (AWS and Vault providers quote a plain-word name again)
- `test_k3_pilot_app_has_no_executor`: KILLED by planted mutant Y3 (a live App builds an Executor: `executor = None if live else Executor(...)` -> always an Executor); needs the Postgres database, so it is skipped without one (the first scan run had none; the rerun with the database killed it)
- `test_the_earlier_refusals_still_come_first`: KILLED by mutant M4g every stage is relaxed (app.py: live = False)
- `test_a_live_build_with_no_test_keyword_is_not_refused[pilot]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 2 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[prod]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 2 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[staging]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 4 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[Demo]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 4 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[demo ]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 4 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 4 more)
- `test_a_live_build_with_no_test_keyword_is_not_refused[None]`: KILLED by mutant M18t a missing golden set file is no longer read as empty (registry.py) (and 4 more)
- `test_demo_accepts_each_test_keyword[secrets]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_accepts_each_test_keyword[channel]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_accepts_each_test_keyword[detector]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_accepts_each_test_keyword[llm]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_accepts_each_test_keyword[clock]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_accepts_each_test_keyword[timeout_s]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_uses_a_timeout_in_the_range_as_given[3]`: KILLED by mutant X1 build refuses test keywords in demo too (and 1 more)
- `test_demo_uses_a_timeout_in_the_range_as_given[0.001]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_uses_a_timeout_in_the_range_as_given[2.5]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_uses_a_timeout_in_the_range_as_given[3600]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_demo_uses_a_timeout_in_the_range_as_given[3600.0]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_run_tick_accepts_a_given_time_in_demo`: KILLED by mutant M13b the tick refuses a handed time in demo too (tick.py) (and 5 more)
- `test_run_tick_accepts_a_given_step_list_in_demo`: KILLED by mutant M13b the tick refuses a handed time in demo too (tick.py) (and 2 more)
- `test_an_appended_step_runs_outside_demo_after_every_built_in_step[pilot]`: KILLED by mutant X1 build refuses test keywords in demo too (and 1 more)
- `test_an_appended_step_runs_outside_demo_after_every_built_in_step[prod]`: KILLED by mutant X1 build refuses test keywords in demo too (and 1 more)
- `test_demo_runs_a_step_list_that_lacks_a_built_in_step`: KILLED by mutant M13f the built-in step check runs in demo too (tick.py) (and 2 more)
- `test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts[0.001]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts[0.5]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts[3]`: KILLED by mutant X1 build refuses test keywords in demo too (and 1 more)
- `test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts[3.5]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_the_config_file_and_the_keyword_accept_the_same_executor_timeouts[3600]`: KILLED by mutant X1 build refuses test keywords in demo too
- `test_the_step_functions_checked_here_are_the_built_in_steps`: KILLED by planted mutant Y4 (a built-in tick step renamed in tick.py); the test is the consistency check between the step list this file uses and the real one
- `test_demo_keeps_a_tick_context_with_a_given_time_and_a_stand_in_context`: KILLED by mutant M13j the tick context refuses a handed time in demo too (tick.py) (and 3 more)
- `test_every_kind_with_a_vault_sign_in_field_is_built_on_the_vault_settings_class`: KILLED by planted mutant Y5 (`VaultSettings` no longer built on the Vault base class)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-secrets-auth0]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 2 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-secrets-auth1]`: KILLED by mutant M12i the Vault check is widened to every sign-in but kubernetes (app.py) (and 3 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-signer-auth0]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 2 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[pilot-signer-auth1]`: KILLED by mutant M12i the Vault check is widened to every sign-in but kubernetes (app.py) (and 3 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-secrets-auth0]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 2 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-secrets-auth1]`: KILLED by mutant M12i the Vault check is widened to every sign-in but kubernetes (app.py) (and 3 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-signer-auth0]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 2 more)
- `test_a_build_accepts_the_other_vault_sign_ins_in_pilot_and_prod[prod-signer-auth1]`: KILLED by mutant M12i the Vault check is widened to every sign-in but kubernetes (app.py) (and 3 more)
- `test_demo_accepts_a_static_vault_token[secrets-auth-written]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 3 more)
- `test_demo_accepts_a_static_vault_token[secrets-auth-left-out]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 3 more)
- `test_demo_accepts_a_static_vault_token[signer-auth-written]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 3 more)
- `test_demo_accepts_a_static_vault_token[signer-auth-left-out]`: KILLED by mutant M16e a settings check splits the URL with the library again (table.py) (and 3 more)
- `test_the_marker_is_in_no_error_text_in_any_probe_row[duplicate key config]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value backend kind]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value backend kind mapping]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value check_modules]`: KILLED by mutant M4a the demo-only check still tests the old word (and 1 more)
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value egress host]`: KILLED by mutant M4a the demo-only check still tests the old word (and 1 more)
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value prompt_file]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value route key]`: KILLED by mutant M4a the demo-only check still tests the old word (and 1 more)
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tool entry not a mapping]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tool list not a list]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tool name]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tool side_effect]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tools_allowed with a manifest]`: CONTROL: one row of the evidence probe set pinned as a test. The marker was in 8 of the 107 probe results at commit 4ccb4f9a (before the fixes of rounds 5 to 8), so the row fails there; at f4acee28 and on main the fixes are already in, so it passes by design. A refusal that prints the marker is the failure it pins
- `test_the_marker_is_in_no_error_text_in_any_probe_row[value tools_allowed without a manifest]`: KILLED by mutant M4a the demo-only check still tests the old word (and 1 more)
- `test_every_probe_row_either_raises_or_is_listed_with_its_reason`: CONTROL: checks the table of probe rows (each accepted row has a reason of at least 30 characters); it guards the test table, not behaviour, so it cannot fail on old code; a row added without a reason fails it
- `test_a_tool_call_with_a_login_in_the_url_is_a_tool_refusal`: KILLED by mutant M17zb a login in a tool URL is no longer refused (tools.py)
- `test_a_tool_name_in_the_app_is_pattern_bound_so_shown_name_there_changes_nothing`: KILLED by mutant M17za a tool name may start with a capital again (tools.py)
- `test_the_guard_finds_each_way_of_printing_a_configured_name_and_a_stale_allowance`: CONTROL: a self-test of the guard on planted source text, so no change in `src` can fail it. Killed by a mutation of the guard itself (the AugAssign site dropped from the guard: 2 guard tests fail, incl. the planted-fault test for that shape)
- `test_an_empty_tools_manifest_does_not_refuse_tools_allowed_but_a_manifest_with_tools_does`: KILLED by mutant M18k an empty manifest narrows tools_allowed again (registry.py) (and 2 more)

## Fail-before: new or changed tests run against the OLD source (f4acee28 `src`, new tests)
19 failed, 4281 passed (files: test_stage_names, test_q8a1_f_string_trace, contracts/test_sources, test_k5_classes, test_k5_round9b, test_s3_gate). Failing on old code:
- test_the_rules_problems_function_takes_a_position_and_never_a_label
- test_a_kubernetes_namespace_that_is_not_a_dns_label_is_refused_by_position_never_by_text
- test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter (the widened guard finds the old sites)
- test_a_host_of_a_tool_manifest_is_said_by_its_position_counted_from_one
- the 1-based pins: test_a_name_pasted_where_the_registry_expects_a_known_one_is_not_shown[over1-...], test_a_chain_approver_must_be_a_person_who_is_in_principals, test_a_right_must_name_an_action_and_approver_of_must_name_a_chain, test_with_a_manifest_a_tools_allowed_entry_with_no_tool_in_it_is_refused, test_a_word_like_loaded_id_prints_as_itself_and_a_reference_that_matched_nothing_never_does, test_a_tool_module_pin_must_be_a_sha256_and_none_of_it_is_printed, test_a_chain_that_no_principal_names_keeps_channel_native_approver_ids, tests/test_s3_gate.py::test_bad_chain_step[step0], [step1]
- trace file: test_a_cloud_error_that_quotes_the_secret_path_is_never_passed_on (3 cases), test_the_aws_and_azure_kinds_say_the_class_of_a_library_error_only, test_a_client_library_error_that_quotes_the_base_url_is_not_passed_on, test_a_database_role_option_that_is_not_a_plain_name_is_refused_by_option_never_by_text
Not run against old code, by nature: the planted-fault and clean-form guard tests (they test the guard on text, so they need the new guard; the guard mutation above fails them) and the trace CONTROLS (stated in their docstrings and the table above).
Also: M21a-e (stage mutants) kill the fixes for hits 1, 2, 7 and the DNS and rules_problems changes.

## Final gates at head af4808e7 (worktree /home/user/build/B-Q8a1-b11)
- ruff check: exit 0 "All checks passed!"; ruff format --check: "328 files already formatted"; bandit -ll -r src: exit 0; tools/scan_repo.py: exit 0
- full pytest -m "not live and not perf" (own Postgres, PG* in the server environment, via heavy.sh): exit 0, "11081 passed, 1 skipped, 28 deselected in 275.01s". (An earlier run on a draft head had 1 failure because my Postgres lacked PG* in its server environment: dblink-connect; fixed by restarting it with them.) The known timing test in tests/test_migration_numbers.py was not touched and did not fail this time.
- tests/stage_mutants.py (via heavy.sh): exit 0, "181 of 181 good". (An earlier run had 3 bad: M18f and M18l had stale snippets after the 1-based change, M19k survived because the shared secrets base now turns the raw OS error into its class sentence; re-pointed, and the folder test now asserts the kind's own sentence.)
- gitleaks on f4acee28..HEAD: no leaks found.


## Follow-up commit (lead's three items)
1. Stage mutants Y3, Y4, Y5 added. Final run via heavy.sh: exit 0, "184 of 184 good". Full pytest: exit 0, "11083 passed, 1 skipped, 28 deselected in 276.86s". ruff check, ruff format --check, bandit -ll, scan_repo all exit 0.
2. Spot check of 10 allowances (module, group): config.py moved-keys join (table in code); guard/http.py host that resolved to a refused address; store/migrate.py role does not exist; store/migration_numbers.py number 0000; sources/kubernetes.py log evidence id; approvals/cards.py button id; audit/chain.py checkpoint number; backends/table.py egress host list; llm/anthropic.py Azure URL; deferred.py not-available key. Each site was changed to print a configured value two ways (appended `+ str(entry)`, then `+ " " + self.settings.region`).
   - FIRST ROUND FOUND A REAL GAP: 9 of 10 passed the guard. A sum counted as a message only when one side was a string literal, so `f"..." + name` and `prefix + name` were not seen. Fixed in `_message_nodes` (a sum is a message unless one side is a number written in the code). Two planted faults added (variable prefix plus name; f-string plus name); both fail on the old guard (checked).
   - The wider rule found 10 more sites; each allowed with a reason after reading (URL builds, a host list, regex text, byte strings for digests, number maths, a list join). Three older inner allowances became part of the outer site and were removed.
   - After the fix: 10 of 10 sites fail the guard test in both variants (exit 1, the new site named as a violation, not only as a stale allowance; checked for the second variant on guard/http.py by hand).
   - Limit, plainly: this spot check proves a change of those 10 sites is caught; it does not prove the other 144 reasons are right.
3. gitleaks first, then one plain push.
