# Runner A results (full suite, serial, no xdist, Python 3.12.3)
Command: `TMPDIR=<tmp> PYTHONPATH=<tree>/src unshare -n python src-v6/drivers/lo_up-q4g.py python -m pytest -q -p no:cacheprovider -rfs` (all of tests/; plain `unshare -n` with loopback up, as the brief allows; no network). Trees: main 61ded9e + patch1 + patch2; `git diff --stat | tail -1`: 20 files changed, 776 insertions(+), 152 deletions(-) (plus 9 untracked new files from the patches).

| run | tree | head sha | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|---|
| run1 attempt1 | A1 | 61ded9e | n/a | n/a | n/a | n/a | 238 s | SIGTERM (exit 143) by something other than me, at ~7%; does not count (run1-killed-SIGTERM-attempt1.log) |
| run1 (attempt2) | A1, TMPDIR=tree-A1/.tmp-run (IN tree, brief's original) | 61ded9e | 3779 | 2 | 198 | 0 | 1303 s | no |
| run2 attempt1 | A2 | 61ded9e | n/a | | | | | killed by container restart ~10:22Z at ~7%; does not count (run2-attempt1-killed-by-container-restart.log) |
| run2 (attempt2) | A2, TMPDIR=/home/user/build/rr6/tmp-tree-A2 (outside tree) | 61ded9e | 3781 | 0 | 198 | 0 | 1293 s | no |
| rerun 2 files | A1, TMPDIR=/home/user/build/rr6/tmp-tree-A1 (outside), .tmp-run removed | 61ded9e | 3 | 0 | 0 | 0 | 2 s | no |

Run 1 failures (both environment-caused by the in-tree TMPDIR, same two named by Runner C):
- tests/test_demo_folder_guard.py::test_a_missing_demo_folder_skips_when_allowed_and_stops_the_run_in_ci (first error line not extracted beyond the FAILED line; see run1.log)
- tests/test_no_placeholders.py::test_no_placeholder_text_ships: AssertionError: files that could not be read as text, so not checked: ['.tmp-run/pytest-of-unknown/...desk.db-shm', ...] (tests/test_no_placeholders.py:44)
Run 2 failures: none. Failure lists differ only by those two (run1 vs run2 differ in TMPDIR location, so this is not a pure repeat comparison).
Skips (198, same in both): playwright not installed (browser tests: 28+113+22+1+1+1 = 166), gitleaks missing (24+1+1+1+1 = 28), 4 others (root can read file, ntpath on 3.12, load measurement, Windows-only).
Not run: ruff/mypy/bandit/gitleaks/hygiene scans (out of scope); browser tests (skipped); no test file excluded. Run1 was not repeated with an outside TMPDIR in full (only the 2 files).
Cleanup: no process of mine left; scratch dirs tree-A1/.tmp-run and tree-A2/.tmp-run removed; tmp-tree-A1, tmp-tree-A2 left under rr6/.
