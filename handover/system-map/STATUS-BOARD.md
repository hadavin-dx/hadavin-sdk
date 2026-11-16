# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T09:33:00Z (15:03 IST)
SESSION: system-map
ORDER: 017, 018, 019 on top of 016; queue refill M10-M15
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 15
ITEMS_OPEN: 8
PERCENT: 75
AGENTS_RUNNING: 5
INTERRUPTED: none
NEXT: collect M11 (owner-ask sweep), M12 (date sweep), M13 (three-way table), owner-view round 3 readers, fresh-clone heavy run; then apply fixes (cap 2 rounds)
CAPACITY: cores about 1.2 of 4 busy plus 1 heavy job (fresh-clone pytest) running; memory 1 of 15 GB; disk free 26 GB; 5 light agents + 1 heavy. Below the 70 percent core target only because light agents read files; heavy slots free: 2 of 3.
FAILED: (1) ORDER 019 answered: the 2 baseline failures were seen in a scratch copy that is not a git repository. test_licences_are_proprietary fails there because `git ls-files` exits 128 (scratch artefact, not a defect). test_no_vendor_brand_string_is_tracked names 'Port.io' in handover/BRIEF-PREAMBLE-studio-2026-11-06.md and handover/demo/portal/portal-design-v2.md and a non-UTF-8 file handover/reviews/P1a-idempotence-probe.txt; those files are NOT in the branch I hold, so in the scratch copy they are leftovers; a fresh clone of cloud/core-hardening is running now to say if it is real there (result next beat). (2) Owner view round 1 had 4 Blockers (clean-up deadline, failed-run clean-up owner, latest start time, `end` deletes): fixed, round 3 readers running. (3) Security reviewer found 5 Blockers in the take steps (S9-1..5, drift section 9): not mine to fix, in QUESTIONS for the studio lead. (4) write_outputs.py overwrite clash (earlier): fixed and tested. (5) Hand edits to SWEEP.md/ONE-PLACE-TABLE.md are not in the generator literals; generator refuses to overwrite them.
PUSHED_UTC: 09:33:00Z

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
| M10 | second-reader ring | running: drift report reader done (B1..B5 found, name table added); owner view round 3 running | 40 | rings/ (next beat) | |
| M11 | FACTS-ALREADY-DONE sweep | running | 10 | | |
| M12 | video-date sweep | running | 10 | | |
| M13 | three-way consistency | running | 10 | | |
| M14 | heavy lane in fresh clone | running (about 15 percent) | 15 | /tmp/sm-fresh.pytest.log | |
| M15 | cut list for unused repo files | not started | 0 | | next free lane |

## AGENTS
| id | role | model | what it does | started UTC / IST | expected end UTC / IST | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a18a0ede | egm-codebase-details | sonnet | M11 sweep | 09:36 / 15:06 | 09:46 / 15:16 | 20 | running | none |
| a66cac7f | egm-codebase-details | sonnet | M12 date sweep | 09:36 / 15:06 | 09:46 / 15:16 | 20 | running | none |
| ad3b715b | egm-codebase-details | sonnet | M13 three-way table | 09:36 / 15:06 | 09:48 / 15:18 | 20 | running | none |
| a216afdb | egm-comprehension | sonnet | owner view naive reader round 3 | 09:38 / 15:08 | 09:44 / 15:14 | 10 | running | none |
| a2717767 | egm-codebase-details | sonnet | owner view facts recheck vs v5 | 09:38 / 15:08 | 09:46 / 15:16 | 10 | running | none |
| (shell) | heavy test | none | M14 fresh clone of cloud/core-hardening, full pytest | 09:35 / 15:05 | 09:45 / 15:15 | 15 | running | 14 percent |
| (done) | adcc09ac, a9e694f6, a09607bb, a6cb0439, a092b8dd | reviewers | owner view facts (4 Blockers), naive reader, citation check, security angle, drift naive reader | | | 100 | reports read; fixes applied |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
1. Name who starts Docker and who runs the first laptop test of the five changed flows in n8n, and when (UTC and IST); no file names anyone (OWNER-VIEW.md, section 3).
2. Decide the open Blockers of drift/REPORT.md: D-01 (which n8n holds the take's credentials), D-02 (who makes the database passwords), D-03 (read-only archive code path or write scope for the HubSpot app), D-10 (real schedule; may be a false Blocker), S-03 (the take-time fill script), and L-01 (the operator can decrypt stored credentials: second Linux user, or the owner accepts it in writing).
3. Check the rights of the saved HubSpot key (the take deletes its own contacts, which needs write) and whether the SENDER app password sits in a file the step 22 shred misses.
4. Say yes or no to each row of ARCHIVE-CUT-LIST.md (archive only, never delete) and say whether the archive may live in this repository.
