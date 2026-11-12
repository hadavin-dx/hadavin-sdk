# PR89 round 27: fail-before table (Issue 10 of the round 26 report)

Old code = the source of head `916c71ea`. Method: the new or changed test files were copied onto a detached worktree of `916c71ea` (source and tools unchanged) and the new or changed tests were run (raw: `fb-old-src.log`). Result: 4 failed, 9 passed, 2 skipped (the two mypy cases: mypy is not installed in the locked test environment).
A test that passes on old code is listed below with one line each: the reason it cannot fail there, and the mutant or the scratch change that makes it fail. The scratch changes are in `fb-scratch.log` and `fb-old-reader.log`.

## Fail on old code (4)
| test | why it fails on old code |
|---|---|
| `test_a_file_with_a_second_name_keeps_its_mode_when_it_is_refused` | old `_make_private_file` narrowed the shared inode to 0600 before the check |
| `test_a_named_pipe_under_the_name_of_a_made_file_does_not_block_the_open` | old open had no `O_NONBLOCK` (the test also fails for the new mutant "a named pipe under the name of a made file blocks the open") |
| `test_the_docstring_says_that_ci_does_not_run_the_mypy_count` | old docstring has the text "left to the lead" and not "the repo test is skipped where mypy is not installed" |
| `test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets` | the re-pointed and new mutants search for text that only the new runner has |

## Pass on old code (9): one line each
| test | reason it passes on old code | what makes it fail |
|---|---|---|
| `test_the_parts_between_are_made_by_the_private_helper_also_under_umask_0277` | the runner code was right; the change is in the test (helper spy first, `OSError` turned into the fragment) | mutant "the folders between are made without the private helper": killed with the fragment as root AND as a user who is not root (see `mutants-nonroot.log`, `mutants-root.log`); on the round 26 test the same mutant gave a `PermissionError` line without the fragment for a non-root user |
| `test_every_folder_and_file_the_runner_creates_is_made_by_one_of_the_helpers` | the count of every creating call of the old runner equals the new pin (the runner has one call per spelling and function, except where the pin says more) | scratch: a second `os.mkdir` in `_make_private_dir` fails the new pin and passes the round 26 pin (`fb-scratch.log` (b)) |
| `test_the_creation_site_walk_sees_aliases_module_level_code_and_the_other_creating_spellings` | the old walk gives the same sites for the old inputs; the new check (two calls in one function) concerns the new return shape | the round 26 walk on that input gives `{'os.mkdir': {'f'}}`, a set that cannot show 2 (`fb-scratch.log` (d)) |
| `test_the_header_names_the_killers_that_drop_a_case_by_the_system_name_and_both_lists_are_checked` | it checks the header and the test file, not the runner | scratch: one name removed from the hand-kept list fails it (`fb-scratch.log` (a)) |
| `test_every_decorator_is_read_even_after_a_true_mark_and_an_unreadable_one_raises` | it tests the reader of the test file, not the runner | scratch: the round 26 reader (`return whole or any(<generator>)`) put back fails it (`fb-old-reader.log`) |
| `test_a_module_level_pytestmark_and_a_named_mark_are_read_and_an_unknown_decorator_is_an_error` | same: tests the reader | the same scratch (`fb-old-reader.log`) |
| `test_the_header_names_every_mutant_whose_killer_is_skipped_on_windows_derived_from_the_skip_marks` | header against marks; the runner is not involved | scratch: a new mutant name removed from the POSIX-only list fails it (`fb-scratch.log` (c)) |
| `test_that_ci_does_not_run_the_mypy_count_is_true_of_the_workflow_and_the_lock_file` | the statement is true of the old tree too (the workflow does not name mypy, the lock has no mypy) | scratch: one word `mypy` added to the workflow file fails it (`fb-scratch.log` (e)) |
| `test_the_header_names_every_mutant_whose_killer_skips_inside_its_body_and_each_skip_is_there` | header against `pytest.skip` calls; the runner is not involved | unchanged list contents; control test of the same class as the one above (not separately mutated) |

## Mypy test (2 cases, skipped on old code here)
`test_mypy_for_win32_reports_the_errors_the_texts_count[3.12|3.13]` is skipped in the locked environment. It was run with mypy 2.4.1 added for the run only (`uv run --with mypy==2.4.1`): see `mypy-test.log`.
