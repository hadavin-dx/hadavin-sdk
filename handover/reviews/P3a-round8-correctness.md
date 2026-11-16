# P3a round 8, correctness review (ticket revision 9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not open `reviews/`. Rerun of a lost earlier run. All traces UNVERIFIED unless read from a file.

Verdict: 0 Blocker, 1 Major, 9 Nit. After the fixes the ticket can freeze under order 16.

## MAJOR

**M-1 (line 88, H11 plants 2 and 3).** The plants are described as a "string-bodied function `p3a_f()`" and a plpgsql function running `EXECUTE 'SET LOCAL ROLE ...'`, run through the real `migrate()` so `check_grants` scans them first. `_SAFE_CREATE` (`migrate.py:80-85`) accepts only `CREATE [UNIQUE] INDEX`, `CREATE OR REPLACE FUNCTION|TRIGGER`, `CREATE TRIGGER`, and `CREATE TABLE|VIEW name (` or `AS`. A plain `CREATE FUNCTION` gives "statement the guard does not read" (`migrate.py:133-136`), the run is refused before connecting, and the test (which asserts the changed item name) fails. Fix: write `CREATE OR REPLACE FUNCTION` in plants 2 and 3 and add it to the "no table that needs a GRANTS row" sentence. Plants 1, 4, 5 and H3 have no CREATE.

## NIT

- N-1 (line 107, M69): the killer "unterminated quote must give a problem" is vacuous: `check_grants([one file])` is never `[]` (`migrate.py:159-161` adds "GRANTS names X, which no migration creates"). Assert the lexer's own text (`not closed at line` / file name), as the ticket's rule on line 87 demands. FAIL-BEFORE 8 and 9 are fine.
- N-2 (line 39): `0004_audit_checkpoint_meta.sql` apostrophe is on line 4 only.
- N-3 (line 127): `ci.yml:86-94` is called the perf step; tests step is 84-88, perf 89-94 (line 57 cites it right).
- N-4 (lines 58, 87): `test_k5_fixes1.py:181-186` should be 183-186.
- N-5 (Open point 16, line 155; coupling row line 165): the P4b2 `cli.py: P3a` sentence IS at `P4b2.md:164` and is a false relay (P3a does not edit `cli.py`); change "UNVERIFIED" to "read at P4b2.md:164"; P4b2 should drop P3a from that list.
- N-6 (lines 69, 145, Open point 6): P2a.md lines 29, 234, 353 say P2a-1's `migrate()` sets `lock_timeout` once via `set_config(...,true)`; P4d.md:271 says P4d's migration starts with `SET LOCAL lock_timeout = '10s'`. P3a allows it (rule (d)); only the "who decides" relay is stale.
- N-7 (Open point 17, line 156): P5a.md:55 says a `ConfigError` subclass inherits `config_invalid` and names P3a's `MigrationNumberError`: the worry is moot. P4d.md:271 says P3a's `tests/migration_schemas.py` IS P4d-b's builder while Open point 17 says "not agreed": note for the lead.
- N-8 (lines 10, 134, Open point 13): the "no round cap, two clean rounds" rule is withdrawn for ticket review by order 16; add a freeze note; no round 4.
- N-9 (line 7): "the 17 template fields" has 19 top-level bullets (17 plus "Merge precondition" and "Where memo 4 and my reading differ"); say two are extras.

## Verified (read from files)

`migrate.py` cites (`_LOCK` 69, `_FILE` 71, `_migration_files` 93, `check_ledger` 97-107, `_scan` 123, `check_grants` 150, `migrate` 283, lock 308-314, `gone` 320-326, INSERT 331, `return applied` 360); old `gone` text; `_LOCK` value 3760701656253510835 recomputed; `errors.py:4`; `cli.py:70-83`; ci.yml (postgres 17.10, steps, fetch-depth 104); `pyproject.toml:52`; conftest psql runner; test cites in test_k2_migrations, test_k5_fixes2, test_p2_postgres, test_k5_round10_postgres; CHANGELOG lines; migration-file statement counts (34 total; 15 CREATE TABLE); counts: 9 FAIL-BEFORE = 10 test functions; mutant groups 10+15+6+23+16+11+15+15 = 111 distinct; 79 ids; 96-11+26 = 111; every M1..M86 accounted for. Relays: P4d.md 17 and 271, P2a.md 32/22/115, P4b2.md:164, P4c.md:117. Evidence files exist; headings match claims (PostgreSQL 16.15).

## Not checked

Git shas and branch claims; memo 4 line numbers; all server and psql behaviour; whether existing grant-scan tests stay green on the new lexer; `Path.glob` on a dangling link; ruff on the new psql test; `reviews/` contents; rest of P2a.md and P4d.md.
