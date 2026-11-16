# checkpoint (EVIDENCE RUNNER, v16 independent)
## 2026-11-16T17:01:01Z t+~10min
done: read doc sections 0,5.6,8,10; sha256 -c on sha256-v16.txt all OK; read the 4 held SQL files and pg_v16.py head.
next: write own cluster script + own check program (pg_ind16.py), run, mutations (40), cites sample 60, banned count.
blockers: none yet. Finding so far: DB-2 file spend_decrease_log.sql contains 0 lines with lock_timeout, but doc 5.6(b)/(n) and INVENTORY say each held file / DB-2 has it. Will test.
## 2026-11-16T17:04:52Z
done: ind16.py main run: 222 of 223 pass; the 1 FAIL = DB-2 file has no lock_timeout (57014 after my 14s cap, not 55P03). 
next: mutations (50), builder rerun, cites, banned, summary.
