# Silent pytest exit: findings (EVIDENCE RUNNER, 2026-11-10 17:55Z / IST 23:25)

## Cause: FOUND (with one part inferred, stated below)
The log file is replaced under the running job by a `git pull --rebase` in the main working tree. pytest does not die.

How it happens:
1. A job writes its log inside the repo tree (handover/evidence/...), via heavy.sh (`cmd >> log`, the shell keeps the file open).
2. The lead's routine runs `git add handover/... && git commit` and then `git pull -q --rebase --autostash origin core/cloud-handover` in /home/user/hadavin-sdk. The half-written log is committed.
3. The rebase checks out the upstream tip (the file is absent there) and then replays the commit, so git DELETES and RE-CREATES the log with the committed half. New inode.
4. The running pytest and its wrapper still write to the old, now unlinked, file: everything after that moment is lost. heavy.sh opens the log again by path at the end and appends `exit=<rc>`, which lands on the new file, right after the cut (often mid-line: "..........exit=0").
5. The exit code is the real one. So a cut log with exit=0 is a pass whose output is lost; exit=1 may be a real failure whose summary is lost (not knowable from the cut log).

## Evidence (raw files in this folder)
- run1.log / run1.xml: tests/contracts/test_store_reserve.py, py3.13, one heavy slot. Log ends `...sum[postgres] exit=0` at 14033 bytes, no summary, wrapper's `echo pytest_rc=` missing. run1.xml (junit, written by pytest itself): 101 tests, 0 failures, 89.78 s. So pytest finished fine.
- git history of the main tree (`git reflog`, `git show 395adca:handover/evidence/silent-exit/run1.log | wc -c`): commit 75b2e82 at 17:41:19Z contained run1.log at 14026 bytes (the log while test b5 postgres was running), and `pull --rebase --autostash` ran at 17:41:20Z (reflog entries 395adca "start/pick/finish"). The final file is 14033 = 14026 + `exit=0\n`... (+ lines of a later commit, a3143e8, same size family). Log size = committed size, mtime of the log = a pull at 17:42:44Z.
- demo-gitpull-rebase-result.txt: a throw-away repo reproduces it: log opened with `>>`, `git add; git commit; git pull --rebase`, inode changes (5140216 -> 5163153), file content afterwards `line1 line2 line3 exit=0`, lines 4-6 lost.
- Control runs that were NOT cut (nobody pulled during them): run2-repo.log (b5 test alone, 2 passed, rc 0), run3.log (full file under strace, 101 passed in 167 s, rc 0). run3.strace shows no close/dup2 of fd 1 or 2 by the test process.

## Hypotheses checked
1. heavy.sh timeout: NO. /home/user/build/heavy.sh has no timeout and no kill; it only flocks a slot, runs `"$@" >>log 2>&1` and appends exit=.
2. test closes or redirects fd 1/2: NO. grep of EV-A3 tests/src/tools: no os._exit, dup2, os.close, sys.stdout reassignment; kill/signal uses in tests/test_mutation_runner.py are guarded (own session, own group). strace of the b5 file: only pytest's own capture dup2 pairs, restored.
3. Interpreter / plugin crash, OOM: NO. 3.13.18, pytest 9.2.0, no xdist, no timeout plugin; the junit file shows complete runs; free -m 5.5 GB free of 16 GB, no swap; no cgroup memory.events on this VM (cannot read OOM counters; not needed since runs completed).
4. Disk full: NO. df: 16 GB free.

## Not proven / uncertain
- I reproduced the mechanism in a toy repo and matched it to the commit times for run1; I did NOT see the actual A3/A7/A8 logs' commit times, so for them it is the same pattern (cut mid-line, exit code present, only in logs under handover/evidence) but not individually proven. Check: `git log --format='%h %ci' -- <logpath>` against the cut time.
- The exit=1 of A3 (18%, 4%, in b5 postgres) may be REAL test failures whose summary was lost. They must be rerun with the log outside the repo tree before anyone calls those runs "infrastructure noise".
- The chunk results "exit 0 at 48%/21%/96%" are probably passes with a lost tail, not proof of a full pass either.

## Fix (not applied; I do not edit scripts/repo; for the lead)
1. Write job logs OUTSIDE the git tree (e.g. /home/user/build/logs/<job>.log) and copy into handover/evidence only after the line `exit=` exists. (heavy.sh callers: A3 driver.sh, A7 run.sh/chunk.sh, A8, EV scripts all write straight into handover/evidence.)
2. Or make the lead's commit routine skip files without a final `exit=` line / add a .gitignore pattern for in-progress logs (e.g. handover/evidence/**/*.running) and have heavy.sh write `<log>.running` then `mv` at the end.
3. Rerun A3/A7/A8 full suites with logs outside the tree and with `--junitxml` (xml is written once at the end and survives).
Next step owner: lead (script change + rerun); no spend needed.
Cleanup: se_ev313 database dropped; no process of mine left running; scratch demo dirs removed.
