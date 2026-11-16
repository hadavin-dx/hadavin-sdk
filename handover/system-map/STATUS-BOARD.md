# STATUS BOARD system-map
UPDATED_UTC: 2026-11-16T09:49:25Z (IST = UTC+5:30)
SESSION: system-map
ORDER: 017-020 on top of 016; queue M10-M16
STATE: WORKING
BOOT_ID: 6bc0bf7e
ITEMS_TOTAL: 16
ITEMS_OPEN: 5
PERCENT: 80
AGENTS_RUNNING: 5 reviewers (target 5+ met): naive owner read, structural read of work list, LEAD-PAGE vs cards, naive read of TAKE-BLOCKERS, architect read of the safe path
INTERRUPTED: none
NEXT: collect the 5 reports and apply Blockers and Majors; refill a lane the same turn one ends; the lead decides QUESTIONS.md items 6, 7, 8 (S9 mechanism, licence files, whether the video needs scenes 5 to 11); core-hardening applies S9 only after those
CAPACITY: 4 cores, load 0.5 (about 1 of 4 busy; reviewers only read, below the 70 percent target, no heavy test queued); memory 0 of 15 GB used (free -g), disk 38 percent used; heavy slots 0 of 3
FAILED: (1) M14 RE-RUN on core-hardening head 60338533, fresh clone: 1 failed, 9390 passed, 455 skipped (rc=1, 4 min 49 s): tests/test_repo_rules.py::test_licences_are_proprietary lists 11 problems in handover/promotion-inputs/*/LICENSE (first: apexc/LICENSE not the proprietary licence text); the earlier vendor-word failure is no longer there; owner core-hardening and the lead. (2) n8n has never run the changed flows (no Docker here); no named person to start Docker and rehearse; no take date. (3) S9-1..5 and S9-12 not applied in v5 or the scope sheet. (4) flow-set choice A to D open; the take-time value substitution (BL-wp6-G1) is not built; the mail credential mf-mail-smtp risk has no written fix. LICENCE-CAUSE (reviewer, unverified by a run): 7 LICENSE files (apexc, dealdesk, portal-kit, refunds proprietary-but-different; helios, warden, killswitch full Apache-2.0) differ from root LICENSE, plus killswitch/pyproject.toml (license Apache-2.0, other author) and portal-kit/pyproject.toml (no authors) = 10 of 11 problems; the 11th not found. Fix = copy root LICENSE over them and set license/authors; the owner must confirm the right to relicense the Apache ones first. core-hardening's files; not touched by system-map.
PUSHED_UTC: 09:49:25Z

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
| M16 | flow-set question | round 1 reviewed, fixes applied (NO-GO rule, credential risk); fresh reader running | 70 | flowset/REPORT.md | |

## AGENTS
| id | role | model | what it does | started UTC / IST | expected end UTC / IST | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aa56eabc | egm-comprehension | sonnet | naive owner read of OWNER-VIEW and the two cards | 09:47Z / 15:17 | 09:57Z / 15:27 | 40 | running | none |
| a82c2eea | egm-structural | sonnet | work list (drift section 13) usable? counts right? | 09:48Z / 15:18 | 09:58Z / 15:28 | 30 | running | none |
| a03f158d | egm-codebase-details | sonnet | LEAD-PAGE rows 16 to 23 against cards and v5 | 09:48Z / 15:18 | 09:58Z / 15:28 | 30 | running | none |
| ae189bb7 | egm-comprehension | sonnet | naive read of TAKE-BLOCKERS.md | 09:48Z / 15:18 | 09:55Z / 15:25 | 20 | running | none |
| af2ae07d | egm-design | sonnet | shortest safe path to a rehearsal and a take; lock-in and least privilege | 09:49Z / 15:19 | 10:00Z / 15:30 | 10 | running | none |

Finished this beat (reports read, fixes pushed): S9 implementation readiness (8 Blockers, wording fixed, 7 decisions to the lead), drift work-list read (rows added), licence cause (10 of 11 problems found), zoom-out "needed for the take" (TAKE-BLOCKERS.md written), flowset fact check (source notes added).
