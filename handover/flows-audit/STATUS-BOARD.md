UPDATED_UTC: 2026-11-16T09:41:28Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 12
PERCENT: 72
AGENTS_RUNNING: 8
CAPACITY: 2.67 load of 4 cores, mem 0/15 GB, disk free 28G, agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: F8 checker: 4 nodes read $env, 2 webhooks lack auth (lead decides); F8 false-pass review found 7 Majors incl crashes (fixer running); F3 mutants + security Majors (fixer running); ROLES coverage script had 5 surviving mutants (fixed, independent rerun running); ROLES r2 security review running; claims table reader Blockers (fixer running), 167 citation quotes still unmatched by naive script; F5 round 3 Blocker false T8 wording (fixer running); F6b re-take path Majors (fixer running)
NEXT: collect fixers; final checks; REPORT.md entries
PUSHED_UTC: 2026-11-16T09:41:28Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback audit | done | 100 | F6-AUDIT.md | 2 review rounds + reader pass; n8n facts unverified |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a72b276594a01d0e0 | fixer F3 r4 | sonnet | kill 3 mutants + security fixes | 09:40 | 09:58 | 20 | running | fill_flows/ |
| ab790c7cf5d1d6137 | fixer F8 r2 | sonnet | REPORT.md start-here + header | 09:37 | 09:50 | 20 | running | flow-check/ |
| (roles sec r3) | reviewer ROLES security r3 | sonnet | fresh security design | 09:57 | 10:05 | 30 | running | - |
| a95683a64bf2e3ca8 | fixer F5 final | sonnet | Blockers and Majors from r3 reader and facts | 10:03 | 10:13 | 20 | running | RUNSHEET-WORDING.md |
| (claims r3 fixer) | fixer claims table reader fixes | sonnet | Blockers/Majors from reader | 10:04 | 10:15 | 30 | running | CLAIMS-TABLE.md |
| (F6b r4 fixer) | fixer F6b re-take path | sonnet | 2 Majors + nits | 10:06 | 10:14 | 20 | running | F6B-AUDIT.md |
| (roles rerun) | evidence ROLES script rerun | sonnet | 18 own mutants | 10:08 | 10:16 | 30 | running | roles-coverage-check/evidence-rerun.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
