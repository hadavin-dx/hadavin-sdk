# PR 72 core/P6a head 0ae044b25a3113244777cd078fc9a784647af924 (cloud3 evidence run; snapshot HEAD printed first in each log)

EVIDENCE RUNNER record: raw output only, no verdict. Machine paths replaced by <snapshot>, <build>, <home>.

FAILED / NOT RUN first:
- ruff check src tests demos tools (gen_evidence scope, adds tools/): inner rc 1, 14 errors, all in tools/p6a1_mutants.py (EXE001 shebang not executable; S603, S607, PLW1510 on its subprocess calls). ci.yml's own scope `src tests demos` (no tools): rc 0 (ruff-check-ci-scope.txt). Both logs kept. Note: ci.yml bandit step in the `security` job is `src demos`; the scope run here is `src demos tools` as the cloud2 run.
- P6a-1 hand mutants, handover/tools/p6a1_mutants_by_hand.py (62 mutants, re-fitted to d15e53a): planted 60 of 62, KILLED 60, SURVIVED 0, 2 NOT-LOCATED (mutant 33 "S6 guardrail item dropped" and 57 "[invented] vendor detector check looks for llm_judge": the text they patch (the `detector: bedrock_guardrail` line) no longer exists at 0ae044b). Script exit 1. Not-located is not a kill; these two did not run. Log: mutants-by-hand-62.txt.
- P6a-1 hand mutants, the PR's own tools/p6a1_mutants.py (63 mutants, current code): planted 63, KILLED 63 (46 with a named killer, 17 with no named killer: any failing test), SURVIVED 0, other problems 0, exit 0. Log: mutants-repo-tool-63.txt. Count is 63, not 62 or 73 (the file's own header says "45 from records + 18 new = 63"; a later line in the same docstring mentions "73"). The ticket's original 62-mutant script and its mutants 56-72 remain lost; mutants 56-72 here are invented (per both scripts' own headers).
- NOT RUN: Vault tests (HADAVIN_TEST_VAULT_ADDR unset; 1 skipped, same as before). CI, CodeQL, SonarCloud, CodeRabbit, gitleaks, trivy, semgrep, pip-audit not run. Postgres here is 16 (CI uses 17.10).
- NOT RUN as a separate check: the earlier gen_evidence "hygiene" is tools/scan_repo.py only (the original hygiene cell script is lost).
- Environment note from before (dblink-connect socket test) did NOT fail in this run; reason not investigated (clusters here listen with unix socket in /tmp and TCP).

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 1 | Found 14 errors | ruff-check.txt |
| ruff check src tests demos (ci.yml scope) | 3.13 | 0 | All checks passed | ruff-check-ci-scope.txt |
| ruff format --check src tests demos tools | 3.13 | 0 | 319 files already formatted | ruff-format.txt |
| ruff format --check src tests demos (ci.yml scope) | 3.13 | 0 | 315 files already formatted | ruff-format-ci-scope.txt |
| bandit -q -r src demos tools -ll (uvx) | 3.13 | 0 | no issue lines | bandit.txt |
| tools/scan_repo.py (hygiene) | 3.13 | 0 | no hits | hygiene.txt |
| pytest -m "not live and not perf" (own Postgres cluster, port A) | 3.13 | 0 | 10513 passed, 1 skipped, 28 deselected, 298.73 s | full-3.13.txt |
| same (own Postgres cluster, port B, run at the same time, different cluster) | 3.12 | 0 | 10513 passed, 1 skipped, 28 deselected | full-3.12.txt |
| pytest -m perf (alone, own cluster) | 3.13 | 0 | 28 passed | perf-3.13.txt |
| pytest -m perf (alone, own cluster) | 3.12 | 0 | 28 passed | perf-3.12.txt |
| python tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good | stage-mutants.txt |
| pytest tests/test_client_profile.py | 3.13 / 3.12 | 0 / 0 | 67 passed / 67 passed | p6a1-client-profile-3.13.txt / -3.12.txt |
| pytest test_k3_pilot_env + test_k5_round8_postgres | 3.13 / 3.12 | 0 / 0 | 11 passed / 11 passed | p6a1-pg-3.13.txt / -3.12.txt |
| p6a1_mutants_by_hand.py (62) | 3.13 | 1 | 60 killed, 0 survived, 2 not located | mutants-by-hand-62.txt |
| tools/p6a1_mutants.py (63) | 3.13 | 0 | 63 killed, 0 survived | mutants-repo-tool-63.txt |
| scan of these logs with scan_repo PATTERNS | - | 0 | no hits | hygiene-logs.txt |

Also here: TABLE-A.md, TABLE-B.md, TABLE-C.md (gen_evidence tables per Postgres cluster), sync312.txt, sync313.txt, head.txt.
Not committed, not pushed. Machine: shared cloud box; other agents' jobs ran at the same time (full suites were not alone).
