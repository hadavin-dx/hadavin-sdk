# Q8b fix batch 6: notes (builder; the lead's reviewers judge)

Base 6f32f0a8, code head 87f3e939 (branch core/q8b-b6, pushed to wip/cloud-q8b-b6). The notes commit after it changes only files under handover/.

## Tests that passed on the old code (review item 7)
New tests of this batch run against 6f32f0a8 source: 13 of 14 in `tests/test_q8b_batch6.py` fail there (raw output: `failbefore-new-tests-on-6f32f0a8.txt`; the CHANGELOG checks read the old CHANGELOG, so those fail for that reason too). The one that passes:
- `test_d6_a_flag_with_an_ordinary_word_stays_readable`: a control (it guards against over-masking by the new glued-flag rule, so it must pass on old code). Killed by mutant M91 (look-ahead for ordinary words removed).

The 3 tests the round-6 report named (they passed on the previous head 999ed05b):
- `test_j1_a_quoted_value_after_authorization_is_masked_whole`: its behaviour was added in an earlier batch; killed by mutant M80 (authorization removed from the quoted-value key words).
- `test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked`: tests the checking function of the test itself (a stand-in that masks only the first word must be reported). Control, no product mutant can fail it. Machinery mutant: `_older_rule_left_readable` made to ignore the other pieces of a half-masked value, run on a copy: the test FAILS (`machinery-mutations.txt`, mutation A); unmutated: passes.
- `test_j4_the_scan_finds_every_shape_of_a_second_list`: tests the scan function `second_key_lists` (tests/q8b_helpers.py). Machinery mutant: the scan needs four credential words instead of three, run on a copy: the test FAILS (`machinery-mutations.txt`, mutation B); unmutated: passes.

## The 44 new test functions (since main) that do not fail on main (list: ../6f32f0a8/failbefore-main-new-tests-passing-on-old.txt)
I assigned the reasons below by reading each test and the mutant list; I did not run a new mutant for each. 7 of the 44 lines are `XFAIL`: tests marked xfail in earlier batches (they record values the later sweep ticket Q8d is to mask; they fail on both main and head by design, unchanged here). The other 37 are listed with a mutant where one names them as its killer, or the stated reason.
| test | killed by | reason |
|---|---|---|
| test_the_plan_line_survives_a_masked_value_at_the_end_of_the_text | M50 | |
| test_i7_a_flag_or_a_key_ends_the_value | M62 | |
| test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked | M54, M55, M64 | |
| test_j1_every_cookie_key_the_older_cookie_rule_masked_is_still_masked_with_its_jar | M77 | |
| test_j2_ordinary_words_stay_readable_in_a_record | M60 | |
| test_j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value | M70 | |
| test_j4_names_that_are_no_credential_stay_readable | M85 | |
| test_n6_f6b_a_domain_outside_code_is_bracketed | M18, M45 | |
| test_n1_a_list_under_a_setting_key | M16 | |
| test_s4_two_placeholders_are_accepted | M5 | |
| test_s7_a_quoted_attempt_without_quotes_is_refused | M4 | |
| test_r4_a_number_or_one_word_in_a_secret_is_not_registered | M41 | |
| test_a_link_alone_is_still_removed_whole, test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept, test_i1_an_unrelated_not_set_line_stays_readable, test_i8_a_link_label_before_a_key_keeps_the_next_parameter, test_j3_the_stop_is_the_same_on_every_path, test_g8_an_ip_shaped_target_is_a_placeholder | none | regression guards: behaviour main already had, kept by the new rules; they must pass on main |
| test_g1_..., test_g2_..., test_g4_..., test_g6_..., test_n1_a_value_under_a_credential_key, test_n1_an_entry_of_a_secret, test_n2_..., test_n3_..., test_t1_every_key_the_older_rule_accepted_is_still_accepted, test_r1_..., test_r3_..., test_r10_... | none | record walk and refusal behaviour that main also had; new coverage of old behaviour (t1 is the oracle against main's own rules, so it passes on main by construction) |
| test_i3_corpus_is_not_empty_and_disjoint, test_i5_the_mutation_copy_list_covers_every_root_file_the_q8b_tests_open, test_n8_the_check_itself_catches_each_way_round, test_x9_has_cases_to_check | none | tests of the test data or helpers, not of product code |
| test_j6_no_shipped_text_names_an_internal_decision_number | none | text check of shipped files; passes on main because main has no such number |
Not done: a mutant for each row marked `none`. They are guards of main's behaviour or of test machinery; a product mutant that breaks main's behaviour is already covered by the neighbouring mutants where one exists.

## Item 1 to 4 (what changed)
See CHANGELOG.md (lines 8 and 11), `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/k1b/redaction.py`, `tests/test_q8b_batch6.py`, `tests/q8b_mutants.py` (M88 to M92 new; M71, M77, M81 re-pointed because the code they mutate changed; M81 was an equivalent mutant once the glued names were read by the shared endings, so it now removes the glued-ending branch).

## Final gate results (code head 915127a6)
- ruff check rc=0; ruff format --check rc=0 (330 files); bandit -ll rc=0 (0 issues); scan_repo rc=0; gitleaks rc=0 (no leaks).
- stage_mutants rc=0.
- First q8b_mutants run: 91 of 92 good, rc=1. M82 pointed at k1b/redaction.py, but the ordinary-word list moved to guard/redact.py (my slip). Re-pointed in 915127a6; second run: 92 of 92 good, rc=0 (q8b-mutants.log).
- mutation_runner_mutants as user nobody: 64 of 64 good, rc=0.
- Full `pytest -m "not live and not perf"` once, via heavy.sh, with the Postgres: rc=0, 10786 passed, 1 skipped, 29 deselected, 16 xfailed in 350.54s.
- test_the_timing_harness_flags_a_quadratic_stand_in (known flake) was not touched.
