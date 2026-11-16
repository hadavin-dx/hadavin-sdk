# Fix report: TAKE-CHECKLIST.md round 63 (Majors 1 to 15), written 2026-11-16 20:45Z (Tue 02:15 IST)
Static work only. Nothing ran in n8n, Postgres or HubSpot; made-up data; no secret printed. Only TAKE-CHECKLIST.md, reviews/take-checklist-changelog.md and this file were written. Backup: scratchpad TAKE-CHECKLIST.bak. Nothing committed or pushed. No status was set to passed or verified.

## Unverified or open first
1. Edits were made with exact-string replacement in a script, each checked to match once. I did not re-read the whole file after editing; a stranger read of the new text has not been done.
2. Cross-file clashes I cannot fix (I edit only this file): RUNBOOK section 10 (h) says WAIT_S is due 08:29Z (13:59 IST), which equals its first use; this file now says answer-by Tue 06:00Z (11:30 IST) and flags it in the Needed-by paragraph. QUESTIONS.md Q31 item 38 (a) says the mutation command is due Tue 03:00Z (08:30 IST) and Q31 item 38 (b) says 03:30Z (09:00 IST) for the round shas: this file proposes Mon 22:00Z (Tue 03:30 IST) and Tue 04:00Z (09:30 IST); the lead must append both changes to Q31. QUESTIONS.md Q31 item 27 and item 30 hold the opposite default to item 20 of this file.
3. Values I chose as AUDIT PROPOSAL (lead to confirm; none applies by itself): mutation command Mon 22:00Z (Tue 03:30 IST); round shas 04:00Z (09:30 IST); items 6 and 15 by Tue 12:30Z (18:00 IST); item 11 and item 18 (d) by Tue 07:00Z (12:30 IST); BODY/HOOK_URL by Tue 06:00Z (11:30 IST); real-take port Tue 05:14Z (10:44 IST); sign-off format Wed 05:45Z (11:15 IST); result.json key Wed 07:30Z (13:00 IST); review slot Tue 10:30Z (16:00 IST) to 13:00Z (18:30 IST).
4. I did not read the RUNBOOK, FIX-PLAN text outside the frozen block, or Q31; the new times are derived only from what TAKE-CHECKLIST.md already says. The reviewer's "Note for lead" (frozen clock block, pin 1 reader window 04:26Z to 04:51Z against step 4b start) is report-only and untouched.
5. The scan for missing IST pairs is my own regex; table cells that give IST in a separate column were left as they are.

## Checks run (output seen)
- `sed -n 32,79p TAKE-CHECKLIST.md | md5sum` = dfd844ddb7085082534434075814e131, equal to FIX-PLAN.md 37-84 (same value).
- check_refs: PASS 5190 references. check_names: PASS 655 rows. check_secrets: PASS 0 hits in 2991 files. check_counts: PASS 52 files / 655 nodes. check_runsheet_paste (RUNSHEET-WORDING.md CLAIMS-TABLE.md): RESULT: PASS. `ruff format --check .`: 1116 files already formatted.

## What changed per Major
1. Block R5f pass text and check 6: Tuesday does not compare attempts (state done plus mail-count 1); Wednesday compares with the RUNBOOK step 22 value. Row 5 pass line says so. Item 17 says Wednesday only.
2. Item 2 now = NEW, BRANCH, PATCH_BRANCH, SHA_R20 to SHA_R23; SHA_FOLDER, SHA_PIN1, SHA_PIN, SHA_SCRIPTS marked MADE BY COMMAND.
3. Round shas answer-by 04:00Z (09:30 IST), after the schedule's last merge; r23 merge time to be filled with item 10; squash or rebase: merge commit sha plus Block R1 again; Block R1 text in the "When Blocks run" paragraph and row 1 changed to match.
4. Item 13 now input, default (AUDIT PROPOSAL), times; Wednesday text removed from the Needed-by paragraph.
5. WAIT_S: Tuesday value (Q31 item 25, 06:00Z (11:30 IST), first use 08:29Z (13:59 IST)) and Wednesday value (Q31 item 50, 05:45Z (11:15 IST)); edited in the Needed-by paragraph, blanket rule, row 5, WAIT_S row, item 17.
6. Tuesday and Wednesday mailbox count commands named in the Needed-by paragraph, row 5 (f), checks 4 and 5b.
7. Check 4 title and Allowance: (a) to (c) before rehearsal 1, (d) before rehearsal 2 (08:40Z (14:10 IST)).
8. Mutation command due Mon 16 Nov 22:00Z (Tue 03:30 IST) in Needed-by, blanket rule, item 8, row 3 and the "When Blocks run" paragraph; MUT_NAME same time.
9. Item 21 now holds the row 2 list (Q31 item 67), a named reviewer and a proposed slot; rows 2 and 6 cannot pass on Tuesday without them (stated). Row 2 and row 6 cells point to it.
10. EVLOG, REPORT, LEDGER_OUT, GREPOUT, ROW1, POSTLOG, RECORDING, TESTREC, RESULT_JSON are "typed per call". MUT_NAME, COMMIT_MSG, TRAILER, BODY, HOOK_URL, item 3 port and sign-off, item 5, item 6, item 8, item 11, item 15, item 18 (d)(e), check 8 key all got a UTC (IST) time or lost the LEAD FILLS label. Items 6 and 15 moved from 14:00Z to Tue 12:30Z (18:00 IST).
11. NEW_PIN and EXPORT_PIN times removed from the Needed-by paragraph.
12. Post-twice script 09:00Z (14:30 IST) added to item 7 and to "Still open" 1.
13. Item 20: one default stated, a single LEAD DECIDES for the clash, item references written as "QUESTIONS.md Q31 item 27 and Q31 item 30".
14. IST pairs added at the places the reader named and a few the scan found (rows 11, header paragraph, item 16, rows 3 and 5 text, item 24, item 22, line about 08:00Z).
15. The count of the ACCEPTED line: PASS if 1 or 2, any other number is NOT a pass (rows 4 and check 1, Block R4 header).
