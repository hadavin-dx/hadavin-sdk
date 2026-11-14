# checkpoint B23 (final, 2026-11-14 ~08:05Z)
All rows 1-20 applied (5, 7 contested as ordered). Patch r4, parts, sha256, notes written. Open: nothing for me. No commit/push.

## Round 5 checkpoint 08:09 UTC
Done (untested beyond narrow runs, unlinted, unstaged): row 6 (config_exit bytes), row 2 (fakes_server --host + IPv6 class), row 5/14/15 (start_all.sh pre-flight, ownership line, bracket rule, formatter text; start_all.ps1 same + try/finally encodings, TEXT PINS), late-refusal tests rewritten (pre-flight, after-check listener, grep shim, IPv6 real), ps1 pins extended. late_refusal + ps1_pins files pass. Next: rows 3,4 (test_reset_scripts), 1 (docs+prose test), 8, 9, 12-19, 20-24, then fails-before on pristine r4 copy, lint, 3x runs, mutants, patch.

## Round 5 checkpoint 08:18 UTC
All 24 rows edited. Lint on a clean ls-files copy: ruff check/format, mypy linux+win32, bandit all rc 0 (raw/b23-r5-lint-*.log). fails-before on a pristine r4 copy: 94 failed (raw/b23-r5-fails-before.log). Running: callers (raw/b23-r5-callers.log). Next: 3x runs of the start_all/late-refusal/reset files, wall-clock tests alone, mutants (/home/user/work/b23-mut5.py), patch, parts, sha256, notes. UNCERTAIN: IPv6 real-bind tests are SKIPPED here (kernel refuses AF_INET6), only class choice is tested with stand-ins.
