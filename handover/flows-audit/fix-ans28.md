# fix-ans28 (ORDERS.md line 138, 5 items) - 2026-11-16
Failures first: none. Not run: n8n, Postgres, HubSpot, SMTP (made-up data only, nothing runs). EXCEPTIONS.md needed no change (it holds no DESK_ALERT_TO or F-013 retry wording; grep checked).
Backups: scratchpad/bak-ans28/ (6 files).
1. Blockers: QUESTIONS Q22-1 marked ANSWERED; REPORT keeps the rating note and gets a line for the answer.
2. F-013: FINDINGS row now says "each of the 3 tries ... ends failed after 3 tries (it does not retry forever)" and "ACCEPTED as the trade-off". Grep of the six files for retry/forever/endless: no other file implies endless retry (FINDINGS 30, 54, 71 and FIX-PLAN 10 are about other things).
3. CUT-LIST: single note = n8n-owns-vs-desk-owns.md (13-line summary first, plain words, glossary, cited by the FINDINGS verdict table); six others are archive candidates; archive = move, never delete; owner's yes asked once by the lead in a table later. QUESTIONS Q22-3 marked partly answered.
4. DESK_ALERT_TO: QUESTIONS Q20 heading, item 4 and Q22-4 ANSWERED (lead sets at take prep, verifies at re-pin); FIX-PLAN item 3 wording changed; no address typed anywhere.
5. Decision 2: Q22-5 marked CONFIRMED.
Checks: count_findings.py = 45 rows, Blocker 5 (BEFORE 5), Major 7, Nit 33; BEFORE 13, AFTER 32. check_patches.sh = PASS 4 patches.
Untouched: CLAIMS-TABLE.md, RUNSHEET-WORDING.md, OWNER-STEPS-q16-rows.md.
