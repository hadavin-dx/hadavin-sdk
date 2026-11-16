# Appendix B: coverage, finding to fix to place (section 8) (appendix of REPORT-c6x.md; the heading and the pointer are in the main file)


COVERAGE OF THE c6v REVIEWS (review-c6v-design.md, review-c6v-naive.md; the line-by-line mapping is in c6w-CHANGES.md; the checks are in verify_c6x_part4.py and, for the old classes, in verify-c6x.py, verify_c6x_part2.py and verify_c6x_part3.py):

| Finding | Finding in short | Fix | Check |
|---|---|---|---|
| design B1 | answer line names c6u and REPORT-c6u.md | the answer line names c6w and REPORT-c6x.md; the typed line says so in step 2 | D-B1 answer line names this report |
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
| naive M2 | one builder, two branches; which branch holds what | box step 1 names both branches, the 90 plus 5 rows and where c6x-APPLIED-ROWS.md and the commits go | N-M2 branch statement equals the table |
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

COVERAGE OF THE c6u REVIEWS (review-c6u-design.md, review-c6u-naive.md, review-c6u-evidence.md, evidence-c6u-independent/mutations-raw.tsv and mutations-raw-batch2.tsv); the line-by-line mapping is in c6v-CHANGES.md; every check named here is in verify-c6x.py, verify_c6x_part2.py or verify_c6x_part3.py:

| Review item | Fix | Where / check |
|---|---|---|
| Design M1 (G12 hold missing on row 8 item 12) | the eleven carve-out rows (1, 2, 5, 15, 17, 19, 30, 34, 83, 93, 94) now say 'the 45 s lease setting is allowed only after G12 is approved' (c6w added the hold to rows 1 and 19 and fixed the stale reason cells) | rows 1, 2, 5, 15, 17, 19, 30, 34, 83, 93, 94; checked for every row that carries the label (class 7) |
| Design M2 (stale counts and versions in sections 0, 5a, 9) | counts recomputed; class 2 check: every count of 30 or more and every owner-sheet version quoted twice is equal; class 7 adds: every count word before 'carve-out rows' or 'rows' equals the rows it lists | verify_c6x_part3.py class 2 |
| Design M3 ('newest sheet' claim) | stated with its check time, regenerated in the last run; check E-mtime | static-checks-output.txt, verify E-mtime |
| Design M4 (row 96 anchor not unique) | old text 'own runs. \| 30 s EST'; class 6 check: a short old text occurs once in the whole file (it also found row 94 and fixed it) | rows 94, 96; class 6 |
| Design M5 (box step 1 target tree; C-1 label) | box step 1 names the branch cloud/flows-audit and the folder handover/; C-1 says DONE on the scratchpad copy, UNVERIFIED against real files | box, section 7 |
| Design m1, m2 (row 76 relayed tag; row 96 Time cell 35 s) | row 76 says 'relayed from the lane3 session's results, not run for this audit'; row 96 gives 35 s EST | rows 76, 96 |
| Design m3 (stale run-sheet leftovers) | rows 97 to 104 (decided items of the run sheet and the lines that said 'scene 5/11 if kept') | rows 97 to 104 |
| Design m4 (L-APP2) | NOT CHECKED here: I did not verify that the owner-sheet track carries L-APP2 | section 9 |
| Naive M1 to M7 (one status per open item; branch; stale counts; G12 one way with a typed form; HubSpot, key, identity defined once; L-SHEET routes A and B; card words) | statuses unified in the box; branch stated; counts recomputed; G12 quoted once with a typed form; words defined in the box before use; routes A and B explained in L-SHEET; card words ('lead' and 'contact', 'other lease settings') only noted in the word list, NOT changed on the card | box, 1c, section 3 |
| Naive m1 to m12 | fixed: terms before definition, scene descriptions, TASKS (4) and (5) builder instruction, stale names; NOT fixed, stated: the deletion gate is still told in four places (each place is checked by the census) | box, 1c, section 9 |
| Naive: box at most 2,500 words, recounted by script | the box is counted WITHOUT its heading line (it says so); the whole box with the heading is also under 2,500; both recounted by verify-c6x.py | check N5, E-count |
| Independent run: 24 of 103 mutations missed | the classes in the FAILURES bullet of section 0; one changed copy per class in neg_new_c6x.py | neg-output.txt W- lines |
| Independent run: symlinked steps-edits crashed build_c6u.py | static-checks.sh, run_all.sh and build_base.py stop with a message that names the cause | run_all.sh |

COVERAGE OF THE c6s REVIEWS (review-c6s-design.md, review-c6s-naive.md, review-c6s-evidence.md, evidence-c6s-independent/00-SUMMARY.md); the line-by-line mapping is in c6u-CHANGES.md; every check named here is in verify-c6x.py or neg_new_c6t.py and was shown to fail on REPORT-c6s.md:

| Review item | Fix | Where / check |
|---|---|---|
| Design M1 (the report says the sheets carry the 45-second sentence; they do not; LRN14:149-150) | L-POST, L-LEASE, box and section 9 no longer say the sheets carry it; TASK (9) is a question; LRN14:149 and LRN14:150 are the evidence of the L-POST default | box, section 3, section 9 |
| Design M2 (lease words on the video against ban item 11) | the words stay in the rows but are HELD under G12 (box, 1c-A, L-POST) | box, 1c-A, section 3 |
| Design M3 (alert-mail gate not carried through; no check row; tables lack the line 2 cut) | TASK (5) provokes the alert (test K3, command UNVERIFIED); check row C-12; Table B with the line 2 cut and the lines 1 and 2 cut and their Time cells | box, 1c-C, section 7 |
| Design M4 (box 'shorter' not true) | the box states its real word count and is under 2,500 words; the verifier recounts | box paragraph 2 |
| Design m1 (rows 53, 54, line 24) | FIXED IN c6u: row 95 added (see c6u-CHANGES.md) | section 0, section 9 |
| Design m2 to m6 | m2: Q27 reading is OWNER-OPEN (box, DATES); m3: stale labels moved to evidence-c6t; m4: scan timing in TASK (6); m5: scene times not checked (stated); m6: 'second person' named | section 0, 3b, 7, box |
| Naive M1 (two 'step N' lists) | WHAT TO TYPE = steps 1 to 5; the second list = TASK (1) to TASK (12) | box, 1c-F |
| Naive M2 (claim) | CLAIM always means reserve; a sentence is a STATEMENT | box, 1c-A |
| Naive M3 (row) | ROW = a row of the edit table; LINE = run sheet line; RECORD = database entry | box, 1c-A |
| Naive M4 (scenes 5 to 11) | the box says the run sheet holds scenes 1 to 4 and a closing card, and scenes 5 to 11 of an older plan are listed, not filmed; L-CUT says so | box, section 3 |
| Naive M5 (box length) | box under 2,500 words; the rest is in section 1c, nothing deleted | box, 1c |
| Naive M6 (option (b) of L-CARDLEN not shown) | the 74-word text and the five dropped items are in the box | box |
| Evidence 1 to 3 (stale time; absolute paths; 13 of 45 planted changes missed; box count never compared) | check times read at run time; relative paths; new checks and negative controls; box word recount; a newer owner sheet or release note fails | evidence-c6x/ (verify_c6x_part2.py, neg_new_c6u.py) |
| Late independent evidence on c6t, item 1 (14 of 40 changed copies missed: row lists, card words and seconds, option (b) words, budget, 45 s, 30 s, cites LRN14:149 and ORD:150, the count of kept runs, 13 minutes, 2 relayed runs) | every copy of a repeated fact is found by pattern and compared with ONE source: card words, seconds and budget recomputed from the four quoted lines; option (b) words recomputed from its quoted lines; the lease seconds read from ORDERS.md line 151; the recovery interval read from mf-recovery.json; the kept-run count from the four test counts; the 13 minutes and the 2 relayed runs from claims-A.md; the release note cites by line number set and the ORDERS cites by the content of the line; row lists by a near-copy rule; each change was tried on the first copy only and on all copies | evidence-c6x/verify_c6x_part2.py, evidence-c6x/neg_new_c6u.py |
| Late independent evidence on c6t, item 2 (run_all.sh needs the whole tree, the banned-names test file and the tree variable) | run_all.sh stops with one line per missing input; the variable is C6U_TREE (the folder 'handover' of the copied demo tree), optional C6U_STEPS; no machine path is written in any script | evidence-c6x/run_all.sh |
| Late independent evidence on c6t, item 3 (v32 and v16 exist) | the check names the newest owner sheet and release note version it found and stops loudly if the rendered files are missing; this report was checked against owner sheet v34 and release note v18 | evidence-c6x/static-checks.sh, section 0 |
| Late independent evidence on c6t, item 4 (the verifier exits 1 on REPORT-c6r.md and REPORT-c6s.md) | NOT FIXED ON PURPOSE: the verifier is written for this report; it also exits 1 on REPORT-c6t.md; this report does not claim a pass anywhere else | section 0, c6u-CHANGES.md |
| Late independent evidence on c6t, item 5 (real-looking gmail.com address) | c6u searched c6-skip-audit: only masked fragments in the c6t copies of old owner sheets (not files of c6u); c6u's own files hold no such address | c6u-CHANGES.md |

COVERAGE OF THE c6r REVIEWS (review-c6r-design.md, review-c6r-naive.md, review-c6r-evidence.md, evidence-c6r-independent/); the line-by-line mapping is in c6s-CHANGES.md:

| Review item | Fix | Where / check |
|---|---|---|
| Design F1 (failed-run saving not carried through C-4a, C-11, C-4 row list; PLAN:125) | C-4a and C-11 follow the defaults (successful runs all, failed runs none); PLAN:125 overridden on that point; C-4 row list corrected | L-SAVE, box, sections 7 and 9; checks 'F1' of verify-c6s.py |
| Design F2 (card line 2 states alert behaviour as fact) | gate: card line 2 not filmed until the loopback re-smoke on the edited flows shows an alert mail, with UTC, IST and a name | row 8 item 12, section 3e entry, box; check 'F2' |
| Design F3 (real-key scan holes: only after the first rehearsal; none between the take and deletion; scanner unreviewed; dump; swap) | scan after every rehearsal with real accounts and after the take BEFORE deletion; scanner read by a second person (someone who did not write the scan) and tested with a fake key; counts only; in place or a dump deleted and counted; swap point named | row 6 items 15 and 16, section 3e, C-6; check 'F3' |
| Design F4 (stale sheets; release note v14; G12 stretched) | sheet check rerun over v19 and later (v30 exists); the verifier fails on a newer sheet than the check time and on a version newer than the named one; release note v14 cited (G12 open); the wider reading of G12 labelled as this report's assumption | box, section 0, section 3, C-10c, section 9; checks 'F4' |
| Design m1 to m4 | crash-then-repeat case in the approval evidence; 'expected to be true until C-9 part 2'; cut-case totals once and a two-line Time cell replacement; EXAMPLE time later than the check time | row 8, row 13, box (L-CARDLEN, CUT CASE, answer line) |
| Naive M1 to M8, minors | box rewritten and shortened; does-not-do list first; reviewer order explained; one OWNER ONLY rule; Q27 and G12 explained; numbered steps; the circle in C-9 part 2 explained; word fixes; stale names; row 11 in 5a; section 0 history moved to 1b | box, sections 0, 1, 1b, 3, 4, 5a |
| Independent evidence (verifier failed 2 of 123 on v30; glob missed v30) | static-checks.sh covers v19 and later; the report names v30 and the check time | evidence-c6s/static-checks.sh |

COVERAGE OF THE c6q REVIEWS (review-c6q-design.md, review-c6q-naive.md, review-c6q-evidence.md, evidence-c6q-independent/00-SUMMARY.md, and the four items of the build coordinator); the line-by-line mapping with the exact lead questions is in c6r-CHANGES.md:

| Review item | Fix | Where / check |
|---|---|---|
| Design M-A (plain statement on card line 1 and caption before G12 is approved) | approval gate and mandatory repeat more than 45 s after the first send | row 8 item 12; section 3e entry; check 'M-A' of verify-c6r.py |
| Design M-B ('it sends one alert' as fact) | card line 2 says 'it sends an alert'; 'one alert' only for stand-in tests | row 14 and the box; check 'one alert' |
| Design M-C (Q27 meaning decided silently; L-DEL says ANSWERED) | labelled MY ASSUMPTION and OWNER-OPEN (ORD:232); L-DEL says what is still open; the sentence does not block Wed 18 Nov | box, row 8 item 11, section 9; check 'M-C' |
| Design M-D (real-key scan: how the key reaches the search; what a hit means; repeat after deletion) | pattern file in memory or standard input, never a command line, never on disk; hit means cancel or replace the key and treat runs as compromised; item 16 repeats the search | row 6 items 15 and 16; check 'M-D' |
| Design M-E (failed-run saving bundled with successful-run saving) | new question L-SAVEERR (default No); rows 53, 55, 62, 64, 66, 68 wait; row 92 keeps the failed-run setting none | box, section 3, 3b, 3c; check 'M-E' and C-4a (defaults only) |
| Design M-F (two constructions in the length table) | one construction; the separate shorter rewrite of line 1 is gone | box table; check 'M-F' |
| Design minors (row 11 viewer cell; rounds text; report voice in rows 40, 48, 49; 'expected' and pruning in rows 50, 52, 14; made-up domain check; run length for the latest start 18:04 UTC (23:34 IST); one-screen 'what to type') | fixed in rows 6, 8, 11, 14, 40, 48, 49, 50, 52 and the box; the card row's own Time cell on run sheet line 41 is NOT edited by any row (a lead question, section 9) | c6r-CHANGES.md |
| Naive M1, M5, M6 (word 'take'; claim table; internal codes; what to type) | 'take' means the filmed run only and the recovery flow 'claims the contact again'; the claim table and the take database are named; C-3 to C-9, G12, K3B, the cut number are explained; a WHAT TO TYPE block opens the box | box; checks 'naive M1', 'naive M5', 'naive M6' |
| Naive M2 (length table: option (b) needs a text the box does not show) | one construction | box table |
| Naive M3 (row 11 viewer cell) | corrected | row 11 |
| Naive M4 (section 3e omits rehearsal item 15) | three entries added; the box says how many stopping steps there are | section 3e |
| Naive minors (72 edits; verify-c6p; row 8 'items 11 to 14'; section 2 one run; build_mainframe.py missing from section 1; 'line 59 if L-POST stays yes') | fixed; the section 0 order (history before how-to) and the use of 'EGM' and 'KEY' in four meanings are NOT fixed here (lead question, section 9) | c6r-CHANGES.md |
| Independent evidence (8 missed mutations: weekdays, lease sentence on caption row 21, capitalised 'The lease question', a wrong count of rows that apply on the default, a wrong wave 1 count, stale card length '58 s' in the box, '(within 45 seconds)' in row 14) and the stale v29 line | all eight are now caught by named checks of verify-c6r.py and each has a negative control; the v29 files and times are restated and the verifier fails if one changed after the stated check time | verify-c6r.py; neg_controls_c6r.py |
| Coordinator: source copy | stated in section 0: the rows are checked against the scratchpad copy; equality with the real files is unverified; 99 of 104 rows cannot be read in the repository | section 0 |

COVERAGE OF THE c6p REVIEWS (review-c6p-design.md, review-c6p-naive.md, evidence-c6p-independent/00-SUMMARY.md); the line-by-line mapping with the exact lead questions is in c6q-CHANGES.md:

| Review item | Fix | Where / check |
|---|---|---|
| Design B1 (default lease sentence on public video text against ORD:230; 'none reverses Q22 (c)' unsupported) | the default is no lease sentence on the card and caption; ONE new yes or no question L-POST asks whether 'public post' includes the card and caption; no row puts the limit sentence in a document (c6t TASK (9)); the claim of 'none' is restated honestly | box, section 3 (L-POST, L-LEASE), rows 11, 13, 21 |
| Design M1, naive M4 (default incoherent: gap under 30 s, scene 2 at 40 s; label 'setting: lease 45 s'; what the viewer sees per answer) | with no lease sentence on the card the gap is only written down; the table of lengths and L-LEASE say what the viewer gets per answer; the label and the words 'other lease settings' are named in L-POST | box, section 3, row 6 item 13 |
| Design M2, naive M1 (card arithmetic for the recommended sentence; 'add sixteen seconds'; 'add' reads as keeping both) | table of lease answer by card length (words, seconds, budget, total); answer 2 REPLACES answer 1 (net +15 words, about +6 s); 'add' removed | box, L-CARDLEN, verify-c6r.py |
| Design M3 (report-only labels in new run-sheet texts; stale 'needs n8n' sentence) | new texts rewritten as plain sentences (rows 6, 8, 13, 21, 25, 37, 47, 57, 70, 72, 90, 91); the sentence is removed from item 11; the check scans for check labels, source cites, 'reading 1/2', 'this report' and question names | verify-c6r.py |
| Design M4 (newest word L-A/B, L-LEN, L-FACTS ignored; L-SHEET and section 9 stale) | L-SHEET reads 'confirm the one final sheet' and names the rendered v29 A and B; C-10c rerun at 16:52:47 UTC = 22:22:47 IST (v19 to v29 (all variants, the templates called SOURCE included)) | section 3, section 9, C-10c, evidence-c6r/static-checks-output.txt |
| Design M5 (item 15 second leak scan plants only fake values) | item 15 says what is searched: real key values read from the file that holds the keys, not printed, counts only | row 6 |
| Design M6 (C-10b PASS and FAIL cells disagree; the line in the box) | both cells say all of (a), (b) and (c); the box says once that there is no take on Mon 23 Nov unless they are shown | C-10b, box |
| Design M7 (REPORT.md line 80; reading-2 facts) | LREP:80 and gate G12 (LRN:33) named as OPEN with the studio lead; the guess 'plausibly meant a second send' withdrawn; the facts of answer 2 are marked not to be spoken as fact before C-9 part 2 | section 0, L-LEASE, section 9 |
| Design minors (row 90 'owned by'; 'the evening inference'; 18:04 as a plan fact; plan line 1051; ORD:147; fresh container; contact grep copied; duplicate section 9 lines; string-only checks) | row 90 ends at the database n8n; the evening inference is gone; 18:04 is called a plan fact that moves with the seconds the take needs; line 1051 is 'called stale by the studio lead, UNVERIFIED'; the departure from ORD:147 is stated in section 0; the rule is looked at again in the take's fresh container; the contact grep was rerun (evidence-c6r/contact-grep-output.txt); the duplicate lines are merged; verify-c6r.py adds recomputed and cross-place checks | section 0, row 8, rows 90, C-9, section 9 |
| Naive M2 (box too long) | box shortened (see its word count in evidence-c6r/verify-c6r-output.txt); the second word list moved to section 1 | box, section 1 |
| Naive M3 (labels used before definition or never defined) | box defines loopback re-smoke, wave 1, rehearsal list, risks list, stand-in, the two test figures, table rule on the contact id, check C-9 part 2, send, same id and the ten files before using them | box |
| Naive M5 (exact card not in the box) | all four card lines are printed in the box | box |
| Naive M6 (reply line) | the three names are placeholders you choose, the form for several exceptions is given, what happens if C-9 part 2 fails is said, and L-SHEET is said to be outside 'apply all defaults' | box |
| Naive minors | L-SCENES mentions removed; rows 81 and 86 named in section 1; one definition of wave 1; the first rehearsal comes after TASKS (5) to (9) everywhere (c6u: the c6t text said 'steps 5 to 9', which are the wrong list); words with more than one meaning listed in section 1; answer 2 no longer says 'refused' or 'recovery part'; raw cites removed from the box; L-SAVE says why failed runs matter | section 1, section 3, box |
| Evidence summary (L-SCENES in 3e; 'ready' and 'n8n' used before definition; C-8, RES:97, PLAN:125 in new texts; owner sheet v28 changed after the check) | 3e reworded; the box defines both words first; the labels are removed from the new texts of rows 25, 37, 47, 57, 70, 72, 91; C-10c rerun | 3e, box, rows, C-10c |

COVERAGE OF THE c6o REVIEWS, AS FIXED IN c6p (c6q changes the card default and the lease rows: see the block above) (review-c6o-design.md, review-c6o-naive.md, review-c6o-evidence.md):

| Review item | Fix | Where / check |
|---|---|---|
| Naive B1 (apply-all-defaults leaves the card half-changed; five contradictions) | one definite card under the defaults: rows 11, 13, 14 hold the (a) text with the reading 1 sentence, exact word count and seconds in the box; all card rows apply together | box, rows 11, 13, 14, L-CARDLEN, section 1 |
| Naive B2, design M1 (L-LEASE) | restated against Q22 (c) (ORD:186) and ORD:230; default 1 (his own answer); sentence texts for 1 and 2; 'none' says it reverses Q22 (c); costs to the viewer; a recommendation; definition of lease corrected | box, section 3 L-LEASE, Words, rows 13, 21, 8 (item 12) |
| Design M2 (row 11 false figure; the two stale word counts; option (a) row; 37-word sentence) | row 11 states 115 words, about 46 s, budget 50 s, about 200 s in all; option (a) is now the text of rows 13 and 14; the reading 2 sentence is counted (40 words) | rows 11, 13, 14, L-CARDLEN |
| Design M3 (section 5a stale, page rows missing) | 5a is made from the table (the count is in its heading) | section 5a |
| Design M4 (newest owner sheet) | C-10c rerun over v19 to v28 at 16:01:45Z = 21:31:45 IST; 'newest' restated with the time; L-SHEET default v28 A | section 0, section 3, C-10c, evidence-c6p/static-checks-output.txt |
| Design M5 (row 90) | new text ends before ' owned by'; 'third place' removed; row 91 says some bookkeeping files stay files | rows 90, 91 |
| Design M6 (row 6 item 16) | says it is not verified that deletion erases; third leak count added | row 6 |
| Design M7 ('row N' in new text; 'accepted'; scene 3 timing; 30 s in the reason) | item 13 no longer says 'row 13 explains'; row 8's view no longer says 'accepted'; row 6's view says the repeat-send check; reasons updated; the check script scans new texts for 'row N' | rows 6, 8, verify-c6p.py |
| Design M8 (row 76 design intent; 'stored'; L-23NOV; Q25/Q27 cover (a)(b)(c); QUESTIONS.md line 73) | row 76 and section 0 say design intent, relayed; rows 25, 37, 38 say 'stored'; 18:04 UTC = 23:34 IST used in row 8, box, C-10b; (a), (b), (c) all required | rows 76, 25, 37, 38, 8, box, C-10b |
| Design m1 to m8 | m1 L-SAVE now says what the owner approved (saving successful runs, ONE:22-27) and that saving failed runs is not in his words, so the studio lead confirms both (box and section 3); m2 'seven steps can stop' (box); m3 3e reworded (retake count, Q21.4, Q24); m4 the 144.3 s figure says 'from n8n coming back up' (rows 47, 77 to 80); m5 none needed; m6 section 1 sentence rewritten; m7 option (a) total includes the lease sentence; m8 controls now cover card length, 'row N', stale numbers (neg-output.txt) | section 3, rows 47, 77 to 80, verify-c6p.py |
| Naive M1 (rows 17, 81 and Words say the 45 s is on the card) | rows 17, 81 and Words say 'may', true for every answer | rows 17, 81, Words |
| Naive M2 (stale numbers in L-CARDLEN) | recomputed (115 words, 46 s; option (b) 87 words) | L-CARDLEN |
| Naive M3 (L-SCENES unanswerable) | the question about restructuring the scenes was removed; its substance is a consequence of answer 1 of the lease question (item 13 and L-LEASE say what the studio lead does) | section 3, row 6 |
| Naive M4 (contact-deletion gate described three ways) | one description: five entries, every request line, searches additional | box, L-DEL, section 6, 3e, row 8 |
| Naive M5 (HubSpot key / identity) | the take script's identity (studio lead's words, UNVERIFIED) is kept apart from the owner's key (unknown) | section 3 L-DEL, section 6 |
| Naive M6 (L-ONEDB and rows 90, 91) | box and section 3 say rows 90 and 91 apply by default and edit only the decision file | box, section 3 |
| Naive M7 (row 14 vs row 44) | row 14's reason says the card line says only 'may stay' and 'not measured', true whatever statement 18 turns out to be | row 14 |
| Naive M8 (step order) | one numbered order in the box; first rehearsal after the re-smoke and the two lines of item 14; Words and 3d agree | box, Words, 3d |
| Naive M9 (L-KILL form and row) | reply form a or b; the question reads 'a/b'; row 74 named | box, section 3 |
| Naive M10 (box too large; labels before definitions; setting names) | box rewritten: words first, a table of questions, one answer line; no setting names in the box | box |
| Naive M11 ('switches ON' vs 'changes no running n8n') | one sentence: it edits the files; the studio lead sets the n8n values | box |
| Naive minors | line 6 'never writes the lead' corrected; 'two crash tests' now 'two of four'; OS25 entry fixed and OS28 added; row 83 reason fixed; row 23 start time; leak-scan store list; row 92 film-v5; K3B/K3 name table kept (section 2) | Words, section 1, rows 23, 83, 92 |
| Evidence caveats (the audited files are not in the repo checkout; the runner's own checker bugs; builder's controls run from a copy) | stated in section 0 (the audited tree is a read-only copy of branch origin/cloud/flows-audit in the build session's scratchpad); verify-c6p.py reads that copy; nothing new is claimed about files that were not read | section 0, section 7 |

COVERAGE OF THE c6n REVIEWS (kept from REPORT-c6o.md):


| Review item | Fix | Where / check |
|---|---|---|
| Naive B1 (repeat-send sentence has two justifications; 'index not seen, accepted') | rows 13 and 21 carry only the plain statement and are NOT FILMABLE until L-LEASE; the flow reading is in row 13; the exit is removed | rows 13, 21, 8 (item 12), C-9, section 3 L-LEASE, 3e |
| Design M1, naive M3 (row 11 known-false total) | row 11 gives 150 s for scenes 1 to 4 and 'EST not measured' for the card; two options with numbers | row 11, L-CARDLEN |
| Design M2 (scenes 2 and 3 restructure) | a question about restructuring the scenes (dropped in c6p) with the effect on the 40 s and 25 s budgets | section 3 |
| Design M3, naive M1 (sped up label, RS:32, 45 s carve-out) | label added to rows 1 and 17; carve-out in rows 2, 5, 15, 19, 30, 34; RS:32 rows 93 and 94 | rows 1, 2, 5, 15, 17, 19, 30, 34, 93, 94 |
| Design M4 (L-CARDTEXT ties; splits; 3b; builder notes and blank) | rows 15, 20, 29, 31 tied; rows 1, 33, 39 split (1/73/74, 33/75, 39/76); 3b recomputed; blank and builder text removed from row 6 | rows 1, 6, 15, 20, 29, 31, 33, 39, 73 to 76, table 3b |
| Design M5, naive M5 (row 8, C-10b, Q23, Q27, key scope, made-up contacts) | rewritten; (a), (b), (c); every request line to be read; key scope UNVERIFIED | rows 8, C-10b |
| Design M6 (n=2) | rows 47, 77, 78, 79, 80 | RES:85 |
| Design M7 (residual lines) | rows 81 to 91; the words 'two stores' and 'three stores' are not used | rows 81 to 91 |
| Design M8 (second leak scan, after-take deletion, generator rule) | rows 6 (items 15, 16), 92, 62 to 69 | rows 6, 62 to 69, 92 |
| Naive M2 to M11 and minors (glossary, six checks, apply-all-defaults, reply line, reply forms, earliest date, run-sheet line numbers) | box rewritten; glossary words added at the top of the box; the run-sheet headings are at lines 49 and 61 (the c6n report wrongly gave 59 and 71, which are item 10 of each list) | box, section 1 |
| Independent summary (check script never fails; 60.1 to 61.9, the split of the kept runs and one IST change undetected; 58 s card) | evidence-c6p/verify-c6p.py exits non-zero on any failed check and has the new checks; the 17 (18 plus control) negative controls rerun; card in L-CARDLEN | section 7, evidence-c6p/neg-output.txt |


| Review item | Fix | Where / check |
|---|---|---|
| Naive B1: the box used terms before they were explained (n8n, scene numbers, K3B and K3, the take, run sheet, rehearsal list, item numbers, wave 1, lane3, alert delay, Q21.2, re-smoke plan, 're-pin') | A seven-point plain preface before the table; the table cells are plain sentences; 're-pin' is defined in the preface and Words and glossary | Box; Words; glossary |
| Naive M1: the answer line was not typeable (time label, IST, names, no example) | One exact line to copy, with UTC and IST, an explained list of names and a worked 'except' example | Box, 'How to answer' |
| Naive M2: 'apply all defaults' hides consequences | Three lists: it does / it does not / you still have to (saving of every run, the unreviewed 45-second sentence, the checks, the builder and reviewers) | Box |
| Naive M3: two gate lists collide; item numbers ambiguous; the contact-deletion check twice | The lists are named RISKS LIST (line 59) and REHEARSAL LIST (line 71); every item number says its list; the contact-deletion search exists only in row 8, and row 6 item 12 holds only the owner-sheet check | Words; rows 6, 8; glossary |
| Naive M4: 'lead' with two meanings (rows 11, 13, 21, 22, 24, 37, 47) | In new texts and prose 'contact' and 'studio lead'; the one exact decision sentence keeps 'lead' and is explained | Rows 9, 11, 13, 21, 22, 24, 37, 41, 48, 49, 50, 54, 59; check script scan 'bare lead' |
| Naive M5: 'alert' and 'lease' unexplained for a viewer; 'take' in a fourth sense | Row 14 line 2 says what an alert is; rows 13 and 21 say 'a setting called the lease' and 'keeps that contact reserved'; the plain sense of 'take' (a run took a contact) is written as 'reserved for the run that took it first' | Rows 13, 14, 21 |
| Naive M6: the rule 'no timing number' contradicts the spoken 45 seconds | One sentence in Words: the video says no test result in seconds and does say the 45-second setting; rows 1 and 17 say 'no test result in seconds' | Words; rows 1, 17 |
| Naive M7: rows 6 and 8 'ready' but depend on an unanswered question; no earliest date | READY defined (text can be applied; gate stays closed); 'You still have to' list; 'Earliest realistic date' says the audit cannot give one and what it depends on | Box; Words |
| Naive M8: stop and continue rules ambiguous (row 6 item 13, row 23, gate 12 free exit, blank owner) | Section 3e: for each gate, who stops, who is told, may the take go on; gate 12 says who may accept, when and what happens otherwise; the gate owner is named in item 14; row 23 says the studio lead stops filming | Section 3e; rows 6, 8, 23 |
| Naive m1: times without IST or without a time | UTC and IST in rows 6 and 23 and in 3d; example format given | Rows 6, 23; 3d; Words |
| Naive m2: 'clean-up' with several meanings | Words: hiding a run, automatic removal (pruning); 'clean-up' only inside quoted file text | Words; rows 14, 23, 44, 50 |
| Naive m3: box and section 3 disagree (L-SHEET; L-ONEDB changes nothing) | Same words in both for L-SHEET; L-ONEDB says no row of wave 1 depends on it | Box; section 3 |
| Naive m4: section 5 unreadable | Section 5a lists the 12 rows a viewer sees in a short table | Section 5a |
| Naive m5: row 1 new text is a note to the filmer, not a caption | The new text begins 'Scene 4 filming note (a note for the person filming; it is not a caption)' | Row 1 |
| Naive m6: C-10c 'done on sheets' versus 'NOT RUN'; 'all 8 flow files'; L-CUT missing from 3d | C-10c part 2 named as the not-run part; row 62 says that only the 4 real-v5 files are edited; rows 63 to 69 share a short reason; L-CUT added to 3d | Section 0; rows 62 to 69; 3d |
| Naive m7: three numberings of the card | Section 5b: old line, new line table | Section 5b |
| Naive m8: developer words in the box | No setting names in the box; 'your answers of 2026-11-16 (Q21.2, Q22)'; 'the owner's choice of 2026-11-16' | Box |
| Naive m9: are owner and studio lead two people? | Words: two roles, different jobs; no file says whether one human fills both | Words; glossary |
| Naive 'could not follow': overlap with a voided run; why a 338.7 s run was voided; 'unique index seen'; 'the handoff' | Section 0 says the overlap is unchecked and not harmless, that a never-finished run could be a hidden failure and that nobody can say who voided it (needs-lead: ask lane3); gate 12 says how the index is seen (psql \d mf_leads); the handoff is handoff\SESSION-HANDOFF.md in the studio folder | Section 0; row 8; glossary; section 9 |
| Design M1: 45 s measured from the first reply, not the first send | Rows 6 (item 13), 13, 21: counted from the first send, under 30 s (15 s margin), scene 2 must be shortened or the first send made late in it; source JF:97 | Rows 6, 13, 21; section 3e |
| Design M2: 'two stores' is false (the stage journal is a third record) | L-ONEDB rewritten: no viewer-facing sentence on the number of stores until C-8 passes; then only 'one Postgres server, two databases' (Q21.3); rows 58 and 59 no longer wait for L-ONEDB | Section 3; rows 58, 59; table 3b |
| Design m3: retention sentence assumes automatic removal is on (NS:42 says it was still being tested) | Rows 14 and 44: 'may stay'; we did not measure how long or whether the removal ever happens | Rows 14, 44 |
| Design m4: rows 3 and 4 not tied to L-CARDTEXT and L-CARDCUT | Ties added; counts of table 3b regenerated and rechecked | Rows 3, 4; table 3b |
| Design m5: contact-deletion check written twice | Kept only in row 8; row 6 item 12 holds the owner-sheet check and points to it | Rows 6, 8 |
| Design m6: 'stale according to that answer' is the report's inference | Row 8: 'probably stale ... he confirms at the re-pin' | Row 8 |
| Design m7: L-KILL default cites decision 8 as the cause | The default cites the missing flow results; decision 8 is named only as not the reason | Section 3, L-KILL |
| Design m8: the count of kept crash runs did not name both voided runs on four report lines (52, 54, 113, 449) | Both labels (VOID-fl45k3b, VOID-fl45k6c) named on those lines; the check script reads every line that counts the kept runs | Section 0; section 2; verify-c6p-output.txt |
| Design m9: C-10c box wording; 'lead verifies at re-pin' only in prose; rows 40 and 48 cite a file on another branch; row 6 item 14 depends on L-SAVE | C-10c says 'any mention of read-only'; rows 6 and 8 say 'the studio lead verifies at the re-pin'; rows 40 and 48 name the branch cloud/core-hardening; item 14 applies only if the flow files are edited (delete it otherwise) | Section 0; rows 6, 8, 40, 48 |

