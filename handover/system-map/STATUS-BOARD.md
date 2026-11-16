# STATUS BOARD system-map (top: what the lead must do; the log is further down)
UPDATED_UTC 2026-11-16T14:03:59Z
PUSHED_UTC 2026-11-16T14:03:59Z
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
AGENTS_RUNNING: 8 (the minimum is 8)
CAPACITY nproc=4 load=0.17 disk: 18G free
NEXT: hand-backs digested through 1364 (a digest = one short line in work/agent-reports-batch4.md for each helper report). Findings on pages the lead holds are in that file for the lead. Next 5 independent tasks: fold L1c, merged-findings, L5b, L4c and FINAL-CROSSCHECK (fold = move old stacked notes into a history file and keep the live text).
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
| agent id | purpose | started (UTC) | expected end | state | what it produced so far |
|---|---|---|---|---|---|
| aa8d7e3fa605b0f29 | structural read GLOSSARY | ~14:05 | ~14:15 | running | nothing yet |
| ac20e39eb9c3837b8 | style read decision-list | ~14:05 | ~14:15 | running | nothing yet |
| a6f2385635e1916fe | style read LEAD-NOTICE | ~14:05 | ~14:15 | running | nothing yet |
| adba2c50d99348a81 | structural read premortem-r1 | ~14:05 | ~14:15 | running | nothing yet |
| a3a27acaabd15c948 | structural read critical-path-r1 | ~14:05 | ~14:15 | running | nothing yet |
| a640b199bda198f21 | zoom-out read end-delete-cases | ~14:05 | ~14:15 | running | nothing yet |
| aa8b00dd14a3b69c0 | structural read merged-findings | ~14:05 | ~14:15 | running | nothing yet |
| af59d34f5249172b2 | structural read t19-gap-facts | ~14:05 | ~14:15 | running | nothing yet |

CAPACITY: 8 running. Next 5: fix BRIEF-EVIDENCE-1/2; banned-claims stub; open-items-table How-to-read; evidence file headers; GLOSSARY shrink.

Words: UTC = world time; IST = UTC plus 5 h 30 min. Cold read = an agent reads one page with no background and lists what it cannot follow. Held = a finding on a page that belongs to the lead, which I do not edit.

## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
