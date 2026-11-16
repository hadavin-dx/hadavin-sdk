UPDATED_UTC: 2026-11-16T12:35:52Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.87 load of 4 cores, mem 0/15 GB, RAM 979/16087 MB, disk 25G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.0G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: none now. ruff format --check rc 0 (504 files), ruff check rc 0 on 12:33Z head; the one file was lead-owned inputs/plan-wp6-resmoke-v5.md (ORDER 037 asked for the run; code-fence reformat only, listed in REPORT.md).
NEXT: collect 6 fixers; evidence + egm review per file; refresh drift-007
PUSHED_UTC: 2026-11-16T12:35:52Z

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
| ad63912 | fixer | sonnet | F8 round 4 (reviewer name, lock path) | 12:40 | 13:10 | running | - |
| ab7bbef | fixer | sonnet | REVIEW.md round 9 | 12:30 | 13:00 | running | - |
| ae01e2f | fixer | sonnet | RUNBOOK r6 Majors (5) + ORDER 037 stand-in text | 12:36 | 13:00 | running | - |
| ac847cb | fixer | sonnet | TAKE-CHECKLIST/FIX-PLAN r6 Majors (10) | 12:36 | 13:10 | running | - |
| a177eb6 | fixer | sonnet | FINDINGS/LEDGER ratings, pass lines (6) | 12:36 | 13:00 | running | - |
| aa359ac | fixer | sonnet | QUESTIONS r8 Majors (8) | 12:36 | 13:00 | running | - |
| a15903a | reviewer | sonnet | owner part stranger read r15 | 12:36 | 12:55 | running | - |
| ad7cb8d | evidence | sonnet | citation/time/sum check RUNBOOK, TAKE-CHECKLIST, FIX-PLAN | 12:36 | 13:00 | running | - |

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
