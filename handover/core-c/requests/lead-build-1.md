# core-c -> lead: three laptop jobs (written 12:24Z, base = origin/cloud/core-c head 7c31dbc97)

HONEST STATE: every ticket that is plan-clean is built or being built: G8 (merged, reviewed twice), G10 (merged, reviewed twice), E9/Q9/G7 (merged), G4 (builder acdb3947 running, files: guard/redact.py _build/_Redactor, runmap.py, defaults.py, tests/b64*), G9 (built on wip-g9; fix builder a7047a97 running on one perf test; files: guard/redact.py sweep/settle/_place_union, runmap.py enforce_map, model_gate.py docstring). The remaining items (G11 = E16 candidate 2, E14, E15) all touch guard/redact.py or runmap.py = overlap with the two running builders, and have no plan-clean ticket yet (G11 needs your accept-or-fix decision on E16). So the three jobs below are the ones with NO file overlap with my builders: they only read cloud/core-c, or touch docs.

Common worktree command (any laptop job):
  git fetch origin cloud/core-c && git worktree add /tmp/lead-c-<item> -b wip/lead-c-<item> origin/cloud/core-c && cd /tmp/lead-c-<item> && uv sync --all-extras --group test
Push only: git push origin wip/lead-c-<item>   (never cloud/core-c; I cherry-pick or merge).

## Job 1 (item "fullsuite"): the NOT RUN whole-suite evidence on the merged head (no files owned; evidence file only)
- Ticket: none needed (acceptance runs named in handover/core-c/REPORT-1200Z.md item 6).
- Runs, on the laptop's cores (12): (a) whole suite incl. perf: uv run --all-extras --group test pytest -q -n 8 --no-header -p no:cacheprovider ; (b) the same on Python 3.12: uv run --python 3.12 --all-extras --group test pytest -q -n 8 ... (pyproject floor is 3.12; the box uses 3.13), (c) PostgreSQL 17 tests if the suite has a marker for it (grep -rn postgres tests | head), using Docker postgres:17; (d) ruff check src tests, ruff format --check src tests tools, uvx bandit -q -r src -ll, uvx gitleaks if available.
- Report: handover/core-c/evidence/LAPTOP-fullsuite.md = exact counts (passed/failed/skipped/xfailed), every failure with id and the first error line, python version, commit sha. Files owned: that one file. Do not fix tests; list them.
- Acceptance: the report exists with sha 7c31dbc97 and both Python versions.

## Job 2 (item "mutants"): every whole-file mutation run on the merged head (no files owned; evidence file only)
- Runs (each prints a SUMMARY line; record it verbatim): python tests/textnorm_mutants.py (256 expected, 244 behaviour / 12 wording), python tests/gate_mutants.py (105 expected, MIN_MUTANTS 105), python tests/redact_mutants.py (94 expected good on its own list: the whole-file summary line "N of N good; problems: [...]"), python tests/g8_mutants.py (35 of 35), python tests/p1d_a_mutants.py (note its count), python tests/stage_mutants.py if present; run them with the runner's own parallel option if it has one, one process per file otherwise (laptop has 12 cores).
- Report: handover/core-c/evidence/LAPTOP-mutants.md with the SUMMARY line of each, every SURVIVED/WRONG_REASON/ERROR with its name. Files owned: that file only. Do not edit mutants or tests.
- Acceptance: one SUMMARY line per file, sha 7c31dbc97.

## Job 3 (item "wording"): SECURITY / CHANGELOG / README wording for the merged items (docs only; no src/tests)
- Ticket: handover/core-c/SECURITY-README-v5.md (stale) + handover/core-c/tickets/SEC-wording-review-3.md / -4.md + the build notes: handover/core-c/evidence/E9-own-output.md, G8-build-notes.md (L15 limit and rows 87-101, L-D13/L-D15/L-D17 stay lead decisions: write the DEFAULT behaviour and mark the decision), G10-build-notes.md and tickets/G10-textfold-deadline-v4.md section 8 (wording for K50/K51: CPU only, no wall clock at any call site, measured maxima named, false-hit rates as a hit rate on this corpus with random values, 5-letter names 63.4 %, 3.9 to 4.5 %), G7 rounds 5-7 refusals (SpelledWorkTooMuch, SpelledMemoryTooMuch, InputTooLarge classes), Q9 (30 changed code points).
- Files owned: handover/core-c/SECURITY-README-v6.md (new, a COPY of v5 with the edits marked) and handover/core-c/CHANGELOG-lines-v6.md (the lines to add). Do NOT edit the repo-root SECURITY.md/CHANGELOG.md/README.md (G4/G9 builders will add their lines; core-c merges the wording last).
- Acceptance: every statement in v6 is checkable against the merged code at sha 7c31dbc97 (cite file:line); no claim of a wall-clock guard, a checksum rule, or "closed" for any item listed as a limit (L15, E10 reach/limits, G4 loose-block limits come later); a fresh egm style review is NOT needed from the laptop (core-c runs it).

Board: all three are listed as WAITING FOR LAPTOP; core-c keeps 2 local builders (G4, G9 fix) and starts an E15 probe agent now.
