# STATUS BOARD system-map (top: what the lead must do; the log is further down)
UPDATED_UTC: 2026-11-16T15:49Z
PUSHED_UTC: 2026-11-16T15:49Z
SESSION: system-map
ORDER: 14:48Z (parallel re-readers while I fix; keep 8 running)
BOOT_ID: 5cbee216
ITEMS_TOTAL: 20
ITEMS_OPEN: 15
PERCENT: 25 (items at 100 percent: 5 of 20; the mean of the per-row percent column is 83; the lead's tool reads this key, so it keeps the name)
STATE: WORKING (video scope: real-v5 only, scenes 1 to 4, decision 1)
BLOCKED: the changed n8n flows have never been run (decision 12: the lead runs the first rehearsal). 1 test fails (a licence-file check, M14; decision 11: licence files are never changed).
NEEDS_YOU, in this order (for the lead session to answer or pass to the studio lead; item 3 may need the owner; paths start at handover/system-map/; times UTC / IST):
  1. Start Docker and run the first rehearsal of the changed flows (steps: work/t19-and-stored-data-steps.md; about 1.5 h, my estimate, unverified). Start by Tue 17 Nov 03:30 UTC / 09:00 IST (decision 12).
  2. Yes or no. The one check that fails (M14) requires every licence file to be proprietary, but three folders under handover/promotion-inputs hold Apache-2.0 copies. YES = I change only the test so it accepts Apache-2.0 there; the licence files stay unchanged (decision 11: licence files are never changed). NO = the test keeps failing and the take is not blocked by it. Whether those folders may be relicensed is a separate question for the owner and is NOT asked here. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
  3. Yes or no: will you paste the SESSION-HANDOFF text (the notes about live state that exist only on your laptop) into inputs/? Row M20 checks the pages against it; without it M20 cannot be done and I drop it. Reply by Tue 17 Nov 12:00 UTC / 17:30 IST.
  4. Answer the 8 open Blockers in drift/REPORT.md (row M3; they are where two files disagree about what the owner types or when; example: D-01 which n8n the owner types secrets into, D-02 which Postgres password). Default if you stay silent: they stay open and the take is not filmed on them. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
  5. Answer D-04 and D-05 in work/decision-list-for-lead.md. D-04: the public post says more than the decisions and evidence allow (needs one agreed sentence plus a list of forbidden words). D-05: the result of the crash-after-mail test must reach the owner before the post. Default if silent: the post text stays unchanged and is not approved. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
FAILED: M14 test_licences_are_proprietary fails (1 failed, 9390 passed); the n8n run has not happened. Full text under Details at the end of this file. Times in the Details are UTC only; IST is +5:30.
PROGRESS: 5 of 20 table items at 100 percent; mean of the percent column 83 (counted from the ITEMS table on this page). Percent is how far a page has been checked, not confidence the take will work.
Terms: take = the one filmed run (video scope: only scenes 1 to 4, version real-v5, decision 1 of inputs/DECISIONS-2026-11-16.md; decisions 5, 11, 12 are in the same file; film-v5 = the longer version that is not filmed); T19 = the test that sends the same made-up lead twice and expects one mail, one HubSpot write, one stored row (work/t19-terms.md); owner = the human; studio lead = the Claude session that does the technical steps and is the only one that messages the owner; lead session = the Claude session that gives me orders; rehearsal = test run on the laptop without a real account; loopback = a self-check on the lead's own machine before it; helper = a read-only agent that reads one page and lists what it cannot follow (cold read); digest = my short note of a helper's report; ORDER n = a standing order in ORDERS.md.
AGENTS_RUNNING: 8 of 8 at 2026-11-16T15:49Z (list below)
CAPACITY nproc=4 load=0.17 disk: 18G free
NEXT: fix my own pages from the board reader's findings (licence question wording, NEEDS_YOU 4 and 5 subjects), work/GLOSSARY.md (heading of the unknown-terms table), decisions/M17-end-never-deletes.md, T19 inline glossary; then 8 fresh readers, one per fixed page
INTERRUPTED: none

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

## AGENTS
| Slot | Agent | Job (read only, cold reader of work/ page) | State |
|---|---|---|---|
| 1 | reader | L1.md (a1e0e7ec137bf34c7) | running |
| 2 | reader | L3.md (a8542dc2103b369f4) | running |
| 3 | reader | BRIEF-EVIDENCE-1.md (a1d91591410eddad8) | running |
| 4 | reader | fixed decision-list-for-lead.md (new) | running |
| 5 | reader | L5.md (new) | running |
| 6 | reader | L2c.md (new) | running |
| 7 | reader | L3c.md (new) | running |
| 8 | reader | L4c.md (new) | running |
Closed and digested through 1899. Fix queue (mine): banned-claims collapse, BRIEF-LANE in-force line, L1c/L2/L4 key wording (no new status word), L6 coverage, drift/REPORT counts, merged-findings, review-r460-tools, T19 header, GLOSSARY. Held-page findings go to LEAD-NOTICE.

## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
