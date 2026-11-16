UPDATED_UTC: 2026-11-16T12:12:44Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 10
PERCENT: 87
AGENTS_RUNNING: 8
CAPACITY: 0.17 load of 4 cores, mem 0/15 GB, RAM 951/16087 MB, disk 26G free of 252G, top3 327M /tmp/core-venv 345M /tmp/e7m 2.2G /tmp/claude-0 , agents 8 (light+heavy per list)
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
NEXT: 8 running; two fixers done and checked, fresh reviews started
PUSHED_UTC: 2026-11-16T12:12:44Z

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
| ae1e348 | fixer | sonnet | F8 flow-check Majors (pin, tcfail, flow sha, reviewer line, test flag leak, raw lock) | 12:11 | 12:50 | running | fix-f8-r10d.md |
| a822207 | fixer | sonnet | RW/CT citation Majors 1-5 | 12:11 | 12:35 | running | fix-rwct7.md |
| a7775df | egm-impl-readiness | sonnet | RUNBOOK round 5 fresh read | 12:11 | 12:30 | running | read-only |
| ab8bd88 | fixer | sonnet | TAKE-CHECKLIST/FIX-PLAN M1-M6 | 12:11 | 12:35 | running | fix-tcfp4.md |
| a2719df | egm-comprehension | sonnet | OWNER-STEPS owner part stranger read r9 (Blockers/Majors only) | 12:11 | +15 min | running | read-only |
| a26019f | egm-comprehension | sonnet | QUESTIONS.md stranger read r4 (Blockers/Majors only) | 12:12 | +15 min | running | read-only |
| a79c4f3 | egm-design | sonnet | F-003 patch fresh review r4 (Blockers/Majors) | 12:12 | +15 min | running | read-only |
| a09ca0b | egm-design | sonnet | core patches REVIEW.md round 5 (uncapped path) | 12:12 | +20 min | running | read-only |

## NEXT 5 (not started, no capacity or waits on a running fix)
1 Post-twice script and run_real_check_n8n.py read-only review (waits: lead puts them on a branch, Q29-4)
2 Fresh egm review of F8 final head + evidence runner (waits: ae1e348 fix report)
3 Citation lane on new RW/CT strings after a822207 and on F-003 patch after a8cad4d
4 Stranger read of QUESTIONS.md and owner part after their fixers land (round cap: Blockers/Majors only)
5 Core patches REVIEW.md round 6 egm-design (money/redaction path, uncapped) after a28e9c0

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
