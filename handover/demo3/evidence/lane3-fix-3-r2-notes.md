# lane3-fix-3 round 2 (B3b): tests only, tests/test_path_confinement_lane3.py
Base f3c39cf8, Python 3.12, worktree /home/user/work/b3b-base. Patch: lane3-fix-3-r2.patch, sha256 5cbcb2c3bac4b5bd8c00667abbab559daf441b7f45adbfbf11b0cedeaab680e3 (1 file, +132). Applies (git apply --check): fresh f3c39cf8, after claims-stack-on-f3c39cf8.patch, after lane3-fix-1.patch.
Unmutated: tests/test_path_confinement.py + new file = 393 passed, 2 skipped (Windows-only tests). New file alone 15 passed, 1 skipped. Only Python 3.12 run (3.13 exists on the box, not run).
| item | experiment | decision | test | mutant proof (first failure) |
|---|---|---|---|---|
| T1 | realpath of tmp+"/a"+U+D800+"b" raises UnicodeEncodeError (a ValueError); confine, confine_existing, confine_anywhere all raise PathRefused "--f: cannot be resolved" | added real-input twin (POSIX only), mock kept with `boom(text,*a,**k)` | test_a_path_with_a_lone_surrogate_is_a_plain_refusal x3, test_a_path_that_cannot_be_resolved_is_a_plain_refusal x3 | M15 (ValueError dropped): 6 failed, first test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] |
| T2 | none | added, skipif not Windows (skipped here, untried on Windows) | test_a_path_on_another_drive_is_not_inside | not provable here |
| T3 | none | renamed to what each protects; ids only in docstrings; "Lane 3" removed from the docstring (file name keeps "lane3") | all | M03, M08, M11 (2 tests), M20 all fail: see the table in the next block |
| T5a | none | added | test_the_path_length_limit_counts_characters_not_bytes | B1 fsencode length: 4 failed, first that test |
| T5b | deleted working folder + relative path: PathRefused "cannot be resolved" for all three functions (deterministic on Linux) | added, skipif Windows | test_a_relative_path_after_the_working_folder_was_deleted_is_a_plain_refusal x3 | B2 `(ValueError,)`: 3 failed, first ...[confine] |
| T5c | mutant `== ""` against ORIGINAL tests: KILLED by test_a_path_that_names_an_allowed_folder_itself_is_refused_as_a_folder[confine] | NOT added | - | - |
| T5d | mutant `endswith("..")` against ORIGINAL tests: KILLED by test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] | NOT added | - | - |
| T4, T5e | declined by the plan | - | - | - |
Round-1 mutants against the renamed tests (all FAILED, unmutated passes): M03 test_a_str_subclass_cannot_answer_differently_on_a_later_call; M08 test_a_path_of_exactly_the_maximum_length_is_accepted (2 failed); M11 test_a_containment_check_that_cannot_decide_says_not_inside (2 failed); M15 as above; M20 test_a_new_name_of_exactly_the_maximum_length_is_accepted.
Mutants restored after each (git checkout in my worktree); git status shows only the new test file.
Not covered: Windows (T2, 255-char name on Windows, surrogate behaviour), Python 3.13, equivalent/POSIX-invisible mutants (normcase, _split_root). T5c/T5d runs used -x, so only the first failing test is recorded.
