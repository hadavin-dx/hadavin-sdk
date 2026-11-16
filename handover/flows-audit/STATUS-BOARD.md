UPDATED_UTC: 2026-11-16T13:54:16Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 85
AGENTS_RUNNING: 6
CAPACITY: 5.49 load of 4 cores, mem 0/15 GB, RAM 998/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.8G /tmp/claude-0 , agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: REVIEW r16 fixer, F8 evidence+review, TC/FP/RUNBOOK fixer, claims r7 reviews
PUSHED_UTC: 2026-11-16T13:54:16Z

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
| a367f46 | fixer | sonnet | REVIEW.md round 16 (uncapped) | 13:46Z | 14:20Z | running | log fix-review12.md |
| aab40a2 | evidence | sonnet | F8 r8 evidence runner | 13:47Z | 14:10Z | running | flow-check/evidence-f8-r8.md |
| a91df71 | reviewer | sonnet | F8 r8 fresh code review (uncapped) | 13:47Z | 14:05Z | running | findings inline |
| a8c98de | fixer | sonnet | RUNBOOK/TC/FP r13 Blockers+Majors | 13:52Z | 14:32Z | running | log fix-tcfp9.md |
| a3aa4e0 | reviewer | sonnet | CLAIMS-TABLE r7 facts review | 13:53Z | 14:10Z | running | findings inline |
| a36aa5c | reviewer | sonnet | CLAIMS-TABLE r7 stranger read | 13:53Z | 14:10Z | running | findings inline |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. RUNSHEET-WORDING.md fixer: counts 119/70/61/29/48 and rows for A-015, A-024, A-049, B-102, A-039 (can start now; check_runsheet_paste FAILS)
2. Fixer for CLAIMS-TABLE r7 Blockers/Majors (waits on a3aa4e0, a36aa5c)
3. Fresh round 17 review of REVIEW.md (waits on a367f46)
4. F8 r9 fixer (waits on aab40a2, a91df71)
5. Post-twice script review (waits on lead, Q29-4)
Missing lanes (2 of 8): rows 2-4 wait on running agents' reports; row 5 waits on lead answer Q29-4. Lead answers needed: claims items (a)-(f) in the claims r6 hand-back (R:41 delete, n of 13-minute delay, loopback line 153, names of adversarial read r2/REVIEW r1, five OVERSTATED rows, check_secrets raw file).

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
