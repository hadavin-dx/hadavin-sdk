UPDATED_UTC: 2026-11-16T10:02:24Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 85
AGENTS_RUNNING: 8
CAPACITY: 3.00 load of 4 cores, mem 1/15 GB, disk free 27G, agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: second reviewer found 5 Majors (no-auth webhook only WARN, webhook credential kind unchecked, HubSpot credential uncovered, placeholder ids pass quietly, alwaysOutputData WARN only) + wrong doc lines; r3 fixer running after the evidence runner; $env nodes may fail on n8n default (unverified); 2 webhooks without auth are lead decisions
F3: rerun clean earlier; fresh security review r2 found no Blocker but 12 real Minor/Nit (nested-template lexer, delete recovery dead end, delete not idempotent, missing-value copy written); r5 fixer running; 3.9/3.10, macOS, live import not run
ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
claims: r4 reader review (lines 1-133 only) found 6 Blockers (overclaims coverage, recovery undefined, lead two meanings, rows 3 and 10 state unseen results) + Majors; facts reviewer and remainder reader running, r5 fixer waits; F-01 review unreadable so B-214, B-215 UNTRACED; fix-f5-r4.md deleted by this lane fixer, rebuilt
F5: r4 facts review 3 Majors (wrong line cites, wrong file named for stand-in start, CRM refuse switch exists) and reader review 6 Blockers (machine actions have no owner, step 9.1 placeholders, "recording" two meanings, rows claim more than evidence); r5 fixer applying scope cut real-v5 only; fix-f5-r4.md was deleted by another agent and rebuilt shorter; Q-A to Q-E moot after scope cut
F2: citation check found C-1 premise false (pydantic already refuses NaN/Infinity), counts wrong, cites wrong; fixer running; patches deferred by lead anyway
NEXT: scope cut to real-v5; collect F3 r5, F8 ev+r3, F5 r5, F2 fix, claims reviews, necessity
PUSHED_UTC: 2026-11-16T10:02:24Z

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
| a4083fcf | F3 round 5 fixer | sonnet | fix 12 security findings | 09:59 | 10:15 | 5 | running | fill_flows/fix-f3-r5.md |
| f8-ev | EVIDENCE RUNNER F8 r2 | sonnet | rerun checker, selftest, gate, mutants | 09:58 | 10:12 | 5 | running | flow-check/evidence-r2.md |
| f8-fix3 | F8 r3 fixer (Majors) | sonnet | fix 5 Majors + docs after evidence | 10:05 | 10:20 | 5 | running | flow-check/fix-f8-r3.md |
| cl-fac | claims r4 facts reviewer | sonnet | sample 40+ rows vs sources | 10:08 | 10:20 | 5 | running | (report inline) |
| nec | necessity review (zoom-out) | sonnet | purpose test after lead decisions | 10:07 | 10:18 | 5 | running | (report inline) |
| f5-fix5 | F5 r5 fixer (scope cut + Majors) | sonnet | real-v5 only, fix facts+reader Majors | 10:12 | 10:30 | 5 | running | fix-f5-r5.md |
| f2-fix | F2/F6b cite fixer | sonnet | fix wrong cites, C-1 premise | 10:12 | 10:25 | 5 | running | reviews/fix-citations-f6b-f2.md |
| cl-rd2 | claims reader review lines 134-end | sonnet | rest of table | 10:12 | 10:25 | 5 | running | (report inline) |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
