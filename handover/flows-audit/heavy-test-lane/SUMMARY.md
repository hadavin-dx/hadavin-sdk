# Heavy test lane summary (queue item H1), 2026-11-16 09:25 UTC / 14:55 IST
Written by flows-audit (main session) from two raw evidence files. Not yet checked by a reviewer.

## What failed or is unverified (first)
- The full test run is NOT green, before or after the patches. Both runs fail the same 2 tests, and both tests only look at files under handover/ (not at the patched source):
  1. tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked ("Port.io" in two handover files; one file is not UTF-8 so it cannot be scanned).
  2. tests/test_repo_rules.py::test_licences_are_proprietary (10 LICENSE files under handover/promotion-inputs/).
  These are not caused by the patches and not by the flows-audit folder. The studio head must decide: fix the handover files or exclude handover/ from these two guards. The repo rules say all gates must be green before a pull request.
- The patched run was not compared test by test with the baseline; only totals and the two failing names match. "Same 2 failures" is read from the two reports.
- A first run of the 70 new tests had AWS_* variables set in the shell (the runner unset them afterwards for the full runs). Result is the same, but it was a rule slip.
- bandit ran from a side venv because `uv run bandit` could not start.
- Not run: demos beyond what pytest collects, Postgres tests, anything needing real services.

## Numbers (raw: evidence-baseline.md, evidence-patched.md)
| run | pytest | ruff check | ruff format | bandit -ll |
|---|---|---|---|---|
| baseline b4cce5b | 2 failed, 9389 passed, 455 skipped (280 s) | rc 0 | rc 0 | rc 0, 0 issues |
| with C-01, A-01, G5-wording | 2 failed, 9404 passed, 455 skipped (282 s) | rc 0 | rc 0 | rc 0, 0 issues |
- 15 more passes after the patches = the new tests. The 70 new and changed tests alone pass (rc 0).
- The three patches apply with `git apply --check` and `git apply`, in order, on b4cce5b.
- This replaces the scratch-tree result in REVIEW.md: the 5 earlier scratch failures do not occur in a full worktree, so they were artefacts of the scratch trees.
