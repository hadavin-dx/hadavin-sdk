# A9 evidence, PR66 core/P4d head da08ce2 (EVIDENCE RUNNER, no verdict)
Working copy: /home/user/build/EV-A9 (copy of WT-A9; later `git init` inside the COPY only, to feed tools/scan_repo.py, which needs git ls-files).
| command | rc | counts | log |
|---|---|---|---|
| uv sync py3.13 / py3.12 (WITHOUT --no-build: with it uv refused the editable project, "no binary distribution") | 0 / 0 | | sync313.log, sync312.log |
| ruff check src tests demos tools (3.13 venv) | 0 | All checks passed | ruff-check.log |
| ruff format --check src tests demos tools | 0 | 321 files already formatted | ruff-format.log |
| bandit -q -r src demos tools -ll (scan-group venv) | 0 | only 2 "nosec B102 no failed test" warnings, tools.py:389 | bandit.log |
| python tools/scan_repo.py | 0 | no output | scan_repo.log |
| pytest -m "not live and not perf" py3.13 (10519 collected, 28 deselected) | NOT FINISHED at 60-min box | at 12%: one F seen at ~11% (name not yet known, -q output, no summary) | pytest-full-py313.log (no exit= line yet) |
## NOT RUN
- pytest py3.12 full suite: NOT RUN (queued after py3.13 in run.sh)
- tests/stage_mutants.py: NOT RUN (queued)
- pytest -m perf: NOT RUN (queued)
- Vault contract tests: no vault server here (HADAVIN_TEST_VAULT_ADDR unset); not checked whether they skip.
- dblink-connect test (needs cluster on /var/run/postgresql:5432): not reached yet; ENV failure text unknown.
- HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55400/a9_ev (own db created, createdb rc=0).
## Uncertainty
- `git init` in the copy happened ~after the pytest start; tests that probe git may differ from a plain copy.
- Machine shared with other runners (EV-A8a, P1a); run is slow.
## Restart
Detached driver /home/user/build/chunks/A9/run.sh (pid 3488) keeps running; done-files in /home/user/build/chunks/A9/ (full313.done, stagemut.done, full312.done, perf.done, ALL.done). Read INNER rc from the exit= line at the end of each log.
