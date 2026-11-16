# EVIDENCE RUNNER report, Q8a-2 head 3210f93acfcde2eb388a2b9b4f2fbdee641f5b04 (fix batch 3)

Raw numbers only, no verdict. Real clock 16:57 to 17:21 UTC (22:27 to 22:51 IST), about 24 min. Machine load average 2.7 to 5 on 4 cores during the runs (other agents), so timings are not quiet-machine numbers. Clean worktree /home/user/build/EV-Q8a2-r4 (clean after all runs, 0 changed files). Own PostgreSQL 16 on 127.0.0.1:56644, started with PGHOST and PGPORT in the server's environment (checked in /proc), stopped at the end. Nothing committed or pushed.

## Read first: what failed or did not go as planned
1. First full-suite log is damaged. Run 1 exited 0, but its log `full1-LOG-TRUNCATED-at-8396-bytes.log` stops at 68% with no summary line. The file stopped changing at 17:03:01 while pytest ran until 17:06:34, so something replaced the file; I do not know what. The same happened to my first two attempts at step 7 (plants), which stopped after 10 and after 4 plants although the exit code was 0. Cause not found. I re-ran step 7 and the full suite writing to a folder outside the repo (/home/user/build/evidence-raw/Q8a2-r4) and copied the files afterwards; those runs are complete. So there are TWO full runs, not one. Run 1's junit XML is complete and agrees with run 2.
2. Fail-before differs from the last report: with this head, `tests/test_q8a2_callback.py` does not even collect on main (module-level `defaults.RECEIVER_READ_TIMEOUT_S` is missing on main), so 0 callback tests ran on main. Same for `tests/test_p7_tick.py` (`handle_action` missing). Only the guard file and the capabilities file give pass/fail counts on main.
3. The builder's mutant script /home/user/build/q8a2-fb3/mut.py, run exactly as is, crashes at once: `FileNotFoundError ... /home/user/build/q8a2-fb3/wt-old/src/hadavin_sdk/approvals/receiver.py` (the folder wt-old does not exist). Output: step4b-builder-mut-as-is.txt. I then ran an ADAPTED COPY (scripts/builder-mut-adapted.py; only the worktree path and the runner changed, mutants unchanged) in my own throwaway worktree /home/user/build/EV-Q8a2-r4-mut. The mutated source (receiver.head.py) is byte-identical to this head's receiver.py (cmp). Result below.
4. Step 8: after the 10 s bound (+2 s), 45 of 50 (silent) and 47 of 50 (short body) held connections were seen closed by the test's check, 50 of 50 for partial first line. Last report had 50 of 50 in all three. Threads were back to 3 to 4 (baseline 3) each time. Raw numbers only; I did not investigate. Variant A (serial opening) was not re-run: only variant B's script was kept.
5. Server stderr in the hostile run: 6 lines, no tracebacks; one of them is at ERROR level: `a request ended with an error: ConnectionResetError while handling AttributeError` (client reset right after a correctly signed click with store None). Same count as last time.
6. Secret-shaped strings found in the junit files (test ids from existing tests, not in this branch's diff, 0 hits in the diff): `AKIA<masked-test-id>` (test_no_hardcoded_values plant id), `AKIAQWERTYUI...` (a redaction test id), `sk-ant-api03-<masked>` (redaction class test id). The allowed literal `AKIA<masked-test-id>` also appears. Files: full1-junit.xml, full2-junit.xml. The lead should decide if the junit files may be committed.
7. Not run: CI, CodeQL, SonarCloud, CodeRabbit; real-store signed approval over the socket for the Slack kind (the real-store fixture builds the fake kind only); the merge with the Q8a-1 branch; variant A of step 8; the diff was not reviewed.

## Table (every test command ran under the env -u list from the brief; heavy ones through heavy.sh)

| # | what | exit | result | file |
|---|---|---|---|---|
| 1 | head sha, `git status --porcelain` | 0 | 3210f93acfcde2eb388a2b9b4f2fbdee641f5b04, clean; origin/main 2a8c2aac | step1-head.txt |
| 1a | ruff check | 0 | All checks passed | ruff-check.log |
| 1b | ruff format --check | 0 | 323 files already formatted | ruff-format.log |
| 1c | bandit -ll -r src tools (throwaway `uv run --with bandit`) | 0 | No issues identified (Low 12, Medium 0, High 0) | bandit.log |
| 1d | tools/scan_repo.py | 0 | no output | scan-repo.log |
| 1e | grep of added diff lines for noqa / nosec / type: ignore | 1 (no match) | 0 hits | suppress-hits.txt |
| 1f | gitleaks detect, log-opts origin/main..HEAD (8 commits) | 0 | no leaks found | gitleaks.log |
| 2 | tests/stage_mutants.py (35 s) | 0 | 37 of 37 good; problems: [] | stage-mutants.log, mut-meta.txt |
| 2b | builder mut.py as is | 1 | FileNotFoundError (item 3) | step4b-builder-mut-as-is.txt |
| 2c | builder mut.py adapted copy, 8 mutants, callback file with -x | 0 | 8 of 8 KILLED (hungup_never, hungup_always_for_conn, message_added, level_error_to_debug, log_raw, no_cut, bool_ok, no_max); each ended "stopping after 1 failures" (a real test failure, not a collection error); worktree clean after; unmutated callback file in that worktree: 106 passed | step4b-builder-mut-adapted.txt, step4b-baseline-in-mut-worktree.log |
| 3 | fail-before, head's test files over main 2a8c2aac (src from main, verified import path) | see below | see below | step5c-* |
| 4a | full pytest run 1 `-m "not live and not perf" -rfEs` (367 s) | 0 | junit: tests=10803, failures=0, errors=0, skipped=1; log truncated (item 1) | full1-junit.xml, full1-meta.txt, full1-LOG-... |
| 4b | full pytest run 2, same command, log outside repo (378 s) | 0 | `10802 passed, 1 skipped, 28 deselected in 375.53s`; skipped: tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape); 0 failures | full2.log, full2-junit.xml, full2-meta.txt |
| 5 | hostile matrix (scripts/hostile.py, same as last time), fake and Slack kinds, read_timeout_s=2.0 | 0 | every status line identical to the f6c2a3d run (only ports, temp paths and sub-0.1 s timings differ; diff checked); stderr 6 lines, 0 tracebacks (item 5) | step6-hostile.txt, step6-server-stderr.txt |
| 5b | guard plants (scripts/plants.py): 44 plants (36 Python + 2 GCS table + 6 SQL) | 0 | 40 reported by at least one scan, 4 all-empty: `# slack`, a docstring naming Slack, SQL `-- slack`, SQL `/* slack */` (same four as last time) | step7-plants.txt, step7-summary.txt |
| 5c | 50 held slow connections, 200 silent (scripts/test_evq8a2f_load.py, variant B) | 0 | fast requests all answered 200/401; medians 1.7 to 2.8 ms signed, 0.4 to 0.9 ms bad-signature while 50 held; baseline signed median 13.0 ms; 200 held: signed median 1.3 ms; closed-after-bound counts in item 4 | step8-load-B-parallel-open.txt |
| 6 | tests/test_q8a2_callback.py three times, machine loaded | 0,0,0 | 106 passed each; 21.96 s, 22.07 s, 21.78 s (wall 22.65, 22.61, 22.37 s); slowest tests 1.2 s, 1.1 s, 1.0 s; load average at start in step9-meta.txt | step9-callback-run1..3.log, step9-meta.txt |
| 7 | wall clock | | 16:57:20 to 17:21:04 UTC | |

### Fail-before detail (main 2a8c2aac, head's test files copied over; each file run alone, then all four with --continue-on-collection-errors)
- tests/test_q8a2_callback.py: exit 2, collection error, 0 tests ran (`AttributeError: module 'hadavin_sdk.defaults' has no attribute 'RECEIVER_READ_TIMEOUT_S'`).
- tests/test_lockin_guard.py: exit 1, 29 failed, 197 passed.
- tests/contracts/test_capabilities.py: exit 1, 2 failed, 41 passed.
- tests/test_p7_tick.py: exit 2, collection error, 0 ran (`cannot import name 'handle_action'`).
- all four with --continue-on-collection-errors: exit 1, 31 failed, 238 passed, 2 errors.
- main worktree restored (dirty-after 0). Files: step5c-meta.txt, step5c-*.log, step5c-*-junit.xml.

## Cleanup
My PostgreSQL stopped. No background process of mine left. Worktrees left on disk: /home/user/build/EV-Q8a2-r4, /home/user/build/EV-Q8a2-r4-main, /home/user/build/EV-Q8a2-r4-mut (all clean). Venv /home/user/build/venv-evq8a2r4. Checkpoint note /home/user/build/EV-Q8a2-r4-checkpoint.md. Scripts in scripts/ (env.sh, full*-inner.sh, fb2-inner.sh, hostile.py, plants.py, test_evq8a2f_load.py, builder-mut-adapted.py).
