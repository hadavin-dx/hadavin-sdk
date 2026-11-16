UPDATED_UTC: 2026-11-16T13:07:17Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 14
PERCENT: 77
AGENTS_RUNNING: 8
CAPACITY: 0.97 load of 4 cores, mem 0/15 GB, RAM 968/16087 MB, disk 24G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 3.5G /tmp/claude-0 , agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: - F8 reviewer_ok accepted Pat O.L.L.M. (fix running a2b5712); shellcheck not installed
NEXT: collect 8; fresh review TAKE-CHECKLIST/FIX-PLAN r9; F8 egm review after evidence; drift-007 refresh; REPORT ORDER 037 file list
PUSHED_UTC: 2026-11-16T13:07:17Z

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
| a8aee16 | evidence | sonnet | citation checker QUESTIONS/RUNBOOK -> reviews/citation-r8.md | 13:00Z | 13:20Z | running | pending |
| a09f239 | fixer | sonnet | FINDINGS r10 fixes (B1 guards, T21 text, M1-M7, N1-N5) | 13:04Z | 13:30Z | running | pending |
| a3e0018 | fixer | sonnet | OWNER-STEPS owner part r18 fixes (M1-M9, N1-N10) | 13:05Z | 13:25Z | running | pending |
| af16b9b | reviewer | sonnet | REVIEW.md r13 design review (approval guard bypasses) | 13:05Z | 13:20Z | running | pending |
| a2612a6 | reviewer | sonnet | REVIEW.md r13 codebase review (cites, counts) | 13:05Z | 13:20Z | running | pending |
| a57157e | evidence | sonnet | EVIDENCE RUNNER F8 r6 (independent) -> evidence-f8-r6-independent.md | 13:06Z | 13:25Z | running | pending |
| a25e6f0 | reviewer | sonnet | RUNBOOK r9 fresh review | 13:06Z | 13:20Z | running | pending |
| a786176 | fixer | sonnet | QUESTIONS r11 fixes + Q31 items 29-31 | 13:06Z | 13:30Z | running | pending |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Fresh stranger read of QUESTIONS after round 7 (Blockers/Majors only) once the owner-part fixer is done
2. Citation lane on RUNBOOK/TAKE-CHECKLIST numbers and cites after r6 reads
3. Post-twice script and run_real_check_n8n.py read-only review (waits: lead puts them on a branch, Q29-4)
4. Evidence runner + review of F8 round 4 after fixer
5. Drift report refresh reviews/drift-007.md before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
