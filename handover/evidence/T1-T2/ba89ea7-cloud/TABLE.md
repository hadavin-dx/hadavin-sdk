# Evidence table, branch core/T1-T2-tests, head ba89ea751e0197ff64bd20143cd606eaa6529d01 (run on 2026-11-10 UTC)
Note: the local branch name core/T1-T2-tests points at 7a35c36; ba89ea7 (one commit later) was used as the brief says. Worktree: /home/user/build/EV-T1T2-ba89ea7/wt. Venvs: /home/user/build/venv-t1t2-312 and -313 (uv sync --all-extras --group test). Postgres 16 throwaway cluster, 127.0.0.1:56181, trust auth, stopped after use.
Warning: while the runs were going, another session overwrote/committed files in this folder (a first set of logs was truncated). Reruns wrote to /home/user/build/EV-T1T2-ba89ea7/out and were copied here (the -final / -verbose-final files). The truncated first-run files are kept as *.first-run-*.txt.

| # | Command (python) | Result | Exit | Log |
|---|---|---|---|---|
| 1a | ruff check (3.13) | no output | 0 | 1-ruff-check.log |
| 1b | ruff format --check (3.13) | see log | 0 | 1-ruff-format.log |
| 1c | bandit -q -r src demos tools -ll (3.13) | first try: bandit not installed in the venv (exit 1, 1-bandit.log). Rerun with `uvx --python 3.13 bandit` (pin not set; uvx latest): only nosec warnings, no issues | 0 | 1b-bandit.log |
| 2 | python tests/meter_mutants.py (3.13) | 14 mutants L1-L8, S1-S6, all KILLED | 0 | 2-meter-mutants.log |
| 3a | store_time_rules + t2_ledger_replay + t1_meter_cap, py3.12, no DSN | 165 passed, 56 skipped | 0 | 3-nodsn-py312.log |
| 3b | same, py3.13, no DSN | 165 passed, 56 skipped | 0 | 3-nodsn-py313.log |
| 3c | same, py3.12, DSN set | 221 passed | 0 | 3-dsn-py312.log |
| 3d | same, py3.13, DSN set | 221 passed | 0 | 3-dsn-py313.log |
| 3e | dblink tests (tests/demo_askdata test_verify_readonly + test_validate_harm, -k "dblink or extension"), 3.13, DSN set | 2 passed, 269 deselected | 0 | 3-dblink-dsn-py313.log |
| 4 | full suite pytest -m "not live and not perf" (3.13, no DSN) | 4 failed, 10109 passed, 510 skipped, 28 deselected in 245s; the 4 failures are the known tests/test_t1_meter_parallel.py ones (50 of 50 calls admitted) | 1 | 4-full-py313-verbose-final.log |
| 5 | postgres_mutants.py P1-P4 (3.13, DSN set), run alone | baseline rc=0; P1, P2, P3, P4 all KILLED; script works on temp copies; worktree git status clean afterwards | 0 | 5-postgres-mutants-final.log |
| 6a | tests/test_t1_meter_parallel.py, DSN set | 4 failed (50 of 50 admitted for caps 2.00, 3.00, 2.50, 1.50) | 1 | 6-meter-parallel-dsn.log |
| 6b | same, no DSN | 4 failed (same) | 1 | 6-meter-parallel-nodsn.log |

Not run: py3.12 full suite; perf tests (excluded by -m); live tests; full suite with DSN set; test_t1_meter_parallel on py3.12; the repo's own tools/mutation_runner.py. Items 3 and 6 also have the same-named first-run logs; 4 and 5 first-run logs were truncated by the overwrite (4-full-py313.log, 5-postgres-mutants.log in this folder are not valid; use the -final files).
