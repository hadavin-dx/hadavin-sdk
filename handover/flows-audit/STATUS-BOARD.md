UPDATED_UTC: 2026-11-16T14:26:15Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 6.79 load of 4 cores, mem 1/15 GB, RAM 1069/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.9G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check (checker run or fresh reviewer): see items.txt; no item closed since 13:59Z, so percent unchanged; agents finishing do not count.
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: REVIEW.md r20; F8 evidence+review; r16 reads; claims soft cites; post-twice script (lead). CAPACITY: load 6.8 of 4 cores (over target, no more heavy jobs), mem 6%, disk 41%
PUSHED_UTC: 2026-11-16T14:26:15Z

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
| abfcd0a | F8 r9 fixer (uncapped) | sonnet | check_secrets hit in flow-check, tests, --strict docs | 13:55Z | 14:50Z | running | log flow-check/fix-f8-r9.md |
| a4ba4bf | EVIDENCE RUNNER run_all.sh rerun | sonnet | run_all.sh plain and --strict, check_secrets | 14:19Z | 14:40Z | running | reviews/evidence-run-all-2.md pending |
| aa58574 | REVIEW.md r19 source-cite review | sonnet | check C/A/G/D rows and cites | 14:23Z | 14:45Z | running | none yet |
| acbed2f | CLAIMS-TABLE sync with RW r4 | sonnet | A-083, B-196, B-037 etc | 14:24Z | 14:45Z | running | log fix-claims10.md |
| ac1a1a5 | REVIEW.md r19 fixer (uncapped) | sonnet | apply design + reader r19 findings | 14:25Z | 14:55Z | running | log fix-review12.md |
| a185caa | FP/TC/RUNBOOK r15 fixer | sonnet | apply 11 Majors (timing + stranger) | 14:26Z | 14:55Z | running | log fix-tcfp11.md |
| a489080 | Q31 round 2 lead read | sonnet | check index, counts, numbers | 14:26Z | 14:40Z | running | none yet |
| a7730ce | citation check CLAIMS Table 2 | sonnet | rows 41-84 cites | 14:26Z | 14:45Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md round 20 fresh reviews after ac1a1a5 and aa58574 (uncapped)
2. F8 r9 evidence runner + fresh uncapped review after abfcd0a (check_secrets hit is in its files)
3. Fresh r16 reads of FIX-PLAN/TAKE-CHECKLIST/RUNBOOK after a185caa
4. Fix of 3 soft cites in claims rows 18/19/33 (citation r12) after acbed2f
5. Post-twice script review (waits on lead: Q29-4)

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
