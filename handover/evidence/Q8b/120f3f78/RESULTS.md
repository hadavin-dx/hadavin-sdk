# Q8b batch 13 head 120f3f78: PARTIAL evidence (written by the lead; the full evidence run did NOT happen)

## NOT RUN (first)
- Full pytest, q8b_mutants, stage_mutants, mutation_runner_mutants re-runs, fail-before on a148bda6, cost and timing: NOT run. The evidence runner could not get a heavy slot (about 18 jobs queued for 3 slots at 15:58 UTC, mostly builder jobs) and handed back. Re-run when slots are free.
- Not run at all: Python 3.12, semgrep, zizmor, trivy, pip-audit, PostgreSQL 17.

## Ran by the evidence runner (exit 0): ruff check, ruff format --check (338 files), scan_repo, bandit -ll, gitleaks origin/main..HEAD.

## Runner probe (G1 overlap joins 1242 cells, G2 capital hyphen 264, G5 prefixed words 1755, G7 json and breaks 214, G9 bare words 90): head readable and main masked: G1 0, G2 0, G5 240 (the 15 bare words plus prefixes '-', 'en', 're'), G7 0, G9 75 (owner item). Main readable and head masked: G1 160, G5 45, G7 190. Raw: /home/user/build/evidence-raw/Q8bb13-120f3f78/ (9-compare.txt).

## Lead probe (lead-probe-d1.py, made-up value built from parts; head snapshot src vs main 2a8c2aac src, two sources run one after the other, redact() on three forms)
Readable on head, masked on main (key=value and quoted-json forms): x--bypass, x--compass, x--overpass, x--possession, -bypass, and the bare word bypass (owner item). Masked on both: x-bypass, new_bypass. The flag form '--key value' is readable on both sides for every key. This CONFIRMS design D1 and CONTRADICTS the codebase reviewer's reading that x--bypass is readable on both sides.
