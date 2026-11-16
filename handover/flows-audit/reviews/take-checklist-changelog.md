# TAKE-CHECKLIST changelog (round history moved out of the checklist)

Moved here by the take-checklist fixer (round 58 pass) so the checklist itself reads as instructions only. Nothing below is an instruction.

## Round-33 status text (removed from the head of TAKE-CHECKLIST.md)

 Round 33 (flows-audit, 2026-11-16): the python3 program of Blocks P1b and P2b (name, date and receipt) was run in a scratch folder on a made-up pin file: receipt `378e1121` written as `# reviewed by: Anna Smith, 2026-11-17, pin sha256 378e1121`; a receipt of 8 other hex characters printed `refused: the receipt is not the first 8 characters of the sha256 line of this pin`; `XYZ` printed `refused: the receipt is not 8 lower-case hex characters`; and `bash flow-check/take_check.sh --check-reviewer-line 'Anna Smith, 2026-11-16, pin sha256 378e1121' 2026-11-16 378e1121` printed `ok` while the same line without the receipt printed `REFUSED (rule: receipt missing)`. The block chains themselves (`need_set`, `$ENVSH`) were not run.

## Review-round tags and sentences removed (pass 1: tags)

```
30	(round 30, M7)	tag removed
30	(round 30, M6)	tag removed
30	(Round 13: 	prefix removed
30	(round 30, M4: 	prefix removed
83	(round 32, finding 6)	tag removed
83	(round 22, finding 1)	tag removed
87	(round 21, M7)	tag removed
101	(round 43)	tag removed
103	(round 34, finding 1)	tag removed
103	(round 32, finding 7: 	prefix removed
104	(round 41, B1)	tag removed
105	(round 21, M8)	tag removed
109	(round 23, M6: 	prefix removed
115	(round 41, M8)	tag removed
126	(round 33, B1)	tag removed
134	(round 13, B4)	tag removed
136	(round 13, M1)	tag removed
156	(rounds 23 and 24)	tag removed
159	(round 41, reader M4: 	prefix removed
161	(round 41, reader M6: 	prefix removed
173	(round 12, M3)	tag removed
173	(round 41, reader M5: 	prefix removed
182	(round 43: 	prefix removed
187	(round 28: 	prefix removed
194	(round 41, M12)	tag removed
200	(round 43: 	prefix removed
208	(round 21, M20)	tag removed
209	(round 21, M20)	tag removed
210	(round 21, M19 and M20)	tag removed
211	(round 21, M5 and M20)	tag removed
212	(round 21, M20)	tag removed
213	(round 21, M20)	tag removed
217	(round 33: 	prefix removed
219	(round 19, operator M2 and M3: 	prefix removed
225	(round 30, M4: 	prefix removed
226	(round 34, shell M4: 	prefix removed
226	(round 33, M1: 	prefix removed
226	(round 21, M1: 	prefix removed
226	(round 33, M1: 	prefix removed
226	(round 21, M3; round 41, reader M3: 	prefix removed
226	(round 43: 	prefix removed
229	(round 34, shell M3: 	prefix removed
229	(round 41, M4: 	prefix removed
234	(round 41, reader M1: 	prefix removed
235	(round 20, M5)	tag removed
257	(round 33, M1: 	prefix removed
386	(round 14)	tag removed
400	(round 33)	tag removed
400	(round 41, M5: 	prefix removed
400	(round 41, reader M9: 	prefix removed
429	(round 33, reader M3)	tag removed
429	(round 41, M10: 	prefix removed
429	(round 32, finding 9: 	prefix removed
429	(round 33, M1: 	prefix removed
430	(round 33, shell M1: 	prefix removed
432	(round 33, M9)	tag removed
434	(round 41, M2)	tag removed
443	(round 41, M11)	tag removed
446	(round 28: 	prefix removed
448	(round 21, M12)	tag removed
481	(round 19, operator M6: 	prefix removed
488	(round 33, B1: 	prefix removed
525	(round 28: 	prefix removed
525	(round 33, M5: 	prefix removed```

## Pass 2: more tags and history sentences

```
item 14 receipt history	round 33, B1: the old text here and the old blocks left the receipt out, so `take_check.sh` would exit 4 with `receipt missing`; 
item 14 ASCII history	Round 34, shell M5: the old text here said NAME must use ASCII letters only and that "José" is rejected; that was WRONG: the helper, run on made-up lines on 2026-11-16, printed `ok` for `José Smith, 2026-11-16` and for `Jose Smith, 2026-11-16` (any alphabet is accepted, only a mix of two alphabets inside one word is refused).
pin proc 488	Round 21, B1: the chains of RUNBOOK step 4b
item 34 history	Q31 item 88, round 21: this text said "no Q31 item yet" and item 78, but item 88 exists in QUESTIONS.md; item 78 is DB_SETUP only; the input named
item 34 time history	; round 23, M5: 05:50Z (11:20 IST) was the time before step 8 moved after step 6)
row 215 history	; round 33: this row used to say LEAD FILLS for the path, which contradicted the next row)
28	; round 30, M6
30	(round 20, M8; 
30	; round 26, finding 7
30	 round 30, M4: 
83	(round 23, M4; 
83	(round 19; 
83	; round 21, M7
83	; round 21, M8
83	; round 30, M5
83	; round 34, finding 5
83	 round 30, M5: 
83	 round 34, finding 3: 
83	 round 34, finding 4: 
87	, round 20, M7: 
97	(round 22, finding 7; 
114	; round 41, M12
119	(round 13; 
136	round 28: 
141	, round 30, M8
143	 round 41, reader M2: 
162	(round 43; 
166	(round 41, M12; 
173	, round 22, finding 4
176	(round 12, M7; 
182	round 41, reader M7: 
193	, round 41, M6
205	 round 41, reader M7: 
219	; round 12, M4
228	(round 41, M9; 
229	(round 41, B1; 
229	 round 41, M3: 
230	(round 41, B1; 
230	; round 30, M3
234	(round 41, M7; 
235	 (round 19, operator M2 to M5)
257	 round 21, M1: 
267	(round 34, shell M4; 
278	; round 12, M2
330	Round 21, B2 and round 22, finding 4: 
378	 round 34, shell M3: 
386	(round 33, shell M4; 
386	; round 41, B1
393	(round 41, M5; 
401	 round 41, reader M8: 
429	, round 30, M2: 
429	Round 28: 
435	, round 41, reader M11
436	 round 33, shell M1: 
436	round 32, finding 9: 
440	(round 41, reader M10; 
442	 round 30, M6: 
443	 round 21, M9: 
481	(round 21, M11; 
481	; round 34, shell M1
487	; round 21, M6
488	, round 34, shell M5```

## Pass 3: last tags

```
1x (the ONE defining row; round 43)
1x (RUNBOOK section 4; round 12, nit)
1x make it instead: round 21, M11), THEN
1x the refused second start; round 34, reader finding 10)
1x (round 21, M10, AUDIT PROPOSAL, lead to confirm:
1x (reworded in round 34, shell M3) that
1x state `done`; round 41, reader M11, the one command
1x (round 30, M6, and the old form printed
1x F-007, round 32):**
1x DEFAULT for the GO (round 41, lead to confirm)
1x ONE DEFAULT (round 34, finding 1; round 41: lead to confirm
2x (round 34, finding 9; AUDIT PROPOSAL, l
1x the receipt part was added in round 33 and run once```

Kept on purpose: references to code rounds 23 and 24 (they name code changes, not review rounds). Tags still inside the shared clock block (lines 32-79) were not touched because that block must stay byte-identical with FIX-PLAN.md.
