UPDATED_UTC: 2026-11-16T12:56:11Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 14
PERCENT: 72
AGENTS_RUNNING: 8
CAPACITY: 0.92 load of 4 cores, mem 0/15 GB, RAM 944/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.4G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: fix batches from r8/r9 reviews; fresh reviews RUNBOOK, REVIEW r12, QUESTIONS, F8; TAKE-CHECKLIST fixer after ab19a3a
PUSHED_UTC: 2026-11-16T12:56:11Z

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
| ab19a3a | reviewer | sonnet | TAKE-CHECKLIST/FIX-PLAN commands check | 12:30Z | 13:15Z | running | pending |
| a1c3222 | reviewer | sonnet | OWNER-STEPS owner part stranger read r17 | 12:50Z | 13:15Z | running | pending |
| a50fc9a | reviewer | sonnet | RUNBOOK r8 readiness review | 12:56Z | 13:20Z | running | pending |
| a354419 | reviewer | sonnet | REVIEW.md r12 design | 12:56Z | 13:20Z | running | pending |
| a590669 | reviewer | sonnet | REVIEW.md r12 code | 12:56Z | 13:20Z | running | pending |
| aa2e135 | fixer | sonnet | FINDINGS/LEDGER r9 fixes | 12:56Z | 13:25Z | running | pending |
| a53e161 | reviewer | sonnet | F8 round 5 result review | 12:56Z | 13:20Z | running | pending |
| a3450a3 | reviewer | sonnet | QUESTIONS fresh review | 12:56Z | 13:20Z | running | pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Fresh stranger read of QUESTIONS after round 7 (Blockers/Majors only) once the owner-part fixer is done
2. Citation lane on RUNBOOK/TAKE-CHECKLIST numbers and cites after r6 reads
3. Post-twice script and run_real_check_n8n.py read-only review (waits: lead puts them on a branch, Q29-4)
4. Evidence runner + review of F8 round 4 after fixer
5. Drift report refresh reviews/drift-007.md before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
