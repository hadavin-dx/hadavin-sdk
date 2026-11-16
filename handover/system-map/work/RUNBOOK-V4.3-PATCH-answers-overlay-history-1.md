Status: DRAFT, unverified

# Runbook v4.3 patch: overlay of the lead's answers 1-26 (written 2026-11-16, UTC)

Purpose: re-mark rows of `work/RUNBOOK-V4.3-PATCH.md` (P01-P62, OD-01..OD-25) and `work/RUNBOOK-V4.3-PATCH-timing-v42.md` (PH-01..PH-17, H-1..H-7) against `work/LEAD-ANSWERS.md`. This file replaces nothing. Rows not listed here keep their old status and text. Nothing was run, no code was read, no v4.2 or patch file was edited.

## How to read this overlay

- Status words are the existing six: READY, WAITING-ON-CODE, LEAD-DECISION, HELD, ALREADY-IN-V4.2, NO-PLACE. The timing file has no status words on its PH rows; their old status is shown as "none" plus its own mark ("DO NOT APPLY until H-1" or "safe"). A closed question that carries no text (H-1, OD rows) is marked READY (answered) or ALREADY-IN-V4.2 (v4.2 stands); the note says which.
- Answer 24 (the lead): apply the wording and remove the "ROUND NN PENDING" labels at v4.3, but only against the FINAL wording of rounds r36, r34 and r35. Answer 24 says the branches r37, r38 and r39 (being reviewed now) carry them. I read that as r36 to r37, r34 to r38, r35 to r39 (order of the sentence; not verified). Every row whose text comes from those rounds therefore stays or becomes WAITING-ON-CODE, with the round named in column 5. Answers 21, 23 and 20 name rounds 35, 37 and 39 directly; those names are copied.
- Answers used by number: 3 delete design; 4.2 take port; 6 what the 49 minutes cover; 7 latest start; 8 film pause 10 minutes; 9 no same-day rerun; 12 no heavy job on the take laptop; 14 the 49 is computed; 15 parts a to g; 16 which cut-off governs; 17 clean-up next morning; 18 limit 180 s; 19, 20 money refusals; 21 exit 2; 22 exit-3 header; 23 drop lslocks; 24 apply only against final wording.
- Meaning of 49 (answers 6, 14): the take program computes it as 2630 s plus 6 times the lease seconds, rounded up (49 minutes at lease 45); it is not stored in stage.env and it is not a measured run time. It covers only the program's own run (posts, table and mail waits, final reads, margin). Typing `y`, the confirmation line and `end`, and owner steps A to D, are outside it (answer 15a).
- "v4.2 has no 18:15, 18:14:40 or 14-minute figure": I searched v4.2 for 18:15, 18:14, 14 min, about 14, 17:40 and 49 min: no hit. Answer 7's "change 18:15 and 18:14:40 everywhere" therefore changes other files (v5, TAKE-BLOCKERS, owner-timeline), not this patch.

## Overlay table

| row id | old STATUS | new STATUS | answer | final-wording round | new text if the answer changes it |
|---|---|---|---|---|---|
| P08 | HELD | ALREADY-IN-V4.2 | 3 | none | No edit. The replacement of section 10 step 5 (lines 510-514) by a per-contact design is cancelled. v4.2 stays: the owner deletes leftover contacts by a filtered list (lines 100, 105, 593 already say so). |
| P36 | HELD | WAITING-ON-CODE | 3 | r34 | Insert after the owner-types bullet (line 486): "`end` only closes the pause. The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list." Heading: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)". The old "unverified" hold is closed by the lead's answer; wording is checked once against the final r34 closing text. |
| P43 | READY | WAITING-ON-CODE | 3 | r34 | Keep the row as written. Read its clean-up line ("delete them in the HubSpot screen") together with the answer: the owner deletes leftovers by a filtered list. The program's own line is taken from final r34. |
| P48 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste "up to 3 contacts". v4.2 keeps its count (maximum 11 or 12, line 252) and "the contacts of the take stay until the one owner clean-up". |
| P49 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the "STOP ... wait for the studio lead's list ... 15 minutes" text. v4.2 line 510 trigger stays. |
| P50 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the per-contact list (lead id plus contact id, at most 3). v4.2 line 512 stays (account name and filter text). |
| P51 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the release words "contacts may be deleted" or the open-each-contact step. v4.2 "clean-up starts" stays. |
| P52 | HELD | ALREADY-IN-V4.2 | 3 | none | Do not paste the delete-one-contact-at-a-time steps. v4.2 stays: bulk delete of the filtered list; the lead re-runs the search (expect 0) before the owner revokes keys (lines 514, 596). |
| OD-17 | HELD | ALREADY-IN-V4.2 | 3 | none | Closed: the filtered-list design wins; v4.2 stands; the program's `end` deletes nothing (confirmed by the lead). |
| P34 | WAITING-ON-CODE | WAITING-ON-CODE | 21 | r35 (r39 widens the except) | Write exit 2 for refusal C: "refused: a money figure above the allowed maximum cannot be shown: check the typed figures". Applied only against final r35 and r39 wording. |
| OD-09 | WAITING-ON-CODE | WAITING-ON-CODE | 21 | r35, r39 | Question closed (exit 2, fixed in code). The row waits only for the final wording. |
| P16 | LEAD-DECISION | WAITING-ON-CODE | 22 | r36 | Header at line 159 becomes: "Exit 3 (the lock is still held by a process this script cannot see)". |
| OD-02 | LEAD-DECISION | WAITING-ON-CODE | 22 | r36 | Closed by the header text in P16. |
| OD-04 (33-36 rows 21, 22: lines 376, 380) | HELD | WAITING-ON-CODE | 23 | r37 | Drop lslocks. The candidate string loses the words "lslocks shows it". Lines 376 and 380 keep the v4.2 strings until the final r37 text says what remains of "(a shared lock or a process of another user also counts)"; no new string is written here. |
| P23 | LEAD-DECISION | WAITING-ON-CODE | 19, 20 | r35 (cap constant removed), r39 (cap-above-credit refusal restored) | Keep both refusals A and B (answer 20). Delete the sentence about an owner exemption for a cap literal: refused and moot, because r35 removes SELF_TEST_CAP_TOTAL_USD; stand-in numbers live in demo_only/dry_fakes.env.example. Refusal A is the spent-figure-independent line "cap above credit total refuses". Texts of A and B are taken from final r39. |
| OD-08 | LEAD-DECISION | LEAD-DECISION | 19, 20 | r35, r39 | Partly closed: exemption X1 refused (19); drop-A refused, both stay (20). Still open: does form (b) (`run_real_check_n8n.py --take`) reach A and B; should A and B say which figure is wrong (13p Y4). No answer covers those two. |
| P45 | WAITING-ON-CODE | WAITING-ON-CODE | 6, 7, 14, 15 | r34 | Delete "[49 = PROPOSAL ...]". Write: the 49 minutes is computed by the program (2630 s plus 6 times the lease seconds, rounded up; 49 at lease 45; no stage.env value) and covers the program's own run only. Never write "about 14 minutes" or "about 15 minutes". Refusal text and the order of checks come from final r34. |
| OD-10 | WAITING-ON-CODE | WAITING-ON-CODE | 7, 14 | r34 | Optional sentence adopted: "the program refuses a start that leaves less than 49 minutes before the stop time; latest start 17:40 UTC = 23:10 IST at lease 45". The 13s X-2 doubt (formula not strictly worst case) is a code check, still open. |
| H-1 | none (blocking question) | READY | 6, 14, 15 | none | Answered. Inside the 49: (b) scene 4 stop and restart (inside person C's post wait), (c) both mailbox waits, (e) the 120 s wait after Ctrl-C (margin), (f) final reads (margin only, not measured), (g) clean-up (margin only). Outside: (a) typing `y`, the confirmation line and `end` (before the window check), (d) the film pause (no pause term in the formula; answer 8 limits it to 10 minutes with an alarm). Releases the PH rows below. |
| H-1a | HELD | WAITING-ON-CODE | 15e | r34 | Add to line 493 (with P41): "(the 120 s wait is inside the margin of the 49-minute worst case)". |
| H-1b | HELD | WAITING-ON-CODE | 7, 14 | r34 | Line 450, "window too close": add "the program refuses a start that leaves less than 49 minutes before the stop time (computed from the lease)". The 14-minute figure is obsolete. |
| H-2 | HELD | READY | 16 | none | Lines 107, 222, 265, 482, 526: "A slipped take should start by Mon 23 Nov 12:00Z (17:30 IST); this is the planning target, so a failed run still has the afternoon. The HARD latest start is 17:40Z (23:10 IST) at lease 45." 12:00Z means the start, not the end. The conflict noted in PH-08 disappears (its example start 11:55Z is before noon). |
| PH-01 | none (DO NOT APPLY until H-1) | READY | 6, 7, 14 | none | Line 107: "Money stop Mon 23 Nov 18:29Z (23:59 IST). The program refuses a start that leaves less than 49 minutes before the stop time; latest start 17:40Z (23:10 IST) at lease 45." Delete "the lead's order ... not a measurement". |
| PH-02 | none (DO NOT APPLY until H-1) | READY | 7, 14 | none | Line 223, new row above the money stop: "Latest start of any run that spends (49 minutes before the stop, at lease 45) / Mon 23 Nov 17:40 / 23:10 / lead answer 7 of 16 Nov". |
| PH-03 | none (DO NOT APPLY until H-1) | READY | 7, 14 | none | Line 236: "No run that spends starts after 17:40Z (23:10 IST) at lease 45; the program refuses a start with less than 49 minutes left." |
| PH-04 | none (DO NOT APPLY until H-1) | READY | 14 | none | Line 76: "The 49-minute figure is computed by the take program from the lease (2630 s plus 6 times the lease seconds, rounded up); the 17:40Z latest start follows from it at lease 45. Neither is a measured run time." |
| PH-05 | none (DO NOT APPLY until H-1) | NO-PLACE | 6 | none | Dropped: H-1 is answered, so nothing is added to the NOT DONE list at line 109. |
| PH-06 | none (DO NOT APPLY until H-1) | READY | 7 | none | Line 88: as proposed; the ask also states that the program can still start by 17:40Z (23:10 IST). |
| PH-07 | none (DO NOT APPLY until H-1) | READY | 7 | none | Line 211: as proposed (clock time and "start by 17:40Z, 23:10 IST"). |
| PH-08 | none (DO NOT APPLY until H-1) | READY | 6, 7, 16 | none | Line 266: as proposed; the take program must start by 17:40Z (23:10 IST); a planned start by 12:00Z (answer 16). Drop the "conflict stated outright" remark. |
| PH-09 | none (first change: DO NOT APPLY until H-1) | READY | 7, 16 | none | Line 524: "take later: the take program must start by Mon 23 Nov 17:40Z (23:10 IST), planning target 12:00Z". Second change (04:12Z, 03:17Z) unchanged. |
| PH-13 | none (safe) | READY | 15b, 18 | none | Line 473: LIMIT_S = 180 s stays and the rehearsal measures the stop, start and takeover together. The scene 4 stop and restart sit inside person C's post wait, which the 49 minutes already contain. The 248 s sum stays an unmeasured example. |
| PH-14 | none (DO NOT APPLY until H-1) | READY | 15c | none | Line 489: add "both waits (at least 340 s together) are inside the program's 49-minute worst case". |
| PH-15 | none (DO NOT APPLY until H-1) | WAITING-ON-CODE | 15a | r34 | Do not apply. The window check comes after the typed answers, so a slow answer cannot push the take past the stop time once r34 is final. P45 replaces this row. |
| H-4 | HELD | WAITING-ON-CODE | 15a | r34 | Closed as moot for the same reason as PH-15; no earlier latest start and no 10-minute margin is written. |
| PH-17 | none (DO NOT APPLY until H-1) | READY | 6, 14 | none | Line 583: "the 49-minute figure is computed by the program from the lease and is not measured; the rehearsal measures the real run". |
| H-3 | HELD | READY | 6, 8 | none | Lines 218, 484: "about 1 h slot (the program's own run is at most 49 minutes at lease 45; the film pause is outside it and limited to 10 minutes, with an alarm)". Whether the program enforces the 10 minutes is core-hardening's answer, not written here. |
| PH-16 | none (safe) | LEAD-DECISION | 9 | none | Answer 9: no same-day rerun; a failed run means a new day inside the credit window, decided by the owner. PH-16 and the retake sums in lines 226, 251, 252, 508 and 528 assume a same-day retake. The answer does not say whether v4.2's Wednesday retake after a bad recording also falls. The lead decides; nothing is applied. |
| H-3b | HELD | NO-PLACE | 9 | none | No sentence about the latest first start of a retake is added: no same-day rerun on Mon 23 Nov. |
| H-6 | HELD | READY | 17 | none | Lines 510, 514, 595 (O6), 596 (O7): the Wed 18 Nov take keeps "same day"; after a late take on Mon 23 Nov the owner clean-up and the key revocation are done the next morning (Tue 24 Nov), time set by the lead. The answer does not define "late" and does not say in words that the model key stays valid until then; both are my reading. |
| P12 | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | No port number is written in any document, including 5690. Text: "The take port is read from the take config; core-hardening confirms the variable name." |
| P13 | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | Same as P12: the plan names the variable once; every other mention points to it. |
| OD-15 | LEAD-DECISION | WAITING-ON-CODE | 4.2 | none | Partly closed: no fixed number anywhere. Not answered: the second port (5691, n8n runner broker, part1 C3). |
| N12 (new; no patch row exists) | none | NO-PLACE | 12 | none | The line goes to v5 and RUNBOOK-SPEED-3, not to v4.2: "From 2 hours before the start until the clean-up is done, no speed run, mutation run, full test run or other heavy job on the take laptop." |
| P01 | READY | WAITING-ON-CODE | 24 | r36 | Deletion of the ROUND 33 PENDING definition; unchanged, applied against final r36. |
| P02 | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P03 | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P04 | READY | WAITING-ON-CODE | 24 | r36 | Unchanged deletion; applied against final r36. |
| P14 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged; it carries no lslocks words (answer 23). |
| P15 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P18 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P19 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P20 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P21 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P22 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P25 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P26 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P27 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P28 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P29 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P30 | READY | WAITING-ON-CODE | 24 | r36 | Text unchanged. |
| P31 | READY | WAITING-ON-CODE | 24 | r36 | Select-String pattern unchanged; check it against the final refusal words (lslocks is gone). |
| P33 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P37 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P41 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged; H-1a adds one clause. |
| P42 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P44 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |
| P46 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged (OD-06 stays open). |
| P47 | READY | WAITING-ON-CODE | 24 | r34 | Text unchanged. |

## Counts per status (new STATUS, rows of the table above: 69)

| STATUS | Rows |
|---|---|
| READY | 15 |
| WAITING-ON-CODE | 42 |
| LEAD-DECISION | 2 |
| HELD | 0 |
| ALREADY-IN-V4.2 | 7 |
| NO-PLACE | 3 |
| total | 69 |

READY rows are H-1, H-2, H-3, H-6 and PH-01, 02, 03, 04, 06, 07, 08, 09, 13, 14, 17. No overlay row stays HELD.

## What I did not check, and open points

- Not changed by any answer, so not in the table: OD-01, OD-03, OD-05, OD-06, OD-07, OD-11, OD-12, OD-13, OD-14, OD-16, OD-18 to OD-25, H-5, H-7. Answers 1, 1b, 2, 4.1, 4.3 to 4.7, 5, 10, 11, 13, 25, 26 have no row in this patch (answer 4.3 and 26 leave OD-16 and the two DECISION-one-store copies open).
- Film pause versus stop time (answer 15d): the 49 minutes has no film-pause term, and answer 8 allows a pause of up to 10 minutes. I did not check whether anything spends money during or after the pause; a start at 17:40Z plus 49 minutes plus a 10-minute pause ends after 18:29Z. The lead should confirm what, if anything, still runs then.
- Answer 8 (whether the program enforces the pause limit or types `end` itself) is not answered; H-3 therefore says only "limited to 10 minutes, with an alarm".
- Answer 9 is read as "no second run on the same day after a failed run". Whether it also removes the Wednesday retake after a bad recording is not stated (PH-16).
- Answer 17 gives "next morning" with no definition of a late take (H-6).
- I read no code, ran nothing, and did not open v4.2 beyond the one search above. I did not check whether round r36, r34 or r35 final text exists yet. Round naming for branches r37, r38, r39 follows answer 24 as I read it.
- EGM skipped: static re-marking of an existing patch list against written answers; the lead session runs the egm:* review before anything is applied. No sub-agents, no spend, no processes left running.
