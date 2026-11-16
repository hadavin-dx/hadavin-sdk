Terms for this page: see work/t19-terms.md (one glossary for all T19 pages).
Terms used on this page (copied from work/t19-terms.md, 16 Nov 2026; the studio lead owes the missing meanings by Tue 17 Nov 12:00 UTC / 17:30 IST, a proposal):
- T19 = the test that posts the same made-up lead twice to the demo's n8n form address and expects exactly 1 mail, 1 HubSpot write and 1 stored row. It has not run.
- take = the one filmed run of the lead-intake demo on made-up data. film-v5 = the unpatched set of n8n flow files the plan imports. patched copy = the same files with the patches applied (folder NOT RECORDED).
- mf_leads = probably the table that stores leads, in the demo's own Postgres database (unverified). state = its status column.
- NOT RECORDED (no file gives a meaning; do not guess; ask the studio lead, the Claude session doing the technical steps): freeze input, STOP class, F8, smk_count, drive.py, hex tool, CUT, EV, $T, c/c20, C1, E2.
- plan = handover/system-map/inputs/plan-wp6-resmoke-v5.md (cites like "plan:316" mean its line 316).
Purpose: list what the plan inputs/plan-wp6-resmoke-v5.md does not yet say about test T19 (send the same made-up lead twice; expect 1 mail, 1 HubSpot write, 1 stored row). Read: plan lines 183-295 and 404-559. NOT read: 296-403, so an item marked unread may exist there. Terms: work/GLOSSARY.md.
# T19 gap table, round 2 (agent read of plan lines 183-295 and 404-559; lines 296-403 NOT read). 16 Nov 2026 10:40 UTC / 16:10 IST. Unverified model output.
NOT FOUND in the plan: form URL, POST body, reply keys, patched copy name/sha, freeze input, real-take clean-up method, T19 row (plan table has 20 rows, none T19; a row T1 "restart gaps with readiness" exists, so work-file steps T1-0..T1-9 would collide: rename them).
PARTIAL: clean-up (plan 420: `timeout 60 docker rm -f -v hadavin-smoke-pg`, this run only; 462 execution deletion by SQL CUT; 482/502 deletion = container removal); execution table (plan 404 assumes `execution_entity` in db n8n schema public, unproven); import (sha 5fdc659d1 at 236 and 533, unpatched film-v5; take import step in unread 296+); mails/CRM counts (files mail.jsonl, crm.log.jsonl at 422; count commands in unread 364/373/389).
FOUND: hex tool `openssl rand -hex` (270); output folder EV in run.sh (216); take folder $HOME/hadavin-smoke/take-smoke-1 (410); mf_leads state values 'new','processing','done','review','unknown','failed' (281); n8n tables in db n8n, mf_leads in db postgres schema app.
Note: plan runs UNPATCHED film-v5 (supports the open question on the patched copy).
