# Reader report: E3b "three cut runs" (read-only, facts only)

Read on 2026-11-14. Nothing was run (no pytest). Sources: FREEZE.md:24, register.md:170 (E3b row), REPORT.md (E3b rows), ORDERS.md (12:58Z order, lines 73-77), evidence/lane3-fix-1-r2-evidence.md, evidence/raw/progress-E3b.txt, the three logs, and the original run folder /home/user/work/e3b-logs/ (still on disk).

## 0. A correction of the question's premise
The three E3b logs do NOT end at the same mark. They end at 86%, 5% and 67%. The "same mark" story (2938 bytes, ~71-72%) belongs to the older A runs (REPORT.md:886), not to E3b. The E3b logs also end with an `EXIT_CODE=` line and, for runs 1 and 3, a full pytest summary line, so they are not truncated copies; the pytest run itself stopped.

## 1. The three logs (all in evidence/raw/, tree f3c39cf8 + lane3-fix-1 round-2 patch, Python 3.12.3, pytest 9.2.0)
Run numbers follow evidence/lane3-fix-1-r2-evidence.md:11-13.

| run | repo file | bytes | lines | last test line (verbatim) | summary / exit |
|---|---|---|---|---|---|
| 1 | fix1-full-run1-interrupted.log | 378125 | 3436 | `tests/test_server_hardening.py::test_huge_item_id_is_not_500[retry-O9999999999999999999] PASSED [ 86%]` (line 3414) | `3196 passed, 184 skipped in 1114.81s`, EXIT_CODE=2 WALL_SECONDS=1115 |
| 2 | fix1-full-run2-sigterm.log | 22292 | 212 | `tests/test_crm_hubspot.py::test_429_uses_the_backoff_without_retry_after_and_gives_up_busy PASSED [  5%]` | no summary; EXIT_CODE=143 WALL_SECONDS=107 |
| 3 | fix1-full-run3-interrupted.log | 288112 | 2690 | `tests/test_portal_demo.py::test_burst_http_protocol_errors[cut_chunked-IncompleteRead] PASSED [ 67%]` (line 2671) | `2584 passed, 56 skipped in 742.47s`, EXIT_CODE=2 WALL_SECONDS=743 |

Last 3 lines verbatim:
- Run 1: `================ 3196 passed, 184 skipped in 1114.81s (0:18:34) ================` / (empty line) / `EXIT_CODE=2 WALL_SECONDS=1115`. Just above them: `!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!` then `/home/user/work/e3b-fix1/src/lead_desk/server.py:1086: KeyboardInterrupt` then `(to show a full traceback on KeyboardInterrupt use --full-trace)` (lines 3431-3433).
- Run 2: `tests/test_crm_hubspot.py::test_5xx_is_unclear_and_the_retry_is_safe[r5xx_after_store] PASSED [  5%]` / `tests/test_crm_hubspot.py::test_429_waits_the_named_seconds_then_succeeds PASSED [  5%]` / `...test_429_uses_the_backoff_without_retry_after_and_gives_up_busy PASSED [  5%]` then the EXIT_CODE line (the tail printed in my read ended: `...gives_up_busy PASSED [  5%]`, `EXIT_CODE=143 WALL_SECONDS=107`).
- Run 3: `================= 2584 passed, 56 skipped in 742.47s (0:12:22) =================` / (empty) / `EXIT_CODE=2 WALL_SECONDS=743`. Same KeyboardInterrupt lines as run 1 at lines 2685-2687.

Test counts: 0 FAILED and 0 ERROR lines in any of the three (grep for `FAILED|ERROR` found only test names containing "Error" in ids).

## 2. Where the line that raised is
Both KeyboardInterrupt stops (runs 1 and 3) point at the same source line: `src/lead_desk/server.py:1086`. In the tree /home/user/work/e3b-fix1 that line is the body of `_on_sigterm`: `raise KeyboardInterrupt` (server.py:1082-1086; docstring: "SIGTERM stops the desk the same way Ctrl+C does"). `main()` installs a handler for SIGTERM and SIGINT (server.py:1189-1192). So: in runs 1 and 3 a SIGTERM (or SIGINT) arrived at the pytest process while a desk handler from `main()` was installed in that same process, and pytest saw a KeyboardInterrupt and stopped with exit 2. Run 2 ended exit 143 (= 128 + 15, SIGTERM with default action), at 5%, in test_crm_hubspot, where no such handler was in place. This is the fact set; who sent the signal is not in the files (section 5).
Fact about the tests: tests/test_stall_eviction.py:354-448 and several others raise or call the handler on purpose (`tests/test_claim_checks_and_crm_mode.py:136`, `test_server_main_reaper.py:27`, `test_sonar_p2_gaps.py:213`), but these appear as test code that raises KeyboardInterrupt inside the test, and a pytest stop from such a test would not print server.py:1086; I did not trace them further.

## 3. How and when the runs were started (from /home/user/work/e3b-logs/, same bytes as the repo copies)
- Run 1 came from `run.sh` (line `TMPDIR=$T timeout 2400 $PY -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$T/btfull > $L/$t-full.log 2>&1`; loop over `fix1` then `stack`, logs in `/home/user/work/e3b-logs`, i.e. OUTSIDE the repo trees). Times: progress-E3b.txt says full start 13:18:11Z; 1115 s wall gives end about 13:36:46Z (log mtime 13:36). The stack run followed in the same script: 3692 passed, 200 skipped, 1140.95 s, EXIT_CODE=0 (stack-full.log; log mtime 13:55; done.flag 13:55).
- Run 2 and run 3 came from `run2.sh` (same pytest command, `--basetemp=$T/btfull2`, log written to e3b-logs/fix1-full.log). progress-E3b.txt: "fix1 rerun start 13:56:04Z". Run 2 (107 s) is dated about 13:56-13:57 (log mtime 13:57); the file name fix1-full-run2-sigterm.log was renamed afterwards, and the e3b-logs copy of run 2 is 22292 bytes, so run 2 was a start of run2.sh that was killed and the same script was started again. Run 3 ended about 14:10 (log mtime 14:10, done2.flag 14:10, 743 s wall). That the second start is "run 3" is by file dates and the evidence table; the exact restart time is not written anywhere.
- The three logs were copied into handover/ in commit ad27aa17 (2026-11-13T14:12:35Z, "lane3: E3b closed (stale r2 evidence, cut runs recorded)"). sha256 of the repo copies equals the e3b-logs copies for runs 1 and 3 (checked prefix b6a68857... and 242497cb...; run 3's source name is e3b-logs/fix1-full.log).
- None of the E3b raw logs was ever in a git-tracked folder while pytest wrote it (logs in /home/user/work/e3b-logs; the first handover commit that has them is ad27aa17, after the E3b close). `git log -- handover/demo3` shows E3b's progress-E3b.txt in several heartbeat commits (11105527 13:17Z, 3ad1d08c 13:18Z, 3abd7881 13:56Z, ad27aa17 14:12Z) but not the logs.

## 4. Git during the runs (ORDERS 12:58Z, point 2)
- The 12:58Z order asked for "log outside the repo, no git command touching the tree". E3b's brief (REPORT.md:531, :555) says the files were `git add`ed before the tests (done before 13:18:11Z). The worktree e3b-fix1 `git reflog` shows only the one entry `HEAD@{0}: f3c39cf` (no commit, reset, checkout or rebase in the tree after creation); `git log` HEAD is f3c39cf. I cannot see a git command that ran in /home/user/work/e3b-fix1 during the runs, but a read-only or `status`/`add` command leaves no reflog trace, so "no git command" is not proven (silent).
- The mechanism proven for the older A/D/C2 logs (git replacing a tracked log, `(deleted)` fds, REPORT.md:886) does not fit E3b: the E3b logs were outside git, end in a pytest summary or an exit line with a signal, and differ in end position. The git-cut hypothesis is REFUTED for E3b by the files (logs outside repo, KeyboardInterrupt/143 signature, three different stop points).
- The parent repo commits at 13:17Z-14:12Z (lead's commits to handover/) touched files in /home/user/hadavin-sdk, not /home/user/work/e3b-fix1; this is by path, and the two folders are separate trees.

## 5. Hypotheses tested by reading
| hypothesis | verdict | basis |
|---|---|---|
| A. git touched the log (the old A-run cause) | REFUTED | logs outside repo (run.sh L=/home/user/work/e3b-logs); ends differ; exit lines are intact |
| B. a git command touched the test tree during the runs | SILENT (not shown, not excluded) | reflog has only the creation entry; `git add` before run is recorded; read-only git leaves no trace |
| C. all three stop at the same mark | REFUTED | 86%, 5%, 67% (three different last test lines) |
| D. the tests themselves failed or hit the 2400 s timeout | REFUTED | 0 FAILED/ERROR; `timeout 2400` would give exit 124 and runs lasted 1115, 107, 743 s |
| E. an outside signal reached the pytest process (SIGTERM, or SIGINT) | SUPPORTED | exit 143 in run 2; server.py:1086 `_on_sigterm` is the raising line in runs 1 and 3 (a handler installed by the desk's `main()` in the pytest process turns SIGTERM into KeyboardInterrupt) |
| F. the signal came from another agent's kill by name (pkill -f) | SILENT | no pkill/killall found in handover/demo3/tools, scratch, REPORT, register, ORDERS (grep); other agents' shell history is not on disk |
| G. the signal came from the crash-soak tools (Q3b/Q3c) killing a stale or reused pid | SILENT | Q3b ran 12:49Z-~13:40Z, Q3c 13:03Z-~14:00Z (register.md:60, :85), overlapping runs 1 (13:18-13:36) and 2 (13:56-13:57); tools/q3-soak.py:149-166, q3b-soak.py:153-170, q3c-soak.py:151-168 use `os.kill(<recorded pid>, SIGKILL/SIGTERM)` with pids they spawned; no file records a pid collision or a kill of a pytest pid |
| H. a test in the suite sends the signal to its own process or group | SILENT | `grep` finds `p.terminate()` (tests/support.py:553, test_smtp_outbox.py:66) and handler calls in test_stall_eviction.py, no `os.kill`/`killpg` in tests/; not traced to an actual send |
| I. a CPU or memory kill (out-of-memory killer) | SILENT | no dmesg/OOM text in the files; free RAM about 8 GB at 13:16Z (REPORT.md:584); an OOM kill would be SIGKILL (137), not 143 or KeyboardInterrupt |
| J. run 2 stopped at 5% by the runner's own cleanup of an earlier script | SILENT | register.md:170 says only "cause UNKNOWN (likely another process)" |

## 6. Later valid runs covering the same ground
- Same tree (e3b-fix1, round-2 patch): no later complete run. The E3b table says so itself (evidence/lane3-fix-1-r2-evidence.md:3 and :21: "fix1 full total NOT proven as one run: run1 + tail cover everything ... Next step: rerun fix1 full alone"). The tail run `fix1-tail.log` (18 test files from test_server_hardening.py to the end): `512 passed, 16 skipped in 93.81s (0:01:33)`, EXIT_CODE=0 WALL_SECONDS=95; this plus run 1 is a union, not one run.
- Same patch on the claims-stack tree: `stack-full.log` (evidence/lane3-fix-1-r2-evidence.md:15; e3b-logs copy) last summary: `================ 3692 passed, 200 skipped in 1140.95s (0:19:00) ================` then `EXIT_CODE=0 WALL_SECONDS=1142`. Valid and complete, but a different tree (claims stack added). Hygiene on both trees: 20 passed, 4 skipped.
- Same ground, other heads: Q1 serial full run on f3c39cf8, log outside the repo: `3683 passed, 200 skipped, 0 failed, 1295.23 s, exit 0` (REPORT.md:770). E3 round 1: 3692 passed, 0 failed, 200 skipped (REPORT.md:601). Later full runs on later patches: fix-1 r6 `3716 passed 200 skipped rc 0` (register.md:211, raw/b1f-full.log); fix-2 r4 `3809 passed, 237 skipped, rc 0` (REPORT.md:319). These cover the same code areas but later code, not the E3b tree at round 2.
- register.md:170 closes E3b as STALE, superseded by r4/r5 runs; "no rerun for r2".

## 7. What the evidence cannot tell
1. Who or what sent the SIGTERM/SIGINT to the pytest processes (no sender is recorded; no process list, dmesg or audit log).
2. Which test was running at the moment of each stop (the last printed line is the last finished test; -v prints a name after it finishes). Next tests in order, from stack-full.log: after run 1's last line, `test_huge_item_id_is_not_500[retry-F99999999999999999999]`; after run 3's, `test_state_http_protocol_errors[garbage_status]`; after run 2's, the rest of test_crm_hubspot (in the order printed by the stack log). Whether a desk `main()` test held the handler at that moment is not shown.
3. Whether a git command (even read-only) ran in /home/user/work/e3b-fix1 during runs 1-3.
4. The exact start time of run 3 (between 13:57 and 14:10 by file dates) and the exact end time of run 2.
5. Whether the signal for run 2 (exit 143, no handler) and for runs 1 and 3 (handler) had the same sender; they share only "outside signal" by exit code and code line.
6. Whether runs 1 and 3 overlapped other agents' soak/kill tools in time in a way that matters (overlap exists on the clock, no causal link is recorded).
7. Whether the xdist-time `COLUMNS` finding (REPORT.md:574) or other known causes relate: not mentioned in any E3b file; no link.
8. Whether the repo's own tests (test_stall_eviction, test_server_main_reaper) can raise SIGTERM at the pytest process: not traced.
