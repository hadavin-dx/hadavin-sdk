# R7U builder A: results (2026-11-14, started 16:06 UTC, written 16:57 UTC; IST = UTC+5:30)

## NOT RUN / NOT CHECKED / FAILED (first)
- NOT RUN: no full suite (the lead runs ONE guard run after the merge). Run only: my file (41 tests) and the related files tests/test_r7t_findings.py, tests/test_real_check_dry.py, tests/test_r7s_findings.py (269 passed together).
- NOT CHECKED: no Windows run; no live service; the other builders' hunks (B: smtp-counter read near line 1308; C: other files) are not merged, so the combined result is untested. My hunks avoid their lines (my F7 block sits after the `floor_checks(...)  # +1: the twin is a lead` call, B's read line is above it).
- NOT MINE (left to B/C per the order): m5, m6, m7, m8, n1-n5, the put-where-_settle_create-raises test, the two-concurrent-puts test, the 201-without-id test. crm_hubspot.py is untouched, so m1 is NOT made exact (see m1 below).
- FAILED: nothing at the end. During the work: one ruff run found 3 E501 + 1 format hit; fixed (comment/docstring wrapping only, wording of the note unchanged), ruff re-run clean.
- Honest note on m2: on r7t sources the value 1e999 does NOT crash the reader: load_json_file already rejects it (test passes on r7t, PIN). The ArithmeticError catch is proven only by monkeypatching load_json_file to raise (those tests fail on r7t).
- Honest note: 10 of my main-level tests run real desk processes (about 20-35 s each, 10-15 min for the file under load); no sleeps in the tests themselves.

## Findings
| id | rule now | tests |
|---|---|---|
| M1 | possible = created + min(max(0,open), max(0, leads - created)); `created` never capped; no lead count: created + open | test_a1_one_more_created_than_leads_is_not_hidden_by_the_cap[1,2,5,9]; test_a1_the_rule_equals_the_brute_force_oracle_on_every_small_input (independent brute-force oracle, 8x9x9x9 inputs); test_a1_named_values_of_the_rule; main-level exit code and message: test_a1_an_out_of_book_contact_ends_the_run_as_failed ("1 contacts may be left"), test_a1_a_duplicate_create_under_list_lag_is_counted_whole ("2 contacts may be left"); test_a1c_...[create_open, create_unknown] |
| m1 | stated in the docstring of contacts_not_accounted_for. Not exact (counters carry no lead ids; fixing it needs crm_hubspot.py, not my file): a create unknown in one desk process and retried with 201 in another counts twice. Safe direction: shows as one contact too many ONLY when another lead has no contact; with every lead holding its contact the cap absorbs it: no false EXIT_FAILED | test_a1b_a_retried_unknown_create_is_absorbed_when_every_lead_has_its_contact (PIN), test_a1b_the_over_count_is_never_a_false_alarm_when_the_list_shows_every_contact (main level, exit 0), test_a1b_a_retry_in_another_desk_process_counts_twice_in_the_safe_direction (real adapter, two counter files, PIN of the residual: f(1,1,1,1)==0, f(1,1,1,2)==1) |
| m2 | a counter value counts only if type(v) is int and v >= 0; one bad value makes the whole file unreadable (nothing added); ArithmeticError caught | test_a2_a_counter_value_that_is_not_a_whole_number_from_zero_is_unreadable[1e999,-1,0.9,1.0,true,false,"5",null,[1],{},-1e999]; test_a2_whole_numbers_from_zero_are_read; test_a2_one_bad_value_...; test_a2_an_arithmetic_error_...[Overflow,ZeroDivision,Arithmetic]; test_a2_a_counter_that_is_not_an_object_is_unreadable; main level test_a2_a_counter_with_a_bad_value_ends_the_real_run_as_failed |
| m3 | F7 check (counter_check) appended to the checks and `counter_known`, `unseen_contacts` put in summary BEFORE write_result; ok false when counter unknown or unseen > 0; table prints "AT LEAST ONE CHECK FAILED" | test_a3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok; test_a3_contacts_not_accounted_for_are_in_the_result_and_the_result_is_not_ok; test_a3_a_clean_run_says_so_in_the_result_and_the_table (exit 0, ALL CHECKS HOLD); test_a3_the_counter_check_is_ok_only_for_a_known_counter_and_no_unseen_contact. The test spies on write_result so it checks the payload at the moment it is written |
| m4 | _readback_failed takes the CounterRead (checked reader); unknown counter: "an unknown number of"; otherwise shows "N create requests were still open and M ended with an unknown outcome (each may have made one more contact)" and "up to X contacts may still be in HubSpot" with X from the counting rule | test_a4_the_readback_note_shows_the_open_and_unknown_creates; ..._with_no_open_create_does_not_mention_one (PIN); ..._does_not_name_a_number_when_the_counter_is_not_known; ..._gives_the_most_contacts_that_may_be_left[(100,0),(0,100),(60,40)] |

## Before/after on r7t sources (41 tests; before = out/R7U-A/before-final.log on a byte copy of tree-R7T + my test file; after = final-a.log)
Before: 29 failed, 12 passed (671.9 s). After (final bytes): 41 passed (646.9 s).
PIN on r7t (12, pass on both; the code was right, they state a rule or kill a mutant): a1b_a_retried_unknown_create_is_absorbed..., a1b_a_retry_in_another_desk_process..., a1c[create_open], a1c[create_unknown], a2_a_counter_that_is_not_an_object, a2 value ids 1e999, -1e999, [1], null, {}, a2_whole_numbers_from_zero_are_read, a4_..._with_no_open_create_does_not_mention_one.
FAILS on r7t (29): all other ids; list in failed-ids.txt (a1 x4 + oracle + named + 2 main-level, a1b main-level (fails because summary has no unseen_contacts), a2 -1, 0.9, 1.0, true, false, "5", one_bad_value, 3 arithmetic, real_run, a3 x4, a4 x3 + 3 parametrized).
Note: the a1 main-level and a3 tests fail on r7t for the reasons the review named (exit 0 with a contact left; ok:true with unknown counter; no fields in the JSON).

## Changed existing tests
None. Existing t15 values (f(8,8,1,9)==1, f(9,9,1,9)==0, f(9,8,1,9)==1, f(8,4,-3,9)==4, f(0,0,1,None)==1) all still hold (test_r7t_findings: passed in the 269).

## Mutants (out/R7U-A/mut_a.py, ONE runner, ONE copy; each file restored from tree-R7U-A and byte-compared: 38 of 38 restored-byte-equal=True; raw: mut-results.tsv, mutraw-*.txt)
38 mutants, 38 KILLED, 0 survived.
- Cap formula M01-M13: leads instead of leads-created, no max(0,..), + for -, swapped operands, min->max, no max(0,open), +1 / -1 / off-by-one on the cap, created - open, `if leads:` for `is not None`, no outer max, max(1,..): all KILLED by test_a1_*/test_a1b_*.
- Int-only check I01-I09: isinstance for type is int, > 0, >= -1, no type clause, any for all, ArithmeticError dropped, raise removed, update emptied, `or` for `and`: all KILLED by test_a2.
- Result file F01-F10: counter_known field True, unseen field 0, F7 not appended, ok = known, ok = not unseen, unseen computed with 0 accounted, compute when counter unknown (crash), create_unknown dropped, create_open dropped, ok ignores last check: all KILLED by test_a3/test_a1c.
- Read-back note B01-B06: known = True, only open counted, always the open sentence, no lead cap, wrong number in the sentence, swallowing reader: all KILLED by test_a4.

## Ruff and suppressions
ruff 0.17.1 on a copy (deleted after): check "All checks passed!", format --check "232 files already formatted". Suppressions by the one method: 367 (r7t 367), delta 0.

## Files
Changed: scripts/run_real_check.py (hunks: _readback_failed + its call, contacts_not_accounted_for + docstring, new counter_check, read_counter_files_checked, F7 block before the table, 2 summary fields, later block uses the values computed earlier); new: tests/test_r7u_a_findings.py.
r7u-A.diff (sha256 fef18f1070ab4e0a6a42be2a49a7c037fca2fae0520c27cabaccbbb9ae789d44; applies with patch -p1 to r7t, result sha256 of run_real_check.py 850c5dbf..., test file 6a9a020e...).

## Residuals
- m1 over-count not exact (above): needs lead ids in the counters (crm_hubspot.py, another builder's area); safe direction, pinned, documented.
- Combined run with B and C not tested.
- Answer to "take-side banner test q1": tests/test_r7q_findings.py::test_q1_the_banner_cost_counts_the_longest_request_the_run_can_send (line 110); "take-side" is not a word in the repo, I took it to mean the Start? banner cost test q1; unverified.
