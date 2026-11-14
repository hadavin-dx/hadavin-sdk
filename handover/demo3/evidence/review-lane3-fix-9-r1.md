# Review of lane3-fix-9 (read-only egm codebase-details reviewer, saved by lane3, 2026-11-14 ~03:48Z)
Tree /home/user/work/rv-fix9. Reviewer ran nothing. Result: 0 Blocker, 0 Major, 7 Minor.
Checked: tests/support.py:609-626 character-identical to core patch helper (evidence/core/core-fix-on-frozen-r7e.patch:6838-6855; sha256 not recomputed; path /handover/core/fix/... does not exist in this tree, the copy is at evidence/core/). Imports shutil/tempfile present; call sites import the helper; `tempfile` removed from both files, `shutil` still used.
1 Minor: no evidence in the log that data/ is absent after the full run (b9-full-313.log:88-89 has the summary and rc=0 only; notes line 54 says after-run check not done at hand-back). Default db path ./data/desk.sqlite3 (src/lead_desk/config.py:422); scripts/start_all.sh:18-20 mkdir -p its parent. Other Config() users (test_loader_missing_demo, test_smtp_provider, test_stamp_locks_and_budget, test_live_claude, test_crm_hubspot) only grepped, not read; test_live_claude.py:527-578 subprocesses not read.
   [lane3 fact: after the run I checked `ls data` in m6-tree: absent; git status --porcelain --ignored only the 4 staged changes. That check is in my heartbeat 83 and MATRIX-1, not in the raw log.]
2 Minor: guard covers only the two files (AFFECTED, tests/test_data_folder_helper.py:64); a session-wide check or final-run check would close it.
3 Minor: guard never checks done.returncode (test_data_folder_helper.py:172-173); `"passed" in stdout` also matches "3 failed, 80 passed"; still fails on old code (b9-fails-before*.log "assert True is False"); inner run cannot recurse.
4 Minor: helper race between data.exists() and mkdtemp with concurrent users; no xdist configured; core-helper property, raise in core r7f rather than edit here.
5 Minor: guard copy uses `git ls-files`; fallback copies only src, tests, scripts, demo_only, pyproject.toml; failures there hidden by finding 3.
6 Minor: symlink case is the xfail(strict) (test_data_folder_helper.py:113-128), honest; refusal accepted as (RuntimeError, OSError).
7 Minor: RuntimeError catch in the body-failure test is fine (match="boom").
Tests vs old code: only the guard proves old leak (b9-fails-before.log, b9-fails-before2.log: 1 failed). Windows: helper tests run there; symlink test skipped.
Not checked: tests/ruff/mypy/bandit; sha256; other stray files; other chdir(REPO) tests (test_hygiene, test_sonar_p2_feed_optional, test_codeant_desk) counted not read; Windows/PowerShell; line length of test_reset_scripts.py:66.
