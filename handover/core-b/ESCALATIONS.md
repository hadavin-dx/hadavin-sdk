# ESCALATIONS of core-b (newest on top)

## E1 (2026-11-20 05:20 UTC / 10:50 IST) Session cron for the one-minute board was refused
- Item: ORDER 003 item 1 (CronCreate with schedule "* * * * *").
- Attempts: 1. The call was denied by the session's permission check ("Destructive or Unwanted Actions"). No raw log file exists; the denial is a tool result in the session.
- Not retried, not worked around (ORDER 003 item 4).
- What I do instead: the fallback written in ORDER 003 item 1: a board at the end of every tool batch through handover/core-b/tools/board.sh. Effect: boards will be more than 1 minute apart whenever one tool batch (for example a long read or a reviewer round) runs longer than that, and no board is written while the session sits idle waiting for an agent.
- Needed from the owner: allow the cron in this cloud session, or accept the fallback rhythm.
