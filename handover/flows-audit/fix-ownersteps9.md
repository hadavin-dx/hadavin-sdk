# fix-ownersteps9 (fixer, round 8 of the owner part of OWNER-STEPS-q16-rows.md)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os9/OWNER-STEPS-q16-rows.md

## Failures and not checked (first)
- `ruff format --check .` FAILS (rc=1): "1 file would be reformatted", the file is inputs/plan-wp6-resmoke-v5.md (a Python block inside a markdown file, line 193). Not mine and outside my allowed file; not changed. Lead or the owner of that file fixes it.
- `python3 -I tools/check_secrets.py`: PASS 0 hits in 1755 files (rc=0).
- Nothing was run except those two commands and my own edit script. Every time I wrote is "planned by the audit, lead to confirm", not a fact. I did not re-read the lead part (line 81 on) for contradictions with the new table; the lead part still says "the audit" and "re-pin" in its own words (fine, it is lead-facing).
- Reviewer words were unverified; I checked each against the file: all 6 Majors and 5 Nits were real (see below). One reviewer claim was imprecise: "challenge has two meanings": the file did say both "program asks you to type back" and "lead tells you the answer in chat"; CLAIMS-TABLE.md line 9 says it is a 6-digit number shown on screen, so I used that (itself UNVERIFIED, marked).

## Fixes (owner part, lines 8 on)
- M1 retake: no answer by 13:00 UTC (18:30 IST) = no retake, no paid call; clean-up and post go on at planned times; lead asks by 12:00 UTC (17:30 IST). Old "everything waits" sentence removed. Key revocation no longer waits on a retake answer.
- M2 challenge: one meaning, a 6-digit number shown by the demo program in its window; nobody tells it in chat.
- M3 item 2: latest message time 09:00 UTC (14:30 IST), "missing" at 09:30; be at computer 09:45-11:15 UTC (15:15-16:45 IST); stated what the typing message names; silence rule (10 min then slip).
- M4: table "What you do and when" added at the top (item | UTC | IST | waits for | reply words | if nothing), NOT YET DECIDED cells kept for item 3 and 4 clock times with a planned safe default; silence and times added to items 3, 4, 6 and delete deadline (1 hour).
- M5: one named blank [CHAT NAME] used everywhere; old "a question for the lead is open" wording removed.
- M6: item 5 ready time 12:00 UTC (17:30 IST), edit window 3 hours to the 15:00 UTC (20:30 IST) post; if ready after 13:00 UTC (18:30 IST) the post moves a day.
- Nits: "re-pin" and "the audit" defined in plain words; removed FACTS-ALREADY-DONE.md, "F-002", "Row 4" from the owner part (owner header lines 5-6 are above line 8, untouched); lowercase address rule in the delete step; one sentence "Latest take day and latest post day" and the three old date mentions now point to it; F-002 failure on Wed: lead tells by 08:00 UTC (13:30 IST), "missing" at 08:30 UTC (14:00 IST), no delete message that day.

## QUESTIONS FOR LEAD (new; not added to QUESTIONS.md)
1. Confirm every "planned by the audit, lead to confirm" time in the new table (rows 0a, 6, 1a, 3, 2a, 2b, 7, 4, 5).
2. Is the challenge a 6-digit number the demo program shows (CLAIMS-TABLE.md line 9), not something you tell the owner in chat? Which window shows it, and does the owner type on a live own computer or remotely?
3. What does typing y confirm?
4. If a retake check failed and the owner is silent on the retake by 13:00 UTC, is the first recording still posted, or is nothing posted? The sheet now says: posted only if the recording-ready message has arrived.
5. May the sheet promise "take stopped and moved one day after 10 minutes of owner silence"?
6. Does a weekend (Sat 21 or Sun 22 Nov) retake day need the owner's yes first (written so)?
7. The header lines 5-6 (above line 8) still use file names and "ORDERS.md"; outside my range.
