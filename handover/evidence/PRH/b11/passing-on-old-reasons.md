# Tests of `tests/test_prh_b11.py` that PASS on 5c430b6a, with the reason each stays

Raw output: `../b12/failbefore-b11-new-tests-on-5c430b6a-regenerated.txt` (batch 12, issue 9: the first file held made-up token-shaped values in test ids and was removed; this one was regenerated from the shipped tests with no local values printed, same result: 45 failed, 29 passed) (45 failed, 29 passed on a clean detached 5c430b6a plus only the new test file). The 29 passing tests, by id, are in `passed-on-old-list.txt`.

| Tests (id fragment) | Reason it passes on the old code and why it stays |
|---|---|
| `g4_a_forged_marker_refusal_is_a_withheld_note_on_the_tool_path` | Pins a rule of batch 10 that the group 4 change (a crash passes, every other refusal is "nothing shown") could have broken: a forged marker is still a withheld note. No mutant; a pin of unchanged behaviour. |
| `g1_any_character_..._is_a_wrapper[!...]`, `[?...]` | `!` and `?` were already in the old list of nine wrapper characters; the rows pin that the new word-class rule keeps them. Mutant 167 (the old list of nine is back) is killed by the other rows of the same test. |
| `g1_a_letter_or_a_digit_glued_in_front...[letter, digit, latin_accent, devanagari]` | The old rule already blocked a run after a letter or digit; the rows pin that the new class (letters, digits, marks) keeps blocking, for ASCII and non-ASCII letters. |
| `g1_a_combining_mark_glued_in_front...` | The old character list already stopped the run before a mark in this one row; the lookbehind added in this batch is what mutant 168 removes, and its killer fails on that code. |
| `g1_the_shapes_of_backslash_e...[...]` (22 rows) | Rows with the expected result `True` before a bracket and `False` for `P X ^ _ n`, `C:\env`, `C:\Users\err\x`, short words: they pin the batch 10 narrowing that group 8 must not undo. The rows that change are the new ones and fail on old. Killer for the shape rule: mutant 171. |
| `g5_a_value_added_after_the_automaton_was_built_is_in_the_next_one` | On old the automaton was rebuilt on every call, so a new value was always in it. The test pins the new cache against going stale; killer: mutant 181. |
| `g8_..._not_shown[hand-ctx]`, `[hand-pre]`, `[shaped-ctx]` | Cells that already held on 5c430b6a (the key word in front, or a front spelling that the old rule masked). They pin the whole grid of the runner's cells; mutants 182 to 184 are killed by the other cells and by their own test (183). |
| `g8_a_windows_path_takes_no_heavier_path_and_is_left_as_written` | Pins the part of batch 10 that group 8 must not undo (`C:\env` stays as written); killer: mutant 185. |

Every other test of the file fails on 5c430b6a (45 of 74).
