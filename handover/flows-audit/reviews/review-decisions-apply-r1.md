# Review of the 2026-11-16 decisions pass (egm-codebase-details, agent ab099e87), saved condensed by flows-audit. Reviewer words unverified until checked. Static.
Edits seen (about 40 of 56) match their decisions. Majors:
M1 REPORT.md:10 vs FINDINGS.md:71 say opposite things about the "one database" count reading.
M2 QUESTIONS.md:18 and FIX-PLAN.md:22 say F-011/F-041 stay AFTER (Nit) but QUESTIONS:23 and FINDINGS rows keep them BEFORE Major; 8/6/31 BEFORE 15 not written anywhere.
M3 stale "8 files/8 flows": FINDINGS:57,58,88,96,97,101; FIX-PLAN:1; EXCEPTIONS:14; SCENE-FLOW-MAP:46,71; QUESTIONS:29.
M4 severities not recounted: F-005, F-006 (Blockers), F-023 (Major), F6B-01, F6B-13 now about cut scenes; lead rules, then recount in FINDINGS, LEDGER-ROWS, REPORT, FIX-PLAN.
M5 FIX-PLAN:10 item 7 and FINDINGS:89 (F-003) still say apply patches F-003/F-004; they insert 60.1 to 61.9 s and scene 5: regenerate, do not apply as is.
M6 QUESTIONS:26 (Q10) recommendation "add run-sheet line switch flow set after scene 4" contradicts decision 1.
M7 F6B-AUDIT:18-26 steps 1-5 still describe film-set switching; mark NOT USED or rewrite. Step 3 TRUNCATE destroys the lead_key to crm_id list decision 2 needs: export first.
M8 SCENE-FLOW-MAP:40 and :68 scene 4 caption still has "K1, 5 runs, median 60.8 s, max 61.9 s" vs line 29 cutting it; lead to decide.
M9 SCENE-FLOW-MAP:37 scene 1 sentence still says "Scenes 5 to 11 say on screen that they use stand-ins".
Nits: F6B:9 says 11 scenes vs map 12; SCENE-FLOW-MAP:66 C1 rule text; FINDINGS:97 and LEDGER:12 "one Postgres"/"separate database"; LEDGER:5 no cut marker; QUESTIONS:29 answered+pending; EXCEPTIONS:10; PLAN-002:27 says one-store file ABSENT but inputs/ has it.
Missed present tense: FINDINGS:59,80,89,95,96; F6B:20,23,82,88,96; QUEUE:13.
Not checked: VIDEO-RUNSHEET, patches, inputs, REPORT.md past line 30, decisions 4-8, 11, 12 greps.
