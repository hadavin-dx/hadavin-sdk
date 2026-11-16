# PR73 round 4 codebase review - head cb0930f, reviewer egm-codebase-details (read-only, snapshot)

Verdict: 0 Blocker, 2 Major, 8 Minor, 3 Nit. Round-3 code findings fixed in the code; the two Majors are a CHANGELOG sentence that contradicts the code and evidence at the head that is still incomplete.

MAJOR 1: CHANGELOG.md:11 (item 5) says migrate refuses a database "where another role owns a table, view, sequence or function of the migration schema"; code (migrate.py:634-736) and case (h) at CHANGELOG:463 refuse only objects the package manages. Fix wording: "a table, view, sequence or function that this package manages in the migration schema (its own tables, schema_migrations and the functions its files create; objects of other applications in the schema are never listed)".
MAJOR 2: evidence at cb0930f not clean (round-3 M3 open): gates.txt has only ruff output (no bandit, no full suite); "995 passed, 1 skipped" with no Python or PostgreSQL version or sha; the skip unexplained; PG 17 not run; fail-before 19 failed/18 passed, the 18 passes not proven per test. Fix: independent runner on every CI Python with -rs, one run against PostgreSQL 17.x, bandit -ll, the 145-mutant run once at the head, skip explained by name.
Minor 1: migrate.py:678-687 _managed_names does not fold unquoted function names to lower case (docstring promises it) and cannot read a quoted name with a space.
Minor 2: tests/migrate_mutants.py:1394-1397 _BROKEN misses AttributeError, TypeError, KeyError, UnboundLocalError, so a mutant that breaks a line with those still counts as KILLED; add them and pass --tb=short (line 1518).
Minor 3: pyproject.toml:85 marker says "no test-only SET ROLE to a plain role" but the helper logs in as the plain role.
Minor 4: residual private ids in touched files already on main (CHANGELOG headings at 312, 325, 333, 347, 362, 375, 384; tests/test_k5_round10_postgres.py:1; tests/test_p7_store.py:1): rewrite in plain words.
Minor 5: CHANGELOG.md:463 case (h) REASSIGN OWNED advice also moves other applications' objects in this schema.
Minor 6: migration_role.py:43-66 and CHANGELOG:11 say the role is dropped "when the test process ends"; only a normal exit does; _USED_DSNS keeps one entry per scratch schema (many connections at exit).
Minor 7: migrate.py:328-346 _excess_privileges (portal) does not ask REFERENCES or TRIGGER (pre-existing); use table_privs.
Minor 8: MAINTAIN and the test-role helper never ran on PG 17 (disclosed).
Nits: CHANGELOG:14 item 8 trigger wording; CHANGELOG:11 purge role also covered by MAINTAIN; migrate.py:874 wraps the refusal text twice.
Checked fixed: design M1, M2, m1, m2b, m7, m8, codebase m1 (SCRAM, no password in log), m2 (DROP OWNED), m3 (hadavin_test_ prefix), m5 (server_version_num >= 170000), the mutant runner unknown-id and BROKEN handling, scratch-prefix rename across tests.
Not checked: anything run; the ticket; lexer and runbook tests; wiring tests :930 :977; the skipped test; PG 17; cloud-managed pg_parameter_acl defaults.
