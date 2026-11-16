# START HERE (system-map folder)
STATE AS OF Mon 16 Nov 2026 09:35 UTC / 15:05 IST. Goal: one safe filmed take, made-up data only, by Mon 23 Nov 18:29 UTC / 23:59 IST (the stop time). Wed 18 Nov is only a target and is NOT confirmed. Dates: TAKE-BLOCKERS.md (Dates paragraph) is the one source.
WARNING: the CURRENT owner steps are inputs/OWNER-STEPS-realrun-v5-core-hardening.md (letters A to J, written Mon 16 Nov); the older inputs/OWNER-STEPS-realrun-v3.md (OS) is superseded and stale at steps 7 and 8 (wrong n8n port, database password model, HubSpot key rights; drift/REPORT.md D-01, D-02, D-03) and in its schedule (D-10, 'Wed to Sun'). Steps 1 to 9 are already done by the studio head (inputs/FACTS-ALREADY-DONE.md). Follow only the owner steps the studio lead re-issues in the chat.

## BEFORE THE TAKE: where each job lives (one place per job)
- What to DO next: TAKE-BLOCKERS.md (the only to-do list; seven rows, with the work order under the table).
- What to DECIDE: QUESTIONS.md (the only decision list; one deadline per item).
- Where things STAND: STATUS-BOARD.md (agents, failures, session work).
- Owner pages: OWNER-VIEW.md, then the two cards. Everything else in this folder is for the studio lead.

## If you are the studio head
Read OWNER-VIEW.md (one page, owner-only items). The lead brings you any decision as a single yes or no; the decision list is in LEAD-PAGE.md section 3. The decisions and their deadlines are in QUESTIONS.md; the studio lead sets the take time at least 3 hours ahead.

## If you are the studio lead (the Claude session that does the technical steps)
1. FIRST: TAKE-BLOCKERS.md is your to-do list. Its order: decide the scope question (row 3), then rows 1 and 2 in parallel, then the date (row 5), HubSpot delete rights and exact lines (row 7), the security edits (row 6), and row 4 only if film-v5 stays. You name the person with a laptop who starts Docker and n8n; if you know nobody, you ask the studio head (the owner) once. The cloud session has no Docker.
2. drift/REPORT.md: apply or reject the replacement texts for D-01 to D-05, D-10, S-03 and L-01 (Blockers).
3. FINAL-CROSSCHECK.md sections 2, 4 and 5: ratings that disagree and fixes that collide.
4. QUESTIONS.md: open questions to you.

## Reference (not needed for the take)
SWEEP.md (findings and fix plan), ONE-PLACE-TABLE.md (one place per job), MASTER-MAP.md (every component), ARCHIVE-CUT-LIST.md (what to archive after the take, never delete), REPORT.md and QUEUE.md (this session's logs), work/ (evidence).
Role of this folder: cloud session system-map writes only here, on branch cloud/system-map. ORDERS.md is written by the lead.

## Words used on these pages (one meaning each)
*Studio head* = the owner. *Studio lead* = the Claude session that does the technical steps (called "lead"; older pages say "laptop lead"). *Rehearsal* = a test run with stand-in programs and no real account (older pages: "laptop trial", "re-smoke"). *Take* = the one recorded real run. *Stop time* = last allowed minute, Mon 23 Nov 18:29 UTC / 23:59 IST (older pages: "window end"). *v5* = inputs/OWNER-STEPS-realrun-v5-core-hardening.md; *v3* = the stale older file. *core-hardening*, *flows-audit*, *system-map* = other Claude sessions, each on its own branch. *S9-n* = security item n of drift/REPORT.md section 9; the edit texts are in drift/APPLIED-S9.md. *Flow set* = a folder of n8n flows (real-v5 or film-v5, see flowset/REPORT.md).

## Which page wins, and which to skip
Owner steps: OWNER-VIEW.md and the two cards win over LEAD-PAGE.md section 2 (stale, v3-based). Precedence, one rule: the owner steps the studio lead re-issues in the chat win; otherwise v5 wins, then drift/APPLIED-S9.md once applied; TAKE-BLOCKERS.md wins over any other to-do list. Skip: work/, reviews-of-core-hardening/, flowcheck/in, egm-dryrun*, inputs/OWNER-STEPS-realrun-v3.md and the v4 difflist, and the Reference list above.
LEAD-PAGE.md section 2 was replaced on 16 Nov by a table of pointers to the cards (the old v3 rows are gone). The clean-up deadline is the studio lead's own and is NOT the stop time (v5 line 46).
