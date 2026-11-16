# STATUS BOARD system-map (top: what the lead must do; the log is further down)
UPDATED_UTC: 2026-11-16T11:58:31Z (17:28 IST)
PUSHED_UTC: 2026-11-16T11:58:31Z
SESSION: system-map
STATE: WORKING (video scope: real-v5 only, scenes 1 to 4, decision 1)
BLOCKED: the changed n8n flows have never been run (decision 12: the lead runs the first rehearsal). 1 test fails (a licence-file check, M14; decision 11: licence files are never changed).
NEEDS_YOU, in this order (lead; one action each; times UTC / IST):
  1. Start Docker and run the first rehearsal of the changed flows. Target: tonight or tomorrow morning IST (decision 12); write the UTC and IST start in the handoff. Nothing else can finish before this.
  2. Yes or no: may the three Apache-2.0 licence copies under handover/promotion-inputs stay as they are? (A yes means the failing test is changed, not the files.)
  3. Paste the SESSION-HANDOFF text into inputs/ by Tue 17 Nov 12:00 UTC / 17:30 IST, or check M20 (0 percent) is dropped. This date is the one I am holding you to; tell me if it is wrong.
  4. Answer the 8 open Blockers in drift/REPORT.md (row M3) and the two open questions D-04 and D-05 (both in work/decision-list-for-lead.md).
  5. Answer work/decision-list-for-lead.md. Its first row (the self-check, run (a)) was due Mon 16 Nov 13:00 UTC / 18:30 IST; its status is UNKNOWN.
FAILED: M14 test_licences_are_proprietary fails (1 failed, 9390 passed); the n8n run has not happened. Full text under Details at the end of this file. Times in the Details are UTC only; IST is +5:30.
PROGRESS: 15 of 20 items open (table below); mean 83.1 percent (1662 / 20). Percent is how far a page has been checked, not confidence the take will work.
Terms: take = the one filmed run; rehearsal = test run on the laptop without a real account; loopback = a self-check on the lead's own machine before it; helper = a read-only agent that reads one page and lists what it cannot follow (cold read); digest = my short note of a helper's report; ORDER n = a standing order in ORDERS.md.
AGENTS_RUNNING: 6 running, 2 missing (ORDER 035). Missing 1: re-read of work/open-items-table.md, waits on my own fix (Person column), not on an answer from you. Missing 2: re-read of work/decision-list-for-lead.md, waits on my own fix (A13 and split rows), not on an answer from you. I fix both next, then start them.
CAPACITY: nproc 4, load low, RAM under 1 GB of 16087 MB, disk 45% used (22 GB free of 252 GB); my disk users: work 2.3 MB, reviews-of-core-hardening 0.4 MB; freed 0 MB (ORDER 031).
NEXT: digested through 423. Fix my own files from digests 411-423 (decision-list A13 and split rows, open-items-table Person column, t19 steps, banned-claims sources, QUEUE glossary), then refill.
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

## AGENTS (ORDER 028/035: 6 running, 2 missing, reasons in AGENTS_RUNNING; last checked 2026-11-16T11:58:31Z)
| agent id | purpose | started (UTC) | expected end | state | produced so far |
|---|---|---|---|---|---|
| a8cdcedff58e2abfc | re-read STATUS-BOARD top | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |
| ad28d2bc6a9f778bc | re-read work/critical-path-r1.md | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |
| a356f4b25f7227072 | re-read work/end-delete-cases.md | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |
| a128fbbb9ff065fa3 | re-read work/rehearsal-passed-limits-draft.md | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |
| a2c4ce259247661e0 | re-read work/not-checked-r2.md | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |
| a0a594bc16bb2587c | re-read work/cleanup-card-held-edits.md | 11:58:31Z | +3 min | running | nothing yet (hand-back arrives) |

NEXT 5 tasks I would start with more capacity: (1) cold read QUEUE.md after glossary; (2) cold read banned-claims.md after sources; (3) cold read reviews-of-core-hardening/CORRECTIONS.md after fix; (4) cold read work/t19-and-stored-data-steps.md after split; (5) cold read PLAN-002.md after the L4 fix. None waits on you.

Words: UTC = world time; IST = UTC plus 5 h 30 min. Cold read = an agent reads one page with no background and lists what it cannot follow. Held = a finding on a page that belongs to the lead, which I do not edit.

## Details (long text moved from the FAILED line)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
