# PR73 round 11: rung table and a failing input per new layer

Rung means the step of the tool ladder (1 reuse what the core has, 2 the client's tool, 3 no-code, 4 MCP, 5 retrieval,
6 newer model features, 7 our own code). All of these are access and redaction checks on a database, so none of the
rungs 2 to 6 applies; the real question for each row is which simpler thing inside our own code was considered.

| New check | Simpler option considered | Why it was rejected | Failing input (what the check refuses) |
|---|---|---|---|
| Read back rights and owner of every relation a file changed (all relkinds r, p, v, m, S, f) by comparing state before and after, keyed by oid | Read only the tables named in the grant map (what round 10 did) | A file can change a table that the map does not name (a `GRANT` in plain text or in dynamic SQL), so nothing read it | `GRANT SELECT ON x TO PUBLIC` on a table that existed before the run (test `..._on_a_table_that_existed_before_the_run_is_refused[table]`) |
| Column rights are part of the relation state (md5 of `relacl` and every `attacl`) | Compare `relacl` only | A column right does not change `relacl` | `GRANT SELECT (a) ON x TO PUBLIC` ([column]); and a second right on a column that already had one (`test_a_second_right_on_a_column_that_already_had_one_is_refused`), which only the text of the rights shows |
| Read the same state for other schemas and for schemas themselves (owner, `nspacl`) | Read the schema of the run only | A function body can change a schema the run does not live in | `GRANT ALL ON SCHEMA other TO PUBLIC`, `ALTER SCHEMA other OWNER TO r` inside dynamic SQL |
| Refuse `WITH GRANT OPTION` on relations, columns, functions and schemas | Trust the named-role check alone | A named role that may pass a right on can give it to anyone later | `GRANT SELECT ON x TO <role> WITH GRANT OPTION` (table, column, schema, function tests) |
| A named role may hold at most SELECT (or USAGE on a sequence) on an object outside the grant map | Refuse every right of a named role outside the map | The runtime role legitimately reads some tables of other applications | `GRANT INSERT ON x TO <role>`, `GRANT UPDATE ON SEQUENCE s TO <role>` |
| Owner of a relation, function or schema read back; refuse an owner handed to another role | Rely on the text rule | `ALTER ... OWNER TO` inside dynamic SQL is invisible to the text rule | `EXECUTE 'ALTER TABLE x OWNER TO r'` for table, sequence, view, function, schema |
| Text rule `ALTER ... OWNER TO` | Leave it to the read-back | An early, plain error is cheaper to read; the read-back stays as the second layer | `ALTER TABLE t OWNER TO r` (also with comments and line breaks between the words) |
| Function state includes a hash of the body and settings (`prosrc`, `proconfig`); no `proowner = me` filter | Compare owner and rights only; keep the owner filter | A file that replaces a body, or a function the role does not own, escaped the read-back | `CREATE OR REPLACE FUNCTION` with a new body; a function owned by another application is left alone unless a file changed it |
| Default rights read for every schema and for every role the migration role belongs to | Read the migration role in the run schema only | `ALTER DEFAULT PRIVILEGES FOR ROLE <member role>` or `IN SCHEMA other` sets rights of later objects | `ALTER DEFAULT PRIVILEGES IN SCHEMA other GRANT SELECT ON TABLES TO PUBLIC`; `... GRANT DELETE ... TO <named role>` |
| Sweep read of `pg_shdepend` inside a savepoint | Let the error end the transaction | A refused read put the caller's transaction in the failed state | a server error inside `_databases_that_still_hold` while the caller is in a transaction |
| Refuse the `REPLICATION` role flag (migration role, roles it belongs to, named roles, re-read after each file) | Leave it out of the list | A role that can replicate can read every change on the server; the other four flags were refused already, so this is the same check with one more flag | a login with `REPLICATION`, or a member of a role that has it |
| Lock wait must be a whole number of seconds from 1 to a maximum | Pass the value to the server | `0`, a bool, a string or a fraction would be taken as no wait or an error far from the cause | `0`, `-1`, `True`, `"5"`, `1.5`, `None`, maximum plus 1 |

Honest notes:
- The `ALTER ... OWNER TO` text rule refuses any statement that also contains the word `rename` (an over-refusal on purpose; the read-back is the real check).
- Objects made by a file cannot serve as the "existed before" objects in tests (the text scan refuses a CREATE that is not in the grant map), so those tests use objects an administrator creates outside the file.
- Nothing here was run on PostgreSQL 17; the logs under /home/user/build/ev-r11/ name what was run.
