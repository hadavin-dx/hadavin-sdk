# Evidence E3: patch lane3-fix-1 (raw output only, no judgement)
Patch sha256 67597283...8ccf27 verified. Base f3c39cf8, Python 3.12, no failures, no errors. Baseline unpatched: 3683 passed, 200 skipped.

| tree | scope | passed | failed | skipped | errors | wall | exit |
|---|---|---|---|---|---|---|---|
| e3-fix1 (base + lane3-fix-1) | tests/test_docs_claims_lane3.py | 9 | 0 | 0 | 0 | 0.26 s | 0 |
| e3-fix1 | full suite | 3692 | 0 | 200 | 0 | 1348 s | 0 |
| e3-stack (base + claims stack + lane3-fix-1) | tests/test_docs_claims_lane3.py | 9 | 0 | 0 | 0 | 0.39 s | 0 |
| e3-stack | full suite | 3692 | 0 | 200 | 0 | 1359 s | 0 |

Count matches expectation (3683 + 9 = 3692). Both full suites ran at the same time.
Raw logs: raw/e3-fix1-full.log, raw/e3-stack-full.log, raw/e3-fix1-new.log, raw/e3-stack-new.log.
Not checked: ruff, mypy, bandit, gitleaks (CI only, by rule).
