# Q8a-1 batch 17 PR notes (builder, 2026-11-12)

Branch core/q8a1-b17 (base 20581c80), push target wip/cloud-q8a1-b17. Head sha: see the report.

## Fail-before (clean detached worktree of 20581c80, only tests/ and CHANGELOG.md copied in)
Command: `uv run --all-extras --group test pytest tests/test_q8a1_b17_fixes.py tests/test_changelog_claims.py tests/test_stage_names.py tests/test_guard_reasons.py tests/test_q8a1_b14_fixes.py tests/test_q8a1_b16_fixes.py tests/test_q8a1_b15_fixes.py -q -p no:cacheprovider -rA`
Result: exit 1, 20 failed, 767 passed. Raw output: /home/user/build/B-Q8a1-b17-failbefore.txt; failed ids: B-Q8a1-b17-failbefore-ids.txt.
Note: the guard and plant tests (tests/test_stage_names.py, tests/test_guard_reasons.py) are test-side code, so on old src they find the old sites; the old allowance table also has the stale rows. They fail on old code as one row each (one parametrized test each).

## Tests that PASS on 20581c80 and why (each is a control or is killed by a named mutant)
- test_a_valid_value_and_a_refusal_for_another_reason_still_work: control. A valid value and an unrelated refusal must keep working after the base class change; passes before and after by design.
- test_check_config_shows_no_text_of_a_failure_of_the_yaml_reader[yaml|other]: control. check-config already printed class only (batch 16); pins it so the new base class cannot reopen it.
- test_the_module_search_path_is_not_changed_by_these_tests: control for the test file's own hygiene (sys.path unchanged).
- test_every_device_name_with_a_digit_is_refused_as_an_event_id[com1|lpt9|con|nul]: control. These names were already refused; only com0 and lpt0 were missing (those two ids fail on old code). Kept so the whole family is pinned. Killers: Z223 (com0), Z224 (lpt0).
- test_a_parameter_borne_value_is_a_carrier_of_a_proc_site and test_a_scoped_allowance_allows_one_function_and_a_count_and_nothing_else: the fix is in the test-side guard (copied in), so they pass on old src by construction. Killed by Z227 (parameter carrier) and Z225/Z226 (scoped count, scoped stale).
- test_changelog_claims: test_every_test_name_in_the_changelog_is_defined_in_tests, test_every_repository_path_in_the_changelog_exists, test_the_numbers_of_older_entries_are_labelled_with_their_batch, test_the_handler_list_of_the_changelog_is_the_handlers_of_the_code: the CHANGELOG was copied in, and these check the CHANGELOG against the tree; on old src the handler list still equals the old handler count differently only through src, which is the same file set. Controls for the CHANGELOG. Killers: Z229 (handler list), Z230 (counts).
- Planted clean forms (R17c clean, R17t, R17u, R16o `n: int`) in tests/test_stage_names.py: controls. A clean form must produce no finding on any code; each is paired with a plant (R17c, R17d-R17s) that fails when the rule is removed (mutants Z202-Z218).
- test_a_failing_detector_is_logged_by_class_only[plain-error|bedrock-bare-id]: restored test. The Bedrock-shaped case (a bare guardrail id in the error) passes on old code because the class-only log existed since batch 14; the test was dropped in batch 16 and is restored, parametrized. Killer: Z90 with param [bedrock-bare-id].

## Handlers marked noqa: BLE001
54 sites in src (the brief said 45; the count is made with ast by tests/test_changelog_claims.py). None prints the text of the error. The per-site table (file, function, number, what is shown) is in CHANGELOG.md, batch 17, item 7. Three sites keep the error object for a caller thread to re-raise (HANDOFF: guard/http.py lookup, k1b/loop.py work, tools.py work); two show error_reason(exc) (REDACTED, still the owner question q-q8a1-hide-ids).

## Other
- Corrected table rows R16i, R16e, R16j, R16a (batch 16 text claimed the hash pin was unchecked and that Decimal is proven by the scan; both fixed in the CHANGELOG).
- Issue 7 (E1 q-q8a1-hide-ids, E2 ConfigName) is OWNER-ONLY, not built.
