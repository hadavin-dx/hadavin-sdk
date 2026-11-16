UPDATED_UTC: 2026-11-16T17:34:42Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 5.02 load of 4 cores, mem 1/15 GB, RAM 1382/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify fixer outputs as they land; fresh readers next
PUSHED_UTC: 2026-11-16T17:34:42Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:50Z | running | run_all.sh intermittent exit 1, cause unknown |
| afb92136 | REVIEW.md r39 fixer | sonnet | 1 Blocker + 29 Majors from design r38 and reader r38 (uncapped) | 17:24Z | 17:50Z | running | editing REVIEW.md |
| a8762897 | Q31 r25 fixer | sonnet | 11 Majors from reader r24 + items 113-117 | 17:27Z | 17:45Z | running | editing QUESTIONS.md |
| a7e25c30 | patch-copies r15 fixer | sonnet | 1 + 11 Majors, two reports (uncapped) | 17:31Z | 17:50Z | running | editing README + DEAD-MAN-CHECK |
| aa94dee5 | plan-files r33 stranger read | sonnet | RUNBOOK 1-68/227-end, FIX-PLAN 73-201, TAKE-CHECKLIST 88-446 | 17:31Z | 17:45Z | running | reading |
| ab23e14c | plan-files r33 shell check | sonnet | commands in TAKE-CHECKLIST/FIX-PLAN, second angle | 17:31Z | 17:45Z | running | reading |
| a7210dc0 | FINDINGS/LEDGER r19 stranger read | sonnet | 45 rows as a doer | 17:32Z | 17:45Z | running | reading |
| a18fc902 | RW/CT r32 stranger read | sonnet | RW 1-321/452-end, CT 468-629/880-end | 17:33Z | 17:47Z | running | reading |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. FINDINGS/LEDGER r19 fixer after stranger read (batch with evidence slip: F-003 cite :50 -> :51)
2. Plan-files r33 fixer after both reports land
3. Q31 r25: verify, then fresh reader; add NQ from RW/CT r31 (Q-new-1 CrmUpsert login) and plan-files r32 (SHA_R20-23 blocks step 1?; HubSpot permission answer time)
4. REVIEW.md r39 verify (count_review 28/4/13/11, 25/3), fix patch-copies cites by heading, citation checker, fresh design/reader
5. F8 r11 report then evidence runner alone plus uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
