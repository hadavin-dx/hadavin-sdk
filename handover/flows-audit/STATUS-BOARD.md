UPDATED_UTC: 2026-11-16T15:53:49Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.26 load of 4 cores, mem 1/15 GB, RAM 1337/16087 MB, disk 8.8G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 16G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5; verified by me: FINDINGS/LEDGER r7 counts 45 rows 5/5/35, RW/CT checks PASS (330 claims, 195 RW rows); percent 70 unchanged until independent reviews close an item
PUSHED_UTC: 2026-11-16T15:53:49Z

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
| acf8ab59 | F8 round 11 fixer | sonnet | run_all.sh intermittent exit 1 (3 of 6 runs), M1-M5, F1-F12 (uncapped) | 15:48Z | 16:30Z | running | none yet |
| a18a4e2d | Q31 round 11 fixer | sonnet | 11+6 Majors, 12 new items (QUESTIONS.md Q31 only) | 15:49Z | 16:15Z | running | none yet |
| abb2c71f | REVIEW.md round 26 design/security review | sonnet | rating rule, least-privilege of fixes, Decisions 26-29 (uncapped) | 15:51Z | 16:10Z | running | none yet |
| a55f3104 | patch-copies round 7 code review | sonnet | verdict script, counts, SQL rights (uncapped) | 15:52Z | 16:12Z | running | none yet |
| a99ca468 | RW/CT round 12 stranger read | sonnet | RW 305-end and CT 120-end not yet read | 15:53Z | 16:12Z | running | none yet |
| ae473f2d | FINDINGS/LEDGER round 7 reader | sonnet | fresh read of 45 rows | 15:55Z | 16:12Z | running | none yet |
| a15c1de2 | plan-files round 22 fixer | sonnet | 2 Blockers x2 + 7 Majors + 4 cites + awk pattern (RUNBOOK/FIX-PLAN/TAKE-CHECKLIST) | 15:57Z | 16:25Z | running | none yet |
| ac7d38d2 | REVIEW.md round 26 citation checker | sonnet | cites of Decisions 26-29, counts, 9394 quote | 15:57Z | 16:10Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 REVIEW.md round 27 fixer: reader r26 (B1-B4, M1-M13) + design r26 + citation r4 in one batch (waits on abb2c71f and ac7d38d2; one editor per file)
2 patch-copies round 7 stranger read (second angle; needs a free slot)
3 plan-files round 23 stranger read (after a15c1de2)
4 F8 fresh evidence runner + uncapped reviews (after acf8ab59)
5 RW/CT round 13 fixer for r12 reader findings (after a99ca468)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
