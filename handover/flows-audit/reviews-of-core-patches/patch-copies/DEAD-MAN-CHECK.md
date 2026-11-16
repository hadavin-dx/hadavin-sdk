# External dead-man check on `tick_state.last_ok_at` (note only: no core code)

**STATUS OF THE PATCH THIS NOTE DEPENDS ON (read first).** `../REVIEW.md:5` says: "A-01 is DEFERRED, the C-01 extras (the token ceiling) are CUT, the G5 wording patch is KEPT (text only)",
and `REVIEW.md` item 3 of its list (line 64) says C-01 is "DO NOT APPLY NOW". These are the lead's defaults of 2026-11-16; the studio head may veto them. So today
`A-01.patch` is NOT applied, and **the query below must be used in its four-name form** (delete the `('audit_reconcile')` entry; see "Which names to check"). What follows is
the ready copy for when the studio head decides to bring A-01 back. Words (tick, step, outbox, audit kind, reconcile, studio head, lead): see the box in `README.md` of this folder.
All line cites are at commit `b4cce5b`, unless marked "head" (`f05790e42`).

RUNG: existing code. The tick already writes one `tick_state` row per step with `last_run_at`, `last_ok_at` and `last_error` (`runtime/tick.py:319`, `store.save_tick_state`;
table in `store/migrations/0003_approvals_tick.sql:30-35`, both at `b4cce5b`). Nothing new is built in core. The check is a query run by something OUTSIDE the tick process.

STATUS OF THE TESTS: the query and rows 1, 4, 5 and 6 of the identity table below were run ONCE on 2026-11-16 on a throwaway Postgres 16.15 with only the `tick_state` table (taken from
the migration file) and made-up rows: "seen once on a throwaway Postgres, not the real store". Raw commands and output: `../fix-patchcopies1.md`. UNVERIFIED (the second and third
passes were static: no database was started): rows 2, 3, 7, 8 and 9 of the table (the password step, the `REVOKE ... FROM PUBLIC` lines, `default_transaction_read_only`,
`CONNECTION LIMIT`, `statement_timeout`), the real store, a real scheduler, an alert channel. **Needs the lead to ask the studio head for a test database with the real migrations
applied; next step there: run the "Negative test" section.**

## Decisions and who does what (this note's part; the full list of decisions is the table in `README.md`)
| # | Decision or task | Who | Blocks a merge? |
|---|---|---|---|
| D1 | Bring A-01 back (without it the step name `audit_reconcile` does not exist) | studio head | no merge of this note; yes for A-01 |
| D2 | Age limit in seconds (`:limit_s`), proposal `180` | studio head | no |
| D3 | Name the human database owner who creates the login (table below) | studio head | no |
| D4 | A second alert channel that is not the one the tick or the app uses, and who pays for it (`system-map` Decision B, a studio note) | studio head | no |
| T1 | Save the query as `dead-man-check.sql` on the machine of the scheduler | whoever owns the scheduler (named by the studio head; for a client build, the client's operations person) | no |
| T2 | Schedule the command below and wire its alert | the same scheduler owner | no |
| T3 | Apply `A-01.patch` (only if D1 is yes) | a builder opens the pull request; the lead merges | yes for A-01 |

## Which names to check (and why A-01 matters)
The step `audit_reconcile` exists only after `A-01.patch` is applied (see `README.md`). Without it the query reports `audit_reconcile` as MISSING on every run and always alarms.
So: while A-01 is deferred, delete the `('audit_reconcile')` entry from the `VALUES` list (four names: `sweep`, `reconcile`, `stuck`, `checkpoint`). The list in the query is typed
by hand: if a step is later added to `STEPS` in `runtime/tick.py` (`:249` at `b4cce5b`), add its name here too, or it is not watched. Words: here "reconcile" is the tick step of that
name; the audit outbox drain that A-01 adds is the separate step `audit_reconcile`.

## What it checks
A tick that has stopped (scheduler dead, container gone, store unreachable) writes nothing, so it cannot report its own silence. The check asks the store whether each step has
succeeded recently. Steps that run every tick: `sweep`, `reconcile`, `stuck`, `checkpoint`, and `audit_reconcile` (after A-01). Steps with their own interval (`purge_evidence`,
`reprobe_sources`) are left out; to add one, use its interval plus a margin as its own age limit.

## The query, in a runnable form
Save it as `dead-man-check.sql` on the machine that runs the scheduler (T1), in a folder only the scheduler's user can write. Placeholder rule: `:limit_s` is a `psql` variable, set on the command line
with `-v limit_s=<seconds>`; it must be a plain number (no quotes). Without it `psql` stops with a syntax error and exit code 3, which counts as "cannot check" (rule 4 below). An
unreachable store gives exit code 2. Suggested value (D2): 3 times the SLOWEST tick period (a tick runs every 30 to 60 seconds), so `180`; if the scheduler runs the tick every 30 seconds
only, `90` is enough. The query assumes the table is the unqualified `tick_state` in schema `public` (as the migration creates it); with another schema, qualify it.
Clock note: `now()` is the database server's clock and `last_ok_at` is written with the clock of the machine that ran the tick; keep both on network time, or a skew of more than the
margin gives false alarms or hides a stop.

```sql
-- One row per tick step that is MISSING from tick_state, never succeeded, or has not succeeded within the age limit.
-- An empty result means healthy.
SELECT w.step,
       t.last_ok_at,
       t.last_run_at,
       CASE
           WHEN t.step IS NULL THEN 'MISSING (no row: never ran)'
           WHEN t.last_ok_at IS NULL THEN 'NEVER SUCCEEDED'
           ELSE 'STALE (last success older than the limit)'
       END AS problem
FROM (VALUES ('sweep'), ('reconcile'), ('stuck'), ('checkpoint'), ('audit_reconcile')) AS w(step)
LEFT JOIN tick_state t ON t.step = w.step
WHERE t.step IS NULL
   OR t.last_ok_at IS NULL
   OR t.last_ok_at < now() - make_interval(secs => :limit_s)
ORDER BY w.step;
```
Run (T2): `psql -h <host> -U deadman_reader -d <database> -v ON_ERROR_STOP=1 -v limit_s=180 -At -f dead-man-check.sql`
- `<host>` and `<database>`: the same host and database name as the store setting of the deployment's config; the database owner (D3) hands them over.
- Password: never on the command line (a process list shows it). The scheduler reads the secret `deadman_reader_password` through the secrets kind (a named lookup) at the start of the job and passes it
  to `psql` for that one process only, either as the environment variable `PGPASSWORD` set on that single command, or through a password file (`PGPASSFILE`, permission 600, written by the
  scheduler at job start and removed at job end). The `psql` manual calls the password file the safer form. If the client's database supports short-lived tokens or client certificates, use those instead.
- Alert when the output has any line, OR when `psql` exits non-zero. Exit codes of `psql` (its manual): 2 = it could not connect (store unreachable or login refused); 3 = the script failed
  (with `ON_ERROR_STOP`), for example a missing `-v limit_s` or `permission denied`; 1 = another fatal error of `psql` itself.
- The scheduler and the alert are not part of core and no `alert` kind exists in `src` (at `b4cce5b`); whoever owns the scheduler (T2) wires the alert (D4).
The query reads only `step`, `last_ok_at` and `last_run_at`. It does not read `last_error`, so error text can never reach the alert channel.

Example of an unhealthy result (made-up data: `sweep` never succeeded, `stuck` last succeeded 10 minutes ago, `audit_reconcile` has no row):
```
audit_reconcile|||MISSING (no row: never ran)
stuck|2026-11-16 14:28:52+00|2026-11-16 14:38:52+00|STALE (last success older than the limit)
sweep||2026-11-16 14:38:52+00|NEVER SUCCEEDED
```
Healthy: no output, exit code 0. (All of these were seen on the throwaway database; timestamps shortened here.)

## The read-only identity (PROPOSAL: the studio head decides; `REVIEW.md` D-3 (2) and the identity table row `dead-man reader` under X-6.6)
Name: `deadman_reader` (a proposed name). **Who runs these statements: a named human, the database owner of the client's or the studio's database (D3), signed in with a SEPARATE
database login that is not the login the app, the tick or any agent uses.** The database owner here means the login that owns `tick_state`, normally the migrations login
(`store/migrate.py`): a role can only grant rights on a table it owns or holds the grant option for, and the runtime login cannot. No agent session creates or holds this role's owner login
(one identity per function, the least-privilege rule). The tick, the agent and this check never create the role. Each statement and its reason:

| # | Statement (run once, in this order, by the database owner) | Reason | Rollback |
|---|---|---|---|
| 1 | `CREATE ROLE deadman_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;` | its own identity; no password text in this file or in any command line | `DROP ROLE deadman_reader;` (after the rows below are revoked) |
| 2 | Password step: the human generates the secret through the secrets kind (a named lookup, `deadman_reader_password`; the value is never typed into a file, a chat or a shell history), then in `psql` runs `\password deadman_reader` and pastes it at the hidden prompt, and stores the same secret for the scheduler (T2) through the secrets kind. | the role cannot log in without a credential; this keeps it out of the repository and the logs | `ALTER ROLE deadman_reader PASSWORD NULL;` |
| 3 | `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` and `REVOKE TEMPORARY ON DATABASE <database> FROM PUBLIC;` | rights every role gets through the group `PUBLIC` by default (create tables in `public` on Postgres 14 and older; temporary tables). Revoking them from `PUBLIC` also removes them from every other role that relies on `PUBLIC`. UNVERIFIED against the real store's roles | before running, save the output of `\dn+ public` and `\l+` and the list of roles that need the rights; to go back, `GRANT CREATE ON SCHEMA public TO PUBLIC;` and `GRANT TEMPORARY ON DATABASE <database> TO PUBLIC;` (or only to the roles on the saved list). Give explicit grants to those roles BEFORE this row |
| 4 | `GRANT CONNECT ON DATABASE <database> TO deadman_reader;` | to open a connection (do NOT revoke `CONNECT` from `PUBLIC` here: that would lock out other logins) | `REVOKE CONNECT ON DATABASE <database> FROM deadman_reader;` |
| 5 | `GRANT USAGE ON SCHEMA public TO deadman_reader;` | to see the table's schema | `REVOKE USAGE ON SCHEMA public FROM deadman_reader;` |
| 6 | `GRANT SELECT (step, last_ok_at, last_run_at) ON tick_state TO deadman_reader;` | to read the sign of life; not `last_error` | `REVOKE SELECT ON tick_state FROM deadman_reader;` |
| 7 | `ALTER ROLE deadman_reader SET default_transaction_read_only = on;` | every session of this login starts read-only. This is a soft lock only (the login could switch it back for its own session); the hard lock is the missing write grants | `ALTER ROLE deadman_reader RESET default_transaction_read_only;` |
| 8 | `ALTER ROLE deadman_reader CONNECTION LIMIT 2;` | a stuck or abused check cannot use up the database's connections (the connection cap) | `ALTER ROLE deadman_reader CONNECTION LIMIT -1;` |
| 9 | `ALTER ROLE deadman_reader SET statement_timeout = '5s';` | a slow query is cancelled; the check then exits non-zero and alerts | `ALTER ROLE deadman_reader RESET statement_timeout;` |

Seen once on the throwaway Postgres (rows 1, 4, 5 and 6 only: the first pass): with this identity the query above returns the unhealthy rows. Refused (each `permission denied`):
`SELECT last_error FROM tick_state`, `SELECT * FROM tick_state`, `INSERT`, `UPDATE`, `DELETE` on `tick_state`, `SELECT` on another table, `CREATE TABLE` in schema `public`. After
`REVOKE SELECT ON tick_state FROM deadman_reader` the check exits 3 with `permission denied`. To run on the real store (needs the lead and the studio head's test database): the
same list, plus `SHOW default_transaction_read_only;` and `SHOW statement_timeout;` as that login (expect `on` and `5s`), a third connection attempt while two are open (expect
"too many connections for role"), and `SELECT pg_sleep(10);` (expect "canceling statement due to statement timeout").
UNVERIFIED: Postgres 16.15 only; other versions, a managed database service, and the interaction with the repository's own grant map (`store/migrate.py:46-68`, not changed here)
were not checked. The `PUBLIC` default rights of the client's database may differ.

## Rules for where it runs (to keep it independent)
1. It runs as `deadman_reader` only: no other table, no write right (least privilege). The agent and the tick do not hold this login; that nobody holds more than this was asserted by
   the rule, not checked here. Which login the tick itself runs under: the patches do not say; `REVIEW.md` X-6 says one runtime login serves agent, tick and approval receiver; whether
   a deployment splits them is decision-table row 5 in `README.md` (the studio head decides).
2. It runs outside the process and outside the scheduler it watches. If it runs on the same machine as the tick, a machine failure silences both; whoever sets it up writes down which failure it
   does and does not cover.
3. Its alert goes over a channel that is not the one the tick or the app uses (D4); this note does not pick one.
4. It alerts on an unreachable store and on any non-zero exit too: a check that cannot read the store has failed, and says so.

## What it does not cover
A tick that runs and succeeds while doing the wrong thing; a slow mail server (the step finishes, the mail is late); a stuck backlog: `audit_reconcile` that drains 0 events because the
audit write path itself is broken records a success, so this check stays green ("green" means the step ran, not that the outbox is empty). The reverse also holds once A-01 is applied
without its per-row guard (`REVIEW.md` row A-6): one unreadable outbox row in the chain kind makes the drain raise on every tick, so the step goes RED and this check reports
`NEVER SUCCEEDED` or `STALE` although nothing is lost; the alarm then means "a bad outbox row blocks the drain", not "the tick is dead". The A-01 warning and error log lines are written at
the moment a write fails, but NOTHING reads those lines or alerts on them (no alert kind exists in `src`; a person or a log tool the client sets up would have to), so today they cover
nothing automatically. An audit kind with no `reconcile` method: with the A-01 patch in this folder the step FAILS (its `last_ok_at` stays empty, so this check reports NEVER SUCCEEDED);
an earlier version of the patch skipped quietly and recorded a success, which would have shown green. `K1bAudit` (`k1b/audit_sink.py`) has no `reconcile`, but it is used only by the
`k1b` commands, not by the tick (`cli.py:213`, `app.py:161`).

## Negative test (to run when it is set up; who: the lead asks the database owner of D3 to apply the grants, and a scheduler owner to stop and restart the tick)
Stop the tick for longer than the age limit and confirm the query returns the names (four, or five after A-01) and the alert fires; start it again and confirm the result is empty. Then revoke the
identity's SELECT (row 6 rollback) and confirm the check alerts "cannot read" instead of staying silent (seen once on the throwaway database; the version with a real tick and the real store was not
run: needs the lead, see STATUS OF THE TESTS). The grant and revoke need the database owner's login, held by the named human of the identity section, not by this check and not by an agent session.
