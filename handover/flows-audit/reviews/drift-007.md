# Drift report ORDER 007 (egm:egm-drift-report), 2026-11-16 08:50 UTC / 14:20 IST
Scope: FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, LEDGER-ROWS, patches/, lanes7/ after review round 2. Static. A python script counted rows and compared FINDINGS with LEDGER-ROWS; I read its output and the grep hits below. Raw script output was not saved as a file.

## Counts
- FINDINGS.md: 45 rows, every row has 10 cells; 8 Blocker, 8 Major, 29 Nit; BEFORE 17, AFTER 28. Matches the expected counts.
- LEDGER-ROWS.md: 45 rows, 9 columns, severities identical to FINDINGS, no extra or missing ids.

## Stale-text search (what I looked at and decided)
- "F-040": 4 hits in FIX-PLAN, FINDINGS (header, F-014) and LEDGER-ROWS (F-014, F-035). Each says "merged into F-014". Intentional, no drift.
- "item 10": 1 hit, lanes7/N7-verdicts.md:124, quotes a reviewer's own item number. Not drift.
- "rung": 13 hits in lanes7/N7-verdicts.md only. Lane working file; the audit documents use "fix kind". Left as is, not fixed: the word is not read by the lead's decision documents.
- resolve-007-r1.md round 1 table shows the round 1 counts (9 Major, 28 Nit); its round 2 addendum states the current counts. Intended.

## Not checked
Anything that needs n8n, Postgres or HubSpot (UNVERIFIED in FINDINGS); per-node tables in FLOWS-AUDIT.md; ledger_check (does not exist in this repository).
Drift found that needs a fix: none.
