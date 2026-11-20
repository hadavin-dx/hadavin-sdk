# n8n trigger workflows for the Hadavin signed endpoint

**Status: an earlier version of these two files was run in n8n 2.47.7 by the lead (record of that run:
`handover/core-a/inputs/lead-evidence-n8n-1.md`). The files as they stand now were changed to follow what that run
showed, and they have NOT been imported or run in any n8n since. Nobody has run this exact version.**

What that means for a reader: the changes follow observed facts, but a file that nobody has imported can still hold a
mistake. Every node carries a `notes` field. A note that starts with `SEEN IN n8n 2.47.7:` describes a node that ran
exactly as it is written here. A note that holds `UNVERIFIED:` names what nobody has seen working. Do not give these
files to a client before the list at the end of this page is done.

## What was run and what was not

Run by the lead in n8n 2.47.7 (a throwaway container, a made-up signing value, a stub receiver in place of
Hadavin), in the order of the record:

1. The n8n version: image tag 2.47.7, no licence key (the free Community edition).
2. Import of both files by command line: accepted without any change to a node, parameter or connection. Two
   faults showed at run time and are fixed in the files now: the Set nodes (typeVersion 3 ignored their
   assignments; 3.4 builds the fields) and the webhook address (no `webhookId`, so `/webhook/<path>` answered 404).
3. The HMAC of the Crypto node against Python's: equal for plain, non-ASCII and JSON-escaped bodies.
4. The bytes sent by the HTTP Request node: equal to the bytes signed in 26 of 26 requests of the fixed version,
   one of them a 300 KB document; always with a `Content-Length` header, never in chunks.
5. A receiver that answers 503: the workflow's own loop (cut to 3 rounds and 2 seconds for the run) signed again
   with a new timestamp in every round and ended in the error workflow; n8n's own Retry On Fail was measured.
6. Where the signing value can live and whether it shows up in an export.
7. Answers 401, 409, 413 and 400: where the status is found, and that the error workflow runs only when published.
8. A missing, null, empty or spaces-only id or text: the guard stopped all of them and nothing was sent.

NOT run by anybody (each is also in the list at the end):

- These two files as they stand now.
- The Crypto node of typeVersion 2 with a credential INSIDE the full chain (it was run in a small test workflow).
- The two "Answer caller" nodes and the webhook response mode they need (added after the run).
- A manual retry of a failed execution from the n8n editor.
- The real loop values: 30 rounds with 60 second waits.
- The real Hadavin endpoint (a stub answered).
- One webhook call that starts two executions.
- n8n Cloud and queue mode.
- n8n versions other than 2.47.7.
- The editor menu for importing a file and the HTTP Request timeout timed live.
- A receiver that answers 502 or 504, and a receiver that gives no answer (refused connection, timeout, reset).
  The loop now treats all of these as "busy"; only 503 was run.

Words used here: a "run" is one piece of work Hadavin does for one event. The "worker" is the Hadavin process that
receives the signed request and does the run. The "tick" is a second, scheduled Hadavin job that looks for runs that
stopped moving. The "sender" is the n8n side: one sender has one id and one secret in Hadavin's configuration. An
"execution" is one pass of an n8n workflow. A "credential" is n8n's own encrypted store for a secret.

## What the two workflows do

- `hadavin-trigger.json` (main): something happens in the client's n8n (a web call, a mail, a schedule). The workflow
  first checks that the business id and the document text are there, then builds one text (the "body") with a
  request key and a document, signs it with a shared secret, and sends it to Hadavin. Hadavin starts at most one run
  per key and answers with a run id and a state. When Hadavin does not acknowledge the request (an answer 502, 503
  or 504, or no answer at all), the workflow waits, signs the same body again with a new timestamp, and sends
  again, for a fixed number of rounds.
- `hadavin-trigger-error.json` (error workflow): when the main workflow fails, n8n starts this one, but only if it
  is published. It builds a short message (workflow name, execution link, last node, error text) for a chat or
  e-mail node that you add.

## Set-up

Every step is required.

1. Create the credential that holds the trigger secret (see "Where the secret lives").
2. In `hadavin-trigger.json`, replace the `webhookId` of "Trigger placeholder" with a fresh UUID (see "The webhook
   address").
3. Import both files. In the lead's run this was done by command line: `n8n import:workflow --input=<file>`, once
   for each file. The editor's menu for importing a file was not run (UNVERIFIED).
4. In the error workflow, replace "Notify placeholder" with your chat or e-mail node.
5. The error workflow must be PUBLISHED (active). An error workflow that is only imported does nothing: in the
   lead's run n8n logged that it "is not active and cannot be executed", the main workflow failed, and nobody was
   told. In the run it was published by command line (`n8n publish:workflow --id=<id of the error workflow>`) and
   n8n was started again afterwards.
6. In the main workflow, in Workflow Settings, choose the error workflow (the JSON holds a placeholder id).
7. In the main workflow, open the node "Sign" and choose the credential from step 1 (the JSON holds a placeholder
   id and name).
8. In the main workflow: replace "Trigger placeholder" with your own trigger if it is not a web call (then also
   delete the two "Answer caller" nodes and connect the guard's second output straight to "Stop: id or text
   missing"); put your own fields for the business id and the document in THREE nodes: "Id and text present?",
   "Hash business id" and "Build request"; in "Send to Hadavin" replace `https://example.invalid/v1/trigger` with
   the real address.
9. Set the two loop numbers for this client: the wait in "Wait before next round" and the number of rounds in "Busy
   and rounds left?" (see "One run at a time" below).
10. Publish the main workflow, send one made-up event, and check that Hadavin answered and that a failed
    execution reaches your chat or e-mail node.

Do not change the `typeVersion` of the Set nodes ("Build request", "Stamp time", "Next round", and "Build message"
in the error workflow). It is 3.4. With typeVersion 3, n8n 2.47.7 ignored the fields these nodes are meant to build
and reported no error: the request went out with the caller's own data, no timestamp header and a useless
signature, and n8n marked the execution as a success.

## The webhook address

The address a caller uses is `<address of your n8n>/webhook/<path>`, where `<path>` is the `path` of "Trigger
placeholder". This address only works when the webhook node has a `webhookId`. In the lead's run the node had none:
n8n then registered the address as `<workflow id>/<node name>/<path>`, and `/webhook/<path>` answered 404 "not
registered". Test workflows whose webhook node had a `webhookId` answered on `/webhook/<path>`.

The `webhookId` in the file, `00000000-0000-4000-8000-000000000000`, is a made-up placeholder. Give every
installation its own: before the import, replace it in the JSON with a fresh UUID (for example the output of
`python3 -c "import uuid; print(uuid.uuid4())"`). UNVERIFIED: which forms of value n8n accepts here, and what
happens when two workflows hold the same value; the run only shows that a node with a `webhookId` got the short
address.

## The guard: no id or no text means no request

"Id and text present?" comes before anything is hashed or signed, and it is a required node. If the business id or
the document text is missing, null, empty or only spaces, the execution FAILS at "Stop: id or text missing" and the
error workflow tells a person. Nothing is sent. This was seen in the lead's run for all four cases.

Why it is required: with the guard taken out of the chain, the run sent a missing id as the hash of the text
"undefined" and a null id as the hash of the text "null". Every such event would get the same key, and Hadavin would
treat them all as one event (the first runs, the rest are answered 409 or silently taken as repeats).

### What the caller of the webhook is told

In the lead's run the caller got HTTP 200 from n8n although the guard had stopped the event and nothing was sent.
To change that, two nodes were added AFTER the run, and the webhook node's response mode was changed to the one they
need (`responseNode`):

- "Answer caller: refused", on the guard's stop branch: answers the caller with 422 and an empty body; then the
  execution fails as before.
- "Answer caller: taken", beside the first node of the sending chain: answers the caller with 202 and an empty
  body. This 202 means only that n8n took the event and will try to send it. It does NOT mean that Hadavin
  accepted it; a later refusal reaches a person through the error workflow, not the caller.

This branch was NOT run in n8n. UNVERIFIED: both nodes (type name, version and parameter names were written from
memory of the n8n documentation), the response mode value, that the stop node still runs after the answer node, and
that n8n answers the caller before it starts the long sending chain (if it does not, the caller waits until the
whole execution ends). Until somebody has run it, do not rely on the status the caller gets.

## Where the secret lives

No secret value is in these files and none may ever be saved in them. Our general rule is that secrets stay out of
n8n; this one secret is the deliberate exception, because n8n must sign the request. The same value is stored on
the Hadavin side under the sender's secret name.

The template has ONE way: the node "Sign" is a Crypto node of typeVersion 2, and it takes the secret from an n8n
credential of the type `crypto`. The node has no field for the secret. In the lead's run, on default n8n settings,
this gave the same HMAC as Python, and the made-up signing value was found 0 times in the workflow export, 0 times
in n8n's database files and 0 times in the normal credential export (which holds it encrypted).

How to create the credential:

- In the editor: create a new credential of the type for the Crypto node and fill its field for the HMAC secret
  (described by n8n as "Secret used in the Hmac action"). UNVERIFIED: the editor path was not run.
- Without a browser, as it was done in the run: write a file with this content, with your own id and name and the
  secret in place of the placeholder words,

      [{"id": "<AN-ID-YOU-CHOOSE>", "name": "<A-NAME-YOU-CHOOSE>", "type": "crypto",
        "data": {"hmacSecret": "<THE-TRIGGER-SECRET>"}}]

  then run `n8n import:credentials --input=<that file>`, and DELETE the file: it holds the secret as plain text.
  Never keep it in a repository, a ticket or a chat.
- `n8n export:credentials --decrypted` prints the secret as plain text (seen in the run). Do not run it into a file
  that stays.

Ways the template does NOT use:

- Typing the secret into a node. A Crypto node of typeVersion 1 has a field for it. In the run a value typed there
  came back as plain text in the workflow export and was found in n8n's database files. Never do this.
- Reading an environment variable of the n8n server in an expression (`$env`). On default settings n8n 2.47.7
  refuses it with "access to env vars denied". It worked in the run only on an n8n started with two non-default
  settings: `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` and `NODE_FUNCTION_ALLOW_BUILTIN=crypto`. (The second one is what
  a Code node needs; a Crypto node with only the first setting was not run on its own.) It also needs a Crypto node
  of typeVersion 1, because typeVersion 2 has no field for a secret.
- Signing in a Code node. On default settings n8n refuses it: "Module 'crypto' is disallowed". With only the
  crypto module allowed, the Code node was still refused the environment variable. The Code node's definition
  lists no credential, so it cannot take the secret from one.
- n8n variables (`$vars`): reading one that does not exist gave no key at all; creating one was not run.

Rules for the value:

- At least 32 characters; the worker refuses to start with a shorter one.
- Not shared with any other sender; the worker refuses to start when two senders hold the same value.
- NEVER the same value as the approvals secret (the secret that signs approve and reject clicks). Both use the same
  signing recipe, and the header names are not part of the signed text. Whoever holds a trigger secret that equals
  the approvals secret could forge an approval click. Nothing in the code read for this file compares the two
  values, so this rule is kept by the people who create the secrets.
- No space or line break at the start or end. A secret file that ends with a line break gives a different value
  than the one stored in n8n, and then every request is answered 401.
- To change a secret without a gap, a sender may have two secrets for a short time: the old and the new. Configure
  no more than two, and remove the old one when the swap is done.

## The signing recipe

1. `body` = `JSON.stringify({key, document})`: one text, with exactly these two fields, both text.
2. `ts` = the current time in whole Unix seconds, as digits (at most 12 digits).
3. `signature` = `"v0="` + HMAC-SHA256(secret, `"v0:" + ts + ":" + body`) written as lowercase hex.
4. Send `POST /v1/trigger` with the raw `body` text, byte for byte as it was signed, and two headers:
   `X-Hadavin-Request-Timestamp: <ts>` and `X-Hadavin-Signature: <signature>`.

A request whose timestamp is more than 300 seconds away from the server's clock (older or newer) is refused with
401. Do not count on the exact edge: treat a signature as good for a little under 300 seconds. If the clocks of the
n8n host and the Hadavin host differ by more than 300 seconds, every request is refused until the clocks are fixed.
A signature can therefore not be reused for a later round: each round needs a new `ts` and a new signature. The
`body` stays the same in every round.

## The key rule

`key` is the SHA-256 hash (64 hex characters) of a stable business id: the Message-ID of a mail, or a record id plus
the event name. NEVER use the n8n execution id: n8n may fire twice for one event, and each firing has a new
execution id, so Hadavin would start two runs. Send the hash, not the raw id: Hadavin stores the key where portal
users can read it, so it must not be personal data, and only letters, digits and `. _ : -` (1 to 128 characters)
are accepted. Same key and same document always give the same run. The same key with a different document is
refused (409).

## What the template does on each answer

| Answer | What it means | What the template does |
|---|---|---|
| 202 or 200 | Hadavin holds a run for this key. 202: its state is RECEIVED or WORKING (first time or a repeat). 200: its state is anything else; this does NOT mean the run has ended (see below). Body: `run_id`, `state`. Nothing runs twice. | Goes on to "Check state (optional)". No retry. |
| 400 | The body is not the two-field JSON, the key has a character that is not allowed, or the Content-Length header is missing or wrong. Empty body. | STOP: no retry, straight to the error workflow. Fix "Build request". |
| 401 | Signature wrong, header missing, secret unknown, or timestamp more than 300 s off. Empty body. | STOP: no retry, straight to the error workflow. Check the secret and both clocks. |
| 409 | The key was already used with a different document. Empty body. | STOP: no retry, straight to the error workflow. A person must look. |
| 413 | The body is larger than the limit (see "Size limits"). Empty body. | STOP: no retry, straight to the error workflow. Send a shorter document. |
| 502, 503 or 504 | 503 comes from the worker (it is busy with another run, it is shutting down, or its database cannot be reached) and means: not acknowledged; send again with the same key; it may already be running. 502 and 504 come from the reverse proxy when the worker behind it is restarting, draining or not answering in time; the template treats them the same way. | BUSY: waits, then sends the same body with the SAME key, a NEW timestamp and a NEW signature. At most 30 rounds (a placeholder); then the error workflow. |
| no answer | No HTTP status at all: the connection was refused, timed out or was reset. This is what a sender without a proxy sees while the worker is stopped or restarting. | BUSY, exactly as for 502, 503 and 504. |

Any other status is a STOP as well: every other 4xx, and also 404 (the path is not `/v1/trigger`), 405 (the method
is not POST), 414 and 431 (the request line or the headers are too long). All have an empty body; none is tried
again.

UNVERIFIED: the "no answer" row and the 502 and 504 part of the row above it. The lead's run had a stub that
answered 503, 401, 409, 413 and 400, and nothing else. What n8n puts on the failed item when there is no HTTP
answer is NOT known. The condition in "Busy and rounds left?" assumes that the field `error.status` is then missing
or is not a three-digit HTTP status, and counts exactly that as busy. The lead runs one more n8n evidence step for
this case; until then do not rely on it.

Two things follow from "no answer counts as busy", and both are meant:

- A wrong address, a host name that does not resolve, or a TLS fault also gives no HTTP status. The template then
  tries for all its rounds (about 30 minutes with the placeholders) before a person is told. Send one made-up
  event after every change of the address (set-up step 10).
- When the worker refuses a request without reading its body (see "Stated limits"), n8n can see a broken
  connection in place of the 413, 400 or 401. That, too, is then tried again for all rounds before it stops.

### A restart of the worker must not land events in the error workflow

Restarting the worker is a routine act (a new version, a changed setting). On the stop signal (SIGTERM) the worker
drains: it closes its port at once, starts no new run, lets the run that is going reach its end, and only then
exits. A run can last minutes, and the process supervisor normally starts the new worker only after the old one
has exited. So for minutes there may be nothing that listens on the port.

An event that arrives in that time gets, depending on what stands in front of the worker: 502 or 504 from the
reverse proxy, a refused connection or a timeout with no proxy, or 503 from a request that was already inside the
worker. None of these means that the event is bad. If the template stopped on them, every event that arrives
during a restart would end with a person who has to send it again by hand. So all of them count as busy: the
template waits and sends again until the new worker answers. Trying again is safe by design: the key stays the
same, so Hadavin starts at most one run for it, and each round has its own timestamp and signature.

### 200 does not mean "ended"

The answer holds only `run_id` and `state`. A 200 can carry any of these states:

- still open, more will happen: PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING, VERIFYING.
- nothing more will happen on its own: NO_ACTION, NEEDS_PERSON, DENIED, REJECTED, EXPIRED, SUCCEEDED, ROLLED_BACK,
  STOPPED.

To learn how a run went, send the same request again later (same key, same document, new signature) and read the
state. The answer never holds a reason and never holds the result of the run.

## One run at a time: what the sender must do when it is not acknowledged

In plain words: with the default setting the worker handles ONE run at a time.

- The setting is `max_running`, and its default is 1. It stays 1 until Hadavin can reserve spend before a model
  call; until then two runs side by side could together go over a spending limit.
- A second event that arrives while a run is going is not queued. The worker holds the request for up to
  `ack_wait_s` (default 5 seconds), in case the first run ends in that time, and then answers 503.
- What 503 means: not acknowledged; send again with the same key; it may already be running. (In most cases
  nothing was stored. But a request that gets the free slot just before its wait is over can be answered 503
  although its run has started. The next send with the same key then finds that run and is answered 202 or 200.)
- A run can last minutes. How long depends on the agent's step limit and the model's timeouts.
- So the sender must keep trying over a span that is LONGER than its longest run, and must sign again for every
  try, because a signature stops being valid 300 seconds after its timestamp. The same holds for 502, 504 and no
  answer (see the table above).

The main workflow does this with a loop: "Busy and rounds left?" then "Next round" then "Wait before next round"
then back to "Stamp time" and the sign node. The outline holds placeholders: a wait of 60 seconds and 30 rounds,
about 30 minutes in total. Nobody has measured a run for this file; set both numbers for each client so that
rounds times wait is longer than that client's longest run. If events arrive faster than runs finish, the waiting
executions pile up in n8n and some will use up their rounds; this setup is for a low event rate.

What the lead's run showed for the loop, cut to 3 rounds and a 2 second wait: 4 requests reached the receiver,
about 2 seconds apart, each with the same body, a new timestamp and a new signature that the receiver found
correct; then the execution failed at "Stop: refused or gave up" and the error workflow ran. The real numbers (30
rounds, 60 seconds) were not run.

The loop finds the status of a failed send in the field `error.status` of the item that leaves the HTTP node's
second output (seen for 401, 409, 413, 400 and 503). There is no field `error.httpCode`. A send with no HTTP answer
is expected to have no status there (UNVERIFIED, see the table above).

When the workflow gives up (30 rounds, each answered 502, 503 or 504 or not answered at all), the execution fails
at "Stop: refused or gave up" and the error workflow tells a person. For that event the rule is the same as for a
single 503: not acknowledged; send again with the same key; it may already be running. The person sends it again
later with the SAME key: if a run exists by then, the answer is 202 or 200 with its state, and nothing runs twice.
Whether n8n's own "retry execution" signs again was not run (see the list at the end); until that is checked,
start the workflow anew.

### Why n8n's own Retry On Fail stays off

The HTTP node has a switch "Retry On Fail". It is OFF in this workflow and must stay off for the 503 case (and for
502, 504 and no answer, which take the same way). What the
lead's run measured with a receiver that always answers 503:

- Switched on with nothing else set: 3 requests, about 1 and 2 seconds apart.
- Switched on with 10 tries and a 10 second wait written in the JSON: n8n sent 5 requests, about 5 seconds apart.
  So the number of tries is capped at 5 and the wait is capped at about 5 seconds, whatever the JSON says.
- Every retry reused the same timestamp and the same signature. Only the first request was signed.

In plain words: Retry On Fail gives up after about 20 seconds at the most, and a run can last minutes. It can never
outlast a run. Only the loop above can, because it waits as long as you set it and signs again in every round.

## When a run shows NEEDS_PERSON after a restart or a crash

If the worker process stops or crashes during a run, that run is not continued when the worker starts again. The
document was only in the worker's memory. Later the tick finds the run that stopped moving and sets its state to
NEEDS_PERSON with the reason "interrupted" (or "outcome_unknown" if it stopped while carrying out an action, or
"verify_interrupted" if it stopped while checking the result). This only happens if the tick runs in the same
deployment. The worker looks once, when it starts, for a good tick of the last 600 seconds; if it finds none it
writes one warning and starts all the same. After the start it does not look again.

A restart that drains (see "A restart of the worker must not land events in the error workflow") does not cut a
run off, as long as the supervisor waits long enough; stated limit 11 says what happens when it does not.

What the client sees and does:

- The same key now answers 200 with state NEEDS_PERSON, every time, forever. The run is never started again
  automatically, and sending the same key again does nothing.
- The answer does not hold the reason. NEEDS_PERSON has many possible reasons (for example a document that is too
  large); "interrupted" is only one of them. The reason is in Hadavin's stored run and in its audit record.
- A person decides what to do. If the event should be worked on again, it must be sent with a NEW key (for example
  the hash of the business id plus a suffix such as `:rerun-1`). A new key is a new run from the start. If the
  reason is "outcome_unknown", an action may already have been carried out: a person checks the target system
  before any re-run.
- Who is told: as far as the code read for this file shows, the tick changes the stored state and writes an audit
  record; it does not post a chat card at that moment. (A run that ends in NEEDS_PERSON by itself, without a
  crash, does post a card for people when a chat channel is set up.) So do not count on a card for an interrupted
  run: watch for NEEDS_PERSON from the n8n side with "Check state (optional)", or look at the stored runs.

## Size limits

- The whole request body may be at most `max_body_bytes` bytes; a larger one is answered 413 without being read.
  The endpoint code has no built-in number for this: it takes the value from the `triggers` block of the
  configuration, and that block is not in the configuration code yet. The value proposed for it is 524288 bytes
  (two times the document limit), with 2097152 as the highest allowed setting.
- The document itself may be at most 262144 bytes as UTF-8 text (`MAX_DOCUMENT_BYTES`). A longer document that
  fits in the body is accepted by the endpoint and the run then stops in NEEDS_PERSON. One test sends such a
  document through the endpoint; it needs a PostgreSQL test database and is skipped without one.
- JSON escaping makes a document larger on the wire. A quote or a backslash takes 2 bytes, a line break 2 bytes, and
  other control characters 6 bytes each. A document made mostly of such characters can be up to six times its own
  size in the body, so a document under the document limit can still be answered 413.

## Stated limits

These are known limits of this version. They are written down so that nobody assumes more.

1. The worker's built-in web server is simple. It starts one thread for every connection and has no cap on
   connections; a client that sends very slowly holds a thread; each connection can hold up to `max_body_bytes` in
   memory; and before a request is refused for a bad signature the worker computes up to 16 signatures over the
   whole body (up to 8 senders with 2 secrets each). So the worker listens only on the local machine by default,
   and the client's reverse proxy in front of it MUST: read the whole request before passing it on (request
   buffering), cap the number of connections and the request size, and end TLS (the worker speaks plain HTTP
   only). Setting `allow_non_loopback` exposes the worker without this protection; do not use it without such a
   proxy.
2. Listen on `127.0.0.1` or `localhost`. The IPv6 local address `::1` is not supported by the built-in server.
3. When the worker refuses a request without reading its body (413, and some 400 and 401 cases), the connection
   may be closed while the sender is still sending. The sender can then see a broken connection instead of the
   status code. On a real connection only one such case is tested (the 400 for a missing Content-Length, and that
   test accepts a reset connection); a 413 or a 401 with a large unread body is not. In the main workflow a broken
   connection has no HTTP status, so it counts as busy: it is tried again for all rounds and only then ends in the
   error workflow.
4. n8n must send a `Content-Length` header. A request sent in chunks without one is answered 400. In the lead's
   run n8n 2.47.7 sent the header in every request, up to a 300 KB document, with no proxy in between.
5. Renaming is not free. The run id is computed from the tenant id, the sender id and the key. If the tenant id or
   a sender id is renamed, every old key gives a NEW run id, so an event that was already handled would run again
   when it is sent again. If a sender's agent or principal is changed, every old key of that sender is answered
   409. Do neither on a deployment that has handled events, unless a person has decided what happens to old keys.
6. A document may contain the NUL character (written `\u0000` in JSON); the endpoint accepts it, and tests pin
   what happens today: the run ends like the same document without the NUL, because the redaction step removes
   every NUL first, and no document text is written to the database. Two things to know: a document with a NUL and
   the same document without it are two different documents (with one key the second is answered 409), and other
   control characters are not removed. Removing NUL characters before sending stays the simple way.
7. Until the `triggers` block exists in the configuration code, the worker uses fallback numbers written in its
   own code (address `127.0.0.1`, port 8081, `max_running` 1, `ack_wait_s` 5). A misspelled setting name is not
   reported; the fallback is used silently. Check the worker's start line for the port it serves on.
8. The tick must run next to the worker. Without it, a run that was cut off stays in its last state and never
   reaches a person. The worker warns once at its start when it finds no recent tick, and starts anyway.
9. Run rows are kept. A key that was used once stays used; there is no way to free a key through this endpoint.
10. A cap on connections and a deadline per request are the reverse proxy's job. The worker has neither. Its only
    time limit is per read: a client that sends one byte just inside each time limit keeps its thread for as long
    as it likes, and every open connection can hold up to `max_body_bytes` in memory before any signature is
    checked. This is one more reason for limit 1: the proxy in front must cap the connections and end a request
    that takes too long as a whole.
11. Set the process supervisor's stop grace period LONGER than the longest run, or runs in flight at a restart end
    with a person. On the stop signal (SIGTERM) the worker closes its port, starts no new run, and lets the run
    that is going reach its end; it does not cut a run, not even in the middle of a model call. If the supervisor
    kills the process before that (Docker, for example, waits 10 seconds unless told otherwise), the run is cut
    off: the tick later sets it to NEEDS_PERSON with the reason "interrupted", and its key is used up (see "When a
    run shows NEEDS_PERSON after a restart or a crash"). As the code reads, a second stop signal does nothing
    while the worker waits for its runs (up to 30 seconds) and kills the process after that. Not tested: a request
    that waits for a free slot when the signal comes, a request that arrives between the signal and the closing of
    the port, and a second signal.
12. There is no fairness among waiting requests: a later request can be served before an earlier one. A request
    that has just arrived tries for the free slot at once; one that is already waiting looks only about once a
    second. With a steady flow of events an early event can lose every round and end in the error workflow while
    later ones run. No request is ever acknowledged without a stored run. This setup is for a low event rate.

## VERIFY ON A REAL n8n BEFORE ANY CLIENT USE

Nobody has run any of these. The record of what WAS run is `handover/core-a/inputs/lead-evidence-n8n-1.md`.

1. NOT VERIFIED: these two files as they stand now import without error and run from the trigger to the answer
   (they were changed after the run and not imported again).
2. NOT VERIFIED: the Crypto node of typeVersion 2 with the credential inside the full chain: it keeps the
   timestamp, the body and the round counter on the item, and the receiver finds the signature correct.
3. NOT VERIFIED: what the import does with the placeholder credential id, and creating the credential in the editor.
4. NOT VERIFIED: the two "Answer caller" nodes: the caller gets 422 when the guard stops the event and 202 when it
   passes, the stop node still fails the execution, and the caller is answered before the sending chain starts.
5. NOT VERIFIED: the placeholder `webhookId` and a fresh UUID in its place both give the address `/webhook/<path>`.
6. NOT VERIFIED: the status check as it is written now (it reads `error.status` only, counts 502, 503 and 504 as
   busy, and counts a missing status as busy).
7. NOT VERIFIED: whether a manual retry from the editor, or a `retryOf` retry, runs the sign node again (if not,
   a retry later than 300 s gets 401).
8. NOT VERIFIED: the real loop values, 30 rounds with 60 second waits, and any wait above 65 seconds.
9. NOT VERIFIED: the real Hadavin endpoint: every status in the run came from a stub that answered with an empty
   body.
10. NOT VERIFIED: one webhook call that starts two executions still yields one run when the key is stable.
11. NOT VERIFIED: n8n Cloud, queue mode, and an external task runner.
12. NOT VERIFIED: n8n versions other than 2.47.7. Pin the version that was tested.
13. NOT VERIFIED: the HTTP Request timeout timed live (its unit, milliseconds, and its default, 10000, were read
    from the node's definition only).
14. NOT VERIFIED: a receiver that gives no answer at all (refused connection, timeout, reset): what the failed
    item holds, that it leaves through the HTTP node's second output, and that the loop counts it as busy. The
    lead runs one more n8n evidence step for this.
15. NOT VERIFIED: the editor menu for importing a file.
16. NOT VERIFIED: a body larger than 300 KB, and a proxy between n8n and the receiver.
17. NOT VERIFIED: the endpoint secret is written down, for each client, as the one exception to "secrets stay
    out of n8n".
18. NOT VERIFIED: an answer 502 or 504 goes the busy way (the run had only 503), and a restart of the real worker
    under load: events sent during the drain are taken by the new worker and none reaches the error workflow.
