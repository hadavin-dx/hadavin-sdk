# n8n trigger workflows for the Hadavin signed endpoint

**Outline, not run in n8n.** The two JSON files here were written from notes about n8n, not exported from a
running n8n. Every node carries a `notes` field; a note that starts with `UNVERIFIED:` names what nobody has checked.
Do not give these files to a client before the list at the end is done.

Words used here: a "run" is one piece of work Hadavin does for one event. The "worker" is the Hadavin process that
receives the signed request and does the run. The "tick" is a second, scheduled Hadavin job that looks for runs that
stopped moving. The "sender" is the n8n side: one sender has one id and one secret in Hadavin's configuration.

## What the two workflows do

- `hadavin-trigger.json` (main): something happens in the client's n8n (a web call, a mail, a schedule). The workflow
  first checks that the business id and the document text are there, then builds one text (the "body") with a
  request key and a document, signs it with a shared secret, and sends it to Hadavin. Hadavin starts at most one run
  per key and answers with a run id and a state. When Hadavin answers "busy" (503), the workflow waits, signs the
  same body again with a new timestamp, and sends again, for a fixed number of rounds.
- `hadavin-trigger-error.json` (error workflow): when the main workflow fails, n8n starts this one. It builds a short
  message (workflow name, execution link, last node, error text) for a chat or e-mail node that you add.

## How to import

1. In n8n, create a new workflow and choose "Import from File" for each of the two files (menu wording UNVERIFIED).
2. In the error workflow, replace "Notify placeholder" with your chat or e-mail node, and publish it (the n8n
   documentation says an error workflow must be published; not seen on a real n8n).
3. In the main workflow: replace "Trigger placeholder" with your own trigger; put your own fields for the business
   id and the document in THREE nodes: "Id and text present?", "Hash business id" and "Build request"; in "Send to
   Hadavin" replace `https://example.invalid/v1/trigger` with the real address; in Workflow Settings choose the
   error workflow (the JSON holds a placeholder id).
4. Choose ONE sign node: option A (Crypto node, connected) or option B (Code node, disabled). Delete the other.
5. Set the two loop numbers for this client: the wait in "Wait before next round" and the number of rounds in "Busy
   and rounds left?" (see "One run at a time" below).

## The guard: no id or no text means no request

"Id and text present?" comes before anything is hashed or signed. If the business id or the document text is
missing, null or empty, the execution FAILS at "Stop: id or text missing" and the error workflow tells a person.
Nothing is sent. Why: n8n would otherwise turn a missing field into the text "undefined", every such event would get
the same key, and Hadavin would treat them all as one event (the first runs, the rest are answered 409 or silently
taken as repeats).

## Where the secret lives

No secret value is in these files and none may ever be saved in them. Both sign nodes read
`$env.HADAVIN_TRIGGER_SECRET`, an environment variable of the n8n server (whether your n8n allows this is
UNVERIFIED; the free Community edition has no custom variables). Where the edition allows it, keep the secret in an
n8n credential instead (UNVERIFIED). Our general rule is that secrets stay out of n8n; this one secret is the
deliberate exception, because n8n must sign the request. The same value is stored on the Hadavin side under
the sender's secret name. Rules for the value:

- At least 32 characters; the worker refuses to start with a shorter one.
- Not shared with any other sender; the worker refuses to start when two senders hold the same value.
- NEVER the same value as the approvals secret (the secret that signs approve and reject clicks). Both use the same
  signing recipe, and the header names are not part of the signed text. Whoever holds a trigger secret that equals
  the approvals secret could forge an approval click. Nothing in the code read for this file compares the two
  values, so this rule is kept by the people who create the secrets.
- No space or line break at the start or end. A secret file that ends with a line break gives a different value
  than the one typed into n8n, and then every request is answered 401.
- If the secret is typed into the Crypto node instead of being read from the environment, it sits as plain text in
  the workflow JSON: never export, mail or commit such a file.
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

## Response codes and what the main workflow does

| Code | Meaning | What the main workflow does |
|---|---|---|
| 202 | Accepted. The run exists and its state is RECEIVED or WORKING (first time or a repeat). Body: `run_id`, `state`. | Goes on to "Check state (optional)". |
| 200 | The run for this key exists and its state is anything other than RECEIVED and WORKING. This does NOT mean the run has ended (see below). Body: `run_id`, `state`. Nothing runs twice. | Goes on to "Check state (optional)". |
| 401 | Signature wrong, header missing, secret unknown, or timestamp more than 300 s off. Empty body. | Stops with an error; the error workflow runs. Check the secret and both clocks. |
| 409 | The key was already used with a different document. Empty body. | Stops with an error; the error workflow runs. A person must look; do not retry. |
| 400 | The body is not the two-field JSON, the key has a character that is not allowed, or the Content-Length header is missing or wrong. Empty body. | Stops with an error; the error workflow runs. Fix "Build request". |
| 413 | The body is larger than the limit (see "Size limits"). Empty body. | Stops with an error; the error workflow runs. Send a shorter document. |
| 503 | Hadavin is busy with another run, or its database cannot be reached. Nothing was accepted. Empty body. | Waits, signs again with a new timestamp, sends again; after the last round it stops with an error and the error workflow runs. |

Also: 404 means the path is not `/v1/trigger`; 405 means the method is not POST; 414 and 431 mean the request line
or the headers are too long. All have an empty body and all stop the workflow with an error.

### 200 does not mean "ended"

The answer holds only `run_id` and `state`. A 200 can carry any of these states:

- still open, more will happen: PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING, VERIFYING.
- nothing more will happen on its own: NO_ACTION, NEEDS_PERSON, DENIED, REJECTED, EXPIRED, SUCCEEDED, ROLLED_BACK,
  STOPPED.

To learn how a run went, send the same request again later (same key, same document, new signature) and read the
state. The answer never holds a reason and never holds the result of the run.

## One run at a time: what the sender must do with 503

In plain words: with the default setting the worker handles ONE run at a time.

- The setting is `max_running`, and its default is 1. It stays 1 until Hadavin can reserve spend before a model
  call; until then two runs side by side could together go over a spending limit.
- A second event that arrives while a run is going is not queued. The worker holds the request for up to
  `ack_wait_s` (default 5 seconds), in case the first run ends in that time, and then answers 503. Nothing is stored
  for that second event.
- A run can last minutes. How long depends on the agent's step limit and the model's timeouts.
- So the sender must keep trying a 503 over a span that is LONGER than its longest run, and must sign again for
  every try, because a signature stops being valid 300 seconds after its timestamp.

The main workflow does this with a loop: "Busy and rounds left?" then "Next round" then "Wait before next round"
then back to "Stamp time" and the sign node. The outline holds placeholders: a wait of 60 seconds and 30 rounds,
about 30 minutes in total. Nobody has measured a run for this file; set both numbers for each client so that
rounds times wait is longer than that client's longest run. If events arrive faster than runs finish, the waiting
executions pile up in n8n and some will use up their rounds; this setup is for a low event rate.

When the workflow gives up (30 rounds answered 503, or no answer at all), the execution fails at "Stop: refused or
gave up" and the error workflow tells a person. The event was NOT accepted and Hadavin holds nothing for it. The
person sends it again later with the SAME key; the same key is safe because nothing ran. Whether n8n's own
"retry execution" signs again is item 6 of the list at the end; until that is checked, start the workflow anew. The HTTP node's own "Retry On Fail" is switched off on purpose: its retries would reuse
the old signature.

## When a run shows NEEDS_PERSON after a restart or a crash

If the worker process stops or crashes during a run, that run is not continued when the worker starts again. The
document was only in the worker's memory. Later the tick finds the run that stopped moving and sets its state to
NEEDS_PERSON with the reason "interrupted" (or "outcome_unknown" if it stopped while carrying out an action, or
"verify_interrupted" if it stopped while checking the result). This only happens if the tick runs in the same
deployment; the worker does not check that it does.

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
  fits in the body is accepted by the endpoint and, as the code reads, the run then stops in NEEDS_PERSON (no test
  sends such a document through the endpoint yet).
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
   status code. This was not tested on a real connection. In the main workflow such a case ends in the error
   workflow.
4. n8n must send a `Content-Length` header. A request sent in chunks without one is answered 400.
5. Renaming is not free. The run id is computed from the tenant id, the sender id and the key. If the tenant id or
   a sender id is renamed, every old key gives a NEW run id, so an event that was already handled would run again
   when it is sent again. If a sender's agent or principal is changed, every old key of that sender is answered
   409. Do neither on a deployment that has handled events, unless a person has decided what happens to old keys.
6. A document may contain the NUL character (written `\u0000` in JSON); the endpoint accepts it. Whether the later
   steps and the database handle such a document was not checked. Remove NUL characters before sending.
7. Until the `triggers` block exists in the configuration code, the worker uses fallback numbers written in its
   own code (address `127.0.0.1`, port 8081, `max_running` 1, `ack_wait_s` 5). A misspelled setting name is not
   reported; the fallback is used silently. Check the worker's start line for the port it serves on.
8. The tick must run next to the worker. Without it, a run that was cut off stays in its last state and never
   reaches a person.
9. Run rows are kept. A key that was used once stays used; there is no way to free a key through this endpoint.

## VERIFY ON A REAL n8n BEFORE ANY CLIENT USE

1. NOT VERIFIED: the raw body is sent byte-identical to the signed string.
2. NOT VERIFIED: where the HMAC secret can live (Community has no custom variables; Code node access to
   credentials is not documented; a Crypto node secret may be plain text in the workflow JSON).
3. NOT VERIFIED: the Crypto node itself (it exists, does SHA-256 hash and HMAC with hex output as used here).
4. NOT VERIFIED: the HTTP Request timeout: its unit and its default.
5. NOT VERIFIED: Retry On Fail: the maximum number of tries and the wait between them (it is off in this
   outline; check this before anyone switches it on).
6. NOT VERIFIED: whether a manual retry or a `retryOf` retry runs the sign node again (if not, a retry later than
   300 s gets 401).
7. NOT VERIFIED: the error workflow runs only when published (the documentation says so; not seen).
8. NOT VERIFIED: one webhook call that starts two executions still yields one run when the key is stable.
9. NOT VERIFIED: the n8n version is pinned and is the one tested (the notes were taken on 2.47.7).
10. NOT VERIFIED: the endpoint secret is written down, for each client, as the one exception to "secrets stay
    out of n8n".
11. NOT VERIFIED: both files import without error; every node type, type version and parameter name in them is
    right; the error workflow's field paths match the real error payload.
12. NOT VERIFIED: n8n sends a Content-Length header and does not send the body in chunks.
13. NOT VERIFIED: `$env` can be read in an expression (it may be blocked by default on newer n8n versions).
14. NOT VERIFIED: the option B Code node's return shape in per-item mode.
15. NOT VERIFIED: the guard: an event with a missing, null or empty id or text fails the execution at the Stop and
    Error node and starts the error workflow, and nothing is sent.
16. NOT VERIFIED: the 503 loop: a failed send leaves through the HTTP node's error output; the status code is
    found where "Busy and rounds left?" looks for it; the Wait node passes the item on; a connection back to an
    earlier node is allowed; each round has a new timestamp and a new signature over the same body.
17. NOT VERIFIED: the loop ends after the set number of rounds and the error workflow then runs.
