# C14 independent claims check of plan-wp6-resmoke-v5.md (egm-style reader, condensed copy), 2026-11-16
Read-only; whole plan (559 lines) read. No hard numeric mismatch in the plan.
1. Plan :398 and :445 say the E repeat costs "about 8 min" (up to 12); its own steps give E.0 1 + E.1 3 + E.2 1 = 5 min (12 only with 11.4 and 11.5). Low severity; fix wording.
2. "153" is not in v5: v5 says 151 steps, 171 min, 2 h 51. 153/173 (2 h 53) comes from the v6 edit list; evidence-c3e.md:105 shows a patch chain at 172 min. Chains differ; unclear if they stack. Treat 151/171 as v5, 153/173 as v6 only.
3. OWNER-STEPS-realrun-v3.md:75 says open n8n at localhost:5678, which conflicts with plan :121 and decision 6 (5678/5679 are the owner's own). Section 10 edit must fix it.
Matches recomputed: block minutes 24+6+10+9+7+12+6+10+9+5+31+11+11 = 151; 171 = 2 h 51; S11 31; 20 rows in section 7 and in section 11 part A; ports; 285 s = 3x45+150; 120 s windows; hashes.
Not checked (files not in checkout): n8n scripts at eec6ba4/1e97f88, drive.py, fill_flows.py, smtp_catcher.py, crm_stub.py, flow JSONs (lease 45 s, recovery 30 s only second-hand), smoke-v3 evidence, bible. No weekday or UTC/IST pairs in the plan; 16 Nov 2026 is a Monday (counted by hand).
