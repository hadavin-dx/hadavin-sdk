# A8 evidence, PR70 core/P1b head e3f946f (copy /home/user/build/EV-A8b, .git dropped). Raw logs in this folder. No verdict.
Run 16:57-17:38 UTC (IST +5:30). Shared machine, heavy slots mostly busy with other agents.

| Check | Python | Result (from the log) | File |
|---|---|---|---|
| ruff check src tests demos tools | 3.13 | exit=0 | ruff-check.log |
| TID251 step A | 3.13 | exit=0 (these two steps are NOT in this head's ci.yml) | tid251-A.log |
| TID251 step B | 3.13 | count=0: tests/fixtures/tid251_forms does not exist in this head (ruff warns "No such file") | tid251-B.log |
| ruff format --check | 3.13 | exit=0 | ruff-format.log |
| bandit -q -r src demos tools -ll | 3.13 | exit=0 | bandit.log |
| tools/scan_repo.py (run in WT-A8b, needs .git) | 3.13 | exit=0 | scan_repo.log |
| pytest -m "not live and not perf" (-v) | 3.13 (HADAVIN_REQUIRE_PINNED_UNIDATA=1) | 1 failed, 11212 passed, 1 skipped, 39 deselected in 526 s; exit=1 | pytest-py313.log |
| pytest -m perf | 3.13 | 39 passed, 11214 deselected in 84.63 s; exit=0 | pytest-perf.log |
| tests/stage_mutants.py | 3.13 | exit=0, 29 lines, all shown rows "ok KILLED" | stage_mutants.log |
| tests/textnorm_mutants.py | 3.13 | ANOMALY: the list has 155 mutants but the log has 45 "ok KILLED" lines, no final "N of M good" line, then exit=0. Not explained; needs a re-run | textnorm_mutants.log |
| pytest, 3.12 | 3.12.3 | NO RESULT: stopped at 58% at the time box (partial log) | pytest-py312.log |

## The 1 failure on 3.13
tests/test_licences_are_proprietary: `git ls-files` exit 128 (the copy has no .git, as the brief says). ENV, not re-run in a git checkout.

## NOT RUN / incomplete
- pytest 3.12 full: stopped at 58%, no result.
- textnorm mutants: log incomplete or odd, see table.
- Vault contract tests: no vault server here (skip).
- ci.yml jobs semgrep, zizmor, pip-audit, gitleaks, trivy: not in this brief.
- Postgres: shared cluster 127.0.0.1:55400, databases a8b_ev and a8b_ev312 (left in place).
