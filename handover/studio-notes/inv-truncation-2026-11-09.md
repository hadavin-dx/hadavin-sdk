# Truncated pytest logs: root cause and fix (2026-11-09, UTC 07:15)

## What I could NOT settle (read first)
- PR74 (21ca680) and PR75 (f8b9056) have NO true full-suite result yet. Their real output was lost with the replaced files. I did not re-run them (not asked; one head only). Only PR75 3.12 `exit=0` is a real pytest exit code (so it passed 3.12; no counts known). With the fixed runner each re-run is about 6.5 min per Python version when the machine is quiet.
- PR63 (bf955e9) and PR86 (8f6b032) logs are truncated the same way; true results NOT obtained.
- The 3.13 `F` seen at about dot 2300 in the old PR66 log: I did not see that process, but the fixed re-run shows exactly ONE failed test on 3.13 (below). I infer the F was that test; I did not prove the position.
- I did not inspect the dying processes with a signal tracer to the end (I started strace, then stopped it once the cause was proven another way). Cause (c) and (d) are not needed to explain the data, but I did not test every `os.kill` test one by one.

## Root cause (RAN, proven)
The evidence logs were written INSIDE the shared git working tree (`handover/evidence/...`, tracked files). Other sessions run `git add/commit/pull --rebase/checkout` in that tree while a test run is still going. Git replaces a tracked file that differs from the commit (delete + create = a new file). Then:
1. pytest keeps writing dots into the OLD, now deleted file (`heavy.sh` opens it once with `>>`).
2. When pytest ends, `heavy.sh` does `echo exit=$rc >> $log`. That opens the log by PATH, so it lands in the NEW file, which holds only the partial text git had committed earlier.
Result: partial dots + `exit=N` on the same line, no summary. `exit=N` is the real pytest exit code; the dots and summary are lost.

Evidence:
- Identical mtimes across different PRs, to the second: PR66-312 and PR75-312 at 06:29:49; PR66-313 and PR75-313 at 06:34:39; PR63-312 and PR74-313 at 06:45:13. Independent runs cannot die in the same second; one git operation rewrote them. `progress.txt` shows PR66 3.12 really ended at 06:28:27 (log mtime 06:29:49 is later).
- `git show b4d1052:handover/evidence/PR66/da08ce2/full-312.txt` (committed 06:23:28) is 250 bytes ending in the dots; the file on disk is those 250 bytes + `exit=1` = 257 bytes (READ).
- Live proof at 06:57 UTC (RAN): `ls -l /proc/18671/fd/5` -> `.../handover/evidence/PR80/4003672/full-312.txt (deleted)`; the open deleted file held 2995 bytes, the file at that path 102 bytes.
- Reproduction in a scratch git repo (RAN): background `( ...dots... ) >>log; echo exit=0 >>log`, then `git checkout -q HEAD -- log.txt` after unlink. Final file: `$ cmd` / `...exit=0` (3 dots committed + exit line, 6 later dots lost).
- Direct runs of the same tests in the same venv with logs outside the tree were not truncated (PR74 3.12: 1843 tests logged without a death; PR66 full re-run below).
- Not the cause: disk (26G free), memory (16G, 10G free), dmesg (no OOM), ulimits, heavy.sh flock (it only holds the lock), no test calls os._exit/dup2 (grep over tests, src, tools, demos).

## Fix applied (to the runner, not to any PR branch)
`/home/user/build/evid.sh` (backup `evid.sh.bak-before-order175`):
- Logs are written to `/home/user/build/evid-out/PR<n>/<sha>/` (outside git) and copied into `handover/evidence/PR<n>/<sha>/` only when a log is complete.
- pytest now runs with `-X faulthandler -q -rA --tb=short --junitxml=<dir>/full-<v>.xml`.
- After the run a `SUMMARY tests=.. failed=.. errors=.. skipped=.. passed=.. pytest_exit=..` line is built from the junit file (never a tail pipe). No junit file prints `SUMMARY NONE (...)` = the run died. It also prints the last 5 lines.
Rule for every reader: a log with no `SUMMARY` line is NOT a result.
Other scripts that write logs under the git tree (`evid-chain.sh`, the P1b/B3a/cilint logs under `handover/evidence/`) have the same flaw; I did not change them. Follow-up: point them at a directory outside the tree.

## Second finding, runner environment (RAN)
`/home/user/build/pgstart.sh` started Postgres on port 56000+PR with socket in /tmp. The test `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]` runs `dblink_connect('dbname=postgres')` INSIDE the server, which uses libpq defaults (`/var/run/postgresql`, port 5432) and so is refused. Fix (backup `pgstart.sh.bak-before-order175`): the server is started with `PGPORT=<port> PGHOST=/tmp`. Proof: with a new cluster started that way, the whole file `tests/demo_askdata/test_validate_harm.py` gives `253 passed in 25.08s` on 3.12 (PR66 head). This is a runner artefact, not a repo bug. Already-running clusters keep the old setting until restarted.

## Proof re-run, PR66 head da08ce2 (branch origin/core/P4d), with the fixed runner (RAN, 07:02-07:14 UTC)
| Python | tests | passed | failed | skipped | pytest exit |
|---|---|---|---|---|---|
| 3.12 | 10519 | 10517 | 1 | 1 | 1 |
| 3.13 | 10519 | 10517 | 1 | 1 | 1 |
The one failure on both is the runner artefact above (dblink-connect), which passes when Postgres is started by the fixed `pgstart.sh`. 28 tests deselected (live/perf). ruff check, ruff format --check and bandit: exit 0 (06:22 run and 07:02 run). Not re-run in full after the pgstart fix; the 253-test file run is the proof. Logs: `handover/evidence/PR66/da08ce2/full-312.txt|xml`, `full-313.txt|xml` (these replaced the truncated files in the working tree; not committed by me).
This also explains the old 3.12 `exit=1`: the same single failure. A full-suite pass for PR66 therefore needs one more run with the fixed `pgstart.sh` (about 6.5 min per version).

## Class check (ORDER 175 item 7)
(a) runner/wrapper: this is the cause (log replaced under a live writer). (b) OOM/CPU: not seen. (c) tests with os.kill/killpg: exist only in `tests/test_mutation_runner.py` (they signal their own child runner); not the cause here. (d) xdist/faulthandler: no xdist installed; faulthandler now on.
