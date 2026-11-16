# c6x-CHANGES.md: what c6x changed against REPORT-c6w.md, finding by finding (written 2026-11-16, UTC; IST = UTC + 5:30)

FAILURES AND OPEN ITEMS FIRST (all mine, none hidden):
1. No EGM reviewer has read REPORT-c6x.md or the class 8 checks (verify_c6x_part5.py). Every 'checked' below means: my own scripts passed on my own text. The independent evidence runner has not run on c6x.
2. UNVERIFIED against the real files: the 104 old texts were checked only against the copy in evidence-c6x/tree/ (99 of 104 rows cannot be read in this repository). The builder who applies the rows must confirm each old text first.
3. G12 stays OPEN (the studio lead's gate). Nothing here approves it. Release note v18 dropping the words 'unless approved in writing' is NOT a decision; the report says so. The scope of G12 (four held items, twelve carve-out rows) is the report's own reading and no reviewer has confirmed it.
4. The 75 first failures 'D-late' of the c6w negative run: the onset was 19:44:35 UTC, after the unchanged copy V0 passed at 19:44:13; the live sheets were rewritten between them. I could not prove the cause from the c6w files alone, so c6x removes the cause (the input is pinned, steps-pinned and late-pinned, hashes in STEPS-PIN.txt and LATE-PIN.txt) and no longer counts a state-only failure as caught.
5. COUNT 314 against 313 (c6w review M-minor m1): the c6w COUNT included the unchanged copy V0. c6x counts changed copies only (V0 excluded); a copy equal to the report is reported NOOP and counts as wrong.
6a. v35 and v19 against v34 and v18 (c6w CHANGES 6a said 'equal'; REPORT-c6w line 75 said DIFFERENT): compared by script, evidence-c6x/compare-late-files-output.txt: all three pairs are DIFFERENT after the version number is changed. CHANGES of c6w was wrong; the report was right. The freeze stays at 2026-11-16T19:30:00Z (= 2026-11-17 01:00:00 IST).
6b. RUN COUNT: see the COUNT line below and run-log.txt (one line per run of run_all.sh, cap 2). Each run's exit lines are in run-log-exits.txt; if a run did not end clean, the report section 9 says so. The output file times against the report time are in order-check-output.txt.
7. NOT RUN: no commit, no push, no n8n run, no model call, no spend; the 104 rows are not applied; the lease re-smoke (TASK (5)) is not run. The old text of 99 rows is unread outside the copy in evidence-c6x/tree/.

## Map A: each finding of review-c6v-design.md and review-c6v-naive.md (carried from c6w; the fix and its check still hold in c6x)

| id | the finding (short) | the fix in REPORT-c6x.md | the check |
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

## Map B: each finding of the c6w reviews (review-c6w-design.md, review-c6w-naive.md, report-c6w-builder.md) and the late independent evidence on c6w

| id | the finding | the fix in c6x | the check |
|---|---|---|---|
| c6w design M1 | the G12 hold lists differ (box, 1c-A, row 96) | the four held items and the 76-word case are in the box item 6, row 96 and Table B | C8-2, C8-3 |
| c6w design M2 | 'in the box' claims were checked against box plus section 1c | the class 8 checks read the start box alone (boxs) | C8-1 to C8-8 |
| c6w design M3 | negative copies marked OK for the wrong reason (75 first failures D-late; the row 19 mutant) | INTENT per copy; state-only failures never count; NOOP detection; row 19 mutant now edits the new-text cell | neg-output.txt (no WRONG line), X-row19-G12-hold-removed-in-new-cell |
| c6w design M4 | CHANGES 6a said equal, the report said DIFFERENT | compared by script; both say DIFFERENT | C8-11 |
| c6w design M5 | card line 3 against L-ONEDB | card line 3 names n8n's own database only, no count; L-ONEDB states its scope | C8-6 |
| c6w design m1 | COUNT 314 included V0 | changed copies only | V13 |
| c6w design m2 to m6 | one crash point in the G12 test; silent L-LEASE no-op; typed line form; counts; word counts | stated in the box and section 9, counted by script | C8-8, C8-9, D-late |
| c6w naive M1 | the box never says no reviewer has read it | said in the first lines and in the box | C8-1, C8-9 |
| c6w naive M2 | 'newest at the check time' against the freeze | 'newest before the freeze' everywhere | C8-14 |
| c6w naive M3 | card line 4 'other lease settings' not listed as held | listed in item 6 | C8-2 |
| c6w naive M4 | only the approving G12 form in the box | the three forms (approved, not approved, closed) in the box | C8-4 |
| c6w naive M5 | two owner items about the take script without label, question, answer | rows L-Q27, L-DELCRIT, L-KEYLINE in the box | C8-5 |
| c6w naive M6 | 'a sentence about the 45-second setting' has two meanings | the box says the label and the carve-out rows; the 45-second sentence is defined | C8-2 and the D-M2 checks |
| c6w naive M7 | run_all.sh run 1 failure and the piece runs not stated | section 0 and section 9 give a statement of each run | C8-12 |
| c6w naive M8 | counts: seven stop steps, eleven gate rows, ten in CHANGES | SEVEN STOP STEPS AND ELEVEN GATE ROWS, counted by script | C8-8 |
| c6w naive M9 | the typed line names: literal or not | the box says the names are chosen by the studio lead and no program reads the line | C8-7 |
| c6w naive minors | words lead, claim, A/B; scene 12; tonight; stale label | defined in the box; dates added; stale label removed | C8-13 |
| c6w builder report | ORD:147 departure needs a lead yes or no | question L-KEYLINE | C8-5 |
| evidence runner 1 | five copies exit 0 with no failed check, and 07-card-87-words-first (first-copy-only edits of repeated numbers or phrases) | the census holds the count of every copy of each card number and the gate phrase; one control per copy position, each with its intended check | class 1 census, C8-15, X-*-copy* in neg-output.txt |
| evidence runner 2 | an unrelated state-dependent failure counted as caught | INTENT map; D-late and the other state checks count only where named; input pinned | neg-output.txt |
| evidence runner 3 | which build produced the report; output time against report time; run count | section 9 names build_c6x.py and the run; order-check-output.txt; run-log.txt | C8-12, V13 |

## Counts (compared by the check script with the output files; a wrong number here fails V13)

COUNT verify checks: 287
COUNT full runs of run_all.sh: 1
COUNT negative changed copies: 330
COUNT negative wrong copies: 0
COUNT scanned files: 0

## Which branch holds what, and who read what
- The report, this file, the scripts and the outputs are in handover/core-hardening/c6-skip-audit/ and its evidence-c6x/ folder (branch cloud/core-hardening). Nothing is committed by me. The 99 demo-file rows concern branch cloud/flows-audit; the 5 rows 70, 71, 72, 90 and 91 concern branch cloud/core-hardening.
- review-c6w-design.md, review-c6w-naive.md and review-c6w-evidence.md read REPORT-c6w.md only. No reviewer has read c6x.

## Files changed or made in c6x
REPORT-c6x.md, REPORT-c6x-TABLE.md, REPORT-c6x-COVERAGE.md, c6x-CHANGES.md, checkpoint-c6x.md, evidence-c6x/ (build_c6x.py, assemble_c6x.py, verify-c6x.py, verify_c6x_part2 to part5, neg_*.py, scan_c6x.py, gen_changes_c6x.py, run_all.sh, static-checks.sh, census-c6x.json, run-log.txt, steps-pinned, late-pinned, outputs). REPORT-c6w.md, c6w-CHANGES.md and evidence-c6w/ were not edited.
