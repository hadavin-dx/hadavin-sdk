# f8-r12 fix log (CHECKPOINT, written at 19:05Z; final status block at the end)

Said first: what is NOT done or NOT proven.
- The intermittent exit 1 is NOT explained. No run reproduced it (evidence-f8-r12-runner.md: 3 plain runs, all as expected). Changes that remove two plausible causes (shared work folder, orphaned helpers, no time limits) are not proof. No test fails on old code for this symptom, so I do not claim it fixed.
- `test_run_all_raw.sh` (rewritten, 3 phases) was NOT run yet on new or old code at this checkpoint. See the final block.
- Old-code proof for `test_run_all_stop.sh` was still running at this checkpoint: the first three failures on the old run_all.sh were already seen (self-test not reached, no INTERRUPTED message, SIGINT not ending the run); the full old-code count is not yet read.
- Not tested: non-root user, macOS, Windows, git older than 2.32 (GIT_CONFIG_GLOBAL; 2.43 here). PATH, TZ and HOME are not scrubbed (PATH trusted).
- `[take_check.sh exit=5]` in every run is by design (the committed pin's reviewer line is unconfirmed), not a failure.
- Stray folder `flow-check/zqwv-hook-val` (563 tracked files, 12 MB, a self-test output folder committed in 36fd181c6) was NOT touched: outside my brief. Lead decides.

## Per finding
| Finding | Bug class | State | Checked by |
|---|---|---|---|
| M1 writer path steerable by `RUN_ALL_RAW` / `--refresh` | writer destination chosen by environment | Fixed: `RUN_ALL_RAW` honoured only in a validated nested run; `--raw-dir` for scratch; publish refuses any destination that is not the physical `raw/` (symlink to it works); manifest written | take-suite cases M1a-d; fail on old code (543/574 passed there) |
| M2 no time limit, orphan helpers, no signal handling | unsupervised helper processes | Fixed: limits in one place (5, env-overridable, validated), `lim` = `timeout -k 10` + wait, `reap_children` before folder removal, INT/TERM/HUP traps. Two further defects found by my new stop test and fixed: handler messages went into the step's output file (now on fds 5/6); `selftest.py` left its work folder when stopped (now removed on a signal) | `test_run_all_stop.sh`: 25 of 25 on new code; old code fails (A, B cases seen, see above) |
| M3 weak parent check, denylist environment | fail-open guard | Fixed: ancestor walk (PPid, 6 levels) requires a running run_all.sh; SHELLOPTS/BASHOPTS refused; `GIT_` prefix scrubbed, unset failure is fatal; git config files off | cases M3a-d |
| m1 extra SELFTEST:/test_take_check: lines | count parsing | Fixed: exactly one line, strict pattern | case m1 |
| m2 duplicate/unknown pin keys | pin parsing | Fixed | case m2 |
| m3 flock message used unset var; git init unchecked; pipeline status | unchecked statuses | Fixed | cases m3c-flock + others |
| m4 fixed /tmp work folder; unbounded disturber loop | paths not from TMPDIR; unbounded loop | Fixed (`TMPROOT`; loop bounded 1800 s + trap) | m5b; test_run_all_raw.sh NOT run |
| m5 relative work folder / relative TMPDIR | path handling | Fixed | cases m5a/b |
| m6 unknown option, two work folders; selftest empties a foreign FC_OUT | argument and folder guards | Fixed | cases m6a/b, m6 |
| m7 | not separately identified in my notes | see lead's review file; nothing extra done | not checked |
| m8 repeat_run_all.sh no per-run limit | no time limit | Fixed: `timeout -k 10 ${REPEAT_RUN_LIMIT:-1800}` per run | `bash -n` only; not run (a run takes 4 min per round) |
| m9 publish leaves temp files / unverified publish | non-atomic publish | Fixed: mktemp + mv, manifest, publish after pass only | test_run_all_raw.sh phase 2/3: NOT run |
| Reviewer claim "timeout kills the direct child only" | claim | Not verified empirically; the stop test shows no process left | - |

Files changed: run_all.sh, selftest.py, test_take_check.sh (574 cases, was 555), test_run_all_raw.sh (rewritten), test_run_all_stop.sh (new), repeat_run_all.sh, README.md, expected-counts.pin (take_suite_cases=574).
Evidence quoted so far: new-code take suite `574 of 574 cases as expected, 0 not as expected` (rc=0); stop test `25 of 25` (rc=0).

## Next (before 19:30Z): ruff format --check, check_secrets, one final run_all.sh. Results are in the final block below if present.
