# FINDINGS/LEDGER round 5 fresh reader (agent a7c0d07). Reviewer words unverified. Saved by flows-audit, condensed.
Verdict: lead cannot tell from the two files whether the take runs. 2 Blockers, 9 Majors. Counts by grep match (45 rows, 5/5/35, Blocker F-002,F-003,F-007,F-031,F-037; Major F-008,F-011,F-018,F-029,F-041). BEFORE 11/AFTER 34 by reading only.
B1 Four Blockers have no written take effect (F-003 FINDINGS 111/LEDGER 4; F-007 112/L7; F-031 113/L8; F-002 110/L3): "no Q31 item exists" (now items 89-93 exist, pointers must be updated; FINDINGS 16 "no Q31 item asks it" -> item 93).
B2 Wednesday clock stated 3 ways: FINDINGS 110 (T19-T21 start ~07:00Z, check 07:30Z), Q30 item 1 (tests end ~07:00Z, Row 4 after, rehearsal ~07:30Z), Q31 8(d) (Row 4 07:00-07:30Z), item 82 (practice 06:00Z, T21 end of hour), F-018 117 (step 10b by 07:00Z and after T19-T21).
M3 F-002b: FINDINGS 110 says fallback for failed T19; Q31 16 writes it now; items 8(e)/49 say NOT used; Q29 item 3 says NO-GO.
M4 F-031 pass line part (2) counts state='review' only; Q31 items 17 (466) and 23 (472) quote ('review','unknown','failed').
M5 F-008: Q31 item 26 (479) quotes old 8-line pass; FINDINGS 115 replaced it (path:2 per file + -H check + ACCEPTED line).
M6 Downgrade writer: FINDINGS 116/119 studio lead alone; Q31 item 10 second person; Q31 item 18 piped greps vs FINDINGS line 23 no pipes; EXCEPTIONS line not yet existing.
M7 Who applies text fixes F-003/F-007/F-031: rows say studio lead; Q31 item 11 default says audit applies to audit files, lead to run-sheet; fixes are in handover/demo; item 11 due Tue 07:00Z vs RUNBOOK step 14 07:15Z/07:44Z.
M8 Tuesday GO cannot pass by default: F-018 pass line Wednesday but counts in GO row 6 (Q31 item 31).
M9 Ratings inconsistent: F-037 and F-003 "by rubric" though risk narrow; F-002/F-007 "by lead order".
M10 Who may overrule a Blocker/NO-GO written nowhere (FINDINGS 16 vs 100); F-008 two deciders.
M11 Words: "unknown:" two meanings (state value vs unanswered question); "Row 4" undefined in these files; "BEFORE n" defined only for items 3,7,8; "re-pin".
Also: FINDINGS line 86 "8 items left" vs 11 BEFORE rows (Major).
Not checked: ORDERS, FIX-PLAN, RUNBOOK, TAKE-CHECKLIST, EXCEPTIONS, CUT-LIST, Q31 items 63-81,85-88, index.
