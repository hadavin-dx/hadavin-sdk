UPDATED_UTC: 2026-11-16T20:13:37Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 0.44 load of 4 cores, mem 1/15 GB, RAM 1190/16087 MB, disk 15G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 9.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5
PUSHED_UTC: 2026-11-16T20:13:37Z

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
| a7636841 | F8 fixer | sonnet | F8 r12 fixes (HEAVY only while it runs tests) | 19:20Z | 20:25Z | running | evidence-f8-r13-fixer.md pending |
| a860fa1c | TAKE-CHECKLIST fixer r63 | sonnet | fix M1-M15 (clock block frozen) | 20:13Z | 20:35Z | running | fix-takechecklist63.md pending |
| a76c3617 | FINDINGS/LEDGER fixer r33 | sonnet | fix M1-M8 | 20:14Z | 20:35Z | running | fix-findings-ledger33.md pending |
| ab2d6ddc | patch-copies reader r26 | sonnet | security-path read README+DMC | 20:17Z | 20:32Z | running | report pending |
| add6db6a | FIX-PLAN reader r64 | sonnet | fresh read lines 85-end | 20:19Z | 20:33Z | running | report pending |
| a0fc3951 | CLAIMS cite checker 3 | sonnet | cites B-141..B-226 + X rows | 20:15Z | 20:30Z | running | report pending |
| a82bc64d | RUNBOOK fixer 3 | sonnet | leftovers (I-table cells, labels) | 20:20Z | 20:45Z | running | fix-runbook54c.md pending |
| a1525dba | REVIEW.md design reviewer r54 | sonnet | uncapped security-path review | 20:20Z | 20:35Z | running | report pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. CLAIMS-TABLE 301-599 reader and RUNBOOK 433+ I-table reader (never read)
2. Independent checks on each fixer's output (my own commands), then fresh uncapped reviewers on the fixed files
3. F8 independent reviewers and evidence runner (heavy; only when load under 6)
4. Fresh reader on new Q31 text (QUESTIONS 420-812) and RUNSHEET-WORDING round 2; FIX-PLAN 181-228
5. drift-007 r3 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
