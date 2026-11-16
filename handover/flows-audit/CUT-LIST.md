# CUT-LIST (candidates only). Rule: owner yes first, then MOVE to an archive folder, never delete; no patch deletes a file. Added by ORDER 003: every older flow version is listed with the one-line reason it is superseded. Evidence for "superseded": the successor named, plus the LIVE-REFERENCE test (every hit is prose in a document; no script, Execute Workflow node or errorWorkflow value points at the folder).
The take uses only n8n-flows-real-v5 and n8n-flows-film-v5 (ORDER 003). The owner counts the many versions as duplicates: 11 older flow folders, 40 files, 525 of 655 nodes.
| folder | files / nodes | successor | one-line reason it is superseded | live-reference hits (prose only) |
|---|---|---|---|---|
| n8n-flows/v1-superseded | 3 / 53 | n8n-flows (mf-*) | first design: no attempts cap, no alert, recovery can double-mail (F-025); README says "kept for the compare only" | 7 docs |
| n8n-flows (mf-* four files) | 4 / 51 | n8n-flows-v3 | v2: alert mail lost if SMTP fails, state failed even when mail sent (F-024) | docs and scripts text |
| n8n-flows-v3 | 4 / 52 | n8n-flows-v4 | 60 s alert lease shorter than a slow send, duplicate alerts (F-024) | 9 |
| n8n-flows-v4 | 4 / 53 | real-v5 / film-v5 | before CrmIdOk: can store the text "undefined" as crm_id (F-016) | 7 |
| n8n-flows-real | 4 / 51 | n8n-flows-real-v3 | same defects as the plain v2 for the real-node variant | 4 |
| n8n-flows-real-v3 | 4 / 52 | n8n-flows-real-v4 | 60 s alert lease | 5 |
| n8n-flows-real-v4 | 4 / 53 | n8n-flows-real-v5 | no CrmIdOk | 2 |
| n8n-flows-film | 4 / 51 | n8n-flows-film-v3 | same defects as plain v2 for the stand-in variant | 6 |
| n8n-flows-film-v3 | 4 / 52 | n8n-flows-film-v4 | 60 s alert lease | 2 |
| n8n-flows-film-v4 | 4 / 53 | n8n-flows-film-v5 | no CrmIdOk | 2 |
| n8n-table-screen | 1 / 4 | n8n-table-screen-v2 | v1 reads seven columns (v2 reads six) | 6 |
Also candidates (owner yes): n8n-flows desk-form-door, desk-webhook-door, desk-error-notifier (write the retired desk store, F-019; retire from the take); n8n-mainframe/build_mainframe_v1.py (only generates v1-superseded); n8n-tests/run_dn1.py (23 of 239 lines differ from run_mf.py, F-027); n8n-rerun/*.py.txt driver copies. Three copies of mf_leads.sql collapse to one with patch F-001 (then mf.py reads that file).
Before any move: update the prose that names these folders (PLAN-4-NLITE-FROM-LEAD.md:3 still names real-v4 as the take; REPORT.md lines named by the lane headers).
