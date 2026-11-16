# fix-q31-2 (Q31 round 2 readability fixes, QUESTIONS.md line 420 to end)

Only QUESTIONS.md (Q31 part) was edited. Not committed. Nothing was run in n8n; text edits only.

M1: every index row that said "DEFAULT: none stated; lead decides" now names the step that does not run (RUNBOOK steps 7, 8, 9, 10, 11, 12, 16, 18, 19, 19a, 21, 23, 24, 25, 26; Block R1, Block R3 part (c); the JUDGED blocks R2j, R6j, R7j). The "schedule effect not stated: lead decides" sentence is said once in the item 66 header and repeated short in each row. Step names are my reading of RUNBOOK's step table and of the cross-references inside the items (RUNBOOK step 26 for who types y is my reading; item 39 only says BLOCKED).
M2: one default, the stricter: a T21 failure is NO-GO, the take-prep message is not sent. Stated in item 8 (e), item 49 (text and answer-by), group D, and the index (49 moved from the Wednesday row to the Tuesday 07:00Z row). Earlier time (Tue 07:00Z) governs.
M3: item 38 (a) and item 14 (b) are the same batch (both quote ORDERS.md line 147; TAKE-CHECKLIST.md row 3 (c) says it runs in Block R3 before RUNBOOK step 1; note: Block R3 is in TAKE-CHECKLIST.md, not RUNBOOK.md). Stated in both items, the top table, the index and group D. 14 (b) moved to 03:00Z.
M4: chose the smaller change: line 421, the "Order of answers" line and item 66 now say the top table covers items 1 to 31 and item 66 is the full list. 38 (f) got an answer-by (Tue 08:00Z, 13:30 IST) and an index mention; default: the audit's reading stands.
M5: item 9 now holds the actual default (the conversation where the owner normally writes to the lead; reply deadline and app written by the lead in each message, sheet cell V1; no deadline number exists in any file, none invented). Copied from OWNER-STEPS-q16-rows.md line 242.
M6: row 53 moved to the 06:00Z row; item 53 text and group D say the earlier time governs. Item 53's own text names no default; I read the item 25 default for it and marked it UNVERIFIED, lead confirms.
Notes: "less than 31 minutes" now says 31 minutes for 03:00Z rows and 1 minute for 03:30Z rows. Counts unchanged (no item added): 67 labelled, 60 OPEN.

Not decided: whether the real default for item 49's alwaysOutputData fallback use exists (no file states it). Not checked: lines 1-419, outside files, History.

Commands: `python3 -I handover/flows-audit/tools/check_refs.py` -> PASS 5166 references (exit 0). No .py file touched.
