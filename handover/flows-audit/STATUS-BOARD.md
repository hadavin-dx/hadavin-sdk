UPDATED_UTC: 2026-11-16T17:45:05Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 6.25 load of 4 cores, mem 1/15 GB, RAM 1196/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: technical read lands, then one patch-copies fixer; empty slot: waits for it
PUSHED_UTC: 2026-11-16T17:45:05Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:55Z | running | run_all.sh intermittent exit 1, cause unknown |
| a8ff9e50 | REVIEW.md r40 fixer | sonnet | r34 reports + leftovers (uncapped) | 17:35Z | 18:00Z | running | editing REVIEW.md |
| a4f7b824 | plan-files r33 fixer | sonnet | B1 receipt + 12 Majors + shell guards | 17:38Z | 18:10Z | running | editing RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a6d264c7 | patch-copies r16 technical read | sonnet | shell/SQL/cites (uncapped) | 17:41Z | 17:52Z | running | reading |
| abad67c2 | Q31 r26 fixer | sonnet | 9 Majors + NQ-A..F | 17:41Z | 18:05Z | running | editing QUESTIONS.md |
| ac9a10df | FINDINGS 61-235 read | sonnet | stranger read | 17:44Z | 17:55Z | running | reading |
| ac75cb3a | FINDINGS Blocker/Major rows read | sonnet | stranger read | 17:44Z | 17:55Z | running | reading |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. patch-copies r16 fixer after technical read (one fixer, both reports)
2. FINDINGS/LEDGER r20 fixer after both range readers
3. Fresh RW/CT r33 readers (comprehension, claims angle)
4. REVIEW.md r40 verify (count_review 28/4/13/11) then citation checker + fresh readers
5. F8 r11 report then evidence runner alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
