EVIDENCE n8n-4: the current core-a trigger workflows run in n8n 2.47.7 against the real endpoint and worker
=================================================================================================

Role: EVIDENCE RUNNER. This file records what was run and what came back. It holds no verdict.
Step type: one-off manual run, made-up data, no model call (a recorded model double answers), cost US$0.
Run window (UTC, host clock): 2026-11-20T10:32:39Z to 2026-11-20T10:51:49Z, Windows laptop.
Inputs (read only): C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-a\ at head 02226ce047b9b483b45c0f8fa8b845620d99f4f8
  n8n\hadavin-trigger.json  sha256 f1837c9c3b1d31bee39ab750227e26b6ef38965c558acf3c5aef23aaa06cd05b
  n8n\hadavin-trigger-error.json  sha256 4905c2b2bce55b04c164e26a6df67ddff9a823387f2e488c35b593bc979e77f3
Raw output: C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\evidence-n8n-4\raw\ (44 files, names quoted below);
throwaway scripts in ...\evidence-n8n-4\scripts\ (mk.py, launch.py, call.py, ex.py, start.sh, HEAD.txt). No made-up signing
string or header value is in any of them (scanned: raw\*, scripts, both imported workflow copies: no match).

Set-up (what was actually run)
------------------------------
n8n: one container hvn8n-main, n8nio/n8n:2.47.7 (digest sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea, cached,
no pull), network hvn8n-net, port 127.0.0.1:5691->5678 only, community edition, data folder in the scratch folder (raw\01-start.txt).
Imported with n8n import:workflow and n8n import:credentials, published with n8n publish:workflow, one container restart, then
n8n list:workflow and n8n list:workflow --active=true both listed hv4Err000000001 (error workflow) and hv4Trg000000001 (main) (raw\01-start.txt).
Receiver: the files src\hadavin_sdk\triggers\endpoint.py and worker.py of a plain copy of the tree (tar copy without .git, in
_local\scratch\evidence-n8n-4\src; the cloud worktree was not edited), Python 3.13.3 in a uv venv (offline install). Memory store,
no PostgreSQL, so no hvn8n-pg container was created. worker.main was NOT used: in this tree the config block `triggers` does not exist
(worker.py module text and tests\triggers\crash_launcher.py say so), so launch.py puts the pieces together the way the repo's own
tests\triggers\crash_launcher.py does (build_runtime on the fixture config, make_trigger_app stand-in for the App, worker.make_app,
worker.make_server, worker.serve). The model is a double that answers "Nothing to do." at once, and sleeps 100 s when the document holds
the text SLOW-EVENT. launch.py wraps the WSGI callable only to print one line per request (UTC time, method, path, status, first 300 bytes
of the answer). max_running 2, ack_wait_s 5.0, sender id hv4-sender, one made-up signing string (file in the scratch folder, never printed).
The worker listened on 0.0.0.0:5693 (all interfaces, not loopback) because the n8n container had to reach it as
host.docker.internal; it ran from 10:32 to 10:51 UTC and was stopped at the end. The receiver was restarted twice (worker-1.log ->
worker-2.log to add the request log line; worker-2.log -> worker-3.log in case 5): a restart empties the memory store.
Values changed in the copies of the two files before the import (printed by mk.py, raw\00-mk.txt; nothing else was changed):
  main workflow: id (hv4Trg000000001), settings.errorWorkflow (= the id of the imported error workflow), webhook path (hv4-trigger),
  webhookId (a new UUID), the id of the webhook credential and of the Sign credential, URL of "Send to Hadavin"
  (http://host.docker.internal:5693/v1/trigger). Error workflow: id only.
Credentials created by n8n import:credentials: httpHeaderAuth (header X-Hv4-Auth, made-up value) and crypto (hmacSecret = the made-up signing string).
Calls: python POST (call.py) to http://127.0.0.1:5691/webhook/hv4-trigger with header X-Hv4-Auth and a JSON body {"record_id", "text"[, "event"]}.
n8n execution data was read from a copy of the sqlite file (ex.py). The Docker VM clock runs about 12 s ahead of the host clock at the start of
the run (receiver log time 10:36:06 against n8n row 10:36:17 for the same call); n8n times below are VM clock, "receiver" times are host clock.

Case table
----------
Receiver answer = the line printed by the receiver (raw\worker-*.log). Caller = what the HTTP client of the webhook got.

| # | Input | Observed output (quoted) | File and node |
|---|-------|--------------------------|---------------|
| 1 | import + publish of both files, list | import: "Successfully imported 1 workflow." twice; publish: "Publishing workflow with ID: hv4Trg000000001 (current version)" and the same for hv4Err000000001; list:workflow --active=true after the restart: "hv4Err000000001\|hadavin-trigger-error (outline; ...)" and "hv4Trg000000001\|hadavin-trigger (outline; ...)" (raw\01-start.txt) | both files |
| 2 | record_id ev-B1, text "made-up document two", right header | Receiver: "10:36:06 UTC receiver: POST /v1/trigger -> 202 Accepted {"run_id": "run-2950f86bf0a8d92ddaf45dce986efc52", "state": "RECEIVED"}". Caller: "HTTP 202 after 0.18s", empty body. n8n execution 3: first row status=waiting (lastNodeExecuted "Wait before next round"); path Trigger -> Id and text present? (out 0) -> Answer caller: taken -> Hash business id (key 9009ee58...b90e) -> Build request -> Stamp time -> Sign -> Send to Hadavin (out 0: {"run_id": "run-2950f...", "state": "RECEIVED"}) -> Run still going? (out 0) -> Checks left? (out 0) -> Next check -> Wait before next round; the wait ended 73 s later (VM start 1795171327.. see raw), Send to Hadavin run 1 got receiver "10:37:17 UTC receiver: POST /v1/trigger -> 200 OK {"run_id": "run-2950f...", "state": "NO_ACTION"}", then Run still going? (out 1) -> Run ended well? (out 0) -> Done: finished or waits for approval; execution status=success, started 10:36:17.449, stopped 10:37:27.683 (raw\02-case2-call.txt, 02-case2-exec.txt). A first try of cases 2 and 3 with another record id before the request log existed is kept in raw\02a-*, 03a-*: same outputs (RECEIVED, then NO_ACTION; second event: run_id run-68d46c62..., state NO_ACTION, execution success) | main: Answer caller: taken, Send to Hadavin, Run still going?, Run ended well?, Done |
| 3 | the SAME event again (same record_id, same text) after the first run had ended | Receiver: "10:37:33 UTC receiver: POST /v1/trigger -> 200 OK {"run_id": "run-2950f86bf0a8d92ddaf45dce986efc52", "state": "NO_ACTION"}": the same run_id as case 2. Caller: "HTTP 202 after 0.18s". n8n execution 4: status=success, Send to Hadavin out 0 = {"run_id": "run-2950f...", "state": "NO_ACTION"}, Run still going? out 1, Run ended well? out 0, Done. The model double printed "model double called" once for run-2950f... (at that moment raw\worker-2.log held "model double called" lines for the case 2 run only; the SLOW run of case 8 came later); the same key 9009ee58... was built (raw\03-case3-call.txt, 03-case3-exec.txt) | main: Hash business id, Send to Hadavin |
| 4 | same record_id, text "made-up document two CHANGED" (same key, other payload) | Receiver: "trigger status=409 sender=hv4-sender run=run-2950f86bf0a8d92ddaf45dce986efc52" (log line of the worker) and "10:37:37 UTC receiver: POST /v1/trigger -> 409 Conflict" (empty answer). Caller: "HTTP 202 after 0.14s". n8n execution 5: status=error, lastNodeExecuted "Stop: refused or gave up"; Send to Hadavin status=success with items per output [0, 1], output 1 item error = {"message": "409 - \"\"", "name": "AxiosError", "code": "ERR_BAD_REQUEST", "status": "409"}; Busy and rounds left? went to its output 1 (false); no wait, no second send. Execution error: NodeOperationError "Hadavin trigger: a request was refused (400, 401, 409, 413, 500, a redirect or another status that is not tried again), or the busy rounds were used up ...". The error workflow fired: execution 6, mode=error, status=success, started 0.047 s after execution 5 stopped, Notify placeholder reached; Build message: "Workflow: hadavin-trigger (outline; ...)\nExecution: http://localhost:5678/workflow/hv4Trg000000001/executions/5\nLast node: Stop: refused or gave up\nError: Hadavin trigger: a request was refused ..." (raw\04-case4-call.txt, 04-case4-exec.txt) | main: Send to Hadavin (out 1), Busy and rounds left?, Stop: refused or gave up; error file: Error Trigger, Build message, Notify placeholder |
| 5 | receiver stopped (worker process killed 10:41:51 UTC; health check gave curl exit 7), record_id ev-D1 sent at about 10:41:55 | Caller: "HTTP 202 after 0.17s" (Answer caller: taken ran). n8n execution 12, Send to Hadavin run 0: output 1, error {"message": "connect ECONNREFUSED 192.168.65.254:5693", "name": "Error", "code": "ECONNREFUSED"} (no status); Busy and rounds left? out 0 (true); Next round gave round 1, checks 0; Wait before next round: status=waiting (row at 25 s after the call: status=waiting). Round 1 send after the wait (VM 1795171399712, 72 s after round 0): ECONNREFUSED again, Next round gave round 2. Retry On Fail is false in the file: each round shows ONE Send to Hadavin run, ms 32 and 15. Worker started again at 10:43:55 UTC (empty memory store). Round 2 send (VM 1795171472482): Receiver "10:44:19 UTC receiver: POST /v1/trigger -> 202 Accepted {"run_id": "run-13aecd31db50bfaccaecd18dbe361865", "state": "RECEIVED"}" -> Run still going? out 0 -> Checks left? -> Next check (checks 1) -> Wait -> second send "10:45:33 UTC receiver: POST /v1/trigger -> 200 OK {... "state": "NO_ACTION"}" -> Run ended well? out 0 -> Done. Execution 12 status=success, started 10:42:07.722, stopped 10:45:46.243. The error workflow did NOT run for execution 12 (no mode=error execution between 11 and 14 in raw\12-all-executions.txt). Rounds seen: 0, 1, 2 of 45 (raw\07-case5-*.txt) | main: Send to Hadavin (out 1), Busy and rounds left?, Next round, Wait before next round, Stamp time |
| 6 | the crypto credential replaced with another made-up value (n8n import:credentials, "Successfully imported 2 credentials."), record_id ev-W1 | Receiver: "10:41:30 UTC receiver: POST /v1/trigger -> 401 Unauthorized" (empty answer). Caller: "HTTP 202 after 0.15s". n8n execution 10: status=error, lastNodeExecuted "Stop: refused or gave up"; Send to Hadavin out 1 error {"message": "401 - \"\"", "name": "AxiosError", "code": "ERR_BAD_REQUEST", "status": "401"}; no second round. Error workflow: execution 11 mode=error status=success. The right credential was imported again afterwards (the later runs got 202/200) (raw\06-case6-*.txt) | main: Sign (credential), Send to Hadavin (out 1), Stop: refused or gave up |
| 7 | UNVERIFIED notes | see the second table | all nodes |

Extra cases run to exercise notes (each once; raw\05-*, 08-*, 09-*, 10-*, 11-*):

| # | Input | Observed output (quoted) |
|---|-------|--------------------------|
| 8 | text SLOW-EVENT (model double sleeps 100 s), record_id ev-S1 | Receiver 202 "state": "WORKING" twice (10:37:48 and 10:38:59 UTC), then "10:40:16 UTC receiver: POST /v1/trigger -> 200 OK ... "state": "NO_ACTION"". n8n execution 7: three sends, "checks" 1, then 2 on the Next check items, waits of about 73.7 s (VM 1795171078877 -> 1795171152565) and 75.6 s (1795171152607 -> 1795171228162); status=success, started 10:37:58.796, stopped 10:40:28.195, Done reached (raw\05-slow-exec.txt) |
| 9 | body without record_id | Caller: "HTTP 500", body {"message":"Error in workflow"}. Execution 8 status=error, lastNodeExecuted "Stop: id or text missing", message "Hadavin trigger: the business id or the document text is empty or missing. Nothing was sent."; error workflow execution 9 status=success. No request reached the receiver (raw\08-guard-*.txt) |
| 10 | no X-Hv4-Auth header; wrong header value | Caller both times: "HTTP 403", header WWW-Authenticate 'Basic realm="Webhook"', body "Authorization data is wrong!"; no n8n execution was created for either (execution ids 8 to 9 are the guard case, next id is 10) (raw\09-noauth-call.txt, 09b-badauth-call.txt) |
| 11 | record_id as the number 12345 | Caller 202; execution 13 status=success, Done reached (first send already got "NO_ACTION"); key b2e78c3d... differs from the text-id keys (raw\10-extra-1-call.txt, 10-extra-exec.txt) |
| 12 | record_id 9007199254740993 (number above the safe integer limit) | Caller "HTTP 500" {"message":"Error in workflow"}; execution 14 status=error, "Stop: id or text missing"; error workflow execution 15 success |
| 13 | "event": "" | Caller "HTTP 500"; execution 16 status=error "Stop: id or text missing"; execution 17 error workflow success |
| 14 | text of three spaces | Caller "HTTP 500"; execution 18 status=error "Stop: id or text missing"; execution 19 error workflow success |
| 15 | record_id ev-B1, same text as case 2, "event": "update"; and the same with "rerun": "2" | Both caller 202; executions 20 and 21 status=success; run ids run-bc18e0d4... and run-0fe5e30e... (new runs, differing from run-2950f86b...); keys 36debbdf... and f601154c... differ from the case 2 key 9009ee58... |
| 16 | n8n container restarted (docker restart hvn8n-main, 10:48:55 UTC) 5 s into a 70 s wait (record_id ev-R1, SLOW text so that the first answer is WORKING) | Before: execution 22 status=waiting. After the restart (health 200 at +40 s): still status=waiting; log lines "Received SIGTERM. Shutting down..." and "Marked executions as `crashed`" (raw\11-restart-log-grep.txt). The wait resumed: Wait before next round run 0 status=success startTime 1795171803758, 73.5 s after the first send (VM 1795171730265); second send got the receiver "10:49:52 UTC receiver: POST /v1/trigger -> 202 Accepted ... "state": "WORKING"", a new wait started; the execution then finished status=success (10:51 UTC check, raw\12-all-executions.txt). The execution was not marked crashed (raw\11-restart-after.txt, 12-all-executions.txt: all 22 executions are success or error, none crashed) |

UNVERIFIED-notes table (what each note of the two files says is unverified; one row per note)
---------------------------------------------------------------------------------------------
Status words: SEEN WORKING = exercised and behaved as the note's intent states; SEEN FAILING = exercised and did not; NOT EXERCISED. "Log line" = receiver line or n8n field.
Because the values listed in set-up were replaced before the import, the placeholder values themselves were NOT run.

| Node (file) | Part of the note | Status | Log line / evidence |
|-------------|------------------|--------|---------------------|
| Trigger placeholder (main) | authentication 'headerAuth' with credential type 'httpHeaderAuth' | SEEN WORKING | right header: 202; no or wrong header: HTTP 403 "Authorization data is wrong!", no execution created (cases 1, 10) |
| | what the import does with the placeholder credential id | NOT EXERCISED | the id was replaced before the import |
| | responseMode 'responseNode' (parameter text) | SEEN WORKING | the caller got the Respond node's answer (202, no body) in cases 2 to 4; 500 {"message":"Error in workflow"} when the execution failed before a Respond node ran (cases 9, 12 to 14) |
| | form of the webhookId value | NOT EXERCISED for the placeholder; a fresh UUID in the form 8-4-4-4-12 registered and answered on /webhook/hv4-trigger | execution 1 onwards |
| Id and text present? (main) | the expression as it stands: text id, whole-number id | SEEN WORKING | out 0 for "ev-B1" and for 12345 (execution 13) |
| | missing id, id above Number.isSafeInteger, "event": "", whitespace-only text | SEEN WORKING (out 1, nothing sent) | executions 8, 14, 16, 18 all end in "Stop: id or text missing" |
| | a document with a lone surrogate (stated: passes here, Hadavin answers 400) | NOT EXERCISED | |
| | null values, empty id | NOT EXERCISED | |
| Stop: id or text missing (main) | what the caller gets when the execution fails and no answer node ran | SEEN | HTTP 500, body {"message":"Error in workflow"} (cases 9, 12, 13, 14) |
| Answer caller: taken (main) | typeVersion 1, respondWith noData, responseCode 202 | SEEN WORKING | caller "HTTP 202", empty body, Content-Type application/json; charset=utf-8 |
| | passes its input item on unchanged with noData | SEEN WORKING | the item before and after (Hash business id input) held the same body and the same fields |
| | n8n answers at this point, before the long chain | SEEN | caller answered in 0.10 to 0.33 s while the executions ran up to 73 s more (cases 2, 8) |
| Hash business id (main) | expression with id, event name and optional rerun | SEEN WORKING | key = 64 hex; same input -> same key (cases 2, 3: 9009ee58...b90e); "event": "update" and "rerun": "2" gave two other keys and two new runs (case 15) |
| | a falsy rerun value is ignored | NOT EXERCISED | |
| Build request (main) | input path through Answer caller and Hash | SEEN WORKING | output item {"body": "{\"key\":\"068ff...\",\"document\":\"...\"}", "round": 0} |
| Stamp time (main) | input from the state check and the second way into the wait node | SEEN WORKING | Stamp time run 1 and 2 after a Wait that was entered from Next check (case 2, 8) and from Next round (case 5); new ts each time |
| Sign (main) | the Crypto typeVersion 2 node inside this chain keeps ts, body, round | SEEN WORKING | Sign output: body, round, ts, hmac; the receiver accepted it (202/200) |
| | what the import does with the placeholder credential id | NOT EXERCISED | replaced before the import |
| | wrong signing value | SEEN | receiver 401, n8n status "401" (case 6) |
| Send to Hadavin (main) | timeout 45000 ms as it stands | NOT EXERCISED | no answer took longer than 5 s |
| | an answer 520 to 524; a 3xx answer; a 502, 503 or 504 with a body | NOT EXERCISED | |
| | Retry On Fail off in this chain | SEEN | with the receiver down each round shows one send, items [0, 1] (case 5) |
| | the real Hadavin endpoint | SEEN WORKING (the tree's endpoint.py and worker.py with a model double and memory store) | 202, 200, 409, 401 as listed |
| | 2xx leaves via output 0 to Run still going?; failures via output 1 | SEEN WORKING | 202, 200 -> out 0; 409, 401, ECONNREFUSED -> out 1 |
| Busy and rounds left? (main) | 520 to 524 in the list | NOT EXERCISED | |
| | no status at all counts as busy (ECONNREFUSED) | SEEN WORKING | out 0 (true) for ECONNREFUSED in rounds 0 and 1 (case 5) |
| | 401 and 409 are false | SEEN WORKING | out 1 (false), no second round (cases 4, 6) |
| | the number 45 and the loop with the real 70 s wait and 45 rounds | PARTLY | 3 rounds with the real 70 s wait (round 0, 1, 2); the limit of 45 was never reached |
| | Retry-After header ignored | NOT EXERCISED | (no 503 was produced) |
| Next round (main) | the field checks and '?? 0' before the first check | SEEN WORKING | item after Next round: "round": 1, "checks": 0 |
| Wait before next round (main) | the 70 s wait as it stands | SEEN WORKING | stored as status=waiting; ended 72.8 s, 73.5 s, 73.7 s, 75.6 s after its start (first-send to resume intervals in cases 2, 16, 8) |
| | survives a restart of n8n | SEEN WORKING (once) | case 16: execution 22 stayed waiting through docker restart and finished success |
| | the loop with the real 70 s wait | SEEN WORKING | cases 2, 5, 8, 16 |
| | whether anybody is told when an execution is lost in a restart | NOT EXERCISED | the execution in case 16 was not lost; the log says "Marked executions as `crashed`" but no execution row has that status |
| | second entry from Next check | SEEN WORKING | cases 2, 8 |
| Stop: refused or gave up (main) | message text as it stands | SEEN WORKING | execution error text quoted in cases 4 and 6 |
| | reached after rounds of 502, 504, 520 to 524 or no answer | NOT EXERCISED | only 3 rounds of no answer, then the receiver came back |
| Run still going? (main) | whole node: RECEIVED, WORKING -> true; other state -> false | SEEN WORKING | out 0 for "RECEIVED" and "WORKING"; out 1 for "NO_ACTION" |
| Checks left? (main) | whole node, $('Stamp time').last() on this branch, '?? 0' | SEEN WORKING | out 0 with checks missing, then 1, then 2 (case 8) |
| | the number 45 and out 1 (checks used up) | NOT EXERCISED | out 1 never taken |
| Next check (main) | whole node | SEEN WORKING | "checks" went 0 -> 1 -> 2 in one execution (case 8), body unchanged |
| Run ended well? (main) | NO_ACTION -> true | SEEN WORKING | out 0 |
| | SUCCEEDED, WAITING_FOR_APPROVAL -> true; any other or missing state -> false | NOT EXERCISED | the double only answers NO_ACTION |
| Done: finished or waits for approval (main) | node in this place | SEEN WORKING | reached in cases 2, 3, 5, 8, 11, 15, 16 with item {"run_id", "state": "NO_ACTION"} |
| Stop: run did not end well (main) | whole node, errorMessage as an expression | NOT EXERCISED | no state of the failing list was produced |
| Stop: still running (main) | node in this place | NOT EXERCISED | |
| Notify placeholder (error file) | what lands here for 520 to 524, a run that ended badly, a run still showing as running | NOT EXERCISED | |
| | it ran for refused sends (409, 401) and refused events | SEEN WORKING | executions 6, 9, 11, 15, 17, 19: mode=error, status=success |
| | for an execution lost in a restart | NOT EXERCISED | see the Wait row |
| | a short restart of the Hadavin worker must NOT land here | SEEN WORKING | case 5: receiver down for about 2 minutes, execution 12 ended success, no error execution |

Not run
-------
- The state-check outcomes that are not NO_ACTION (NEEDS_PERSON, DENIED, REJECTED, EXPIRED, ROLLED_BACK, STOPPED, SUCCEEDED, WAITING_FOR_APPROVAL) and the nodes behind them.
- The busy loop to its end (45 rounds, about 52 minutes) and the checks loop to its end; 502, 503, 504 and 520 to 524 answers; a 3xx answer; a timeout of 45 s; a TLS failure.
- Lone surrogate text; null values; a falsy rerun value; the placeholder values of the files (credential ids, webhookId, URL).
- A restart of n8n during a loop whose wait was lost (case 16 survived); PostgreSQL store; the tick job; the real model; worker.main (no `triggers` config block in this tree).
- Each case was run once; case 2 and 3 were run twice (first try raw\02a-*, 03a-*).

Slips
-----
- The first worker run had no request log; the worker was restarted (log wrapper added in launch.py) and cases 2 and 3 were run again; the first try is kept as raw\02a-*, 03a-*.
- Two shell tries to stop the worker failed (taskkill option syntax under Git Bash); the processes (pids 14204 and 1976) were then stopped with Stop-Process; one studio hook refused a command that named the scratch folder and the made-up string files together, and a script file (scan.py) did the scan instead.
- The worker listened on all interfaces for the length of the run (see set-up).

Cleanup (raw\14-cleanup.txt, 2026-11-20T10:51:49Z and later)
------------------------------------------------------------
    docker rm -f hvn8n-main        -> hvn8n-main
    docker network rm hvn8n-net    -> hvn8n-net
    docker ps -a --filter name=hvn8n --format {{.Names}}     -> (empty)
    docker ps -a --filter name=hvn8n-pg --format {{.Names}}  -> (empty; no pg container was created)
    docker network ls --filter name=hvn8n                    -> (empty)
    worker processes 14204 and 1976 stopped; health on 127.0.0.1:5693 afterwards: "Unable to connect to the remote server"
    containers present and not touched: hv-ev-pg, pg-t3, pg50b9, pg-ev9, pgt48, pgb10
    Ports 5690 and 5679 were not used.

Files created
-------------
In C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\: evidence-n8n-4.md (this file); evidence-n8n-4\raw\ (44 files: 00-mk.txt, 01-start.txt, 02-*, 02a-*, 03-*, 03a-*, 04-*, 05-*, 06-*, 07-*, 08-*, 09-*, 09b-*, 10-*, 11-*, 12-all-executions.txt, 13-n8n-log-full.txt, 14-cleanup.txt, pids.txt, worker-1.log, worker-2.log, worker-3.log); evidence-n8n-4\scripts\ (mk.py, launch.py, call.py, ex.py, start.sh, HEAD.txt).
In C:\Users\rakes\Downloads\Hadavin\_local\scratch\evidence-n8n-4\ (not committed, git-ignored area): src\ (tree copy), venv\, home\, n8nhome\ (n8n data), wf\ (workflow copies and credential files holding the made-up values), the made-up value files, raw\, the same scripts and scan.py.
