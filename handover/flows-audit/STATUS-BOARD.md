UPDATED_UTC: 2026-11-16T13:40:06Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 83
AGENTS_RUNNING: 6
CAPACITY: 0.19 load of 4 cores, mem 0/15 GB, RAM 931/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.5G /tmp/claude-0 , agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: TC/FP fixer, REVIEW r16 x2, claims fixer, F8 r8, REPORT fixer
PUSHED_UTC: 2026-11-16T13:40:06Z

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
| a83d02c | fixer | sonnet | F8 take_check.sh reviewer_ok round 8 (uncapped) | 13:31Z | 14:15Z | running | edits flow-check files |
| a7b9b54 | fixer | sonnet | CLAIMS-TABLE r5 Majors | 13:35Z | 14:10Z | running | CLAIMS-TABLE.md edited (33 lines so far) |
| a494960 | fixer | sonnet | RUNBOOK/TC/FP round 12 Majors | 13:45Z | 14:25Z | running | log fix-tcfp8.md |
| a044860 | reviewer | sonnet | REVIEW.md round 16 design (uncapped) | 13:50Z | 14:10Z | running | findings inline |
| a57a3a0 | reviewer | sonnet | REVIEW.md round 16 facts (uncapped) | 13:50Z | 14:10Z | running | findings inline |
| a107e04 | fixer | sonnet | REPORT.md drift items and ORDER 037 file list | 13:41Z | 14:00Z | running | log fix-report3.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Evidence runner + fresh F8 review after a83d02c reports
2. Facts + second-angle review of CLAIMS-TABLE after a7b9b54
3. Citation-fix pass (41 MISMATCH) after TC/FP/RUNBOOK fixer a494960 settles
4. Fixer for REVIEW.md round 16 findings (after a044860, a57a3a0)
5. Post-twice script review (waits on lead, Q29-4)
Missing lanes (2 of 8): rows 1-4 each wait on a running agent's report; row 5 waits on a lead answer.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
