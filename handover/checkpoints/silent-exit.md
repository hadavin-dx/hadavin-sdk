# silent-exit checkpoint 1 (17:46Z / IST 23:16)
H1 heavy.sh: no timeout anywhere; ruled out by reading it.
H2 grep of tests/src: no os._exit/dup2/fd close; ruled out for those patterns.
REPRODUCED the cut in one chunk: evidence/silent-exit/run1.log (tests/contracts/test_store_reserve.py, py3.13): log stops at "test_b5_ten_thousand..[postgres] " but run1.xml (junit) shows pytest ran all 101 tests, 0 failures, and the wrapper's own `echo pytest_rc` is missing too. So pytest did NOT die; the LOG lost its later writes.
Working hypothesis: the log file's inode is replaced/cut while the run is writing (writers keep the old inode; heavy.sh reopens by path to write exit=). Testing with inode monitor (run2).
## 17:55Z FINAL: cause found: git pull --rebase in main tree recreates committed in-progress logs (new inode), writers orphaned. See evidence/silent-exit/FINDINGS.md.
