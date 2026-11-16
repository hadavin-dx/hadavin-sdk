UPDATED_UTC: 2026-11-16T11:54:16Z
SESSION: core-hardening
ORDER: 021 + decisions 10:02Z; 024; 027-029, 031, 032, 034 (4 running, reasons below)
STATE: WORKING
BOOT_ID: 3dcae981
ITEMS_TOTAL: 14
ITEMS_OPEN: 9
PERCENT: 95
AGENTS_RUNNING: 4
CAPACITY: load 0.20 of 4 cores, mem 1.0 of 15.7 GB used (15.1 GB available), DISK (df -h . and /tmp, same volume): 8.8 GB free, Used 30G, Size 252G; df Size is not usable space, the allowance is about 39 GB (30 used + 8.8 free), 78% used; free is above the 6 GB cleanup line so freed 0 MB; top 3 disk users I created: /tmp/c8b 2.1G, /tmp/c5v2 1.9G, /tmp/c5v3 1.8G (finished scratch, go first if free falls under 6 GB); /tmp/claude-0 is the session own state, never removed
INTERRUPTED: none
FAILED: (1) Owner sheet v16 FAILED all 5 reviews: security 8 majors (wrong-key cancel rule, no money-stop mechanism, probe key file erased too early, lease sentence circular), adversarial 3 blockers + 8 majors (flow checksum cannot be compared, two cancel rules for older keys, step 0 clean-up reads an erased file), contradiction 7 majors (rows 4-7 vs 4,5,7 in the room, step 0 vs decisions 2 and 8, key deadline not tied to run date), stranger 15 majors; 7 rows of v16-CHANGES marked FIXED are not fixed. v17 builder STOPPED by me on ORDER 034 (nothing reviewed); root-cause readers running. (2) Lead checklist rev 9 failed 3 reviews; rev 10 builder running. (3) run.py r4 security review: 3 majors (uncaught signals, settings above root, no tree re-check) + 12 nits; r5 builder running; S603 needs lead decision. (4) Plan chain verified (28f92c5d, 780 lines); checklist still names old sha and marker lines 777/778 until rev 10 lands. (5) Lease wording A/B, take port, Q18 approval of run.py r3/r4 undecided. (6) Nothing run with n8n, Postgres, PowerShell, WSL, Git Bash. (7) REPORT.md rows for C3b and C8 and board rows C13/C14 still stale (I will fix after builders land).
NEXT: ORDER 034: v17 owner sheet NOT started until the two root-cause readers (cold read + zoom-out, findings only) report; then fix that class once, then five reviews. Rev 10 and r5 builders running.
PUSHED_UTC: 2026-11-16T11:54:16Z

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

## AGENTS (4 running, counted from the real agent list at 2026-11-16T11:54:16Z; 4 short of 8)
| id | role / lane | model | what it does | started UTC | expected end UTC | state |
|---|---|---|---|---|---|---|
| ad38a5720a8797d65 | builder lead checklist rev 10 | sonnet | fixes all findings of 4 reviews | 11:38Z | 12:40Z | running |
| a0112918e044959da | builder run.py r5 (security, uncapped) | sonnet | 3 majors + nits of r4 security review | 11:41Z | 13:00Z | running |
| a00128c7b1402808e | reader root cause (egm-comprehension) | sonnet | reads only v14-v16 review findings, names the common cause | 11:53Z | 12:15Z | running |
| a9a6b6f936d76b5ea | reader shape (egm-zoom-out) | sonnet | what to cut or move to the lead, smallest sheet | 11:53Z | 12:15Z | running |
Stopped: owner sheet v17 builder (a53557b39686d6457) on ORDER 034; its unfinished files are in steps-edits/ and not reviewed.
ORDER 029/034 reasons for 4 not 8: v17 builder waits for the two root-cause reports; the v17 reviewers and citation check have nothing to review; rev 10 reviewers, citation checker, evidence runner wait for the rev 10 hand-back; r5 security reviewer and evidence runner wait for the r5 hand-back; C5, C7, C8 new work stopped by Q18; C3b and C6 wait on lead answers. Waiting on the lead: lease wording A/B, exit-code rule, OI-1 to OI-38, take port, CHAIN choice, S603, Q18 approval of run.py r3/r4/r5, step 0 vs decision 8, owner role beyond decision 7.
