# NOTES: nodemo-optional-hygiene-repo-v4.patch

Base db54e13. Studio rules: R6 (failures first), R7 (mutants), R19 (one pytest at a time, all my processes ended). EGM not run by me. Nothing pushed.

## Needs before it: NOTHING. Applies on db54e13 alone and in any order with the 10 patches (measured).

## What failed or is limited (first)
- nodemo-ci-job-v3 is RED on the lead's stack (v3.2 and the others, not v3.1): the no-demo job measured `passed 917, failed 0, skipped 84, collected 1001`; its floor MIN_PASSED=970 (set on the v3.1 stack, 988 measured) fails with "only 917 passed, the floor is 970". Skips 84 <= budget 85 (one spare). Every chunk exit code 0, 0 failed. This is NOT caused by v4 (v4 adds 1 test); the v3.1 stack had ~80 more tests in test_hygiene.py. Not fixed here (a different patch; the number to put there is for the lead: about 917 minus the 18 margin used before = 899). I did not run the job on a GitHub runner; steps were run locally as `bash -e`, Python 3.13, gitleaks step replaced by an offline binary copied to RUNNER_TEMP/gitleaks/gitleaks.
- My first two job runs were my own set-up errors (DPLD_REQUIRE_DEMO=1 left exported in my shell; gitleaks binary not at the job's path): reruns are in evidence-nodemo4-6.
- The test counts of v3 (108 / 102+6) cannot be reproduced on this stack: they came from the v3.1 stack, where P1 v3.1 had added ~90 tests to test_hygiene.py. Same two files, this stack: git copy 27 passed; no-.git copy 22 passed, 5 skipped. Measured v3.1+v3 for comparison: 106+2 = 108 collected there.
- v4 does NOT apply after sonar-p1-quickwins-v3.1 (that patch edits the same import block). v3.1 is superseded by v3.2 in the lead's series.
- Same trade as v3: a no-.git copy cannot run the repository scan (skipped by name, not failed); O3 is equivalent in a git copy.
- Not run: Windows, Python 3.12, GitHub runner, full suite (the lead runs it).

## Design (how it avoids the crlf-guard-v5 hunks)
New file tests/_repo_root.py: `REPO = Path(__file__).resolve().parent.parent` (from the file, not from support, which needs demo_only/), `need_git_work_tree()` (skip when REPO has no `.git`: `.exists()`, so a folder or a file), `need_git_work_tree_for(cwd)` (only when cwd == REPO), `skipped(call, *args)` (test helper).
Edits to existing files, each one line, away from the crlf hunks (which are old lines 3-14, 54-, 147-, 191-, 204-):
- tests/test_hygiene.py: the import line `from support import REPO` becomes `from _repo_root import REPO, need_git_work_tree, need_git_work_tree_for, skipped` (old line 19, after crlf's import hunk ends at 14); one line after `def _git(...)`: `need_git_work_tree_for(cwd)` (old line 45, before crlf's hunk at 54); one line `need_git_work_tree()` after the comment `# 2. the real tree` (old line ~142, between crlf hunks); the new test appended at the END of the file (crlf inserts mid-file).
- tests/test_no_placeholders.py: the import line only.
The test `test_git_work_tree_skip_is_for_this_repository_only_and_accepts_a_git_file` is the v3 test unchanged in logic (no-.git folder skips, also through `_git`; `.git` folder no skip; real `git worktree add` with a `.git` FILE no skip and git works; another folder than REPO never skips), pointed at `_repo_root.REPO` with monkeypatch.setattr.
Touches: tests/test_hygiene.py is also edited by crlf-guard-v5 (no overlap, measured); nothing else in the series edits these three files.

## Apply matrix (evidence-nodemo4-1, driver evidence-nodemo4-drivers/matrix.py; git apply --cached on a temp index)
- Alone on db54e13: v4 applies. (sonar-p1-quickwins-v3.2.1-delta alone does not: it needs v3.2 first, as before.)
- All 110 ordered pairs of the 11 patches: the only pairs with v4 that fail are the two containing v3.2.1-delta without v3.2 before it.
- 300 random orders of the 10 others with v4 inserted at a random place: v4 applied every time and every other patch had the same result as in the same order without v4 (0 differences).
- 300 more random orders with v3.2 before delta, v4 anywhere: all 11 applied, 300 of 300.
The full stack (v3.2, delta, crlf-guard-v5, yaml-trimmed-v2, semgrep v5.1, p2 v2.1, p3 v3, nodemo-fix-v3, isort, ci-job-v3, v4) was applied with real `git apply` in that order and committed.

## Mutants (evidence-nodemo4-3; B = git copy demo deleted, C = no-.git copy; files test_hygiene + test_no_placeholders)
| mutant | B | C |
|---|---|---|
| O1 helper never skips | 1 failed | 5 failed |
| O2 _git does not call helper | 1 failed | 4 failed |
| O3 scan test does not call helper | equivalent in a git copy (27 passed) | 1 failed |
| O4 .git must be a directory | 1 failed | 1 failed |
| O5 REPO one level too low | 13 failed | 13 failed |
| O6 helper inverted | 1 failed | 5 failed |
| O7 _git skips for any folder | 1 failed | 1 failed |
| O8 .git must be a file | 1 failed | 1 failed |
| O9 (mine) _git skips only for other folders | 1 failed | 4 failed |
Baselines (evidence-nodemo4-2): B 27 passed; C 22 passed, 5 skipped, named: test_no_control_characters_in_markdown, test_hygiene_scan_public, test_sh_blobs_no_cr, test_the_secret_scan_files_have_no_carriage_return (all "not a git work tree" or in the crlf file list) and test_no_placeholder_text_ships. The skip location printed by pytest is tests/_repo_root.py:20 (where pytest.skip is called), the test name is in the -v list.

## Other proofs (evidence-nodemo4-4, -5, -6)
- Demo present (DPLD_REQUIRE_DEMO=1, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1 after git add -A and commit): hygiene + no_placeholders + except_hierarchy + gitleaks_exceptions 123 passed; workflow_files_parse + workflow_run_flags 24 passed. Unchanged behaviour: the only change with demo present is where REPO comes from (same path).
- Planted `http://169.254.169.254/latest/meta-data` in a tracked file of the git copy (demo deleted): test_hygiene_scan_public fails and names scripts/planted_probe.py:1.
- Gates on the stack (demo present): ruff check clean; ruff format --check 156 files clean; mypy --platform linux and win32 no issues in 28 files; bandit -ll 0 Medium / 0 High. No-demo copy: ruff check clean (isort known-first-party) and 147 files formatted.
- No-demo job Tests step (see the limit at the top): 9 chunks all exit 0, 917 passed / 84 skipped / 0 failed; red only by the floor of nodemo-ci-job-v3.

## Files
sonar/nodemo-optional-hygiene-repo-v4.patch (new tests/_repo_root.py, 3 files edited); evidence-nodemo4-1..6-*.txt; evidence-nodemo4-drivers/ (matrix.py, mut4.py).
