UPDATED_UTC: 2026-11-16T17:09:49Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 2.20 load of 4 cores, mem 1/15 GB, RAM 1347/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 8th slot empty: next job (patch-copies citation check) waits for r13 reader to avoid two agents on the same files; ITEMS_OPEN 30, 70 percent = 7 of 10 verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T17:09:49Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:30Z | running | run_all.sh intermittency work |
| a0a16684 | plan-files r30 fixer | sonnet | 8 Majors + stray fragment from reader r29 | 17:06Z | 17:25Z | running | editing RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a89dbf18 | Q31 r22 reader | sonnet | stranger read of Q31 | 17:06Z | 17:20Z | running | reading |
| a7ac5d80 | RW/CT r26 reader | sonnet | stranger read of unread RW/CT parts | 17:07Z | 17:20Z | running | reading |
| ab0a31d9 | FINDINGS/LEDGER r16 fixer | sonnet | 6 Majors from reader r15 | 17:08Z | 17:25Z | running | editing |
| afb10ffb | REVIEW.md r37 fixer | sonnet | design r36 B1+M, reader r36 M, citation caveats (uncapped) | 17:09Z | 17:35Z | running | editing REVIEW.md |
| a6b0babc | patch-copies r13 reader | sonnet | stranger read README+DEAD-MAN-CHECK (uncapped) | 17:09Z | 17:20Z | running | reading |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Verify REVIEW.md r37 fixer report, then design + reader + citation round 38 (uncapped)
2. Patch-copies r13 reader report, then fixer, then citation check
3. Q31 r22 reader report, then one batched Q31 fixer (scene 2 item, item 100 extension, REPO eighth value of item 59)
4. RW/CT r26 reader report, then fixer if Majors; FINDINGS/LEDGER r17 reader
5. F8 r11 report, then evidence runner alone plus fresh uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
