UPDATED_UTC: 2026-11-16T16:20:27Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.09 load of 4 cores, mem 1/15 GB, RAM 1467/16087 MB, disk 17G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 7.6G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: next5 in /tmp/gen7/next5.txt; disk 17G free 57%; percent basis 70 = 7 of 10 independently verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T16:20:27Z

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
| acf8ab59 | fixer | sonnet | F8 flow-check round 11 (uncapped) | 15:48Z | 16:40Z | running | edits in flow-check/ |
| a81f425a | fixer | sonnet | REVIEW.md round 29 (uncapped) | 16:13Z | 16:35Z | running | edits in REVIEW.md |
| a61a8f40 | citation | sonnet | Q31 citation check r14 | 16:15Z | 16:30Z | running | reviews/citation-q31-r14.md |
| a18f1c8d | fixer | sonnet | plan files round 24 | 16:18Z | 16:40Z | running | edits in RUNBOOK/FIX-PLAN/TAKE-CHECKLIST |
| a026f1e0 | fixer | sonnet | FINDINGS/LEDGER round 10 | 16:18Z | 16:40Z | running | edits in FINDINGS/LEDGER-ROWS |
| ae51eddb | fixer | sonnet | Q31 round 14 | 16:19Z | 16:40Z | running | edits in QUESTIONS.md |
| a8632c07 | reviewer | sonnet | patch-copies r9 code review (uncapped) | 16:20Z | 16:35Z | running | findings inline |
| a03734e9 | citation | sonnet | patch-copies r9 citation check | 16:20Z | 16:35Z | running | reviews/citation-patchcopies-r9.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 RW/CT round 16 reader; 2 patch-copies fixer (after r9 reviews); 3 REVIEW.md round 30 readers; 4 F8 evidence runner then reviews; 5 Q31 round 15 reader

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
