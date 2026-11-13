# Path confinement tests, c14a514 vs 6b1fe49 (PR #14)

Evidence runner G. Raw output only. No failures, no errors. The delta 6b1fe49..c14a514 changes 2 files (`tests/test_path_confinement.py`, `tools/pathconfine.py`); only the first is a test file, so JOB 1 covers it (the same file on both heads). `requirements-dev.txt` diff is empty, so /home/user/work/final-venv (Python 3.12.3) was reused. Linux. Both runs were sequential, not in parallel.

| head | file | passed | failed | skipped | errors | wall time |
|---|---|---|---|---|---|---|
| c14a514 | tests/test_path_confinement.py | 378 | 0 | 1 | 0 | 67.56 s (script 68 s) |
| 6b1fe49 | tests/test_path_confinement.py | 378 | 0 | 1 | 0 | 36.69 s (script 37 s) |

Skipped (both heads): `tests/test_path_confinement.py:284: ntpath.isreserved needs Python 3.13` (venv is 3.12.3). The delta's changed Windows-only skip (C0 name) did not skip on Linux; the lone-surrogate test passed.

Observation: wall time is 31 s longer on c14a514; not investigated (the run on c14a514 came first, nothing else of mine was running; other machine load not measured).

Failures: none.

Commands (exit 0 both; wrapper script `/home/user/work/g-run.sh <worktree> <head>`):
`cd <worktree>; . /home/user/work/final-venv/bin/activate; TMPDIR=/home/user/work/g-tmp timeout 900 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt tests/test_path_confinement.py`
Worktrees: /home/user/work/g-final (c14a514, created with `git worktree add`), /home/user/work/f-final (6b1fe49).
Raw logs: `raw/path-tests-c14a514.log`, `raw/path-tests-6b1fe49-sidebyside.log` (originals in /home/user/work/g-logs/).
