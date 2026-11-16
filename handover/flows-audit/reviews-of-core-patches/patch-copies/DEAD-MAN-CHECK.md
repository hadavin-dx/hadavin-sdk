# External dead-man check on `tick_state.last_ok_at` (note only: no core code)

**STATUS OF THE PATCH THIS NOTE DEPENDS ON (read first).** `../REVIEW.md:5` says: "A-01 is DEFERRED, the C-01 extras (the token ceiling) are CUT, the G5 wording patch is KEPT (text only)",
and `REVIEW.md` item 3 of its list says C-01 is "DO NOT APPLY NOW". These are the lead's defaults of 2026-11-16; the studio head may veto them. So today
`A-01.patch` is NOT applied, and **the query below ships in its four-name form, ready to copy as it stands**. The fifth name `audit_reconcile` exists only after A-01 is applied; it is one separate line to
add after A-01 (see "Which names to check"). Words (tick, step, outbox, audit kind, reconcile, studio head, lead, database administrator, migrations login, scheduler operator, live): see the box in `README.md` of this folder.
All line cites are at commit `b4cce5b`, unless marked "newest commit" (the newest commit of this working copy; `README.md` says which). This folder is for a copy, never the live code; this note adds no core code.

RUNG: existing code. The tick already writes one `tick_state` row per step with `last_run_at`, `last_ok_at` and `last_error` (`runtime/tick.py:319`, `store.save_tick_state`;
table in `store/migrations/0003_approvals_tick.sql:30-35`, both at `b4cce5b`). Nothing new is built in core. The check is a query run by something OUTSIDE the tick process.

STATUS OF THE TESTS: the query (with five names) and rows 1, 3, 4 and 5 of the identity table below were run ONCE on 2026-11-16 on a throwaway Postgres 16.15 with only the `tick_state` table (taken from
the migration file) and made-up rows: "seen once on a throwaway Postgres, not the real store". **That server was started by the `postgres` operating-system user and accepted every connection on a local socket without a password (`../fix-patchcopies1.md`, section 6), so the statements almost certainly ran as a superuser, which is allowed to do everything: the run does NOT show which login rights each statement needs on a real store. That is why the section "Which login runs each statement" below states the rights from the Postgres manual, marked UNVERIFIED where no database was used.** Raw commands and output: `../fix-patchcopies1.md` (the file `handover/flows-audit/reviews-of-core-patches/fix-patchcopies1.md`, one folder up from this one). UNVERIFIED (the second and third
passes were static: no database was started): rows 2, 6, 7 and 8 of the table (the password step, `default_transaction_read_only`,
`CONNECTION LIMIT`, `statement_timeout`) and decision D5 (the database-wide `REVOKE` lines), the real store, a real scheduler, an alert channel. **Needs the lead to ask the studio head for a test database with the real migrations
applied; next step there: run the "Negative test" section.**

## Decisions and who does what (this note's part; the full list of decisions is the table in `README.md`)
Defaults marked AUDIT PROPOSAL are the audit session's proposals, **lead to confirm**; none is a studio-head decision yet.
| # | Decision or task | Who | Blocks a merge? | Default if nobody decides |
|---|---|---|---|---|
| D1 | Bring A-01 back (without it the step name `audit_reconcile` does not exist) | studio head | no merge of this note; yes for A-01 | stays deferred (`../REVIEW.md:5`) |
| D2 | Age limit in seconds (`:limit_s`), proposal `180` | studio head | no | AUDIT PROPOSAL, lead to confirm: `180` (90 if the tick runs every 30 seconds only) |
| D3 | Name the database administrator (the human who may sign in with the logins that the statements below need, see "Which login runs each statement") and who creates the login | studio head | no | AUDIT PROPOSAL, lead to confirm: for the studio's own test database, the studio head; for a client build, the client's own database administrator, named in writing before the first grant. Until a person is named, nobody runs the statements and nothing is set up |
| D4 | A second alert channel that is not the one the tick or the app uses, and who pays for it (`system-map` Decision B: see the words box in `README.md`) | studio head | no | AUDIT PROPOSAL, lead to confirm: a plain e-mail sent by the scheduler machine's own mail command to a mailbox the studio head names, which is not the mailbox or channel the app uses; no paid service (a paid channel needs the studio head's yes with numbers). Whether the scheduler machine has a mail command is not known here (UNVERIFIED) |
| D5 | Whether to also remove two default rights of the group `PUBLIC` database-wide (a separate hardening of the whole database, NOT part of this read-only identity; text under the identity table) | studio head, with the database administrator | no | not done |
| D6 | Name the scheduler operator: the person who saves the query file on the scheduler machine and wires its schedule and alert (T1, T2) | studio head | no | AUDIT PROPOSAL, lead to confirm: the studio head for the studio's own runs; for a client build, the client's operations person, named in writing |
| T1 | Save the query as `dead-man-check.sql` on the machine of the scheduler | scheduler operator (D6) | no | not done |
| T2 | Schedule the command below and wire its alert | scheduler operator (D6) | no | not done |
| T3 | Apply `A-01.patch` (only if D1 is yes) | a builder opens the pull request; the lead merges | yes for A-01 | not done |

## Which names to check (and why A-01 matters)
The query ships with FOUR names: `sweep`, `reconcile`, `stuck`, `checkpoint`. The step `audit_reconcile` exists only after `A-01.patch` is applied (see `README.md`); while A-01 is deferred, do NOT add it:
the query would report `audit_reconcile` as MISSING on every run and alarm forever. **After A-01 is applied (and not before)**, change the one line of the query that reads
`FROM (VALUES ('sweep'), ('reconcile'), ('stuck'), ('checkpoint')) AS w(step)` to
`FROM (VALUES ('sweep'), ('reconcile'), ('stuck'), ('checkpoint'), ('audit_reconcile')) AS w(step)`; nothing else changes. The list is typed by hand: if a step is later added to `STEPS` in
`runtime/tick.py` (`:249` at `b4cce5b`), add its name here too, or it is not watched. Words: here "reconcile" is the tick step of that name; the audit outbox drain that A-01 adds is the separate step `audit_reconcile`.

## What it checks
A tick that has stopped (scheduler dead, container gone, store unreachable) writes nothing, so it cannot report its own silence. The check asks the store whether each step has
succeeded recently. Steps that run every tick: `sweep`, `reconcile`, `stuck`, `checkpoint`, and `audit_reconcile` (only after A-01). Steps with their own interval (`purge_evidence`,
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
FROM (VALUES ('sweep'), ('reconcile'), ('stuck'), ('checkpoint')) AS w(step)   -- four names; add ('audit_reconcile') only after A-01 is applied
LEFT JOIN tick_state t ON t.step = w.step
WHERE t.step IS NULL
   OR t.last_ok_at IS NULL
   OR t.last_ok_at < now() - make_interval(secs => :limit_s)
ORDER BY w.step;
```
Run (T2): `psql -h <host> -U deadman_reader -d <database> -v ON_ERROR_STOP=1 -v limit_s=180 -At -f dead-man-check.sql`, with `PGSSLMODE=verify-full` and `PGSSLROOTCERT=<path of the CA file>` set for that one command (see "Connection" below).
- `<host>` and `<database>`: the same host and database name as the store setting of the deployment's config; the database administrator (D3) hands them over.
- Password: never on the command line (a process list shows it), and not as an environment variable if a password file is possible. First choice: a password file (`PGPASSFILE`, permission 600, written by the
  scheduler at job start from the secret `deadman_reader_password` read through the secrets kind (a named lookup), removed at job end; the one line in it has the form `<host>:<port>:<database>:deadman_reader:<password>`); the `psql` manual calls it the safer form. Second choice, only where a password file is
  impossible: the environment variable `PGPASSWORD` set on that single command (a process environment can be read by the same user on some systems). If the client's database supports short-lived tokens or client certificates, use those instead.
- Connection (UNVERIFIED against the real store): the password must not cross the network in clear text. Set `PGSSLMODE=verify-full` and `PGSSLROOTCERT` to the CA file of the database's certificate for that one command, so the check refuses a server it cannot verify. If the database cannot offer TLS (for example a socket on the same machine), the studio head accepts that in writing.
- Alert when the output has any line, OR when `psql` exits non-zero. Exit codes of `psql` (its manual): 2 = it could not connect (store unreachable or login refused); 3 = the script failed
  (with `ON_ERROR_STOP`), for example a missing `-v limit_s` or `permission denied`; 1 = another fatal error of `psql` itself.
- The scheduler and the alert are not part of core and no `alert` kind exists in `src` (at `b4cce5b`); the scheduler operator (D6) wires the alert (D4).
The query reads only `step`, `last_ok_at` and `last_run_at`. It does not read `last_error`, so error text can never reach the alert channel.

Example of an unhealthy result (made-up data, seen with the five-name form after A-01: `sweep` never succeeded, `stuck` last succeeded 10 minutes ago, `audit_reconcile` has no row; with today's four-name form that first line would not appear):
```
audit_reconcile|||MISSING (no row: never ran)
stuck|2026-11-16 14:28:52+00|2026-11-16 14:38:52+00|STALE (last success older than the limit)
sweep||2026-11-16 14:38:52+00|NEVER SUCCEEDED
```
Healthy: no output, exit code 0. (All of these were seen on the throwaway database; timestamps shortened here.)

## The read-only identity (PROPOSAL: the studio head decides; `REVIEW.md` D-3 (2) and the identity table row `dead-man reader` under X-6.6)
Name: `deadman_reader` (a proposed name). **Who runs these statements: the database administrator (D3, a named human) of the client's or the studio's database.** The statements need DIFFERENT rights, so no one login is assumed to be enough (next section). No agent session creates or holds any of these logins (one identity per function, the least-privilege rule). The tick, the agent and this check never create the role. Each statement and its reason:

### Which login runs each statement (rights come from the Postgres manual; UNVERIFIED on a real store, see "STATUS OF THE TESTS")
| Row | Statement needs | Why (Postgres rule) | Tested? |
|---|---|---|---|
| 1 `CREATE ROLE` | a login with the `CREATEROLE` attribute, or a superuser | creating a role is a right of those attributes; the migrations login does not normally have it | only as a superuser on a throwaway (rows 1, 3, 4, 5 seen once); not tested with a plain `CREATEROLE` login |
| 2 password step | the same login as row 1 (it must be allowed to change that role) | `\password` runs `ALTER ROLE ... PASSWORD` | not tested |
| 3 `GRANT CONNECT ON DATABASE` | the database-owning login (normally the one that created the database), a superuser, or a login that holds `CONNECT` with the grant option | a grant needs the right to give it | only as a superuser |
| 4 `GRANT USAGE ON SCHEMA public` | the schema-owning login (at Postgres 15 and later the schema `public` belongs to the built-in role `pg_database_owner`, which means the database-owning login), a superuser, or a login with the grant option | same | only as a superuser |
| 5 `GRANT SELECT (...) ON tick_state` | the table-owning login (the migrations login, `store/migrate.py`), a superuser, or a login with the grant option on that column | same | only as a superuser |
| 6, 7, 8 `ALTER ROLE ... SET / CONNECTION LIMIT` | a superuser, or a login with `CREATEROLE` that is allowed to change that role (at Postgres 16 the login that created the role is) | changing another role's settings needs those rights | NOT tested at all (static) |
**Plainly:** the only rows tested were run on a throwaway where the login was almost certainly a superuser. What the manual says, not what was seen, is in this table. In the usual case one administrator login (a superuser, or the provider's top login on a managed database service) can run rows 1 to 4 and 6 to 8, and the table-owning login or that same administrator runs row 5. A managed database service may not allow a superuser at all: then the provider's administrator login stands in, and what it may do is the provider's documentation (not read here).

**How the database administrator finds which login to use** (read-only queries; run each as the login you are considering, in `psql`; this was NOT run against a database in this pass):
```
SELECT current_user, rolsuper, rolcreaterole FROM pg_roles WHERE rolname = current_user;      -- row 1, 2, 6, 7, 8: rolsuper = t, or rolcreaterole = t
SELECT pg_get_userbyid(datdba) AS database_owner FROM pg_database WHERE datname = current_database();   -- row 3
SELECT nspowner::regrole AS schema_owner FROM pg_namespace WHERE nspname = 'public';          -- row 4
SELECT tableowner FROM pg_tables WHERE tablename = 'tick_state';                               -- row 5 (the table-owning login)
```
If the login you hold is not the name printed (and is not a superuser), ask the administrator who holds it; if a statement still answers `permission denied` or `must have CREATEROLE`, that login lacks the right: stop, do not widen any role, and ask the studio head (D3). Never run these statements with the runtime login of the app (it cannot grant rights, and it must not).

### The statements (run once, in this order, by the database administrator, each with the login named in the table above)
| # | Statement | Reason | Rollback |
|---|---|---|---|
| 1 | `CREATE ROLE deadman_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;` | its own identity; no password text in this file or in any command line | `DROP ROLE deadman_reader;` (after the rows below are revoked) |
| 2 | Password step (below the table): generate a random secret with `openssl rand -base64 24`, keep it off the screen, set it with `\password deadman_reader` at the hidden prompt, and store the same secret for the scheduler | the role cannot log in without a credential; this keeps it out of the repository and the logs | `ALTER ROLE deadman_reader PASSWORD NULL;` |
| 3 | `GRANT CONNECT ON DATABASE <database> TO deadman_reader;` | to open a connection (do NOT revoke `CONNECT` from `PUBLIC` here: that would lock out other logins) | `REVOKE CONNECT ON DATABASE <database> FROM deadman_reader;` |
| 4 | `GRANT USAGE ON SCHEMA public TO deadman_reader;` | to see the table's schema | `REVOKE USAGE ON SCHEMA public FROM deadman_reader;` |
| 5 | `GRANT SELECT (step, last_ok_at, last_run_at) ON tick_state TO deadman_reader;` | to read the sign of life; not `last_error` | `REVOKE SELECT ON tick_state FROM deadman_reader;` |
| 6 | `ALTER ROLE deadman_reader SET default_transaction_read_only = on;` | every session of this login starts read-only. This is a soft lock only (the login could switch it back for its own session); the hard lock is the missing write grants | `ALTER ROLE deadman_reader RESET default_transaction_read_only;` |
| 7 | `ALTER ROLE deadman_reader CONNECTION LIMIT 2;` | a stuck or abused check cannot use up the database's connections (the connection cap) | `ALTER ROLE deadman_reader CONNECTION LIMIT -1;` |
| 8 | `ALTER ROLE deadman_reader SET statement_timeout = '5s';` | a slow query is cancelled; the check then exits non-zero and alerts | `ALTER ROLE deadman_reader RESET statement_timeout;` |

**Password step (row 2), typeable.** Nobody types or sees the secret on the screen, and it is never put in a command line, a chat or a shell history. On the database administrator's machine, in `bash`:
```
umask 077                                                                  # the next file is readable by you only
openssl rand -base64 24 | tr -d '\n' > "$HOME/deadman_reader.secret"       # 24 random bytes = 32 characters, written to a file, not shown
# copy the file's content to the clipboard without showing it: Linux `xclip -selection clipboard < "$HOME/deadman_reader.secret"`, macOS `pbcopy < ...`
DBHOST=...; DBNAME=...; ADMIN_LOGIN=...                                 # fill in the three values (see "Run (T2)" for host and database; the login is the one chosen above)
psql -h "$DBHOST" -d "$DBNAME" -U "$ADMIN_LOGIN"                           # then inside psql:  \password deadman_reader   (paste at the hidden prompt, twice)
# store the same file content in the place the scheduler reads `deadman_reader_password` from (below), then delete the local copy:
shred -u "$HOME/deadman_reader.secret"                                     # where `shred` is not available: `rm` it and clear the clipboard
```
`\password` hashes the secret on the client before sending it (with the default `password_encryption = scram-sha-256` of Postgres 14 and later; UNVERIFIED here), so the plain value is not written to the server log by that command. **Where the scheduler stores it: UNANSWERED lead item.** Which secrets-kind backend the scheduler machine reads `deadman_reader_password` from (a file the scheduler writes, a vault of the client's cloud, an environment of the job) is chosen by the scheduler operator (D6) and is not named anywhere in this folder or in `REVIEW.md`; the lead asks the studio head. Rotation: repeat this step with a new secret and replace the stored one (the old one stops working at once); no interval is set here (`REVIEW.md` Decision 21).

Seen once on the throwaway Postgres, as a superuser (rows 1, 3, 4 and 5 only: the first pass): with this identity the query above returns the unhealthy rows. Refused (each `permission denied`):
`SELECT last_error FROM tick_state`, `SELECT * FROM tick_state`, `INSERT`, `UPDATE`, `DELETE` on `tick_state`, `SELECT` on another table, `CREATE TABLE` in schema `public`. After
`REVOKE SELECT ON tick_state FROM deadman_reader` the check exits 3 with `permission denied`. To run on the real store (needs the lead and the studio head's test database): the
same list, plus `SHOW default_transaction_read_only;` and `SHOW statement_timeout;` as that login (expect `on` and `5s`), a third connection attempt while two are open (expect
"too many connections for role"), and `SELECT pg_sleep(10);` (expect "canceling statement due to statement timeout").
UNVERIFIED: Postgres 16.15 only; other versions, a managed database service, and the interaction with the repository's own grant map (`store/migrate.py:46-68`, not changed here)
were not checked. The `PUBLIC` default rights of the client's database may differ.

**Separate decision D5 (not part of this identity).** Earlier text had a row that ran `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` and `REVOKE TEMPORARY ON DATABASE <database> FROM PUBLIC;` as part of creating the read-only login. That was wrong in kind:
those two statements change the rights of every role that relies on the group `PUBLIC` (they can break the app, the tick or the migrations), so they are a hardening of the whole database, not a statement about one read-only identity. What it means for this login: on the tested Postgres 16 `PUBLIC` has no right to create tables in `public`, so the login has none; on Postgres 14 and older it does have that right through `PUBLIC`
(a right cannot be taken from one role alone while it comes from `PUBLIC`), and then only the soft lock of row 6 stands in the way until D5 is done. Check `\dn+ public` before you start. If the studio head wants them (D5), the database administrator does it as its own change: first save the output of `\dn+ public` and `\l+` and the list of roles that need those rights, give those roles explicit grants, then run the two `REVOKE` lines;
to go back, `GRANT CREATE ON SCHEMA public TO PUBLIC;` and `GRANT TEMPORARY ON DATABASE <database> TO PUBLIC;` (or only to the roles on the saved list). UNVERIFIED against the real store's roles; default D5: not done.

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

## Negative test (to run when it is set up; who: the lead asks the database administrator of D3 to apply the grants, and the scheduler operator of D6 to stop and restart the tick; the alert it fires goes to the channel of D4, so the test cannot be completed until D4 and D6 are answered)
Stop the tick for longer than the age limit and confirm the query returns the names (four, or five after A-01) and the alert fires; start it again and confirm the result is empty. Then revoke the
identity's SELECT (row 5 rollback) and confirm the check alerts "cannot read" instead of staying silent (seen once on the throwaway database; the version with a real tick and the real store was not
run: needs the lead, see STATUS OF THE TESTS). The grant and revoke need the logins named in "Which login runs each statement" (the table-owning login for row 5), held by the database administrator (the named human, D3), not by this check and not by an agent session.
