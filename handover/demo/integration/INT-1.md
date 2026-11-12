batch 1 applies cleanly in order on pr-3-tests 558d37f: yes; gitleaks 0 findings: yes (dir and git, both exit 0); hygiene: 10 passed (gitleaks test ran, not skipped); full suite: 2400 passed, 116 skipped in 914.67s (exit 0)

# INT-1 integration check of batch 1 (EVIDENCE RUNNER: run and record only, no judgement)

## Failures
None in the ordered apply, gitleaks, hygiene, ruff, mypy, bandit or the full suite.
Notes (not failures):
- In the full-suite run the gitleaks test in tests/test_hygiene.py was SKIPPED because GITLEAKS_BIN was not set for that run ("no gitleaks program on PATH"). It was run separately with GITLEAKS_BIN and DPLD_REQUIRE_SCAN=1: 10 passed, no skip (evidence-int1-hygiene.txt).
- Expected count was "about 2349 + new tests"; actual 2400 passed (51 more than 2349; not broken down per patch).

## Heads verified (git fetch origin, fresh full clone /tmp/work/int1-base)
pr-1-code d23cf8f0c470e59f2943bca2b3c725a127fa55cc
pr-2-demo-folder f31e2619ad51490ee938956e7b116220422b3c13
pr-3-tests 558d37fe5372f8c378e7ea07c6193a738f4497ed
initial-code 43110e75b8ad96da306d5f8bb66a47ce9fa4323e (43110e7 is an ancestor of pr-1-code? the check printed nothing: `git merge-base --is-ancestor 43110e7 origin/pr-1-code` returned non-zero, so NOT an ancestor; pr-3-tests is 13 commits after 43110e7)
Note: new files (tests/portal_log_probe.js, tests/test_except_clause_hierarchy.py) are created by the patches, so "MISSING" for them is expected.

## A. Placement table (raw: evidence-int1-placement.txt)
Files touched, and presence at pr-1 / pr-2 / pr-3 / initial-code:
- docs-fixes: contract.md, docs/portal.md, docs/tests.md: exist on all four.
- js-portal: portal/pages/log.js, overview.js, portal.js exist on all four; tests/portal_log_probe.js new on all; tests/test_portal_mode.py exists only on pr-3-tests and initial-code.
- py-retry: demo_only/fake_imap.py, fake_smtp_tls.py exist on pr-2, pr-3, initial (not pr-1); tests/test_lead_crm_copy.py exists on pr-3 and initial only; tests/test_except_clause_hierarchy.py new; the other 9 src/load_tools files exist everywhere.
- extra-demo-only: demo_only/portal_demo.py exists on pr-2, pr-3, initial (not pr-1).
- gitleaks-toml-fix-v2: .gitleaks.toml and exceptions.txt exist on all four (content differs at initial-code).

git apply --check per fresh worktree:
| patch | pr-1-code | pr-2-demo-folder | pr-3-tests | initial-code 43110e7 |
|---|---|---|---|---|
| 1 docs-fixes | OK | OK | OK | OK |
| 2 js-portal | error: tests/test_portal_mode.py: No such file or directory | same error | OK | OK |
| 3 py-retry | error: demo_only/fake_imap.py, demo_only/fake_smtp_tls.py, tests/test_lead_crm_copy.py: No such file or directory | error: tests/test_lead_crm_copy.py: No such file or directory | OK | OK |
| 4 extra-demo-only | error: demo_only/portal_demo.py: No such file or directory | OK | OK | OK |
| 5 gitleaks-v2 | OK | OK | OK | error: patch failed .gitleaks.toml:97 and exceptions.txt:26 (written against 558d37f) |
First stack branch where the whole patch applies: 1 = pr-1-code; 2 = pr-3-tests; 3 = pr-3-tests; 4 = pr-2-demo-folder; 5 = pr-1-code.
Consequence: patches 2 and 3 only apply on pr-3-tests (they edit tests that exist only there), so a single push to pr-3-tests carries all five; pushing patches 1 and 5 to pr-1-code would carry through the stack only if the later branches are rebased/merged.

## B. Order table on pr-3-tests 558d37f (clones /tmp/work/int1-o-*, scratch commit after each step; raw: evidence-int1-order.txt)
| order | step results | result tree |
|---|---|---|
| 1,2,3,4,5 | all plain `git apply`, no fallback needed | f621866d970b7e64f91f938f6bbc7aea0b25d90c; 24 files changed, 381 insertions, 35 deletions |
| 5,1,2,3,4 (gitleaks first) | all plain | identical tree f621866d... |
| 1,2,3,4 then 5 | same as first row (repeated as a second clone) | identical |
--3way and -C1 were never needed. Patch 5 and patches 1-4 touch disjoint files.

## C. Merged tree checks (clone /tmp/work/int1-o-A, HEAD = scratch commit 9fed3ae on 558d37f)
(i) gitleaks 8.30.1 (/tmp/work/gl/gitleaks), lint.yml flags: `dir .` -> "no leaks found", exit 0; `git .` -> 14 commits scanned, "no leaks found", exit 0 (evidence-int1-gitleaks.txt). The git scan covers the 5 scratch commits.
(ii) tests/test_hygiene.py with GITLEAKS_BIN and DPLD_REQUIRE_SCAN=1: 10 passed in 11.66s, 0 skipped (evidence-int1-hygiene.txt).
(iii) ruff check: All checks passed; ruff format --check: exit 0; mypy --platform linux: no issues in 26 files; mypy --platform win32: no issues (extra, as lint.yml does); bandit -ll -r src tools scripts: exit 0 (evidence-int1-lint.txt). Venv /tmp/work/int1-venv from requirements-dev.txt with --require-hashes (ruff 0.17.4, mypy 2.4.1, pytest 9.2.0).
(iv) Full serial pytest, one process: command `timeout 2700 python -m pytest -p no:cacheprovider -q -rs`, PATH included venv and /opt/node22/bin. uptime before: load 1.58 1.21 1.82; after: 1.74 1.39 1.44. Result: 2400 passed, 116 skipped, exit 0, 914.67s (0:15:14). Skips: 112 Playwright (not installed), 1 gitleaks (GITLEAKS_BIN unset in this run), 1 load measurement, 1 Windows-only, plus the rest listed in the file.
(v) Node portal probes: no skip line mentions node, so they were not skipped; individual test ids not listed because -q was used (not separately verified per test).

## Not checked
- Playwright/browser tests (not installed; 112 skipped).
- Windows run, the actual CI, CodeQL, SonarCloud, CodeRabbit.
- Whether the 51 extra passed tests are exactly the tests added by the patches (no per-test diff against a baseline run on 558d37f; a baseline run was not done).
- Individual node-probe test results by name.
- Nothing pushed, nothing committed in the public clone; only scratch commits in /tmp/work/int1-o-*.
