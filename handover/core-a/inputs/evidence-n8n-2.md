EVIDENCE n8n-2: what n8n 2.47.7 hands to the workflow when the receiver gives no usable answer
==============================================================================================

Role: EVIDENCE RUNNER. This file records what was run and what came back. It holds no verdict.
Ledger row: BL-core-complete-2026-11-20-D-B (item shape for a refused connection, a timeout, 502 and 504).
Run window (UTC, host clock): 2026-11-20T06:23:31Z to 2026-11-20T06:31:28Z, on the Windows laptop, Docker server 29.7.2.
Step type: one-off manual verification on made-up data. CODE-LAST n/a: evidence run, no component created.
EGM skipped for the run itself: an evidence runner records, EGM reviewers judge this file.
Method: the same as evidence-n8n-1.md (first run). Nothing of the first run was changed.

Where the raw output is
-----------------------
Folder: C:\Users\rakes\Downloads\Hadavin\_local\scratch\n8n-verify\step2\
  raw\01-images.txt                   image tags and digests
  raw\02-mk2.txt                      every change made to the base workflow, printed by mk2.py
  raw\03-start.txt                    start of the containers, import, publish
  raw\04-import-err-again.txt         second import of the error workflow (see Slips)
  raw\05-probe-calls.txt              cases 1 to 8 and the comparison statuses: caller side and receiver side
  raw\06-probe-case1-try2.txt         case 1, second try
  raw\07-loop-calls.txt               item 9 (loop) and item 10 (caller answer), base response mode
  raw\08-lastnode-calls.txt           item 10 extra: caller answer when the webhook waits for the last node
  raw\09-executions.txt               all 35 executions decoded from a copy of the n8n database (stack text cut to 300 characters)
  raw\09-executions-full-stack.txt    the same with the full stack text
  raw\10-n8n-log.txt, raw\11-recv-log.txt   container logs
  raw\12-stall-repeat.txt, raw\13-stall-repeat-executions.txt   cases 8a and 8b run twice more
  raw\14-cleanup.txt                  removal of the containers and the network
  raw\recv2-all.jsonl                 every request the receiver got (33 lines, all headers)
  wf\p2.json, wf\l2.json, wf\w2.json  the three test copies; wf\err.json = copy of the first run's error workflow (Set 3.4)
  recv2.py, mk2.py, start2.sh, drive.py, ex2.py, chk.py   the throwaway scripts
  n8nhome\                            a fresh n8n data folder for this step (the first run's n8nhome was not touched)

Read only from the first run: wf\t2.json (base), wf\err.json, in\good.json, execs.py (decoder), and the
made-up 40-character signing string (never printed; the scripts replace it by <SIGNING-STRING>).

Set-up
------
Two containers on one docker network (hvn8n-net), never more than two at once:
  hvn8n-main   n8nio/n8n:2.47.7, port published only as 127.0.0.1:5691->5678, community edition, no account,
               no licence, no browser. Settings as the first run's CONFIG B: N8N_BLOCK_ENV_ACCESS_IN_NODE=false,
               NODE_FUNCTION_ALLOW_BUILTIN=crypto, HADAVIN_TRIGGER_SECRET = the made-up signing string.
  hvn8n-recv   python:3.13-slim running recv2.py (raw sockets, stdlib only), no published port, listens on 8080 only.
               It reads the whole request, recomputes the signature, then behaves by path:
                 /s/<code>    that status, Content-Length: 0, Connection: close
                 /hang        sends nothing and holds the connection (up to 40 s)
                 /close       closes normally (FIN) without one response byte
                 /reset       closes abruptly (SO_LINGER 0, RST) without one response byte
                 /stallbody   sends "HTTP/1.1 200 OK", Content-Type and Content-Length: 50, the empty line, no body byte, then holds
                 /stallhdr    sends "HTTP/1.1 200 OK" and one header line, never the empty line that ends the headers, then holds
                 /ok          202 with a JSON body
               For every request it records held_s (seconds from the first request byte to the end) and who ended the connection.

Image tag and digest (raw\01-images.txt, 2026-11-20T06:23:31Z):

    docker image inspect n8nio/n8n:2.47.7 python:3.13-slim --format '{{.RepoTags}} {{.RepoDigests}} id={{.Id}} created={{.Created}}'

    [n8nio/n8n:2.47.7] [n8nio/n8n@sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea] id=sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea created=2026-11-13T09:36:08.238489272Z
    [python:3.13-slim] [python@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90] id=sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 created=2026-11-05T08:02:05.509998459Z
    docker exec hvn8n-main n8n --version  ->  2.47.7

Test copies (mk2.py, raw\02-mk2.txt). Base for all three: the first run's wf\t2.json (Set typeVersion 3.4, loop of
3 rounds, 2 s wait, HTTP Request typeVersion 4, retryOnFail false, onError continueErrorOutput).

    wf/p2.json id=hvp2000000000000      (probe copy, cases 1 to 8)
      change: id, name, webhook path = hv-p2
      change: Send to Hadavin url = the query parameter u of the webhook call (whole address)
      change: Send to Hadavin options.timeout 30000 -> 3000
      unchanged: Send to Hadavin retryOnFail = False onError = continueErrorOutput typeVersion = 4
      change: new Set node 'Probe values' between the error output of Send to Hadavin and the IF node: [["probe_error_keys", "={{ Object.keys($json.error ?? {}).join(',') }}"], ["probe_status_typeof", "={{ typeof $json.error?.status }}"], ["probe_status_as_json", "={{ JSON.stringify($json.error?.status) ?? 'undefined' }}"], ["probe_httpCode_typeof", "={{ typeof $json.error?.httpCode }}"], ["probe_code_as_json", "={{ JSON.stringify($json.error?.code) ?? 'undefined' }}"], ["probe_if_busy_or_no_answer", "={{ String(['', '502', '503', '504'].includes(String($json.error?.status ?? ''))) }}"]]
      change: IF node 'Busy and rounds left?' leftValue = ={{ ['', '502', '503', '504'].includes(String($json.error?.status ?? '')) }} (no round count)
      change: IF true output -> new No Operation node 'Probe: busy or no answer'; false output -> 'Stop: refused or gave up' as before
    wf/l2.json id=hvl2000000000000      (loop copy, items 9 and 10)
      change: id, name, webhook path, url and timeout as above
      change: Busy and rounds left? leftValue = ={{ ['', '502', '503', '504'].includes(String($json.error?.status ?? '')) && $('Stamp time').last().json.round < 3 }}
      unchanged: Wait before next round amount = 2 seconds
    wf/w2.json id=hvw2000000000000      (item 10 extra)
      l2 + change: Trigger placeholder responseMode onReceived -> lastNode

The IF node is the base's own: typeVersion 2, one condition, operator boolean "true", leftValue = the expression above.
In the probe copy a run that ends in 'Probe: busy or no answer' is a successful execution by construction of the
probe (the loop and the Stop node are not behind that output); the loop copy l2 has the base's wiring.

Each case = one POST of in\good.json to the workflow's production webhook address
(http://127.0.0.1:5691/webhook/<id>/trigger%2520placeholder/hv-<copy>?u=<address the HTTP Request node must call>),
sent by drive.py with Python urllib. Addresses used:
    connection refused : http://hvn8n-recv:8081/ok          (the receiver container listens on 8080 only)
    name not resolving : http://hvn8n-nohost.invalid:8080/ok
    all others         : http://hvn8n-recv:8080/<path>

Slips and blocks during the run (not n8n results)
-------------------------------------------------
- start2.sh imported the error workflow while n8n on the fresh data folder was still running its database
  migrations; that import failed ("SQLITE_ERROR: duplicate column name: createdByThreadId", raw\03-start.txt).
  The other three imports succeeded. The error workflow was imported and published again at 06:26:11Z
  (raw\04-import-err-again.txt), n8n restarted, all four workflows listed as active.
- Case 1, first try (06:26:36Z): n8n answered the webhook call itself with 404 "Cannot POST /webhook/..."
  about 25 s after the restart; no execution was created. Second try at 06:28:18Z worked (execution 19).
  Case 1 therefore has execution number 19, after the other probe cases.
- Clock: the Docker VM clock was about 12 s ahead of the Windows clock (webhook call sent 06:26:57.344Z by the
  host clock, n8n logged the execution start as 06:27:09.651). Times in "drive" output are host clock, times in
  execution records and recv_unix are VM clock. Durations are taken inside one clock only.
- The studio hook was not triggered in this step. The owner's secrets folder was not read or written.
- The agents register (_local\agents-register.md) was not written by this runner (brief: write only in step2\
  and in this file).

Cases 1 to 8: the item on the error output of the HTTP Request node
-------------------------------------------------------------------
Run: python drive.py probe (06:26:36Z to 06:28:09Z), python drive.py probe1 (06:28:18Z), then python ex2.py.
Raw: raw\05-probe-calls.txt, raw\06-probe-case1-try2.txt, raw\09-executions.txt.

In every case below the node 'Send to Hadavin' has run status success and put one item on output 1 (the second,
"error" output) and none on output 0. The item keys were always: body, round, ts, hmac, error.
"error object" is the value of the field error as stored in the execution data; the field stack is cut here
(full text in raw\09-executions-full-stack.txt). "Probe values" is what expressions in the next node saw.
"IF" is the output of the IF node with the expression  ['', '502', '503', '504'].includes(String($json.error?.status ?? ''))
(output 0 = true, output 1 = false).

Case 1, connection refused (execution 19, node ms=14, receiver saw nothing):

    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "connect ECONNREFUSED 172.19.0.2:8081", "name": "Error", "stack": "Error: connect ECONNREFUSED 172.19.0.2:8081\n    at AxiosError.from (/usr/local/lib/node_modules/n8n/node_modules/.pnpm/axios@1.20.0_.../axios/dist/node/axios.cjs:1577:24)\n    at RedirectableRequest.handleRequestError ... (stack cut, 3163 chars)", "code": "ECONNREFUSED"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ECONNREFUSED\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 2, name that does not resolve (execution 1, node ms=157, receiver saw nothing):

    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "getaddrinfo ENOTFOUND hvn8n-nohost.invalid", "name": "Error", "stack": "Error: getaddrinfo ENOTFOUND hvn8n-nohost.invalid\n    at AxiosError.from (...axios.cjs:1577:24)\n    at RedirectableRequest.handleRequestError ... (stack cut, 3169 chars)", "code": "ENOTFOUND"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ENOTFOUND\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 3, receiver accepts and never answers, node timeout 3000 ms (execution 2):

    node 'Send to Hadavin' run 0 status=success ms=3014 items per output=[0, 1]
    receiver: path=/hang sig_match=True held_s=3.0 ended='client closed the connection'
    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "timeout of 3000ms exceeded", "name": "AxiosError", "stack": "AxiosError: timeout of 3000ms exceeded\n    at createTimeoutError (...axios.cjs:4308:14)\n    at RedirectableRequest.handleTimeout ... (stack cut, 2923 chars)", "code": "ECONNABORTED"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ECONNABORTED\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)
    Waiting time measured: 3014 ms by n8n's node time; 3.0 s by the receiver. In the loop runs (item 9) the
    same case gave node ms 3009, 3006, 3011, 3008 and 3010, 3008, 3007, 3009; receiver held_s 2.998 to 3.0.

Case 4, 502 with an empty body (execution 3, node ms=32, one request at the receiver, sig_match True):

    error keys: ['message', 'name', 'stack', 'code', 'status']
    error object: {"message": "502 - \"\"", "name": "AxiosError", "stack": "AxiosError: Request failed with status code 502\n    at settle (...axios.cjs:2530:12)\n    at RedirectableRequest.handleResponse ... (stack cut, 3342 chars)", "code": "ERR_BAD_RESPONSE", "status": 502}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request,response,status,statusCode,error", "probe_status_typeof": "number", "probe_status_as_json": "502", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ERR_BAD_RESPONSE\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 5, 504 with an empty body (execution 4, node ms=14, one request at the receiver, sig_match True):

    error keys: ['message', 'name', 'stack', 'code', 'status']
    error object: {"message": "504 - \"\"", "name": "AxiosError", "stack": "AxiosError: Request failed with status code 504 ... (stack cut, 3342 chars)", "code": "ERR_BAD_RESPONSE", "status": 504}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request,response,status,statusCode,error", "probe_status_typeof": "number", "probe_status_as_json": "504", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ERR_BAD_RESPONSE\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 6, 503 with an empty body (execution 5, node ms=12, one request at the receiver, sig_match True):

    error keys: ['message', 'name', 'stack', 'code', 'status']
    error object: {"message": "503 - \"\"", "name": "AxiosError", "stack": "AxiosError: Request failed with status code 503 ... (stack cut, 3342 chars)", "code": "ERR_BAD_RESPONSE", "status": 503}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request,response,status,statusCode,error", "probe_status_typeof": "number", "probe_status_as_json": "503", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ERR_BAD_RESPONSE\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 7, receiver closes after reading the request, no response byte. Two ways of closing were run.

  7a, normal close (FIN) (execution 6, node ms=13, receiver: path=/close sig_match=True held_s=0.0):

    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "socket hang up", "name": "Error", "stack": "Error: socket hang up\n    at AxiosError.from (...axios.cjs:1577:24)\n    at RedirectableRequest.handleRequestError ... (stack cut, 3151 chars)", "code": "ECONNRESET"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ECONNRESET\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

  7b, abrupt close (RST) (execution 7, node ms=15, receiver: path=/reset sig_match=True held_s=0.001):

    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "read ECONNRESET", "name": "Error", "stack": "Error: read ECONNRESET\n    at AxiosError.from (...axios.cjs:1577:24) ... (stack cut, 3142 chars)", "code": "ECONNRESET"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ECONNRESET\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)

Case 8, receiver sends a status line and headers and then stalls. Two forms were run, each three times.

  8a, status line "HTTP/1.1 200 OK" + complete headers (Content-Length: 50) + no body byte
      (executions 8, 32, 34; node ms=3012, 3011, 3011; receiver held_s=3.001, 3.001, 3.001, ended='client closed the connection'):

    item keys: ['body', 'round', 'ts', 'hmac', 'error']
    error keys: str                      (the field error is a plain text, not an object)
    error object: "aborted"
    Probe values: {"probe_error_keys": "0,1,2,3,4,5,6", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "undefined", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)
    The item has no message, name, code or status in this case; the status 200 the receiver sent appears nowhere on the item.

  8b, status line "HTTP/1.1 200 OK" + one header line, header block never finished
      (executions 9, 33, 35; node ms=5735, 3015, 3010; receiver held_s=5.721, 2.997, 3.0, ended='client closed the connection'):

    error keys: ['message', 'name', 'stack', 'code']
    error object: {"message": "timeout of 3000ms exceeded", "name": "AxiosError", "stack": "AxiosError: timeout of 3000ms exceeded\n    at createTimeoutError (...axios.cjs:4308:14)\n    at RedirectableRequest.handleTimeout ... (stack cut, 2923 chars)", "code": "ECONNABORTED"}
    Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request", "probe_status_typeof": "undefined", "probe_status_as_json": "undefined", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ECONNABORTED\"", "probe_if_busy_or_no_answer": "true"}
    IF: items per output=[1, 0]  (true)
    The first of the three runs waited 5735 ms with the timeout set to 3000 ms (message still says 3000ms); the two
    repeats waited 3015 and 3010 ms. Why the first was longer was not looked into.

Comparison: refused requests and an accepted one (same probe copy, 06:27:46Z to 06:28:05Z host clock)

    400 (execution 10): error object {"message": "400 - \"\"", "name": "AxiosError", "stack": "...", "code": "ERR_BAD_REQUEST", "status": 400}
        Probe values: {"probe_error_keys": "message,name,isAxiosError,code,config,request,response,status,statusCode,error", "probe_status_typeof": "number", "probe_status_as_json": "400", "probe_httpCode_typeof": "undefined", "probe_code_as_json": "\"ERR_BAD_REQUEST\"", "probe_if_busy_or_no_answer": "false"}
        IF: items per output=[0, 1]  (false) -> node 'Stop: refused or gave up' status=error -> execution status=error -> execution 11 workflow=hv-err mode=error status=success
    401 (execution 12): "message": "401 - \"\"", "code": "ERR_BAD_REQUEST", "status": 401; probe_if_busy_or_no_answer "false"; IF [0, 1]; Stop node; error workflow execution 13
    409 (execution 14): "message": "409 - \"\"", "code": "ERR_BAD_REQUEST", "status": 409; probe_if_busy_or_no_answer "false"; IF [0, 1]; Stop node; error workflow execution 15
    413 (execution 16): "message": "413 - \"\"", "code": "ERR_BAD_REQUEST", "status": 413; probe_if_busy_or_no_answer "false"; IF [0, 1]; Stop node; error workflow execution 17
    202 (execution 18): node 'Send to Hadavin' items per output=[1, 0]; output 0 item: {"run_id": "run-00000000000000000000000000000000", "state": "RUNNING"}; the error output and the IF node did not run

Seen in all cases:
- The stored error object has the keys message, name, stack, code and, only when the receiver sent a status, status
  (a number). While the next node's expressions ran, Object.keys($json.error) listed other names:
  message,name,isAxiosError,code,config,request and, with a status, also response,status,statusCode,error.
  The keys isAxiosError, config, request, response, statusCode and error are not in the stored execution data;
  their values were not printed in this run.
- $json.error.httpCode was undefined in every case.
- name is "AxiosError" for a status answer and for a timeout, and "Error" for ECONNREFUSED, ENOTFOUND and ECONNRESET.
- With 502, 503, 504 code is "ERR_BAD_RESPONSE"; with 400, 401, 409, 413 code is "ERR_BAD_REQUEST".

Item 9: the loop with the changed "busy" test, cases 1, 3 and 4
---------------------------------------------------------------
Expression in the IF node 'Busy and rounds left?' of copy l2 (operator boolean "true"):

    ={{ ['', '502', '503', '504'].includes(String($json.error?.status ?? '')) && $('Stamp time').last().json.round < 3 }}

3 rounds, 2 s wait, node timeout 3000 ms, Retry On Fail off. Run: python drive.py loop, 06:28:27Z to 06:29:39Z
(raw\07-loop-calls.txt; executions 20 to 25 in raw\09-executions.txt).

Case 1, connection refused (execution 20, started 06:28:38.464, stopped 06:28:44.612 VM clock):

    receiver records added by this call: 0        (nothing listens on that port, so no request can be counted there)
    node 'Send to Hadavin' ran 4 times (run 0 to 3), each: items per output=[0, 1], error code ECONNREFUSED
    node 'Stamp time' run 0: round=0 ts=1795156118    'Sign' run 0: hmac=b19312c1ddb070c47c4dbdeb3656221619fe203c5ed769305073c373afaa6ad7
    node 'Stamp time' run 1: round=1 ts=1795156120    'Sign' run 1: hmac=d8e04d329b7deb1283a363020216063afdaa6bb88a68605f634185576c17f326
    node 'Stamp time' run 2: round=2 ts=1795156122    'Sign' run 2: hmac=70809fb5f35586a4f48bf05fcd82c26ccb6eaf39e21bfb7e87770ebb2c660583
    node 'Stamp time' run 3: round=3 ts=1795156124    'Sign' run 3: hmac=28ca825039c3b087d4c27a6e714c419a81ebc16fcaa3f6682fdfc949ea5aed93
    node 'Busy and rounds left?' run 0, 1, 2: items per output=[1, 0]; run 3: items per output=[0, 1]
    node 'Wait before next round' ran 3 times, ms=2001, 2001, 2000
    node 'Stop: refused or gave up' run 0 status=error
    execution 20 status=error, lastNodeExecuted: Stop: refused or gave up
    execution 21 workflow=hv-err mode=error status=success, lastNodeExecuted: Notify placeholder
       {"message": "Workflow: hv-l2\nExecution: http://localhost:5678/workflow/hvl2000000000000/executions/20\nLast node: Stop: refused or gave up\nError: Hadavin trigger: the request was refused, got no answer, or was answered busy (503) in every round. The event was NOT accepted. Send it again by hand with the SAME key."}

Case 3, accepts and never answers (execution 22, started 06:28:59.579, stopped 06:29:17.682 VM clock):

    receiver records added by this call: 4
       recv_unix=1795156139.618 path=/hang ts=1795156139 sig=v0=666011674e597d064b8afcdffd713bc2fc278638d719da4a641064dc56ec618a sig_match=True body_sha256=a75dfaa1a0663446 held_s=2.998 ended='client closed the connection'
       recv_unix=1795156144.636 path=/hang ts=1795156144 sig=v0=2359dcbc5b032f77b14d96add3e0d64b7f74f3e7c74ae20f1f1479e6104b1056 sig_match=True body_sha256=a75dfaa1a0663446 held_s=2.999 ended='client closed the connection' gap_s=5.018
       recv_unix=1795156149.656 path=/hang ts=1795156149 sig=v0=072b4c677066100fdeea7d4660d7b5ece8047f88528920dc96aac9b5791ca0a4 sig_match=True body_sha256=a75dfaa1a0663446 held_s=3.0 ended='client closed the connection' gap_s=5.020
       recv_unix=1795156154.675 path=/hang ts=1795156154 sig=v0=a505f2fd087dfa5a4768ae44082a2bbb8f56500a6216ec9bb76f8cd76e2474b3 sig_match=True body_sha256=a75dfaa1a0663446 held_s=3.0 ended='client closed the connection' gap_s=5.019
    node 'Send to Hadavin' ran 4 times, ms=3009, 3006, 3011, 3008, each: error code ECONNABORTED, "timeout of 3000ms exceeded"
    node 'Busy and rounds left?' run 0, 1, 2: items per output=[1, 0]; run 3: items per output=[0, 1]
    execution 22 status=error, lastNodeExecuted: Stop: refused or gave up
    execution 23 workflow=hv-err mode=error status=success

Case 4, 502 with an empty body (execution 24, started 06:29:33.221, stopped 06:29:39.365 VM clock):

    receiver records added by this call: 4
       recv_unix=1795156173.281 path=/s/502 ts=1795156173 sig=v0=957613ff9f9a081879b21dfaa3d7befc8f934fca24ca7a2a26f18d0af2d9b6ca sig_match=True body_sha256=a75dfaa1a0663446 held_s=0.001 ended='receiver answered and closed'
       recv_unix=1795156175.315 path=/s/502 ts=1795156175 sig=v0=d193747c21732d7ffdafb77b83916464671091c8a215d0978168df23b2e81da5 sig_match=True body_sha256=a75dfaa1a0663446 held_s=0.0 ended='receiver answered and closed' gap_s=2.034
       recv_unix=1795156177.337 path=/s/502 ts=1795156177 sig=v0=75185ecb325ced183f0f44b1079c663e667baa540852f22872094d2a6ffdce53 sig_match=True body_sha256=a75dfaa1a0663446 held_s=0.0 ended='receiver answered and closed' gap_s=2.022
       recv_unix=1795156179.356 path=/s/502 ts=1795156179 sig=v0=c32dbacb45547bc6cccee165134aaec58d0cefd7a3fc51cbfc8387aefef514ce sig_match=True body_sha256=a75dfaa1a0663446 held_s=0.0 ended='receiver answered and closed' gap_s=2.019
    node 'Send to Hadavin' ran 4 times, each: "status": 502, "code": "ERR_BAD_RESPONSE"
    node 'Busy and rounds left?' run 0, 1, 2: items per output=[1, 0]; run 3: items per output=[0, 1]
    execution 24 status=error, lastNodeExecuted: Stop: refused or gave up
    execution 25 workflow=hv-err mode=error status=success

In the three cases: 4 send attempts per run (round 0 plus 3 further rounds), the same body each time
(body_sha256 a75dfaa1a0663446 where the receiver saw it), a different timestamp and a different signature in
every round, every signature the receiver saw matched its own recomputation, and each run ended in the node
'Stop: refused or gave up' followed by one run of the error workflow.

Item 10: what the caller of the webhook received in cases 1, 3 and 4
-------------------------------------------------------------------
(a) Base response mode (Trigger placeholder responseMode onReceived), copy l2, the three calls of item 9 (raw\07-loop-calls.txt):

    case1 connection refused      caller got: HTTP 200 after 0.119 s, body: {"message":"Workflow was started"}
    case3 accepts, never answers  caller got: HTTP 200 after 0.051 s, body: {"message":"Workflow was started"}
    case4 502 empty body          caller got: HTTP 200 after 0.084 s, body: {"message":"Workflow was started"}

    The same answer, HTTP 200 {"message":"Workflow was started"}, came back for every probe call of cases 1 to 8
    and for 400, 401, 409, 413 and 202 (raw\05-probe-calls.txt), before the HTTP Request node had finished.

(b) Extra, not the base: the same loop with responseMode lastNode (copy w2), python drive.py last, 06:29:39Z to 06:30:20Z
    (raw\08-lastnode-calls.txt; executions 26 to 31):

    case1 connection refused      caller got: HTTP 500 after 6.781 s, body: {"message":"Error in workflow"}     receiver records: 0
    case3 accepts, never answers  caller got: HTTP 500 after 18.182 s, body: {"message":"Error in workflow"}    receiver records: 4
    case4 502 empty body          caller got: HTTP 500 after 6.757 s, body: {"message":"Error in workflow"}     receiver records: 4

    Executions 26, 28, 30: status=error, lastNodeExecuted: Stop: refused or gave up, 4 runs of 'Send to Hadavin' each,
    a new ts and hmac in every round; executions 27, 29, 31: workflow=hv-err mode=error status=success.

NOT RUN, all items in one list
------------------------------
1. Why the first run of case 8b waited 5735 ms instead of 3000 ms (seen once in three runs; not looked into).
2. The values of the live-only keys of $json.error (isAxiosError, config, request, response, statusCode, error);
   only their names were recorded.
3. Cases 2, 5, 6, 7 and 8 through the loop copy (the brief asked for 1, 3 and 4).
4. 502, 503, 504 with a body (only empty bodies); a TLS failure; a redirect; a receiver that answers after the timeout.
5. The outline's real loop values (30 rounds, 60 s wait) and the real 30000 ms timeout; any Wait above 65 s.
6. HTTP Request typeVersion other than 4; Retry On Fail on; n8n versions other than 2.47.7; n8n Cloud; queue mode.
7. The real Hadavin endpoint and a real proxy in front of it: all behaviours came from a stub receiver on a docker network.
8. A connection that is neither refused nor accepted (packets dropped, connect timeout).

Other notes
-----------
- No case had to be marked NOT RUN for failing three tries; case 1 needed a second try (see Slips).
- Bible R-numbers grepped for this run (bible\RULES.md): R351 (which failures an adapter retries), R334 (bounded retries).
  They are named here only as the rules the brief's question belongs to; this file draws no conclusion from them.
- CAPACITY: docker reported cpus=12 mem=16434511872; this run used 2 light containers; disk C: 79 percent used.
- No model API was called, no browser was used, nothing was pushed, nothing under projects\ or _local\scratch\wt\ was touched.
- Files left: the step2\ folder (throwaway n8n database in step2\n8nhome\, scripts, raw output). chk.py counted the
  made-up signing string in the raw files, the workflow copies and this file: 0 occurrences in each.

Clean-up
--------
Run 2026-11-20T06:31:23Z (raw\14-cleanup.txt):

    docker rm -f hvn8n-main hvn8n-recv
    docker network rm hvn8n-net

    hvn8n-main
    hvn8n-recv
    hvn8n-net
    --- docker ps -a --filter name=hvn8n-
    (end of filter output)
    --- docker network ls --filter name=hvn8n
    (end of filter output)
    --- port 5691
    http_code=000
    --- all containers
    hvfix-run	python:3.13-slim	Up 8 minutes
    hvfix-pg	postgres:17.10	Up 8 minutes
    hv-ev-pg	postgres:17.10	Up 2 hours
    pg-t3	postgres:17	Exited (0) 31 hours ago
    pg50b9	postgres:17	Exited (137) 2 weeks ago
    pg-ev9	postgres:17	Exited (0) 2 weeks ago
    pgt48	postgres:17	Exited (137) 2 weeks ago
    pgb10	postgres:17	Exited (137) 2 weeks ago
    2026-11-20T06:31:28Z

Both filter commands printed nothing between their header line and the end marker: no container and no network
with the name prefix hvn8n exists. The containers listed under "all containers" belong to other jobs and were
not named by any command of this run.
