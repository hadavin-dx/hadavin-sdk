# Checkpoint, hand-off v19 (UTC 2026-11-16 18:05)
Start. v18 evidence copied to evidence-handoff-v19/ (v18 files untouched). Next: guard v19 allow-list + mutants, then DB-3/DB-2 SQL minors (m1, m2, m7), pg_v19, text patch v19, CHANGES, resolve. No commit.

## 18:40 UTC (clock of this machine; start was 18:01)
Done: guard v19 (real allow-list, 152 mutant checks 0 failed, runner's 30 spellings 30 of 30), DB-2 and DB-3 files v19 (m1 INSERT record, m2 settle needs the day row, m7 statement_timeout, day window, agent-name rule, reserve of 0), pg_v19.py 120 safety checks + 24 controls + 3 stated, twice; v16 regress 175 of 175 twice; secrets 12 of 12 + one-line precheck. Next: text patch of the main file (readiness Ma1 to Ma4 and minors), CHANGES, OPEN-FOR-LEAD, resolve, sha256. Blockers: none. No commit.
