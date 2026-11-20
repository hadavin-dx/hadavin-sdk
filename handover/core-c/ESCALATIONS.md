# ESCALATIONS of core-c (newest on top)

## E1. One-minute board cron could not be created (2026-11-20T05:20Z)
- Item: ORDER 003 item 1, session cron `* * * * *` for the board.
- Tries: 2 (05:20 UTC and 05:22 UTC, CronCreate tool). Stopped at 2, not retried a third time.
- Exact error both times: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Destructive or Unwanted Actions]."
- Cause as I understand it: the session's own permission layer refuses a recurring every-minute job. This is a control of the cloud session, not a fault in the repo.
- What I did instead (the fallback the order itself gives for "no cron tool"): a board script renders, commits, pulls --rebase and pushes the board at the end of every tool batch.
- Gap this leaves: when I am only waiting for background agents and run no tool, no board is pushed. Boards can then be older than 1 minute.
- Not tried on purpose: a background shell loop that pushes every minute. That would go around the denial (ORDER 003 item 4: do not work around a denial).
- Needed from the owner: allow the cron in this cloud session's permission prompt/settings, or accept boards per tool batch.
