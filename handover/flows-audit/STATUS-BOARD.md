UPDATED_UTC: 2026-11-16T19:47:19Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.37 load of 4 cores, mem 1/15 GB, RAM 1112/16087 MB, disk 19G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 4.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: F8 fixer held until load under 6
PUSHED_UTC: 2026-11-16T19:47:19Z

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
| a1bdef8f | fixer | sonnet | FINDINGS/LEDGER r31 (light, edits only) | 19:41Z | 20:41Z | working | - |
| acf7be5f | fixer | sonnet | QUESTIONS Q31 r49 (light) | 19:46Z | 20:46Z | working | - |
| a4341ca7 | fixer | sonnet | TAKE-CHECKLIST + FIX-PLAN r43 (light) | 19:48Z | 20:48Z | working | - |
| a7013236 | fixer | sonnet | REVIEW.md r49 (uncapped, light) | 19:49Z | 20:49Z | working | - |
| ab296e5f | fixer | sonnet | CLAIMS-TABLE r45 (light) | 19:45Z | 20:45Z | working | - |
| a4e60b74 | reader | sonnet | patch-copies README 330-641 (uncapped) | 19:51Z | 20:10Z | working | - |
| a6725e95 | reader | sonnet | RUNBOOK 227-244 | 19:52Z | 20:10Z | working | - |
| a9f34c77 | reader | sonnet | REVIEW.md 333-407 (uncapped) | 19:52Z | 20:10Z | working | - |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 F8 fixer (HEAVY: reruns test_run_all_raw.sh about 12 min): HOLD until load under 6; evidence: new test_run_all_raw.sh phase 2 fails 4 of 13 (exit 1 not 0, raw files differ, manifest, refreshed message); old code 7/13 and stop test 16/25 as planned
2 RUNBOOK fixer after readers 227-433 finish (batch r50, r51); more RUNBOOK readers for 245-433
3 REVIEW.md readers 459-590, 633-884 (uncapped)
4 RUNSHEET-WORDING reader round 2 and CLAIMS-TABLE 600-1052 reader
5 drift-007 r3 and trigger-word grep before FINAL
HEAVY RUNS NOW: none (F8 evidence runner finished 19:46Z; 0 test processes). Max 3 heavy at once. DISK 19G free; top users: pc21 1.4G, tmp clones 2.9G unconfirmed, /root/.claude 888M, repo 773M, p20 218M; 6 /tmp/fc8raw.* folders left by F8 runner (kept on purpose)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
