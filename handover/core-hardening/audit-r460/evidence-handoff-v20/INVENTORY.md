# Inventory, evidence-handoff-v20 (author-run, PostgreSQL 16.15 only, scratch clusters deleted by trap)

`sha256-v20.txt` hashes every file of this folder except itself; it includes this file. Check: `sha256sum -c sha256-v20.txt` inside this folder.

Postgres: `run_pg_v20.sh` (usage in its second line), `pg_v20.py` (177 safety checks, 27 controls, 3 stated exploits; section "v20" holds the round-6 proofs), `pg_v16_regress.py` (175 checks on the v20 files).
Guard: `secdef_guard_v20.py`, `allow_v20.py` (allow-lists, trigger pins, function fingerprint pins, statement-kind pins), `chk.py`, `secdef_mutants_v20.py` (197 checks), `spell30_guard_v20.py` (30 spellings), `secdef_audit_v20.py` (start-up query prototype). Older guards v16 to v19 are kept only for comparison.
Secrets: `run_secrets_v20.sh`, `agent_probe_v20.py` (12 checks; example in section 5.6, L18).
Gate: `gate4_v20.sh` (NOT run as one script; its five commands were run one by one, `raw/raw-gate4-v20-*.txt`), `compare_gate4.py`, `baseline/`.
Build: `patch_v20_main.py` builds `../CORE-PR-HANDOFF-v20.md` from v19. `banned_count_v20.py <paths>` counts banned strings (reads the list at run time).
Held files: `held-sql/` (DB-3 changed in v20; the other four are unchanged copies of v19).

Raw files (`raw/`): `raw-pg-v20-run1.txt` and `-run2.txt` differ only in the timing figure of one m5 line (checked with `diff`); `raw-pg-v16-regress-on-v20-run1.txt` and `-run2.txt` differ in timing lines only (checked with `diff`); `raw-pg-v20-try1.txt` to `-try4.txt` are earlier runs kept as history (try1: one expected FAIL, the NFC line the new agent-id rule changes; try2 to try4: my own harness errors, fixed; try4 is the run after the last harness fix and was followed by run1 and run2); in `raw-gate4-v20-pytest.txt` the vendor strings that the repo's own brand test prints about OTHER folders are replaced by `[BANNED-STRING-MASKED]` (the only edit of a raw file; the counts and failure names are untouched); `raw-secdef-mutants-v20.txt`, `raw-spell30-v20.txt`, `raw-chk-v20.txt`, `raw-secrets-v20-run1.txt`, `raw-secrets-v20-precheck.txt`, `raw-gate4-v20-{ruff,format,bandit,pytest,perf}.txt`, `raw-gate4-compare-v20.txt`, `raw-banned-count-v20.txt`, `raw-sha256-check-v20.txt`.
