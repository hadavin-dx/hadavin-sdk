# Result review round 2 (of max 2). Saved by the session lead from the reviewers' hand-backs.
Status: codebase-details NOT YET REPORTED when this file was first written (section 4 is added when it reports).

## 1. Zoom-out (0 Blocker, 5 Major)
- Z-M1: SWEEP Fix plan rows 3 and 4 (second alert channel; three roles plus a fourth identity and new scopes) are banded "before the video", against DECISION lines 14 and 16 and the refusal at ORDERS.md:197. Mark as laptop lead choice; each breaks "config only on proven flows".
- Z-M2: use two columns: date (before or after Wed 18 Nov) and yes (needed or not). Merge Blocker rows 13-15 into rows 1-2. Postgres re-smoke before the video. Replace the lump rows of 65 Majors with real actions.
- Z-M3: honest dedup. L6-FD-001, 002, 005, 017 restate L2 Blockers; deduplicated is about 16 or fewer. Add column "Blockers that touch the take, deduplicated" and state the rule.
- Z-M4: 15-line headline at the top of SWEEP.md (one line per job: owner, copies, verdict). Correct row count 49 to 48 + 10 appendix. Fix unclear verdicts L6-J-037, L6-J-005. Check L6-J-040 evidence cut.
- Z-M5: COUNTER has no recommended owner: propose stage.journal for the take and core Limits for the later portal; name the cap owner before the video.

## 2. Design (4 Blocker, 6 Major)
- D-B1: Fix plan rows 1, 3, 4 are labelled config-only but add nodes, a channel, roles. Move after the video or split; attach a re-smoke with pass criterion.
- D-B2: rows 2, 10, 15 contradict (execution saving on before the video with no yes; n8n data move after the video). One sequence: engine move, planted-data check, saving on, masking/prune/retention written.
- D-B3: COUNTER has two jobs (proof count, money cap) and one Owner line; money cap has none. L6-J-035 claims "the cap in effect" while line 78 says it is not a dollar ceiling. Same for LOG (execution log and audit). OTHER owner none (identity and role job has no owner). Money-cap owner line must say "none, open".
- D-B4: "independent count" is an n8n Code node stand-in in the same n8n/Postgres: not independent. Add Claims-check row UNVERIFIED; say whether count runs outside n8n; name identity; add negative test.
- D-M1: DECISION says three roles, SWEEP says four. No negative tests for alert credential, heartbeat, stage.journal writer, count scopes; n8n and app role share one n8n.
- D-M2: lost/double message exposures accepted untested (L6-EX-07, L6-EX-05, mf-hook source column, review state gets no notice). State as defects with next step, not accepted.
- D-M3: Fix plan rows 13-15 action cells hold cut-off evidence text, not actions.
- D-M4: L6-EX-10 covers only tracked credential files; not n8n folders with keys (~220 MB), SQLite with planted data, rotation. Name what may be deleted, who says yes, removal trigger. EX-03/04/05/06/08 say "none" for trigger; EX-04 says "no lead data" while the claim is CONTRADICTED.
- D-M5: state column "OK" conflicts with seed check (L6-J-001 CONFLICT; L6-J-003, 014 unverified).
- D-M6: single-dependency audit for the take (n8n, SMTP, model) missing; SECURITY/OPS/workflow-walk checklist sections must be marked UNVERIFIED with reason.

## 3. Comprehension (3 Blocker, 8 Major)
- C-B1: Fix plan rows 13-18 action cells cut off mid-sentence; rows 13-15 repeat rows 1-2; rows 16-18 need yes but the action is not stated.
- C-B2: "owner" has two meanings (place vs person). Rename person column to "responsible person"; reserve "owner" for the place.
- C-B3: "lead" has four meanings (sales request, sales lead person, laptop lead, bare "lead decides"). Define laptop lead and studio head; "the order"; "Hadavin".
- C-M1: NOT-NEEDED definition does not match use (L6-J-005, 037 say DUPLICATE/MERGE-INTO).
- C-M2: OWNER row with state PLAN NOT DONE; CONFLICT/CONSISTENT/UNVERIFIED and Blocker/Major/Nit not defined in ONE-PLACE-TABLE where first used.
- C-M3: "Exception" defined one way and used another; EX-03/04/05/06/08 say "not an exception".
- C-M4: overloaded claim, state, key, sweep, job; lead states (review, unknown, failed) never listed.
- C-M5: job keys do not cover what is filed under them (COUNTER holds test totals, slot limits; FILTER holds gates and scans; LOG holds audit and evidence reports; OTHER "not a place" but has a place row).
- C-M6: undefined labels (flows, stand-in, canary, GREP, Fc, k1b, core Limits, DeadLetter, SpendLedger, film-v5, real-v5, schema app, heartbeat, this box; id kinds WK, T, D, EX).
- C-M7: take, proof, the video, Hadavin, client undefined.
- C-M8: severity cells contradict text (L1-FD-021 Blocker "lead decides"; "same:" unexplained; L2-FD-018 who decides force-push).

## 4. Codebase-details: pending
