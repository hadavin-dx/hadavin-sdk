# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T09:42:25Z (IST = UTC+5:30)
SESSION: system-map
ORDER: 017-020 on top of 016; queue M10-M16
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 16
ITEMS_OPEN: 5
PERCENT: 80
AGENTS_RUNNING: 4 reviewers + 1 heavy test run (5 lanes)
INTERRUPTED: none
NEXT: collect four reviews (cards vs v5, README and lead page, ONE-PLACE table, tools R460); read the M14 re-run on core-hardening head 60338533 (76 percent done, result not known yet); core-hardening still has to apply drift/APPLIED-S9.md (S9-1..5 and S9-12)
CAPACITY: 4 cores, load average 1.0 (about 25 percent, below the 70 percent target; the test run is single-process and the reviewers read only); memory 1 of 15 GB (7 percent); disk 38 percent used, 25 GB free; heavy slots 1 of 3 used
FAILED: (1) ORDER 019 CLOSED, real defect: fresh clone of cloud/core-hardening gives 2 failed, 9389 passed, 455 skipped (rc=1): vendor word 'Port.io' in handover/BRIEF-PREAMBLE-studio-2026-11-06.md and patch-test-runs logs, one non-UTF-8 file handover/reviews/P1a-idempotence-probe.txt; 10 handover/promotion-inputs/apexc files with a wrong licence text. None of those paths is on main, so a PR from this branch fails 2 guard tests. Fix owner: core-hardening. (2) Owner cards facts check had 5 Majors: fixed, re-read pending. (3) v5 still lacks the S9 edits (APPLIED-S9.md). (4) No take date in v5; no one named for Docker (R8-4).
PUSHED_UTC: 09:42:25Z

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
| M14 | heavy lane in fresh clone | earlier head: 2 real failures; RE-RUN on new head 60338533 running | 70 | /tmp/sm-fresh2.pytest.log | |
| M15 | cut list reconcile | reconciliation note added to ARCHIVE-CUT-LIST.md; one list to sign after the take | 80 | ARCHIVE-CUT-LIST.md | |
| M16 | flow-set question | round 1 reviewed, fixes applied (NO-GO rule, credential risk); fresh reader running | 70 | flowset/REPORT.md | |

## AGENTS
| id | role | model | what it does | started UTC / IST | expected end UTC / IST | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a03ce68b | egm-codebase-details | sonnet | owner cards against v5 facts | 09:41 / 15:11 | 09:48 / 15:18 | 30 | running | none |
| a0d023db | egm-comprehension | sonnet | README and lead page naive read | 09:41 / 15:11 | 09:48 / 15:18 | 30 | running | none |
| a1891dd1 | egm-design | sonnet | ONE-PLACE table alignment | 09:41 / 15:11 | 09:48 / 15:18 | 30 | running | none |
| a7d88c75 | egm-design | sonnet | R460 on tools: generator literals and hand edits | 09:42 / 15:12 | 09:50 / 15:20 | 10 | running | none |
| heavy-2 | pytest (shell, not an agent) | n/a | core test suite, fresh clone head 60338533 | 09:39 / 15:09 | 10:10 / 15:40 | 76 | running | /tmp/sm-fresh2.pytest.log |
