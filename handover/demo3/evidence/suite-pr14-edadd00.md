# Full suite, PR #14 head edadd00 (evidence runner E, raw output only)

Failures: none. Gaps: Playwright browser tests skipped by instruction; the 200 skips are listed with reasons in the raw log (`-rs`). Not run: ruff, mypy, bandit, gitleaks (not in this job). One run only, so no flake statistics.

| head | run | passed | failed | skipped | wall time | hang yes/no |
|---|---|---|---|---|---|---|
| edadd00e9da24cc4297ca4461c7a09f74400a3db | 1 | 3681 | 0 | 200 | 1215.22 s (0:20:15); script wall 1216 s | no |

Last line of log: `3681 passed, 200 skipped in 1215.22s (0:20:15)` then `EXIT_CODE=0 WALL_SECONDS=1216`. Counts by grep match the summary (PASSED 3681, FAILED 0, ERROR 0).

Exact command (run by /home/user/work/e-run.sh, in /home/user/work/e-final):
`TMPDIR=/home/user/work/e-tmp timeout 2400 /home/user/work/final-venv/bin/python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt > /home/user/work/e-logs/suite-edadd00.log 2>&1`

Machine facts: Linux 6.18.44, 4 cores, 16 GB RAM, Python 3.12.3. Venv: reused /home/user/work/final-venv; E compared requirements-dev.txt of edadd00 with d5b4451 (no difference) and every pinned name is installed in the venv (name check only; versions and hashes not compared). Other agents ran pytest at the same time (not touched). Raw: raw/suite-edadd00.log, raw/suite-edadd00.partial.log (copy at 11:04:24Z).
Start 10:44Z (16:14 IST), end 11:04Z (16:34 IST).
