# fix-questions1: fixes to QUESTIONS.md from line 420 on (Q31)

Fixer: a Claude session, static only (nothing was run except the six checks at the end). Date: 2026-11-16. All new text is untested static wording. Reviewer words are quoted as unverified. Nothing was committed or pushed.

Inputs read in full: reviews/questions-reader-r1.md (11 Majors; the reader's own read was incomplete), reviews/questions-reader-r2-500-579.md (M1 to M11), reviews/questions-reader-r2-660-739.md (B1, M2 to M14).

## What did not go perfectly (read first)

1. No lead decision, time, rating or default was changed. Where two values clash and the files do not say which wins, the clause says LEAD DECIDES with an owner and a due time, and both values stay visible. That is about 39 new LEAD DECIDES marks (49 in the file now, 10 before; one decision can carry two marks). They are decisions for the lead, not fixed by this pass.
2. Some clauses rest on reviewer words, which I did not check against the other files: the 12:14Z, 12:25Z and 12:55Z take starts of item 85, the RUNBOOK 08:30Z against 09:45Z times of items 120 and 130 (I did not re-read RUNBOOK), the 07:30Z clash of item 108 with items 87 and 101, and the order of items 18, 21 and 26 in the two lists. Each clause says "reviewer words unverified".
3. The IST pass was automatic: 787 bare times ending in Z got "(HH:MM IST)" added by a pattern. After a time that is later than 18:30Z the text says ", next day". A few forms were left alone on purpose (a time already followed by "(", "=" or "IST"; table cells of the answer-by column got a Z only). I spot-checked 8 places, not all 787.
4. Line numbers below are the numbers after my edits (the file grew from 812 to 815 lines).
5. Not done, and why: see section "Not fixed" below.

## Check results (run from handover/flows-audit after the last edit; last lines printed in my report)

See the end of this file for the exact last lines.

## Per item

| Reader point | Item and line | Result | What was done or why not |
|---|---|---|---|
| r1 M6 stale count | line 498 | fixed | "130 numbered items" became "134" (39 + 95 = 134; 132 OPEN + 1 ANSWERED + 1 NOTE). The older sentence is kept with a note. Lines 40 and 42 (frozen) still say 130: for the lead. |
| r1 M7 glossary | line 421 (new, before the heading) | fixed in part | A short glossary was added before the heading: L5, L12, L22, L24, L32, Q17 and the other Q sections, Row 4, RW, CT, F-003/011/018/029/031/037, T19/T19H/T20/T21, scene 4, NO-GO/SLIP/NO TAKE, TAG, GROUP C, item 43 of the second list, Timing case against Retake case, [step clock], LEAD DECIDES, S9-2/S9-3, V17/V18, P4a, N-5a, A-012, WL-3, K3/K3B. K3 and K3B are NOT defined (the finding row only says they mean different things): marked UNVERIFIED. Not done: "about 15 labels" became about 30 in one paragraph; the reader asked for a read-me style, which I did not format further. |
| r1 M1 what wakes the lead | line 423 (READ THIS FIRST) | already fixed before this pass | The paragraph "WHAT STARTS THE LEAD" already says no file says it and carries a LEAD DECIDES. Only IST was added by the pass. |
| r1 M2, r2 M1, M2 item 3 | line 501 | fixed (by clause) | Split into (3a) how many sends and which runs, and (3b) the ask for a new written yes for a retake: owner, no time stated anywhere, so LEAD DECIDES; default on silence = no retake (item 1). Ceiling 3 against the count of 4 of item 117: both values kept, LEAD DECIDES. |
| r1 M3 item 1 and 134 | line 499 | fixed (by clause) | States the times of item 134 and that item 1 does not say it uses them: LEAD DECIDES. |
| r1 M8, item 1, 2 | lines 499, 500 | already structured | Both already carry SUB-ITEMS with one default and one time each (earlier fix). No further change except IST. |
| item 5 | line 503 | fixed | Plain question first; owner, due time and default. |
| r2 M3 item 6 | line 504 | fixed (by clause) | Last send 10:07Z (15:37 IST) against 10:18Z (15:48 IST) in the hand-run case, after the chase at 10:08Z (15:38 IST): both kept, LEAD DECIDES, due 06:50Z (12:20 IST). |
| r2 M6 item 7 | line 505 | fixed (by clause) | "stays as the lead names it later" now has an owner and a due time; the default is stated as not stated in the files. |
| r2 M4, M5 item 8 | line 506 | fixed (by clause) | The same take-prep decision asked in items 8, 27, 30, and the three take-start limits (10:00Z, 11:30Z, 12:00Z) against Timing case starts 10:07Z and 11:02Z: both kept, LEAD DECIDES. I did not pick a winner. |
| r2 M8 items 21, 26 | lines 519, 528 | fixed | Plain question first. The F-011 repeat of item 10 (a) and the missing path for F-037/F-029 are named with a LEAD DECIDES. Item 26's title already said six or seven (item 89): already fixed before this pass. Order of 18, 21, 26 added. |
| r2 M7 item 24 | line 522 | fixed | Plain question first; split (a1) late message, (a2) whether the owner still writes "missing: GO or NO-GO" at 16:00Z (21:30 IST); "bring Wednesday back" LEAD DECIDES. |
| r2 M9, M10, r1 M11 items 27, 30 | lines 529, 532 | fixed (by clause) | The two reply-by times (Tue 01:00Z, Wed 08:00Z of item 120) are both visible with LEAD DECIDES; one silence rule: the ask is sent only by the lead and silence is recorded "not confirmed". |
| r1 M10 item 33 | lines 535 and the index row of 04:00Z | fixed | Plain question first; the Monday 21:00Z ask and the owner's reply-by Tue 01:00Z were added to the index row. |
| r1 M5 items 34, 59, 38 (b) | index row of 03:30Z | fixed (by clause) | Both consequences kept (no default and step 1 cannot start, against step 1 waits then does not start): LEAD DECIDES. |
| r1 M4 items 47, 132, 140 | lines 543, 744, 764 | fixed (by clause) | Plain question first; the three times 03:30Z, 04:54Z and 06:59Z are listed in item 47; LEAD DECIDES whether 140 answers 47. |
| r2 M2, M3 item 69 | line 661 | fixed | Plain question first, one latest time to decide (04:51Z, 04:40Z or 04:46Z), the RUNBOOK line 336 value added, and the order with item 113 as LEAD DECIDES. |
| r2 M2, M12 items 71, 72, 77 | lines 663, 664, 674 | fixed | Plain question first; item 71 split into (71a), (71b), (71c) with owner, time, default. |
| r2 B1 items 73 and 104 | lines 666, 716 | fixed as asked, not decided | Both texts are stated and the question is LEAD DECIDES: is 73 (c) the same check as RW step 2a? Owner the lead, due Tue 17 Nov 08:00Z (13:30 IST). I did not pick. |
| r2 M12 item 74 | line 668 | fixed | Parts (74a-c), (74d), (74e) each with owner, time and default. |
| r2 M12 items 75, 76 | lines 670, 672 | fixed | Parts with owner, time, default; the three-item overlap of run_real_check_n8n.py and the post-twice script is a LEAD DECIDES; the "none asks the owner" against (c) is a LEAD DECIDES. |
| r2 M4, M5 items 80, 81 | lines 677, 678 | fixed (by clause) | Order against items 105 and 109 stated; LEAD DECIDES. |
| r2 M9 item 85 | line 697 | fixed (by clause) | The default 06:53Z gives take starts after 12:00Z in three of four cases: LEAD DECIDES. |
| r2 M9 item 84 table, Sun 22 Nov row | lines 692, 695 | fixed | The replacement gate text was moved word for word into a paragraph below the table; the cell points to it. |
| r2 M13 items 89 to 91 | lines 701 to 703 | fixed | The three repeated paragraphs (1272 characters, compared before replacing: all three equal) are written once in item 89; items 90 and 91 point to it. "A seventh counted row" is explained; the F-031 difference is a LEAD DECIDES. |
| r2 M6 items 95, 96 | lines 707, 708 | fixed (by clause) | Both consequences kept, LEAD DECIDES. |
| r2 M11, M12 items 100, 110 | lines 712, 722 | fixed (by clause) | Parts, owners and times; the timing clash against the GO minute is a LEAD DECIDES. |
| r2 M8 item 103 | line 715 | fixed (by clause) | LEAD DECIDES ask earlier or drop the condition. |
| r2 M14 item 108 | line 720 | fixed | Plain question first; line 270 is frozen and is listed below for the lead; the possible clash with items 87 and 101 is a LEAD DECIDES. |
| r2 M3 item 113 | line 725 | fixed | Pointer to item 69. |
| r2 M10 item 117 | line 729 | fixed | "ANSWER BY" given, count 4 against ceiling 3 kept as LEAD DECIDES. |
| r2 M7 items 120, 130 | lines 732, 742 | fixed (by clause) | Same question marked; both times and both RUNBOOK claims kept. |
| r2 M9 item 122 | line 734 | not deleted, fixed | The seven times are already explained in the text, so no list was removed (nothing deleted); "answered by item 85" added. |
| r2 M12 item 126 | line 738 | fixed (by clause) | Five parts named, each with owner, time and default. The rulings themselves are not copied from RUNBOOK (not verified). |
| r1 M9 item 135 | line 747 | fixed (by clause) | "Fixes applied" against "steps run as written until then": LEAD DECIDES which first. |
| r1 M8 items 136, 137, 141, 15A | lines 748, 749, 765, 761 | fixed (by clause) | Parts with owners, times, defaults. 15A already explains that "you" means the human key holder. |
| r1 smaller: table lines 469-491, item 45 | lines 470-493, 759 | fixed | "Z" added to the answer-by column; item 45 "08:25 to 08:40Z" got IST. |
| r2 M14 IST and labels | many | fixed by pass | 787 times got IST. Forms such as "06:20Z = 11:50 IST" were left as they are. |
| r2 M14 RW, CT, Group C, TAG GO, item 43 | line 421 | fixed | In the glossary. |

## Not fixed

- r1 M7: the glossary is not placed in a separate file and does not mark every reader or fix tag as provenance. Reason: only lines 420 and later may be edited; the fix-q31-N tags carry the provenance already.
- r2 M12: item 76 header text about "none asks the owner" was kept as it was; the conflict is marked as LEAD DECIDES.
- r2 M7: I did not re-read RUNBOOK to settle 08:30Z against 09:45Z. This needs the lead.
- r2 M5 and M4: the order of decisions (which item is asked first) is kept as a LEAD DECIDES; it needs the lead.
- The new LEAD DECIDES clauses (about 39 marks) need the lead. I named the lead as owner because the item asks the lead; no human is named by me.

## For the lead (problems in lines 1 to 419, frozen, not edited)

- Lines 40 and 42 say "130 numbered items" (current count 134).
- The glossary rows at lines 161, 163 and 178 are stale (reader r1).
- Item 6 and the owner sheet and glossary give 09:30Z, this file 09:43Z.
- Q13 line 270 ("listed once") conflicts with items 5 and 108.
- Item 3 ceiling 3 against item 117 count 4.
- Items 40 to 46 stand outside the main numbering.
- The glossary was placed as line 421, directly before the "## Q31" heading, because the brief said before line 421; line 420 belongs to the section above. It sits above the Q31 heading, so a reader of the Q31 section starts one line earlier than before.

## Final check lines

1. `sed -n 1,419p QUESTIONS.md | md5sum`: 682a52817ce62b3c (unchanged)
2. `python3 -I tools/check_refs.py`: PASS 5190 references
3. `check_names.py`: PASS 655 rows
4. `check_secrets.py`: PASS 0 hits in 3022 files
5. `check_counts.py`: PASS 52 files / 655 nodes
6. `ruff format --check .`: 1147 files already formatted
