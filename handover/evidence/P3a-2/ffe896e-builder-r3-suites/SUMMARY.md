# Suites at head ffe896e (PR branch core/P3a-2), PostgreSQL 16.15 scratch server on the build machine

| Run | Result | File |
|---|---|---|
| Full suite, Python 3.12.3, run alone | 10708 passed, 1 failed, 1 skipped, 28 deselected (exit 1). The one failure is `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`: it connects to the server through the default socket `/var/run/postgresql/.s.PGSQL.5432`, and the scratch server listens on port 56073. Not touched by this change. | full-py312-alone-dblink-env-failure.log |
| That test file with `PGHOST`/`PGPORT` pointing at the scratch server, Python 3.13 | 253 passed | ../0354512-builder-r3/askdata-dblink-with-PGPORT.log |
| Postgres and migration test files together, Python 3.13, run alone, `PGHOST`/`PGPORT` set (test_k5_postgres, test_migration_*, test_k2_migrations, test_p2_postgres, test_k5_fixes2, demo_askdata) | 1757 passed (exit 0) | py313-postgres-and-migration-files-alone.log |
| Full suite, Python 3.13 | NOT clean at this head. A first run (alongside the 3.12 run on the same server) had 10707 passed, the same dblink failure and one error in `test_k5_postgres.py::test_a_whole_tooled_run_on_postgres`: the read-back after a file saw a role change made by the other run at the same moment (`pg_auth_members` is read for the whole server; the code comments call this a false refusal, run again). A later single run printed no output and exit 0 (cause not found). The files that error touched pass alone (line above). | concurrent-first-attempts/ |

Before this head (0354512, same code except the test-role change): full suite 3.12 10708 passed + the same dblink failure; 3.13 10707 passed, dblink failure, and two failures that only happen when two suites share one server (role name shared, parameter grant seen by the other run, "tuple concurrently updated"). The role name is now one per test process (ffe896e), dropped at exit.
Not run: PostgreSQL 17 (the CI version).
