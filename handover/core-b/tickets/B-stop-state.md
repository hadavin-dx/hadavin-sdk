# TICKET B: stop state with a separate reset identity

- Owner: core-b (SPINE). Path class: security (extended review: yes). Migration: `0006_stop_state.sql`.
- Depends on: step A merged first (for the tick step list only; B adds no tick step). Ticket review: one EGM round.
- Written 2026-11-20 from the lead's draft (inputs/draft-tickets-A-B.md), every cited line opened on origin/main 51c9fc4; branch read with `git show origin/core/P2a-1:<path>` (7f32349). Nothing was run. S = `src/hadavin_sdk`.
- Tests are written by a different agent than the builder. Code goes in commits named "code B: ...".

## Problem in plain words
The stop switch ("kill switch") is one database row with an on/off flag. The program that runs the agents (the runtime) logs in to the database with a login that may write that row, so it can switch the stop off as easily as on. A misbehaving agent, or a bug, could therefore undo an operator's stop. After B the runtime login can only add a stop. Only a second login, held by the operator and never by the runtime (the reset role), can clear stops, and it must write the reset into the audit log first.

## Checked (draft claims against main)
- CONFIRMED, lines exact: 0001_core.sql:94-100; 0003_approvals_tick.sql:24-27; postgres.py:444-451, 453-464; migrate.py:23-37, 55, 169-187, 193-262, 298-303, 333-339, 346-353; limits.py:43-51; cli.py:93-105, 138, 182-209, 312-339, 366-409 (stop at 391, reset at 399); app.py:198-207; table.py:120; platform_secrets.py:18-20; chain.py:529 (the probe reads audit_checkpoints); 0002_audit_chain.sql:25-26; test_p7_store.py:160-171; test_k2_migrations.py:119 and 383; test_k5_round10_postgres.py:157; test_migration_numbers_guards.py:363; test_p2_postgres.py:290. Connections are autocommit (postgres.py:146), so a refused statement does not poison the next one.
- CONFIRMED, three findings: the branch is +6128 lines in 66 files, carries 0006_spend_reservations and 0007_kill_switch_guard, needs `require_backend` (not on main); its `Grant.reset` is set only on the view kill_switch_state.
- CORRECTED 1 (new pin, breaks without an edit): tests/test_p7_store.py:152-153 asserts the runtime role CAN UPDATE kill_switch. The draft looked for this in test_p2_postgres.py:173-196 and test_k2_migrations.py; neither assumes it (172-196 checks `runs` only; k2 lines 101, 270, 283-289 are about the portal role).
- CORRECTED 2 (new pin, breaks without an edit): tests/test_k5_fixes2.py:260-273 builds a folder of renamed migrations and calls migrate() with the real grant map (test at 282-309). With new GRANTS rows and no stop-state file in that folder, check_grants (migrate.py:305) refuses first and the expected message is never reached.
- CORRECTED 3: "a hand GRANT DELETE ON kill_switch_clears to the reset role" is not refused. `_apply_grants` does REVOKE ALL first (migrate.py:179), so migrate removes a direct grant and succeeds. A refusal happens only for a right the role holds through PUBLIC or through another role.
- CORRECTED 4: "a role that does not exist" does not reach migrate.py:204-205. The GRANT at migrate.py:173 (or pg_has_role at 336) raises psycopg `UndefinedObject` first; the CLI turns it into exit 3 with no traceback (cli.py:71-84); the transaction rolls back.
- CORRECTED 5 (hostile case the draft missed): with `id BIGSERIAL` the runtime login, which may INSERT, could insert rows with ids ahead of the sequence; after a reset the next honest stop would hit a duplicate key and fail. The ticket uses a random UUID id (no sequence, no sequence grant row).
- CORRECTED 6: the audit row does not record which database login wrote it. The normal test proves "written by the reset login" by giving the secrets provider only the reset DSN.
- CORRECTED 7: line numbers. Table-to-model map is test_p2_postgres.py:31-41 (not 36-41); sha helper is test_migration_numbers_guards.py:356-357; the agent_loop hunk on main applies at 250-251 and 785-792 (12 changed lines).
- RESOLVED (was UNVERIFIED): test_p2_postgres.py:31-41 needs no row (the map lists only tables that have a model; the column regex at 44-58 reads the new tables without error). test_migration_numbers.py:485-491 is a hand-written list ("0004_x.sql"), no row needed. tests/test_cuj.py:254, test_review_fixes.py:153, test_s5_runtime.py:127 all run on MemoryStore (test_s5_runtime.py:27; conftest make_cfg), so they are untouched. tests/test_p2_postgres.py:199-215 runs CLI stop and reset on the schema OWNER's DSN in a demo config and asserts `by == "user:a"` while ON: it keeps passing if the read returns the open stop's `by`. tests/contracts/test_store.py:197-203 only stops as the runtime role: passes. tests/test_migration_numbers.py:789-794 runs every real file through the refusal list: the SQL below has only CREATE statements, so it passes by reading.
- RESOLVED: tests/test_stop_state_loop.py of the branch. Its imports exist on main (`_approve`, `_doc`, `_pending` re-exported at test_review_pr3_round2.py:24; fixture `app` at 38-39; `__wrapped__` exists in pytest 9.2.0). On main without the hunk both tests fail (the RuntimeError leaves `handle` at agent_loop.py:251 and `_recheck` at 790). With the hunk they should pass; `limits_unavailable` is already a used reason (agent_loop.py:715-718, tests/test_k3_leftovers.py:47).
- Note: the facts file (notes, B.8) says no test pins "different roles"; test_k2_migrations.py:119 does. The draft was right.

## NEEDED-CHECK
- ONE-PLACE-PER-JOB: one place holds the stop state (the Postgres store, `get_kill_switch` / `set_kill_switch`), one place holds rights (`GRANTS` in migrate.py), one place audits stop and reset (`Limits`). B changes these three in place and adds no second reader, no second grant mechanism, no second audit path.
- On main: one row, upserted for stop and reset alike; runtime holds SELECT, INSERT, UPDATE on it; the grant mechanism, the effective-rights check and the second-DSN pattern (purge) already exist and are reused.
- Branch core/P2a-1: solves the same problem with database functions, a guard trigger, login labels, a stop role, version checks and a probe. It is a parts store only: it is stacked on the spend-reservation migration, forked from an old main (stage name `dev`, refused on main), makes `reset_role` required (edits about 20 test files) and was never run against main's migration guards.
- Verdict: NEEDED. Nothing on main separates stop from reset; the branch cannot land as it is.

## RUNG TABLE (CODE-LAST v1; scale: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code)
| Component | Need | Rung tried | Evidence (source, date) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Migration 0006 | two append-only tables | 3: plain PostgreSQL tables, FK, triggers; 2: reuses `hadavin_audit_append_only()` (0002:25-26) | read 2026-11-20 | nothing; pure SQL, no new function | CUT-TO-CONFIG+GLUE (SQL only) |
| Grants rows | least rights per role | 2: `GRANTS`, `_apply_grants`, `effective_problems` | migrate.py:46-68, 169-262, read 2026-11-20 | one new slot `reset` on `Grant`, about 12 lines | CUT-TO-CONFIG+GLUE |
| Store read/write | read ON/OFF, add stop, clear | 2: PostgresStore helpers `_select`, `_exec`, `_lock`; 3: PostgreSQL role system does the refusing | postgres.py:201-228, 444-464 | three short statements, about 25 lines | KEEP-CODE (rung 5, small) |
| CLI reset path | second login for reset | 2: purge second-DSN pattern | app.py:198-207, cli.py:182-209 | about 20 lines of wiring | CUT-TO-CONFIG+GLUE |
| Limits wrap | audit a refused reset | 2: `write_intent` / `write_outcome` | limits.py:48-51 | 4 lines | KEEP-CODE |
Rung 1 (no-code tools) and rung 4 (libraries): not applicable, the guarantee must sit in the database's own rights; UNVERIFIED that no library offers it, not searched.

## INVARIANTS
1. On PostgreSQL after `migrate --runtime-role R --reset-role X`, no statement the runtime role may run turns the switch from ON to OFF.
2. ON = the kill_switch row is missing, OR its flag is on, OR at least one kill_switch_stops row has no kill_switch_clears row.
3. A stop is one INSERT and works with the audit down. Its id is a random UUID chosen by the database default, so no login can make a later stop collide.
4. A reset clears only the stops its statement can see; a stop committed during or after it stays ON; two resets at once both succeed.
5. A reset is audited before it happens. Audit unavailable means not reset, exit 3. A reset the database refuses leaves a `limits.reset_failed` outcome (best effort, never raises) and the switch ON; the chain then holds `reset` followed by `reset_failed`.
6. The reset role holds exactly: kill_switch SELECT, UPDATE; kill_switch_stops SELECT; kill_switch_clears SELECT, INSERT; audit_entries SELECT, INSERT; audit_checkpoints SELECT; USAGE on the schema; nothing else.
7. Runtime, portal, purge and reset are four different roles and not members of each other; migrate refuses otherwise, and refuses a reset role that effectively holds more than the map (a direct excess grant is removed, not refused).
8. kill_switch_stops and kill_switch_clears are append-only for every role, by trigger and by grant.
9. The runtime process never resolves the reset DSN: the field name does not end in `_secret_name`, so the start-up probe (platform_secrets.py:18-20) and `bound()` (23-33) ignore and refuse it.
10. An unreadable stop state means no model call and no action: the run goes to a person with `limits_unavailable` or `recheck.limits_unavailable`.
11. Python signatures of `Store.get_kill_switch`, `Store.set_kill_switch`, `Limits.stop`, `Limits.reset` are unchanged; the memory store is unchanged and guarantees nothing.
12. A flag that is ON at upgrade stays ON after 0006 (the flag is still read; no data is copied).
13. (added) Stated limits: the database owner and a superuser are outside the guarantee; old code does not see new stops, so old and new runtime processes must never run against one database at the same time.

## Migration 0006_stop_state.sql (full text; needs PostgreSQL 14 or newer, as 0002 already does)
```sql
-- Stop state (step B). A stop is one new row in kill_switch_stops. A reset adds one row per open stop to
-- kill_switch_clears. The switch reads ON while the kill_switch row is missing, or its flag is on, or a stop
-- has no clear. Both tables are append-only for every role: the trigger function of 0002 refuses UPDATE,
-- DELETE and TRUNCATE. The id is a random UUID, not a serial number, so a role that may insert cannot guess
-- the next id and block a later stop.
CREATE TABLE kill_switch_stops (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "by" TEXT,
    ts   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kill_switch_clears (
    stop_id UUID PRIMARY KEY REFERENCES kill_switch_stops (id),
    "by"    TEXT,
    ts      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER kill_switch_stops_append_only BEFORE UPDATE OR DELETE ON kill_switch_stops
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_stops_no_truncate BEFORE TRUNCATE ON kill_switch_stops
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_clears_append_only BEFORE UPDATE OR DELETE ON kill_switch_clears
    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
CREATE OR REPLACE TRIGGER kill_switch_clears_no_truncate BEFORE TRUNCATE ON kill_switch_clears
    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
```
Manifest and pins (same PR, last commit, "written at merge"): tests/fixtures/migrations_released.json gains `"0006_stop_state": <sha256 of the LF-normalised file>` (helper test_migration_numbers_guards.py:356-357); `== 5` at :363 becomes `== 6`; the list at test_p2_postgres.py:290 gains `"0006_stop_state"`.

## GRANTS rows (S/store/migrate.py; `Grant` gains `reset: str = ""` after `purge_cols`)
```python
    "kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE"),          # was Grant("table", _RW)
    "kill_switch_stops": Grant("table", _APPEND, reset="SELECT"),             # new
    "kill_switch_clears": Grant("table", "SELECT", reset=_APPEND),            # new
    "audit_entries": Grant("table", _APPEND, portal=True, reset=_APPEND),     # gains reset
    "audit_checkpoints": Grant("table", _APPEND, portal=True, reset="SELECT"),  # gains reset
```
Every other row keeps `reset=""`. No sequence row (UUID id). In migrate(), after the purge block (346-353):
```python
        if reset_role:
            _apply_grants(db, reset_role, lambda g: g.reset)
            if bad := effective_problems(db, reset_role, lambda g: g.reset if g else ""):
                raise ConfigError("the reset role holds more than the grant map: " + "; ".join(bad[:20]))
```

## Files
Create
- `S/store/migrations/0006_stop_state.sql`: the text above.
- `tests/test_stop_state_roles.py` (Postgres, real logins), `tests/test_stop_state_unit.py` (no database), `tests/test_stop_state_loop.py` (taken from the branch as is, 39 lines), `tests/stop_state_mutants.py` (not collected by pytest; format of the branch file, runner `tools/mutation_runner.py` which is on main).
- `docs/stop-state-runbook.md`: create the role, migrate, set the ref, stop, reset, what each exit code means (parts of the branch runbook).
Modify
- `S/store/migrate.py`: `Grant.reset` (23-37); GRANTS rows (55, 57, 58 and two new); `migrate(..., reset_role=None)` (283-293) added to the name loop and `named` (298-301); messages at 303 and 338 become "the runtime, portal, purge and reset roles must be different roles" and "... must not be members of each other" (the pinned substrings stay); the reset block above; from the branch as is: `_FORBIDDEN_ROLES = frozenset({"public", "none", "session_user", "current_user"})` checked at 299 (a quoted "public" still means PUBLIC in a GRANT), and the four-line owner-membership check in `effective_problems` after 217.
- `S/store/postgres.py` 444-464: `get_kill_switch` keeps the missing-row branch; flag on returns the row; flag off runs `SELECT s."by", s.ts FROM kill_switch_stops s WHERE NOT EXISTS (SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id) ORDER BY s.ts, s.id LIMIT 1` and returns `KillSwitch(on=True, by=..., ts=...)` if a row comes back, else the flag row. `set_kill_switch` with `on=True`: `INSERT INTO kill_switch_stops ("by", ts) VALUES (%s, %s)`. With `on=False`, inside `with self._lock, self._db.transaction():` first `UPDATE kill_switch SET "on" = FALSE, "by" = %s, ts = %s WHERE id = 1`, then `INSERT INTO kill_switch_clears (stop_id, "by", ts) SELECT s.id, %s, %s FROM kill_switch_stops s WHERE NOT EXISTS (SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id) ON CONFLICT (stop_id) DO NOTHING`.
- `S/store/protocol.py` 112-116: docstrings only (what ON means; a reset may be refused by the store).
- `S/limits.py` 48-51: wrap the clear in try/except Exception: `self.audit.write_outcome(self._event(True, by, "reset_failed"))`, then re-raise. Docstring line 1 unchanged.
- `S/runtime/agent_loop.py` 250-251 and 785-792: the branch hunk (limits unreadable gives NEEDS_PERSON `limits_unavailable`, and `recheck.limits_unavailable` in `_recheck`).
- `S/backends/table.py` after line 120: `reset_credential_ref: str | None = None` with a comment: the name of the secret holding the reset role's DSN; deliberately not `*_secret_name` (platform_secrets.py:18-20) so the runtime never reads it.
- `S/cli.py`: usage docstring lines 5 and 9; `--reset-role` beside 97-105; pass it at 138 into `_migrate` (312-339) and on to migrate(); `_migrate` prints a warning when a runtime role is named and no reset role ("nobody but the owner can reset"). In the limits path (182-209), for `reset` only: if `b.store.reset_credential_ref` is unset and `is_live(cfg.environment)` (pilot or prod), print a refusal naming `backends.store.reset_credential_ref` and `migrate --reset-role`, return 2 before anything is built or written; if set, `store_cfg = b.store.model_copy(update={"dsn_secret_name": ref, "purge_dsn_secret_name": None})`, `platform_secrets.check(secrets, [store_cfg, b.audit], set())`, build the store from `store_cfg` and the audit with `signer=None, anchor=None` (no checkpoint is written at chain.py:203); unset in demo: today's path. `_kill_switch_store_down` (366-380): when `what == "reset"`, add one sentence naming the reset role and the ref; keep the substrings "NOT", "migrate", "Nothing was changed" (pinned at tests/test_cuj.py:295, 308).
- `tests/test_p7_store.py` 152-153: take `kill_switch` out of the UPDATE tuple; assert the runtime role has SELECT and no INSERT, UPDATE, DELETE on it. Add after 171 "an open stop reads ON with the stop's by".
- `tests/test_k5_fixes2.py` 260-273: `RENAMED` gains `"0007_stop_state.sql"` and `_folder` maps it to the real `0006_stop_state.sql` (0006_evidence keeps mapping to 0005_evidence.sql).
- `tests/test_p2_postgres.py:290`, `tests/test_migration_numbers_guards.py:363`, `tests/fixtures/migrations_released.json`: as above.
- Docs: README.md:33 (the waiver no longer lists UPDATE kill_switch; add the reset role), SECURITY.md (the Stop sentence below), CHANGELOG.md (upgrade steps below).
Delete: none. Unchanged on purpose: `S/app.py`, `S/store/memory.py`, `S/runtime/tick.py`, `S/models.py`.

## Signatures
- `migrate(dsn, *, runtime_role=None, portal_role=None, purge_role=None, reset_role=None, iam_auth=False, region=None, sslmode=None, sslrootcert=None) -> list[str]`
- CLI: `hadavin-sdk migrate [--runtime-role R] [--portal-role P] [--purge-role U] [--reset-role X]`; `hadavin-sdk limits stop|reset --by WHO` unchanged. Exit codes unchanged: 0 done, 2 refused or store answered with an error, 3 audit unavailable, 4 store unreachable.
- Config: `backends.store.reset_credential_ref: <secret name>` (optional field of PostgresSettings).
- `Grant(kind, runtime, portal=False, purge="", purge_cols=(), reset="")`.
- Unchanged: `Store.get_kill_switch() -> KillSwitch`, `Store.set_kill_switch(ks: KillSwitch) -> None`, `Limits.stop(by: str) -> None`, `Limits.reset(by: str) -> None`.

## Interfaces
- Offered: audit operation `limits.reset_failed` (result "on"); run reasons `limits_unavailable` and `recheck.limits_unavailable`; the `reset` slot of `Grant` for later steps; the SECURITY Stop sentence: "Stop: takes effect at the next gate check; a call already in flight is not interrupted; the command-line eval and replay paths do not read the stop state. On PostgreSQL with the grants applied, the runtime login can add a stop and cannot clear one; only the reset login can, and its reset is written to the audit log first. The database owner and a superuser are outside this guarantee; the memory store guarantees nothing."
- Needed: step A merged (tick step list); the operator creates the reset role as a LOGIN role (migrate never creates roles) and stores its DSN as a secret only on the operator's machine; `HADAVIN_MIGRATE_DSN`; PostgreSQL 14 or newer.

## Security and least privilege
| Role | Exact rights on the stop relations and audit | Why each right |
|---|---|---|
| runtime | kill_switch SELECT; kill_switch_stops SELECT, INSERT; kill_switch_clears SELECT; audit rows as today | read the flag; add a stop and read open stops; see which stops are cleared. No UPDATE or INSERT on kill_switch and no INSERT on clears: that is the whole guarantee |
| reset | kill_switch SELECT, UPDATE; kill_switch_stops SELECT; kill_switch_clears SELECT, INSERT; audit_entries SELECT, INSERT; audit_checkpoints SELECT | UPDATE clears the old flag (SELECT is needed by its WHERE); SELECT stops and clears to find open stops; INSERT clears is the reset; audit SELECT, INSERT writes the intent row (duplicate check and last hash need SELECT); checkpoints SELECT is the build probe at chain.py:529. No right on runs, plans, tool_calls, redaction_maps, spend, audit_outbox; cannot stop |
| purge | none on the three stop relations | deletes evidence only |
| portal | none on the three stop relations (kill_switch stays on the never-list, test_k2_migrations.py:101) | read-only views of runs |
| owner (migration role) | owns everything; UPDATE, DELETE, TRUNCATE on the two new tables refused by trigger | can still drop a trigger: outside the guarantee, said in SECURITY |
Secrets: the reset DSN lives only where the operator runs `limits reset`. Personal data: `by` is free text typed by the operator, stored as given (no label scheme; out of scope). Known cost: the reset login can append any audit row, as the runtime already can.

## Tests (Postgres tests skip without HADAVIN_TEST_PG_DSN, with the same skip line as tests/test_k5_round10_postgres.py:14-17)
Fixture `World` (edit of branch tests/test_stop_state_db.py:31-108): a fresh schema, four LOGIN roles (runtime, reset, purge, portal) with random suffixes, `migrate(scoped, runtime_role=, reset_role=, purge_role=, portal_role=)`, a store per role built with `make("store", PostgresSettings(...), FakeSecretProvider({...}))`, cleanup with DROP OWNED and DROP ROLE. No stop role, group or labels. "Denied" means `psycopg.errors.InsufficientPrivilege` exactly; a missing relation must not count as a pass.
- FAIL-BEFORE (each fails on today's main): F1 (Postgres) after a stop, `runtime_store.set_kill_switch(KillSwitch(on=False))` raises InsufficientPrivilege and a second connection still reads ON (main: succeeds, reads OFF). F2 (no database) `GRANTS["kill_switch"].runtime == "SELECT"` and `GRANTS["kill_switch_clears"].runtime == "SELECT"` (main: "SELECT, INSERT, UPDATE", KeyError). F3 (no database) tests/test_stop_state_loop.py, both tests (main: RuntimeError leaves the loop).
- Normal: N1 stop by the runtime login reads ON with `by` from a second connection. N2 reset by the reset login reads OFF (this also settles that the foreign-key check lets the reset role insert a clear). N3 CLI round trip in a pilot config with the ref set and a secrets provider that holds ONLY the reset DSN for the reset call: exit 0, 0; the chain holds `limits.stop` then `limits.reset`; `audit verify` passes. N4 migrate twice keeps the state and the grants. N5 a store built without a reset role named in migrate still stops and reads.
- Edge: E1 reset with nothing open: exit 0, OFF. E2 two resets at once (two threads, a Barrier): both return, OFF. E3 a stop inserted on connection A and left uncommitted while the reset runs, then committed: ON. E4 1000 stops then one reset: OFF. E5 the owner sets the flag ON, reset: OFF. E6 the flag row deleted: ON, and still ON after a reset. E7 apply 0001-0005, set the flag ON, apply 0006: ON; then reset: OFF. E8 audit down at reset: exit 3, ON, no clear row. E9 migrate run without `--runtime-role` after 0006: the runtime read raises and the loop sends the run to a person (no model call). E10 `limits reset` in pilot and in prod without the ref: exit 2, no audit row, no store built (monkeypatch `make` to fail if called); in demo without the ref: today's path.
- Hostile: H1 `--by` empty, with a newline, 10,000 characters, with a NUL: exit code in {0, 2}, never a traceback, state consistent with the exit code. H2 the runtime login inserts a stop with an id it chose, then a reset, then an honest stop: the honest stop succeeds (kills the serial-id attack). H3 the runtime login appends a fake `limits.reset` audit row: the switch stays ON. H4 a role name with SQL in it and each name in `_FORBIDDEN_ROLES`: ConfigError before any connection.
- Per-role negative (each Denied unless said): runtime: INSERT on kill_switch_clears; UPDATE and INSERT and DELETE on kill_switch; UPDATE, DELETE, TRUNCATE on kill_switch_stops; `limits reset` on the runtime DSN: exit 2, ON, chain holds `reset` then `reset_failed`. Reset: INSERT on kill_switch_stops; UPDATE and DELETE on both new tables; DELETE and INSERT on kill_switch; SELECT on runs, plans, tool_calls, redaction_maps, spend; INSERT on audit_outbox and audit_checkpoints; UPDATE on audit_entries. Purge and portal: SELECT and INSERT on the three stop relations. Owner: UPDATE, DELETE, TRUNCATE on both new tables raise `psycopg.errors.RaiseException` (trigger).
- migrate refusals (ConfigError unless said): reset role same as runtime ("different roles"); reset a member of runtime and the reverse ("members of each other"); reset role superuser; reset role owns a relation; reset role member of the owner; `GRANT INSERT ON kill_switch_clears TO PUBLIC` with a runtime role named; `GRANT SELECT ON runs TO PUBLIC` with a reset role named. Not a refusal: a direct `GRANT DELETE ON kill_switch_clears TO <reset>` is gone after migrate. A role that does not exist: `psycopg.errors.UndefinedObject` from migrate(), CLI exit 3, 0006 not applied.
- Unit (no database): U1 `Limits.reset` with a store whose `set_kill_switch` raises: the audit holds `reset` then `reset_failed`, the exception leaves. U2 intent raises AuditUnavailable: `set_kill_switch` never called (existing test_review_fixes.py:143-154 stays green). U3 `secret_names(PostgresSettings(..., reset_credential_ref="x"))` does not contain "x". U4 `check_grants` on the real folder is clean; every sequence and every non-stop row has `reset == ""` except the five rows above.

## Mutation plan (mutant -> killing test)
runtime grant on kill_switch_clears becomes append -> runtime INSERT negative; runtime grant on kill_switch back to `_RW` -> F1, F2; reset block in migrate skipped -> N2; `effective_problems` not run for the reset role -> "SELECT ON runs TO PUBLIC"; `reset_role` left out of `named` -> "different roles"; read drops the NOT EXISTS -> N2; read ignores open stops -> N1; read ignores the flag -> E5 (before the reset) and E7; ON CONFLICT removed -> E2; clear and flag update not in one transaction -> E8 variant with the second statement failing; `Limits.reset` clears before the intent -> E8; `reset_failed` not written -> U1; triggers removed from 0006 -> owner negatives; CLI reset ignores the ref -> N3; CLI pilot refusal removed -> E10; missing row reads OFF -> E6; reset grant on audit_entries dropped -> N3; id back to BIGSERIAL -> H2; loop hunk removed -> F3; `_FORBIDDEN_ROLES` check removed -> H4.

## Evidence commands (raw output saved under handover/core-b/evidence/B-*.txt)
```
uv run --all-extras --group test pytest tests/test_stop_state_unit.py tests/test_stop_state_loop.py tests/test_k2_migrations.py tests/test_migration_numbers.py tests/test_migration_numbers_guards.py tests/test_cuj.py tests/test_review_fixes.py tests/test_s5_runtime.py tests/test_k3_leftovers.py
HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test pytest tests/test_stop_state_roles.py tests/test_p2_postgres.py tests/test_p7_store.py tests/test_k2_migrations.py tests/test_k5_fixes2.py tests/test_k5_round10_postgres.py tests/test_k5_round8_postgres.py tests/contracts
HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/stop_state_mutants.py
uv run --all-extras --group test ruff check src tests && uv run --all-extras --group test ruff format --check src tests
```
Without HADAVIN_TEST_PG_DSN the Postgres tests SKIP; a skipped run is reported NOT RUN, never as passed.

## Settled only by a run
- The foreign-key check lets the reset role insert a clear without a right on kill_switch_stops beyond SELECT: test N2.
- `gen_random_uuid()` and the 0006 text pass the lexer and guards: tests/test_migration_numbers.py::test_the_real_files_read_clean, tests/test_k2_migrations.py::test_the_real_ledger_and_grant_map_agree_with_the_migrations.
- The owner-membership check does not refuse the runtime and purge roles of existing fixtures: tests/contracts and tests/test_k5_round10_postgres.py on Postgres.
- tests/test_stop_state_loop.py passes after the hunk: F3.
- A NUL in `--by` exits cleanly: H1.
- The reset login can build the chain audit with no signer and write the intent: N3.

## Rollback
Tag `pre-B` before merge. The migration is additive (two new tables); the released file is frozen by the manifest row, a later fix is a new migration. The change of meaning is NOT revertible by code alone: old code does not read kill_switch_stops and its stop needs UPDATE on kill_switch, which the runtime role no longer holds, so an old `limits stop` fails loudly with exit 2 (the loud-failure test is the runtime UPDATE negative). To go back: stop every runtime process; as owner run `UPDATE kill_switch SET "on" = TRUE WHERE EXISTS (<open stop query>)` so an open stop is not lost; restore the snapshot taken before migrating, or by hand `GRANT INSERT, UPDATE ON kill_switch TO <runtime>` and delete the `0006_stop_state` ledger row after dropping the two tables. CHANGELOG upgrade steps: stop all runtime processes (no mixed versions); create the reset LOGIN role; run `migrate --runtime-role R --purge-role U --reset-role X` in ONE command; set `backends.store.reset_credential_ref` on the operator's machine only; start the new code.

## What stays out
Everything in the draft's not-reused list (database functions with definer rights, the session-user guard trigger, login labels and audit/labelkey.py, the version and open-count pair and `--expect-*` flags, a stop role, runtime/stop_state.py and the probe tick step, `limits check|whois|status`, ALTER ROLE defaults, StoreBusy and a cap on open stops, LimitsSettings, a required reset_role); database-attested "who"; privacy labels for `by`; a grant-drift probe; the eval and replay paths reading the stop state; an audit_outbox right for the reset role (a `reset_failed` that cannot be appended is kept in memory and lost at exit); pruning old stop rows.

## Open questions (each with the recommended answer)
1. The small shape above instead of the branch design? Yes.
2. The reset login writes the reset audit row itself (so the operator needs one DSN, not two)? Yes; cost: it can append any audit row, as the runtime can.
3. Keep the old flag in the read? Yes (invariant 12, no data copy).
4. Require `reset_credential_ref` in the pilot/prod config validator? No; the runtime must not need it. The CLI refuses `limits reset` without it in pilot and prod.
5. May the reset login also stop? No.
6. Take the branch's loop hunk and its test? Yes (read: imports resolve on main, the test fails before and should pass after; F3 settles it).
7. UUID id instead of the draft's BIGSERIAL? Yes (closes the planted-id attack, removes the sequence and its grant row). If refused: keep BIGSERIAL, add the sequence row `Grant("sequence", "USAGE")` and accept that a hostile runtime can make a stop fail.
8. Take the owner-membership check and `_FORBIDDEN_ROLES` from the branch? Yes; the membership check also applies to the runtime and purge roles, so the full Postgres suite must run.
9. The reset updates the flag row every time (records who reset last), not only when the flag was on? Yes; it matches what an OFF read returns today.
10. Warn in `migrate` when a runtime role is named without a reset role? Yes (3 lines); do not refuse, demo setups have no reset role.
11. Change the `reset` exit-2 text? Extend only; three substrings are pinned.

## Size
About 26 SQL lines, 95 source lines (migrate 30, postgres 25, cli 22, agent_loop 12, limits 4, table 3), 380 test lines in four files plus 15 lines of edits in five existing test files, 45 doc lines.

## RESOLUTION of review round 1 (binding; where it differs from the text above, THIS section wins). Report: tickets/B-review-1.md
S1 (cb-B1, temporary tables). Code: the store resolves its schema once at connect (current_schema()) and every statement on kill_switch, kill_switch_stops and kill_switch_clears names the schema explicitly, so a temporary table cannot shadow them. New invariant 14: a temporary table with one of the three names does not change what the store reads. Stated limit (new, also in SECURITY): the guarantee is about the state stored in the database; a runtime PROCESS that is itself taken over can ignore any switch, so it must also be stopped from outside (stop the process).
S2 (cb-M1, cb-M2, ir-8, who else can clear). Code: whenever migrate applies grants, it lists every role in the database, other than superusers, the owner and the named reset role, that could clear a stop: it holds INSERT on kill_switch_clears or UPDATE on kill_switch, or it is a member (with or without inheritance, pg_has_role MEMBER) of a role that does, including the reset role. Any such role is a refusal that names the role. With no reset role named the same check runs with nobody excluded but the owner, so a forgotten old runtime role with UPDATE is refused too. Invariant 7 now reads: after a successful migrate no role other than the owner, superusers and the reset role can clear a stop, whichever roles were named in that call.
S3 (cb-M3). Stated limit: "the reset is audited first" is done by the limits reset command; the database does not force it. A person with the reset login can clear by hand without an audit row.
S4 (cb-M4, ir-10). Line 135 reads: the reset role cannot add a stop row; it can set the old flag ON (a stop), which is the safe direction. No column grant is built.
S5 (cb-M5). Invariant 4 reads: a reset clears the stops visible to its clear statement; a stop committed after that statement began stays ON; a stop committed between the audit intent and that statement is cleared. Run a second reset, or read the state, to be sure. Code comment, protocol docstring and runbook say the same.
S6 (cb-M6, ir-1, ir-5). Mutants run with tests/stop_state_mutants.py --hand (the runner gives its child no database DSN by design). "ON CONFLICT removed" is killed only by a test with two resets while the kill_switch row is missing (added); if it still survives it is listed as equivalent with the reason. "Not one transaction" is killed by a test that makes the clear insert fail for the reset login (REVOKE INSERT on kill_switch_clears from the reset role by the owner) and asserts the flag is still ON.
S7 (cb-M7). Code: a reset whose UPDATE on kill_switch touches no row raises (the row is missing: broken schema); Limits.reset then writes reset_failed and the command exits 2 with the state still ON. E6 expects exit 2 and reset_failed.
S8 (cb-M8, ir-2, ir-3, ir-4). Owner negatives: rows exist in both tables first; TRUNCATE is tested with CASCADE (a plain TRUNCATE fails earlier on the foreign key with FeatureNotSupported). E7 applies the five older SQL files by hand, sets the flag, then runs migrate. The config set-up for N3 and E10 is the one in tests/test_stop_state_roles.py (the env secrets kind with only the reset DSN); the runtime-DSN reset case runs in pilot with the ref pointing at the runtime DSN.
S9. tests/test_stop_state_unit.py (U1, U2, U4, F2), the migrate warning test and exit 4 for reset are still to be written (test writer, after fix round 3).
S10. Rollback steps go into docs/stop-state-runbook.md with the full open-stop query written out.
S11 (ir-6, ir-7). The six "from the branch" items are no longer references: they are in the tree (owner-membership check migrate.py:226-229, loop hunk agent_loop.py:250-254 and 788-791, tests/test_stop_state_loop.py, the role fixture in tests/test_stop_state_roles.py, tests/stop_state_mutants.py, docs/stop-state-runbook.md). Commit order as built: source with pins and existing-test edits together; role tests; docs. Edits to existing tests were made by the builders and are listed in notes/builder-B-report.md and the fix reports.
S12 (nits). Code: the stop INSERT does not pass ts (the database clock sets it) and the table refuses a ts that is not finite. The "Open questions" are DECISIONS (taken by core-b, verdict column in DECISIONS.md for the lead). 0006_stop_state is the final number. notes/builder-B-report.md is stale where it says BIGSERIAL, sequence, WHERE "on" and "loop hunk not taken". Not done, stated: the PostgreSQL 17 MAINTAIN right is not checked by effective_problems (UNVERIFIED whether it matters); an ungranted reset login gets the message "the audit tables are missing".
