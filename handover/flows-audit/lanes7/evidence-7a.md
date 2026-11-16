# Evidence 7a (ORDER 007 item 1): raw record, run by the lead's cloud session; the patches are static files, n8n was NOT run
Commands and what they printed (copied from the terminal, 2026-11-16 ~08:22 UTC):
1. `sh handover/flows-audit/tools/check_patches.sh` -> `PASS 5 patches` (git apply --check on each patch against the original files; JSON parse of any patched .json: none patched).
2. F-002 and F-008 applied together to a copy of handover/demo/n8n-mainframe, then `MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py /tmp/g/out PGID SMTPID SUBID 45 HSID` (the V5-README command for real-v5) wrote the four flow files. Parsed: node names unique in each file.
   - mf-form 15 nodes, mf-hook 15 nodes, mf-recovery 10, mf-sub-crm-mail 20.
   - saveDataSuccessExecution: mf-form all, mf-hook all, mf-sub-crm-mail all, mf-recovery none.
   - Claim: alwaysOutputData False, onError continueErrorOutput. KeyOk condition: `/^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key)`.
   - Connections: KeyOk 0 -> Claim, 1 -> ReplyBadKey; Claim 0 -> Claimed, 1 -> ReplyStoreFail.
   - Node-name diff against n8n-flows-real-v5: mf-form and mf-hook: new KeyOk, ReplyBadKey, ReplyStoreFail, none gone; mf-recovery and mf-sub-crm-mail: no difference in node names.
3. F-004 fact: `grep -ho "now() + interval '[0-9]* seconds'"` in the folders: real-v5 and film-v5: '45 seconds' x3, '60 seconds' x1, '720 seconds' x1; n8n-flows-v4: '120 seconds' x3; real-v4 and film-v4: 45 x3. V5-README lines 8-9 pass lease argument 45.
NOT checked: how n8n behaves at run time (error output with alwaysOutputData off; zero items from an INSERT that hits ON CONFLICT: the build comment at build_mainframe.py:114 says the Postgres node returns one item {success: true}, read from the n8n source by an earlier session, not re-read here: UNVERIFIED). Test T19 (same key twice, answer still arrives) on the laptop decides it.
