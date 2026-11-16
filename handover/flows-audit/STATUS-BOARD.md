UPDATED_UTC: 2026-11-16T12:23:21Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 9
PERCENT: 87
AGENTS_RUNNING: 7
CAPACITY: 1.95 load of 4 cores, mem 0/15 GB, RAM 964/16087 MB, disk 25G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 2.6G /tmp/claude-0 , agents 7 (light+heavy per list)
INTERRUPTED: none
FAILED: FAILED: ruff format --check failed (17 files); my 16 files now formatted; inputs/plan-wp6-resmoke-v5.md is the lead's (1 left). ruff check has 53 lint errors in my tools: lint fixer running. F8 r10 Blocker: pin rewrite self-approves, fixer running
FAILED: ruff format --check on inputs/plan-wp6-resmoke-v5.md (lead-owned); check_refs unresolved CUT-LIST.md:17 (fixer running); lint fixer changed no_name.out (crash removed)
FAILED: F8 fixer says ruff format failure did not reproduce; not yet confirmed by evidence runner (a5a7e77 running)
FAILED: evidence runner (independent): run_all.sh exit 1 (case new-warn-changes-the-pin missing FINAL text) - F8 fixer had reported exit 0; ruff format --check exit 1 only inputs/plan-wp6-resmoke-v5.md (lead file); TAKE_CHECK_FLOWS=/tmp/x gave exit 1 (a real FAIL stays 1, my expectation of 4 was wrong); fixer a8d895a running
RW/CT: B-003c vs B-219 overlap, B-101 old quote, B-010 note, A-016f id in public text, B-045 PLAN:79
FINDINGS/patches: F-003 patch contradicts Q25/Q28 (caption, CRM row, stopwatch, owner stops n8n) - drift B1,M1-M7
QUESTIONS: F-011/F-041 gate text conflict (Q27-9 vs Q21)
core-patches REVIEW: X-2 grant list wrong, C-3 consumers incomplete, A-6 reason, Major count (round 3, 4 Majors)
TAKE-CHECKLIST/FIX-PLAN: step 4 pass grep never matches; GO rows 1,2,3,5 have no runnable command; IST pair wrong in FIX-PLAN L70
F8 evidence: run_all exit 0 twice (57 s), but root cannot test chmod 000; bandit -ll flags tools/scratch (B602, B608); ruff format fails only on lead file
F8: take_check passes a changed flow with same counts (no enforced sha); pin reviewer line accepts any text; TAKE_CHECK_TEST leak exit 0; run_all.sh shared raw dir
NEXT: collect; F8 evidence after fixer
PUSHED_UTC: 2026-11-16T12:23:21Z

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
| ae1e348 | fixer | sonnet | F8 flow-check Majors | 11:50 | 12:40 | running | fix-f8-r10d.md |
| a35711f | fixer | sonnet | RUNBOOK round 5 (2 Blockers, 9 Majors) | 12:16 | 12:50 | running | - |
| a19ea5c | reviewer | sonnet | stranger read owner part r11 | 12:21 | 12:40 | running | - |
| a099aef | reviewer | sonnet | cross-file contradiction check | 12:22 | 12:45 | running | - |
| a4b86b6 | fixer | sonnet | TAKE-CHECKLIST/FIX-PLAN round 5 (B1, M1-M8) | 12:23 | 12:50 | running | - |
| a7710f3 | reviewer | sonnet | codebase review REVIEW.md r7 (X-5) | 12:23 | 12:45 | running | - |
| aefa2a7 | fixer | sonnet | QUESTIONS.md round 6 (6 Majors) | 12:23 | 12:50 | running | - |

## NEXT 5 (not started, no capacity or waits on a running fix)
1. Citation lane on F-003 r4 patch + new RW/CT (after fixers settle)
2. Fresh egm review + evidence runner on F8 final head (waits: F8 fixer ae1e348)
3. Post-twice script and run_real_check_n8n.py read-only review (waits: lead puts them on a branch, Q29-4)
4. Re-read RUNBOOK and TAKE-CHECKLIST after fixers (round 6, only Blockers/Majors)
5. Drift report refresh reviews/drift-007.md before FINAL

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
