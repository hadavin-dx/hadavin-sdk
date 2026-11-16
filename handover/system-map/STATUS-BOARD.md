# STATUS BOARD system-map (top: what the lead must do; the log is further down)
UPDATED_UTC: 2026-11-16T15:00:56Z
PUSHED_UTC: 2026-11-16T15:00:56Z
SESSION: system-map
STATE: WORKING (video scope: real-v5 only, scenes 1 to 4, decision 1)
BLOCKED: the changed n8n flows have never been run (decision 12: the lead runs the first rehearsal). 1 test fails (a licence-file check, M14; decision 11: licence files are never changed).
NEEDS_YOU, in this order (studio lead; one action each; times UTC / IST):
  1. Start Docker and run the first rehearsal of the changed flows (steps: work/t19-and-stored-data-steps.md; about 1.5 h, my estimate, unverified). Start by Tue 17 Nov 03:30 UTC / 09:00 IST (decision 12).
  2. Yes or no: may the system-map session change the failing licence test so it accepts the three Apache-2.0 licence copies under handover/promotion-inputs? Yes = the files stay unchanged and only the test changes. No = the test stays failing. Reply by Tue 17 Nov 06:00 UTC / 11:30 IST. Decision 11 forbids changing the files.
  3. Yes or no: will you paste the SESSION-HANDOFF text (the live-state text on your laptop) into inputs/? Reply by Tue 17 Nov 12:00 UTC / 17:30 IST. If no, I drop row M20.
  4. Answer the 8 open Blockers in drift/REPORT.md (row M3). Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
  5. Answer D-04 and D-05 in work/decision-list-for-lead.md (the questions are written there). Reply by Tue 17 Nov 06:00 UTC / 11:30 IST.
FAILED: M14 test_licences_are_proprietary fails (1 failed, 9390 passed); the n8n run has not happened. Full text under Details at the end of this file. Times in the Details are UTC only; IST is +5:30.
PROGRESS: 5 of 20 table items at 100 percent (M1, M11, M12, M13, M16); mean about 83 percent. Percent is how far a page has been checked, not confidence the take will work.
Terms: take = the one filmed run; rehearsal = test run on the laptop without a real account; loopback = a self-check on the lead's own machine before it; helper = a read-only agent that reads one page and lists what it cannot follow (cold read); digest = my short note of a helper's report; ORDER n = a standing order in ORDERS.md.
AGENTS_RUNNING: 8 of 8 (2026-11-16T14:52:51Z)
CAPACITY nproc=4 load=0.17 disk: 18G free
NEXT: hand-backs digested through 1636. Next 5 independent tasks: fix L5ac old lines 2-8; fix GLOSSARY Majors (digest 1545); fix L5b; fix v5-edits-for-M17; fix decision-list-for-lead rows.
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
UPDATED_UTC: 2026-11-16T15:00:08Z | PUSHED_UTC: 2026-11-16T15:00:08Z
Running (8): L3c 1-60 (a8eeb0ab3459f8777); L6 100-end (a936f38d048b990c5); six new: not-checked-r2, open-items-table, ARCHITECTURE-AUDIT-CHECKLIST, banned-claims-clean, end-delete-cases, t19-terms (ids in session list).
Closed and digested 1633-1636: abd14a3aa42add6ae, a96dc65fdf92a6490, ae8e634b8aca10ceb, a0603595fe6a76adf. Earlier 1631-1632: a602134eee67160a4, a8b6a4cf908a8ee42. Earlier 1625-1630: a9736197cd289fa57, aaaccbd483fcb454b, a93921ab4f6712335, acdf230aa66f521d2, a53053c9c98bb5c86, ac42d4d03f5ceca39.
FINDING: readers of later ranges cannot see the KEY at the top. Class fix: a REMINDER line (job keys, take, DECISION, UNVERIFIED) now sits under every section heading on all 12 pages. Not yet proven by a re-read.
CAPACITY: 8 of 8. No missing slots.
NEXT 5: claim column for L3 Findings and merged-findings L3 rows; L1 blank line 334, FD-021, FD-025; L5b status line and void findings FD-003 to 005; group note with grep patterns above 71-row tables; L1c finding sentences. Held-page items (1580, 1582, 1588) to LEAD-NOTICE.


## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
