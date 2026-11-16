# fix-q31-4 (fixer; static; nothing run except check scripts and a counting script; not committed)
File edited: QUESTIONS.md only (Q31 section, count lines 40, 42, 449, 579 and the Q31 preamble). Reviewer words (reviews/q31-lead-readability-r4.md) were unverified; each cited line was re-read before changing it.

## What did not work, first
- My first run of the edit script stopped on a text that did not match (item 68 is followed by item 69, not 72) and a second time on the count lines (they differ slightly per line). Nothing was written either time (the script writes once at the end); I corrected the script and ran it once. QUESTIONS.md was backed up before the run.
- tools/check_secrets.py prints FAIL 1 hit: flow-check/raw/test-take-check.txt:178 (token-like, length 47). That file is not mine and I did not touch it; I did not check whether it is a made-up value. It needs the lead or its author.
- Not changed: item 24 is still written over five lines (nit); merging them would move line numbers. Nothing cites those lines (grep of other files for QUESTIONS.md line cites found only early lines), so the lead may merge them. I did not do it.

## M1 Monday-night conflict
New item 74 (own number, QUESTIONS.md after item 73), answer-by Mon 16 Nov 20:00Z (01:30 IST Tue), before items 30 and 27; IF UNANSWERED line = audit proposal: choice (a), asks go out at 21:00Z as written plus an owner sheet exception; marked "audit proposal, lead to confirm". Index: the old OPEN CONFLICT paragraph now points to item 74; new row at the top of GROUP A.

## M2 item 58 / 70 / index
- Item 58 ANSWER BY now says Tue 17 Nov 09:00Z (item 70 governs), Wed 05:45Z only for the other scripts of item 38 (d). Item 71 ANSWER BY: run_real_check_n8n.py due Tue 09:00Z, rest Wed 05:45Z. Item 70 IF UNANSWERED names who carries what.
- Index: new row Tue 09:00Z (start of GROUP C) naming the carrier of each file: post-twice script = item 58; run_real_check_n8n.py = item 71; time = item 70; who writes = item 75. The Wed 05:45Z row no longer lists 58 or the run_real_check_n8n.py part; GROUP D lines for 38 (d) and the "same script, two times" line updated.

## M3 "none stated" items
Each item with "DEFAULT: none stated ... not stated" now carries "AUDIT PROPOSAL, lead to confirm" with a step wait or "the step does not run": items 33, 34, 35, 36 (a to d), 37, 38 (a to f), 47, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 68, 69, 71, 72, 73, 566 line (one person or several), and the "schedule effect" lines of index rows 514, 516, 526 and the Tue 14:00Z row. Waits come from RUNBOOK section 6 numbers (171-minute spare, latest start of step 1 06:51Z) and the item's step; the 30-minute wait is the audit's own figure (a proposal, not from a lead file). Item 73: proposal that GO does not depend on it, because grep of TAKE-CHECKLIST.md for qualify_stage shows 0 hits (UNVERIFIED by the lead).

## M4 glossary
One glossary added at the end of the KEY paragraph (QUESTIONS.md line 422, no new line): GO row 1 to 7, Block R1 to R8 with sub-blocks, answer cells, L-numbers, TAKE-CHECKLIST row 3 (c). Meanings checked against TAKE-CHECKLIST.md lines 180 to 186 and block headings, RUNBOOK section 4.

## Nits
Item 26 against item 18 (both 07:00Z): GROUP D now says they are answered in one message, item 18 first. 15A: index row says where it is (last item, after the History heading). Item 39: its own times are stated in one place.

## Item 75 (new, first message)
Who writes the post-twice script before Tue 09:00Z (RUNBOOK W-Wed counts the 30 minutes, W-Tue does not; fix-tcfp12.md M1): answer-by Tue 17 Nov 06:15Z, IF UNANSWERED = audit proposal (nobody named, GO row 2 not passed, NO-GO). Arithmetic: W-Tue 170 + 30 = 200 minutes, start 00:40Z instead of 01:10Z (audit's own sum; RUNBOOK not changed).

## Second message from the coordinator
1. New item 76 (grouped, parts a to e): Q-A person at the keyboard in scenes 1 to 3 (answer by Tue 14:00Z), Q-D web addresses (Tue 14:00Z), Q-G caption program (Wed 11:00Z), Q-I channel for "tell the lead" (Tue 06:30Z, with item 9), Q-J (the check is item 73 (c); part e adds where the result is written, Tue 08:00Z). Each part has an IF UNANSWERED line (audit proposals). RUNSHEET-WORDING.md still says "no Q31 item" at lines 21, 67, 143, 451: not edited here.
2. New item 77: the made-up address that lands in the intake mailbox and the name of its setting; answer by Tue 05:00Z with item 61; IF UNANSWERED = step 9 waits 30 minutes, then NO-GO; no address invented.
3. Items 39 (a), 39 (b) and 43 corrected to ORDERS.md line 156 item 10 (Q27 item 10: owner types y, the challenge and end on camera; also Step D, S9-3, S9-2) and line 166 item 4 (Q28 item 4: current owner list, no Step A). Item 43 is now [ANSWERED]; item 7 notes that who types is answered; index rows (Tue 14:00Z row, GROUP D 7 + 39 (a) + 43 and 2 + 39 (b), the 39 (b) IF NOT) and the "notes without a question" line updated.
Index 66: rows added for items 74, 75, 76, 77 and the Tue 09:00Z row; GROUP D lines added for 73 (c) + 76 (e) and 61 + 77.

## Counts (script output, run at 14:50Z on Mon 16 Nov, from the Q31 heading to the end of the file)
{('main', 'OPEN'): 68, ('main', 'ANSWERED'): 1, ('main', 'NOTE'): 1, ('second/15A', 'OPEN'): 2, ('second/15A', 'NOTE'): 5, ('second/15A', 'ANSWERED'): 1}
labelled 78 OPEN 70
Main list: 70 numbered items (1 to 39 and 47 to 77); second list 40 to 46 (1 OPEN, 1 ANSWERED, 5 NOTE) plus 15A (OPEN). Count lines updated at QUESTIONS.md lines 40, 42, 449, 579 (and 421, 445, 567).

## Checks
- python3 tools/check_refs.py -> PASS 5166 references
- python3 tools/check_names.py -> PASS 655 rows
- python3 tools/check_secrets.py -> FAIL 1 hit (flow-check/raw/test-take-check.txt:178), not mine, see top.
Not checked: a full re-read of every edited item for wording by a second reader; check_counts.py and other checkers were not run.
