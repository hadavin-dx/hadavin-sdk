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
  `hadavin-sdk migrate ... --reset-draft 0011_money_definer` (version of the changed file). It deletes the ledger row of
  that version and every later one, in the migrate transaction, and applies them again. Refused for a released
  version, and for any version in the shipped manifest even if `UNRELEASED_MIGRATIONS` still lists it. By hand: `DELETE FROM schema_migrations WHERE version >= '0011_money_definer';` after dropping the objects.
- The database already matches the file: `--accept-changed-draft 0011_money_definer` records the file's checksum.

**Roles named (the production path: any runtime, purge, release, reset or caps role is given) vs `--no-roles`.** With
roles named, a changed 0010 or 0011 (the money wall) is a `ConfigError` naming the file and saying that the database
holds an older draft of an unreleased migration, with both remedies above; nothing is applied and nothing is granted.
A NULL recorded checksum (a draft applied before checksums existed) is the same refusal: 0010 and 0011 were never
released, so NULL is an unverified draft. The reason: a stale 0011 body keeps running (a draft's 7-argument
`hadavin_reserve_spend` takes the caps from the caller, so the runtime could book past any cap). Without roles
(`--no-roles`, a dev database) and for 0008 and 0009 it stays a warning (a NULL is trusted once). A persistent staging
database with named roles hard-fails after every edit of 0010 or 0011 until it is reset.

**Functions left behind by a draft.** A draft database may hold a `hadavin_*` function whose signature is no longer in
`FUNCTION_GRANTS` or `EXCLUDED_FUNCTIONS` (for example the 7-argument `hadavin_reserve_spend`, still executable by the
runtime). `migrate` refuses and rolls back, naming each such function with its argument types and the statement:
`DROP FUNCTION <schema>.<name>(<types>)`, or run `migrate --reset-draft <version>`. `--reset-draft <version>` itself
drops the unmapped `hadavin_*` functions of the schema that the migrating login owns, before it re-applies the files,
except those whose name an OLDER shipped file creates (they belong to a migration that is not re-applied). Never another
owner's, never other names, never another schema, never `CASCADE`: a dependent object (a trigger, a column default)
is a `ConfigError` naming it; drop or change that object first.

**Recipe for `--reset-draft`.** 0010 and 0011 are idempotent over what a draft made while they are unreleased:
0010 drops and re-creates its three guard triggers (`spend_money_guard`, `spend_month_money_guard`,
`spend_reservations_money_guard`); 0011 uses `CREATE TABLE IF NOT EXISTS` for `hadavin_limits` and `hadavin_caps` (an
existing table with other columns stops the run) and creates the two `*_usd_range` constraints only when missing. So
`--reset-draft 0011_money_definer` (or `0010_money_guard`, which re-applies 0011 too) needs no manual drops and keeps
the caps rows. Before any reset, back the caps up anyway: `CREATE TABLE hadavin_caps_backup AS SELECT * FROM
hadavin_caps;` (as the owner; the table has no grants). Functions are replaced by the re-applied file (CREATE OR
REPLACE); the stale overloads are dropped by the reset as above. After it run `limits check-caps`. Test:
`tests/test_migrations_draft_upgrade_pg.py`.

**`--accept-changed-draft` is the operator's call.** It records the file's checksum and changes nothing else. On a
database whose objects do NOT match the file, the old bodies keep running and migrate no longer warns; only the
unmapped-function refusal above still stops an old overload. Use it only when you have compared the objects.

A NULL checksum on an unreleased file is trusted once (warning) and recorded, except 0010 and 0011 with roles named (refused, above).

## What the lead does at the merge that releases 0008 to 0011

1. Add the four rows to BOTH `src/hadavin_sdk/store/migrations_released.json` and
   `tests/fixtures/migrations_released.json` (SHA-256 of the file bytes with CRLF read as LF), e.g. run for each file:
   `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read().replace(b'\r\n',b'\n')).hexdigest())" src/hadavin_sdk/store/migrations/0008_release_expired_spend.sql`
2. Empty `UNRELEASED_MIGRATIONS` in `store/migrate.py`.
3. In `tests/test_migration_numbers_guards.py` set `RELEASED_CUTOFF = 12`, the manifest length to 11, and delete
   `test_the_manifest_has_no_row_for_the_unreleased_files_yet`; in `tests/test_migrations_checksum.py` replace the
   unreleased tests.

Do not add the rows before the release: the files are still being edited.
