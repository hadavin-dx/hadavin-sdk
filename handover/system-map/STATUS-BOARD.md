# STATUS BOARD system-map (top: what the lead must do; the log is further down)
UPDATED_UTC: 2026-11-16 20:39
PUSHED_UTC: 2026-11-16 20:39
SESSION: system-map
ORDER: lead order 16:04Z (ORDERS.md lines 177-184): 4 agents on runbook v4.3 patch + 49-minute window check, 4 on my open items (queue mode R461)
BOOT_ID: 5cbee216
ITEMS_TOTAL: 20
ITEMS_OPEN: 15
PERCENT: 83 (the mean of the per-row percent column in the ITEMS table; only 5 of 20 items are fully done; the lead's tool reads this key, so it keeps the name)
STATE: working
BLOCKED: the changed n8n flows have never been run (decision 12: the lead runs the first rehearsal). 1 test fails (a licence-file check, M14; decision 11: licence files are never changed).
NEEDS_YOU, in this order (for the lead session to answer or pass to the studio lead; item 3 may need the owner; paths start at handover/system-map/; times UTC / IST):
  0. CORRECTION 16:12Z: the v4.2 runbook (inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md) and LANE-D-13o/13p/13q/13r/13s.md ARE in the checkout; my earlier 'missing' claim was wrong. Nothing missing now except laptop-only files (run program, run sheet). Patch rebuilt against v4.2 (agents below).
  1. Start Docker and run the first rehearsal of the changed flows (steps: work/t19-and-stored-data-steps.md; about 1.5 h, my estimate, unverified). Start by Tue 17 Nov 03:30 UTC / 09:00 IST (decision 12).
  2. Yes or no. The one check that fails (M14) requires every licence file to be proprietary, but three folders under handover/promotion-inputs hold Apache-2.0 copies. YES = I change only the test so it accepts Apache-2.0 there; the licence files stay unchanged (decision 11: licence files are never changed). NO = the test keeps failing and the take can still go ahead, but the test keeps failing by it. Whether those folders may be relicensed is a separate question for the owner and is NOT asked here. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
  3. ANSWERED by the lead 18:29Z: no paste (SESSION-HANDOFF holds live laptop state and account names). M20 is dropped in the cloud.
  4. Answer the 8 open Blockers in drift/REPORT.md (row M3; they are where two files disagree about what the owner types or when; example: D-01 which n8n the owner types secrets into, D-02 which Postgres password). Default if you stay silent: they stay open and the take is not filmed on them. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
  5. Answer D-04 and D-05 in work/decision-list-for-lead.md. D-04: the public post says more than the decisions and evidence allow (needs one agreed sentence plus a list of forbidden words). D-05: the result of the crash-after-mail test must reach the owner before the post. Default if silent: the post text stays unchanged and is not approved. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
FAILED: M14 test_licences_are_proprietary fails (1 failed, 9390 passed); the n8n run has not happened. Full text under Details at the end of this file. Times in the Details are UTC only; IST is +5:30.
PROGRESS: 5 of 20 table items at 100 percent; mean of the percent column 83 (counted from the ITEMS table on this page). Percent is how far a page has been checked, not confidence the take will work.
Terms: M-number (M3, M14, M20) = a row of the ITEMS table below; D-number (D-01) = a row of drift/REPORT.md, a place where two documents disagree; studio head = a role name from older notes whose meaning is UNVERIFIED; take = the one filmed run (video scope: only scenes 1 to 4, version real-v5, decision 1 of inputs/DECISIONS-2026-11-16.md; decisions 5, 11, 12 are in the same file; film-v5 = the longer version that is not filmed); T19 = the test that sends the same made-up lead twice and expects one mail, one HubSpot write, one stored row (work/t19-terms.md); owner = the human; studio lead = the Claude session that does the technical steps and is the only one that messages the owner; lead session = the Claude session that gives me orders; rehearsal = test run on the laptop without a real account; loopback = a self-check on the lead's own machine before it; helper = a read-only agent that reads one page and lists what it cannot follow (cold read); digest = my short note of a helper's report; ORDER n = a standing order in ORDERS.md.
AGENTS_RUNNING: 2
CAPACITY nproc=4 load=0.18 (read at 2026-11-16 20:39Z) disk: 13G free (floor 6G)
NEXT: finish the 3 running agents only (L-01 fixer, steps r14 readers); verify, digest, fix only Blockers/Majors on the video path; then stop and report (lead order 20:36Z)
INTERRUPTED: none

## VIDEO PATH (lead order 20:36Z, owner cut list): per item, needed for the video yes or no
Rule applied: only agents already running finish; a new round starts ONLY for a Blocker or Major on the video path (the take, money, secrets, the n8n flows); a page whose last review had no Blocker or Major is DONE (Minors listed in REPORT.md, entry 20:40Z); no 100x loops, no mutation runs; 3 agents or fewer.
| item | needed for the video | action |
|---|---|---|
| steps sheet v5 (inputs/OWNER-STEPS-realrun-v5-core-hardening.md, money path) | YES | round-14 readers running; a new fixer only if they report a Blocker or Major |
| L-01 pages (L01, OWNER-VIEW M5, LEAD-PAGE; secrets) | YES | round-13 fixer running; one more round only for a Blocker or Major |
| M1 flowcheck | YES (the n8n flows) | done; n8n run of patched flows still NOT TESTED (lead's rehearsal) |
| M3 drift sections and the 8 Blockers in drift/REPORT.md | YES (where owner-typed things disagree) | no more rounds by me; the lead answers D-01..D-10 |
| M17 end-never-deletes replacement lines | YES (the take deletes nothing; contacts) | written, NOT applied to v5/program: waits the lead; no new round |
| M18 D-04 and D-05 | YES (what the post may claim) | written, awaiting the lead; no new round |
| M19 owner steps read (run-day and clean-up cards) | YES | stop after the steps v5 and L-01 results; no new round unless Blocker/Major |
| RUNBOOK-V4.3-PATCH (work/) | YES (runbook rows) | done at the reader cap; waits r41 (overdue), r42; r43 cancelled |
| resmoke list, DECISION-one-store, AGENT-SCOPE | YES but DONE (reader cap) | no more rounds; the stale step-file line cites in drift/REPORT.md and the resmoke list are a Minor, listed in REPORT.md |
| M14 licence test (1 failing) | NO | not video path; waits the lead's yes; I never edit the test |
| M2 FINAL-CROSSCHECK round 2 | NO | stop; not run |
| M4 MASTER-MAP, ONE-PLACE-TABLE | NO | stop; archive after the take (ARCHIVE-CUT-LIST.md) |
| M5 earlier OWNER-VIEW rounds | covered by L-01 row | see L-01 row |
| M6 own tools audit, M7, M9 stale items | NO | stop |
| M8, M15 archive cut list | NO | one list for the owner to sign after the take |
| M10 second-reader ring | NO | stop |
| M11, M12, M13, M16 | NO (done) | done |
| M20 SESSION-HANDOFF live state | NO | dropped 18:29Z |
Archive: items marked NO are stopped; nothing is moved or deleted now (the owner signs ARCHIVE-CUT-LIST.md after the take).

## ITEMS
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| M1 | flowcheck and third read | done | 100 | flowcheck/REPORT.md | n8n run of patched flows NOT TESTED (no Docker here) |
| M2 | FINAL-CROSSCHECK.md | reviewed round 1, fixes applied; round 2 not run | 80 | FINAL-CROSSCHECK.md | round 2 not run |
| M3 | drift check of take documents | sections 1-13 written | 92 | drift/REPORT.md | 8 Blockers in drift/REPORT.md row 101; need the studio lead |
| M4 | MASTER-MAP and ONE-PLACE-TABLE | round 1 fixes applied; some rows not yet aligned | 90 | MASTER-MAP.md | |
| M5 | OWNER VIEW | rewritten round 2 (7 table rows; claim narrowed, `end` deletes nothing, message order fixed); round 2 read running | 90 | OWNER-VIEW.md | |
| M6 | R460 audit of own tools | scan_outputs and write_outputs fixed; 74 tests OK (python3 -m unittest discover -s tests, 16 Nov) | 90 | work/review-r460-tools.md | row-number keying open |
| M7 | stale done items | applied | 95 | drift/REPORT.md section 6 | |
| M8 | archive cut list | draft; reconciliation note added (M15); one list to sign after the take | 85 | ARCHIVE-CUT-LIST.md | |
| M9 | done items listed open | covered by M7 | 90 | drift/REPORT.md section 6 | |
| M10 | second-reader ring | partly done, fresh round running | 60 | rings/RING-LOG.md | |
| M11 | FACTS-ALREADY-DONE sweep | DONE (drift section 11) | 100 | drift/REPORT.md | |
| M12 | video-date sweep | DONE (drift section 11) | 100 | drift/REPORT.md | |
| M13 | three-way consistency | DONE (drift section 12) | 100 | drift/REPORT.md | |
| M14 | heavy lane in fresh clone | ran twice; latest head: 1 real failure (licence files) still open, see FAILED | 90 | /tmp/sm-fresh2.pytest.log | |
| M15 | cut list reconcile | reconciliation note added to ARCHIVE-CUT-LIST.md; one list to sign after the take | 80 | ARCHIVE-CUT-LIST.md | |
| M17 | end never deletes: replacement lines | written (not applied to v5 or the program) | 70 | decisions/M17-end-never-deletes.md | v5 and the program text still say delete |
| M18 | D-04 and D-05 | written, awaiting the lead | 90 | decisions/D04-D05.md | |
| M19 | independent read of the owner steps | cold reads of the card and OWNER-VIEW done, fixes applied; round 2 running | 60 | work/agent-reports-batch3.md | |
| M20 | SESSION-HANDOFF live state | DROPPED by lead 18:29Z (no paste; the lead checks the pages against it on the laptop later if time allows) | 0 | | none in the cloud |
| M16 | flow-set question | DONE, closed by decision 1 (real-v5 only; film-v5 out) | 100 | flowset/REPORT.md | |

## AGENTS
- a82accddcb36455f9 | steps v5 round-14 fixer (money path, video path YES) | started about 20:44Z | running | expected end about 21:05Z | next: verify wc, master sentence x2, FILL vs rows, then mark DONE unless a Blocker remains
- aa5fd0a3bdaf02fcf | L-01 round-13 fixer (security path, new stamp 23:15Z) | started about 20:32Z | running (overdue vs 20:45Z) | next: verify stamp, md5, 11-block identity
## EMPTY SLOTS
- 3rd slot: empty, cut list (lead order 20:36Z) allows no new round except a video-path Blocker/Major fix; no reader needed until both fixers report

## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
