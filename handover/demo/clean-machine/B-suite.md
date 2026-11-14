# Agent B: full suite run

Head: f3c39cf (clone of origin main into <scratch>/repo, <scratch> = the agent B scratch folder). Python 3.12.3, fresh venv in <scratch>/venv.
Not done: the bible and handoff files named in the preamble were not read (no studio folder path was given in the brief); no R-numbers cited. No EGM step run (evidence runner task; EGM is the lead's step). No sub-agents, no model calls, no spend. Nothing pushed; the clone was not edited.

## Install (as docs/tests.md says)
1. python3.12 -m venv; then `python -m pip install --require-hashes -r requirements-dev.txt`: rc 0, 24 s. Gave pytest 9.2.0, ruff 0.17.4, bandit 1.9.4, mypy 2.4.1.
2. `python -m pip install --require-hashes -r requirements-browser.txt`: rc 0. Gave playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1. The browser was already present on this machine (build 1243 in the folder named by PLAYWRIGHT_BROWSERS_PATH, already set); `playwright install chromium` was not run. Node 22 was on PATH.
3. gitleaks: NOT installed on this machine. See finding F1.

## Run method
Resumable runner: 92 test files (tests/test_*.py, sorted) split into 12 chunks (7 to 9 files each, `split -n l/12`). One pytest process per chunk, `python -m pytest -q -rs -p no:cacheprovider <files>`, rc written from pytest itself (`pytest ...; echo $? > rc`), one process at a time. Env: DPLD_REQUIRE_SCAN=1, git commit signing off for tests. Loopback only, no network namespace used. Collected: 3883 tests (`--collect-only`).
After the lead's note: GITLEAKS_BIN was set to the gitleaks file (version 8.30.1) for chunks 02b, 03b and 04 to 11. Chunk 04 was first started without it, killed by process group before finishing, its partial log deleted and re-run with it. Chunks 00 and 01 ran without GITLEAKS_BIN and passed (they do not use gitleaks).

## Per chunk results (rc = pytest's own exit code; wall = seconds)
| chunk | files (first .. last) | no gitleaks | with gitleaks |
|---|---|---|---|
| 00 | ai_after_claim .. codeant_desk (8) | rc 0, 112 passed, 76 s | not needed |
| 01 | codeant_fakes .. env_numbers (8) | rc 0, 624 passed, 165 s | not needed |
| 02 | except_clause_hierarchy .. gitleaks_semgrep_lock (7) | rc 1, 26 failed, 204 passed, 28 s | 02b: rc 0, 230 passed, 46 s |
| 03 | http .. later_approval (9) | rc 1, 4 failed, 183 passed, 99 s | 03b: rc 0, 187 passed, 107 s |
| 04 | later_messages .. load_tools (8) | | rc 0, 310 passed, 51 s |
| 05 | loader_missing_demo .. mutation_guards (8) | | rc 0, 211 passed, 60 s |
| 06 | n8n_api_url .. portal_demo (8) | | rc 0, 968 passed, 2 skipped, 288 s |
| 07 | portal_drawer_long_name .. portal_mode (8) | | rc 0, 207 passed, 257 s |
| 08 | portal_phone_layout .. reset_ps1_links (7) | | rc 0, 172 passed, 224 s |
| 09 | reset_scripts .. shell_single_bracket (7) | | rc 0, 512 passed, 1 skipped, 65 s |
| 10 | slow_sender .. stage_confirm_browser (8) | | rc 0, 259 passed, 70 s |
| 11 | stall_eviction .. workflow_run_flags (6) | | rc 0, 87 passed, 1 skipped, 15 s |

Run-1 failures (no gitleaks), all with the same message "gitleaks binary not found: put it on PATH or set GITLEAKS_BIN":
- chunk 02, 26 tests in tests/test_gitleaks_semgrep_lock.py: test_the_exact_line_is_allowed, <long test name>, <long test name>, <long test name>, and 22 cases of <long test name>.
- chunk 03, 4 tests: <long test name>, test_hygiene_scan_public, <long test name>, (all in tests/test_hygiene.py; the log has 3 headings and 4 tracebacks: test_hygiene_scan_public shows two, at lines 153 and 347 of that file; I did not work out why one test heading shows two tracebacks).
With gitleaks present all of these passed (chunks 02b and 03b).

## Totals with gitleaks present (chunks 00, 01, 02b, 03b, 04 to 11)
3879 passed, 4 skipped, 0 failed = 3883 (equals the collected count). Summed wall time of the chunks: about 1380 s (23 min), serial; the README says about 20 minutes.

## Skipped tests (4), with the reason printed by -rs
1. tests/test_n8n_api_url.py line 510: "root (and Windows) can read a file with no permissions" (this run was as root).
2. tests/test_path_confinement.py line 284: "ntpath.isreserved needs Python 3.13".
3. tests/test_server_hardening.py line 224: "measurement run: set LEAD_DESK_LOAD_N".
4. tests/test_stall_eviction.py line 526: "the reset that destroys the reply happens on Windows only".
Hygiene scan: it RAN (not skipped) in chunk 03b with DPLD_REQUIRE_SCAN=1 and gitleaks 8.30.1; test_hygiene tests passed. No browser test was skipped (Playwright, browser build and Node were all present). docs/tests.md says 3 skipped on the earlier run; this run has 4 (item 1 is new: it appears because the run was as root; docs/tests.md lists "the secret scan, the load measurement, one Windows-only test" and does not list items 1 or 2 by name). Whether the docs count of 3 was measured as a non-root user was not checked.

## Findings
- F1 (docs/tests.md, "How to run the tests", and README line 130; docs/settings.md line 124): a stranger who follows the install lines and runs the suite with DPLD_REQUIRE_SCAN=1 gets 30 failures (26 + 4) because no gitleaks program is installed. The README line 130 does not mention gitleaks. docs/settings.md line 124 explains that GITLEAKS_BIN is the path of the program and that DPLD_REQUIRE_SCAN makes a missing program a failure, but no file I read tells where to download gitleaks or which version (docs/tests.md names 8.30.1 only in the measurement sentences; the CI workflow installs it with a checked checksum, which a stranger would have to find). Stranger's action: unknown; would have to search for gitleaks, and without it must run without DPLD_REQUIRE_SCAN, which skips or fails the scan. Wording I would add to docs/tests.md after the Linux install lines: "To run the secret scan tests, install gitleaks 8.30.1 (the version the tests were measured with), put it on PATH or set GITLEAKS_BIN to its file, then set DPLD_REQUIRE_SCAN=1. Without gitleaks, those tests fail when DPLD_REQUIRE_SCAN is set, and skip when it is not." (docs/settings.md already states the second part; the install source and the version are the gap.)
- F2: the docs say "about 20 minutes" for the full run; measured serial wall time about 23 minutes (sum of chunk times), no failure other than F1. Consistent enough; recorded as a fact.
- F3: the README line 130 says the supported Linux combination is Python 3.12 and requirements-dev.txt; the browser lock file is documented only in docs/tests.md ("Browser tests"), not in the README. A stranger following only the README gets browser tests skipped (not tested here, since I installed it from docs/tests.md).

## Not checked
Ruff, mypy, bandit were installed but not run (not in the task). Coverage run not done. Windows not tried. Running as non-root not tried. The studio bible/handoff were not read.

## Files
Logs in <scratch>/logs: chunk.NN.log, chunk.NN.done (rc), chunk.NN.wall, and chunk.02b/03b equivalents; runner <scratch>/run.sh; install logs pip.log, pip2.log. This report: <scratch>/B-suite.md
Processes started by me: all stopped (runner finished, ALL.done written, no pytest left running).
Token use: not measured by me.
