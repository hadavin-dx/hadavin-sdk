# What the n8n Postgres Insert (Skip on Conflict) returns for a new row and a duplicate

Written 08:56Z; section 3 added after the 08:55Z order. All statements are "in my runs": n8n 2.46.6, Node 24.22.2, Linux, a Postgres 16 container (pinned image), synthetic lead ids, loopback only, one n8n process, default concurrency. Nothing here comes from the n8n docs; the docs do not say what a skipped row returns.

## The one plain sentence

Yes. In my runs a flow can branch on "was this new?": a new insert output one item holding the inserted row (it has the fields id, lead_id, note), and a skipped duplicate also output one item, but that item held only success true and no row fields, so an IF node that tests "lead_id is not empty" separates the two. I first read the two shapes in the reply bodies (all 20 Postgres bursts: exactly 1 reply of 10 had the row fields, 9 had success true), then built the IF node and ran it (section 3: 20 of 20 bursts exactly 1 new, 9 duplicate).

## Setup (what I built)

- Table: leads_skip (id serial primary key, lead_id text, note text) plus a UNIQUE index on lead_id. Made with psql.
- Workflows (webhook, response mode "last node"; body field lead_id):
  - sk-a: Webhook, Postgres Insert (operation insert, option Skip on Conflict on). Reply = the Insert node output.
  - sk-b: same, then a Code node that reports the number of items and their fields.
  - sk-c: same as sk-b with Always Output Data on for the Insert node.
  - dt-up: Webhook, Data Table Upsert (match on lead_id), Code report.
  - dt-ne: Webhook, Data Table "If Row Does Not Exist", Code report (no insert).
  - dt-ne-ins: Webhook, "If Row Does Not Exist", Data Table Insert, Code report (check, then write, two steps).
- Data Table operations in 2.46.6 (read from the node source in the install): insert, upsert, If Row Exists, If Row Does Not Exist, update, get, delete. There is no single "insert if not exists" operation. "If Row Does Not Exist" only checks: it passes the input item on when no row matches and outputs 0 items when one does.
- Files: scripts and raw outputs are in n8n-rerun/skip/ (driver-skipc.py.txt, burst-*-master_skipc.out.txt, probe-master_skipc.out.txt, summary-table.txt).

## 1. What the node outputs (one stack, single calls: first the NEW id, then the same id again)

| Workflow | Call | HTTP | Reply body (as printed) | Insert/Upsert node output items |
|---|---|---|---|---|
| sk-a | NEW | 200 | {"id":1,"lead_id":"probe-sk-a-...","note":"synthetic"} | 1 |
| sk-a | DUPLICATE | 200 | {"success":true} | 1 |
| sk-b | NEW | 200 | {"seen_items":1,"items":[{"id":3,"lead_id":"...","note":"synthetic"}]} | 1 |
| sk-b | DUPLICATE | 200 | {"seen_items":1,"items":[{"success":true}]} | 1 |
| sk-c | NEW | 200 | {"seen_items":1,"items":[{"id":5,"lead_id":"...","note":"synthetic"}]} | 1 |
| sk-c | DUPLICATE | 200 | {"seen_items":1,"items":[{"success":true}]} | 1 |

- Always Output Data made no difference, because the node already outputs one item on a skip.
- A skipped insert still used up a number of the serial id column: the new rows got ids 1, 3, 5 (the duplicates took 2 and 4). In the first fresh burst stack a skipped insert burned 9 numbers (new row id 1, the next new row, from the next workflow, id 11). Anyone relying on gap-free ids needs to know this.
- Data Table Upsert: NEW and existing both give 1 item with id, lead_id, createdAt, updatedAt. New: createdAt equals updatedAt. Existing: updatedAt is later (the upsert updated the row). Same as my earlier variant c.
- Data Table "If Row Does Not Exist" then Insert, single DUPLICATE: the check output 0 items, the Insert and Code nodes did not run, and the webhook replied HTTP 500 with the message "No item to return was found" (the execution itself is recorded as success).

## 2. Burst results: 10 calls at once, same lead id, count rows for that id

"Fresh stack" = new work folder, new Postgres container, new n8n, the first burst on it. "Reused stack" = one n8n that took 5 bursts in a row (a new lead id per burst, same id inside a burst). Row counts were read from the table (psql count, or the Data Table rows) after each burst.

| Workflow | Fresh stacks (5 stacks, 1 burst each): rows for the id | Reused stack (5 bursts): rows for the id |
|---|---|---|
| sk-a (Postgres Insert, skip) | 1, 1, 1, 1, 1 | 1, 1, 1, 1, 1 |
| sk-c (same, Always Output Data on) | 1, 1, 1, 1, 1 | 1, 1, 1, 1, 1 |
| dt-up (Data Table Upsert) | 1, 1, 1, 1, 1 | 1, 1, 1, 1, 1 |
| dt-ne-ins (check, then insert) | 9, 10, 1, 9, 3 | 8, 8, 2, 9, 3 |

What each execution saw (all 4 workflows, all 40 bursts = 400 executions): every execution finished with status success.
- sk-a, sk-c (20 bursts): HTTP 200 for all 10 calls; the Insert node output exactly 1 item in every execution; in each burst exactly 1 reply carried the row fields (id, lead_id, note) and 9 carried success true.
- dt-up (10 bursts): HTTP 200 for all; the node output 1 item in every execution; in each burst exactly 1 reply had createdAt equal to updatedAt and 9 had later updatedAt values.
- dt-ne-ins (10 bursts): the replies were a mix of HTTP 200 and HTTP 500 "No item to return was found". Number of 200 replies equalled the number of rows in every burst. The check-then-write is a race: more than one call passed the check before the first row was written. The table has no unique rule, so the extra rows were kept.

## 3. The real IF node on the branch signal (order of 08:55Z)

Workflow sk-if: Webhook, Postgres Insert (Skip on Conflict, unique index on lead_id), IF node (condition: lead_id is not empty, strict string check), true path = a Code node answering branch new, false path = a Code node answering branch duplicate. 10 calls at once, same lead id. Stack conditions as in section 2: 10 fresh stacks (1 burst each) and 1 reused stack (10 bursts), n8n 2.46.6, one machine.

Exact distribution (from if-summary-table.txt): 20 of 20 bursts gave rows for the id = 1, "new" hits = 1, "duplicate" hits = 9, all 10 executions success, no HTTP error (10 fresh, 10 reused). No burst gave any other split. The IF read the skipped item (success true, no lead_id) as the false path every time. Per execution (from the stored execution data): the new one ran the Insert, the IF (true output) and NewBranch; each duplicate ran the Insert, the IF (false output) and DupBranch.
Not tested: an IF on the id column instead of lead_id; other n8n versions; more than 10 parallel calls.

## What this does and does not say

- In my runs, a unique index in Postgres plus Skip on Conflict kept exactly 1 row in 20 of 20 bursts, with the single-run shapes above. This is the database enforcing the rule; the node's option only turns the error into a no-error answer.
- In my runs the Data Table Upsert also kept 1 row in 10 of 10 bursts. I did not check how it does that (no claim about locking or a unique rule).
- The two-step "If Row Does Not Exist" then Insert made extra rows in 9 of 10 bursts for one id (1 row in one fresh burst; 2 to 10 rows in the other nine). I did not repeat this beyond the 10 bursts, so I give the spread, not a rate.
- Not tested: another n8n version, a different unique key type, more than 10 parallel calls, conflicts on two columns, a queue-mode n8n, a failure that is not a conflict.
- Side finding to keep in mind: the dt-ne-ins HTTP 500 comes from the webhook "last node" reply with 0 items, not from a failed execution.

## Process notes

- Order of events: the first probe stack ran at 08:35Z; my first burst launches failed on my own script (limit 200 on the executions list, API refuses above 100); the disk filled up once (each work folder's link copy of node_modules costs about 280 MB of metadata), so I deleted only my own failed sk folders, and the launcher now saves results and deletes each stack folder. The final series ran 08:47Z to 08:55Z.
- The first probe's execution lists used a time window and repeated the previous execution in the duplicate rows (my error, shown in the raw probe file); the reply bodies and the burst series use an id baseline.
