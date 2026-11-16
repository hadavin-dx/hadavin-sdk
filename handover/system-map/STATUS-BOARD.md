# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T11:56:41Z (17:26 IST)
SESSION: system-map
ORDER: 017-028 read (ORDER 028 at 11:31Z: start up to 8, name them here); lead ANSWER 10:23Z item 8 (pause stays) read; no Q22 text exists in ORDERS.md or inputs/
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 20
ITEMS_OPEN: 15 (rows below 100 percent: M2-M10, M14, M15, M17-M20; 5 rows are at 100). CORRECTION: my earlier "14" and "6 at 100" were wrong; recounted by script at 11:36Z over the 20 rows. PERCENT mean of the table is 83.1 (sum 1662 over 20 rows), not 83.6. M3, M4, M6 queue tags now match the board (checked 11:26Z, digest 152); M9 and M15 queue tags say DONE while the board says 90 and 80 percent (digest 152)
PERCENT: 83.1 (script recount: 1662 / 20; the earlier 83.6 was wrong)
AGENTS_RUNNING: 8 running (all started 11:56:41Z; table below). ORDER 035 read.
INTERRUPTED: none
NEXT: digested through 410. Collect hand-backs as 308 on, refill to 8 in the same turn one ends. Then: open-items-table fixes, decision-list rows still lacking names, CORRECTIONS item 7, end-delete-cases case B closed by decision 2.
CAPACITY: nproc 4, load low, RAM under 1 GB used of 16087 MB, disk 45% used (22 GB free of 252 GB at the work volume); top disk users I made: work 2.3 MB, reviews-of-core-hardening 0.4 MB, nothing else; freed 0 MB (no clean-up needed). ORDER 031 applied.
NEEDS_YOU (lead; plain words, UTC / IST): (1) Start Docker and run the first rehearsal of the changed flows; nothing has run them yet (decision 12). (2) Say whether the three Apache-2.0 licence copies under handover/promotion-inputs may stay as they are; decision 11 says never re-license, so this is a yes/no on whether the one failing licence test is changed, not the files. (3) Paste the SESSION-HANDOFF text into inputs/ by Tue 17 Nov 12:00 UTC / 17:30 IST, or that check (M20, stuck at 0 percent) is dropped. (4) Answer the 8 open Blockers in drift/REPORT.md (M3) and D-04/D-05. (5) Answer the decision list work/decision-list-for-lead.md; run (a) was due Mon 16 Nov 13:00 UTC / 18:30 IST.
FAILED: M14 test_licences_are_proprietary fails (1 failed, 9390 passed); the n8n run has not happened. Full text under Details at the end of this file. Times in the Details are UTC only; IST is +5:30.
PUSHED_UTC: 2026-11-16T11:56:41Z

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
| M20 | SESSION-HANDOFF live state | BLOCKED: file is on the studio laptop, not in the repo | 0 | | the lead pastes the text into inputs/; the lead has set no date |
| M16 | flow-set question | DONE, closed by decision 1 (real-v5 only; film-v5 out) | 100 | flowset/REPORT.md | |

## AGENTS (ORDER 028/035: 8 running; last checked 2026-11-16T11:56:41Z)
| agent id | purpose | started (UTC) | expected end | state | produced so far |
|---|---|---|---|---|---|
| a86c4caf499195ff6 | re-read work/rehearsal-passed-limits-draft.md (rewritten 11:57Z) | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| ac713cbf17d052706 | re-read work/not-checked-r2.md (rewritten 11:58Z) | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| ab30df66c15d67526 | cold read work/open-items-table.md round 3 | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| a4ece75922e199384 | cold read work/end-delete-cases.md round 2 | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| a569b6ba67cffd1ab | cold read work/decision-list-for-lead.md round 6 | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| a4b2e785a0ede826c | cold read work/critical-path-r1.md round 2 | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| a6702e8edee78f4ff | cold read work/t19-and-stored-data-steps.md | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |
| a76377943038093a3 | cold read PLAN-002.md round 4 | 11:56:41Z | about 12:26 +5 min | running | nothing yet (report arrives as a hand-back) |

NEXT 5 tasks I would start with more capacity: (1) cold read work/cleanup-card-held-edits.md; (2) cold read reviews-of-core-hardening/CORRECTIONS.md after I fix it; (3) cold read reviews-of-core-hardening/REVIEW.md; (4) cold read work/banned-claims.md after sources are added; (5) cold read work/premortem-r1.md. None waits on an answer from the lead.

Words: UTC = world time; IST = UTC plus 5 h 30 min. Cold read = an agent reads one page with no background and lists what it cannot follow. Held = a finding on a page that belongs to the lead, which I do not edit.

## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
