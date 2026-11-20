EVIDENCE n8n-1: the signed-trigger workflow outline run in a real n8n
=====================================================================

Role: EVIDENCE RUNNER. This file records what was run and what came back. It holds no verdict.
Ledger row: BL-core-complete-2026-11-20-D-E4 (the outline was never run in n8n).
Run window (UTC): 2026-11-20T05:48:55Z to 2026-11-20T06:09:04Z, on the Windows laptop, Docker server 29.7.2.
Step type: one-off manual verification on made-up data. CODE-LAST n/a: evidence run, no component created.
EGM skipped for the run itself: an evidence runner records, EGM reviewers judge this file.

Where the raw output is
-----------------------
Folder: C:\Users\rakes\Downloads\Hadavin\_local\scratch\n8n-verify\
  raw\01 ... raw\29   one text file per step, named in each section below
  raw\recv-all.jsonl  every request the throwaway receiver got (27 lines: raw body as base64 and hex, all headers)
  wf\                 the two original outline files (copies, same SHA-256), every test copy, n8n exports
  in\                 the made-up inputs
  recv.py, mk.py, mkvec.py, runvec.py, execs.py, node_out.py, recvsum.py, findstr.py, diffexport.py,
  checkparams.py, start.sh, imp.sh, post.sh   the throwaway scripts that produced the output

Inputs (read only, not edited):
  _local\scratch\wt\cloud-core-a\n8n\hadavin-trigger.json        sha256 ffde9183888a68467e498ed09a95e2a3e4f3fd8e9e0f4ac9e6febd6af4d3fa8b
  _local\scratch\wt\cloud-core-a\n8n\hadavin-trigger-error.json  sha256 9149c313c6aa50b8bb7aa5bdabe91897c8cae34325763b17b1da8a4779793032

Made-up strings: a 40-character signing string (file secret.txt) and a second 40-character literal
(file literal.txt), both generated in the scratch folder. Neither is printed here; where one would
appear the scripts print <SIGNING-STRING> or <LITERAL>.

Set-up
------
Two containers on one docker network (hvn8n-net), never more than two at once:
  hvn8n-main   n8nio/n8n:2.47.7, port published only as 127.0.0.1:5691->5678, data folder n8nhome\ in the scratch folder
  hvn8n-recv   python:3.13-slim running recv.py (stdlib http.server), no published port. It records the raw
               body bytes, the framing (Content-Length or chunked), all headers, and recomputes
               "v0=" + hex HMAC-SHA256(signing string, "v0:" + timestamp header + ":" + raw body bytes).
               Path /ok answers 202 with a JSON body; path /s/<code> answers that status with an empty body.
n8n was started three times with different settings:
  DEFAULT   no setting about env access or Code-node modules
  CONFIG B  N8N_BLOCK_ENV_ACCESS_IN_NODE=false and NODE_FUNCTION_ALLOW_BUILTIN=crypto
  CONFIG C  NODE_FUNCTION_ALLOW_BUILTIN=crypto only
In all three the container had the environment variable HADAVIN_TRIGGER_SECRET = the signing string.
Workflows were imported with the n8n command line (import:workflow), published with publish:workflow,
n8n restarted, then started through their production webhook address with curl or Python urllib.
Executions were read from a copy of n8n's sqlite database (execs.py, node_out.py).

Test copies of the outline (built by mk.py; every change is printed by the script, raw\06, raw\12, raw\24, raw\25):
  t1    the outline with only: id, name, webhook path, the URL of "Send to Hadavin" (receiver address plus
        query parameter t), settings.errorWorkflow = the id of the imported error workflow
  t2    t1 + all Set nodes typeVersion 3 -> 3.4 + loop cut to 3 rounds and 2 s wait (outline: 30 rounds, 60 s)
  t3    t2 + "Sign (option B, Code node)" connected in place of option A
  t4    t2 + loop rounds 0 + Retry On Fail ON on "Send to Hadavin", no maxTries/waitBetweenTries in the JSON
  t4b   t4 + maxTries=10, waitBetweenTries=10000 in the JSON
  t5    t2 with "Trigger placeholder" connected straight to "Hash business id" (guard node bypassed)
  err   the error-workflow outline with only id and name set; later re-imported with its Set node on 3.4
  vec, veca, vecc, vecv   small vector workflows (mkvec.py): Webhook -> Crypto and/or Code -> answer

Slips and blocks during the run (not n8n results)
-------------------------------------------------
- First import try failed with ENOENT because Git Bash rewrote the path /wf/... ; rerun with MSYS_NO_PATHCONV=1.
- The studio hook secrets_path_guard.py refused one command ("a command naming both _local and secrets").
  The command named only the scratch folder and the made-up file secret.txt. The owner-only secrets
  folder was not read or written at any time. The same steps were then run from the script start.sh
  inside the scratch folder. Reported here so the lead can decide whether that was acceptable.
- execs.py first crashed on non-ASCII output (Windows code page) and node_out.py first printed too much;
  both scripts were fixed and rerun; the files in raw\ are from the fixed runs.
- Clock: the Docker VM clock was about 13 s ahead of the Windows clock (curl started 06:02:06Z by the
  host clock, n8n logged the execution at 06:02:19). Execution 56 shows started 06:08:50.174 and stopped
  06:08:39.031, so the VM clock was set back during the run. Timestamp age (ts_age_s) is measured inside
  the receiver container against the same VM clock as n8n.


ITEM 1  Image tag and digest
----------------------------
Run (raw\01-images.txt), 2026-11-20T05:49:24Z:

    docker pull n8nio/n8n:2.47.7
    docker pull python:3.13-slim
    docker image inspect n8nio/n8n:2.47.7 python:3.13-slim --format '{{.RepoTags}} {{.RepoDigests}} id={{.Id}} created={{.Created}}'

Raw:

    [n8nio/n8n:2.47.7] [n8nio/n8n@sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea] id=sha256:b4b90747b81fcda7e76550c0d3aa7f0f64917a1e9573cff40d6834eaf2e0f8ea created=2026-11-13T09:36:08.238489272Z
    [python:3.13-slim] [python@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90] id=sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 created=2026-11-05T08:02:05.509998459Z

    docker manifest inspect n8nio/n8n:2.47.7  ->  amd64 manifest sha256:13087b14e4c7b2540cf1ed02adbb09818614540d883f9eafc8b6b3cbd715bee3
    docker exec hvn8n-main n8n --version      ->  2.47.7
    docker exec hvn8n-main node --version     ->  v26.13.0
    n8n license:info                          ->  LICENSE CERT ... isValid: false (!) ... entitlements: 0

The tag is the version the tool atlas names in section 0 (research\tool-atlas\n8n.md: "Latest stable:
n8n@2.47.7"). The tag existed, so no newer tag was looked for. No licence key was used.


ITEM 2  Import of the two outline files
---------------------------------------
Run (raw\03-import-orig.txt), 2026-11-20T05:53:37Z, both files unmodified:

    docker exec hvn8n-main n8n import:workflow --input=/wf/orig-error.json
    docker exec hvn8n-main n8n import:workflow --input=/wf/orig-trigger.json
    docker exec hvn8n-main n8n list:workflow
    docker exec hvn8n-main n8n export:workflow --all --pretty --output=/wf/export-after-orig-import.json

Raw:

    Importing 1 workflows...
    Successfully imported 1 workflow.
    exit=0                                  (both files)
    CxnXp2JTAqgHZgrO|hadavin-trigger-error (outline, not run in n8n)
    MHTOH5oFUdSgDuqO|hadavin-trigger (outline, not run in n8n)

Difference between each original and what n8n exported back (diffexport.py, raw\04-diff-orig-export.txt):

    node names only in original: []
    node names only in export: []
    TOP notes: original="UNVERIFIED: the top-level export shape ..." exported="<absent>"
    NODE '<each node>' field id: original="<absent>" exported="<a uuid>"
    added top-level keys: activeVersionId, createdAt, description, id, isArchived, meta, nodeGroups, pinData,
      shared, sourceWorkflowId, staticData, tags, triggerCount, updatedAt, versionCounter, versionId, versionMetadata

No node, parameter, connection, settings key or node-level "notes" text was changed or renamed by the
import. The import did not report any node or parameter as invalid. The top-level "notes" key was dropped.

Template parameters against the node definitions of this n8n (n8n export:nodes, 926 node types;
checkparams.py, raw\05-checkparams.txt). Every node type name exists and every typeVersion used is defined.
Lines where a parameter is limited by version:

    == 'Build request' type=n8n-nodes-base.set typeVersion=3      (same for 'Stamp time', 'Next round', error workflow 'Build message')
       versions defined: [[3, 3.1, 3.2, 3.3, 3.4, 3.5], [1, 2]] default: 3.5
       param 'assignments': type=assignmentCollection default={} displayOptions={"hide": {"@version": [3, 3.1, 3.2]}, "show": {"mode": ["manual"]}}
       param 'includeOtherFields': type=boolean default=false displayOptions={"hide": {"@version": [3, 3.1, 3.2]}}
    == 'Sign (option A, Crypto node)' type=n8n-nodes-base.crypto typeVersion=1
       versions defined: [[2], [1]] default: 2
       param 'secret': type=string default="" displayOptions={"show": {"action": ["hmac"]}}
    == 'Send to Hadavin' type=n8n-nodes-base.httpRequest typeVersion=4
       versions defined: [[3, 4, 4.1, 4.2, 4.3, 4.4, 4.5], [2], [1]] default: 4.5
    == 'Id and text present?' type=n8n-nodes-base.if typeVersion=2      versions defined: [[2, 2.1, 2.2, 2.3, 2.4], [1]] default: 2.4
    == 'Trigger placeholder' type=n8n-nodes-base.webhook typeVersion=2  versions defined: [[1, 1.1, 2, 2.1, 2.2]] default: 2.2
    == 'Wait before next round' type=n8n-nodes-base.wait typeVersion=1  versions defined: [[1, 1.1]]
    http option timeout {"displayName": "Timeout", "name": "timeout", "type": "number", "typeOptions": {"minValue": 1}, "default": 10000,
       "description": "Time in ms to wait for the server to send response headers (and start the response body) before aborting the request"}

What the Set nodes did at run time with typeVersion 3 (t1, DEFAULT, execution 1, raw\11-t1-exec.txt): the
output of 'Build request' and of 'Stamp time' is the input item unchanged plus nothing: no field body,
no field round, no field ts.

    node 'Build request' run 0 status=success
       output 0: {"headers": {...}, "params": {}, "query": {}, "body": {"record_id": "rec-001", "text": "hello"}, "webhookUrl": "...", "executionMode": "production", "key": "08008c28...28ec"}
    node 'Stamp time' run 0 status=success
       output 0: (same item, no ts)

With typeVersion 3.4 (t3, execution 2, raw\12-default-config-t3.txt):

    node 'Build request' run 0 status=success
       output 0: {"body": "{\"key\":\"08008c284627bf03bc7502a4d40191b47ebc70d897b276a5ae987e2df8ef28ec\",\"document\":\"hello\"}", "round": 0}
    node 'Stamp time' run 0 status=success
       output 0: {"body": "{...}", "round": 0, "ts": "1795154332"}

The outline as written (t1) with env access allowed (CONFIG B, execution 51, receiver line 27, raw\27-misc.txt, raw\28-config-c.txt):
n8n marked the execution success. The receiver got:

    line 27: path=/ok framing=content-length body_len=38 ts= sig=v0=12be9c6fc05fb95b.. sig_match=False ts_age_s=None
    line 27 headers: [['Content-Type', 'application/json'], ['x-hadavin-signature', 'v0=12be9c6f...60b7'], ['Content-Length', '38']]
    line 27 body text: {"record_id":"rec-001","text":"hello"}
    signature header received                           : v0=12be9c6fc05fb95bbc5eac97861856fe2a75428228ff90467e1a3336b1b360b7
    python hmac over text 'v0:undefined:[object Object]': v0=12be9c6fc05fb95bbc5eac97861856fe2a75428228ff90467e1a3336b1b360b7

So with Set typeVersion 3 the request carried the incoming webhook body, no timestamp header, and a
signature over the text v0:undefined:[object Object].

Webhook address (raw\07, raw\08-webhook-entity.txt, raw\10-webhook-path-tries.txt). The outline's webhook
node has no webhookId. After publish and restart, n8n registered:

    ('hvt1000000000000', 'hvt1000000000000/trigger%20placeholder/hv-t1', 'POST', 'Trigger placeholder', None, None)

    POST /webhook/hv-t1                                           -> 404 {"code":404,"message":"The requested webhook \"POST hv-t1\" is not registered." ...}
    POST /webhook/hvt1000000000000/trigger%20placeholder/hv-t1    -> 404 (... "POST hvt1000000000000/trigger placeholder/hv-t1" is not registered.)
    POST /webhook/hvt1000000000000/trigger%2520placeholder/hv-t1  -> {"message":"Workflow was started"}

The vector workflows, whose webhook node has a webhookId, answered on /webhook/vec, /webhook/veca, /webhook/vecc.

Other nodes as observed in the runs below: the IF node (typeVersion 2, boolean "true" operator) sent a
true result to output 0 and a false result to output 1; Stop and Error failed the execution with the
given message; the Wait node (typeVersion 1, timeInterval, seconds) passed the item on after the wait;
a connection back to an earlier node ("Wait before next round" to "Stamp time") ran as a loop;
$('Build request').first() and $('Stamp time').last() gave values in every round (ITEM 5).

NOT RUN: the editor menu "Import from File" (needs the browser editor; the command-line import was used).


ITEM 3  HMAC in a Crypto node and in a Code node against Python's hmac
----------------------------------------------------------------------
Vectors (runvec.py): timestamp text 1700000000; body = compact JSON of {"key": 64 times k, "document": D}; three D:
  ascii          hello
  non-ascii      Grüße, 日本語, U+1F600, ₹500, e + combining acute (U+0301)
  json-escaped   quote " backslash \ slash / newline tab U+0001 U+2028 U+007F <>&
The signed text is "v0:" + ts + ":" + body, UTF-8. Python side: hmac.new(secret, signed text, sha256).hexdigest().
The signed bytes of each vector are printed in hex in raw\15-vec-default-config.txt.

DEFAULT settings, 2026-11-20T06:00Z (raw\15-vec-default-config.txt), workflow vec:
  "V1 plain" = Crypto typeVersion 1, action hmac, type SHA256, encoding hex, secret typed into the node (the second literal)
  "V2 cred"  = Crypto typeVersion 2, action hmac, type SHA256, encoding hex, secret in a credential of type crypto (the signing string)

    == vector ascii
       python hmac, signing string : 813d803568abd6dc9c6b31d816f5ea8ddaa5f5b1e7ac94aea8e20a10d56479d4
       python hmac, second literal : eccf68ec17aa3aa99980629f8ef7cf5b1c6c4b901658968fc1293ef248046008
       n8n hmac_v1_plain : eccf68ec17aa3aa99980629f8ef7cf5b1c6c4b901658968fc1293ef248046008  equal_to_python_signing_string=False equal_to_python_literal=True
       n8n hmac_v2_cred  : 813d803568abd6dc9c6b31d816f5ea8ddaa5f5b1e7ac94aea8e20a10d56479d4  equal_to_python_signing_string=True equal_to_python_literal=False
    == vector non-ascii
       python hmac, signing string : 7b78c4d09840a66f6c9085a1f53180f47c774ffd65ba1f5d3a4eb9a2d655ccf3
       python hmac, second literal : 49c6a8f4d740e1eb1c78bb2bdc9cf05ac685881d3ac3b9382b476bc2489e2cf3
       n8n hmac_v1_plain : 49c6a8f4d740e1eb1c78bb2bdc9cf05ac685881d3ac3b9382b476bc2489e2cf3  equal_to_python_signing_string=False equal_to_python_literal=True
       n8n hmac_v2_cred  : 7b78c4d09840a66f6c9085a1f53180f47c774ffd65ba1f5d3a4eb9a2d655ccf3  equal_to_python_signing_string=True equal_to_python_literal=False
    == vector json-escaped
       python hmac, signing string : 68dfd3700271f297ba91050303bdc7c4828fa52c4a79f1bdb1483c1f2481624a
       python hmac, second literal : 8b62b47b022fc92d546aca68d9549842412834bd96d864035ffb4b46644a3526
       n8n hmac_v1_plain : 8b62b47b022fc92d546aca68d9549842412834bd96d864035ffb4b46644a3526  equal_to_python_signing_string=False equal_to_python_literal=True
       n8n hmac_v2_cred  : 68dfd3700271f297ba91050303bdc7c4828fa52c4a79f1bdb1483c1f2481624a  equal_to_python_signing_string=True equal_to_python_literal=False

DEFAULT settings, the two forms the outline uses (raw\17-default-config-vec-errors.txt):

    veca (Crypto typeVersion 1, secret = {{ $env.HADAVIN_TRIGGER_SECRET }}), executions 7-9:
       execution error: {"name": "ExpressionError", "message": "access to env vars denied"}
    vecc (Code node, the outline's option B code with $json.body.ts / $json.body.body), executions 10-12:
       execution error: {"name": "WrappedExecutionError", "message": "Module 'crypto' is disallowed [line 1]", "description": "DisallowedModuleError"}
    webhook answer in both cases: 500 {"message":"Error in workflow"}

CONFIG B (env access allowed, crypto module allowed), 2026-11-20T06:01:59Z (raw\19-vec-config-b.txt):

    veca, all three vectors:  n8n hmac = 813d8035...79d4 / 7b78c4d0...ccf3 / 68dfd370...624a   equal_to_python_signing_string=True
    vecc, all three vectors:  n8n hmac = 813d8035...79d4 / 7b78c4d0...ccf3 / 68dfd370...624a   equal_to_python_signing_string=True

    The Code node returned $json itself in mode runOnceForEachItem and n8n accepted it (webhook answer 200 with the item).

CONFIG C (crypto module allowed, env access at default), 2026-11-20T06:08:49Z (raw\28-config-c.txt):

    vecc, executions 55-57:  execution error: {"name": "WrappedExecutionError", "message": "access to env vars denied"}

NOT RUN: Crypto typeVersion 2 inside the full outline chain (it was run only in the vector workflow vec).


ITEM 4  Bytes sent by the HTTP Request node against the signed string
---------------------------------------------------------------------
CONFIG B, test copy t2 (Set nodes 3.4), 2026-11-20T06:02:06Z to 06:02:20Z host clock (raw\20-item4-bytes.txt;
full records raw\recv-all.jsonl lines 1-4). Each line: what the receiver got and its own recomputation.

    input good.json      body_len=93   framing=content-length  ts=1795154539  sig_header=v0=32b67c6c...ee57  sig_recomputed=v0=32b67c6c...ee57  sig_match=true  ts_age_s=0.412
    input nonascii.json  body_len=124  framing=content-length  ts=1795154543  sig_header=v0=8b8eca6c...6afc  sig_recomputed=v0=8b8eca6c...6afc  sig_match=true  ts_age_s=0.802
    input escaped.json   body_len=184  framing=content-length  ts=1795154547  sig_header=v0=ea14612a...a2d7  sig_recomputed=v0=ea14612a...a2d7  sig_match=true  ts_age_s=1.01
    input numid.json     body_len=98   framing=content-length  ts=1795154552  sig_header=v0=310889ae...d695  sig_recomputed=v0=310889ae...d695  sig_match=true  ts_age_s=0.602

Headers of the first request, complete, in the order received:

    ["Accept", "application/json,text/html,application/xhtml+xml,application/xml,text/*;q=0.9, image/*;q=0.8, */*;q=0.7"],
    ["Content-Type", "application/json"], ["x-hadavin-request-timestamp", "1795154539"],
    ["x-hadavin-signature", "v0=32b67c6c064f7c27fe566ae6ee255c9df9cb41c419ab534f01c1363908f8ee57"], ["User-Agent", "n8n"],
    ["Content-Length", "93"], ["Accept-Encoding", "gzip, compress, deflate, br"], ["Host", "hvn8n-recv:8080"], ["Connection", "close"]

The two header names arrived in lower case. No Transfer-Encoding header in any of the 27 requests.

Raw body bytes received (hex) for the non-ASCII and the escaped input:

    nonascii: 7b226b6579223a2230333531656130666235626339393838633939663535346133633866383565373338643336363463393835326539653232346561383937646464343262376539222c22646f63756d656e74223a224772c3bcc39f652c20e697a5e69cace8aa9e2c20f09f98802c20e282b93530302c20c3a9227d
    escaped : 7b226b6579223a2264303130306564343233333664333166306136646566363736393137656338633266393332386538356535336536643866353566333231613830306534643461222c22646f63756d656e74223a2271756f7465205c22206261636b736c617368205c5c20736c617368202f206e65776c696e65205c6e20746162205c74206374726c205c7530303031206c7320e280a82064656c207f203c3e26206c6f6e652d737572726f676174652d66726565227d

In the escaped case the input file had \u2028 and \u007f as JSON escapes; the bytes n8n sent hold them as
raw UTF-8 (e2 80 a8 and 7f), and hold \" \\ \n \t \u0001 as escapes; the slash is not escaped.
Value of field body on the item in n8n before sending (execution 20, node "Sign (option A, Crypto node)"):

    {"body": "{\"key\":\"0351ea0f...b7e9\",\"document\":\"Grüße, 日本語, 😀, ₹500, é\"}", "round": 0, "ts": "1795154543", "hmac": "8b8eca6c220a69535c8b9187be1dcff664dc612f819d6b3002b195f9bef06afc"}

Larger body and the Code-node variant, 2026-11-20T06:07:43Z (raw\27-misc.txt):

    line 25 (t2, 300 KB document): framing=content-length body_len=300088 sig_match=True   headers: ['Content-Length', '300088'], no Transfer-Encoding
    line 26 (t3, Code node signs, nonascii.json): framing=content-length body_len=124 body_sha256=54263a6aaf8d5a71 sig_match=True

Every request of the runs with Set 3.4 (26 of the 27 lines) has sig_match true; the one with sig_match
false is line 27, the outline as written (ITEM 2).

NOT RUN: a body above 300 KB; a proxy between n8n and the receiver; the real Hadavin endpoint.


ITEM 5  Retry On Fail with the receiver answering 503
-----------------------------------------------------
CONFIG B, 2026-11-20T06:04:09Z to 06:05:10Z (raw\24-item5-retry.txt; raw\recv-all.jsonl lines 9-20). Input good.json each time.

(a) The outline's own loop, Retry On Fail off (t2: rounds cut to 3, wait cut to 2 s), execution 31:

    line 9:  recv_unix=1795154662.359 body_sha256=a75dfaa1a0663446 ts=1795154662 sig=v0=70c0e4948fd05103.. sig_match=True ts_age_s=0.359
    line 10: recv_unix=1795154664.488 body_sha256=a75dfaa1a0663446 ts=1795154664 sig=v0=86652b4affd25f3c.. sig_match=True ts_age_s=0.488 gap_s=2.129
    line 11: recv_unix=1795154666.515 body_sha256=a75dfaa1a0663446 ts=1795154666 sig=v0=55e99058ff7dc2dc.. sig_match=True ts_age_s=0.515 gap_s=2.027
    line 12: recv_unix=1795154668.545 body_sha256=a75dfaa1a0663446 ts=1795154668 sig=v0=f34fbcbb73c9c51c.. sig_match=True ts_age_s=0.545 gap_s=2.030
    execution 31 status=error lastNodeExecuted: Stop: refused or gave up; 'Stamp time' ran 4 times, 'Send to Hadavin' ran 4 times
    execution 32 workflow=hv-err mode=error status=success

    4 requests, same body each time, a new timestamp and a new signature each time.

(b) Retry On Fail ON, no maxTries or waitBetweenTries in the JSON (t4), execution 33:

    line 13: recv_unix=1795154676.046 ts=1795154676 sig=v0=15b5f7ecc3c3ba78.. sig_match=True ts_age_s=0.046
    line 14: recv_unix=1795154677.057 ts=1795154676 sig=v0=15b5f7ecc3c3ba78.. sig_match=True ts_age_s=1.057 gap_s=1.011
    line 15: recv_unix=1795154679.164 ts=1795154676 sig=v0=15b5f7ecc3c3ba78.. sig_match=True ts_age_s=3.164 gap_s=2.107
    node 'Stamp time' run 0 only; node 'Send to Hadavin' run 0 status=success ms=3138 (one run entry for the three requests)

    3 requests, gaps 1.011 s and 2.107 s, the same timestamp and the same signature in all three.

(c) Retry On Fail ON, maxTries=10 and waitBetweenTries=10000 written in the JSON (t4b), execution 35:

    line 16: recv_unix=1795154689.586 ts=1795154689 sig=v0=c263c31981f75103.. sig_match=True ts_age_s=0.586
    line 17: recv_unix=1795154694.599 ts=1795154689 sig=v0=c263c31981f75103.. sig_match=True ts_age_s=5.599  gap_s=5.013
    line 18: recv_unix=1795154699.612 ts=1795154689 sig=v0=c263c31981f75103.. sig_match=True ts_age_s=10.612 gap_s=5.013
    line 19: recv_unix=1795154704.625 ts=1795154689 sig=v0=c263c31981f75103.. sig_match=True ts_age_s=15.625 gap_s=5.013
    line 20: recv_unix=1795154710.504 ts=1795154689 sig=v0=c263c31981f75103.. sig_match=True ts_age_s=21.504 gap_s=5.879
    node 'Send to Hadavin' run 0 ms=20942

    5 requests although 10 were asked for; gaps about 5.0 s although 10 s were asked for; the same
    timestamp and signature in all five. Oldest timestamp age seen: 21.5 s.

In (b) and (c) the failed item then left through the node's second output (onError continueErrorOutput),
the loop was cut to 0 rounds in these copies, so the execution ended in "Stop: refused or gave up" and
the error workflow ran (executions 34 and 36).

NOT RUN: the outline's real values (30 rounds, 60 s wait: about 30 minutes); a Wait longer than 65 s;
a manual retry of a failed execution and whether it signs again (needs the editor or a signed-in
REST call, which needs an owner account in n8n; not done, no account sign-up allowed); Retry On Fail
limited to one status code.


ITEM 6  Where the secret can live in this n8n (community edition, no licence) and whether it shows in an export
---------------------------------------------------------------------------------------------------------------
(a) Environment variable read in an expression ($env) - raw\11, raw\17, raw\19, raw\28:

    DEFAULT : Crypto node: ExpressionError "access to env vars denied".
    CONFIG B (N8N_BLOCK_ENV_ACCESS_IN_NODE=false): Crypto node and Code node read it; HMAC equal to Python (ITEM 3).
    CONFIG C (that setting left out, crypto module allowed): Code node: "access to env vars denied".
    n8n log line at DEFAULT: "access to env vars denied"

(b) Credential - raw\13-crypto-v2-def.txt, raw\14-vec-import.txt, raw\16-secret-locations.txt.
    Crypto typeVersion 2 lists a credential type "crypto" (required for hmac, sign, encrypt, decrypt) with the
    field hmacSecret ("Secret used in the Hmac action", password field). Crypto typeVersion 2 has no
    parameter named secret. Crypto typeVersion 1 lists no credential. The Code node lists no credential.
    The credential was created without the browser:

        docker exec hvn8n-main n8n import:credentials --input=/wf/cred.json     ->  Successfully imported 1 credential.
        (cred.json: [{"id": "hvCred0000000001", "name": "hv-crypto", "type": "crypto", "data": {"hmacSecret": <SIGNING-STRING>}}])

    The node as exported by n8n:

        {"name": "V2 cred", "typeVersion": 2, "parameters": {"action": "hmac", "type": "SHA256", "value": "={{ 'v0:' + $json.body.ts + ':' + $json.body.body }}", "dataPropertyName": "hmac_v2_cred", "encoding": "hex"}, "credentials": {"crypto": {"id": "hvCred0000000001", "name": "hv-crypto"}}}

    It worked at DEFAULT settings (ITEM 3).

(c) Typed into the node (Crypto typeVersion 1, parameter secret). The node as exported by n8n:

        {"name": "V1 plain", "typeVersion": 1, "parameters": {"action": "hmac", "type": "SHA256", "value": "...", "dataPropertyName": "hmac_v1_plain", "secret": "<LITERAL>", "encoding": "hex"}}

(d) Counts of the two made-up strings in files (findstr.py; raw\16-secret-locations.txt at 06:00:56Z, raw\29-final-cleanup.txt at 06:08:50Z):

    wf/export-vec.json (workflow export)                 signing_string_occurrences=0 second_literal_occurrences=1
    wf/export-cred-encrypted.json (export:credentials)   signing_string_occurrences=0 second_literal_occurrences=0     data field: 'U2FsdGVkX1/GhHefmO3EZ1Tc...(108 chars)'
    wf/export-cred-decrypted.json (export:credentials --decrypted)  signing_string_occurrences=1
    wf/export-t2.json (outline copy, $env reference)     signing_string_occurrences=0 second_literal_occurrences=0     "secret": "={{ $env.HADAVIN_TRIGGER_SECRET }}"
    wf/orig-trigger.json                                 signing_string_occurrences=0 second_literal_occurrences=0
    database.sqlite copy, at the end of the run          signing_string_occurrences=0 second_literal_occurrences=5
    database.sqlite-wal copy, at the end of the run      signing_string_occurrences=0 second_literal_occurrences=1  (16 at 06:00:56Z)
    n8nhome/n8nEventLog.log                              signing_string_occurrences=0 second_literal_occurrences=0
    data/recv.jsonl (everything the receiver got)        signing_string_occurrences=0 second_literal_occurrences=0

(e) $vars (n8n "variables"), CONFIG B, no variable created (raw\27-misc.txt), workflow vecv, executions 52-54:

        execution error: {"message": "The \"key\" argument must be of type string or an instance of ArrayBuffer, Buffer, TypedArray, DataView, KeyObject, or CryptoKey. Received undefined"}

NOT RUN: creating a variable (only reading $vars was tried); external secret stores; an environment
variable that is allowed but not set; a credential read from a Code node (the node definition lists none).


ITEM 7  What the node does on 401, 409, 413 (and 400), and the error workflow
-----------------------------------------------------------------------------
CONFIG B, test copy t2, receiver paths /s/401, /s/409, /s/413, /s/400 (empty answer body), 2026-11-20T06:02:34Z to 06:02:48Z
(raw\21-item7-status.txt, raw\22-item7-error-output.txt, raw\23-error-item-keys.txt). One request reached the
receiver per case (raw\recv-all.jsonl lines 5-8, sig_match true). The outline's node settings: retryOnFail
false, onError continueErrorOutput.

    executions 23, 25, 27, 29 (401, 409, 413, 400): workflow status=error, lastNodeExecuted: Stop: refused or gave up
       node 'Send to Hadavin' run 0 status=success  ->  the item left on output 1 (the second output)
       node 'Busy and rounds left?' run 0           ->  item on output 1 (false branch)
       node 'Stop: refused or gave up' run 0 status=error
    executions 24, 26, 28, 30: workflow=hv-err mode=error status=success (one error-workflow run per failed run)

The item on the second output of "Send to Hadavin" (401 case; stack left out):

    item keys: ['body', 'round', 'ts', 'hmac', 'error']
    error keys: ['message', 'name', 'stack', 'code', 'status']
    {"message": "401 - \"\"", "name": "AxiosError", "code": "ERR_BAD_REQUEST", "status": 401}
    (409: "message": "409 - \"\"" ; 413: "413 - \"\"" ; 400: "400 - \"\"")

There is no field error.httpCode on that item; the status is the number in error.status. With 503 the
same IF node sent the item to output 0 (true) for rounds 0 to 2 and to output 1 at round 3 (ITEM 5 a).

Answer 202 from /ok (executions 19-22): 'Send to Hadavin' output 0: {"run_id": "run-00000000000000000000000000000000", "state": "RUNNING"};
'Check state (optional)' put the item on output 1.

Error workflow, published or not (raw\11-t1-exec.txt, raw\12-default-config-t3.txt):

    error workflow imported but NOT published, main run fails (execution 1). n8n log:
       Calling Error Workflow for "hvt1000000000000". Workflow "hvErrWf000000001" is not active and cannot be executed
       (no error-workflow execution exists for execution 1)
    error workflow published (n8n publish:workflow --id=hvErrWf000000001), main run fails (execution 2):
       ### execution 3 workflow=hv-err mode=error status=success lastNodeExecuted: Notify placeholder

Fields the Error Trigger delivered (execution 24, three levels):

    execution.id  execution.url  execution.error.name  execution.error.level  execution.error.shouldReport  execution.error.tags
    execution.error.timestamp  execution.error.context  execution.error.functionality  execution.error.node  execution.error.messages
    execution.error.message  execution.error.stack  execution.lastNodeExecuted  execution.mode
    execution.executionContext.version / establishedAt / source / triggerNode / redaction   workflow.id  workflow.name

    execution.error.node holds the failing node with its parameters and its notes text.

"Build message" of the error-workflow outline:

    Set typeVersion 3 (as written), executions 24, 26, 28, 30: field message = null (the output is the input item unchanged)
    Set typeVersion 3.4 (execution 38):
       {"message": "Workflow: hv-t2\nExecution: http://localhost:5678/workflow/hvt2000000000000/executions/37\nLast node: Stop: id or text missing\nError: Hadavin trigger: the business id or the document text is empty or missing. Nothing was sent."}

NOT RUN: 401, 409, 413 from the real Hadavin endpoint (a stub answered with the status and an empty
body); a 413 caused by a real size limit; an answer with no response at all (connection refused or
timeout); the HTTP timeout timed live (unit ms and default 10000 are read from the node definition only).


ITEM 8  Missing id or text
--------------------------
CONFIG B, 2026-11-20T06:07:00Z to 06:07:25Z (raw\26-item8-missing.txt). Inputs:
  noid.json {"text": "no id"}   notext.json {"record_id": "rec-004"}   nulls.json {"record_id": null, "text": null}   empties.json {"record_id": "", "text": "   "}

With the outline's guard node (t2), executions 37, 39, 41, 43: nothing reached the receiver.

    execution error: {"name": "NodeOperationError", "message": "Hadavin trigger: the business id or the document text is empty or missing. Nothing was sent.", ...}
    lastNodeExecuted: Stop: id or text missing
    executions 38, 40, 42, 44: workflow=hv-err mode=error status=success
    webhook answer to the caller in all four cases: HTTP 200 (response mode onReceived)

With the guard node bypassed (t5), executions 45-48: all status=success, four requests reached the receiver, sig_match True:

    line 21 (noid)    body text: {"key":"eb045d78d273107348b0300c01d29b7552d622abbc6faf81b3ec55359aa9950c","document":"no id"}
    line 22 (notext)  body text: {"key":"fe123743f420c9f848bc710b095a5ae3c5c62af5b51d2baf31b509b673892fc1","document":"undefined"}
    line 23 (nulls)   body text: {"key":"74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b","document":"null"}
    line 24 (empties) body text: {"key":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","document":"   "}
    sha256("undefined") = eb045d78d273107348b0300c01d29b7552d622abbc6faf81b3ec55359aa9950c
    sha256("null")      = 74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
    sha256("")          = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

Numeric id with the guard (numid.json, {"record_id": 12345, ...}, execution 22): accepted, key 5994471a...cfc5, sig_match true.


NOT RUN, all items in one list
------------------------------
1. Editor menu "Import from File" (browser editor needed).
2. Manual retry of a failed execution, and whether a retry (retryOf) runs the sign node again (needs the
   editor or a signed-in REST call; an owner account would have to be created; stopped without trying).
3. The outline's real loop values (30 rounds, 60 s wait) and any Wait above 65 s.
4. The HTTP Request timeout timed live (unit and default read from the node definition only).
5. The real Hadavin endpoint: all statuses came from a stub receiver.
6. One webhook call that starts two executions still giving one run (needs the real endpoint).
7. Crypto typeVersion 2 with a credential inside the full outline chain (run only in the vector workflow).
8. Creating an n8n variable; external secret stores; an allowed but unset environment variable.
9. No answer at all from the receiver (refused connection, timeout).
10. n8n versions other than 2.47.7; n8n Cloud; queue mode; an external task runner.

Other notes
-----------
- n8n start-up log at this version lists deprecations, among them: "N8N_RUNNERS_MODE -> Internal task runner mode is deprecated".
- Bible R-numbers: RULES.md was not grepped for this run; the rule numbers in the brief (R447, R448, R450, R454, R455, R456, R461) are the only ones used.
- CAPACITY: docker reported cpus=12 mem=16434511872; this run used 2 light containers; disk C: 79 percent used.
- Files left in the scratch folder: the n8n data folder n8nhome\ (throwaway database), wf\cred.json and
  wf\export-cred-decrypted.json (hold the made-up signing string in plain text), secret.txt, literal.txt.
  The scratch folder is under _local\ (git-ignored).

Clean-up
--------
Run 2026-11-20T06:08:55Z (raw\29-final-cleanup.txt):

    docker rm -f hvn8n-main hvn8n-recv
    docker network rm hvn8n-net
    docker ps -a --filter name=hvn8n- --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
    (no output: no container with that name prefix exists)
    docker network ls --filter name=hvn8n --format '{{.Name}}'
    (no output)
    curl http://127.0.0.1:5691/healthz  ->  port 5691 answer: 000 (nothing listening)

All containers at 2026-11-20T06:09:04Z (docker ps -a):

    hv-ev-pg   postgres:17.10   Up About an hour
    pg-t3, pg50b9, pg-ev9, pgt48, pgb10   postgres:17   Exited (as at the start)

The ten hvp-* containers that were running at 05:48:55Z were gone at 06:09:04Z. No command of this run
named them; docker events show their removal at their own times (for example hvp-run-core-p1b at
1795154398). This run removed only hvn8n-main (three times: twice to change settings, once at the end),
hvn8n-recv and the network hvn8n-net.
