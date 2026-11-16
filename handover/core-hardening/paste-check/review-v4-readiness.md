# C3b v4 readiness review (egm-implementation-readiness, condensed copy), 2026-11-16
Verdict: NOT ready for a fresh runner without guessing. 2 Blocker, 8 Major, 7 Nit. Not checked: patches applied, n8n_kill.py final head (round 5 not on disk), any Windows/WSL behaviour.
## Blockers
B1 Step (d) leftover count has no positive control: empty output from a wrong path / tool error looks like a clean plan. Needs "error = STOP" and a pattern that must match (e.g. `HEAD_PIN =`); no named copy of the plan on the laptop; Grep path form for C:/ not stated.
B2 P-4b / exit-3 rule rests on text not in the plan and an unread script ("n8n-shaped" = cmdline contains n8n is a guess; positive-control stub untried on WSL). Resume after a stop at end of P-3a undefined. Default is safe (stop), but run cannot start until lead supplies text.
## Major
M1 no explicit release signal for the step (c) diff gate (suggest `LEAD-GO RE-PIN` line). M2 second fill run uses checked-out HEAD, not the pinned sha; round 5 still building in that worktree; LEAD-FILL 5 default unsafe. M3 plan never says who runs lead steps (a)/(c) or where (Git Bash on laptop?). M4 R2 has no paste name/log/prefix; KILL not conditional on pid alive. M5 `LEAD-YES R2 pid=` line: starts-with vs UTC/IST prefix ambiguous; GONE-FAIL in S13 needs ask-and-wait. M6 CR-in-strings.txt step (c)(i) has no trigger for the runner. M7 P-2 stops have no resume path; P-1 irreversible may run before gate (d). M8 decisions 6, 7, 8, 12 not reflected (real-take port, n8n_api.py, ONE made-up lead, times in handoff).
## Nits
gone() leaves dead `[ $e -ne 0 ] ||`; acceptance rule over-strict on any "exit" word; fill loop drops last line w/o newline; WORDS omits `<UTC time>`/`<digits>`; LEAD-FILL 9 path guess in two commands; H1/H2 FILE-MISSING over-conservative; count 17 markers on 10 lines confirmed.
Defaults: Q1,1b,2,3,4,7,8 safe; Q5 unsafe (moving head); Q6 safe but over-conservative; Q9 weak.
