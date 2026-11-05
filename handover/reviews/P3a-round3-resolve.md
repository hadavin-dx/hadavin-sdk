# P3a round 3 resolve report (egm:egm-resolve, Opus 5.5)

Status: resolved (categorised; ticket NOT edited here; the author rewrites revision 5)
Target: `handover/tickets/P3a.md` rev 4 (2fe14e1). Inputs: `P3a-round3-adversarial.md` (A1-A15), `P3a-round3-correctness.md` (C1-C11). Interactive gate skipped (auto mode; no contest or escalation).
Governing order: LEAD-ORDERS 6(f): REMOVE `--accept-late` and `migrate(accept_late=...)`; go back to the hand recipe of A13(5) (apply the late file by hand, insert its ledger row by hand, under the migration lock); KEEP the CI check; write the runbook path for a database that applied the PR #41/#49 migrations.

| id | category | decision for revision 5 |
|---|---|---|
| A1 | MOOT by 6(f) | The accept-late flag is gone. Replace the refusal message: it must not give a command that cannot succeed; point to the written hand recipe. |
| A2 | MOOT by 6(f) (the hand recipe keeps an audit need) | The recipe prints an audit line to write into the change log; no flag, no new column. |
| A3 | PROPOSE FIX | Keep the `_UNREAD` list and ADD transaction control and session changes: `COMMIT`, `BEGIN`, `ROLLBACK`, `SAVEPOINT`, `SET TRANSACTION`, `SET ROLE`, `SET SESSION AUTHORIZATION`, `RESET ROLE`, persistent `SET search_path`; planted tests; literal-text false-positive test (ties to C8). |
| A4 | MOOT by 6(f) | The "grants in the same run" claim goes with the flag. Drop mutants M22-M26 that concern accept-late; keep a test that a normal run applies grants. |
| A5 | PROPOSE FIX | State how schemas A, U and F are built; apply files by direct SQL or patch `check_grants` to `[]` (as `test_k2_migrations.py:392`); say how a later GRANTS row does not break baseline builds (ties to C1). |
| A6 | PROPOSE FIX | Either build A, U, F with the real roles and compare ACLs, or stop claiming ACL comparison: state that GRANTS map changes are checked by `check_grants`/the grants test; add seed rows that exercise UPDATE/DELETE paths; hand-written seeds (ties to C2). |
| A7 + C10 | PROPOSE FIX | Write the runbook for a database that applied PR #41/#49 migrations (`0005_measure`, `0005_reservations`, `0006_evidence`): exact check queries, the DBA-run hand steps under the migration lock, and what to do when no matching file exists yet; reword the merge-precondition rationale per C10 (those databases are already refused today); owner question stays open. |
| A8 | PROPOSE FIX | Hand recipe takes the lock explicitly: give the lock SQL with the numeric value of `_LOCK` (`migrate.py:69`) computed and verified by a test; steps in one transaction; no interleaving with a running `migrate`. |
| A9 | PROPOSE FIX | Correct the cost-of-declining argument; keep the manifest scope recommendation but state it buys hash immutability only. Stays PENDING LEAD. |
| A10 | PROPOSE FIX | The message does not print a full command; refer to the runbook. List P2a (`--reset-role`), P5b3, P6b2 as editors of `_migrate`/sub-parser in the hot files. |
| A11 | MOOT by 6(f) | Concerned the flag. |
| A12 + C11 | PROPOSE FIX | Escape file names (repr) in all messages; self-contained message text (no CHANGELOG pointer only); test with a control-char and surrogate name; state exit code for `MigrationNumberError` (C4 remainder). |
| A13 | PROPOSE FIX | Add `late_files(applied, files)` as a pure function with unit tests; the new Postgres tests must fail, not skip, when the CI flag is set (ties to P4d `require_backend`). (C5 same.) |
| A14 | PROPOSE FIX | Runbook warns about `ACCESS EXCLUSIVE` with no `lock_timeout` until P4d; document online-index path as a later ticket; `--` inside string literals noted in the stripping text. |
| A15 | PROPOSE FIX | Fix word definitions ("released" = manifest list; CI claim only for committed files; plain statement on layer 1). |
| C1 | PROPOSE FIX | Layer 1 applies files with `check_grants` patched to `[]` or direct SQL; add planted cases for sequence settings, type/domain, `COMMENT ON`, or drop those M27 mutants. |
| C2 | PROPOSE FIX | Hand-written seed rows per table; plant data change on a CHECK-free column (`UPDATE runs SET agent_id = upper(agent_id)`); say whether "migration raises" counts as failing for the NOT NULL plant. |
| C3 | PROPOSE FIX | Split the `gone` message: if the ledger's highest number is above the folder's highest, say "this database is newer than this release; do not rename or drop; run the newer image"; test the text. |
| C4 | MOOT in part | Flag test moot; keep: state failure output and exit code of `MigrationNumberError` at the CLI. |
| C5 | PROPOSE FIX | `late_files()` pure function; `order_problems` wraps it (no `done.add` needed without the flag). |
| C6 | PROPOSE FIX | Cite `migrate.py:308-360`. |
| C7 | PROPOSE FIX | Add a plant where upgrade path differs from fresh; name the killer test. |
| C8 | PROPOSE FIX | M21 only for CONCURRENTLY, VACUUM, ALTER SYSTEM, ALTER TYPE ... ADD VALUE, REINDEX, DROP DATABASE; literal-text false-positive test; say whether `pglast` (already `pyproject.toml:52`) was considered. |
| C9 | PROPOSE FIX | Add P2a to the hot-file sentence; P3a merges first. |

Counts: 26 findings; PROPOSE FIX 19, MOOT 7 (A1, A2, A4, A11 whole; C4 in part), CONTEST 0, ESCALATE 0, DECLINE 0. Severity unchanged. Model: Opus 5.5.
