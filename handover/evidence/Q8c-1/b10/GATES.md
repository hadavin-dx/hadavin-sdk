# Q8c-1 batch 10, gates (written by the batch 11 builder from the raw logs; the batch 10 builder's own GATES.md was not found)

Read this first. The batch 10 builder's `GATES.md` could not be found on disk when batch 11 started (round 10 review issue 8 asked for it to be committed). This file was written afterwards from the raw logs now committed in `logs/`; it says only what those logs show. Nothing here is a new run.

| Gate | What the log shows | Log |
|---|---|---|
| `ruff check` | "All checks passed!" | `logs/g-ruff.log` |
| `ruff format --check` | "326 files already formatted" | `logs/g-fmt.log` |
| bandit `-ll` | only warnings ("nosec encountered", "Test in comment"); the exit code was not written to the log | `logs/g-bandit.log` |
| `tools/scan_repo.py` | no output besides the uv warning; the exit code was not written to the log | `logs/g-scan.log` |
| `tools/policy_page.py --check` | no output besides the uv warning; the exit code was not written to the log | `logs/g-page.log` |
| `tests/stage_mutants.py` | 37 of 37 good | `logs/g-stage.log` |
| `tests/policy_mutants.py` real clock | 141 of 141 good, weak 0 of 141 | `logs/g-pm-real.log` |
| the same with `--day 2026-12-11` | 141 of 141 good, weak 0 of 141 | `logs/g-pm-1211.log` |
| the same with `--day 2026-12-12` | 141 of 141 good, weak 0 of 141 | `logs/g-pm-1212.log` |
| gitleaks | "no leaks found", 14 commits scanned | `logs/g-gitleaks.log` |
| push | new branch `wip/cloud-q8c1-b10` | `logs/g-push.log` |
| full `pytest -m "not live and not perf"` | **This log has no result:** it ends at 10 percent with no summary line. The pass count and exit code for batch 10 come from the independent run only (`../d8441218/RESULTS.md` and the round 10 review report: exit 0, 10908 passed, 13 skipped) | `logs/g-full.log` |

Three things are not shown by these logs: the exit codes of bandit, the repository scan and `--check` (no output is not an exit code), and a finished full test run. Batch 11 ran the full suite on its own final head (see `../b11/GATES.md`).

Fail-before of batch 10 (corrected). `logs/fail-before.log` shows **3 failed, 368 passed** in 9.19 seconds: the batch 10 builder ran three test files (guard, docs, changelog) on a clean copy of c6bd7108. That is not the whole picture. The independent run (`../d8441218/RESULTS.md`, items c) on the same old tree gives: the four changed test files copied in alone, **7 failed, 365 passed, 1 error** (the error is a collection error: `tests/test_notes_lines_check.py` needs `tools/notes_lines_check.py`, which c6bd7108 does not have); with `tests/policy_mutants.py` also copied in, **3 failed, 369 passed, 1 error** (the same collection error). The count depends on which files are copied, and the notes file test cannot be collected on the old tree at all. The numbers to quote for batch 10 are those two independent ones.
