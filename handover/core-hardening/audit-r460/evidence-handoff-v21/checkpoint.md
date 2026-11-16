# Checkpoint v21 builder (round 8)
- 19:10 UTC (00:40 IST on 2026-11-17) start.
- 19:32 UTC (01:02 IST) checkpoint 1. Done: held DB-3 file edited (settle returns no row when rejected); guard v21 built and reproducible from patch_guard_v21.py (also now: m8 EXECUTE-string rule after ';', split_statements `AS end`/`AS case`, call rules for invoker bodies); allow_v21 pins (29); audit prototype v21 (one signature, tgenabled check, pg_depend check); mutants 226 checks 0 failed; chk clean; spell30 30 of 30; pg_v21.py run 1 (3 failures, my own wrong expectations, fixed), run 3 (204 of 204), run 4 (210 of 210); v16 regress run 1 175 of 175. Final runs (pg run 5, regress run 2) started in the background.
- Next: write the v21 main text (chunks chunk_sec0.md, chunk_56c.md, chunk_o.md written; patch script next), other-tracks file, CHANGES, OPEN-FOR-LEAD, INVENTORY, sha256, secrets run, gate4.
- Blockers: none. Not committed, nothing pushed, no spend.
gate4 bg started 19:34 UTC, expected ~6 min, log /tmp/claude-0/gate4_run.out
