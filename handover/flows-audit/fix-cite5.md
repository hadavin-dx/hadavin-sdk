# fix-cite5 log (fixer, 2026-11-16, from reviews/citations-sweep2-r1.md and drift-008.md). Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-cite5/ (9 files). Nothing ran in n8n; made-up data only.

## Unfixed or for the lead first
1. Lead-owned, not edited: QUEUE.md:8 and ORDERS.md:20 still say executions "deleted at clean-up" (untagged; SUPERSEDED by Q19-1/Q21). STATUS-BOARD.md:29 still holds an old finding count untagged.
2. Not editable by me: fix-ans28.md cites "Q22-1", "Q22-4", "Q22-5" meaning the list now headed Q22b; QUESTIONS Q22b heading says so. CLAIMS-TABLE.md and RUNSHEET-WORDING.md "Q22 item N" cites mean the FIRST Q22 (take-day read); left as is.
3. ROLE COUNT stays undecided (ROLES parked): the three numbers are recorded in the F-010 row.
4. PLAN-4:106 "up to 3 HubSpot contacts archived at the end": added as FINDINGS NOT COVERED item 29 (take scripts unseen; lead verifies at re-pin).

## Fixed
- QUESTIONS:5 SUPERSEDED tag (Q19-1, Q21). EXCEPTIONS:8 now "Rows 1 and 3".
- F-010 row holds the role count once (two / three plus n8n's own / four plus one table-owner); F-041 points to it.
- FINDINGS item 27: line ranges replaced by "historic scope" and row ids.
- F6B-AUDIT and fix-f6b-r2: F-031 cited by row id (line 107 now).
- QUESTIONS: second Q22 renamed Q22b, first marked "first of two"; FIX-PLAN Q22-3/4/5 cites say "first Q22 list".
- fix-sweep2: dated correction note appended (Q20-4 answered; Q22b).
- Coordinator extras: FINDINGS F-018 and LEDGER-ROWS F-018 DESK_ALERT_TO answered; LEDGER F-013 status ACCEPTED (severity unchanged); REPORT "deleted at clean-up" tagged SUPERSEDED; REPORT unverified line says "in the take's own database".

## Checks run
- tools/count_findings.py: 45 rows, 5/7/33, BEFORE 13, AFTER 32.
- check_patches.sh from repo root: PASS 4 patches.
- FINDINGS vs LEDGER-ROWS: 45 rows each, same 45 ids as sets (order differs: FINDINGS groups by severity).
