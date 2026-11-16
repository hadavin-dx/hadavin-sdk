UPDATED_UTC: 2026-11-16T09:46:14Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 80
AGENTS_RUNNING: 9
CAPACITY: 5.22 load of 4 cores, mem 0/15 GB, disk free 28G, agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: fixer done (14 mutants killed by its own run); independent rerun + fresh security review running; Python 3.9/3.10 never run (README says 3.9+)
ROLES: script fixed by its own run (22 of 25 new tests fail on old; S3 credential check OFF by default, 14 failures with it on); independent rerun running; doc fixer running (8 Majors)
claims: no fresh review of r3 yet (2 reviewers running); F-01 unreadable; 'the lead' wording left in pasted text
F5: all Blockers/Majors fixed by r3 fixer but NOT reviewed since; N-8 start commands, ports, take-script switch UNCHECKED; 2 fresh reviewers running
NEXT: collect 9 agents; load above 4 cores so no new lanes until some finish
PUSHED_UTC: 2026-11-16T09:46:14Z

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
| (roles sec r3) | reviewer ROLES security r3 | sonnet | fresh security design | 09:57 | 10:05 | 30 | running | - |
| (claims r3 fixer) | fixer claims table reader fixes | sonnet | Blockers/Majors from reader | 10:04 | 10:15 | 30 | running | CLAIMS-TABLE.md |
| (roles rerun) | evidence ROLES script rerun | sonnet | 18 own mutants | 10:08 | 10:16 | 30 | running | roles-coverage-check/evidence-rerun.md |
| ae5d88f1 | claims reader r3 | egm-comprehension | naive read of CLAIMS-TABLE | 09:44 | 09:52 | 5 | running | inline |
| aa4dd7eb | claims facts r3 | egm-codebase-details | cites and totals check | 09:44 | 09:55 | 5 | running | inline |
| aeb408d4 | ROLES doc fixer r3 | sonnet | fix M1-M8, N1-N10 in ROLES-PROPOSAL.md | 09:47 | 10:00 | 5 | running | reviews-roles/fix-roles-r3.md |
| afea7e66 | F3 evidence rerun | sonnet | EVIDENCE RUNNER tests, mutants, hostile inputs | 09:50 | 10:02 | 5 | running | fill_flows/evidence-f3-r4-rerun.md |
| a3c7bc5f | F3 security reviewer r2 | egm-design | fresh static security review | 09:50 | 10:00 | 5 | running | inline |
| aab6e65c | F5 facts reviewer | egm-codebase-details | fresh cites/numbers check | 09:52 | 10:02 | 5 | running | inline |
| ad7e2658 | F5 reader reviewer | egm-comprehension | fresh naive read | 09:52 | 10:00 | 5 | running | inline |
| a10cbf4d | ROLES script evidence r4 | sonnet | EVIDENCE RUNNER tests, mutants, 15 hostile flows | 09:55 | 10:07 | 5 | running | roles-coverage-check/evidence-r4.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
