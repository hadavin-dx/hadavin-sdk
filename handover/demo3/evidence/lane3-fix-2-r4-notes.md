# Lane 3 fix 2, round 4 (B2d)
Base f3c39cf8 + lane3-fix-2-r3.patch. Worktree /home/user/work/b2d-base. No commit, no push; ruff/mypy/bandit not run (CI only).

## Failures and unproven first
1. Tests were NOT strictly written first: envnum/kind code came first, tests second; fails-before was then run on the plain r3 tree (raw/b2d-fails-on-r3.txt, 22 failed). That run used a stand-in for the missing env_file_problem, so some failures there are only the missing function; the behaviour failures are: non-ASCII key accepted by one kind, inner-space live key accepted, "password" in live texts, live_claude imports smtp_provider, 3 copies of the rule, stats/ledger path inside a file passed, ENAMETOOLONG/EINVAL/Windows codes -> unreadable, symlink-loop db path = RuntimeError traceback (REAL r3 defect, found by the loop test; fixed in lockfile.lock_path -> LockUnavailableError, exit 2), approvers message, constants comment, docs claims, docstring order, check_start=None crash. Tests that pass on r3 (regression guards): start-up call order, class guard (r3 had no hits), over-long db name no traceback.
2. Full serial suite on the final head: 3809 passed, 237 skipped, EXIT_CODE=0, 1133 s (raw/b2d-full.log). Tree unchanged: patch sha256 before and after identical (51a2af1b...). Skips: node/playwright/gitleaks missing, Windows-only, root-only (chmod test skipped as root).
3. Non-root run (user b2dtest, copy of tree WITHOUT .git, 9 files): 758 passed, 4 failed, 3 skipped; the 4 failures are hygiene tests that need git (not a git repository in my copy): my copy method, not the code. The chmod tests ran and passed as non-root (raw/b2d-nonroot.log).
4. r6 re-cut (lane3-fix-2-r4-on-fix-1-r6.patch) checked by 193 tests (new test file, settings_lane3, portal_wording, hygiene) on that tree, not by a new full suite. Reverse order (fix-2 before fix-1-r6) does NOT apply: both change the same exit-code lines; fix-2 goes after fix-1-r6.
5. Not done / contested: item 13 (bind boundary) left as is (contested); check_secret_files stays after the lock (declined), so a refused key file leaves <name>.lock (now documented). write_stats still swallows OSError other than path-inside-file. Windows not tested.

## Rung table
Rung 1 reuse: extended envnum.py (read_secret_file, env_file_problem, path_kind). Rung 7 custom code only for these refusals. Rungs 2-6 do not apply (local start-up checks).

## Changes
One neutral envnum.read_secret_file(path, what, noun, *, strip_inner_space=False); crm_hubspot, smtp_provider (thin wrapper, strip only for SMTP password, raises SendRefused) and live_claude use it; no kind imports another; SECRET_FILE_MAX_BYTES moved to constants.py. env_file_problem + file_problem_text shared by book_problem, refuse_unusable_file, live ledger, both stats files. path_kind: ENAMETOOLONG, EINVAL, winerror 123/21/1921 -> absent. loader.check_secret_files uses getattr/callable. lockfile.lock_path loop fix. read_approvers names DESK_APPROVERS_FILE. server.main docstring order; constants comment. Docs: settings.md live key row and :111, contract.md steps 2,3,7 and exit line, limits.md exit lines (lead-book wording).
New tests: tests/test_one_key_file_rule_and_path_walk.py (name avoids the *secret* gitignore rule); one assertion text updated in tests/test_settings_lane3.py.

## sha256 and git apply --check (all rc 0): see raw/b2d-patch-sha256.txt, raw/b2d-apply-check.txt, raw/b2d-apply-check-r6.txt
