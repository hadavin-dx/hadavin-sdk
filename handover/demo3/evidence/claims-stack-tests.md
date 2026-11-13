# Claims stack tests (EVIDENCE RUNNER I)
Base: main f3c39cf8. Stack: base + claims-stack-on-f3c39cf8.patch (sha256 7138e884...194c, applied rc=0). Venv: /home/user/work/final-venv (python 3.12.3; requirements-dev.txt unchanged c14a514..f3c39cf8; all pinned names installed). Raw logs: raw/suite-stack.log, raw/suite-base.log, raw/hyg-*.log.

| head | scope | passed | failed | skipped | errors | wall | exit |
|---|---|---|---|---|---|---|---|
| STACK | full suite | 3683 | 0 | 200 | 0 | 1192 s | 0 |
| BASE | full suite | 3683 | 0 | 200 | 0 | 1189 s | 0 |
| STACK | tests/test_hygiene.py | 20 | 0 | 4 | 0 | 34.6 s | 0 |
| BASE | tests/test_hygiene.py | 20 | 0 | 4 | 0 | 33.1 s | 0 |
| STACK | tests/test_codeant_hygiene.py | 7 | 0 | 0 | 0 | 0.5 s | 0 |
| BASE | tests/test_codeant_hygiene.py | 7 | 0 | 0 | 0 | 0.3 s | 0 |

Failures: none on either head. Note: identical counts (3683) mean the stack adds no tests and no test changed outcome.
Skips (200 each, same on both): 6 playwright not installed (no browser tests, per brief); gitleaks not on PATH (4 in hygiene + 2 more); Windows-only reset (1); root can read no-permission file (1); ntpath.isreserved needs Python 3.13 (1); load measurement needs LEAD_DESK_LOAD_N (1); the rest are the same per-case repeats of these reasons (see `-rs` summary in raw logs).
Lint/gitleaks: skipped (no lead note newer than 11:40Z in demo3/ORDERS.md; ORDER 8 at 11:40Z is the latest). Studio backslash files not in this checkout.
Hygiene files chosen by name: test_hygiene.py, test_codeant_hygiene.py (other grep hits are other topics).

Commands (each run: cd to worktree, TMPDIR=/home/user/work/i-tmp-<x>):
- worktrees: git -C /home/user/work/src worktree add --detach /home/user/work/i-base|i-stack f3c39cf8...; git -C i-stack apply <patch>
- hygiene: python -m pytest -v -rs -p no:cacheprovider --basetemp=$TMPDIR/bt tests/<file>.py
- full: timeout 2400 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt (stack and base at the same time, log in /home/user/work/i-logs/)
Started 11:36Z, suites 11:38Z-11:58Z. Worktrees i-base, i-stack left in place (read-only use).
