# PR73 result review round 3, head ffe896e, reviewer egm:egm-design (read-only; ran nothing)

Verdict: 0 Blocker, 3 Major, 8 Minor. Round-2 security findings fixed in code except one narrow gap (m1). Ticket scope question BL-core-a5-w2-03 still with the lead. Not checked: ticket beyond lines 1-51, lexer/runbook tests, PostgreSQL 17.10, mutant logs are at 0354512.

MAJOR
- M1 ownership refusal is scoped to the whole schema (migrate.py:604-618; test test_migration_postgres.py:1473; CHANGELOG case h): in a shared schema other applications' tables make migrate refuse, and the advice moves their objects into the migration role (opposite of least privilege). Fix: restrict to package-managed objects (GRANTS, schema_migrations, objects the files create); test that a foreign table outside that set does not refuse.
- M2 server-wide pg_auth_members / pg_db_role_setting diff (migrate.py:405-408, 398-402, 752-761; CHANGELOG item 7) refuses falsely when other sessions change roles (shown live in the builder's concurrent first-attempt log). Safe direction (rollback), but a denial-of-service lever and a misleading message. Fix: re-run the guard's own invariant queries after each file; scope member/settings diffs to current_user, session_user and the named roles plus the closure; message says it may be another session.
- M3 evidence at the head not clean (3.13 full suite never clean; silent exit-0 run unexplained; 3.12 dblink environmental; mutants at 0354512). Independent runner aade658247 is on it.

MINOR
- m1 parameter grants held by a NOINHERIT-member role are missed (migrate.py:559-564); test every role the user is a member of with has_parameter_privilege(r.oid,...); real-server test.
- m2b say REPLICATION is not covered.
- m3a CHANGELOG:410 "P3a changes no stored data"; m3b tests/test_migration_numbers_guards.py:148 and tests/migration_numbers_mutants.py:317 "ticket way"; m3c tests/migrate_mutants.py:943 "round 2"; m3d private names already on main in touched files (P1m CHANGELOG sections incl. handover/reviews path, K5/K6/P3b/P4b in migrate.py:95,111, pyproject.toml:30-31, tests/conftest.py:51, tests/test_k2_migrations.py:1).
- m4 pin tests cannot fail alone (test_migration_wiring.py:854,862; stub answers by exact text).
- m5 no killers for ALTER SYSTEM / session_user halves of _PARAMETER_GRANTS_SQL, pg_database_owner exemption, zero-arg aggregate branch (migrate.py:654), owned-sequence exemption.
- m6 trigger allow-list: newly created trigger left D/R refused even if entry names it; CHANGELOG item 8 must say "existing trigger" or honour the entry.
- m7a CHANGELOG item 5 "tests never run as superuser" (the refusal tests do); m7b migrate.py:16-18,832-834 "current user" (both read); m7c migrate.py:515 "md5" (raw text); m7d CHANGELOG item 11 promise outside the file.
- m8 do not grant CREATE with GRANT OPTION (only USAGE needs it): migrate.py:538-541.
