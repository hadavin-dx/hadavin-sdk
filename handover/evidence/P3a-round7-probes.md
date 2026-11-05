# P3a round 7 probes (run by the resolve session, throwaway server, PostgreSQL 16.15, psql 16, 2026-11-05)

Server: `/tmp/pgprobe`, port 54329, host 127.0.0.1, superuser, throwaway data directory. Every probe ran with `psql -w -q -t -A` and, unless a line says otherwise, `-X` (no startup file). Nothing was run against the repository suites. Probe files lived in `/tmp/p3a7/` (not kept). Output below is copied from the terminal; blank values are SQL NULL.

Purpose: check the claims of round 7 findings that need a server (order 7: probes allowed only to verify SQL claims).

## P1. ADV-R7-1: the printed command has no `-X`; a startup file undoes `ON_ERROR_STOP` (CONFIRMED)

Startup file `rc` (set through `PSQLRC`): `\set ON_ERROR_STOP off` and `\set ON_ERROR_ROLLBACK on`.
Recipe shape (the same as the ticket's: `SET search_path`, `BEGIN`, one good `CREATE TABLE a`, one failing `INSERT INTO nosuch`, `CREATE TABLE b`, the ledger `INSERT`, `COMMIT`).

| run | command | result |
|---|---|---|
| 1a | `PSQLRC=rc psql -w -q -v ON_ERROR_STOP=1 -f recipe.sql` (what the ticket prints, no `-X`) | error printed for `nosuch`, then ledger rows = 1, `a` and `b` both exist (a half-applied file with a ledger row) |
| 1b | `PSQLRC=rc psql -w -q -X -v ON_ERROR_STOP=1 -f recipe.sql` | error printed, ledger rows = 0, `a` absent (nothing kept) |
| 1c | `PSQLRC=rc psql -w -q -v ON_ERROR_STOP=1 -f recipe2.sql`, where `recipe2.sql` is the recipe with the extra first line `\set ON_ERROR_STOP on` and NO `-X` | error printed, ledger rows = 0, `a` absent (nothing kept) |

Reading: the printed command can be defeated by a person's startup file. Two independent protections work: `-X`, and a first line `\set ON_ERROR_STOP on` inside the recipe itself.

## P2. ADV-R7-2: indirection past the text rules (CONFIRMED)

Inside one transaction, with `application_name` first set to `orig`:
- `SELECT query_to_xml($q$select set_config('application_name','viaxml',true)$q$, true, true, '')` ran, and `current_setting('application_name')` afterwards was `viaxml`.
- A function created with a string body (`AS 'select set_config(''application_name'',''viafn'',true)'`) changed it to `viafn` when called.
- `CREATE ROLE p7r NOLOGIN; SET LOCAL ROLE p7r; SELECT current_user, session_user` gave `p7r|postgres` (so a read-back of `current_user` against `session_user` sees a role change; a `set_config('session_authorization', ...)` would move both, so the read-back compares with the values saved BEFORE the file).

## P3. ADV-R7-5 and COR-R7-2: E-string cases (server side)

- `SELECT E'\' ; COMMIT; --'` returned the single string ` ; COMMIT; --` (valid; a lexer without the backslash rule reads a live `COMMIT` and refuses it, so "not refused" kills that mutant).
- `SELECT E'a\'b'` returned `a'b`.
- Dollar tags are case sensitive and nest as text: `SELECT $a$ $b$ COMMIT; $b$ $a$` and `SELECT $a$ x $A$ COMMIT; $a$` both returned one string; neither holds a live `COMMIT`.

## P4. COR-R7-4: a file that ends in a `--` comment with no newline swallows the ledger INSERT (CONFIRMED)

File: `BEGIN;`, `CREATE TABLE p7.t4 (x int); -- done INSERT INTO p7.schema_ledger VALUES (1);` (the INSERT text sits on the comment line, as the recipe would write it after a file that ends in a comment), `COMMIT;`. Run with `-X -v ON_ERROR_STOP=1`: no error; ledger rows = 0, table `t4` exists.

## P5. ADV-R7-7 and COR-R7-6: `DISABLE TRIGGER` (CONFIRMED)

On a table with a `BEFORE UPDATE` trigger that raises: inside a transaction `ALTER TABLE ... DISABLE TRIGGER aud_append_only; UPDATE ...` succeeded (`updated despite trigger|2`), and after `COMMIT` `pg_trigger.tgenabled` was `D`. (`ENABLE ALWAYS` is `A`; the comparer must read `tgenabled`.)

## P6. ADV-R7-13: `:{?name}` (CONFIRMED on psql 16)

After `\set zz 1`: `select :{?zz} as set_var, :{?nope} as unset_var;` printed `t|f`. So the bare-variable rule must also refuse a colon followed by `{`.

## P7. ADV-R7-3: the two `re.sub` lines in `_scan` (`src/hadavin_sdk/store/migrate.py` lines 131-132, ce70eb5)

`check_grants` itself could not be run here (the `psycopg` package is not installed in this session). I ran only the two `re.sub` lines on the two texts: `SELECT 1; -- x<CR>CREATE TABLE evil_cr (x INT);` leaves `SELECT 1; ` (the CREATE is gone) and `SELECT '--'; CREATE TABLE evil_str (x INT);` leaves `SELECT '` (the CREATE is gone). Both hide a `CREATE TABLE` from the grant scan although the server would run it (P3 case 2 in the round 6 probe file shows the CR rule). The real `check_grants` outcome is therefore INFERRED from reading, not run.

## P8. Round 6 claims that had no saved output (COR-R7-1, ADV-R7-4), re-run now

- `SELECT U&"set\005fconfig"('application_name','q',true)` returned `q`; the lower-case spelling `u&"..."` also returned `q` (COR-R7-7: the rule must be case-insensitive).
- Whitespace in a file run by `psql -f`: carriage return and form feed are whitespace (`SELECT 1<CR>, 2;` and `SELECT 1<FF>, 2;` both printed `1|2`); vertical tab is not (`SELECT 1<VT>, 2;` gave a syntax error).
- `SELECT 1 \g` then `SELECT 2;` under `-f` printed `1` and `2` (a backslash command runs in the middle of a line); a file whose only line is `\! echo SHELL_RAN` printed `SHELL_RAN` (a shell command ran).
- `select :'DBNAME'` printed the database name `postgres`.
- NOT re-run: the `x[1:n]` unset-name case (I used a literal slice `[1:2]`, which proves nothing about a name); the ticket's claim stays "probed in round 6, summary only".
- The round 6 abort probe file `P3a-abort-commit-probe.md` still names `/tmp/r67.sql` without its SQL; the author adds the SQL text from the recipe shape of P1 above or marks the claim summary-only.
