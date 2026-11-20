# Migration checksums

`migrate` records a SHA-256 of every applied migration file in `schema_migrations.checksum` (the column is added by
`migrate` itself, not by a numbered migration). On every run, an applied file whose checksum differs is refused with a
`ConfigError` naming the file, unless it is in `UNRELEASED_MIGRATIONS` (`store/migrate.py`): then the new checksum is
recorded and a warning names the file. An unreleased file is not re-run, so a changed table definition does not reach a
database that holds an earlier draft; drop what it made and run `migrate` again in that case. A ledger row with no
checksum (applied before this existed) takes the file's current checksum on the next run.

## What the lead does at the merge that releases 0008 to 0011

1. Add the four rows to `tests/fixtures/migrations_released.json` (same hash rule as the test: SHA-256 of the file bytes
   with CRLF read as LF):
   `python -c "import hashlib,json,pathlib;d=pathlib.Path('src/hadavin_sdk/store/migrations');m=json.load(open('tests/fixtures/migrations_released.json'));[m.__setitem__(p.stem,hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()) for p in sorted(d.glob('001[01]_*.sql'))+sorted(d.glob('000[89]_*.sql'))];json.dump(dict(sorted(m.items())),open('tests/fixtures/migrations_released.json','w'),indent=2)"`
2. Empty `UNRELEASED_MIGRATIONS` in `store/migrate.py`.
3. In `tests/test_migration_numbers_guards.py` set `RELEASED_CUTOFF = 12`, the manifest length to 11, and delete
   `test_the_manifest_has_no_row_for_the_unreleased_files_yet`; in `tests/test_migrations_checksum.py` replace the
   unreleased tests with the new (empty) set.

Do not add the rows before the release: the files are still being edited.
