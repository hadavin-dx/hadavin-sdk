UPDATED_UTC: 2026-11-16T17:14:41Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 2.27 load of 4 cores, mem 1/15 GB, RAM 1337/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 8th slot empty: every remaining independent job reads a file an agent is editing now (drift-007 r3 and citation checks wait for the fixers); ITEMS_OPEN 30, 70 percent = 7 of 10 verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T17:14:41Z

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
| ab0a31d9 | FINDINGS/LEDGER r16 fixer | sonnet | 6 Majors from reader r15 | 17:08Z | 17:25Z | running | editing |
| afb10ffb | REVIEW.md r37 fixer | sonnet | design r36 B1+M, reader r36 M, citation caveats (uncapped) | 17:09Z | 17:35Z | running | editing REVIEW.md |
| a8c4d118 | Q31 r23 fixer | sonnet | 6 Majors from reader r22 + 4 new items | 17:11Z | 17:30Z | running | editing QUESTIONS.md |
| a45191d1 | RW/CT r28 reader | sonnet | stranger read of parts not yet read | 17:12Z | 17:25Z | running | reading |
| a0007ab5 | plan-files r31 reader | sonnet | stranger read RUNBOOK steps 1-17, FIX-PLAN, TAKE-CHECKLIST | 17:13Z | 17:28Z | running | reading |
| a17610d4 | patch-copies r13 fixer | sonnet | 6 Majors from reader r13 (uncapped) | 17:14Z | 17:35Z | running | editing README/DEAD-MAN-CHECK |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. FINDINGS/LEDGER r16 fixer report: verify (compare14 0 differences), then r17 reader
2. REVIEW.md r37 fixer report: verify counts, then design + reader + citation round 38 (uncapped)
3. Q31 r23 fixer report: verify label counts, then fresh reader
4. RW/CT r28 and plan-files r31 reader reports: save, then one fixer each
5. F8 r11 report: evidence runner alone plus fresh uncapped reviews; patch-copies r13 fixer report then citation check

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
