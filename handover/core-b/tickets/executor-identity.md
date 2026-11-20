# TICKET DRAFT executor-identity: a separate executor identity in pilot and prod (owner core-b SPINE)

- Source: QUEUE.md row Q17 (full text read). DRAFT ONLY: no source edited, nothing run, nothing committed. The EGM plan review of this ticket is ordered in ORDER 003.
- Path class: security (extended review: yes). Migration: NONE proposed (see "Migration number needed"; the lead is asked).
- Depends on (merged first): step B (the `reset` slot of `Grant` and the `reset_role` parameter of `migrate()` are the pattern and share the lines), F-store (the `release` slot, same lines). Written 2026-11-20 against the tree at /home/user/hadavin-sdk as it stands now (migrations 0001 to 0008 present). S = `src/hadavin_sdk`.
- Tests are written by a different agent than the builder. Code goes in commits named "code executor-identity: ...".

## Purpose in plain words
Today one program holds everything. The same process that talks to the model, writes run state and reads the secret store also builds the part that holds a client's secret and performs an approved action (the executor). In demo that is fine. In pilot and prod the core currently performs NO action (the executor is None; http contracts are refused), so the problem is not live yet. The day a client wants the core to perform approved writes, the executor must not share a login or a secret store with the runtime: a runtime that is confused or taken over must not be able to read the client's action secret or to write as the executor. This ticket defines that separate identity, using the same pattern as the purge, reset and release identities: its own database role with the fewest rights, its own connection string kept as a secret the runtime never reads, and a start-up refusal when the two meet.

## NEEDED-CHECK (files and lines read, 2026-11-20)
- ONE-PLACE-PER-JOB: rights are in `GRANTS` (store/migrate.py); a second login is wired by a `*_credential_ref` field (backends/table.py); secrets reach only the executor through `SecretProvider`. This ticket adds a slot and a field in those places and builds no second grant mechanism.
- Read: `S/actions/executor.py` 1-179. The executor "holds a client-system secret" (docstring 1-5); `Executor.__init__` takes the one `SecretProvider` (47-51); `_caller` reads the action secret at 63; `execute` returns a `RunResult` and never writes run state (94-148, docstring 1-5). It holds no database connection of its own and no identity: it is a class called in-process.
- Read: `S/app.py` 45-62 (`App.executor: Executor | None`, comment "None in pilot and prod: Hadavin executes nothing there"), 152-155 (`executor_names` = secret names of http contracts), 174-204 (sender, release and reset refs refused if a tool, source or executor secret carries the same name; `platform_secrets.check`), 228-255 (the SAME `secrets` provider builds signer, anchor, store, audit, llm, channel AND the Executor at 254-256: one provider, one process), 289-293 (hooks: `execute`, `verify`, `rollback` are bound only when an executor exists).
- Read: `S/backends/platform_secrets.py` 1-64 and 67-97. `check()` at 59-64 reads EVERY platform name AND every executor name once at start-up in the building process; so a runtime that builds with executor names resolves the client's action secret itself. `bound()` 24-34 limits a backend to its own `*_secret_name` fields. Nothing here makes an identity for the executor.
- Read: `S/deferred.py` 46-60 (`check`): an http contract is refused in pilot and prod ("not available in pilot or prod until Phase 2", 53-56); manual is refused everywhere (51-52); level `act` is refused (82-83).
- Read: `S/runtime/agent_loop.py` 811-826 (`execute` ends NEEDS_PERSON `executor_not_configured` when `hooks.execute` is None, so a live run is safe) and 176-178 (`Hooks`).
- Read: `S/identity.py` 1-15: only `Principal` (person or service with rights and approver roles). It is a caller identity for the gate, not a database or secret identity.
- Read: `S/store/migrate.py` 1-80 (`Grant` with `purge`, `purge_cols`, `reset`, `release` slots; the `GRANTS` map; `RELEASE_FUNCTION`), 209-215 (`effective_problems`), 402-470 (`migrate(...)` roles tuple at 415, the purge block at 466-470). `S/store/migration_numbers.py` 1-20 (the numbering rule; the last file on disk is `0008_release_expired_spend.sql`). `S/store/migrations/0006_stop_state.sql` 1-30 (append-only tables with a UUID id; pattern for an append-only table).
- Read: `S/backends/table.py` 120-128 (`purge_dsn_secret_name`, `reset_credential_ref`, `release_credential_ref`; the two refs deliberately do not end in `_secret_name`).
- Read: `docs/stop-state-runbook.md` 1-123 (the role set-up recipe, "the secrets policy of the runtime's identity must NOT list the secret" at 18-21 and 101-104, the migrate role-difference check at 8-16, the limits "owner and superuser are outside the guarantee" at 49-50).
- Read: handover/core-b/PLAN-READBACK.md 1-42 (my steps; "no live executor" at line 22, no tier 2 code), LANE-MAP.md 24, 35, 63, 150, 242 (executor identity line, migrate and executor rows, runtime grants), tickets/B-stop-state.md 25-54 and 85-125 (NEEDED-CHECK, invariants and `reset` slot pattern), tickets/F-store.md 108-124, 184 and 357-370 (GRANTS row pattern, Out list), inputs/review-plan-1-codebase.md 7 and 18 (finding: no executor identity exists; B1 asks for one explicit ticket), inputs/plan-v2.md 26 (AK-G15 deferred, trigger: a client wants the core to perform writes).
- Other tools: n8n or Make could hold the client secret and perform the write themselves (the client's own tool as the executor, which is the plan's default: "the client's tool may only notify", old-plan-v4-3.md 400). Neither can give a database role, a start-up refusal or the append-only audit of the act. A free library does not exist for "the runtime may not read this secret"; the guard is the secret store's own access policy plus a start check. The CRM is not involved.
- Module already in src/hadavin_sdk that does it? NO. The purge, reset and release identities show the pattern but none covers executing an action. `Principal` is not a login.
- VERDICT: NEEDED, CONDITIONAL. Needed as soon as the owner lifts the deferral that lets the core perform writes in pilot or prod (AK-G15 / `deferred.py:53-56`). Until then it is NOT-NEEDED for any running pilot or prod; this ticket builds nothing that runs an action. The lead decides whether to build it this round or keep it as a ledger row with its trigger (plan-v2.md lines 6 and 26: tier 2 items get a ledger row with a trigger). I make no claim that it is wanted this round.

## RUNG TABLE (CODE-LAST v1; scale: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code)
| Component | Need | Rung tried | Evidence (source, date) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Executor database role and its rights | least rights for the process that acts | 2: `GRANTS`, `_apply_grants`, `effective_problems`; 3: the PostgreSQL role system does the refusing | migrate.py 46-80, 209-215, 466-470, read 2026-11-20 | one more slot (`executor`) and one more `migrate` parameter, about 15 lines | CUT-TO-CONFIG+GLUE |
| Executor connection secret | runtime never holds the login | 2: the `*_credential_ref` pattern of reset and release | table.py 124-128; app.py 190-203 | one optional field and one name check, about 10 lines | CUT-TO-CONFIG+GLUE |
| Runtime does not read action secrets in pilot and prod | no resolve of executor names in the runtime process | 2: `platform_secrets.check` already takes the executor names as a separate argument | platform_secrets.py 37-64; app.py 204 | one condition: in pilot and prod the runtime passes an empty executor set and the executor process resolves its own | KEEP-CODE (rung 5, small) |
| Where the secret lives | client secret kept apart from the runtime | 3: the secret store's own access policy (IAM, vault policy) | runbook 18-21 and 101-104 | nothing: a policy, written in the runbook, not code | CUT-TO-CONFIG |
| Doing the write itself | the act on the client's system | 1: the client's tool (n8n, Make, the CRM) | old-plan-v4-3.md 400; deferred.py 53-56 | not built here | NOT IN THIS TICKET |
Rung 1 and rung 4 do not give a database-level refusal; UNVERIFIED that no library offers it, not searched.

## Generic-words check
No project, client or product name appears in a core type, field, role or message. New names: slot `Grant.executor`, parameter `executor_role`, field `backends.store.executor_credential_ref`, CLI flag `--executor-role`, audit domain word `action` (already used). Stages are written only demo, pilot and prod (`stages.is_live`: pilot and prod). A scan of the new names for any customer word is part of the review.

## What this ticket is (and the line it does not cross)
IDENTITY ONLY: a database role with a written grant row, a credential name the runtime never reads, and a start-up refusal. It does not build the executor process, does not hand work to it, and does not lift the refusals in `deferred.py`. After this ticket, `build()` in pilot and prod still sets `executor = None` and the live run still ends `executor_not_configured`.

## Files
Create
- `tests/test_executor_identity_roles.py` (PostgreSQL, real logins), `tests/test_executor_identity_unit.py` (no database), `tests/executor_identity_mutants.py` (not collected; runner `tools/mutation_runner.py`).
Modify
- `S/store/migrate.py`: `Grant` gains `executor: str = ""` (after `release`); GRANTS rows below; `migrate(..., executor_role=None)` joins the role loop and the `roles` tuple (415), a block after the purge block (466-470): `_apply_grants(db, executor_role, lambda g: g.executor)` then `effective_problems(db, executor_role, lambda g: g.executor if g else "")` refusing with "the executor role holds more than the grant map"; the "must be different roles" and "must not be members of each other" messages name the executor role (pinned substrings stay).
- `S/backends/table.py` after line 128: `executor_credential_ref: str | None = None`, comment: the NAME of the secret holding the executor role's connection string; deliberately not `*_secret_name` so the runtime never reads it (platform_secrets.py:21).
- `S/app.py` 190-203: the loop `for ref_field in ("release_credential_ref", "reset_credential_ref")` gains `"executor_credential_ref"`; the ref name is also added to the set passed to `check_senders` (181-189). In pilot and prod the runtime's `platform_secrets.check` gets `set()` instead of `executor_names` (204) so it never resolves an action secret (today the set is empty in live because http is refused; this keeps it empty when the refusal is lifted). Exact line to be confirmed against the tree when the ticket is built: UNVERIFIED which of the two spellings the lead prefers.
- `S/cli.py`: `--executor-role` beside the other role flags (the `_migrate` signature at 393-397); pass it into `migrate()`. No warning for a missing executor role (see Out).
- `tests/test_grants_negative_roles.py` and any test that pins the exact field list of `Grant` or iterates GRANTS rows per role (as the F-store ticket notes for `release`): adjust; run to find them.
- Docs: `docs/stop-state-runbook.md` is NOT edited; a new section "Executor identity" goes in the same file's role set-up area only if the lead agrees (otherwise handover note). README.md and SECURITY.md get NO new guarantee sentence in this change (B3: a positive sentence enters only with the change that lands its step; nothing here makes a live executor). CHANGELOG.md: one upgrade-step line.
Delete: none. Unchanged on purpose: `S/actions/executor.py`, `S/deferred.py`, `S/runtime/agent_loop.py`, `S/store/postgres.py`, `S/store/memory.py`, `S/store/protocol.py`, `S/identity.py`.

## GRANTS rows (S/store/migrate.py)
The executor never writes run state (executor.py docstring 1-5; it returns a `RunResult`). Proposed rights, least first; each row is a question to the reviewer, not a decided fact:
```python
    "runs":               Grant("table", _RW, portal=True, purge_cols=(...), executor="SELECT"),
    "plans":              Grant("table", _RW, portal=True, executor="SELECT"),
    "gate_decisions":     Grant("table", _APPEND, portal=True, executor="SELECT"),
    "approval_decisions": Grant("table", _APPEND, portal=True, executor="SELECT"),
    "audit_entries":      Grant("table", _APPEND, portal=True, reset=_APPEND, release=_APPEND, executor=_APPEND),
    "audit_checkpoints":  Grant("table", _APPEND, portal=True, reset="SELECT", release="SELECT", executor="SELECT"),
```
Every other row keeps `executor=""`. The executor role gets no right on `spend`, `spend_month`, `spend_reservations`, `kill_switch*`, `tick_state`, `redaction_maps`, `tool_calls`, `dead_letters`, `audit_outbox`, and no sequence. Reason it reads those four tables: to re-check the plan hash against the stored plan, the gate decision and the approval (executor.py 106-114). Reason it appends audit: the act and its outcome are written by the identity that performed it. Open: whether `runs` SELECT is needed at all (it re-checks `run_id` only, executor.py 107). Recommended: drop it unless the builder shows a read.
The relations keep the exact owner-check, the PUBLIC and role-membership checks of `effective_problems`; a direct excess grant is removed by `REVOKE ALL` (migrate.py 188 pattern), a right held through PUBLIC or another role is refused.

## Public signatures
- `migrate(dsn, *, runtime_role=None, portal_role=None, purge_role=None, reset_role=None, release_role=None, executor_role=None, iam_auth=False, region=None, sslmode=None, sslrootcert=None) -> list[str]` (the existing parameters keep their order; the new one is keyword-only).
- CLI: `hadavin-sdk migrate ... [--executor-role E]`. Exit codes unchanged.
- Config: `backends.store.executor_credential_ref: <secret name>` (optional field of the Postgres settings).
- `Grant(kind, runtime, portal=False, purge="", purge_cols=(), reset="", release="", executor="")`.
- Unchanged: every `Store` method, `Executor.__init__(registry, secrets, timeout_s=10.0)`, `Executor.execute`, `Limits`, `Hooks`.

## Invariants
1. After `migrate --runtime-role R --executor-role E`, E can SELECT the plan, gate decision and approval rows and append and read audit entries; E can do nothing else, on any relation of the schema, including relations not in GRANTS.
2. R (runtime) holds no right E holds and E holds none that R holds beyond the read tables above; R, portal, purge, reset, release and E are different roles and not members of each other (migrate refuses otherwise).
3. The runtime process never resolves the executor connection string: the ref does not end in `_secret_name`, so `secret_names()` (platform_secrets.py:21) and `bound()` ignore and refuse it.
4. In pilot and prod the runtime process resolves no action secret at start-up (the set given to `platform_secrets.check` is empty). In demo it resolves them as today.
5. `executor_credential_ref` may not equal the runtime, purge, reset or release credential name, nor any tool, source, executor, sender or restored-hash secret name (canonical form, `secret_name.canonical_secret_name`); the start stops with a message that names the field and never the value.
6. No behaviour change in demo, pilot or prod runs: `executor` is still None when live; a live run still ends NEEDS_PERSON `executor_not_configured`.
7. A grants-only change: no migration file, no new table. If the lead chooses otherwise, the number is asked (next section).
8. Stated limits: the database owner and a superuser are outside the guarantee; a secrets policy that lets the runtime's identity read the executor secret defeats it and nothing in code can stop that (the runbook already says this for reset and release).

## Migration number needed (ask, do not pick)
Proposed: NONE. The executor role is a grants slot plus a check; no relation is created. QUESTION TO THE LEAD: do you want the executor's outcome kept in a new append-only table (for example a table of results written by the executor role)? If yes, one migration number is needed. The files on disk run 0001 to 0008 and numbers are given by the lead in ORDERS.md; I do not choose. If no, none is needed.

## Interfaces
Offered (by me):
- `Grant.executor` slot and `migrate(executor_role=...)` for any later step that needs a different identity.
- `backends.store.executor_credential_ref`: the name the future executor process reads with its own provider.
- A rule for the future executor process: it builds its own `SecretProvider` and opens its own store with the executor DSN; it never shares the runtime's provider (app.py 254-256 today does).
Needed (from others):
- From the lead: the decision on conditional status (build now or ledger row); the migration question above; whether README and SECURITY stay untouched (B3).
- From core-a (DOOR): nothing now. Later, if a worker loop picks up approved runs, it is core-a's or a new ticket's file; this ticket names no file of the triggers package.
- From core-c (TEXT): nothing. The restored inputs the executor receives (agent_loop.py `inputs_view`) are unchanged.
- From the operator (at use time): create the executor role as a LOGIN role (migrate never creates roles); keep its connection string in a secret the runtime's identity cannot read; keep the action secrets in a store the runtime's identity cannot read.

## Tests (written by a different agent than the builder)
Unit (no database)
- `Grant("table", "SELECT", executor="SELECT")` is accepted; the default is `""`; a GRANTS row naming an executor right on `kill_switch*`, `spend*` or `redaction_maps` fails a table-driven test that lists the forbidden relations.
- `migrate` refuses (before any connection) when the executor role equals the runtime, portal, purge, reset or release role; refuses a role named `public`, `none`, `session_user`, `current_user` (existing `_FORBIDDEN_ROLES`); the message contains the pinned substrings.
- Config: a name in `executor_credential_ref` that folds (case, punctuation) to any tool, source, executor, sender, restored-hash, reset or release name stops `build()`; the message names the field and not the value (hostile: the value is itself a secret mistyped into the field; the message must not contain it).
- `executor_credential_ref` is not a `*_secret_name` field: `platform_secrets.secret_names` ignores it; `bound()` raises `ConfigError` for it (the runtime cannot read it).
- Pilot and prod: `build()` with an http contract is still refused by `deferred.check` (no behaviour change); with the executor ref set and no contract, `build()` succeeds, `app.executor is None`, and a run ends `executor_not_configured`.
- Demo: `build()` is unchanged (`app.executor` is an `Executor`; executor secrets are read as before).
PostgreSQL (real logins; the executor DSN is the only secret given to the second connection)
- E can SELECT `plans`, `gate_decisions`, `approval_decisions`; E can INSERT into `audit_entries` and SELECT `audit_checkpoints`.
- E cannot: INSERT, UPDATE, DELETE or TRUNCATE any other relation; cannot UPDATE or DELETE `audit_entries`; cannot SELECT `redaction_maps`, `tool_calls`, `spend*`, `kill_switch*`; cannot call `hadavin_release_expired_spend`; cannot `SET ROLE` to another; cannot CREATE in the schema.
- The runtime role cannot read what only the executor role reads (there is nothing today) and holds no executor-only right; the table-driven loops over GRANTS in the existing grant tests cover the new column.
- Hostile cases: (a) a hand `GRANT ... TO PUBLIC` on a money table makes `migrate --executor-role` refuse; (b) E made a member of the runtime role is refused; (c) E made owner of a relation is refused; (d) the same login named as runtime and executor is refused before connecting; (e) a role that does not exist fails with the existing exit 3 without a traceback; (f) a hand `GRANT SELECT ON spend TO E` is REMOVED by `migrate` (REVOKE ALL first), not refused: the test pins this exactly as the B ticket does for reset (tickets/B-stop-state.md line 16, CORRECTED 3); (g) a right through PUBLIC on a relation outside GRANTS is refused.
- Rollout: running `migrate` twice is idempotent; running it without `--executor-role` after it was named once does NOT remove E's grants (a stated limit; documented, tested as "unchanged").
Contract tests, one per interface
- Interface `migrate(executor_role=...)`: the contract test calls it on the schema owner DSN with all six roles and asserts, through `effective_problems`, that each role's effective rights equal its column of GRANTS exactly. It fails if any role gains a right another role lost.
- Interface `executor_credential_ref`: the contract test builds an app with a provider that records every `get()` name; asserts the executor ref name is never asked, in demo, pilot or prod, by the process that built the app.
- Interface "runtime reads no action secret in pilot and prod": with a provider that records every `get()` name and a config whose http contract is allowed by a test double of `deferred.check`, assert the recorded names do not include the contract's `secret_name` when the environment is pilot or prod, and DO include it in demo. (The double exists only in the test; the production refusal stays.)
Mutation plan (file `tests/executor_identity_mutants.py`): drop the `executor_role` check block; widen the `audit_entries` row to `_RW`; add `executor="SELECT"` to `redaction_maps`; make the ref end in `_secret_name`; remove the ref from the overlap check in app.py; pass `executor_names` back into the live `check`. Each must be killed by a named test above.
Fail-before test: a test that, on today's tree, shows `platform_secrets.check` reading an executor secret in the runtime's own `build()` when an http contract is allowed in a test double (this is the gap in the NEEDED-CHECK).

## Evidence commands (to be run by the builder and the test writer, raw output saved under handover/core-b/evidence/)
`uv run pytest tests/test_executor_identity_unit.py tests/test_grants_negative_roles.py tests/test_k2_migrations.py -q`; the PostgreSQL file against the lane's PostgreSQL 16 only as an extra signal (CAPABILITY.md; the lead runs the real one); `uv run ruff check src tests`; `uv run python tools/mutation_runner.py tests/executor_identity_mutants.py`. NOT run for this draft.

## What stays out
- The executor PROCESS, any worker loop that hands an approved run to it, and any change to `agent_loop.py`, `deferred.py` or `app.py` that makes `executor` non-None in pilot or prod. The refusal at `deferred.py:53-56` stays. (Trigger: the owner lifts the AK-G15 deferral, plan-v2.md 26.)
- Which contract kinds may run live, effect-once (stored `RunResult`, blind flag), non-HTTP executors, rollback live, manual executor.
- A new table, a new store method, a new store kind, a Protocol change, a migration file (unless the lead answers yes above).
- Creating database roles or secrets (migrate never creates roles; the operator does).
- Secret-store policy changes, key rotation, a vault or cloud provider change in `actions/secrets_*.py`.
- Tier 2 code, any live action, any secret value, any spend, a live model call.
- A positive guarantee sentence in README or SECURITY (B3).
- A warning or refusal for a missing executor role in `migrate` (nothing runs as that role yet).
- Anything in core-a's triggers package or core-c's guard text modules.
- Ask-your-data, demos and any project or customer word.

## Open questions (recommended answer)
1. Build this round, or keep a ledger row until a client wants the core to write? Recommended: ledger row; do not build without the trigger.
2. A results table, or does the runtime store the returned `RunResult` after the executor hands it back? Recommended: the executor returns the result and the runtime records it; no table, no migration.
3. Does the executor need `runs` SELECT? Recommended: no.
4. Is `audit_entries` INSERT right for the executor, or should the executor hand its audit event to the runtime? Recommended: INSERT, so the identity that acted writes its own row (the reset and release roles do the same).
5. Where does the executor process live and who owns that file? Recommended: a separate ticket, owner decided by the lead.

## Size (estimate, not measured)
SQL: 0. Source: about 40 lines (migrate 25, table 3, app 8, cli 4). Tests: about 400 lines. Docs: about 20 lines.

## Files read (summary)
S/actions/executor.py, S/actions/secrets.py, S/app.py, S/backends/platform_secrets.py, S/backends/table.py, S/deferred.py, S/identity.py, S/stages.py, S/models.py (RunResult 315-319), S/runtime/agent_loop.py (176-178, 811-826), S/store/migrate.py, S/store/migration_numbers.py, S/store/migrations/0006_stop_state.sql, docs/stop-state-runbook.md, handover/core-b/QUEUE.md (Q17), PLAN-READBACK.md, LANE-MAP.md, tickets/B-stop-state.md, tickets/F-store.md, inputs/review-plan-1-codebase.md, inputs/plan-v2.md, inputs/TICKET-TEMPLATE.md, inputs/old-plan-v4-3.md (line 400). Not read: the older reviews and the other lanes' tickets.
