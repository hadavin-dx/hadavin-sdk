# NOTES: no-demo patches v2 (client copy = demo_only/ deleted)

Base db54e13. Rules: studio R6 (failures first), R7 (class level, mutants), R19 (one pytest process at a time). EGM not run by me (lead's step). Nothing pushed.
Method additions this round: gitleaks 8.30.1 (/tmp/work/gl/gitleaks) with DPLD_REQUIRE_SCAN=1 on every hygiene run; new files `git add -A` before the scan.

## What did NOT work / limits (first)
- nodemo-optional-hygiene-repo-v2.patch applies on db54e13 alone, but on db54e13 alone it only changes the 3 spots that exist there; its real use is on top of P1 v3. ORDER LIMIT: it must be applied AFTER sonar-p1-quickwins-v3 (both edit the import lines at the top of tests/test_hygiene.py; optional-then-P1 fails with "patch failed: tests/test_hygiene.py:15"). P1, P2, P3, nodemo-fix-v2, isort and ci-job apply in any order (all 6 orders of P1/P2/P3 checked).
- nodemo-ci-job.patch was NOT run on a GitHub runner. I ran each `run:` block of the YAML locally under `bash -e -o pipefail` with a small driver (Python 3.13, not 3.12; venv from requirements-dev.txt with --require-hashes --only-binary=:all:). The gitleaks download/checksum step was not run (offline binary used); actionlint is not installed here, so the file is checked with yaml.safe_load plus the repo's own workflow tests (test_workflow_files_parse, test_workflows_are_pinned_and_limited, the curl-flags and `[[` tests: all pass with the file present).
- Not run: Windows, Python 3.12, browser tests (no playwright in the CI-like venv; they skip).

## (1) nodemo-fix-v2.patch (tests/test_except_clause_hierarchy.py, +24/-4)
A row is skipped only if its path starts with `demo_only/` AND the folder `demo_only/` is absent. A product row (src/, load_tools/) can never skip; a missing single demo file while the folder exists fails. It is the reviewer's diff, taken as is.
Measured (evidence-nodemo2-1-narrow-guard.txt):
| case | result |
|---|---|
| row ids vs db54e13 (collect-only) | 49 and 49, identical |
| demo present | 49 passed |
| demo deleted | 43 passed, 6 skipped (6 named rows, reason "demo_only/ was removed") |
| typo in a product row path, demo present, DPLD_REQUIRE_DEMO=1 | 3 failed (FileNotFoundError); same on plain db54e13: 3 failed; old nodemo-fix.patch: 46 passed, 3 skipped (the hole) |
| same typo, demo deleted | 3 failed, 40 passed, 6 skipped |
| demo folder present, fake_imap.py removed | 3 failed |

## (2) nodemo-optional-hygiene-repo-v2.patch (tests/test_hygiene.py, tests/test_no_placeholders.py)
REPO from `__file__` (as v1). New: helper `_need_git_work_tree()` skips (named skip "not a git work tree (a source archive)") when REPO has no `.git`. It is called inside `_git()` when the folder is REPO (this covers the 4 tests that list files with git, including the two P1 added) and in test_hygiene_scan_public just before the scan of the real tree (the canary part still runs without a repository). test_no_placeholders.py already skipped without git. A skip rather than a decorator on each test, so a future test using `_git(REPO, ...)` is covered too. Evidence evidence-nodemo2-4-optional-hygiene.txt (final stack, gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1):
| case | before (v1) | after (v2) |
|---|---|---|
| demo deleted, .git removed, hygiene+placeholders | 5 failed, 56 passed, 1 skipped | **0 failed**, 56 passed, 6 skipped (5 + 1 named) |
| demo deleted, git init + add -A, same two files | n/a | 62 passed (the reviewer's 59 was an older stack; P1 v3 adds hygiene tests) |
| demo present, hygiene+placeholders+gitleaks_exceptions | 106 passed | 106 passed (unchanged) |
| plant a 169.254.169.254 literal in a new src/ file | | git copy: test_hygiene_scan_public FAILS (caught); demo present: FAILS (caught); no-git copy: skipped by name (cannot see files without git) |
The no-git case therefore runs fewer scans than a git copy; that is the stated trade (named skip, not red, not silently green).

## (3) nodemo-ruff-isort.patch (pyproject.toml, +4)
`[tool.ruff.lint.isort] known-first-party = ["demo_only"]`. db54e13 demo deleted: 27 errors (all I001); with the patch: `All checks passed!`, `ruff format --check` clean, with demo deleted (137 files) and present (146). Diff of `ruff check --show-settings` before/after: one line, `isort.known_modules` gains demo_only => FirstParty. evidence-nodemo2-3-ruff-isort.txt.

## (4) nodemo-ci-job.patch (OPTIONAL): new file .github/workflows/nodemo.yml (not lint.yml, so no conflict with P1 v3)
Job `no-demo`: checkout (same SHA pins), setup-python 3.12, gitleaks 8.30.1 install with the same SHA-256 as lint.yml and the curl `--proto/--proto-redir/--tlsv1.2` flags, pinned dev tools with hashes, `git rm -r -q demo_only`, `ruff check` + `ruff format --check`, then the tests in 9 chunks (one pytest at a time, `python -u`) with DPLD_REQUIRE_SCAN=1 and DPLD_REQUIRE_DEMO deliberately unset; a Python summary step requires 9 summary lines, 0 failed/errors, passed >= MIN_PASSED=800 (876 measured without the optional patch, 938 with it). Read-only permissions, no secrets. Needs nodemo-fix-v2 + isort to be green (and optional for the hygiene files to run). Local runs (evidence-nodemo2-5-ci-job.txt):
| case | job result |
|---|---|
| final stack | exit 0, 938 passed, 0 failed, 80 skipped |
| without optional patch | exit 0, 876 passed, 0 failed |
| product-row typo | exit 1, 2 failed |
| conftest mutated to skip every file | exit 1, "only 0 passed, the floor is 800" |
| without isort patch | exit 1, ruff "Found 27 errors" |
| without nodemo-fix-v2 | exit 1, 6 failed |
Cost: about 90 s of tests plus install. Wiring beyond this file (branch protection, required check name `no-demo`) is not done: lead decides.

## Gates on the final stack (evidence-nodemo2-7...)
P1v3 + P2v2 + P3v2 + nodemo-fix-v2 + optional-v2 + isort + ci-job, demo present: `ruff check` clean, `ruff format --check` 150 files clean, mypy linux and win32 "no issues" (28 files), bandit -ll severity Medium 0 / High 0; demo present, DPLD_REQUIRE_DEMO=1, DPLD_REQUIRE_SCAN=1: except_hierarchy + hygiene + no_placeholders + gitleaks_exceptions + workflow_files_parse = 168 passed.

## Line for RUN ON LAPTOP (no-demo)
`demo_only/ deleted (git rm), chunked 9 x pytest, python -u, P1v3+P2v2+P3v2+nodemo-fix-v2+optional-v2+isort+ci-job on db54e13: 0 failed, 938 passed, 80 skipped; ruff check clean (141 files formatted)`. Not the full suite with demo present (not requested; affected files only: 168 passed).

## Apply matrix (evidence-nodemo2-6-apply-matrix.txt)
Each of nodemo-fix-v2, optional-v2, isort, ci-job applies on db54e13 alone. All 6 orders of P1v3/P2v2/P3v2 followed by the nodemo patches apply and ruff stays clean. Files: nodemo-fix-v2.patch, nodemo-optional-hygiene-repo-v2.patch, nodemo-ruff-isort.patch, nodemo-ci-job.patch. Replaces nodemo-fix.patch and nodemo-optional-hygiene-repo.patch (v1; do not use v1 optional with P2 v1).
