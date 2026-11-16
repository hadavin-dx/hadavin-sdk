Checkpoint (run.py round 4), 2026-11-16, first note
Done: r3 copies kept in raw/.codecopies/run-r3.py and safety-tests-r3.sh; r3 code re-run in this environment with the r3 script: 126 PASS, FAILED CHECKS 0 (so the baseline reproduces). run.py edited (Major A plugin allowlist, Major B hard-link checks, ini above root, deleted target restore, stop_group failure in restore, pid reuse after reap, control-run window, more signals, stop_orphan identity, first-marker fallback, docstring). safety-tests.sh got T36-T46, plugin refusals in T25, and a check count.
Next: run new script on new code, then on r3 code (must FAIL), ruff, hashes, REPORT-runpy5.md.
Blockers: none yet. Commit SHA: none (files edited in place, no commit by instruction).
