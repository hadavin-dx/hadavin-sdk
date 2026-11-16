# fix-questions4 (fixer, QUESTIONS.md stranger read r4, M1-M4 and Nit)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-q4/QUESTIONS.md. Static edit only; nothing committed.
Confirmed against ORDERS.md: L7 text "set at take prep" (Q22 follow-up item 4) and "verifies at re-pin" (Q20 item 4) both exist with no day for take prep; Q17 item 5 vs Q25 item 1 / Q28 item 3 conflict exists; "fresh three-lane review" and "one mutation batch" appear only in the Q26 schedule line with no explanation.

## Changes
- M1: glossary "take prep" added (day = lead question Tue after re-pin vs Wed 18 Nov ~07:00Z; contents = Q20 item 1, L4, L7, L12, L14, L22, L33). L7 now "set at take prep, verified once it is set" and states the order problem. L4/L12/L14/L22 point to the glossary. Re-smoke glossary notes the Tuesday fill may be a test fill. Q31 item 8 now asks the day.
- M2: Q31 answer-by reordered (table below). Item 9 moved 14:00Z to 07:00Z.
- M3: L5 made CONDITIONAL; states both yeses with ORDERS lines, asks the lead in Q31 item 3 (conflict 2) which applies; answer-by Tue 07:00Z; ask time planned by the audit (Tue 15:00Z = 20:30 IST), lead to confirm.
- M4: glossary entries desk, the lead's own values file, the challenge, Qualify duration, three-lane review, one mutation batch; unknowns are marked UNVERIFIED and collected in new Q31 item 14 (answer by Tue 08:00Z).
- Nit: index cell for Q31 now says "L29 (follow-up of item 12 only)"; L29 When cell gives the planned Tue 08:00Z, lead to confirm. Counts changed 13 to 14 in index row, count line and Q31 header.

## Q31 dependency table (answer-by, Tue 17 Nov)
| Item | Needs first | Due Z | Due IST |
|---|---|---|---|
| 2 clock times, key | none | 07:00 | 12:30 |
| 3 ceiling, retake, Row 4 yes | none | 07:00 | 12:30 |
| 5 number of delete messages | none | 07:00 | 12:30 |
| 8 take prep day, message times | none | 07:00 | 12:30 |
| 9 chat, reply deadline | none | 07:00 | 12:30 |
| 1 silence rules | 2, 3, 5, 8, 9 | 08:00 | 13:30 |
| 6 GO/NO-GO message | 9 | 08:00 | 13:30 |
| 10, 11, 12 | none | 08:00 | 13:30 |
| 14 words | none | 08:00 | 13:30 |
| 4, 7, 13 | none | 14:00 | 19:30 |
Dependencies are the audit's reading of the item texts; planned by the audit, lead to confirm.

## Commands (run in handover/flows-audit)
- recount script: 33 L-rows, 33 unique; index L-ids equal table L-ids; types DO 19, VERIFY 6, DECIDE 5, ASK OWNER 3 (=33); Q31 items = 14. Exit 0.
- python3 -I tools/check_secrets.py: PASS 0 hits, exit 0
- python3 tools/check_refs.py: PASS 5146 references, exit 0
- ruff check .: passed, exit 0
- ruff format --check QUESTIONS.md: already formatted, exit 0

## Not checked
Line numbers of ORDERS cited in new text were taken from the file's existing citations (117, 144, 147, 166), not re-verified one by one. Q31 dependencies are inference. Other files (OWNER-STEPS, RUNBOOK) that quote the old Q31 answer-by times or "13 questions" were not searched or edited.
