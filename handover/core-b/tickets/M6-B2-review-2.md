# M6 + B2 review 2 (hostile, after the fix rounds)

Tests run on my own DB (hadavin_test_rm6): tests/test_migrations_checksum.py 19 passed; tests/test_live_path_reserve_settle.py 32 passed.
No Blocker. 1 Major, 4 Minor.

## Major

### B2-M1. The ambiguous-failure default under-counts the RUN cost (the unsafe direction for `max_run_usd`)
`src/hadavin_sdk/runtime/agent_loop.py:391-415` (`_settle_model_call`). Only `(ValueError, NotFound)` is "definite"; EVERY other
exception is treated as "the settle may have committed" and books nothing. There is no list of connection errors: the default for an
unknown class is "ambiguous, do not book". But several definite, rolled-back failures reach that branch:
`RuntimeError("spend counter row missing")` (HD003, and memory store settle_spend), `ConfigError` (HD004/HD005 from `_money_error`,
postgres.py:467-472), `StaleState`, psycopg `DataError`/serialization errors, a TypeError from a store bug. In each, nothing was
committed, the hold stays at the worst case (day/month over-count: fine), but the call's real cost is in NO run cost, so
`_limits_stop` (`run.cost_usd >= max_run_usd`, line ~316) never sees it. Scenario: counter row missing or a schema fault during
settle on every step: a run makes up to `max_steps` paid calls and the per-run cap never trips. The run does continue
(returns None). The over-count direction is safe for a cap (booking twice only stops a run early); not booking is not.
Fix: make the ambiguous set explicit and small (psycopg.OperationalError, InterfaceError, TimeoutError/OSError, i.e. a lost
connection) and send every other exception down the definite path (add_cost); for the true ambiguous case, end the run
NEEDS_PERSON `limits.limits_unavailable` (the store is down, the next `_limits_stop` read would fail anyway) or add the worst case
to the run cost instead of nothing.

## Minor

### B2-m1. "Never raises" is not true
`agent_loop.py:391-415`: inside the `except (ValueError, NotFound)` the fallback `self._to(run, NEEDS_PERSON, ...)` calls
`store.get_run` and `advance`, and `_note` (audit). If the store is down (the reason `add_cost` just failed) `_to` raises out of
`handle` and leaves the run in WORKING. Fix: drop "Never raises" from the docstring, or wrap that `_to` and fall back to the
run-stuck path of the tick (log and return a run whose state the tick will close).

### B2-m2. Docs overclaim: "concurrent runs cannot overshoot the cap for that call"
README.md:47, SECURITY.md:80, CHANGELOG.md:6. `Limits.settle` never refuses and books the real cost above the worst case
(`_settle` overshoot, audited after commit), and the kill-switch read and the reserve are not one transaction
(docs/stop-state-runbook.md:162). Also nothing says the run cost can lag when a settle fails ambiguously. Fix: "cannot overshoot by
more than the amount a provider reports above the priced worst case (booked and audited as an overshoot)", plus one clause on the
per-run cost after an ambiguous settle failure (or fix B2-M1 and drop it).

### M6-m1. Nothing ties `UNRELEASED_MIGRATIONS` to the manifest, so `--reset-draft` can re-run a released version
`src/hadavin_sdk/store/migrate.py:1124-1137`, `:1067-1074`. `_reset_draft` checks only the hard-coded set and deletes every row
`>= version`; it never looks at the manifest. At the 0012 merge, if the lead adds the four hashes (both copies; the equality test
`test_the_packaged_released_hashes_equal_the_test_fixture` and the `RELEASED_CUTOFF` guard in tests/test_migration_numbers_guards.py:
569-585 do cover that) but forgets to empty the set, `--reset-draft 0008_...` is accepted for a released version and deletes 0008
to 0012 rows (the checksum still matches, so `_check_released` passes). No test asserts `UNRELEASED & manifest == {}`. The only
guard is the hard-coded "exactly 0008..0011" test (test_migrations_checksum.py:30), which fails loudly but is rewritten at the same
moment. After release the intended state is fine: 0012 unreleased resets only >= 0012. Fix: in `_reset_draft` and in
`_verify_applied` refuse (ConfigError) any version, or any later version, that is in `_released_hashes()`; add a test
`UNRELEASED_MIGRATIONS.isdisjoint(_released_hashes())`.

### M6-m2. Doc and CLI text will go stale or is wrong
docs/migration-checksums.md says `hadavin migrate ... --reset-draft` (the command is `hadavin-sdk migrate`; also the cli.py
help text at cli.py:191-199 hard-codes "(0008-0011)", which is wrong after the release step the doc lists, and that doc step list
does not mention it). Exit codes are right: a ConfigError exits 2 through `main`; a re-apply that fails on existing objects is a
psycopg error and exits 3 with the ledger delete rolled back (tested). Fix: write `hadavin-sdk`, and make the help say "an
unreleased migration (see the migrate docs)" or add the file to the release-step checklist.

## Checked and fine
- Ledger: one read per file (hash = what runs); advisory xact lock is taken before `_ensure_ledger`, the ledger read, reset and
  apply, all in one transaction; reset's delete rolls back with a failed re-apply; accept on an unapplied version is a no-op;
  the applied checksum is kept for a changed unreleased file and the warning repeats; NULL checksum on a released file is filled
  only after `_check_released` matched the manifest.
- Packaged manifest equals the fixture today (diff empty) and a test keeps them equal; both hold 0001-0007.
- Double count: on `(ValueError, NotFound)` nothing was committed (store function raises before the claim/rolled back), so the
  direct `add_cost` cannot double count; a settle that committed returns normally. A repeat settle returns `claimed=false` and does
  not add run cost again. Kill-switch at reserve goes to STOPPED `kill_switch`; a pricing or store failure at reserve goes to
  NEEDS_PERSON `limits.limits_unavailable` with no model call (the bare reason code was fixed).
- Provider error after reserve: hold stays at worst case, no run cost booked (cost unknown), matches README/runbook wording.
