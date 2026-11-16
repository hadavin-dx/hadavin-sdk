UPDATED_UTC: 2026-11-16T20:06:02Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.52 load of 4 cores, mem 1/15 GB, RAM 1451/16087 MB, disk 16G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 8.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5
PUSHED_UTC: 2026-11-16T20:06:02Z

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
| a7636841 | F8 fixer | sonnet | F8 r12 fixes (HEAVY only while it runs tests) | 19:20Z | 20:20Z | running | evidence-f8-r13-fixer.md pending |
| aaf24a7e | REVIEW.md fixer | sonnet | REVIEW.md r50-r53 uncapped | 19:25Z | 20:20Z | running | fix-review53.md pending |
| ad9f2b55 | TAKE-CHECKLIST fixer | sonnet | r56+r58 | 19:30Z | 20:20Z | running | fix-takechecklist58.md pending |
| a3c5bd18 | patch-copies fixer | sonnet | README+DEAD-MAN-CHECK uncapped | 19:30Z | 20:20Z | running | fix-patchcopies25.md pending |
| a71e490b | FIX-PLAN fixer | sonnet | r60 | 19:40Z | 20:20Z | running | fix-fixplan60.md pending |
| af089b75 | RUNBOOK fixer 2 | sonnet | remaining items + r62 input table | 19:45Z | 20:25Z | running | fix-runbook54b.md pending |
| a969e49f | CLAIMS-TABLE fixer | sonnet | r61, no grade changes | 19:50Z | 20:25Z | running | fix-claims61.md pending |
| ad429f48 | FINDINGS reader r33 | sonnet | fresh read of ten fixed rows | 20:06Z | 20:20Z | running | report pending |

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
