Status: DRAFT, unverified

# Runbook v4.3 patch: overlay of the lead's answers 1-26 (written 2026-11-16, UTC)

Purpose: re-mark rows of `work/RUNBOOK-V4.3-PATCH.md` (P01-P62, OD-01..OD-25) and `work/RUNBOOK-V4.3-PATCH-timing-v42.md` (PH-01..PH-17, H-1..H-7) against `work/LEAD-ANSWERS.md`. This file replaces nothing. Rows not listed here keep their old status and text. Nothing was run, no code was read, no v4.2 or patch file was edited.

## Glossary (read first; one line each)

- **P-row** (P01 to P80): a numbered edit row in `work/RUNBOOK-V4.3-PATCH.md`; each row says which v4.2 line changes and to what.
- **OD** (OD-01 to OD-32): an open-decision row in the same patch file: a question the lead must answer before a row can be written. OD-26 to OD-32 are the timing holds H-1 to H-7.
- **PH** (PH-01 to PH-17): a timing edit row in `work/RUNBOOK-V4.3-PATCH-timing-v42.md` (changes about the 49-minute window and clock times).
- **H-row** (H-1 to H-7, with H-1a, H-1b, H-3b): a held question in the timing file; "held" = do not apply until the lead answers.
- **r34, r35, r36**: build rounds of the take program and its scripts, each reviewed by the lane D review lane. Recorded: r34 = take-program wording (report 13s), r36 = exact wording (report 13r); from the lead answers: r35 removes the cap constant SELF_TEST_CAP_TOTAL_USD and moves `build_notice` inside the try. Report names of r35: NOT RECORDED.
- **r37, r38, r39**: the three branches under review now. Answer 24 says they carry the final wording of rounds 36, 34, 35. The pairing r36 to r37, r34 to r38, r35 to r39 is MY READING (order of the sentence), TO CONFIRM BY THE LEAD. Further facts from the answers: round 37 removes lslocks from the start script; round 39 widens the except and restores the "cap above credit total refuses" line.
- **refusal A**: the take program refuses when the code cap (DESK_LIVE_CAP_TOTAL_USD) is above the credit total typed as REAL_CONSOLE_LIMIT_USD. **refusal B**: it refuses when the cap minus the ledger total is above the credit total minus the spent figure the owner typed. **refusal C**: it refuses when a money figure above the allowed maximum cannot be shown (exit 2, answer 21). Source: P23, P34.
- **X1**: the owner exemption for a cap literal in code (patch row P23, OD-08). Refused by answer 19.
- **drop-A**: the proposal (lane D report 13p, item X3) to remove refusal A because A and B are the same check twice. Refused by answer 20: both stay.
- **form (b)**: the take program `run_real_check_n8n.py --take`; form (a) is the post-twice script (patch OD-14). Whether form (b) reaches refusals A and B: NOT RECORDED.
- **LEAD-ANSWERS.md**: [`work/LEAD-ANSWERS.md`](LEAD-ANSWERS.md). **"answer N"** = item N of that file (for example answer 4.2 = its item 4.2).
- **LEAD-DECISION** (status word): the lead must decide before the row can be applied. **WAITING-ON-CODE**: waits for the final wording of a named round.

## How to read this overlay

- Status words are the existing six: READY, WAITING-ON-CODE, LEAD-DECISION, HELD, ALREADY-IN-V4.2, NO-PLACE. The timing file has no status words on its PH rows; their old status is shown as "none" plus its own mark ("DO NOT APPLY until H-1" or "safe"). A closed question that carries no text (H-1, OD rows) is marked READY (answered) or ALREADY-IN-V4.2 (v4.2 stands); the note says which.
- Answer 24 (the lead): apply the wording and remove the "ROUND NN PENDING" labels at v4.3, but only against the FINAL wording of rounds r36, r34 and r35, which the branches r37, r38 and r39 carry. The pairing r36 to r37, r34 to r38, r35 to r39 is TO CONFIRM BY THE LEAD (my reading of the order of the sentence; not verified). Every row that cites it is WAITING-ON-CODE (the round named in column 6; rows P01 to P47 below and those marked r34, r35, r36, r37 or r39). Answers 21, 23 and 20 name rounds 35, 37 and 39 directly; those names are copied.
- LEAD-DECISION rows added in this fix: PH-01, PH-02, PH-03 and H-3 (the 10-minute film pause: is it inside the 49 minutes? 17:40Z plus 49 plus 10 minutes ends after 18:29Z) and H-6 ("late" is not defined). Every other row that uses 17:40Z (PH-04, PH-06 to PH-09, H-2, OD-10, H-1b) shows no pause in its text and keeps its status, but is read with the same open question.
- Answers used by number: 3 delete design; 4.2 take port; 6 what the 49 minutes cover; 7 latest start; 8 film pause 10 minutes; 9 no same-day rerun; 12 no heavy job on the take laptop; 14 the 49 is computed; 15 parts a to g; 16 which cut-off governs; 17 clean-up next morning; 18 limit 180 s; 19, 20 money refusals; 21 exit 2; 22 exit-3 header; 23 drop lslocks; 24 apply only against final wording.
- Meaning of 49 (answers 6, 14): the take program computes it as 2630 s plus 6 times the lease seconds, rounded up (49 minutes at lease 45); it is not stored in stage.env and it is not a measured run time. It covers only the program's own run (posts, table and mail waits, final reads, margin). Typing `y`, the confirmation line and `end`, and owner steps A to D, are outside it (answer 15a).
- "v4.2 has no 18:15, 18:14:40 or 14-minute figure": I searched v4.2 for 18:15, 18:14, 14 min, about 14, 17:40 and 49 min: no hit. Answer 7's "change 18:15 and 18:14:40 everywhere" therefore changes other files (v5, TAKE-BLOCKERS, owner-timeline), not this patch.

## Overlay table

| row id | change the row makes (one clause) | old STATUS | new STATUS | answer | final-wording round | new text if the answer changes it |
|---|---|---|---|---|---|---|
| P08 | replaces section 10 step 5 with a per-contact delete design | HELD | ALREADY-IN-V4.2 | 3 | none | No edit. The replacement of section 10 step 5 (lines 510-514) by a per-contact design is cancelled. v4.2 stays: the owner deletes leftover contacts by a filtered list (lines 100, 105, 593 already say so). |
| P36 | inserts after the owner-types bullet that `end` only closes the pause and deletes nothing | HELD | WAITING-ON-CODE | 3 | r34 | Insert after the owner-types bullet (line 486): "`end` only closes the pause. The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list." Heading: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)". The old "unverified" hold is closed by the lead's answer; wording is checked once against the final r34 closing text. |
| P43 | adds the take addresses and the program clean-up line to item 3 | READY | WAITING-ON-CODE | 3 | r34 | Keep the row as written. Read its clean-up line ("delete them in the HubSpot screen") together with the answer: the owner deletes leftovers by a filtered list. The program's own line is taken from final r34. |
| P48 | writes "up to 3 made-up contacts are left for you to delete by hand" | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste "up to 3 contacts". v4.2 keeps its count (maximum 11 or 12, line 252) and "the contacts of the take stay until the one owner clean-up". |
| P49 | adds a STOP step that waits for the studio lead list, 15 minutes | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the "STOP ... wait for the studio lead's list ... 15 minutes" text. v4.2 line 510 trigger stays. |
| P50 | adds a clean-up message listing lead id and contact id, at most 3 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the per-contact list (lead id plus contact id, at most 3). v4.2 line 512 stays (account name and filter text). |
| P51 | adds the release words "contacts may be deleted" and an open-each-contact step | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the release words "contacts may be deleted" or the open-each-contact step. v4.2 "clean-up starts" stays. |
| P52 | adds delete-one-contact-at-a-time steps | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the delete-one-contact-at-a-time steps. v4.2 stays: bulk delete of the filtered list; the lead re-runs the search (expect 0) before the owner revokes keys (lines 514, 596). |
| OD-17 | asks which delete design wins (filtered list or per contact) | HELD | ALREADY-IN-V4.2 | 3 | none | Closed: the filtered-list design wins; v4.2 stands; the program's `end` deletes nothing (confirmed by the lead). |
| P34 | adds refusal C (a money figure above the allowed maximum) to the refusal list of form (b) | WAITING-ON-CODE | WAITING-ON-CODE | 21 | r35 (r39 widens the except) | Write exit 2 for refusal C: "refused: a money figure above the allowed maximum cannot be shown: check the typed figures". Applied only against final r35 and r39 wording. |
| OD-09 | asks whether the exit number for refusal C is 1 or 2 (build_notice outside any try) | WAITING-ON-CODE | WAITING-ON-CODE | 21 | r35, r39 | Question closed (exit 2, fixed in code). The row waits only for the final wording. |
| P16 | gives the exit-3 bullet header at line 159 (no wording was given) | LEAD-DECISION | WAITING-ON-CODE | 22 | r36 | Header at line 159 becomes: "Exit 3 (the lock is still held by a process this script cannot see)". |
| OD-02 | asks for the wording of the exit-3 header | LEAD-DECISION | WAITING-ON-CODE | 22 | r36 | Closed by the header text in P16. |
| OD-04 (33-36 rows 21, 22: lines 376, 380) | asks whether the held-lock refusal keeps the words "lslocks shows it" | HELD | WAITING-ON-CODE | 23 | r37 | Drop lslocks. The candidate string loses the words "lslocks shows it". Lines 376 and 380 keep the v4.2 strings until the final r37 text says what remains of "(a shared lock or a process of another user also counts)"; no new string is written here. |
| P23 | adds the two money refusals A and B for `--take` and an exemption sentence for a cap literal | LEAD-DECISION | WAITING-ON-CODE | 19, 20 | r35 (cap constant removed), r39 (cap-above-credit refusal restored) | Keep both refusals A and B (answer 20). Delete the sentence about an owner exemption for a cap literal: refused and moot, because r35 removes SELF_TEST_CAP_TOTAL_USD; stand-in numbers live in demo_only/dry_fakes.env.example. Refusal A is the spent-figure-independent line "cap above credit total refuses". Texts of A and B are taken from final r39. |
| OD-08 | asks about dropping refusal A, exemption X1, whether form (b) reaches A and B, and naming the wrong figure | LEAD-DECISION | LEAD-DECISION | 19, 20 | r35, r39 | Partly closed: exemption X1 refused (19); drop-A refused, both stay (20). Still open: does form (b) (`run_real_check_n8n.py --take`) reach A and B; should A and B say which figure is wrong (13p Y4). No answer covers those two. |
| P45 | replaces the ROUND 28 PENDING text with the window check after the `y` prompt and its refusal | WAITING-ON-CODE | WAITING-ON-CODE | 6, 7, 14, 15 | r34 | Delete "[49 = PROPOSAL ...]". Write: the 49 minutes is computed by the program (2630 s plus 6 times the lease seconds, rounded up; 49 at lease 45; no stage.env value) and covers the program's own run only. Never write "about 14 minutes" or "about 15 minutes". Refusal text and the order of checks come from final r34. |
| OD-10 | asks whether to add a sentence that the program refuses a start with too little time | WAITING-ON-CODE | WAITING-ON-CODE | 7, 14 | r34 | Optional sentence adopted: "the program refuses a start that leaves less than 49 minutes before the stop time; latest start 17:40 UTC = 23:10 IST at lease 45". The 13s X-2 doubt (formula not strictly worst case) is a code check, still open. |
| H-1 | asks what the 49 minutes contain | none (blocking question) | READY | 6, 14, 15 | none | Answered. Inside the 49: (b) scene 4 stop and restart (inside person C's post wait), (c) both mailbox waits, (e) the 120 s wait after Ctrl-C (margin), (f) final reads (margin only, not measured), (g) clean-up (margin only). Outside: (a) typing `y`, the confirmation line and `end` (before the window check), (d) the film pause (no pause term in the formula; answer 8 limits it to 10 minutes with an alarm). Releases the PH rows below. |
| H-1a | adds the 120 s Ctrl-C wait wording to line 493 | HELD | WAITING-ON-CODE | 15e | r34 | Add to line 493 (with P41): "(the 120 s wait is inside the margin of the 49-minute worst case)". |
| H-1b | adds the window-too-close wording at line 450 | HELD | WAITING-ON-CODE | 7, 14 | r34 | Line 450, "window too close": add "the program refuses a start that leaves less than 49 minutes before the stop time (computed from the lease)". The 14-minute figure is obsolete. |
| H-2 | reconciles the 12:00Z slipped-take cut-off with the 17:40Z latest start | HELD | READY | 16 | none | Lines 107, 222, 265, 482, 526: "A slipped take should start by Mon 23 Nov 12:00Z (17:30 IST); this is the planning target, so a failed run still has the afternoon. The HARD latest start is 17:40Z (23:10 IST) at lease 45." 12:00Z means the start, not the end. The conflict noted in PH-08 disappears (its example start 11:55Z is before noon). |
| PH-01 | rewrites line 107 (money stop and latest start of a run that spends) | none (DO NOT APPLY until H-1) | LEAD-DECISION | 6, 7, 14 | none | Line 107: "Money stop Mon 23 Nov 18:29Z (23:59 IST). The program refuses a start that leaves less than 49 minutes before the stop time; latest start 17:40Z (23:10 IST) at lease 45." Delete "the lead's order ... not a measurement". LEAD-DECISION until the lead confirms whether the 10-minute film pause is inside the 49 minutes (17:40Z + 49 + 10 minutes ends after 18:29Z). If the lead says it is inside or not needed, apply the text below as written. |
| PH-02 | adds a section 3 table row for the latest start of a run that spends | none (DO NOT APPLY until H-1) | LEAD-DECISION | 7, 14 | none | Line 223, new row above the money stop: "Latest start of any run that spends (49 minutes before the stop, at lease 45) / Mon 23 Nov 17:40 / 23:10 / lead answer 7 of 16 Nov". LEAD-DECISION for the same reason as PH-01. |
| PH-03 | rewrites line 236 (no run that spends starts after the latest start) | none (DO NOT APPLY until H-1) | LEAD-DECISION | 7, 14 | none | Line 236: "No run that spends starts after 17:40Z (23:10 IST) at lease 45; the program refuses a start with less than 49 minutes left." LEAD-DECISION for the same reason as PH-01. |
| PH-04 | rewrites line 76 (how the 49-minute figure is labelled) | none (DO NOT APPLY until H-1) | READY | 14 | none | Line 76: "The 49-minute figure is computed by the take program from the lease (2630 s plus 6 times the lease seconds, rounded up); the 17:40Z latest start follows from it at lease 45. Neither is a measured run time." |
| PH-05 | adds an H-1 item to the NOT DONE list at line 109 | none (DO NOT APPLY until H-1) | NO-PLACE | 6 | none | Dropped: H-1 is answered, so nothing is added to the NOT DONE list at line 109. |
| PH-06 | rewrites line 88 (re-smoke has no limit; ask states the latest start) | none (DO NOT APPLY until H-1) | READY | 7 | none | Line 88: as proposed; the ask also states that the program can still start by 17:40Z (23:10 IST). |
| PH-07 | rewrites line 211 (re-smoke row with clock time and latest start) | none (DO NOT APPLY until H-1) | READY | 7 | none | Line 211: as proposed (clock time and "start by 17:40Z, 23:10 IST"). |
| PH-08 | rewrites line 266 (G7 with the latest start) | none (DO NOT APPLY until H-1) | READY | 6, 7, 16 | none | Line 266: as proposed; the take program must start by 17:40Z (23:10 IST); a planned start by 12:00Z (answer 16). Drop the "conflict stated outright" remark. |
| PH-09 | rewrites line 524 (Tue NO-GO routing: take-later start) | none (first change: DO NOT APPLY until H-1) | READY | 7, 16 | none | Line 524: "take later: the take program must start by Mon 23 Nov 17:40Z (23:10 IST), planning target 12:00Z". Second change (04:12Z, 03:17Z) unchanged. |
| PH-13 | rewrites line 473 (scene 4 rehearsal total time) | none (safe) | READY | 15b, 18 | none | Line 473: LIMIT_S = 180 s stays and the rehearsal measures the stop, start and takeover together. The scene 4 stop and restart sit inside person C's post wait, which the 49 minutes already contain. The 248 s sum stays an unmeasured example. |
| PH-14 | rewrites line 489 (counts proof: two mailbox waits) | none (DO NOT APPLY until H-1) | READY | 15c | none | Line 489: add "both waits (at least 340 s together) are inside the program's 49-minute worst case". |
| PH-15 | rewrites line 497 (slow answer margin, ROUND 28 PENDING) | none (DO NOT APPLY until H-1) | WAITING-ON-CODE | 15a | r34 | Do not apply. The window check comes after the typed answers, so a slow answer cannot push the take past the stop time once r34 is final. P45 replaces this row. |
| H-4 | asks for the margin before the round 28 change lands (line 497) | HELD | WAITING-ON-CODE | 15a | r34 | Closed as moot for the same reason as PH-15; no earlier latest start and no 10-minute margin is written. |
| PH-17 | rewrites line 583 (what this document did not check) | none (DO NOT APPLY until H-1) | READY | 6, 14 | none | Line 583: "the 49-minute figure is computed by the program from the lease and is not measured; the rehearsal measures the real run". |
| H-3 | asks how a planned 60-minute take fits a 49-minute slowest case | HELD | LEAD-DECISION | 6, 8 | none | Lines 218, 484: "about 1 h slot (the program's own run is at most 49 minutes at lease 45; the film pause is outside it and limited to 10 minutes, with an alarm)". Whether the program enforces the 10 minutes is core-hardening's answer, not written here. LEAD-DECISION: it uses 17:40Z and the film pause; same question as PH-01. |
| PH-16 | rewrites line 508 (same-day retake condition) | none (safe) | LEAD-DECISION | 9 | none | Answer 9: no same-day rerun; a failed run means a new day inside the credit window, decided by the owner. PH-16 and the retake sums in lines 226, 251, 252, 508 and 528 assume a same-day retake. The answer does not say whether v4.2's Wednesday retake after a bad recording also falls. The lead decides; nothing is applied. |
| H-3b | asks for the latest first start of a retake | HELD | NO-PLACE | 9 | none | No sentence about the latest first start of a retake is added: no same-day rerun on Mon 23 Nov. |
| H-6 | asks whether clean-up "the same day" holds after a late Monday take | HELD | LEAD-DECISION | 17 | none | Not applied. LEAD-DECISION: "late" is not defined in any source, so the lead must say what counts as a late take (and the owner whether the model key stays valid until the next morning). Not applied. |
| P12 | writes the rehearsal port 5690 and a take port placeholder | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | No port number is written in any document, including 5690. Text: "The take port is read from the take config; core-hardening confirms the variable name." |
| P13 | splits the port row into rehearsal and take, the take port named in one place | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | Same as P12: the plan names the variable once; every other mention points to it. |
| OD-15 | asks for the take port number and the second port | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | Partly closed: no fixed number anywhere. Not answered: the second port (5691, n8n runner broker, part1 C3). |
| N12 (new; no patch row exists) | adds a line forbidding heavy jobs on the take laptop before the start (v5 and RUNBOOK-SPEED-3) | none | NO-PLACE | 12 | none | The line goes to v5 and RUNBOOK-SPEED-3, not to v4.2: "From 2 hours before the start until the clean-up is done, no speed run, mutation run, full test run or other heavy job on the take laptop." |
| P01 | deletes the ROUND 33 PENDING definition at line 5 | READY | WAITING-ON-CODE | 24 | r36 | Deletion of the ROUND 33 PENDING definition; unchanged, applied against final r36. |
| P02 | deletes a ROUND 33 PENDING fragment in change-log row V5 (line 13) | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P03 | deletes a ROUND 33 PENDING fragment in change-log row V7 (line 15) | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P04 | deletes the ROUND 33 PENDING mark in change-log row V18 (line 26) | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P14 | rewrites the exit-3 last line at line 159 (lock held by a process the script cannot see) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged; it carries no lslocks words (answer 23). |
| P15 | rewrites the first PENDING mark at line 159 (which stream carries the exit-3 reason) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P18 | deletes the second PENDING mark at line 159 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P19 | rewrites the exit-130 line (line 160) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P20 | rewrites the second Ctrl-C mark (line 160) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P21 | rewrites the stop codes (line 161) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P22 | rewrites the n8n start line at line 126 (no n8n.out re-check) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P25 | rewrites the probe-folder sentence (line 366) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P26 | rewrites the filesystem refusal (line 376) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P27 | replaces the n8n.pid and n8n.out refusals (line 376) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P28 | keeps two n8n subfolder refusals, deletes the mark, adds one (line 376) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P29 | adds two refusals for folders above the take folder (line 376) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P30 | adds the new order of checks (line 376) | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P31 | checks the Select-String pattern at line 554 against the final refusal words | READY | WAITING-ON-CODE | 24 | r36 | Select-String pattern unchanged; check it against the final refusal words (lslocks is gone). |
| P33 | appends the exit-code clause to the take program paragraph (line 450) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P37 | rewrites the sentence on what the take prints (line 487) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P41 | adds the 120 s closing sentence for Ctrl-C (line 493) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged; H-1a adds one clause. |
| P42 | rewrites item 2 on a hung clean-up (line 494) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P44 | rewrites item 4 on an uncaught failure (line 496) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P46 | rewrites item 6 on how `result.json` is written (line 498) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged (OD-06 stays open). |
| P47 | adds two exit-3 reasons for posts still in flight (line 499) | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |

## Counts per status (new STATUS, counted by script from the table above: 69 rows)

| STATUS | Rows |
|---|---|
| READY | 10 |
| WAITING-ON-CODE | 42 |
| LEAD-DECISION | 7 |
| HELD | 0 |
| ALREADY-IN-V4.2 | 7 |
| NO-PLACE | 3 |
| total | 69 |

READY rows (10, listed from the table by the same script): H-1, H-2, PH-04, PH-06, PH-07, PH-08, PH-09, PH-13, PH-14, PH-17. No overlay row stays HELD.

## What I did not check, and open points

- Not changed by any answer, so not in the table: OD-01, OD-03, OD-05, OD-06, OD-07, OD-11, OD-12, OD-13, OD-14, OD-16, OD-18 to OD-25, H-5, H-7. Answers 1, 1b, 2, 4.1, 4.3 to 4.7, 5, 10, 11, 13, 25, 26 have no row in this patch (answer 4.3 and 26 leave OD-16 and the two DECISION-one-store copies open).
- Film pause versus stop time (answer 15d): the 49 minutes has no film-pause term, and answer 8 allows a pause of up to 10 minutes. I did not check whether anything spends money during or after the pause; a start at 17:40Z plus 49 minutes plus a 10-minute pause ends after 18:29Z. The lead should confirm what, if anything, still runs then.
- Answer 8 (whether the program enforces the pause limit or types `end` itself) is not answered; H-3 therefore says only "limited to 10 minutes, with an alarm".
- PH-01 to PH-03, H-3: see the LEAD-DECISION note above; the lead confirms whether the pause is inside the 49 minutes.
- Answer 9 is read as "no second run on the same day after a failed run". Whether it also removes the Wednesday retake after a bad recording is not stated (PH-16).
- Answer 17 gives "next morning" with no definition of a late take: H-6 is now LEAD-DECISION and nothing is applied.
- I read no code, ran nothing, and did not open v4.2 beyond the one search above. I did not check whether round r36, r34 or r35 final text exists yet. The pairing r36 to r37, r34 to r38, r35 to r39 is unconfirmed (see the glossary).
- EGM skipped: static re-marking of an existing patch list against written answers; the lead session runs the egm:* review before anything is applied. No sub-agents, no spend, no processes left running.
