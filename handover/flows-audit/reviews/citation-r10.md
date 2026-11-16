# citation-r10 (citation checker, read-only; input fix-cite11.md)

Honest scope first. The files hold more than 5000 references (the fixer's check_refs counts 5167). I did NOT open every one. I opened (a) every file:line cite the fixer's log lists, (b) every new phrase or row pointer in fix-cite11.md, (c) a large sample of the other file:line cites found by a script, checked against the canonical copies under handover/demo/ (copies under flows-audit/tools/scratch/ are other versions and were excluded). Several targets (take_check.sh, run_all.sh) are being edited at the same time, so line numbers drift; phrase cites are the reliable kind. Nothing was edited except this report. No secrets seen or printed.

## Counts (cites I gave a verdict on)
- MISMATCH: 4
- SOFT MISMATCH (pointer wording does not fit its target): 3
- CANNOT-CHECK (target file absent): 9 groups (demo3/kill/RESULTS.md, run_real_check.py, crm_hubspot.py, harness.py, old-file heading lines in QUESTIONS 522ff, and similar)
- MATCH: all other checked rows, including every new pointer in fix-cite11.md except those listed below
- NOT A CITE: evidence-5.md lines 386 and 512 (raw grep dumps quoted as evidence, not pointers)

## MISMATCH (fix these first)

| file:line | cite | verdict | note |
|---|---|---|---|
| FINDINGS.md:153 (F-046) and LEDGER-ROWS.md:46 | "CLAIMS-TABLE.md row B-054 (line 559)" | MISMATCH | Row B-054 is at CLAIMS-TABLE.md:717, quoted target: "B-054 | PLAN:122 | T1 (burst of 10) and K1 (n=5) re-run o...". Line 559 is wrong. Better: drop the line number, keep "row B-054". |
| QUESTIONS.md:481 (item 29) | "flow-check/run_all.sh (line 96)" as a place that prints/checks the "(decision 4)" text | MISMATCH | run_all.sh:96 is a comment about the FINAL line. The text "ACCEPTED: recovery flow not part of the take (decision 4)" is at run_all.sh:99. Line numbers drift; point at the phrase instead. |
| QUESTIONS.md:300 and :304 (Q300 item 3) | "RUNSHEET-WORDING.md ... the line 'rule 7'" / "RUNSHEET-WORDING rule 7 forbids [normally one]" | MISMATCH | RUNSHEET-WORDING.md rule 7 is "Numbers rule (W-18): a recovery number is quoted only for one stop point at a time...". The phrase "normally one" does not occur in RUNSHEET-WORDING.md at all (0 hits). The forbidding sentence ("the words \"normally one\" are forbidden") is in CLAIMS-TABLE.md (line 76). Fix: say CLAIMS-TABLE.md line 76 instead of RUNSHEET-WORDING rule 7. |
| QUESTIONS.md:318 | "FINDINGS.md lines 115 (F-011), 117 (F-041), 150 (F-044)" | MISMATCH | Line 115 = F-011 (MATCH). Line 117 is F-029, F-041 is at line 118. Line 150 is not F-044; F-044 is at line 151. Also drifts; cite by finding id only. |

## SOFT MISMATCH (pointer wording not fully supported by the target)

| file:line | cite | verdict | note |
|---|---|---|---|
| QUESTIONS (item 1/2/3, OWNER-STEPS pointers) | OWNER-STEPS-q16-rows.md "values only the lead can give" | SOFT MISMATCH | Target heading is "### Values only the lead can supply" (line 305). Wording differs by one word; a search for the quoted words finds nothing. |
| QUESTIONS (item 29 area) | take_check.sh "header comment" | SOFT MISMATCH | The phrase is found in the check logic (take_check.sh:592-593 now), not in a header comment. fix-cite11 says lines 11/461/462; they are 592/593 in the current file. Phrase cite 'recovery flow not part of the take' exists and is fine. |
| QUESTIONS (RUN-ON-LAPTOP:27 cite for T18) | T18 | SOFT MISMATCH | T18 is not named on RUN-ON-LAPTOP.md line 27; the line there is about the 8 kills per test, no T-id. |

## CANNOT-CHECK (target not in this checkout)
- handover/demo3/kill/RESULTS.md:40-48 (FINDINGS row 63): the file is absent; fixer marked it so, correct. A basename match to demo/hang/RESULTS.md is NOT the same file.
- run_real_check.py:993, crm_hubspot.py:492-499 (QUESTIONS item 8) and harness.py:26 (REPORT:45): absent; fixer marked "(file not in this checkout)", correct.
- The "Original heading line N of the old file" lines in QUESTIONS.md (522 onward): the old file is gone; the quoted text is restated in place.

## Fixer's new pointers, re-read independently (fix-cite11.md rows)

| fix-cite11 row | new cite | verdict | note |
|---|---|---|---|
| F-002 sentence | dn1_common.py: no 422 line; take() resends when reply has no 'verdict' | MATCH | file has no "422"; take() code re-sends on missing verdict |
| F-008 | take_check.sh 'saveManualExecutions' / 'run saving not all/all/True' | MATCH | phrases found in take_check.sh |
| F-010 | FIX-PLAN [config] 'F-010 three database roles (plus n8n's own: four)'; ROLES-PROPOSAL 'Proposed logins' | MATCH | both found once |
| plan-wp6 line 193 | 'the python block that starts import collections, re, sys' | MATCH | block found in inputs/plan-wp6-resmoke-v5.md (190-194) |
| CLAIMS-TABLE glossary pointers (K1..K3B, SQLite, CrmIdOk, P checks, line 73/45/112/114/117) | glossary entries/section names | MATCH | each found by name |
| Q300 row numbers 6,16,24,27,30,62,71,78 | CLAIMS-TABLE rows | MATCH | all row ids exist; claim ids A-007, A-053, A-057, N-3 exist in RUNSHEET-WORDING.md |
| OWNER-STEPS 'A retake', row 7, V17, V18 | headings | MATCH | exist |
| REPORT:15 | 'deleted at clean-up' not found in take_check.sh or fill_flows README | MATCH | fixer's statement holds (no hit) |
| ID-VID-CHECK 50-57, 61, 62 | claim ids / row numbers / section names | MATCH on rows 50-57, 61, 62 checked by id; row 50 now cites check P4a | not every id in the rows was opened one by one |
| PLAN-4-NLITE-FROM-LEAD.md:82 | "single-flight" | MATCH | present on line 82 |
| mf-recovery.json (real-v5) | recovery flow | MATCH | checked against n8n-flows-real-v5 |

## Not fully checked (say so plainly)
- ID-VID-CHECK rows 17, 18, 25 and the remaining pointers in 50-62 beyond the id-exists check.
- REPORT lines 27 and 45 (45 is CANNOT-CHECK), FINDINGS rows 61, 110, 111 pointers.
- REPORT:151 stable phrases (RUNBOOK.md, TAKE-CHECKLIST.md, fill_flows README): fixer says "recheck after edits stop"; I did not re-grep them.
- QUESTIONS item 29 "ORDERS.md line 156 item 8": line 156 of ORDERS.md begins with "1 n8n_start.sh, n8n_kill.py ..."; I did not confirm that an "item 8" with "decision 1" is on that line. Treat as UNVERIFIED.
- The bulk of the roughly 5000 other references: sampled only.

## Next step
Fix the 4 MISMATCH rows (drop volatile line numbers, name rows/ids/phrases), reword the 3 soft ones, then re-run check_refs and ask for a short re-check of those rows. A separate note: fix-cite11 reports check_secrets FAIL with 3 hits (reviews/citation-r9.md:413, flow-check/evidence-f8-r8.md:55, flow-check/raw/test-take-check.txt:177); that is not a citation matter but it is still open and must be fixed or classified.
