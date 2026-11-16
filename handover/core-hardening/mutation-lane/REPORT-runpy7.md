# REPORT run.py round 6 (file name runpy7) - fix of review-runpy5-security.md

Not reviewed. The lead runs the EGM result review (I could not invoke EGM skills from here). No bible access here: no R-numbers cited.
Files: run.py sha256 b095825c...2892c, safety-tests.sh sha256 4d74116c...dce1 (full list: raw/run-py-r6-final-sha256.txt).

## Failures and gaps first
1. The ONE full run (raw/run-py-safety-tests-r6-final.txt) shows `FAILED CHECKS: 1 (of 317)`: T47a. Cause: a bug in MY new test hook (it wrapped restore_target twice, RecursionError), not in run.py. I fixed the hook and re-ran T47a alone on run.py r6 and on the r5 copy: both PASS (102 cases, 0 bad; raw/run-py-r6-T47a-rerun-*.txt). The full script was NOT re-run after that fix (brief said once). So 316 of 317 checks passed in the full run; the 317th passes in the isolated rerun only.
2. A bug in my own new run.py code was found by the new test T63c: `restore_target` built a file object before checking the file is regular, so a FIFO raised io.UnsupportedOperation instead of a refusal. Fixed (fstat first). The prelim log raw/run-py-r6-newtests-on-r6code-prelim.txt predates that fix and shows T63c failing; the final full run has it passing.
3. S603 (2 sites, subprocess call) remains reported by ruff check. Per lead answer Q29: no suppression, no noqa, run.py stays out of every pull request (tool only). `ruff format --check` clean.
4. Real memory faults (SEGV/BUS/FPE/ILL) with a Python handler still spin forever (measured, T64a passes on r5 too, since behaviour is unchanged). Not fixable inside Python (the GIL is held, a watchdog thread cannot run). Docs corrected. Trade-off for the lead: keep restore-on-sent-signal (current) vs die-on-fault (no restore). Needs the lead's decision.
5. Not run: Python 3.11.4 minimum was tested only by simulation (T73: fake version and no tomllib), no real old interpreter. EGM steps, independent evidence runner, review of this round. The pytest used is 9.2.0 in a private venv; toy repo only, never the real code.

## Per finding
| id | fixed | test | fails-on-r5 proved |
|---|---|---|---|
| M1 failing/all-skipped baseline hides | yes: mutants refused (exit 2) unless baseline exit 0 and a test passed; NO-TEST-PASSED verdict; flag when failing set equals baseline | T66a-f | yes: T66a,b,c,d,e,f FAIL on r5 (raw/run-py-r6-newtests-on-r5code.txt) |
| M2 exit 0 despite COULD-NOT-PLANT/TIMEOUT/ERROR | yes: exit 5 INCOMPLETE, SUMMARY line and <prefix>-summary.txt, docstring and exit table updated; exit 4 wins | T67a-g, T46b changed to expect 5 | yes: T67a-e FAIL on r5; T67f,g are guards and pass on both |
| M3 restore compared by path (decoy) | yes: restore_target compares, writes, verifies on one fd opened with dir_fd+O_NOFOLLOW; marker kept on mismatch (exit 3) | T63a,b (decoy with original bytes, both --restore and the run's own restore), T63c (unit cases incl. swap during write, FIFO, read-only, two names, re-creation) | yes: T63a,b,c FAIL on r5 |
| N1 real SEGV spin, wrong comment | text fixed (no longer "acts like SIGKILL"); behaviour measured, unchanged | T64a (measures the hang), T64b | T64b fails on r5; T64a passes on r5 by design (behaviour same). Behaviour question open, see 4 |
| N2 SIG.allow window on non-signal exception | yes: nested try/finally sets allow=False, critical=True on any exit | T65 (planted and control variants, signal injected at first cleanup line) | yes: both FAIL on r5 |
| N3 --restore no marker says "nothing to restore" | yes: says CANNOT TELL, exit 0 | T68 | yes: FAIL on r5 |
| N4 restore_control traceback / marker removed with orphan alive | yes: bad JSON is Refused (exit 2); marker kept unless settled (exit 3) | T69a,b (c guard) | yes: T69a,b FAIL on r5; T69c passes on both (guard) |
| N5 import check per mutant | yes: re-run before each mutant, COULD-NOT-PLANT on change | T70 | yes: FAIL on r5 |
| N6 contamination before first mutant | yes: stop_if_dirty exit 4 after import check and control run | T71a,b | yes: FAIL on r5 (r5 also exits 4 but only after planting m1; test requires no m1 file) |
| N7 reserved ids baseline/tree-diff/summary | yes: refused exit 2 | T72 x3 | yes: FAIL on r5 |
| N8 Python >= 3.11.4, tomllib | yes: version checked first, exit 2 with message | T73 (simulated) | yes: FAIL on r5 (traceback, exit 1) |
| N9 --sha pin | yes: rev-parse --verify sha^{commit}, full id recorded | T74a,b (c guard) | yes: T74a,b FAIL on r5; T74c passes both |
| header T1-T66 vs T62 | header now T1-T75 | n/a | n/a |
| git/patch env=None | yes: clean env (PATH, HOME, LC_ALL=C) | T75 | yes: FAILS on r5 (exit 2 with bogus GIT_DIR) |
| inherited output pipe gives TIMEOUT | unchanged, safe side (stated only) | none | n/a |

Tests that cannot fail on r5 and were not proved with a mutant: T64a, T67f, T67g, T69c, T74c (guards or behaviour-unchanged); T66e/T67e fail on r5 only because the summary text is new.

## Evidence
- Full run on final run.py: raw/run-py-safety-tests-r6-final.txt (317 checks, 1 FAILED = T47a, see 1).
- r5 test script on r6 code (prelim): only T46b and T47a failed, both expected (exit-code change, restore hook); both updated.
- New tests on r5 code: raw/run-py-r6-newtests-on-r5code.txt: 33 of 38 fail, the 5 passing are the guards above.
- Checks: py_compile ok, bash -n ok, ruff format clean, ruff check only 2 x S603.
- Backups: raw/.codecopies/run-r5.py, safety-tests-r5.sh (before), run-r6.py, safety-tests-r6.sh (after).
- Processes: all started runs finished; no process left running (pgrep empty).
