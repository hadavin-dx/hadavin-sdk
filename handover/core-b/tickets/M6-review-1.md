# M6 review 1 (hostile reviewer)

Scope: store/migrate.py ledger region (1059-1125, 1207-1226), tests/test_migrations_checksum.py, the 10b additions in
tests/test_migration_numbers_guards.py, docs/migration-checksums.md. Ran tests/test_migrations_checksum.py plus
tests/test_migrations_0009_0010_round2.py: 26 passed.

## Failing round2 test
`test_upgrade_from_0008_with_a_planted_ts_succeeds_and_new_plants_are_refused` PASSED in my run (both files together).
Not reproducible, and M6 does not touch check_grants (it only adds checksum code after `check_grants(files)` runs on the
shipped file set, which is unchanged). Not caused by M6 as far as I can show; if the builder saw it fail, suspect a
leftover DB/schema from an earlier run or test ordering, and re-run it alone on a fresh DB before attributing it.

## Blocker
none.

## Major
1. migrate.py:1109-1113 (and docs line 5-6) - the unreleased warning is false. It says "function bodies are re-applied";
   they are not. migrate's loop (1216) does `if path.stem in done: continue`, so an applied 0008-0011 file is never run
   again. Only `_pin_search_path`/grants are re-done. Scenario: a draft DB applied 0011 earlier; 0011's function body (or
   table) is edited; migrate warns, records the new checksum, and the DB keeps the OLD function. Fix: delete the
   "function bodies are re-applied" claim in the warning, the docstring (1090) and the doc; say plainly that nothing of
   the changed file reaches this database.
2. migrate.py:1124 - the warning fires once, then the checksum is overwritten, so every later run is silent while the DB
   has diverged from the file for good. A stale draft DB is then indistinguishable from a correct one. Fix: for an
   unreleased changed file keep the OLD checksum (do not UPDATE) so the warning repeats every run until the operator
   resets it; or add a `drifted` marker. Alternatively refuse unless an explicit flag (`--accept-unreleased-drift`) is passed.
3. migrate.py:1111-1113 and docs:6 - the operator instruction "drop what it made and run migrate again" does not work:
   the ledger row for that version still exists, so migrate skips the file and recreates nothing. Real recipe:
   drop the objects AND `DELETE FROM schema_migrations WHERE version = '0011_money_definer'` (0008-0011 chain: later files
   depend on earlier ones, so delete the rows from the changed file onward). State that in the message and doc, with the
   exact SQL; or provide `migrate --reset-unreleased <version>` that does it in the locked transaction.
4. migrate.py:1103-1107 - trust on first use hides a changed RELEASED file. The runtime does not consult
   tests/fixtures/migrations_released.json (it is a test fixture, not shipped). A DB whose ledger rows have NULL checksum
   (every DB from before M6, i.e. every released install) accepts whatever file is on disk for 0001-0007 and records it;
   same for any row an attacker/operator NULLs (`UPDATE schema_migrations SET checksum = NULL` then edit the file: only a
   warning). Fix: ship the released hashes in the package (e.g. `store/migrations_released.json` read by migrate) and, for
   a NULL-checksum row of a released file, compare to that hash and refuse on mismatch; TOFU only for UNRELEASED files.
   The same shipped manifest also closes the "fresh DB, edited released file" path (a fresh run records the edited
   file's hash and nothing ever compares it to the manifest at runtime).

## Minor
5. migrate.py:1085 - `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` runs on EVERY migrate. In Postgres the owner check and
   an ACCESS EXCLUSIVE lock happen even when the column exists, so (a) a migrate login that is not the ledger owner now
   fails with "must be owner of table schema_migrations" where it worked before; (b) the lock blocks any concurrent
   reader of the ledger (it is inside the advisory-lock transaction, so only other readers, but still). Fix: first
   `SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='schema_migrations' AND column_name='checksum'`
   and ALTER only when absent; give a clear ConfigError naming the needed owner when ALTER is denied. No test covers a
   limited login.
6. migrate.py:1074-1076 - checksum maps only CRLF to LF, but the SQL actually executed is `read_text` (universal
   newlines: lone CR also becomes LF; the module docstring of migration_numbers.read_files says so). A file with a
   lone CR hashes differently from its LF twin yet runs identically. Matches migrations_released.json's rule (CRLF only),
   so consistent with the manifest; only flag: document it, or normalise both the same way. CRLF itself is handled
   correctly and tested (test_a_crlf_copy...).
7. migrate.py:1223 - `_checksum(path)` re-reads the file after `read_text` executed it; a file changed between the two
   reads records a hash of code that did not run. Fix: read bytes once, hash them, decode and execute the same bytes.
8. No escape hatch is documented for a legitimately fixed released file. Refusal text says "put the change in a new
   numbered migration", which is the correct and safe policy; just add to the docs that the only override is hand-editing
   the ledger row (and that doing so after fix 4 is also refused for released files, by design).
9. Tests missing: no concurrent-run test (two migrate() in threads; advisory lock is taken before `_ensure_ledger`, so I
   read it as correct), no NULL-checksum-on-a-released-file test, no limited-login test (item 5), no test that the
   warning repeats (item 2). Doc step 3 deletes `test_the_manifest_has_no_row_for_the_unreleased_files_yet` and
   resets RELEASED_CUTOFF by hand: error-prone, but it is a documented lead checklist.

## Checked and fine
- Advisory lock (pg_advisory_xact_lock, _LOCK = same key as migration_numbers.MIGRATE_LOCK) taken before
  `_ensure_ledger`, `done`, `_verify_applied` and applying, all in one transaction: two runs serialise; the second sees
  the first's rows and checksums.
- Fresh DB records every file's checksum in the same insert as the apply.
- CRLF copy of a released file is not a change (tested).
- Ledger without the column gets it and is filled (tested).
