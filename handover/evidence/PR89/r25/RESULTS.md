# PR89 round 25 evidence (EVIDENCE RUNNER: records only, no judgement, nothing fixed)
Head 580b4adf1f2e57398fd0c3f9a0e6430fb29f5d21 (worktree clean, `git rev-parse HEAD` matches); previous 4cc427b5; base origin/main 2a8c2aac. Raw logs: /home/user/build/evidence-raw/pr89-580b4adf/.

## Deviations and not run (first)
- `uv sync --locked --no-build` FAILED (hadavin-sdk editable has no binary distribution); I used `uv sync --locked --all-extras --group test` (rc 0). Log: sync.log, sync2.log.
- mypy is not in the locked venv, so in the full pytest the 2 mypy-win32 test cases SKIPPED (3 skipped total, builder had 1). I installed mypy into my own venv and ran those two cases alone: 2 passed at head (3.12 and 3.13); 2 failed on 4cc427b5.
- Fail-before on origin/main: the overlaid test module does not import (ImportError: cannot import name PASS_ENV_ALLOWED from tools.mutation_runner), so no per-test result exists there.
- Not run: Windows/macOS; perf and the flaky timing test (the ticket names no perf item); CI-only steps (CodeQL, Sonar, CodeRabbit). The leak probe and the builtin-name probe use the builder's own instrument scripts (leak.py, worker.py, copied with only paths changed), not scripts of mine.
- Other agents ran heavy jobs at the same time; my pytest took 427 s, wall time in queue not significant.

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| Changed files vs origin/main | git diff --name-only origin/main...HEAD | 0 | 9 files: CHANGELOG.md, src/hadavin_sdk/testing/mutation.py, tests/conftest.py, tests/fixtures/mutation_manifest.json, tests/mutation_runner_mutants.py, tests/test_mutation_runner.py, tests/test_mutation_runner_keywords.py, tests/test_mutation_runner_meta.py, tools/mutation_runner.py |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 319 files already formatted |
| bandit | uv run --with bandit bandit -q -r src demos tools -ll | 0 | only 2 "nosec encountered (B102)" warnings in src/hadavin_sdk/tools.py:389 |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| stage_mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| gitleaks origin/main..HEAD | gitleaks git --log-opts origin/main..HEAD | 0 | no leaks found |
| Full pytest at head, own Postgres 16.15 (PGHOST/PGPORT/PGUSER in server env), via heavy.sh | pytest -p no:cacheprovider -q -m "not live and not perf" -rs | 0 | 10816 passed, 3 skipped, 28 deselected in 427.70s |
| Full mutant run, alone after pytest, via heavy.sh | python tests/mutation_runner_mutants.py | 0 | 320 of 320 good; problems: [] |
| mypy --platform win32 tools/mutation_runner.py, Python 3.12 | uv run --python 3.12 --no-project --with mypy mypy --python-version 3.12 --platform win32 ... | 1 | Found 13 errors in 1 file (checked 1 source file) |
| same, Python 3.13 | same with 3.13 | 1 | Found 13 errors in 1 file |
| 498-case leak probe at head | leak.py (builder's, paths changed) | 0 | cases 498 with any SHOWN 0 worker_rc!=0 0 |
| Builtin-name probe (see below) | leak_builtin.py | 0 | cases 1185 with any SHOWN 8 worker_rc!=0 0 |

mypy 13 error lines (identical on 3.12 and 3.13): line 340 import-not-found for hadavin_sdk.testing.mutation (run with --no-project); getuid missing at 1143, 1154, 1236, 1276; os.O_DIRECTORY and os.O_NOFOLLOW at 1304; os.P_PID, WEXITED, WNOHANG, WNOWAIT at 1516; os.killpg and os.SIGKILL at 1541. Files: mypy-3.12.txt, mypy-3.13.txt.

## Builtin class name probe (71 built-in exception classes)
Password = class name in lower, upper and swapcase, 5 modes each (assert message, exception message, dynamic class named by the password, literal class, failing baseline raising the class): 355 + 355 + 355 cases, cases with any password form SHOWN: 0, 0, 0.
Also 8 class names (TimeoutError, ValueError, KeyError, OSError, RuntimeError, ConnectionError, PermissionError, AssertionError): password = first half of the name (40 cases): 8 cases SHOWN; password = "x9" + name + "q7" (40) 0 shown; password = "x9" + lowercase name + "q7" (40) 0 shown.
The 8 SHOWN cases: PFX_TimeoutError--baseline_fail_class (form lower, channel traceback text); PFX_ValueError x4 (assert_msg, exc_msg, exc_class_dynamic_plain, exc_class_literal; form lower, channel first_lines); PFX_RuntimeError--exc_msg (plain, first_lines); PFX_RuntimeError--baseline_fail_class (plain, traceback text and exception.repr); PFX_AssertionError--assert_msg (plain, first_lines). In each the password is a piece of the class name, or of the neutral word "value must be one" shown as the expect text; the builder's report says pieces do not hide the class (a test pins that). Record only, no judgement. Records: leak-builtin/leak-records.json in the raw folder.

## Fail-before (4cc427b5 src and tools, head test files, mutants and manifest overlaid; run of tests/test_mutation_runner.py + _keywords.py + _meta.py)
Head: 357 passed, 2 skipped (mypy absent). 4cc427b5 with overlay: 16 failed, 341 passed, 2 skipped (fb-wt-prev.log). Of the 16 new test functions added since 4cc427b5 (git diff -U0 of tests):
- FAIL on old code: test_a_file_that_is_not_private_is_refused_with_its_reason; test_a_made_private_file_is_checked_on_the_open_file_and_a_second_name_is_refused; test_a_temp_folder_is_made_by_the_one_helper_and_checked_and_a_refused_one_is_removed; test_every_folder_and_file_the_runner_creates_is_made_by_one_of_the_helpers; test_the_temp_folder_the_tests_folder_and_the_settings_folder_are_made_by_the_helpers; test_the_runner_does_not_call_os_fchmod_which_mypy_does_not_know_on_windows_before_python_3_13; test_a_password_equal_to_a_built_in_class_name_is_not_shown_as_the_class; test_a_password_equal_to_the_class_the_child_raises_is_not_in_first_lines; test_the_module_docstring_says_a_class_equal_to_a_secret_is_not_shown; test_a_bare_string_for_crash_markers_of_a_mutant_is_a_type_error_not_letters; test_connect_timeout_takes_one_to_five_digits_in_the_texts_and_in_the_code; test_the_order_of_the_bare_string_guards_is_the_one_the_docstring_gives; test_mypy_for_win32_reports_the_errors_the_texts_count (both [3.12] and [3.13], with mypy installed).
- PASS on old code: test_a_password_that_is_only_a_piece_of_a_class_name_does_not_hide_the_class; test_a_password_that_holds_a_whole_class_name_does_not_hide_the_class; test_the_header_names_every_mutant_whose_killer_is_skipped_on_windows_derived_from_the_skip_marks.
- Changed older tests that also failed on old code: test_the_manifest_pins_the_files_a_demo_copies; test_a_private_file_is_mode_0600_whatever_the_umask_is_emptied_and_follows_no_link; test_a_new_os_or_signal_name_is_noticed_so_the_win32_error_count_in_the_texts_stays_true; test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets.
- origin/main: collection ImportError (see above); not counted.

## Private-folder creation sites in tools/mutation_runner.py (grep: mkdtemp, mkstemp, open, write_text, makedirs, mkdir, os.open, copytree, copy; sites.txt)
Through helpers: mkdtemp 1189 (_make_private_temp_dir); os.mkdir 1179 (_make_private_dir), 1209 (_make_dirs); os.open 1253 (_make_private_file). Own checked code: os.mkdir 1303 and os.open 1304 (_open_lock_dir, fstat-checked); lock file os.open 1393/1395 (lock code, own checks).
Not through a helper (listed, no judgement): shutil.copytree at 1911, 1918, 1963, 1972 (create folders below the already private tmp/snap, `src` and extra dirs, in the default mode by copytree); shutil.copy at 1915, 1969 (create copied test files); p.write_text at 2011 (overwrites an existing file in the mutant copy; no folder or file created). No uses of mkstemp, makedirs, Path.write_text or builtin open( found by the grep in code lines (hits at 1178, 1186, 1697, 1899 are comments or docstrings).
