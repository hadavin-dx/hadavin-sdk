# fix-rwct23: round 19 fixes for RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)
Non-security path. Static, nothing run. Counts unchanged: RW 195 rows, CT 330 claims, RW 558 lines, CT 1048 lines. No paste string changed. The audit invented no lead answer; proposals are marked "planned by the audit, lead to confirm".

Finding -> result (RW line numbers are those of the file after the edit; no line moved)
1 fixed: RW 91, 136, 156, 448 (429 pointer). Playwright = screen capture and the scene of the typed answers are UNANSWERED (lead; Q31 items 72, 100; the typed answers have no Q31 item, the lead adds one).
2 fixed, partly needs lead: RW 90, 171. Derived only: 4.5 h sum, 07:00Z + 4.5 h = 11:30Z, 18:29Z - 4.5 h = 13:59Z, steps 3 to 5 lie in the 30 or 40 minutes after 07:00Z. The margin and whether steps 3 to 5 fit are the lead's (Q31 items 6, 85, 101, 3). New open point: re-pin 07:00Z on the NO-GO path is after the 06:00Z practice start.
3 fixed: RW 171 (same KIND of leads, different lead IDs; practice run before P4a and the filter), 176 (never-reuse rule in step 7).
4 fixed: RW 138, 167 (new item 4), 168 (F-008 rebuild before 1b, re-pin done only after item 4).
5 fixed as needs lead: RW 169. Who starts the stage service, fake model program, Postgres, n8n is UNANSWERED; no Q31 item holds it, lead adds one.
6 fixed: RW 472 (rule HELD covers section 7 rows whose old sentence is in a file the take reads).
7 fixed: RW 412 (waits only for the re-pin), 177 (LIVE means a step to do, not needed to film; defined once in the CT legend line 75).
8 fixed: RW 505.
9 fixed: RW 506, 507, 508, 519, 553 (Waits for: Q-E answered yes by the lead). Q-E at 558 unchanged.
10 fixed: RW 154.
11 fixed: RW 483.
12 fixed by the allowed alternative (adding the word to the Panes line, RW 498): changing the strings of A-030, A-035 and S5-b would need a CT change of paste strings.
13 fixed as a proposal: RW 175 (f) and (d). Q25 item 12 says "from the start of n8n"; the new wording is marked planned by the audit.
14 fixed: RW 333. The paste cell stays ONE quoted string (the checker forces it); the condition is in the note cell: paste only if A-073a is pasted, otherwise the lead types 19; renumbering of 18 to 20 is UNANSWERED (lead). CT line 314 was WRONG (the reviewer said CT agreed): fixed to match RW.
15 fixed: RW 379, 381 own reasons. B-095: the date is known (credits stop Mon 23 Nov 18:29Z = 23:59 IST, ORDERS.md line 156 item 6); which credits is not said.
16 fixed: RW 136 (adds 2c), 145 (who supplies the send command), 429 (pointer to a row that does not exist removed).
17 fixed: RW 509, 521.

Needs the lead: Q31 items for (a) typed answers scene, (b) who starts the stage service and fake model, (c) re-pin date and renumbering after A-073b; the 07:00Z margin.
Noticed, not changed: RW says delete request 1 is sent at the end of step 6, RUNBOOK step 20 sends message 1 during the 19a mailbox wait; row (o) BLOCKER text differs from Q31 item 100 defaults.
Reviewer line numbers for finding 12 (163, 177, 479) do not hold "test mailbox"; it is at 516 and 520.

Checks (last lines): check_refs PASS 5176 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2662 files; check_rw_ct_pairs 140 found of 140, not found 0; check_runsheet_paste total rows 195, RESULT: PASS; claims-count ids 330 unique 330 (A 100, B 226, X 4), offenders 0; ruff format --check: 810 files already formatted.
