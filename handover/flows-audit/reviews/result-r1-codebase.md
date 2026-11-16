# Result review round 1 - codebase-details lens (agent a52c620d686a34950, Sonnet 5.5, read-only)
Saved by the lead session. Reviewer text condensed; every finding kept. Verdict: no Blocker; 4 Major, several Nits. Reviewer ran nothing.

## Major
- C-M1 F-012 (L1-11): "about 42 s" worst path is wrong for real-v5. CrmUpsert in real-v5 is the HubSpot node (n8n-nodes-base.hubspot 2.2): retry True/2/1000, NO timeout option (build_mainframe.py:27). The 10 s timeout applies only to the film-v5 HTTP stand-in. Real worst case before MailClaim is not bounded at 42 s. ClaimStuck part holds (LIMIT 5, lease 45 s, RunSub serial, attempts<3, attempts+1 on claim, build_mainframe.py:98-100).
- C-M2 F-014 (L1-16): "alerted again every sweep" is wrong. AlertClaim sets alert_until = now() + 720 s (line 124 both v5 recovery files). If AlertMark fails the row is not re-claimable until the window ends: repeat about every 12 min. 60 s x LEAST(attempts,5) backoff applies only on AlertSend error. "No cap on alert attempts" is true. Reword.
- C-M3 Patch F-003: contradicts itself and states as measured a number the finding calls UNVERIFIED. Hunks line up (scene 4 :33, scene 10 :39, scene 12 :41, "seven columns" :62). Unchanged lines saying the opposite: scene 4 "NO NUMBER measured for 45 s" column; don't-say "Any measured recovery number for 45 s. Within 60 s"; risk 2 "The 45 s lease has no measurement" (~:51); "Real waits ... UNMEASURED at 45 s". Scene 12 closing card gets the same number. Fix: caption "relayed, not seen by us" or edit the four lines in the same patch.
- C-M4 Ranking breaks ORDER 003: F-020 and F-021 (Major, take) sit after F-019 (Major, not take); F-028 (Nit, take) after F-026/F-027 (Nit, not take). F-023 (table-screen README) marked not-in-take but scene 10 films the table screen: arguably take.

## Nits
- F-004 patch leaves Tag "45 s: NOT RUN", Test "lease table, not run" (PAGE-STATEMENTS-V4.md:121-123) and totals at :132, :139 contradicting it. "144.2 to 144.4 s" is supported by statement 20 (:157).
- F-008 title says six recovery nodes swallow errors but lists five (ClaimStuck, MarkFailed, AlertClaim, AlertBackoff, AlertMark); sixth is RunSub (not a database node). saveDataSuccessExecution present in all 8 v5 files, no errorWorkflow hit.
- F-006: run sheet line 4 says scenes 1-5, line 11 says 1-4, line 12 says scene 5 is a stand-in; F-006 does not mention line 11.
- F-007 line numbers :153/:159 are def k3b()/k3(); kill_case descriptions at :158/:164. Substance confirmed.
- F-001 substance holds; "byte-identical" not confirmed by cmp by this reviewer (read only). Patch old lines match; v4 text not diffed.

## Checks passed (about 27)
F-001 table defs and mf.py:44-47; F-002 Claim no onError/retry in mf-form and mf-hook; F-005 smtp_catcher.py:40, :44-47, RunSub waitForSubWorkflow true, run sheet :35; F-003 ReadLeads six columns, no DELETE/TRUNCATE in flow json (Postgres delete operation not checked); F-004 45 s vs 120 s; F-006 CrmUpsert hubspot 2.2 to httpRequest 4.2; F-009 Receive no auth; F-010 all postgres nodes n8n-publish-pg; F-011 N8N-START.md:4; F-015 UnknownNewA/UnknownNew; F-016 String($json.vid count 1/1/1/0; F-017 10 of 12 identical; F-021 DESK_URL; F-023 README lines; F-026 525 of 655.
F-002 patch: hunk numbers (-79,8 and -90,7) and old text match; helper signatures hold; links consistent; generator only. Caveat: ReplyStoreFail 503 "not_stored" even if INSERT committed; resend safe (idempotent key).
Same-as sampling: about 10 rows sampled, all correct (L1 film-v5, L2b-3 v3 recovery rows 232-240, v3 sub-crm-mail 251-252).

## Could not verify
Runtime n8n behaviour, relayed lane3 numbers, F-013 (stage_server.py absent), F-019/F-020 stage details, cmp byte-identical, tools/scratch rebuild, sender retry rule, L3.findings.md L3-2.
