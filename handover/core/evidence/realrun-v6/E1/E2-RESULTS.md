# E2 RESULTS (13:00-13:03Z). Tree /home/user/build/rr6/tree-E2, test: tests/test_no_placeholders.py::test_no_placeholder_text_ships, run alone.
Nothing failed in any of the 9 runs. The question's premise (fails with TMPDIR in tree) was NOT reproduced.
Tree state: git status --short (31 lines, saved in git-status.txt): HEAD 61ded9e, patches applied uncommitted; tests/conftest.py and 8+ test files show M versus HEAD (patch 1/2 content). I could not compare to a "ee3d6ce baseline" or RR/tree-E2old: that folder does not exist, so I do not know whether E1's fix.patch changed tests.
Package path printed was under the tree (see first line of each log).
| run | mode | TMPDIR | rc | result | wall s |
|---|---|---|---|---|---|
| 1 | out | RR/tmp-E2/t | 0 | 1 passed in 0.17s | 0.64 |
| 2 | in | tree-E2/.tmp-run | 0 | 1 passed in 0.12s | 0.51 |
| 3 | out | out | 0 | 1 passed in 0.12s | 0.44 |
| 4 | in | in | 0 | 1 passed in 0.12s | 0.49 |
| 5 | out | out | 0 | 1 passed in 0.15s | 0.60 |
| 6 | in | in | 0 | 1 passed in 0.14s | 0.52 |
| 7 | out | out | 0 | 1 passed in 0.18s | 0.57 |
| 8 | in | in | 0 | 1 passed in 0.13s | 0.57 |
| 9 | other in-tree name tree-E2/scratch-x | | 0 | 1 passed in 0.12s | 0.52 |
Logs: run-out-N.log, run-in-N.log, run-scratchx-1.log. In-tree dir deleted before each run; helper script RR/tmp-E2/run1.sh.
Observation (not a judgement): the test file list comes from git ls-files --others --exclude-standard and keeps only regular files. This test creates no files in TMPDIR, so the in-tree folder stayed empty; empty folders are never listed. A failure would need a file with a marker inside the in-tree TMPDIR (e.g. from another test run in the same session); I did not run other tests.
Not run: all other test files. Processes left running: 0 (started by me).
