# n8n trigger workflows for the Hadavin signed endpoint

**Status: an earlier version of these two files was run in n8n 2.47.7 by the lead (record of that run:
`handover/core-a/inputs/lead-evidence-n8n-1.md`). The files as they stand now were changed after review rounds 1 and 2
(round 3 changed text only), and they have NOT been imported or run in any n8n since. Nobody has
run this exact version. The automatic tests that come with these files read the JSON and this page: they prove the
shape and the wording, not how n8n behaves. Three behaviours were seen later in n8n 2.47.7 (third record, `handover/core-a/inputs/evidence-n8n-3.md`, each case run once): a wait of 60 seconds is lost in a restart of n8n, a wait of 120 seconds survives it; a Respond node followed by a Stop and Error node; two Respond nodes in a row.**

Who this is for: the set-up steps below are for the Hadavin operator (the person who runs Hadavin for the client)
TOGETHER WITH the client's automation builder (the person who builds workflows in the client's n8n). Neither can finish
them alone: the operator holds the Hadavin address and the secret, the builder holds n8n.

What that means for a reader: the changes follow observed facts, but a file that nobody has imported can still hold a
mistake. Every node carries a `notes` field. A note that starts with `SEEN IN n8n 2.47.7:` describes a node that ran
exactly as it is written here. A note that starts with `UNVERIFIED:` names what nobody has seen working (the same
note may also say what WAS seen on an earlier version). Do not give these files to a client before the list at the end
of this page is done.

## Words used here

- Hadavin: the system that receives the signed request and does the work.
- run: one piece of work Hadavin does for one event. It has a run id and a state.
- key: the text that names one event for Hadavin (here: a hash of a stable business id). The same key always means the
  same run, so sending an event twice never starts two runs.
- sender: the n8n side, as Hadavin knows it. One sender has one id and one secret in Hadavin's configuration. The
  request does not say which sender it comes from: Hadavin finds out by trying its secrets.
- state: the word that says where a run is, for example RECEIVED, WORKING or SUCCEEDED (the full table is below).
- NEEDS_PERSON: the state "the run stopped and waits for a person".
- tick: a second, scheduled Hadavin job that looks for runs that stopped moving and ends them.
- worker: the Hadavin process that receives the signed request and does the run.
- execution: one pass of an n8n workflow. credential: n8n's own encrypted store for a secret.
- tenant: the client, as Hadavin's configuration names it; the run id is built from it, the sender and the key.
- agent: the Hadavin agent (a record in its registry) that does the work for one sender; the sender's entry names it.
- principal: the identity the run acts as, taken from the sender's entry in Hadavin's configuration, never from the request.
- ack_wait_s: how many seconds the worker waits for a stored run before it answers 503 (no acknowledgement).
- max_running: how many runs the worker does at the same time (default 1); a request above that gets 503.
- max_steps: the most steps one run of the agent may take; it is a field of the agent's record.
- registry: Hadavin's list of agents and their settings.

## Before you start: what you need from the Hadavin operator

Ask the operator for these four things, in writing, before anything else:

1. The address of the endpoint, for example `https://<host>/v1/trigger`. The worker speaks plain HTTP only and listens on
   the local machine only by default (stated limits 1 and 2), so the address must go through a reverse proxy that ends
   TLS. It is the address you put into "Send to Hadavin".
2. The trigger secret: at least 32 random characters, no space or line break at the start or end. The operator creates
   it and stores it on the Hadavin side under the sender's secret name; the builder receives it over a safe channel,
   never by chat or ticket. One way to make one without a trailing line break:
   `python3 -c "import secrets; print(secrets.token_urlsafe(48), end='')"` (another: `openssl rand -hex 32 | tr -d '\n'`).
3. Confirmation that the sender is configured: its entry (sender id, tenant, agent, principal) holds this secret and the
   worker was started with it. The request carries no sender id, so a wrong secret and an unknown sender look the same:
   a 401 with an empty body.
4. The agent's `max_steps` and the settings `ack_wait_s` and "the tick runs next to the worker" (see "The numbers"
   and "One run at a time"). Also the stated fact that the `triggers` configuration block of the endpoint is NOT in the
   configuration code on this branch yet: until it is merged the worker uses fallback numbers written in its own code
   (stated limit 7), and the operator has to say how the senders are wired in.

## What was run and what was not

Run by the lead in n8n 2.47.7 (a throwaway container, a made-up signing value, a stub receiver in place of
Hadavin), in the order of the record:

1. The n8n version: image tag 2.47.7, no licence key (the free Community edition).
2. Import of both files by command line: accepted without any change to a node, parameter or connection. Two
   faults showed at run time and are fixed in the files now: the Set nodes (typeVersion 3 ignored their
   assignments; 3.4 builds the fields) and the webhook address (no `webhookId`, so `/webhook/<path>` answered 404).
3. The HMAC of the Crypto node against Python's: equal for plain, non-ASCII and JSON-escaped bodies.
4. The bytes sent by the HTTP Request node: equal to the bytes signed in 26 of the 27 requests the receiver recorded
   (26 of the 27 requests were signed by a Crypto node of typeVersion 1; one (`lead-evidence-n8n-1.md` line 273) by a
   Code node. The request whose signature did not match was the outline as written, with Set typeVersion 3, which
   signed the wrong text; that is the fault that led to 3.4), one of the 26 a 300 KB document; always with a `Content-Length` header, never in chunks. Those runs
   signed with a secret from an environment setting, not with the typeVersion 2
   node and the credential that the files use now (that one was run only in a small test workflow).
5. A receiver that answers 503: the workflow's own loop (cut to 3 rounds and 2 seconds for the run) signed again
   with a new timestamp in every round and ended in the error workflow; n8n's own Retry On Fail was measured.
6. Where the signing value can live and whether it shows up in an export.
7. Answers 401, 409, 413 and 400: where the status is found, and that the error workflow runs only when published.
8. A missing, null, empty or spaces-only id or text: the guard stopped all of them and nothing was sent.

A second run by the lead (record: `handover/core-a/inputs/evidence-n8n-2.md`) looked at what n8n hands to the workflow when the
receiver gives no usable answer. The cases are quoted where they matter below ("What the template does on each
answer").

A third run (record: `handover/core-a/inputs/evidence-n8n-3.md`, 2026-11-20, one n8n 2.47.7 container, made-up data, EVERY case run ONCE) looked at three behaviours the loops depend on. SEEN there:

- A restart of n8n during a Wait node (lines 46 to 80; `docker restart`, which allows 10 seconds to stop). An execution in a wait of 60 seconds, restarted at about second 20, was LOST: it was marked crashed, never resumed (checked up to about 73 to 82 seconds past the planned end of the wait, so at least 70 s; the evidence says 82 s in one place and its own timeline gives 73 s), and the caller had already got 200 (lines 51 to 63). An execution in a wait of 120 seconds, restarted at about second 30, was saved as waiting, survived the restart and finished with success about 2 seconds after its planned end (lines 65 to 78). So loops with 60 second waits do not survive a restart; the template waits 70 seconds (the 65 s figure comes from outside the evidence (the lead's brief); the evidence file only says it as a premise, lines 51 and 65).
- A Respond to Webhook node, then a Stop and Error node (lines 82 to 96): the caller got HTTP 200 with the body of the Respond node, the execution ended in error, and the error workflow ran once, 0.12 seconds after the execution began. The answer node's early answer therefore stands when a later node fails the execution.
- Two Respond to Webhook nodes in a row (lines 98 to 118): the caller got the first body only; the second Respond node received the item that came before it (the item of the first Respond node, or of a Set node placed between them) and nothing was raised in the log, no warning and no error. The first Respond node passes its input item on unchanged except the headers, which the printout left out (evidence lines 104 to 105; with respondWith json).

NOT run by anybody (each is also in the list at the end):

- These two files as they stand now.
- The Crypto node of typeVersion 2 with a credential INSIDE the full chain (it was run in a small test workflow).
- The "Answer caller: taken" node as written (noData, code 202), and the webhook authentication setting (added
  after the run). The Respond node was seen once in the third run with respondWith json only; noData, the 202 code and an early answer before a long chain were not seen (see above).
- The changed guard and the new key text (event name and rerun value).
- A manual retry of a failed execution from the n8n editor.
- The real loop values: 45 rounds with 70 second waits, and an n8n restart during a wait of exactly 70 seconds (the restart was run with 60 and 120 seconds only; see the third run above).
- The state check after a 202 or 200 answer (added after the run): the seven nodes from "Run still going?" on, the
  second way into the wait node, and the real Hadavin states in an answer (the stub's state was a made-up word).
- The real Hadavin endpoint (a stub answered).
- One webhook call that starts two executions.
- n8n Cloud and queue mode.
- n8n versions other than 2.47.7.
- The editor menu for importing a file and the HTTP Request timeout of 45 seconds timed live.
- A receiver that answers 520 to 524, a redirect, a TLS failure, and Retry On Fail switched on. (A receiver that
  answers 502 or 504, and a receiver that gives no answer, WERE run in the second record.)

## What the two workflows do

- `hadavin-trigger.json` (main): something happens in the client's n8n (a web call, a mail, a schedule). The workflow
  first checks that the business id and the document text are there, then builds one text (the "body") with a
  request key and a document, signs it with a shared secret, and sends it to Hadavin. Hadavin starts at most one run
  per key and answers with a run id and a state. When Hadavin does not acknowledge the request (an answer 502, 503,
  504 or 520 to 524, or no answer at all), the workflow waits, signs the same body again with a new timestamp, and sends
  again, for a fixed number of rounds. When Hadavin does acknowledge it (202 or 200), the workflow is NOT finished:
  it asks again, with the same key, until the answer shows how the run ended, and it fails (so that a person is
  told) when the run ended badly or never ends (see "A 202 is not the end").
- `hadavin-trigger-error.json` (error workflow): when the main workflow fails, n8n starts this one, but only if it
  is published. It builds a short message (workflow name, execution link, last node, error text) for a chat or
  e-mail node that you add.

## Set-up

These steps are for the Hadavin operator together with the client's automation builder. Every step is required.

1. Get the four things named in "Before you start: what you need from the Hadavin operator".
2. Create both credentials BEFORE the import, so that the ids you write exist: the one that holds the trigger secret
   (see "Where the secret lives", Crypto) and the webhook header credential (see "Webhook authentication", Header
   Auth). The id of a credential you made is in the address of its page in the n8n editor, after `/credentials/`
   (UNVERIFIED: not run).
3. In `hadavin-trigger.json`: write the id and name of the trigger secret credential into the node "Sign" and those of
   the webhook header credential into the node "Trigger placeholder"; replace the `webhookId` of "Trigger placeholder"
   with a fresh UUID and the `path` with a long random value (see "The webhook address").
4. Import both files. After the import open "Sign" and "Trigger placeholder" and check that each shows its credential. In the lead's run this was done by command line: `n8n import:workflow --input=<file>`, once
   for each file; `n8n list:workflow` then printed the id and the name of each workflow (seen). The editor's menu for
   importing a file was not run (UNVERIFIED).
5. In the error workflow, replace "Notify placeholder" with your chat or e-mail node. The message to send is
   `{{ $json.message }}`.
6. The error workflow must be PUBLISHED (active). An error workflow that is only imported does nothing: in the
   lead's run n8n logged that it "is not active and cannot be executed", the main workflow failed, and nobody was
   told. In the run it was published by command line (`n8n publish:workflow --id=<id from n8n list:workflow>`) and
   n8n was started again afterwards (this restart happens at set-up, before any event is sent; it is not the restart of step 12); whether the restart is required was not tried (UNVERIFIED). The editor's own
   Publish switch was not run (UNVERIFIED).
7. In the main workflow, in Workflow Settings, choose the error workflow (the JSON holds a placeholder id).
8. Set up the webhook authentication and give the caller its header (see "Webhook authentication"). This step is
   REQUIRED: without it anyone who can reach the address can start runs.
9. In the main workflow: replace "Trigger placeholder" with your own trigger if it is not a web call (then also delete
   "Answer caller: taken" and connect the guard's first output straight to "Hash business id"); put your own fields for
   the business id, the event name, the rerun value and the document in THREE nodes: "Id and text present?", "Hash
   business id" and "Build request"; in "Send to Hadavin" replace `https://example.invalid/v1/trigger` with the real
   address. Connect your own follow-up steps, if any, after "Done: finished or waits for approval" and nowhere else:
   the first output of "Send to Hadavin" must lead to "Run still going?" and to nothing else. Your follow-up steps must
   tolerate running TWICE for one key: n8n may fire twice for one event, and an event sent again with the key of a run
   that already finished also reaches "Done". And "Done" does NOT mean that the action happened: it is also reached
   for NO_ACTION (nothing had to be done) and WAITING_FOR_APPROVAL (a person has not yet approved anything).
10. Set the loop numbers for this client: the wait in "Wait before next round" (keep it ABOVE 65 seconds, 70 here: a wait of 60 seconds was lost in a restart of n8n, see stated limit 15; the 65 s figure comes from outside the evidence, the lead's brief), the busy rounds in the expression of "Busy
    and rounds left?" (the part `round < 45`) and the checks in the expression of "Checks left?" (the part `< 45`),
    together with the text of "Stop: still running" (see "The numbers" and "One run at a time").
11. Publish the main workflow and test it with a TEST sender or a test agent: a made-up event starts a REAL run, so
    send it only to an agent that has nothing real to act on. Check that Hadavin answered. Then send one event with an
    EMPTY text and check that the failure notice reaches your chat or e-mail node.
12. Operating rule, a known fact in n8n 2.47.7 (stated limit 15): do not restart or update n8n while an event is in flight. The operator checks this in the n8n Executions list: no execution is Running or Waiting (UNVERIFIED: whether the Executions list shows a Waiting state for a Wait node; the evidence shows the word waiting only in the database rows, not in the list). A crash or a host reboot has the same effect as a restart. The 105 minutes below is the worst case. Step 6's restart is the one before any event is sent. An execution that is in a wait of 60 seconds at a restart is lost for good (marked crashed, never resumed) although the caller was already answered; an execution in a wait of 120 seconds survived (seen once each). Wait for the loops to end (up to about 105 minutes, see limit 15), or accept that after the restart the operator must compare what the client sent with the runs Hadavin holds.

Do not change the `typeVersion` of the Set nodes ("Build request", "Stamp time", "Next round", "Next check", and
"Build message" in the error workflow). It is 3.4. With typeVersion 3, n8n 2.47.7 ignored the fields these nodes are meant to build
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
error workflow tells a person. Nothing is sent. This was seen in the lead's run for all four cases. The guard was changed after the run: a number id must be a whole
number that n8n can hold exactly (`Number.isSafeInteger`; a bigger number loses digits and two ids could get one
key), and an `event` field, if the caller sends one, must be a non-empty text. UNVERIFIED: that changed expression.

Why it is required: with the guard taken out of the chain, the run sent a missing id as the hash of the text
"undefined" and a null id as the hash of the text "null". Every such event would get the same key, and Hadavin would
treat them all as one event (the first runs, the rest are answered 409 or silently taken as repeats).

### What the caller of the webhook is told

In the lead's run the caller got HTTP 200 from n8n although the guard had stopped the event and nothing was sent.
To change that, one node was added AFTER the run, and the webhook node's response mode was changed to the one it needs
(`responseNode`):

- "Answer caller: taken" sits IN SERIES on the guard's first output: guard, then "Answer caller: taken", then "Hash
  business id". It answers the caller with 202 and an empty body. This 202 means only that n8n took the event and will
  try to send it. It does NOT mean that Hadavin accepted it; a later refusal reaches a person through the error
  workflow, not the caller. In plain words: the caller's 202 means "taken by the workflow", not "done". The caller
  never learns from this answer how the run ended.
- A refused event (the guard's second output) has NO answer node. "Stop: id or text missing" is the only node on that
  output, so a refused event always fails the execution and the error workflow tells a person. The caller then gets
  n8n's own error answer. UNVERIFIED: its status and body (in the run, with another response mode, the caller got 200;
  in the second record, with the mode "last node", a failed execution gave the caller HTTP 500 with the body
  `{"message":"Error in workflow"}` after the whole execution had ended, lines 285 to 293 of `handover/core-a/inputs/evidence-n8n-2.md`). A caller
  should treat only a 202 as "taken".

This branch was NOT run in n8n as written. SEEN IN n8n 2.47.7 (third record, `handover/core-a/inputs/evidence-n8n-3.md`, each case once): a Respond to Webhook node answered the caller with the status and body it was given (lines 85 to 86); it passed its input item on unchanged except the headers, which the printout left out (lines 104 to 107, with respondWith json); and when a Stop and Error node ended the same execution later, the caller KEPT the Respond answer (HTTP 200 there), the execution ended in error and the error workflow ran once (lines 82 to 96). This chain relies on exactly that: the caller's 202 stands, and a failed run reaches a person through the error workflow. A second Respond node in one execution never reaches the caller and raises no warning (lines 98 to 118), so never add another answer node to this chain. UNVERIFIED: this node as written (type name, version and parameter names were written from memory of the n8n documentation; the run used respondWith json and no response code), the exact parameter text of the response mode value (the record names the mode only as "Respond node mode"), that it passes its input item on unchanged when it is set to noData (the hash node reads the id from it), and that n8n answers the caller before it starts the long sending chain (the cases seen ended within about 0.1 seconds; if n8n does not answer early, the caller waits until the whole execution ends). Until somebody has run it as written, do not rely on the status the caller gets.

## Webhook authentication

The webhook address is open to anyone who can reach it. Without a check, a stranger can start runs, use up keys (a key
claimed by a forged event with another document makes the real event be refused with 409) and flood the error
workflow. So one of these is a REQUIRED set-up step (step 8):

- Header authentication (preferred). In n8n create a credential of the "Header Auth" kind: a header name and a long
  random value (at least 32 random characters; never the trigger secret; never saved in these files). Choose it in the
  Authentication setting of "Trigger placeholder" and give the caller the header name and value. The JSON holds
  `"authentication": "headerAuth"` and a credential reference of the type `httpHeaderAuth` with a placeholder id.
  UNVERIFIED: that shape. It was written from memory of the n8n documentation and never imported; what the import does
  with the placeholder credential id is not known either. Open the node after the import and check it shows the
  credential.
  How to create it without a browser (the same file form as the Crypto credential under "Where the secret lives"; the
  record of the lead's run shows `n8n import:credentials` only for the Crypto type): write a file with
  `[{"id": "<AN-ID-YOU-CHOOSE>", "name": "<A-NAME-YOU-CHOOSE>", "type": "httpHeaderAuth", "data": {"name": "<HEADER-NAME>",
  "value": "<LONG-RANDOM-VALUE>"}}]`, run `n8n import:credentials --input=<that file>`, and DELETE the file.
  UNVERIFIED: the field names `name` and `value` are from memory of n8n's documentation and appear in no evidence file;
  the import of this type was not run. In the editor, a credential's id is in the address of its page (the part after
  `/credentials/`); UNVERIFIED: the editor was not run. `n8n export:credentials` also lists the ids.
- If you cannot use that setting: an unguessable path. Replace `replace-with-your-path` with a random value of at least 32
  characters, treat the whole address as a secret (it can show up in logs of proxies and callers), and do not post it
  in tickets. This is weaker than a header: it protects only as long as nobody sees the address.

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
- n8n encrypts its credentials with its own key (the setting `N8N_ENCRYPTION_KEY`, or one that n8n makes in its data
  folder). Set it yourself and keep a copy in the operator's safe place: without it a restored database cannot read the
  credential and every request is signed wrongly. (UNVERIFIED: not run; the run only showed that the credential export
  holds the value encrypted.)
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

- At least 32 characters; the worker refuses to start with a shorter one. When you write it into the credential file
  above, it is a JSON text: a quote or a backslash in it must be escaped, so use only letters, digits, `-` and `_`.
  Do not type it on a command line that your shell keeps in its history.
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

## What the caller sends to the webhook

One call: a POST with a JSON body. `record_id` (the business id) and `text` (the document) are required; `event` and
`rerun` are optional (see "The key rule"). These field names are placeholders for the client's own and are changed in
three nodes (set-up step 9). With header authentication on (set-up step 8):

    curl -i -X POST 'https://<your-n8n-address>/webhook/<path>' \
      -H 'Content-Type: application/json' \
      -H '<HEADER-NAME>: <HEADER-VALUE>' \
      -d '{"record_id": "rec-1001", "text": "The text of the document, as one string"}'

The expected answer is HTTP 202 with an empty body: taken by the workflow, not done (see "What the caller of the
webhook is told"). Any other answer means the event was not taken.

## The key rule

`key` is the SHA-256 hash (64 hex characters) of ONE text: the business id (trimmed), a colon, the event name, and,
only when the caller sends a non-empty `rerun` value (0, an empty text and false are silently ignored), a colon and that value. The business id is stable: the Message-ID of a
mail, or a record id. The event name is the caller's `event` field (the word `default` when there is none), so that
two different events on one record ("created", "updated") get two keys and two runs. NEVER use the n8n execution id: n8n
may fire twice for one event, and each firing has a new execution id, so Hadavin would start two runs. Send the hash,
not the raw id: Hadavin stores the key where portal users can read it, so it must not be personal data, and only
letters, digits and `. _ : -` (1 to 128 characters) are accepted. Same key and same document always give the same run.
The same key with a different document is refused (409).

To re-run an event whose key is used up (see "When a run shows NEEDS_PERSON after a restart or a crash"), the caller
sends the same call with a NEW `rerun` value such as `rerun-1`, then `rerun-2`. A new value is a new key and a new run.
A person checks the target system first: a run that stopped while carrying out an action may already have done it.

A Message-ID must be turned into the same text every time, by one rule in one place that every path passes: for
example take it from the mail header, remove the angle brackets and surrounding spaces, and lower-case it, always. If
one path sends `<abc@x>` and another `abc@x`, those are two keys and two runs. A number id must be a whole number
below 2 to the power 53 (or sent as text); a longer one loses digits in n8n.

## What the template does on each answer

| Answer | What it means | What the template does |
|---|---|---|
| 202 or 200 | Hadavin holds a run for this key. 202: its state is RECEIVED or WORKING (first time or a repeat). 200: its state is anything else. This does NOT mean the run has ended (see below). Body: `run_id`, `state`. Nothing runs twice. | NOT the end. Goes on to the state check "Run still going?": while the run is going, the workflow waits and asks again with the same key; then it ends as a success or fails, by the state (see "A 202 is not the end"). |
| 400 | The body is not the two-field JSON, the key has a character that is not allowed, or the Content-Length header is missing, zero or longer than the bytes sent (a shorter one gives a cut body and a 401). A document with a lone surrogate (a broken half of an emoji, for example) passes the guard in n8n and is answered 400 "document is not valid text": that is a STOP, and the text must be cleaned at the source. Empty body. | STOP: no retry, straight to the error workflow. Fix "Build request". |
| 401 | Signature wrong, header missing, secret unknown, or timestamp more than 300 s off. Empty body. | STOP: no retry, straight to the error workflow. Check the secret and both clocks. |
| 409 | The key was already used with a different document. Empty body. | STOP: no retry, straight to the error workflow. A person must look. |
| 413 | The body is larger than the limit (see "Size limits"). Empty body. | STOP: no retry, straight to the error workflow. Send a shorter document. |
| 502, 503, 504 or 520 to 524 | 503 comes from the worker (it is busy with another run, it is shutting down, or its database cannot be reached) and means: not acknowledged; send again with the same key; it may already be running. 502 and 504 come from the reverse proxy when the worker behind it is restarting, draining or not answering in time; 520 to 524 are statuses some proxies and content-delivery services give when the server behind them does not answer (UNVERIFIED: which ones your proxy uses; nobody sent one); the template treats all of them the same way. | BUSY: waits, then sends the same body with the SAME key, a NEW timestamp and a NEW signature. At most 45 rounds (a placeholder, 46 sends); then the error workflow. |
| no answer | No HTTP status at all: the connection was refused, timed out or was reset. This is what a sender without a proxy sees while the worker is stopped or restarting. | BUSY, exactly as for 502, 503 and 504. |

Any other status is a STOP as well: every other 4xx, and also 404 (the path is not `/v1/trigger`), 405 (the method
is not POST), 414 and 431 (the request line or the headers are too long; these two come from the stdlib HTTP server layer in `server.py`, not from the worker's own code). All have an empty body; none is tried
again. A 500 is a STOP too: the worker never sends 500 itself, so it is a fault that a person must look at, not a
busy signal. A 3xx answer (a redirect) is a STOP: whether n8n follows it first was not run (UNVERIFIED).

The HTTP node's timeout is 45 seconds (45000 milliseconds). It must stay LONGER than the time the worker may hold a
request before it answers 503: `ack_wait_s` is 5 seconds by default and at most 30. A timeout that is too short makes n8n
give up on a request that the worker would still have answered, and the request then counts as "no answer".

UNVERIFIED: the "no answer" row and the 502 and 504 part of the row above it. (This sentence stands for the record of
the first run only; the second record, `handover/core-a/inputs/evidence-n8n-2.md`, has since run these cases, see below.) What the second record
shows, in n8n 2.47.7 against a stub receiver, for the HTTP node with Retry On Fail off:

- The item on the failed output (output 1) always has the keys `body`, `round`, `ts`, `hmac` and `error`; `error.httpCode`
  is undefined in every case (lines 110 to 111, 217).
- A refused connection (ECONNREFUSED, line 117), a name that does not resolve (ENOTFOUND, line 124), a reset
  (ECONNRESET, lines 172 to 177) and a hang-up ("socket hang up", also code ECONNRESET, lines 165 to 170) have NO
  status in `error`.
- A timeout is an AxiosError with the code ECONNABORTED and no status (lines 131 to 140 and 191 to 199).
- 502, 503 and 504 are AxiosError with the code ERR_BAD_RESPONSE and a numeric `error.status` (lines 142 to 161);
  400, 401, 409 and 413 are ERR_BAD_REQUEST with a numeric status (lines 201 to 208).
- In one case (a status line and headers, then silence) the field `error` is the plain text "aborted" with no message,
  name, code or status (lines 179 to 189).
- The expression `['', '502', '503', '504'].includes(String($json.error?.status ?? ''))` gave true for all of these
  and false for 400, 401, 409 and 413. The empty text in the list is what counts "no status" as busy. In the loop,
  ECONNREFUSED, a timeout and a 502 each ran all rounds with a new timestamp and a new signature, then ended in "Stop:
  refused or gave up" and the error workflow (lines 221 to 272).

Still UNVERIFIED: 520 to 524 (added to the list after the run), a redirect, a TLS failure, a receiver that answers after
the timeout, Retry On Fail switched on, the loop with the real values (45 rounds, 70 second wait, 45 second timeout),
the real Hadavin endpoint behind a real proxy, n8n Cloud and queue mode.

Two things follow from "no answer counts as busy", and both are meant:

- A wrong address, a host name that does not resolve (seen: ENOTFOUND, no status), or a TLS fault also gives no HTTP status. The template then
  tries for all its rounds before a person is told: about 52 to 53 minutes (45 waits of 70 seconds) plus up to 45 s per send (about 87 minutes when each of the 46 sends times out) with the placeholders; about 52 to 53 minutes only when the connection is refused at once. Send one made-up
  event after every change of the address (the last set-up step).
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
state. The answer never holds a reason and never holds the result of the run. The main workflow does exactly this
by itself; the next section says how.

## A 202 is not the end

The state check is a REQUIRED part of the main workflow, not an extra. It starts at the node "Run still going?",
which is the only node after the first output of "Send to Hadavin". Do not take it out and do not connect anything
else to that output.

### Why: an acknowledged request whose work was never done

A design review of the worker found this sequence. The worker's code cannot close it alone, so the template must.

1. A request for a key arrives. The worker stores the run (one row, state RECEIVED). Then the worker process dies,
   before it has sent its answer. The sender has no acknowledgement.
2. The sender tries again, as it should. The stored run is still there, in state RECEIVED, so the new worker
   answers 202. But no work is going on anywhere: the document lived only in the memory of the process that died,
   and a stored run is never started a second time.
3. A workflow that takes a 202 as the end now finishes as a success. Nothing tries again after a 2xx.
4. Later Hadavin's clean-up job (the tick) finds the run that never moved and sets it to NEEDS_PERSON with the
   reason "interrupted". It changes the stored state and writes an audit record. It sends NO message to a person.

The result without the state check: the client's automation shows a success, the work was never done, and nobody
is told. The same end is reached after an acknowledged request when the worker is killed during a restart, because
the process supervisor waited a shorter time than the run needed.

### What the workflow does after a 202 or 200

- "Run still going?" reads the `state` of the answer. If the run is still going, "Checks left?" looks at the
  count, "Next check" takes the SAME body again (same key, same document) and adds one to the count, "Wait before
  next round" waits, and then "Stamp time" and "Sign" make a new timestamp and a new signature and the request is
  sent again. For Hadavin, the same signed request with the same key IS the question "what is the state of this
  run?". There is no other address for it. It never starts a second run.
- When the answer shows a state in which the run has ended, or in which it waits for an approval, "Run ended
  well?" decides: a success ends at "Done: finished or waits for approval"; everything else fails the execution at
  "Stop: run did not end well", with a message that names the state and the run id. The answer holds no reason,
  so the message cannot name one: NEEDS_PERSON after a crash ("interrupted") looks the same from here as
  NEEDS_PERSON for any other reason. The reason is in Hadavin's stored run, but no lookup tool exists yet in this tree
  (the command line has no command that shows a run): ask the Hadavin operator, giving the run id from the message. The
  message holds the run id, not the key. The key text is the field `key` in the output of "Hash business id" in the
  failed execution (the message has the execution link). The operator can check it: the run id is `run-` and the first 32
  hex characters of the SHA-256 of tenant, a NUL byte, sender, a NUL byte and key.
- When the checks are used up and the run still shows as going, the execution fails at "Stop: still running"
  ("still shown as running after 45 checks, about 52 minutes").
- A check that is answered 502, 503, 504 or 520 to 524, or not answered, goes the busy way like any other send (wait,
  sign again, send again). The busy rounds are counted over the whole execution: 45 in all, not 45 for each check, and
  one counter serves the first send and every check.
- Every failure starts the error workflow, which tells a person. The workflow fails closed: a state it does not
  know, or an answer without a state, is treated as "did not end well".

### The states

Every state Hadavin has (`RunState` in `src/hadavin_sdk/models.py`), and what the template does with it. A test
compares this table and the workflow's expressions with the code, so a renamed or new state fails the test.

| State | What it means in plain words | What the template does |
|---|---|---|
| RECEIVED | The run is stored; the work has not begun. | STILL GOING: waits and asks again. |
| WORKING | The agent is reading and thinking. | STILL GOING: waits and asks again. |
| PLAN_READY | The agent has a plan; the rules are being applied to it. A short step. | STILL GOING: waits and asks again. |
| EXECUTING | The planned action is being carried out. | STILL GOING: waits and asks again. |
| VERIFYING | The action was carried out; its result is being checked. | STILL GOING: waits and asks again. |
| NO_ACTION | The run finished and nothing had to be done (or it only posted a proposal). | SUCCESS: the workflow ends. |
| SUCCEEDED | The action was carried out and the check passed. | SUCCESS: the workflow ends. |
| WAITING_FOR_APPROVAL | The plan waits for a person to approve it. Hadavin has asked the approvers itself. | SUCCESS: the workflow ends. What happens after the approval is not watched (see the limits). |
| NEEDS_PERSON | The run stopped and waits for a person. A run cut off by a crash or a forced kill ends here ("interrupted"). | ERROR: fails, the error workflow tells a person. |
| DENIED | A rule refused the plan. Nothing was carried out. | ERROR: fails, the error workflow tells a person. |
| REJECTED | A person said no to the plan. Nothing was carried out. | ERROR: fails, the error workflow tells a person. |
| EXPIRED | Nobody answered the approval in time. Nothing was carried out. | ERROR: fails, the error workflow tells a person. |
| ROLLED_BACK | The action was carried out, the check failed, and the action was undone. | ERROR: fails, the error workflow tells a person. |
| STOPPED | The stop switch ended the run. | ERROR: fails, the error workflow tells a person. |

There is no state named FAILED in the code: a run that fails ends in one of the six ERROR states above.

Why five states count as "still going" although Hadavin answers 202 only for the first two: PLAN_READY, EXECUTING
and VERIFYING are answered 200, but the run is still on its way in them, and a run that dies in one of them is
ended by the tick in the same way (as NEEDS_PERSON). The five are exactly the states the tick's stuck step looks
at. If the workflow took them as an end, the gap described above would stay open for a crash in those states.

### The numbers

- The stuck limit: how long a run may stay quiet before the tick ends it. The code computes it for each agent
  (`stuck_after_s` in `src/hadavin_sdk/runtime/tick.py`): the agent's `max_steps` times `call_timeout_s` times
  `max_attempts`, plus 60 seconds. `max_steps` is set for each agent and has no default. The other two are
  settings of the model connection with the defaults 60 seconds and 3.
- The tick gap: nothing in the worker starts the tick; the operator's scheduler runs it every 30 to 60 seconds.
  The code takes 60 seconds as the longest gap (`TICK_SLACK_S` in the same file).
- Example, an agent with `max_steps` 12 on the defaults: 12 x 60 x 3 + 60 = 2220 seconds (37 minutes); with one
  tick gap, 2280 seconds (38 minutes).
- The template's placeholders: a wait of 70 seconds ("Wait before next round"; above 65 seconds on purpose, see stated
  limit 15) and 45 checks ("Checks left?"), 3150 seconds (about 52 to 53 minutes). That is longer than the 2280 seconds of the example.
- The rule for each client: checks times wait must be LONGER than that client's stuck limit plus one tick gap.
  With the 70 second wait and the default model settings: `max_steps` 6 needs more than 17 checks, `max_steps` 12
  more than 32, `max_steps` 20 more than 53. When you change the number in "Checks left?", change the text of
  "Stop: still running" too. Keep the wait above 65 seconds (a 60 second wait was lost in a restart of n8n, a 120 second wait survived: stated limit 15; the 65 s figure itself comes from outside the evidence, the lead's brief), and do not restart n8n while events are in flight.
- Where to find `max_steps`: it is a field of the agent's record in Hadavin's registry (the list of agents), so the
  operator can read it for the agent this sender starts. Ask for it before you set any number here.
- The two numbers to set sit in two expressions: the busy rounds, in the node "Busy and rounds left?" (the part
  `round < 45`), and the checks, in the node "Checks left?" (the part `< 45`). Each is multiplied by the wait.
- Busy rounds: the placeholder is 45. With the 70 second wait that is 45 waits, 3150 seconds, which is longer than the
  2280 seconds of the example. 45 rounds make 46 sends (the first send and one for each round). The same rule holds:
  busy rounds times wait must be LONGER than the stuck limit plus one tick gap. The `Retry-After` header that the
  worker sends with a 503 (1 second) is ignored: the template waits its own wait.
- These numbers are a floor, not a recommendation. They are right for the example agent only; a client whose agent has
  a larger `max_steps` must raise them. Nobody has measured a real run.
- With too few checks nothing is lost: the workflow then fails at "Stop: still running" for a run that is merely
  slow, and a person gets a notice that was not needed. It never ends as a success for a run that is not done.

### Which failures are permanent and which are an outage

| Kind | Answers | Who acts | What to do |
|---|---|---|---|
| Permanent | 400, 401, 409, 413 (and every other 4xx, and 500) | A person must act. Sending again never helps. | Stop. Fix the document, the secret, the clocks or the size, or look at the 409 (the key was used with another document). A new key is needed only if the document really is new. |
| Outage | 503 from the worker; 502 or 504 from the proxy; no HTTP answer; a timeout | Nobody yet: the worker or its store is busy, restarting or not reachable. | Send again with the SAME key. The first send may already be running; the key makes a repeat safe. |

One limit of this table: in the code, an exception inside the worker's start step is answered 503 whatever its
cause, so a fault that is really permanent can look like an outage and the template then tries again until its
rounds run out. This is the lead's reviewer's finding (round 3, Minor 5); the answer is not split in this version.

### Where the worker runs

- Start the worker on Linux or in a container. The stop signal SIGTERM (close the port, start no new run, let the
  running one finish, exit 0) is handled by `serve` in `src/hadavin_sdk/triggers/worker.py`, and the tests that show it run on Linux.
- On a Windows laptop only Ctrl-C stops the worker cleanly. SIGTERM is never delivered there, so a stop by n8n's
  host, a service wrapper or `taskkill` is a hard kill with no drain, and the tick later sets a cut run to
  NEEDS_PERSON "interrupted" (`handover/core-a/WINDOWS-NOTES.md`, W02). The worker's docstring says Ctrl-Break
  (SIGBREAK) is handled like SIGTERM, but WINDOWS-NOTES says it kills the process; which is true is UNVERIFIED.
- The worker listens on 127.0.0.1 by default and refuses another host unless `allow_non_loopback` is true, which
  a config cannot set today (stated limit 7). n8n in a container cannot reach a loopback-only worker: inside a
  container 127.0.0.1 is the container itself (`WINDOWS-NOTES.md`, W03). The operator must put a TLS proxy in front
  of the worker, or run n8n on the same host and network as the worker (for example both natively, or in one
  network namespace). Whether a given Docker setup can then reach it is UNVERIFIED; nobody has run it.

### Three limits

1. Until the tick has run, a dead run looks alive. A run whose process died keeps the state RECEIVED or WORKING
   (or PLAN_READY, EXECUTING, VERIFYING) until the tick ends it, and the answer cannot tell a dead run from a live
   one. So the check can take up to the stuck limit plus one tick gap to notice (38 minutes in the example), and
   the stuck limit counts from the run's last sign of life, not from the first 202. If the tick does not run at
   all, the run stays "going" forever; the workflow then fails at "Stop: still running" when its checks are used
   up, so a person is still told.
2. The worker itself tells no person about an interrupted run. The tick changes the stored state and writes an
   audit record, nothing more. This template's error workflow is the only notice today. It works only if the error
   workflow is published and its "Notify placeholder" was replaced (set-up steps 5 and 6), and only for events
   that came through this template.
3. The rule for restarts: set the process supervisor's stop grace period longer than the longest run. A run that
   is cut by a forced kill ends as "interrupted", and its key is never run again: a NEW key is needed to redo the
   work (see "When a run shows NEEDS_PERSON after a restart or a crash").

Also know: the workflow stops watching at WAITING_FOR_APPROVAL. If the plan is later rejected, expires, or fails
when it is carried out, this execution has already ended as a success, and this template tells nobody about
those later ends. And an event that is sent again with the key of a run that ended
badly fails again, every time: that is meant, the key is used up.

UNVERIFIED: all of this section's n8n side. The state check was added after the lead's run and nobody has run it
in any n8n. Seen in the run: the IF node, the Set node, the Wait node and the Stop and Error node as types, a
connection back to "Stamp time" running as a loop, and an answer 202 whose item held `run_id` and `state`.

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
then back to "Stamp time" and the sign node. The outline holds placeholders: a wait of 70 seconds and 45 rounds,
about 52 to 53 minutes in total. Nobody has measured a run for this file; set both numbers for each client so that
rounds times wait is longer than that client's longest run. If events arrive faster than runs finish, the waiting
executions pile up in n8n and some will use up their rounds; this setup is for a low event rate.

What the lead's run showed for the loop, cut to 3 rounds and a 2 second wait: 4 requests reached the receiver,
about 2 seconds apart, each with the same body, a new timestamp and a new signature that the receiver found
correct; then the execution failed at "Stop: refused or gave up" and the error workflow ran. The real numbers (45
rounds, 70 seconds) were not run.

The loop finds the status of a failed send in the field `error.status` of the item that leaves the HTTP node's
second output (seen for 401, 409, 413, 400, 502, 503 and 504). There is no field `error.httpCode`. A send with no HTTP answer has
no status there (seen for ECONNREFUSED, ENOTFOUND, ECONNRESET, a hang-up, a timeout and one plain text "aborted";
see the table above and `handover/core-a/inputs/evidence-n8n-2.md`).

When the workflow gives up (45 rounds, each answered 502, 503, 504 or 520 to 524 or not answered at all), the execution fails
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
  large); "interrupted" is only one of them. The reason is in Hadavin's stored run and in its audit record; no lookup tool exists yet in this tree, so ask the Hadavin
  operator with the run id (see "A 202 is not the end").
- A person decides what to do. If the event should be worked on again, it must be sent with a NEW key (the caller sends the same
  call with a new `rerun` value such as `rerun-1`, see "The key rule"). A new key is a new run from the start. If the
  reason is "outcome_unknown", an action may already have been carried out: a person checks the target system
  before any re-run.
- Who is told: as far as the code read for this file shows, the tick changes the stored state and writes an audit
  record; it does not post a chat card at that moment. (A run that ends in NEEDS_PERSON by itself, without a
  crash, does post a card for people when a chat channel is set up.) So do not count on a card for an interrupted
  run: the main workflow's state check is what tells a person (it fails at "Stop: run did not end well" and the
  error workflow runs; see "A 202 is not the end"). For events that did not come through this template, the operator
  has to look at the stored runs directly: no lookup tool exists yet in this tree.

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
    off: the tick later sets it to NEEDS_PERSON with the reason "interrupted", and its key is used up: the key is
    never run again, and a NEW key is needed to redo the work (see "When a run shows NEEDS_PERSON after a restart
    or a crash"). As the code reads, a second stop signal does nothing
    while the worker waits for its runs (up to 30 seconds) and kills the process after that. Not tested: a request
    that waits for a free slot when the signal comes, a request that arrives between the signal and the closing of
    the port, and a second signal.
12. There is no fairness among waiting requests: a later request can be served before an earlier one. A request
    that has just arrived tries for the free slot at once; one that is already waiting looks only about once a
    second. With a steady flow of events an early event can lose every round and end in the error workflow while
    later ones run. No request is ever acknowledged without a stored run. This setup is for a low event rate.
13. A dead run looks alive until the tick has run. The answer cannot tell a run whose process died from one that
    is working: both show RECEIVED or WORKING. The main workflow's state check therefore needs up to the stuck
    limit plus one tick gap to notice (see "A 202 is not the end" for the numbers).
14. The worker tells no person about an interrupted run. The tick sets the state and writes an audit record; no
    chat card, no mail. The error workflow of this template is the only notice today.

15. The caller's 202 is given before anything is stored in Hadavin, and the sending loops live in n8n. The workflow
    answers the caller (202) first and sends afterwards. From then on the event exists only inside one n8n execution:
    until Hadavin has answered 202 or 200 there is no record of it anywhere else, and the caller will not send it again,
    because it was told 202. The loops can take long: up to 45 busy waits and then up to 45 checks, 70 seconds each,
    6300 seconds of waiting, about 105 minutes plus the time of the sends. If n8n stops, restarts or is updated in that time, the execution may be
    lost. SEEN IN n8n 2.47.7 (third record, `handover/core-a/inputs/evidence-n8n-3.md`, lines 46 to 80, each case run once, with `docker restart` and its 10 second stop timeout): an execution in a wait of 60 seconds, restarted at about second 20, was LOST (marked crashed, never resumed, checked up to about 73 to 82 seconds past the planned end of the wait, so at least 70 s; the evidence says 82 s in one place and its own timeline gives 73 s; the caller had already got 200); an execution in a wait of 120 seconds, restarted at about second 30, was saved as waiting, survived, and finished about 2 seconds after its planned end. So the loops of this template use a wait of 70 seconds, above 65 (the 65 s figure comes from outside the evidence (the lead's brief); the evidence file only says it as a premise, lines 51 and 65). UNVERIFIED: that a wait of exactly 70 seconds is saved like the 120 seconds one (an inference from the threshold, not run); a restart at another moment (during a send, between two nodes); a crash of n8n or a longer stop timeout; whether the error workflow runs for a lost execution (the test workflow had no error workflow). If an execution is lost, this template tells nobody (an error workflow runs for an execution that fails inside a running n8n, seen once for a Stop and Error node, lines 90 to 95;
    UNVERIFIED for a crash of n8n itself). The rule: keep the wait above 65 seconds (70); do not restart n8n while events are in flight; after any n8n
    restart the operator compares what the client sent with the runs Hadavin holds, and an event with no run is sent
    again with the SAME key.
16. WAITING_FOR_APPROVAL ends the workflow as a success, but the tick can later turn a run in that state into NEEDS_PERSON
    with the reason `approval_missing` (a crash between the wait and the saving of the approval request leaves a
    wait that nobody can answer). Like a rejection, an expiry or a failure when the action is carried out, that later
    end is not watched from here and this template tells nobody.
17. n8n keeps the document. The item that moves through the workflow holds the document text, and n8n stores the data
    of an execution in its own database (the run read executions from it). Set n8n's retention of execution data short,
    or stop it saving the data of successful executions, so that documents do not pile up there. UNVERIFIED: the names
    of those n8n settings were not checked here; read n8n's own documentation for your version.
18. Not run, and not stated as working: a manual retry of a failed execution from the editor (see verify item 7), the
    error workflow when n8n itself crashes, and that the Respond to Webhook node set to noData (the one seen used respondWith json) and the Crypto node of version 2 pass
    the item through unchanged.

## VERIFY ON A REAL n8n BEFORE ANY CLIENT USE

Nobody has run any of these. The records of what WAS run are `handover/core-a/inputs/lead-evidence-n8n-1.md`,
`handover/core-a/inputs/evidence-n8n-2.md` and `handover/core-a/inputs/evidence-n8n-3.md`. These checks prove nothing by themselves about n8n: the automatic tests only read the JSON and this page.

1. NOT VERIFIED: these two files as they stand now import without error and run from the trigger to the answer
   (they were changed after the run and not imported again).
2. NOT VERIFIED: the Crypto node of typeVersion 2 with the credential inside the full chain: it keeps the
   timestamp, the body and the round counter on the item, and the receiver finds the signature correct.
3. NOT VERIFIED: what the import does with the placeholder credential id, and creating the credential in the editor.
4. NOT VERIFIED: the "Answer caller: taken" node as written (noData, code 202): the caller gets 202 when the guard passes and is answered before the
   sending chain starts, and the node passes its item on to the hash node unchanged. (A Respond node with respondWith json was seen to answer the caller and to pass its item on, once, and a later Stop and Error node did not change the caller's answer: third record.)
5. NOT VERIFIED: the placeholder `webhookId` and a fresh UUID in its place both give the address `/webhook/<path>`.
6. NOT VERIFIED: the status check as it is written now (it reads `error.status` only, counts 502, 503, 504 and 520 to
   524 as busy, and counts a missing status as busy). The same form without 520 to 524 was run in the second record.
7. NOT VERIFIED: whether a manual retry from the editor, or a `retryOf` retry, runs the sign node again (if not,
   a retry later than 300 s gets 401).
8. NOT VERIFIED: the real loop values, 45 rounds with 70 second waits, and a wait of exactly 70 seconds (a 120 second wait was seen once to be saved and a 60 second wait was seen once to be lost, see stated limit 15).
9. NOT VERIFIED: the real Hadavin endpoint: every status in the run came from a stub that answered with an empty
   body.
10. NOT VERIFIED: one webhook call that starts two executions still yields one run when the key is stable.
11. NOT VERIFIED: n8n Cloud, queue mode, and an external task runner.
12. NOT VERIFIED: n8n versions other than 2.47.7. Pin the version that was tested.
13. NOT VERIFIED: the HTTP Request timeout timed live (its unit, milliseconds, and its default, 10000, were read
    from the node's definition only).
14. NOT VERIFIED: no answer at all from the REAL Hadavin endpoint behind a real proxy, a redirect, a TLS failure, and
    statuses 520 to 524. (A stub that refused, reset, hung up or timed out was run in the second record; see "What
    the template does on each answer".)
15. NOT VERIFIED: the editor menu for importing a file.
16. NOT VERIFIED: a body larger than 300 KB, and a proxy between n8n and the receiver.
17. NOT VERIFIED, and not checkable by a test because it is a policy statement: the trigger secret is stored in n8n on
    purpose, as the one exception to "secrets stay out of n8n", and the operator writes that exception down for each
    client.
18. NOT VERIFIED: an answer 502 or 504 goes the busy way behind a real proxy (the stub case was run in the second
    record), and a restart of the real worker
    under load: events sent during the drain are taken by the new worker and none reaches the error workflow.
19. NOT VERIFIED: the state check after a 202 or 200: the workflow asks again with a new signature while the state
    is one of the five "still going" states, ends as a success on NO_ACTION, SUCCEEDED and WAITING_FOR_APPROVAL,
    fails with the state in the message on the six other states and on an answer without a state, and fails at
    "Stop: still running" after the set number of checks. Also: the count of checks survives a busy round, the
    wait node works when entered from "Next check", and the Stop and Error node takes an expression as its
    message.
20. NOT VERIFIED: the gap itself, against a real worker and a real tick: kill the worker right after it stored a
    run, send again, and see the execution fail with NEEDS_PERSON within the stuck limit plus one tick gap, and
    the error workflow tell a person.
21. NOT VERIFIED: the webhook authentication: the setting `headerAuth` and the credential type `httpHeaderAuth` as the
    JSON writes them import without error, the node shows the credential, a call without the header is refused and a
    call with it reaches the guard.
22. NOT VERIFIED: an n8n restart during a wait of 70 seconds: whether the execution resumes (60 seconds: lost, 120 seconds: survived,
    once each, third record; the 65 s threshold comes from outside the evidence, the lead's brief), and whether anybody is told of a lost execution.
23. NOT VERIFIED: the publish steps: that `n8n publish:workflow` needs a restart of n8n afterwards (the run restarted it),
    and the editor's own Publish switch.
24. NOT VERIFIED: a refused event (an empty text): "Stop: id or text missing" always runs and fails the execution, the
    error workflow tells a person, and what status and body the caller gets from n8n.
25. NOT VERIFIED: the Respond to Webhook node set to noData and the Crypto node of version 2 pass the item through to the next node
    unchanged (the Respond node with respondWith json was seen to pass it on); a manual retry; the error workflow when n8n itself crashes; the execution retention setting.
