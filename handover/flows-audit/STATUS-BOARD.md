UPDATED_UTC: 2026-11-16T15:09:56Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 2.04 load of 4 cores, mem 1/15 GB, RAM 1761/16087 MB, disk 17G free of 252G, top3 422M /tmp/tmp.SjFcfMab07 552M /tmp/pytest-of-root 11G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running abfcd0a); check_secrets FAIL 1 hit flow-check/raw/test-take-check.txt:178; run_all.sh rc 1 (reviews/evidence-run-all-2.md)
Percent basis (ORDER 041): 70 percent = 7 of 10 items verified by an independent check; none closed since 13:59Z; fixers reported but unverified.
NEXT: see next5
PUSHED_UTC: 2026-11-16T15:09:56Z

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
| aa1b7a5d | fixer | sonnet | RUNBOOK/FIX-PLAN/TAKE-CHECKLIST round 19 (15 Majors) | 14:50Z | 15:30Z | running | edits pending, log fix-tcfp14.md |
| a94cd3cf | fixer (uncapped) | sonnet | patch-copies round 3 (4 Blockers B1-B4, 6 Majors) | 14:58Z | 15:30Z | running | log fix-patchcopies3.md pending |
| aefca634 | fixer | sonnet | Q31 round 6 (1 Blocker, 13 Majors) | 15:00Z | 15:25Z | running | log fix-q31-7.md pending |
| a473c63c | fixer | sonnet | FINDINGS/LEDGER-ROWS round 2 (1 Blocker: F-011 cell differs) | 15:02Z | 15:25Z | running | log fix-findings-ledger3.md pending |
| a0d317b5 | fixer | sonnet | CLAIMS-TABLE r7 + RW r8 + citation findings in one batch | 15:09Z | 15:35Z | running | log fix-rwct15.md pending |
| a75883d7 | fixer (uncapped) | sonnet | REVIEW.md round 23 (2 design Majors, 10 reader Majors) | 15:10Z | 15:40Z | running | log fix-review16.md pending |
| a419eeb7 | evidence runner | sonnet | F8 run_all x3, strict, test_take_check, ruff, secrets alone | 15:10Z | 15:40Z | running | evidence-f8-r9-runner.md pending |
| a5351c64 | reviewer egm-codebase-details | sonnet | F8 round 10 fresh uncapped review | 15:10Z | 15:25Z | running | none yet |

## NEXT 5 (not started, no capacity or waits on a running fix)
Verify each fixer output with own commands, then fresh reader per file (Q31 round 7, plan files, patch-copies round 4 uncapped)
Fresh CLAIMS-TABLE/RW round after a0d317b (Blockers/Majors only)
REVIEW.md round 24 uncapped after fixer
F8 fixer round 10 if the review or evidence finds faults
drift-007 refresh and trigger-word grep before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
