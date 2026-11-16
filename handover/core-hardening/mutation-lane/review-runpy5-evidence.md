# run.py round 5 evidence (EVIDENCE RUNNER: records only, no judgement), 2026-11-16
Raw logs: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/ (out-final.txt, out-r4.txt, out-r4b.txt). Private copy of the lane folder: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/copy. Nothing in the repo was edited except this file.

## Failures and gaps first
1. Step 3 does NOT reproduce the builder's 41 FAILED: two runs of the r4 code gave 73 FAILED of 276 (203 PASS), same 73 names both times (run A: run-r4.py left in raw/.codecopies inside my private copy; run B: run-r4.py copied to a folder named run.py inside scratch).
   Observation only: in both runs the r4 code printed 'REFUSED: git rev-parse failed for --repo <folder of run.py> (rc 128): not a git repository' 18 times (e.g. T5 --restore). My copies live outside any git work tree. The builder's r4 copy lived under /home/user/hadavin-sdk (inside a git work tree), where that refusal may not happen. This is a hypothesis; I did NOT verify it: my attempt to run the r4 file in place (inside the repo) was blocked by the permission system, and I did not work around it.
2. ruff check: 2 findings (S603 at run.py:419 and run.py:1115) when run from the repo folder with the repo's pyproject (ruff 0.16.9 installed; pyproject pins ruff==0.17.1, so the version differs). Run in my scratch copy with no config (default line length 88): I001 import-order finding and format --check reports 'would be reformatted'; that is the missing project config (line-length 100), not a real result.
3. Not run: T35 in step 3 (SKIP_T35=1 as instructed); real mutants, real repo test suite, bandit, non-Linux, non-root.

## (1) sha256 check (raw/run-py-r5-final-sha256.txt, run with sha256sum -c in the lane folder)
11 lines checked: run.py OK, safety-tests.sh OK, MUTANTS-V2-PLAN.md OK, raw/.codecopies/run-r4.py OK, safety-tests-r4.sh OK, run-r3.py OK, run-r4-mut-envleak/memberstart/startcheck/unreaped/worksin.py OK. Mismatches: 0. run.py sha256 starts 16d3ed1adb19.

## (2) safety-tests.sh vs final run.py (private copy, SCRATCH under scratchpad, VENV=/home/user/hadavin-sdk/.venv with pytest 9.1.1)
Result line: 'FAILED CHECKS: 0 (of 279 checks run; skipped: none)'. PASS lines: 279, FAIL lines: 0. Script exit rc=0.
Extra output: one bash line 'Killed' for the background test run (expected from the kill tests). T35 ran (it writes to the shared tmp folder; no /tmp/hadavin-mutation-lane-* folder exists afterwards).
Tail (truncated):
parsed: ['/a/root/with space/m', '/a/root/back\\slash']
  PASS: T62b refuse_mounts logic: a mount inside is refused; the root, .venv and a sibling prefix are not
== T61 (review r4 evidence) PYTEST_ADDOPTS, PYTEST_PLUGINS and other steering variables of the caller never reach the tests
  PASS: T61 with those set in the caller's environment the tests run and see none of them (rc 0, verdict SURVIVED, '1 passed')
FAILED CHECKS: 0 (of 279 checks run; skipped: none)
rc=0

## (3) safety-tests.sh with SKIP_T35=1 vs raw/.codecopies/run-r4.py (r4 code)
Run A and run B both: 'FAILED CHECKS: 73 (of 276 checks run; skipped: T35)'; 203 PASS. Builder claim: 41 FAILED, 235 PASS. NOT CONFIRMED (see failure 1).
Failures per check group (count of FAIL lines): T10 x2, T11 x1, T15 x2, T23 x1, T38 x3, T43a x1, T43b x1, T43c x1, T44 x2, T45 x2, T46 x1, T46b x1, T47a x1, T47b x9, T48 x5, T48a x1, T49 x3, T5 x2, T51a x2, T51b x3, T51c x1, T52a x1, T52b x1, T53 x1, T54 x1, T55a x1, T55b x2, T56 x1, T57a x1, T57b x1, T58a x1, T58b x1, T58c x1, T58d x1, T59 x1, T6 x3, T60 x1, T62 x1, T62b x1, T7 x3, T8 x2, T9 x2, 
Run A and run B list identical group counts.
Full list of the 73 FAIL lines (truncated to 170 characters):
```
  FAIL: T5 file restored
  FAIL: T5 state folder empty
  FAIL: T6 exit 143
  FAIL: T6 file restored
  FAIL: T6 state empty
  FAIL: T7 exit 130
  FAIL: T7 file restored
  FAIL: T7 state empty
  FAIL: T8 first run still alive
  FAIL: T8 file restored after
  FAIL: T9 exit 0
  FAIL: T9 state empty
  FAIL: T10 file unchanged
  FAIL: T10 state empty
  FAIL: T11 file unchanged
  FAIL: T15 orphan stopped
  FAIL: T15 file restored
  FAIL: T23 genuine restore still works
  FAIL: T38 exit 0 and the file is back with the original text (rc 2)
  FAIL: T38 mode 640 restored
  FAIL: T38 state empty
  FAIL: T43a restore exit 0 and the file is back (rc 2)
  FAIL: T43b a marker with a group but no recorded identity: file restored (rc 2) and the group found by the recorded command (review r4 nit 7: fallback)
  FAIL: T43c a marker with a group and NO identity and NO command at all: file restored (rc 2), nothing stopped on a guess
  FAIL: T44 restore exit 0, file back (rc 2)
  FAIL: T44 the surviving member was stopped
  FAIL: T45 restore exit 0, file back (rc 2)
  FAIL: T45 the orphan was stopped
  FAIL: T46 SIG.allow was already False when the timeout branch called stop_group, and the result is TIMEOUT (no traceback)
  FAIL: T46b through run.py itself (stop_group failing, timeout 3 s): exit 0 (got 1), raw file says VERDICT: TIMEOUT, file restored, state empty
  FAIL: T47a all handled signals in the plant window and the restore window: exit 128+N, file restored, state empty
  FAIL: T47b TRAP exit 133 (got 133), file restored, state empty, no orphan
  FAIL: T47b RTMIN exit 162 (got 162), file restored, state empty, no orphan
  FAIL: T47b RTMAX exit 192 (got 192), file restored, state empty, no orphan
  FAIL: T47b SYS exit 159 (got 159), file restored, state empty, no orphan
  FAIL: T47b 16 exit 144 (got 144), file restored, state empty, no orphan
  FAIL: T47b SEGV exit 139 (got 139), file restored, state empty, no orphan
  FAIL: T47b BUS exit 135 (got 135), file restored, state empty, no orphan
  FAIL: T47b FPE exit 136 (got 136), file restored, state empty, no orphan
  FAIL: T47b ILL exit 132 (got 132), file restored, state empty, no orphan
  FAIL: T48a the command carries --rootdir and --confcutdir (both = root)
  FAIL: T48 setup.py above the root refused (rc 0, hits 0)
  FAIL: T48 conftest.py above the root refused (rc 0, hits 0)
  FAIL: T48 pyproject.toml WITHOUT a pytest section above the root refused (rc 0, hits 0)
  FAIL: T48 pyproject.toml with a dotted-key pytest setting above the root refused (rc 0, hits 0)
  FAIL: T48 pyproject.toml is parsed: dotted keys, inline tables, native table found; no section and look-alike table not; invalid TOML counted (fail closed)
  FAIL: T49 test_writeconf.py: exit 4 (got 4), the loop stopped after m1 (no X-m2.txt), m1's raw file records the changed file
  FAIL: T49 test_writedata.py: exit 4 (got 4), the loop stopped after m1 (no X-m2.txt), m1's raw file records the changed file
  FAIL: T49 a clean two-mutant run: exit 0 (got 0), both raw files record 'differing files (0; 0 = clean): []' and a digest
  FAIL: T51a identical command line, other start time: stranger left alone, file restored (rc 2)
  FAIL: T51a (control) identical command line AND identical start time: stopped (rc 2)
  FAIL: T51b outside-root: member left alone, file restored (rc 2)
  FAIL: T51b early-start: member left alone, file restored (rc 2)
  FAIL: T51b control (member works in root, started after the recorded start): stopped (rc 2)
  FAIL: T51c works_in matches whole path parts: /root2/x is not inside /root
  FAIL: T52a read-only target: exit 2 (got 3) with 'cannot plant', no 'RESTORE FAILED', file unchanged, state empty
  FAIL: T52b file already equals the backup (two names): --restore exit 0 (got 2), marker and backup cleared, nothing written
  FAIL: T53 and the genuine restore works afterwards
  FAIL: T54 hard-linked docs/note.txt refused naming the file (rc 0, hits 0); target untouched
  FAIL: T55a leftover 'sleep 3141' stopped (rc 0), the raw file says so
  FAIL: T55b the next run refuses and points at --restore (rc 0)
  FAIL: T55b --restore exit 0 (got 2), the orphaned control test group stopped, state empty, file unchanged
  FAIL: T56 non-Linux: exit 2 (got 2) with 'Linux only'
  FAIL: T57a the printed command contains --repo EV/s2/toy/repo
  FAIL: T57b --restore from a copy of the script in a folder that is no git repository: exit 0 (got 2), file back
  FAIL: T58a --raw file is a link: exit 2 (got 0), the victim is untouched, nothing planted
  FAIL: T58b --out-json is a link: exit 2 (got 0), victim untouched, nothing planted
  FAIL: T58c --raw is a symbolic link to a folder: exit 2 (got 0), nothing written into it
  FAIL: T58d reap kills AND waits: no zombie, returncode set
  FAIL: T59 mode 640 after a restore under umask 077 (got )
  FAIL: T60 the file behind the swapped link was not written
  FAIL: T62 mount point docs/ refused for that reason (rc 0)
  FAIL: T62b refuse_mounts logic: a mount inside is refused; the root, .venv and a sibling prefix are not
```

## (4) ruff
```
S603 `subprocess` call: check for execution of untrusted input
   --> run.py:419:12
    |
417 | ) -> subprocess.CompletedProcess:
418 |     """The one place that starts a helper program (git, patch, the import probe): fixed argument list, no shell."""
419 |     return subprocess.run(
    |            ^^^^^^^^^^^^^^
420 |         argv, input=input_bytes, capture_output=True, check=False, cwd=cwd, env=env, timeout=timeout
421 |     )
    |

S603 `subprocess` call: check for execution of untrusted input
    --> run.py:1115:16
     |
1113 |     try:
1114 |         # one process group, so a timeout or a signal can stop all of it
1115 |         proc = subprocess.Popen(
     |                ^^^^^^^^^^^^^^^^
1116 |             cmd,
1117 |             cwd=root,
     |

Found 2 errors.
rc=1
1 file already formatted
rc=0
ruff 0.16.9
```
Scratch copy without project config (for the record): ruff check rc=1 (I001 only, import block at run.py:103), ruff format --check rc=1 (many 88-column rewrites); both caused by the missing line-length = 100 setting.

## (5) leftovers
- Processes: none left (pgrep for safety-tests, run.py, run-r4, sleepbin, pytest returned nothing).
- Mounts: none created (the only 'ev/' matches were /dev entries).
- State folders (all under my scratch, private): /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/s1..s4 hold tmpstate with a lock file each and 83 mutation-ref-* temporary folders; s4 is empty of results (run blocked). No planted mutant left in the repo; run.py sha256 unchanged after the runs (16d3ed1adb19).
- No /tmp/hadavin-mutation-lane-* folder exists. Repo: only this file was written.
