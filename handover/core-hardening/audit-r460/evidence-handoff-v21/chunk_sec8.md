## 8. Evidence saved this pass (`evidence-handoff-v21/`; `evidence-handoff-v16/` and the older folders stay as they were and are named where a file is carried)

`sha256-v21.txt` hashes every file of `evidence-handoff-v21/` except itself and includes `INVENTORY.md`, which names it; run `sha256sum -c sha256-v21.txt` inside that folder (result of my run: `raw/raw-sha256-check-v21.txt`; not run on a Windows checkout). Only the DB-3 file changed from v20.

| Held file (`evidence-handoff-v21/held-sql/`) | sha256 | Same as v20? |
|---|---|---|
| `spend_nonneg.sql` (DB-1 default) | `5d765255bd1c7477d0bab11c281171b2bb331f0ac4dd08c2151403ba47cc1093` | yes |
| `spend_nonneg_finite.sql` (DB-1 variant) | `bd0409c9bde0ef91dc71f1b28eb960caad4818e01312a669b12e260949d9fe84` | yes |
| `spend_nonneg_upgrade.sql` (DB-1 upgrade) | `fafa71faa08df60423276e4235714e9772f47256d64321f7e7f189691bbf041f` | yes |
| `spend_decrease_log.sql` (DB-2) | `c0c4913eede84ead97a33b1e1d2c3f055987f7e12854936ba27ef0b3585cdaf2` | yes |
| `spend_guarded_writes.sql` (DB-3) | `e2f8017c1975f88c251e6ec2426e3c54f89cf6a3dc61c7f0417d2e8473a075fb` | **no** (v20: `3aa7ed7048a5b9392d87b30a2cbce147bd8b019b0d4ae4dd0cc0e8a4b4f010cc`; the change: a settle that its checks reject returns no row) |

**Files of the current layer (all author-run, Postgres 16.15 only):** `run_pg_v21.sh` (private throwaway cluster, password logins only, one cluster at a time, deleted by a trap), `pg_v21.py` (210 safety checks, 31 controls, 3 stated exploits), `pg_v16_regress.py` (the 175 v16 checks against the v21 files; its `ALLOWED` set carries the one edit of v19), `secdef_guard_v21.py` (built by `patch_guard_v21.py` from the v20 guard; `cmp` shows it reproduces), `allow_v21.py` (built by `make_allow_v21.py`: allow-lists, 14 trigger pins, 29 function fingerprints, statement-kind pins), `secdef_audit_v21.py` (the one `secdef_problems` signature, `policy_for_applied`, `apply_function_grants`), `secdef_mutants_v21.py`, `chk.py`, `spell30_guard_v21.py` with `spell30_runner_v18_copy.py` and `spellings*.json`, `run_secrets_v21.sh` with `agent_probe_v21.py`, `gate4_v21.sh` with `compare_gate4.py` and `baseline/` (two known failing guard tests of the unchanged tree), `banned_count_v21.py` (reads the banned list at run time), `patch_v21_main.py` with the `chunk_*.md` and `fill_*.txt` files (they build this text from the v20 text), `checkpoint.md`, `INVENTORY.md`.

**Copies kept only for comparison, not part of v21:** the v16 to v20 guards and allow-lists (`secdef_guard_v1x.py`, `allow_v1x.py`), `pg_v18.py` to `pg_v20.py`, `secdef_audit_v18.py` to `secdef_audit_v20.py`, `secdef_mutants_v18.py` to `secdef_mutants_v20.py`, the v18 to v20 gate, secrets, probe and patch scripts, and the v19 and v20 files in `raw/`. The mutant and Postgres scripts import some of them to show that the old design fails (the controls).

**Raw files (`raw/`):** `raw-pg-v21-run1.txt` to `-run5.txt` (run 1 keeps my three wrong expectations; run 2 one; runs 4 and 5 are the final text), `raw-pg-v16-regress-on-v21-run1.txt` and `-run2.txt`, `raw-pg-version-*` (the server version line of each run), `raw-secdef-mutants-v21.txt`, `raw-spell30-v21.txt`, `raw-chk-v21.txt`, `raw-secrets-v21-run1.txt`, `raw-gate4-v21-*.txt` and `raw-gate4-compare-v21.txt` (section 0 item 1), `raw-banned-count-v21.txt`, `raw-sha256-check-v21.txt`.

**Carried and not re-run in v21:** the citation, planned-name, import-graph, cycle, snippet and fence programs and their raw files in `evidence-handoff-v14/` to `evidence-handoff-v16/`; the v16 Postgres program `pg_v16.py` (its 175 checks are re-run through `pg_v16_regress.py`).
