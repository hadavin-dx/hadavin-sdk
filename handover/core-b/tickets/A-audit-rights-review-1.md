# A-audit-rights review 1 (fresh reviewer, 2026-11-20, read-only, against cloud/core-b)

Verdict: the ticket is right on the two findings but wrong on three points. (a) Its "no new SQL migration" is wrong for the outbox. (b) Its recommended mark column does NOT make the runtime unable to lose an undrained row. (c) The SECURITY DEFINER checkpoint idea does not close the checkpoint finding. Recommendation: checkpoint role (grants only, no migration) plus a SECURITY DEFINER outbox function in a new migration 0012.

## (1) audit_checkpoints INSERT

Facts: `checkpoint()` (chain.py:649-670) reads the head, signs `hadavin-audit:{seq}:{head}` in Python and INSERTs. 0009's `hadavin_audit_checkpoint_guard` already forces seq = a real row and hash = that row's hash. The inline call is chain.py:323 (`seq % checkpoint_every == 0`). The only residual harm of runtime INSERT: a row at the CURRENT head with a junk signature (verify false alarm, and `signed_through() >= seq` stops the real signature for that head, `ON CONFLICT DO NOTHING`).

Design X, SECURITY DEFINER `hadavin_write_checkpoint(seq, hash, sig, alg, label)` recomputing the head: REJECT. The function cannot verify an ed25519/KMS signature, so the runtime still chooses the signature. The junk-row-at-head attack survives unchanged, and the hash check is what the 0009 trigger already does. Blast radius is not reduced; it adds a migration, a function pin, EXECUTE bookkeeping and tests for zero gain.

Design Y, checkpoint role: RECOMMENDED. Own login, `Grant.checkpoint = "SELECT, INSERT"` on audit_checkpoints and `"SELECT"` on audit_entries (it must read the head; nothing else). The runtime drops to SELECT on audit_checkpoints. Blast radius: the runtime can no longer write any checkpoint row. Operator burden: one more role and DSN secret, the same pattern as `release_credential_ref`/`purge_dsn_secret_name` (precedent: app.py:193-253, table.py:124-132). Test cost: moderate; copy the release-role tests (test_stop_state_roles.py World). Honest limit to write in SECURITY.md: if the signer key stays in the runtime's config, a runtime compromise can still sign a bad row by borrowing the checkpoint step; the gain is that a runtime SQL injection or a stray write path cannot. Full key separation (checkpoint step in its own process) is out of scope.

Inline checkpoint: when `checkpoint_dsn_secret_name` is set, the inline call at chain.py:323 is skipped; only the tick `checkpoint` step writes, on a second `ChainAudit` db handle (`checkpoint_db`) opened with the checkpoint login. The runtime never attempts the INSERT. With no checkpoint role (memory/SQLite store, dev, `--no-roles`) behaviour is unchanged (inline stays). Cost of removal: checkpoints are per tick, not per `checkpoint_every` rows; the head is signed whole, so coverage lag is at most one tick interval. Prod/pilot: make `checkpoint_dsn_secret_name` required when `backends.audit.kind=chain` AND a signer is set (as app.py:138 does for purge).

## (2) audit_outbox DELETE

Mark column + purge role: REJECT. A column-level UPDATE lets the runtime mark ANY undrained row `drained`, and the purge then deletes it: same loss, one step later. It also needs a column-UPDATE grant kind that `Grant`/`effective_problems` lack, a new purge-role grant and a purge job.

SECURITY DEFINER `hadavin_audit_outbox_done(event_id text)`: RECOMMENDED. Body: `DELETE FROM audit_outbox WHERE event_id = $1 AND EXISTS (SELECT 1 FROM audit_entries WHERE event_id = $1)`. The database enforces the invariant "a parked event leaves the outbox only once it is in the chain". Runtime: `Grant.runtime = "SELECT, INSERT"` on audit_outbox, EXECUTE on the function.

The ticket missed the quarantine path: `_quarantine` (chain.py:588-596) INSERTs a copy under `AUDIT_QUARANTINE_PREFIX + id` and DELETEs the original, and the event is NOT in audit_entries, so `_done` would refuse. Add a second function `hadavin_audit_outbox_quarantine(event_id text, prefix text)`: `UPDATE audit_outbox SET event_id = prefix || event_id WHERE event_id = $1 AND event_id NOT LIKE prefix || '%'` (a rename, nothing is lost; the poison row stays). chain.py `_quarantine` calls it instead of INSERT+DELETE. The prefix is a parameter, not hard-coded, so defaults.py stays the one source; the function must not accept an empty prefix.

Both functions: `LANGUAGE sql`/plpgsql, `SECURITY DEFINER`, `SET search_path = pg_catalog, <schema>, pg_temp` exactly like the 0011 functions (copy their header), owner = migrating owner, EXECUTE revoked from PUBLIC. Placement under psycopg schema pinning: check `_pin_money_functions` for how the schema is substituted.

## (3) Migration number

New migration `0012_audit_outbox_functions.sql`. Do not edit 0009 (the outbox needs no 0009 content; 0009 is applied on dev DBs, M6 draft warning would force `--reset-draft`) and do not edit 0011 (still being edited by F-money-definer; merge conflicts and a reset for everyone). 0012 is unreleased-safe: free number per MIGRATIONS.md; update that table row. The checkpoint role needs no migration (grants only; the 0009 trigger stays).

## (4) Files, order, tests, mutants

Files: `src/hadavin_sdk/store/migrations/0012_audit_outbox_functions.sql` (new); `src/hadavin_sdk/store/migrate.py`; `src/hadavin_sdk/audit/chain.py`; `src/hadavin_sdk/backends/table.py`; `src/hadavin_sdk/app.py`; `src/hadavin_sdk/cli.py`; `tests/test_audit_runtime_rights_pg.py`; new `tests/test_audit_rights_roles_pg.py`; `tests/test_audit_rights_mutants.py`; `handover/core-b/MIGRATIONS.md`; `SECURITY.md`, `README.md` (drop the two limits).

migrate.py regions (wip/lead-b-migrate edits the laptop-side copy; rebase after it merges, then re-read line numbers; today's numbers): `Grant` dataclass 38-62 (add field `checkpoint: str = ""`); `FunctionGrant` 65-72 (unchanged); GRANTS rows 97-99 (`audit_entries` add `checkpoint="SELECT"`; `audit_checkpoints` runtime `"SELECT"`, `checkpoint=_APPEND`; `audit_outbox` runtime `"SELECT, INSERT"`); `MONEY_FUNCTIONS`/`FUNCTION_GRANTS` 126-150 (add the two functions, runtime=True; extend `_pin_money_functions` list); `migrate()` signature 1195-1202 and role tuple/distinctness 1232-1239 (add `checkpoint_role`, message "runtime, portal, purge, reset, release and checkpoint"); apply block after release 1357-1363 (copy it with `g.checkpoint`, "the checkpoint role holds more than the grant map"); `_apply_money_functions` role dict 1366-1372 (add `"checkpoint": checkpoint_role`, FunctionGrant gains no right for it). New refusal: owner check (below) in the same function before grants. Do not touch `_apply_grants`, `effective_problems` internals.

Order: (1) 0012 + migrate.py map/function pins + role plumbing + owner refusal; (2) cli.py `--checkpoint-role` (parallel to `--release-role`, lines 173, 240, 497-533); (3) table.py/app.py `checkpoint_dsn_secret_name`, same-login and same-secret refusals like app.py:193-210, required in pilot/prod with chain+signer; (4) chain.py: `checkpoint_db`, skip inline when set, `_drain_item` uses `SELECT hadavin_audit_outbox_done(?)`, `_quarantine` uses the rename function; tick.py needs no change (`checkpoint` step calls `audit.checkpoint()`, which uses `checkpoint_db`); (5) tests; (6) docs.

Owner refusal (ticket point 3): after roles are known, query `pg_tables.tableowner` for the three audit tables and `pg_has_role(role, owner, 'USAGE')` for every named role; any hit raises ConfigError naming the table. A superuser stays outside the guarantee.

Acceptance: remove both `xfail` marks in tests/test_audit_runtime_rights_pg.py and both pass (World needs `checkpoint` role in `w.roles`; update World in tests/test_stop_state_roles.py accordingly). New tests: checkpoint login writes a checkpoint and `audit verify` is ok; runtime INSERT is 42501; runtime `SELECT hadavin_audit_outbox_done('seed-o1')` deletes nothing while 'seed-o1' has no audit row, deletes the row once an `audit_entries` row with that event_id exists; quarantine function renames and never deletes; runtime owning audit_entries (or member of the owner) makes migrate refuse naming the table; `test_audit_drain*.py` unchanged green; ruff clean; the exact-rights tests of reset/release/portal/purge green; `check_grants` sees 0012's functions mapped.

Mutants (add to a mutants file in the style of tests/audit_drain_mutants.py): drop the `EXISTS (...)` from `_done` (undrained delete must be caught); runtime INSERT back on audit_checkpoints; runtime DELETE back on audit_outbox; checkpoint role given UPDATE/DELETE or INSERT on audit_entries; remove the inline-skip (runtime attempts INSERT, 42501 logged each N rows); `_quarantine` back to INSERT+DELETE; function without `search_path`; EXECUTE left on PUBLIC; owner refusal skipped for membership.

## (5) Failure paths when the runtime loses a right

Intent/outcome writes need only audit_entries SELECT+INSERT and keep both; none touches checkpoints or outbox deletes, so no `AuditUnavailable` site (chain.py `write_intent` 330-334; callers cli.py 700, 855, 1002, 1010; agent_loop.py 829, 914; limits.py 278; postgres.py 1007; k1b/audit_sink.py; replay.py) changes. `write_outcome` (340-357) still INSERTs to the outbox (kept). Paths that DO change:
- chain.py:323 inline `checkpoint()` and the tick `checkpoint`: swallowed, never raises, logs `InsufficientPrivilege` each time if the runtime still tried. Hence the inline skip.
- `_drain_item` (561) and `_quarantine` (595): today a failed DELETE is counted `not_deleted` and `reconcile` raises `RuntimeError("audit outbox: ... not_deleted")` so the `audit_drain` tick step fails every tick. Same outcome if the operator deploys the new runtime before running migrate 0012 (EXECUTE missing). Rollout order: migrate (0012 + `--checkpoint-role`) first, then deploy. Say so in the release note.
- Other ChainAudit users that hold only SELECT on checkpoints already (release role, reset role: cli.py:341) keep working: their inline checkpoint is already swallowed.
- Time-order: a drained row not deleted stays and is dedup-deleted next pass (existing behaviour), unchanged.

## Builder brief (execute as written, no questions)

1. Create `0012_audit_outbox_functions.sql` with `hadavin_audit_outbox_done(text)` and `hadavin_audit_outbox_quarantine(text, text)`: SECURITY DEFINER, pinned search_path as in 0011, `REVOKE ALL ... FROM PUBLIC`. In migrate.py add both to MONEY_FUNCTIONS and FUNCTION_GRANTS (`runtime=True`) and to the pin list.
2. migrate.py: `Grant.checkpoint`; set GRANTS rows as in section (4); add `checkpoint_role` to `migrate()`, the distinct-role check, grants/effective-problems block and the role dict; add the owner/membership refusal.
3. cli.py `--checkpoint-role` and `backends.store.checkpoint_dsn_secret_name` in table.py; app.py: open the checkpoint connection, refuse same login/secret as runtime/purge/release/reset, require it in pilot/prod when audit=chain with a signer.
4. chain.py: optional `checkpoint_db`; skip inline checkpoint when set; `checkpoint()` reads and writes through `checkpoint_db`; outbox delete via `SELECT hadavin_audit_outbox_done(?)`; quarantine via the rename function (memory/SQLite store: keep the old SQL path, the function exists only in Postgres; branch on the store kind the file already knows).
5. Tests and mutants as in (4); remove the two xfail marks; update MIGRATIONS.md (0012 row, next free 0013), SECURITY.md, README.md.
6. Run `pytest` with HADAVIN_TEST_PG_DSN set, ruff, and the mutant file. Do not edit 0009 or 0011.
