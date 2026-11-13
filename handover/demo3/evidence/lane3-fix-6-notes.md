# lane3-fix-6 (builder B6): documentation defects found by cold readers on f3c39cf8
Worktree /home/user/work/b6-base (detached at f3c39cf8). Patch: `lane3-fix-6.patch` (4 files, +79 -6). Product code changed: none. No commit.

## Failed or not done, first
- The FIRST full suite run on the final tree failed: `1 failed, 3689 passed, 199 skipped in 1240.99 s` (`raw/b6-full-suite.log`). Cause: my own new test had the regex text `src:\.`, and the repo hygiene test flags the characters `c:\.` as a hardcoded Windows path. I fixed the test (`src:[.]`). I did NOT repeat the 21-minute full suite (brief: one full run); I re-ran `tests/test_hygiene.py` plus the new file: `26 passed, 4 skipped` (exit 0, `raw/b6-rerun-hygiene.log`; the 4 skips are the gitleaks ones, no gitleaks program here). So there is no single green full run on the final tree; the one failure was in the test file I then changed, and the rest of the suite is unchanged by the fix.
- Not checked: Windows commands in the docs (`;` form only copied from the existing text); the browser/gitleaks/3.13 numbers were NOT reproduced by me, quoted from `unskip-browser.md`, `unskip-gitleaks.md`, `py313-unskip.md`, `skipped-on-purpose.md`.
- Number conflict: the brief says 29 gitleaks skips and the cold reader says about 29 and 163 browser skips; `skipped-on-purpose.md` (read from the log) says 30 gitleaks (24+2+4) and 166 browser (22+28+113+3). My own full run's skip lines show 24 + 2 + (3 of 4 hygiene, the 4th ran as the failing test) and 22+28+113+3 browser, which agree with 30 and 166. I wrote 30 and 166 (166+30+4 = 200).

## Each defect: command before and after (ports and database moved to private values with DESK_PORT, DESK_FAKES_PORT, DESK_DB_PATH; made-up data)
| # | command | before | after |
|---|---|---|---|
| 1 | `PYTHONPATH=src python scripts/crash_desk.py` (demo servers up) | exit 1, RuntimeError: folder demo_only is missing | docs now say `PYTHONPATH=src:.`; with it, flag `D2` + `scripts/feed.py` request: "simulate crash", exit 137, flag file removed |
| 2 | `python -m lead_desk.server` with no demo servers | exit 1 "cannot reach the demo servers" | docs say start `PYTHONPATH=src:. python -m demo_only.fakes_server --outbox keyed --port 8766` first; no servers: exit 1 (as documented); servers up: desk "listening" (my timeout ended it, exit 124 is mine). Also found: the desk command itself needs `src:.` not `src`, README line 132 and tests.md fixed. |
| 3 | `run_real_check.py --dry-fakes </dev/null` | exit 1 "Start? [y/N] stopped ... no terminal" | docs name `--assume-yes` (flag read from the parser, line 818, only with `--dry-fakes`); `--dry-fakes --assume-yes`: exit 0, "ALL CHECKS HOLD" |
| 4 | counts | docs: 2513 passed, 3 skipped | docs: 3683 passed, 200 skipped, 21 min 24 s, coverage 23 min 14 s, line rate 0.9352, reasons with numbers; old counts kept but labelled "NOT the current count" |
| 5 | people in dry run | docs: about 12 | docs: 12 is the real-run default (`REAL_PERSONS`); dry run printed `people: 8 + a twin` = 9 leads |
| 6 | blind mail, many follow-ups | table covers one follow-up | paragraph added under the crash table: `unknown`, reason `crash_while_sending`, 0 or 1 mails, in the review list, never 2; checker needs `--max-unknown N` (flag in `load_tools/check_invariants.py:701`, default 0) |
Extra honest note: that dry run itself ended with 8 sent + 1 unknown (the crash window) and still "ALL CHECKS HOLD".

## New test file `tests/test_docs_tests_md_lane3.py` (6 tests, regular expressions on text files, no slow work, max line length 120 checked: 0 lines over)
- Patched tree: `6 passed` (`raw/b6-new-tests-patched.log`, and in the hygiene rerun). Base f3c39cf8 with the test copied in: `6 failed` (`raw/b6-new-tests-on-base.log`).
- Hygiene test after `git add -A`: passed in the rerun above.
- Not touched: tests/test_email_case_rule.py, README Same-lead lines, docs/limits.md lines 24-26.
- Sandbox: only my own processes started (fakes servers, desks); all stopped (the fakes servers by exact command line, my own). Progress: `raw/progress-B6.txt`.
