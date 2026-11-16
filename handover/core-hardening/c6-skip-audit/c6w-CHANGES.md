# c6w-CHANGES.md: what c6w changed against REPORT-c6v.md, finding by finding (written 2026-11-16, UTC; IST = UTC + 5:30)

FAILURES AND OPEN ITEMS FIRST (all mine, none hidden):
1. No EGM reviewer has read REPORT-c6w.md or the new class 7 checks. Every 'checked' below means: my own scripts passed on my own text. The independent evidence runner's own run on c6w is not done.
2. UNVERIFIED against the real files: the 104 old texts were checked only against the copy in evidence-c6w/tree/ (99 of 104 rows cannot be read in this repository). The builder who applies the rows must confirm each old text first.
3. G12 stays OPEN (the studio lead's gate). Nothing here approves it. That release note v18 dropped the words 'unless approved in writing' is NOT a decision; the report says so.
4. The box is 2,465 words, not the 2,500 I aimed at, plus 17 heading words; the verifier requires the box including its heading line under 2,500 (it is 2,482 with the heading).
5. Not fixed in c6w: naive m9 is only named in section 9 (the three counts are not reconciled in the text); the 1c-I G12 order was not re-read by anyone but me.
6. Slip of c6v, restated: c6v ran 6 full runs of run_all.sh against a cap of 3. c6w ran it 2 time(s) (cap 2); extra single script runs (verify alone, neg alone) are not full runs.

## Map: each finding of review-c6v-design.md and review-c6v-naive.md to its own fix and its own check

| id | the finding (short) | the fix in REPORT-c6w.md | the check (verify_c6w_part4.py unless named) |
|---|---|---|---|
| design B1 | answer line names c6u and REPORT-c6u.md | the answer line names c6w and REPORT-c6w.md; the typed line says so in step 2 | D-B1 answer line names this report |
| design M1 | box line 22 says release note lines 8, 33, 149, 150 equal v18; other lines say 8 and 149 differ; G12 reasoning rests on v14:149 | line 22 and the 1c text say 33 and 150 equal, 8 and 149 differ; every cite of item 11 says 'words in v14 only'; the G12 word gives its WHY | D-M1 one statement about release note lines |
| design M2 | G12 hold missing on rows 1 and 19; stale reason cells; 'eight' versus 11 rows | rows 1 and 19 carry the hold; the reason cells say the stopwatch is allowed and the lease setting only after G12; 'the eleven carve-out rows' | D-M2 every row with the lease label holds G12; count words equal listed rows |
| design M3 | rows 11 to 14 and row 96 contradict (40 s and 90 words versus 35 s) | row 96 sets 40 s like row 11; the defaults cut nothing by hand; Table B cases are not defaults | D-M3 one card state in rows 11, 13, 14, 96 |
| design M4 | card line 4 and 'lease' ship by default; card wording deferred to a question that does not exist | new question L-CARDLEASE (default keep, held under G12) in the box and in section 3 | D-M4 every question label used exists in the box table |
| design M5 | verifier claims exceed what is checked; box count excludes part 2; '267 copies' is my word | the box states its count and part 2 separately; HOW MUCH IS PROVEN BY WHOM says the counts are my own run; class 7 checks count words | D-M5 box count honest; count words equal rows |
| design m1 | first rehearsal list differs (5)-(9) versus (5)-(10) | ONE LIST in the box, 1c, 3d and section 0 | D-m1 one list before the first rehearsal |
| design m2 | v30 to v33 written-time statements conflict; mtime only | section 0 states the bulk write and that no content hash is used | D-m2 written-time statement |
| design m3 | example 'v30A' versus v34A | 'v34 rendering A' everywhere | D-m3 no 'v30A' |
| design m4 | stale labels c6t and 'done in' while nothing is applied | labels replaced by 'written in c6x, not applied' | D-m4 no stale label |
| design m5 | 'no sub-agent' versus six full runs | the sentence names the number of runs of run_all.sh and the cap | D-m5 run count named |
| design m6 | option (b) of L-CARDLEN has a 0.4 s margin | margin stated; (b) may run over until a stopwatch run | D-m6 margin stated |
| design m7 | default none reverses Q22 (c) for the video | L-LEASE row says plainly that the default follows ORD:230 and reverses ORD:186 | D-m7 reversal stated |
| naive B1 | same as design B1 | same fix | D-B1 answer line names this report |
| naive B2 | G12 has two forms and a circular order; re-smoke cases not placed | ONE form (the ORDERS.md line), results written first under risks list item 12, the three cases run in the loopback re-smoke (TASK (5)), the line is TASK (10) | N-B2 one G12 form, no 'lease wording approved' outside history |
| naive M1 | same as design M1 | same fix | D-M1 one statement about release note lines |
| naive M2 | one builder, two branches; which branch holds what | box step 1 names both branches, the 90 plus 5 rows and where c6w-APPLIED-ROWS.md and the commits go | N-M2 branch statement equals the table |
| naive M3 | reviewing described two ways | section 0 WHO HAS READ WHAT | N-M3 who-read-what bullet |
| naive M4 | same as design M3 | same fix | D-M3 one card state in rows 11, 13, 14, 96 |
| naive M5 | row 1 lacks the hold | same as design M2 | D-M2 every row with the lease label holds G12 |
| naive M6 | sheet A/B has two meanings | RENDERING A/B (two files) and KEY ROUTE A/B (two ways for the older key) | N-M6 no 'sheet A', both names present |
| naive M7 | non-default answers have no warning; L-LEASE ignored under L-POST yes; card wording deferral | paragraph EVERY ANSWER OTHER THAN THE DEFAULT NEEDS A FURTHER ROUND; L-CARDLEASE | N-M7 further-round paragraph |
| naive M8 | first-rehearsal precondition differs; TASK (9) is a question | ONE LIST; TASK (9) done when answered | D-m1 one list before the first rehearsal |
| naive M9 | box about 2,500 words, step 1 a run-on, labels before explanation | box shorter, step 1 in two parts, no undefined label before the WORDS list | N-M9 no undefined label before the WORDS list; box words stated equal counted |
| naive m1 | words with two meanings (step, line, check, key, lead) | LABELS bullet defines STEP, CHECK, KEY, PRIMARY KEY, lead | N-m1 labels bullet |
| naive m2 | undefined labels (L-APP2, G19, N1, classes, W-, release note versions) | LABELS bullet defines each | N-m2 labels bullet defines them |
| naive m3 | stale text (c6u this file, c6t box, NOT FIXED count 96) | replaced | D-m4 no stale label |
| naive m4 | 37 viewer rows versus 38 default rows | one sentence says they are different sets | N-m4 sets named |
| naive m5 | rows 39 and 76 same viewer text; reason cells long history | sentence in section 5: the reason cell after the first stop is history; rows 39 and 76 are two edits of two lines | N-m5 history sentence |
| naive m6 | reviewer-name order wording | reviewer-B and reviewer-C roles said | D-B1 answer line names this report |
| naive m7 | 'the lead' reader versus roles | box: if you are also the owner the roles stay separate | N-m7 roles sentence |
| naive m8 | section 3e item numbers | see section 9: stated, not renumbered | N-m8 listed in section 9 |
| naive m9 | counts to reconcile (seven stop steps, ten gate rows, six) | one sentence in section 9 names the three sets and what each counts | N-m9 listed in section 9 |

## Late evidence of the independent runner on c6v (message of the coordinator), each with its fix and check

| id | the finding | the fix | the check |
|---|---|---|---|
| L1 | 7 of 19 fresh mutations missed (check time in one of two places; v34-A to v33-A in one sentence; Five to Four; line 33 to line 34; v18 to v17; G12 hold removed from L-LEASE with the word count kept; 'cannot be filmed' flipped) | the census of verify_c6w_part3.py counts every copy of each of these phrases (check time in each written form, the L-LEASE G12 counts per line); verify_c6w_part4.py C7-1 to C7-7 read the meaning | C7-1 to C7-7; negative copies W-C7-* in neg_new_c6w.py, one per copy |
| L2 | nothing parses the numbers of CHANGES | the COUNT lines below are compared with the live check count, run-log.txt, neg-output.txt and scan-c6w-output.txt | V13 in verify-c6w.py |
| L3 | staleness fires on file time although the content is byte-identical | static-checks.sh now records a sha256 of every owner sheet and release note; the check treats a file as changed only if it is newer AND its hash differs from the recorded one | E-mtime and C-10c in verify_c6w_part2.py |
| L4 | the scan reports mail hits inside copies of the sheets | scan_c6w.py skips evidence-c6w/tree/ and evidence-c6w/steps-snapshot/ and prints the folders it scanned | scan-c6w-output.txt (line 'SCANNED (own output only ...)') |

## Counts (compared by the check script with the output files; a wrong number here fails V13)

COUNT verify checks: 0
COUNT full runs of run_all.sh: 2
COUNT negative changed copies: 0
COUNT negative wrong copies: 0
COUNT scanned files: 0

## Which branch holds what, and who read what
- The report, this file, the scripts and the outputs are in handover/core-hardening/c6-skip-audit/ and its evidence-c6w/ folder (branch cloud/core-hardening). Nothing is committed by me. The 99 demo-file rows concern branch cloud/flows-audit (folder handover/); the 5 rows 70, 71, 72, 90 and 91 concern inputs/DECISION-one-store.md on cloud/core-hardening.
- review-c6v-design.md and review-c6v-naive.md read REPORT-c6v.md only. No reviewer has read c6w.

## Files changed or made in c6w
REPORT-c6w.md, c6w-CHANGES.md, checkpoint-c6w.md, evidence-c6w/ (build_c6w.py, verify-c6w.py, verify_c6w_part2.py, part3, part4, neg_*.py, scan_c6w.py, run_all.sh, static-checks.sh, census-c6w.json, run-log.txt, outputs). REPORT-c6v.md, c6v-CHANGES.md and evidence-c6v/ were not edited.
