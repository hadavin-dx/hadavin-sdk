# B10 fix-8 r2 notes (checkpoint 1)
Done: tests first (failing on r1 tree: 20 failed, 49 passed, raw/b10-fails-before.log), F8-1..F8-6 fixed, 69 tests in tests/test_domain_labels.py pass, hand mutants on identity.py (raw/b10-mutants.log), patch + on-fix-4-r4 variant made. Full suite started detached.
Next: wait for full.log, then git status --ignored and ls data.
Checkpoint 2: full suite on head 1 (before the hygiene-literal fix): 1 failed (test_hygiene_scan_public: 62-char alphabet literal in my fuzz test), 3781 passed, 170 skipped, rc=1, 1138 s. Fixed (string.ascii_letters), hygiene+domain+edge tests re-run: 98 passed. Full suite NOT re-run on final head (time box).
