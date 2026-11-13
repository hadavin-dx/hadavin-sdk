# Evidence E4: lane3-fix-3 patch (raw, no judgement)
Run 2026-11-13T12:58:52Z. Base f3c39cf89ec989f032ea48a23cfd824b88da9c68, worktree /home/user/work/e4-base, Python 3.12.3.
sha256 of lane3-fix-3.patch: 9084e0d849c9b59efa38fe0a357522df0b854aaf5418a882da0231276e0c6073 (matches, applied with git apply).

Note: a first step-2 run with TMPDIR inside the worktree gave 11 failed / 375 passed (my setup slip: repo-internal temp dir). Re-run with TMPDIR outside the repo: result below.

## Counts
- Step 1 (new file alone): 8 passed.
- Step 2 (old file + new file): 386 passed, 1 skipped.
- results.jsonl re-read: 34 mutants, 5 SURVIVED (M03, M08, M11, M15, M20), no new survivors.

## Survivors of Q8 (all 5 old texts occur exactly once)
| mutant | old -> new | original tests | with the patch | first failing test |
|---|---|---|---|---|
| M03 | `text = str.__str__(text)` -> `pass` | SURVIVES (PASS 378 passed, 1 skipped) | KILLED | test_m03_a_str_subclass_cannot_change_the_ans |
| M08 | `if len(text) > MAX_PATH_CHARS:` -> `if len(text) >= MAX_PATH_CHARS:` | SURVIVES (PASS 378 passed, 1 skipped) | KILLED | test_m08_path_length_boundary_uses_the_consta |
| M11 | `except ValueError:         return False` -> `except ValueError:         return True` | SURVIVES (PASS 378 passed, 1 skipped) | KILLED | test_m11_inside_answers_not_inside_when_commo |
| M15 | `except (OSError, RuntimeError, ValueError) as exc:` -> `except (OSError, RuntimeError) as exc:` | SURVIVES (PASS 378 passed, 1 skipped) | KILLED | test_m15_a_value_error_while_resolving_is_a_c |
| M20 | `len(name) > MAX_NAME_CHARS` -> `len(name) >= MAX_NAME_CHARS` | SURVIVES (PASS 378 passed, 1 skipped) | KILLED | test_m20_new_name_length_boundary_uses_the_co |

New file alone also fails on each of the 5 (same test names).

## Optional step 4: the 29 mutants Q8 already marked KILLED, against the new file alone
3 fail in the new file, 26 pass in the new file alone (they are killed by the original file; the new file targets only the survivors). Raw: /home/user/work/e4tmp/kill.txt

## git status
Worktree after each mutant: git diff --stat empty (checked after survivor and killed runs). The only change is the untracked patch file tests/test_path_confinement_lane3.py; I moved it out, and git status --short is then empty (0 lines).
