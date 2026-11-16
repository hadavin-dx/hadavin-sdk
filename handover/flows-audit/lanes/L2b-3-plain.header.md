# Lane L2b-3-plain: older "plain" flows and table screen v1 (Tier B)
Written 2026-11-16 by builder L2b-3 (static reading only; nothing was run; UNVERIFIED = needs a running n8n, database, mail or CRM stand-in). Paths are relative to handover/demo/.

## Real counts (the brief said 14 files; the real number is 16)
16 files, 213 nodes: n8n-flows/v1-superseded 3 files (19+19+15 = 53), n8n-flows mf-* 4 files (12+12+7+20 = 51), n8n-flows-v3 4 files (12+12+9+19 = 52), n8n-flows-v4 4 files (12+12+10+19 = 53), n8n-table-screen 1 file (4). Source: tools/out/counts.txt. Rows: 213; full-judgement rows 74; `same as` rows 139; TODO rows 0 (see assemble output in the lane report).
Full-judgement rows per file: v1-superseded mf-form 18, mf-hook 18, mf-recovery 15 (all 15: structurally different from v2); n8n-flows mf-recovery 4, mf-sub-crm-mail 4, mf-form 0, mf-hook 0; v3 mf-recovery 2 (rest 0); v4 mf-form 1, mf-hook 1, mf-recovery 2, mf-sub-crm-mail 6; table-screen 3.
Rule used (PLAN-002 section 1, mechanical): a node gets full judgement when the diff file to its successor names it (REMOVED, ADDED, CHANGED line, or an edge line from or to it); everything else is `same as`. Diff partner of each file: v1-superseded -> n8n-flows (mf-*) -> n8n-flows-v3 -> n8n-flows-v4 -> n8n-flows-real-v5; n8n-table-screen -> n8n-table-screen-v2. Note: the nodes of v1-superseded that the diff names as REMOVED are v1 nodes, so v1 gets full rows; the `same as` rows point at the successor file where the node exists. n8n-flows/mf-sub-crm-mail.json has no counterpart in v1-superseded but does have one in v3, so it follows the v3 diff.
Generator side note: I did not run the generator (not my lane). build_mainframe_v1.py looks like the generator of v1-superseded (its text builds SaveLabel, SetCrm=crm_done, StoredState); only REPORT.md:526 and no script mentions it (UNVERIFIED that its output equals the saved v1 json).

## Inputs read and absent files
Read: the 16 json files; tools/out diff files (17 used, one per file pair; the two table-screen diff files are the same content); n8n-flows/v1-superseded/README.txt; n8n-flows/mf_leads.sql, n8n-flows-v3/mf_leads.sql, n8n-flows-v4/mf_leads.sql; n8n-flows-v3/V3-README.md and n8n-flows-v4/V4-README.md only for their folder and generator statements (not as facts); n8n-table-screen/README.md and the first lines of n8n-table-screen-v2/README.md; build_mainframe_v1.py and mf.py (DDL lines only).
Absent: no v1 table DDL file (README.txt and mf_leads.sql both say v1 needs "the same DDL plus: label text" but no such file exists anywhere under handover/demo); DECISION-one-store.md (searched by the plan, absent); n8n-flows-v4/V4-README.md and n8n-flows-v3/V3-README.md exist (not absent). Everything else the brief listed is present.
Not read on purpose: AUDIT-*.md, claims-audit.md, claims-audit/, claims-code-bugs.md. A grep hit line that sat inside HYGIENE-FINDINGS.md or PAGE-STATEMENTS-V4-DRAFT.md was shown only as a one-line hit.

## mf_leads.sql: three copies compared with diff and md5sum
- n8n-flows/mf_leads.sql  md5 bd257c8e556a5942cbf8f01a7ec26ffd (11 columns, no alert columns).
- n8n-flows-v3/mf_leads.sql md5 6cc7cf2daa4816cab951d15654a7ac1b.
- n8n-flows-v4/mf_leads.sql md5 6cc7cf2daa4816cab951d15654a7ac1b (byte-identical to the v3 copy; `diff` printed nothing).
- `diff n8n-flows/mf_leads.sql n8n-flows-v3/mf_leads.sql` shows: a new first comment line and four new columns alert_sent, alert_token, alert_until, alert_attempts. So the schema of the one store exists in TWO versions, plus a fourth copy written inline in n8n-mainframe/mf.py lines 44-47 (same columns as v3, plus `DROP TABLE IF EXISTS mf_leads` before it). Findings L2b3-1 and L2b3-2.
- No v1 DDL (the label column and the state crm_done are needed by v1 flows): L2b3-3.

## LIVE-REFERENCE verdicts (regex (?<![\w-])NAME(?![\w-]) with grep -P over md, txt, py, sh, json, sql under handover/ excluding handover/flows-audit/; hits inside the folder itself are not counted)
- v1-superseded: LIVE-REFERENCE by the rule. Hits (7): n8n-flows/DESIGN-A-README.md:3; n8n-flows/mf_leads.sql:1; n8n-flows-v3/mf_leads.sql:2; n8n-flows-v4/mf_leads.sql:2; REPORT.md:33, 526, 528. All are descriptions; no script, workflow or test runs the folder. Successor n8n-flows (mf-*). Archive candidate, owner yes first (L2b3-14).
- n8n-flows (mf-* files only; the desk-* doors are lane L2a): LIVE-REFERENCE. File names mf-form 23 files, mf-hook 21, mf-recovery 8, mf-sub-crm-mail 10 hit; scripts build_mainframe.py, build_mainframe_v1.py, mf.py and (sub only) n8n-tests/test_crmid_regex.py name them. DESIGN-A-README.md:3 calls v2 "current version" while its own line 38 says v3 alert text supersedes it. Folder name hits: REPORT.md 13, ORDERS.md 3, RUN-ON-LAPTOP.md 2, FILM-README.md 1, PLAN-4-NLITE-FROM-LEAD.md 1, HYGIENE-FINDINGS.md 1.
- n8n-flows-v3: LIVE-REFERENCE. Hits outside the folder: REPORT.md:227, 238, 240, 241; DESIGN-A-README.md:38, 40; RUN-ON-LAPTOP.md:82; HYGIENE-FINDINGS.md:3; n8n-flows-v4/mf_leads.sql:1. No script reads the saved json: RUN-ON-LAPTOP.md:82 and REPORT.md:227 say tests rebuild flows with build_mainframe.py at test time (L2b3-15).
- n8n-flows-v4: LIVE-REFERENCE. Hits: REPORT.md:157, 160; PAGE-STATEMENTS-V4-DRAFT.md:3; DESIGN-A-README.md:45; n8n-table-screen/README.md:17; n8n-table-screen-v2/README.md:27; HYGIENE-FINDINGS.md:3. The table DDL that table-screen points to lives in this folder. Successor n8n-flows-real-v5 (L2b3-15).
- n8n-table-screen: LIVE-REFERENCE. Hits: n8n-table-screen-v2/README.md:3; DOUBTFUL-SCENE.md:13; REPORT.md:37, 111; HYGIENE-FINDINGS.md:3, 92. Successor n8n-table-screen-v2 (different webhook path demo-table-v2). Conflicting run claims: L2b3-13.

## Per-folder summary
- v1-superseded (3 files, 53 nodes): full v1 process: webhook -> Insert (claim by primary key) -> Qualify -> SaveLabel -> CRM search then create -> state crm_done -> mail_sent flag -> mail to the lead -> done; recovery every 30 s re-runs the whole chain for rows untouched 20 s. No lease token, no attempts cap, no alert mail. No dead node by the machine rule (all Y or ENTRY).
- n8n-flows mf-* (v2, 4 files, 51 nodes): claim with token and lease, sub-workflow for CRM and mail, recovery with attempts cap. Alerts are fire-and-forget.
- n8n-flows-v3 (52): alert as state (alert_sent, alert_token, alert_until). n8n-flows-v4 (53): AlertClaim lease 720 s and AlertBackoff node on a send failure. Form, hook and sub-workflow are identical between v3 and v4 (machine diff: no node line).
- n8n-table-screen (4): GET page of mf_leads, 7 columns, 5 s reload.
All 16 files: reachable column is Y or ENTRY on every row (no NO-INCOMING, no UNREACHED-FROM-TRIGGER); settings.errorWorkflow is absent in every file (flow settings are executionOrder v1 and no saved execution data); no disabled node. Semantic dead branches are listed in L2b3-6 and L2b3-9.

## What v1-superseded did that later versions dropped (all from the machine diff and the v1 nodes)
1. Label stored on the row (SaveLabel, RSaveLabel; column label) and returned to the caller (ReplyDone, StoredState). Later: label travels only inside the run.
2. CRM search-then-create through HTTP /search and /create (CrmSearch, CrmCreate). Later: single /upsert keyed hadavin_lead_id (v2 sub: CrmUpsert).
3. Progress state crm_done. Later: states are only new, processing, done, review, unknown, failed.
4. Thank-you mail sent to the lead address (SendMail: toEmail from the request). Later: fixed intake address (L2b3-17).
5. Reply text: v1 verdict new or needs_person and repeat flag with label; later: verdicts done, processing, review, unknown, failed.
What v1 lacked and later versions added: field check of email (Valid), review state, lease and claim_token, attempts cap with MarkFailed, sub-workflow, alerts.

## Secrets and personal data
No secret value in any of the 16 files. Credential names only: n8n-publish-pg (Postgres), mf-mail-smtp (SMTP); credential ids are the placeholders PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID. Environment variable names read: MF_STAGE_URL, MF_CRM_URL, MF_STAGE_TIMEOUT_MS (values not in files). Mail addresses in the files are made-up .test addresses (desk@, alerts@, intake@example.test). Personal data in the design: mf_leads stores email and name as plain text (made-up in the demo); the table screen reads neither.
