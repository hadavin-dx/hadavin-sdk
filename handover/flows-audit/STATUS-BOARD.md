UPDATED_UTC: 2026-11-16T09:48:47Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 82
AGENTS_RUNNING: 7
CAPACITY: 1.81 load of 4 cores, mem 0/15 GB, disk free 28G, agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: fixer done (14 mutants killed by its own run); independent rerun + fresh security review running; Python 3.9/3.10 never run (README says 3.9+)
ROLES: script fixed, rerun running; doc v4 rewritten (guard uses unverified psql features), 2nd security review running; script still has S3 credential check off by default
claims: reviews found 16 Majors (swapped rows 13/18 cites, wrong OWNER-STEPS line, "lead" word, undefined labels, 114 SUPPORTED includes rows needing a run); r4 fixer running; F-01 still unreadable
F5: fresh reader found 4 Blockers (address wording, ungated "same alert logic", step 9 switch, card line numbers) + 15 Majors; facts reviewer pending; round 4 fixer to follow
NEXT: collect F8, F3 x2, F5 facts, ROLES evidence + doc review, claims fixer; then F5 round 4 fixer
PUSHED_UTC: 2026-11-16T09:48:47Z

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
| ab790c7cf5d1d6137 | fixer F8 r2 | sonnet | REPORT.md start-here + header | 09:37 | 09:50 | 20 | running | flow-check/ |
| afea7e66 | F3 evidence rerun | sonnet | EVIDENCE RUNNER tests, mutants, hostile inputs | 09:50 | 10:02 | 5 | running | fill_flows/evidence-f3-r4-rerun.md |
| a3c7bc5f | F3 security reviewer r2 | egm-design | fresh static security review | 09:50 | 10:00 | 5 | running | inline |
| aab6e65c | F5 facts reviewer | egm-codebase-details | fresh cites/numbers check | 09:52 | 10:02 | 5 | running | inline |
| a10cbf4d | ROLES script evidence r4 | sonnet | EVIDENCE RUNNER tests, mutants, 15 hostile flows | 09:55 | 10:07 | 5 | running | roles-coverage-check/evidence-r4.md |
| a40b5f68 | ROLES doc v4 security reviewer | egm-design | fresh static security review | 09:52 | 10:02 | 5 | running | inline |
| a7314db5 | claims r4 fixer | sonnet | fix 3 facts Majors + 13 reader Majors | 09:54 | 10:10 | 5 | running | reviews-f1/fix-f1-r4.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
