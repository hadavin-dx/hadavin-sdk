UPDATED_UTC: 2026-11-16T14:19:10Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.15 load of 4 cores, mem 1/15 GB, RAM 1050/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.8G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check (checker run or fresh reviewer): see items.txt; no item closed since 13:59Z, so percent unchanged; agents finishing do not count.
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: REVIEW.md r19; F8 r9 evidence; r15 reads; claims r10; post-twice script (lead)
PUSHED_UTC: 2026-11-16T14:19:10Z

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
| abfcd0a | F8 r9 fixer (uncapped) | sonnet | fix check_secrets hits, test_take_check, --strict docs | 13:55Z | 14:45Z | running | log fix-f8-r9.md |
| aad5a30 | FP/TC/RUNBOOK r14 fixer | sonnet | apply r14 findings, make Clock blocks identical | 14:00Z | 14:40Z | running | log fix-tcfp10.md |
| a741c91 | REVIEW.md r18 fixer (uncapped) | sonnet | apply reader/design/facts findings | 14:05Z | 14:50Z | running | log fix-review12.md |
| a786e82 | citation r11 on FINDINGS, LEDGER-ROWS | sonnet | recheck cites | 14:08Z | 14:35Z | running | reviews/citation-r11.md pending |
| ac1d614 | RUNSHEET-WORDING r3 fixer | sonnet | apply r3 reader M1-M11 | 14:14Z | 14:40Z | running | log fix-rswording9.md |
| a488ff4 | CLAIMS-TABLE r9 fixer | sonnet | apply facts blockers/majors + r5 part 2 + nits | 14:19Z | 14:50Z | running | log fix-claims9.md |
| a01ed9d | QUESTIONS Q31 fixer r1 | sonnet | counts, labels, answer-first index, key | 14:19Z | 14:45Z | running | log fix-q31-1.md |
| a4ba4bf | EVIDENCE RUNNER run_all.sh rerun | sonnet | run_all.sh plain and --strict, check_secrets | 14:19Z | 14:35Z | running | reviews/evidence-run-all-2.md |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md round 19 fresh reviews after a741c91 (uncapped)
2. F8 r9 evidence runner + fresh uncapped review after abfcd0a
3. Fresh r15 reads of FIX-PLAN/TAKE-CHECKLIST/RUNBOOK after aad5a30
4. Claims r10 fresh read after a488ff4, and RUNSHEET-WORDING re-read after ac1d614
5. Post-twice script review (waits on lead: Q29-4)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
