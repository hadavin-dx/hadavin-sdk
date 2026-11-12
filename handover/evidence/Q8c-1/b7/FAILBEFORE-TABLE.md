# Fail-before table, Q8c-1 round 7 fix batch (builder notes, not an independent result)

Base for "old": `5015c990` (round 5 head) with the kind modules from that commit. Source of the lists:
`handover/evidence/Q8c-1/d598d967/passes-on-old.txt` (334 tests of the head's test files that pass there; the
runner copied head's `tools/policy_page.py` and `docs/declared-permissions.md` onto the old base). I picked, from
those 334, the tests that are new or changed in `5015c990..d598d967` (compared function by function with `ast`;
script output: 19 tests) and added the two `{path_prefix}` guard tests that the round 6 review asked about.

Why each one passes on old: the rule it guards lives in `tools/policy_page.py`, which the runner supplied from
the head, and the test plants its own data. The only source change of the delta (`secrets_vault.py`, the R17
reason text) is not involved. So "passes on old" says nothing about the guard; the proof that the guard is live
is the mutant: a revert of one rule in the tool, which the named test must fail first, with the message
fragment shown in `tests/policy_mutants.py` (`python tests/policy_mutants.py` reports `KILLED`).

| # | Test (all in tests/test_policy_guard.py) | Kind | Mutant that proves the guard live |
|---|---|---|---|
| 1 | test_a_builder_only_source_is_marked_wherever_the_page_lists_it | plant against supplied data (page text) | B3 a builder-only source id is shown without the mark; B5 the two builder-only lists of the head are returned in the wrong order |
| 2 | test_a_claim_text_that_ends_in_two_semicolons_or_repeats_is_refused | plant (edited head line) | B6 a claim text that holds two semicolons is accepted |
| 3 | test_a_claim_text_under_both_marks_is_refused | plant (edited head line) | B6 a claim text under both marks is accepted |
| 4 | test_a_claim_with_no_mark_two_marks_or_a_stale_text_is_a_problem_and_a_bad_line_is_refused | plant (changed marks object) | B5 a claim that carries two marks is accepted; B5 a start of a claim that matches no claim is accepted; B6 an empty claim text in the head is accepted |
| 5 | test_a_clause_appended_to_a_claim_is_no_longer_the_listed_claim | plant (edited module text) | B6 a claim with a clause added is still matched by its start |
| 6 | test_a_grant_whose_name_is_unchecked_with_no_pending_row_is_reported_by_the_check | plant (edited module text) | B6 the check command does not run the rule for names with no dated entry |
| 7 | test_a_kind_whose_module_could_not_be_read_adds_no_stale_class_line | plant (a kind left out) | B6 a kind that could not be read gets a stale class line for each of its notes |
| 8 | test_a_new_unchecked_claim_with_no_pending_row_is_reported_by_the_check | plant (edited module text) | B6 the check command does not run the rule for claims with no dated entry |
| 9 | test_an_empty_vault_prefix_is_refused_and_the_page_says_so_first | control for an earlier class (a value must match its grammar) | E5 a value that does not match its grammar is put into the text |
| 10 | test_every_claim_has_one_of_two_marks_taken_from_the_head_of_the_sources_file | data pin on the real files, rule in the tool | B5 the two marks of a claim are swapped |
| 11 | test_every_note_with_a_sources_class_shows_its_source_ids_after_the_note_and_in_the_source_list | control for an earlier class (note classes) | B4 a note of class sources shows no source ids; B4 the page lists no source named only by a note |
| 12 | test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim | control for an earlier class (no copy-ready text with an unchecked item) | E2 copy-ready text is offered for a kind with an unchecked grant; B3 ... an unchecked claim (only that clause dropped) |
| 13 | test_the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line | plant (edited head) | B4 a builder-only id that is no row of the sources file is accepted; B4 a second builder-only line is accepted |
| 14 | test_the_builder_only_marks_are_read_from_the_head_of_the_sources_file_and_match_its_list | data pin on the real head | NEW in this batch: B7 the last id of each id line of the head is dropped |
| 15 | test_the_fixture_head_names_the_builder_read_claims_as_they_are | data pin on the fixture text (no code rule to revert) | no code mutant possible; probes on the fixture (this batch, reverted after): "(6 different texts)" to "(5 ..." fails with `assert '(6 different texts)' in ...`; "the other 7" to "the other 8" fails with `assert 'the other 7' in ...`; dropping B-POL from the PARTLY line fails with `assert 8 == 9`. The probe that changed "only V-POL and B-POL have a builder-read passage" did not match the text (the sentence wraps over two lines), so that phrase is not probed |
| 16 | test_the_marks_of_r17_and_r18_swapped_in_the_sources_file_are_reported_by_the_check | plant (edited head) | B6 a builder-read mark on a claim of an entry that names no builder-only source is accepted; B6 an entry that names a builder-only source needs no builder-read claim |
| 17 | test_the_page_head_lists_the_claims_of_each_mark_from_the_sources_file_not_from_prose | plant (changed marks object) | NEW in this batch: B7 the page head lists the claims of the first mark from the wrong list (the assertion message was made unique so the first-line check is not weak) |
| 18 | test_the_page_takes_its_marks_from_the_root_it_is_given | plant (a second root) | NEW in this batch: B7 the page takes its marks from the default root, not from the root it is given |
| 19 | test_the_path_prefix_setting_is_read_as_one_or_more_parts_each_ending_in_a_slash | control for an earlier class (the `{path_prefix}` automaton, round 5) | B5 a `+` reads exactly one character; the B4 mutants "read as one part only" and "not ended by a slash" are killed by the sibling test below |
| 20 | test_a_never_path_deeper_than_the_prefix_grant_is_not_reported_as_covering_it (the `{path_prefix}` guard test the round 6 review named; unchanged, passes on old and on main) | control for an earlier class (a deeper never path must not overlap grant R17) | B5 the two paths of a prefix check may hold a different number of parts for the one setting (`k` against `k + 2`), expect fragment `{mount}/data/{path_prefix}+/deeper/+`; also B5 the lookahead that keeps `{path_prefix}` out of the one-word replacement is dropped (killer: test_a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught) |

## Tests added or changed in this batch (round 7)

| Test | Fail before (old tool = d598d967) | Mutant |
|---|---|---|
| test_from_the_review_date_the_write_command_and_the_check_command_both_stop (new) | On the old tool (with only an alias `DECIDED` added so the test file imports) it fails: `main()` takes no `today` (TypeError). 12 tests of the file fail there for that reason, 329 pass | B7 the write command writes the page although the dated entries are overdue; B7 the check command ignores the day it is given |
| test_a_reason_is_matched_by_its_exact_text_even_when_a_class_key_is_its_unique_prefix (new) | Passes on old by construction (the tool already matches a reason by exact text); the proof is the mutant | B5 a reason is matched by its start, not by its exact text: its killer is now this test (planted unique prefix `zq planted reason ...`, no look-alike in the data), with its own expect text `is read as the class of that prefix` |
| the 13 date-dependent tests (`_check`, `data_problems`, `main` calls now pass `today=DECIDED`) | With the clock faked to 2026-12-12 (a pytest plugin that replaces `datetime` in the tool): old guard test file 13 failed, 326 passed; new guard, changelog and docs test files together 0 failed, 345 passed | the red signal itself is kept by test_the_check_command_reports_..._overdue_entry (today=2026-12-12) and the new write/check test |
| the byte-order mark in `tools/policy_page.py` written as an escape | grep for the literal bytes EF BB BF in `src tools tests` (sources, not caches): no hit after the change | B6 the byte-order mark is not dropped from the sources file (its `old` text now holds the escape as written in the tool) |
