UPDATED_UTC: 2026-11-16T17:38:35Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 3.10 load of 4 cores, mem 1/15 GB, RAM 1495/16087 MB, disk 11G free of 252G, top3 522M /tmp/tmp.4gOIkjhGSB 603M /tmp/tmp.iOksNU37hQ 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: save reports, verify fixers, fresh readers
PUSHED_UTC: 2026-11-16T17:38:35Z

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
| a7e25c30 | patch-copies r15 fixer | sonnet | README/DEAD-MAN-CHECK Majors (uncapped) | 17:15Z | 17:50Z | running | editing |
| a5856771 | FINDINGS/LEDGER r19 fixer | sonnet | r19 findings + F-003 cite :51 | 17:20Z | 17:50Z | running | editing |
| a8ff9e50 | REVIEW.md r40 fixer | sonnet | r34 reports, leftovers (uncapped) | 17:30Z | 18:00Z | running | editing REVIEW.md |
| a0aa4509 | Q31 r26 stranger read | sonnet | read QUESTIONS.md | 17:28Z | 17:45Z | running | reading |
| a4f7b824 | plan-files r33 fixer | sonnet | B1 receipt + 12 Majors + shell guards | 17:38Z | 18:10Z | running | editing RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| ae6343b9 | RW/CT r32 fixer | sonnet | 2 Blockers + 10 Majors | 17:38Z | 18:05Z | running | editing RW/CT |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Q31 fixer after r26 read (Q-new-1, SHA_R20-23, HubSpot answer time)
2. Fresh readers for plan-files, RW/CT after fixers
3. REVIEW.md r40 verify (count_review 28/4/13/11), citation checker
4. patch-copies r16 readers after r15 fixer
5. F8 r11 report then evidence runner alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
