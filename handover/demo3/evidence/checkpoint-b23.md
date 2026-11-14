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
