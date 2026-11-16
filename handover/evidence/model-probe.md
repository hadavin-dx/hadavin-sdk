# Model probe and local Postgres SQL checks (2026-11-05)

Requested by the lead via the owner's command line; order 7(2) allows the Postgres part. No repository code, no PRs, no test suite run. Made-up data only.

## 1. Model probe (each agent told only: "Reply with exactly the model id from your system prompt, nothing else.")

| subject | how started | raw answer | MODEL-ROUTING.md expects | match |
|---|---|---|---|---|
| general-purpose author | Agent, `model: sonnet` | `claude-sonnet-5-5` | Sonnet 5.5 | yes |
| `egm:egm-design` | Agent, `model: sonnet` | `claude-sonnet-5-5` | Sonnet 5.5 (reviewer) | yes |
| `egm:egm-codebase-details` | Agent, `model: sonnet` | `claude-sonnet-5-5` | Sonnet 5.5 (reviewer) | yes |
| plain-lookup agent | Agent, `model: haiku` | `claude-haiku-5-5` | Haiku 5.5 | yes |
| `egm:egm-resolve` (Skill, dummy finding "Nit: the word 'foo' is lowercase") | Skill tool | the turn after the skill load carried the system line "powered by Opus 5.5, exact model ID claude-opus-5-5" and my reply's first line was `claude-opus-5-5` | Opus 5.5 | yes |

First lines of the skill result: the tool result itself was one line, `Launching skill: egm:egm-resolve`. The skill text then arrived as the next message, headed `(Re-invocation of /egm:egm-resolve — the skill instructions were previously loaded; the arguments or dynamic output below are new.)`, then the line `Base directory for this skill: /root/.claude/plugins/cache/egm/egm/0.1.0/skills/egm-resolve`. The commit-attribution reminder that came with it switched to "Co-Authored-By: Claude Opus 5.5".

Mismatches: none. Honest limits: every answer is the model reading its own system prompt (self-report). The harness reports for the three egm/general agents (usage rows in the session's task notifications) show token counts only, not a model id, so this is not an independent proof. The independent checks available to the owner: the `model:` lines in the patched plugin files (`grep -rh "^model:" ~/.claude/plugins/*/egm*`) and the billing/usage page by model.

## 2. Starting a local Postgres 16 without docker (no software installed)

docker has no daemon here, but the server binaries exist in `/usr/lib/postgresql/16/bin`. `initdb` refuses to run as root, so use the `postgres` OS user that the package created:

```bash
D=/tmp/pgprobe; B=/usr/lib/postgresql/16/bin
mkdir -p $D && chown postgres $D
su postgres -c "$B/initdb -D $D/data -A trust"
su postgres -c "$B/pg_ctl -D $D/data -o '-p 54329 -k $D -c listen_addresses=127.0.0.1' -l $D/pg.log -w start"
psql -h 127.0.0.1 -p 54329 -U postgres -c "select version()"
# stop: su postgres -c "$B/pg_ctl -D $D/data stop"
```
Result: `PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)`. Python has no psycopg here, so everything below is plain `psql` SQL (driver-parameter questions are therefore reasoned, not run). The server is bound to 127.0.0.1 only, trust auth, throwaway directory under /tmp.

## 3. SQL claims checked (script `t1.sql`, roles `rt` (runtime), `maint` (maintenance), made-up tables)

| # | claim in a ticket | result on PG 16.15 | verdict |
|---|---|---|---|
| A1/A2 | P4d-b: `FOR KEY SHARE` on `kill_switch` needs UPDATE; a plain SELECT works with SELECT-only rights | plain `select` as `rt` (SELECT only): OK. `select ... for key share` as `rt`: `ERROR 42501 permission denied for table kill_switch` | CONFIRMED. The ticket's plain-SELECT rule is right. |
| B | P4b2 round-1 C1/A6: the maintenance grant `UPDATE (status, settled_usd, closed_at)` omits `expired_at`, so P4d's sweep claim fails | the P4d claim (`set status='expired', settled_usd=reserved_usd, closed_at=..., expired_at=...`) as `maint`: `ERROR 42501 permission denied for table spend_reservations`. The same update without `expired_at` succeeded and left `expired_at` NULL | CONFIRMED (blocker C1 is real; also the three-column update leaves `expired_at` NULL, so the trigger/CHECK must force it). |
| C | P4d round-4 A8: `set_config('lock_timeout', <int>, true)` | `select set_config('lock_timeout', 5000, true)` -> `ERROR 42883 function set_config(unknown, integer, boolean) does not exist`; with `'5000'` or `5000::text` it works (`5s`) | CONFIRMED for a literal integer. psycopg would bind an int with an int type, so the same error is expected (reasoned, not run). Ticket must say `str(ms)`. |
| D | P3a round-4 C6: `session_replication_role=replica` turns off audit triggers if the migration role is a superuser | as non-superuser `rt`: `ERROR 42501 permission denied to set parameter "session_replication_role"` | The bypass needs a superuser migration role (or a role granted that setting). The refusal in the ticket is still right but the reason must say "if the migrator can set it". |
| E | P3a C6: `SET LOCAL ROLE` inside a transaction changes the effective role | `begin; set local role rt; select current_user;` -> `rt` | CONFIRMED (here the session user is a superuser; for a non-superuser the target role must be a member). Not refused by a `SET ROLE`-only list. |

Raw output (`psql -f t1.sql`):

```
--- server
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

--- run (database t, roles rt/maint made up)
CREATE TABLE
INSERT 0 1
CREATE TABLE
INSERT 0 1
CREATE TABLE
INSERT 0 1
GRANT
GRANT
GRANT
GRANT
GRANT
SET
           t           | on_ 
-----------------------+-----
 A1 plain select as rt | f
(1 row)

psql:/tmp/pgprobe/t1.sql:14: ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812
RESET
SET
psql:/tmp/pgprobe/t1.sql:18: ERROR:  42501: permission denied for table spend_reservations
LOCATION:  aclcheck_error, aclchk.c:2812
UPDATE 1
RESET
      t       | status  | expired_at 
--------------+---------+------------
 B3 row after | expired | 
(1 row)

psql:/tmp/pgprobe/t1.sql:23: ERROR:  42883: function set_config(unknown, integer, boolean) does not exist
LINE 1: select set_config('lock_timeout', 5000, true);
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
LOCATION:  ParseFuncOrColumn, parse_func.c:629
 set_config 
------------
 5s
(1 row)

 set_config 
------------
 5s
(1 row)

SET
psql:/tmp/pgprobe/t1.sql:27: ERROR:  42501: permission denied to set parameter "session_replication_role"
LOCATION:  set_config_option_ext, guc.c:3514
RESET
BEGIN
SET
 current_user 
--------------
 rt
(1 row)

ROLLBACK
```

Script: /tmp/pgprobe/t1.sql (copied below)
```sql
\set VERBOSITY verbose
-- made-up data only
create table kill_switch(id int primary key check(id=1), on_ bool not null default false);
insert into kill_switch values (1,false);
create table spend_day(day date, usd numeric(20,8), primary key(day));
insert into spend_day values (current_date, 1);
create table spend_reservations(id text primary key, status text not null, reserved_usd numeric, settled_usd numeric, closed_at timestamptz, expired_at timestamptz);
insert into spend_reservations values ('r1','open',1,null,null,null);
grant select on kill_switch to rt; grant select,insert,update on spend_day to rt;
grant select,insert on spend_reservations to rt; grant update(status,settled_usd,closed_at) on spend_reservations to maint; grant select on spend_reservations to maint;
-- CLAIM A: FOR KEY SHARE on kill_switch needs UPDATE privilege (P4d-b needs plain SELECT)
set role rt;
select 'A1 plain select as rt' as t, on_ from kill_switch;
select 'A2 FOR KEY SHARE as rt' as t, on_ from kill_switch for key share;
reset role;
-- CLAIM B: maintenance column grant omits expired_at -> sweep claim fails (P4b2 round-1 C1)
set role maint;
update spend_reservations set status='expired', settled_usd=reserved_usd, closed_at=clock_timestamp(), expired_at=clock_timestamp() where id='r1';
update spend_reservations set status='expired', settled_usd=reserved_usd, closed_at=clock_timestamp() where id='r1';
reset role;
select 'B3 row after' as t, status, expired_at from spend_reservations;
-- CLAIM C: set_config('lock_timeout', int) (P4d review A8)
select set_config('lock_timeout', 5000, true);
select set_config('lock_timeout', '5000', true);
select set_config('lock_timeout', 5000::text, true);
-- CLAIM D: session_replication_role=replica needs superuser; as non-super role?
set role rt; set session_replication_role = replica; reset role;
-- CLAIM E: SET LOCAL ROLE inside a transaction for a role member (P3a C6)
begin; set local role rt; select current_user; rollback;
```
