# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T10:25:07Z (IST = UTC+5:30)
SESSION: system-map
ORDER: 017-025; lead ANSWER 10:23Z item 8 (pause stays) read
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 16
ITEMS_OPEN: 4
PERCENT: 85
AGENTS_RUNNING: 5 (numbering clash; ONE-PLACE stale gates; merged rehearsal rows; board and queue fact check; round-2 read of OWNER-VIEW and card). Refilling to 6 next. Applied: claim narrowing in OWNER-VIEW, card step wording.
INTERRUPTED: none
NEXT: patched-copy answer already applied everywhere; next: apply the 6 agent reports' wording fixes (STATUS-BOARD, OWNER-VIEW row 3, REPORT.md, README/LEAD-PAGE structure); scan_outputs.py fix and tests still to do. ORDER 024: sed never ran, counts 6 opus, 64 sonnet, 0 fable. M14: 1 failed (licence, branch artefact), 9390 passed, rc=1. HELD for the lead: v5 step J editor; D-04/D-05 (post only); QUESTIONS 8 (film pause); rehearsal trim; row 1 builder and date.
CAPACITY: nproc 4, load 0.51, RAM 0 GB used of 15, DISK / 24 GB free of 252 GB (40 percent used); top 3 disk users: /tmp/pytest-of-root 616M, /tmp/sm-fresh 624M, /tmp/claude-0 1.3G (nothing removed; free space is above the limits)
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); the studio lead starts Docker and runs the rehearsal (decision 12); no take date. (3) S9-5, S9-12, S9-3, S9-2 not yet applied in v5 or the scope sheet; S9-1 and S9-4 deferred, describe-only (decision 5). (4) the take-time value substitution (BL-wp6-G1) is not built. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
PUSHED_UTC: 2026-11-16T10:11:31Z

## ITEMS
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| M1 | flowcheck and third read | done | 100 | flowcheck/REPORT.md | n8n run of patched flows NOT TESTED (no Docker here) |
| M2 | FINAL-CROSSCHECK.md | reviewed round 1, fixes applied | 95 | FINAL-CROSSCHECK.md | round 2 not run |
| M3 | drift check of take documents | sections 1-10 written; sections 9 (security angle) and 10 (cite check) added | 92 | drift/REPORT.md | 5 security Blockers need the studio lead |
| M4 | MASTER-MAP and ONE-PLACE-TABLE | round 1 fixes applied; some rows not yet aligned | 90 | MASTER-MAP.md | |
| M5 | OWNER VIEW | rewritten round 2 (11 rows, all fact-check Blockers and Majors applied); round 3 readers running | 90 | OWNER-VIEW.md | |
| M6 | R460 audit of own tools | fixed and tested (42 tests) | 90 | work/review-r460-tools.md | row-number keying open |
| M7 | stale done items | applied | 95 | drift/REPORT.md section 6 | |
| M8 | archive cut list | draft; two lists (39 vs 13 rows) not reconciled | 85 | ARCHIVE-CUT-LIST.md | |
| M9 | done items listed open | covered by M7 | 90 | drift/REPORT.md section 6 | |
| M10 | second-reader ring | partly done, fresh round running | 60 | rings/RING-LOG.md | |
| M11 | FACTS-ALREADY-DONE sweep | DONE (drift section 11) | 100 | | |
| M12 | video-date sweep | DONE (drift section 11) | 100 | | |
| M13 | three-way consistency | DONE (drift section 12) | 100 | | |
| M14 | heavy lane in fresh clone | DONE twice; latest head: 1 real failure (licence files), see FAILED | 100 | /tmp/sm-fresh2.pytest.log | |
| M15 | cut list reconcile | reconciliation note added to ARCHIVE-CUT-LIST.md; one list to sign after the take | 80 | ARCHIVE-CUT-LIST.md | |
| M16 | flow-set question | DONE, closed by decision 1 (real-v5 only; film-v5 out) | 100 | flowset/REPORT.md | |

## AGENTS
| id | role | model | what it does | started UTC / IST | expected end UTC / IST | state |
|---|---|---|---|---|---|---|
| a0fbca6c | egm-codebase-details | sonnet | cite check of README and LEAD-PAGE edits | 10:08Z / 15:38 | 10:14Z / 15:44 | running |
| ae7ae345 | egm-design | sonnet | end-delete reconciliation text, both cases | 10:10Z / 15:40 | 10:16Z / 15:46 | running |
| afd36344 | egm-codebase-details | sonnet | exact OWNER-VIEW and cleanup-card fixes | 10:10Z / 15:40 | 10:16Z / 15:46 | running |
| adc9115a | egm-comprehension | sonnet | naive read of TAKE-BLOCKERS and QUESTIONS | 10:10Z / 15:40 | 10:16Z / 15:46 | running |
| aee72fde | egm-zoom-out | sonnet | fastest safe path to the take, cut list | 10:10Z / 15:40 | 10:16Z / 15:46 | running |
| ae144e61 | egm-style | sonnet | plain-wording read of OWNER-VIEW | 10:10Z / 15:40 | 10:16Z / 15:46 | running |
| (shell) | pytest | - | M14 fresh clone of b6c40a9bd, log in scratchpad m14c.log | 10:03Z / 15:33 | 10:20Z / 15:50 | running |
