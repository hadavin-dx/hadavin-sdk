# Q11 xdist root cause (evidence runner; base f3c39cf89ec989f032ea48a23cfd824b88da9c68, worktree /home/user/work/q11-base)

## Cause (PROVEN by one-change experiments)
Under xdist the worker process has COLUMNS=80 (and LINES=24) in its environment; serial pytest has neither. The tests pass `env={**os.environ, ...}` to `bash scripts/reset.sh`, so the script's `ps` inherits COLUMNS=80. With COLUMNS set, procps-ng 4.0.4 `ps` cuts `-o args=` at that many columns even when output is a pipe (unset: no cut). The fake desk's command line is `python -c <code> lead_desk.server <ready>`; the marker `lead_desk.server` is the LAST argument, past column 80, so scripts/reset.sh:34 gets a cut line, falls to `*)` (line 45) and exits 6 ("is not the desk"). Exit 6 = the pid in the pid file is a live process that is not the desk/demo server (script lines 45-46; no docs/limits.md entry for it).
Classification: SCRIPT portability defect (real, any system where COLUMNS is set, e.g. an interactive 80-column terminal), triggered by the xdist environment; the tests are right. Not a test-order/race problem: deterministic, 100% in 6 of 6 xdist runs.
File:line: scripts/reset.sh:34 (`ps -p "$pid" -o args=`). Sibling check: lines 27 and 35 use `-o stat=` (short, not affected).
Side finding: COLUMNS=80 is not in os.environ of a serial worker, but a plain `subprocess.run` with env=None in serial pytest also got a cut line, so the C-level environment of the pytest process holds a COLUMNS value there too; which library sets it was NOT traced (not needed for the proof). Tests that pass an explicit env copy of os.environ do not get it serially.

## Fix (text only; tried in my own worktree copy, then reverted; diff saved raw/q11-fix.diff)
```diff
-    what="$(ps -p "$pid" -o args= 2>/dev/null || true)"
+    what="$(ps -ww -p "$pid" -o args= 2>/dev/null || true)"
```
`-ww` = unlimited width (procps, also BusyBox/macOS accept -ww). Result: both tests pass at -n1 and -n2; whole tests/test_reset_scripts.py passes under -n 2 (45 passed). Not tested: macOS/BusyBox ps, the full suite with the fix. Alternative: read /proc/PID/cmdline (Linux only; less portable).

## Experiments (exact commands in the session; venvs final-venv serial, q1-xdist-venv xdist; two target tests only)
1. Serial, final-venv, 3 runs: 2 passed each. Serial, xdist-venv with `-p no:xdist`, 3 runs: 2 passed. `-p xdist -n 0`: 2 passed (xdist inactive, no workers).
2. `-p xdist -n 1` 3 runs: 2 failed each (`assert 6 == 5`, `assert 6 == 0`). `-n 2` 3 runs: 2 failed each. (-n 0 run once only; my shell loop for -n 0 repeats was broken, single run shown.)
3. Probe (scratch/q11_probe.py, q11_probe2.py), same venv: serial worker COLUMNS=None LINES=None; xdist worker COLUMNS='80' LINES='24'. TERM=linux, stdin/out/err not a tty in both. Process group/session differ but irrelevant. `/proc/PID/cmdline` holds the full line (91 chars) in both. `ps -p PID -o args=` returned 80 chars in xdist; `ps -ww` returned the full line in both.
4. Plain shell, long-arg process: default/stdin variants 148 chars (full); `COLUMNS=80 ps` 81 bytes (cut); `COLUMNS=500` 148; `-ww` 148; `LINES=24` alone 148; TERM variants and `env -i` full. So COLUMNS alone causes the cut; stdin type, TERM and pipe do not.
5. Probe2 in pytest: env without COLUMNS/LINES -> 90 (full); env COLUMNS=500 -> 90; default env=None -> 80 in both modes (see side finding).
6. ONE change: `COLUMNS=500` set when launching pytest -> xdist -n1: 2 passed, -n2: 2 passed. Opposite direction: `COLUMNS=80` serial -> 2 failed (6 vs 5 and 6 vs 0). 
7. ONE change in the script copy (`ps -ww`): see Fix.
Q1's guess (ps cuts at 80 without a terminal) was half right: the cut needs COLUMNS=80 in the environment, not "no terminal".
