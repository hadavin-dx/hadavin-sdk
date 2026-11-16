UPDATED_UTC: 2026-11-16T17:49:50Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.30 load of 4 cores, mem 1/15 GB, RAM 1136/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: REVIEW.md reads land then one fixer; Q31 reader then fixer
PUSHED_UTC: 2026-11-16T17:49:50Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 18:00Z | running | run_all.sh intermittent exit 1, cause unknown; running 2h |
| a4f7b824 | plan-files r33 fixer | sonnet | B1 receipt + 12 Majors + shell guards | 17:38Z | 18:10Z | running | editing RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a0fef7e3 | patch-copies r16 fixer | sonnet | 4 Majors + 8 Nits (uncapped) | 17:46Z | 18:10Z | running | editing README/DEAD-MAN-CHECK |
| aa23f813 | REVIEW.md r35 design read | sonnet | design critique (uncapped) | 17:46Z | 17:58Z | running | reading |
| a46b7605 | REVIEW.md r40 citation checker | sonnet | cites and numbers | 17:46Z | 17:58Z | running | writing citation-review40.md |
| a0d9069a | FINDINGS/LEDGER r20 fixer | sonnet | r20/r21a/r21b findings | 17:47Z | 18:15Z | running | editing FINDINGS/LEDGER |
| a37a1cd3 | Q31 r27 stranger read | sonnet | QUESTIONS 420-737 | 17:48Z | 18:00Z | running | reading |
| aeddf43e | REVIEW.md r35b read 440-610, 745-804 | sonnet | stranger read (uncapped) | 17:49Z | 18:00Z | running | reading |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md r41 fixer after design r35, citation, r35b reads (one fixer)
2. Q31 r27 fixer after reader
3. Fresh readers for plan-files (r34) and RW/CT (r33) after fixers
4. Patch-copies r17 readers after r16 fixer
5. F8 r11 report then evidence runner alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
