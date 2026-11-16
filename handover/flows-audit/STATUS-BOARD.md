UPDATED_UTC: 2026-11-16T14:12:03Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 0.66 load of 4 cores, mem 0/15 GB, RAM 1017/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check (checker run or fresh reviewer): see items.txt; no item closed since 13:59Z, so percent unchanged; agents finishing do not count.
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: 1. REVIEW.md round 18 fixer for Blockers/Majors (waits on the three r18 reviewers) 2. Evidence runner for F8 round 9 final head, then fresh uncapped review (waits on abfcd0a) 3. Fresh stranger read of RUNSHEET-WORDING after round 2 (waits on a1660d9) 4. Fresh r15 review of FP/TC/RUNBOOK (waits on aad5a30) 5. Post-twice script review (waits on lead, Q29-4) 
PUSHED_UTC: 2026-11-16T14:12:03Z

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
| abfcd0a | fixer | sonnet | F8 round 9 (uncapped) + raw-file secret fix | 13:58Z | 14:48Z | running | log flow-check/fix-f8-r9.md |
| a1660d9 | fixer | sonnet | RUNSHEET-WORDING round 2 + count line 19 | 14:07Z | 14:40Z | running | log fix-rswording8.md |
| aad5a30 | fixer | sonnet | FP/TC/RUNBOOK round 14 (part 1, part 2, consistency) | 14:08Z | 14:55Z | running | log fix-tcfp10.md |
| aad511e | citation | sonnet | citation checker r10 on rewritten cites | 14:09Z | 14:30Z | running | reviews/citation-r10.md |
| a71df70 | fixer | sonnet | CLAIMS-TABLE round 8 (reader + facts) | 14:10Z | 14:45Z | running | log fix-claims8.md |
| a178eab | reviewer | sonnet | REVIEW.md r18 stranger read (uncapped) | 14:11Z | 14:30Z | running | findings inline |
| afb3350 | reviewer | sonnet | REVIEW.md r18 design review (uncapped) | 14:11Z | 14:30Z | running | findings inline |
| a7bdfc7 | reviewer | sonnet | REVIEW.md r18 facts review (uncapped) | 14:11Z | 14:30Z | running | findings inline |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md round 18 fixer for Blockers/Majors (waits on the three r18 reviewers)
2. Evidence runner for F8 round 9 final head, then fresh uncapped review (waits on abfcd0a)
3. Fresh stranger read of RUNSHEET-WORDING after round 2 (waits on a1660d9)
4. Fresh r15 review of FP/TC/RUNBOOK (waits on aad5a30)
5. Post-twice script review (waits on lead, Q29-4)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
