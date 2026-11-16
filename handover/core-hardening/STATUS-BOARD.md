UPDATED_UTC: 2026-11-16T11:59:11Z
SESSION: core-hardening
ORDER: 021 + decisions 10:02Z; 024; 027-029, 031, 032, 034, 035 (8 running)
STATE: WORKING
BOOT_ID: 3dcae981
ITEMS_TOTAL: 14
ITEMS_OPEN: 9
PERCENT: 95
AGENTS_RUNNING: 8
CAPACITY: load 1.59 of 4 cores, mem 1.1 of 15.7 GB used (15.0 GB available), DISK (df -h . and /tmp, same volume): 8.8 GB free, Used 30G, Size 252G; df Size is not usable space, the allowance is about 39 GB (30 used + 8.8 free), 78% used; free above the 6 GB cleanup line so freed 0 MB; top 3 disk users I created: /tmp/c8b 2.1G, /tmp/c5v2 1.9G, /tmp/c5v3 1.8G (finished scratch, go first if free falls under 6 GB); /tmp/claude-0 is the session own state, never removed
INTERRUPTED: none
FAILED: (1) Owner sheet v16 FAILED all 5 reviews: security 8 majors (wrong-key cancel rule, no money-stop mechanism, probe key file erased too early, lease sentence circular), adversarial 3 blockers + 8 majors (flow checksum cannot be compared, two cancel rules for older keys, step 0 clean-up reads an erased file), contradiction 7 majors (rows 4-7 vs 4,5,7 in the room, step 0 vs decisions 2 and 8, key deadline not tied to run date), stranger 15 majors; 7 rows of v16-CHANGES marked FIXED are not fixed. two root-cause readers agreed the sheet shape is wrong (owner doing lead work, rules stated in 4-6 places); new short v17 builder running (nothing reviewed yet). (2) Lead checklist rev 9 failed 3 reviews; rev 10 built (builder ran only on Linux, nothing on Windows, WSL, Git Bash, PowerShell; apply script defects F3 damaged RENUMBER line not refused and F4 dangling symlink written through are lead-owned; 3 reviews running). (3) run.py r4 security review: 3 majors (uncaught signals, settings above root, no tree re-check) + 12 nits; r5 builder running; S603 needs lead decision. (4) Plan chain verified (28f92c5d, 780 lines); checklist still names old sha and marker lines 777/778 until rev 10 lands. (5) Lease wording A/B, take port, Q18 approval of run.py r3/r4 undecided. (6) Nothing run with n8n, Postgres, PowerShell, WSL, Git Bash. (7) NEW: static audit of spend/cap code in src found 3 blockers (no window-end check, per-run cap checked after the spend, daily/monthly check and charge not atomic) and 5 majors incl. Decimal money accepting NaN/negative; I re-read the lines for 3 of them; independent verification running; core fix is not mine (src/ out of scope). (8) REPORT.md rows for C3b and C8 and board rows C13/C14 still stale (I will fix after builders land).
NEXT: 8 running; on hand-back: save condensed copy, banned scan, commit, fix pass. v17 short owner sheet then five reviews; spend-guard audit verification then lead hand-off (core fix is the lead session job, src/ is out of scope).
PUSHED_UTC: 2026-11-16T11:59:11Z

## ITEMS (QUEUE.md ids; detail in REPORT.md)
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| C1 | cross-review flows-audit | done | 100 | reviews-of-flows-audit/REVIEW.md | |
| C2 | hygiene patches | done | 100 | hygiene-patches/ | static |
| C3 | paste check of re-smoke plan | done | 100 | paste-check/REPORT.md | nothing run with pwsh or n8n |
| C3b | re-pin patch (ORDER 017) | v8 round 6: 0 blockers, 1 major (fence) fixed in place; PROGRESS.md-exists question open for lead | 95 | paste-check/handback-c3b-v7.md, review-c3b-v6-readiness-r4.md | |
| C4 | steps vs decisions edits | done | 100 | steps-edits/EDITS.md | |
| C4b | OWNER-STEPS | v16 failed 5 reviews (see FAILED 1); v17 builder running | 90 | steps-edits/review-v14-stranger.md, review-v14-security.md, citation-check-v14.md, cross-read/adversarial-v14.md, contradiction-v14.md | money/secret path, uncapped |
| C5 | core patches | v5 done, no blocker or major | 100 | patches-ready/review/design-r5-c5v5.md | scope cut by decision 4; no new work (Q18) |
| C6 | video audit | C6f round 2 done | 97 | c6-skip-audit/REPORT-c6f.md | questions Q1/Q2 wait for lead |
| C7 | heavy lane: tests per patch | C7b fix 4 round 5: 0 blockers, 0 majors | 97 | patches-ready/review/design-c7b-fix4-r5.md | flake = describe-only (Q16) |
| C8 | mutation lane C-01 A-01 | run.py r3 reviewed: 2 majors (-p no:NAME, hard links) + minors; r4 fix builder running | 90 | mutation-lane/REPORT-runpy3.md | tool only, not in take path |
| C9 | apply S9 decisions into owner steps | in v14 | 86 | steps-edits/ | |
| C10 | who-types-what table | in v14 | 86 | steps-edits/ | |
| C11 | HubSpot probe step | in v14 (separate secrets procedure) | 86 | steps-edits/ | |
| edit list v10 | real-v5 edits | round 6 clean; primary-source git show check done: all claims confirmed, no table file in real-v5 | 99 | paste-check/review-v10-r6.md | decision 6 is the lead's |

## AGENTS (8 running, counted from the real agent list at 2026-11-16T11:59:11Z)
| agent id | purpose | started UTC | expected end UTC | state | produced so far |
|---|---|---|---|---|---|
| a0112918e044959da | builder run.py r5 (security path, uncapped) | 11:41Z | 13:00Z | running | partial edit to mutation-lane/safety-tests.sh; no hand-back |
| a0ab6ad6e35d49839 | builder owner sheet v17 SHORT + lead release note + map + checker | 11:55Z | 12:55Z | running | OWNER-SHEET-v17.md and checkpoint-v17.md exist (in progress, not reviewed) |
| a1435dd023a896622 | cold read of lead checklist rev 10 | 11:56Z | 12:20Z | running | nothing yet |
| afa215e7512fb10a8 | adversarial read of lead checklist rev 10 | 11:56Z | 12:20Z | running | nothing yet |
| aa005ba2f4b31785c | EVIDENCE RUNNER + citation check, checklist rev 10 | 11:56Z | 12:30Z | running | nothing yet (will write paste-check/evidence-chain-c10.md) |
| aee8ac3e47fc89f6e | static audit of the approval gate write shapes (read only) | 11:58Z | 12:25Z | running | nothing yet |
| aeb83fa16af9c7393 | static audit of redaction and masking (read only) | 11:58Z | 12:25Z | running | nothing yet |
| aab21600ed9108770 | independent verification of the spend-guard audit | 11:59Z | 12:25Z | running | nothing yet |
Finished and saved since last board: spend-guard audit (audit-r460/spend-guard-audit.md; 3 blockers, 5 majors; unverified by a second reader yet), lead checklist rev 10 builder, root-cause readers 1 and 2.
NEXT 5 independent tasks if capacity frees: (1) security reviewer on v17 sheet and lead release note when the builder reports; (2) C7 patch-test re-run on a second scratch copy, blocked by your Q18 stop [answer: lift?]; (3) mutation re-run on run.py r5, needs Q18 approval of r3/r4/r5 [answer: approve?]; (4) C6 run-sheet fixes M1-M3, needs your Q1/Q2 answers; (5) audit of the secrets kind and the audit-trail code (read only), starts when one of the 8 frees.
