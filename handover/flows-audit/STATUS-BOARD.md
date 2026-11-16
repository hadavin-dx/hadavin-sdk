UPDATED_UTC: 2026-11-16T09:56:48Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 85
AGENTS_RUNNING: 7
CAPACITY: 1.04 load of 4 cores, mem 0/15 GB, disk free 27G, agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: fixer done (469 as expected, 0 not, 32 skipped; own mutation 39 of 42 caught, 3 equivalent); independent rerun + second reviewer running; $env nodes + 2 webhooks without auth are lead decisions; secret values of 5 characters or fewer not checked
F3: rerun clean earlier; fresh security review r2 found no Blocker but 12 real Minor/Nit (nested-template lexer, delete recovery dead end, delete not idempotent, missing-value copy written); r5 fixer running; 3.9/3.10, macOS, live import not run
ROLES: v4 doc has a security Blocker (Part C unguarded, can lock out the administrator) + 8 Majors, marked in file, NOT fixed (parked pending Q11); script: 3 mutants still survive (R5-08, R5-20, R5-22), r6 fixer running; split-string SQL in Code nodes only caught if text names mf_leads
claims: reviews found 16 Majors (swapped rows 13/18 cites, wrong OWNER-STEPS line, "lead" word, undefined labels, 114 SUPPORTED includes rows needing a run); r4 fixer running; F-01 still unreadable
F5: round 4 reviews found 4 Blockers + about 20 Majors incl. false "not in this checkout" reason (programs ARE in handover/demo); r4 fixer running
NEXT: collect F3 r5, F5 r4, claims r4, ROLES r6, cite check, F8 rerun+review
PUSHED_UTC: 2026-11-16T09:56:48Z

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
| a7314db5 | claims r4 fixer | sonnet | fix 3 facts Majors + 13 reader Majors | 09:54 | 10:10 | 5 | running | reviews-f1/fix-f1-r4.md |
| aca2f0a2 | F5 round 4 fixer | sonnet | fix 5 facts Majors + 4 Blockers + Majors | 09:56 | 10:12 | 5 | running | fix-f5-r4.md |
| a4083fcf | F3 round 5 fixer | sonnet | fix 12 security findings | 09:59 | 10:15 | 5 | running | fill_flows/fix-f3-r5.md |
| a242e3cb | ROLES r6 fixer | sonnet | kill 3 surviving mutants | 09:58 | 10:12 | 5 | running | roles-coverage-check/fix-roles-r6.md |
| cite-f6b-f2 | citation checker F6b+F2 | sonnet | check cites in F6B-AUDIT, F2 REVIEW | 09:57 | 10:10 | 5 | running | reviews/citations-f6b-f2.md |
| f8-ev | EVIDENCE RUNNER F8 r2 | sonnet | rerun checker, selftest, gate, mutants | 09:58 | 10:12 | 5 | running | flow-check/evidence-r2.md |
| f8-rev | F8 second reviewer | sonnet | find false passes | 09:58 | 10:10 | 5 | running | (report inline) |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
