UPDATED_UTC: 2026-11-16T13:59:21Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 6
CAPACITY: 0.39 load of 4 cores, mem 0/15 GB, RAM 980/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.8G /tmp/claude-0 , agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: 4 fixers, runsheet read, citation check
PUSHED_UTC: 2026-11-16T13:59:21Z

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
| a8c98de | fixer | sonnet | RUNBOOK/TC/FP r13 Blockers+Majors | 13:52Z | 14:32Z | running | log fix-tcfp9.md |
| a0e711c | fixer | sonnet | CLAIMS-TABLE round 7 (reader+facts) | 13:57Z | 14:37Z | running | log fix-claims7.md |
| a50b314 | fixer | sonnet | REVIEW.md round 17 (uncapped) | 13:58Z | 14:43Z | running | log fix-review12.md |
| abfcd0a | fixer | sonnet | F8 round 9 (uncapped) + check_secrets raw fix | 13:58Z | 14:48Z | running | log flow-check/fix-f8-r9.md |
| a502aa4 | reviewer | sonnet | RUNSHEET-WORDING stranger read | 14:00Z | 14:20Z | running | findings inline |
| a344961 | citation | sonnet | citation checker rerun (FINDINGS, QUESTIONS, REPORT, etc.) | 14:00Z | 14:30Z | running | reviews/citation-r9.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Evidence runner for F8 round 9 final head (waits on abfcd0a)
2. Fresh uncapped F8 round 9 review (waits on abfcd0a and evidence)
3. Fresh REVIEW.md round 18 review, uncapped (waits on a50b314)
4. Claims round 8 facts + stranger reviews, Blockers/Majors only (waits on a0e711c)
5. Post-twice script review (waits on lead, Q29-4)
Missing lanes (2 of 8): rows 1-4 wait on running fixers (editing the same files, so reviewing now would read stale text); row 5 waits on lead answer Q29-4. Lead answers needed: claims r6 items (a)-(f); RUNBOOK commands (n8n start, sub-workflow id, values loop, import, export); who types end/y/challenge number; F8 refused-name remedy.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
