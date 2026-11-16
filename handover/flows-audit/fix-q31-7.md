# fix-q31-7 (fixer log, Mon 16 Nov 2026)

Scope: QUESTIONS.md only (Q31 part from line 420, plus the count sentences at lines 40, 42, 449 and the Note paragraph). Nothing committed. No answer of the lead was changed.

## What is NOT done or not checked (first)
- NOT verified by the lead: every new default is an audit proposal, marked "lead to confirm".
- Item 84 default (new re-pin day = next calendar day, Wed 18 Nov) is the audit's reading; no file names a day.
- Item 85: where the 367 and 422 minute sums come from was taken from the old item 6 text and RUNBOOK section 8; only the arithmetic after them was recomputed (below), not the sums themselves.
- Item 80/81: RUNBOOK step 4a does not say where the sentence of item 80 goes; the text says so (UNVERIFIED) and gives a reading.
- Not run: flow-check and raw (no such script exists under tools/; not mine).
- Not done: RUNBOOK.md and the owner sheet were not edited (out of scope); RUNBOOK step 4a still needs a line that items 80 and 81 exist.
- I planned items 83 to 88 and wrote 83 to 87 (five); no item 88 was needed, since the positive-control send and the "same file?" question took 86 and 87.
- An own slip: my first edit script lost three edits (item 78 default, item 58 split, new items) because of a Python name-binding mistake; I detected it by grep, redid them, and re-ran the three checks afterwards. Another slip: a global replace of backslash-quote removed two original `\"` sequences (lines 185 and 472 of the original); restored and counted (2 and 2).

## Changes per review finding (reviews/q31-lead-readability-r6.md 1-14, citation-q31-r2 Nits)
- Item 6 split into 6, 83 (which cut-off decides NO-GO), 84 (what a Tuesday NO-GO triggers), 85 (slip-day arithmetic). Each has one default and one answer-by time (6 and 83 at 06:50Z in ONE MESSAGE; 85 at 06:56Z; 84 at 06:57Z).
- Item 25 / 53 / 38 (c): one time (06:00Z), one message, 25 first; each item has its own default; new item 86 (is the Tuesday loop the same file as the reviewed script?).
- Item 58 split: it now means only the reviewed file on the review branch (due Tue 09:00Z); the positive-control send of two different lead IDs is item 87 (Wed 05:45Z). Glossary names the three meanings of "post-twice script". Citations of "item 58" in other files stay valid.
- Items 8 (e) / 49: one time (Tue 07:00Z), one message. Item 14 (b)/38 (a): one question, one message.
- Items 34, 59, 38 (b) and the SCHEDULE EFFECT line of item 66: the 06:51Z wait limit removed (06:51Z is the latest start of step 1, 04:00Z + 171; a wait up to it would use the whole spare); default is 30 minutes after the step's start time.
- Item 78: single default (step 8 waits 30 minutes after 05:29Z, then does not run; NO-GO).
- Item 61: the eight key names listed from RUNBOOK step 9 (a), names only, no value.
- Item 69: "DECISIONS items 1 and 7" and "run sheet N-9..N-11" explained; what the new text must express stated.
- Item 4: V19 and V20 explained. Item 5 and 8 (d): rehearsal 2 end stated as 09:25Z (dated plan) or 09:37Z (with start-state checks), not 09:35Z/09:47Z.
- Item 15: end-time mix-up corrected (start 03:31Z -> end 08:00Z, 4b 03:57Z, 13 06:45Z; an end of 07:00Z would mean start 02:31Z, 4b 02:57Z, 13 05:45Z).
- Items 80, 81 (citation Nits) and item 6's stale "355, lead to confirm" sentence: reworded (no 355 default remains; 355 appears once in item 85 as the old count).
- Glossary paragraph: Row 4, GO row N, timing case 1/2, Retake case A/B, chain sum 1/2, the sheet's Case A, gate, clock, step, step clock, re-pin event, post-twice script, ONE MESSAGE.
- Table, "Order of answers", item 66 index: one-message pairs marked (25+53+38 (c)+86; 83+6); rows added for 84, 85, 87; line 421 garble fixed; "items 32 to 87" and "items 67 to 87" updated.

## Recompute (python3 output)
```
sum1 367 take starts 307 after event end; latest end for 12:00Z 06:53; for 11:55Z 06:48
sum2 422 take starts 362 after event end; latest end for 12:00Z 05:58; for 11:55Z 05:53
re-pin end 07:00Z -> take at 12:07Z
rehearsal block from 07:30Z: +115 = 09:25, +127 = 09:37 (from 07:40Z the figures 09:35/09:47 are wrong: that is rehearsal 1's start)
start 03:31 -> end 08:00, 4b 03:57, 13 06:45; start 02:31 -> end 07:00, 4b 02:57, 13 05:45; 04:00 + 171 = 06:51
```

## Counts (script over QUESTIONS.md from line 420)
Main list: 80 labelled (78 OPEN, 1 ANSWERED, 1 NOTE); second list: 8 (2 OPEN incl. 15A, 1 ANSWERED, 5 NOTE); total 88 labelled, 80 OPEN. Count sentences at lines 40, 42, 449 and the Note paragraph updated.

## Checks (from flows-audit, python3 -I)
```
check_refs.py    PASS 5176 references
check_names.py   PASS 655 rows
check_secrets.py PASS 0 hits in 1991 files
check_counts.py  PASS 52 files / 655 nodes
```
Changed line numbers (diff against backup): 40, 42, 421-422, 431-597 (Q31 items, table, index) and new lines 598-602 (items 83-87), 604.
