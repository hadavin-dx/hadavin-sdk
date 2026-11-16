# fix-q31-1: Q31 lead-readability fixes (fixer; nothing run except check_refs.py and check_secrets.py)

## Uncertain or not done (first)
- Review items checked against the file myself; the reviewer's counts were out of date (the file had grown to items 1 to 58 while I worked).
- Per-item "IF UNANSWERED" lines for items 32 to 65 say "DEFAULT: none stated; lead decides" where the item states no default. I invented none. What the schedule does while an input is missing (wait, skip, NO-GO) is not stated in those items; the lead decides.
- Not rewritten: the 600 to 1000 word items (1, 3, 8, 10, 24, 27, 30) keep their text. Their one-line ask, time and default are in the index item 66 instead (M1 handled by the index, not by splitting the paragraphs). The reuse of sub-letters and the skipped letters in item 24 are explained in item 24 itself; left as is.
- check_secrets.py prints FAIL 1 hit at flow-check/raw/test-take-check.txt:178 (token-like, length 47). That file is not mine and I did not open or print the value. Needs the owner of that raw log to check it; I changed nothing there.
- Race: fixer aad5a30 (fix-tcfp10.md) may still point at the old numbers 40 to 46 in files it edits later. If so, they mean 59 to 65.

## Coordinator message: number clash (done)
- The round 14 inputs numbered 40 to 46 clashed with the RUNSHEET-WORDING items 40 to 46. Per the coordinator I renumbered only the NEW ones: 40->59, 41->60, 42->61, 43->62, 44->63, 45->64, 46->65, moved after item 58 in QUESTIONS.md.
- Pointer fixes by regex (only "item(s) N" next to Q31/QUESTIONS): FIX-PLAN.md 6 lines, RUNBOOK.md 3 lines, TAKE-CHECKLIST.md 2 lines (including "items 40 to 52" -> "47 to 52 and 59 to 65"), fix-tcfp10.md 4 lines (including "40-58" -> "47-58 and 59-65"). Backups: scratchpad `*.bak-q31-1`.
- Unique numbers now: grep of the lines after the Q31 heading shows no repeated item number (0 duplicates).

## Review items
- B1 counts: true count by grep: 59 numbered items in the main list (numbers 1 to 39 and 47 to 66), 57 [OPEN], 1 [ANSWERED] (item 20), 1 [NOTE] (the index, item 66); second list items 40 to 46 (2 [OPEN], 5 [NOTE]) and 15A ([OPEN]); 67 labelled, 60 [OPEN]. Written in the status row, the LEAD-ACTION COUNT paragraph and the line before item 1; stale sentences in items 38 and 39 and the Note (round 14) corrected.
- B2: second list (old 40 to 46) heading says it is live, not history; each item has [OPEN] or [NOTE], ANSWER BY, IF UNANSWERED. Addendum is now item 15A with the same.
- B3: items 32 to 65 each carry one appended line "ANSWER BY ... IF UNANSWERED ..."; abbreviated times in items 32 to 38 now carry the date.
- B4: duplicates listed in group D of the index (checked by reading each item); 14 (c)/46 and 6/24 (a) are NOT duplicates by their text (said so); the same-script/two-times clash with L20 and L27 and the "one person or several" question are stated with "DEFAULT: none stated".
- B5: key added in the paragraph before item 1; every mapping verified by grep in TAKE-CHECKLIST.md and OWNER-STEPS-q16-rows.md.
- B6: where answers go is stated once, before item 1: flows-audit/ORDERS.md, block "Q31 item N: answer"; owner replies copied by the lead.
- M2: statements labelled [NOTE]. M3: near deadlines flagged in item 66. M4: item 66. M5: counts fixed; twin script times stated. M6: item 12 links ORDER 037 item 2 (ORDERS.md line 177); the file list is UNVERIFIED.

## Files changed
QUESTIONS.md; FIX-PLAN.md, RUNBOOK.md, TAKE-CHECKLIST.md, fix-tcfp10.md (pointers only). Backups in the scratchpad. ORDERS.md not touched. Not committed.

## Raw output of python3 handover/flows-audit/tools/check_refs.py (run from flows-audit, exit code 0)
```
PASS 5166 references
```

EGM skipped: edit of audit notes by a fixer on the lead's instruction; the lead runs the review step. R-numbers: none looked up (no bible access here).
