UPDATED_UTC: 2026-11-16T11:40:15Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 10
PERCENT: 62
AGENTS_RUNNING: 7
CAPACITY: 0.82 load of 4 cores, mem 0/15 GB, RAM 915/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 1.9G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
FAILED: ruff format --check on inputs/plan-wp6-resmoke-v5.md (lead-owned); check_refs unresolved CUT-LIST.md:17 (fixer running); lint fixer changed no_name.out (crash removed)
FAILED: F8 fixer says ruff format failure did not reproduce; not yet confirmed by evidence runner (a5a7e77 running)
NEXT: wait for 7 agents; verify F8 evidence, RUNBOOK reviews, RW/CT + owner-sheet fixes
PUSHED_UTC: 2026-11-16T11:40:15Z

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
| a27d6c9 | RW/CT fixer | sonnet | adversarial B1-M9 | 11:40 | - | 40 | RUNNING | fix-rwct3.md |
| a36a8ea | OWNER-STEPS fixer | sonnet | stranger B1-B6 | 11:40 | - | 40 | RUNNING | fix-ownersteps3.md |
| a488a19 | citation check CHECKLIST | sonnet | TAKE-CHECKLIST cites | 11:41 | - | 50 | RUNNING | inline |
| a8b8781 | stranger read RUNBOOK | sonnet | RUNBOOK | 11:50 | - | 5 | RUNNING | inline |
| af37b44 | readiness RUNBOOK | sonnet | RUNBOOK cmds | 11:50 | - | 5 | RUNNING | inline |
| a5a7e77 | EVIDENCE RUNNER F8 r10 | sonnet | flow-check rerun | 11:52 | - | 5 | RUNNING | flow-check/evidence-r10.md |
| a3330df | review F8 r10 | sonnet | flow-check code | 11:52 | - | 5 | RUNNING | inline |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
