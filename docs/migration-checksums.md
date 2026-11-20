# Migration checksums

`migrate` records a SHA-256 of every applied migration file in `schema_migrations.checksum` (the column is added by
`migrate` itself, only when missing, not by a numbered migration; a login that cannot add it gets a ConfigError saying
to run migrate once as the ledger owner). The hash is of the bytes `migrate` runs (read once), Windows line endings
read as Unix ones.

## Released files (0001 to 0007)

The released hashes ship in the package: `src/hadavin_sdk/store/migrations_released.json`.
`tests/fixtures/migrations_released.json` is a copy and a test keeps the two equal. On every run, each file named
there must still hash to it, on a fresh install, on a NULL ledger checksum (applied before checksums existed), and
against the recorded checksum. A mismatch is a `ConfigError` naming the file. There is no override: put the change in
a new numbered migration. (Hand-editing the ledger does not help either: the shipped hash is checked too.)

## Unreleased files (`UNRELEASED_MIGRATIONS`: 0008 to 0011)

A file not in the manifest may still change. A DB that applied an earlier draft keeps that draft: **nothing of a
changed file reaches it** (the file is not run again; its tables, functions and constraints stay as the old draft made
them). The ledger keeps the checksum of what was applied, so `migrate` warns, naming the file, on every run until the
operator acts. Two ways:

- The database must follow the new file: drop everything that file and every later unreleased file made, then run
  `hadavin migrate ... --reset-draft 0011_money_definer` (version of the changed file). It deletes the ledger row of
  that version and every later one, in the migrate transaction, and applies them again. Refused for a released
  version. By hand: `DELETE FROM schema_migrations WHERE version >= '0011_money_definer';` after dropping the objects.
- The database already matches the file: `--accept-changed-draft 0011_money_definer` records the file's checksum.

A NULL checksum on an unreleased file is trusted once (warning) and recorded.

## What the lead does at the merge that releases 0008 to 0012

1. Add the five rows to BOTH `src/hadavin_sdk/store/migrations_released.json` and
   `tests/fixtures/migrations_released.json` (SHA-256 of the file bytes with CRLF read as LF), e.g. run for each file:
   `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read().replace(b'\r\n',b'\n')).hexdigest())" src/hadavin_sdk/store/migrations/0008_release_expired_spend.sql`
2. Empty `UNRELEASED_MIGRATIONS` in `store/migrate.py`.
3. In `tests/test_migration_numbers_guards.py` set `RELEASED_CUTOFF = 13`, the manifest length to 12, and delete
   `test_the_manifest_has_no_row_for_the_unreleased_files_yet`; in `tests/test_migrations_checksum.py` replace the
   unreleased tests.

Do not add the rows before the release: the files are still being edited.
