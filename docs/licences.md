# Licence notes for dependencies

This file explains four packages that a licence scanner (CodeAnt, 2026-11-12) listed as "needs review". It is a plain-words
note, not legal advice. The licence of this repository itself is in `LICENSE` (proprietary; the `pyproject.toml` field
`license = "LicenseRef-Proprietary"` says the same, and the built wheel carries it as `License-Expression`).

- **pglast (GPL-3.0-or-later).** Used only by tests: it is declared only in the `test` dependency group of `pyproject.toml`
  (`tests/test_migration_numbers_guards.py` and the Ask-your-data demo tests compare our own SQL reader with the PostgreSQL
  scanner). It is not in `dependencies` or in any extra, and no file under `src/` imports it. Check:
  `uv export --no-hashes --all-extras --no-dev --no-group test | grep -c pglast` prints 0. It must stay that way; a runtime
  or client dependency under GPL, AGPL, SSPL or BUSL needs the owner's written yes first.
- **psycopg and psycopg-binary (LGPL-3.0).** Installed unmodified from PyPI with `pip` or `uv`, only through the `pg` and
  `askdata` extras, and imported (never copied into this repository) by `store/postgres.py` and `store/migrate.py`. Because
  the library is installed as a separate package that a client can replace, the LGPL conditions are met by keeping it that way:
  do not vendor, patch or bundle it into a client's build.
- **certifi (MPL-2.0).** Not a direct dependency. It arrives through `requests`, which the `azure`, `gcp` and `anthropic` extras pull in.
  Used unmodified from PyPI as a list of certificate authorities; nothing is copied or changed.
- **python-dateutil (dual licence: Apache-2.0 and BSD).** Not a direct dependency. It arrives through `botocore` (the `aws`
  extra, and `moto` in tests). Used unmodified from PyPI.
