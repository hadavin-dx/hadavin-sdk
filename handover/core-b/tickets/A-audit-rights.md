# TICKET A: audit runtime rights (migrate.py). From xreview bfix2 finding 2 (handover/core-b/requests/xr-bfix2-from-core-a.md). Written 2026-11-20.
- Dependency: AFTER G (migrate.py). G is editing the GRANTS rows; do not start before G is merged, then re-read the lines below (they are from cloud/core-b 976e938fb and will have moved).
- Path class: migrate change (grants and a refusal), no new SQL migration needed for the first two points. Tests: tests/test_audit_runtime_rights_pg.py already holds the target (two xfail tests that must flip to pass; remove their xfail marks in the same commit).

## What is wrong today
1. `src/hadavin_sdk/store/migrate.py:93` `"audit_outbox": Grant("table", "SELECT, INSERT, DELETE")`: the runtime login can DELETE parked events (they are not yet in audit_entries, so nothing shows the loss).
2. `migrate.py:92` `"audit_checkpoints": Grant("table", _APPEND, portal=True, reset="SELECT", release="SELECT")`: the runtime login can INSERT a checkpoint. A planted row at the head's seq gives a false alarm in verify. (0009 `hadavin_audit_checkpoint_guard` requires seq = a real entry and its hash, so only a row for the current head or an older entry's seq is possible.)
3. `migrate` does not refuse a runtime role that owns the audit tables (DECISIONS.md:62 as cited by the review); an owner can disable the append-only triggers.

## Who writes what (read from the code)
- audit_outbox DELETE: only `ChainAudit.reconcile`/`_drain` (src/hadavin_sdk/audit/chain.py, "_drain"), run by the tick step `audit_drain` under the runtime login (tick.py STEPS). It is the one legitimate deleter, so the runtime cannot simply lose DELETE: the drain must move to a role that holds it, or the outbox row must be marked instead of deleted (for example an `drained_at` column, runtime UPDATE of that column only, a purge job deleting old drained rows under the purge role). Decide in the ticket review; recommended: a mark column plus purge by the existing purge role (`purge="DELETE"`, columns as `tool_calls`).
- audit_checkpoints INSERT: `ChainAudit.checkpoint()` (chain.py:647-670), called (a) inline from the audit write path every `checkpoint_every` rows (chain.py:321-322) in the runtime process and (b) by the tick step `checkpoint` (tick.py:179-181, STEPS 333) under the runtime login. The reset and release roles hold only SELECT on it (cli.py:326-327 says the reset role "may not write a checkpoint; the tick does that under the runtime login"). So today the ONLY writer is the runtime login, and the signer key is available to it.
- Therefore removing the runtime INSERT needs a NEW role: a checkpoint role (name `checkpoint_role`, `migrate --checkpoint-role`, `Grant(..., checkpoint="SELECT, INSERT")` on audit_checkpoints and SELECT on audit_entries), used only by the tick `checkpoint` step with its own DSN (like `purge_dsn_secret_name`, `reset_credential_ref`). The inline checkpoint at chain.py:321-322 must go (the tick signs instead) or take that second connection. Without a signer there is no checkpoint at all and the runtime needs nothing on the table beyond SELECT. This is a real design change (a second login and a secret for it): it needs a ticket review; the cheaper alternative is to keep runtime INSERT and state it as a limit (already done in SECURITY.md).

## Change
- migrate.py:93 runtime `"SELECT, INSERT"` (+ `"UPDATE"` on the mark column only, or nothing if the drain moves to a deleting role); migrate.py:92 runtime `"SELECT"`, new role gets the INSERT; extend `Grant`, `check_grants`, the role-distinctness checks (migrate.py ~1058-1130) and `--checkpoint-role` for the new role.
- New refusal in `migrate`: if the runtime role (or the checkpoint role) owns audit_entries, audit_checkpoints or audit_outbox, or is a member of the owner role, exit with a ConfigError naming the table; a superuser/owner outside the guarantee as for the stop state.
- Docs: SECURITY.md and README.md (the conditional sentence added with this ticket) drop the two "wider than needed" limits once they hold.

## Acceptance tests (tests/test_audit_runtime_rights_pg.py, plus the existing exact-rights tests)
- The two xfail tests `test_runtime_has_no_delete_on_audit_outbox` and `test_runtime_has_no_insert_on_audit_checkpoints` pass with the xfail marks removed.
- New: a runtime role that owns audit_entries (ALTER TABLE ... OWNER TO) makes `migrate` refuse, naming the table; same for a member of the owner role.
- New: the tick `checkpoint` step under the checkpoint login writes a checkpoint; under the runtime login a checkpoint insert is InsufficientPrivilege; `audit verify` is ok afterwards.
- New: events parked in audit_outbox are still drained by `audit_drain` (tests/test_audit_drain.py unchanged green) and the runtime cannot remove an undrained row.
- The exact-rights tests of the other roles (reset, release, portal, purge) stay green; ruff clean.

## Out
No change to the hash chain, signer or anchor formats; no change to audit_entries rights (already enforced and tested).
