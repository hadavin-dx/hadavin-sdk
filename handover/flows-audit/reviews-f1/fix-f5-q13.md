# fix-f5-q13 (fixer, text only)
Source: ORDERS.md ANSWER Q13 (10:23Z); CLAIMS-TABLE.md rows B-067, B-091, B-215, row 33. Backup: scratchpad rw-q13/RUNSHEET-WORDING.md.
Failed on the way (fixed): first edit hit the wrong cell (overwrote the original-quote cell); restored from backup and redone. Checker then FAILED on apostrophes in paste cells (B-067, B-091); changed to "archive_contacts is no"; re-run PASS.
Applied in RUNSHEET-WORDING.md: rows B-067, B-091, B-215, B-215b (paste text and note cell, round 7 replaces the round 6 HELD text); P4c summary line 59; line 295; section 6 counts: "(73 in round 6)" -> 80, UNTRACED (69) -> 50 with 43 having no row (checker's current output).
Not checked: take scripts absent; text is the lead's statement, lead verifies at re-pin. B-215 and B-214 remain UNTRACED. Row B-214 (NO PASTE) left unchanged.
Checker: python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> "RESULT: PASS", rc=0.
