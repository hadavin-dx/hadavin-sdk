# checkpoint B23 (final, 2026-11-14 ~08:05Z)
All rows 1-20 applied (5, 7 contested as ordered). Patch r4, parts, sha256, notes written. Open: nothing for me. No commit/push.

## Round 5 checkpoint 08:09 UTC
Done (untested beyond narrow runs, unlinted, unstaged): row 6 (config_exit bytes), row 2 (fakes_server --host + IPv6 class), row 5/14/15 (start_all.sh pre-flight, ownership line, bracket rule, formatter text; start_all.ps1 same + try/finally encodings, TEXT PINS), late-refusal tests rewritten (pre-flight, after-check listener, grep shim, IPv6 real), ps1 pins extended. late_refusal + ps1_pins files pass. Next: rows 3,4 (test_reset_scripts), 1 (docs+prose test), 8, 9, 12-19, 20-24, then fails-before on pristine r4 copy, lint, 3x runs, mutants, patch.

## Round 5 checkpoint 08:18 UTC
All 24 rows edited. Lint on a clean ls-files copy: ruff check/format, mypy linux+win32, bandit all rc 0 (raw/b23-r5-lint-*.log). fails-before on a pristine r4 copy: 94 failed (raw/b23-r5-fails-before.log). Running: callers (raw/b23-r5-callers.log). Next: 3x runs of the start_all/late-refusal/reset files, wall-clock tests alone, mutants (/home/user/work/b23-mut5.py), patch, parts, sha256, notes. UNCERTAIN: IPv6 real-bind tests are SKIPPED here (kernel refuses AF_INET6), only class choice is tested with stand-ins.

## Round 5 final (about 08:58 UTC)
Survivors r4-3, r4-13, r5-5 fixed and killed. r4-10 still unexplained. Lint rc 0 all five. 3 runs 216 passed/10 skipped (run 3 redone once after a cut-off log). Patch + 5 parts + sha256 cut; same tree c494f120 on double apply and parts. Notes: lane3-fix-10-r5-notes.md. Handing back.

## Round 6 checkpoint 1 (09:19 UTC; started 09:12; stop at 10:12)
Done: rows 3, 4, 11, 12, 20 in start_all.sh (deadline clock, desk alive after its line, timeout refused, second kill -0 comment, own test kills mutant r4-10), row 6 (reset 5 two causes via reset.sh/ps1 + table text, reset 8 text, code-8 uniqueness test), row 7 (config_exit.write_line, all refusal prints through it, cp1252 tests), row 9, 18. Fails-before log raw/b23-r6-fails-before-start.log. Next: row 1 (table-only numbers), 5, ps1 text for 4/12, 8, 16, 17, 19, 2 (20 reruns), 13-15, lint, final full run. Not committed.

## Round 6 checkpoint 2 (about 09:35 UTC)
Done: rows 3,4,5,6,7,9,10,11,12,18,19,20 coded and tested; row 8 (reset slow-stop test now released by a file, not a 3 s sleep; other sleeps listed as justified in the notes); row 16 (producing tests for crash_desk 1, reset_check 4, the 7 causes of start_all row 1; ps1 rows printed as "not produced on Linux; needs a run on Windows (WINDOWS-RUN-1)"); held-socket ports in reset tests; lint clean (ruff check, format).
Running: row 2, 20 setsid reruns of the three timing files, logs in raw/b23-r6-reruns/ (summary.txt). Tree id of the rerun snapshot ff10a6bb.
Next: pristine-r5 red-first, mutants (row 13), mypy and bandit on a clean copy, 3 logged narrow runs (row 15), ONE final full run, patch and notes.

## Round 6 checkpoint 3 (about 09:44 UTC) - row 2 cause
Coordinator named the cause of the log cut-offs: a `git pull --rebase --autostash` run by the coordinator (09:32:35 inside run 03; 09:38:56-09:39:09 inside run 10) rewrote the live log file that sits inside the git tree while pytest held it open. I checked: runs 03 and 10 have rc=0 and a complete junit xml (114 tests, 0 failures, 0 errors, 2 skipped, about 60 s); their logs stop mid-test (5845 and 2223 bytes). Every other run (01-13 so far) has a full 14053-byte log and the same xml. Kept as "log truncated by git, xml complete". From now on live logs go outside the git tree (/home/user/work/b23-logs) and are copied at the end.
