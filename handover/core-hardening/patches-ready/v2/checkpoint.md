# C5 v2 checkpoint (UTC)
- 09:30 builder started; scratch /tmp/c5v2/work (b4cce5b + old patches reworked). C-01, A-01, G5 code and tests written; targeted tests green (43 + 18), ruff check/format clean, bandit clean.
- Next: full suite run (started 09:3x, log /tmp/c5v2/v2raw/full.log), mutation re-run of the 9 survivors on a second copy, make patches with diff -u, dry-run on a fresh extract, README.
- Blockers: none yet.
- 09:50 done: patches made with diff -u, dry-run OK alone and in order on fresh extracts, applied tree equals the work tree; full suite 2 failed (also on pristine), 9451 passed; ruff, format, bandit clean; mutation 27 hand mutants, 3 survived (2 equivalent/double-covered, 1 killed after a new test). Real repo only got v2/.
