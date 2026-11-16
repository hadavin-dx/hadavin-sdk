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
8 (update 2026-11-16T16:45:09Z): owner said "scan yes" in chat; the lead ran it, counts only, no text read. Seven files: sk-ant 0, generic sk- 0, HubSpot pat- 0, AWS AKIA 0 in all seven. Loose patterns hit a few ordinary tokens: git-style hex ids in 1 file (REVIEW-real-run-v6), a few 16-letter words in 2 files; no mixed letter-and-digit key-like token in any of them. 1b | no: no key or secret needs changing on this evidence. Limits: pattern counts, not a read; an app password written as ordinary words with spaces could slip past; the lead did not open the files. Keep the digest lines visible (answer 1 stays: delete is not needed; reply 1 | keep).

## Batch 3 (lead, 2026-11-16T16:50:21Z). Defaults chosen by the lead; owner may veto. 
CORRECTION to the archive sentence, same facts: decision 2 of 2026-11-16 keeps the take's HubSpot key READ-ONLY (no archive or delete right). The program still calls archive after end; with a read-only key the call is refused and all three contacts are listed as left behind, which the owner archives or deletes by hand from the printed list. Whether the refusal prints cleanly: UNVERIFIED until the re-smoke. Wording for the pages: "The take's HubSpot key cannot archive or delete. After end the program tries once; whatever it cannot archive it lists, and you archive or delete those by hand."
1: done, I corrected inputs/DECISIONS-2026-11-16.md line 3 (copy on your branch updated by me).
2: builders r37, r38, r39 (laptop lead agents); finish about 17:15Z, 18:10Z, 18:40Z = 22:45, 23:40, 00:10 IST; then reviews and merge chain; re-pin target Tue 17 Nov 08:00Z (13:30 IST).
3: F-002 and security rules A, E, F, I: not known to the lead; write UNVERIFIED, core-hardening names them if it can.
4: [OWNER FILLS] look of the HubSpot accounts and proof-screen choices; films: Claude records via Playwright, the owner watches and posts; backstop line name: core-hardening reads it from stage.env.
5: profile name and place: [OWNER FILLS at the profile and filming check]; deadline exception stays UNVERIFIED.
6: HubSpot check line and date: [LEAD FILLS at re-pin]; login-key choice: closed after the scan (no key found in the seven files).
7: third refill time 17:30Z (23:00 IST); percents for M1 M2 M4-M8 M10-M13 M20: [LEAD FILLS at refill from the live state]; video: post Wed 18 Nov 15:00Z = 20:30 IST (recording earlier that day).
8: dollar limit: the API credits (US$189 prepaid, in-code backstop below it, window to Mon 23 Nov 18:29Z); agent-day estimate: about 2 days of agent time to the take.
9: DESK_* meanings: UNVERIFIED, core-hardening confirms.
10: generator path: UNVERIFIED, core-hardening names it; n8n_api.py is scripts/n8n_api.py in the take repo; crash test (DM): required; rehearsal-passed rule covers the loopback re-smoke and the rehearsal (answer 4.6); program notice and prompt text: edited by the fix builders, the lead approves.
11: v4.2 lines 453 and 507: the lead corrects them in v4.3 (system-map drafts the wording from the sentence above); HubSpot key right: stays read-only by decision 2; whether HubSpot's filtered list shows archived contacts: UNVERIFIED, the re-smoke shows it.

## RETRACTION (lead, 2026-11-16T17:46:03Z): my "CORRECTION" in Batch 2 and Batch 3 was WRONG. I read an OLD integration branch (take/nlite-int 8eba53a) that still called archive_all; the program that will be taken is the r34+ line (run_real_check_n8n.py head r38 0cead2c), and there the code is read-only on HubSpot: it has no create/update/delete or archive call, prints "this script only reads HubSpot and never deletes: it counts and lists them at the end and you delete them by hand" and "left in HubSpot (this take never deletes): N contact(s)". So the ORIGINAL sentence was right: "The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list." Put that sentence back on all ten held pages and in the v4.3 rows; decision 2 of 2026-11-16 and inputs/DECISIONS-2026-11-16.md line 3 are restored. Keep it UNVERIFIED until the loopback re-smoke on the merged head. Also item 11 of batch 3: v4.2 lines 453 and 507 ("no archive call, read-only identity", "never deletes") are therefore CORRECT for the final program; do not rewrite them. Item 12 filter text, from the r38 clean-up list: search take-<tag>-a, -b, -c (example.com). Item 13 pause: unchanged (no timer in the code I read).
