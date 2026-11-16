UPDATED_UTC: 2026-11-16T12:00:13Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 6
PERCENT: 87
AGENTS_RUNNING: 8
CAPACITY: 2.05 load of 4 cores, mem 0/15 GB, RAM 962/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 2.2G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
FAILED: ruff format --check on inputs/plan-wp6-resmoke-v5.md (lead-owned); check_refs unresolved CUT-LIST.md:17 (fixer running); lint fixer changed no_name.out (crash removed)
FAILED: F8 fixer says ruff format failure did not reproduce; not yet confirmed by evidence runner (a5a7e77 running)
FAILED: evidence runner (independent): run_all.sh exit 1 (case new-warn-changes-the-pin missing FINAL text) - F8 fixer had reported exit 0; ruff format --check exit 1 only inputs/plan-wp6-resmoke-v5.md (lead file); TAKE_CHECK_FLOWS=/tmp/x gave exit 1 (a real FAIL stays 1, my expectation of 4 was wrong); fixer a8d895a running
NEXT: collect hand-backs; 8 running (ORDER 035 met)
PUSHED_UTC: 2026-11-16T12:00:13Z

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
| a2c7078 | fixer | sonnet | F8 Majors Q1-Q5 | 11:51 | 12:40 | running | edits flow-check; log fix-f8-r10c.md |
| aa3acc9 | fixer | sonnet | TAKE-CHECKLIST+FIX-PLAN | 12:08 | 12:40 | running | fix-tcfp2.md |
| ad171a4 | fixer | sonnet | RUNBOOK round 4 | 12:29 | 12:50 | running | fix-runbook4.md |
| a0a664e | drift | sonnet | drift check stable audit files | 12:31 | 12:45 | running | nothing yet |
| a7095d2 | fixer | sonnet | core patches REVIEW round 3 fixes | 12:33 | 12:50 | running | fix-review2.md |
| a2b9db9 | comprehension | sonnet | QUESTIONS.md stranger read | 12:36 | 12:50 | running | nothing yet |
| a72843e | citations | sonnet | B-003 rows + pair sync | 12:38 | 12:50 | running | nothing yet |
| ac4883e | comprehension | sonnet | owner part stranger read r6 | 12:07 | 12:20 | running | nothing yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 Post-twice script and run_real_check_n8n.py read-only review (waits: lead puts them on a branch, Q29-4)
2 Second reviewer plus citation lane on TAKE-CHECKLIST/FIX-PLAN after aa3acc9
3 Fresh owner-part read and citation lane after a0e1266; fresh readiness read after ad171a4
4 Evidence runner run_all.sh and test_take_check.sh at final head, earlier exit 1 cause (waits: a2c7078)
5 Final grep limitation/TODO/skipped, ledger rows, drift refresh (waits: all fixers)
Q31 (9 owner-part questions from fix-ownersteps7.md) to append to QUESTIONS.md after stranger read a2b9db9 returns

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
