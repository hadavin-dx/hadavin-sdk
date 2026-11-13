# Evidence E4b: lane3-fix-3 r2 and r3 (tests only, raw results, no judgement)
Run 2026-11-13 13:01-13:32Z (IST +5:30). Base f3c39cf89ec989f032ea48a23cfd824b88da9c68, Python 3.12 final-venv, TMPDIR /home/user/work/e4b-tmp and e4c-tmp (outside worktrees).
Gaps: a first command with an rm of a TMPDIR glob was refused by the safety check (not run; fresh folder used instead). No other gaps. Hand-mutant (d) survives new file alone (killed only by old file).

## Section r2
sha256 5cbcb2c3bac4b5bd8c00667abbab559daf441b7f45adbfbf11b0cedeaab680e3: MATCH (sha256sum of lane3-fix-3-r2.patch). Worktree /home/user/work/e4b-base; after patch `git status --short` = `?? tests/test_path_confinement_lane3.py` only.

### Counts
| Run | Result |
|---|---|
| new file alone | 15 passed, 1 skipped (rc 0) |
| old file alone | 378 passed, 1 skipped |
| old + new | 393 passed, 2 skipped (rc 0) |
| new file alone, ids reversed | 15 passed, 1 skipped (rc 0) |
| old + new, 395 ids reversed | 393 passed, 2 skipped (rc 0) |

Order dependence: none seen (forward and reversed both green; pytest-randomly not installed).

### Mutants (old string replaced once in tools/pathconfine.py, restored after each; git diff --stat empty after every one)
| id | old -> new | new file alone | old file alone | old+new |
|---|---|---|---|---|
| M03 | `'text = str.__str__(text)' -> 'pass'` | KILLED by tests/test_path_confinement_lane3.py::test_a_str_subclass_cannot_answer_differently_on_a_later_call | SURVIVES | not run |
| M08 | `'if len(text) > MAX_PATH_CHARS:' -> 'if len(text) >= MAX_PATH_CHARS:'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_of_exactly_the_maximum_length_is_accepted | SURVIVES | not run |
| M11 | `'    except ValueError:\n        return False' -> '    except ValueError:\n        return True'` | KILLED by tests/test_path_confinement_lane3.py::test_a_containment_check_that_cannot_decide_says_not_inside | SURVIVES | not run |
| M15 | `'except (OSError, RuntimeError, ValueError) as exc:' -> 'except (OSError, RuntimeError) as exc:'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] | SURVIVES | not run |
| M20 | `'len(name) > MAX_NAME_CHARS' -> 'len(name) >= MAX_NAME_CHARS'` | KILLED by tests/test_path_confinement_lane3.py::test_a_new_name_of_exactly_the_maximum_length_is_accepted | SURVIVES | not run |
| Ha | `'len(text) > MAX_PATH_CHARS' -> 'len(os.fsencode(text)) > MAX_PATH_CHARS'` | KILLED by tests/test_path_confinement_lane3.py::test_the_path_length_limit_counts_characters_not_bytes | KILLED by tests/test_path_confinement.py::test_a_lone_surrogate_is_a_plain_refusal_not_a_unicode_error | KILLED by tests/test_path_confinement.py::test_a_lone_surrogate_is_a_plain_refusal_not_a_unicode_error |
| Hb | `'except (OSError, RuntimeError, ValueError)' -> 'except (ValueError,)'` | KILLED by tests/test_path_confinement_lane3.py::test_a_relative_path_after_the_working_folder_was_deleted_is_a_plain_refusal[confine] | KILLED by tests/test_path_confinement.py::test_a_deleted_working_folder_is_not_a_traceback | KILLED by tests/test_path_confinement.py::test_a_deleted_working_folder_is_not_a_traceback |
| Hc | `'except (OSError, RuntimeError, ValueError)' -> 'except (OSError, RuntimeError)'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] | SURVIVES | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] |
| Hd | `'name.endswith(".")' -> 'name.endswith("..")'` | SURVIVES | KILLED by tests/test_path_confinement.py::test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] | KILLED by tests/test_path_confinement.py::test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] |

## Section r3
sha256 b272b9a88b6daa96dc76cc7ed150552c1d16ee26b8aee051ed374db88db4d4ed: MATCH (sha256sum of lane3-fix-3-r3.patch). Worktree /home/user/work/e4c-base; after patch `git status --short` = `?? tests/test_path_confinement_lane3.py` only.

### Counts
| Run | Result |
|---|---|
| new file alone | 15 passed, 1 skipped (rc 0) |
| old file alone | 378 passed, 1 skipped |
| old + new | 393 passed, 2 skipped (rc 0) |
| new file alone, ids reversed | 15 passed, 1 skipped (rc 0) |
| old + new, 395 ids reversed | 393 passed, 2 skipped (rc 0) |

Order dependence: none seen (forward and reversed both green; pytest-randomly not installed).

### Mutants (old string replaced once in tools/pathconfine.py, restored after each; git diff --stat empty after every one)
| id | old -> new | new file alone | old file alone | old+new |
|---|---|---|---|---|
| M03 | `'text = str.__str__(text)' -> 'pass'` | KILLED by tests/test_path_confinement_lane3.py::test_a_str_subclass_cannot_answer_differently_on_a_later_call | SURVIVES | not run |
| M08 | `'if len(text) > MAX_PATH_CHARS:' -> 'if len(text) >= MAX_PATH_CHARS:'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_of_exactly_the_maximum_length_is_accepted | SURVIVES | not run |
| M11 | `'    except ValueError:\n        return False' -> '    except ValueError:\n        return True'` | KILLED by tests/test_path_confinement_lane3.py::test_a_containment_check_that_cannot_decide_says_not_inside | SURVIVES | not run |
| M15 | `'except (OSError, RuntimeError, ValueError) as exc:' -> 'except (OSError, RuntimeError) as exc:'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] | SURVIVES | not run |
| M20 | `'len(name) > MAX_NAME_CHARS' -> 'len(name) >= MAX_NAME_CHARS'` | KILLED by tests/test_path_confinement_lane3.py::test_a_new_name_of_exactly_the_maximum_length_is_accepted | SURVIVES | not run |
| Ha | `'len(text) > MAX_PATH_CHARS' -> 'len(os.fsencode(text)) > MAX_PATH_CHARS'` | KILLED by tests/test_path_confinement_lane3.py::test_the_path_length_limit_counts_characters_not_bytes | KILLED by tests/test_path_confinement.py::test_a_lone_surrogate_is_a_plain_refusal_not_a_unicode_error | KILLED by tests/test_path_confinement.py::test_a_lone_surrogate_is_a_plain_refusal_not_a_unicode_error |
| Hb | `'except (OSError, RuntimeError, ValueError)' -> 'except (ValueError,)'` | KILLED by tests/test_path_confinement_lane3.py::test_a_relative_path_after_the_working_folder_was_deleted_is_a_plain_refusal[confine] | KILLED by tests/test_path_confinement.py::test_a_deleted_working_folder_is_not_a_traceback | KILLED by tests/test_path_confinement.py::test_a_deleted_working_folder_is_not_a_traceback |
| Hc | `'except (OSError, RuntimeError, ValueError)' -> 'except (OSError, RuntimeError)'` | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] | SURVIVES | KILLED by tests/test_path_confinement_lane3.py::test_a_path_with_a_lone_surrogate_is_a_plain_refusal[confine] |
| Hd | `'name.endswith(".")' -> 'name.endswith("..")'` | SURVIVES | KILLED by tests/test_path_confinement.py::test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] | KILLED by tests/test_path_confinement.py::test_v3_a_new_name_that_ends_with_a_dot_is_refused[new.] |
Mutants M03,M08,M11,M15,M20 are all SURVIVED rows of q8-logs/results.jsonl (34 rows: 29 killed, 5 survived); Ha-Hd are hand-made; Hc equals M15.
