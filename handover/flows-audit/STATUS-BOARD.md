UPDATED_UTC: 2026-11-16T11:47:13Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 10
PERCENT: 72
AGENTS_RUNNING: 5
CAPACITY: 0.83 load of 4 cores, mem 0/15 GB, RAM 938/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 2.0G /tmp/claude-0 , agents 5 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
FAILED: ruff format --check on inputs/plan-wp6-resmoke-v5.md (lead-owned); check_refs unresolved CUT-LIST.md:17 (fixer running); lint fixer changed no_name.out (crash removed)
FAILED: F8 fixer says ruff format failure did not reproduce; not yet confirmed by evidence runner (a5a7e77 running)
FAILED: evidence runner (independent): run_all.sh exit 1 (case new-warn-changes-the-pin missing FINAL text) - F8 fixer had reported exit 0; ruff format --check exit 1 only inputs/plan-wp6-resmoke-v5.md (lead file); TAKE_CHECK_FLOWS=/tmp/x gave exit 1 (a real FAIL stays 1, my expectation of 4 was wrong); fixer a8d895a running
NEXT: 5 running, not 8: RUNBOOK and F8 reviewers/evidence must wait for their fixers; started RW/CT and OWNER-STEPS fixers. Disk 26G free 34pct
PUSHED_UTC: 2026-11-16T11:47:13Z

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
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a8d895a | F8 r2 fixer | sonnet | flow-check fixes | 11:20 | 12:30 | 60 | running | flow-check/fix-f8-r10b.md |
| a56ef1f | RUNBOOK fixer | sonnet | RUNBOOK r2 + Q27 | 11:15 | 12:15 | 60 | running | fix-runbook2.md |
| ab1ebd7 | design | sonnet | stale Q27 text checklist/FIX-PLAN | 11:47 | 12:05 | 40 | running | reviews/ |
| a28c12d | fixer | sonnet | RW/CT r2 BL1 MJ1-5 | 11:50 | 12:20 | 10 | running | fix-rwct4.md |
| aeccf8b | fixer | sonnet | OWNER-STEPS r2 + NOTE | 11:57 | 12:25 | 5 | running | fix-ownersteps5.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
