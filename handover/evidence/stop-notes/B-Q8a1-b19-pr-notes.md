# Q8a-1 batch 19: builder notes (fail-before and per-test reasons)

Base 51f206bc. Fail-before was measured in a clean detached worktree of 51f206bc (src as at 51f206bc), with the head versions of the
12 changed test files copied in over its tests/ folder (no shim was needed: the new test file imports on the old src because the
helpers it needs live in tests/). Raw output: /tmp/claude-0/failbefore.txt and /tmp/claude-0/b19_old.txt (scratch, not committed).

## Measured counts
- 7 test files run on old src with head tests: 879 tests, 23 failed, 856 passed.
- tests/test_q8a1_b19_fixes.py alone: 28 tests, 16 failed, 12 passed on old src.
- The old guard (tests/_text_guard.py of 51f206bc) with the head plants: R19a, R19b, R19c, R19h, R19i, R19j fail (6 of 12 new plant rows);
  the others pass on old (reasons below).
- Of the 23 failures on old src, 3 test_changelog_claims tests fail only because the old worktree has the old CHANGELOG text (not a
  behaviour fail-before: they check the new entry and counts); 1 is the mutant-list check on the old hidden_input.py text; 1 is
  the CLASSNAMES row check (config.py text changed); 1 is the guard scan of config.py; the rest are the Issue 1, 5, 7 behaviour tests.

## Per-test reasons for tests that pass on old code
- test_a_subclass_of_the_config_sentence_class_is_kept_as_that_class: control. The subclass kept its class in b18 already; the
  test pins it because the new `_without_chain` could break it (it did, in my first draft).
- test_a_second_pass_over_a_rebuilt_error_changes_nothing: control (idempotence held in b18; the new class methods run the rebuild on
  more paths, so it is pinned).
- test_the_place_line_of_a_dict_through_the_class_method_still_names_the_field: control for the new class methods (the place line
  of a mapping must keep the field name).
- test_the_scan_for_validate_options_finds_each_option_in_a_planted_source: control of a scan helper that lives in the test file.
- test_a_dict_entry_ignores_strict_so_the_model_config_is_what_applies: pins a pydantic behaviour (already true).
- Store tests (3): they test helpers in tests/_text_guard.py; the head helper is used here, so they pass; with the old helper they fail
  on ImportError (STORE_READS and the other names do not exist at 51f206bc).
- test_an_error_text_that_reaches_a_stored_record_is_found (3 rows): pins existing detection (r17 sinks) next to the new "not seen" rows.
- test_a_rebuilt_error_is_not_rebuilt_a_second_time_by_the_config_text: control of the plain-model test beside it.
- Plant rows that pass on the old guard: R19f (control: the text directive is still read), R19k (dict key carrier: existing branch,
  now killed by mutant Z272), R19l found-row (existing branch, killed by Z159 restored) and its clean twin, R19d (clean row, a control: it also passes with Z258 applied, measured) and R19e (clean row; killed by Z258 = restored Z163), R17t/R17u (renamed controls, as the review asked).

## Equivalence proofs (measured here, 2026-11-12)
- M16s (tools.py prints the raw `loc`): applied with the fix, test_an_unknown_key_in_a_tool_manifest_entry_is_not_shown still passes.
- M18v (strict_model.py without hide_input_in_errors): applied, test_a_kubernetes_api_url_with_a_login_does_not_put_the_url_in_the_raw_error_either
  still passes. Both stay removed; the rebuilt error already holds no text on that channel.
- Z159: NOT equivalent: restored with plant R19l (found 1 with the branch, 0 without; measured).
