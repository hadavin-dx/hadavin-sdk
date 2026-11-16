# Hand-off v16 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16T17:10:17Z
Raw: audit-r460/evidence-handoff-v16-independent/00-SUMMARY.md. Recorded, not judged. PostgreSQL 16.15 only.
Failures first:
1. DB-2 held file spend_decrease_log.sql has 0 lines with lock_timeout; document 5.6(b), 5.6(n) and INVENTORY.md claim it. With another session holding ROW EXCLUSIVE, the three DB-1 files fail 55P03 after ~5 s; DB-2 waited until a 14 s statement_timeout (57014). Builder's 175 of 175 covers the lock check only for the default file.
2. Section 8 lists no sha256 for held files; upgrade file hash only in sha256-v16.txt; line 458 prints v15's DB-2 hash c7e1213d... (v16 file is 4c37aea8...).
3. Cites: sample 60 of 312 (231 distinct): 20 HIT, 4 MOVED, 16 MISSING, 20 RANGE-ONLY by program (unreliable); by hand 39 of 40 non-HIT match; guard/redact.py:1162 unconfirmed.
Passes: sha256 7 of 7 vs sha256-v16.txt; own suite 222 of 223 (the one fail is #1); builder pg_run_v16.sh unchanged 175 of 175 rc 0; secdef owned by non-superuser, search_path pg_catalog, pg_temp, PUBLIC no EXECUTE; temp-table attack fails; reader SELECT only; append-only 42501; key-column refused; lowering fails when log unwritable; 47 of 47 planted mutants caught (own oracle; 4 search_path mutants and 2 index mutants only by catalog checks); banned 0 of 50 files.
Not run: PostgreSQL 14 and 17.10, parallel load, Windows, ruff/pytest/bandit.
