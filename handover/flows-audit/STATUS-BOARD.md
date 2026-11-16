UPDATED_UTC: 2026-11-16T17:29:56Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 5.67 load of 4 cores, mem 1/15 GB, RAM 1422/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: patch-copies fixer when technical check lands; verify fixers
PUSHED_UTC: 2026-11-16T17:29:56Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:45Z | running | run_all.sh intermittent exit 1, cause unknown |
| a323882c | plan-files r32 fixer | sonnet | 10 Majors from reader r31 + check 13 | 17:16Z | 17:40Z | running | editing plan files |
| a2ad4097 | FINDINGS/LEDGER r18 fixer | sonnet | fixes from reader r17 | 17:22Z | 17:40Z | running | editing |
| afb92136 | REVIEW.md r39 fixer | sonnet | 1 Blocker + 29 Majors from design r38 and reader r38 (uncapped) | 17:24Z | 17:50Z | running | editing REVIEW.md |
| a45da8a1 | patch-copies r15 technical check | sonnet | shell/SQL accuracy, second angle (uncapped) | 17:25Z | 17:37Z | running | reading |
| a8762897 | Q31 r25 fixer | sonnet | 11 Majors from reader r24 + items 113-117 | 17:27Z | 17:45Z | running | editing QUESTIONS.md |
| aa447663 | RW/CT r31 fixer | sonnet | 10 Majors from reader r30 | 17:29Z | 17:50Z | running | editing RW/CT |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Patch-copies r15 fixer (waits for technical check report; 11 Majors from reader r15 saved) = the 8th slot
2. Verify plan-files r32 fixer output, then round 33 reader
3. Verify FINDINGS/LEDGER r18 fixer (compare 0 differences), then round 19 reader
4. Verify Q31 r25 and RW/CT r31 fixers, then fresh readers (RW 1-321, 452-558; CT 468-629, 880-end never read)
5. REVIEW.md r39 verify (count_review, patch-copies cites), citation checker, fresh design/reader; F8 evidence runner alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
