# START HERE (system-map folder)
STATE AS OF Mon 16 Nov 2026 (updated 2026-11-16T10:35Z, after the lead's 10:23Z answer) (IST = UTC+5:30). Goal: one filmed take, made-up data only, by Mon 23 Nov 18:29 UTC / 23:59 IST (the stop time). Wed 18 Nov is only a target and is NOT confirmed. Dates: TAKE-BLOCKERS.md (Dates paragraph) is the one source.
**NEXT ACTION:** the studio lead starts TAKE-BLOCKERS.md row 1: fill DESK_URL, DESK_TIMEOUT_MS and DESK_ALERT_TO into a local copy of the PATCHED real-v5 flows. Row 1 has no named builder and no finish date yet (UNVERIFIED who). Row 3 and run (a) of row 2 can run beside it; run (b) of row 2 waits for row 1; then row 4 (take date), then row 5.
**BLOCKED:** (1) row 1: the fill step is not built (blocker BL-wp6-G1, TAKE-BLOCKERS.md). (2) The patched flows have never run in n8n (the cloud session has no Docker; the studio lead runs the laptop rehearsal), so Wed 18 Nov is NOT confirmed. (3) "Processed once" is NOT VERIFIED until test T19 passes (work/t19-and-stored-data-steps.md is a proposal, not yet runnable).
**DECIDED (16 Nov, lead 10:13Z, 10:20Z, 10:23Z):** real-v5 only, film-v5 out; the take never deletes (`end` lists leftovers, the owner deletes by hand); the take imports the patched copy; the film pause stays; the studio lead starts Docker and runs the first rehearsal; take prep is ONE made-up lead. Open: QUESTIONS.md item 2 only (post wording; blocks the post, not the take).
WARNING: the CURRENT owner steps are inputs/OWNER-STEPS-realrun-v5-core-hardening.md (letters A to J, written Mon 16 Nov); the older inputs/OWNER-STEPS-realrun-v3.md (OS) is superseded and stale at steps 7 and 8 (wrong n8n port, database password model, HubSpot key rights; drift/REPORT.md D-01, D-02, D-03) and in its schedule (D-10, 'Wed to Sun'). Steps 1 to 9 are already done by the studio head (= v3 Phase 0; inputs/FACTS-ALREADY-DONE.md lines 3 and 5). Follow only the owner steps the studio lead re-issues in the chat.

## BEFORE THE TAKE: where each job lives (one place per job)
- What to DO next: TAKE-BLOCKERS.md (the only to-do list; five rows, with the work order under the table).
- What to DECIDE: QUESTIONS.md (the only decision list; one deadline per item).
- Where things STAND: STATUS-BOARD.md (agents, failures, session work).
- Owner pages: OWNER-VIEW.md, then the two cards. Everything else in this folder is for the studio lead.

## If you are the studio head
Read OWNER-VIEW.md (one page, owner-only items). The lead brings you any decision as a single yes or no; the decision list is in QUESTIONS.md. The decisions and their deadlines are in QUESTIONS.md; the studio lead sets the take time at least 3 hours ahead.

## If you are the studio lead (the Claude session that does the technical steps)
1. FIRST: TAKE-BLOCKERS.md is your to-do list. Its order: START WITH ROW 1 (patched real-v5 copy, then fill the `$env` values); rows 1 and 3 and run (a) of row 2 run in parallel, but run (b) of row 2 waits for row 1 (row 2 = the rehearsals; run (a) is the first rehearsal, which the studio lead runs, decision 12; row 3 = the four security text edits); then row 4 (take date); then row 5 (apply decisions/M17-end-never-deletes.md, then the HubSpot lines). Scope is decided: real-v5 only (decision 1). The studio lead starts Docker Desktop (plan-wp6-resmoke-v5.md:489; decided, lead 10:13Z item 3). The cloud session has no Docker.
2. drift/REPORT.md: APPLY D-01 to D-03, D-10, S-03, L-01 as text edits (lead 10:13Z). D-04 and D-05: decisions/D04-D05.md, the lead decides; post only, not a take blocker.
3. FINAL-CROSSCHECK.md sections 2, 4 and 5: ratings that disagree and fixes that collide.
4. QUESTIONS.md: only item 2 (D-04, D-05) is open; item 8 (film pause) is answered (lead 10:23Z).

## Reference (not needed for the take)
SWEEP.md (findings and fix plan), ONE-PLACE-TABLE.md (one place per job), MASTER-MAP.md (every component), ARCHIVE-CUT-LIST.md (what to archive after the take, never delete), REPORT.md and QUEUE.md (this session's logs), work/ (evidence).
Role of this folder: cloud session system-map writes only here, on branch cloud/system-map. ORDERS.md is written by the lead.

## Words used on these pages (one meaning each)
*Studio head* = the owner. *Studio lead* = the Claude session that does the technical steps Older pages say "lead" or "laptop lead". Always write "studio lead". Sales lead = a made-up customer enquiry the demo handles; never write "lead" alone. *Rehearsal* = a test run with stand-in programs and no real account (older pages: "laptop trial", "re-smoke"). *Take* = the one recorded real run. *Stop time* = last allowed minute, Mon 23 Nov 18:29 UTC / 23:59 IST (older pages: "window end"). *v5* = inputs/OWNER-STEPS-realrun-v5-core-hardening.md; *v3* = the older owner-steps file, archived and replaced by v4 and later (decision 10). *core-hardening*, *flows-audit*, *system-map* = other Claude sessions, each on its own branch. *S9-n* = security item n of drift/REPORT.md section 9; the edit texts are in drift/APPLIED-S9.md. *Flow set* = a folder of n8n flows. This video uses only real-v5; film-v5 is out of scope (decision 1).

## Which page wins, and which to skip
Owner steps: OWNER-VIEW.md and the two cards win; LEAD-PAGE.md section 2 is only a table of pointers to them. Precedence, one rule: the owner steps the studio lead re-issues in the chat win; otherwise v5 wins, then drift/APPLIED-S9.md once applied; TAKE-BLOCKERS.md wins over any other to-do list. Skip: work/, reviews-of-core-hardening/, flowcheck/in, egm-dryrun*, the archived v3 and the v4 difflist, and the Reference list above.
LEAD-PAGE.md section 2 was replaced on 16 Nov by a table of pointers to the cards (the old v3 rows are gone). The clean-up deadline is the studio lead's own and is NOT the stop time (v5 line 46).
