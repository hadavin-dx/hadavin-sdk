# FINDINGS/LEDGER round 9 cites and commands (agent a8401c8; reviewer words unverified; nothing was run)
Blockers: none. Not checked: any command run, fix-cell byte diff for 35 rows, n8n behaviour claims, stage_server/smtp_catcher cites, lanes files.
Major
1. F-007 fix cell (FINDINGS:110, LEDGER F-007) cites TAKE-CHECKLIST "check 13, line 108"; check 13 is at :257 (108 is the $VALUES row).
2. F-041 fix cell (FINDINGS:117, LEDGER F-041) cites "row 7, line 88"; row 7 is :145, Block R7 :226-236. "marked LEAD FILLS" not found in row 7 / R7. Fix cites and wording.
3. TAKE-CHECKLIST:246 (check 3b) still says T21 uses REVOKE CONNECT (invalid: CONNECT is granted to PUBLIC) and T19 "under 10 s fixed bound" (N=10 s is PROVISIONAL). Point 3b to the F-002 T21 METHOD; drop "fixed bound".
4. FINDINGS:30-31 (NOT COVERED 1-2) say next step is laptop run of T17-T21, M0, M1, K1 (mf.py stand-in flows) - stale vs ORDER 037 item 3 (RUNBOOK:99). Say the take build is tested by T19-T21, re-smoke and Row 4 on the one filled flow set with the real trial credential; M0/M1/K1 history only.
Nit
- T21 step 3 psql needs the role password supplied (PGPASSWORD/service file).
- T21 step 2 count(*) over pg_terminate_backend counts targeted sessions; $PGADMIN needs superuser/pg_signal_backend; state it.
- T20 never sends a body with lead_key absent; add one case.
- F-007 pass line needs heading "Kill case names (one table)" in both files; lead must write it.
- F-041 downgrade check (a) greps `one database|single database`; R7 Part A greps only `one database`; align.
- F-041 cites REPORT.md:622 as "one database" wording; line does not contain it.
- F-029/F-037 pass lines use grep -c (one count per file); use grep -rlF like check 3.
