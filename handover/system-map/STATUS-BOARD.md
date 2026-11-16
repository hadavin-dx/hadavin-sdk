# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T10:27:05Z (IST = UTC+5:30)
SESSION: system-map
ORDER: 017-025; lead ANSWER 10:23Z item 8 (pause stays) read
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 16
ITEMS_OPEN: 4
PERCENT: 85
AGENTS_RUNNING: 6 (scan-defect fixes; TAKE-BLOCKERS and QUESTIONS read; contradictions between risk fixes; two more below). Applied: cleanup card verbs and .used wording; v5 edit table written for core-hardening (decisions/v5-edits-for-M17.md).
INTERRUPTED: none
NEXT: patched-copy answer already applied everywhere; next: apply the 6 agent reports' wording fixes (STATUS-BOARD, OWNER-VIEW row 3, REPORT.md, README/LEAD-PAGE structure); scan_outputs.py fix and tests still to do. ORDER 024: sed never ran, counts 6 opus, 64 sonnet, 0 fable. M14: 1 failed (licence, branch artefact), 9390 passed, rc=1. HELD for the lead: v5 step J editor; D-04/D-05 (post only); QUESTIONS 8 (film pause); rehearsal trim; row 1 builder and date.
CAPACITY: nproc 4, load low, RAM 15 GB total (agents are remote; local use small), DISK / 24 GB free of 252 GB (40 percent used); top 3: /tmp/claude-0 1.3G, /tmp/sm-fresh 624M, /tmp/pytest-of-root 616M; removed nothing
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
PUSHED_UTC: 2026-11-16T10:27:05Z

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
| M14 | heavy lane in fresh clone | DONE twice; latest head: 1 real failure (licence files), see FAILED | 100 | /tmp/sm-fresh2.pytest.log | |
| M15 | cut list reconcile | reconciliation note added to ARCHIVE-CUT-LIST.md; one list to sign after the take | 80 | ARCHIVE-CUT-LIST.md | |
| M17 | end never deletes: replacement lines | written (not applied to v5 or the program) | 70 | decisions/M17-end-never-deletes.md | v5 and the program text still say delete |
| M18 | D-04 and D-05 | written, awaiting the lead | 90 | decisions/D04-D05.md | |
| M19 | independent read of the owner steps | cold reads of the card and OWNER-VIEW done, fixes applied; round 2 running | 60 | work/agent-reports-batch3.md | |
| M20 | SESSION-HANDOFF live state | IMPOSSIBLE-NOW (file is on the studio laptop, not in the repo) | 0 | | needs the lead's text |
| M16 | flow-set question | DONE, closed by decision 1 (real-v5 only; film-v5 out) | 100 | flowset/REPORT.md | |

## AGENTS (rebuilt from the real agent list; started 10:2xZ)
| id | role | what it does | state |
|---|---|---|---|
| aa42c47b | egm-implementation-readiness | merged rehearsal rows (T19, F8, six new) | running |
| a98f3932 | egm-comprehension | round 2 read of OWNER-VIEW and card | running |
| acc4e9c8 | egm-codebase-details | v5 lines to change for M17 | running |
