# Evidence runpy5 (independent). EVIDENCE RUNNER: raw output, no judgement. Date 2026-11-16

## Setup and slips (read first)
- Scratch copies under /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev (ml = run.py r4 + script, git-initialised copy; ml3 = raw/.codecopies/run-r3.py as run.py + the current safety-tests.sh, git-initialised). VENV = /home/user/hadavin-sdk/.venv (only symlinked, pytest 9.1.1). Real tree untouched (sha256 of run.py and safety-tests.sh re-checked after the runs: unchanged).
- My first r4 attempt (log kept at /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/r4-attempt1-nogit.log) gave 190 PASS / 30 FAIL because my scratch copy was not inside a git repository and run.py defaults --repo to its own folder (REFUSED: git rev-parse failed). That was my setup error, not a run.py result. I git-init'ed the copy and re-ran; the numbers below are from the re-run. A stale toy marker that attempt left in /tmp/hadavin-mutation-lane-0 was removed by me (it was mine, created during my run).
- r3 run and r4 run ran one after the other (T35 writes the shared /tmp folder). Hostile inputs ran while r3 was running (own scratch, own TMPDIR).
- NOT run: mutation runs on real code, the repo pytest suite, bandit, the real repo tree, uv-based gates, a Windows run, the r1/r2 code copies.

## 1. sha256sum -c raw/run-py-r4-final-sha256.txt (run from the mutation-lane folder)
```
run.py: OK
safety-tests.sh: OK
MUTANTS-V2-PLAN.md: OK
raw/.codecopies/run.py: OK
raw/.codecopies/run-r1.py: OK
raw/.codecopies/run-r3.py: OK
raw/.codecopies/safety-tests-r3.sh: OK
rc=0
(Run from raw/ instead, the paths in the file are relative to mutation-lane, so all 7 fail to open: my first try, same file, wrong cwd.)
```

## 2. bash -n safety-tests.sh
```
rc=0
```

## 3. ruff 0.16.9 on run.py (scratch copy)
```
$ ruff check --no-cache --config <repo pyproject.toml> --output-format concise run.py
run.py:291:12: S603 `subprocess` call: check for execution of untrusted input
run.py:827:16: S603 `subprocess` call: check for execution of untrusted input
Found 2 errors.
rc=1
$ ruff format --check --no-cache --config <repo pyproject.toml> run.py
1 file already formatted
rc=0
$ ruff format --check --no-cache run.py   (NO repo config: default line length 88, scratch has no pyproject; for information only)
1 file would be reformatted
rc=1
$ ruff check --no-cache run.py   (NO repo config)
All checks passed!
```

## 4. safety-tests.sh against run.py round 4: totals
```
PASS lines: 220
FAIL lines: 0
FAILED CHECKS: 0 (of 220 checks run; skipped: none)
rc=0
```

## 5. same script against round 3 code (raw/.codecopies/run-r3.py): totals
```
PASS lines: 147
FAIL lines: 73
FAILED CHECKS: 73 (of 220 checks run; skipped: none)
rc=0
--- FAIL lines
  FAIL: T25 -p no:runner (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:skipping (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:python (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:terminal (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:mark (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:assertion (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:capture (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:fixtures (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:logging (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:main (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:warnings (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:debugging (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:setuponly (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:setupplan (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:unittest (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:faulthandler (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:doctest (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:monkeypatch (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:recwarn (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:stepwise (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:junitxml (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:pastebin (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -pno:runner (attached form) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:RANDOMLY (plugin names are exact) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:randomly.runner refused by the argument check (rc 2, hits 0)
  FAIL: T36a target hard-linked to a real repository file: refused for that reason (rc 0, hits 0)
  FAIL: T36a the real repository file was not even touched (content and modification time)
  FAIL: T36b tree built with cp -al: refused (rc 0, hits 0)
  FAIL: T36b the linked original was not touched
  FAIL: T36c write_target itself refuses a two-name file before truncating it, and still writes a one-name file
  FAIL: T37a pytest.ini above the root refused (rc 0, hits 0)
  FAIL: T37b pyproject.toml with a pytest section above the root refused (rc 0, hits 0)
  FAIL: T38 exit 0 and the file is back with the original text (rc 2)
  FAIL: T38 mode 640 restored
  FAIL: T38 state empty
  FAIL: T39 restore finished although stop_group raised PermissionError (rc 1)
  FAIL: T39 the report says the orphan was not stopped
  FAIL: T40 no signal was sent to the reaped leader's number
  FAIL: T41 no orphan pytest left
  FAIL: T42 QUIT file restored
  FAIL: T42 QUIT state empty
  FAIL: T42 QUIT no orphan pytest
  FAIL: T42 ABRT file restored
  FAIL: T42 ABRT state empty
  FAIL: T42 ABRT no orphan pytest
  FAIL: T42 USR1 file restored
  FAIL: T42 USR1 state empty
  FAIL: T42 USR1 no orphan pytest
  FAIL: T42 USR2 file restored
  FAIL: T42 USR2 state empty
  FAIL: T42 USR2 no orphan pytest
  FAIL: T42 ALRM file restored
  FAIL: T42 ALRM state empty
  FAIL: T42 ALRM no orphan pytest
  FAIL: T42 XCPU file restored
  FAIL: T42 XCPU state empty
  FAIL: T42 XCPU no orphan pytest
  FAIL: T42 VTALRM file restored
  FAIL: T42 VTALRM state empty
  FAIL: T42 VTALRM no orphan pytest
  FAIL: T42 PROF file restored
  FAIL: T42 PROF state empty
  FAIL: T42 PROF no orphan pytest
  FAIL: T42 IO file restored
  FAIL: T42 IO state empty
  FAIL: T42 IO no orphan pytest
  FAIL: T42 PWR file restored
  FAIL: T42 PWR state empty
  FAIL: T42 PWR no orphan pytest
  FAIL: T43a the stranger was left alone
  FAIL: T43b a marker with a group but no recorded identity: file restored (rc 0), group not stopped on a guess
  FAIL: T44 the surviving member was stopped
  FAIL: T45 the orphan was stopped
```

## 6. Five hostile inputs (own toy repo; run.py r4; rc printed as RC=)
```
##### H0 control (plain run, expect KILLED rc 0)
m1 KILLED tests/test_fast.py::test_f
tree diff: 0 difference(s)
RC=0
  file now:     return 1
##### H1 -p no:runner
REFUSED: TESTS argument '-p no:runner' may only switch off one of the plugins ['cacheprovider', 'cov', 'randomly', 'xdist'] (no:NAME): refused (allowed: -k EXPR, -m EXPR, -q, -x, -p no:NAME with NAME one of ['cacheprovider', 'cov', 'randomly', 'xdist'], and paths inside --root)
RC=2
  file now:     return 1
##### H2 -pno:runner
REFUSED: TESTS argument '-pno:runner' may only switch off one of the plugins ['cacheprovider', 'cov', 'randomly', 'xdist'] (no:NAME): refused (allowed: -k EXPR, -m EXPR, -q, -x, -p no:NAME with NAME one of ['cacheprovider', 'cov', 'randomly', 'xdist'], and paths inside --root)
RC=2
  file now:     return 1
##### H3 hard-linked target
REFUSED: mutant m1 target /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/host/root/src/mod.py is not a regular file with exactly one name (links: 2): a hard-linked scratch tree would plant the mutant in the file it is linked to: refused
RC=2
  file now:     return 1
  hardlink copy:     return 1 ; root file:     return 1
##### H4 PYTEST_ADDOPTS=--collect-only
m1 KILLED tests/test_fast.py::test_f
tree diff: 0 difference(s)
RC=0
  file now:     return 1
##### H5 conftest.py with os._exit(0) in scratch root
REFUSED: scratch tree differs from git archive 2decd2bd8fc7196018000482a9f00ac63c0cd3e7 + patches in 1 file(s), first: ['conftest.py']: it may hold a planted change; rebuild it from the archive
RC=2
  file now:     return 1
##### H5b same, conftest in tests/
REFUSED: scratch tree differs from git archive 2decd2bd8fc7196018000482a9f00ac63c0cd3e7 + patches in 1 file(s), first: ['tests/conftest.py']: it may hold a planted change; rebuild it from the archive
RC=2
  file now:     return 1
```
Script used: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/hostile.sh

## 7. Leftover processes after all runs
```
pgrep matches: 0
ls: cannot access '/tmp/hadavin-mutation-lane-0': No such file or directory
```

## 8. Full logs
### r4 full log
```
== T1 the real repository as --root is refused (exit 2)
REFUSED: --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/repo is, contains or lies inside the real repository /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-961
  exit code 2
  PASS: T1 exit 2
== T2 SIGKILL while a mutant is planted
  file now: return2
safety-tests.sh: line 41:  6227 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T2 file stays planted
== T3 the next run refuses and says how to restore
REFUSED: a mutant (X-m1) is still planted in src/mod.py from an earlier run that was killed. Restore with: python3 /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9
  exit code 2
  PASS: T3 exit 2
== T4 marker lost: the tree check against a fresh git archive still refuses
REFUSED: scratch tree differs from git archive 3df9c9ae54937fb004126570b4c69d4b1e805bd7 + patches in 1 file(s), first: ['src/mod.py']: it may hold a planted cha
  exit code 2
  PASS: T4 exit 2
== T5 --restore puts the saved original back
test group already gone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matches saved original: True
  PASS: T5 file restored
  PASS: T5 state folder empty
== T6 SIGTERM during a run restores the file and removes the marker
  exit code 143
  PASS: T6 exit 143
  PASS: T6 file restored
  PASS: T6 state empty
== T7 SIGINT likewise, exit code read directly from $?
  exit code 130
  PASS: T7 exit 130
  PASS: T7 file restored
  PASS: T7 state empty
== T8 two runs at once: the second is refused by the lock, and the first is still alive
REFUSED: another run holds the lock for /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/
  second run exit code 2
  PASS: T8 second refused (2)
  PASS: T8 first run still alive
  PASS: T8 file still planted by the first
  PASS: T8 file restored after
== T9 a clean run to the end: KILLED, backup gone, tree diff clean, exit 0
m1 KILLED tests/test_fast.py::test_f
tree diff: 0 difference(s)
  exit code 0
  PASS: T9 exit 0
  PASS: T9 state empty
differing files (0; 0 = clean): []
== T10 absolute path as the mutant file is refused (exit 2), nothing planted
REFUSED: mutant m1 file: must be relative to the root and contain no '..': '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/root/src/mod.py'
  exit code 2
  PASS: T10 exit 2
  PASS: T10 file unchanged
  PASS: T10 state empty
== T11 '..' in the mutant file is refused (exit 2)
REFUSED: mutant m1 file: must be relative to the root and contain no '..': '../root/src/mod.py'
  exit code 2
  PASS: T11 exit 2
  PASS: T11 file unchanged
== T12 symlinked folders inside the scratch root
REFUSED: scratch tree differs from git archive 3df9c9ae54937fb004126570b4c69d4b1e805bd7 + patches in 1 file(s), first: ['evil/']: it may hold a planted change; rebuild it from the archive
  (extra symlinked folder 'evil') exit code 2
  PASS: T12b exit 2
  PASS: T12b real repo file unchanged
REFUSED: scratch tree differs from git archive 3df9c9ae54937fb004126570b4c69d4b1e805bd7 + patches in 2 file(s), first: ['src/', 'src/mod.py']: it may hold a planted change; rebuild it from the archive
  (src itself is a link to the real repo) exit code 2
  PASS: T12a exit 2
  PASS: T12a real repo file unchanged
== T13 git cannot tell (rev-parse fails): fail closed
REFUSED: git cannot tell whether --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/root is a work tree (rc 128): fatal: detected dubious ownership in repositor
  (work-tree check fails) exit code 2
  PASS: T13a exit 2
REFUSED: git rev-parse failed for --repo /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/repo (rc 128): fatal: detected dubious ownership in repository
  (show-toplevel fails) exit code 2
  PASS: T13b exit 2
== T14 a leftover file after the loop gives a non-zero exit; a declared --extra does not
  undeclared leftover: exit code 4
  PASS: T14a exit 4
  declared --extra: exit code 0
  PASS: T14b exit 0
== T15 SIGKILL of run.py leaves the test group alive; --restore stops it and restores
safety-tests.sh: line 79:  6840 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T15 orphan pytest alive
stopped orphaned test group 6849; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matches saved original: True
  PASS: T15 orphan stopped
  PASS: T15 file restored
== T16 SIGHUP restores too (exit 129)
  exit code 129
  PASS: T16 exit 129
  PASS: T16 file restored
== T17 --restore while a run is live is refused (lock)
REFUSED: another run holds the lock for /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/
  exit code 2
  PASS: T17 exit 2
  PASS: T17 run still planted
== T18 a mutant id that climbs out of --raw is refused
REFUSED: mutant id is not a plain unique name: '../escape'
  exit code 2
  PASS: T18 exit 2
  PASS: T18 no file outside raw
== T19 an error while the tests start (no .venv python) still removes the marker
REFUSED: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/root/.venv/bin/python does not exist: the scratch root needs its ow
  exit code 2
  PASS: T19 exit 2
  PASS: T19 file unchanged
  PASS: T19 state empty
== T20 four signals in a row while a mutant is planted (5 times): file restored, marker gone, exit 129/130/143
  (probabilistic: it cannot force the second signal into the exact window; see T21 for the deterministic part)
  PASS: T20.1 exit 129/130/143 (got 129)
  PASS: T20.1 file restored
  PASS: T20.1 state empty
  PASS: T20.2 exit 129/130/143 (got 129)
  PASS: T20.2 file restored
  PASS: T20.2 state empty
  PASS: T20.3 exit 129/130/143 (got 129)
  PASS: T20.3 file restored
  PASS: T20.3 state empty
  PASS: T20.4 exit 129/130/143 (got 129)
  PASS: T20.4 file restored
  PASS: T20.4 state empty
  PASS: T20.5 exit 129/130/143 (got 129)
  PASS: T20.5 file restored
  PASS: T20.5 state empty
== T21 signal handler logic (deterministic): a signal while planted is only remembered, then delivered once
handler logic ok
  PASS: T21 handler logic
== T22 state folder checks: wrong mode, a link, another owner are refused (exit 2)
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22a mode 755 refused (got 2)
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22b symlinked state folder refused (got 2)
  PASS: T22b nothing written through the link
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22c other owner refused (got 2)
== T23 forged state: a backup whose hash differs, a marker that is a link, --restore inside the real repository: all refused, nothing written
safety-tests.sh: line 371:  8956 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
REFUSED: the saved backup does not match the hash recorded in the marker: refused
  PASS: T23a hash mismatch refused (got 2)
  PASS: T23a file not written
REFUSED: state file /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.
  PASS: T23b marker as a link refused (got 2)
  PASS: T23b file not written
test group already gone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matches saved original: True
  PASS: T23 genuine restore still works
REFUSED: --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/repo is, contains or lies inside the real reposito
  PASS: T23c --restore in the real repository refused for that reason (got 2, reason hits 1)
== T24 import check: the tests would load the target from another tree (exit 2); the right tree passes and is recorded
REFUSED: import check: `import mod` loads '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/repo/src/mod.py', not /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpa
  PASS: T24a refused (got 2)
  PASS: T24a file unchanged
  PASS: T24b recorded in the raw file
  PASS: T24b raw file lists 4 environment names
== T25 TESTS is an allowlist: every bypass named in review r2 is refused by the argument check (exit 2, message 'TESTS argument'), one check each
  PASS: T25 @argsfile refused by the argument check (rc 2, hits 1)
  PASS: T25 -k @argsfile refused by the argument check (rc 2, hits 1)
  PASS: T25 -qc (clustered c) refused by the argument check (rc 2, hits 1)
  PASS: T25 -qo (clustered o) refused by the argument check (rc 2, hits 1)
  PASS: T25 -qp (clustered p) refused by the argument check (rc 2, hits 1)
  PASS: T25 -c refused by the argument check (rc 2, hits 1)
  PASS: T25 -cfoo.ini refused by the argument check (rc 2, hits 1)
  PASS: T25 -oaddopts=-x refused by the argument check (rc 2, hits 1)
  PASS: T25 --collect-only refused by the argument check (rc 2, hits 1)
  PASS: T25 --co refused by the argument check (rc 2, hits 1)
  PASS: T25 --setup-plan refused by the argument check (rc 2, hits 1)
  PASS: T25 --setup-only refused by the argument check (rc 2, hits 1)
  PASS: T25 --help refused by the argument check (rc 2, hits 1)
  PASS: T25 -h refused by the argument check (rc 2, hits 1)
  PASS: T25 --version refused by the argument check (rc 2, hits 1)
  PASS: T25 -V refused by the argument check (rc 2, hits 1)
  PASS: T25 --noconftest refused by the argument check (rc 2, hits 1)
  PASS: T25 --ignore=tests refused by the argument check (rc 2, hits 1)
  PASS: T25 --ignore tests refused by the argument check (rc 2, hits 1)
  PASS: T25 -p other refused by the argument check (rc 2, hits 1)
  PASS: T25 -pother refused by the argument check (rc 2, hits 1)
  PASS: T25 -p (no value) refused by the argument check (rc 2, hits 1)
  PASS: T25 -k (no value) refused by the argument check (rc 2, hits 1)
  PASS: T25 --basetemp refused by the argument check (rc 2, hits 1)
  PASS: T25 --rootdir refused by the argument check (rc 2, hits 1)
  PASS: T25 --junitxml refused by the argument check (rc 2, hits 1)
  PASS: T25 --confcutdir refused by the argument check (rc 2, hits 1)
  PASS: T25 --override-ini refused by the argument check (rc 2, hits 1)
  PASS: T25 --import-mode refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:runner (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:skipping (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:python (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:terminal (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:mark (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:assertion (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:capture (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:fixtures (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:logging (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:main (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:warnings (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:debugging (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:setuponly (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:setupplan (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:unittest (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:faulthandler (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:doctest (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:monkeypatch (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:recwarn (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:stepwise (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:junitxml (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:pastebin (core plugin) refused by the argument check (rc 2, hits 1)
  PASS: T25 -pno:runner (attached form) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:RANDOMLY (plugin names are exact) refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no:randomly.runner refused by the argument check (rc 2, hits 1)
  PASS: T25 -p no: (empty name) refused by the argument check (rc 2, hits 1)
  PASS: T25 path ../ outside root refused by the argument check (rc 2, hits 1)
  PASS: T25 absolute path outside root refused by the argument check (rc 2, hits 1)
  PASS: T25 path through a link out of the root refused by the argument check (rc 2, hits 1)
  PASS: T25 -- terminator refused by the argument check (rc 2, hits 1)
  PASS: T25 file unchanged, state empty
  PASS: T25 the allowed forms still run (-q -x -p no:NAME -k -m path::node) (got 0)
== T26 the start hook fails after the tests were started: the test group is still stopped (review 4 M2)
RuntimeError as expected: start hook failed
  PASS: T26 no orphan pytest left
== T27 a mutant whose new text equals the old text is refused (exit 2)
REFUSED: mutant m1: old text is empty or equal to new text (a no-op)
  PASS: T27 exit 2 (got 2)
== T28 a clean run leaves no temporary file in the state folder
  PASS: T28 state empty (ls -A)
== T29 stopping the test group fails (no permission): the leader is still stopped and signals stay disarmed (review r2 nit)
raised as expected: RuntimeError
SIG.allow after: False
  PASS: T29 SIG.allow is False afterwards
  PASS: T29 no orphan pytest left although stop_group failed
== T30 import check fails closed: a target that is not a .py module is refused unless --skip-import-check (recorded)
REFUSED: import check: 'docs/note.txt' is not a plain .py module path, so the check cannot tell which file the tests import; pass --skip-import-check if that is intended (it is recorded in the raw fil
  PASS: T30a refused (rc 2, 'import check' hits 1)
  PASS: T30a file unchanged
  PASS: T30b with --skip-import-check it runs (rc 0) and the raw file says so
== T31 a timeout keeps the output printed before it
  PASS: T31 raw file says TIMEOUT and holds the early output
--- output printed before the timeout ---
.
  PASS: T31 file restored
== T32 special files are never read: a FIFO in the tree, and a FIFO as the marker, give a refusal (exit 2) instead of a hang
  PASS: T32a FIFO in the tree refused, no hang (got 2; 124 or 137 = hung)
  PASS: T32b FIFO as marker refused, no hang (got 2; 124 or 137 = hung)
== T33 a .venv folder deeper than the top is compared like any other folder (exit 2)
  PASS: T33 nested .venv refused (got 2)
== T34 test output that is not UTF-8 is replaced, not an error (fake python that prints byte 0xff and fails)
  PASS: T34 run ends normally (rc 0) with verdict KILLED in the raw file
  PASS: T34 file restored
== T35 --restore with another TMPDIR: the marker kept by a run that used the default folder is found; exit 3 while the file is still planted
safety-tests.sh: line 371: 10526 Killed                  ( export TMPDIR=/tmp; exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
STILL PLANTED: src/mod.py differs from the backup kept by a run that used another TMPDIR; restore with: TMPDIR=/tmp python3 /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/ml/run.py --root /tm
  PASS: T35a exit 3 (got 3) and the file is still planted
  PASS: T35b restoring with the right TMPDIR works
  PASS: T35c nothing planted anywhere: exit 0 (got 0)
== T36 hard links (review r3 safety Major B): a target with two names would plant the mutant in the other file
REFUSED: mutant m1 target /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/root/src/mod.py is not a regular file with exactly one name (links: 2): a hard-linked scra
  PASS: T36a target hard-linked to a real repository file: refused for that reason (rc 2, hits 1)
  PASS: T36a the real repository file was not even touched (content and modification time)
  PASS: T36b tree built with cp -al: refused (rc 2, hits 1)
  PASS: T36b the linked original was not touched
refused: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/hl/a.txt i
both names unchanged and a one-name file still written: True
  PASS: T36c write_target itself refuses a two-name file before truncating it, and still writes a one-name file
== T37 an ini file ABOVE --root would change what pytest runs (review r3 minor)
REFUSED: pytest would take its settings from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/toy/pytest.ini, outside --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-
  PASS: T37a pytest.ini above the root refused (rc 2, hits 1)
  PASS: T37a file unchanged, state empty
  PASS: T37b pyproject.toml with a pytest section above the root refused (rc 2, hits 1)
  PASS: T37c a setup.cfg above WITHOUT a pytest section is no setting: the run goes ahead (rc 0)
== T38 --restore re-creates a deleted target with its recorded mode (review r3 minor)
safety-tests.sh: line 371: 10786 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
test group already gone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matches
  PASS: T38 exit 0 and the file is back with the original text (rc 0)
  PASS: T38 mode 640 restored
  PASS: T38 state empty
== T39 the orphan cannot be stopped (no permission) during --restore: the file is still restored (review r3 minor)
safety-tests.sh: line 371: 10931 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
True could NOT stop test group 10940 (Operation not permitted): file restored anyway; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matche
  PASS: T39 restore finished although stop_group raised PermissionError (rc 0)
  PASS: T39 the report says the orphan was not stopped
== T40 a signal right after the leader was reaped must not signal its (maybe reused) number (review r3 minor)
interrupted as expected
stop_group calls: []
  PASS: T40 no signal was sent to the reaped leader's number
== T41 control run: a signal right after the fork, before the handle is stored, must not leak the test group (review r3 minor)
interrupted as expected (<Signals.SIGTERM: 15>,)
  PASS: T41 no orphan pytest left
== T42 signals that used to kill run.py with the file still planted (review r3 minor): QUIT ABRT USR1 USR2 ALRM XCPU VTALRM PROF IO PWR
  PASS: T42 QUIT exit 131 (got 131)
  PASS: T42 QUIT file restored
  PASS: T42 QUIT state empty
  PASS: T42 QUIT no orphan pytest
  PASS: T42 ABRT exit 134 (got 134)
  PASS: T42 ABRT file restored
  PASS: T42 ABRT state empty
  PASS: T42 ABRT no orphan pytest
  PASS: T42 USR1 exit 138 (got 138)
  PASS: T42 USR1 file restored
  PASS: T42 USR1 state empty
  PASS: T42 USR1 no orphan pytest
  PASS: T42 USR2 exit 140 (got 140)
  PASS: T42 USR2 file restored
  PASS: T42 USR2 state empty
  PASS: T42 USR2 no orphan pytest
  PASS: T42 ALRM exit 142 (got 142)
  PASS: T42 ALRM file restored
  PASS: T42 ALRM state empty
  PASS: T42 ALRM no orphan pytest
  PASS: T42 XCPU exit 152 (got 152)
  PASS: T42 XCPU file restored
  PASS: T42 XCPU state empty
  PASS: T42 XCPU no orphan pytest
  PASS: T42 VTALRM exit 154 (got 154)
  PASS: T42 VTALRM file restored
  PASS: T42 VTALRM state empty
  PASS: T42 VTALRM no orphan pytest
  PASS: T42 PROF exit 155 (got 155)
  PASS: T42 PROF file restored
  PASS: T42 PROF state empty
  PASS: T42 PROF no orphan pytest
  PASS: T42 IO exit 157 (got 157)
  PASS: T42 IO file restored
  PASS: T42 IO state empty
  PASS: T42 IO no orphan pytest
  PASS: T42 PWR exit 158 (got 158)
  PASS: T42 PWR file restored
  PASS: T42 PWR state empty
  PASS: T42 PWR no orphan pytest
== T43 --restore must not stop a stranger that has the orphan's number (review r3 minor: start time + full argument list)
safety-tests.sh: line 371: 12301 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T43 setup: the stranger (a pytest of its own that names the root) is its own group leader
process 12379 is not this run's pytest (or cannot be verified): left alone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mu
  PASS: T43a restore exit 0 and the file is back (rc 0)
  PASS: T43a the stranger was left alone
safety-tests.sh: line 371: 12379 Killed                  ( cd "$T/root" && exec setsid "$T/root/.venv/bin/python" -m pytest -q -p no:cacheprovider tests/test_slow.py > /dev/null 2>&1 )
safety-tests.sh: line 371: 12405 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
process 12414 is not this run's pytest (or cannot be verified): left alone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mu
  PASS: T43b a marker with a group but no recorded identity: file restored (rc 0), group not stopped on a guess
== T44 the leader is dead but a member of the test group still runs: --restore stops it (review r3 minor)
safety-tests.sh: line 371: 12525 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_spawn.py ) > /dev/null 2>&1
  PASS: T44 setup: the leader is gone, 'sleep 3137' (a member of its group) still runs
stopped orphaned test group 12534; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; hash matches saved ori
  PASS: T44 restore exit 0, file back (rc 0)
  PASS: T44 the surviving member was stopped
== T45 SIGKILL before the second marker (no group recorded yet): --restore finds the group by the command the first marker names (review r3 minor)
safety-tests.sh: line 371: 12908 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T45 setup: the orphan runs
stopped orphaned test group 12917; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc4/tmpstate/hadavin-mutation-lane-0/d8ec2a4841c57245.backup; ha
  PASS: T45 restore exit 0, file back (rc 0)
  PASS: T45 the orphan was stopped
== T46 timeout branch with stop_group failing: signals disarmed BEFORE stop_group is called, leader still stopped (review r3 evidence Major 1)
raised as expected: PermissionError
SIG.allow seen inside stop_group: [False, False] after: False
  PASS: T46 SIG.allow was already False when the timeout branch called stop_group
  PASS: T46 no orphan pytest left although stop_group failed in the timeout branch
FAILED CHECKS: 0 (of 220 checks run; skipped: none)
rc=0
```
### r3 full log
```
== T1 the real repository as --root is refused (exit 2)
REFUSED: --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/repo is, contains or lies inside the real repository /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-961
  exit code 2
  PASS: T1 exit 2
== T2 SIGKILL while a mutant is planted
  file now: return2
safety-tests.sh: line 41: 13574 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T2 file stays planted
== T3 the next run refuses and says how to restore
REFUSED: a mutant (X-m1) is still planted in src/mod.py from an earlier run that was killed. Restore with: python3 /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9
  exit code 2
  PASS: T3 exit 2
== T4 marker lost: the tree check against a fresh git archive still refuses
REFUSED: scratch tree differs from git archive d5eb24c916c0d82441ef765e547a8dfca139c2a8 + patches in 1 file(s), first: ['src/mod.py']: it may hold a planted cha
  exit code 2
  PASS: T4 exit 2
== T5 --restore puts the saved original back
process 13583 is not this run's pytest: left alone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; hash matches saved original: True
  PASS: T5 file restored
  PASS: T5 state folder empty
== T6 SIGTERM during a run restores the file and removes the marker
  exit code 143
  PASS: T6 exit 143
  PASS: T6 file restored
  PASS: T6 state empty
== T7 SIGINT likewise, exit code read directly from $?
  exit code 130
  PASS: T7 exit 130
  PASS: T7 file restored
  PASS: T7 state empty
== T8 two runs at once: the second is refused by the lock, and the first is still alive
REFUSED: another run holds the lock for /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/
  second run exit code 2
  PASS: T8 second refused (2)
  PASS: T8 first run still alive
  PASS: T8 file still planted by the first
  PASS: T8 file restored after
== T9 a clean run to the end: KILLED, backup gone, tree diff clean, exit 0
m1 KILLED tests/test_fast.py::test_f
tree diff: 0 difference(s)
  exit code 0
  PASS: T9 exit 0
  PASS: T9 state empty
differing files (0; 0 = clean): []
== T10 absolute path as the mutant file is refused (exit 2), nothing planted
REFUSED: mutant m1 file: must be relative to the root and contain no '..': '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/root/src/mod.py'
  exit code 2
  PASS: T10 exit 2
  PASS: T10 file unchanged
  PASS: T10 state empty
== T11 '..' in the mutant file is refused (exit 2)
REFUSED: mutant m1 file: must be relative to the root and contain no '..': '../root/src/mod.py'
  exit code 2
  PASS: T11 exit 2
  PASS: T11 file unchanged
== T12 symlinked folders inside the scratch root
REFUSED: scratch tree differs from git archive d5eb24c916c0d82441ef765e547a8dfca139c2a8 + patches in 1 file(s), first: ['evil/']: it may hold a planted change; rebuild it from the archive
  (extra symlinked folder 'evil') exit code 2
  PASS: T12b exit 2
  PASS: T12b real repo file unchanged
REFUSED: scratch tree differs from git archive d5eb24c916c0d82441ef765e547a8dfca139c2a8 + patches in 2 file(s), first: ['src/', 'src/mod.py']: it may hold a planted change; rebuild it from the archive
  (src itself is a link to the real repo) exit code 2
  PASS: T12a exit 2
  PASS: T12a real repo file unchanged
== T13 git cannot tell (rev-parse fails): fail closed
REFUSED: git cannot tell whether --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/root is a work tree (rc 128): fatal: detected dubious ownership in repositor
  (work-tree check fails) exit code 2
  PASS: T13a exit 2
REFUSED: git rev-parse failed for --repo /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/repo (rc 128): fatal: detected dubious ownership in repository
  (show-toplevel fails) exit code 2
  PASS: T13b exit 2
== T14 a leftover file after the loop gives a non-zero exit; a declared --extra does not
  undeclared leftover: exit code 4
  PASS: T14a exit 4
  declared --extra: exit code 0
  PASS: T14b exit 0
== T15 SIGKILL of run.py leaves the test group alive; --restore stops it and restores
safety-tests.sh: line 79: 14458 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T15 orphan pytest alive
stopped orphaned test group 14467; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; hash matches saved original: True
  PASS: T15 orphan stopped
  PASS: T15 file restored
== T16 SIGHUP restores too (exit 129)
  exit code 129
  PASS: T16 exit 129
  PASS: T16 file restored
== T17 --restore while a run is live is refused (lock)
REFUSED: another run holds the lock for /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/
  exit code 2
  PASS: T17 exit 2
  PASS: T17 run still planted
== T18 a mutant id that climbs out of --raw is refused
REFUSED: mutant id is not a plain unique name: '../escape'
  exit code 2
  PASS: T18 exit 2
  PASS: T18 no file outside raw
== T19 an error while the tests start (no .venv python) still removes the marker
REFUSED: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/root/.venv/bin/python does not exist: the scratch root needs its ow
  exit code 2
  PASS: T19 exit 2
  PASS: T19 file unchanged
  PASS: T19 state empty
== T20 four signals in a row while a mutant is planted (5 times): file restored, marker gone, exit 129/130/143
  (probabilistic: it cannot force the second signal into the exact window; see T21 for the deterministic part)
  PASS: T20.1 exit 129/130/143 (got 129)
  PASS: T20.1 file restored
  PASS: T20.1 state empty
  PASS: T20.2 exit 129/130/143 (got 129)
  PASS: T20.2 file restored
  PASS: T20.2 state empty
  PASS: T20.3 exit 129/130/143 (got 129)
  PASS: T20.3 file restored
  PASS: T20.3 state empty
  PASS: T20.4 exit 129/130/143 (got 129)
  PASS: T20.4 file restored
  PASS: T20.4 state empty
  PASS: T20.5 exit 129/130/143 (got 129)
  PASS: T20.5 file restored
  PASS: T20.5 state empty
== T21 signal handler logic (deterministic): a signal while planted is only remembered, then delivered once
handler logic ok
  PASS: T21 handler logic
== T22 state folder checks: wrong mode, a link, another owner are refused (exit 2)
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22a mode 755 refused (got 2)
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22b symlinked state folder refused (got 2)
  PASS: T22b nothing written through the link
REFUSED: state folder /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0 is not a plain 
  PASS: T22c other owner refused (got 2)
== T23 forged state: a backup whose hash differs, a marker that is a link, --restore inside the real repository: all refused, nothing written
safety-tests.sh: line 371: 15335 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
REFUSED: the saved backup does not match the hash recorded in the marker: refused
  PASS: T23a hash mismatch refused (got 2)
  PASS: T23a file not written
REFUSED: state file /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.
  PASS: T23b marker as a link refused (got 2)
  PASS: T23b file not written
process 15344 is not this run's pytest: left alone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; hash matches saved original: True
  PASS: T23 genuine restore still works
REFUSED: --root /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/repo is, contains or lies inside the real reposito
  PASS: T23c --restore in the real repository refused for that reason (got 2, reason hits 1)
== T24 import check: the tests would load the target from another tree (exit 2); the right tree passes and is recorded
REFUSED: import check: `import mod` loads '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/repo/src/mod.py', not /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpa
  PASS: T24a refused (got 2)
  PASS: T24a file unchanged
  PASS: T24b recorded in the raw file
  PASS: T24b raw file lists 4 environment names
== T25 TESTS is an allowlist: every bypass named in review r2 is refused by the argument check (exit 2, message 'TESTS argument'), one check each
  PASS: T25 @argsfile refused by the argument check (rc 2, hits 1)
  PASS: T25 -k @argsfile refused by the argument check (rc 2, hits 1)
  PASS: T25 -qc (clustered c) refused by the argument check (rc 2, hits 1)
  PASS: T25 -qo (clustered o) refused by the argument check (rc 2, hits 1)
  PASS: T25 -qp (clustered p) refused by the argument check (rc 2, hits 1)
  PASS: T25 -c refused by the argument check (rc 2, hits 1)
  PASS: T25 -cfoo.ini refused by the argument check (rc 2, hits 1)
  PASS: T25 -oaddopts=-x refused by the argument check (rc 2, hits 1)
  PASS: T25 --collect-only refused by the argument check (rc 2, hits 1)
  PASS: T25 --co refused by the argument check (rc 2, hits 1)
  PASS: T25 --setup-plan refused by the argument check (rc 2, hits 1)
  PASS: T25 --setup-only refused by the argument check (rc 2, hits 1)
  PASS: T25 --help refused by the argument check (rc 2, hits 1)
  PASS: T25 -h refused by the argument check (rc 2, hits 1)
  PASS: T25 --version refused by the argument check (rc 2, hits 1)
  PASS: T25 -V refused by the argument check (rc 2, hits 1)
  PASS: T25 --noconftest refused by the argument check (rc 2, hits 1)
  PASS: T25 --ignore=tests refused by the argument check (rc 2, hits 1)
  PASS: T25 --ignore tests refused by the argument check (rc 2, hits 1)
  PASS: T25 -p other refused by the argument check (rc 2, hits 1)
  PASS: T25 -pother refused by the argument check (rc 2, hits 1)
  PASS: T25 -p (no value) refused by the argument check (rc 2, hits 1)
  PASS: T25 -k (no value) refused by the argument check (rc 2, hits 1)
  PASS: T25 --basetemp refused by the argument check (rc 2, hits 1)
  PASS: T25 --rootdir refused by the argument check (rc 2, hits 1)
  PASS: T25 --junitxml refused by the argument check (rc 2, hits 1)
  PASS: T25 --confcutdir refused by the argument check (rc 2, hits 1)
  PASS: T25 --override-ini refused by the argument check (rc 2, hits 1)
  PASS: T25 --import-mode refused by the argument check (rc 2, hits 1)
  FAIL: T25 -p no:runner (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:skipping (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:python (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:terminal (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:mark (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:assertion (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:capture (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:fixtures (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:logging (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:main (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:warnings (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:debugging (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:setuponly (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:setupplan (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:unittest (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:faulthandler (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:doctest (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:monkeypatch (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:recwarn (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:stepwise (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:junitxml (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:pastebin (core plugin) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -pno:runner (attached form) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:RANDOMLY (plugin names are exact) refused by the argument check (rc 2, hits 0)
  FAIL: T25 -p no:randomly.runner refused by the argument check (rc 2, hits 0)
  PASS: T25 -p no: (empty name) refused by the argument check (rc 2, hits 1)
  PASS: T25 path ../ outside root refused by the argument check (rc 2, hits 1)
  PASS: T25 absolute path outside root refused by the argument check (rc 2, hits 1)
  PASS: T25 path through a link out of the root refused by the argument check (rc 2, hits 1)
  PASS: T25 -- terminator refused by the argument check (rc 2, hits 1)
  PASS: T25 file unchanged, state empty
  PASS: T25 the allowed forms still run (-q -x -p no:NAME -k -m path::node) (got 0)
== T26 the start hook fails after the tests were started: the test group is still stopped (review 4 M2)
RuntimeError as expected: start hook failed
  PASS: T26 no orphan pytest left
== T27 a mutant whose new text equals the old text is refused (exit 2)
REFUSED: mutant m1: old text is empty or equal to new text (a no-op)
  PASS: T27 exit 2 (got 2)
== T28 a clean run leaves no temporary file in the state folder
  PASS: T28 state empty (ls -A)
== T29 stopping the test group fails (no permission): the leader is still stopped and signals stay disarmed (review r2 nit)
raised as expected: RuntimeError
SIG.allow after: False
  PASS: T29 SIG.allow is False afterwards
  PASS: T29 no orphan pytest left although stop_group failed
== T30 import check fails closed: a target that is not a .py module is refused unless --skip-import-check (recorded)
REFUSED: import check: 'docs/note.txt' is not a plain .py module path, so the check cannot tell which file the tests import; pass --skip-import-check if that is intended (it is recorded in the raw fil
  PASS: T30a refused (rc 2, 'import check' hits 1)
  PASS: T30a file unchanged
  PASS: T30b with --skip-import-check it runs (rc 0) and the raw file says so
== T31 a timeout keeps the output printed before it
  PASS: T31 raw file says TIMEOUT and holds the early output
--- output printed before the timeout ---
.
  PASS: T31 file restored
== T32 special files are never read: a FIFO in the tree, and a FIFO as the marker, give a refusal (exit 2) instead of a hang
  PASS: T32a FIFO in the tree refused, no hang (got 2; 124 or 137 = hung)
  PASS: T32b FIFO as marker refused, no hang (got 2; 124 or 137 = hung)
== T33 a .venv folder deeper than the top is compared like any other folder (exit 2)
  PASS: T33 nested .venv refused (got 2)
== T34 test output that is not UTF-8 is replaced, not an error (fake python that prints byte 0xff and fails)
  PASS: T34 run ends normally (rc 0) with verdict KILLED in the raw file
  PASS: T34 file restored
== T35 --restore with another TMPDIR: the marker kept by a run that used the default folder is found; exit 3 while the file is still planted
safety-tests.sh: line 371: 16271 Killed                  ( export TMPDIR=/tmp; exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
STILL PLANTED: src/mod.py differs from the backup kept by a run that used another TMPDIR; restore with: TMPDIR=/tmp python3 /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/ml3/run.py --root /t
  PASS: T35a exit 3 (got 3) and the file is still planted
  PASS: T35b restoring with the right TMPDIR works
  PASS: T35c nothing planted anywhere: exit 0 (got 0)
== T36 hard links (review r3 safety Major B): a target with two names would plant the mutant in the other file
m1 KILLED tests/test_fast.py::test_f
tree diff: 0 difference(s)
  FAIL: T36a target hard-linked to a real repository file: refused for that reason (rc 0, hits 0)
  FAIL: T36a the real repository file was not even touched (content and modification time)
  FAIL: T36b tree built with cp -al: refused (rc 0, hits 0)
  FAIL: T36b the linked original was not touched
no refusal
both names unchanged and a one-name file still written: False
  FAIL: T36c write_target itself refuses a two-name file before truncating it, and still writes a one-name file
== T37 an ini file ABOVE --root would change what pytest runs (review r3 minor)
m1 SURVIVED 
tree diff: 0 difference(s)
  FAIL: T37a pytest.ini above the root refused (rc 0, hits 0)
  PASS: T37a file unchanged, state empty
  FAIL: T37b pyproject.toml with a pytest section above the root refused (rc 0, hits 0)
  PASS: T37c a setup.cfg above WITHOUT a pytest section is no setting: the run goes ahead (rc 0)
== T38 --restore re-creates a deleted target with its recorded mode (review r3 minor)
safety-tests.sh: line 371: 16579 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
REFUSED: marker file: 'src/mod.py' is not a regular file under /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/root
tail: cannot open '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/toy/root/src/mod.py' for reading: No such file or directory
  FAIL: T38 exit 0 and the file is back with the original text (rc 2)
  FAIL: T38 mode 640 restored
  FAIL: T38 state empty
== T39 the orphan cannot be stopped (no permission) during --restore: the file is still restored (review r3 minor)
safety-tests.sh: line 371: 16685 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
    ~~~~~~~~~~^^^^^^
  File "<stdin>", line 3, in cannot
PermissionError: [Errno 1] Operation not permitted
  FAIL: T39 restore finished although stop_group raised PermissionError (rc 1)
  FAIL: T39 the report says the orphan was not stopped
== T40 a signal right after the leader was reaped must not signal its (maybe reused) number (review r3 minor)
interrupted as expected
stop_group calls: [16780]
  FAIL: T40 no signal was sent to the reaped leader's number
== T41 control run: a signal right after the fork, before the handle is stored, must not leak the test group (review r3 minor)
interrupted as expected (<Signals.SIGTERM: 15>,)
  FAIL: T41 no orphan pytest left
== T42 signals that used to kill run.py with the file still planted (review r3 minor): QUIT ABRT USR1 USR2 ALRM XCPU VTALRM PROF IO PWR
safety-tests.sh: line 316: 16804 Quit                    ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 QUIT exit 131 (got 131)
  FAIL: T42 QUIT file restored
  FAIL: T42 QUIT state empty
  FAIL: T42 QUIT no orphan pytest
safety-tests.sh: line 316: 16865 Aborted                 ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 ABRT exit 134 (got 134)
  FAIL: T42 ABRT file restored
  FAIL: T42 ABRT state empty
  FAIL: T42 ABRT no orphan pytest
safety-tests.sh: line 316: 17001 User defined signal 1   ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 USR1 exit 138 (got 138)
  FAIL: T42 USR1 file restored
  FAIL: T42 USR1 state empty
  FAIL: T42 USR1 no orphan pytest
safety-tests.sh: line 316: 17158 User defined signal 2   ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 USR2 exit 140 (got 140)
  FAIL: T42 USR2 file restored
  FAIL: T42 USR2 state empty
  FAIL: T42 USR2 no orphan pytest
safety-tests.sh: line 316: 17278 Alarm clock             ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 ALRM exit 142 (got 142)
  FAIL: T42 ALRM file restored
  FAIL: T42 ALRM state empty
  FAIL: T42 ALRM no orphan pytest
safety-tests.sh: line 316: 17436 CPU time limit exceeded ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 XCPU exit 152 (got 152)
  FAIL: T42 XCPU file restored
  FAIL: T42 XCPU state empty
  FAIL: T42 XCPU no orphan pytest
safety-tests.sh: line 316: 17660 Virtual timer expired   ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 VTALRM exit 154 (got 154)
  FAIL: T42 VTALRM file restored
  FAIL: T42 VTALRM state empty
  FAIL: T42 VTALRM no orphan pytest
safety-tests.sh: line 316: 17800 Profiling timer expired ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 PROF exit 155 (got 155)
  FAIL: T42 PROF file restored
  FAIL: T42 PROF state empty
  FAIL: T42 PROF no orphan pytest
safety-tests.sh: line 316: 17928 I/O possible            ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 IO exit 157 (got 157)
  FAIL: T42 IO file restored
  FAIL: T42 IO state empty
  FAIL: T42 IO no orphan pytest
safety-tests.sh: line 316: 17964 Power failure           ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T42 PWR exit 158 (got 158)
  FAIL: T42 PWR file restored
  FAIL: T42 PWR state empty
  FAIL: T42 PWR no orphan pytest
== T43 --restore must not stop a stranger that has the orphan's number (review r3 minor: start time + full argument list)
safety-tests.sh: line 371: 18054 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T43 setup: the stranger (a pytest of its own that names the root) is its own group leader
stopped orphaned test group 18125; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; ha
safety-tests.sh: line 371: 18125 Killed                  ( cd "$T/root" && exec setsid "$T/root/.venv/bin/python" -m pytest -q -p no:cacheprovider tests/test_slow.py > /dev/null 2>&1 )
  PASS: T43a restore exit 0 and the file is back (rc 0)
safety-tests.sh: line 30: kill: (18125) - No such process
  FAIL: T43a the stranger was left alone
safety-tests.sh: line 371: 18154 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
stopped orphaned test group 18163; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; ha
  FAIL: T43b a marker with a group but no recorded identity: file restored (rc 0), group not stopped on a guess
== T44 the leader is dead but a member of the test group still runs: --restore stops it (review r3 minor)
safety-tests.sh: line 371: 18222 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_spawn.py ) > /dev/null 2>&1
  PASS: T44 setup: the leader is gone, 'sleep 3137' (a member of its group) still runs
process 18231 is not this run's pytest: left alone; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; hash 
  PASS: T44 restore exit 0, file back (rc 0)
  FAIL: T44 the surviving member was stopped
== T45 SIGKILL before the second marker (no group recorded yet): --restore finds the group by the command the first marker names (review r3 minor)
safety-tests.sh: line 371: 18448 Killed                  ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) > /dev/null 2>&1
  PASS: T45 setup: the orphan runs
no test group recorded; restored src/mod.py from /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev/sc3/tmpstate/hadavin-mutation-lane-0/9f19e33546c26ecd.backup; hash matches 
  PASS: T45 restore exit 0, file back (rc 0)
  FAIL: T45 the orphan was stopped
== T46 timeout branch with stop_group failing: signals disarmed BEFORE stop_group is called, leader still stopped (review r3 evidence Major 1)
raised as expected: PermissionError
SIG.allow seen inside stop_group: [False, False] after: False
  PASS: T46 SIG.allow was already False when the timeout branch called stop_group
  PASS: T46 no orphan pytest left although stop_group failed in the timeout branch
FAILED CHECKS: 73 (of 220 checks run; skipped: none)
rc=0
```
