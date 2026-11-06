# Licence scan of what the core ships (lead order 67 item 2, R450). Findings only; no checker built.

Date: 2026-11-06. Method: `importlib.metadata` over the Python 3.13 test environment of the core (100 installed distributions; extras and groups installed), compared with the 101 package names in `uv.lock`; the 4 names not installed there were read from the PyPI JSON for the pinned versions. Fields read: License-Expression, License, License classifiers. UNVERIFIED: this reads what each package DECLARES; I did not open the licence files, and I did not scan the native libraries bundled inside wheels (the binary wheel of psycopg bundles libpq and other C libraries, whose licences are not in the Python metadata). Not legal advice (R450 f).

## Not in the permissive set (MIT, BSD, Apache-2.0, ISC, PSF, MPL-2.0)
| package | version | declared licence | where it enters (pyproject) | shipped to a client? | note |
|---|---|---|---|---|---|
| pglast | 8.7 | GPL-3.0-or-later | dependency group `test` | no (test only) | GPL is not allowed without the owner's written yes (R450 d). It is already in the test group and `uv.lock`. T-123 says a test-only use is the lead's decision; the P3a ticket (BN-20) says "pglast stays out". Decide: remove it from the group, or get the owner's yes for test-only use. Nothing in `src` imports it; `tests/demo_askdata/oracle.py`, `test_validate_oracle.py` and `test_corpus_on_server.py` do (so removing it means changing those tests, which are a differential oracle for the Ask-your-data demo). |
| psycopg | 3.3.6 | LGPL-3.0-only | extras `pg` and `askdata`; imported by src/hadavin_sdk/store/postgres.py, migrate.py, protocol.py, runtime/tick.py | yes, for any client build that installs the `pg` extra | LGPL is not on the allowed list. It is a separate library used unmodified (dynamic use), which LGPL allows, but the R450 rule says owner's written yes, and the replacement/relink and notice duties must be met. NEEDS OWNER (via lead). |
| psycopg-binary | 3.3.6 | LGPL-3.0-only | same extras (via `psycopg[binary]`) | yes, same | The wheel also bundles C libraries (libpq, OpenSSL and others) with their own licences: UNVERIFIED, not read. |
| pytest-postgresql | 10.0.0 | LGPL-3.0-or-later (T-129) | NOT in pyproject; read in TOOLS.md only | no | Rejected for P4d already (T-129); listed so it is not adopted by accident. |

## Declared with a combined or odd string (all permissive on reading)
cryptography 50.0.2 (Apache-2.0 OR BSD-3-Clause); packaging 26.3 (Apache-2.0 OR BSD-2-Clause); sniffio 1.3.1 (MIT OR Apache-2.0); python-dateutil 2.9.0.post0 ("Dual License": BSD and Apache classifiers); isodate 0.7.2 (BSD; the License field holds the copyright text); protobuf 7.36.2 ("3-Clause BSD License"); certifi 2026.10.19 (MPL-2.0, allowed); defusedxml 0.7.1 (PSFL, allowed); python-dotenv 1.2.4 (BSD-3-Clause). Read from PyPI for the 4 packages not installed here: boolean.py 5.0 (BSD-2-Clause), tzdata 2026.6 (Apache-2.0), httpx2-jsfetch 1.0 (BSD-3-Clause), colorama 0.4.6 (BSD classifier). Packages with NO licence data at all: none found.

## Our own package
hadavin-sdk 0.1.0 is `LicenseRef-Proprietary` (the repo LICENSE file: all rights reserved). Fine for our code; it is the reason a GPL runtime dependency is excluded.

## Base install
The four base dependencies (markdown-it-py, pydantic, pydantic-settings, pyyaml) are MIT. Everything in the list above enters only through optional extras or the test group.

## Findings for the lead (one decision each)
1. psycopg and psycopg-binary (LGPL-3.0): the Postgres store, migrations and tick all import it. Needs the owner's written yes, or a replacement driver (asyncpg is Apache-2.0; pg8000 is BSD-3-Clause; both UNVERIFIED by me and a store rewrite is large: do not start without the owner's decision). My recommendation: ask the owner for a yes for unmodified dynamic use, with the notice shipped, because the alternative is a rewrite of the store layer.
2. pglast (GPL-3.0) in the test group: my recommendation is to remove it, because P3a decided against it (BN-19/BN-20) and the oracle use was only for a one-off differential in TOOLS.md T-125. Removing it changes `pyproject.toml` and `uv.lock` (a PR, not mine to merge).
3. Third-party notices: the core's THIRD-PARTY-NOTICES coverage for the shipped extras was not checked in this scan.
