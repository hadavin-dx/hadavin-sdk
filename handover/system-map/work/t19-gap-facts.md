Terms for this page: see work/t19-terms.md (one glossary for all T19 pages).
Terms used on this page (copied from work/t19-terms.md, 16 Nov 2026; the studio lead owes the missing meanings by Tue 17 Nov 12:00 UTC / 17:30 IST, a proposal):
- T19 = the test that posts the same made-up lead twice to the demo's n8n form address and expects exactly 1 mail, 1 HubSpot write and 1 stored row. It has not run.
- take = the one filmed run of the lead-intake demo on made-up data. film-v5 = the unpatched set of n8n flow files the plan imports. patched copy = the same files with the patches applied (folder NOT RECORDED).
- mf_leads = probably the table that stores leads, in the demo's own Postgres database (unverified). state = its status column.
- NOT RECORDED (no file gives a meaning; do not guess; ask the studio lead, the Claude session doing the technical steps): freeze input, STOP class, F8, smk_count, drive.py, hex tool, CUT, EV, $T, c/c20, C1, E2.
- plan = handover/system-map/inputs/plan-wp6-resmoke-v5.md (cites like "plan:316" mean its line 316).
Purpose: facts for filling gaps in test T19 (send the same made-up lead twice; expect 1 mail, 1 HubSpot write, 1 stored row). 'plan' in every cite below = inputs/plan-wp6-resmoke-v5.md. $T = the test output folder; key = the lead id being tested. Terms are in work/GLOSSARY.md; labels run (a)/(b), DM, C1, G.2, v5 138 in the premortem line: meaning not recorded.
# Facts that fill gaps in work/t19-and-stored-data-steps.md (agent read, 16 Nov 2026; check each cite before use). Made-up data only.
- Form door: POST, path mf-form, responseMode responseNode (flowcheck/in/real-v5/mf-form.json:6-8). Take n8n port 5690 (inputs/plan-wp6-resmoke-v5.md:121); URL form http://127.0.0.1:5690/webhook/mf-form is INFERRED from plan:316, never printed as one string.
- Body fields: submission_id, email, name (mf-form.json:25-39). Exact JSON shape, key format, and the 422/503 reply bodies: NOT FOUND (dn1_common is not in the folder).
- Mails counted: lines in $T/mail.jsonl whose subject == "[demo] lead " + key (plan:389); alert mails to alerts@example.test counted separately (flowcheck/in/builder/mf.py:72). smtp_catcher.py source NOT in the folder.
- CRM writes counted: lines in $T/crm.log.jsonl with op == upsert and lead_key == key (plan:364, 373).
- mf_leads columns: lead_key (primary key), email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent, created_at, updated_at, alert_* (flowcheck/in/builder/mf.py:45-47; the F-001 patch has another CREATE TABLE, not compared).
- Database: postgres on host port 55433 (plan:121); n8n's own database is separate (plan:288). So "mf_leads is in n8n's database" is wrong.
Still missing for a runnable T19: import folder and sha, the hex tool, output folder, "freeze input" meaning, clean-up method, a T19 row in the plan, step T1-8.
PREMORTEM ROUND 3 (rehearsal fails tomorrow, agent read, most likely first): (1) fill tool for $env not built, no builder named; run (a) can start first; (2) T19 not runnable as written; (3) "rehearsal passed" rule undefined (DM choose, C1 "D", runs (a) vs (b)); (4) Docker/n8n/Postgres down or laptop asleep, no preflight row (premortem-r1 item 6); (5) wrong flow copy imported, sha not named, no import row; (6) leftover list exists only after `end`, v5 138 and G.2 match looser than the card.
