# Flows v5 (WP4: CRM id). BUILT, NOT RUN. Folders: n8n-flows-real-v5 and n8n-flows-film-v5 (v3 and v4 folders untouched).
## What changed against v4 (nothing else)
- SetCrmId stores crm_id = String($json.id ?? $json.vid ?? ''). v4 real stored String($json.vid): a HubSpot answer with only id gave the text "undefined".
- NEW IF node CrmIdOk right after SetCrmId. It checks the same value (read from the CrmUpsert answer). Non-empty goes on to OwnsClaim1 (the old path). Empty goes to OutStage, the SAME node a CRM refusal uses, so the lead is retried by the normal rule and ends failed with 1 alert, never done.
- The generator takes the HubSpot credential id as argv[6] (LEASE is argv[5]). Without argv[6] the old placeholder text stays.
- Known small effect: on an empty answer SetCrmId has already written an empty text into crm_id (not NULL, not numeric). The take treats it as not has_crm.
## Commands (run in the n8n-mainframe folder)
real-v5: MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
film-v5: MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../n8n-flows-film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
(The v4 folders were reproduced byte for byte by the OLD generator with these same settings; the lease of real-v4 is 45 and it uses 2 tries and 10 s, like film.)
HS_CRED_PLACEHOLDER is a made-up text; the lead replaces it with the real id in a local copy.
## Checks done
- Old generator with the old settings reproduces film-v4 and real-v4 exactly (diff, no output).
- Node-by-node diff real-v5 against real-v4: see V5-NODE-DIFF.txt (only SetCrmId, CrmIdOk with its connections, the credential id). Film-v5 against film-v4: same, without the credential line.
- py_compile of build_mainframe.py, crm_stub.py, mf.py: ok.
## NOT RUN
No stack here: T17, T18, M1 and K1 on v5 have NOT been run.
## Stand-in changes
- crm_stub.py: control field upsert_answer on POST /control: "id" (default, the old answer), "vid", "none". Persistent until set back.
- mf.py: new tests T17 (id only: done, numeric crm_id, 1 mail, 0 alerts) and T18 (neither: failed, 0 mails, 1 alert, crm_id not numeric). They build their flows with build_mainframe.py (not from these folders), so MF_V4, MF_TRIES, MF_TMO_MS and the lease are passed as environment.
