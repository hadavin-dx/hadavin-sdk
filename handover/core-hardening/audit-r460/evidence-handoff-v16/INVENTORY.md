# evidence-handoff-v16 inventory (every file named in the v16 documents exists here)
Run order and commands: `bash pg_run_v16.sh <out_dir> /home/user/hadavin-sdk/.venv/bin/python /home/user/hadavin-sdk/src <1|2>` (own cluster folder, password logins, random passwords never printed, deleted by a trap). Baseline gate: `gate4_v16.sh`. Hashes: `sha256-v16.txt`.
| File | What |
|---|---|
| `pg_v16.py`, `pg_run_v16.sh`, `secdef_guard_v16.py` | the Postgres program, its runner and the SQL-file guard prototype (not product code) |
| `held-sql/spend_nonneg.sql`, `spend_nonneg_finite.sql` | v15's two files, byte-identical |
| `held-sql/spend_nonneg_upgrade.sql`, `spend_decrease_log.sql` | new in v16 (the second: kill-switch record, append-only triggers, `lock_timeout`) |
| `raw-pg-v16-run1.txt`, `raw-pg-v16-run2.txt`, `raw-pg-version-v16.txt` | 175 of 175 checks each, PostgreSQL 16.15 |
| `gate4_v16.sh`, `raw-gate4-base-{ruff,format,pytest,perf,bandit}.txt`, `gate4-base-console.txt` | baseline on the unchanged tree (pytest rc=1: 2 baseline failures) |
| `raw-import-graph-v16.txt` | the v14 import-graph program with `--table CORE-PR-HANDOFF-v16.md`: 0 new cycles |
| `banned-count-v16.txt` | counts only |
| `patch_v16_main_{a,b,c,d}.py` | the scripts that turned v15 into v16 (replay aid; after a replay, `174 of 174` becomes `175 of 175` and the two timing numbers are edited by hand) |
Not here, carried and not re-run: citation, planned-name, snippet, fence and cycle programs of v14 and v15.
