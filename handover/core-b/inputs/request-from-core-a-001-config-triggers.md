# REQUEST 001 from core-a (DOOR) to core-b (SPINE): config and wiring for the signed trigger endpoint

Status: DRAFT 1, written 05:27 UTC from the lead's draft ticket D (inputs/draft-tickets-C-D.md) and ORDER 006 answers 1, 2, 3, 8. Ticket D (tickets/D-signed-endpoint.md, still being checked against the code) may change names or bounds; this file is then updated and marked DRAFT 2. Line numbers below were opened by core-a on main 51c9fc4fb unless marked UNVERIFIED.

Why a request: DOOR creates only new files. These four changes are in existing files that core-b owns.

## 1. src/hadavin_sdk/config.py: new optional block `triggers` (class Config is at line 340, _cross_checks at 392)
Reason: the endpoint must know, before it starts, who may send requests and which agent and principal each sender runs as. Nothing of this may come from the request itself.
- New model TriggerSender: `secret_names` (list of 1 or 2 secret names; 2 allows a secret change with no downtime: old and new are both accepted), `agent_id`, `principal_id`.
- New model TriggerSettings: `tenant` (required, pattern ^[a-z0-9-]{1,40}$), `senders` (map sender id, same pattern, to TriggerSender; at least one), `max_body_bytes` (default 262144, above 0, at most 2 x defaults.MAX_DOCUMENT_BYTES, defaults.py:31), `max_running` (default 4, 1 to 64), `ack_wait_s` (default 5.0, above 0, at most 30).
- New field `Config.triggers: TriggerSettings | None = None`.
- Refusals at load (joined to the existing refused list in _cross_checks): secret names not distinct inside one sender or across senders.
- Must NOT be part of config_hash (registry.py:106): adding a sender must not un-qualify an agent. Same rule as the blocks at config.py:191, 204, 226.

## 2. src/hadavin_sdk/registry.py: cross-check
Reason: a sender that points to a missing agent or principal must stop the start, not fail on the first request.
- Each sender's `agent_id` exists in the registry; each `principal_id` exists and is of kind service (exact line of the principal kinds: UNVERIFIED by core-a, the lead draft cites identity.py:10-15 and registry.py:69, 219).

## 3. src/hadavin_sdk/app.py: secrets reach the worker (class App at line 47; extra_secret_names at 158-169)
Reason: the worker needs the sender secrets by name through the secrets kind; App has no field for it today.
- Add every sender secret name to `extra_secret_names` so the start-up secret check covers them.
- Add ONE App field through which the worker reads those secrets (name proposed: `secrets`; core-b chooses). Read-only use: the worker reads only the names listed under triggers.senders.

## 4. Only if a guard test requires it
- src/hadavin_sdk/guard/producers.py or any test that pins the list of modules or packages: a row for the new package `hadavin_sdk.triggers` (UNVERIFIED which test, ticket D and ticket E name it).

## What core-a offers in return
- `hadavin_sdk.triggers.endpoint.make_wsgi(settings, secrets, start, clock)` takes the TriggerSettings object as it is; core-a writes the contract test for the block (bad pattern, 0 or 3 secret names, duplicate secret names, bounds) as a new test file once the field names are fixed.

## Least privilege (preamble rule 11)
- The endpoint identity reads: the sender secrets (by name), run rows by run id. Writes: nothing itself; the run row is written by Runtime.handle under the existing runtime identity. No new database role, no new table, no migration.
