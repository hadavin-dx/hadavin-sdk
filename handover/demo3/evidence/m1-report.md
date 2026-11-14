# M1 evidence report (facts only)

Commit f3c39cf89ec989f032ea48a23cfd824b88da9c68, worktree /home/user/work/m1-tree (detached). Python 3.13.18 (full `pip list` in raw/m1-env.txt).
Command: `python -m pytest -q -rs -p no:cacheprovider --basetemp=$TMPDIR/bt -p shuffleorder --shuffle-seed 20261114` with TMPDIR=/home/user/work/priv/m1-tmp, DPLD_REQUIRE_SCAN=1, PYTHONPATH=/home/user/work/priv/shuffle. Started 02:52 UTC (08:22 IST).
Log: raw/m1-run.log (original /tmp/runlogs/m1-run.log). EXIT_CODE=1 (pytest's own rc). Wall 881 s (pytest says 880.06 s). Seed 20261114.

## Failures first
Counts: 30 failed, 3684 passed, 169 skipped, 0 errors.
All 30 failures have the same cause (read from the log): `gitleaks binary not found: put it on PATH or set GITLEAKS_BIN` (the tests insist because DPLD_REQUIRE_SCAN=1). `which gitleaks` finds nothing; GITLEAKS_BIN is unset. First failure line for each: `E  Failed: gitleaks binary not found: put it on PATH or set GITLEAKS_BIN` (24 tests), or `E  AssertionError: gitleaks binary not found: ...` followed by `assert None` (6 tests: the 2 hygiene ones + the 4 others below).
Failed tests (30):
- tests/test_gitleaks_exceptions.py: test_the_exact_line_is_allowed; test_a_blank_in_front_of_the_exact_line_is_allowed[leading blank]; test_a_near_miss_is_reported_by_gitleaks[...] x 22 (other project letters and digits, last character changed, dash suffix, equals suffix, space and text suffix, trailing blank, dot suffix, upper-case value, capital first letter, lower-case name, upper-case name, other character at the dot, spaces around the equals sign, text before the name, key twice space between, CRLF line ending, look-alike file name, other character at the dot of the file name, text after the file name, other folder and name, other toml file, readme)
- tests/test_gitleaks_semgrep_lock.py: test_semgrep_lock_allowances_are_narrow; test_widening_an_allowance_makes_the_negative_cases_pass
- tests/test_hygiene.py: test_hygiene_scan_public; test_gitleaks_reports_a_carriage_return_in_the_key_file_but_not_the_lf_copy; test_lock_file_hashes_are_allowed_only_at_the_root; test_a_relative_gitleaks_path_still_works_when_the_scan_changes_folder
Exact node ids: raw/m1-rerun-default-1.log (`-rf` summary).

## Re-runs of the failing tests (files tests/test_gitleaks_exceptions.py, test_gitleaks_semgrep_lock.py, test_hygiene.py, whole files, 3x each)
| order | run 1 | run 2 | run 3 |
|---|---|---|---|
| default | 30 failed / 42 passed | 30 failed / 42 passed | 30 failed / 42 passed |
| shuffled (seed 20261114) | 30 failed / 42 passed | 30 failed / 42 passed | 30 failed / 42 passed |
The failing set is identical in all 6 runs (compared by node id). Classification: ALWAYS FAILS in this environment (missing program), not flaky, not order-dependent. Cause is explained by the log (no gitleaks program). Whether they pass with gitleaks installed was NOT checked (I may not install anything).
Logs: raw/m1-rerun-default-{1,2,3}.log, raw/m1-rerun-shuf-{1,2,3}.log. Note: I re-ran whole files (72 tests), not single node ids; the other 42 in those files passed every time.

## Skips (169), grouped by reason
- 28 + 22 + 1 + 1 + 1 + 113 = 166: `could not import 'playwright.sync_api': No module named 'playwright'` (test_portal_browser.py 28; test_mode_safety.py 22; test_portal_wording_and_masking.py 3; test_portal_lead_pages.py 113). So no browser test ran.
- 1: test_stall_eviction.py:526 "the reset that destroys the reply happens on Windows only"
- 1: test_server_hardening.py:224 "measurement run: set LEAD_DESK_LOAD_N"
- 1: test_n8n_api_url.py:510 "root (and Windows) can read a file with no permissions" (I ran as root)

## Time per group
Not measurable: -q without --durations gives only dots and percent. Total 881 s only.

## Clean-tree check
- Before: `git status --porcelain` empty (0 lines); `git ls-files | wc -l` = 248 (raw/m1-status-before.txt).
- After: `git status --porcelain` empty; ls-files = 248. No tracked file changed, no new untracked non-ignored file.
- New in repo tree (ignored, so invisible to status): `__pycache__/` folders (demo_only, load_tools, scripts, src/lead_desk, tests, tools) and an EMPTY folder `/home/user/work/m1-tree/data/` created 02:57:14 UTC during the run (`data/` is in .gitignore). Which test made it: not determined; guess: a test that starts the desk with its default relative data folder (candidates by name: tests/test_reset_scripts.py, tests/test_portal_browser.py, or src smtp_outbox/smtp_provider default path). GUESS ONLY.
- Outside TMPDIR: nothing found under $HOME or /tmp that is attributable to this run. (Other new things appeared but belong to other agents: /home/user/work/m2-tree/data, /home/user/work/priv/m2-tmp, /home/user/hadavin-sdk/.git and handover/demo3/REPORT.md.) Ignored: python bytecode, /tmp/claude-0, /tmp/*.log of the harness.
- Tests that write into the repo tree: the `data/` folder above (guess) and bytecode caches. Outside TMPDIR: none seen.
- Note: the run used cwd = repo root, which is why a relative `data/` ended up there.

## Environment
- Before the run my script unset every variable starting AWS_, ANTHROPIC_, AZURE_, GOOGLE_, GCP_, GCLOUD, CLOUDSDK, OPENAI. Names before: raw/m1-envnames-before.txt (had ANTHROPIC_BASE_URL, AWS_ACCESS_KEY_ID, AWS_CA_BUNDLE, AWS_SECRET_ACCESS_KEY, CLOUDSDK_*). Names during the run: raw/m1-envnames-run.txt. One name still containing "CLOUD" remained: CLAUDE_CODE_ARTIFACT_TYPE_CLOUD_CREATE (a harness flag, not a credential).
- The re-runs of the 3 files were started from my shell WITHOUT unsetting the cloud variables (the 3 files are hygiene/scan tests; they failed on the same missing program). Disclosure: not clean-env.
- Other jobs (M2 etc.) ran on the same machine at the same time, so the wall time includes shared load.

## Not checked
- Behaviour of the 30 failing tests with gitleaks present.
- Which test created `data/`.
- Per-group timings.
