# Lane 3 fix 3 (B3): tests that kill Q8 survivors in tools/pathconfine.py
Base f3c39cf8. Patch: evidence/lane3-fix-3.patch (one new file tests/test_path_confinement_lane3.py, 82 lines, tests only). SHA256 9084e0d849c9b59efa38fe0a357522df0b854aaf5418a882da0231276e0c6073.
Q8 results re-read at 32 lines: survivors are still only M03, M08, M11, M15, M20 (Q8 may still be running).

| Mutant | Verdict | Why | New test | Fails on mutant? first failure line |
|---|---|---|---|---|
| M03 (pathconfine.py:211) | real gap | a str subclass could answer strip() etc. differently; the exact-str copy is the only guard | test_m03_a_str_subclass_cannot_change_the_answer | yes: PathRefused: f: empty path |
| M08 (:216) | real gap | boundary: exactly MAX_PATH_CHARS must be accepted | test_m08_path_length_boundary_uses_the_constant (MAX-1, MAX, MAX+1) | yes: PathRefused: f: path too long |
| M11 (:126) | real gap, security-relevant | ValueError in commonpath must mean "not inside" | test_m11_inside_answers_not_inside_when_commonpath_raises (direct, relative vs absolute); test_m11_public_functions_refuse_when_the_containment_check_raises (commonpath patched to raise; confine and confine_existing refuse) | yes: assert True is False |
| M15 (:224) | real gap | ValueError from realpath must become PathRefused | test_m15_..._clean_refusal x3 (confine, confine_existing, confine_anywhere; realpath patched to raise ValueError for the argument only) | yes: ValueError: embedded null byte |
| M20 (:132) | real gap | boundary: name of MAX_NAME_CHARS accepted | test_m20_new_name_length_boundary_uses_the_constant (MAX-1, MAX, MAX+1) | yes: PathRefused: f: not usable as the name of a new file |

No equivalent mutants among these five. Limits: M11 and M15 inputs are produced by patching os.path functions (on Linux a real input cannot reach ValueError: NUL and mixed paths are refused earlier or made absolute); the direct _inside call is a real input.

## RUNG TABLE
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| 6 tests in lane3 file | kill 5 mutants | 1 reuse existing tests: they pass with the mutants | Q8 results.jsonl | boundary and error-class checks of our own helper | custom test code, rung 7 |

## Evidence (commands run in /home/user/work/b3-base, Python 3.12 final-venv, TMPDIR private)
- new file on unmutated tree: 8 passed. ruff check and ruff format --check: clean.
- each mutant applied alone, restored with git checkout: first failure lines above (1 to 2 failures each; M15 3 params).
- tests/test_path_confinement.py + new file, unmutated: 386 passed, 1 skipped.
- git apply --check: on fresh f3c39cf8 worktree OK; on f3c39cf8 + claims-stack-on-f3c39cf8.patch OK.
Not covered: mutants Q8 adds after 32 lines; Windows behaviour.
