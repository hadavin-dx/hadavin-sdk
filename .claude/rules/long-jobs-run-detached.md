---
name: long-jobs-run-detached
description: Background Bash tasks are stopped at ~30 min regardless of timeout; run long jobs (mutation check) detached and check leftovers
metadata:
  node_type: memory
  type: feedback
  originSessionId: 21fd50e7-2e36-4add-87bc-7319957a0764
  modified: 2026-10-01T06:14:50.745Z
---

Background Bash tasks in this environment are stopped at about 30 minutes even with a larger `timeout`. A stopped
`scripts/mutation_check.py` leaves its planted mutation in `src/` (no `finally` runs), and on Windows killing
pytest leaves xdist workers running.

**Why:** 2026-10-01 three checklist runs were killed mid-mutation; each left a mutated file (redaction.py,
observability.py, verifier.py) that had to be restored with `git checkout --`.

**How to apply:** run anything over ~25 min detached with PowerShell `Start-Process ... -RedirectStandardOutput
<log>` and follow the log with Monitor; after any killed run, check `git status` for leftover mutations and
`Get-Process python*` for stray workers before continuing. Related: [[verify-tests-and-evals]].
