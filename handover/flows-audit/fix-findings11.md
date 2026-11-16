# Round 11 fix log (reviews/findings-r11-commands.md: M1, N1-N5)
Static; edited FINDINGS.md, LEDGER-ROWS.md, patches/F-004-page-statement-17.patch only. Backups: scratchpad bak-f11/. Same text in FINDINGS and LEDGER-ROWS unless noted.
- M1 (true): PAGE-STATEMENTS-V4.md NAMING line (:150) carried the false K3B sentence and lane3 names as a patch context line. Fixed in the F-004 patch: that line is now a '-' line plus a '+' line (this page's names only; K3B = mail not yet delivered, K3 = mail delivered). `git apply --check` on a scratch copy of the page (exit 0) and a real apply: no "killed after the mail left" left in the patched copy. F-007 text: the allowed list is now REPORT.md:49 only after F-004; page :150 and :153 allowed only until F-004 is applied; plain statement that two false sentences stay if F-004 is not applied. F-004 row mentions the reword.
- N1 (true): F-008 pass (2) now uses -H.
- N2 (true, not edited by me): TAKE-CHECKLIST.md stale line numbers (GO row 7 is at 155 not 145; Block R7 starts at 250, pass line 257 not 226-236). Owner of that file must match by heading.
- N3 (true): F-031 pass (2) counts state = 'review' only; unknown/failed are alerted (build_mainframe.py:105).
- N4 (true): F-018 control notes the sender address (fromEmail, mf-recovery.json:177) may be the same mailbox; read the hit, toEmail only.
- N5 (true): F-011 downgrade (b) says the pattern matches any one line, lead reads the hit; PGADMIN needs CREATEROLE with admin option (Postgres 16+), in the variables note (FINDINGS.md line 22) and in the F-011 row (both files).
Not done: TAKE-CHECKLIST.md, FIX-PLAN.md untouched by order; F-007 table text still LEAD FILLS.
