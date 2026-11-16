# P2a database evidence (revision 6): raw output of the scratch SQL run

- Run by the P2a ticket author, 2026-11-05 (UTC; IST = UTC+5:30), against the throwaway PostgreSQL 16.15 cluster already running on 127.0.0.1 port 54329 (trust authentication, superuser `postgres`). The run created one database `p2a6_sql` and roles `p2a6_*` and dropped all of them at the end (last lines of the output). Nothing else on the cluster was touched or stopped.
- PostgreSQL 16.15 only. The CI service is 17.10: behaviour on 17 is UNVERIFIED (P0e must confirm).
- This is a model of the design (tables, trigger function, grants) in the non-public schema `t_p2a6`, written by hand in SQL. It is NOT the migration file or `migrate()` (neither exists yet). What it proves is database behaviour; claims about Python (`migrate()` re-issuing the function, `Store` methods, the CLI) are not covered and stay UNVERIFIED until code exists.
- The test ids S1-S28 are cited from `tickets/P2a.md`. Script text follows, then raw output. Re-run: save the script and run it with `psql` access to a throwaway server (edit the `H` variable).
- Known limits of this run: no PG 17 run; the advisory-lock key in S23 is computed in SQL, not read from `migrate.py`; S21 uses a 1 s timeout and one held lock; S3 runs the 1000 stops in one transaction (not 1000 round trips).

## Script

```bash
#!/bin/bash
# Throwaway-database run for P2a revision 6. Port 54329, PG 16. Creates and drops only p2a6_* objects.
H="-h 127.0.0.1 -p 54329"; DB=p2a6_sql; S=t_p2a6
su_() { psql $H -U postgres -d "${2:-$DB}" -v VERBOSITY=verbose -At -c "$1" 2>&1; }
as() { psql $H -U "$1" -d $DB -v VERBOSITY=verbose -At -c "$2" 2>&1; }
t() { echo; echo "## $1"; }
cleanup() { psql $H -U postgres -d postgres -qAt -c "drop database if exists $DB" >/dev/null 2>&1
 for r in p2a6_out p2a6_ownmem p2a6_bg p2a6_op p2a6_rt p2a6_mig p2a6_grp; do psql $H -U postgres -d postgres -qAt -c "drop role if exists $r" >/dev/null 2>&1; done; }
cleanup
psql $H -U postgres -d postgres -qAt <<SQL
create database $DB;
create role p2a6_mig login; create role p2a6_rt login; create role p2a6_grp nologin;
create role p2a6_op login in role p2a6_grp; create role p2a6_bg login in role p2a6_grp;
create role p2a6_out login; create role p2a6_ownmem login noinherit in role p2a6_mig;
SQL
psql $H -U postgres -d $DB -q <<SQL
create schema $S authorization p2a6_mig;
set session authorization p2a6_mig;
create table $S.kill_switch(id int primary key check (id=1), "on" bool not null, "by" text not null, ts timestamptz not null default now(), schema_version int not null default 1, version bigint not null default 0);
insert into $S.kill_switch(id,"on","by") values (1,false,'seed');
create table $S.kill_switch_guard_config(id smallint primary key check(id=1), reset_group text);
create table $S.kill_switch_login_labels(login_name text primary key, label text not null);
create table $S.kill_switch_resets(old_version bigint primary key, reset_at timestamptz, login_label text, old_by text);
create function $S.append_only() returns trigger language plpgsql as \$f\$ begin raise exception 'append only' using errcode='42501'; end \$f\$;
create trigger resets_append_only before update or delete on $S.kill_switch_resets for each row execute function $S.append_only();
reset session authorization;
SQL
# guard function built with the migrator's schema as an identifier (finding ADV-A1 / COR-C2)
psql $H -U postgres -d $DB -q <<'SQL'
set session authorization p2a6_mig;
DO $do$
DECLARE s text := 't_p2a6';
BEGIN
EXECUTE format($fn$
CREATE OR REPLACE FUNCTION %1$I.hadavin_kill_switch_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
DECLARE grp text; lbl text;
BEGIN
  IF OLD."on" AND NOT NEW."on" THEN
    SELECT reset_group INTO grp FROM %1$I.kill_switch_guard_config WHERE id = 1;
    IF NOT coalesce(pg_has_role(session_user, grp, 'MEMBER'), false) THEN
      RAISE EXCEPTION 'kill switch: only the reset role may clear it' USING ERRCODE = '42501'; END IF;
    SELECT label INTO lbl FROM %1$I.kill_switch_login_labels WHERE login_name = session_user::text;
    IF lbl IS NULL THEN RAISE EXCEPTION 'kill switch: login not registered' USING ERRCODE = '42501'; END IF;
    INSERT INTO %1$I.kill_switch_resets VALUES (OLD.version, now(), lbl, OLD."by");
    NEW."by" := lbl; NEW.version := OLD.version + 1; NEW.ts := now();
  ELSIF NEW."on" AND NOT OLD."on" THEN
    NEW.version := OLD.version + 1; NEW.ts := now();
  ELSE
    NEW."on" := OLD."on"; NEW."by" := OLD."by"; NEW.ts := OLD.ts; NEW.version := OLD.version;
  END IF;
  NEW.id := OLD.id; RETURN NEW;
END $f$;$fn$, s);
EXECUTE format('REVOKE ALL ON FUNCTION %1$I.hadavin_kill_switch_guard() FROM PUBLIC', s);
EXECUTE format('CREATE OR REPLACE TRIGGER kill_switch_guard BEFORE UPDATE ON %1$I.kill_switch FOR EACH ROW EXECUTE FUNCTION %1$I.hadavin_kill_switch_guard()', s);
EXECUTE format('ALTER TABLE %1$I.kill_switch ENABLE ALWAYS TRIGGER kill_switch_guard', s);
END $do$;
reset session authorization;
SQL
psql $H -U postgres -d $DB -q <<SQL
grant usage on schema $S to p2a6_rt, p2a6_grp, p2a6_out;
grant select, update on $S.kill_switch to p2a6_rt, p2a6_grp;
grant select on $S.kill_switch_resets, $S.kill_switch_guard_config to p2a6_rt;
insert into $S.kill_switch_guard_config values (1,'p2a6_grp');
insert into $S.kill_switch_login_labels values ('p2a6_op','label-op'),('p2a6_bg','breakglass');
SQL
K=$S.kill_switch; RT=p2a6_rt; OP=p2a6_op
t "S1 (A1/C2): guard installed in a NON-public schema ($S); first stop by the runtime login sets version 1"
as $RT "update $K set \"on\"=true, \"by\"='stop-a' where id=1 returning \"on\",\"by\",version"
t "S2 (A2): a second stop keeps the first by and version"
as $RT "update $K set \"on\"=true, \"by\"='stop-b' where id=1 returning \"on\",\"by\",version"
t "S3 (A2): 1000 stops in one transaction, then the ORIGINAL token (1) still resets"
as $RT "do \$\$ begin for i in 1..1000 loop update $K set \"on\"=true, \"by\"='s'||i where id=1; end loop; end \$\$"
as $RT "select version from $K"
t "S4: runtime login ON->OFF is refused (SQLSTATE 42501 and the fixed message)"
as $RT "update $K set \"on\"=false where id=1"
t "S5: outsider login (no grant) is refused"
as p2a6_out "update $K set \"on\"=false where id=1"
t "S6: runtime INSERT, DELETE, TRUNCATE are denied"
as $RT "insert into $K(id,\"on\",\"by\") values (2,true,'x')"
as $RT "delete from $K"
as $RT "truncate $K"
t "S7: stale token updates 0 rows"
as $OP "update $K set \"on\"=false, \"by\"='typed-raw' where id=1 and \"on\" and version=99 returning version"
t "S8 (A7): correct token succeeds; stored by is the LABEL not the typed text; one resets row written with the label"
as $OP "update $K set \"on\"=false, \"by\"='typed-raw@example.test' where id=1 and \"on\" and version=1 returning \"on\",\"by\",version"
as $RT "select old_version, login_label, old_by from $S.kill_switch_resets"
t "S9: runtime cannot update or delete the resets table"
as $RT "update $S.kill_switch_resets set login_label='x'"
t "S10: breakglass login reset gets label 'breakglass'"
as $RT "update $K set \"on\"=true,\"by\"='again' where id=1 returning version"
as p2a6_bg "update $K set \"on\"=false,\"by\"='bg' where id=1 and \"on\" and version=3 returning \"by\",version"
as $RT "select old_version, login_label from $S.kill_switch_resets order by 1"
t "S11: an UNREGISTERED login, even a superuser, is refused (label test); superuser with session_replication_role=replica is still refused (state is ON)"
as $RT "update $K set \"on\"=true,\"by\"='again2' where id=1 returning version"
su_ "update $K set \"on\"=false where id=1"
psql $H -U postgres -d $DB -v VERBOSITY=verbose -At -c "set session_replication_role=replica; update $K set \"on\"=false where id=1" 2>&1
t "S12 (A5): NOINHERIT member of the owner role: membership TRUE, USAGE FALSE, table privilege FALSE, yet it can disable the trigger"
su_ "select pg_has_role('p2a6_ownmem','p2a6_mig','MEMBER'), pg_has_role('p2a6_ownmem','p2a6_mig','USAGE'), has_table_privilege('p2a6_ownmem','$K','UPDATE')"
as p2a6_ownmem "set role p2a6_mig; alter table $K disable trigger kill_switch_guard; select tgenabled from pg_trigger where tgname='kill_switch_guard'"
t "S13 (A12): the runtime login can read tgenabled (D after the disable) and, after the owner re-enables with ENABLE ALWAYS, A"
as $RT "select tgenabled from pg_trigger where tgname='kill_switch_guard' and tgrelid='$K'::regclass"
as p2a6_mig "alter table $K enable always trigger kill_switch_guard"
as $RT "select tgenabled from pg_trigger where tgname='kill_switch_guard' and tgrelid='$K'::regclass"
t "S14: CREATE OR REPLACE TRIGGER resets tgenabled to O (so migrate() must re-assert ENABLE ALWAYS)"
as p2a6_mig "create or replace trigger kill_switch_guard before update on $K for each row execute function $S.hadavin_kill_switch_guard()"
as $RT "select tgenabled from pg_trigger where tgname='kill_switch_guard' and tgrelid='$K'::regclass"
as p2a6_mig "alter table $K enable always trigger kill_switch_guard"
t "S15: the runtime can read prosecdef and proconfig (probe inputs)"
as $RT "select prosecdef, proconfig from pg_proc where proname='hadavin_kill_switch_guard'"
t "S16: the runtime cannot create a function in the schema, cannot disable the trigger"
as $RT "create function $S.evil() returns int language sql as 'select 1'"
as $RT "alter table $K disable trigger kill_switch_guard"
t "S17 (A8): dry run as the runtime login in a rolled-back transaction: first UPDATE succeeds, second raises 42501 with the fixed message"
as $RT "begin; update $K set \"on\"=true where id=1; update $K set \"on\"=false where id=1; rollback"
t "S18 (A8): a lost UPDATE grant also gives 42501 but with a DIFFERENT message (so the probe must match the message AND need the first UPDATE to succeed)"
su_ "revoke update on $K from p2a6_rt"
as $RT "begin; update $K set \"on\"=true where id=1; rollback"
su_ "grant update on $K to p2a6_rt"
t "S19: group NULL refuses with the fixed 42501 message; a group naming a missing role, or the empty string, raises 42704 (role does not exist) and still refuses"
su_ "update $S.kill_switch_guard_config set reset_group=null"
as $OP "update $K set \"on\"=false where id=1"
su_ "update $S.kill_switch_guard_config set reset_group='nosuchrole'"
as $OP "update $K set \"on\"=false where id=1"
su_ "update $S.kill_switch_guard_config set reset_group=''"
as $OP "update $K set \"on\"=false where id=1"
su_ "update $S.kill_switch_guard_config set reset_group='p2a6_grp'"
t "S20 (A9/C8): set_config with an integer argument fails (42883); with text it works; inside a transaction (autocommit needs one)"
as $RT "select set_config('lock_timeout', 1000, true)"
as $RT "begin; select set_config('lock_timeout', '1000', true); show lock_timeout; commit"
t "S21 (A10): a session holding FOR UPDATE makes a stop fail with 55P03 after lock_timeout"
( as $RT "begin; select 1 from $K where id=1 for update; select pg_sleep(5); rollback" >/dev/null & ) ; sleep 1
as $RT "begin; select set_config('lock_timeout','1000',true); update $K set \"on\"=true,\"by\"='blocked' where id=1; rollback"
sleep 5
t "S22 (A3): old core upsert (INSERT ... ON CONFLICT) fails without INSERT, works after GRANT INSERT"
as $RT "insert into $K(id,\"on\",\"by\") values (1,true,'old') on conflict (id) do update set \"on\"=excluded.\"on\", \"by\"=excluded.\"by\""
su_ "grant insert on $K to p2a6_rt"
as $RT "insert into $K(id,\"on\",\"by\") values (1,true,'old') on conflict (id) do update set \"on\"=excluded.\"on\", \"by\"=excluded.\"by\" returning \"on\", \"by\", version"
as $RT "update $K set \"on\"=false where id=1"
su_ "revoke insert on $K from p2a6_rt"
t "S23 (A3): the recipe lock text: pg_advisory_xact_lock with the migrate lock key"
su_ "begin; select pg_advisory_xact_lock((('x'||encode('hadvnmig','hex'))::bit(64)::bigint)>>1); grant insert on $K to p2a6_rt; rollback"
t "S24 (A14): a missing row. Superuser deletes it; a stop UPDATE affects 0 rows; re-seed as ON then a registered login resets with the new token"
su_ "delete from $K"
as $RT "update $K set \"on\"=true,\"by\"='x' where id=1 returning version"
su_ "insert into $K(id,\"on\",\"by\",version) values (1,true,'dba',7) on conflict do nothing returning \"on\",version"
as $OP "update $K set \"on\"=false,\"by\"='t' where id=1 and \"on\" and version=7 returning \"on\",\"by\",version"
t "S25: stored group value and ownership: the function and tables are owned by the migrator, not the runtime"
su_ "select reset_group from $S.kill_switch_guard_config"
su_ "select c.relname, pg_get_userbyid(c.relowner) from pg_class c where c.relnamespace='$S'::regnamespace and c.relkind='r' order by 1"
su_ "select pg_get_userbyid(proowner) from pg_proc where proname='hadavin_kill_switch_guard'"
t "S26: function text installed (schema name is an identifier built by the migrator; no public. anywhere)"
su_ "select position('public.' in prosrc) as public_dot, position('$S.' in prosrc) as schema_dot, position('kill_switch_guard_config' in prosrc)>0 from pg_proc where proname='hadavin_kill_switch_guard'"
t "S27 (A1 negative control): the same function text hard-coded to public.* in this non-public schema raises 'relation does not exist' (SQLSTATE 42P01), not 42501"
psql $H -U postgres -d $DB -q <<SQL
create schema t_bad authorization p2a6_mig;
set session authorization p2a6_mig;
create table t_bad.ks(id int primary key, "on" bool, "by" text, version bigint);
insert into t_bad.ks values (1,true,'x',1);
create function t_bad.g() returns trigger language plpgsql security definer set search_path = pg_catalog, pg_temp as \$f\$ declare grp text; begin if OLD."on" and not NEW."on" then select reset_group into grp from public.kill_switch_guard_config where id=1; end if; return NEW; end \$f\$;
create trigger g before update on t_bad.ks for each row execute function t_bad.g();
reset session authorization;
SQL
su_ "update t_bad.ks set \"on\"=false where id=1"
t "S28: PostgreSQL version"
su_ "select version()"
cleanup
echo; echo "## cleanup done (database and p2a6_* roles dropped)"
```

## Raw output

```text

## S1 (A1/C2): guard installed in a NON-public schema (t_p2a6); first stop by the runtime login sets version 1
t|stop-a|1
UPDATE 1

## S2 (A2): a second stop keeps the first by and version
t|stop-a|1
UPDATE 1

## S3 (A2): 1000 stops in one transaction, then the ORIGINAL token (1) still resets
DO
1

## S4: runtime login ON->OFF is refused (SQLSTATE 42501 and the fixed message)
ERROR:  42501: kill switch: only the reset role may clear it
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 7 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897

## S5: outsider login (no grant) is refused
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812

## S6: runtime INSERT, DELETE, TRUNCATE are denied
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812

## S7: stale token updates 0 rows
UPDATE 0

## S8 (A7): correct token succeeds; stored by is the LABEL not the typed text; one resets row written with the label
f|label-op|2
UPDATE 1
1|label-op|stop-a

## S9: runtime cannot update or delete the resets table
ERROR:  42501: permission denied for table kill_switch_resets
LOCATION:  aclcheck_error, aclchk.c:2812

## S10: breakglass login reset gets label 'breakglass'
3
UPDATE 1
breakglass|4
UPDATE 1
1|label-op
3|breakglass

## S11: an UNREGISTERED login, even a superuser, is refused (label test); superuser with session_replication_role=replica is still refused (state is ON)
5
UPDATE 1
ERROR:  42501: kill switch: login not registered
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 9 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897
SET
ERROR:  42501: kill switch: login not registered
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 9 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897

## S12 (A5): NOINHERIT member of the owner role: membership TRUE, USAGE FALSE, table privilege FALSE, yet it can disable the trigger
t|f|f
SET
ALTER TABLE
D

## S13 (A12): the runtime login can read tgenabled (D after the disable) and, after the owner re-enables with ENABLE ALWAYS, A
D
ALTER TABLE
A

## S14: CREATE OR REPLACE TRIGGER resets tgenabled to O (so migrate() must re-assert ENABLE ALWAYS)
CREATE TRIGGER
O
ALTER TABLE

## S15: the runtime can read prosecdef and proconfig (probe inputs)
t|{"search_path=pg_catalog, pg_temp"}

## S16: the runtime cannot create a function in the schema, cannot disable the trigger
ERROR:  42501: permission denied for schema t_p2a6
LOCATION:  aclcheck_error, aclchk.c:2812
ERROR:  42501: must be owner of table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2950

## S17 (A8): dry run as the runtime login in a rolled-back transaction: first UPDATE succeeds, second raises 42501 with the fixed message
BEGIN
UPDATE 1
ERROR:  42501: kill switch: only the reset role may clear it
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 7 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897

## S18 (A8): a lost UPDATE grant also gives 42501 but with a DIFFERENT message (so the probe must match the message AND need the first UPDATE to succeed)
REVOKE
BEGIN
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812
GRANT

## S19: group NULL refuses with the fixed 42501 message; a group naming a missing role, or the empty string, raises 42704 (role does not exist) and still refuses
UPDATE 1
ERROR:  42501: kill switch: only the reset role may clear it
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 7 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897
UPDATE 1
ERROR:  42704: role "nosuchrole" does not exist
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 6 at IF
LOCATION:  get_role_oid, acl.c:5271
UPDATE 1
ERROR:  42704: role "" does not exist
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 6 at IF
LOCATION:  get_role_oid, acl.c:5271
UPDATE 1

## S20 (A9/C8): set_config with an integer argument fails (42883); with text it works; inside a transaction (autocommit needs one)
ERROR:  42883: function set_config(unknown, integer, boolean) does not exist
LINE 1: select set_config('lock_timeout', 1000, true)
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
LOCATION:  ParseFuncOrColumn, parse_func.c:629
BEGIN
1s
1s
COMMIT

## S21 (A10): a session holding FOR UPDATE makes a stop fail with 55P03 after lock_timeout
BEGIN
1s
ERROR:  55P03: canceling statement due to lock timeout
CONTEXT:  while locking tuple (8,45) in relation "kill_switch"
LOCATION:  ProcessInterrupts, postgres.c:3411

## S22 (A3): old core upsert (INSERT ... ON CONFLICT) fails without INSERT, works after GRANT INSERT
ERROR:  42501: permission denied for table kill_switch
LOCATION:  aclcheck_error, aclchk.c:2812
GRANT
t|again2|5
INSERT 0 1
ERROR:  42501: kill switch: only the reset role may clear it
CONTEXT:  PL/pgSQL function t_p2a6.hadavin_kill_switch_guard() line 7 at RAISE
LOCATION:  exec_stmt_raise, pl_exec.c:3897
REVOKE

## S23 (A3): the recipe lock text: pg_advisory_xact_lock with the migrate lock key
BEGIN

GRANT
ROLLBACK

## S24 (A14): a missing row. Superuser deletes it; a stop UPDATE affects 0 rows; re-seed as ON then a registered login resets with the new token
DELETE 1
UPDATE 0
t|7
INSERT 0 1
f|label-op|8
UPDATE 1

## S25: stored group value and ownership: the function and tables are owned by the migrator, not the runtime
p2a6_grp
kill_switch|p2a6_mig
kill_switch_guard_config|p2a6_mig
kill_switch_login_labels|p2a6_mig
kill_switch_resets|p2a6_mig
p2a6_mig

## S26: function text installed (schema name is an identifier built by the migrator; no public. anywhere)
0|109|t

## S27 (A1 negative control): the same function text hard-coded to public.* in this non-public schema raises 'relation does not exist' (SQLSTATE 42P01), not 42501
ERROR:  42P01: relation "public.kill_switch_guard_config" does not exist
LINE 1: select reset_group          from public.kill_switch_guard_co...
                                         ^
QUERY:  select reset_group          from public.kill_switch_guard_config where id=1
CONTEXT:  PL/pgSQL function t_bad.g() line 1 at SQL statement
LOCATION:  parserOpenTable, parse_relation.c:1428

## S28: PostgreSQL version
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit

## cleanup done (database and p2a6_* roles dropped)
```
