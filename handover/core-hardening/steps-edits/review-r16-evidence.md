# EDITS r16 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: steps-edits/evidence-r16-independent/ (00-TABLE.md first). Recorded, not judged.
## Failures and deviations first
1. 6 of 14 fresh mutations (batch B) caught by neither checker: B03 shred "no space" rule dropped; B04 appendix K-A "20 minutes between" instead of 10; B05 step 21 heading changed to a consistent 18:21 UTC = 23:51 IST; B08 sentence "The assistant never opens the key file" deleted; B09 D.3 "no reply counts as `more takes`" turned into `no more takes` (reverses the safe default); B10 key step K "revoke the key at that time anyway" turned into "wait for the take" (safety reversal).
2. verify16.py misses 15 of the first 60 mutations: absolute path, `ORD:` code and `DEC:` code in owner text, dropped `not sure` option in key step F, dropped "do not shred part (a) while a take is running", spending-window end moved to 18:19, card item 1 "revoke at 18:19" changed to 18:29 (list in 00-TABLE.md section 4).
3. The runner's own 60 of 60 on batch A is tuned (53 of 60 before tuning). Fair comparison is the 14 fresh mutations: verify16.py catches 8, the runner's checker 5.
4. The runner's checker flags one item in the builder's file: Appendix K intro names "row E-48" (an internal row code in owner-sheet text). Low.
5. Not checked: any click path, clipboard setting, a live take; the builder's 161 controls were not re-planted separately.
## Runs
build-r16.py: "written 1056 lines", output identical to live EDITS.md. verify16.py: FAILURES 0 (60 rows, 48 Apply now, 12 Hold, 161 controls caught, 61 old texts 0 overlaps; its counts 146 UTC/IST pairs, 69 weekday-date pairs, banned 0 of 10, secret-shaped 0); on round 15 text it prints 45 FAIL, exit 1.
## Independent checker
UTC = IST + 5:30 for all 146 pairs; 69 weekday-date pairs, 0 wrong; cross-references 0 failures; each OLD text once on its stated line; secret-shaped 0; banned 0 of 10; semantic checks pass (card order, exact-address delete clause in E-04/E-42/E-62, five shred checks order, four D.2 cases, alarms, margin 18:00:00 + 1:00 + 14:20 = 18:15:20 UTC = 23:45:20 IST, 3 min 40 s before 18:19).
## Mutations
Batch A 60: verify16 45, runner 53 (60 after tuning). Batch B 14 fresh: 8 and 5. Total 74: 53 and 65; neither 6.
## Word counts
E-48 new text 3,643 (builder 3,647); appendix K 928 (matches); OWNER-STEPS rows new text 16,609 (builder 16,464, 145 not explained); all rows 18,127; whole EDITS.md 52,990 (builder 52,771). Applied sheet length not recounted (builder: 18,632 vs cap 6,300, L-LEN open).
## Status
inputs/, src/, tests/ 0 changes; no processes left; copies left in a/b/steps-edits and two read-only symlinks.
