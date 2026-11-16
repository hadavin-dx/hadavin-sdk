UPDATED_UTC: 2026-11-16T12:20:37Z
SESSION: core-hardening
ORDER: 021 + decisions 10:02Z; 024; 027-029, 031, 032, 034, 035, 036 (9 running)
STATE: WORKING
BOOT_ID: 3dcae981
ITEMS_TOTAL: 14
ITEMS_OPEN: 9
PERCENT: 95
AGENTS_RUNNING: 9
CAPACITY: load 0.54 of 4 cores, mem about 1.1 of 15.7 GB used (14.2 GB available), DISK: 8.8 GB free, Used 30G, Size 252G (df Size is not usable space; allowance about 39 GB, 78% used); top 3 disk users I created: /tmp/c8b 2.1G, /tmp/c5v2 1.9G, /tmp/c5v3 1.8G; MB freed this beat: 0 (free is above 6 GB, nothing cleaned)
INTERRUPTED: none
FAILED: (1) Owner sheet v16 FAILED all 5 reviews (security 8 majors incl. wrong-key cancel rule and no money-stop mechanism; adversarial 3 blockers; contradiction 7 majors; stranger 15 majors); two root-cause readers: wrong shape. v17 short sheet (71 lines) + lead release note built; its checker only tests form (0 problems), NOT reviewed yet, 5 reviews running (security uncapped); v17 weakened two controls on purpose (owner account check cut; flow/file checksum compare moved to lead) and 19 open items need the lead. (2) Lead checklist rev 10: adversarial review 9 majors (release does not prove the plan matches the chosen CHAIN; permission check reads text not the process; mv can overwrite earlier .old; refused path characters not refused; control file circular; D2 misses live parts; question 2 flag self-set; executed files not fingerprinted), stranger 1 blocker + 8 majors, evidence runner 3 citation mismatches; evidence: 42 of 42 blocks pass bash -n and dash -n, chain walk 28f92c5d/780 lines reproduced on Linux only; nothing run on Windows, WSL, Git Bash, PowerShell; rev 11 fix builder running. (3) run.py r4 security review 3 majors + 12 nits; r5 builder running; S603 needs lead decision. (4) NEW audits saved, core fixes not mine (src/ out of scope): spend guard 3 blockers + 5 majors (audit + second reader); redaction 1 blocker (extract() sends the raw document to the model) + majors; approval-text command filter 2 blockers + 11 majors (its fail-closed promise is false for programs off its list; a command wrapped with backslash-newline passes); all from reading, nothing run. (5) Lease wording A/B, take port, Q18 approval of run.py r3/r4/r5 undecided. (6) Nothing run with n8n, Postgres, PowerShell, WSL, Git Bash. (7) REPORT.md rows for C3b and C8 and board rows C13/C14 still stale (fix after builders land). (8) Evidence runner left dangling symlinks /c and /mnt/c (blocked from removal; needs `rm /c /mnt/c` by the user); plan text holds the owner's user names in paths (lead's file).
NEXT: on hand-back: save condensed copy, banned scan, commit; v18 owner sheet then 5 fresh reviews (security uncapped); checklist rev 11 then 2 reviewers max; run.py r5 then security reviewer + evidence runner; C4 round 2 then resolve; lead hand-off of the core audits (spend guard, redaction, G4 filter, secrets/audit trail) in REPORT.md
PUSHED_UTC: 2026-11-16T12:20:37Z
## ITEMS (QUEUE.md ids; detail in REPORT.md)
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| C1 | cross-review flows-audit | done | 100 | reviews-of-flows-audit/REVIEW.md | |
| C2 | hygiene patches | done | 100 | hygiene-patches/ | static |
| C3 | paste check of re-smoke plan | done | 100 | paste-check/REPORT.md | nothing run with pwsh or n8n |
| C3b | checklist rev 11 built (45 blocks pass bash -n/dash -n in builder run); round-2 evidence runner + 2 reviewers running | v8 round 6: 0 blockers, 1 major (fence) fixed in place; PROGRESS.md-exists question open for lead | 95 | paste-check/handback-c3b-v7.md, review-c3b-v6-readiness-r4.md | |
| C4 | EDITS.md round 3 confirmed: 0 blockers, 2 majors fixed by lead session; contact rows need a take code change (CODE-CHANGE-NEEDED) | 95 | 100 | steps-edits/EDITS.md | |
| C4b | v18 owner package built (form check 0 problems; v17 failed 5 reviews); security, stranger, evidence reviews running | 92 | 90 | steps-edits/review-v14-stranger.md, review-v14-security.md, citation-check-v14.md, cross-read/adversarial-v14.md, contradiction-v14.md | money/secret path, uncapped |
| C5 | core patches | v5 done, no blocker or major | 100 | patches-ready/review/design-r5-c5v5.md | scope cut by decision 4; no new work (Q18) |
| C6 | citation check: 229 of 240 match, 11 mismatches; corrections builder running | C6f round 2 done | 97 | c6-skip-audit/REPORT-c6f.md | questions Q1/Q2 wait for lead |
| C7 | heavy lane: tests per patch | C7b fix 4 round 5: 0 blockers, 0 majors | 97 | patches-ready/review/design-c7b-fix4-r5.md | flake = describe-only (Q16) |
| C8 | mutation lane C-01 A-01 | run.py r3 reviewed: 2 majors (-p no:NAME, hard links) + minors; r4 fix builder running | 90 | mutation-lane/REPORT-runpy3.md | tool only, not in take path |
| C9 | apply S9 decisions into owner steps | in v14 | 86 | steps-edits/ | |
| C10 | who-types-what table | in v14 | 86 | steps-edits/ | |
| C11 | HubSpot probe step | in v14 (separate secrets procedure) | 86 | steps-edits/ | |
| edit list v10 | real-v5 edits | round 6 clean; primary-source git show check done: all claims confirmed, no table file in real-v5 | 99 | paste-check/review-v10-r6.md | decision 6 is the lead's |

## AGENTS (9 running, counted from the real agent list at 2026-11-16T12:20:37Z)
| agent id | purpose | started UTC | expected end UTC | state | produced so far |
|---|---|---|---|---|---|
| a0112918e044959da | builder run.py r5 (security path, uncapped) | 11:41Z | 13:00Z | running | partial edit to mutation-lane/safety-tests.sh; no hand-back |
| a5d1d982574764fad | builder: core PR hand-off v2 (both reviews, ordered PR split) | 12:17Z | 13:00Z | running | nothing yet |
| ae8ea811db4d13166 | EVIDENCE RUNNER: checklist rev 11 independent run | 12:19Z | 13:00Z | running | nothing yet |
| ac7bd39c028f44326 | readiness review, checklist rev 11 (round 2) | 12:19Z | 12:45Z | running | nothing yet |
| a1d160e9889cf049c | adversarial review, checklist rev 11 (round 2) | 12:19Z | 12:45Z | running | nothing yet |
| a0af9e578b584d6c4 | builder: C6 report corrections X1-X11 + design Majors | 12:19Z | 13:00Z | running | nothing yet |
| a2594e16f31318dbb | security/money review of v18 (uncapped) | 12:20Z | 12:50Z | running | nothing yet |
| a5648fa6cba9ef012 | stranger read of v18 sheet | 12:20Z | 12:40Z | running | nothing yet |
| a2d54113b4ad27eec | EVIDENCE RUNNER + citation check v18 | 12:20Z | 12:50Z | running | nothing yet |

Missing from 8: none (9 running). Waiting, not agents: v18 contradiction and readiness reviews wait for slots (row C4b); run.py r5 security review waits on the r5 builder (row C8; S603 needs a lead answer); hand-off v2 reviews wait on its builder.

Finished since last board: v18 builder; C4 round-3 builder and confirm; rev 11 builder; core-audit hand-off + readiness + zoom-out reviews (2 Blockers, 11 Majors; v2 building); blocker verifier; C6 citation checker.
NEXT 5 independent tasks if capacity frees: (1) v18 contradiction + readiness reviews; (2) run.py r5 security review + evidence runner; (3) hand-off v2 two reviews; (4) fix stale REPORT.md top block and rows; (5) v18 fix pass after reviews (security path, uncapped).
