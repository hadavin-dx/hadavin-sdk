# Hand-off v19 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16T18:32:18Z
Raw: audit-r460/evidence-v19-independent/ (00-TABLE.md). Postgres 16.15 only. Recorded, not judged.
## Misses first
- F1 guard misses 4 of 21 hostile bodies of a listed definer: DELETE FROM spend and a WITH ... DELETE are clean and the server accepted them (runtime login left 0 rows); TRUNCATE and LEAKPROOF clean but refused by the server. Tables are pinned, statement kinds are not.
- F2 expressions inside allowed shapes unread: CHECK calling pg_read_file, DEFAULT calling current_setting, GENERATED calling a function, two CREATE INDEX with function expressions came back clean (5 of 91).
- F3 run_secrets_v19.sh exits 3 from a folder nobody cannot enter (designed pre-check); 12 of 12 elsewhere.
- F4 runtime login can create a trigger or rule on its own TEMP table named spend (my first run had 2 EXPECT FAIL, 64 of 66); DB-3 functions still wrote the real table.
- F5 reserve of 0, negative, -Infinity, NULL returns no row and no error; settle with negative, -Infinity, NULL likewise; NFC cafe, fullwidth A, zero-width space, NBSP lead, RTL override, case variants are separate budgets.
- F6 gate4_v19.sh, ruff, format, pytest, bandit, PG 14, PG 17, product tests not run.
## Passes
sha256 56 of 56; pg_v19 120 of 120, 24 of 24 controls, 3 of 3 exploits shown; v16 regress 175 of 175; mutants 152 of 152; spell30 30 of 30; chk.py clean; comparator exits 0,1,1,1,1; 66 of 66 money cases incl. 300 random steps; runtime login refused SET ROLE, set_config, CREATE/ALTER/GRANT/DROP on DB-3 objects; banned 0.
