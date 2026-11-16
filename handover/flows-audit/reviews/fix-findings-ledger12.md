# fix-findings-ledger12 (round 12, non-security path): fixes for reviews/findings-ledger-reader-r12.md
Fixer: the audit (cloud session flows-audit). Static work only: nothing ran, no network, made-up data. Edited: FINDINGS.md, LEDGER-ROWS.md (the F-003 and F-011 fix cells and the F-008, F-018, F-031, F-002, F-041-area cite cells were changed with identical text in both files); new: this file. No severity, no status and no count changed (45 rows, 5 Blocker, 5 Major, 35 Nit, BEFORE 11, AFTER 34). QUESTIONS.md, RUNBOOK, FIX-PLAN, TAKE-CHECKLIST were read, not edited.

## Failures and uncertainty first
- Finding 3 cannot be FIXED in the sense of making fix A runnable: the Postgres version of T7b and an import command for the 4 take flows do not exist anywhere in the tree (grep result below). I wrote that plainly and removed fix A from the minimum set; the downgrade route stays. TAKE-CHECKLIST.md (GO row 7, Inputs item 22) and FIX-PLAN item 8 still describe fix A as a live route; their owners must align them (not edited here).
- Line-number cites: I converted every cite to ORDERS.md, TAKE-CHECKLIST.md, N8N-START.md, DESIGN-A-README.md, mf.py (T7b), n8n-owns-vs-desk-owns.md, fill_flows/README.md and lanes7/N7-new-findings.md into heading or section cites (a grep for those files followed by line/lines/colon and a number now finds nothing in either file). I did NOT change line cites into frozen evidence files and patches (for example build_mainframe.py:105, PAGE-STATEMENTS-V4.md:150, VIDEO-RUNSHEET.md:24, mf-recovery.json line 177, patch lines 17/84/106): they point at frozen demo code and patch positions that no fixer of this round edits, and a heading cite does not exist for a code line. This is a scoped decision; if the reviewer wants those changed too it is a further sweep.
- Not run: nothing in n8n; the F-011 grep for T7b/import was a text search only.

## Status per finding
1. FIXED (reviewer right). New READ-FIRST LIST (ten project words: take and NO-GO, studio lead, Q31, GO test and GO row, re-pin, ledger row, T19-T21 with F-002b and SECOND_ADMIN, $REPO, WEDNESDAY CLOCK, GRACE PERIOD) placed directly above the first paragraph that uses them; line 2 has a pointer to it and to the full section 'Words used in this file'; 'defined in the words list' for studio lead now says where. The reviewer's lines 80-128 were about 15 lines off in the current file (the words list is a section, found by heading).
2. FIXED (reviewer right). Inputs row 4: TAKE-CHECKLIST.md Inputs item 22 and its 'Needed by' paragraph both say 03:00Z (read); the invented '04:00Z by Inputs item 22' is gone and the cell now names the one real tension (03:00Z route time against 'at the re-pin' in the F-011 row). Cites by line for check 12 (said 359) and Inputs item 12 (said 70) became heading cites; the same sweep is described above.
3. FIXED IN WORDING (reviewer right, cannot be made runnable now). Grep result: T7b in handover/demo/n8n-mainframe/mf.py scans n8n's SQLite folder (the files under n8nhome); no other file adapts it to Postgres; the only import lines in the tree are a general loop in inputs/plan-wp6-resmoke-v5.md step 2.4 (the re-smoke, not GO row 7, not run); the runner question is not yet in Q31. Written in the F-011 cell as 'STATE OF FIX A ON 2026-11-16' (both files); F-011 summary and who-list (6) say it; the minimum set item (2) at the top is now the downgrade route only (fix A would return only if the studio lead first writes both pieces and answers by 03:00Z); the causes bullet, decision-table row 10 (a) and the NEW runner row carry the same sentence. Plain-wording change, not a severity change. The old text in paragraph 'THE ANSWERS IN TIME ORDER' still lists the 03:00Z answers (the question can still be asked).
4. FIXED (reviewer right). GRACE PERIOD is defined once in the first paragraph: the smaller of 30 minutes and what is left of the shared cap (24 minutes Tuesday, 28 Wednesday, Q31 item 51); a Wednesday grace period from 05:45Z (11:15 IST) ends at the latest 06:13Z (11:43 IST), not 06:15Z. Rows for items 59, 50, 54 and the WEDNESDAY CLOCK sentence now say that (the item 82 row has no grace wording of its own, so the reviewer's 'item 82' only means the definition). The other '30 minutes' texts (the F-002b slot of 30 minutes) are a different meaning and were left.
5. FIXED (reviewer right). One plan in every place: apply at RUNBOOK step 4a, re-read in step 14, recorded by Tue 17 Nov 08:29Z (13:59 IST), before the 14:00Z GO test; Wed 18 Nov 06:00Z (11:30 IST) is only the fallback last date (borrowed from Q30 item 2, which names F-007 and F-031 only). The default of Q31 item 11 (the studio lead applies run-sheet text including F-003) governs step 4a because item 11 is due 07:00Z, after step 4a at 04:16Z. 'Still open at 14:00Z' is now conditional (only if the plan is not carried out). Changed in: the causes bullet, minimum set item (5), WEDNESDAY CLOCK, inputs row 10, decision-table row 11, F-003 cell parts (1), (4) and the Tuesday/Wednesday paragraph (both files).

## Proposed Q31 text
No new Q31 item is needed beyond the F-011 runner item already proposed in reviews/fix-findings-ledger11.md. One addition to that item (lead to confirm, not in QUESTIONS.md): 'Also: who writes the Postgres version of T7b and the import command for the 4 flows of real-v5 before Tue 17 Nov 03:00Z (08:30 IST)? Without both, fix A is dropped and only the downgrade route (items 10 (b), (c) and 18) can clear GO row 7.'

## Raw output (run from handover/flows-audit)
```
$ python3 -I compare.py FINDINGS.md LEDGER-ROWS.md      (script text in reviews/fix-findings-ledger11.md)
45 45 differences: 0
$ python3 -I tools/count_findings.py
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
$ python3 -I tools/check_refs.py
PASS 5171 references
$ python3 -I tools/check_names.py
PASS 655 rows
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2674 files
$ ruff format --check .
822 files already formatted
```
check_secrets did not fail on reviews-of-core-patches/patch-copies/README.md in this run.

Files: /home/user/hadavin-sdk/handover/flows-audit/FINDINGS.md, /home/user/hadavin-sdk/handover/flows-audit/LEDGER-ROWS.md, this report. No git commits. EGM skipped for the executed edits: the lead runs the EGM review of the result; this fixer cannot invoke it from here. Own token use: not measured.
