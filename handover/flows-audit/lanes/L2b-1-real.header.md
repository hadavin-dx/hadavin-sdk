# Lane L2b-1: n8n-flows-real, n8n-flows-real-v3, n8n-flows-real-v4 (Tier B, 12 files, 156 nodes)
Written by builder L2b-1, 2026-11-16. Static reading only: nothing ran. Tier B rule of PLAN-002 section 1: full judgement only where the diff file names the node (REMOVED, ADDED, CHANGED, or an edge from or to it); every other row says `same as <successor>:<node> (machine diff identical)`. Successor chain: n8n-flows-real -> n8n-flows-real-v3 -> n8n-flows-real-v4 -> n8n-flows-real-v5.

## Inputs read
- handover/demo/n8n-flows-real/{mf-form,mf-hook,mf-recovery,mf-sub-crm-mail}.json (51 nodes), n8n-flows-real-v3/ (52), n8n-flows-real-v4/ (53).
- Diff files tools/out/diff__<folder>__<file>__TO__<successor>__<file>.txt, 12 files (real->v3, v3->v4, v4->v5).
- Docs: handover/demo/n8n-flows-real/README.md, NODE-DIFF-vs-film.txt, n8n-flows-v3/V3-README.md, n8n-flows-v4/V4-README.md, n8n-flows-v3/mf_leads.sql, n8n-flows/mf_leads.sql, REPORT.md lines 34 and 334, PLAN-4-NLITE-FROM-LEAD.md. All treated as unverified claims; checked against the diff (results below).
## Absent files
- n8n-flows-real-v3/ and n8n-flows-real-v4/ contain only the 4 json files: no README, V3-README.md or V4-README.md there. Those two files live in n8n-flows-v3/ and n8n-flows-v4/ and describe the real-v3/real-v4 folders in one sentence each (Nit L2b1-9). n8n-flows-real/ has README.md and NODE-DIFF-vs-film.txt (present).
- DECISION-one-store.md absent (PLAN-002); not needed here.
## README claims against the diff
- V3-README "form and hook flows identical": diff real->v3 mf-form and mf-hook print no node line, settings equal True. CONFIRMED.
- V3-README node list (REMOVED AlertUnknown, FailedRow, AlertFailed; CHANGED MarkFailed; ADDED AlertClaim, AlertRow, AlertSend, AlertMark; unknown paths go straight to OutUnknown): matches diff lines one for one. CONFIRMED.
- V4-README (AlertClaim window 720 s; ADDED AlertBackoff on the error output of AlertSend; everything else as v3): matches diff real-v3->real-v4 (CHANGED AlertClaim.parameters, ADDED node AlertBackoff, ADDED edge AlertSend 1 -> AlertBackoff). CONFIRMED. The 720 s basis (nodemailer timeouts) is a reading of a library, not measured (V4-README says so): UNVERIFIED.
- README real "Nothing else differs ... same 20 / 12 / 12 / 7 nodes": node counts 20, 12, 12, 7 CONFIRMED by the json; the claim "no stand-in names in these files (grep for MF_, loopback, example.test: 0)": my grep over the three folders gives 0 hits. CONFIRMED.
- Not in any of the three folders' docs, found by the diff: v4->v5 (CrmIdOk, SetCrmId change, credential id rename) is described in V5-README, which this lane did not read (belongs to L1).
## Per-folder summary
| folder | files | nodes | what it is | successor change (diff) |
|---|---|---|---|---|
| n8n-flows-real | 4 | 51 (12, 12, 7, 20) | first HubSpot-node variant; in-run alert mails (AlertUnknown, AlertFailed), fire and forget | v3: alert as state: AlertUnknown, AlertFailed, FailedRow REMOVED; AlertClaim, AlertRow, AlertSend, AlertMark ADDED; MarkFailed sets unknown when mail_sent; 14 rows judged: 8 here |
| n8n-flows-real-v3 | 4 | 52 (12, 12, 9, 19) | alert sweep with 60 s x (1+attempts) claim window | v4: AlertClaim window 720 s, AlertBackoff ADDED; 2 rows judged |
| n8n-flows-real-v4 | 4 | 53 (12, 12, 10, 19) | 720 s window plus backoff on send failure | v5: CrmIdOk ADDED, SetCrmId stores id safely, credential id placeholder renamed; 4 rows judged |
mf-form and mf-hook: machine diff identical in all three steps (settings equal True), so 72 of their rows (24 nodes x 3) are same_as. Dangling edges and duplicate node names: none in the 12 files (`dump_nodes.py check`). No node has reachable NO-INCOMING or UNREACHED-FROM-TRIGGER (checked from the machine table): no dead node by the script's rule.
Counts: 156 rows, 14 full judgement, 142 same_as.
## Secrets and personal data
No secret value and no personal data in the 12 json files. Credential ids are placeholders only: PG_CREDENTIAL_ID (38 uses), SMTP_CREDENTIAL_ID (7), HUBSPOT_CREDENTIAL_ID (3, in the three older folders; v5 uses HS_CRED_PLACEHOLDER). Credential names (n8n-publish-pg, mf-mail-smtp, hubspot-app-token) are names only. E-mail address pattern grep in the three folders: 0 hits (addresses are the constants FROM_ADDRESS_PLACEHOLDER and INTAKE_ADDRESS_PLACEHOLDER; recipient of alerts is the environment name DESK_ALERT_TO). tools/check_secrets.py: `PASS 0 hits in 120 files` (whole-audit scope).
## LIVE-REFERENCE verdict
Command (repo root parent handover/): `grep -rIPn --exclude-dir=flows-audit "(?<![\w-])NAME(?![\w-])" .` for NAME in the three folder names. Only md files hit; no .py, .sh, .json, .txt hit and no Execute Workflow or errorWorkflow reference (settings carry no errorWorkflow; RunSub uses the placeholder SUB_WORKFLOW_ID).
- n8n-flows-real: LIVE-REFERENCE (doc references only): demo/DECISION-INPUTS.md:24, demo/ORDERS.md:652, demo/REPORT.md:34, demo/REPORT.md:334.
- n8n-flows-real-v3: LIVE-REFERENCE (doc references only): demo/n8n-flows-v4/mf_leads.sql:1 (a comment line in an sql file, so the table file names this folder), demo/n8n-flows/PAGE-STATEMENTS-DRAFT.md:4, demo/n8n-flows-v3/V3-README.md:3, demo/n8n-flows-v3/mf_leads.sql:1, demo/REPORT.md:227.
- n8n-flows-real-v4: LIVE-REFERENCE: demo/n8n-flows-v4/V4-README.md:6, demo/PLAN-4-NLITE-FROM-LEAD.md:3 (frozen plan names real-v4 as the flows of the real take, while v5 is the current fixed version: Nit L2b1-8).
By the plan's rule all three are LIVE-REFERENCE, not SUPERSEDED, although the successor is named in PLAN-002 section 1. Honest reading: every hit is a document or a comment, none is code or a flow; REPORT.md:34 says "Do not edit v3/v4". An archive move needs the owner's yes (CUT-LIST), and the docs above would then need their path updated. UNVERIFIED: whether the generator (n8n-mainframe/build_mainframe.py, tests) writes into these folder names at run time: the grep over .py found no folder name, the output folder is an argument.
