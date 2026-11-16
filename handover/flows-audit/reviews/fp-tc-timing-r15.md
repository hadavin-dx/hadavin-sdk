# FIX-PLAN / TAKE-CHECKLIST / RUNBOOK round 15: timing and consistency review (agent a8f517f)
Saved by flows-audit, condensed. Reviewer words unverified. Nothing was run. 0 Blockers, 7 Majors.

Checked clean (by reviewer): Clock tables identical in FIX-PLAN, TAKE-CHECKLIST and RUNBOOK section 6; Tuesday 269 min total and start times (04:00, 04:16, 04:26, 04:51, 04:54, 05:54, 07:14, 07:44, 08:29); latest-start limits; Wednesday blocks (115 and 127 min, Case A 10:07-11:07 msg 11:27, Case B 11:02-12:02 msg 12:22); sampled IST conversions.

Majors
1. Re-smoke command has three answer-by times: QUESTIONS item 25 (line ~430) Tue 06:00Z; item 38(c) (~490) 08:00Z; TAKE-CHECKLIST line 99 says 08:00Z and line 58 "before 08:29Z". Pick one.
2. F-011/F-041 evidence standard: TAKE-CHECKLIST lines 58, 70, 80 (Inputs 11, 12, 22) say before 04:00Z; QUESTIONS item 10 parts b, c (~431) and L24 say 06:15Z; part (a) 03:00Z.
3. Post-twice script contradicts itself: TAKE-CHECKLIST 58 needs it before 08:29Z with two reviews before 14:00Z; RUNBOOK 255 says re-smoke does not use it, branch by Tue 09:00Z; RUNBOOK 253 writes it in W-Wed (latest end Wed 05:45Z); Tuesday GO row 2 needs its review closed before 14:00Z; Wednesday fix pass at 05:30Z starts before writing ends 05:45Z.
4. PIN_NAME set two ways: RUNBOOK ~112 fixed "REPLACE_ME_I36" with no ${PIN_NAME:-} default; TAKE-CHECKLIST ~91 says lead types it in the call; every block re-sources $ENVSH which overwrites a typed value; TAKE-CHECKLIST 58 and Q31 item 48 say it is filled in shas.env by 03:30Z.
5. REPLACE_ME_I## tags in the skeleton use RUNBOOK I-numbers, not Q31 item numbers (JUDGE_WHO I48 vs Q31 item 33; PGADMIN and WAIT_S both I13 vs Q31 items 41 and 50; PIN_NAME item 48). Replace with Q31 item numbers.
6. Q31 item numbers cited for wrong inputs: TAKE-CHECKLIST 58 "Q31 item 40" for BRANCH, PATCH_BRANCH, SHA_R20-R23 (shas are item 38(b)); TAKE_FOLDER in items 34 and 40; BRANCH in 38(b) and 40 (TAKE-CHECKLIST 99 says a number is never used for two inputs); TAKE-CHECKLIST 101 cites item 38 for "desk doors" but 38 is the remaining-inputs bundle; Q31 answer-by table and count line stop at item 31.
7. Run-once guards for sha appends: FIX-PLAN ~77 (SHA_FOLDER), TAKE-CHECKLIST ~361 (SHA_PIN1), FIX-PLAN ~94 (SHA_SCRIPTS) append to $ENVSH without grep -q guard (RUNBOOK ~194 has one); TAKE-CHECKLIST ~392 (SHA_PIN) prints sha-written-repeat on repeat of step 13 and does not record the new pin sha, so a later restore from $SHA_PIN restores the OLD pin and export check exits 4. Text says "written once, never edited". Decide overwrite or SHA_PIN2 and apply to all three.

Known open re-confirmed: step 1 start 04:00 vs 03:31 (Q31 item 32, Mon 22:00Z; all other answer-by times keyed to 04:00; Block R3 unmeasured, item 51); recording-ready "planned by 12:00Z" (FIX-PLAN 44, TAKE-CHECKLIST 38) vs Case B 12:22; take start and text-fix times (FIX-PLAN 71: 05:29 step 8, 04:16 step 4a vs Clock 07:44 steps 14, 15).

Not checked by reviewer: RUNBOOK 89-178 and 195-243 (grep only), sections 7-10; TAKE-CHECKLIST beyond 142; FIX-PLAN beyond 78; Q31 items 33-52 answer-by times; whether each BLOCKED input in RUNBOOK steps 5-30 has a Q31 item; run-once guards on send steps.
