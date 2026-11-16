UPDATED_UTC: 2026-11-16T12:51:46Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 92
AGENTS_RUNNING: 8
CAPACITY: 1.66 load of 4 cores, mem 0/15 GB, RAM 984/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.3G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: collect fixers/reviewers; ORDER 037 stale-text alignment; drift-007 refresh; limitation grep
PUSHED_UTC: 2026-11-16T12:51:46Z

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
| ae01e2f | fixer | sonnet | RUNBOOK round 7 B1+M1-M10 + 2 more | 12:46Z | 13:20Z | running | none yet |
| ac782bc | fixer | sonnet | REVIEW.md round 11 | 12:49Z | 13:15Z | running | none yet |
| a7d8d25 | fixer | sonnet | OWNER-STEPS owner part round 16 | 12:50Z | 13:15Z | running | none yet |
| a8401c8 | egm-codebase-details | sonnet | FINDINGS/LEDGER r9 cites+commands | 12:48Z | 13:05Z | running | none yet |
| a98c43c | egm-implementation-readiness | sonnet | FINDINGS r9 readiness | 12:48Z | 13:05Z | running | none yet |
| af4d0e2 | evidence runner | sonnet | F8 round 5 evidence | 12:51Z | 13:15Z | running | none yet |
| ab19a3a | egm-codebase-details | sonnet | TAKE-CHECKLIST/FIX-PLAN r8 commands | 12:51Z | 13:10Z | running | none yet |
| a83994a | egm-implementation-readiness | sonnet | TAKE-CHECKLIST/FIX-PLAN r8 readiness | 12:51Z | 13:10Z | running | none yet |

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
