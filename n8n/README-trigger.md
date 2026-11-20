# n8n trigger workflows for the Hadavin signed endpoint

**Outline, not run in n8n.** The two JSON files here were written from notes about n8n, not exported from a
running n8n. Every node carries a `notes` field; a note that starts with `UNVERIFIED:` names what nobody has checked.
Do not give these files to a client before the list at the end is done.

## What the two workflows do

- `hadavin-trigger.json` (main): something happens in the client's n8n (a web call, a mail, a schedule). The workflow
  builds one text (the "body") with a request key and a document, signs it with a shared secret, and sends it to
  Hadavin. Hadavin starts at most one run per key and answers with a run id and a state. The outcome of the run
  reaches people later as a card in the chat channel, not through n8n.
- `hadavin-trigger-error.json` (error workflow): when the main workflow fails, n8n starts this one. It builds a short
  message (workflow name, execution link, last node, error text) for a chat or e-mail node that you add.

## How to import

1. In n8n, create a new workflow and choose "Import from File" for each of the two files (menu wording UNVERIFIED).
2. In the error workflow, replace "Notify placeholder" with your chat or e-mail node (whether it must also be
   published before it runs is UNVERIFIED).
3. In the main workflow: replace "Trigger placeholder" with your own trigger; in "Hash business id" and "Build
   request" put your own fields for the business id and the document; in "Send to Hadavin" replace `https://example.invalid/v1/trigger` with the real
   address; in Workflow Settings choose the error workflow (the JSON holds a placeholder id).
4. Choose ONE sign node: option A (Crypto node, connected) or option B (Code node, disabled). Delete the other.

## Where the secret lives

No secret value is in these files and none may ever be saved in them. Both sign nodes read
`$env.HADAVIN_TRIGGER_SECRET`, an environment variable of the n8n server (whether your n8n allows this is
UNVERIFIED; the free Community edition has no custom variables). Where the edition allows it, keep the secret in an
n8n credential instead (UNVERIFIED). Our general rule is that secrets stay out of n8n; this one secret is the
deliberate exception, because n8n must sign the request. The same value is stored on the Hadavin side under
the sender's secret name. It must be at least 32 characters and must not be shared with any other sender. If the
secret is typed into the Crypto node instead, it sits as plain text in the workflow JSON: never export, mail or
commit such a file. Hadavin accepts two secrets per sender at once, so a secret can be changed without a gap.

## The signing recipe

1. `body` = `JSON.stringify({key, document})`: one text, with exactly these two fields, both text.
2. `ts` = the current time in whole Unix seconds, as digits (at most 12 digits).
3. `signature` = `"v0="` + HMAC-SHA256(secret, `"v0:" + ts + ":" + body`) written as lowercase hex.
4. Send `POST /v1/trigger` with the raw `body` text, byte for byte as it was signed, and two headers:
   `X-Hadavin-Request-Timestamp: <ts>` and `X-Hadavin-Signature: <signature>`.

A request whose timestamp is more than 300 seconds away from the server's clock (older or newer) is refused.

## The key rule

`key` is the SHA-256 hash (64 hex characters) of a stable business id: the Message-ID of a mail, or a record id plus
the event name. NEVER use the n8n execution id: n8n may fire twice for one event, and each firing has a new
execution id, so Hadavin would start two runs. Send the hash, not the raw id: Hadavin stores the key where portal
users can read it, so it must not be personal data, and only letters, digits and `. _ : -` (1 to 128 characters)
are accepted. Same key and same document always give the same run. The same key with a different document is
refused (409).

## Response codes and what n8n does

| Code | Meaning | What n8n does |
|---|---|---|
| 202 | Accepted. The run exists and is still working (first time or a repeat). Body: `run_id`, `state`. | Node succeeds; workflow goes on. |
| 200 | The run for this key has ended. Body: `run_id`, final `state`. Nothing runs twice. | Node succeeds; workflow goes on. |
| 401 | Signature wrong, header missing, secret unknown, or timestamp more than 300 s off. Empty body. | Node fails; retries reuse the same signature and fail again; error workflow runs. Check the secret and the server clock. |
| 409 | The key was already used with a different document. Empty body. | Node fails; error workflow runs. A person must look; do not retry. |
| 400 | Signed correctly, but the body is not the two-field JSON, the key has a bad character, or Content-Length is missing or wrong. Empty body. | Node fails; error workflow runs. Fix "Build request". |
| 413 | Body larger than the limit (default 262144 bytes). Empty body. | Node fails; error workflow runs. Send a shorter document. |
| 503 | Hadavin is busy or its store is down. Nothing was accepted. Empty body. | Node fails; Retry On Fail sends the same request again, which is safe with the same key. |

Also: 404 means the path is not `/v1/trigger`; 405 means the method is not POST. Retry On Fail retries on every
failure, not only on 503 (whether it can be limited is UNVERIFIED); retries of 401, 409, 400 and 413 are harmless.

## VERIFY ON A REAL n8n BEFORE ANY CLIENT USE

1. NOT VERIFIED: the raw body is sent byte-identical to the signed string.
2. NOT VERIFIED: where the HMAC secret can live (Community has no custom variables; Code node access to
   credentials is not documented; a Crypto node secret may be plain text in the workflow JSON).
3. NOT VERIFIED: the Crypto node itself (it exists, does SHA-256 hash and HMAC with hex output as used here).
4. NOT VERIFIED: the HTTP Request timeout: its unit and its default.
5. NOT VERIFIED: Retry On Fail: the maximum number of tries and the wait between them.
6. NOT VERIFIED: whether a manual retry or a `retryOf` retry runs the sign node again (if not, a retry later than
   300 s gets 401).
7. NOT VERIFIED: whether the error workflow must be published before it runs.
8. NOT VERIFIED: one webhook call that starts two executions still yields one run when the key is stable.
9. NOT VERIFIED: the n8n version is pinned and is the one tested (the notes were taken on 2.47.7).
10. NOT VERIFIED: the endpoint secret is written down, for each client, as the one exception to "secrets stay
    out of n8n".
11. NOT VERIFIED (added by this outline): both files import without error; every node type, type version and
    parameter name in them is right; the error workflow's field paths match the real error payload.
