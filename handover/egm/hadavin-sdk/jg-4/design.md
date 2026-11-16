> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-4: incident portal data and API contract

* **Author:** Claude (cloud session, `egm:egm-draft`, AUTO mode)
* **Date:** 2026-11-06 (from about 08:35 UTC / 14:05 IST)
* **Input:** `concepts_brief.md` in this folder (same author, same session).
* **Status:** draft for the JG-4 ticket rounds. Not reviewed.

**Honest notes.** (1) AUTO mode: every section gate, the "author decides architecture" gate and the save-location gate were skipped, as the lead's brief requires. Where the skill would ask, the option a FROZEN sibling ticket took is used and named ("as AK-G15", and so on); choices no sibling covers are marked PENDING LEAD with a recommendation. (2) The skill's `resources/execution_instructions.md` is missing from the installed plugin (`skills/egm-draft/resources/` does not exist); the SKILL.md steps and `references/design_doc.md` were followed instead. (3) No Goldfish has read this. (4) AK-G17, JG-2, JG-3 and JG-5 have no ticket text yet; what JG-4 needs from them is written here as a contract they must meet, marked UNVERIFIED until their tickets say so.

## Overview

One portal per client deployment, at one configured address (for the demo, a "demo" deployment). A signed-in person of the client sees: the incident history, one incident's detail (what the agent did, masked, and the summary), the changes waiting for approval, the items waiting for a person, and a chat with the agent about that incident. JG-4 defines the requests the portal screens make and the answers they get, and the checks our code makes before answering. It does not draw screens.

## The Problem

Order 47 asks for a portal that holds history and past incidents in one place, shows only what each person may see, and lets the client chat by their own permissions. The pieces of data exist or are being built (runs, tool calls, approvals and audit in core; receipts in AK-G2; "needs a person" items in AK-G15; conversations in AK-G1), but:
- there is no read path that pages, filters by tenant and checks a person's permission;
- three core records (`Run`, `ApprovalRequest`, `ToolCallRecord`; `src/hadavin_sdk/models.py:90-100`, `:160-174`, `:235-247`) have no tenant;
- the read-only portal database role (`store/migrate.py:23-28`) cannot read tool calls (`:63-65`) or any of the new kit tables (`tickets/AK-G1.md:181`; `tickets/AK-G15.md:262-275`);
- some stored fields are not known to be masked (`Plan.inputs`, `models.py:116`; `Run.trigger_ref`, `:95`) and one is a hash of raw bytes (`ToolCallRecord.output_sha256`, `:244`).

Without a contract the lead's UI would read tables directly, and every one of those gaps would become a leak.

## Goals

1. Eight requests (seven reads, one chat post), each with a fixed answer shape, a closed set of error codes and exactly one permission.
2. Tenant isolation in the data access, not only in the screen: every read takes the tenant and returns nothing for another tenant.
3. Nothing in any answer that a masking writer did not produce; no raw prompt, no redaction map, no raw-byte hash; placeholders shown as labels.
4. Newest-first keyset paging on every list.
5. A read interface with an in-memory fake, so screens and tests run on made-up data before any database work.
6. One portal address and one environment display name from config.

## Non-Goals

- Screens, layout, styling (the lead, laptop, order 47).
- Sign-in, sessions, the role-to-permission mapping, SCIM (AK-G17).
- Approve and reject, and the passkey step-up (G14 / JG-5).
- Claim, release, close and reopen of "needs a person" items (AK-G15 `StoreQueue`).
- The Slack threaded reply (JG-3); it only uses `incident_url()` from here.
- More than one tenant per deployment (order 27 item 56).
- Search, filters beyond `state`, export, editing anything, live push (polling only).
- Choosing the HTTP framework (PENDING LEAD, see Open Questions).

## Open Questions (each with a recommendation; PENDING LEAD)

- **PL1 HTTP framework.** Core has none: only the standard-library server in `approvals/receiver.py:12`, `:40-65`, and no web dependency in `pyproject.toml`. Options: (a) JG-4 ships the framework-free contract only; the route table is data; contract tests call `PortalAPI` directly; a later adapter ticket adds the server. (b) Same as (a) plus an ASGI adapter in its own kind module (`portal/web_asgi.py`) on one maintained framework, with the standard-library adapter as the no-dependency alternative. (c) The lead's UI server calls `PortalAPI` in-process. **Recommendation: (a) now**, because it adds no dependency and does not block the lead; (b) as the next ticket, after an AK0-style licence and maintenance check (order 27 item 53), with the framework name UNVERIFIED until that check.
- **PL2 Chat post identity.** Options: (a) `ChatPort` default calls AK-G1 `handle_turn` in-process, allowed only when `environment == "dev"`; (b) the portal posts the message to AK-G2's signed door, so only the runtime identity runs the exchange. **Recommendation: (a) for the demo, (b) required before any pilot** (v1.1 row V2), because (a) gives the portal process the runtime's rights.
- **PL3 "demo" and the safety class.** `environment` stays `dev | pilot | prod` (`config.py:317`). **Recommendation:** the demo runs with `environment: dev` and `portal.environment_name: demo`; the name is shown in every answer and never used in a rule.
- **PL4 Where the incident summary is stored.** No core record holds it. **Recommendation:** JG-3 (or the agent run that writes it) stores it masked, keyed by run id, behind the `SummarySource` port defined here; until then the field is `null` and the fake returns made-up masked text.
- **PL5 Which sources are alert sources.** **Recommendation:** config `portal.incident_sources` (a list of AK-G2 source names, pattern as AK-G2 `tickets/AK-G2.md:179`, 1 to 20 entries); JG-2 names its source there.

## Critical User Journeys (CUJs)

### CUJ 1: open the incident from Slack
A responder clicks the link under the alert in Slack (JG-3 builds it as `incident_url(incident_id)`). The browser opens `<base_url>/incidents/<incident_id>`; the UI calls E2, then E3, E4 (filtered to this incident), E6. With `incidents.read` but not `incidents.tool_calls`, E3 answers `forbidden` and the UI hides that panel.

### CUJ 2: a viewer of another tenant guesses an id
They call E2 with a real incident id of tenant B. The session tenant is A: the answer is `not_found`, the same bytes as for an id that never existed.

### CUJ 3: chat about the incident
A person with `chat.read` and `chat.write` posts `{message_id, text}` to E7. The answer is `accepted`, `retry` or `handed_off`. The reply is read with E6 (polling), as masked text with labels.

## Technical Plan (Architecture)

```
 lead's UI ──HTTP (adapter: PENDING LEAD PL1)──► PortalAPI (route table, checks, DTOs)
                                                   │ Viewer (from AK-G17 session)
                                                   ▼
                                          PortalReads  ◄── memory fake (JG-4-a)
                                                   │    ◄── Postgres views, portal role (JG-4-b)
                     ChatPort ──► AK-G1 handle_turn (dev only)   SummarySource ──► JG-3 (PL4)
```

**Modules (new package `src/hadavin_sdk/portal/`).**
- `portal/contract.py`: permissions, error codes, DTOs, the route table.
- `portal/service.py`: `PortalAPI`, the only place that checks permissions, tenant and readers and builds DTOs.
- `portal/reads.py`: `PortalReads` protocol and `MemoryPortalReads`.
- `portal/postgres_reads.py` (JG-4-b): `PostgresPortalReads`, run under the portal role.
- `portal/fields.py`: the masking allowlist and `to_labels(text)`.

**The viewer.** `Viewer(principal_id: str, tenant: str, permissions: frozenset[Permission])`, frozen. AK-G17 builds it from a valid session; JG-4 never reads a cookie or token. `__repr__` shows the tenant and the permission count only. Contract for AK-G17 (UNVERIFIED until its ticket): a Viewer exists only for a signed-in person, `principal_id` is the opaque id AK-G17 issues (never an e-mail address), `permissions` is a subset of `PERMISSIONS`.

**Permissions (closed list, `PERMISSIONS`).**

| Permission | Allows |
|---|---|
| `incidents.read` | E1, E2 |
| `incidents.tool_calls` | E3 |
| `approvals.read` | E4 |
| `queue.read` | E5 |
| `chat.read` | E6 |
| `chat.write` | E7 (also needs `chat.read`) |

E8 (`/me`) needs only a Viewer. There is no admin permission and no wildcard; an unknown permission string from AK-G17 is a `ConfigError` at start (load rule), never ignored.

**Checks, in this order, for every request (one function `_guard`).**
1. Viewer present, else `unauthenticated`.
2. `viewer.tenant == config.portal.tenant`, else `not_found` (single records) or `forbidden` (lists). Said plainly: a session of another tenant can only reach this deployment through a sign-in bug in AK-G17; this check makes that bug fail closed.
3. The route's permission is in `viewer.permissions`, else `forbidden` for lists and `not_found` for single records.
4. `viewer.principal_id` is in the tenant's CURRENT config readers (as AK-G15 PL18 (a), `tickets/AK-G15.md:143`; config field name UNVERIFIED, the builder uses AK1's merged `Readers`), else as step 3.
5. Parameters: `limit` 1-100 (default 25), `cursor` decodes, `state` in its closed set, ids match their patterns; else `bad_request`.
6. The read itself always passes `tenant`; a record whose tenant differs is treated as missing (defence in depth for the memory fake and custom backends).

**Endpoints (paths relative to `base_url`; all answers JSON).**

| Id | Method and path | Permission | Answer |
|---|---|---|---|
| E1 | `GET /api/v1/incidents?cursor&limit&state` | `incidents.read` | `Page[IncidentSummaryDTO]` |
| E2 | `GET /api/v1/incidents/{incident_id}` | `incidents.read` | `IncidentDTO` |
| E3 | `GET /api/v1/incidents/{incident_id}/tool-calls?cursor&limit` | `incidents.tool_calls` | `Page[ToolCallDTO]` |
| E4 | `GET /api/v1/approvals?status&incident_id&cursor&limit` | `approvals.read` | `Page[ApprovalDTO]` |
| E5 | `GET /api/v1/queue?state&cursor&limit` | `queue.read` | `Page[QueueItemDTO]` |
| E6 | `GET /api/v1/incidents/{incident_id}/chat?before&limit` | `chat.read` | `ChatDTO` |
| E7 | `POST /api/v1/incidents/{incident_id}/chat/messages` | `chat.write` + `chat.read` | `ChatPostDTO` |
| E8 | `GET /api/v1/me` | (signed in) | `MeDTO` |

**Envelope.** Every answer: `{"environment_name": str, "data": <DTO> | null, "error": {"code": str} | null}`. No error message text (codes only; the UI owns wording). HTTP status per code: `unauthenticated` 401, `forbidden` 403, `not_found` 404, `bad_request` 400, `conflict` 409, `retry` 503, `internal` 500. An exception inside `PortalAPI` becomes `internal` with one ERROR log line (route id and exception class name only).

**DTOs (pydantic, `extra="forbid"`, frozen). Every field listed; nothing else is ever returned.**
- `Page[T]`: `items: list[T]`, `next_cursor: str | None`.
- `IncidentSummaryDTO`: `incident_id`, `source`, `state` (receipt state, AK-G2's closed set), `received_at`, `run_state: RunState | None` (latest generation's run), `pending_approvals: int`, `open_queue_items: int`.
- `IncidentDTO`: the summary fields plus `runs: list[RunDTO]` (one per generation, oldest first), `timeline: list[TimelineEntryDTO]` (newest last, at most `defaults.PORTAL_TIMELINE_MAX` = 500 entries, then `timeline_truncated: true`), `summary: str | None` (from `SummarySource`, through `to_labels`), `chat_available: bool`.
- `RunDTO`: `run_id`, `generation`, `state`, `reason_code`, `created_at`, `updated_at`. NOT `principal_id`, `trigger_ref`, `cost_usd` (cost is not for client viewers in v1, V5).
- `TimelineEntryDTO`: `ts`, `kind` (`run_state` | `audit` | `tool_call` | `approval`), `run_id`, `code` (an audit `domain/operation`, a run state, a tool name, or an approval status), `decision: str | None`. From `audit.events(run_id)` (`audit/protocol.py:33`; hashes and codes only, `models.py:188-189`); never `inputs_hash`, `principal`, `object_ref`.
- `ToolCallDTO`: `call_id`, `run_id`, `tool`, `inputs` (`to_labels` applied to every string leaf), `output` (`to_labels`), `created_at`, `duration_ms`, `error`. NOT `output_sha256`, `attempt`.
- `ApprovalDTO`: `approval_id`, `run_id`, `incident_id`, `status`, `risk_class`, `summary` (stored `ApprovalRequest.summary`, template-built and redacted, `approvals/requests.py:33-50`, then `to_labels`), `current_step`, `step_count`, `step_expires_at`, `created_at`. NOT `plan_hash`, `chain_id`, `steps` (approver names), `requested_by`, `channel_ref`, and never `Plan.inputs`.
- `QueueItemDTO`: `item_id`, `kind`, `state`, `reason`, `round`, `opened_at`, `incident_id: str | None` (inbound items), `claimed: bool`. NOT `assignee`, `readers`, `binding`, `idempotency_key` (AK-G15 record fields, `tickets/AK-G15.md:218`).
- `ChatDTO`: `conversation_state: "none" | "open" | "handed_off"`, `turns: list[TurnDTO]` (oldest first), `before: int | None` (cursor for older turns).
- `TurnDTO`: `turn_no`, `role`, `text` (`to_labels`), `fixed`, `created_at`. NOT `message_id`, `run_id`, `readers`.
- `ChatPostDTO`: `outcome: "accepted" | "duplicate" | "retry" | "handed_off" | "refused"`.
- `MeDTO`: `principal_id`, `permissions` (sorted list), `environment_name`, `base_url`.

**Masking rule (`portal/fields.py`).** `to_labels(text)` replaces every placeholder token (the P5c pattern, `<KIND_N>`; pattern name UNVERIFIED until P5c merges) with the label `[hidden kind]` and is applied to every free-text field above. Free text is taken ONLY from these writers: tool-call `inputs` and `output` (stored redacted, `models.py:236`, `:242-243`), `ApprovalRequest.summary`, AK-G1 turn `text` (masked, `tickets/AK-G1.md:166`), and `SummarySource` (contract: masked, PL4). `PORTAL_FIELDS`, a dict from DTO name to its field names, is the single allowlist; a test compares it with each DTO's `model_fields`, and a test refuses any field whose name contains `prompt`, `message` (except `ChatPostDTO` has none), `system`, `mapping`, `sha256`, `secret`, `token`.

**Incident identity and how each read model is backed.**

| Read model | Backed by (record, where defined) | Tenant from |
|---|---|---|
| Incident list and detail | AK-G2 `inbound_receipts` (`tickets/AK-G2.md:142`), `source in portal.incident_sources`; `incident_id = "inc-" + delivery_key[:32]` | receipt `tenant` |
| Runs | core `runs` (`store/migrations/0001_core.sql:5`, `models.py:90`) by the receipt's `run_id` (AK-G2 `run_id_for`, `tickets/AK-G2.md:158`) for each generation | the receipt |
| Timeline | core audit `events(run_id)` (`audit/protocol.py:33`) plus run state and tool calls and approvals of those runs | the receipt |
| Tool calls | core `tool_calls` (`0005_evidence.sql:5`; `list_tool_calls`, `store/protocol.py:125`) | the receipt (via run id) |
| Approvals | core `approval_requests` (`0001_core.sql:46`; `list_approvals`, `store/protocol.py:102`), only rows whose `run_id` is a run of an incident of the tenant | the receipt (via run id) |
| Queue items | AK-G15 `queue_items` (`tickets/AK-G15.md:218`; `list_queue_items`, `:197`) | item `tenant` |
| Chat | AK-G1 `conversations` and `turns` (`tickets/AK-G1.md:165-166`; `get_conversation` `:170`, `list_turns`) | conversation `tenant` |
| Summary | `SummarySource` (PL4) | the receipt |

The chat conversation id is `"conv-" + sha256_hex(tenant_key(tenant, "portal-chat", incident_id, principal_id))[:32]`, so the portal finds it with `get_conversation(tenant, id, reader=principal_id)` and needs no list method and no link table. The first E7 creates it (`create_conversation`; `ConversationConflict` means it already exists and is ignored). AK-G1's own rule that only the owner may post (`tickets/AK-G1.md:112`) holds because the owner is the viewer.

**`PortalReads` (new protocol; NOT part of `Store`, so custom stores are untouched, as AK-G15 kept its helpers out, `tickets/AK-G15.md:194`).**
1. `list_incidents(tenant, sources, *, states, after, limit) -> list[IncidentRow]` newest `received_at` first, then `delivery_key`.
2. `get_incident(tenant, sources, incident_id) -> IncidentRow | None`.
3. `runs_of(tenant, incident_id) -> list[Run]`.
4. `list_tool_calls(tenant, run_ids, *, after, limit) -> list[ToolCallRecord]`.
5. `list_approvals(tenant, sources, *, statuses, incident_id, after, limit) -> list[ApprovalRow]` (the join to receipts happens in the read, not in Python after it).
6. `list_queue_items(tenant, *, states, after, limit) -> list[NeedsPersonItem]` (newest first; `closed` allowed here, read-only, closing AK-G15's V13 for the portal only; the Postgres view adds its own index).
7. `audit_codes(tenant, run_ids, limit) -> list[AuditEvent]`.
8. `counts(tenant, incident_ids) -> dict[str, tuple[int, int]]` (pending approvals, open items) for one list page in one read.
Chat reads use AK-G1's own store methods (they already filter by tenant and reader).

**JG-4-b Postgres.** One migration adds views `portal_incidents`, `portal_tool_calls`, `portal_queue_items`, `portal_turns`, `portal_conversations` with ONLY the columns the DTOs need (no `output_sha256`, `mapping`, `body`, `assignee`, `readers`, `user_id`, `binding`, `idempotency_key`), each with `GRANTS` rows `Grant("view", "", portal=True)` (pattern `store/migrate.py:46-73`). No table grant changes; `redaction_maps` stays unreadable (`:42-43`). The views are `security_barrier`; every query has `tenant = %s` in its `WHERE`.

**Paging.** Cursor = urlsafe base64 of canonical JSON `{"v":1,"t":<iso time>,"k":<id>}`; decoding refuses any other shape, any extra key, more than 256 characters. Newest first by `(time DESC, id DESC)`. For chat, `before` is a turn number (int ≥ 2).

**Config (`config.py`, new `PortalSettings`, optional; absent = no portal).** `base_url: str` (`https://` only, host required, path `/` or empty, no query, no fragment; `http://localhost` and `http://127.0.0.1` allowed only when `environment == "dev"`), `environment_name: str` (`[a-z][a-z0-9-]{0,31}`), `tenant: str` (AK1 `TENANT_PATTERN`), `incident_sources: list[str]` (1-20). `incident_url(incident_id) -> str` is the only function that builds a portal link (JG-3 uses it).

**Logging.** One INFO line per request: route id, outcome code, duration in ms, item count. Never a principal id, tenant, query value, text or exception message.

## Alternatives Considered

### Alternative A: add `tenant` to `runs`, `approval_requests`, `tool_calls`
Rejected by author: three core tables and every writer change for a case order 27 item 56 excludes. Reaching them through the tenant-bearing receipt gives the same isolation for one-tenant deployments. v1.1 row V1, trigger "before one deployment serves two tenants".

### Alternative B: add paged reads to the `Store` protocol
Rejected by author: every custom store would fail at start (`missing_methods`, `tickets/AK-G1.md:180`). Separate `PortalReads`.

### Alternative C: a link table from incidents to conversations
Rejected by author: a new table and writer; the derived conversation id needs neither.

### Alternative D: unmasked tool output for an admin role
Rejected by author: the owner's masking rule has no admin exception; the originals live only in `redaction_maps`, which the portal role must never read.

### Alternative E: grant the portal role whole tables
Rejected by author: column-limited views keep raw-byte hashes, maps, bodies and person ids out at the database.

### Alternative F: choose the HTTP framework here
Rejected by author: the lead made it PENDING LEAD; see PL1.

### Alternative G: signed cursors
Rejected by author: the server filters by tenant and permission on every page, so a forged cursor only moves within rows the person may already see; signing adds a key to manage for no gain.

## Non-Functional Requirements

- **Security (authorization path; extended review, no round cap):** deny by default; one permission per route; same `not_found` for missing, other tenant and not allowed; field allowlist; column-limited views; no write except E7 through `ChatPort`.
- **Isolation:** two-tenant canary test on the memory fake and on Postgres (JG-4-b): tenant B's rows never appear for tenant A, with colliding ids (R369).
- **Load:** each read is one query (Postgres) or one pass (memory); a list page is at most 3 reads (list, counts, nothing else). Target, measured in JG-4-b evidence on made-up data: E1 p95 under 50 ms at 10,000 receipts per tenant, 3 tenants (UNVERIFIED until measured).
- **Privacy:** no person id or text in logs; `MeDTO` returns the viewer's own id only.

### Future Improvements (v1.1 rows)
V1 tenant columns on core tables; V2 chat through AK-G2's door (required before pilot); V3 live push; V4 search and filters; V5 cost per incident for a cost role; V6 HTTP adapter (PL1 (b)); V7 a second deployment per client (staging).

## Detailed Implementation Plan

### Target Files to Create/Modify

#### JG-4-a
1. `src/hadavin_sdk/portal/__init__.py` (Create): package marker; exports `PortalAPI`, `Viewer`, `PERMISSIONS`.
2. `src/hadavin_sdk/portal/contract.py` (Create): permissions, error codes and HTTP statuses, DTOs, `ROUTES` (id, method, path pattern, permission).
3. `src/hadavin_sdk/portal/fields.py` (Create): `PORTAL_FIELDS`, `to_labels`.
4. `src/hadavin_sdk/portal/reads.py` (Create): `PortalReads` protocol, row types, `MemoryPortalReads` (built from a `MemoryStore` plus AK-G2 and AK-G15 memory records).
5. `src/hadavin_sdk/portal/service.py` (Create): `PortalAPI(config, reads, store, audit, chat: ChatPort, summaries: SummarySource)`, `_guard`, one method per route, cursor codec, `incident_url`.
6. `src/hadavin_sdk/portal/ports.py` (Create): `ChatPort`, `SummarySource` protocols; `InProcessChat` (dev only; refuses at construction when `environment != "dev"`); `NoSummaries`.
7. `src/hadavin_sdk/config.py` (Modify): `PortalSettings`, optional `portal` field, validators.
8. `src/hadavin_sdk/defaults.py` (Modify, own block `# --- portal (JG-4-a) ---`): `PORTAL_PAGE_DEFAULT = 25`, `PORTAL_PAGE_MAX = 100`, `PORTAL_TIMELINE_MAX = 500`, `PORTAL_CURSOR_MAX = 256`.
9. `tests/test_portal_permissions.py`, `tests/test_portal_isolation.py`, `tests/test_portal_masking.py`, `tests/test_portal_paging.py`, `tests/test_portal_chat.py`, `tests/test_portal_config.py` (Create; flat layout, as `tests/` is today): the rows in the ticket.
10. `CHANGELOG.md` (Modify, append).

#### JG-4-b
11. `src/hadavin_sdk/portal/postgres_reads.py` (Create): `PostgresPortalReads` under the portal role.
12. `src/hadavin_sdk/store/migrations/<next>_portal_views.sql` (Create, number at merge, A3): the five views.
13. `src/hadavin_sdk/store/migrate.py` (Modify): five `GRANTS` rows.
14. `tests/contracts/test_portal_reads.py` (Create; next to `tests/contracts/test_store.py`): contract suite shared with the memory fake; grants and negative grant tests; the canary and the load plan.

### Verification Plan
All rows and mutants of the ticket; `ruff check`, `ruff format --check`, `bandit -ll`, repo guard tests; for JG-4-b, PostgreSQL 16 and 17 (order 27 item 46).
