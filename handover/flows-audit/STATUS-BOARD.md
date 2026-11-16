UPDATED_UTC: 2026-11-16T09:23:56Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 4
PERCENT: 80
AGENTS_RUNNING: 5
CAPACITY: 0.39 load of 4 cores, mem 0/15 GB, disk free 29G, agents 5 (light+heavy per list)
INTERRUPTED: none
NEXT: F1 lands then F1 r2 + F5 fixer; F3 delta review; F8 recheck
PUSHED_UTC: 2026-11-16T09:23:56Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 90 | CLAIMS-TABLE.md | fixer running, then round 2 reviews |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | waiting | 60 | RUNSHEET-WORDING.md | fix after F1 table lands |
| F6 | idle fallback audit | running | 95 | F6-AUDIT.md | reader pass fixing; done after |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | running | 92 | SCENE-FLOW-MAP.md | round 2 found 1 Major; fixer running |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| ad7e698a4ee4826f8 | fixer F1 | sonnet | claims table batch | 09:14 | 09:35 | 09:30 | running | CLAIMS-TABLE.md |
| aaa5a08748ba9d17a | fixer F8 r1 | sonnet | flow checker fixes | 09:27 | 09:45 | 09:30 | running | flow-check/ |
| a60d5a90afa592604 | EVIDENCE RUNNER F3 r3 | sonnet | tests, hostile, mutants | 09:27 | 09:40 | 09:30 | running | fill_flows/evidence-f3-r3.md |
| a9674547ae6741df7 | fixer F9 r2 | sonnet | scene map r2 fixes | 09:28 | 09:38 | 09:30 | running | SCENE-FLOW-MAP.md |
| a704845eb8984b16b | fixer F6 reader | sonnet | F6 audit plain wording | 09:28 | 09:40 | 09:30 | running | F6-AUDIT.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
