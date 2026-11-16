Status: resolved (round 1 of max 2; the second round was not run)
# C4 resolve log, round 1 (egm-resolve, headless auto-accept), 2026-11-16
Target: steps-edits/EDITS.md. Findings: review-c4-r1.md (two independent egm reviewers). Contested: 0. Escalated: 0. Declined: 6 nits listed below. PROPOSE FIX applied: 24 findings in 21 row edits, 2 new rows (E-36, E-37), 1 block rewrite (NOT DECIDED), 1 new list section ("New lines for E-25").

## Applied (finding -> change)
- K-B1 -> E-01: old text now includes the branch name; new text adds one sentence after the worktree clause; "now on r3 to r5" replaced by "pinned at r3 (provisional), r4 and r5 in progress".
- D-M1 -> new row E-36 (OWNER-STEPS:131, "on its own credentials" -> "with a separate check of ours"); E-18 gets the independent-login item in the must-NOT-say list.
- D-M2 -> E-10 moved to the start of step 8 (before the credentials), old text changed to the "Credentials, Add credential..." sentence, no made-up e-mail asked.
- D-M3 + K-M -> E-27 (one Postgres server, two compartments, aim until rehearsal) and E-30 (planned, no procedure).
- D-M4 -> NOT DECIDED item 2 reworded as a non-blocking confirmation request.
- D-M5 + FACTS line 5 -> new row E-37 (Phase 0 status note); E-37 plus item 12 hand the full rewrite to the lead.
- K-M1 -> E-16 now names removal of the container, not removal of setting lines.
- K-M2 -> E-06 invented rule removed.
- K-M3 -> E-25 item 18: "repeated once only if the first try missed".
- K-M4 / D-m2 -> E-05: one gloss at first use (line 95) covering lines 103, 104 and AGENT-SCOPE 20; no claim about the delete right.
- K-M5 -> E-19 old text now includes the "Independent review rounds 3 to 9 are done." sentence; E-02 why names AGENT-SCOPE 16 and 22.
- m4 -> E-07, E-08 marked DEFERRED (no edit now) until the lead confirms P14. m5 -> E-13 DEFERRED, line 11 added to its note. m6 -> E-25 list moved out of the table. m7 -> E-09 "the lead tells you". m8 -> E-17, E-18 editor notes moved to the "why" column, E-18 is its own sentence. m9 -> E-30 no procedure. m10 -> codes removed from owner-facing new text (row DM, P14, HEAD_PIN-style names, EXECUTIONS_*, mf_leads, decision numbers) in E-09, E-14, E-15, E-16, E-17, E-18, E-19, E-22, E-25. m11 -> E-31 old text is now the clause with the closing parenthesis. m12 -> E-14 why says to rewrite step 19 item (4) together.
- NOT DECIDED list: 13 items -> 12 (fill-step, second pass and clean-up method removed as not lead-only); items renumbered, cross-references in the rows checked.

## Declined (nits recorded, not fixed)
E-20 "default SQLite" -> fixed (word removed), counted as applied; declined: E-29 "module downloads" (the row already says "not guaranteed", plan UNVERIFIED 1); E-35/E-23 "decision 6" not in plan v5 (it is a lead decision in QUEUE.md rule 6; cited there now, so no change to the text); E-14 "may show the company address" (hedged); DECISION-one-store CORRECTIONS at line 25 not 26 (corrected in item 10); AGENT-SCOPE 16/22 old round wording (dated history, left unchanged and said so in E-02); E-12 "no pass, no take" is a policy addition by the lead's decision 5, kept and labelled.

## Checks after the edits
- Each of the 5 new/changed old-text strings (E-01 branch clause, E-10, E-19, E-31, E-36, E-37) was grepped in the inputs: occurs exactly once (counts 1,1,1,1,1,1).
- Row count by script: 37 rows (CONTRADICTION 5, STALE 11, UNCLEAR WORD 7, MISSING STEP 11, DEFERRED 3). Banned-brand scan of EDITS.md: 0 hits.
- NOT run: a second fresh review of the corrected file (round cap for this non-security path is 2; round 2 only if a Major is expected); all the other old-text strings were not re-grepped after this round (only those whose old text changed: E-01, E-10, E-19, E-31, E-36, E-37).
