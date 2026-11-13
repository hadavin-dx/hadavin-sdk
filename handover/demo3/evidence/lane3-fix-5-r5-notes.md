# lane3-fix-5 round 5 notes (builder B5e)

Patch: lane3-fix-5-r5.patch (full diff from f3c39cf8). sha256 in the last section.

## Failures, unproven and not done (first)
- A first full serial run FAILED (57 failed, 13 errors; raw/b5e-full-invalid-run1-basetemp-outside-TMPDIR.log). Cause: my run script put pytest's --basetemp outside TMPDIR, and the repository's path guard refuses paths outside the allowed folders. Proven by experiment (raw/b5e-smtp-experiment.log): tests/test_smtp_outbox.py gives 13 errors with basetemp outside TMPDIR and 67 passed inside, on the final tree AND on the r4 tree. Not caused by the conftest release or the free_port change. The xdist runs did overlap in time with that first run (started 1 s apart, finished before it); they were not the cause. The valid run was then done alone (below).
- reset.ps1 was NOT run on Windows (no Windows runner here). What ran: text tests on the script, and its two patterns applied with Python `re` (not the PowerShell engine). Two Windows-only tests exist and are skipped here. Unverified by run.
- ruff, ruff format, mypy, bandit were not run (CI only). Import order, quote style and wrapping follow the rules by reading.
- The chmod-000 pid-file test skips for root; it was run as user 65534 and passes (raw/b5e-nonroot-chmod.log, fails on r4).
- Not verified: macOS/BSD (ps text fallback tested with a stand-in ps only), busybox, hidepid /proc. bash 4.4 or newer is needed for the exact /proc check (mapfile -d); older bash falls back to the ps text rule.
- Stand-in port numbers 41001-41005 in tests/test_port_helpers.py are made-up values of a fake socket module, not ports that are opened.
- Residual by design: free_port() still closes its socket at once, so a number can be taken by another process before the caller binds it. Held numbers and numbers free_port gave out in the same process are now never mixed; across xdist workers the only protection is held_port() (used by the reset tests).
- reset_run's `# noqa: S603` line comes from r4 (moved there), not added in r5.

## Fails-before (raw/b5e-fails-before.log, list in raw/b5e-fails-before-list.txt)
Part A: r5 tests against the r4 scripts: 38 failed. Part B: tests/test_port_helpers.py against the whole r4 tree: 4 failed, 1 passed. Total 42 listed.
| Item | Tests that fail on r4 |
|---|---|
| M1 (reset.ps1) | test_reset_ps1_pid_rules.py: text test, 16 command-line rows, 7 pid-shape rows |
| m1 exact argv | quoted shell (bash -c ... marker), python-tools/bin/less (desk and fakes), `-c`/`-u` before `-m` rows |
| m2 [Pp]ython | real shape with program named Python; ps fallback Python.framework row |
| ps fallback tightened | rows: python-tools/bin/less, my python/bin/less, bash -c python -m ..., path with space (safe side) |
| m6 | pid file as named pipe, socket file (r4 hangs/aborts), folder (exit 7) |
| m4 | autouse fixture present in conftest (test_port_helpers.py) |
| m5 | free_port never a held number; held_port never a number free_port gave; clear error when exhausted |
| m3 | no new failing test: pid helper dead_pid() and HOST are used (checked by reading) |
Also raw/b5e-old-script-8cases.log: the 8 real-process marker cases against the ORIGINAL f3c39cf8 reset.sh (sha256 equal to base), COLUMNS unset: 8 failed.

## What changed
- scripts/reset.sh: is_ours() reads /proc/PID/cmdline with mapfile -d '': argv[0] basename [Pp]ython*, argv[1] -m, argv[2] exactly one of the two modules. Fallback (no /proc): the ps text must START with the interpreter word (ps joins arguments, so a quoted string cannot be told apart otherwise); a program path with a space is refused (exit 6, safe side). Pid file read with the shell's own `read -N 64` only for a regular file (a pipe would hang, a socket/unreadable file would abort under set -eu): anything unreadable or 64+ characters is stale. A pid file that cannot be removed (a folder) gives exit 7 (README documents it).
- scripts/reset.ps1: raw read in try/catch, $null guard, Trim, `-cmatch '^[1-9][0-9]*$'` plus [int]::TryParse; command line judged by an anchored pattern (first word is the interpreter, then -m, then the exact module); unquoted interpreter path with a space is refused (safe side).
- tests: support.py (start_proc program/cwd, stub_tree, start_module_proc, dead_pid, free_port/held_port class fix, reset_run timeout), conftest.py autouse release (per-file copies removed), test_reset_ps_width.py, test_reset_scripts.py (real `python -m lead_desk.server` shape), new test_reset_ps1_pid_rules.py and test_port_helpers.py.

## Evidence on the final tree (tree id ede143b5..., after README wrap)
- ONE full serial run, alone: `python -m pytest -q -rs`: 3780 passed, 206 skipped in 1273.29 s, EXIT_CODE=0 (raw/b5e-full.log).
- 20 runs of the two reset test files plus test_port_helpers.py and test_reset_ps1_pid_rules.py at -n 4 in the xdist venv: 20 of 20 passed, 142 passed 6 skipped each (raw/b5e-xdist.log).
- git apply --check of the patch: on f3c39cf8 rc=0; on f3c39cf8 + claims-stack-on-f3c39cf8.patch rc=0.

## Rung table
| Component | Rung | Why lower rungs were rejected |
|---|---|---|
| Which process reset may stop (sh and ps1) | 7, small fix at the existing decision point | Rungs 1-6 cannot decide which process id to stop; no core module does this |
| Port helpers | 1, extends tests/support.py | free_port stays; held_port added |
| Test process shapes | 1, reuse start_proc | one helper, no new process code |

## sha256
lane3-fix-5-r5.patch 67f7d04cfbe080cc59489af96ba693bb3d94280909dc2a6a3dabc47399d95b9d
