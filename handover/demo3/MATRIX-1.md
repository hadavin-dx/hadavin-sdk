# MATRIX-1: test matrix facts for demo3 (facts only, no verdicts)

Written by evidence runner M7 on 2026-11-14 about 03:40 UTC (09:10 IST). Code under test: commit f3c39cf89ec989f032ea48a23cfd824b88da9c68. Every number below was read by me from the raw log tail named next to it. Where a report and a log disagree, both are written and flagged.

## 1. Summary (failures first)

- 30 tests fail in every full run without the program "gitleaks" (a secret scanner), because the runs set DPLD_REQUIRE_SCAN=1, which turns "program missing" from a skip into a failure. The same 30 tests passed once a checksum-verified gitleaks 8.30.1 was present (M4: 72 passed on the three files, and 3714 passed / 0 failed on the full suite).
- Three full runs without gitleaks (three different test orders, Python 3.13) gave identical counts: 30 failed, 3684 passed, 169 skipped, 0 errors (logs m1-run.log, m2-run.log, m3-run.log last lines).
- 166 of the 169 skips were a missing Python module "playwright" (browser tests). With the repo's pinned playwright 1.63.0 and an already-installed chromium, those browser test files ran: 646 passed, 0 skipped (M6).
- Tests that write into the repo tree: three places create an empty git-ignored `data/` folder. Fix-9 (a patch, not committed) removes it; its three-file proofs pass on 3.13 and 3.12. Its own full run finished later: 3690 passed, 199 skipped, 1 xfailed, rc 0, no data/ afterwards (section 5).
- Flakiness: no flaky test was found, but only file-level re-runs were done (see section 4).
- Not run at all: Python 3.11, ruff, mypy, bandit, Windows.
- Differences between report and disk, flagged: (a) M6 report says no data folders appeared, but `/home/user/work/m7-tree/data` (the tree M6 used) exists, empty, created 03:28:38 UTC; (b) m3-run.log and m4-full.log contain no "SKIPPED" detail lines although the final line says 169 skipped (m1-run.log and m2-run.log have 9 such lines each).

## 2. Table of runs

"Order": seed 20261114 = shuffled; seed 0 = reversed file order and reversed tests; seed 987654 = shuffled; default = normal order. All on Python 3.13.18 (`/home/user/work/py313-venv/bin/python -V` printed 3.13.18 when I ran it).

| id | Python | order | files | passed / failed / skipped / errors | rc | wall seconds | log |
|---|---|---|---|---|---|---|---|
| M1 full | 3.13 | seed 20261114 | all tests/ | 3684 / 30 / 169 / 0 | 1 | 881 (pytest 880.06) | raw/m1-run.log (last 2 lines) |
| M2 full | 3.13 | seed 0 (reversed) | all tests/ | 3684 / 30 / 169 / 0 | 1 | 882 (pytest 879.94) | raw/m2-run.log |
| M3 full | 3.13 | seed 987654 | all tests/ | 3684 / 30 / 169 / 0 | 1 | 904 (pytest 903.24) | raw/m3-run.log |
| M1 re-run x3 | 3.13 | default | 3 gitleaks-related files (72 tests) | 42 / 30 / 0 / 0 each | not in log tail (pytest line only) | 34.22, 35.35, 33.60 (pytest) | raw/m1-rerun-default-1..3.log |
| M1 re-run x3 | 3.13 | seed 20261114 | same 3 files | 42 / 30 / 0 / 0 each | not in log tail | 35.27, 34.21, 34.46 (pytest) | raw/m1-rerun-shuf-1..3.log |
| M2 re-run x3 | 3.13 | default | same 3 files | 42 / 30 / 0 / 0 each | not in log tail | 34.04, 34.53, 34.53 (pytest) | raw/m2-rerun/default-1..3.log |
| M2 re-run x3 | 3.13 | seed 0 | same 3 files | 42 / 30 / 0 / 0 each | not in log tail | 37.24, 35.09, 34.61 (pytest) | raw/m2-rerun/reversed-1..3.log |
| M4 no program | 3.13 | seed 20261114 | 3 files | 42 / 30 / 0 / 0 | 1 | 35 | raw/m4-nobin.log |
| M4 with program | 3.13 | seed 20261114 | 3 files | 72 / 0 / 0 / 0 | 0 | 67 | raw/m4-bin-s20261114.log |
| M4 with program | 3.13 | seed 0 | 3 files | 72 / 0 / 0 / 0 | 0 | 66 | raw/m4-bin-s0.log |
| M4 full with program | 3.13 | seed 20261114 (per report) | all tests/ | 3714 / 0 / 169 / 0 | 0 | 924 (pytest 923.92) | raw/m4-full.log |
| M6 run 1 (browser) | 3.13 | default | test_portal_lead_pages, test_portal_browser, test_mode_safety, test_portal_wording_and_masking | 113 / 0 / 0 / 0 | 0 (raw/m6-run1.rc) | 98 (pytest 97.52) | raw/m6-run1.log |
| M6 run 2 (browser) | 3.13 | default | 11 files listed in raw/m6-run2-files.txt (test_portal_api ... test_stage_confirm_browser) | 533 / 0 / 0 / 0 | 0 (raw/m6-run2.rc) | 422 (pytest 421.98) | raw/m6-run2.log |
| B9 three files | 3.13 | default | test_reset_scripts, test_mode_safety, test_data_folder_helper (fix-9 patch applied) | 92 / 0 / 8 skipped / 1 xfailed | 0 | 64.98 (pytest) | raw/b9-three-313.log |
| B9 three files | 3.12 | default | same | 92 / 0 / 8 skipped / 1 xfailed | 0 | 64.36 (pytest) | raw/b9-three-312.log |
| B9 fails-before | 3.13 | default | new test file on unpatched tree | 0 passed / 1 failed ("data exists") | not in log | 32.87 (pytest) | raw/b9-fails-before2.log (b9-fails-before.log: 32.41 s, same failure, first helper version) |
| B9 full | 3.13 | default (serial) | all tests/ | 3690 passed / 0 failed / 199 skipped / 1 xfailed / 0 errors | 0 (rc= line in log) | 945.14 | raw/b9-full-313.log |

Notes on the table:
- M4 full: the M4 report gives seed 20261114 for the full run; the log tail does not show the seed. Not matched to a log line.
- M1/M2 rerun rc: the log tails I read end with the pytest summary line and no rc line, so I could not read an rc for them. The M1 and M2 reports say failed counts only. rc is not stated there for the re-runs either.
- M3 and M4-full: pytest wall time was matched to the last lines above; M4's 3714 equals 3684 + 30 (arithmetic, same test count 3883 total including skips for 3714 + 169).
- Skip total check: 3684 + 30 + 169 = 3883; 3714 + 169 = 3883. Same size of suite.

## 3. The 30 failing tests

Cause (read from the M1, M2, M3 reports and the FAILED/summary lines in the logs): "gitleaks binary not found: put it on PATH or set GITLEAKS_BIN", with DPLD_REQUIRE_SCAN=1. M1 and M2 reports state `which gitleaks` finds nothing and GITLEAKS_BIN is unset. I did not re-run `which` myself.

File split, counted from `raw/m2-rerun/ids-d1` (30 lines):
- tests/test_gitleaks_exceptions.py: 24 (22 near-miss cases, 1 "leading blank", 1 "the exact line is allowed")
- tests/test_gitleaks_semgrep_lock.py: 2
- tests/test_hygiene.py: 4
- Total 30 (24 + 2 + 4).

Same ids in all runs: M3 and M4 reports say their sorted failed ids matched ids-d1 with an empty diff; I did not re-run the diffs but m3-failed.txt exists in raw/. The six M1 and six M2 re-runs each end with "30 failed, 42 passed".

Proof that they pass with the program present (M4):
- Program: gitleaks 8.30.1 (`gitleaks version` printed 8.30.1, per M4 report; not re-run by me).
- Source: https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz, plus the published checksums file in the same release.
- sha256 of the ARCHIVE gitleaks_8.30.1_linux_x64.tar.gz (published in the checksums file downloaded with it equals computed; checked again by the number checker): 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb. The sha256 of the extracted program /home/user/work/priv/gitleaks-bin/x/gitleaks is 88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509 (computed by the checker; the first version of this line wrongly called the archive hash the program's hash).
- Result: 72 passed on the three files (seed 20261114: m4-bin-s20261114.log, 66.52 s; seed 0: m4-bin-s0.log, 65.47 s), and the full suite 3714 passed, 169 skipped, 0 failed (m4-full.log).
- The sha256 and URL come from the M4 report; the raw m4 logs do not contain them. Not matched to a log.

The 30 node ids (copied from raw/m2-rerun/ids-d1):

tests/test_gitleaks_exceptions.py
1. test_a_blank_in_front_of_the_exact_line_is_allowed[leading blank]
2. test_a_near_miss_is_reported_by_gitleaks[CRLF line ending]
3. test_a_near_miss_is_reported_by_gitleaks[capital first letter]
4. test_a_near_miss_is_reported_by_gitleaks[dash suffix]
5. test_a_near_miss_is_reported_by_gitleaks[dot suffix]
6. test_a_near_miss_is_reported_by_gitleaks[equals suffix]
7. test_a_near_miss_is_reported_by_gitleaks[key twice, space between]
8. test_a_near_miss_is_reported_by_gitleaks[last character changed]
9. test_a_near_miss_is_reported_by_gitleaks[look-alike file name]
10. test_a_near_miss_is_reported_by_gitleaks[lower-case name]
11. test_a_near_miss_is_reported_by_gitleaks[other character at the dot of the file name]
12. test_a_near_miss_is_reported_by_gitleaks[other character at the dot]
13. test_a_near_miss_is_reported_by_gitleaks[other folder and name]
14. test_a_near_miss_is_reported_by_gitleaks[other project, letters and digits]
15. test_a_near_miss_is_reported_by_gitleaks[other toml file]
16. test_a_near_miss_is_reported_by_gitleaks[readme]
17. test_a_near_miss_is_reported_by_gitleaks[space and text suffix]
18. test_a_near_miss_is_reported_by_gitleaks[spaces around the equals sign]
19. test_a_near_miss_is_reported_by_gitleaks[text after the file name]
20. test_a_near_miss_is_reported_by_gitleaks[text before the name]
21. test_a_near_miss_is_reported_by_gitleaks[trailing blank]
22. test_a_near_miss_is_reported_by_gitleaks[upper-case name]
23. test_a_near_miss_is_reported_by_gitleaks[upper-case value]
24. test_the_exact_line_is_allowed

tests/test_gitleaks_semgrep_lock.py
25. test_semgrep_lock_allowances_are_narrow
26. test_widening_an_allowance_makes_the_negative_cases_pass

tests/test_hygiene.py
27. test_a_relative_gitleaks_path_still_works_when_the_scan_changes_folder
28. test_gitleaks_reports_a_carriage_return_in_the_key_file_but_not_the_lf_copy
29. test_hygiene_scan_public
30. test_lock_file_hashes_are_allowed_only_at_the_root

Not checked: no test with "semgrep" in its name was shown running in the M4 log (M4 grep: 0 hits); `which semgrep` finds nothing (M2 report). Two of the 30 tests are about a "semgrep lock" and failed only on the missing gitleaks program per their first failure line (M2 report).

## 4. Flaky tests, order dependence, skips, browser run

Flaky tests: none found. What was tested:
- File level: the three failing files were run 3 times in default order and 3 times shuffled by M1 (6 runs), and 3 times default and 3 times reversed by M2 (6 runs). Every one gave "30 failed, 42 passed" (log last lines, section 2). Those runs were whole files, not single test ids.
- The full suite was run 3 times without the program in 3 orders, plus once with the program (4 full runs). Counts were identical across the three without-program runs.
- Browser tests: run ONCE each (M6 run 1 and run 2, default order). No repeat. M6 says run 2 includes timing-sensitive layout and log-poll tests. No flakiness evidence either way for them.
- No test was run on its own, one per process.

Order dependence: none seen in 3 orders (seed 20261114, seed 0 = reversed, seed 987654) plus the default order for file subsets. Browser tests were run in default order only.

Skips (169) grouped, from the M1/M2 log SKIPPED lines (9 lines, sum 169, which I summed myself):
- 166 = playwright module missing: 113 (tests/test_portal_lead_pages.py:113) + 28 (test_portal_browser.py:27) + 22 (test_mode_safety.py:110) + 3 (test_portal_wording_and_masking.py lines 204, 171, 257, 1 each). Sum 113 + 28 + 22 + 3 = 166.
- 1 = Windows only: test_stall_eviction.py:526 ("the reset that destroys the reply happens on Windows only").
- 1 = load measurement: test_server_hardening.py:224 ("measurement run: set LEAD_DESK_LOAD_N").
- 1 = file readable by root: test_n8n_api_url.py:510 ("root (and Windows) can read a file with no permissions"; runs were as root).
- 166 + 1 + 1 + 1 = 169.
- Note: m1-run.log tail showed 3 of its 9 lines; I counted all 9 lines (169 total) in both m1-run.log and m2-run.log. The M1 report lists the 28 and 22 groups too, matching.

Playwright run (M6, from its report and raw logs):
- Versions (M6 report, raw/m6-pip-list.txt not re-read by me): playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1, pytest 9.2.0; new venv /home/user/work/priv/browser-venv; install with `pip install --require-hashes -r requirements-dev.txt -r requirements-browser.txt`, rc 0, 9.7 s.
- Browser found: playwright 1.63.0 expects chromium revision 1243; /opt/pw-browsers already held chromium-1243 and chromium_headless_shell-1243; used by setting PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers. No download, no `playwright install`. pytest-playwright was not used (the tests call the sync API directly).
- Results: 113 passed (97.52 s, m6-run1.log) + 533 passed (421.98 s, m6-run2.log) = 646 passed, 0 skipped. Both rc 0 (m6-run1.rc, m6-run2.rc: "rc=0 wall=98", "rc=0 wall=422").
- Difference to flag: the 166 skipped browser tests are by file 113 + 28 + 22 + 3; M6's run 1 has 4 files (113 passed) and run 2 has 11 files (533 passed). M6 says it did not map the 28/22/3 groups to files. 646 passed is not equal to 166 skipped; I did not investigate the gap (the 11 files in run 2 are not all among the 4 skipped files).
- Whole suite with the browser venv was NOT run in one go: the 646 are only the portal/browser files.

## 5. Tests that write into the repo tree, and things left behind

Empty git-ignored `data/` folder (`.gitignore:1:data/`):
- Created by three sites (M5 hand-back; the three lines were read by the lead): tests/test_reset_scripts.py:67 (a single test), the book fixture at tests/test_reset_scripts.py:82 (used by 23 tests), and tests/test_mode_safety.py:334. They create `<repo>/data` and remove only their own `reset-*` sub-folder.
- M5 control run: 5 other files made no `data/`. The other files were not run one by one, so other creators are not ruled out. There is no m5-report.md on disk (not present); the M5 facts come from the lead's hand-back text and register.md row "M5 ... CLOSED 03:14Z".
- On disk now (my `stat`): empty `data/` in /home/user/work/m1-tree (02:57:14), m2-tree (03:00:31), m3-tree (03:26:32), m4-tree (03:20:49), and m7-tree (03:28:38, the tree M6 ran browser tests in). m5-tree has no `data/` and m6-tree and m6-chk have none. FLAG: the M6 report says no data folders appeared; m7-tree/data exists and was created at 03:28:38, during M6's run 1 window (started about 03:26 UTC).
- M1 and M2 said they could not say which test made it (M1 guessed); M2 said only bytecode appeared (its worktree m2-tree/data exists on disk, 03:00:31). That is a difference between the M2 report ("only `__pycache__/*.pyc`" new in repo tree) and the disk.

Fix-9 patch (builder B9, worktree /home/user/work/m6-tree, not committed, no push; base f3c39cf8):
- Patch file: handover/demo3/evidence/lane3-fix-9.patch, sha256 b56dfdde4af159429a0bed82c37a27a5906bdf2fe43fe5aab62eaa716ebbac08 (computed by me with `sha256sum`; lane3-fix-9-notes.md does not state a sha256 for the patch, so this is not copied from the notes).
- Core helper `book_folder_in_repo(prefix)` copied byte for byte from core patch core-fix-on-frozen-r7e.patch (lines 6838-6855 per notes) into tests/support.py. The patch file in evidence/core/ has sha256 89ca3a2ddeba2a1a1c006d32a38520643861aa94848730b8fcdcf1a46457cee8 (computed by me; equals the value in the notes).
- Added by B9 beyond the copied helper: `import shutil` and `import tempfile` in tests/support.py (the base file lacked them). I confirmed the added lines `+import shutil` and `+import tempfile` are in the patch (patch lines 9 and 15).
- Call sites changed: tests/test_reset_scripts.py (the test at line 67 and the `book` fixture), tests/test_mode_safety.py (test_reset_sh_refuses_when_ps_is_missing); unused `tempfile` import removed from both.
- New file tests/test_data_folder_helper.py: helper tests, a repo-wide guard (runs the two files in a copy of the repo and asserts no `data/` exists afterwards), and `test_a_data_folder_that_is_a_link_is_not_followed` marked xfail(strict=True) because the copied core helper follows a pre-existing `data` symlink (core finding; core r7f is fixing it).
- Proof runs: three-file 3.13 = 92 passed, 8 skipped, 1 xfailed, rc=0 (b9-three-313.log); three-file 3.12 = same counts, rc=0 (b9-three-312.log); fails-before = 1 failed "data exists" (b9-fails-before2.log). Note: B9 notes say "93 passed" for the first helper version (b9-new-313.log, b9-new-312.log) and 92 passed + 1 failed for the core helper before a test fix (b9-new2-313.log); I read all of those tails and they match the notes.
- Full run (3.13, serial) of the patched tree, finished (updated 03:41Z, lead read the tail): `3690 passed, 199 skipped, 1 xfailed in 945.14s (0:15:45)`, then `rc=0`. Afterwards `/home/user/work/m6-tree` has no `data/` (`ls data`: no such file) and `git status --porcelain --ignored` shows only the 4 staged fix-9 changes (tests/support.py, tests/test_data_folder_helper.py, tests/test_mode_safety.py, tests/test_reset_scripts.py). The 199 skips are NOT explained by a skip-reason listing: the lead's reading (not proven) is 169 baseline + the 30 gitleaks tests skipped because this run had no GITLEAKS_BIN and DPLD_REQUIRE_SCAN unset.
- Not run for fix-9: ruff, mypy, bandit, gitleaks, Windows, comparing the test_mode_safety long line to base.

Outside the repo tree:
- /helper.txt, 865 bytes, owner root, created 03:20 UTC (I read the file's metadata; first line `@contextmanager`, i.e. it holds a copy of the helper text). Created by a mistaken command of builder B9, outside the tree and in no patch. Removal was blocked by the safety check; the lead decided to leave it in place.
- Worktrees and scratch dirs named in reports and found on disk: /home/user/work/m1-tree, m2-tree, m3-tree, m4-tree, m5-tree, m6-tree, m6-chk, m7-tree (the first four, m3 and m7 left in place; git worktree records for m2/m3/m4 live in the /home/user/work/src clone's .git/worktrees per the M2/M3/M4 reports; M1 says detached worktree). Scratch: /home/user/work/priv/{m1-tmp, m2-tmp, m3-tmp, m4-tmp, m6-tmp, m7-tmp, gitleaks-bin, browser-venv, shuffle}, /home/user/work/py313-venv, /tmp/runlogs, /tmp/claude-0/n.txt and o.txt (M4 helper files). M2's TMPDIR holds 8 `real-dry-*` folders made by tests; M6's m7-tmp holds bt1, bt2 and 4 `.org.chromium.Chromium.*` dirs. I did not list every one of these myself; those named from /home/user/work/ and /home/user/work/priv/ I saw in `ls`, except priv/browser-venv and priv/shuffle which I did not see in the truncated listing.

## 6. Python 3.11

Not run. `pyproject.toml` line 5 reads `requires-python = ">=3.12"` (I grepped /home/user/work/m1-tree/pyproject.toml). M2 reports /usr/bin/python3.11 is 3.11.18 and has no pytest installed. M2 grepped src/ and scripts/ for version_info, python_requires, requires-python, sys.version and found nothing enforcing it in code; M2 did NOT grep tests/ or CI files. Fix-9 was run on 3.13 and 3.12 only.

## 7. Time per group

Not measurable: the runs used `-q` without `--durations`, so logs show only dots and percentages. Only total wall times exist (section 2). The M2 note "Wall" and the "pytest" figure differ by 1-2 seconds (shell time versus pytest's own timer). M1's 881 s and M2's 882 s ran while other agents used the same machine (M1 report says so), so the figures include shared load.

## 8. Still unreviewed or unproven

- fix-8, fix-2 round 4, fix-5 round 5: no independent review yet (from the lead's brief; not checked by me against the register).
- fix-9: independent review started 03:41Z (read-only egm reviewer); report not yet in.
- No ruff, mypy or bandit run; no Windows run (fix-9 notes, M-reports).
- Core r7f (the fix for the symlink case): not reviewed and not copied into this repo's tests/support.py. The symlink test is an expected failure (xfail strict): it will fail the run by itself once the helper is fixed.
- The 30 gitleaks tests were only proved to pass with gitleaks 8.30.1 on Linux. Not run: with a different gitleaks version.
- Browser tests: single run, default order; not run with the whole suite together.
- The 166 vs 646 count gap (section 4) is unexplained.
- `data/` creators other than the three sites: not ruled out (only 5 other files run together).

## NOT DONE / NOT CHECKED

| Item | Why | Next step |
|---|---|---|
| (closed 03:41Z) fix-9 full-suite result | log finished | 3690 passed, 199 skipped, 1 xfailed, rc=0; no data/ in m6-tree afterwards |
| rc values of the re-run logs (M1 and M2 re-runs) | log tails end with the pytest line only | re-read the log head or re-run with rc written |
| gitleaks version, URL and sha256 | stated in M4 report only; not in the raw m4 logs | re-run `gitleaks version` and `sha256sum` on /home/user/work/priv/gitleaks-bin/x/gitleaks and the archive |
| Seed of M4 full run | log tail has no seed | read raw/m4-full.log head or the m4 run script /home/user/work/priv/m4-run.sh |
| m7-tree/data vs M6 report | disagreement found | ask M6 or re-run run 1 in a clean copy and check |
| m2-tree/data vs M2 report | disagreement found | same as above |
| m5-report.md | file absent; facts from the lead's hand-back | ask for it to be saved, or rely on register.md row |
| Python 3.11 | not run; no pytest on 3.11 | install nothing; if wanted, run on a 3.11 venv with an approved install |
| Single-test and repeated browser runs | one run each | repeat run 2 twice (M6 suggestion) |
| Per-file mapping of 28/22/3 skips to M6 passes | not done by M6 | `pytest --collect-only -q` per file |
| ruff, mypy, bandit, Windows | not run | CI or a local gate run |
| Numbers I could not match to a raw log | listed here | see "numbers not matched" below |

Numbers not matched to a log: gitleaks URL, version 8.30.1 and sha256 551f6fc8...470eb (M4 report only); M4 full seed 20261114; playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1, pytest 9.2.0 and pip rc 0 / 9.7 s (M6 report; raw/m6-pip-*.log not opened by me); chromium revision 1243 (M6 report); the 24/2/4 split came from ids-d1 which I counted, not from a log summary line. | CHECKED 03:50Z (evidence/matrix1-check.md): gitleaks version 8.30.1 matches (the program prints it); playwright/greenlet/pyee/pytest versions match raw/m6-pip-list.txt; chromium 1243 matches /opt/pw-browsers; the 24/2/4 split matches ids-d1. Still only in reports, not in any raw log: gitleaks download URL, M4 full-run seed 20261114 (the run script takes it as an argument and does not record it), pip rc 0, rc of the M1/M2 re-runs (no rc line in those 12 logs).

## WHAT I WOULD DO NEXT (ranked 3)

1. Read the finished raw/b9-full-313.log (counts and rc), then check that no `data/` folder exists in m6-tree, and get an independent review of fix-9.
2. Install the verified gitleaks 8.30.1 (and the browser requirements) in the standard test setup so the suite runs 0 failed and 0 browser skips, then run the full suite once in that setup with `--durations` to get time per group.
3. Resolve the two disagreements about `data/` (m7-tree and m2-tree exist although M6 and M2 reported none) by running each test file alone in a fresh copy, so the list of creators is complete before fix-9 is called finished.

## ADDED 04:01Z: M8 and M9 (facts from raw logs)
- M8 portal flake (11 browser files, 533 tests): run A default order 533 passed in 431.10s rc 0; run B shuffled seed 20261114 533 passed in 439.53s rc 0; 0 failed; tree clean, no data/. Shuffle checked by lane: collect-only md5 differs with the seed. Two runs only. (evidence/m8-report.md, raw/m8-runA.log, raw/m8-runB.log)
- M9 full run 3.13 base with data/ watcher: 3684 passed, 199 skipped, rc 0, 892.56s. Only data/ creator: tests/test_mode_safety.py::test_reset_sh_refuses_when_ps_is_missing (creates `data/` in the repo, leaves it empty). 199 skips = 166 playwright + 30 gitleaks + 3 others. (evidence/m9-report.md, raw/m9-full.log, raw/m9-datawatch.txt)
