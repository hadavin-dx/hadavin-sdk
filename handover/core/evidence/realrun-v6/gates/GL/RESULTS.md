# GL results (tree RR/tree-GL, head 464fc4a on local-patched, base 61ded9e). Raw logs in this folder.
Tests that can skip without gitleaks: tests/test_gitleaks_exceptions.py, tests/test_hygiene.py (tests/test_codeant_hygiene.py also run; it has no gitleaks skip).
| run | command (short) | head | passed | failed | skipped | errors | wall | notes |
|---|---|---|---|---|---|---|---|---|
| 1 BEFORE | env -u GITLEAKS_BIN -u DPLD_REQUIRE_SCAN, PATH without gitleaks (`which gitleaks` empty); venv312 pytest on the 3 files | 464fc4a | 47 | 0 | 28 | 0 | 10.2s | skips: 24 in gitleaks_exceptions:145, 1 each at test_hygiene:150,344,533,580 (=28) |
| 2 AFTER | GITLEAKS_BIN=RR/bin/gitleaks DPLD_REQUIRE_SCAN=1, unshare -n + lo_up-q4g.py; test_gitleaks_exceptions.py | 464fc4a | 44 | 0 | 0 | 0 | 14.8s | |
| 3 AFTER | same; test_hygiene.py | 464fc4a | 24 | 0 | 0 | 0 | 19.4s | |
| 4 AFTER | same; test_codeant_hygiene.py | 464fc4a | 7 | 0 | 0 | 0 | 0.5s | |
| 5 canary | same; -k hygiene_scan_public over tests/ (test_hygiene.py::test_hygiene_scan_public) | 464fc4a | 1 | 0 | 0 | 0 | 21.9s | 3981 deselected |
| 6 AFTER all 3 | same; the 3 files in one run, TMPDIR=RR/tmp-GL | 464fc4a | 75 | 0 | 0 | 0 | 35.9s | 44+24+7 = 75 |
Failures: none. No hang. Cloud-image-only vs repo causes: n/a (no failures).
Notes: runs 2-4 used TMPDIR=tree-GL/.tmp-run (inside the tree, as the brief's HOW TO says; untracked, removed afterwards; gitleaks dir scans the tree so it was present during runs 2-4; runs 5-6 used RR/tmp-GL outside the tree). git status clean at the end. No files edited.
Not run: all other test files; ruff/mypy/bandit; gitleaks CLI scans outside the tests; Windows.
Processes left: 0 (pgrep pytest|gitleaks = 0).
