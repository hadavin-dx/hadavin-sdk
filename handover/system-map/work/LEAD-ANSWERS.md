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

## Batch 2 (lead, 2026-11-16T16:41:38Z). CORRECTION FIRST: my answers 3 and the facts line said "the take never deletes contacts". WRONG. Code read (take/nlite-int scripts/run_real_check_n8n.py, _archive_once, line 1038): after the owner types end the program ARCHIVES this take's made-up contacts in HubSpot (archive_all); any it cannot archive are listed "left behind: archive them in HubSpot by hand"; the printed clean-up list (cleanup_list) tells the owner to search take-<tag>-a, -b, -c (example.com) and delete them. Use this sentence on all ten held pages instead: "After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints." Mark it UNVERIFIED until the test run in item 11. Replace "studio head" with "owner" after reading each line in context.
1: v5 steps A-D = the owner's steps (the written yes, laptop settings, mailbox check, profile and filming check), before the start. v4.2 "Step D" (clean-up after) is a different list; reword v4.2 to avoid the clash.
2: outside, plan latest start 17:30Z (23:00 IST). The program still ACCEPTS a start up to 17:40Z (its formula has no pause term); the lead's rule is 17:30Z so a 10-minute pause still ends before 18:29Z.
3: comfort margin only. No later day exists on Mon 23 Nov; say so. Noon is not a promise of a rerun.
4: bars only a failed take; rehearsals and recording-defect retakes are allowed (they send no new lead through the real take path only if the owner approves the new run yes).
5: both. The program prints its own notice at every start (each start needs its own); the lead sends the owner a message at least 3 h before the start time named in it; sender: lead.
6: typing 5 min (planning figure, rehearsal measures); teardown next morning with the owner's clean-up.
7: owner chooses the day, inside the credit window; Thu 19 Nov is the default offer.
8: asked owner (owner-only folder; no helper opens it). Until his yes: NOT CHECKED stays; digest lines hidden. The owner decides, no studio head.
9: system-map applies all ten pages now on this written word, with the corrected sentence above; each page gets one more fresh read afterwards. Page-owner rules: lead pages and core-hardening pages are covered by this order.
10: yes, replace (plain copy of the inputs copy, then re-run the diff).
11: lead runs it in the loopback re-smoke (one made-up contact, then end), day: after the re-pin, Tue 17 Nov or Wed 18 Nov before the take; result in egm/duplicate-proof-lead-desk/wp6/ (file named by the lead). Pages say UNVERIFIED until then.
12: ask core-hardening: the clean-up list prints search text take-<tag>-a, -b, -c with the example.com domain; where <tag> first appears on screen is not verified.
13: not enforced. Code: after the verdict the program waits for the typed word end (2 tries; end of input also ends it); no timer, no alarm, never types end itself. The 10-minute limit is the owner's own clock alarm; no code change (RIGHT-SIZE).
14: core-hardening edits step J (it owns the v5 sheet).
15: lead fixes M-1 at the merge (qualify app.mf_leads in n8n_drive.py and the stale test); the read-only count role is separate and not planned for the take.
