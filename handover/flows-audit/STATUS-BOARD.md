UPDATED_UTC: 2026-11-16T16:30:41Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.29 load of 4 cores, mem 1/15 GB, RAM 1351/16087 MB, disk 15G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 9.7G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: next5 in /tmp/gen7/next5.txt; disk 15G free 63%; percent basis 70 = 7 of 10 independently verified, none closed since 13:59Z
PUSHED_UTC: 2026-11-16T16:30:41Z

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
| acf8ab59 | fixer | sonnet | F8 flow-check round 11 (uncapped) | 15:48Z | 16:45Z | running | edits in flow-check/ |
| a7a8fefa | citation | sonnet | REVIEW.md r30 citation check | 16:26Z | 16:40Z | running | reviews/citation-review-r30.md |
| a2fcaea8 | reader | sonnet | FINDINGS/LEDGER r10 stranger read | 16:27Z | 16:40Z | running | findings inline |
| a185aa9a | fixer | sonnet | REVIEW.md round 31 (uncapped) | 16:28Z | 16:50Z | running | edits in REVIEW.md |
| a6c32441 | reader | sonnet | patch-copies r10 stranger read (uncapped) | 16:29Z | 16:40Z | running | findings inline |
| aad501d7 | fixer | sonnet | Q31 round 15 | 16:30Z | 16:50Z | running | edits in QUESTIONS.md |
| a213005e | reader | sonnet | plan files r25 stranger read | 16:30Z | 16:45Z | running | findings inline |
| a6a3a4ee | reader | sonnet | RW/CT r18 stranger read | 16:30Z | 16:45Z | running | findings inline |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 patch-copies r10 code reviewer + citation checker (uncapped); 2 F8 evidence runner then fresh uncapped reviews; 3 REVIEW.md r31 readers/design/citation; 4 FINDINGS/LEDGER fixer from r10 reader; 5 plan-files/RW-CT/Q31 fixers from the new reads

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
