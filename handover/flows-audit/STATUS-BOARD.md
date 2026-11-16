UPDATED_UTC: 2026-11-16T09:30:00Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 6
PERCENT: 75
AGENTS_RUNNING: 8
CAPACITY: 0.94 load of 4 cores, mem 0/15 GB, disk free 29G, agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: F3 4 of 13 mutants survived (fixed, 75 tests, rerun running); F8 checker false passes (fixer running); roles proposal had a missing grant claim_token (Blocker, fixer running); claims table round-2 reader found 3 Blockers on readability (fix pending); 157 quotes in citations not matched (triage running)
NEXT: collect fixers (F1 r2, F5, F8, ROLES), F6b fixer after design review, F3 rerun results
PUSHED_UTC: 2026-11-16T09:30:00Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 92 | CLAIMS-TABLE.md | round 2 fixer running; citation triage running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | waiting | 60 | RUNSHEET-WORDING.md | fix after F1 table lands |
| F6 | idle fallback audit | done | 100 | F6-AUDIT.md | 2 review rounds + reader pass; n8n facts unverified |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aaa5a08748ba9d17a | fixer F8 r1 | sonnet | flow checker fixes | 09:27 | 09:45 | 70 | running | flow-check/ |
| a4cf28342000cc23b | fixer F5 r1 | sonnet | run-sheet wording fixes | 09:20 | 09:40 | 70 | running | RUNSHEET-WORDING.md |
| a2bafbe63ce21dd88 | fixer F1 r2 | sonnet | claims table round 2 + ORDER 017 facts | 09:30 | 09:50 | 10 | running | CLAIMS-TABLE.md |
| aab50790343456f97 | fixer ROLES r1 | sonnet | roles proposal fixes (security path) | 09:30 | 09:50 | 10 | running | ROLES-PROPOSAL.md |
| ae0051a8039d6a7df | reviewer F6b design | sonnet | review F6B-AUDIT.md | 09:30 | 09:40 | 30 | running | - |
| aee4bb56840c8d24b | citation triage | sonnet | classify 157 unmatched quotes | 09:30 | 09:45 | 20 | running | CITATION-TRIAGE.md |
| abc2d22151b3aca4e | EVIDENCE RUNNER F3 r4 | sonnet | tests, mutants, hostile inputs | 09:31 | 09:45 | 20 | running | fill_flows/evidence-f3-r4.md |
| a05a4f788c5ade6f3 | reviewer F3 security | sonnet | second reviewer, security and portability | 09:31 | 09:42 | 20 | running | - |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
