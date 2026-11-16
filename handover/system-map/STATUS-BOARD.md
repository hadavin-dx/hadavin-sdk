# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T11:23:24Z
SESSION: system-map
ORDER: 017-028 read (ORDER 028 at 11:31Z: start up to 8, name them here); lead ANSWER 10:23Z item 8 (pause stays) read; no Q22 text exists in ORDERS.md or inputs/
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 20
ITEMS_OPEN: 14 (rows below 100 percent in the table; counted by an agent, it found 12 was wrong). PERCENT mean of the table is 83.6, not 85. M3, M4, M6 queue tags now match the board (checked 11:2xZ, digest 152); M9 and M15 queue tags say DONE while the board says 90 and 80 percent (digest 152)
PERCENT: 83.6 (mean of the table, counted by an agent; was 85)
AGENTS_RUNNING: 8 at the beat (ORDER 028): 7 running now (table), a 8th is started in the same turn this beat is pushed. Digested through batch 198.
INTERRUPTED: none
NEXT: collect and digest the 8 new hand-backs; build the decision list for the lead (open-items-table fixes first); next board beat in 5 minutes.
CAPACITY: nproc 4, load 0.15 0.25 0.21, RAM 872/16087 MB used, disk / 43% used (23G free), my folder 4.4 MB. Top disk users: /tmp/claude-0 1.3 GB (session scratch, not mine to clear), my folder 4.4 MB, none else measured.
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
PUSHED_UTC: 2026-11-16T11:23:24Z

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

## AGENTS (ORDER 028: 6 still running, 2 started this beat)
| id | role | what it does | state |
|---|---|---|---|
| a0e82acf25da5b062 | comprehension | banned-claims and DECISION-one-store | running |
| aedd102730e31a9b9 | codebase-details | REPORT.md lines 41-120 claims | running |
| a14f027da3e53c908 | comprehension | flowcheck/REPORT.md read | running |
| a3478005c210f7eba | codebase-details | drift/REPORT.md sections 1-5 cites | running |
| a6af482a86283d8ef | comprehension | ORDERS.md lines 86-136 cold read | running |
| afc255efc63d09442 | codebase-details | TAKE-BLOCKERS cites after fixes | running |
