# fix-findings-ledger33 (2026-11-16): fixes for reviews/findings-ledger-reader-r33.md M1 to M8

Static edit of FINDINGS.md and LEDGER-ROWS.md only. Nothing was run in n8n, Postgres or HubSpot. The command blocks in the fix cells were edited as text and NOT run. No severity changed, no status moved (all 45 stay OPEN). Backup: the scratchpad folder `bak33` (FINDINGS.md and LEDGER-ROWS.md before this round).

## Unverified or not fully closed (first)
- QUESTIONS.md item 137 still says 07:00Z (12:30 IST); I may not edit that file, so the rows now say 06:15Z (11:45 IST) and carry a LEAD FILLS line that the studio lead edits item 137 to match before 06:15Z.
- TAKE-CHECKLIST.md GO row 7 and FIX-PLAN item 8 still describe fix A as live; not edited (outside my files). The F-011 row now carries a LEAD FILLS line (studio lead aligns both by Tue 17 Nov 03:00Z (08:30 IST)).
- The new default-runner paragraph is the audit's reading, studio lead to confirm. The rows F-037, F-008, F-029 and F-011 fix A keep "nobody" (as Q31 items 26 and 136 say); I did not reword those items.
- Probe slot (M3) Wed 05:45Z to 06:00Z is a proposal; the probe length is still unmeasured.
- Only the listed checks ran; no reader re-read these edits.

## Per item
- M1 (F-011 LEAD FILLS without owner/time): fixed. The studio lead (or a builder he names) writes the Postgres T7b, the import command and N8N_ROLE/N8N_DB/N8N_PW by Tue 17 Nov 03:00Z (08:30 IST); if not, fix A is dropped (already the default). "Who adapts T7b" now has owner and time. Needs lead: the name of any builder.
- M2 (item 137 input and second read both 07:00Z): fixed. Item 137 input due 06:15Z (11:45 IST) in F-011, F-041 (all places) and the two paragraphs above the table; second read stays 07:00Z (12:30 IST), 45 minutes later; F-041 now says "THREE TIMES, NOT ONE". Needs lead: edit QUESTIONS.md item 137 (see above).
- M3 (HubSpot probe no runner/slot): fixed as a proposal. Runner studio lead, slot Wed 05:45Z to 06:00Z (11:15 to 11:30 IST) outside the practice hour; minutes LEAD FILLS by Tue 17 Nov 07:00Z (12:30 IST); LEAD DECIDES another slot if over 15 minutes.
- M4 (F-002 rehearsal minutes; SECOND_ADMIN.sh): fixed. Rehearsal minutes: no measurement is planned, optional fill with owner and time by Tue 17 Nov 07:00Z (12:30 IST), else the stricter default stands. SECOND_ADMIN.sh and mailbox_count.sh: studio lead writes or names a writer by Wed 18 Nov 05:45Z (11:15 IST); the `--check` contract and "T21 counts as not passed without it" are stated at the NOT WRITTEN line. (I used the existing item 82 time, not Tue 07:00Z.)
- M5 (re-type F003-4 after step 14): fixed in the F-003 fix cell (WHO NEXT and PASS LINE) and in the F-003 status cell (closing list, FINDINGS only).
- M6 (F-003 rating basis): fixed once in F-002: three Blockers by lead order alone (F-002, F-007, F-031), two by rubric (F-003, F-037); ORDER 007 item 2 names four of five (checked in ORDERS.md line 32: F-003, F-005, F-006, F-007, F-031, and F-002 until T1 passes), not F-037; F-003 stays rubric-rated. The F-003 row already said this.
- M7 (default runner): fixed. One paragraph "DEFAULT RUNNER RULE" in FINDINGS.md (after the "WHO ANSWERS THE Q31 QUESTIONS" paragraph) and one pointer bullet in the LEDGER-ROWS.md header; all ten rows point to it. Studio lead runs everywhere except F-037, F-008, F-029 and fix A of F-011 (nobody until Q31 item 26 or 136). LEAD DECIDES: item 26 by 07:00Z (12:30 IST), item 136 by 03:00Z (08:30 IST).
- M8 (GO row 7 / FIX-PLAN item 8 vs fix A): fixed by a LEAD FILLS line with owner and time (above), and the row says it is the authority until aligned. The two files themselves are not changed.

## Checks run (from the flows-audit folder)
- compare14.py: `45 45 differences: 0`
- tools/count_findings.py: rows 45, Blocker 5, Major 5, Nit 35
- tools/check_refs.py, check_names.py, check_secrets.py, check_counts.py: all PASS, exit 0
- ruff format --check .: 1108 files already formatted
