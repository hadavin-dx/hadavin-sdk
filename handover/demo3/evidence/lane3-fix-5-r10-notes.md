# B21 / lane3 fix-5, round 10 (security path, uncapped). Notes, 2026-11-14

Base: round 9 tree ce7113ea1552ecb5d111a4c2db8d2abd676130aa. Result tree: 8069ec3055cdbca0b50b4705de0b42239a493254 (git add -A, never committed).

## FAILED / UNCERTAIN / NOT DONE (first)
1. NOT DONE, row 5 second half (needs the lead): tests/test_path_confinement.py still holds Windows path forms (a drive-letter path, a network-share path, an extended path, a device path) at lines ~1026-1029, 1271, 1329-1333, 1352-1362, 1403. They are the INPUTS of the code under test (the confinement code that must refuse network and device paths on Windows); removing them deletes the test, and building them from parts (the way the ps1 test did in round 9) is the evasion the review named. My proposal: keep them, and add the file to the scan's allowed list with this reason. Next step: the lead decides (allowed list, or delete those cases). The other half of row 5 is done: reset_ps1 tests have no drive letter and no \Users path any more.
2. UNCERTAIN, never run here: reset.ps1 (no Windows). Every ps1 row is a text pin named test_text_only_*; a text pin proves the words are in the file, not that PowerShell behaves so. Windows-run lines for the lead are at the end.
3. UNCERTAIN, row 10: only bash 5.2.21 is installed here. Nothing was run on bash 4.4. The README now says so ("it was run only on bash 5.2, so bash 4.4 itself is untested") instead of claiming 4.4 works.
4. Round 9 mistakes confirmed by review and corrected now: (a) the 61 round-8 mutants were not re-run in round 9 (my stated reason was false); they are now (below). (b) My round 9 generator labelled three mutants (r9 M1, M2, M3) "equivalent". They are NOT equivalent: all three are KILLED (b21-r10-mutants-ALL.log); the labels were wrong and are removed from the names in this round's files. (c) One of my own new round-10 mutants ("config refusal back to a traceback", an inserted `true;`) is a no-op by construction (SURVIVED, equivalent); I replaced it by "handler removed" (KILLED).
5. FOUND BY THE MUTANTS this round, fixed: mutant "ps1 exit 5 forgets already stopped" SURVIVED (the pin only checked that the words exist somewhere in pass 2). The pin now checks that the note is built from what was stopped and that the "did not stop in time" line carries it; the mutant is KILLED on re-run.
6. Lead's two answers were followed (08:50Z and 09:15Z). Because the second changed wording, the full run was restarted once (my own run, killed by me, no result used).

## Rows (resolve-lane3-fix-5-r9.md)
| Row | Status | Where |
|---|---|---|
| 1 ps1 crash mapping, stale $LASTEXITCODE | FIXED (text pins; not run on Windows) | reset.ps1: `$LASTEXITCODE = $null` before the call; 0/3/4 pass through, anything else or no code at all = line "refused: the check program failed (exit N) ... nothing was deleted, not even the pid files" and exit 5. Pins: test_text_only_the_check_program_runs_with_continue_in_force..., test_text_only_the_check_exit_is_mapped_like_reset_sh... |
| 2 exit 5 two meanings | FIXED per lead (09:15Z text) | one README row, both causes named; headers of both scripts; test_text_only_the_readme_names_both_meanings_of_exit_5_and_the_script_says_the_same_in_its_header |
| 3 re-run all 61 round-8 mutants | DONE on the final scripts | below |
| 4 save diffs, generator, per-mutant results; name equivalents; byte-count isolation | DONE | raw/b21-r10-mutants-*.log (name, KILLED/SURVIVED, pytest last line, first failing test), raw/b21-r10-mutant-diffs-*.txt (one unified diff per mutant), raw/b21-r10-mutation-tools/ (generators mutate.py, mutate-r10.py, -r10b/c/d/e, r9 mut2.py). Equivalent real mutants: none found. The byte count is isolated by r9 M5/M10 (length rule alone, 64 -> 65), killed by test_reset_sh_counts_the_64_bytes_after_a_byte_order_mark |
| 5 rows 19 and 24 | 19 FIXED; 24 half done, see FAILED item 1 | all 80 cases of pure text pins are in 34 tests named test_text_only_* (an AST scan of the reset test files finds no unlabelled test that only reads script text) |
| 6 deterministic row-7 test | FIXED | test with a fake `ps` first on PATH that ends the process during the look; expects exit 0, no "another program", desk ended, pid file deleted; killed by r9 M7 |
| 7 zsh/ash guard | FIXED in code (not only the test) | reset.sh and start_all.sh: `[[ a == a && -n ${BASH_VERSINFO+x} ]]`; README says dash, busybox sh and zsh are refused (exit 2); tests: guard refuses a shell that runs [[ but has no BASH_VERSINFO (2 cases), text pin |
| 8 alive-as-nobody precondition | FIXED | setpriv --reuid=65534 ...; the precondition (kill -0 on process 1 is refused for that user) is asserted, skip only when setpriv cannot run |
| 9 widen AST bind guard | FIXED | tests/test_port_helpers.py `_ast_sites`: a (host, 0) pair inside any call, assigned, or returned; start_server/serve with port 0; 15 planted cases and 7 leave-alone cases (a `server_address` attribute or property binds nothing) |
| 10 bash 4.4 | REWORDED (see UNCERTAIN 3) | README line 47 |
| 11 pid-reuse window | IMPOSSIBLE NOW, named | comment in reset.sh: between the look and the kill the number could be reused; bash has no process handle (no pidfd), so it cannot be closed from bash; the second look in pass 2 narrows it |
| 12 setting refusal code | FIXED per lead: exit 8 | reset.sh and reset.ps1: bad RESET_STOP_WAIT_SECONDS, database outside data/, and a setting Config refuses (used to end with a traceback and exit 1) all give exit 8 with one line; exit 2 stays only for wrong shell or old bash; README rows 2 and 8; header text equals the lead's table text. Tests: test_reset_sh_gives_a_refused_desk_setting_exit_8..., stop-wait (12 cases) and database-outside now expect 8, text pin for ps1 (three exits, none 2). The table row itself lives in the fix-10 table, which is not in this tree: the lead adds the row "a setting is refused (start_all, run_real_check, reset)" |
| 13 python-missing wording | FIXED | exit code 127 from the check gives "refused: python was not found, so the check program could not run (exit 127) ..." and exit 5; test_reset_sh_says_python_was_not_found_when_the_check_program_cannot_start (the script's own exit stays 5) |
| 14 count wording | FIXED here | 34 text-pin tests (80 cases) in the reset and port tests; all named test_text_only_* |
| 15 end-to-end EPERM test | FIXED | test_reset_sh_refuses_with_exit_5_and_keeps_every_file_when_it_may_not_signal_the_desk (run as user 65534; desk still running, exit 5, files kept); killed by r9 M8 |
| 16 pass-2 pin structure | FIXED | the pin asserts the markers and the strings before indexing, instead of raising ValueError |
Also: I wrote a dash guard test in test_reset_order_and_words.py this round and dropped it again before any run, because tests/test_reset_scripts.py already holds the same case. No test of round 9 was deleted. The README exit list test now checks 2..8 with the 8 row's words.

## Failing before (raw/b21-r10-fails-before.log: round 9 scripts and README at ce7113ea, round 10 tests)
39 failed, 317 passed, 15 skipped = 15 tests failing (39 cases). Split: tests that RUN the script 5 (17 cases: exit 8 for a refused Config setting, python-not-found wording, guard without BASH_VERSINFO [2 cases], database outside data/ [exit 8], stop-wait [12 cases]); text pins 10 (22 cases: README exit list, README both meanings of exit 5, shell-guard text, ps1 exit 8, ps1 Continue + $LASTEXITCODE, ps1 exit mapping, three ps1 link tests, the short-name tests [13 cases + 1]). Regression tests that PASS on the old code (they guard behaviour round 9 already fixed and are not claimed as failing-before): the EPERM end-to-end test and alive-as-nobody (killed by mutant M8), the fake-ps pass-2 test (killed by M7), the AST bind-guard additions.

## Mutants (final scripts; raw/b21-r10-mutants-ALL.log)
First pass: 91 mutants = 61 round-8 + 10 round-9 + 20 new. 84 KILLED, 5 NOT APPLIED (the scripts' text had moved: pass-2 recheck, reset_check dropped, reset_check failure ignored, ps1 count after the mark, 64 -> 65 after the mark), 2 SURVIVED (see FAILED 4c and 5). Reruns: the 5 not applied were re-pointed at the current text and all 5 KILLED; the real survivor was KILLED after the pin was strengthened; the no-op was replaced and KILLED; r9 M1-M3 in their true two-edit form KILLED. After the 09:15Z wording change, 6 more mutants on the README and both headers (each loses one meaning or the "same meaning as" clause) KILLED (the three README/header mutants of the first pass were against the earlier wording and are superseded by these). Each run stopped at the first failing test (-x); the killing test is named per mutant. Survivors still open: none.

## Lint (clean `git ls-files` copy of the final tree)
raw/b21-r10-lint-*.log: ruff check rc=0, ruff format --check rc=0, bandit -ll rc=0, mypy linux rc=0 (28 files), mypy win32 rc=0. Narrow run on the 6 touched files at the final tree: 356 passed, 15 skipped (raw log in /home/user/work/b21-logs/r10-narrow2.log).

## Full run
See the end of this file (written after the run).

## Patch
lane3-fix-5-r10.patch (177,318 bytes), cumulative on base tree 79006fe3e7dcf6d72db72c343c3e468697915462 (claims series + r6); parts in lane3-fix-5-r10-parts/ (4 parts, 43 KB, 32 KB, 62 KB, 40 KB). Whole patch and the 4 parts in order, each applied on a temporary index, both give 8069ec3055cdbca0b50b4705de0b42239a493254. sha256 in raw/b21-r10-patch-sha256.txt. No test that existed at ce7113ea was deleted (the one test removed in round 9, row 14 of the r9 notes, was test_reset_sh_deletes_a_pid_file_that_is_not_a_number_whatever_its_size_in_bytes in tests/test_reset_scripts.py, 4 parametrized cases of a bytes-of-e-acute test that could not fail; its job is done by the digit-count table; I name it here because the r9 notes did not).

## Windows-run lines for the lead (reset.ps1 never ran here)
1. `$env:PATH` without python, then `powershell -File scripts/reset.ps1`: expect the line "refused: a desk setting was refused (or python was not found) ..." and exit 8.
2. With python present and a stand-in `python.cmd` that exits 1 for scripts\reset_check.py: expect "refused: the check program failed (exit 1) ..." and exit 5, pid files kept.
3. In the same session first run `cmd /c exit 9`, then the reset with the check stand-in printing nothing and ending without an exit code: expect exit 5 (the stale 9 must not be used).
4. `$env:DESK_PORT='abc'`, then the reset: exit 8. `$env:RESET_STOP_WAIT_SECONDS='08'`: exit 8.
5. Plain run with a running desk: exit 0 as before.
