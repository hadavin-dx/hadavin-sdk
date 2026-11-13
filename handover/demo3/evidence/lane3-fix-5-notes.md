# lane3-fix-5: reset.sh reads the whole command line (builder B5, base f3c39cf8, worktree /home/user/work/b5-base)

## Failures and gaps first
- My first version broke 2 existing tests (empty pid file): an empty pid made the script read /proc//cmdline = /proc/cmdline (the kernel boot line), so exit 6. Found by the serial run, fixed by requiring a plain number before using /proc. Not an issue in the final patch.
- NOT tested: macOS ps, BusyBox ps, the plain-ps fallback branch (on this Linux the /proc branch always answers; the `ps -ww` branch was proven only by Q11's one-line experiment). Whole-repo suite not run (only the files below). No lint/mypy/bandit (owner rule).

## Reproduction on base (serial, venv q1-xdist-venv, the 2 existing tests)
- no COLUMNS: 2 passed. COLUMNS=80 LINES=24: 2 failed, `assert (6 == 5)` and `assert 6 == 0` (exit 6 "not the desk" for a real desk).
## Change (scripts/reset.sh, +8/-1): new function proc_args: if pid is digits and /proc/PID/cmdline is readable -> tr NUL to space; else `ps -ww -p PID -o args=`, else plain `ps -p PID -o args=`. Exit codes and messages unchanged. Exit 6 = pid file names a live process that is not the desk or demo server.
## Tests: tests/test_reset_ps_width.py (3 tests, new): slow-stop refusal (exit 5) and 3-second stop (exit 0) with COLUMNS=80 LINES=24; a command line of about 300 characters with the marker last under COLUMNS=20 (exit 5, not 6).
- Fails before first: on base script all 3 FAILED (6==5, 6==0, 6==5); patched: 3 passed.
## xdist (-p xdist -n 2, tests/test_reset_scripts.py): before 2 failed 43 passed; after (plus new file) 48 passed 0 failed. COLUMNS=80 serial, patched: 45 passed.
## Serial patched: test_reset_scripts + test_reset_ps_width + test_hygiene + test_shell_single_bracket: 214 passed, 4 skipped, 0 failed. (test_shell_single_bracket checks base lines only; unaffected.)
## reset.ps1: uses Get-CimInstance CommandLine (full line, no width cut): no same defect, unchanged.
## Other ps uses: scripts/reset.sh only `-o stat=` (short, safe) on the other lines; tests/test_shell_single_bracket.py:210-212 is a quoted copy of base lines (stat=, safe); tests/test_reset_scripts.py ps -o stat= safe. No `args` use in start_all.sh, crash_desk.py or src: none. 
## Patch: evidence/lane3-fix-5.patch (128 lines, sha256 0d347d4c7152e2b3d002e0a81b191147447d6752848e31c1f95599b3740b17a5). git apply --check OK on fresh f3c39cf8; after claims-stack-on-f3c39cf8.patch; after that + lane3-fix-1-r2.patch + lane3-fix-3-r3.patch.
## Rung table: 1 reuse (existing script, existing test helpers) ; custom code only for the 8-line helper; no tool/library rung applicable.
## Process register: no background processes left; worktrees b5-chk* removed; b5-base and TMPDIR /home/user/work/b5-tmp remain.
