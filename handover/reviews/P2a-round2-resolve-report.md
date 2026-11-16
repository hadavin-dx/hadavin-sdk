# Goldfish Annotated Review Report (resolve, round 2)

Status: findings categorised; the author applies them (ticket revision 4)

**Target:** `handover/tickets/P2a.md` (revision 3). Findings: `handover/reviews/P2a-round2-adversarial.md`, `handover/reviews/P2a-round2-correctness.md`. Counts: 30 findings, all PROPOSE FIX (none contested, none escalated: the lead answered the open questions in `LEAD-ORDERS.md` order 5 / amendment A14).

## Lead decisions that apply (order 5)
Order 5 (a): Route A, fully specified: exact grant lists (runtime role keeps INSERT, UPDATE or the store changes to plain UPDATE: choose and say; reset role SELECT, UPDATE plus audit rights), a reset DSN secret name in the store settings (files: backends/table.py, app.py, cli.py), `migrate(reset_role=...)` creating the trigger function with the role name (deny-all when no reset role), per-person login roles in a NOLOGIN reset group, `ENABLE ALWAYS TRIGGER`, `session_user`, start-up probe that refuses in pilot/prod, `release` as an operator-process action on a reset-role store. Route B is refused (the least-privilege rule needs a real separate credential). (g): fix every blocker and major, or contest with evidence in the disposition file. Wiring owner and scope of P2a-2/P2a-3 stay PENDING LEAD with a recommendation.

Note on the gate (skill Step 4): the owner told the cloud session to follow `LEAD-ORDERS.md` (allowed actions only) and to run the resolve step; the auto-accept path is taken for every PROPOSE FIX, as in round 1.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** Security (agent runtime bullet); Files of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The ticket narrows the runtime grant on `kill_switch` to `SELECT, UPDATE` and reuses the existing unconditional upsert. In Postgres, `INSERT ... ON CONFLICT DO UPDATE` needs INSERT privilege on the table, so `stop` stops working.
*   **Rationale:** evidence: `postgres.py:453-460` (upsert); `migrate.py:55` (`_RW`, which includes INSERT); the ticket lists the postgres.py change only as `clear_kill_switch_if`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security (agent runtime bullet); Files
    *   Change: Rewrite `set_kill_switch` as a plain `UPDATE ... WHERE id=1` (the seed row exists, `0003:25-27`), or keep INSERT and say so. Add a negative test as a real runtime login: stop succeeds and clear is refused. State the effect on old code in Rollback.

### [Issue 2] [`egm-design`] - Severity: Blocker (finding id A2, adversarial)
*   **Affected Scope:** Interface (`StopGate.release`); Security of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The gate keeps `release(by)`, which calls `Limits.reset`, inside the agent-runtime process. Reset needs the reset database role, and the ticket says the runtime must not hold it.
*   **Rationale:** evidence: Ticket lines 30-31 and 47-49 conflict. The Security section never says which process holds the reset-role connection.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (`StopGate.release`); Security
    *   Change: Say which process holds which DSN. Remove `release`/`restore(False)` from the runtime-held gate, or define them as an operator-process API on a separate store handle built with the reset DSN. Add a test that the runtime process cannot construct a reset-capable `Limits`.

### [Issue 3] [`egm-codebase-details`] - Severity: Blocker (finding id C1, correctness)
*   **Affected Scope:** Security (DB-role design, "GRANTS['kill_switch'] changes to runtime SELECT, UPDATE with reset-role UPDATE"); Files (P2a-1) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** As written, the database part cannot be built correctly. (a) The runtime stop cannot be written. `PostgresStore.set_kill_switch` is `INSERT ... ON CONFLICT (id) DO UPDATE`. Postgres needs INSERT privilege for any INSERT statement. A runtime grant of `SELECT, UPDATE` makes `Limits.stop` fail with "permission denied" on the real runtime role, so the emergency stop stops working. The ticket says the runtime keeps "UPDATE" and does not mention INSERT or changing the store to a plain UPDATE. (b) The reset role gets "UPDATE" only. `clear_kill_switch_if` has a WHERE on `id`, `"on"`, `by` and `ts`, so it also needs SELECT. `Limits.reset` also writes audit rows through a sink built on the same store connection, so that role needs the audit INSERT rights too, or the reset needs a second connection. The ticket gives the reset role neither. (c) There is no path for the reset credential. The only precedent is the purge role: `backends/table.py:120` (`purge_dsn_secret_name`), `app.py:86-89` and `152-160` (second `make("store")`), and `migrate.py:288-353` (`purge_role` in three places). The CLI builds one store from `b.store` (`cli.py:189`) and passes it to `Limits` (`cli.py:209`). The ticket's new config section `limits` has only `reset_names`, `label_key_secret`, `key_id`, `max_cache_ttl_s`. No reset DSN secret name, no change to `backends/table.py` (a hot file in amendment F6) or `backends/builtin.py`, and no second store in `app.py` or `cli.py` is listed. So "connecting with the reset database role" has no implementation. (d) The trigger cannot learn the reset role name from a migration file. `migrate()` applies static SQL files (`migrate.py:327-332`) and only afterwards takes the role arguments. The ticket marks this UNVERIFIED but calls the whole item a GATING ITEM. It also does not say that `migrate()` must add `reset_role` to the validation tuple and the distinct-role and not-members-of-each-other checks (`migrate.py:298-303`, `333-339`). It does not say what the trigger does when no reset role was given (it should refuse for everyone). (e) Every existing Postgres test that resets uses the owner or superuser DSN: `tests/test_p2_postgres.py:213` and the `pg_schema` DSN (CI runs as `postgres`, `ci.yml:86`). The trigger will refuse those. The existing role tests create NOLOGIN roles and only check `has_table_privilege` (`test_p2_postgres.py:173-196`; `test_p7_store.py:136-158`), so the ticket's "negative tests with the runtime credential" need `SET ROLE` in a superuser session or LOGIN roles. The ticket mentions none of this. On PENDING LEAD item 3: the trigger itself is sound. A BEFORE UPDATE trigger fires on the `ON CONFLICT DO UPDATE` path. `_SAFE_CREATE` (`migrate.py:80-85`) allows `CREATE OR REPLACE FUNCTION` and `CREATE [OR REPLACE] TRIGGER`, and `0002_audit_chain.sql:25-31` is a precedent. But it is sound only after (a)-(e) are fixed. Note also: a runtime role with UPDATE can still rewrite `by` and `ts` while the switch is ON. That is attribution forgery, and it can keep invalidating the reset token.
*   **Rationale:** evidence: `postgres.py:453-464`; `migrate.py:46-68,80-85,283-353`; `app.py:56,86-89,152-160`; `cli.py:183-209`; `backends/table.py:120`; `ci.yml:86`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security (DB-role design, "GRANTS['kill_switch'] changes to runtime SELECT, UPDATE with reset-role UPDATE"); Files (P2a-1)
    *   Change: Name the privilege lists exactly: runtime `SELECT, INSERT, UPDATE` (keep the upsert), or change the store to UPDATE-only and say so. Reset role `SELECT, UPDATE` on `kill_switch`, plus whatever the audit sink needs. Add `reset_dsn_secret_name` to the store settings and to the file list (`backends/table.py`, `app.py`, `cli.py`). Specify how `migrate(reset_role=...)` sets the trigger (e.g. a Python-issued `CREATE OR REPLACE FUNCTION` using `sql.Literal`, deny-all by default). Specify how tests obtain the reset and runtime roles (`SET ROLE`). Option that honours A13(3) literally: runtime role SELECT-only on the table, plus a `SECURITY DEFINER` function "stop(by)" that can only set ON, with EXECUTE granted to the runtime. `_apply_grants` and `effective_problems` do not manage function privileges, so the ticket would have to add that.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A10, adversarial)
*   **Affected Scope:** Test plan of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The mutation plan has no rows for the parts that enforce the rule. The 48 gate rows and the runner rows mutate Python snippets only.
*   **Rationale:** evidence: Ticket line 53 marks the CI requirement UNVERIFIED. `HADAVIN_TEST_PG_DSN` is a single DSN, with no plan to create the separate runtime, reset and migration logins.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Test plan
    *   Change: Add mutation rows for `migrate.py` GRANTS, the migration SQL, and the `clear_kill_switch_if` WHERE clause (drop `by`, drop `ts`, drop `"on"`). Make the Postgres tests create their own logins and fail, not skip, when the DSN is missing or the role cannot create roles. Say that threads alone do not prove the race (item g). The 200-interleaving test uses threads in one process (a seeded schedule on the GIL is not a deterministic proof), so label it a smoke test and rely on race (b) plus a real two-connection test.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A3, adversarial)
*   **Affected Scope:** Security (trigger); UNVERIFIED "how the reset role name reaches the trigger" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The role name has no workable route into the trigger.
*   **Rationale:** evidence: `migrate.py:283-339`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security (trigger); UNVERIFIED "how the reset role name reaches the trigger"
    *   Change: Do not take the name from a setting. Check `pg_has_role(session_user, '<reset group>', 'MEMBER')` against a role created by the migration or a fixed documented name, or look the name up in a table that the runtime cannot UPDATE. Define the default as fail closed and make the migration idempotent for re-runs. Add `reset_role` to the pairwise membership check and to `effective_problems`.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** Security (trigger bypass) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The ticket never says which of `session_user` or `current_user` the trigger tests, and never covers owner, superuser or `ENABLE ALWAYS`.
*   **Rationale:** evidence: `migrate.py:218-219` already treats owner == role as a problem for the runtime, but only against the grant map. `0002_audit_chain.sql:28` uses plain triggers.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security (trigger bypass)
    *   Change: Use `ALTER TABLE ... ENABLE ALWAYS TRIGGER`. Use `session_user` and require non-membership of the runtime role in the reset group. Make `migrate` refuse a runtime role that owns `kill_switch` or the trigger function. Qualify the schema in the trigger function and fix `search_path`. Negative tests must connect as separate logins, never `SET ROLE` from a superuser.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** Security (reset role); Breakglass of `handover/tickets/P2a.md`
*   **Discrepancy Description:** One shared reset database role is used by every person in `reset_names`, and the same credential is also called "dormant breakglass". Attribution is the typed `--by` only. The reset CLI also needs more grants than the ticket gives it.
*   **Rationale:** evidence: Ticket lines 47, 50; `cli.py:209` builds one `Limits(store, audit, reg)`; `Grant` has no `reset` field today (`migrate.py:23-37`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security (reset role); Breakglass
    *   Change: Per-person login roles that are members of a NOLOGIN reset group. Let the trigger record `session_user` and the time in an append-only table in the same transaction. That gives a DB-authenticated attribution and an audit that survives a down audit sink. Keep breakglass as a separate dormant login. List the exact reset-role grants (kill_switch SELECT/UPDATE plus the audit_outbox/sequence privileges) and run `effective_problems` for it.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** Security; Done of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Nothing at startup checks that the DB enforcement is actually present. The code-level `reset_names` check is a typo guard (the ticket says so), and it is the only enforcement on the memory store and on any Postgres without the migration or role split.
*   **Rationale:** evidence: Ticket line 20 admits that the list is not access control.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Security; Done
    *   Change: In app start-up and in `limits reset`, probe the trigger (it exists and is ENABLE ALWAYS) and the runtime role (not a member of the reset group, cannot UPDATE ON to OFF). Refuse in pilot/prod when the check fails. Make that probe a P2a-1 merge requirement.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Interface (fail closed); agent_loop of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The fail-closed fix names only `_limits_stop` (lines 359, 421, 460). The execution-time check `_recheck` at `agent_loop.py:744` calls `limits.blocked` bare. Line 670 is already guarded and goes to NEEDS_PERSON, not STOPPED.
*   **Rationale:** evidence: `agent_loop.py:730-751, 760-773`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (fail closed); agent_loop
    *   Change: Treat every `limits.blocked` call site the same way (grep all five: 240, 670, 744). Test `execute()` with an unreadable store. Also check whether STOPPED is resumable, so that a one-second database blip does not end runs permanently.

### [Issue 10] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** PENDING LEAD item 1 (wiring); Done of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The recommended position is unsafe for a Tier A stop. The gate ships "unwired". `tick.py` has no stop concept (the ticket's own line 44), and the wiring is handed to P4c, whose scope is `max_run_usd`. Nothing in "Done" requires any real action path to be blocked by `StopGate`.
*   **Rationale:** evidence: Ticket lines 44, 58, 78.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: PENDING LEAD item 1 (wiring); Done
    *   Change: Either name the wiring owner in this ticket and make "a stop blocks the executor call, including the in-flight case" a P2a-1 done condition, or do not call it a stop gate (rename it, and drop the "stops running actions" wording from the Problem paragraph). Settle the UNVERIFIED `tick.py` question before building. Do not rely on P4c.

### [Issue 11] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** Depends on; Files; Done of `handover/tickets/P2a.md`
*   **Discrepancy Description:** P2a-1 is not "one reviewable package" for Tier A. It combines the Limits identity and compare-and-set change, masking, the gate, the CLI, config, `app.py`, `agent_loop.py`, three store files, a migration with a trigger and grants, and the contract kind. It also waits for P3a and P4d-a/b/c. The plan puts P2a in S2 and the stop rule is per pull request, so a defect in the gate blocks the database guard.
*   **Rationale:** evidence: Ticket lines 9-10, 79; plan row P2a (S2, depends on P1) versus P3a (S3).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Depends on; Files; Done
    *   Change: Split P2a-1. (a) Limits CAS and identity, masking, CLI: needs only P1 plus `limits.py`. (b) Store `clear_kill_switch_if`, migration, trigger, grants and role probe: after P3a and P4d. (c) Gate. (d) `agent_loop` fail-closed. "Two commits in one PR" is the wrong remedy because Tier A reviews the head, not the commits. Re-check that P4b1 does not depend on P2a-1 beyond `limits.py` text.

### [Issue 12] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Interface (`release`, `restore`), Security of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The ticket does not say where `StopGate.release(by)` runs. `release` calls `Limits.reset`, which calls `clear_kill_switch_if`. With the trigger in place, the runtime role can never clear, so `release` can never succeed from the process that engaged. The in-process flag `_on` would stay on until restart, and the whole "release vs engage" design (sections on release re-stop window, race test f) only runs when the gate's `Limits` sits on a reset-role store. The ticket does not describe this process split.
*   **Rationale:** evidence: `stop_gate.py:375-411` (PR50-local); `limits.py:48-51`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (`release`, `restore`), Security
    *   Change: State the intended split: either the gate's `Limits` uses a reset-role store, or `release` is an operator-process action. State what `restore(False)` does for a runtime that cannot clear. Add the matching tests.

### [Issue 13] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Files: "Existing tests that call reset ... must be changed" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The list is incomplete. A required `expect` and new required CLI flags break more tests. (1) `tests/test_cuj.py:244-249`: `limits reset --by user:a` on the memory store expects exit 2 and the text "refused". With required `--expect-by/--expect-ts`, argparse exits 2 with a different message. (2) `tests/test_cuj.py:283-306`: fake `Down`/`NotReady` limits define `reset = stop(self, by)` and call `cli.kill_switch(Down(), "reset", "user:a")`. A new `kill_switch(limits, action, by, expect=...)` or `reset(by, expect=)` call raises TypeError, not the expected exit 4 or 2. (3) `tests/test_p2_postgres.py:122-141`: reset with an unreachable store expects exit 4 via `limits reset --by user:a` (line 139). It would hit the argparse error. Also, the helper `cli.kill_switch(limits, action, by)` (`cli.py:383`) has no `expect` parameter, and the ticket does not say how it changes. Also `FakeLimits` in the PR50 gate tests (`test_promoted_controls.py:255-262`, signature pinned `["self","by","source"]`) lacks `status` and `clear_kill_switch_if`. The new gate constructor refuses such a Limits (TypeError), so every moved gate test needs a new fake. The ticket says only "moved".
*   **Rationale:** evidence: files and lines as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Files: "Existing tests that call reset ... must be changed"
    *   Change: Add these tests and `FakeLimits` to the P2a-1 change list. State the new `cli.kill_switch` signature and the exit codes for a missing `--expect-*`.

### [Issue 14] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** Tests, FAIL-BEFORE (1), (2), (5) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The named heads would fail these tests by TypeError or by an unrelated exception, not by an assertion. (1) and (2) call `Limits(..., reset_names=...)` and `reset(..., expect=...)`. Core `Limits.__init__` takes only (store, audit, registry) (`limits.py:14`) and core `reset(by)` has no `expect` (`limits.py:48`). PR50-pushed `reset(by, source)` has no `expect` (`limits.py:52`). PR50-local has `expect` but no `reset_names` (`limits.py:57-59`). A required `expect` (the new rule) means the old-behaviour check cannot be written in the new call shape. (5): the core `_limits_stop` raising propagates out of `handle` as the store's own exception, not an AssertionError. (3) needs Postgres, because the memory CLI path is refused (`cli.py:173-182`). The new `limits` config section is rejected by `extra="forbid"` (`config.py:52,316`), so the test must rely on the dev default key.
*   **Rationale:** evidence: as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, FAIL-BEFORE (1), (2), (5)
    *   Change: Write each fail-before test so the old-shape step runs first and asserts the behaviour (e.g. reset with an unlisted name via the old call shape, assert the switch is still ON). Or state that "fails by TypeError" is accepted and say which tests need a probe helper. State per test the head, the call shape, and the expected failure line.

### [Issue 15] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** "THE WEAK ROW" (ii) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The ticket says "NEW test `RowStore(max_rows=None)` without opt-in raises `ValueError` (none exists), plus the row `rows: unbounded without opt-in accepted`". Both already exist on PR50-local. The test is `test_a_store_without_a_limit_needs_the_named_opt_out_and_the_contract_checks_full_stores` (`test_pr50_fix_batch3.py:353-358`: `pytest.raises(ValueError)` for `max_rows=None`, `max_row_bytes=None` and `max_total_bytes=None`). The row is `b3: a store without a limit needs no opt-out` (`promoted_mutants.py:2088-2095`, `if not unbounded_ok:` to `if False:`). The mechanism of the weak row (fix (i)) matches the code: `rowstore.py:127,134-138`, the row at `promoted_mutants.py:867-873`, pinned test `test_promoted_controls.py:1787`.
*   **Rationale:** evidence: as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: "THE WEAK ROW" (ii)
    *   Change: Delete (ii), or reword it to "keep the existing test and row". Keep (i).

### [Issue 16] [`egm-codebase-details`] - Severity: Major (finding id C6, correctness)
*   **Affected Scope:** Interface "Release re-stop window"; race test (f) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The window is not closed as claimed. In `release`, `_gen` is checked before the store write. In `engage`, the flag is set and `_gen` bumped first, and `Limits.stop` is written later (`stop_gate.py:322-336`). If `engage` runs after the `_gen` check but before `clear_kill_switch_if`, the clear sees the old token and succeeds. The store is OFF for a moment until the engage's stop write lands. If the engage's stop write fails (store error), the store stays OFF while the flag is on. So test (f) "the store is never observed OFF while an engage is pending" cannot hold.
*   **Rationale:** evidence: `stop_gate.py:322-336,379-411`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface "Release re-stop window"; race test (f)
    *   Change: Reword the claim to "the final state is ON, and the store write of a later engage is never lost". Or close the gap: hold the gate lock across the conditional write. Change test (f) to assert the final state only.

### [Issue 17] [`egm-codebase-details`] - Severity: Major (finding id C7, correctness)
*   **Affected Scope:** Mutation plan of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The plan has no mutant for the security property itself. No row for: the migration trigger (removed or loosened), the `reset` field in `GRANTS`, the SQL conditions of `clear_kill_switch_if` (drop `AND "on"`, `by IS NOT DISTINCT FROM`, `ts=`) or its memory twin, or the `reset_names` check in the config path. The runner can mutate any relative file, including `.sql`. The new rows are listed by name with no count, so the "262/103/48" arithmetic stops at the existing rows: 41 + 14 + 48 = 103 is right, but the final row count is not stated. Killers that need Postgres are skipped without `HADAVIN_TEST_PG_DSN` (`tests/contracts/kinds/store_postgres.py:22-24`). A skipped killer means rc 0, so the mutant SURVIVES. Evidence command 3 does not set the DSN.
*   **Rationale:** evidence: as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Mutation plan
    *   Change: Add rows for the trigger, the grants, the SQL conditions and the memory twin, and state the final row count per sub-PR. Add the DSN to evidence command 3 and make the runner refuse a skipped killer.

### [Issue 18] [`egm-codebase-details`] - Severity: Major (finding id C8, correctness)
*   **Affected Scope:** Files (P2a-2) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** P2a-2 owns the runner and judge rows (5 `mutation.py` + 16 `mutation_runner.py` = 21), but the file list names only `tests/test_stop_state_rowstore.py`. The killers of those 21 rows are tests in the four PR50 test files (`test_promoted_controls.py`, `test_pr50_fix_batch*.py`: 12, 4, 6, 4 mentions of the runner or judge). The Tests list for P2a-2 names no runner/judge tests. The new file `tests/test_stop_state_runner.py` (or equivalent) is missing from CREATE.
*   **Rationale:** evidence: `promoted_mutants.py` rows with `MU` and `MR`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Files (P2a-2)
    *   Change: Add the runner and judge test file to P2a-2, with its killers.

### [Issue 19] [`egm-design`] - Severity: Nit (finding id A11, adversarial)
*   **Affected Scope:** Rollback of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The Rollback statement is wrong for the trigger. "A revert silently re-allows any reset" is false once the forward-only trigger exists.
*   **Rationale:** evidence: Ticket line 73.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Rollback
    *   Change: Rewrite the rollback text to the real behaviour (loud failure, not silent permission). Put the downgrade test against the true old code at `ce70eb5` on a migrated database.

### [Issue 20] [`egm-design`] - Severity: Nit (finding id A12, adversarial)
*   **Affected Scope:** Config (`max_cache_ttl_s`) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The `cache_ttl` cap is itself configurable, with default 5 s and no ceiling in code.
*   **Rationale:** evidence: Ticket lines 29-30.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Config (`max_cache_ttl_s`)
    *   Change: Hard ceiling in code (for example 10 s). Never cache on the `status()` path used for the reset token. Reject the config if above the ceiling.

### [Issue 21] [`egm-design`] - Severity: Nit (finding id A13, adversarial)
*   **Affected Scope:** Interface (token) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The reset token is `(by, ts)` with `ts` set by the writer's Python clock, while reset sets `ts=now()` in the database. A reset can be refused indefinitely by repeated stops.
*   **Rationale:** evidence: `models.py:19-20, 251-254` (as the ticket cites); `limits.py:45`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (token)
    *   Change: Since a migration is already being added, add a server-side `version` BIGINT incremented by the trigger and use it as the token. Write `ts` with the database clock. Rate-limit or collapse repeated stops by the same masked name, and document the lock-out case.

### [Issue 22] [`egm-design`] - Severity: Nit (finding id A14, adversarial)
*   **Affected Scope:** Masking and keys of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The label key sits in the agent-runtime process, so a compromised runtime can compute the label of any known login and write a stop or audit entry under that label. The hash gives privacy, not authenticity. Retention conflicts with erasure.
*   **Rationale:** evidence: Ticket lines 27-28
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Masking and keys
    *   Change: State that `by` is unauthenticated unless it comes from the DB role (see A5). Have the reset CLI and the runtime hold different keys, or let only the operator CLI hold the reverse key. Write the erasure position into the runbook. Keep the dev fallback out of any stored data that outlives the process.

### [Issue 23] [`egm-design`] - Severity: Nit (finding id A15, adversarial)
*   **Affected Scope:** Neutral default / alternative of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The `StopBackend` outline defines `clear_if`, but `Limits` and the gate use `Store.clear_kill_switch_if`. Two interfaces, and no statement of how one is chosen. A hosted adapter also bypasses the DB trigger.
*   **Rationale:** evidence: Ticket lines 35, 30
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Neutral default / alternative
    *   Change: In the outline state: the adapter must carry its own restricted-reset identity, `Limits` takes the backend by injection, and the contract suite includes the "runtime credential cannot clear" case. Add the single-dependency audit line the rules ask for.

### [Issue 24] [`egm-design`] - Severity: Nit (finding id A16, adversarial)
*   **Affected Scope:** Row store; neutral default of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The memory store kill switch is per process and lost on restart. The ticket only addresses row-store durability (item 5), not the switch.
*   **Rationale:** evidence: `memory.py:218-224`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Row store; neutral default
    *   Change: Make `limits stop/reset/status` refuse on a memory store unless `environment == dev`. Add that to P2a-1's tests instead of waiting for P6a.

### [Issue 25] [`egm-design`] - Severity: Nit (finding id A17, adversarial)
*   **Affected Scope:** Wording of `handover/tickets/P2a.md`
*   **Discrepancy Description:** (1) "STOP is never refused" is later followed by `Limits.stop` raising after the write when the audit is down; the CLI wording for that case is not specified. (2) "The old `stop_identities` list is deleted": it does not exist in core. (3) "the runtime role is read-only on kill_switch" (A13(3)) versus the ticket's deviation: acceptable, but the ticket calls its own proposal "the property that matters" before the lead has decided. (4) `_SAFE_CREATE` allows `CREATE OR REPLACE FUNCTION` and `CREATE TRIGGER` but not plain `CREATE FUNCTION`; the migration must use the first form. (5) "all deterministic" in Tests conflicts with the seeded thread test.
*   **Rationale:** evidence: |
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Wording
    *   Change: Fix the wording in the same batch.

### [Issue 26] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** Interface "Who may do what" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** "The old `stop_identities` list is deleted": no such list exists in core, PR50-local or PR50-pushed (grep found nothing in the snapshots). It was only a revision-1 idea of the ticket (ledger BL-core-p2a-r1-adv-A2).
*   **Rationale:** evidence: grep over `/tmp/.../snap`; `handover/ledger.md:49`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface "Who may do what"
    *   Change: Delete the sentence.

### [Issue 27] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** Interface (`StopGate` signature; masking) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** `StopGate(limits, *, cache_ttl, unaudited)` drops PR50-local's `label_key`. But the gate writes its own audit rows: `restore` events (`stop_gate.py:230-238`) and `_audit_stop_failed` (`364-373`), both via `_lbl(by)`. The ticket says masking happens "ONCE in `Limits._event`" but does not say which function these gate rows use, so the "same form on every path" claim is unsupported. Also `Limits.is_stopped` (used by the gate at `stop_gate.py:180,197`) is missing from the Interface and from the constructor check (stop, status, `clear_kill_switch_if`). Core `Limits` has no `is_stopped` (core `limits.py` has none).
*   **Rationale:** evidence: as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (`StopGate` signature; masking)
    *   Change: Say the gate asks `Limits` for the masked form, and list `is_stopped` as a NEW core method.

### [Issue 28] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** Mutation plan "Existing gate rows kept" of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Two existing rows target code the redesign deletes: `release ... expect=self._wrote` (`promoted_mutants.py:2026-2031`) and `b3: reset ignores a changed switch` (`2032-2039`, targets the read-then-write in `limits.py:66-67`). The runner reports an error when the snippet is not found. The ticket lists four "kept" rows but does not say which of the 48 are re-pointed.
*   **Rationale:** evidence: as given
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Mutation plan "Existing gate rows kept"
    *   Change: List the re-pointed rows.

### [Issue 29] [`egm-codebase-details`] - Severity: Nit (finding id C13, correctness)
*   **Affected Scope:** Depends-on / hot files of `handover/tickets/P2a.md`
*   **Discrepancy Description:** Amendment F6 lists `store/postgres.py` as (P4d, P4b1, P6b2). The ticket says P4b1 no longer edits it (A11 is later and wins) but does not say where P2a-1 sits relative to P6b2. `CHANGELOG.md` is a hot file (plan rule 10), and P2a-2 and P2a-3 both change it with no stated order relative to the other packages.
*   **Rationale:** evidence: `amendments.md:22,30`; `plan-v3.md:68`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Depends-on / hot files
    *   Change: State the position of P2a-1 on `store/postgres.py` against P6b2, and the CHANGELOG order.

### [Issue 30] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Fail closed (`agent_loop`) of `handover/tickets/P2a.md`
*   **Discrepancy Description:** The `_limits_stop` fix says a store error ends the run STOPPED. `_to` and `_note` write to the same store (and audit), so with a really unreachable store they raise again. The change only takes effect when `get_kill_switch` alone fails (e.g. a grant error). The gap of the same class at `agent_loop.py:744` (`_recheck` calls `self.limits.blocked(agent.id)` without a handler, right before execution) is not mentioned. `670-672` already handles it.
*   **Rationale:** evidence: `agent_loop.py:239-250,421,460,744`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Fail closed (`agent_loop`)
    *   Change: State the limit of the fix. Guard `_recheck` the same way.
