UPDATED_UTC: 2026-11-16T20:39:01Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 7
CAPACITY: 3.74 load of 4 cores, mem 1/15 GB, RAM 1129/16087 MB, disk 14G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 9.9G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: cut list: finish running agents only
PUSHED_UTC: 2026-11-16T20:39:01Z

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
| a3e1970f | F8 EVIDENCE RUNNER r13 (HEAVY) | sonnet | flow-check run_all + stop test; video path: YES (take check) | 20:33Z | 21:00Z | running | raw output pending |
| af9239e4 | F8 design reviewer r13 | sonnet | flow-check review; video path: YES | 20:33Z | 21:10Z | running | none yet |
| a4b5d2d7 | F8 codebase reviewer r13 | sonnet | flow-check review; video path: YES | 20:33Z | 21:10Z | running | none yet |
| a5e0ccb1 | REVIEW.md fixer r56 | sonnet | core patch review (security); video path: NO, finishing only | 20:35Z | 21:20Z | running | none yet |
| ad0e03dc | FIX-PLAN fixer r65 | sonnet | fix plan; video path: YES (Tue re-pin), finishing only | 20:35Z | 21:20Z | running | none yet |
| a26f78a9 | RUNSHEET-WORDING fixer r42 | sonnet | run sheet wording; video path: YES, finishing only | 20:35Z | 21:20Z | running | none yet |
| a8af5aed | patch-copies pass 28 fixer | sonnet | patch copies; video path: NO, finishing only | 20:37Z | 21:10Z | running | none yet |

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
