# fix-findings-ledger24 (2026-11-16): round 25 reader M1 to M5

Editor: single editor of FINDINGS.md and LEDGER-ROWS.md; new file ledger-history-cells.md. Static; nothing run against n8n, Postgres or HubSpot; made-up data; no secret printed. Edits were exact-string replacements, each asserted at its real count in both files (same text in both). Reader words were checked against the row text first. Not committed.

## What is uncertain (first)
- No new command was run; the new `need_set` prefixes and the second-file grep are typed text only. need_set exists only after shas.env is loaded (it is defined there).
- M5: I took the smaller option (header corrected), not the move of SUMMARY to the front; the cells stay 8k-30k characters long, so the cold-reader load complaint is only partly addressed.
- Not edited (not my files): RUNBOOK.md, TAKE-CHECKLIST.md, QUESTIONS.md (item 82 is cited, not changed).

## Per item
| Item | Reader right? | Done | How checked |
|---|---|---|---|
| M1 F-002 T21 second way | Yes. The closed-port way leaves the role NOLOGIN. | Done: the "second way" is now SECOND_ADMIN (Q31 item 82); closed port is stated as NOT a recovery; new HARD PRECONDITION before the pre-check of (2): do not type the first command of (2) unless SECOND_ADMIN is named and shown to work, else T21 does not run and counts as not passed; the "if it stops" pointer in (5) names SECOND_ADMIN. | Read row text before and after; count asserts |
| M2 F-011 runner question | Yes. | Done: (c) now says the runner question is Q31 item 136 (due Tue 17 Nov 03:00Z (08:30 IST), one message with items 10 (a) and 112); "answers the runner question" became "answers item 136". | Read QUESTIONS.md line 731 |
| M3 F-011 setup commands | Partly. The F-011 PASS LINE does have a VARIABLES FIRST line (loads shas.env), so "no VARIABLES FIRST" is wrong; the setup block itself had no guard, no pg-secrets.env note, and N8N_* undefined: right. | Done: a "where each variable comes from" sentence (PGADMIN, TAKE_DB in shas.env; PGADMIN_PW and N8N_PW in $KEEP/pg-secrets.env; N8N_ROLE, N8N_DB names in shas.env; the three N8N_* still NOT WRITTEN, LEAD FILLS); the four psql commands each start with `need_set <their names> &&`; the reason (empty -U falls back to the OS user, empty password prompts) is stated. | Read need_set text (RUNBOOK 173) |
| M4 F-041 downgrade evidence | Yes. | Done: (a) now tests and greps both VIDEO-RUNSHEET.md and n8n-flows/PAGE-STATEMENTS-V4.md (prints FILE2-OK too) with a positive control for the second file; "downgrade route is the only one left" reworded: also needs item 10's answers and under its default no downgrade counts, GO row 7 NOT PASSED (QUESTIONS.md 732). Same (a) command also sits in F-011, so I changed it there too (same class). | Compared with Part A text and QUESTIONS 732 |
| M5 order and history | Yes. | Done (smaller option): LEDGER-ROWS.md line 15 corrected to the real order (PASS LINE, WHO NEXT, WORDS USED, then SUMMARY); the 10 SUMMARY labels in each file no longer say "moved to the top". Six round-history sentences moved to ledger-history-cells.md (F-002 closed port, F-002 older F-002b text, F-003 item 111 history, F-003 T20 round 21, F-031 round 21; F-011 "not yet in Q31"); each live rule kept in the row. No severity, count or verdict changed. | Count asserts; checks below |
| Notes (F-018 GO row 6 Tuesday, REPLACE_ME loader Nit) | Not edited: Nit-level, second grep controls, Q31 item 31 open. | Not done on purpose | |

## Check output (from handover/flows-audit)
- count_findings: rows 45 unique 45; Blocker 5/0 (5); Major 5/0 (5); Nit 1/34 (35); all BEFORE 11, AFTER 34.
- compare14.py: `45 45 differences: 0`.
- check_refs PASS 5182 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2812 files; check_counts PASS 52 files / 655 nodes; ruff format --check: 938 files already formatted.
