# M2 evidence report (facts only)

Commit f3c39cf89ec989f032ea48a23cfd824b88da9c68, worktree /home/user/work/m2-tree (detached). Python 3.13.18 (/home/user/work/py313-venv/bin/python -V).
Command: python -m pytest -q -rs -p no:cacheprovider --basetemp $TMPDIR/bt -p shuffleorder --shuffle-seed 0 (seed 0 = reversed file order and reversed tests). TMPDIR=/home/user/work/priv/m2-tmp, DPLD_REQUIRE_SCAN=1, PYTHONPATH=/home/user/work/priv/shuffle.
Cloud variables unset before the run (names found in the shell): AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL.
Raw log: evidence/raw/m2-run.log (original /tmp/runlogs/m2-run.log). EXIT_CODE=1 (pytest's own rc), wall 882 s (pytest says 879.94 s).

## Result: FAILED
30 failed, 3684 passed, 169 skipped, 0 errors. Seed 0.

## Failures (30), all with the same first failure line
First line for all 30: `gitleaks binary not found: put it on PATH or set GITLEAKS_BIN` (AssertionError in 6 tests, `Failed:` in 24 via pytest.fail). The run had DPLD_REQUIRE_SCAN=1, which turns "no gitleaks" from skip into failure. `which gitleaks` finds nothing; GITLEAKS_BIN is not set. (`which semgrep` also finds nothing.)
- tests/test_hygiene.py (4): test_a_relative_gitleaks_path_still_works_when_the_scan_changes_folder, test_lock_file_hashes_are_allowed_only_at_the_root, test_gitleaks_reports_a_carriage_return_in_the_key_file_but_not_the_lf_copy, test_hygiene_scan_public
- tests/test_gitleaks_semgrep_lock.py (2): test_widening_an_allowance_makes_the_negative_cases_pass, test_semgrep_lock_allowances_are_narrow
- tests/test_gitleaks_exceptions.py (24): test_a_near_miss_is_reported_by_gitleaks[...] x22 (readme, other toml file, other folder and name, text after the file name, other character at the dot of the file name, look-alike file name, CRLF line ending, key twice space between, text before the name, spaces around the equals sign, other character at the dot, upper-case name, lower-case name, capital first letter, upper-case value, dot suffix, trailing blank, space and text suffix, equals suffix, dash suffix, last character changed, other project letters and digits), test_a_blank_in_front_of_the_exact_line_is_allowed[leading blank], test_the_exact_line_is_allowed
(Full node ids: evidence/raw/m2-rerun/ids-d1.)

## Re-run of each failing test alone (3x default order, 3x reversed seed 0)
The three failing files were run as files (not one test per process): default order 3 times, reversed 3 times. Every one of the 6 runs: 30 failed, 42 passed, same 30 node ids (compared by diff), same first line. Logs: evidence/raw/m2-rerun/default-{1,2,3}.log, reversed-{1,2,3}.log.
Verdict for all 30: always-fails in this environment, independent of order. Cause: the gitleaks program is not installed here and DPLD_REQUIRE_SCAN=1 makes that a failure. I did not install it (instruction: install nothing). Not an order dependence.

## Skips (169), grouped
- 166: could not import 'playwright.sync_api': No module named 'playwright' (113 in test_portal_lead_pages.py:113, 28 in test_portal_browser.py:27, 22 in test_mode_safety.py:110, 3 in test_portal_wording_and_masking.py)
- 1: the reset that destroys the reply happens on Windows only (test_stall_eviction.py:526)
- 1: root (and Windows) can read a file with no permissions (test_n8n_api_url.py:510); the run is as root
- 1: measurement run: set LEAD_DESK_LOAD_N (test_server_hardening.py:224)

## Clean-tree check
- `git status --porcelain` before: empty (0 lines). After: empty. Tracked/untracked-not-ignored files: no change.
- New files in the repo tree during the run: only `__pycache__/*.pyc` (ignored by git; in demo_only, load_tools, scripts, src/lead_desk, tests, tools). No other new file.
- New files under $HOME or /tmp (find -newer marker, excluding my log, TMPDIR, the worktrees, the handover folder): the run itself created none outside TMPDIR. Files that did change in the window are under /root/.cache/pip, /root/.cache/python-entrypoints, /root/.cache/Microsoft/DeveloperTools, /root/.pki/nssdb. I did not run pip or a browser; I cannot say which process wrote them (other agents share this machine); cause unknown.
- TMPDIR (outside every worktree) holds bt, my re-run basetemps, and 8 `real-dry-*` folders created by the tests. They stay for inspection.
- The first re-run in /home/user/work/src: the shared clone's .git was not modified by my own commands except `git worktree add` (added the m2-tree worktree record).

## Extra fact check: Python 3.11 and requires-python
- /usr/bin/python3.11: 3.11.18 (main, Oct 26 2026, 15:28:55) [GCC 13.3.0]. `python3.11 -m pytest --version`: "No module named pytest". Suite not run on 3.11 (as instructed).
- pyproject.toml line 5: `requires-python = ">=3.12"`.
- grep of src/ and scripts/ for version_info, python_requires, requires-python, sys.version: no matches. Nothing in src/ or scripts/ enforces the version in code. (I did not check tests/, CI files or install tooling; pip/uv enforce requires-python at install time by their own behaviour, not verified here.)

## Not checked
Test-level timing; 3.11 behaviour; whether the playwright-dependent tests pass (166 skipped, not run); gitleaks-dependent behaviour (30 tests could not run).
