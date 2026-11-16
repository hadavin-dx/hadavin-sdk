UPDATED_UTC: 2026-11-16T13:35:49Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 80
AGENTS_RUNNING: 6
CAPACITY: 0.36 load of 4 cores, mem 0/15 GB, RAM 940/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.5G /tmp/claude-0 , agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: claims fixer, drift refresh, r12 reviews, F8 r8, REVIEW r15
PUSHED_UTC: 2026-11-16T13:35:49Z

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
| a83d02c | fixer | sonnet | F8 take_check.sh reviewer_ok round 8 (uncapped) | 13:31Z | 14:15Z | running | edits flow-check files, log fix-f8-r8.md |
| ac31c40 | fixer | sonnet | REVIEW.md round 15 (core patches, uncapped) | 13:32Z | 14:15Z | running | edits REVIEW.md, log fix-review12.md |
| ac58611 | reviewer | sonnet | r12 consistency review RUNBOOK/TAKE-CHECKLIST/FIX-PLAN | 13:34Z | 13:55Z | running | findings inline |
| a57e58c | reviewer | sonnet | r12 stranger read FIX-PLAN/TAKE-CHECKLIST | 13:34Z | 13:55Z | running | findings inline |
| a7b9b54 | fixer | sonnet | CLAIMS-TABLE r5 Majors | 13:35Z | 14:10Z | running | edits CLAIMS-TABLE.md, log fix-claims5.md |
| a05ea97 | drift | sonnet | refresh drift-007 | 13:36Z | 13:55Z | running | writes reviews/drift-007.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Facts + second-angle review of CLAIMS-TABLE after fixer a7b9b54 (needs its report)
2. Citation-fix pass for 41 MISMATCH rows (waits for QUESTIONS/RUNBOOK/TC to settle)
3. Evidence runner + fresh F8 review after a83d02c (needs its report)
4. Round 16 REVIEW.md review after ac31c40 (needs its report)
5. Post-twice script / run_real_check_n8n.py review (needs lead to place files on a branch, Q29-4)
Missing lanes (2 of 8): rows 1-5 above each wait on a running agent or a lead answer.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
