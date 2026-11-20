EVIDENCE n8n-3: Wait node restart, Respond then Stop and Error, chained Respond nodes (n8n 2.47.7)
===================================================================================================

Role: EVIDENCE RUNNER. This file records what was run and what came back. It holds no verdict.
Ledger need: core-a ESCALATIONS E6 (the template loops depend on these behaviours).
Run window (UTC, host clock): 2026-11-20T08:47:26Z to 2026-11-20T08:57:46Z, Windows laptop.
Step type: one-off manual verification on made-up data. CODE-LAST rung 1 (the no-code tool itself), nothing built.
Same method as evidence-n8n-1.md and evidence-n8n-2.md. No signing string, no receiver container was needed.

Image tag and digest (raw\01-start.txt):

    [n8nio/n8n:2.47.7] [n8nio/n8n@sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea]
    docker exec hvn8n-main n8n --version  ->  2.47.7

Where the raw output is: C:\Users\rakes\Downloads\Hadavin\_local\scratch\n8n-verify\step3\
  raw\01-start.txt          start, import, publish of 6 workflows
  raw\02-cases23-calls.txt  caller side of cases 2 and 3 (full HTTP headers and body)
  raw\03-exec-cases23.txt   executions of cases 2 and 3 decoded from a copy of the n8n database
  raw\04-items-cases3.txt   output item of each Respond and Set node in case 3
  raw\05-log-cases23.txt    n8n container log after cases 2 and 3
  raw\06-case1-w60.txt, raw\07-case1-w120.txt   case 1 timelines
  raw\08-exec-all.txt       all 6 executions decoded at the end
  raw\09-log-grep.txt, raw\10-n8n-log-full.txt  n8n log
  raw\11-cleanup.txt        removal proof
  wf\*.json (test workflows), mk3.py, start3.sh, c23.sh, run1.sh, st.py, ex3.py, items3.py (throwaway scripts)

Set-up
------
One container hvn8n-main (n8nio/n8n:2.47.7) on network hvn8n-net, port 127.0.0.1:5691->5678 only, community edition,
no account, no licence, no browser. Fresh data folder step3\n8nhome (persistent between the restarts, mounted
as /home/node/.n8n). Six workflows imported with n8n import:workflow and published with n8n publish:workflow, then
one restart, then n8n list:workflow --active=true showed all six active (raw\01-start.txt):

    w120  webhook (respond: immediately) -> Wait 120 s (time interval) -> Set
    w60   the same with Wait 60 s
    stop  webhook (Using Respond to Webhook node) -> Respond R1 -> Stop and Error; settings.errorWorkflow = hv-err
    two   webhook (Respond node mode) -> Respond R1 -> Respond R2
    set   webhook (Respond node mode) -> Respond R1 -> Set Mid -> Respond R2
    hv-err  the error workflow of the earlier runs (Error Trigger -> Set -> No Operation), copy of wf\err.json

Respond nodes answer with json: {from: R1 or R2, got: the incoming item}. Calls were made with curl POST, body
{"n":1,"who":"made-up"}, to http://127.0.0.1:5691/webhook/<path>. Clock note: the Docker VM clock runs about 12 s
ahead of the host clock (seen in the earlier run); the times in database rows are VM clock, the "-- hh:mm:ss" lines
of the timelines are host clock. Durations are taken inside one clock only.

Case 1: Wait node and a restart of the container (one try each, no repeat)
---------------------------------------------------------------------------
Method: call the webhook, wait the stated seconds, print execution rows from a copy of the database (st.py),
docker restart hvn8n-main (default 10 s stop timeout), then print the rows every 15 s.

1a. Wait 60 s (below the 65 s threshold), restart at about second 20 (raw\06-case1-w60.txt):

    -- before restart 08:51:15 (t+20s):
       (5, 'w60', 'webhook', 'running', 0, '2026-11-20 08:51:06.826', None)
    -- restart returned 08:51:20 (t+25s)
    -- 08:51:51 (t+56s) health=200
       (5, 'w60', 'webhook', 'crashed', 0, '2026-11-20 08:51:06.826', '2026-11-20 08:51:06.858')
    ... same row at t+71 s, 87, 102, 117, 133 s (82 s past the planned end of the wait): still crashed, never resumed.

    The webhook caller had already got 200 (respond immediately). Execution 5 ended with status crashed and
    finished = 0. It did not resume. The n8n log at the restart says: Received SIGTERM, Waiting for 1 active executions
    to finish (twice), then on the next start: Last session crashed ... Marked executions as crashed ...
    [Recovery] Logs available, amended execution ... Found unfinished executions: 5 (raw\10-n8n-log-full.txt).

1b. Wait 120 s (above the threshold), restart at about second 30 (raw\07-case1-w120.txt):

    -- before restart 08:53:38 (t+30s):
       (6, 'w120', 'webhook', 'waiting', 0, '2026-11-20 08:53:19.608', '2026-11-20 08:53:19.662')
    -- restart returned 08:53:40 (t+32s)
    -- 08:53:55 (t+47s) health=200   row 6 still waiting (also at t+63 s and in the next rows)
    -- 08:55:58 (t+170s) health=200
       (6, 'w120', 'webhook', 'success', 1, '2026-11-20 08:53:19.608', '2026-11-20 08:55:21.635')

    The execution was saved with status waiting (stoppedAt 0.054 s after start) before the restart, survived the
    restart, and finished with status success. VM-clock times (raw\08-exec-all.txt): Hook startTime 1795164799638,
    Wait node run startTime 1795164921620, so the Wait node resumed 121.98 s after the Hook node; the execution
    stopped at 08:55:21.635 VM clock, started 08:53:19.608, total 122.0 s, i.e. about 2 s after the 120 s wait
    would have ended. The restart did not shorten or lengthen the wait (the wait end time is stored).
    Resume was seen at the first row printed after 08:55:21 VM time; the exact host-clock moment was not sampled
    (rows were printed every 15 s).

Case 2: Respond to Webhook first, then Stop and Error (workflow stop, errorWorkflow set; raw\02, raw\03)
-------------------------------------------------------------------------------------------------------

    caller got: HTTP/1.1 200 OK, Content-Type: application/json; charset=utf-8, Content-Length: 288,
    body: {"from":"R1","got":{"headers":{...},"params":{},"query":{},"body":{"n":1,"who":"made-up"},"webhookUrl":"http://localhost:5678/webhook/stop","executionMode":"production"}}
    execution 1 workflow=stop mode=webhook status=error, lastNodeExecuted: Stop,
      execution error: NodeOperationError "deliberate stop after respond"
      Hook success, R1 success (51 ms), Stop status=error
    execution 2 workflow=hv-err mode=error status=success started 08:50:44.893 (VM clock), 0.12 s after execution 1 started:
      Error Trigger, Build message, Notify placeholder all success. Message built:
      "Workflow: stop / Execution: http://localhost:5678/workflow/hv3stop0000000000/executions/1 / Last node: Stop / Error: deliberate stop after respond"
    n8n log after the call: two lines "deliberate stop after respond" (raw\05-log-cases23.txt).

    The caller got the Respond answer with status 200 (not the error); the execution status is error; the
    error workflow fired once.

Case 3: two Respond to Webhook nodes in a row (raw\02, raw\03, raw\04)
-----------------------------------------------------------------------
Workflow two (R1 -> R2): caller got HTTP 200, body {"from":"R1","got":{...body {"n":1,"who":"made-up"}...}}
(Content-Length 287). Only the first answer reached the caller. Execution 3 status=success, lastNodeExecuted R2,
R1 success (8 ms), R2 success (14 ms), no error. Output item of R1 and of R2 (headers removed in the printout):

    two R1 output item: {"params": {}, "query": {}, "body": {"n": 1, "who": "made-up"}, "webhookUrl": "http://localhost:5678/webhook/two", "executionMode": "production"}
    two R2 output item: {"params": {}, "query": {}, "body": {"n": 1, "who": "made-up"}, "webhookUrl": "http://localhost:5678/webhook/two", "executionMode": "production"}

So R2 received the item that R1 passed on (R1 passes its input item through unchanged) and its output is the same.
Workflow set (R1 -> Set Mid -> R2): caller got HTTP 200, body {"from":"R1",...} again. Execution 4 status=success,
last node R2, all four nodes success:

    set R1 output item: {"params": {}, "query": {}, "body": {...}, "webhookUrl": ".../webhook/set", "executionMode": "production"}
    set Mid output item: {"mid": "set-between"}
    set R2 output item: {"mid": "set-between"}

R2 received the item of Mid (not of R1). The caller never saw the R2 answer. Warning in the n8n log: none found for
either workflow; the log after the calls (raw\05-log-cases23.txt) shows only the startup lines and the two stop-error
lines; the grep over the whole log for warn, respond, already (raw\09-log-grep.txt) matched only migration names and
the restart recovery lines. No error or warning was raised for the second Respond node.

NOT RUN
-------
Nothing from the brief was left out. Not done and not asked: repeats (every case ran once, each gave a clear result);
the exact host-clock second at which the 120 s wait resumed was not sampled (15 s sampling).

Slips: the first start script call hit the tool time limit and ran in the background; it completed normally
(raw\01-start.txt shows the full run). No retry was needed. The agents register was not written (brief: write only in
step3\ and this file). The owner's secrets folder was not touched; no model API was called; no browser was used.

Cleanup (raw\11-cleanup.txt, 2026-11-20T08:57:46Z):

    docker rm -f hvn8n-main   -> hvn8n-main
    docker network rm hvn8n-net  -> hvn8n-net
    docker ps -a --filter name=hvn8n --format {{.Names}}   -> (empty)
    docker network ls --filter name=hvn8n --format {{.Name}} -> (empty)
    other containers present and not touched: run-hvfix3-15, run-hvfix3-17, hvfix3-pg15, hvfix3-pg17, hv-ev-pg
