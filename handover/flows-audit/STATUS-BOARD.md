UPDATED_UTC: 2026-11-16T19:12:49Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 1.22 load of 4 cores, mem 1/15 GB, RAM 1109/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: fixers r21/r29/r35, F8 reviewers and evidence runner running; empty slots none
PUSHED_UTC: 2026-11-16T19:12:49Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback + recovery audit | done | 100 | F6-AUDIT.md, F6B-AUDIT.md | n8n facts unverified; F6b SQL untested |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | state | produced so far |
|---|---|---|---|---|---|---|---|
| a144d2ea | fixer | sonnet | plan-files r39 fixer (RUNBOOK, TAKE-CHECKLIST, FIX-PLAN) | 19:03Z | about 19:40Z | running | not yet |
| aabf71c4 | evidence runner | sonnet | F8 r12 raw tests, new and old code (detached driver) | 19:09Z | about 19:55Z | running | evidence file started |
| abe4d295 | reader | sonnet | RW/CT r43 stranger read | 18:58Z | about 19:25Z | running | not yet |
| aa90da17 | fixer | sonnet | patch-copies README+DMC r21 fixer (uncapped) | 19:13Z | about 20:10Z | running | not yet |
| a6bfb5b2 | fixer | sonnet | FINDINGS/LEDGER r29 fixer | 19:13Z | about 20:10Z | running | not yet |
| ad79fb59 | fixer | sonnet | Q31 r35 fixer | 19:13Z | about 20:10Z | running | not yet |
| ac860969 | reviewer | sonnet | F8 r12 egm-codebase-details (uncapped) | 19:13Z | about 19:35Z | running | not yet |
| ad5cfec8 | reviewer | sonnet | F8 r12 egm-design (uncapped) | 19:13Z | about 19:35Z | running | not yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify each fixer on hand-back with own commands (counts, checkers, ruff, sha, md5 clock block)
2 REVIEW.md readers for unread ranges 133-332, 408-451, 459-550, 580-884 (r46 fixer done, checked)
3 save F8 r12 reviewer and evidence reports, then one uncapped F8 fixer
4 Q31 lines 557-805 unread: stranger readers in ranged slices after the r35 fixer
5 drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
