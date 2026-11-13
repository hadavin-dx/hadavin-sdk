# lane3-fix-5 round 3 (builder B5c), fixes review-lane3-fix-5-r2.md (3 blockers, 4 majors, minors)
Patch: evidence/lane3-fix-5-r3.patch (full diff against f3c39cf8; replaces r2). sha256 e677e3d664c9df8ec5082d8dd2487c5eb7772ecc18362c7efce06688abaf709f
Not checked: ruff, mypy, bandit (CI-only, not run by me; E501/isort/noqa checked by hand: awk, grep, reading); macOS, busybox; a command line that is truly only NUL bytes was not built (stand-in `tr` used instead); the earlier unexplained xdist flake of r2 did not recur (xdist -n 2 ran once now: 60 passed) but its cause is still unknown.
Deviation to know: the diff still shows ONE `# noqa: S603` line as added (support.py reset_run), because reset_run MOVED from tests/test_reset_scripts.py (the same line is shown as removed there). `git diff | grep '^+.*noqa'` -> 1 line, `grep '^-.*noqa'` -> 1 line, same text. The new test file has 0 noqa. No higher count than the base.
| # | fix | proof |
|1| 3 long lines wrapped; one more comment line shortened (121 chars). awk length>120 on tests/test_reset_ps_width.py: 0. Other long lines in test_reset_scripts.py (3) and support.py (1) are in the base too (base 3 and 1), unchanged | awk |
|2| new test file calls no subprocess itself: children via support.start_proc (existing Popen helper, closed with stop_proc), stand-in-`ps` runs via reset_run(code=, first_on_path=). No new noqa (see deviation for the moved one) | grep |
|3| support.py imports in isort order (secrets, shutil, socket, sqlite3 ...; unittest before urllib) | read |
|5| support.py no longer imports pytest: reset_run raises ToolMissing(unittest.SkipTest); pytest reports it as skipped (checked with a scratch test: "1 skipped", file removed) | pytest run |
|6| reset.sh proc_args: /proc answer used only if `[[ "$proc_line" == *[![:space:]]* ]]`, else ps -ww, else ps; new test with a stand-in `tr` printing three spaces | on the r2 script it fails: `assert ('   \n', 0) == ('[kernel-thread]\n', 0)`; passes on r3 |
|7| pid-file cases "", "   ", "99999999999999999999" added. True outcome found by running (not copied from the review): exit 0, pid file removed, nothing run. Passes on old and new script (regression guards) | 7 pid-file cases pass on old script |
|8| long line split into nested if blocks (reset.sh proc_args) | read; tests/test_shell_single_bracket.py passes |
|10| "%02d" now an f-string |  |
|9,11,12| no change (harmless; same race as old tests; nothing to update) |  |
Old-script proof (worktree = f3c39cf8 with the r3 patch and f3c39cf8's own scripts/reset.sh): 8 failed, 7 passed (3 width tests and 5 proc_args tests fail; the 7 pid-file cases pass). r2 script + r3 tests: 1 failed (the blank test), 14 passed.
Final run on the r3 worktree (git add -A, python final-venv, TMPDIR and --basetemp outside git): serial tests/test_reset_scripts.py tests/test_reset_ps_width.py tests/test_shell_single_bracket.py tests/test_hygiene.py: exit 0, 226 passed, 4 skipped (gitleaks absent). xdist -n 2 (q1-xdist-venv) on the two reset files: exit 0, 60 passed. No full suite (evidence runner).
git apply --check: fresh f3c39cf8 OK; after claims-stack-on-f3c39cf8.patch + lane3-fix-3-r5.patch + lane3-fix-1-r3.patch (applied in that order): OK.
Worktrees left: /home/user/work/b5c-base (r3 applied, staged); b5c-old, b5c-r2, b5c-chk removed; logs in /home/user/work/priv/b5c-tmp. No process left running.
