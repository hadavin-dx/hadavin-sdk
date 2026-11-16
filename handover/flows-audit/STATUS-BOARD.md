UPDATED_UTC: 2026-11-16T16:35:29Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 30
PERCENT: 70
AGENTS_RUNNING: 8
CAPACITY: 3.49 load of 4 cores, mem 1/15 GB, RAM 1201/16087 MB, disk 13G free of 252G, top3 459M /tmp/tmp.ddW834IdiF 522M /tmp/tmp.4gOIkjhGSB 12G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: none (F8 run_all.sh intermittent exit 1 is an evidence finding: 3 of 6 plain runs failed, cause unknown, fixer acf8ab59 on it; ruff format --check passes 741 files)
NEXT: Collect 8 reports, verify, launch fresh readers; disk 13G free (67%); percent stays 70 (no item closed by an independent check since 13:59Z)
PUSHED_UTC: 2026-11-16T16:35:29Z

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
| acf8ab59 | fixer | sonnet | F8 flow-check round 11 (uncapped) | 15:48Z | 16:50Z | running | edits in flow-check/ |
| a213005e | reader | sonnet | plan files (RUNBOOK/FIX-PLAN/TAKE-CHECKLIST) r25 stranger read | 16:31Z | 16:41Z | running | findings inline |
| af7e2278 | fixer | sonnet | FINDINGS/LEDGER round 11 (13 Majors) | 16:31Z | 16:45Z | running | edits in FINDINGS.md, LEDGER-ROWS.md |
| ac464f5c | code reviewer | sonnet | patch-copies README/DEAD-MAN-CHECK r10 (uncapped) | 16:33Z | 16:45Z | running | findings inline |
| a19c5921 | citation | sonnet | patch-copies r10 cite check (git apply, counts) | 16:33Z | 16:45Z | running | reviews/citation-patchcopies-r10.md |
| a4a9cce2 | reader | sonnet | Q31 round 16 stranger read | 16:34Z | 16:44Z | running | findings inline |
| a695e7c1 | fixer | sonnet | RW/CT round 19 (17 Majors) | 16:34Z | 16:50Z | running | edits in RUNSHEET-WORDING.md, CLAIMS-TABLE.md |
| aeb002de | reader | sonnet | REVIEW.md r32 full read (uncapped) | 16:35Z | 16:45Z | running | findings inline |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. REVIEW.md round 32 design reviewer (egm-design, uncapped): waits for a free slot (8 running).
2. Patch-copies round 10 fixer (all three reports: reader, code, citation): waits for ac464f5c and a19c5921.
3. Fresh FINDINGS/LEDGER round 11 reader: waits for af7e2278.
4. Fresh RW/CT round 19 reader: waits for a695e7c1.
5. F8 evidence runner (alone) plus fresh uncapped reviews: waits for acf8ab59.
Disk free 13G (67%); percent basis: 70 = 7 of 10 items verified by an independent check; none closed since 13:59Z.

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Audit is NOT final: agents are running and fixes are unverified; see QUESTIONS.md Q31 item 66 for what the lead answers first.
