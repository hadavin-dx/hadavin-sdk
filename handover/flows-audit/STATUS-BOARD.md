UPDATED_UTC: 2026-11-16T16:46:40Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 5.91 load of 4 cores, mem 1/15 GB, RAM 1436/16087 MB, disk 12G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: 7 running (8th slot empty: load 4.2 of 4 cores); disk 12G free 70%; FINDINGS/LEDGER r11 verified, r12 reader started; percent stays 70 (no independent close since 13:59Z)
PUSHED_UTC: 2026-11-16T16:46:40Z

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
| acf8ab59 | F8 flow-check round 11 fixer (uncapped) | sonnet | fix F8 run_all.sh intermittency and review findings | 15:49Z | about 17:00Z | running | edits in flow-check/ |
| a294f937 | plan-files round 26 fixer | sonnet | fix 11 Majors in RUNBOOK/FIX-PLAN/TAKE-CHECKLIST | 16:37Z | about 17:05Z | running | edits in progress |
| a3736717 | REVIEW.md round 33 fixer (uncapped) | sonnet | fix design B1 + M2-M8, reader F1-F10 | 16:42Z | about 17:10Z | running | edits in progress |
| a6f19722 | patch-copies round 11 fixer (uncapped) | sonnet | fix 9 Majors README/DEAD-MAN-CHECK | 16:43Z | about 17:10Z | running | edits in progress |
| ab3ee0ff | RW/CT round 20 reader | sonnet | stranger read of RUNSHEET-WORDING/CLAIMS-TABLE | 16:44Z | about 16:58Z | running | pending |
| a26c1f8a | Q31 round 18 reader | sonnet | stranger read of Q31 | 16:45Z | about 16:58Z | running | pending |
| a1f4e17f | FINDINGS/LEDGER round 12 reader | sonnet | stranger read after round 11 fix (verified: counts 45/5/5/35, all checkers pass) | 16:46Z | about 17:00Z | running | pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Save RW/CT r20 and Q31 r18 reader reports, launch their fixers
2. Verify plan-files fixer a294f937 (clock diff, refs), launch round 27 reader
3. Verify REVIEW.md fixer, launch design + reader + citation (uncapped)
4. Verify patch-copies fixer, launch reader + code + citation (uncapped)
5. F8: evidence runner alone, then fresh uncapped reviews

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
