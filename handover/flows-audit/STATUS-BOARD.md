UPDATED_UTC: 2026-11-16T19:43:03Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 8.52 load of 4 cores, mem 1/15 GB, RAM 1253/16087 MB, disk 19G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 4.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: load 8.1 at 19:43Z, no new heavy runs until under 6
PUSHED_UTC: 2026-11-16T19:43:03Z

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
| a1bdef8f | fixer | sonnet | FINDINGS/LEDGER r31 | 19:41Z | 20:41Z | working | - |
| acf7be5f | fixer | sonnet | QUESTIONS Q31 r49 | 19:46Z | 20:46Z | working | - |
| a4341ca7 | fixer | sonnet | TAKE-CHECKLIST + FIX-PLAN r43 | 19:48Z | 20:48Z | working | - |
| a7013236 | fixer | sonnet | REVIEW.md r49 (uncapped) | 19:49Z | 20:49Z | working | - |
| a4929f91 | reader | sonnet | CLAIMS-TABLE 300-600 | 19:45Z | 20:00Z | working | - |
| a55ebcd3 | reader | sonnet | RUNBOOK 1-220 r50 | 19:46Z | 20:00Z | working | - |
| a7b8dca1 | reader | sonnet | patch-copies README 1-330 r23 (uncapped) | 19:49Z | 20:05Z | working | - |
| aabf71c4 | evidence runner | sonnet | F8 r12 evidence (driver running) | 19:00Z | 20:00Z | waiting driver | partial |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 RUNBOOK reader 220-433 (fresh, round 2)
2 REVIEW.md readers 1-132, 333-407, 459-590, 633-884 (uncapped)
3 F8 fixer after evidence driver, then fresh uncapped reviewers
4 RUNSHEET-WORDING reader round 2 and CLAIMS-TABLE 600-1052
5 drift-007 r3 and trigger-word grep before FINAL
DISK 19G free; load about 4 of 4; top users: pc21 1.4G, tmp clones 2.9G unconfirmed, /root/.claude 888M, repo 773M, p20 218M

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
