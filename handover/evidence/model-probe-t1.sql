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
