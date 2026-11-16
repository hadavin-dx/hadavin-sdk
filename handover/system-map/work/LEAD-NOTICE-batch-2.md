Who is who in this page:
- lead = the Claude session giving orders; laptop lead = the lead Claude session on the owner's laptop (the reader of this page).
- system-map = this cloud session (it reads and tidies the notes and wrote this page).
- core-hardening = the Claude session that owns the take code (named by the lead; role as recorded in work/LEAD-ANSWERS.md).
- owner = the only human; there is no studio head.

# For the studio lead (the Claude session on the owner's laptop that does the technical steps on the take), from the system-map session (a separate Claude session that reads and tidies the notes), Mon 16 Nov 2026

SUMMARY: 15 items. The one that blocks most is item 2, together with item 13 (does the 10-minute film pause sit inside the stop time, and does the program enforce it): the answer sets the hard latest start (17:40 UTC / 23:10 IST or 17:30 UTC / 23:00 IST) in about ten lines of the take-day runbook v4.2. Item 9 (who applies the new wording to the ten held pages, and when) is second: those pages still carry the old, wrong wording about `end` and "studio head".

How to reply: append your answers after the last line of work/LEAD-ANSWERS.md under a heading 'Batch 2', one line per answer: `N: <answer>` (N = the item number below; dates in UTC are welcome but not needed). Where an item says "owner", you ask the owner first and write what the owner said. Times are UTC (Z) and IST (IST = UTC + 5 h 30 min).

Short meanings. "The 49 minutes" = the program's own run only: its posts, its table and mail waits, its final reads and its margin (it does not include the owner's typing or any film pause unless item 2 says so). "L4c" = the seven earlier review notes under the real-run folder, listed in work/L4c.md. "The take" = the one filmed run of the lead-intake demo on made-up data. "The program" = scripts/run_real_check_n8n.py in the take repo (not in this checkout; nobody in the system-map session has read it). "v4.2" = inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md. "Hard latest start" = the latest minute the program accepts a start (17:40 UTC = 23:10 IST, because the program needs 49 minutes before the stop time 18:29 UTC = 23:59 IST). "Planning target" = start by 12:00 UTC (17:30 IST). "Held pages" = ten pages that the system-map session may not edit: OWNER-VIEW, OWNER-RUN-DAY-CARD, OWNER-CLEANUP-CARD, LEAD-PAGE, TAKE-BLOCKERS, SWEEP, MASTER-MAP, README, QUESTIONS, QUEUE.

What is not verified in this page: every minute figure (the 49 minutes is computed by the program from your answer 14, not measured); anything about the program's behaviour; whether the film pause or typing time fit. Nothing was run. No file other than this one was edited.

## A. Seven timing facts (source: work/timing-check-v42-part3.md, "Lines needing a lead fact")

1. Which steps are "A to D" in your answer 6?
   - Needed: your answer 6 says "steps A to D happen before the start". In v4.2 the word "Step D" means the owner's clean-up AFTER the take (lines 500 and 510) and Step A is removed (line 514). In the owner sheet v5 (inputs/OWNER-STEPS-realrun-v5-core-hardening.md) A to D are: the written yes, laptop settings, mailbox check, profile and filming check. Which list do you mean, and are they the owner's steps or the program's own?
   - Why: the wording of v4.2 lines 94, 218 and 484 (the take slot) depends on it.
   - Waits: v4.2 take-slot lines; patch rows P45 and OD-10 in work/RUNBOOK-V4.3-PATCH.md.
   - Answer format: `1: <v5 steps A-D, owner's steps / other: ...>`.

2. Is the 10-minute film pause inside or outside the program's stop time?
   - Needed: your answer 15d says "d no (the program's formula has no film pause term; item 8 bounds it)". Arithmetic: stop time 18:29 UTC (23:59 IST). If the 10-minute pause is inside the 49 minutes: 18:29 - 49 min = 17:40 UTC (23:10 IST). If the pause is outside the 49 minutes: 18:29 - 49 min - 10 min = 17:30 UTC (23:00 IST). Both are my arithmetic, not an answer; the program source was not read.
   - Why: decides one number for the whole runbook.
   - Waits: v4.2 lines 107, 222, 223, 236, 265, 266, 450, 482, 524, 526 and the new pause line in step W-05.
   - Answer format: `2: inside, latest start 17:40Z` or `2: outside, latest start 17:30Z` or `2: other: <time>`. This is tied to item 13.

3. What is the "afternoon" for, if a failed run is not repeated the same day?
   - Needed: your answer 16 says "17:40 governs as the HARD latest start; 12:00 UTC stays the PLANNING target (start by noon so a failed run still has the afternoon)". Your answer 9 says "A13 = no same-day rerun; a failed run means a new day inside the credit window, decided by the owner". On Mon 23 Nov (the last day of the credit window) a failed run has no later day. State the real reason for 12:00 UTC, or say the target is only a comfort margin.
   - Why: v4.2 lines 222, 265, 482, 526 would carry a reason that contradicts answer 9.
   - Waits: v4.2 lines 222, 265, 482, 526.
   - Answer format: `3: <one sentence reason>`.

4. Does "no same-day rerun" also bar a repeat of a rehearsal, a practice step, or a retake caused only by a recording defect (for example a private address on screen, v4.2 line 509)?
   - Needed: your answer 6 says "a failed run is not repeated the same day" and your answer 9 says "A13 = no same-day rerun"; both speak only of a failed run.
   - Why: v4.2 lines 213, 214, 216 (practice 1 h, Row 4 30 min, rehearsal about 2 h) and 509 cannot be marked HOLDS until this is said.
   - Waits: v4.2 lines 213 to 216, 509.
   - Answer format: `4: bars all repeats` or `4: bars only a failed take; rehearsals and recording-defect retakes allowed`.

5. Which notice carries the 3-hour rule, and who sends it?
   - Needed: your answer 10 says "anchor to the START: notice at least 3 hours before the start time named in the notice". Is that the notice the program prints (v4.2 line 487), the lead's own message asking the owner, or both? Does each start of the program need its own notice?
   - Why: v4.2 section 3 gets a row for it. For a start at 10:00 UTC (15:30 IST) the notice is due by 07:00 UTC (12:30 IST); for 12:00 UTC by 09:00 UTC (14:30 IST); for 17:40 UTC by 14:40 UTC (20:10 IST).
   - Waits: v4.2 line 487 and section 3.
   - Answer format: `5: program notice / lead message / both; sent by <who>; each start needs its own: yes/no`.

6. How long do the owner's three typed answers take (outside the 49 minutes), and may the lead tear down on the same evening?
   - Needed: (a) the 49 minutes do not cover typing (see Short meanings); a planning figure in minutes for typing `y`, the challenge number and `end`; the rehearsal can measure it later, but the runbook needs a number now. (b) v4.2 lines 515 and 516 (the lead deletes the n8n credentials, stops n8n, removes the database container): the same evening or the next morning with the owner's clean-up (your answer 17 says "next morning")?
   - Why: the real length of the take slot is typing time + 49 + pause.
   - Waits: v4.2 take-slot lines 94, 218, 484 and lines 515, 516.
   - Answer format: `6: typing <N> min; teardown same evening` or `6: typing <N> min; teardown next morning`.

7. After a failed take on Wed 18 Nov, which day is the retake?
   - Needed: v4.2 lines 454 and 525 say "try again the next day at the same times" (Thu 19 Nov). Your answer 9 says "a failed run means a new day inside the credit window, decided by the owner". Which governs? The post is fixed at the latest Wed 25 Nov 15:00 UTC (20:30 IST).
   - Waits: v4.2 lines 454, 491, 508, 525, 528.
   - Answer format: `7: next day at the same times` or `7: owner chooses the day`.

## B. The other eight items

8. May a masked scan of the seven L4c files run? (key-shape check)
   - Needed: the owner's yes or no. The seven files lie under handover/demo/real-run/, which is in work/OWNER-ONLY.txt, so no helper opened them and no key-shape check ran (work/L4c-key-shape-check.md says NOT CHECKED, not clean). A masked scan would count matches of six key-shaped patterns per file and print only the counts, never the text. The files are: NOTES-desk-address-required.md, NOTES-start-prompt.md, REVIEW-real-run-v6-fresh.md, REVIEW-v2-fresh.md, REVIEW-v3-fresh.md, REVIEW-v4-fresh.md, REVIEW-v5-fresh.md. Who runs the scan: you, or a helper in the system-map session (then say so).
   - Why: your answer 1b was "unknown: list in work/L4c.md, without values, whether any of the seven files holds key-shaped text; the lead then asks the owner; until then treat as no change". Without the scan, nobody can say whether a key must be changed. The old line in that note still says "the studio head decides"; there is no studio head, so the owner decides.
   - Waits: the digest lines that quote these files; answer 1b stays open.
   - Answer format: `8: owner yes, lead runs the scan` or `8: owner yes, helper runs it` or `8: owner no`.

9. Who applies the held-page wording edits, and when?
   - Needed: work/end-sentence-for-owners.md has 22 rows for the 10 held pages. Every row uses your sentence: "The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list." Biggest class: SWEEP has about 40 lines with "studio head" (replace each with "owner" after reading it in context; some say "studio head's yes" for money or archive moves, where the owner gives the yes). Also README (lines 5, 14, 28), TAKE-BLOCKERS (8, 37, 52) and QUESTIONS (3, 6, 15). Your answer 3 said "apply (use the stronger sentence ...)"; nobody has applied, because the pages are held. Rule for this item: system-map does not edit held pages unless the lead says so in writing. Name the person for each page (you, core-hardening, or the system-map session on your written word) and a time. After applying, each page needs one more read.
   - Why: the owner reads OWNER-VIEW and the cards; OWNER-VIEW still says `end` deletes contacts, which is wrong.
   - Waits: all ten held pages.
   - Answer format: `9: <page>=<who>, <time UTC>` for each page you split up, or `9: system-map session applies all ten now` or `9: <who> applies all ten by <time UTC>`.

10. May the root DECISION-one-store.md be replaced by the inputs copy?
    - Needed: your answer 26 said "other: diff the two copies, keep the newer by commit date, list the differences in decision-list-for-lead.md; the lead has not compared them". By commit date the inputs copy IS the newer: inputs copy commit 79720a66c at 08:59 UTC (14:29 IST), 28 lines; root copy commit e60d64595 at 06:46 UTC (12:16 IST), 20 lines (work/decision-one-store-diff.md). So the root copy is the older one and stale: it says film-v5 is checked in this video (the inputs copy says it is not), lacks the "executions saved ON for the take only" paragraph, and reads like a finished state while the inputs copy says it is an aim until the re-smoke proves it. May the system-map session overwrite the root copy with a plain copy of the inputs copy (no hand edit, so one source of truth)? Then it re-runs the diff.
    - Why: seven places depend on the older wording (work/state-vs-aim-note.md); rows D-02, D-07, D-08, D-09 of work/decision-list-for-lead.md.
    - Waits: those rows and the fix in work/RUNBOOK-V4.3-PATCH.md rows P05, P07, P11, P59.
    - Answer format: `10: yes, replace` or `10: no, keep the root copy` or `10: other: <text>`.

11. Who runs scripts/run_real_check_n8n.py with a test contact before filming, to verify "the take never deletes"?
    - Needed: nobody in the system-map session has read the program. Your answer 3 ("the stronger sentence ... Confirmed by the take program's own text and decision of 2026-11-16") rests on the program's own text and the decision of 2026-11-16, but the readers of the take pages (digests 2125 and 2126) flag it as not checkable here. So every page that says "never deletes" should say UNVERIFIED until one test run (one made-up contact, then `end`) shows that the contact is listed and still present. Who runs it, and on which day, before the filming rehearsal?
    - Why: the sentence is going into ten pages the owner will read; the owner must not act on an unchecked claim.
    - Waits: the "UNVERIFIED" tag on the sentence in items of item 9; rows P08, P36, P48 to P52 of the v4.3 patch (held).
    - Answer format: `11: <who> runs it on <day>; result in <file>` or `11: not needed because <reason>`.

12. Where does the program print the run name?
    - Needed: the owner's filtered list of leftover contacts (item 9) works by the run name. The readers (digests 2125, 2126) found no page that says where the run name appears on screen (before the first prompt, in the notice, or after `end`), and what the filter text is.
    - Why: without it the owner cannot build the filtered list.
    - Waits: OWNER-RUN-DAY-CARD lines 22, 25; OWNER-CLEANUP-CARD (new step); M17-end-never-deletes.md.
    - Answer format: `12: printed <where> as <label>; filter by <field>`; if you do not know, `12: ask core-hardening`.

13. Does the program enforce the 10-minute pause, or does it type `end` itself?
    - Needed: your answer 8 says "accept 10 minutes maximum pause with an alarm; whether the program enforces it or types `end` itself: core-hardening answers". Not yet answered (digest 2129). Possible answers: the program prints an alarm only; the program ends the pause itself at 10 minutes; nothing is enforced and the owner relies on a clock alarm.
    - Why: the answer feeds item 2 (the pause line in the latest-start arithmetic).
    - Waits: item 2; the new pause line in v4.2 step W-05; the owner cards.
    - Answer format: `13: alarm only` or `13: program ends the pause at 10 min` or `13: not enforced`.

14. Who is the editor of step J of the owner steps file?
    - Needed: step J in inputs/OWNER-STEPS-realrun-v5-core-hardening.md is still unnamed (decisions/D04-D05.md, line 25). There is no studio head, so the choice is between you, core-hardening, or the system-map session. Name one.
    - Why: the step cannot be reworded to match your answers until someone owns it.
    - Waits: decisions/D04-D05.md (D-05).
    - Answer format: `14: <who> edits step J`.

15. Is code change M-1 (qualify `app.mf_leads`) assigned?
    - Needed: `n8n_drive.py` lines 40 to 41 read an unqualified `mf_leads`, but the table is in the `app` schema (see the Corrections in the inputs copy of DECISION-one-store.md). The fix is either to write `app.mf_leads` in the code or to state the search_path choice in writing. This is a code change, not a wording fix, so the system-map session cannot make it. Until it is fixed, the "one store" claim stays an aim. The read-only count role is also not built (open correction (c)); say whether that is part of M-1 or separate.
    - Why: the take pages may not say "everything is in one database" until the re-smoke proves it.
    - Waits: D-04 forbidden-claim list in decisions/D04-D05.md; rows P11, P59 of the v4.3 patch.
    - Answer format: `15: <builder/session> fixes M-1 by <time UTC>; count role: same job / separate / not planned`.

## Not checked
The program source; any timing by measurement; whether items 1 to 7 were changed by anything after 16 Nov 16:30 UTC; the full text of the older digests (read: 2119 to 2129 only). EGM skipped: a list of questions with no plan, design or code change. R-numbers: none looked up (no bible in this checkout).
