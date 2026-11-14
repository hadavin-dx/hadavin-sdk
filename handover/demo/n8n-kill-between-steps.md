# What happens when n8n is killed after the Postgres insert and before the reply, and the same lead is sent again

Written 09:12Z. In my runs: n8n 2.46.6 (regular mode, not queue mode), one Linux machine, one fresh stack (new work folder, new Postgres container, new n8n), loopback, synthetic ids, a stand-in outbox program as the "work done for the lead". Nothing here comes from the n8n docs.

## One plain sentence

In my runs the first lead was processed ZERO times (lost) in 5 of 5 kills: the row was in the table, the caller lost its connection, n8n marked that run "crashed" after the restart and did not run it again, and when the same lead id was sent again the insert said "duplicate", so the work was never done. The "duplicate" answer means "a row was written before", not "the work was done".

## What I built

Workflow sk-k: Webhook, Postgres Insert (Skip on Conflict, unique index on lead_id), a Wait of 4 seconds, IF (lead_id not empty), "new" path: a request to the stand-in outbox (this stands for the real work, so one outbox call = the lead was processed once) then a Code step that answers branch new; "duplicate" path: a Code step that answers branch duplicate. The webhook replies with the last step reached.

Method: a control without kill (same lead id sent twice), then 5 kills on the same stack, one after the other, each with a new lead id: send the lead, wait 1.5 s (this is inside the Wait, after the insert), read the table and the outbox count, kill the whole n8n process group (kill confirmed: nothing listened on the n8n ports after), start n8n again and wait until the webhook answers, wait 2 s, send the SAME lead id again, wait 7 s (to see whether n8n re-runs the crashed run on its own), read table, outbox and the list of runs.

## Raw counts

Control (no kill): call 1 answered branch new, call 2 answered branch duplicate; rows 1; outbox calls 1.

| Kill | Rows before kill | Outbox before kill | Caller's first call | Run list after restart | 2nd call (same id) answered | Final rows | Final outbox calls (work done) |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0 | connection dropped (RemoteDisconnected) | run 3 "crashed" | duplicate (200) | 1 | 0 |
| 2 | 1 | 0 | connection dropped | run 5 "crashed" | duplicate (200) | 1 | 0 |
| 3 | 1 | 0 | connection dropped | run 7 "crashed" | duplicate (200) | 1 | 0 |
| 4 | 1 | 0 | connection dropped | run 9 "crashed" | duplicate (200) | 1 | 0 |
| 5 | 1 | 0 | connection dropped | run 11 "crashed" | duplicate (200) | 1 | 0 |

- Distribution: 5 of 5 kills = row kept (1), second call took the duplicate path, work done 0 times. Zero of 5 gave the work once; zero of 5 gave it twice.
- The "crashed" status is n8n's own record of the interrupted run, written after the restart. The run list showed no new run for the first lead in the 9 seconds after the restart: n8n did not run it again on its own in these runs (default settings, nothing changed).
- The runs of the second calls ended with status success (they only answered duplicate).

## What it means (one sentence)

With "Skip on Conflict" the database keeps the first insert, so a retry after a crash is told "duplicate" and is skipped: the dedupe step alone turns a crash between insert and work into a LOST lead (the lost-message class), so a client build needs a status that is written after the work is done (for example a status column plus a re-send job for rows that never reached "done"); I did not test that fix here.

## Limits (not tested)

- The kill is always inside the 4-second Wait after the insert and before any work (outbox before kill 0 in 5 of 5). Kills at other points (after the outbox call, before the reply) are not in this test; for those my earlier variant e kill runs apply, not this one.
- One stack, 5 kills, one machine; other n8n versions, queue mode, the "recover crashed runs" settings of n8n, a Postgres that is killed, and a client that retries by itself are not tested.
- The reply to the caller was never delivered in these runs (the connection dropped), so I cannot say what a caller that did not retry would see beyond the dropped connection.
- Raw files: n8n-rerun/skip/kill-* and driver-skipk.py.txt.
