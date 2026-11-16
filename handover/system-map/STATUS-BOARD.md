# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T11:30:22Z
SESSION: system-map
ORDER: 017-028 read (ORDER 028 at 11:31Z: start up to 8, name them here); lead ANSWER 10:23Z item 8 (pause stays) read; no Q22 text exists in ORDERS.md or inputs/
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 20
ITEMS_OPEN: 15 (rows below 100 percent: M2-M10, M14, M15, M17-M20; 5 rows are at 100). CORRECTION: my earlier "14" and "6 at 100" were wrong; recounted by script at 11:3xZ over the 20 rows. PERCENT mean of the table is 83.1 (sum 1662 over 20 rows), not 83.6. M3, M4, M6 queue tags now match the board (checked 11:2xZ, digest 152); M9 and M15 queue tags say DONE while the board says 90 and 80 percent (digest 152)
PERCENT: 83.1 (script recount: 1662 / 20; the earlier 83.6 was wrong)
AGENTS_RUNNING: 8 running (ORDER 028), all started this beat: a95029aa80572f0d1, ab78283631eddd623, a97217dce4b7a3659, a672a5ac7582f96e9, a3a04be5fb2df00a1, aa1c426c076709cb3, a9415445d5bf6a4b2, ab9d9e3029bb722a6. The 11 earlier cold reads all finished. Digested through 234 (225 and 229-231 from agent hand-backs I saw; line cites in 225 checked by me for lines 114-130 only).
INTERRUPTED: none
NEXT: digest the 8 new hand-backs (run-day card, clean-up card, QUESTIONS, ARCHIVE-CUT-LIST, SWEEP 1-200, decision list, MASTER-MAP, FINAL-CROSSCHECK); fix board gaps from digest 229 (stamp, agent rows with started/due, glossary); next pass on the decision list (digest 226-234 items); send the list to the lead.
CAPACITY: nproc 4, load 0.07, RAM 876/16087 MB used, disk / 43% used (22G free); top disk users: /tmp/claude-0 about 1.3 GB (session scratch), /home/user/hadavin-sdk about 304 MB, my folder about 4.5 MB.
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
PUSHED_UTC: 2026-11-16T11:30:22Z

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

## AGENTS (ORDER 028: 8 running; started 2026-11-16T11:30:22Z, expected end within 10 minutes)
| id | purpose | state |
|---|---|---|
| a95029aa80572f0d1 | run-day card cold read | running, read-only |
| ab78283631eddd623 | clean-up card cold read | running, read-only |
| a97217dce4b7a3659 | QUESTIONS cold read | running, read-only |
| a672a5ac7582f96e9 | ARCHIVE-CUT-LIST cold read | running, read-only |
| a3a04be5fb2df00a1 | SWEEP 1-200 cold read | running, read-only |
| aa1c426c076709cb3 | decision list cold read | running, read-only |
| a9415445d5bf6a4b2 | MASTER-MAP cold read | running, read-only |
| ab9d9e3029bb722a6 | FINAL-CROSSCHECK cold read | running, read-only |
