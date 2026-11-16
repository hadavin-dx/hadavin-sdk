UPDATED_UTC: 2026-11-16T09:51:49Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 84
AGENTS_RUNNING: 6
CAPACITY: 1.29 load of 4 cores, mem 0/15 GB, disk free 28G, agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: rerun clean earlier; fresh security review r2 found no Blocker but 12 real Minor/Nit (nested-template lexer, delete recovery dead end, delete not idempotent, missing-value copy written); r5 fixer running; 3.9/3.10, macOS, live import not run
ROLES: reviewer says it serves none of the 3 purposes of ORDER 017 for the take: marked CLIENT BUILD / AFTER VIDEO, question Q11 to coordinator; script fails repo lint gate + crashes on nodes:null (r5 fixer running); 2nd security review of v4 doc running
claims: reviews found 16 Majors (swapped rows 13/18 cites, wrong OWNER-STEPS line, "lead" word, undefined labels, 114 SUPPORTED includes rows needing a run); r4 fixer running; F-01 still unreadable
F5: round 4 reviews found 4 Blockers + about 20 Majors incl. false "not in this checkout" reason (programs ARE in handover/demo); r4 fixer running
NEXT: collect F8, F3 r5, F5 r4, claims r4, ROLES doc review, ROLES script r5; coordinator answers Q11
PUSHED_UTC: 2026-11-16T09:51:49Z

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
| a40b5f68 | ROLES doc v4 security reviewer | egm-design | fresh static security review | 09:52 | 10:02 | 5 | running | inline |
| a7314db5 | claims r4 fixer | sonnet | fix 3 facts Majors + 13 reader Majors | 09:54 | 10:10 | 5 | running | reviews-f1/fix-f1-r4.md |
| aca2f0a2 | F5 round 4 fixer | sonnet | fix 5 facts Majors + 4 Blockers + Majors | 09:56 | 10:12 | 5 | running | fix-f5-r4.md |
| a3e7d2e4 | ROLES script r5 fixer | sonnet | fix lint, bandit, null crash, notes, disabled, size | 09:57 | 10:10 | 5 | running | roles-coverage-check/fix-roles-r5.md |
| a4083fcf | F3 round 5 fixer | sonnet | fix 12 security findings | 09:59 | 10:15 | 5 | running | fill_flows/fix-f3-r5.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
