SUPERSEDED by work/critical-path-r2.md (the table below was built on a missed 14:00 start)

# CRITICAL PATH: when can the first filmed take happen? (current answer, 16 Nov 2026)

Note (16 Nov, added in a wording fix): conflict 4 from r2. Condition 5 below and open-items-table.md say fill_flows.py is not built, while the plan (lines 4 and 223) says it read a file fill_flows.py in the glue folder. UNVERIFIED which is right; I searched this checkout and found no such file, but the glue folder may not be in it.

## Answer
NO CONFIRMED DATE. If all six conditions below hold and row 2a starts by Mon 16 Nov 17:00 UTC / 22:30 IST, the earliest filmed take is Tue 17 Nov 05:00 UTC / 10:30 IST (setup from 04:30 UTC / 10:00 IST; the 3-hour owner notice counts back from the setup time, so it goes out by 01:30 UTC / 07:00 IST). The 05:00 time is my guess at when the owner wakes (ASSUMED, UNVERIFIED). If any condition is missing there is no date.

## The six conditions (none is confirmed; the row each one blocks is in brackets)
1. A builder is named for row 1 (none yet) [row 1].
2. A person is named for row 2c (none yet) [row 2c].
3. A4 is answered yes (answer UNKNOWN) [row 2a start].
4. scripts/n8n_api.py is supplied (not in the checkout) [row 1 import].
5. fill_flows.py is built (no owner) [row 1].
6. core-hardening's edits are finished [rows 2a and 2b run on them].

## Terms
- take = one filmed run of the lead-intake demo through n8n (a tool that runs the demo steps) on made-up data. lead = the studio lead = the Claude session doing the technical steps. owner = the human at the laptop. studio head = the human who runs the studio (not named). core-hardening = a separate Claude session that owns the held pages and the program patch. Held pages = pages the lead or core-hardening own; I do not edit them.
- A4 = a yes or no from the studio head to start row 2a (item A4 of work/decision-list-for-lead.md). Owner notice = a message the studio lead sends the owner at least 3 hours before the start so they can get ready.
- Flow copy = the copy of the demo flows with the three settings (the values the laptop must fill in; the list is NOT RECORDED) filled in. fill_flows.py = the script that fills them (not built). scripts/n8n_api.py = the script that imports flows into n8n (not in the checkout). Stand-in services = test programs that replace the real mail and contact tools. Program patch = the change to the program that runs the take (for example the behaviour of `end`, which the owner types to stop it); not yet made. Run values = the take's settings, such as the port; not yet set.
- T19 = the test that sends one made-up contact twice (not run). Rehearsal = a test run with stand-in programs (not run).

## Prep chain (hours)
Row 1 build and import the flow copy: 2.5. Row 1 has not started (checked 16 Nov 14:25 UTC): its proposed slot of Mon 11:30-14:00 UTC has passed, so the plan's row 1 slot is missed; the latest start that still keeps the 17:00 start of row 2a is Mon 14:30 UTC / 20:00 IST. Row 2a loopback self-check (the studio lead runs the flows against stand-in services, all on the studio lead's own machine): 5. Row 2b rehearsal: 1.5. Row 2c review (a person reads the rehearsal results): 2. Owner notice: 3. Row 1 must finish before row 2a. The notice (3 h) is sent after row 2c ends and the owner's setup starts 3 h later. Chain end (setup start) = row 2a start + 11.5 h (5 + 1.5 + 2 + 3); from the start of row 1 it is 14 h. Setup is wanted at 04:30 UTC (my guess at when the owner wakes), so the latest row 2a start is 17:00 UTC.

## One timeline (UTC / IST; arithmetic from my proposal that row 2a starts Mon 14:00 UTC, UNVERIFIED)
| row | proposed slot | latest start that still keeps the take at Tue 05:00 UTC |
|---|---|---|
| 1 build and import | Mon 11:30-14:00 UTC / 17:00-19:30 IST (already missed; row 1 has not started) | Mon 14:30 UTC / 20:00 IST |
| 2a loopback self-check | Mon 14:00-19:00 UTC / 19:30-00:30 IST | Mon 17:00 UTC / 22:30 IST |
| 2b rehearsal | Mon 19:00-20:30 UTC / 00:30-02:00 IST | follows 2a |
| 2c review | Mon 20:30-22:30 UTC / 02:00-04:00 IST | follows 2b |
| owner notice (sent after 2c; then 3 h wait) | sent Mon 22:30 UTC / Tue 04:00 IST in the proposed timeline | sent by Tue 01:30 UTC / 07:00 IST |
With the proposed 14:00 start the chain could allow setup at Tue 01:30 UTC, but the owner is probably asleep, so the owner-awake guess (04:30 setup) is the limit, not the chain. A row 2a start up to 3 hours later (by 17:00 UTC) still gives setup at 04:30 and does not move the take; beyond 17:00, each hour of delay adds an hour. Why 14:00: my proposal, not decided.
