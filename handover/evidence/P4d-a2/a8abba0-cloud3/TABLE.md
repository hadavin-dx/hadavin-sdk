# A3 evidence, PR75 `core/P4d-a2` head a8abba0 (EVIDENCE RUNNER, no verdict)
VOID IF THE PR66 HEAD CHANGES (base core/P4d = da08ce2 at read time; A9 tests it). Run 2026-11-10 16:34-17:40 UTC (IST 22:04-23:10), cloud container, Postgres 16.15 (not 17), copy EV-A3 of WT-A3 (no .git), uv sync --locked WITHOUT --no-build (editable package needs a build; with the flag uv refuses).

| Check | Command (env) | Result | Raw file |
|---|---|---|---|
| ruff check | `ruff check src tests demos tools` (3.13 venv) | rc=0 "All checks passed" | ruff-check.txt |
| ruff format | `ruff format --check src tests demos tools` | rc=0, 325 files formatted | ruff-format.txt |
| scan_repo | `python tools/scan_repo.py` (in WT-A3, needs git) | rc=0 | scan_repo.txt |
| bandit | `bandit -ll -q -r src demos` | rc=0 (two nosec warnings only) | bandit.txt |
| contracts, Postgres required | `HADAVIN_REQUIRE_PG=1 pytest tests/contracts/ -rs -q`, 3.13, own DB | 735 passed, 1 skipped (Stubber), exit=0, session-end check silent | req.txt |
| a1 harness mutants | `a1_mutants.py` (my reading of ticket a1-1..a1-6, copy EV-A3-mut, baseline 32 passed first) | 8 variants, 8 KILLED, killer test named per row | mut.txt, a1-6-manual.txt |
| full pytest 3.13 and 3.12 | `pytest -m "not live and not perf" -rs`, CI env minus Vault | NO RESULT: see below | full-*-attempt*.txt, chunks/ |
| perf (`-m perf`) | 3.13 | NO RESULT: log has dots then `exit=0`, no pytest summary line | perf.txt |

## What failed or is uncertain (first)
1. NO valid full-suite result on either Python. Five attempts (3 whole-suite, then chunked) ended with the log cut off and no pytest summary: whole-suite 3.12 `exit=1` at about 18%, 3.13 `exit=1` at about 4%, 3.12 again `exit=1` inside `test_b5_ten_thousand_..._[postgres]`; chunked 3.12 c1 (contracts) `exit=0` after 48%, c2 `exit=0` after 21%, c3 `exit=0` at 96%. The same contracts directory ran to the end in the REQUIRE_PG run (735 passed). So pytest ends early or its output is lost on some runs; cause NOT found. `exit=0` with a cut log cannot be read as pass; `exit=1` with a cut log means at least one failure that I could not see (no FAILED lines survived). Likely next step (not done): rerun a chunk with `--junitxml=<file>` so the result survives a lost stdout, and check which test redirects or closes file descriptor 1.
2. The 60-minute box was mostly spent waiting for a heavy slot (25 waiting `heavy.sh` jobs machine-wide; my first job started 16:50 UTC, after 15 min).
3. a1 mutants: the repo has no runner for a1-1..a1-6 (the ticket lists them in words), so rows a1-1 to a1-6 are my reading; a1-5 ("pairing check dropped") is my guess (memory pair returns two separate stores). a1-6 first showed KILLED without failure lines in the log (my line filter); a manual re-run shows 1 FAILED + 5 ERROR (a1-6-manual.txt). Mutated files were restored (diff against EV-A3 clean).
4. dblink-connect tests: ENV only, not run on purpose (dblink extension exists on the cluster: pg-info.txt; the tests that need it were inside the lost runs).

## NOT RUN
- Python 3.12 and 3.13 full suite (no valid result, see 1); chunks 312-c4, 313-c2..c4 never started; 313-c1 started and was stopped by me at the box end.
- perf tests (no valid result).
- Postgres 17.10 (only 16.15 binaries exist on this machine; CI image is 17.10).
- Vault contract tests (no Vault server; `HADAVIN_TEST_VAULT_ADDR` unset).
- gitleaks, Trivy, CodeQL, SonarCloud, CodeRabbit, real GitHub check list.
- Mutation runner (`tests/stage_mutants.py`, `tests/mutation_runner_mutants.py`): not in scope of the row.

## Restart
Chunk driver: `/home/user/build/chunks/A3/driver.sh <312|313>` (runs c1..c4 through heavy.sh; markers `/home/user/build/chunks/A3/<ver>-<chunk>.done`); add `--junitxml` in `chunk.sh` first. Processes I started: all stopped (0 left). Databases a3_ev* on cluster 55400 left in place (drop with `dropdb`).
