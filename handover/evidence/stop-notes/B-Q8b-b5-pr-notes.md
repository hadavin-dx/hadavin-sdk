# Q8b fix batch 5: notes for the PR (builder, 2026-11-12)

Base 999ed05b, final head 666ec6fd (branch core/q8b-b5). Raw outputs are in /home/user/build/B-Q8b-b5-raw/ and /home/user/build/B-Q8b-b5-scratch/.

## Issue 11: the 8 batch-4 tests that passed on the old code

A test that passes on old code must say which change it guards. One line each: the mutant that makes it fail (a mutant puts the old, wrong code back), or why it is a control.

| Test | Why it passes on 999ed05b | What proves it still guards something |
|---|---|---|
| j3 `..._the_stop_is_the_same_on_every_path` | batch 4 already fixed the stop | mutant X1 (M70 text, this test as the killer, scratch/mutant_extra.py); M70 also kills the sibling j3 test |
| j3 `..._a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value` (the "stop" test) | same | M70 (killer, the expected-text assert) |
| j4 `..._names_that_are_no_credential_stay_readable` | control: it pins words that must NOT be masked | M85 (a flag name is read through the rest of its word) |
| j4 `..._the_scan_finds_every_shape_of_a_second_list` | control for the drift scan; it only passes if the scan is right | X3 (scan loses the `split` branch) and X4 (scan strips no non-letters), scratch/mutant_extra.py |
| j5 `..._a_secret_split_by_a_tag_is_masked_on_a_card` | batch 4 already fixed the card | M68 |
| j5 `..._the_card_test_reads_the_one_list_of_secret_kinds` | same | X2 (M68 text, this test as the killer) |
| j6 `..._the_comma_pin_matches_the_code` | pins the comma rule | M86 (comma always ends the value) |
| j6 `..._the_whole_line_after_a_bearer_key_is_masked` | pins the bearer rule | M87 (bearer key alternative removed) |

Results of X1-X4 and M85-M87 are in B-Q8b-b5-raw/q8b-mutants.log and B-Q8b-b5-scratch/mut-extra.log (see the report for what ran).

## Fail-before proof

The new and changed batch-5 tests, run on 999ed05b source: 8 failed, 140 passed, 15 xfailed (B-Q8b-b5-scratch/failbefore.log). The 8 failures: j1 oracle, j1 session jar, j1 every cookie key with its jar, j2 oauth, j2 corpus benign keys, j3 digit-led semicolon, j4 glued flag names, j6 changelog.

## Issue 10: the 8 `--KEY value` cases (raw: B-Q8b-b5-scratch/issue10-raw.md)

| Flag | main | 999ed05b | now |
|---|---|---|---|
| --newpass, --oldpass, --postgresauth | value readable (space form) | readable | masked (added to the flag rules) |
| --authorization | value readable, also in `=` form | readable | masked |
| --bypass, --compass, --oauth, --obsession | readable | readable | readable, as on main (ordinary words); `oauth` is masked in a record key |

Not fixed, stated plainly: other glued flag words (for example `--confirmpass`) stay readable as on main, because the ordinary-word list lives in k1b and guard may not import it.

## Gate at the final head (6f32f0a8; the only change after 666ec6fd is one mutant line in tests/q8b_mutants.py)

- Full pytest `-m "not live and not perf"` at 666ec6fd: 10772 passed, 1 skipped, 29 deselected, 16 xfailed, rc 0 (raw/pytest-full.log). Not re-run at 6f32f0a8: the diff is one line of a file pytest does not collect (stated, not hidden).
- q8b_mutants.py: the run at 666ec6fd gave 86 of 87 good: M85 survived (raw/q8b-mutants.log). Cause: my M85 removed an end boundary that never changes an output (every flag rule needs `=` or a space right after the name), so it was an equivalent mutant. Replaced by "a flag name is read through the rest of its word", which `test_j4_names_that_are_no_credential_stay_readable` kills (raw/q8b-m85.log). Run at 6f32f0a8: 87 of 87 good (raw/q8b-mutants-final.log).
- stage_mutants.py 37 of 37 good; mutation_runner_mutants.py as user nobody 64 of 64 good (raw/stage-mutants.log, raw/runner-mutants.log).
- X1-X4 extra killers: all KILLED (scratch/mut-extra.log).
- ruff check, ruff format --check, bandit -ll, scan_repo, gitleaks (origin/main..HEAD): see raw/*2.log.
