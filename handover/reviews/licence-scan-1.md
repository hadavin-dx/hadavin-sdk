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

## Part 2 (order 69, 2026-11-06): what is inside the psycopg-binary wheel
Read: the file `psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64` wheel from pypi.org, unpacked with Python in isolated mode in a fresh directory. Only this one platform wheel was read. The macOS and Windows wheels bundle other libraries and are NOT read (UNVERIFIED; the notice text below must be re-checked if a client builds on them).

Finding that matters: the wheel ships ONE licence file (`LICENSE.txt`, LGPL-3.0-only, METADATA `License-Expression: LGPL-3.0-only`). It ships NO licence text for the 15 bundled shared libraries in `psycopg_binary.libs/`. So the SPDX values below are from the well-known licence of each upstream project, matched by library name and version string, NOT read from the wheel. Treat each as UNVERIFIED until the upstream licence file for the exact version is read.

| bundled library (file) | upstream project | SPDX (from upstream, UNVERIFIED) | on the allowlist? |
|---|---|---|---|
| libpq 5.18 | PostgreSQL | PostgreSQL | yes (BSD-style; equivalent to MIT/ISC) |
| libssl 3, libcrypto 3 | OpenSSL 3 | Apache-2.0 | yes |
| libgssapi_krb5, libkrb5, libk5crypto, libkrb5support, libcom_err | MIT Kerberos 5 | BSD-style / MIT-style (krb5 notice file) | yes (permissive) |
| libsasl2 | Cyrus SASL | BSD-Attribution-HPND-disclaimer (CMU BSD-style) | yes (permissive, BSD-style) |
| libldap, liblber (2.0.200) | OpenLDAP | OLDAP-2.8 (OpenLDAP Public License) | NOT named on the allowlist; BSD-style in effect. GOES TO THE LEAD |
| libpcre 1.2.0 | PCRE (1) | BSD-3-Clause | yes |
| libselinux | SELinux userspace | Public domain (libselinux) | not named; no restriction. GOES TO THE LEAD with the OpenLDAP row |
| libkeyutils 1.5 | keyutils (string `keyutils-1.5.8` found in the file) | LGPL-2.1-or-later | yes (LGPL, unmodified, separate shared object) |
| libcrypt | libxcrypt | LGPL-2.1-or-later | yes (LGPL, unmodified, separate shared object) |

Result: no GPL, AGPL, SSPL, BUSL, non-commercial or unknown library is bundled by name. Two rows are not literally on the allowlist (OLDAP-2.8 and public-domain libselinux). Both are permissive in effect, but the allowlist is the owner's hard rule, so I send both to the lead (not decided by me). Also: three LGPL pieces ship together (psycopg itself LGPL-3.0, keyutils and libxcrypt LGPL-2.1+). All are used unmodified and sit in separate files, so the replace-by-the-user condition holds. I did not run `ldd` or verify which of the 15 libraries are really loaded.

### Draft THIRD-PARTY-NOTICES entry (text only; no repository file edited; for the P0a / hygiene ticket)
> **psycopg and psycopg-binary (LGPL-3.0)** — Used unmodified, for the PostgreSQL store, through the optional install groups `pg` and `askdata`. Installed as a separate package, so you can replace it with another build of psycopg (for example `pip install psycopg` with your own libpq) without changing our code. The licence text is in the package (`psycopg_binary-<version>.dist-info/licenses/LICENSE.txt`). The binary wheel also carries shared libraries from other projects (PostgreSQL libpq, OpenSSL, MIT Kerberos, Cyrus SASL, OpenLDAP, PCRE, keyutils, libxcrypt, SELinux), each under its own licence; their texts are in those projects. Source for psycopg: its public repository.
Open for the lead: the wording "source offer" if a client ships our package in a product; and whether the entry lists the bundled libraries by name (as above) or only points to the wheel.

### Register line (order 69 item 2)
pglast 8.7 — GPL-3.0-or-later — **test-only, GPL, owner decision 2026-11-01, must never be added to a runtime extra.** Used only as the CI oracle for the ask-your-data SQL check. A test must prove that `src/` never imports it (guard row to be added to the P0a / hygiene ticket; see q160).

## Part 3 (order 70, 2026-11-06): lead answers
- OpenLDAP (OLDAP-2.8) and libselinux (public domain): **accepted by lead 2026-11-06, FYI to owner.** keyutils and libxcrypt (LGPL-2.1-or-later, unmodified, separate shared objects) are inside the allowlist.
- THIRD-PARTY-NOTICES entry, final wording rule: it lists the bundled libraries by name and version string, marked "licence from upstream, not shipped in the wheel". Entry text (no repo file edited yet; goes to the P0a / hygiene ticket):
> **psycopg-binary 3.3.6 (LGPL-3.0-only)** — Used unmodified through the optional install groups `pg` and `askdata`; installed as a separate package, so you can replace it with your own build of psycopg and libpq without changing our code. Licence text: `psycopg_binary-3.3.6.dist-info/licenses/LICENSE.txt` in the package. The Linux wheel (cp313, manylinux x86_64) also carries these shared libraries; **licence from upstream, not shipped in the wheel**: libpq 5.18 (PostgreSQL), libssl 3 and libcrypto 3 (Apache-2.0), MIT Kerberos 5: libgssapi_krb5 2.2, libkrb5 3.3, libk5crypto 3.1, libkrb5support 0.1, libcom_err 2.1 (MIT-style), libsasl2 3.0.0 (Cyrus SASL, BSD-style), libldap and liblber 2.0.200 (OpenLDAP, OLDAP-2.8), libpcre 1.2.0 (BSD-3-Clause), libselinux (public domain), libkeyutils 1.5 / keyutils-1.5.8 (LGPL-2.1-or-later), libcrypt (libxcrypt, LGPL-2.1-or-later). Other platform wheels carry other libraries and are not listed (not read).
- TOOLS.md rows T-135 to T-141 added (presidio, scrubadub, structlog, pydantic, hypothesis, psycopg-binary, pglast decision), all UNVERIFIED = yes.
