# Lane 9 hang hunt: RESULTS (EVIDENCE RUNNER: runs and records, no judging, no fixes)

Tree: public branch pr-3-tests, head b29bb1f5b1c0b702e37198120d08b080861006fc (verified), clone /tmp/work/hang-tree, python3.12 venv, `pip install --require-hashes -r requirements-dev.txt`. Playwright NOT installed (test_hung_adapter_calls.py and the 17 files before it do not use it; in the full run 116 browser tests were skipped). `-p no:randomly` did not error (pytest-randomly is NOT installed, so order is the default file order anyway). No commit, no push, nothing changed in the tree.

## 1. ANSWER (failures first)
**NOT REPRODUCED.** Zero failures, zero hangs, zero faulthandler dumps, zero early ends in 51 pytest runs (list below). No ROOT CAUSE found; no stack to report.
Deviations from the order, stated plainly:
- Only **17** test files sort before test_hung_adapter_calls.py (not 20); I ran those 17 + the file = 18 files, 880 tests (hung file is the last 42 of them, i.e. tests 839-880 in this order; the reported "near test 840" is its start).
- "Together" batches: 2 runs without load + 5 under load (not 10), because one together run takes 3.4-4.8 min. "Alone": 3 without load + 30 under load, as ordered.
- Load = 2 `yes > /dev/null` loops (PIDs 24367/24368 in the last batch, killed by trap; `pgrep -x yes` empty at the end) on a 4-vCPU VM that ALSO had another lane's pytest (`--cov`, pid 5362, ~15 min) running, plus my own full serial run (section 3) overlapping the first 3 loaded together runs. Load average during loaded together runs: 2.6-4.1.
- The "SLOW over 60 s" flag in the together batches is just the normal duration of 880 tests (200-290 s); no run was near the 300 s kill limit. First run over 60 s in the together batches = the first one (nl-together-1, 259.7 s) and it is normal. In the alone batches NO run exceeded 15 s.

## 2. Per-run seconds
| batch | runs | load | seconds (min / max) | exit codes | result |
|---|---|---|---|---|---|
| nl-alone (hung file alone) | 3 | none, load avg ~0.8 | 13.1 - 13.3 (see log) | all 0 | 42 passed each |
| load-alone | 30 | 2 busy loops, load avg 1.4-2.8 | 13.3 / 14.8 | all 0 | 42 passed each |
| nl-together (18 files) | 2 | none | 230.1 / 259.7 | 0,0 | 880 passed each |
| load-together (18 files) | 5 | 2 busy loops + other lane + my full run | 202.8 / 289.5 (289.5, 202.8, 238.0, 207.5, 239.3) | all 0 | 880 passed each |
| full suite, serial, one process | 1 | other lane's pytest + my loaded batch | 857 s (14 min 16 s) | 0 | 2349 passed, 116 skipped (Playwright absent), summary line printed |
Per-run lines: batch-log.txt; raw output with uptime before/after and `--durations=5`: run-*.txt. Slowest tests in the hung file in every alone run: test_stop_waits_only_its_timeout 1.5-1.6 s, test_reaper_survives_hung_send/_crm_put about 1.1 s. Slowest in the together runs: test_clock_steps dry-run tests 34 s (64 s once under load, run load-together-1), test_burst_distinct_emails 28-30 s, test_startup_50_pending 17 s. None in the hung file.

## 3. Memory (lead's hypothesis D10): NOT supported by counters
Files: memory-start.txt, memory-start-b.txt, memory-fullrun.txt, memory-end.txt, memory-lead-session-1.txt.
- 16086 MiB, no swap, cgroup v1 (no memory.events). memory.oom_control `oom_kill 0`, `under_oom 0` at start, after the full run and at the end; memory.failcnt 0; limit unlimited; max_usage 5.31 GB (start) -> 6.72 GB (after full run) -> 6.84 GB (end); that figure includes page cache (buff/cache 4-5.5 GB, "used" only about 0.9 GB).
- dmesg readable: no oom / "Killed process" lines.
- ONE full serial pytest process of the final tree: peak RSS **190 MiB** (python resource.getrusage on the child; /usr/bin/time does not exist here). Full pytest suite ~190 MiB, at most one other child process (small). Capacity on 16 GiB: roughly 16000 / 190 = 80 suites by RSS, so memory alone would not limit a handful of lanes; a Playwright chromium adds typically several hundred MiB (I did not measure it; Playwright not installed) so even 4 suites + 4 browsers would be only a few GiB by estimate. CPU (4 vCPU) is the tighter limit: a suite is mostly CPU/sleep bound (user 61 s + sys 11 s over 857 s wall, so it is waiting, not computing).
- Caveat: these counters are THIS VM's. The lane 1 / lane 4 runs happened elsewhere (their own containers?). I cannot say what their counters were; only that on this VM no OOM happened and a full run uses little memory.

## 4. SYN-flooding lines (lead's loopback hypothesis)
dmesg has 4 lines "Possible SYN flooding on port 127.0.0.1:<port>" at kernel times 740.6, 852.0, 2051.7 and 3755.7 s; no NEW line after 3755.7 s (end of my work: uptime 5774 s). My batches began at about 3540 s. The 3755.7 s line (about 19:53) falls inside my first together run (nl-together-1, 19:50:56-19:55:15, 259.7 s, the slowest of the unloaded together runs but with no stall: it passed 880 tests). The other three lines predate my work. The hung file itself opens NO sockets (it patches `adapters._exchange` with in-process fakes; the only URLs, http://127.0.0.1:9, are never connected), so loopback connect/accept does not enter its waits; the SYN lines come from server tests in other files (server uses request_queue_size = LISTEN_QUEUE = 1024 in constants.py:46, somaxconn 4096, tcp_max_syn_backlog 1024). Stall pattern vs SYN lines: no run over 60 s apart from the normal 880-test runs; the only slower-than-usual run (289.5 s, load-together-1, with 64 s in one clock test) has NO SYN line in its window. So not supported by my runs; I did not observe a stall at all.

## 5. start_proc pipe lead (quick confirm): NOT supported
test_hung_adapter_calls.py has no Popen/start_proc (grep). Among the 17 files before it only test_desk_http_edge_cases.py (4 uses) and test_http.py (6) use start_proc (tests/support.py:441, stdout PIPE, never drained until stop_proc); they run lead_desk.server, a few lines of output. No run stalled, so there is no stack inside a pipe read; I did not measure bytes written.

## 6. Wait table (READING ONLY, NOT PROOF; tests/test_hung_adapter_calls.py = T, src/lead_desk = S)
| where | what | bound |
|---|---|---|
| T:25 SHORT | real-time call deadline in tests (monkeypatched CALL_DEADLINE_MAX_SECONDS) | 0.5 s, load-sensitive: a worker thread must finish or be cut within 0.5 s |
| T:43-49 wait_for | polling helper `time.sleep(0.02)` until condition | 10 s default; used in the reaper tests; returns False after 10 s (then assertion fails, no hang) |
| T:76, 98, 104, 685 | HangCrm/Hangs/other stand-in `release.wait(8)` | 8 s cap, released by test in `finally` |
| T:138,141,158,161,176,178,576 | wait_for for reaper to record error / send other lead | 10 s (T:576 stop test 10 s); under CPU load the reaper pass (0.05 s interval, deadline 0.5 s) must fit in 10 s |
| T:372 gate_open.wait(8); T:377 Barrier(timeout=15); T:394 t.join(15) | threaded burst | 8 s / 15 s / 15 s |
| T:573 stop_background(timeout=0.2), assert < 1.2 s | stop returns by its own timeout; CALL_DEADLINE 1.5 s there | 0.2 s join; 1.2 s assertion is wall-clock load-sensitive |
| T:805, 830, 862 gate.wait(5); T:812, 838, 870 started.wait(5); T:816, 842, 874 slow.join(5) | refresh races | 5 s each |
| S:desk.py:1490 `call.done.wait(budget)` | the desk waits for the hung adapter call (daemon worker thread) | budget = _call_deadline() = min(send_timeout, CALL_DEADLINE_MAX 9 s); bounded. The worker itself is not killed (daemon, abandoned) |
| S:desk.py:630 `thread.join(timeout)` in stop_background | stop waits for reaper | BUSY_WAIT_SECONDS*2 default (10 s if busy wait 5 s), 0.2 s in T:573 |
| S:desk.py:652-654 `while older.is_alive(): older.join(0.05)` | a new reaper waits for older reapers | **UNBOUNDED loop**, exits only when the older thread ends or `stop` is set |
| S:desk.py:655 `while not self._started.wait(0.05)` | reaper waits for startup() | **UNBOUNDED**, exits only when started or `stop` set |
| S:desk.py:664 `stop.wait(interval)` | pause between passes | interval (0.05 s in tests) |
| S:desk.py:725, gate.py:35 REAPER_PASS_SECONDS | pass time budget | 10 s of real time per pass (may overrun by one drive: up to 3 bounded calls of 9 s) |
| S:desk.py:643 finally `self.close()` | reaper closes its DB handle at end | no explicit bound read (SQLite busy handling lives in db.py/gate.py: FairSemaphore/WriteGate `ticket.wait(timeout)` at gate.py:112, 157, caller-given timeouts) |
| S:adapters.py:70 `_OPENER.open(req, timeout=timeout)` | real HTTP exchange (not executed in this file) | per-call timeout, per read (not a total) |
| S:server.py listen | request_queue_size = 1024 (constants.py:46); the OS caps it (somaxconn 4096) | not used by this file |
Not read in full: gate.py wait internals, db.py busy timeout, test fixtures in tests/conftest.py and support.py. This table is a reading, not proof: no wait was seen unbounded in any run.

## 7. What was NOT checked
Playwright runs (lane 1 had Playwright installed; a hang near test 840 there could involve browser tests or a different ordering (random order / `--cov` / xdist) that I did not reproduce); other lanes' containers' memory counters; runs with more than 2 busy loops or more concurrent pytest processes; Python/pytest versions on lane 1/4 vs this venv; whether the full run on lane 4 used `--cov` (the other lane's pytest here does, I did not run with `--cov`).
Processes: all mine stopped (yes loops killed by trap, pgrep empty; no batch/rss.py left). Other lanes' pytest (pid 5362) untouched.
