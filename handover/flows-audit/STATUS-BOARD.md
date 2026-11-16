UPDATED_UTC: 2026-11-16T19:25:04Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 5
CAPACITY: 2.47 load of 4 cores, mem 1/15 GB, RAM 1271/16087 MB, disk 19G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 4.8G /tmp/claude-0 , agents 5 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: see next5; disk and load order done (freed 8774 MB)
PUSHED_UTC: 2026-11-16T19:25:04Z

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
| ad8cc2b7 | fixer | sonnet | plan-files r41 (RUNBOOK, TAKE-CHECKLIST, FIX-PLAN) | 19:25Z | +60 min | working | - |
| a07d45a1 | fixer | sonnet | Q31 r36 (QUESTIONS from line 420) | 19:25Z | +60 min | working | - |
| a0cab3b9 | fixer | sonnet | FINDINGS/LEDGER r30 | 19:25Z | +60 min | working | - |
| ae9180af | fixer | sonnet | REVIEW.md r47 (uncapped) | 19:25Z | +60 min | working | - |
| aabf71c4 | evidence runner | sonnet | F8 r12 evidence (heavy; only heavy job) | 19:10Z | ~19:50Z | working | raw test run in progress |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 REVIEW.md readers 408-451, 459-550, 580-884 (after r47 fixer)
2 Q31 reader lines 641-805
3 RUNBOOK reader 1-214 and 233-428
4 F8 fixer after evidence, then fresh reviewers
5 verify r43/r21 outputs by fresh reviewers; drift-007 r3
DISK 19G free (was 9.9G, freed 8774 MB). Top 5 users: scratchpad pc21 1455MB, six /tmp/tmp.* clones ~2.9G (not yet checked), /root/.claude 888MB, repo 773MB, p20 218MB. Load 3.6, heavy jobs 1 of 3.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
