# Q7: the formerly skipped 196 tests under Python 3.13.18 (EVIDENCE RUNNER, raw output only, 2026-11-13 12:33-12:40Z / 18:03-18:10 IST)

Failures: none. Skips: none. Not checked: only the 10 browser files and the 3 gitleaks files were run (not the full suite); one run per cell, no timing repeats; both heads ran at the same time (2 processes); ruff, mypy, bandit not run.

| group | head | python | passed | failed | skipped | wall | 3.12 result (unskip-*.md) |
|---|---|---|---|---|---|---|---|
| browser pass 1 (4 files) | BASE f3c39cf | 3.13.18 | 113 | 0 | 0 | 111 s | 113 passed, 104 s |
| browser pass 2 (6 files) | BASE | 3.13.18 | 128 | 0 | 0 | 255 s | 128 passed, 207 s |
| gitleaks (3 files, DPLD_REQUIRE_SCAN=1) | BASE | 3.13.18 | 72 | 0 | 0 | 86 s | 72 passed, 76 s |
| browser pass 1 | STACK | 3.13.18 | 113 | 0 | 0 | 111 s | 113 passed, 105 s |
| browser pass 2 | STACK | 3.13.18 | 128 | 0 | 0 | 257 s | 128 passed, 206 s |
| gitleaks | STACK | 3.13.18 | 72 | 0 | 0 | 82 s | 72 passed, 75 s |

Differences from 3.12: none in counts or status; 3.13 wall time is somewhat longer (two runs shared 4 cores with other agents). Exit code 0 on all six runs.

Setup: BASE = f3c39cf89ec989f032ea48a23cfd824b88da9c68 (/home/user/work/q7-base); STACK = same plus claims-stack-on-f3c39cf8.patch (applied cleanly, /home/user/work/q7-stack). Venv /home/user/work/q7-venv is a FRESH 3.13.18 venv (not a copy of py313-venv): `pip install --require-hashes -r requirements-dev.txt` rc=0, then `-r requirements-browser.txt` rc=0. Locked 3.13 wheels exist (greenlet 3.5.6 cp313, playwright 1.63.0 py3-none, pyee 13.0.1). Chromium build 1243 at /opt/pw-browsers, Node /opt/node22/bin, gitleaks 8.30.1 from /home/user/work/tools/gitleaks-bin (nothing downloaded from outside the pip locks).
Command (script /home/user/work/q7-run.sh <base|stack> <worktree>): `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers TMPDIR=/home/user/work/q7-tmp/<group>-<head> timeout 1500 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt <same files as unskip-browser.md / unskip-gitleaks.md>`.
Logs: raw/py313-unskip-{browser1,browser2,gitleaks}-{base,stack}.log, raw/py313-unskip-pip-{dev,browser}.log; progress in raw/progress-Q7.txt. Worktrees q7-base, q7-stack and venv left in place; no process of mine still running.
