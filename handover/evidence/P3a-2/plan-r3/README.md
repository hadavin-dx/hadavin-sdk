# P3a-2 ticket rev 3: author probes (2026-11-11, 16:59-17:15 UTC, 22:29-22:45 IST)

Who ran them: the rev 3 ticket author (not an evidence runner). Raw outputs; no judgement in the files.
Server: own throwaway PostgreSQL 16.15 cluster (initdb -E UTF8 --locale=C.UTF-8, port 56417, unix socket only,
max_prepared_transactions=5), made-up roles r3_* only, stopped at the end. psycopg 3.3.6, Python 3.13 (repo .venv).

| file | what | ticket fact |
|---|---|---|
| scripts/queries.py | Q1-Q4, STEP4 copied from plan-r2 evidence + Q0 and VERSION exactly as ticket rev 2 prints them | 48 |
| scripts/p3.py -> p3.out | A REFERENCES/temp, B TEMPORARY/type/language, C DML per relkind, D schema USAGE, E psycopg isolation on autocommit, F COMMIT terminate/cancel, G Q0+version, H empty arrays + two-entry family | 41-43, 45, 46, 48 |
| scripts/p3b.py -> p3b.out | I pg_stat_statements + ALTER EXTENSION UPDATE re-grant, J file_fdw DML, K schema USAGE attempt, L pg_database_owner REVOKE, M grant option from two grantors, N limits order | 44, 45, 47-50 |
| scripts/p3c.py -> p3c.out | database owner when everyone's database rights are revoked; V2 read | 48 |
| scripts/affected_mutants.py -> affected_mutants.out | mutants of the 4d328e3d tree (git archive) overlapping rev 3's planned edit ranges | 50 |
| affected_vs_rev2_lists.out | the overlap compared with rev 2's lists (the id "by" is a regex artefact, not a mutant) | 50 |

Commands (exit codes): p3.py rc=0; p3b.py first run rc=1 (setup error: r3_boss lacked USAGE on schema app; notices
not captured), fixed and re-run rc=0 (p3b.out is the second run); p3c.py first run rc=1 (revoking the owner's own
CONNECT made the database unreachable for it; the probe was wrong, not the server), fixed to revoke only PUBLIC, rc=0;
affected_mutants.py: three failed runs while finding a loadable tree (module registration, missing tools/, missing
hadavin_sdk.testing), then rc=0 against `git archive 4d328e3d`.
