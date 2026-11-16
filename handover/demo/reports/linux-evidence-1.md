# linux-evidence-1 (ORDER 199) - raw output, no verdicts
Date: 2026-11-09 ; host: 4 cores, 16086 MB RAM, Linux 6.18.44-fc-v310; Python Python 3.12.3; tree: dpld-fix1-aed689a.tar.gz unpacked in /tmp/dpld (no .git in the tarball, so commit aed689a not verifiable here); deps via pip --require-hashes -r requirements-dev.txt.
gitleaks 8.30.1 linux_x64 downloaded, sha256 551f6fc8...70eb checked OK against lint.yml.

## 1. Full pytest -q x3 (cmd: pytest -q -rA --tb=short -p no:cacheprovider)
full-1 exit=1 2 failed, 40 passed in 31.67s 09:57:02
full-2 exit=1 2 failed, 40 passed in 25.34s 09:57:28
full-3 exit=1 2 failed, 40 passed in 24.90s 09:57:53

Failures (all 3 runs identical):
run1: FAILED tests/test_hygiene.py::test_hygiene_scan_public - RuntimeError: git gr...
run1: FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
run2: FAILED tests/test_hygiene.py::test_hygiene_scan_public - RuntimeError: git gr...
run2: FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...
run3: FAILED tests/test_hygiene.py::test_hygiene_scan_public - RuntimeError: git gr...
run3: FAILED tests/test_hygiene.py::test_hygiene_wordlist - AssertionError: set HYG...

test_hygiene_scan_public detail (run 1):
11:    raise RuntimeError(f"git grep failed ({p.returncode}): {p.stderr[-300:]}")
12:E   RuntimeError: git grep failed (128): fatal: not a git repository (or any of the parent directories): .git
111:FAILED tests/test_hygiene.py::test_hygiene_scan_public - RuntimeError: git gr...

Same test in a COPY of the tree with 'git init' and one commit (/tmp/dpld-git, not the delivered tree): tests/test_hygiene.py -> 1 failed (test_hygiene_wordlist, needs private list), 3 passed (incl. test_hygiene_scan_public with gitleaks 8.30.1 on PATH). gitleaks printed 'leaks found: 6' in its stderr while the test passed; I did not inspect what the 6 are (not checked).

## 2. Concurrency tests x50 each (one pytest process per run, -k NAME)
test_concurrent_same_source_ref passed=50 failed=0 of 50 09:58:37
test_retry_twice_concurrent passed=50 failed=0 of 50 09:59:18
test_ten_parallel passed=50 failed=0 of 50 10:00:13
test_reconcile_counts passed=50 failed=0 of 50 10:00:58

Failure logs: none written (all 200 runs passed).
