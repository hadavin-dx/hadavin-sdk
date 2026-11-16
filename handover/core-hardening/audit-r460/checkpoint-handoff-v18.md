# Checkpoint, hand-off v18 (UTC 2026-11-16 17:33)
Start. Files copied v17 to v18. Next: guard v18 + mutants, startup query + MA3 test in pg_v18.py, text patches. No commit.

## 17:38 UTC
Done: guard v18 (evidence-handoff-v18/secdef_guard_v18.py, allow_v18.py), mutants 96 of 96 (raw/raw-secdef-mutants-v18.txt; v17 guard misses 39, v16 66; runner's 8 missed spellings all flagged; missing argument exits 2). Next: pg_v18.py (startup query MA2, migrate twice MA3, m2/m4/m7 SQL), then text patch v18, sha256, CHANGES. Blockers: none. No commit.
