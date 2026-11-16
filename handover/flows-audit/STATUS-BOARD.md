UPDATED_UTC: 2026-11-16T17:01:10Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 4.65 load of 4 cores, mem 1/15 GB, RAM 1331/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 13G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: verify arriving reports; next: Q31 r20 read, plan-files r28, patch-copies r12, F8 evidence
PUSHED_UTC: 2026-11-16T17:01:10Z

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
| acf8ab59 | F8 flow-check r11 fixer | sonnet | fix flow-check (uncapped) | 15:50Z | 17:20Z | running | run_all.sh intermittency work |
| ae59e2df | REVIEW.md r35 fixer | sonnet | fix design r34 + reader r34 (uncapped) | 16:50Z | 17:20Z | running | edits in progress |
| a88baea0 | plan-files r28 fixer | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST from r27 + fix A sentence | 16:55Z | 17:15Z | running | edits in progress |
| aa679f36 | Q31 r20 reader | sonnet | stranger read of Q31 | 16:58Z | 17:08Z | running | reading |
| a1e95c64 | patch-copies r12 fixer | sonnet | README/DEAD-MAN-CHECK from 2 reviews (uncapped) | 17:00Z | 17:25Z | running | starting |
| a9f2669b | FINDINGS/LEDGER r14 fixer | sonnet | 9 Majors from reader r13 | 17:00Z | 17:20Z | running | starting |
| a3f52522 | RW/CT r24 reader | sonnet | stranger read of unread RW/CT parts | 17:01Z | 17:12Z | running | starting |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 verify Q31 r20 reader report, launch fixer
2 verify plan-files r28, launch round 29 reader
3 verify patch-copies r12, launch citation checker
4 F8 evidence runner after acf8ab59 reports
5 REVIEW.md r35 verify, then design + reader + citation reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
