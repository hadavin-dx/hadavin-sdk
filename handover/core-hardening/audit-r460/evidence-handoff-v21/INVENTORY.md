# Inventory, evidence-handoff-v21 (author-run, PostgreSQL 16.15 only, scratch clusters deleted by trap)

`sha256-v21.txt` hashes every file of this folder except itself; it includes this file. Check: `sha256sum -c sha256-v21.txt` inside this folder.

Current layer (v21):
- Postgres: `run_pg_v21.sh` (usage in its second line), `pg_v21.py` (safety checks, controls and stated exploits: counts in `CORE-PR-HANDOFF-v21.md` section 0 item 5), `pg_v16_regress.py` (175 v16 checks on the v21 files).
- Guard: `secdef_guard_v21.py` (built by `patch_guard_v21.py` from the v20 guard), `allow_v21.py` (built by `make_allow_v21.py`), `secdef_audit_v21.py`, `chk.py`, `secdef_mutants_v21.py`, `spell30_guard_v21.py` with `spell30_runner_v18_copy.py` and `spellings*.json`.
- Secrets: `run_secrets_v21.sh`, `agent_probe_v21.py`.
- Gate: `gate4_v21.sh`, `compare_gate4.py`, `baseline/`.
- Build of the documents: `patch_v21_main.py` (with `chunk_*.md`, `fill_*.txt`, `gate4_state*.txt`) builds `../CORE-PR-HANDOFF-v21.md` from v20; `patch_v21_other.py` builds `../CORE-PR-HANDOFF-v21-other-tracks.md`. `banned_count_v21.py <paths>` counts banned strings (reads the list at run time). `checkpoint.md`.
- Held files: `held-sql/` (DB-3 changed in v21; the other four are byte copies of v20).

Comparison copies only (not v21; the mutant and Postgres scripts import some of them to show that old designs fail): `secdef_guard_v16.py` to `_v20.py`, `allow_v18.py` to `_v20.py`, `pg_v18.py` to `_v20.py`, `secdef_audit_v18.py` to `_v20.py`, `secdef_mutants_v18.py` to `_v20.py`, `gate4_v18.sh`, `gate4_v19.sh`, `run_pg_v18.sh`, `run_pg_v19.sh`, `run_secrets_v18.sh`, `run_secrets_v19.sh`, `agent_probe_v18.py` to `_v20.py`, `banned_count_v19.py`, `banned_count_v20.py`, `spell30_guard_v19.py`, `spell30_guard_v20.py`, `patch_v18_main.py` to `patch_v20_main.py`, `sha256-v19.txt`, `sha256-v20.txt`, and every `raw/` file whose name has v19 or v20.

Raw files of v21 (`raw/`): `raw-pg-v21-run1.txt` to `-run6.txt` (run 1 and run 2 show failures that were my own wrong expectations; run 6 is the final text), `raw-pg-v16-regress-on-v21-run1.txt` to `-run3.txt`, `raw-pg-version-*`, `raw-secdef-mutants-v21.txt`, `raw-spell30-v21.txt`, `raw-chk-v21.txt`, `raw-secrets-v21-run1.txt`, `raw-secrets-v21-precheck-nopackages.txt`, `raw-gate4-v21-{ruff,format,pytest,perf,bandit}.txt`, `raw-gate4-compare-v21.txt`, `raw-banned-count-v21.txt`, `raw-sha256-check-v21.txt`.

Not in this folder: any product code (nothing of `src/` or `tests/` was changed), any commit, any spend.
