UPDATED_UTC: 2026-11-16T17:25:13Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.87 load of 4 cores, mem 1/15 GB, RAM 1373/16087 MB, disk 11G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify fixer outputs as they land; fresh readers next
PUSHED_UTC: 2026-11-16T17:25:13Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:40Z | running | run_all.sh intermittent exit 1, cause unknown |
| a3f55414 | RW/CT r29 fixer | sonnet | 9 findings from reader r28 | 17:15Z | 17:35Z | running | editing RW/CT (WIP pushed, unverified) |
| a323882c | plan-files r32 fixer | sonnet | 10 Majors from reader r31 + check 13 | 17:16Z | 17:40Z | running | editing plan files |
| ac219645 | Q31 r24 reader | sonnet | stranger read of Q31 | 17:20Z | 17:35Z | running | reading |
| a2ad4097 | FINDINGS/LEDGER r18 fixer | sonnet | fixes from reader r17 | 17:22Z | 17:40Z | running | editing |
| afb92136 | REVIEW.md r39 fixer | sonnet | 1 Blocker + 29 Majors from design r38 and reader r38 (uncapped) | 17:24Z | 17:50Z | running | editing REVIEW.md |
| a5b477bd | patch-copies r15 stranger read | sonnet | README+DEAD-MAN-CHECK (uncapped) | 17:25Z | 17:37Z | running | reading |
| a45da8a1 | patch-copies r15 technical check | sonnet | shell/SQL accuracy, second angle (uncapped) | 17:25Z | 17:37Z | running | reading |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Verify RW/CT r29 fixer output, then fresh RW/CT reader on never-read ranges
2. Verify plan-files r32 fixer output, then round 33 reader
3. Save Q31 r24 reader report; one Q31 fixer incl. proposed texts from FINDINGS r18
4. Verify REVIEW.md r39 fix (count_review, cites in patch-copies), then citation checker and fresh design/reader
5. F8 r11 report then evidence runner alone plus uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
