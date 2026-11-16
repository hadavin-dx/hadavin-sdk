# PR73 result review round 3, head ffe896e, reviewer egm:egm-codebase-details (read-only; ran nothing)
Verdict: 0 Blocker, 1 Major, 8 Minor. Read: snapshot, ledger rows, builder evidence; NOT round 1/2 reviews, ticket lines 52+. PostgreSQL 16.15 only evidence.
MAJOR
- M1 private ids still in public files: tests/migration_numbers_mutants.py lines 313,323,331,339,347,355 (+2) mutant-name prefix "o100:" (order 100); tests/test_migration_numbers_guards.py:148 and tests/migration_numbers_mutants.py:317 "..._called_the_ticket_way_..."; CHANGELOG.md:410 "P3a changes no stored data", CHANGELOG.md:390 handover/reviews path and "by the lead"; pyproject.toml:30-31 P4b/P3b (context lines, in touched files); minor wording tests/migrate_mutants.py:943 "round 2", tests/test_k2_migrations.py:308 "review round".
MINOR
- m1 test role password goes into the server log: tests/fixtures/migration_role.py:72-87 runs CREATE ROLE ... PASSWORD on every connect(); after the first it fails with DuplicateObject and the failing statement (with the password) is logged. Fix: look in pg_roles first, create once, set password only at creation.
- m2 role drop at exit is best effort (DROP OWNED BY RESTRICT, current database only); no test shows the role is gone.
- m3 _is_scratch accepts prefix "t_" (migration_role.py:31-34): use "hadavin_test_" only.
- m4 mutant runner tests/migrate_mutants.py:1159-1235: (a) unknown id in the comma list silently dropped (M88,TYPO runs 1, exit 0); (b) any pytest exit 1 counts as a kill, even a NameError from a malformed mutant; no check that the named assertion failed; (c) mutant evidence at 0354512 not re-run at head.
- m5 PostgreSQL 17: has_table_privilege lists lack MAINTAIN (new in 17) in effective_problems/_excess_privileges (not in this diff; version-guarded follow-up, fix here as it is the CI version). New catalog queries read correct on 16 and 17 (unverified by run).
- m6 server-wide pg_auth_members read: false refusal under other sessions' role changes; narrow to the migration user names and roles they touch (same as design review M2).
- m7 trigger code: no bug; prolang not compared; _Saved comment says md5 (migrate.py:515); allow-list match ignores case.
- m8 printed SQL: no injection found; types and domains owned by another role are not listed (relkind r,p,v,m,S,f only).
- m9 PLAIN_MIGRATION_ROLE_SQL grants CREATE WITH GRANT OPTION; only USAGE needs it.
Other: tests/test_migration_wiring.py:156-161 and :1099-1104 call the released stub twice (copy artifact); :930 asserts an absent string is absent, :977 pins a comment word; empty-list trigger-file test is vacuous; tests/conftest.py:97 docstring says SET ROLE but code connects as the plain role.
