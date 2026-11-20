# A-audit-rights build, review 2 (hostile, round 2: fdf4b214e, 366938404, 0a2e0bd7f)

Ran in worktree RAB52 with a private DB: tests/test_audit_rights_roles_pg.py, tests/test_audit_checkpoint_app_pg.py and
tests/test_migrate_cli_checkpoint_warning.py: 39 passed.

Verdict: no Blocker. 1 Major (doc overclaim), 4 Minor.

## Verified clean

1. 0012 quarantine (src/hadavin_sdk/store/migrations/0012_audit_outbox_functions.sql, quarantine body).
   - The only DELETE targets `o.event_id = p_event_id`, which is the row just locked by `SELECT ... FOR UPDATE` and
     proven not under the prefix. It runs only when the candidate holds an identical `body`. The table is
     (event_id, body) only, so identical body means identical content: after the delete a row with the same content
     stays. Nothing is lost. A planted `prefix||X` (or `#n`) row with the same body deletes only the new copy; with a
     different body the new row goes to the next free `#n`. Both are tested (test_a_planted_quarantine_name_..., A10).
   - A runtime that plants a copy of its own parked row and then quarantines it hides the row: already the documented
     residual (rename-hide). It gains nothing new.
   - Race of two ticks on one id: the second blocks on FOR UPDATE; after the first commits its RENAME the re-check
     fails and it returns 0. No double rename.
   - Concurrent `done` on the same id: quarantine blocks, then finds nothing and returns 0. Quarantine renames while
     `done` waits: `done` then finds no row with the old id and deletes nothing (a renamed id is never done: correct,
     a poison row is not in audit_entries).
   - `#` in event ids: `a` at `#1` vs an event actually named `a#1` can contend for one name. The loser gets a unique
     violation (or the next name); the runtime's `_quarantine` catches the exception and retries next tick. Nothing is
     replaced, because the body differs (the body carries the event id).
   - 1001 INSERTs at `prefix||X#1..#1000` with different bodies: the function returns 0, X stays parked, the cost is
     about 1000 SELECTs per tick. Bounded DoS, nothing lost.
   - Drain and reconcile selects use `NOT LIKE 'poison:%'` and COUNT with the same prefix, unchanged; renamed rows
     (`poison:E#n`) are excluded by the same prefix.
2. In-place edit of 0012 is acceptable: `0012_audit_outbox_functions` is in `UNRELEASED_MIGRATIONS`
   (store/migrate.py:1134); the ledger keeps the old checksum and migrate warns on every run (M6). See Minor 4 for the
   missing runbook hint.
3. `app.build` try/except (app.py, the `except BaseException` block): re-raises with a bare `raise` (original traceback
   kept), `BaseException` so KeyboardInterrupt closes then propagates, the dict keyed by `id` dedupes store/purge_store
   when they are one object, `getattr(None, "_db", None)` is safe for a missing checkpoint_store. Nothing is closed on
   the success path, so no closed-but-used connection. The audit's `_Db` wraps `ck._db`; on failure nothing uses it.
4. CLI warning text matches the code (a runtime role without a checkpoint role leaves SELECT only on
   audit_checkpoints). tests/test_migrate_cli_checkpoint_warning.py asserts the new text and the absence of the old
   "still writes".
5. Mutants: A10 (DELETE of `v_cand` instead of the new row) is killed by
   test_quarantine_of_a_row_that_duplicates_a_quarantined_one_removes_only_the_new_row (it asserts `dup-1` gone and
   `poison:dup-1` present). A11 (`0..0`) is killed by test_quarantine_renames_and_never_deletes (`== [(1,)]` on the
   second park). Both die for the intended reason.

## Major

M1. Overclaim about postgres without a checkpoint role. SECURITY.md ("A deployment migrated without `--checkpoint-role`
(demo, dev, `--no-roles`) writes NO checkpoint at all with postgres ... Only the memory store keeps the inline
checkpoint") and docs/stop-state-runbook.md:331-332 ("A postgres deployment without the role writes NO checkpoint at
all"). Code: with no `checkpoint_db`, `ChainAudit.checkpoint` and the inline path write on `self._db`
(audit/chain.py ~l.277, l.680 `cdb = self._checkpoint_db or self._db`). Whether that INSERT works depends on the
login's grants. It fails only after `migrate --runtime-role` took INSERT away. With `--no-roles`, or a dev login that is
the owner/superuser (the usual demo setup), the runtime keeps INSERT and DOES write checkpoints inline; `--no-roles`
does not touch grants at all. `app.build`'s own warning is correctly conditioned on `has_table_privilege`, the docs are
not. Also (3) of the tamper-evidence conditions is then false in those setups, which the paragraph does not say.
Fix: reword to "a deployment migrated with `--runtime-role` but without `--checkpoint-role` writes no checkpoint
(the runtime login holds SELECT only); one that skipped roles (`--no-roles`, an owner login) still writes them inline on
the runtime login, so (3) does not hold there", in both files.

## Minor

m1. app.py try/except does not cover every failure after a store is opened. `make("store")` for purge_store, the
`missing_methods(store)` ConfigError, and everything after `make("audit")` (llm, detector, channel, Limits, Runtime ...)
are outside the try, so `store`, `purge_store` and the checkpoint connection (held by `audit`) leak on those failures.
The comment and the ticket wording ("on any failure") overclaim. Fix: widen the try to the end of `build` (close only
on exception), or narrow the comment to "the login comparison and make('audit')".

m2. `conn.close()` in the except block is not guarded: a close that raises replaces the original exception (with the
original chained as context only). Fix: `with contextlib.suppress(Exception): conn.close()` per store.

m3. The reconcile report counts wrongly after a duplicate removal. `_quarantine` returns 1 when the function deleted a
duplicate (chain.py ~l.607), and `r.marked` feeds `earlier = COUNT(prefix rows) - r.marked` (l.457-461). A duplicate
removal adds no quarantined row, so `earlier` is understated by 1 each time (floored at 0). A report figure only.
Fix: make the function return 2 (or a second value) for a removed duplicate and count only renames.

m4. TOCTOU in the duplicate branch: the candidate row is read with a plain SELECT, not locked. An operator deleting that
quarantined row (tickets/A-audit-drain.md removal) between the SELECT and the `DELETE ... p_event_id` leaves zero copies
of the body. Narrow window, operator-initiated. Fix: `SELECT ... FOR SHARE` on the candidate. Related untested edges:
the 1000-name cap (`return 0`) and `#`-named ids have no test, so a mutant shrinking `0..1000` survives. Also an id near
the btree entry limit (about 2.7 KB) plus `#1000` could fail on the UPDATE every tick (error caught, retried forever,
nothing lost).

m5. (docs) The runbook does not tell an operator whose DRAFT database already applied the old 0012 that the new function
body does not reach it (migrate warns, the old function keeps refusing a repeat rename and returning 0, so repeats never
converge). Add one line: run `reset_draft` for 0012 (after dropping the two functions) or `accept_changed_draft` once the
functions are replaced by hand.
