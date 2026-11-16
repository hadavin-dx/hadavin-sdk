# fix-takechecklist68: fixer log for reviews/take-checklist-reader-r68-196-540.md (M1 to M9 and the three notes)
Static only. Nothing was run in n8n, psql or curl, and TAKE-CHECKLIST.md itself was not run. New commands are untested text; the only test was `bash -n` on scratch copies of all 28 code blocks (and of the row 3 (e) one-liner) under the scratchpad: all passed syntax. Backup: scratchpad/TAKE.before68. Clock block lines 32-79: md5 and line count unchanged (48 lines); lines 1-31 untouched.
Honest limits: the logic of the new words was read, not executed; "LEAD DECIDES" items below are the lead's to confirm.

| Finding | Status | Where (lines of the new file; search the block name) |
|---|---|---|
| M1 words | FIXED (all 28 blocks end in a computed NAME-PASS / NAME-FAIL): R1, R2, R2s, R2j (needs ITEMS_WANT), R3, R3L, R3n, R3c, R4 (exit number + 8 counts), R4r (cmp with pin 1), R4b-1, R4b-2, R4f, R5e, R5w, R5b, R5f, R6, R6j, R7, R7j, R8, P1a, P1b, P1c, P2a, P2b, P2c | rule (0) in "How to paste a block"; each block |
| M2 WAIT_S switch | FIXED in this file: new Block R5w (checks one `WAIT_S=` line, comment `# WAIT_S_TUE=<n>` present on WED and absent on TUE); R5b and R5f embed the same check and refuse otherwise. RUNBOOK step 18 sentence NOT edited (other agent), see below | Block R5w; placeholder row WAIT_S |
| M3 need_set | FIXED: R5f need_set now holds TAKE_FOLDER and ADDR; one row verdict R5f-PASS (control lines, wait over, two date lines, row done, attempts on WED, mail-count 1, count file exit 0) | Block R5f |
| M4 attempts | FIXED: ATTEMPTS_WANT (new placeholder row) required and compared when DAYWORD=WED; row 6 text updated | Block R5f, check 6 |
| M5 contract and 5b | FIXED: count-file contract written (POSTLOG, ADDR list, one `mail-count N` line, exit 0); new Block R5b prints R5b-PASS and writes a control line into $TESTLOG; R5f refuses unless the line exists for the same DAYWORD (WED: two different addresses). New input CTLLOG. PARTLY a lead decision: the old text said the Tuesday control runs right after the mailbox count of RUNBOOK step 16; R5f now needs it first. Marked "LEAD DECIDES: owner = the lead, due Tue 06:00Z (11:30 IST)" | MAILCOUNT row, Block R5b, R5f header, check 5b |
| M6 date lines | FIXED in text: post-twice script must write one `date -u +%Y-%m-%dT%H:%M:%SZ` line before each POST; R5f refuses unless exactly two. The script itself still does not exist (LEAD FILLS, Q31 item 70, on a branch by Tue 09:00Z (14:30 IST)) | GO row 5, check 5, Block R5f |
| M7 row 3 (e) | FIXED: `rm -f` first, `&&` chain, prints code-check-ran, exit 0, R3e-PASS (or R3e-FAIL) | GO row 3 |
| M8 four-file guard | FIXED as hard guards (REFUSED + `exit 1`): R4b-1, P1a (on $FLOWS), P2a (on $EXPORT); also inside the P1c and P2c commit chains (silent stop) | those blocks |
| M9 owners/times | FIXED: rows REFUSAL_LINE, PG*, PGCONN_*, PGCONN_SELECT_ONLY, POSTFILE, PIN_*, RUNSHEET, JUDGE_WHO now carry owner and due time taken from this file (Q31 items 25, 58, 60, 70; Inputs-list items 4, 31, 24; row 11); 444 now "Wed 18 Nov about 10:00Z (15:30 IST)". JUDGE_WHO: 03:30Z is earlier than Q31 item 33's 04:00Z, so it stands | placeholder table, check 11 |
| Note R7 PART A | FIXED: exit number kept, control and PART B controls kept, R7-PASS computed | Block R7 |
| Note R6j substring | FIXED: id must be `F-` + 3 digits and start a `.decides` row; judged set must equal the `.decides` set | Block R6j |
| Note R6 hardcoded topic | FIXED: LEDGER_TOPIC input (new row; AUDIT PROPOSAL `duplicate-proof-lead-desk`, Inputs-list item 11, Tue 07:00Z (12:30 IST)) | Block R6 |

New placeholder rows: CTLLOG, ATTEMPTS_WANT, LEDGER_TOPIC, ITEMS_WANT.

## Sentence RUNBOOK step 18 needs for WAIT_S (M2; RUNBOOK.md not edited by this fixer)
"Before step 18 starts, type `DAYWORD="WED"` and run Block R5w of TAKE-CHECKLIST.md; it must print `WAIT_S=<the Wednesday number> for WED` and then `R5w-PASS`. It refuses when `shas.env` does not hold exactly one `WAIT_S=` line and the comment line `# WAIT_S_TUE=<number>` that the Wednesday switch leaves behind (new text, untested; LEAD DECIDES: owner = the lead, due Tue 03:30Z (09:00 IST))."

## Checks run (last line of each)
See the final report of the fixer (same output).
