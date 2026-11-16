# LEAD PAGE
For the lead only (the lead is the Claude session that gives the orders and does the technical steps with the owner). Moved out of OWNER-VIEW.md on 2026-11-16 (ORDER 017, defined in section 5); sections 1 and 2 were rewritten the same day. Everything here is for the lead: accounts, keys, Docker, engineering status, drift items. Facts the lead stated are in work/LEAD-ANSWERS.md.

Written Mon 16 Nov 2026, about 09:15 UTC / 14:45 IST, by the system-map session from the other sessions' files; updated Mon 16 Nov 2026. Made-up data only. A number or claim taken from another file shows its source as file:line or section.

## Words (each used in one meaning only)
Files and pages
- **v5** = the current owner-steps file, `inputs/OWNER-STEPS-realrun-v5-core-hardening.md`. Cite v5 only.
- **OS** = the old owner-steps file `inputs/OWNER-STEPS-realrun-v3.md` (v3). It is archived, not deleted, and replaced by v4 and later (decision 10). OS line numbers below belong to v3 and are kept only as sources.
- **OWNER-VIEW.md** = the owner's own page (the order of messages and the owner's tasks). **OWNER-RUN-DAY-CARD.md** = the owner's numbered steps for the take day. **OWNER-CLEANUP-CARD.md** = the owner's numbered steps after the last take. The two cards are the "cards".
- **TAKE-BLOCKERS.md** = the table of numbered rows (row 1 to row 5) that must be done before the take.
- **STATUS-BOARD.md** = the live status page. **QUESTIONS.md** = the open questions to the owner.
- **FINAL-CROSSCHECK** = the file that merges the three audits.
- **decision N** = a numbered decision in `inputs/DECISIONS-2026-11-16.md` (for example decision 12: the lead runs the first laptop rehearsal).

Roles
- **the lead** = the Claude session that gives the orders and does the technical steps with the owner. **the owner** = the one person who runs the studio. There is no other person: nobody else reviews or approves.
- **sales lead** = a person who asked for something through the web form. **sales request** = what that person sends through the form. The bare word "lead" is not used for either; where a quoted claim contains it, it means sales lead.
- **LP-1 to LP-5** = "lead point": the five numbered open choices in section 3. This label is this page's own; no other file defines it.

The take
- **the take** = one real recorded run of the sales-request desk demo (up to two are possible; a failed one needs a new written yes, OS:111-112, OS:117). A failed take is not repeated the same day (lead answer 9).
- **take id** = a short name picked fresh for each take (OS:95). **`.used` marker** = a small file the take script leaves so a take id is not used twice. **take config** = the settings file of one take.
- **take script** = the program the lead starts that runs the take and asks the owner to confirm. After the verdict it waits for the typed word `end` (2 tries; end of input also ends it; no timer; it never types `end` itself). What it does at `end` is in section 1, "Still yours, later".
- **request id** = the number a sales request carries so a repeat can be spotted.
- **n8n** = the tool that moves each sales request from step to step. **flow** = one n8n workflow. **the changed flows** = the five that flows-audit patched.
- **form address** = the web address the form sends a sales request to.
- **CRM** = the customer database; the take writes a contact into HubSpot, the CRM product used.
- **Postgres** = one Postgres server with two databases (n8n's own and the take's) (decision 10).
- **WSL window** = the Linux command window on the owner's Windows laptop.
- **the cut** = the edited video. **filmed** = recorded on screen.

Checks and trials
- **re-smoke** (also called laptop trial, smoke test, loopback re-smoke, first laptop rehearsal and run (a) of TAKE-BLOCKERS row 2) = a trial run of the whole chain with no paid model call (cost US$0) before any real take. The plan quotes 3.5 to 4.5 hours realistic, about 2 h 51 min if nothing goes wrong (plan-wp6-resmoke-v5.md, near the top). Run (b) is the filled, patched real-v5 run.
- **rehearsal passed** = one full run with zero refusals and zero tracebacks, the sent count equal to the stored count, one mail per request id, the T19 test (section 5) giving one mail, one HubSpot write and one stored row, and every exit code 0 (lead answer 4.6).
- **an audit** = a read-through of the files that lists faults; there are three (core-hardening, flows-audit, system-map). **Blocker / Major / Nit** = most serious / serious / small fault (each audit draws the line a little differently).
- **drift check** = a read-through that lists where two documents disagree (items D-01 to D-20, S-01 to S-07, T-01 to T-06 and L-01 to L-06 in drift/REPORT.md). **flowcheck** = our own check that the five patches apply.

Secrets and limits
- **secret** = any password, token or key. An **app password** opens one mailbox. The **HubSpot read key** and **HubSpot write key** are the long codes the two HubSpot apps give (the files also call them tokens). The **model key** pays for model calls.
- **mailbox A and B** = the two throwaway Gmail accounts: one receives the form mails (the RECEIVER), one sends them (the SENDER). So there are two app passwords, two HubSpot apps (one reads, one writes) and two secret files.
- **spending backstop** (older word: cap) = a dollar limit in the settings file `stage.env`. v5 line 52 says the program does not enforce it and a person checks it. The lead's batch 3 answer 8 says: the limit is the API credits (US$189 prepaid) with an in-code backstop below it, window to Mon 23 Nov 18:29 UTC / 23:59 IST. Whether the program really enforces that backstop: UNVERIFIED until the code is read; until then a person still checks it.
- **stop time** (older pages: window end) = Mon 23 Nov 18:29 UTC / 23:59 IST.

## What you decide today (the lead)
1. Row 1 builder and date are settled (see the answer below); confirm the builders finish on time. TAKE-BLOCKERS.md row 1 is the extension of `fill_flows.py` (BL-wp6-G1, section 5). Row 4 (take date) needs that date. Answered by the lead (batch 3, answer 2): the builders are r37, r38 and r39 (laptop lead agents, not a named person). They finish about 17:15 UTC / 22:45 IST, 18:10 UTC / 23:40 IST and 18:40 UTC / 00:10 IST (Tue 17 Nov); then reviews and the merge chain; re-pin target Tue 17 Nov 08:00 UTC / 13:30 IST
2. Say whether the "rehearsal passed" rule (Words) applies to run (a) the re-smoke, run (b) the filled patched real-v5 run, or both (TAKE-BLOCKERS.md row 2).
3. Answer D-04 and D-05 by replying "D-04 apply, D-05 apply" (or with edits). Core-hardening edits step J (lead answer 14, batch 2). Sources: QUESTIONS.md item 2 and decisions/D04-D05.md. This blocks the post on Wed 25 Nov, not the take.
4. Decide LP-1 (form password, yes or no) and LP-5 (accept that the session can read secrets, or use a second laptop user). LP-4 depends on D-05. LP-1, LP-4 and LP-5 are open and are due Tue 17 Nov 12:29 UTC / 17:59 IST. LP-3 may wait until after the take. LP-2 is answered. All five are in section 3.
5. Start Docker Desktop and run the first laptop rehearsal (the re-smoke) once the final evidence run has passed on the merged head. It does not start today (Mon 16 Nov): the earliest start is about Tue 17 Nov 00:30 UTC / 06:00 IST, and you ask the owner first with the clock times (lead answer 4.5). Wed 18 Nov is not yet confirmed.

## Next action
START WITH TAKE-BLOCKERS.md row 1: builders r37 to r39 (laptop lead agents) extend `fill_flows.py` to the PATCHED real-v5 copy (fill DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO). DESK_URL, DESK_TIMEOUT_MS and DESK_ALERT_TO are three `$env` settings (values the flows read from the environment); BL-wp6-G1 is in section 5.
- Row 3 (four security text edits) and run (a) of row 2 (the re-smoke, run by the lead) run beside row 1. Run (b) of row 2 waits for row 1.
- Then row 4 (take date).
- Then row 5: apply decisions/M17-end-never-deletes.md. Its file name is older than the lead's correction: the take's HubSpot key is read-only and cannot archive or delete, so the program's one archive try is expected to be refused and the contacts are archived or deleted by hand (see section 1, "Still yours, later"). Then the HubSpot lines (check line and date: [LEAD FILLS at re-pin]).
Live status: STATUS-BOARD.md.

## 1. One-minute summary
**Verdict: Wed 18 Nov is NOT yet confirmed.** It cannot be promised until the patched flows that real-v5 uses have run successfully in n8n on the laptop. Nobody has run them.
**Rehearsal time (the one statement):** the lead runs the first rehearsal (decision 12) only after the final evidence run passes on the merged head, earliest about Tue 17 Nov 00:30 UTC / 06:00 IST; the lead asks the owner first, with clock times, before it starts. Allow 3.5 to 4.5 h (2 h 51 min if clean).
**Take timing:** the plan is that the take starts by 17:30 UTC / 23:00 IST at the latest. The program still accepts a start up to 17:40 UTC / 23:10 IST (its formula has no pause term), but the plan time is 17:30 UTC so that a 10-minute pause still ends before the stop time 18:29 UTC / 23:59 IST. The take program refuses a start that leaves less than 49 minutes before the stop time (49 is computed from the lease of 45 seconds, rounded up). Noon UTC (12:00) is the planning target for the start, so a failed take still leaves the afternoon; it is not a promise of a rerun. The earlier 18:14:40 UTC figure is obsolete. The lead's notice must come at least 3 h before the start time named in it.
**Accounts:** nothing new. Steps 1 to 9 are already done by the owner (inputs/FACTS-ALREADY-DONE.md).
**Still yours, later (owner tasks):** typing `y`, the 6-digit number and `end` yourself at the take prompt (the film pause limit of 10 minutes is the owner's own clock alarm; the program does not enforce it). The take's HubSpot key cannot archive or delete (decision 2 of 16 Nov keeps it read-only). After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list. Because the key is read-only, the expected case is that all three contacts are on the printed list. UNVERIFIED until the lead's loopback re-smoke (Tue 17 or Wed 18 Nov, result in egm/duplicate-proof-lead-desk/wp6/): whether the refusal prints cleanly, and whether HubSpot's filtered list shows archived contacts. The clean-up list prints search text take-<tag>-a, -b, -c with the example.com domain; where <tag> first shows on screen is not verified. The other owner tasks: the written yes with numbers before each paid take; the laptop settings; watching the cut; the clean-up revoke after the last take; posting. Details in section 2.
**Finished (reading only, nothing run):** the three audits are written. Flows-audit: 45 faults found, 8 Blocker, 8 Major, 29 Nit; 17 should be fixed before the video, 28 after (flows-audit REPORT.md, top block "Result"). Core-hardening's cross-review of flows-audit found all five flows-audit patches apply (core-hardening REPORT.md, top block "Item 1"). Our own check of the five flow patches: all apply and none breaks the flow graph (flowcheck/REPORT.md:14).
**Open facts, filled as the lead stated (batch 3):** look of the HubSpot accounts and proof-screen choices: [OWNER FILLS]. Who films: the lead's Claude records with Playwright; the owner watches and posts. Backstop line name: core-hardening reads it from stage.env (UNVERIFIED until then). Take profile name and place: [OWNER FILLS at the profile and filming check]; the deadline exception stays UNVERIFIED. Third refill time 17:30 UTC / 23:00 IST; percents M1, M2, M4 to M8, M10 to M13 and M20: [LEAD FILLS at refill from the live state]. Video: recorded Wed 18 Nov earlier that day, posted Wed 18 Nov 15:00 UTC / 20:30 IST. Agent-time estimate to the take: about 2 days. `scripts/n8n_api.py` is in the take repo. Crash test (mail step): required. "Rehearsal passed" covers the loopback re-smoke and the rehearsal. Program notice and prompt text are edited by the fix builders; the lead approves. Login-key choice: closed after the scan (no key found in the seven files; counts only).
**Live status:** see STATUS-BOARD.md.
**Blocked:** TAKE-BLOCKERS row 1: the three `$env` values are not filled into real-v5 (BL-wp6-G1); the builders r37 to r39 have not yet finished (times in section "What you decide today", item 1). Also: no one has run the changed flows in n8n. The cloud session has no running Docker, so every n8n behaviour is untested (flowcheck/REPORT.md:9, flowcheck/evidence/n8n-try.txt). A laptop run is the only fix. The lead starts Docker Desktop.

## 2. The owner's tasks: moved (the old v3 table was removed 16 Nov 2026, round 3)
The old rows 16 to 23 here were written from the stale v3 steps file and contradicted v5 and the cards (clean-up deadline, written-yes contents, "archived" for deleted, a wildcard `shred`, an unsourced US$189 backstop, an incomplete post list, wrong latest-start time). They are removed, not patched, so no one can follow them. One place per job:

| owner task | where it is now |
|---|---|
| written yes with numbers (v5 step A) | OWNER-VIEW.md row 1. The written yes holds three things: the number of model calls (at most 3), the US$ total (3 times the worst-case price of one call) and the stop time (v5:76). The lead's message before it also lists the worst case per call, the money spent so far, the spending backstop and the stop time as in `stage.env`, and the rehearsal result file. The owner compares the money spent so far and the backstop by eye in `stage.env`; they are not in the yes. |
| laptop settings (v5 B) | OWNER-VIEW.md row 2 |
| label, profile (v5 C) | OWNER-RUN-DAY-CARD.md steps 1 to 4; restore at OWNER-CLEANUP-CARD.md step 7. The n8n sign-in is no longer an owner step (decision 7): first-visit setup is done (inputs/FACTS-ALREADY-DONE.md); the lead imports and activates the flows with scripts\n8n_api.py. |
| the run, the pause, `end`, failed run (v5 E, F, G) | OWNER-RUN-DAY-CARD.md steps 8 to 16 (v5 E), 17 to 22 (v5 F), 23 to 25 (v5 G). Run exit codes: 0 pass, 1 wrong answer, 2 refused to start or go on, 3 count or verdict failed (v5 lines 188 to 192). What `end` does: section 1, UNVERIFIED. |
| watch the cut (v5 H) | OWNER-RUN-DAY-CARD.md step 27 (OWNER-VIEW.md row 4) |
| after the run: delete demo mails, "accepted", model key (v5 I) | OWNER-RUN-DAY-CARD.md step 22 (delete by hand, rules in 23 to 25), step 26 ("accepted") and step 28 (model key; step 27 is the cut review, its own row above); then OWNER-CLEANUP-CARD.md |
| clean-up (v5 I) | OWNER-CLEANUP-CARD.md and its release words. The deadline is the lead's own and is NOT the stop time. |
| post (v5 J) | OWNER-VIEW.md row 6: the full must-NOT list and the rule that the lead's exact final words and a check by the lead against the bible rules come first (lead answer 4.4) |
| latest start | plan 17:30 UTC / 23:00 IST; the program still accepts a start up to 17:40 UTC / 23:10 IST; stop time 18:29 UTC / 23:59 IST. The earlier figure 18:14:40 is obsolete (lead order 16:41Z). |

## 3. Decisions only you can make (LP-1 to LP-5)
Test owner is no longer a decision: the lead runs the first rehearsal (decision 12). The other open decisions are in QUESTIONS.md. Due Tue 17 Nov 12:29 UTC / 17:59 IST (a suggestion; the lead may move it): LP-1, LP-4 and LP-5. LP-3 can wait until after the take.
Sources: FINAL-CROSSCHECK.md sections 4 and 8, OS:133-137 (v3; v5 is the current file), flows-audit QUESTIONS.md. The flows-audit questions Q4 to Q9 are already answered by the lead (marked ANSWERED there), so they are not asked again.
- **LP-1. OPEN** (no answer in QUESTIONS.md or decisions of 16 Nov). Should the form address demand a shared code (a "form password": the sender must include it, otherwise the form refuses the request)? It is not an app password and not a HubSpot key. Today anyone who knows the address can send a sales request (flowcheck/REPORT.md:7). Yes: closes that gap, needs a change and a laptop test, which uses time before the filming. No: faster, fine only on your own closed laptop network, and the video must not claim the intake is secure.
- **LP-2. ANSWERED** (lead, Mon 16 Nov 10:13 UTC / 15:43 IST, QUESTIONS.md item 5): after the take, archive, never delete; the lead decides per row. The question was where the old files go and whether each move is agreed. 39 rows: 2 can move once an archive place outside the repository is named, 28 not yet, 9 no (FINAL-CROSSCHECK.md section 6). The archive goes outside the repository, because a repository test fails on banned words in any file inside it (FINAL-CROSSCHECK.md section 6).
- **LP-3. OPEN** (no answer recorded). Keep or archive `extract.py`? Keep: two tests use it, nothing is lost (FINAL-CROSSCHECK.md section 6, row 31). Archive: less code, but the tests must change.
- **LP-4. OPEN** (D-05 pending, QUESTIONS.md item 2; the estimate is unanswered). Narrow claim and the build-time estimate (the throwaway mailboxes are already decided and done). The only claim allowed in the post is "A lead sent twice with the same id is processed once." ("lead" here = sales lead; only a second send with the same request id, inside one take folder). It is NOT yet allowed: it needs a test of the mail-step crash case or your written yes accepting that risk (D-05). Your answer: accept the risk in writing, or wait for the test. Build estimate: about 20 hours on the critical path, about 41 hours in all, both UNMEASURED (OS:135-137; v3; v5 is the current file). Say yes or no to each.
- **LP-5. OPEN** (L-01 text edit applies; the accept-or-second-user choice is not decided). Do you accept in writing that the engineering session can technically read the take's secrets? The rule "the lead never sees a secret" is a working rule, not a lock: the session runs as the same laptop user and can probably decrypt what n8n stores (inferred, not checked: drift/REPORT.md, L-01). Options: (1) accept it, because the accounts are throwaway and the data made up; the clean-up card revokes the two mail app passwords and the two HubSpot apps (OWNER-CLEANUP-CARD.md steps 1 and 2) and the owner revokes the model key (OWNER-CLEANUP-CARD.md step 6a; S9-3, decision 5) (no set-up cost, one live key); (2) keep the secrets under a second laptop user the session cannot read (cost: set-up time before the take). Same for "you alone approve": it is a working rule (L-02). Decide with LP-1 and LP-4 by Tue 17 Nov 12:29 UTC / 17:59 IST.

**Not yours (the lead handles these; you are only told):** patch C-01 extras are cut (decision 4); a minimal price and answer-length check applies only if the take's model program loads Route config (unverified, not in the video path); the order of switching on saved run records and the n8n settings (FINAL-CROSSCHECK.md section 4 rows 1 and 2, section 8); the spending backstop figure (lead answer 8: API credits US$189 prepaid, in-code backstop below it; enforcement UNVERIFIED, so a person still checks it).

## 4. What is NOT verified
1. **The changed flows were never run in n8n.** The take imports the patched real-v5 copy (F-002 and F-008, then fill values); the lead starts Docker and imports it; take prep sends one made-up sales request. "Processed once" stays NOT VERIFIED until test T19 passes. Docker had no running service in the cloud session, so n8n could not start (flowcheck/REPORT.md:9, :22). That the form-address password check, the refusal replies for a missing code (422) and for overload (503), and "stored nothing on a repeat" work is untested.
2. Nothing in the three audits was run against Gmail, HubSpot, mail sending or a model call (flows-audit REPORT.md and core-hardening REPORT.md, top blocks).
3. The click paths in OS (OS:178-193; headed 13, listing 14) are marked UNVERIFIED by their author (OS:7); no live take, Gmail filter or real label behaviour has run (OS:161-166). OS is v3; v5 is the current file.
4. Test counts in OS:151-159 come from an older head (4d7c335) and are not the take's current state; the current head is named in the re-smoke plan (OS:151).
5. Network egress (outside connections) from n8n is switched off by setting names; it is observed, not enforced (QUEUE.md:8). The re-smoke costs US$0 and runs before any real take; the take branches stay on the laptop (QUEUE.md:8).
6. The core-hardening patches were checked with a copy of the guard scan, not the real test (pytest not installed there) (core-hardening REPORT.md, top block). Three files still fail the vendor-word test (its "Item 2").

## 5. Codes used on this page
- T19: the rehearsal test "one sales request posted twice gives one mail and one CRM write" (TAKE-BLOCKERS.md:34).
- F-002: one of the five flows-audit patches, file "F-002-take-key-check-and-claim-error-path"; it edits build_mainframe.py (work/evidence-patches-2.md:6-8). Its effect in plain words: UNVERIFIED (the patch name is the only source; core-hardening names it if it can, lead answer 3). Security rules A, E, F, I and the DESK_* meanings are also UNVERIFIED for the same reason.
- F-008: the flows-audit patch "save runs for the take"; it turns on saving of run records in n8n (work/evidence-patches-2.md:15-17; TAKE-BLOCKERS.md:34).
- C-01: a core-hardening patch; its "extras" are cut and only a minimal price and answer-length check stays, if the take's model program loads Route config (inputs/DECISIONS-2026-11-16.md:5, decision 4). What the rest of the patch fixes: UNVERIFIED.
- D-04: the owner's post says more than the video proves; the only allowed claim is "a lead (sales lead) sent twice with the same id is processed once" (decisions/D04-D05.md:11-16).
- D-05: the limit for a crash between mail send and "finished" mark never reaches the owner, so "crash-safe" must not be claimed (decisions/D04-D05.md:18-20).
- L-01: the rule "the operator never sees a secret" is procedure only, because the session runs as the same laptop user (drift/REPORT.md:97).
- L-02: approval is typing on a terminal the operator can reach, so it is procedure only (drift/REPORT.md:98).
- S9-3: the model key is never revoked; fix is a dedicated key with a provider-side limit plus a revoke line (drift/REPORT.md:146).
- BL-wp6-G1: the blocker-ledger row for "the step that fills DESK_URL, DESK_TIMEOUT_MS and DESK_ALERT_TO into a local copy of the flows is not built" (TAKE-BLOCKERS.md:17).
- ORDER 017: the lead's order of 16 Nov. Every output must remove a risk to the take, prove a claim the video makes, or keep records true (ORDERS.md:68-69).
- 4d7c335: an older code head on which the v3 test counts were recorded; not the current head (inputs/OWNER-STEPS-realrun-v3.md:151-152).
