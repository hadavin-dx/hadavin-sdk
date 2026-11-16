# fix-q14-q17 (fixer, 2026-11-16; static work, nothing ran in n8n, Postgres or HubSpot; no commit)

## Failures and what is unverified (first)
- No command failed. Everything below is text and file moves; the counts come from one script, the patch check only proves the 4 patches still apply.
- UNVERIFIED: whether the lead meant F-001 to be re-rated Nit or removed from the 45 rows. I kept the row (45 rows stay) and rated it "Nit (dropped)", AFTER, with the DROPPED wording. If the lead wants 44 rows, say so.
- UNVERIFIED: I moved F-005, F-006, F-023 from BEFORE to AFTER ("for a later video"). The order only said re-rate to Nit; moving them is my reading, so the BEFORE/AFTER split depends on it (without the move: BEFORE 17 - 1 (F-001) = 16, AFTER 29).
- I did NOT cut the relayed numbers on PAGE-STATEMENTS statements (rows A-073b, A-076a, A-085, A-087a, B-032, B-056, to-do rows 3, 25, 27): they are page or planning text, not a caption or card. Say if they must go too.
- patches/archive-pre-decision1/ still holds old "+" lines with 60.x numbers (old history, not applied); left as is. Current patches F-003/F-004 only delete those numbers (grep "^+" for 60.8/61.9/60.1: no hit).
- Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-q14/
- Regenerating LEDGER-ROWS "the way it was done before": no generator exists in earlier logs (the file was hand-edited rows). I edited the 4 rows and the header by script and checked the row count by script (45; 5/7/33).

## Counts (one recount, tools/count_findings.py, new file)
| | old | new |
|---|---|---|
| Blocker | 8 | 5 (F-002, F-003, F-007, F-031, F-037) |
| Major | 8 | 7 |
| Nit | 29 | 33 |
| rows | 45 | 45 |
| BEFORE | 17 (8/8/1) | 13 (5/7/1) |
| AFTER | 28 | 32 |
Alternative if F-011 and F-041 move AFTER: old 8/6/31, BEFORE 15 -> new 5/5/35, BEFORE 11, AFTER 34.
Re-rated: F-005, F-006 Blocker->Nit; F-023 Major->Nit (all "for a later video"); F-001 Blocker->Nit (dropped). F6B-AUDIT (own 17 rows, not in the 45): F6B-01 Blocker->Nit, F6B-13 Major->Nit; its take counts 1 Blocker/2 Major/2 conditional Major/1 Nit-maybe-Major/11 Nit -> 0/1/2/1/13.
Checks (own rc): python3 tools/count_findings.py rc 0 (old backup file reproduces 8/8/29, 17/28); LEDGER-ROWS row count by script 45, 5/7/33.

## Files changed
- FINDINGS.md: 4 rows re-rated and moved into the AFTER block; counts table, paragraph, F-011/F-041 alternative, summary lines 9 and 12, scenes paragraph, BEFORE line; F-001 fix cell marked DROPPED.
- LEDGER-ROWS.md: header counts, rows F-001, F-005, F-006, F-023.
- REPORT.md: Result and disagreement (4) lines.
- FIX-PLAN.md: header counts, item 1 DROPPED, item 7 list, "Lead answers applied" counts plus one sentence "T19 and T20 run on the PATCHED copy (F-002 and F-008 applied, one sha named once)" (Q17-4; no text said "unpatched first" in FIX-PLAN), check_patches PASS 4.
- F6B-AUDIT.md: F6B-01, F6B-13, summary count 3.
- RUNSHEET-WORDING.md: A-017b, A-019b, A-051b, A-081b paste cells = DELETE, marked "CUT by decision 1" (rows kept); A-081a paste has no K1 numbers; A-019a note; scope note line 11.
- CLAIMS-TABLE.md: A-017, A-019, A-051, A-081 fix cells; D1, D2 lines; to-do rows 22 and 28. Verdict cells untouched.
- patches/F-001-one-ddl.patch moved to patches/archive/ (not deleted); patches/REGENERATED-NOTE.md updated.
- OWNER-STEPS-q16-rows.md: new row 4 (one made-up lead through the real HubSpot trial; "lead verifies at re-pin"); closing line says four rows.
- QUEUE.md: F3 FROZEN, F8 PARKED, F2 and F6 PARKED. QUESTIONS.md: Q13 to Q17 headings marked ANSWERED 2026-11-16 with pointer to ORDERS.md.
- New: tools/count_findings.py, lanes7/evidence-q14-q17.txt, this log.

## Commands and rc
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: PASS, rc 0 (157 rows, same as before)
- python3 claims-count.py CLAIMS-TABLE.md: rc 0; verdicts unchanged: UNSUPPORTED 29, SUPPORTED 124, UNTRACED 51, OVERSTATED 54, RELAYED-ONLY 69 = 327; to-do rows 87; offenders 0 (no counts text to change)
- sh handover/flows-audit/tools/check_patches.sh (from repo root): PASS 4 patches, rc 0 (was 5); raw in lanes7/evidence-q14-q17.txt
