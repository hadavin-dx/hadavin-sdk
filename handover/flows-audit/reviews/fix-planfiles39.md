# Fix report planfiles39 (fixer; edits only RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md; nothing was run in n8n, Postgres or HubSpot)

## Failures and doubts first
1. SCRATCH ACCIDENT: my first edit script in the SHARED scratchpad was overwritten by another agent's QUESTIONS.md editor, so my first invocation ran that script (it printed "FAIL 0 1 | 11 who applies F-031..." and changed nothing in my files; md5 of my three files matched backups). QUESTIONS.md has mtime 19:06:33, the same instant as that other script, so most likely its own agent wrote it; I cannot rule out my accidental run touched it. Lead: diff QUESTIONS.md against its last known state.
2. Not verified by running: no new command was executed on the real tree. Only `bash -n` and a small positive test of the Block R3c process search (it found a planted process named like the pattern).
3. `bash -n`: all 26 TAKE-CHECKLIST fences, 2 RUNBOOK fences pass (also before my edits). My inline-span extractor gave 7 false alarms (prose between mis-paired backticks, not commands); the real command spans passed.
4. FIX-PLAN item 8b says it "uses the same text" as Block R7; I did NOT add the new R7 control lines there (the item points to TAKE-CHECKLIST). Lead: confirm that pointer is enough.
5. Not edited, lead must align: QUESTIONS.md Q31 items 50, 53, 55, 56 (older due times), ORDERS.md, owner sheet.

## Verification output (last lines)
check_refs: PASS 5193 references | check_names: PASS 655 rows | check_secrets: PASS 0 hits in 2873 files | check_counts: PASS 52 files / 655 nodes | ruff format --check: 998 files already formatted | md5 FIX-PLAN 37-84 and TAKE-CHECKLIST 8-55: both 929febdfab0142f49dfd50627d87285d (block changed: row 4a, owner credential row, R3 exclusion, 74-min default, step 14 (f) wording).

## TAKE-CHECKLIST r40
- B1 FIXED: downgrade of F-011/F-041 = lead changes ledger flag `counts` to `lead decides` before Block R6, plus JUDGED row 6 line with the same evidence file. Edited row 6, row 7, text after R6j, Inputs item 21, clock line (both files).
- M2 FIXED: one order (read first, trusted only after control); check 5b now Tue and Wed.
- M3 FIXED: R6 captures ledger_check exit, stops on Python error, no-id plus non-zero exit = NOT PASSED; pass cell updated.
- M4 FIXED: `columns-control-ok` (Blocker/Major rows above 0 and every status cell valid = rows).
- M5 FIXED: R7 Part A planted-file control, Part B requires grep exit 0 and non-empty unfiltered list.
- M6 FIXED: R3c pattern from new `$MUT_NAME` (placeholder row), grep exit 0/1/other handled, ps must list this shell.
- M7 FIXED by statement: R1/R3/R3L/R3n/R3c run Monday night or before 03:30Z, not in clock block.
- M8 FIXED (item 32: step 7 only on route B).
- M9 FIXED: Tuesday re-smoke uses Block R5e; script needs reviews for GO row 2, first run is Wednesday rehearsal.
- M10 FIXED: table-file run renamed (0); row 5 now (a) to (d).
- M11 FIXED: "two commands"; gate items named per RUNBOOK step 24 ((e) = HubSpot search).
- M12 FIXED: rows added for KEEP, REFUSAL_LINE, JUDGE_ITEM, PGHOST/PGPORT/PGPASSFILE, MUT_NAME; PGCONN = PGCONN_TAKE; "eight names"; BRANCH wording. Contested in part: none.

## RUNBOOK r40 (B1, M1-M18) and plan-files r39 (P1-P7, labels)
Fixed in the earlier checkpoint (29 RUNBOOK pairs, 25 FIX-PLAN pairs plus block edits), see the list in my handback. Contested: M12 (stepjudge skeleton already guarded; guards and note added anyway); P5 (RUNBOOK section 10 (h) already fixed WAIT_S at Tue 08:29; resolved by naming the two mailbox commands); section 8's 18:29Z chain is lead-owned and unchanged.

## Lead decisions (defaults written as "lead to confirm")
1 credential ask Wednesday, earlier made-up writes allowed under ORDER 037 item 3; 2 Tuesday positive control required (74-min latest starts 06:37 / 06:07); 3 Block R3 and siblings outside the clock, Monday night or before 03:30Z; 4 one take limit, start by 12:00Z Mon 23 Nov, 18:29Z money stop; 5 no second n8n for the take; 6 recording-ready message sent after 12:00Z too, owner told the time; 7 no same-day retake; 8 downgrade = flag change to `lead decides`; 9 Tuesday re-smoke uses Block R5e; 10 `$MUT_NAME` supplied by lead.
