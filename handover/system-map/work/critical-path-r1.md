# Critical path to a filmed take (re-timed Mon 16 Nov 2026 12:00 UTC / 17:30 IST by the system-map session). EST = my estimate, no source file.
Nothing has started: row 1 needs scripts\n8n_api.py (not in this checkout) and row 2a waits on decision A4 (work/decision-list-for-lead.md; answer was due 13:00 UTC / 18:30 IST, status unknown). Every time below assumes the rows start at 12:00 UTC / 17:30 IST; if they start later, add the delay. Wed 18 Nov is the lead's target; it has no time of day and is not confirmed.

Words: take = the one filmed run (real-v5, scenes 1 to 4); owner = the person at the laptop who types y, the 6-digit number and end; studio lead = the Claude session that prepares the take; core-hardening = the Claude session that patches the core and flows; T19 = the test that sends one lead twice and expects one result; rehearsal = a test run on the laptop with no real account; rerun = a second try of the take after a failed first try.

Hard limits (from the lead's orders, not from the decisions file): latest start Mon 23 Nov 18:14:40 UTC / 23:44:40 IST; stop 18:29 UTC / 23:59 IST; the studio lead's notice at least 3 h before the start (last day: by 15:14:40 UTC / 20:44:40 IST); post Wed 25 Nov 15:00 UTC / 20:30 IST.

| Row | Who | Work | Start | Done (EST) |
|---|---|---|---|---|
| 1 | studio lead | build and import the filled patched flow copy with scripts\n8n_api.py (decision 7) | 12:00 UTC / 17:30 IST | 14:30 UTC / 20:00 IST (2.5 h) |
| 2a | studio lead | loopback self-check on the lead's own machine (decision 12), not a film scene | 12:00 UTC / 17:30 IST | 16:00 to 17:00 UTC / 21:30 to 22:30 IST (4 to 5 h by the plan) |
| 2b | studio lead (the owner is not needed; the rehearsal uses stand-in programs) | first laptop rehearsal: T19 and the stored-data check; needs rows 1 and 2a | 16:00 to 17:00 UTC / 21:30 to 22:30 IST | 17:30 to 18:30 UTC / 23:00 to 00:00 IST (1.5 h) |
| 2c | a named independent reviewer (NOT NAMED: the studio lead names one; the lead's own plan, not decision 12, asks for review rounds) | up to 2 review rounds of 1 h each | 17:30 to 18:30 UTC / 23:00 to 00:00 IST | 19:30 to 20:30 UTC / 01:00 to 02:00 IST Tue |
| notice | studio lead | after "rehearsal passed" (here = end of row 2c) sends the owner date and start, at least 3 h ahead | 19:30 to 20:30 UTC / 01:00 to 02:00 IST Tue | the earliest start is the notice time plus 3 h: 22:30 to 23:30 UTC Mon / 04:00 to 05:00 IST Tue |
| take | owner at the laptop | setup 0.5 h; the filmed run has no sourced length | not set | not set |
| cut and check | NOT NAMED (no person in any file I hold) | about 4 to 6 h (EST) | after the take | not set |
| clean-up | owner | delete leftover made-up contacts by hand (decision 2); revoke the model key | after "last run done" | not set |

If row 2a only starts at 14:00 UTC / 19:30 IST (decision A4 as proposed), rows 2a, 2b, 2c and the notice move 2 h later (row 1 does not move, it starts independently): rehearsal passed by 22:30 UTC / 04:00 IST Tue, earliest start 01:30 UTC Tue / 07:00 IST Tue. That is still Tuesday, so the A4 time does not by itself make Tue 17 Nov fail; the real limit is when the owner is awake, which no file states (assumption: Tue 17 Nov about 04:30 UTC / 10:00 IST).
Row 1 "done" at 14:30 UTC is my estimate; the lead's own "row 1 done" message time is not set and may differ.
TAKE-BLOCKERS row 3 (core-hardening's edits) has no estimate in any file I hold, so whether Wed 18 Nov is reachable is UNKNOWN until core-hardening gives one.
TAKE-BLOCKERS has 3 rows: its row 1 = row 1 here; its row 2 = rows 2a to 2c here; its row 3 is not scheduled here. Rows run in parallel only where files differ; row 1 and row 2a can start together, and row 2b waits for both.
