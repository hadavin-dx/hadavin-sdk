# Resolution log, round 8 (C4 edit list)

Started about 14:55 UTC (20:25 IST), finished about 15:10 UTC (20:40 IST), Mon 16 Nov 2026. Builder only. The egm:egm-resolve skill was not used (as in round 7); the lead runs the reviewers. Round 7 is kept as `EDITS.round7.md`.

## Failures and gaps first
- Nothing was run except text and count checks (`verify8.py`, output in `resolve-r8-check-output.txt`: FAILURES 0). No code, smoke evidence or click path was read.
- UNVERIFIED and not fixable here: whether the model stage starts with a made-up key file in the flow rehearsal and in the preparation enquiry (ND6); the route of the preparation enquiry (ND8); EL-1 to EL-7 and finding M-1 (files not in this folder, ND10); text of rules A, E, F, I (ND11).
- The preparation enquiry is NOT applied: E-49, E-50, E-53 are Hold (new gate G5). Consequence: D8's "one made-up lead" is not done until G5 opens; the take rests on the tests. This is the safe default, not a deferral by choice: a paid call cannot be shown impossible today.
- The glosses of the plan codes are my reading of the plan (checked by grep), not confirmed by its author.
- The new owner texts are not read by a stranger. No commit.

## Finding to fix to where
| finding (round 7) | fix | row |
|---|---|---|
| Design M1: E-11 mixed tests and preparation enquiry; "stop and ask" is not a control | E-11 now only the laptop tests; paid call excluded by absence of the real key (rule 2, scope line 27, plan step 3.3), flow rehearsal setup marked not confirmed; enquiry paragraph moved to held E-49, scope row E-53, gate G5, ND6 and ND8 | E-11, E-49, E-53, G5 |
| Design M1 (fact 5) | fact 5 moved to held E-50; E-12 asks four facts | E-12, E-50 |
| Design M2: ND8 option A unverified | route A marked unproven and unable to send one enquiry; B is the only written route; what is left: nothing sent until answered | ND8, ND6, G5 |
| Design M3: unproven facts stated as facts | "planned", "not yet confirmed", "UNVERIFIED" wording in E-11, E-15, E-20, E-25, E-30 | several |
| Design m1: wrong step numbers | steps 17 and 18 (lines 95, 103) named | E-37 |
| Design m2: traces of the enquiry | listed (contact, mail, table row, saved run, journal and spend line) | E-49 |
| Design m3: "missed" exception wrong | exception is first run and repeat both missed (plan lines 14, 505); "41 pass" example replaced by "N pass" | E-12 |
| Design m4: E-48 key stays live, copies | asks again before window ends; rule per case; `shred -u` in text | E-48, R7 |
| Design m5: shred versus rm | `.n8n/config` removed by plain rm by default; ND9 | E-30, ND9 |
| Design m6: filming overrule | step 19 still applies in full | E-14 |
| Design m7: S9-2 | honest sentence added | E-51 |
| Naive M1: "that address" pointed to the forbidden address | E-06 and E-07 name the take n8n address | E-06, E-07 |
| Naive M2: "the lead", "executions" undefined in scope sheet | defined in first line | E-26 |
| Naive M3: password via file or prompt | file is the only way planned; two database passwords stated | E-09, ND1 |
| Naive M4: circular pass rule, "the plan" | three conditions, consequence, one exception; plan named in the words list | E-12, E-52 |
| Naive M5: failed confirmation had no consequence | no yes, assistant says what to change, asks again | E-04, E-37 |
| Naive M6 to M7: glossary block, words with several meanings | glossary split into bullets in the sheet's word list; secret key, password, encryption key, database user told apart | E-01, E-52 |
| Naive M8: long sentences | E-31 split; E-30 brackets reduced | E-31, E-30 |
| Naive minors | file path removed from E-03; post subject in E-18; hook door, name lookup explained; count lines plain | E-03, E-18, E-22, E-34, E-24, E-25 |
| Names: lead versus studio lead | "the studio lead" in this file; confirmations and NEEDS-STUDIO-LEAD renamed; ND10 and ND11 hold the open checks | header |

## Counts (from the script)
51 rows (E-01 to E-53 without E-10 and E-35): OWNER-STEPS 33, AGENT-SCOPE 14, DECISION-one-store 4. Apply now 39, Hold 12 (G1: 7, G3: 1, G4: 1, G5: 3). Types: STALE 15, UNCLEAR WORD 9, MISSING STEP 14, CONTRADICTION 12, DEFERRED 1.

## Check
Command: `python3 -I verify8.py > resolve-r8-check-output.txt`. Last line: `FAILURES 0`. 52 old texts each found once on the stated line, no overlaps, banned strings none, secret-like matches none.
