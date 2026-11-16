# Plan edit list for real-v5 (builder report, condensed copy, 2026-11-16 about 10:25 UTC = 15:55 IST)
Written: paste-check/plan-v5-real-v5-edits.md (19 edits R1-R20 without R9), checkpoint-real-v5.md. The plan itself was NOT edited. Only read-only git show/diff/cmp ran; a script confirmed each old text occurs exactly once in the plan (19 of 19). Banned-word count 0 on the edit list and checkpoint.
## Failures and unverified first
1. Real-v5 cannot run unchanged on loopback: its CrmUpsert is n8n's HubSpot node (mf-sub-crm-mail.json:94-95, type n8n-nodes-base.hubspot, credential placeholder), which calls the internet and breaks the loopback-only rule (sampler would give EGRESS-FAIL). Edit R8 adds step 2.1b: a derived copy swapping ONLY that node for a loopback CRM stand-in call (POST <CRM_URL>/upsert). Evidence becomes "real-v5 minus one node", not unchanged real-v5. Lead must confirm. No third way found.
2. Glue fill_flows.py is not on this branch. UNVERIFIED: that it accepts `real` for `film`, its printed line ("filled real 4 object" is a guess), that it fills real-v5's tokens and placeholders, that it exits non-zero when a placeholder remains (the repo's own tool exits 3 and has different syntax). Lead: read the glue, fix 2.1's expected line (UNVERIFIED 13).
3. drive.py is not here. Lead check: grep -n -i "film\|MF_" drive.py fill_flows.py.
4. Laptop worktree $HD not checked; in this repo real-v5 is at 5fdc659d1 (6 files), git diff against origin/cloud/flows-audit empty.
5. Workflow ids: real-v5 files carry none; glue assigns smkForm000000001 etc. (R4, R10 UNVERIFIED).
6. Swap code unrun; heredoc python not syntax-checked; n8n 2.46.6 importing HTTP Request typeVersion 4.2 there expected, not run (UNVERIFIED 14).
7. Clean-start names UNVERIFIED 15: the take's database/schema/table not read; plan container uses database postgres, schema app, table mf_leads; TRUNCATE must run as owner/superuser (app role denied N4, N9). OWNER-STEPS v4+ not in builder inputs; written as row CS (section 7) plus lead step in section 10 (R15, R17); lead adds the numbered row to the steps.
8. Still unproven after the edit: HubSpot's real answer (id or vid) and CrmIdOk on a real answer; reply to an empty or missing lead id (mf-form.json:27 copies body.submission_id unchecked). Written in section 9 (R16).
## Verified
- mf-form.json and mf-hook.json byte-identical between film-v5 and real-v5 (cmp 0). mf-recovery.json differs only in fromEmail/toEmail strings. mf-sub-crm-mail.json differs in Qualify ($env.DESK_* vs MF_STAGE_*), two address strings, the CrmUpsert node. So the Claim step (mf-form.json:97, INSERT ... ON CONFLICT (lead_key) DO NOTHING) is the same bytes: cases A, B, B2 on real-v5 with the swap test real-v5's own claim path. This closes static-pass failure 1.
- Lease 45 s at mf-form.json:97 and mf-recovery.json:26; recovery every 30 s; attempts < 3. A second send after the lease is still stopped by the stored row (insert never reads claimed_until): backs the Q15.3 lease sentence (R17).
- Real-v5 queries use INSERT INTO, UPDATE, SELECT on mf_leads (plus FOR UPDATE SKIP LOCKED): smk_app grants hold (R7). Subject '[demo] lead ' at line 258 (R18). crm_stub.py /upsert answers a numeric id so CrmIdOk passes against the stand-in.
- The 7 plan lines containing "film" (120, 126, 236, 284, 298, 302, 543) are covered by R3, R4, R6, R7, R8, R10, R18.
## Edit map (plan line -> edit)
4 R1; before 8 R2 CHANGES table; 120 R3; 126 R4; 223 R5; 236 R6; 284 R7; 298 R8 (+2.1b); 302 R10; 341 R11; 464 R12 (rows 20 to 21); 473 R13; 477 R14; 486 R15 new row CS; 489 R19; 493 R16; 505 R17; 543 R18; 558 R20 (UNVERIFIED 13 to 15).
## Not checked
Glue files, run_real_check_n8n.py, WP6-RUNBOOK.md, OWNER-STEPS v4+. 2.1b adds about 2 min (estimate, not measured; lead decides whether S2 goes 12 to 14 min and steps 151 to 153). That 3.3, drive.py or flow-values.env give 2.1b the CRM address (plan line 271 lists CRM_URL=http://127.0.0.1:8771).
