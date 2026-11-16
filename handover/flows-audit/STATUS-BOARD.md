UPDATED_UTC: 2026-11-16T13:44:54Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 84
AGENTS_RUNNING: 5
CAPACITY: 1.80 load of 4 cores, mem 0/15 GB, RAM 1001/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.6G /tmp/claude-0 , agents 5 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: F8 r8, TC/FP fixer, REVIEW r16 facts, claims r6, FINDINGS cites
PUSHED_UTC: 2026-11-16T13:44:54Z

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
| a494960 | fixer | sonnet | RUNBOOK/TC/FP round 12 Majors | 13:39Z | 14:25Z | running | log fix-tcfp8.md |
| a57a3a0 | reviewer | sonnet | REVIEW.md round 16 facts (uncapped) | 13:39Z | 14:00Z | running | findings inline |
| a25d7a2 | fixer | sonnet | CLAIMS-TABLE round 6 (reader+facts) | 13:44Z | 14:20Z | running | log fix-claims6.md |
| FINDINGS-cite | fixer | sonnet | FINDINGS.md citation repoint (28 MISMATCH) | 13:45Z | 14:15Z | running | log fix-cite9.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Fixer for REVIEW.md round 16 (design findings saved; waits on facts reviewer a57a3a0)
2. Evidence runner + fresh F8 review (waits on a83d02c)
3. Facts + second-angle review of CLAIMS-TABLE round 7 (waits on a25d7a2)
4. Citation fix for OWNER-STEPS-q16-rows.md (8 MISMATCH; file owned by owner-sheet lane) and RUNBOOK/TC cites (after a494960)
5. Post-twice script review (waits on lead, Q29-4)
Missing lanes (3 of 8): rows 1-4 each wait on a running agent's report; row 5 waits on a lead answer.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
