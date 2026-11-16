# fix-q22-claims (2026-11-16, fixer; Q22 items 1 and 4, ORDERS.md 11:30Z)

## Failures and unfixed items first
- No failure. Both checks pass (below).
- Not changed on purpose (these count test results, they do not claim the CRM was called once): CLAIMS-TABLE rows B-051, B-119, B-120, B-185, B-195 to B-200 and the matching RUNSHEET rows B-051, B-101, B-195 to B-200, and the F-014 / T15 "0 CRM rows" lines. They are about our own load tests and failure runs, not the take. If the lead wants B-101 (lost = done with other than 1 CRM row or 1 mail) reworded too, say so.
- Verdict words: none changed (A-016, A-014, A-016a to A-016f keep their verdicts). Counts still 327.
- Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-q22c/

## CLAIMS-TABLE.md
- Start-here scene 2 and scene 3 lines: the CRM row is "display only, not proof".
- Scene 4 line: lead runs scene 4 with the take scripts; owner phone clock is the stopwatch; Q-A/Q-B answered for scene 4.
- Start-here new item 11 (front status line for this change).
- Row 8 / A-016 note and A-016 fix cell: say "1 mail in the mailbox"; CRM row shown, not proof.
- A-014 fix cell: 1 mail is the proof; no sentence says the CRM was called once.

## RUNSHEET-WORDING.md
- Status at a glance: new row for this change; N-5a/N-5b, Q-A, Q-B rows updated.
- Step 8 (scene 4): the lead stops and starts n8n; owner never does; phone clock is the stopwatch.
- Paste cells changed (no apostrophes): A-016b, A-016c, A-016e (no CRM row named), A-050b (doubled no longer lists a CRM row). Notes of A-016c, A-016e (via A-016c), A-016f area, step 10 and rule 2 reworded.
- Checks: check_runsheet_paste.py -> RESULT: PASS (158 rows). claims-count.py -> 327 unique, 87 to-do rows, 0 offenders.
