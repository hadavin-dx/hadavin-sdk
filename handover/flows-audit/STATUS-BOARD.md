UPDATED_UTC: 2026-11-16T09:44:23Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 76
AGENTS_RUNNING: 8
CAPACITY: 4.66 load of 4 cores, mem 0/15 GB, disk free 28G, agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: fixer done (14 mutants killed by its own run); independent rerun + fresh security review running; Python 3.9/3.10 never run (README says 3.9+)
ROLES: script 5 mutants survive + 7 script gaps; doc 8 Majors from security r3 (two fixers running)
claims: no fresh review of r3 yet (2 reviewers running); F-01 unreadable; 'the lead' wording left in pasted text
F5: T8 Blocker (final fixer running)
NEXT: collect F8, F5, ROLES x2, claims x2, F3 x2
PUSHED_UTC: 2026-11-16T09:44:23Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
