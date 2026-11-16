# START HERE (system-map folder)
STATE AS OF Mon 16 Nov 2026 09:35 UTC / 15:05 IST. Goal: a safe filmed take on Wed 18 Nov 2026, made-up data only. Wed 18 Nov is NOT yet confirmed.
WARNING: the CURRENT owner steps are inputs/OWNER-STEPS-realrun-v5-core-hardening.md (letters A to J, written Mon 16 Nov); the older inputs/OWNER-STEPS-realrun-v3.md (OS) is superseded and stale at steps 7 and 8 (wrong n8n port, database password model, HubSpot key rights; drift/REPORT.md D-01, D-02, D-03) and in its schedule (D-10, 'Wed to Sun'). Steps 1 to 9 are already done by the studio head (inputs/FACTS-ALREADY-DONE.md). Follow only the owner steps the studio lead re-issues in the chat.

## BEFORE THE TAKE: the one open list (16 Nov 2026, about 12:00 UTC / 17:30 IST; every item blocks the take)
1. Take date and start time (v5 gives none; target Wed 18 Nov, not confirmed).
2. A named person to start Docker and run the first rehearsal (the five changed flows have never run in n8n).
3. Security edits S9-1 to S9-5 and S9-12 applied in v5 and the scope sheet by core-hardening (list: drift/APPLIED-S9.md).
4. Flow-set decision A, B, C and D (flowset/REPORT.md); default: two separate sessions, no live switch.
5. HubSpot key must be able to delete contacts (drift R8-5), plus the HubSpot check and login-key choice (OWNER-VIEW row 7; the exact lines do not exist yet: the studio lead writes them or removes the row).
6. The two failing guard tests on core-hardening (not a take blocker, blocks a pull request).
Owner pages: OWNER-VIEW.md, then the two cards. Everything else here is for the studio lead.

## If you are the studio head
Read OWNER-VIEW.md (one page, owner-only items). The lead brings you any decision as a single yes or no; the decision list is in LEAD-PAGE.md section 3. For the lead: decide by Tue 17 Nov 12:29 UTC / 17:59 IST (a suggested time; if you cannot, the take moves, latest Mon 23 Nov 18:29 UTC / 23:59 IST): item 1 name the test owner and a start time; items 5 and 6a as written there (D-05 and L-01 are your decisions too). Item 3 (archive of extract.py) is a clean-up choice and can wait until after the take. The take time on Wed 18 is set by the lead at least 3 hours ahead.

## If you are the studio lead (the Claude session that does the technical steps)
1. FIRST: the numbered list "BEFORE THE TAKE" above is your to-do list (the old block "LEAD ACTIONS NEEDED" exists only in STATUS-BOARD.template.md and is not used). Order: item 2 (a person with a laptop must start Docker and n8n; the cloud session has none, so you ask the studio head to name that person), then item 5 (HubSpot delete rights), then item 3 and 4.
2. drift/REPORT.md: apply or reject the replacement texts for D-01 to D-05, D-10, S-03 and L-01 (Blockers).
3. FINAL-CROSSCHECK.md sections 2, 4 and 5: ratings that disagree and fixes that collide.
4. QUESTIONS.md: open questions to you.

## Reference (not needed for the take)
SWEEP.md (findings and fix plan), ONE-PLACE-TABLE.md (one place per job), MASTER-MAP.md (every component), ARCHIVE-CUT-LIST.md (what to archive after the take, never delete), REPORT.md and QUEUE.md (this session's logs), work/ (evidence).
Role of this folder: cloud session system-map writes only here, on branch cloud/system-map. ORDERS.md is written by the lead.

## Words used on these pages (one meaning each)
*Studio head* = the owner. *Studio lead* = the Claude session that does the technical steps (called "lead"; older pages say "laptop lead"). *Rehearsal* = a test run with stand-in programs and no real account (older pages: "laptop trial", "re-smoke"). *Take* = the one recorded real run. *Stop time* = last allowed minute, Mon 23 Nov 18:29 UTC / 23:59 IST (older pages: "window end"). *v5* = inputs/OWNER-STEPS-realrun-v5-core-hardening.md; *v3* = the stale older file. *core-hardening*, *flows-audit*, *system-map* = other Claude sessions, each on its own branch. *S9-n* = security item n of drift/REPORT.md section 9; the edit texts are in drift/APPLIED-S9.md. *Flow set* = a folder of n8n flows (real-v5 or film-v5, see flowset/REPORT.md).

## Which page wins, and which to skip
Owner steps: OWNER-VIEW.md and the two cards win over LEAD-PAGE.md section 2 (stale, v3-based). If two pages disagree on a number, v5 wins, then drift/APPLIED-S9.md once applied. Skip: work/, reviews-of-core-hardening/, flowcheck/in, egm-dryrun*, inputs/OWNER-STEPS-realrun-v3.md and the v4 difflist, and the Reference list above.
Known conflict, not yet fixed: LEAD-PAGE.md rows 16 to 23 (v3) list different written-yes numbers, "archived" wording and a cleanup deadline of the stop time; the cards and OWNER-VIEW are the truth. The cleanup deadline is set by the studio lead and must be before the stop time.
