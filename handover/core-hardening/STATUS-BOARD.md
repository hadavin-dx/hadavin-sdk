UPDATED_UTC: 2026-11-16T12:04:51Z
SESSION: core-hardening
ORDER: 021 + decisions 10:02Z; 024; 027-029, 031, 032, 034, 035 (8 running)
STATE: WORKING
BOOT_ID: 3dcae981
ITEMS_TOTAL: 14
ITEMS_OPEN: 9
PERCENT: 95
AGENTS_RUNNING: 8
CAPACITY: load 0.75 of 4 cores, mem 1.2 of 15.7 GB used (14.9 GB available), DISK (df -h . and /tmp, same volume): 8.7 GB free, Used 30G, Size 252G; df Size is not usable space, allowance about 39 GB, 78% used; free above the 6 GB cleanup line so freed 0 MB; top 3 disk users I created: /tmp/c8b 2.1G, /tmp/c5v2 1.9G, /tmp/c5v3 1.8G (finished scratch, go first if free falls under 6 GB); /tmp/claude-0 is the session own state, never removed
INTERRUPTED: none
FAILED: (1) Owner sheet v16 FAILED all 5 reviews (security 8 majors incl. wrong-key cancel rule and no money-stop mechanism; adversarial 3 blockers; contradiction 7 majors; stranger 15 majors); two root-cause readers: wrong shape. v17 short sheet (71 lines) + lead release note built; its checker only tests form (0 problems), NOT reviewed yet, 5 reviews running (security uncapped); v17 weakened two controls on purpose (owner account check cut; flow/file checksum compare moved to lead) and 19 open items need the lead. (2) Lead checklist rev 10: adversarial review 9 majors (release does not prove the plan matches the chosen CHAIN; permission check reads text not the process; mv can overwrite earlier .old; refused path characters not refused; control file circular; D2 misses live parts; question 2 flag self-set; executed files not fingerprinted), stranger 1 blocker + 8 majors, evidence runner 3 citation mismatches; evidence: 42 of 42 blocks pass bash -n and dash -n, chain walk 28f92c5d/780 lines reproduced on Linux only; nothing run on Windows, WSL, Git Bash, PowerShell; rev 11 fix builder running. (3) run.py r4 security review 3 majors + 12 nits; r5 builder running; S603 needs lead decision. (4) NEW audits saved, core fixes not mine (src/ out of scope): spend guard 3 blockers + 5 majors (audit + second reader); redaction 1 blocker (extract() sends the raw document to the model) + majors; approval-text command filter 2 blockers + 11 majors (its fail-closed promise is false for programs off its list; a command wrapped with backslash-newline passes); all from reading, nothing run. (5) Lease wording A/B, take port, Q18 approval of run.py r3/r4/r5 undecided. (6) Nothing run with n8n, Postgres, PowerShell, WSL, Git Bash. (7) REPORT.md rows for C3b and C8 and board rows C13/C14 still stale (fix after builders land). (8) Evidence runner left dangling symlinks /c and /mnt/c (blocked from removal; needs `rm /c /mnt/c` by the user); plan text holds the owner's user names in paths (lead's file).
NEXT: 8 running; on hand-back: save condensed copy, banned scan, commit; checklist rev 11 then 2 reviewers max; v17 reviews then ONE fix pass (security uncapped); lead hand-off of the three core audits.
PUSHED_UTC: 2026-11-16T12:04:51Z
## ITEMS (QUEUE.md ids; detail in REPORT.md)
| # | item | state | % | evidence file | note |
|---|---|---|---|---|---|
| C1 | cross-review flows-audit | done | 100 | reviews-of-flows-audit/REVIEW.md | |
| C2 | hygiene patches | done | 100 | hygiene-patches/ | static |
| C3 | paste check of re-smoke plan | done | 100 | paste-check/REPORT.md | nothing run with pwsh or n8n |
| C3b | re-pin patch (ORDER 017) | v8 round 6: 0 blockers, 1 major (fence) fixed in place; PROGRESS.md-exists question open for lead | 95 | paste-check/handback-c3b-v7.md, review-c3b-v6-readiness-r4.md | |
| C4 | steps vs decisions edits | done | 100 | steps-edits/EDITS.md | |
| C4b | OWNER-STEPS | v16 failed 5 reviews (see FAILED 1); v17 short sheet built (form check 0 problems), 5 reviews running | 90 | steps-edits/review-v14-stranger.md, review-v14-security.md, citation-check-v14.md, cross-read/adversarial-v14.md, contradiction-v14.md | money/secret path, uncapped |
| C5 | core patches | v5 done, no blocker or major | 100 | patches-ready/review/design-r5-c5v5.md | scope cut by decision 4; no new work (Q18) |
| C6 | video audit | C6f round 2 done | 97 | c6-skip-audit/REPORT-c6f.md | questions Q1/Q2 wait for lead |
| C7 | heavy lane: tests per patch | C7b fix 4 round 5: 0 blockers, 0 majors | 97 | patches-ready/review/design-c7b-fix4-r5.md | flake = describe-only (Q16) |
| C8 | mutation lane C-01 A-01 | run.py r3 reviewed: 2 majors (-p no:NAME, hard links) + minors; r4 fix builder running | 90 | mutation-lane/REPORT-runpy3.md | tool only, not in take path |
| C9 | apply S9 decisions into owner steps | in v14 | 86 | steps-edits/ | |
| C10 | who-types-what table | in v14 | 86 | steps-edits/ | |
| C11 | HubSpot probe step | in v14 (separate secrets procedure) | 86 | steps-edits/ | |
| edit list v10 | real-v5 edits | round 6 clean; primary-source git show check done: all claims confirmed, no table file in real-v5 | 99 | paste-check/review-v10-r6.md | decision 6 is the lead's |

## AGENTS (8 running, counted from the real agent list at 2026-11-16T12:04:51Z)
| agent id | purpose | started UTC | expected end UTC | state | produced so far |
|---|---|---|---|---|---|
| a0112918e044959da | builder run.py r5 (security path, uncapped) | 11:41Z | 13:00Z | running | partial edit to mutation-lane/safety-tests.sh; no hand-back |
| a9efce51c6e087d1a | builder checklist rev 11 (all rev 10 findings, one batch) | 12:04Z | 13:04Z | running | nothing yet; waits on none |
| a61f790b84711bf34 | security/money review of v17 sheet + release note (uncapped) | 12:04Z | 12:30Z | running | nothing yet |
| a573be13e4740e6c5 | stranger read of v17 sheet | 12:04Z | 12:25Z | running | nothing yet |
| a9731eec8a5c1b30e | adversarial readiness review of the lead release note | 12:04Z | 12:30Z | running | nothing yet |
| aebffb3eda66e0780 | contradiction review of v17 files vs binding inputs | 12:04Z | 12:30Z | running | nothing yet |
| abcacc72a250e3ef4 | EVIDENCE RUNNER + citation check, v17 files (evidence-v17.md) | 12:04Z | 12:30Z | running | nothing yet |
| ab94845c9a30941b1 | static audit of secrets kind and audit-trail code (read only) | 12:05Z | 12:35Z | running | nothing yet |
Finished and saved since last board (12:04Z): v17 short sheet builder, checklist rev 10 adversarial review and evidence runner, gate-filter audit, redaction audit, spend-guard verification (all in audit-r460/ or paste-check/ or steps-edits/). No agent is missing: 8 of 8.
NEXT 5 independent tasks if capacity frees: (1) fix pass on v17 after the five reviews (security path, uncapped); (2) run.py r5 security reviewer + evidence runner when the builder reports [lead answer needed for S603 suppression]; (3) C7 patch-test re-run on a second scratch copy, blocked by Q18 stop [answer: lift?]; (4) C6 run-sheet fixes M1-M3, needs your Q1/Q2 answers; (5) REPORT.md and board stale-row fixes (C3b, C8, C13/C14) after hand-backs.
