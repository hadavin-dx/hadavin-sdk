UPDATED_UTC: 2026-11-16T13:49:30Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 85
AGENTS_RUNNING: 5
CAPACITY: 2.05 load of 4 cores, mem 0/15 GB, RAM 952/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.6G /tmp/claude-0 , agents 5 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: claims r6, REVIEW r16, consistency review, F8 evidence+review
PUSHED_UTC: 2026-11-16T13:49:30Z

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
| a25d7a2 | fixer | sonnet | CLAIMS-TABLE round 6 (reader+facts) | 13:44Z | 14:20Z | running | log fix-claims6.md |
| a367f46 | fixer | sonnet | REVIEW.md round 16 (uncapped) | 13:46Z | 14:20Z | running | log fix-review12.md |
| a87f48a | reviewer | sonnet | r13 consistency review RUNBOOK/TC/FP | 13:47Z | 14:05Z | running | findings inline |
| aab40a2 | evidence | sonnet | F8 r8 evidence runner (run_all plain vs --strict) | 13:47Z | 14:10Z | running | flow-check/evidence-f8-r8.md |
| a91df71 | reviewer | sonnet | F8 r8 fresh code review (uncapped) | 13:47Z | 14:05Z | running | findings inline |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Fixer for FIX-PLAN/TC/RUNBOOK round 13 (stranger read saved; waits on consistency review a87f48a)
2. Facts + second-angle review of CLAIMS-TABLE round 7 (waits on a25d7a2)
3. Fresh round 17 review of REVIEW.md (waits on a367f46)
4. F8 round 9 fixer (waits on aab40a2 and a91df71)
5. Post-twice script review (waits on lead, Q29-4)
Missing lanes (3 of 8): rows 1-4 wait on a running agent's report; row 5 waits on a lead answer. check_secrets currently FAILS on flow-check/raw/test-take-check.txt (long hostile line written by the evidence run); recheck after aab40a2.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
