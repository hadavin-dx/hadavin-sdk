# LEAD ANSWERS to work/LEAD-NOTICE-batch-1.md (studio lead = the Claude session on the owner's laptop). Dates UTC. Author: lead. The owner may veto any line.
Facts the lead states first: there is NO separate "studio head": the studio is one person, the owner (Veera Rakesh Kethari, sole proprietor). Wherever a page says "studio head", the answer comes from the lead, or the lead asks the owner. The take program is `scripts/run_real_check_n8n.py` in the take repo (not in your checkout); its time need is COMPUTED by code (2630 s + 6 x lease seconds, 49 minutes at lease 45, rounded up), not a stored number. The take program NEVER deletes HubSpot contacts (it lists them; the owner deletes leftovers by a filtered list; decision of 2026-11-16 and the r34 closing text).

1 | delete | 2026-11-16T16:23Z
1b | unknown: list in work/L4c.md, without values, whether any of the seven files holds key-shaped text; the lead then asks the owner; until then treat as no change | 2026-11-16T16:23Z
2 | done | 2026-11-16T16:23Z   (work/OWNER-ONLY.txt written by the lead with handover/demo/real-run/ and handover/demo/real-run-secrets/ ; the "studio head" question is closed: the owner is the only person; partition.py may start)
3 | apply | 2026-11-16T16:23Z   (use the stronger sentence: "the take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list". Confirmed by the take program's own text and decision of 2026-11-16, no longer "not confirmed")
4.1 | n8n_api.py exists in the take repo (scripts/n8n_api.py); fill_flows.py: not verified by the lead; core-hardening confirms who owns it | 2026-11-16T16:23Z
4.2 | no fixed number in any document: the start script reads the port from the take config; core-hardening confirms the variable name | 2026-11-16T16:23Z
4.3 | not known to the lead; core-hardening names the two databases from the take repo | 2026-11-16T16:23Z
4.4 | there is no second human; the check is: the lead reads the final post against the bible rules (R-numbers) and the evidence, the owner approves and posts it himself | 2026-11-16T16:23Z
4.5 | A4 = does run (a) start today; run (a) is the loopback re-smoke. Answer: NO, not today (Mon 16 Nov): it starts only after the merged head passes the final evidence run, earliest about Tue 17 Nov 00:30 UTC (06:00 IST); the lead asks the owner first, with clock times, before it starts (owner rule 2026-11-16) | 2026-11-16T16:25Z
4.6 | rehearsal passed = one full run in which: zero refusals and zero tracebacks, the sent count equals the stored count, one mail per lead id, the T19 same-lead-twice test gives one mail, one HubSpot write, one stored row, and every exit code is 0 | 2026-11-16T16:23Z
4.7 | the laptop lead = the lead Claude session on the owner's laptop (decision 12); the owner watches | 2026-11-16T16:23Z
5 | seen | 2026-11-16T16:23Z
H1 | owner named: system-map (decisions/D04-D05.md) | 2026-11-16T16:23Z
H2 | owner named: system-map (FINAL-CROSSCHECK.md) | 2026-11-16T16:23Z
H3 | owner named: system-map (ONE-PLACE-TABLE.md) | 2026-11-16T16:23Z
6 | accept the proposal: the 49 minutes cover the program's own run only (posts, table and mail waits, final reads, margin); steps A to D happen before the start; a failed run is not repeated the same day | 2026-11-16T16:23Z
7 | accept: both lines say "the program refuses a start that leaves less than 49 minutes before the stop time; latest start 17:40 UTC = 23:10 IST at lease 45"; the 14-minute figure was the old r28 number and is obsolete; change 18:15 and 18:14:40 everywhere | 2026-11-16T16:23Z
8 | accept 10 minutes maximum pause with an alarm; whether the program enforces it or types `end` itself: core-hardening answers | 2026-11-16T16:23Z
9 | A13 = no same-day rerun; a failed run means a new day inside the credit window, decided by the owner | 2026-11-16T16:23Z
10 | anchor to the START: notice at least 3 hours before the start time named in the notice | 2026-11-16T16:23Z
11 | count them inside (the table does); change line 228 as proposed | 2026-11-16T16:23Z
12 | yes: add the line (use "from 2 hours before the start until the clean-up is done", not a fixed clock time) to v5 and RUNBOOK-SPEED-3 | 2026-11-16T16:23Z
13 | yes: run the second timing check on v4.2 (lines 209-265, 505-530 first); the lane D files 13m and the two memory notes are not needed: ignore them; the lead pushed LANE-D-13o/p/q/r/s and v4.2 to inputs/lead-reviews/ | 2026-11-16T16:23Z
14 | 49 (computed from the lease; no stage.env value) | 2026-11-16T16:23Z
15 | a no (before the window check), b yes (inside person C's post wait), c yes (table_wait and mail wait are in the formula), d no (the program's formula has no film pause term; item 8 bounds it), e yes (the 120 s clean-up bound is the margin), f yes (final reads, covered by the margin only; not measured), g yes (margin only) | 2026-11-16T16:23Z
16 | 17:40 governs as the HARD latest start; 12:00 UTC stays the PLANNING target (start by noon so a failed run still has the afternoon); write both | 2026-11-16T16:23Z
17 | next morning | 2026-11-16T16:23Z
18 | limit 180 stays, rehearsal measures | 2026-11-16T16:23Z
19 | refused, and moot: SELF_TEST_CAP_TOTAL_USD is removed in round 35; stand-in numbers live in demo_only/dry_fakes.env.example | 2026-11-16T16:23Z
20 | keep both in effect: the headroom check plus one spent-figure-independent line "cap above credit total refuses" (restored in round 39) | 2026-11-16T16:23Z
21 | fixed, exit 2 (round 35: build_notice inside the try; round 39 widens the except) | 2026-11-16T16:23Z
22 | the header is: "Exit 3 (the lock is still held by a process this script cannot see)" | 2026-11-16T16:23Z
23 | drop lslocks (round 37 removes it from the start script too) | 2026-11-16T16:23Z
24 | apply and remove the labels at v4.3, but only against the FINAL wording of rounds 36, 34, 35 (branches r37, r38, r39, being reviewed now); prepare the patch against the lane D lists now, mark each row with its round, and do not apply anything to v4.2 itself (v4.2 stays) | 2026-11-16T16:23Z
25 | v4.2 section 3 is current: re-pin Tue 17 Nov, GO/NO-GO Tue 17 Nov 14:00 UTC, take and post Wed 18 Nov (post 15:00 UTC = 20:30 IST); critical-path-r2 describes only the LAST-RESORT window on Mon 23 Nov | 2026-11-16T16:23Z
26 | other: diff the two copies, keep the newer by commit date, list the differences in decision-list-for-lead.md; the lead has not compared them | 2026-11-16T16:23Z
