# fix-q31-3 (Q31 fixer, round 3). Edited QUESTIONS.md only. Backup: scratchpad bk3/QUESTIONS.md. Not committed.

## New Q31 item numbers (for the plan-file fixer to cite; all [OPEN], each with answer-by, IF UNANSWERED, an index row in item 66)
- 67: list of review report files ($REPORT, GO row 2). Answer by Tue 10:30Z. Unanswered: GO row 2 not PASSED, NO-GO.
- 68: I24, are four shas accepted. Answer by Tue 03:30Z. No default stated.
- 69: new text for DECISIONS items 1 and 7 and run sheet N-9..N-11 (RUNBOOK 4a (1)). Answer by Tue 04:16Z (step 4a start; latest 04:51Z).
- 70: one time for the post-twice script and run_real_check_n8n.py: governing time Tue 09:00Z (L27); item 70 itself answered by Tue 07:00Z. Item 58 (Wed 05:45Z) now points to it. Unanswered: 09:00Z stands; if missed, GO row 2 NO-GO.
- 71: take program commands, Wednesday script set, scene 4 stop/start, RESULT_JSON path (I18). Answer by Wed 05:45Z.
- 72: recording start/stop commands, RECORDING path, length tool (I39). Answer by Wed 08:25Z.
- Input 5 (table and count line stopped at item 31): no new item; the paragraph before item 1 now says items 32 to 72 are in item 66; counts updated.
- RESULT_JSON tag REPLACE_ME_Q31_38 should become Q31_71; RECORDING tag Q31_4 should become Q31_72; REPLACE_ME_Q31_NONE (REPORT) becomes Q31_67 (the plan-file fixer edits those).

## Counts by grep (python, 14:38Z Mon 16 Nov)
Main list 65 numbered items: 63 OPEN, 1 ANSWERED (20), 1 NOTE (66). Second list plus 15A: 8 labelled (3 OPEN: 40, 43, 15A; 5 NOTE). Total 73 labelled, 66 OPEN. Count lines updated at QUESTIONS.md lines 40, 42 (outside Q31; same counts), 449, and the Note after item 66.

## Review items
M1: item 66 header states the 04:00Z assumption, tags [step clock] rows, lists the seven rows that move 29 min earlier on a 03:31Z start (04:16, 04:54, 05:14, 05:54, 06:24, 06:39, 06:59), and says which rows do not move. No longer claims every time is copied (new items carry planned times, said so).
M2: index rebuilt as one time row per item (script check: every open item appears at least once; split items 3, 8, 10, 14, 36, 38, 39, 56 appear in more than one row only because their parts have different times). Duplicate rows for items 2 and 15 removed (owner asks moved to a separate "Monday night asks" paragraph); 39 (b) now in the 07:00Z row; "their own lines below" removed.
M3: every pair has a governing time in group D (37+52+60 = 04:54Z; 14 (d)+61 = 05:00Z, one message; 52/37; 8 (e)+49 = 07:00Z; 38 (d) group = Wed 05:45Z except item 70 scripts = Tue 09:00Z; 37 vs 52/60 stated).
M4: each row carries a tag GO / STEP n / NONE / UNKNOWN taken from the item text; where the text names no effect: "unknown: lead decides". Nothing invented. Items 33 (GO rows 2, 6, 7) uses TAKE-CHECKLIST.md Inputs item 24 text.
M5: conflict stated, not decided: Monday-night asks (items 2, 15, 27, 21:00Z) go before item 9 (Tue 06:30Z) and before "re-check done"; OWNER-STEPS-q16-rows.md (about line 125) says until "re-check done" the owner acts on no request; sheet line 242 says the lead writes chat and deadline into each message; no default deadline exists. Options a, b, c listed for the lead; owner-sheet follow-up not made here.
Smaller: batch list now "9, 3, 5, 8" in both places; item 8 (e) now also asks the alwaysOutputData fallback patch (no default beyond NO-GO); "32 to 65" and "32 to 66" both now "32 to 72".
Coordinator extras: (1) Inputs item 22 time fixed to Tue 03:00Z (08:30 IST) in item 10 and in the GATE paragraph at line 50 (outside Q31, same edit); (2) item 8 (d) step 20 wording fixed; (3) step 17 item (6a); (4) ORDERS lines 125/138/160 wording fixed in both places; (5) ORDERS line 156 item 2 wording fixed in both places.

## Raw results
python3 -I tools/check_refs.py: PASS 5166 references. check_secrets.py: FAIL 1 hit flow-check/raw/test-take-check.txt:178 (existing, not mine).
## Not decided / not checked
Whether any step is on the GO path (tags say "unknown: lead decides"). The 04:16Z time of item 69 and 10:30Z of item 67, 07:00Z of item 70, 08:25Z for 72 are audit plans (72 and 71 from RUNBOOK I39/I18). OWNER-STEPS line 125 read from a grep context only. Items 1-31 text was read in part. Did not re-read the full file after edits.

## Added later: item 73 (citation-r17-rw3.md)
73: who writes and runs qualify_stage.py and test qs_01, and who checks the stage uses the fake model (RUNSHEET-WORDING B-045, B-046, A-004; not item 25). Answer by Tue 08:00Z (audit plan; no file gives a time). Index row Tue 08:00Z. Counts now by script: 66 numbered main items (64 OPEN, 1 ANSWERED, 1 NOTE), plus second list and 15A 8 (3 OPEN): 74 labelled, 67 OPEN; the counts above in this log are one item lower. Count lines in QUESTIONS.md updated (lines 40, 42, 449, Note).
