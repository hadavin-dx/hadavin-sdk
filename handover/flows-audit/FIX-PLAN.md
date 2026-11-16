# FIX-PLAN (ordered). Take first (ORDER 003). P = patch file ready (applies cleanly, checked by check_patches.sh); T = needs a test run in n8n on the laptop; O = owner decision.
1. F-001 (Blocker) P: apply patches/F-001-one-ddl.patch, then make n8n-mainframe/mf.py:45 read that file and ship it beside the v5 flows. Verify: T on a fresh database, alert_sent column exists, one alert mail.
2. F-002 P+T: apply patches/F-002-take-key-check-and-claim-error-path.patch to build_mainframe.py, rebuild real-v5 and film-v5 with the V5-README commands (lead evidence: rebuild diff is only the 3 new nodes, Claim onError, 5 edges), run T1 (empty key) and a Postgres-down case.
3. F-003, F-004 P: apply the two text patches; supply the lane3 run count for statement 14; then re-read both files against the take.
4. F-005, F-006, F-007 O: one rehearsal for scene 6; decide what the video says about the HubSpot path; map the lane3 K names.
5. F-008, F-009, F-010, F-011 O: privacy trade-off for saved runs, webhook auth credential, two database roles, n8n on Postgres.
6. F-012 to F-018 T: lease per row, stage idempotency, alert cap, remove dead IFs, order CrmIdOk before SetCrmId, merge mf-form and mf-hook, run the UNVERIFIED items (T17, T18, kill tests) on the laptop.
7. F-019 to F-023: retire the desk doors, name owner for the journal, rename DESK_URL for the stage, fix the table-screen status text.
8. F-024 to F-028: archive per CUT-LIST.md after the owner's yes; fix stale numbers.
