# checkpoint (EVIDENCE RUNNER, v16 independent)
## 2026-11-16T17:01:01Z t+~10min
done: read doc sections 0,5.6,8,10; sha256 -c on sha256-v16.txt all OK; read the 4 held SQL files and pg_v16.py head.
next: write own cluster script + own check program (pg_ind16.py), run, mutations (40), cites sample 60, banned count.
blockers: none yet. Finding so far: DB-2 file spend_decrease_log.sql contains 0 lines with lock_timeout, but doc 5.6(b)/(n) and INVENTORY say each held file / DB-2 has it. Will test.
