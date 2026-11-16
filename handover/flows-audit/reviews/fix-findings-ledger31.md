# Fix report: findings ledger, round 31 (fixer, non-security, round 2 of 2)

Scope: FINDINGS.md and LEDGER-ROWS.md only, ten rows: F-002, F-003, F-007, F-031, F-037, F-008, F-011, F-018, F-029, F-041. Severity and status unchanged (5 Blocker / 5 Major / 35 Nit, all OPEN). RUNBOOK.md, QUESTIONS.md, TAKE-CHECKLIST.md and FIX-PLAN.md were not touched. Nothing committed.

## Gaps first (what is NOT done or NOT verified)

1. Nothing was run in n8n or on the real take folders. Every pass block was syntax-checked with `bash -n` and, for the changed ones, run against made-up folders; none ran on the real tree.
2. No row can close today. Inputs that no file holds (LEAD FILLS or NOT WRITTEN): the export command, the take folder path and new folder name (Q31 item 59), the mailbox count command, WAIT_S, the owner sheet path and allowed-places list (Q31 item 137), the answers of Q31 items 10, 18, 26, 31. Each row now says this first (STATE TODAY).
3. PROPOSED Q31 items N1 to N4 are proposals written inside the FINDINGS rows only. They are not in QUESTIONS.md (out of scope for me); the studio lead must add them.
4. "$B still set" (a RUNBOOK phrase named in a reader report) was not found in FINDINGS.md or the other in-scope files; the RUNBOOK is out of scope, so it is not fixed here. Someone with RUNBOOK rights must check it.
5. The bash -n sweep covers only the 15 pass-line command spans my filter could recognise as commands. The long blocks of F-002 (T21), F-003, F-008, F-037 and F-029 were also run on stubs earlier in this session; the remaining shorter commands were not each extracted. This is a gap in coverage, not a known failure.
6. Whether the n8n export keeps the words PG_CREDENTIAL_ID and others is UNVERIFIED; the F-029 block fails loudly (never a false PASS) if it does.

## Per finding (all fixed in the rows; none declined)

Common to all ten: a STATE TODAY paragraph at the front of the fix cell (what can print today, which inputs are LEAD FILLS or NOT WRITTEN, default runner named or "nobody"); the rating basis stated once; one closing test list, stated once, in the status cell; undefined terms defined in a words line; the LEDGER-ROWS fix cell kept equal to the FINDINGS fix cell.

- F-002: five inputs named first; default runner the studio lead; T21 now sets S3OK/S4OK flags and the final block can pass only if both were set in the same shell; a separate LOGIN BACK block so no FAIL line means success; the closing list names four tests (T19, T19H, T20, T21); VARIABLES setup made one clean two-line form with a guard.
- F-003: narrow-route clause, ORDER 007 and line 90 defined; BLOCKED UNTIL (1) covers blocks 2, 3 and 4; F003-4 rewritten without pipes using anchored `grep -c` counts (the earlier pipe version split the row into 13 cells; fixed and re-checked).
- F-007: STATE TODAY (F-004 patch first); both blocks plus the re-read line in the PASS LINE; F007-1 matches the file name only, not line numbers; lane3, L3-5, naming table defined.
- F-031: PROPOSED Q31 items N1 (PGSELECT_PW) and N2 (KEYS31) with the typed commands; one rating basis; duplicated PGCONN paragraph removed; "four F-003 checks"; the "closed as disclosed" label explained.
- F-037: only the CONTROL lines can print today; export command NOT WRITTEN, PROPOSED N3; default runner nobody; CONTROL-NAMES prints `grep exit` and requires 0; path written `scripts/n8n_api.py`.
- F-008: which command writes $LOG stated; block also requires exactly one `FINAL: take_check exit status 0.` line and no line starting `!!!`; "KNOWINGLY FALSE AS ENGLISH" replaced by plain words.
- F-011: three-decision list and NOT WRITTEN inputs first; evidence (a) stated as the same run as F-041's, no second proof; ORDER 004, Reading A, UNANSWERED, NEEDS LEAD, need_set, EXCEPTIONS.md defined.
- F-018: Q31 item 31 answer first (recommend OUT); step 7 check pointed at a real command; C18 exactly-1 explained; N4 and step 10b defined.
- F-029 (this session's last two rows): STATE TODAY with five missing inputs; `scripts\n8n_api.py` corrected to `scripts/n8n_api.py` (three places); BLOCKED UNTIL numbering and LEAD words defined; closing list (`F029 FILLED PASS`, `F029 EXPORT PASS`, `F029 CONTROL-FLOWS PASS`) in the status cell. The chk29 block was run on made-up folders (control folder = copies of the real-v5 files, clean folders = empty JSON stubs) and printed all three PASS lines.
- F-041: STATE TODAY with the two times explained (07:00Z inputs due, 14:00Z GO test) and Block R7 named as the only copy of the grep; `NOT A PASS BY COMMAND` renamed `NEEDS-READ` everywhere so no result line contains the word PASS unless it is a pass; STATUS MOVE now points to the closing list in the status cell (F041-R7, F041-CTRL, F041-OWNER, JUDGED row 7, or the downgrade route); $ENVSH, $OWNER_SHEET, need_set and the numbered conditions defined.

## Command output (final run, 2026-11-16)

- compare14.py: `45 45 differences: 0`
- count_findings.py: `sev {'Blocker': 5, 'Major': 5, 'Nit': 35}`, 45 rows
- cell counts: every F- row has 10 cells in FINDINGS.md and 9 in LEDGER-ROWS.md (no row split by a stray " | ")
- check_refs: PASS 5190 references (exit 0); check_names: PASS 655 rows (exit 0); check_secrets: PASS 0 hits in 2933 files (exit 0); check_counts: PASS 52 files / 655 nodes (exit 0)
- ruff format --check: 1058 files already formatted (exit 0)
- bash -n on 15 extracted command spans of the ten rows: 0 failures
