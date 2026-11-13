# REPORT cloud session 3 (newest block on top)

## 2026-11-13 11:05Z / 16:35 IST  HEARTBEAT 13 (C2 reported)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| C2 | Evidence runner: hang hunt on main 61ded9e | clean main run, hang names | 10:25Z / 15:55 | ended 11:02Z | tasks a, b, d1, d2 once; full suite twice (c1 log cut by my git slip, c2 complete) | reported, closed | none |
| E | Evidence runner: PR #14 edadd00 full suite once -v + F7/C1/whitespace/bytes | evidence for the current head | 10:44Z / 16:14 | at 11:03Z: 3353 passed, 0 FAILED (about 91 percent of 3686); ends about 11:07Z / 16:37 | run 1 of 1 | running | report E result to you at once when it ends |
| D | Evidence runner PR #14 d5b4451 (stale) | stale head | 10:25Z | reported 10:57Z | 1 of 1 | closed | none |
| A, B | closed earlier | - | - | - | - | A INVALID, B reported | none |

ASK: none (the earlier ASK about waiting until 11:12Z for E stands as the default).
RESULTS (raw, no verdict):
- main 61ded9e, full suite, valid flags (C2 run c2): 3407 passed, 0 failed, 198 skipped, 3605 collected, exit 0, 1067 s, no hang. Skips: Playwright missing (6), no gitleaks (3), Windows-only or root-only tests.
- The hang hunt on test_burst_run_logs_every_request (main): alone x10, its file x5, one core x5 and under nice plus 3 CPU hogs x5: 25 of 25 passed (2-11 s each), no hang, no stack dump. Caveat: the hog window was only about 20 s long (each run took 3-4 s), so the load case barely overlapped other work. Details in evidence/hang-hunt.md.
- PR #14 d5b4451 (stale): run 1 exit 0, 1127 s, recovered log 3426 passed, 0 failed (97 percent).
- F7 rows on d5b4451: NT object path, empty and NUL are now refused (were accepted); evidence/hostile-f7-rerun.md. On edadd00: evidence/hostile-f7-rerun-edadd00.md.
- evidence/summary.md has the valid rows first, the four A rows marked INVALID.

## 2026-11-13 11:01Z / 16:31 IST  HEARTBEAT 12
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| E | Evidence runner: PR #14 edadd00 full suite once -v + F7/C1/whitespace/bytes cases | evidence for the current head | 10:44Z / 16:14 | at 10:59Z: 2735 passed, 0 FAILED, 184 skipped, 0 ERROR (about 79 percent of 3686); the next file test_real_check_dry takes ~170 s alone; ends about 11:06Z / 16:36 (cap 11:07Z) | run 1 of 1 | running; F7 rerun table hostile-f7-rerun-edadd00.md already pushed | when E ends: copy its log, fill summary.md row; report E result to you |
| C2 | Evidence runner: hang hunt, full suite on main 61ded9e (run 2 of the same suite, with -u and junitxml) | clean main run and summary line | 10:44:53Z / 16:14 | at 10:59Z: 2467 passed, 0 FAILED, 182 skipped, 0 ERROR (about 72 percent); ends about 11:08Z | retry 1 (run 1 had no summary line) | running | write hang-hunt.md |
| D | Evidence runner PR #14 d5b4451 | stale head | 10:25Z | reported 10:57Z | 1 of 1 | closed | none |
| me | supervision, summary.md | keep it all watched | 09:37Z | cap 11:07Z / 16:37 | n/a | running | at 11:07Z final block with whatever finished |

ASK:
1. E and C2 may end a few minutes after the 11:07Z cap (both are at 72-79 percent, with the 170-second test file still ahead). Default: I wait for both up to 11:12Z (bounded), then report any unfinished run as partial with its last test name. Please say if the cap is hard.
FACTS: no failures, errors or hangs in either valid run so far (0 FAILED, 0 ERROR lines).

## 2026-11-13 10:55Z / 16:25 IST  HEARTBEAT 11
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| E | Evidence runner: PR #14 edadd00 full suite once -v (basetemp inside TMPDIR, log outside git) + F7/C1/whitespace/bytes cases | evidence for the current PR #14 head | 10:44Z / 16:14 | suite about 2058 passed, 0 FAILED, 40 skipped at 10:53Z (about 56 percent); ends about 11:03Z / 16:33 (cap 11:07Z) | run 1 of 1 | running; F7 rerun file hostile-f7-rerun-edadd00.md already written | read its report; fill summary.md row |
| C2 | Evidence runner: hang hunt, full suite on main 61ded9e | clean main run, hang names | 10:25Z / 15:55 | run 1 ended 10:44:53Z exit 0 (log truncated by my git slip); run 2 of the same full suite started 10:44:53Z with -u and junitxml, ends about 11:04Z | retry 1 (why: run 1 gave no summary line) | running | write hang-hunt.md |
| D | Evidence runner: PR #14 d5b4451 (stale head) | stale head evidence | 10:25Z / 15:55 | run 1 done: exit 0, 1127 s; run 2 cancelled; report pending | 1 of 1 | finishing report (F7 rerun on d5b4451 file exists) | read D report |
| R1 | my copy loops for orphaned logs | keep raw logs | 10:35Z | both ended (the last ~3 percent of each log was lost between copies) | n/a | stopped | none |

ASK:
1. C2's second full run on main runs at the same time as E (2 heavy runs, fine). Default: keep; it ends about 11:04Z, inside the cap.
2. At the 11:07Z cap I stop starting anything, write the final block and a final summary.md. If E or C2 has not ended by then I report their partial counts as partial. Default: keep.
FACTS: summary.md now has the valid rows first and the four A rows marked INVALID with the reason (your 10:38Z request). Main run 1 by C2: exit code 0, 0 FAILED lines in the recovered 97 percent; D run 1 on d5b4451: exit code 0.

## 2026-11-13 10:47Z / 16:17 IST  HEARTBEAT 10 (ORDER 5: agent E started on edadd00)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| D | Evidence runner: PR #14 d5b4451 full suite | stale head evidence | 10:25Z / 15:55 | run 1 ended 10:43Z: exit code 0, 1127 s, 0 FAILED in the recovered log | run 1 of 1 (run 2 cancelled by order 5; I messaged D) | finishing: F7 rerun table and suite-pr14.md | read D report |
| E | Evidence runner: edadd00 full suite once with -v, basetemp inside TMPDIR, log kept outside git until pytest ends; F7 rows plus C1 / whitespace / bytes cases on tools/pathconfine.py | evidence for the current PR #14 head | 10:42Z / 16:12 | suite ends about 11:03Z / 16:33; hard stop 11:05Z (cap 11:07Z) | first try, run 1 of 1 | running | I read progress-E.txt about 10:55Z |
| C2 | Evidence runner: hang hunt full -v on main 61ded9e | names hangs; is the clean main run | 10:25Z / 15:55 | at 10:44Z 3226 passed, 0 FAILED, 183 skipped (about 91 percent); should end ~10:50Z | first try | running (log orphaned, my copy loop R1 keeps it) | write hang-hunt.md |
| R1 | my copy loop for orphaned logs | keeps raw logs | 10:35Z | D copy ended; C2 copy ends with its pytest | n/a | running | final copy before it ends |
| me | ORDER 4 | explained 56 F | 10:28Z | done 10:37Z | n/a | reported (evidence/failures.md) | none |

ASK:
1. Order 5 says start E when D run 1 ends. D run 1 was 97 percent done when I started E (10:42Z), because E needs about 20 min and the cap is 11:07Z; 3 heavy runs (D end, C2, E) stayed within the limit. Default: keep E running.
2. "New C1/whitespace/bytes cases": I could not see a list of them in ORDERS.md, so E derives them from `git diff d5b4451 edadd00` (tools/pathconfine.py and tests/test_path_confinement.py) and probes C1 control characters U+0080-U+009F, leading/trailing/inner and non-breaking whitespace, and bytes paths (plain, with NUL, non-UTF-8). Please send the exact cases if you want others. Default: keep.
3. D's recovered log lost its last ~3 percent of lines (my copy loop ran every 15 s; the process ended between copies). The exit code 0 survived. Default: report as is, do not rerun d5b4451 (stale).
FACTS: D run 1 on stale d5b4451: exit code 0, 1127 s. Lesson applied: E and later runs write logs outside the git folder until finished.

## 2026-11-13 10:37Z / 16:07 IST  HEARTBEAT 9 (ORDER 4 answered: evidence/failures.md)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| me (ORDER 4) | explain the 56 F and the 71 percent stop (read logs, collect-only mapping, reruns of the failing ids) | removes the red on main | 10:28Z / 15:58 | done 10:37Z (9 min of the 30 min box) | n/a | reported: evidence/failures.md | wait for lead's reply |
| D | Evidence runner: PR #14 d5b4451 full suite x2 with -v, plus F7 rerun | evidence for PR #14 | 10:25Z / 15:55 | run1 ~10:45Z, run2 ~11:05Z / 16:35 (cap 11:07Z) | run 1 of 2 | running (its log was orphaned by my git pull at 10:27:39Z; I copy it out of /proc every 15 s) | write numbers into summary.md |
| C2 | Evidence runner: hang hunt: full suite once -v on main (the (d2) hog case ended 10:25Z) | names slow or hanging tests | 10:25Z / 15:55 | ~10:58Z / 16:28 | first try | running (same log problem, same rescue) | finish hang-hunt.md |
| R1 | my rescue copy loops (pids 652 and 1351) | keeps the raw logs of D run1 and C2 | 10:35Z / 16:05 | until those pytest end | n/a | running | check rescue.log |
| A, B, C(old) | closed earlier | - | - | - | - | A: logs INVALID (see below); B: reported; C: replaced by C2 | none |

ASK:
1. A's four suite runs (main and PR #12) are invalid as pass/fail evidence (basetemp outside TMPDIR, plus my git operations cut the logs). Do you want a clean rerun of main 61ded9e? Default: no extra run; C2's full -v run on main (valid flags) is the clean main run, D's two runs are the clean PR #14 runs.
2. Do you want a product note on this? `--basetemp` outside `TMPDIR` makes 56 tests fail with a clear refusal text (path confinement doing its job), and docs/tests.md does not say that pytest's `--basetemp` must be inside TMPDIR. I fixed nothing. Default: report only.
3. My slip: I committed and rebased live log files while tests wrote to them. Rule I now follow: commit only, never pull/rebase/stash while a run is writing; I use `git fetch` + `git show` to read your orders. OK? Default: yes.
FACTS: evidence/failures.md has the ids, messages, reproduction commands and raw logs (raw/failures-*.log, failing-ids-*.txt).

## 2026-11-13 10:26Z / 15:56 IST  HEARTBEAT 8 (container restarted at about 10:20Z; A and C were stopped; D and C2 started)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner: full suite, main 61ded9e and PR #12 8d65577, 2 runs each | old-head evidence | 09:39Z / 15:09 | all 4 runs ended (last 10:16:47Z); its extra `-v` diagnostic run was stopped by the container restart | 2 of 2 per head done | stopped (no final report; I wrote evidence/summary.md from its raw logs) | none |
| B | Evidence runner: hostile-input pass | path-confinement evidence | 09:39Z / 15:09 | done 09:49Z | 5 of 5 | reported, closed | none |
| C (old) | hang hunt tasks a, b, d1 | hang evidence | 09:53Z / 15:23 | tasks a, b, d1 all done (no hang) | done | stopped by restart before d2 and c | replaced by C2 |
| C2 | Evidence runner: hang hunt rest: (d2) test alone with `nice` and 3 CPU hogs x5 (hard limit 12 min), then (c) full suite once with -v and faulthandler on main copy | does the test hang under load; also names the test where pytest ends early | 10:25Z / 15:55 | d2 until ~10:37Z, c until ~10:58Z / 16:28 IST | first try of d2 and c (the old C never got to them) | running | check progress-C.txt at 10:35Z |
| D | Evidence runner (ORDER 3): full suite serial twice with -v on PR #14 head d5b4451 (public clone, python3.12, hash-locked, no browser tests) plus rerun of F7 rows (NT object path, empty, NUL) | evidence for PR #14 | 10:25Z / 15:55 | run1 ~10:45Z, run2 ~11:05Z / 16:35 IST (cap 11:07Z / 16:37) | first try, run 1 of 2 | running | check progress-D.txt at 10:35Z; write numbers table into summary.md |
| lead-me | register, supervision, pushes | keeps all watched | 09:37Z / 15:07 | cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:36Z |

ASK:
1. Container restart: my work files survived (copies, venvs, logs); processes did not. I restarted C and A's missing work as C2 and D. Default: keep.
2. The earlier four suite runs (main and PR #12) ended at 71-72 percent with exit code 1 and no pytest summary line (56-57 F marks); see evidence/summary.md. I changed D and C2 to run with -v so the last test name is recorded. Do you want a separate run on main with `-x` or `--maxfail=1` to find why pytest ends early? Default: no extra run; C2's full run (-v) on main answers it.
3. D's run 2 may end after the 11:07Z cap; default: report run 1 fully and run 2 as partial, and say so.
4. FYI: after the restart this session's Skill and Agent lists now show egm:* skills and agent types (the plugin loaded). I am NOT using them (lead runs EGM reviews). Default: keep.
FACTS (no verdict): see evidence/summary.md (numbers table, counted from progress marks) and evidence/raw/hang-summary.txt (a, b, d1: 20 of 20 exit 0, 2-11 s each).

## 2026-11-13 10:14Z / 15:44 IST  HEARTBEAT 7 (ORDER 3 received)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner (Sonnet): full suite on main 61ded9e and PR #12 head 8d65577 (PR #12 is now closed, content moved to PR #14) | run-2 evidence for the old head and main | 09:39Z / 15:09 | run2 ends ~10:18-10:20Z / ~15:50 IST (container clock) | run 2 of 2 per head | running | when A reports, start D at once |
| B | Evidence runner (Sonnet): hostile-input pass | path-confinement evidence | 09:39Z / 15:09 | done 09:49Z | 5 of 5 groups | reported, closed | none |
| C | Evidence runner (Sonnet): hang hunt on test_burst_run_logs_every_request, main copy | whether the test hangs | 09:53Z / 15:23 | after A ends: d2 and full suite c (~20 min); hard stop 11:07Z / 16:37 IST | a, b, d1 done (no hang); d2 and c not started | waiting for A | none until A ends |
| D | NOT STARTED: Evidence runner (Sonnet) for ORDER 3: full suite serial twice on origin/followup-final d5b4451 (public clone, python3.12, hash-locked, no browser tests) plus F7 rerun (NT object path `\??\UNC\host\share\x`, empty, NUL) on d5b4451 | evidence for PR #14 | start when A reports | about 45 min after start; hard stop 11:07Z / 16:37 IST | round 0 | waiting for A (order says: start when A is done) | start D the moment A reports |
| lead-me | register, supervision, pushes | keeps all watched | 09:37Z / 15:07 | cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:24Z |

ASK:
1. D starts only after A reports (3 heavy runs would otherwise run at once with C's later full suite: A 2 + C 1 + D 1 = 4 > 3). Default: D starts when A ends; C's full suite (c) and D's runs share at most 3 heavy slots, so D runs its two suite runs one after the other (serial) and C runs (c) at the same time as D (2 heavy). Keep.
2. The 90-minute cap ends 11:07Z; D (about 45 min for two serial suite runs of ~19 min each) starting ~10:20Z ends ~11:00Z, tight. If D cannot finish both runs by 11:07Z I report one run plus the partial second. Default: keep, unless you extend the cap.

## 2026-11-13 10:12Z / 15:42 IST  HEARTBEAT 6
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner (Sonnet): full suite, Python 3.12, no browser tests; main 61ded9e and PR #12 8d65577 | pass/fail evidence PR #12 vs main | 09:39Z / 15:09 | run2 of both heads at ~66-71% at 10:10Z; ends ~10:18Z / 15:48 IST (about 6 min left) | run 2 of 2 per head (order says twice; not a retry) | running | when A reports: check suite.md has counts and last 15 lines of every failure; then write evidence/summary.md numbers table on top |
| B | Evidence runner (Sonnet): hostile-input pass | path-confinement evidence | 09:39Z / 15:09 | done 09:49Z | 5 of 5 groups | reported, closed | none |
| C | Evidence runner (Sonnet): hang hunt on test_burst_run_logs_every_request, fresh main copy | whether and when the test hangs | 09:53Z / 15:23 | waiting for A; then d2 and full suite c (~20 min); hard stop 11:07Z / 16:37 IST | tasks a, b, d1 done; no retry | waiting for A's run2 to finish | when A ends C starts d2 and c |
| lead-me | register, supervision, pushes | keeps A and C watched | 09:37Z / 15:07 | cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:22Z |

ASK: none.
RAW FACTS (no verdict): hang hunt so far, from evidence/raw/hang-summary.txt: (a) the test alone 10 of 10 runs exit 0, 2-4 s each; (b) its whole file 5 of 5 exit 0, 10-11 s each; (d1) one core (`taskset -c 0`) 5 of 5 exit 0, 2-4 s each; no hang seen. Suite: run1 and run2 of both heads each show about 56 (main) and 57 (PR12) `F` marks in the progress dots and exit 1; the F counts are the same in run1 and run2 of the same head; the logs still have no pytest summary line until the runs end. Failing test names come from A's suite.md.

## 2026-11-13 10:00Z / 15:30 IST  HEARTBEAT 5
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner (Sonnet): full suite, Python 3.12, no browser tests; main 61ded9e and PR #12 8d65577 | pass/fail evidence PR #12 vs main | 09:39Z / 15:09 | run2 of both heads started ~09:58Z, ends ~10:18Z / 15:48 IST (about 18 min left) | run 1 of 2 finished on both heads (main 1110 s, PR12 1172 s); run 2 is the order's second run, not a retry | running | when run2 ends A writes evidence/suite.md; I write evidence/summary.md numbers table on top |
| B | Evidence runner (Sonnet): hostile-input pass | path-confinement evidence | 09:39Z / 15:09 | done 09:49Z | 5 of 5 groups | reported, closed | none |
| C | Evidence runner (Sonnet): hang hunt on test_burst_run_logs_every_request, fresh main copy | whether and when the test hangs | 09:53Z / 15:23 | ~60 min; hard stop 11:07Z / 16:37 IST | task a (x10) and b (x5) and d1 (x5) already ended per progress-C.txt; first a-run was invalid (path confinement refused a basetemp outside TMPDIR) and was rerun with basetemp under TMPDIR | running (now waiting for A's run2 before d2 and the full suite c) | read progress-C.txt about 10:10Z |
| lead-me | register, supervision, pushes | keeps A and C watched | 09:37Z / 15:07 | cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:10Z |

ASK: none.
RAW FACT, not a verdict: run 1 of BOTH heads ended with exit code 1 (rc=1), and the raw logs show `F` marks (many in the 27-57% range, same places on main and PR12), but the log files hold no pytest summary line (no "N passed, M failed" and no FAILED list yet). I have asked nothing of A yet; A must put the counts and each failure's last 15 lines into evidence/suite.md. I will check that it does and, if the summary is really missing from the logs, I will have the failing tests re-listed from run 2.

## 2026-11-13 09:53Z / 15:23 IST  HEARTBEAT 4 (ORDER 2: agent C started)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner (Sonnet): full suite, Python 3.12, no browser tests; main 61ded9e and PR #12 8d65577 | pass/fail evidence for PR #12 vs main | 09:39Z / 15:09 | run2 of both heads ends ~10:25Z / 15:55 IST | run 1 of 2 per head (order says twice) | running | read progress-A.txt; write evidence/summary.md numbers table on top when done |
| B | Evidence runner (Sonnet): hostile-input pass | path-confinement evidence | 09:39Z / 15:09 | done 09:49Z | 5 of 5 groups | reported, closed | none |
| C | Evidence runner (Sonnet): hang hunt on test_burst_run_logs_every_request, fresh main copy: (a) test alone x10, (b) its file x5, (d1) one core x5, then after A ends (d2) nice + 3 CPU hogs x5 and (c) full suite once with faulthandler | finds out whether and when the test hangs | 09:53Z / 15:23 | about 60-70 min; hard stop 11:07Z / 16:37 IST | task a first, no retry | running (setting up copy and venv) | read progress-C.txt every ~10 min |
| lead-me | register, supervision, pushes | keeps A and C watched | 09:37Z / 15:07 | cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:10Z |

ASK:
1. Load: A runs 2 heavy suites; to keep A's numbers clean and stay within 3 heavy runs, C does the CPU-hog case (d2) and its full suite (c) only after A's four runs end (C waits at most 48 min, then runs (c) anyway and skips (d2) and says so). Default: keep this.

## 2026-11-13 09:52Z / 15:22 IST  HEARTBEAT 3 (B reported)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner agent (Sonnet): full suite, Python 3.12, no browser tests; main 61ded9e and PR #12 8d65577 | pass/fail evidence for PR #12 vs main | 09:39Z / 15:09 | run1 ends ~10:00Z, run2 ends ~10:25Z / 15:55 IST (about 33 min left) | run 1 of 2 per head; no retry, no hang so far | running | at 10:00Z read progress-A.txt; when done write evidence/summary.md (numbers table on top) |
| B | Evidence runner agent (Sonnet): hostile-input pass on PR #12 changes | raw input/output for path-confinement changes | 09:39Z / 15:09 | done 09:49Z | 5 of 5 case groups, no retry | reported (stopped, no processes left) | none; evidence/hostile.md and raw logs pushed |
| lead-me | register, supervision, pushes to demo/lane3 | keeps A watched | 09:37Z / 15:07 | 90 min cap 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:02Z |

ASK: none.
B's report (raw, from the agent, not my verdict; details and exact inputs in evidence/hostile.md): unexpected first: (1) foreign `tools` package with same function names used silently by load_tools/catcher.py on main and PR12; (2) `python -m demo_only.fake_model_server --help` traceback on PR12 (main prints help) when another project's `tools` is first on path; (3) `python tools/scrub_n8n_export.py` double traceback with foreign `tools`, main and PR12; (4) scripts/n8n_api.py fails with foreign `tools` first and repo on PYTHONPATH, and on PR12 only gives `ImportError: cannot import name 'ROOTS_ENV'` when an already-imported foreign `tools` lacks it; (5) hard links inside a confined root pass on main and PR12, a write through one changed the outside file; (6) ntpath helper: `\??\UNC\...` not refused, `readonly_sqlite_uri` accepts empty and NUL text; (7) `LEAD_DESK_PATH_ROOTS=/` allows `--key-file /etc/hostname` on PR12. Worked on PR12: all other UNC/mixed forms refused; all `..`, absolute and symlink escapes for the three server options exit 2 (main starts the server every time); `check_invariants.read_book` raises clean InputError (main AttributeError). Not run: real Windows, SQLite on a network share, mapped drive.

## 2026-11-13 09:51Z / 15:21 IST  HEARTBEAT 2
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap (and why) | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner agent (Sonnet): full product suite on Linux, Python 3.12, no browser tests; main 61ded9e and PR #12 8d65577 | pass/fail evidence for PR #12 vs main | 09:39Z / 15:09 | run1 of both heads about 64% done at 09:49Z; run1 ends ~10:00Z, run2 ends ~10:25Z / 15:55 IST (about 35 min left) | run 1 of 2 per head (each head runs twice by order); no retry, no hang seen so far | running | read progress-A.txt at 10:00Z; write evidence/summary.md numbers table when A finishes |
| B | Evidence runner agent (Sonnet): hostile-input pass on PR #12 changes | raw input/output for path-confinement changes | 09:39Z / 15:09 | finished writing evidence/hostile.md at 09:49Z; waiting for its final report message | case groups 5 of 5 done; no retry | done writing, final report not yet received | read its report; push evidence; check hostile.md has no real-looking secrets |
| lead-me | this session: register, supervision, pushes to demo/lane3 | keeps A and B watched | 09:37Z / 15:07 | 90 min cap ends 11:07Z / 16:37 IST | n/a | running | heartbeat by 10:01Z |

ASK: none (lead answers of 09:48Z applied: python3.12, browser tests skipped with skip count recorded, container clock, two runs at once; summary.md numbers table will be written when A finishes).
Early note, raw, not a verdict: hostile.md lists unexpected items first (F1: a foreign `tools` package with the same function names is used by load_tools/catcher.py on both main and PR12; F2: `python -m demo_only.fake_model_server --help` ends in a traceback on PR12 when another project's `tools` is first on the path, main prints help). Details in evidence/hostile.md.

## 2026-11-13 09:39Z / 15:09 IST  HEARTBEAT 1 (ORDER 1 started on GO)
| id | what it does | why (what it unblocks) | started UTC+IST | expected end / time left | round or retry n of cap | state | next action |
|---|---|---|---|---|---|---|---|
| A | Evidence runner agent (Sonnet): full product suite on Linux, PR #12 head 8d65577 and main 61ded9e, each twice, Python 3.12, hash-locked install, no browser tests | gives lead pass/fail evidence for PR #12 vs main | 09:39Z / 15:09 | ~10:45Z / 16:15 (about 65 min) | run 0 of 4; no retry yet | running (setting up copies and venvs) | check progress-A.txt at 09:50Z |
| B | Evidence runner agent (Sonnet): hostile inputs on PR #12 changes (UNC paths, hard links, foreign `tools` package, n8n_api import order, fake model server path options) | gives lead raw input/output proof for the path-confinement changes | 09:39Z / 15:09 | ~10:10Z / 15:40 (about 30 min) | case group 0 of 5 | running | check progress-B.txt at 09:50Z |
| lead-me | this session: supervision, register, commits to demo/lane3 | keeps both agents watched | 09:37Z / 15:07 | until both report (90 min cap: 11:07Z / 16:37 IST) | n/a | running | heartbeat by 09:49Z |

ASK:
1. Python: the machine default is 3.13; the lock is for 3.12, so I use /usr/bin/python3.12 for the venvs. Default if no answer in 10 min: keep this.
2. Playwright/Chromium: not installed (docs/tests.md says browser tests then skip, ~113 skipped); order allows only the hash-locked pip install, so I skip the browser lock. Default: keep skipped, record the skip count.
3. The clock in this container reads 09:37Z while your message says 09:40Z; I use the container clock (`date -u`). Default: keep.
4. I run the main copy and the PR copy at the same time (2 heavy runs, serial inside each copy). Default: keep.

## 2026-11-13 09:36Z / 15:06 IST  EGM SETUP PROOF (partial: dry run NOT done, needs a session reload)
FAILED / NOT DONE (first):
- Dry run (egm-review-loop with reviewers design and style) NOT run. The Skill and Agent lists of this running session were read at session start, before the install, so this session's Skill tool lists no egm:* skills and its Agent tool lists no egm:* agent types. I cannot reload them from inside the session (/plugin reload is a typed slash command). Needed from lead/owner: reload plugins or start a new session on branch demo/lane3, then I run the dry run. I did not substitute a general-purpose agent.
- `/plugin ...` slash commands cannot be typed by me; I used the equivalent CLI `claude plugin marketplace add google/elephant-goldfish-model` and `claude plugin install egm@egm` (both succeeded).
- Studio files templates\agents\BRIEF-PREAMBLE.md, bible\RULES.md, tools\hooks\agent_preamble_gate.py are NOT in the hadavin-sdk checkout (handover/BRIEF-PREAMBLE.md is). Not invented. The Agent-model hook mentioned in MODEL-ROUTING.md is therefore absent here; I set model on every Agent call by hand.
- Agent file names differ from the list in the order: the design reviewer file is design_critic.md with name egm-design (fine); plugin also ships extra egm-inventive-catalyst and egm-bootstrap-orchestrator.
DONE (with output):
- `claude plugin list`: egm@egm, Version 0.1.1, Scope user, Status enabled (note: "Default agents/ folder is ignored because the manifest sets agents").
- Claude Code version: 2.1.323 (>= 2.1.271).
- ~/.claude/settings.json now has model claude-sonnet-5-5, effortLevel medium, enabledPlugins egm@egm true, plus the extraKnownMarketplaces entry the install added.
- On disk the plugin has the 7 skills (egm-bootstrap, brainstorm, draft, drift-report, resolve, review, review-loop) and agent names egm-design, -codebase-details, -comprehension, -implementation-readiness, -structural, -style, -zoom-out, -synthesizer (+ bootstrap-orchestrator, inventive-catalyst).
- Ran handover/tools/egm_model_patch.py (read it first; it only edits model: lines and removes disable-model-invocation in the plugin cache): 70 files changed in 2 plugin folders. Check: `grep -rh ^model:` gives 6 claude-opus-5-5 (3 skills x 2 copies) and 64 claude-sonnet-5-5, no inherit; disable-model-invocation count 0 in all 7 cached skills. Needs a new session to take effect.
- Repo: demo/lane3 checked out (HEAD tracks origin/demo/lane3). Read BRIEF-PREAMBLE.md, MODEL-ROUTING.md, ORDERS.md. ORDERS NOT STARTED, waiting for GO.
- No secrets, no spend, no settings change on GitHub, no merge.
Register: no agents/shells/jobs running.


