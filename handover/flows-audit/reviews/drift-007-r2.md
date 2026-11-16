# Drift check of stable audit files (egm-codebase-details, agent a0a664edf0b8172ff). Verdict NOT CLEAN: 1 Blocker, 6 Majors.
Saved by flows-audit, condensed. Reviewer words unverified; reviewer had no shell, counted by hand. Not checked: count_findings.py, check_patches.sh, ledger_check, FIX-PLAN, QUESTIONS, REPORT, OWNER-STEPS, node counts, behaviour.
B1 Blocker: patches/F-003-runsheet-claims.patch contradicts Q19-2/Q25-2/Q28-1: scene 3 caption (patch L66) says "one CRM row and one e-mail message" and "receiving mailbox"; card line (L68) broad "processed once"; REGENERATED-NOTE L11,24 keep the broad sentence open.
M1: scene 3 proof (patch L65-66, rehearsal item 11 L130) uses CRM row count; Q22-4/Q28-2 need mailbox count after wait plus mf_leads row in frame.
M2: patch uses on-screen stopwatch (L19,40,44,45,67,76,79,129); Q25-12 no on-screen timer; no "cut scene 4 if no takeover in 3 minutes" rule.
M3: patch L67 owner stops/restarts n8n; Q22-1 and decision 7 say lead does it.
M4: "deleted at clean-up" survives in lanes7/N7-new-findings.md:147,148,167; N7-verdicts.md:36,50; FINDINGS F-041 (L117) and LEDGER L16 say paste N7-7; no SUPERSEDED marker; EXCEPTIONS.md:16 paste lacks "audit text only, not for the video" label.
M5: FINDINGS F-004 (L113) stale ORDER 007 sentence vs patch statement 17.
M6: FINDINGS F-003 (L109) says patch marks scene 4 caption "relayed from the lane3 test"; patch does not.
M7: LEDGER vs FINDINGS: F-013 status differs (OPEN vs ACCEPTED); statuses CLOSED-DROPPED, ACCEPTED not in ledger vocabulary; F-001 free text.
Nits: N1 LEDGER L44 and lanes7 cite CUT-LIST:17, should be :18; N2 F-012 "usually one lead" unmeasured; N3 CUT-LIST:21 cites ORDERS:547 etc of handover/demo/ORDERS.md, add path; N4 LEDGER header stale, ~25 truncated cells; N5 lanes7 verdict labels differ from FINDINGS table; N6 no raw file for the current 4-patch check.
Verified OK by reviewer reads: 45 rows (5 Blocker, 7 Major, 33 Nit; 13 BEFORE, 32 AFTER), LEDGER 45 rows same ids, patch hunks match sources, cited lines hold.
