> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-4: what the incident portal may read, and how (data and API contract)

* **Author:** Claude (cloud session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06 (written from about 08:20 UTC / 13:50 IST; IST = UTC+5:30)

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill asks for six reviewer lenses run as fresh sub-agents. This author's brief forbids sub-agents, so none was run, and a review in the same context does not count as a Goldfish review. The "Analysis" below is the author's own stress test against the six lens questions. The real independent check is the ticket's review rounds.
- **AUTO mode.** Every interactive gate (clarifying turns, readiness gate, iteration loop, handoff gate) was skipped, as the lead's brief for this ticket requires. Where the skill would ask, this brief takes the option a FROZEN sibling ticket (AK-G1, AK-G2, AK-G15) already took, and says which.
- **Scope.** Only the data and API contract of the portal (LEAD-ORDERS order 47 item 1, JG-4). The screens are built by the lead on the laptop; nothing here designs a screen. Sign-in itself (AK-G17), approving with a passkey (G14 / JG-5) and the Slack link (JG-3) are other tickets.
- **Sources.** `LEAD-ORDERS.md` orders 23, 27, 43, 47; `tickets/AK-G1.md`, `tickets/AK-G2.md`, `tickets/AK-G15.md` (all FROZEN at revision 3 with build notes); `studio-notes/GAPS.md:13` (G14). Core code read on `ce70eb5` (the last commit that touches `src/`). AK-G17, JG-2 and JG-3 had no ticket text when this was written (`cloud-register.md:655`), so nothing of theirs is cited, only named.

## Overview

Jagrat (the one showcase demo) answers a monitoring alert: it reads the client's cloud, writes a summary, posts it in Slack under the alert, and links to one portal. In the portal a person of the client sees past incidents, opens one, reads what the agent did (masked), sees which proposed changes wait for approval, and chats with the agent. What a person may see depends on their role, which comes from the client's sign-in (AK-G17).

JG-4 is the contract between that portal's screens (the lead's) and our data: the list of requests the screens may make, the exact fields each answer carries, the error codes, and the permission each request needs. Plus a read store interface with an in-memory fake, so the lead can build screens against made-up data before any database work lands.

Who uses it: the lead's portal UI; JG-3 (it builds the link `<base URL>/incidents/<incident id>`); tests.

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **Core records have no tenant today.** `Run` (`src/hadavin_sdk/models.py:90-100`), `ApprovalRequest` (`:160-174`) and `ToolCallRecord` (`:235-247`) carry no `tenant` and no `readers`. Only AK-G1's conversations and turns, AK-G2's receipts and AK-G15's items do. A portal that lists runs or approvals directly could not tell one tenant's from another's. Order 27 item 56 says one deployment per client; that makes it safe today only by deployment, not by data. The contract must reach every tenant-less record THROUGH a record that has a tenant (the alert's receipt), never on its own.
2. **The read paths that exist do not page.** `list_runs(state, updated_before, limit)` (`store/protocol.py:64`), `list_approvals(statuses)` (`:102`), `list_tool_calls(run_id)` (`:125`) and AK-G15's `list_queue_items` (open and claimed only; closed is V13, `tickets/AK-G15.md:197`, `:568`) are worker reads. None is a newest-first, keyset-paged, tenant-filtered history list. A new read interface is needed; changing the `Store` protocol would break every custom store (AK-G1 had to say so, `tickets/AK-G1.md:180`), so the new interface is separate.
3. **The portal database role cannot read most of it.** The existing read-only portal role (`store/migrate.py:23-28`) may SELECT `runs`, `plans`, approvals and audit (`:46-73`), but NOT `tool_calls` (`:63-65`), and the frozen tickets give it nothing on conversations, turns (`tickets/AK-G1.md:181`), queue items or receipts (`tickets/AK-G15.md:262-275`). `redaction_maps` must never be portal-readable (`migrate.py:42-43`).
4. **"Masked" must hold by construction, not by hope.** Some stored fields are masked by their writer: tool-call inputs and output (`models.py:236`, `:242-243`), approval summaries (template-built and redacted, `approvals/requests.py:33-50`), audit events (codes and hashes only, `models.py:188-189`), turns (masked, unsaved placeholders labelled, `tickets/AK-G1.md:166`). Others are not known to be masked: `Plan.inputs` (`models.py:116`), `Run.trigger_ref` (`:95`), `ToolCallRecord.output_sha256` (a hash of the RAW bytes, `:244`; a hash of a short value can be confirmed by guessing). The contract therefore lists every field it returns (an allowlist), never returns those three, and turns every placeholder into its plain label (no put-back, as AK-G1 V3).
5. **Raw model prompts.** Core stores no prompt: no store method holds one (`store/protocol.py:50-141`). The risk is a later ticket adding one and a read model picking it up. A test refuses any answer field named like a prompt, and the field allowlist makes a new field a reviewed change.
6. **Chat posts are writes.** Reading a conversation is a read. Posting a message starts an agent exchange (AK-G1 `handle_turn`), which needs the runtime's rights. A portal process that holds the runtime's rights breaks "one identity per function". This needs a decision (Key decisions D7).
7. **"demo" is not an environment class.** `environment` is the closed safety class `dev | pilot | prod` (`config.py:317`) that drives refusals (`:366`). Order 47 item 5 asks for the name "demo" as a config value. Adding "demo" to the class would change every refusal rule; the name must be a separate display value.
8. **The incident summary has no home yet.** No core record holds an incident summary. JG-3 (or the agent run) writes it; neither has ticket text. The contract names the field and the port that supplies it; where it is stored is a dependency.

**Lens questions, answered briefly.**
- *YAGNI:* screens need 7 reads and 1 write; no search, no export, no filters beyond state, no edit of anything. Approving and queue actions stay in G14 / JG-5 / AK-G15 (their checks already exist there). The HTTP framework is not chosen here (order 47 brief: PENDING LEAD); the contract is plain Python, so the choice can come later.
- *Cost and load:* reads only; page size capped at 100; one incident page = a small fixed number of reads. No model call anywhere in JG-4.
- *UX and developer ergonomics:* one JSON envelope for every answer and every error; closed error codes; opaque cursors; ids only in links. The UI never builds a query string beyond `cursor`, `limit` and `state`.
- *Migration:* JG-4-a adds no table and changes no existing record. JG-4-b adds views and `GRANTS` rows only (additive).
- *Observability:* one log line per request: route id, outcome code, duration, counts; never text, never a person id (as AK-G1's log rule).
- *Tech debt:* the read interface is separate from `Store`; the field allowlist is one module; every DTO is a pydantic model with `extra="forbid"`, like core records.

## Goals vs. Non-Goals

* **In-Scope Goals:** the endpoint list, request and answer shapes (DTOs), error codes, the permission each endpoint needs, the tenant and reader checks, keyset paging, the masking allowlist, the read interface `PortalReads` with an in-memory fake (JG-4-a); the Postgres read adapter, its views and portal grants (JG-4-b); config `portal.base_url`, `portal.environment_name`; a permission test table (who sees what).
* **Out-of-Scope Non-Goals:** screens and their look (lead); sign-in, sessions and role mapping (AK-G17); approve and reject, and the passkey step (G14 / JG-5); claim and close of "needs a person" items (AK-G15 `StoreQueue`); the Slack message (JG-3); a multi-tenant deployment (order 27 item 56); search, export, edits; the HTTP framework adapter (PENDING LEAD).

## Alternatives Weighed

- **Add `tenant` to `runs`, `approval_requests`, `tool_calls` now.** Rejected by author: changes three frozen-era tables and every writer for a case that order 27 item 56 excludes (one deployment per client); the portal reaches them through the receipt instead. Kept as a v1.1 row with the trigger "before a deployment serves two tenants".
- **Extend the `Store` protocol with paged reads.** Rejected by author: every custom store would fail `missing_methods` at start (AK-G1 had to state this cost, `tickets/AK-G1.md:180`). A separate `PortalReads` interface is used, as AK-G15 kept its Postgres helpers out of the protocol (`tickets/AK-G15.md:194`).
- **A portal-side link table between incidents and conversations.** Rejected by author: a new table and a new writer. The conversation id is derived from `(tenant, incident id, user id)` with core's `tenant_key` pattern (AK1), so the portal can fetch it without a list.
- **Show tool output in full, unmasked, to admins.** Rejected by author: the owner's masking rule has no admin exception, and the unmasked value is not stored (only the map, which is never portal-readable).
- **Grant the portal role whole tables.** Rejected by author: column-limited views keep `output_sha256`, `mapping`, `body` and person ids out of reach at the database, not only in Python.
- **Choose an HTTP framework in this ticket.** Rejected by author: the lead's brief makes it PENDING LEAD; core uses only the standard-library server today (`approvals/receiver.py:12`, `:40-65`) and has no web framework dependency (`pyproject.toml` dependencies).

## Key Decisions & Staging for Next Steps

- **D1 An incident is one alert receipt.** Incident = one AK-G2 `InboundReceipt` (`tickets/AK-G2.md:142`: `tenant`, `source`, `readers`, `delivery_key`, `run_id`, `state`, `received_at`) from a source that JG-2 marks as an alert source. `incident_id = "inc-" + delivery_key[:32]` (same shape as AK-G2's `item_id`). Its runs are the receipt's `run_id` for each generation. Everything else (tool calls, approvals, audit events, queue items, chat) is reached from that run id or from the tenant key. (Chosen like AK-G15, which keys items on the receipt, `tickets/AK-G15.md:191`.)
- **D2 Tenant check twice.** The signed-in session's tenant (AK-G17) must equal the deployment's configured tenant AND the record's tenant. A record of another tenant, a missing record and a record the person may not read all give the same `not_found` (no hint that it exists), as AK-G1's reads do (`tickets/AK-G1.md:168`).
- **D3 Readers: the tenant's CURRENT config readers decide.** Same rule as AK-G15 PL18 (a) (order 43 item 18); stored `readers` are a record only.
- **D4 Permissions are a closed list owned by JG-4; AK-G17 maps roles onto them.** `incidents.read`, `incidents.tool_calls`, `approvals.read`, `queue.read`, `chat.read`, `chat.write`. No `approve` here (G14 / JG-5 with passkey). A missing permission on a list gives `forbidden`; on a single record, `not_found`.
- **D5 Masking by allowlist.** Every answer field is listed; text fields come only from writers that mask; every placeholder becomes its label; `Plan.inputs`, `Run.trigger_ref`, `output_sha256`, redaction maps and any prompt are never returned.
- **D6 Paging.** Keyset cursor over `(time, id)`, newest first, `limit` 1-100 (default 25), as AK-G15's `after` cursor (`tickets/AK-G15.md:197`). The cursor is opaque base64 of JSON; a bad one gives `bad_request`. No signing needed: filters run on the server, so a forged cursor only moves within the person's own rows.
- **D7 Chat posts go through a `ChatPort`.** Neutral default (dev only): in-process call to AK-G1 `handle_turn`; refused when `environment` is not `dev`. Alternative (outline, trigger "before any pilot"): post to the AK-G2 signed door so only the runtime identity runs the exchange. PENDING LEAD.
- **D8 Config.** `portal.base_url` (https, no path beyond `/`, validated), `portal.environment_name` (pattern `[a-z][a-z0-9-]{0,31}`, the demo sets "demo"), `portal.tenant`. The safety class `environment` is unchanged; the demo runs as `dev`. PENDING LEAD (mapping "demo" to `dev`).
- **D9 HTTP framework: PENDING LEAD.** Recommendation in the design.
- **Staging:** JG-4-a (contract, DTOs, permissions, service, in-memory fake, tests) can start once AK-G1-a, AK-G2-a and AK-G15-a records exist in code (it imports their record types) and AK-G17 publishes its session type; JG-4-b (Postgres views, grants) after those migrations merge.
