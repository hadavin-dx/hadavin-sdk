# Unskipped gitleaks tests (evidence runner L; raw output only, no judgement)
Failures: none. Gaps: see the end.

| group | tests | passed | failed | skipped | wall time BASE / STACK |
|---|---|---|---|---|---|
| tests/test_hygiene.py (all) | 24 | 24 | 0 | 0 | part of one run |
| tests/test_gitleaks_exceptions.py | 44 | 44 | 0 | 0 | part of one run |
| tests/test_gitleaks_semgrep_lock.py | 4 | 4 | 0 | 0 | part of one run |
| total | 72 | 72 | 0 | 0 | 76 s / 75 s (exit code 0 both) |

BASE = f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree /home/user/work/l-base). STACK = same commit plus claims-stack-on-f3c39cf8.patch (applied cleanly, /home/user/work/l-stack).
Base-suite skip list (suite-base.log) for gitleaks: 24 (exceptions:145) + 2 (semgrep_lock:38) + 4 (hygiene:150, 344, 533, 580) = 30. The brief said 24+5+1; the log shows 24+2+4. Same total.

Versions: gitleaks 8.30.1 (`gitleaks version`). Tarball sha256 verified equal to lint.yml GITLEAKS_SHA256: 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb. URL pattern from lint.yml: https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz (download was allowed). Binary at /home/user/work/tools/gitleaks-bin/gitleaks.

Command (script /home/user/work/l-run.sh <worktree> <name>): `DPLD_REQUIRE_SCAN=1 TMPDIR=/home/user/work/l-tmp/<name> PATH=/home/user/work/tools/gitleaks-bin:/home/user/work/final-venv/bin:$PATH timeout 1500 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt tests/test_hygiene.py tests/test_gitleaks_exceptions.py tests/test_gitleaks_semgrep_lock.py`
(TMPDIR is a per-run subfolder of l-tmp so the two parallel runs do not share a basetemp.) Venv: final-venv reused; I did not run the requirements-dev diff (the git diff against c14a514 was empty, 0 lines).
Logs: raw/unskip-gitleaks-base.log, raw/unskip-gitleaks-stack.log.

Gaps: only the three files above ran, not the full suite. With DPLD_REQUIRE_SCAN=1 the history scan (`gitleaks git .`) also ran in the hygiene test; it passed on both worktrees. Worktrees l-base and l-stack left in place (not removed).
