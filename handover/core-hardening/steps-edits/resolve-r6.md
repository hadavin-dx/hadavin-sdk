# C4 resolve pass, round 6 (money, secret, delete and data-leaving paths: no round cap), 2026-11-16
Status: resolved (headless, every PROPOSE FIX accepted). Only `EDITS.md` changed (the round-5 file is kept as `EDITS.round5.md`), plus this log, `checkpoint-r6.md` and `resolve-r6-check-output.txt`. Inputs untouched. Nothing run except text and count checks; no code, network, spend or commit. The result of round 6 is NOT reviewed yet.

## Failures and gaps first
- Nothing contested; no finding left silently open. Items that stay open and why: the "no paid model call" mechanism for the preparation test contact is UNVERIFIED (no input shows it); E-12's wording, the meaning of "flow rehearsal" (D12) and EL-1 to EL-7 need the lead's confirmation (FOR THE LEAD TO CONFIRM d, g); NOT DECIDED 1 to 7 need the lead or the owner (who and where recorded are now stated); 11 rows are on Hold behind gates G1 to G4 and 1 is Conditional.
- Changed my own approach: round 5's table cells with inner backticks were ambiguous. Round 6 moves every old and new text into a four-tilde block, one block per row, and keeps only an index table.
- Decision made by me, to be confirmed: E-36 default is the wider-wording text W (smaller claim), so nothing depends on an unanswered question.

## Findings -> fix -> check
| finding | fix | check |
|---|---|---|
| design M1, R1/R2 crash-safe | R2 drops only the narrow "count by a different database user" item; "crash-safe" stays forbidden while plan row NC (line 477) has uncovered windows; R1 needs DM PASS and (E passed or E2 passed) | read plan lines 14, 477, 505 |
| design M2 E-12 | message must say both tests ran, where the result is, that independent reviewers read it; "passed" defined; crash check exception | text vs plan lines 14, 505 |
| design M3 E-48 | no guessed path; assistant's copy goes with the take folder; owner's own copy deleted via step 22 item 6 (`shred -u`, else `rm`); conditional on ND 7a | text vs AGENT-SCOPE line 13, step 22 items 1, 6 |
| design M4 E-11 | no "no paid call" promise as fact; stop-and-ask sentence; marked UNVERIFIED; ND 6 | UNVERIFIED stated |
| design m1 | preparation contact deleted before the take (E-04 follows E-11) | text |
| design m2 | E-03 flat claim removed; Docker Desktop and firewall rule in own sentences, none planned | plan 102, 506 |
| design m3 | E-01 "Edited ... still to be checked" | grep "Re-checked": 0 in owner texts |
| design m4 | E-31 "is planned to prove" | text |
| design m5 | pointers renumbered (E-07 ND5, E-09 ND4 and ND1, E-16 ND3, header ND3); confirm letters a to g without gaps | read |
| design m6 | E-16 and R-rules; Hold/Apply status per row; E-36 default | counts |
| design m7 | one word each: database server, n8n's own database, the take's database, container; "schema" explained in E-31 | read |
| design m8 | E-26: one Postgres server is lead decision 10, only saved runs is the owner's | read |
| naive B1 | E-36 text W (default) and text N | both in the row |
| naive B2 | E-39 text per answer and "not applied tonight" | both in the row; Hold G4 |
| naive B3 | gates G1 to G4 name who opens them and the evidence; every row marked; recount | counts below |
| naive M1 | stale NOT DECIDED pointers fixed | read |
| naive M2 | E-31 uses M-1 (as DECISION-one-store names it); F-01 stays the contact delete (E-40, E-44) | read |
| naive M3 | E-19 plan file name removed | grep "plan-wp6": 0 in owner texts |
| naive M4 | "rehearsal" split into stand-in test (D8) and flow rehearsal (D12), defined in E-03 and E-26 | grep owner texts: "rehearsal" only in E-03, E-11, E-12 |
| naive M5 | E-11 "lead" for the enquiry is "test contact"; E-01 says what "the lead" means | read |
| naive M6 | "different database user" is the one phrase for the count (E-15, E-18, E-31, E-36) | grep "login" in owner texts: 0 |
| naive M7 | where crash results are recorded (INDEX of evidence-2) and who judges (independent reviewers) stated before R1 to R5; R5 timing | read |
| naive M8 | E-01 wording, E-03 claim limited, E-11 one real-account run named, E-12 gives a written statement to check, E-20/E-21 "trial, left items open", E-37 key not listed as plainly done | read |
| naive M9 | E-24 "count: 17 live items; item 10 was removed, so the numbers run 1 to 18" | read OWNER-STEPS lines 178-193 |
| naive M10 | quoting convention (four-tilde blocks); E-06 and E-33 punctuation exact | verify script parses all 46 rows |
| naive M11 | E-48 plain words | read |
| naive m1 | E-11 old text now includes the failed-check sentence | verify script |
| naive m2 | E-33 final full stop | read |
| naive m3 | E-40, E-44, E-45 gated (G1) | status |
| naive m4 | E-17 changes the post, E-22 the status list, R1 links both | why cells |
| naive m5 | branch names explained in E-02; "fix round" explained; SQLite and mode 600 explained | read |
| naive m6 | container, firewall rule, Docker Desktop explained in own sentences (E-03) | read |
| naive m7 | EL-1 to EL-7 listed in one paragraph, check item g; letters a to g | read |
| naive m8 | E-48 says the file numbers its items and names the part S9-3 | read |
| naive words / ND clarity | jargon explained or removed in owner texts; ND 1 to 7 each: who, options, default, record line | read |

## Checks by script (raw output: `resolve-r6-check-output.txt`)
`verify6.py` (in the scratchpad) parses `EDITS.md` itself (not the build data): 46 rows parsed; 47 old texts (E-13 has two) each occur exactly once in their input file, on the stated line; 0 failures; 0 overlaps between old texts on one file; all 34 Apply-now rows applied to scratch copies of the inputs without conflict (E-36 with text W); old and new texts have no leading or trailing space; banned vendor strings: none; secret patterns: none; the personal folder path is no longer copied (E-01 old text shortened). Counts: Apply now 34, Hold 11, Conditional 1 = 46; OWNER-STEPS 29, AGENT-SCOPE 13, DECISION-one-store 4; types STALE 15, UNCLEAR WORD 6, MISSING STEP 10, CONTRADICTION 12, DEFERRED 3.

## Not checked
No code, smoke evidence, click path or `review-codebase-1.md`; plan only on named lines; the new owner texts have not been read by a stranger; the Hold rows' texts are not applied-tested; the model-call bypass, the start-script options (ND 1) and the meaning of "flow rehearsal" are unproven.
