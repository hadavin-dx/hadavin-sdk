# Build notes for ticket P3a (package P3a-2), round 12, for the lead

Written by the builder of branch `core/P3a-2-clean` (started from 8382bdd). The ticket file `P3a.md` is not in this
branch, so the notes are here for the lead to copy into the ticket. Nothing under `handover/` was edited.

These notes describe what the code on the branch does. They are the builder's account, not a review.

## Notes that close codebase finding M4 (the ticket did not describe the built result)

**BN-P3a-2-f. Command line.** `hadavin-sdk migrate` takes `--lock-wait-seconds <seconds>` (a whole number from 1 to
2147483; the default is `MIGRATE_LOCK_WAIT_SECONDS`, 600). It is how long the run waits for the migration lock before
it gives up, changes nothing and names who holds the lock.

**BN-P3a-2-g. Every `SET` and `RESET` in a migration file is refused**, with no exception, `SET LOCAL lock_timeout`
and `SET LOCAL statement_timeout` included. `migrate` sets the two time limits itself.

**BN-P3a-2-h. The read-back after each file compares eleven values** with the values saved before the first file:
current user, session user, `session_replication_role`, `search_path`, `standard_conforming_strings`,
`backslash_quote`, `client_encoding`, `lock_timeout`, `statement_timeout`, the transaction clock and the transaction
id. It also compares role memberships, saved settings and every trigger of the schema.

**BN-P3a-2-i. The list of released files** is `src/hadavin_sdk/store/migrations_released.json` (shipped inside the
package), and the list of allowed trigger changes is `src/hadavin_sdk/store/migrations_trigger_changes.json`.

**BN-P3a-2-j. Five role flags.** The migration role, and each of the runtime, portal and purge roles, is refused when
it is a superuser or holds `CREATEROLE`, `CREATEDB`, `BYPASSRLS` or `REPLICATION` (five flags, not four).

## Notes for what round 12 changed (decision D-009)

**BN-P3a-2-k. A named role gets nothing outside the grant map.** The runtime, portal and purge roles get the rights of
the grant map (the list in the code of tables, views and sequences and the rights each role has on each) and `USAGE`
on a schema. Refused now, each of which round 11 accepted: `SELECT` on a table, view or column that is not in the
grant map, in any schema; `USAGE` or `SELECT` on a sequence that is not in the grant map (`USAGE` lets the role take
the next number, which changes the sequence); any right on a function; `CREATE` on any schema; any default right
(`ALTER DEFAULT PRIVILEGES`). Builder's own reading of D-009, to be confirmed by the lead: the refusal of a right on a
FUNCTION for a named role. D-009 says "no right outside the grant map"; a function is never in the grant map, and
this package gives no role a right on a function, so the builder refused it. Round 11 let a named role hold
`EXECUTE`. If a later release needs a named role to call a function, that needs a reviewed list like
`REVIEWED_DEFINER_FUNCTIONS`.

**BN-P3a-2-l. SECURITY DEFINER.** A `SECURITY DEFINER` function in the schema of the run that the migration role, or a
role it belongs to, owns is refused also when no file of this run made or changed it (unless its name is on
`REVIEWED_DEFINER_FUNCTIONS`, which is empty). The RIGHTS of a plain function that no file touched are still not
read. Not looked at: an untouched `SECURITY DEFINER` function in another schema, or one that another role owns.

**BN-P3a-2-m. What "changed" means for a function.** Each of these is compared on its own (no hash, no md5): the
`SECURITY DEFINER` flag, the rights, the owner, the body kept as text (`prosrc`), the body of a function written in
the SQL-standard form (`RETURN ...`; read with `pg_get_function_sqlbody`, which exists from PostgreSQL 14), the
library file (`probin`), the language and the saved settings. Probed on PostgreSQL 16.15: for
`CREATE FUNCTION f() RETURNS int LANGUAGE sql RETURN 1` the server keeps `prosrc` empty and `prosqlbody` set, so the
reviewer's claim was true.

**BN-P3a-2-n. Scope of the before/after comparison.** An object is compared when the migration role, or a role it
belongs to, owns it or gave a right on it, before or after the files. Of an object that another role owns, only the
rights that the migration role or a role it belongs to gave are compared. What another session commits on its own
objects while the run is open does not stop the run. Still refused, and the message says another session may be the
cause: a change by another session to an object that IS in scope (for example an administrator who grants a right on
a table of the migration role while the run is open). The comparison covers one run; nothing is compared between two
runs.

**BN-P3a-2-o. Default rights.** Read for the migration role and every role it belongs to, for one schema or for all.
Refused: a default right for any role (a named role included) and for everyone. Not refused: the right of the role
the default is set for; a right that a role the migration role belongs to gives to the migration role itself; and the
server's own entry for all schemas, "everyone may call a new function" and "everyone may use a new type", which
PostgreSQL 16.15 writes into the list as soon as any default right for functions or types is set for all schemas
(probe: `{=X/r,r=X/r,x=X/r}`). The same right for everyone set for ONE schema is refused.

**BN-P3a-2-p. `pg_database_owner`.** The built-in role that stands for the owner of the database is accepted on a
schema only where it is the owner of that schema (as on `public` from PostgreSQL 15). A right for it on a schema it
does not own is refused like a right for any other role. Round 11 accepted it everywhere.

**BN-P3a-2-q. Owner change in a file.** `ALTER ... OWNER TO` at the start of a statement is refused. The only
statement with the words `owner to` that passes is the rename of a column, attribute or constraint that is called
`owner`, read from the start of the statement (`ALTER TABLE|VIEW|MATERIALIZED VIEW|FOREIGN TABLE|TYPE|DOMAIN <name>
RENAME [COLUMN|ATTRIBUTE|CONSTRAINT] owner TO ...`). A table, type or column called `rename` no longer switches the
rule off. An owner change made by dynamic SQL in a function body is found by the read-back for relations, functions
and schemas only.

**BN-P3a-2-r. One set of ids and of names per catalog.** The ids that "kept their owner" and the names this package
manages are kept apart for relations (`pg_class`), functions (`pg_proc`) and schemas (`pg_namespace`). A function
that is called like a table of the grant map (for example a function `spend()` of another application) is not this
package's.

**BN-P3a-2-s. Messages.** A refusal names each object with its kind and its schema (a view is called a view; a
function carries its argument list), lists at most 20 things and then says how many more there are. The role check
also reads foreign tables of the schema.

**BN-P3a-2-t. Prepared transaction.** When the migration lock is held by a prepared transaction (`PREPARE
TRANSACTION`; it has no session), the message says so, lists the oldest prepared transactions of the database and
names `ROLLBACK PREPARED` and `COMMIT PREPARED`. The real-server test for this only exercises the message on a server
whose `max_prepared_transactions` is above 0 (the PostgreSQL default is 0); on a server with 0 it asserts that the
server refuses `PREPARE TRANSACTION`. The wording is also tested without a server.

## Mutants removed or renamed in `tests/migrate_mutants.py` (so the lead can check nothing was dropped quietly)

- RA3 removed: the three catalogs now share one comparison line, so RA3 and SD5 planted the same line; RA3's killers
  were added to SD5.
- GO7 removed: one grant-option check is left for functions, the line GO4 plants; GO7's killer was added to GO4.
- PO1 removed: its rule (functions the migration role owns are not read) changed; SD6, SD7, SD8 and SD9 hold the new
  rule. The reference to a mutant "PO2", which never existed, is gone from the test docstring.
- PDO1 replaced by PDO2 and RO2 replaced by RO3 and RO5: the rules they held were reversed on purpose (notes k and p).
