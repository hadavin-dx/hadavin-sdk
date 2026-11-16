# P3a-2 ticket rev 3: author report (plan round 3, the last plan round)

Author: ticket author agent (Opus 5.5), 2026-11-11 16:59-17:17 UTC (22:29-22:47 IST). EGM-GATE v1: I am the ticket author; I did not review my own work; fresh reviewers judge rev 3.

## Still open or unverified (read first)

1. Nothing ran on PostgreSQL 17 or 18. All probes are on 16.15. The first 17.10 run is the CI run of the built branch.
2. The oracle has still not been built. Rev 3 probed the attempts the reviewers doubted (E03 REFERENCES, E19-E21 and TEMPORARY, DML/TRUNCATE/REINDEX per relation kind, foreign tables, schema USAGE). NOT re-probed: TRIGGER on a view, DML on partitioned tables and partitions, `CALL`, large objects, foreign server/wrapper USAGE, tablespace CREATE, parameter SET. The sensitivity control stays the build-time guard.
3. Five owner decisions are open, each with a default written into the ticket: sharing the migration role or schema (one question, two consequences), extension-owned objects such as `pg_stat_statements` (default: refused, no statement printed), sign-off of striking rule O5, the CI route for `max_prepared_transactions`, the CI cost of the matrix. Written to handover/questions-for-lead.md (block "~17:20Z ... P3a-2 ticket rev 3").
4. Rung-table rows for pg_permissions, pgTAP and ldap2pg were NOT researched live. Rev 3 marks them "not evaluated" and rests KEEP-CODE on three stated constraints only (ticket section 8). The build order does not depend on them.
5. Session, mutant-batch and matrix times are still guesses.
6. The mutant re-check list is computed from planned line ranges (106 overlaps). A builder edit outside the planned ranges is caught only by the per-commit rule in 5.5, which the builder must run.
7. The `_COMMIT_REFUSED_STATES` allowlist is backed by runs for 23503, 57014 and 57P01 only; the other classes come from the PostgreSQL SQLSTATE table, not from runs.
8. `pg_stat_statements` being present in the CI image `postgres:17.10` is not checked.
9. I ran no test, lint or mutant of the repository. I ran PostgreSQL/psycopg probes and one script over the mutant lists.
10. A reviewer claim that turned out wrong: design review F1 suggested `SELECT NULL::s.typ` to show type USAGE without TEMPORARY. The probe shows it is allowed WITHOUT USAGE (p3.out B2), so the ticket uses `CREATE TABLE` in a scratch schema instead. Readiness M5's "25 problem kinds" is a miscount: the ticket's table has 21.
11. Process note: the lead's "sync handover working files" commits (26e48081, be7140a2) committed my ticket and evidence files while I was still editing them. HEAD now equals my final working tree for the ticket and questions file. handover/evidence/P3a-2/plan-r3/README.md (written last) is untracked. I made no commit myself.

## What changed (every round-2 finding -> ticket section)

| id | answer | section |
|---|---|---|
| F1 | E03 REFERENCES via a permanent scratch table (TEMP gives 42P16 first); E20 via `CREATE TABLE` in a scratch schema, E21 via `DO ... LANGUAGE plpgsql` (neither needs TEMPORARY); attempts chosen per relation kind from the measured codes; schema-USAGE scaffold inside the savepoint plus its own `DROP TABLE IF EXISTS` attempt; table "rights the oracle cannot see" | 7.2, facts 41-45 |
| F2 | test -> commit table; tests moved to the commit that makes them true | 9.3 |
| F3 | commit 3 split into 3a/3b/3c (each green); side-branch squash rule | 9.3, 9.4 |
| F4 | rows "not evaluated"; KEEP-CODE on constraints (1)-(3) | 8 |
| F5 | exit 2 only for an SQLSTATE allowlist + open + IDLE; terminate = 57P01, closed, UNKNOWN, not committed (probed) | 4.1 step 7, fact 46 |
| F6 | "why retired" table; refusals dropped on purpose need sign-off | 5.4 |
| F7 | limits first (measured: both orders pass 100/100); `transaction_timeout` not neutralised, claim narrowed | 3.1, 9.5, fact 47 |
| F8 | 6.4 moved to split ticket C; count 313 | 6.4, 10.2 |
| F9 | `pg_database_owner` by hand (REVOKE only warns, probed); grant option per grantor with `SET ROLE` (probed) | 3.1a, 4.2, facts 48-49 |
| F10 | cluster-wide leftover guard at session start and end | 7.2 |
| F11 | "NOT THIS PACKAGE'S OBJECT" lines; separate second statement block | 4.2 |
| F12 | probed `pg_stat_statements` (2 views open to everyone; extension update re-grants); default refuse, no statement; owner question | 3.3 E1, 10.3 item 13, fact 50 |
| Nit / wording | glossary | top |
| M1 | test -> commit table; MIGRATION_TEST_FILES and `problems_with_the_list()` commits named | 9.3 |
| M2 | "How to run here" (initdb/start as postgres user, DSN form, `uv run --offline`, heavy.sh, bounds); `DSN=...` replaced | 9.0, 9.1 |
| M3 | 3a/3b/3c; squash rule; B2 after C1; "may run at the same time" defined | 9.3, 9.4 |
| M4 | heavy.sh form, timeout inside the slot, bounds | 7.10, 9.0 |
| M5 | `Rows`, `_read`, `_judge`, `statements_for` signatures; `Problem` fields and `order`; `line()` for all 21 kinds; S5 for a group reached by two named roles; exit-2 cap; `KNOWN_ACL_COLUMNS` format; `RUN_SCHEMA` resolved in `migrate` | 3.1, 3.1a, 3.3, 3.6, 4.2 |
| M6 | attempt per kind; C10 cells decided; carriers as functions of a `make` text; the three exclusion tables filled; 12 numbered controls | 7.2, 7.4 |
| M7 | 106 overlapping mutants; 30 that were in no rev 2 list are now listed per commit; CHANGELOG ids re-checked at commit 6; prefix edit of kept queries dropped; `BATCH_2_IDS` | 5.5, 3.1 |
| M8 | Q0 and the version read ran (14 rows, 160015); V2 reads version and database owner; qualification rule defined for relations in the new module only | 3.1, 3.2, 3.5, fact 48 |
| m1-m14, n1 | answered one by one in the ticket's "Changes since rev 2" table | top |

## Commands and exit codes

| command | exit |
|---|---|
| `runuser -u postgres -- initdb -D /home/user/build/pg-rev3 -E UTF8 --locale=C.UTF-8 -U postgres` | 0 |
| `pg_ctl ... -l /home/user/build/pg-rev3.log ... start` (log in a root-owned folder) | 1 (Permission denied for the log; my mistake) |
| `pg_ctl -D ... -l $D/server.log -o "-p 56417 -k <sock> -c listen_addresses='' -c max_prepared_transactions=5" -w start` | 0 (16.15, mpt 5) |
| `.venv/bin/python -I scripts/p3.py <sock> 56417 scripts > p3.out` | 0 |
| `scripts/p3b.py` first run | 1 (setup error: a role lacked USAGE on the schema) |
| `scripts/p3b.py` second run (notices captured) | 0 |
| `scripts/p3c.py` first run | 1 (my probe revoked the owner's own CONNECT; wrong probe) |
| `scripts/p3c.py` second run | 0 |
| `scripts/affected_mutants.py` (3 runs failed while finding a loadable tree) | 1, 1, 1 |
| `scripts/affected_mutants.py <git archive 4d328e3d>` | 0 |
| `uv run --offline --all-extras --group test python -c "import psycopg, pytest"` | 0 (3.3.6, 9.1.1) |
| `uvx --offline bandit --version` | 0 (the first try, `uv run ... bandit --version`, exited 2: bandit is not in the test group) |
| `git show 4d328e3d:tools/heavy_slot.py` | 128 (the file does not exist) |
| `pg_ctl -D /home/user/build/pg-rev3 -m fast stop` | 0; afterwards 0 processes match pg-rev3 |

## Files

- handover/tickets/P3a-2-r13-verify-final-state.md (rev 3, 1376 lines)
- handover/evidence/P3a-2/plan-r3/: README.md, p3.out, p3b.out, p3c.out, affected_mutants.out, affected_vs_rev2_lists.out, scripts/ (queries.py, p3.py, p3b.py, p3c.py, affected_mutants.py)
- handover/questions-for-lead.md (new block at the end)
- handover/reviews/P3a-2/author-rev3-report.md (this file)
- checkpoint: /home/user/build/A-P3a2-rev3-checkpoint.md

Processes: my own PostgreSQL cluster (port 56417) is stopped. No other process, shell or agent started by me is running. Bible R-numbers: the studio bible is not in this container; the rules applied are from .claude/rules (rule 20 CODE LAST = R448 for section 8; fix-dont-defer; least privilege: this ticket creates no identity). Token use: not measured by me.
