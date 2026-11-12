# New tests of batch 12 that also pass on 242dfd66, with the one reason each exists

Raw output: `failbefore-b12-new-and-changed-tests-on-242dfd66.txt` (clean detached worktree at 242dfd66; the three changed or new
test files copied in; 68 failed, 163 passed over `tests/test_prh_b12.py`, `tests/test_prh_b11.py`, `tests/test_prh_b8.py`).
Of the new file `tests/test_prh_b12.py` the tests that PASS on 242dfd66 are (counted per test function; the number is the count of
parameter rows):

| Test | Rows | The one reason it exists |
|---|---|---|
| `test_b12_i1_extract_and_the_k1b_loop_let_a_crash_of_the_redactor_stop_the_run` | 1 | Issue 1: those two catchers already let a crash pass; the test pins it so a later "catch everything" change fails. Not a mutant of its own (no code changed there). |
| `test_b12_i1_the_injection_check_stops_the_run_when_the_log_line_crashes_the_redactor` | 1 | Issue 1: the rule for this catcher lives in `safe_head` (mutant 163); the test pins the whole path through `injection_check`. |
| `test_b12_i2_a_backslash_e_glued_between_two_characters_of_a_word_is_read_as_esc` | 1 of 5 | The two last rows (12 characters after, and a colon that is no drive letter) pass on old code: they pin the 12-after rule and the colon rule one reason each. The other 4 rows fail. |
| `test_b12_i2_a_path_name_after_a_backslash_is_left_as_written` | 5 | Control: a path name is not read as ESC. It passes on old code because the old rule had no glued rule; it pins that the new glued rule does not read folder names (mutants 193 and 194). |
| `test_b12_i2_a_value_with_a_backslash_e_at_any_place_is_not_shown` | 22 of 63 | The cells (offsets and every-N spellings) the old code already masked or withheld; the other 41 fail on old code. Kept in the grid so the grid is complete. |
| `test_b12_i2_the_chain_rule_reads_a_backslash_e_one_character_from_the_next_one` | 2 | The chain rule already existed (batch 11); the test is the only direct test of it after batch 12 moved the glued rule next to it (mutant 182). |
| `test_b12_i3_a_key_that_is_a_piece_of_a_held_secret_is_still_not_new` | 1 | Control: a piece of a held SECRET is still "already found" at both sites, so the fix did not make every reading win. |
| `test_b12_i6_a_spaced_key_with_a_gap_character_glued_at_the_head_or_the_tail_is_masked` | 12 | The review's claim that this shape regressed end to end was measured wrong: on old code the hidden-character strip runs first and the key is masked at run and tool level. The test pins the result for the rows the review named, beside the run-level test that fails on old code. |
| `test_b12_i7_a_long_held_value_still_covers_a_spaced_copy_inside_it` | 1 | Control: the 12-character limit does not break the case batch 11 built. |
| `test_b12_i8_computing_does_use_up_the_work_budget` | 1 | Control: the budget still stops a call that computes past it. |

The two docs tests of issue 4 (`test_b12_every_figure_...`, `test_b12_a_planted_wrong_figure_...`, `test_b12_the_numbers_file_...`)
read the new numbers file, which does not exist on 242dfd66, so they are not part of this fail-before run (documents are not in the
mutant run either). The planted-figure test is the proof asked for: it shows the comparison reports figures that no file holds.
