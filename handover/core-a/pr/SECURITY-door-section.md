Append to SECURITY.md after "Stated limits of redaction", same style (a heading, short bullets, reviewed-not-bugs wording) [SECURITY.md].

## The signed trigger door: threat model and stated limits

The door (`hadavin_sdk.triggers`) takes one signed POST per run. What it defends and what it leaves to the deployment:

- **Forgery.** A request is accepted only when its HMAC "v0" signature verifies; nothing of the body is parsed before that. Agent and principal come from configuration, never from the request. Every refusal has an empty body and no header names the reason [endpoint.py docstring; ticket D invariant 10].
- **Replay.** The timestamp must be within 300 seconds [approvals/hmac_v0.py `MAX_AGE_S`]. A replay inside the window cannot start a second run: one run per key rests on the primary key of the runs table, and the same key with another document is a 409 [worker.py docstring]. A replay of the identical request returns the stored state.
- **Conflict audit.** A signed 409 writes one audit event `trigger.conflict` (run id, principal, key, both payload hashes; never the document or the signature), at most 10 per sender per minute. Refused (unsigned) requests write no audit row, so a caller who cannot sign cannot grow the audit chain [ticket D d-fix6, section "Logged and not logged"].
- **Secret handling.** The worker reads only the secret names listed for its senders, once at start, through `App.trigger_secret`; it is never given the whole secret provider. A secret must meet the minimum length and the same value under two senders is refused. Logs never hold a body, key, header value or secret [worker.py docstring; ticket D invariants 10 and 14].
- **One secret per tenant and per stage.** The tenant is not in the signed string. A secret shared between tenants or stages makes a request for one valid for the other within the 300 second window; the worker sees only its own config, so a reuse on another worker cannot be detected [worker.py docstring; ticket D d-fix18 M3].
- **Slowloris and connection flood.** The server has 256 global connection slots, an absolute read deadline, a header cap of 16382 bytes and a body cap, but no per-peer limit. A reverse proxy with per-peer connection limits is required; TLS is the proxy's job; the worker listens on loopback unless `--allow-non-loopback` is given [server.py and worker.py docstrings].
- **Memory store.** Refused outside the `demo` stage [worker.py `check_store_stage`].
- **After the 2xx.** A run that is cut off ends as NEEDS_PERSON with no notification and no stored document; the sender must poll the run state. This is not "never lost". Whether to store the document and notify is an open owner decision [ESCALATIONS.md E-door-1].

Out of scope: TLS termination, per-peer rate limiting, per-tenant secret separation across workers, the senders' own storage of events (n8n needs queue mode for no event loss), and Windows (not run) [REPORT.md; n8n/README-trigger.md].
