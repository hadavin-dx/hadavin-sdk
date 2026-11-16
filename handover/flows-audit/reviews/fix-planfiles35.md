# fix-planfiles35 (round 35, fixer on RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md)
Real clock at start: 2026-11-16T18:20Z (23:50 IST). Nothing was run on n8n, Postgres or HubSpot. Not committed.

## NOT done or uncertain (read first)
1. Clash left for the lead: QUESTIONS.md Q31 item 50 still says WAIT_S is due Wed 05:45Z and item 51 (c) is not edited; I did not touch QUESTIONS.md. The plan files now say Tue 08:29Z (13:59 IST) (RUNBOOK section 10 M7 (h)).
2. Reader item 4 changes a due time, not only a wording: by the lead's earlier-time rule (M7) the step 4a wait now ENDS 04:40Z (10:10 IST) and 4b starts 04:50Z (10:20 IST) (new M7 (i)). The 04:46Z / 04:56Z figures stay only as the labelled worst case (section 6, clock block). The 269-minute chain and the other Tuesday times were NOT recomputed: they still use the 30-minute worst case, so they are 6 minutes pessimistic. Lead to confirm M7 (h) and (i).
3. Reader item 3 gave "gate 08:36Z" for rehearsal 2: WRONG against section 6 (rehearsal 2 starts 08:52Z in Case A, 09:02Z in Case B, so its gate starts 08:48Z (14:18 IST) / 08:58Z (14:28 IST), recomputed by hand). I used those.
4. Shell blocks are only syntax-checked with `bash -n`; behaviour unproven. Full bare "item N" sweep and a read of the unread ranges the reader named (RUNBOOK 247-267, 289-356; FIX-PLAN 90-200; TAKE-CHECKLIST outside 216-239) were NOT done by me.
5. UTC without IST: I fixed the lines the reader named (206, 273, 32, 217, 164/166/168 skeleton comments, step 19 title). I did not scan every other line of the three files for a bare UTC time.

## Reader r28 (round 35), six Majors, each checked against the text first
1. WAIT_S two due times: CONFIRMED (I20 and step 16 Tue 08:29Z; I55, FIX-PLAN, TAKE-CHECKLIST 183, comment Wed 05:45Z). Fixed: M7 (h); I55 (also now lists step 16); FIX-PLAN mailbox sentence and "Not Tuesday blockers" list (item 50 moved out); TAKE-CHECKLIST row `$WAIT_S`; skeleton comment. I44 and I57 now say which governs (I44 Tue 06:39Z (12:09 IST), I57 Tue 04:00Z (09:30 IST); the Wednesday time is only the last change). Q31 item 50 not editable by me (point 1).
2. Monday-night deadline: CONFIRMED only in RUNBOOK section 2 ("due Mon 16 Nov 20:30Z"); step 16.11, M7 (a) and FIX-PLAN already said 21:00Z. Fixed to 21:00Z (Tue 02:30 IST), item 30 = the decision, Tue 05:54Z (11:24 IST) the answer-by that follows.
3. Step 19 (d) vs rehearsal 1: CONFIRMED. Fixed in step 19 and section 2 (rehearsal 1 gate 07:44Z (13:14 IST) may write (e) NOT CHECKED; first gate needing (e) is rehearsal 2). Reader's 08:36Z rejected (point 3 above).
4. Step 4a wait two times: CONFIRMED (04:46Z vs 04:40Z "item 51 (c)", which was undefined). Fixed in RUNBOOK 4a (both cells), section 6, M7 (i), FIX-PLAN lines 28, 52, 188, 189, TAKE-CHECKLIST lines 22, 46, 85. The two clock blocks were edited with the same text.
5. Terms: CONFIRMED. Added the Qnn-N definition with ORDERS.md lines (Q25 144, Q26 147, Q27 156, Q28 166, Q29 167, Q30 171: each read with sed this round) to RUNBOOK section 2 and FIX-PLAN "Read first"; "database gate" renamed "database check" (RUNBOOK step 8 title, TAKE-CHECKLIST line 201); "unfinished rows" defined once in section 2 (same as step 24 (b); step 17 (6a) named as the different stricter count; "17.14" in the reader's note does not exist as such, I used "step 17 (6a)").
6. UTC without IST: CONFIRMED. IST added (UTC+5:30, each pair recomputed by hand) to RUNBOOK 206, 273, 32, 217, the three skeleton comments; step 19 title wrong ("(13:00 IST)") now "07:00 to 07:30 UTC, 12:30 to 13:00 IST".

## Reader r27 items 1-6, 8-9 (fix-planfiles34 does not list them as done by number, so each was checked in the current text)
1. need_set guards / database name check: ALREADY DONE (TAKE-CHECKLIST check 2 has `need_set REPO PGCONN TAKE_DB`, `current_database()` equals TAKE_DB, `-v ON_ERROR_STOP=1`; RUNBOOK 4a/4b status commands start with `need_set REPO ...`). Not redone.
2. $KEEP guard: ALREADY DONE (RUNBOOK step 9 (d)/(e) and FIX-PLAN Step 5 use `need_set KEEP`/`FILLED`).
3. FIX-PLAN status check: ALREADY DONE (Step 0 uses need_set and a positive `status-clean` line; Step 4c uses the guarded chain).
4. One due time per input: ALREADY DONE for (a)-(e) (M7 (a)-(g), I24 Tue 04:26Z in FIX-PLAN and RUNBOOK, values loop 06:24Z in FIX-PLAN and TAKE-CHECKLIST). (b) I57 vs FIX-PLAN is the labelled conflict plus my I57 edit above.
5. Labelled "step 5" / "step 10": ALREADY DONE in TAKE-CHECKLIST (lines 200, 369, 389 say "RUNBOOK step 5" or "Pin procedure, step 5"). RC8 says "RUNBOOK step 10" and RUNBOOK step 10 IS the fill check (FIX-PLAN mapping: FIX-PLAN Step 7 = RUNBOOK step 10), so the reader's doubt is not borne out; left.
6. "desk doors": ALREADY DONE (TAKE-CHECKLIST 112, FIX-PLAN 9 same definition).
8. $LOG guard form: ALREADY DONE (TAKE-CHECKLIST 162 gives the one REFUSED form).
9. Pin first look: ALREADY DONE (TAKE-CHECKLIST 466 excludes `#` lines, with `test` guards).
Checked by reading and grep only; not run.

## Outputs (from handover/flows-audit, after the last edit)
- python3 -I tools/check_refs.py: PASS 5182 references
- check_names.py: PASS 655 rows
- check_secrets.py: PASS 0 hits in 2801 files
- check_counts.py: PASS 52 files / 655 nodes
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS
- ruff format --check .: 928 files already formatted (count includes this report's folder state)
- bash -n on all 28 code fences (2 RUNBOOK, 26 TAKE-CHECKLIST, 0 FIX-PLAN): 0 failures. Inline commands I touched: none added.
- Tuesday clock block (48 lines from the bold "Tuesday 17 Nov: the re-pin event" line), FIX-PLAN vs TAKE-CHECKLIST: diff printed DIFF-EMPTY.
Files changed: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md, reviews/fix-planfiles35.md. R-numbers cited: none looked up (static wording pass). EGM skipped for the sequence: lead runs the review step (no EGM skill call from here).
