UPDATED_UTC: 2026-11-16T17:59:20Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 4.12 load of 4 cores, mem 1/15 GB, RAM 1108/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify four fixers then fresh readers; patch-copies and FINDINGS reads then fixers
PUSHED_UTC: 2026-11-16T17:59:20Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 18:05Z | running | run_all.sh intermittent exit 1, cause unknown; running 2h10 |
| a485bdf2 | REVIEW.md r41 fixer | sonnet | r35/design/r35b/citation findings (uncapped) | 17:53Z | 18:20Z | running | editing REVIEW.md |
| a82b2326 | RW/CT r33 fixer | sonnet | 6 Majors on RW/CT | 17:56Z | 18:20Z | running | editing RW/CT |
| ad853ad1 | patch-copies r17 stranger read | sonnet | README/DEAD-MAN-CHECK (uncapped) | 17:56Z | 18:08Z | running | reading |
| a9363e9e | patch-copies r17 shell/security read | sonnet | shell/SQL accuracy (uncapped) | 17:57Z | 18:10Z | running | reading |
| a6927939 | FINDINGS/LEDGER r22 ranged read | sonnet | ten Blocker/Major rows | 17:57Z | 18:10Z | running | reading |
| a97d5beb | Q31 r27 fixer | sonnet | 10 Majors + new questions | 17:58Z | 18:25Z | running | editing QUESTIONS.md |
| aeb2251e | plan-files r34 fixer | sonnet | 15 Majors on RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 17:59Z | 18:25Z | running | editing plan files |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Verify RW/CT r33 fixer output then fresh r34 readers
2. Verify REVIEW.md r41 then fresh readers (count_review 28/4/13/11)
3. Verify Q31 r27 fixer (counts) then r28 reader
4. Verify plan-files r34 fixer then r35 readers
5. patch-copies r17 reports then one fixer; F8 r11 report then evidence runner alone

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
