# REQUEST 002 from core-a (DOOR) to core-b (SPINE): sentences for README.md, SECURITY.md and CHANGELOG.md about the signed trigger endpoint

Status: DRAFT 1, 2026-11-20. Source: the lead's review `inputs/lead-review-code-D-1.md` (items named below as "Major N" / "Minor N") and ORDER 012. This is item R3 of REQUEST 001, now with exact text.

Why a request: the three files belong to core-b; core-a does not edit them. Each row gives the file, the section, the exact sentence proposed, the reason and the review item. core-b may reword; the facts are what matters.

What the sentences rest on: the code of `src/hadavin_sdk/triggers/endpoint.py`, `worker.py`, `server.py`, `approvals/hmac_v0.py`, `runtime/tick.py` and `models.py` as read on 2026-11-20. Nothing here was run against a real n8n or a real reverse proxy. Three sentences depend on code changes that are still being made in the same review round; they are marked HOLD and must be checked against the merged code before they are copied.

Words: "worker" = the process started with `python -m hadavin_sdk.triggers.worker`; "tick" = the scheduled job that ends runs that stopped moving; "sender" = one entry of `triggers.senders` in the config.

## README.md

| # | Section | Sentence | Reason | Review item |
|---|---|---|---|---|
| R-1 | new section "Signed trigger endpoint (limits)", after "Limits and trust (K5 read tools)" | "The trigger worker handles one run at a time by default (`triggers.max_running` is 1 until spend can be reserved before a model call). A second event that arrives during a run is not queued: the worker holds the request for up to `ack_wait_s` (default 5 seconds) and then answers 503, and nothing is stored for it. A run can last minutes, so the sender must retry a 503 over a span longer than its longest run and sign each retry anew, because a signature is refused 300 seconds after its timestamp." | States the throughput honestly; without it a reader assumes a queue. | Major 1 |
| R-2 | same section | "At most one run per (tenant, sender, key) rests on the primary key of the runs table. It does not cover a sender that sends one event under two different keys." | The once-only sentence of plan B3 with its limit. | REQUEST 001 R3 |
| R-3 | same section | "An answer 200 means the run exists and is past RECEIVED and WORKING; it does not mean the run has ended. The states PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING and VERIFYING are also answered 200." | The n8n README said 200 means ended; the code answers 200 for four open states. | Minor 10 |
| R-4 | same section | "If the worker stops or crashes during a run, the run is not continued. The tick later sets it to NEEDS_PERSON with reason `interrupted` (`outcome_unknown` if it stopped while executing, `verify_interrupted` if it stopped while verifying). The same key then answers 200 NEEDS_PERSON for good and is never run again automatically; a person decides, and a re-run needs a new key. The tick must run in the same deployment, or such a run never reaches a person." | A client cannot resubmit under the same key; this must be written where operators read. | Major 2, Minor 14 |
| R-5 | same section | "The worker's built-in web server has no connection cap and no TLS, and a slow client holds a thread. It listens on the local machine by default. The client's reverse proxy in front of it must buffer whole requests, cap connections and request size, and end TLS. `triggers.allow_non_loopback: true` exposes the worker without that protection." | An exposed stdlib server is open to cheap resource use by unsigned clients. | Minor 2 |
| R-6 | same section | "Renaming the tenant id or a sender id changes every run id, so an event that was already handled runs again when it is sent again. Changing a sender's agent or principal makes every old key of that sender answer 409." | Neither effect is documented anywhere. | Minor 13 |
| R-7 | same section | "The request body limit is `triggers.max_body_bytes` (default two times `MAX_DOCUMENT_BYTES`). JSON escaping can make a document up to six times larger in the body, so a document under the document limit can still be answered 413." HOLD: the default exists only in REQUEST 001, not yet in `config.py`. | The n8n README named a stale default; the true one is a config default core-b owns. | Minor 11 |
| R-8 | same section | "When the worker refuses a request without reading its body (413 and some 400 and 401 cases), the sender may see a closed connection instead of the status code. Not tested on a real connection." | Stated limit instead of a silent surprise. | Minor 4 |
| R-9 | same section | "The n8n workflow files under `n8n/` are an outline that was not run in n8n; `n8n/README-trigger.md` lists what must be verified on a real n8n before any client use." | Never claim more than was run. | n8n outline section |

## SECURITY.md

| # | Section | Sentence | Reason | Review item |
|---|---|---|---|---|
| S-1 | new section "Signed trigger endpoint", after "Stated limits of redaction" | "Never use the approvals secret as a trigger secret, or the other way round. Both are checked with the same signing recipe and the header names are not part of the signed text, so whoever holds a trigger secret equal to the approvals secret can forge an approval click. The code does not compare the two values." HOLD: drop the last sentence if core-b adds a value comparison at start. | Cross-use of one secret breaks the rule that the approver is a different identity than the sender. | Minor 9 |
| S-2 | same section | "A trigger secret has at least 32 characters, is not shared between senders, and has no space or line break at its start or end; a sender has at most two secrets, the second only during a swap." HOLD: the checks for two secrets and for spaces are being added to `check_secrets` in this round; the 32-character and not-shared checks are in the code today. | The bound "at most 16 signatures per request" rests on it; a trailing line break gives a permanent 401. | Minor 5 |
| S-3 | same section | "Before a request with a fresh timestamp is refused for a bad signature, the worker computes up to 16 signatures over the whole body, and each connection may hold up to `max_body_bytes` in memory. This is acceptable only behind a reverse proxy that buffers requests and caps connections." | Names the cost an unsigned client can cause. | Minor 2 |
| S-4 | same section | "A request is refused when its timestamp is more than 300 seconds from the server clock, older or newer. A captured request can be replayed inside that window; a replay gives the same run and starts nothing new." | States the replay window and why it is harmless. | Minor 1, invariant 3 |
| S-5 | same section | "A document may contain the NUL character; the endpoint accepts it. Whether redaction and the PostgreSQL text columns handle it was not checked." | Open item, stated instead of assumed. | Minor 12 |
| S-6 | same section | "Until the `triggers` config block exists, the worker falls back to numbers in its own code (127.0.0.1, port 8081, one run at a time, 5 seconds wait), and a misspelled setting name is not reported." HOLD: delete this sentence when REQUEST 001 lands and the fallbacks are removed. | A silent fallback can hide a wrong setting. | Minor 6 |
| S-7 | same section | "The built-in server does not listen on the IPv6 local address `::1`; use 127.0.0.1 or localhost." HOLD: check against the merged `check_bind`. | Today `::1` passes the check and the bind then fails. | Minor 7 |

## CHANGELOG.md

| # | Section | Sentence | Reason | Review item |
|---|---|---|---|---|
| C-1 | "Unreleased", new bullet | "**Signed trigger endpoint (new).** `python -m hadavin_sdk.triggers.worker` serves `POST /v1/trigger`: a sender signs `{key, document}` with HMAC-SHA256 (the same recipe as the approval callbacks, under the `X-Hadavin` header prefix) and the worker starts at most one run per (tenant, sender, key). Answers: 202 while the run is RECEIVED or WORKING, 200 for any later state (not only ended ones), 409 for the same key with another document, 503 when busy or the store is down. One run at a time by default. Limits are in README.md and SECURITY.md; the n8n files under `n8n/` are an outline that was not run in n8n." | One entry that names the new surface and its main limits. | Major 1, Minor 10 |
| C-2 | "Unreleased", under "Upgrade steps" | "The trigger worker needs a new `triggers:` block in config.yaml; without it the worker exits with code 2. Existing configs without the block are unchanged." HOLD: only when REQUEST 001 has landed. | An operator must know the new block is optional for everything else. | REQUEST 001 |

## Not asked
- No change to any code file of core-b. The value comparison of the approvals secret and the trigger secrets (Minor 9, "if it is cheap") is left to core-b's judgement; S-1 is written for the case that it is not added.
- The n8n-side wording (guard node, wait-and-sign-again loop, the verify list) is in `n8n/README-trigger.md`, which core-a owns.
