#!/usr/bin/env bash
# Independent test of the three held SQL files. usage: suite_indep.sh <dir with the 3 sql files> <label>
# Needs the throwaway cluster of start_cluster.sh. Prints PASS/FAIL per check, then "SUMMARY pass=N fail=M". Exit 0 only if fail=0.
SQLDIR="$1"; LABEL="$2"
D=/var/lib/postgresql/hadavin_v15_indep
MIGD=/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations
DB="d_${LABEL}"; FB="f_${LABEL}"; LB="l_${LABEL}"
P=0; F=0
ps() { local role="$1" db="$2"; shift 2; runuser -u postgres -- psql -X -h $D -U "$role" -d "$db" -At -v VERBOSITY=sqlstate "$@" 2>&1; }
# q ROLE DB SQL  -> output (stdin script)
q() { local role="$1" db="$2" sqltext="$3"; printf '%s\n' "$sqltext" | ps "$role" "$db"; }
ok()   { P=$((P+1)); echo "PASS $1"; }
bad()  { F=$((F+1)); echo "FAIL $1  [$2]"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "got '$2' want '$3'"; fi; }
err()  { # name, role, db, sql, sqlstate
  local out; out=$(q "$2" "$3" "$4"); if printf '%s' "$out" | grep -q "^ERROR:  $5\$"; then ok "$1"; else bad "$1" "want $5; got: $(printf '%s' "$out" | tr '\n' ' ' | cut -c1-120)"; fi; }
noerr(){ local out; out=$(q "$2" "$3" "$4"); if printf '%s' "$out" | grep -q "^ERROR"; then bad "$1" "$(printf '%s' "$out" | tr '\n' ' ' | cut -c1-120)"; else ok "$1"; fi; }
val()  { q "$1" "$2" "$3" | tr -d '\n'; }
adm()  { runuser -u postgres -- psql -X -h $D -d postgres -qAt -c "$1" 2>&1; }
mkdb() { adm "DROP DATABASE IF EXISTS $1" >/dev/null; adm "CREATE DATABASE $1 OWNER mig_ind" >/dev/null
  for f in $MIGD/000[1-5]*.sql; do runuser -u postgres -- psql -X -h $D -U mig_ind -d $1 -q -v ON_ERROR_STOP=1 -1 -f $f >/dev/null 2>/tmp/indep_mig_err_$LABEL || { echo "migration $f failed"; cat /tmp/indep_mig_err_$LABEL; }; done
  rm -f /tmp/indep_mig_err_$LABEL
  adm "REVOKE CONNECT ON DATABASE $1 FROM PUBLIC; GRANT CONNECT ON DATABASE $1 TO mig_ind, rt_ind, audrd_ind, nobody_ind" >/dev/null
  q mig_ind $1 "GRANT USAGE ON SCHEMA public TO rt_ind, audrd_ind, nobody_ind; GRANT SELECT, INSERT, UPDATE ON spend, spend_month TO rt_ind;" >/dev/null; }
applyf() { runuser -u postgres -- psql -X -h $D -U mig_ind -d "$1" -q -v ON_ERROR_STOP=1 -v VERBOSITY=sqlstate -1 -f "$SQLDIR/$2" 2>&1; }
seed() { q mig_ind $1 "INSERT INTO spend VALUES ('a1','2026-11-16',1.0),('a2','2026-11-16',5.0); INSERT INTO spend_month VALUES ('a1','2026-11-01',1.0),('a2','2026-11-01',5.0);" >/dev/null; }

# ============ DEFAULT FILE (DB-1 default) + DB-2 on database $DB
mkdb $DB; seed $DB
eq "M1 migration role is NOT superuser" "$(adm "select rolsuper::text||rolcreaterole::text||rolcreatedb::text||rolbypassrls::text from pg_roles where rolname='mig_ind'")" "falsefalsefalsefalse"
out=$(applyf $DB spend_nonneg.sql); eq "D0 default file applies as non-superuser (no output = ok)" "$out" ""
eq "D1 spend_usd_ok exists, def is usd >= 0" "$(val mig_ind $DB "select pg_get_constraintdef(oid) from pg_constraint where conname='spend_usd_ok' and conrelid='spend'::regclass")" "CHECK ((usd >= (0)::numeric))"
eq "D1b spend_month_usd_ok exists, def is usd >= 0" "$(val mig_ind $DB "select pg_get_constraintdef(oid) from pg_constraint where conname='spend_month_usd_ok' and conrelid='spend_month'::regclass")" "CHECK ((usd >= (0)::numeric))"
for T in "spend:day:2026-11-16" "spend_month:month:2026-11-01"; do IFS=: read tb col dv <<<"$T"
  err "D2 [$tb] negative INSERT ... ON CONFLICT DO UPDATE refused 23514 (new key)" rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('zz','$dv',-0.01) ON CONFLICT (agent_id,$col) DO UPDATE SET usd=$tb.usd+EXCLUDED.usd;" 23514
  err "D2b [$tb] negative INSERT ... ON CONFLICT DO UPDATE refused 23514 (existing key, row would end positive)" rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('a2','$dv',-1) ON CONFLICT (agent_id,$col) DO UPDATE SET usd=$tb.usd+EXCLUDED.usd;" 23514
  eq "D3 [$tb] negative delta via UPDATE ... RETURNING works (5.0 + -1.5 = 3.5)" "$(val rt_ind $DB "UPDATE $tb SET usd=usd+(-1.5) WHERE agent_id='a2' RETURNING usd;" | head -c 20)" "3.5UPDATE 1"
  err "D4 [$tb] UPDATE to a negative total refused 23514" rt_ind $DB "UPDATE $tb SET usd=usd-100 WHERE agent_id='a2';" 23514
  err "D4b [$tb] UPDATE to -Infinity refused 23514" rt_ind $DB "UPDATE $tb SET usd='-Infinity' WHERE agent_id='a2';" 23514
  err "D4c [$tb] INSERT -Infinity refused 23514" rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('zz','$dv','-Infinity');" 23514
  eq "D5 [$tb] UPDATE to exactly 0 allowed" "$(val rt_ind $DB "UPDATE $tb SET usd=0 WHERE agent_id='a1';")" "UPDATE 1"
  eq "D6 [$tb] default lets NaN in (documented)" "$(val rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('nan','$dv','NaN');")" "INSERT 0 1"
  eq "D7 [$tb] default lets Infinity in (documented)" "$(val rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('inf','$dv','Infinity');")" "INSERT 0 1"
  noerr "D8 [$tb] positive INSERT ok" rt_ind $DB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('pos','$dv',2.5);"
done
q mig_ind $DB "UPDATE spend SET usd=1.0 WHERE agent_id='a1'; UPDATE spend_month SET usd=1.0 WHERE agent_id='a1'; DELETE FROM spend WHERE agent_id IN ('nan','inf','pos'); DELETE FROM spend_month WHERE agent_id IN ('nan','inf','pos');" >/dev/null
eq "D9 default file text has SET LOCAL lock_timeout" "$(grep -c "^SET LOCAL lock_timeout = '5s';" $SQLDIR/spend_nonneg.sql)" "1"

# ---- DB-2 on the same database
out=$(applyf $DB spend_decrease_log.sql); eq "L0 DB-2 file applies as non-superuser (no output = ok)" "$out" ""
q mig_ind $DB "GRANT SELECT ON spend_decrease_log TO audrd_ind;" >/dev/null   # what the move PR's GRANTS entry would do (audit_read)
eq "L1 spend_log_decrease: SECURITY DEFINER" "$(val mig_ind $DB "select prosecdef::text from pg_proc where proname='spend_log_decrease'")" "true"
eq "L1b spend_log_decrease: search_path exactly pg_catalog, pg_temp (pg_temp last)" "$(val mig_ind $DB "select proconfig::text from pg_proc where proname='spend_log_decrease'")" '{"search_path=pg_catalog, pg_temp"}'
eq "L1c spend_keep_keys: search_path exactly pg_catalog, pg_temp" "$(val mig_ind $DB "select proconfig::text from pg_proc where proname='spend_keep_keys'")" '{"search_path=pg_catalog, pg_temp"}'
eq "L1d spend_keep_keys is NOT security definer" "$(val mig_ind $DB "select prosecdef::text from pg_proc where proname='spend_keep_keys'")" "false"
eq "L1e functions owned by the non-superuser migration role" "$(val mig_ind $DB "select string_agg(r.rolname||r.rolsuper::text, ',' order by p.proname) from pg_proc p join pg_roles r on r.oid=p.proowner where p.proname in ('spend_log_decrease','spend_keep_keys')")" "mig_indfalse,mig_indfalse"
eq "L2 PUBLIC has no EXECUTE on spend_log_decrease (no grantee 0 in proacl; acl present)" "$(val mig_ind $DB "select (proacl is not null)::text||(select count(*) from aclexplode(proacl) a where a.grantee=0) from pg_proc where proname='spend_log_decrease'")" "true0"
for r in rt_ind audrd_ind nobody_ind; do eq "L2b $r has no EXECUTE on spend_log_decrease" "$(val mig_ind $DB "select has_function_privilege('$r','spend_log_decrease()','EXECUTE')::text")" "false"; done
err "L2c role without privilege cannot call the function (42501)" nobody_ind $DB "SELECT spend_log_decrease();" 42501
err "L2d runtime role cannot call the function directly (42501)" rt_ind $DB "SELECT spend_log_decrease();" 42501
eq "L3 PUBLIC has no privilege on spend_decrease_log (grantee 0 absent from relacl)" "$(val mig_ind $DB "select count(*) from aclexplode((select relacl from pg_class where relname='spend_decrease_log')) a where a.grantee=0")" "0"
eq "L3b relacl of the log: only owner (all) and audrd (SELECT)" "$(val mig_ind $DB "select string_agg(g.rolname||':'||a.privilege_type, ',' order by g.rolname, a.privilege_type) from aclexplode((select relacl from pg_class where relname='spend_decrease_log')) a join pg_roles g on g.oid=a.grantee")" "audrd_ind:SELECT,mig_ind:DELETE,mig_ind:INSERT,mig_ind:REFERENCES,mig_ind:SELECT,mig_ind:TRIGGER,mig_ind:TRUNCATE,mig_ind:UPDATE"
eq "L3c index spend_decrease_log_by_agent on (agent_id, period, at)" "$(val mig_ind $DB "select indexdef from pg_indexes where indexname='spend_decrease_log_by_agent'" | sed 's/.*(//')" "agent_id, period, at)"
eq "L4 four triggers present on the two tables" "$(val mig_ind $DB "select string_agg(tgname,',' order by tgname) from pg_trigger where not tgisinternal and tgrelid in ('spend'::regclass,'spend_month'::regclass)")" "spend_keep_keys,spend_log_decrease,spend_month_keep_keys,spend_month_log_decrease"
cnt() { val mig_ind $DB "select count(*) from spend_decrease_log $1"; }
c0=$(cnt); eq "L5a log empty before any lowering" "$c0" "0"
q rt_ind $DB "UPDATE spend SET usd=usd-0.25 WHERE agent_id='a2' AND day='2026-11-16';" >/dev/null
eq "L5b lowering (day) writes exactly 1 row" "$(cnt)" "1"
eq "L5c row content (a2, 2026-11-16, spend, 3.5 -> 3.25, who=rt_ind)" "$(val mig_ind $DB "select agent_id||'|'||period||'|'||scope||'|'||old_usd||'|'||new_usd||'|'||who from spend_decrease_log")" "a2|2026-11-16|spend|3.5|3.25|rt_ind"
q rt_ind $DB "UPDATE spend_month SET usd=usd-1 WHERE agent_id='a2' AND month='2026-11-01';" >/dev/null
eq "L5d lowering (month) row content" "$(val mig_ind $DB "select agent_id||'|'||period||'|'||scope||'|'||old_usd||'|'||new_usd||'|'||who from spend_decrease_log where scope='spend_month'")" "a2|2026-11-01|spend_month|3.5|2.5|rt_ind"
n=$(cnt); q rt_ind $DB "UPDATE spend SET usd=usd+1 WHERE agent_id='a2';" >/dev/null; eq "L5e a raise writes no row" "$(cnt)" "$n"
q rt_ind $DB "UPDATE spend SET usd=usd WHERE agent_id='a2';" >/dev/null; eq "L5f an equal total writes no row" "$(cnt)" "$n"
q rt_ind $DB "UPDATE spend SET usd='NaN' WHERE agent_id='a2';" >/dev/null; eq "L5g total becoming NaN is logged" "$(cnt)" "$((n+1))"
q rt_ind $DB "UPDATE spend SET usd='NaN' WHERE agent_id='a2';" >/dev/null; eq "L5h NaN to NaN not logged" "$(cnt)" "$((n+1))"
q rt_ind $DB "UPDATE spend SET usd=1 WHERE agent_id='a2';" >/dev/null; eq "L5i NaN to 1 is a lowering (logged)" "$(cnt)" "$((n+2))"
q rt_ind $DB "UPDATE spend SET usd='Infinity' WHERE agent_id='a2';" >/dev/null; eq "L5j total becoming Infinity logged" "$(cnt)" "$((n+3))"
q rt_ind $DB "UPDATE spend SET usd='Infinity' WHERE agent_id='a2';" >/dev/null; eq "L5k Infinity to Infinity not logged" "$(cnt)" "$((n+3))"
eq "L5l rows with scope spend_month: exactly 1 so far" "$(cnt "where scope='spend_month'")" "1"
q rt_ind $DB "UPDATE spend_month SET usd='NaN' WHERE agent_id='a2';" >/dev/null; eq "L5m month table: becoming NaN logged" "$(cnt "where scope='spend_month'")" "2"
q rt_ind $DB "UPDATE spend SET usd=1.0 WHERE agent_id='a2'; UPDATE spend_month SET usd=1.0 WHERE agent_id='a2';" >/dev/null
for T in "spend:day:agent_id:'zz'" "spend:day:day:day-3650" "spend_month:month:agent_id:'zz'" "spend_month:month:month:(month - interval '1 month')::date"; do IFS=: read tb col key newv <<<"$T"
  err "K1 [$tb.$key] key column change refused 42501" rt_ind $DB "UPDATE $tb SET $key=$newv WHERE agent_id='a1';" 42501
done
eq "K2 key guard: usd-only update still works on both tables" "$(val rt_ind $DB "UPDATE spend SET usd=usd WHERE agent_id='a1'; UPDATE spend_month SET usd=usd WHERE agent_id='a1';" | tr -d '\n')" "UPDATE 1UPDATE 1"
eq "K3 key guard even for the table owner (trigger not role-specific)" "$(q mig_ind $DB "UPDATE spend SET agent_id='x' WHERE agent_id='a1';" | tr -d '\n')" "ERROR:  42501"
# temp-table attack: TEMP still allowed here (not yet revoked)
before=$(cnt)
out=$(q rt_ind $DB "CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz default now(), who text default 'x');
UPDATE spend SET usd=usd-0.1 WHERE agent_id='a1';
SELECT 'temprows='||count(*) FROM pg_temp.spend_decrease_log;")
eq "T1 temp-table attack: temp copy got 0 rows" "$(printf '%s' "$out" | grep -o 'temprows=[0-9]*')" "temprows=0"
eq "T1b temp-table attack: real log got the row" "$(cnt)" "$((before+1))"
# operator step: revoke TEMP
adm "REVOKE TEMPORARY ON DATABASE $DB FROM PUBLIC; GRANT TEMPORARY ON DATABASE $DB TO mig_ind;" >/dev/null
err "T2 after REVOKE TEMPORARY the runtime role cannot create a temp table (42501)" rt_ind $DB "CREATE TEMP TABLE t1(x int);" 42501
err "T2b audit reader cannot create a temp table (42501)" audrd_ind $DB "CREATE TEMP TABLE t1(x int);" 42501
noerr "T2c migration role still can" mig_ind $DB "CREATE TEMP TABLE t1(x int);"
eq "T2d lowering still logs after revoke" "$(q rt_ind $DB "UPDATE spend SET usd=usd-0.1 WHERE agent_id='a1';" >/dev/null; cnt)" "$((before+2))"
# runtime role has no rights on the log
for s in "SELECT * FROM spend_decrease_log" "INSERT INTO spend_decrease_log(agent_id,period,scope,old_usd,new_usd) VALUES ('x','2026-11-01','spend',1,0)" "UPDATE spend_decrease_log SET new_usd=1" "DELETE FROM spend_decrease_log" "TRUNCATE spend_decrease_log"; do
  err "R1 runtime role denied: ${s%% *} on the log" rt_ind $DB "$s;" 42501; done
# audit reader: SELECT only
eq "A1 audit reader can SELECT the log" "$(val audrd_ind $DB "select count(*)>0 from spend_decrease_log")" "t"
for s in "INSERT INTO spend_decrease_log(agent_id,period,scope,old_usd,new_usd) VALUES ('x','2026-11-01','spend',1,0)" "UPDATE spend_decrease_log SET new_usd=1" "DELETE FROM spend_decrease_log" "TRUNCATE spend_decrease_log" "SELECT * FROM spend" "SELECT * FROM spend_month" "SELECT * FROM kill_switch" "SELECT * FROM audit_entries" "SELECT * FROM runs" "UPDATE spend SET usd=0" "CREATE TABLE zz(x int)" "DROP TABLE spend_decrease_log" "ALTER TABLE spend DISABLE TRIGGER ALL"; do
  err "A2 audit reader denied: ${s:0:40}" audrd_ind $DB "$s;" 42501; done
eq "A3 audit reader table grants over the whole database = exactly SELECT on the log" "$(val mig_ind $DB "select string_agg(table_name||':'||privilege_type,',') from information_schema.role_table_grants where grantee='audrd_ind'")" "spend_decrease_log:SELECT"
eq "A3b audit reader has no column grants and no function EXECUTE except default PUBLIC ones on non-DB-2 functions" "$(val mig_ind $DB "select count(*) from information_schema.role_column_grants where grantee='audrd_ind' and table_name<>'spend_decrease_log'")" "0"
eq "A3c audit reader is in no other role" "$(val mig_ind $DB "select count(*) from pg_auth_members m join pg_roles r on r.oid=m.member where r.rolname='audrd_ind'")" "0"
# nobody
for s in "SELECT * FROM spend" "SELECT * FROM spend_decrease_log" "UPDATE spend SET usd=0" "INSERT INTO spend_decrease_log(agent_id,period,scope,old_usd,new_usd) VALUES ('x','2026-11-01','spend',1,0)"; do
  err "N1 role without privilege denied: ${s:0:40}" nobody_ind $DB "$s;" 42501; done
# lock timeout behaviour: hold a lock 9 s, apply default file on a second DB
mkdb $LB
( runuser -u postgres -- psql -X -h $D -U mig_ind -d $LB -q -c "BEGIN; LOCK TABLE spend IN ROW EXCLUSIVE MODE; SELECT pg_sleep(9); COMMIT;" >/dev/null 2>&1 & )
sleep 1; t0=$(date +%s.%N); out=$(applyf $LB spend_nonneg.sql); t1=$(date +%s.%N)
el=$(python3 -c "print(round($t1-$t0,1))")
if printf '%s' "$out" | grep -q "55P03" && python3 -c "import sys; sys.exit(0 if 4.5<=$el<=6.5 else 1)"; then ok "W1 held lock: default file fails 55P03 after about 5 s (${el}s)"; else bad "W1 lock timeout" "elapsed ${el}s out='$(printf '%s' "$out"|tr '\n' ' '|cut -c1-100)'"; fi
sleep 5
# W2: same lock test for the VARIANT file (added after run 1 showed no test caught a dropped lock_timeout in the variant)
LB2="w_${LABEL}"; mkdb $LB2
( runuser -u postgres -- psql -X -h $D -U mig_ind -d $LB2 -q -c "BEGIN; LOCK TABLE spend IN ROW EXCLUSIVE MODE; SELECT pg_sleep(9); COMMIT;" >/dev/null 2>&1 & )
sleep 1; t0=$(date +%s.%N); out=$(applyf $LB2 spend_nonneg_finite.sql); t1=$(date +%s.%N)
el=$(python3 -c "print(round($t1-$t0,1))")
if printf '%s' "$out" | grep -q "55P03" && python3 -c "import sys; sys.exit(0 if 4.5<=$el<=6.5 else 1)"; then ok "W2 held lock: variant file fails 55P03 after about 5 s (${el}s)"; else bad "W2 lock timeout (variant)" "elapsed ${el}s out='$(printf '%s' "$out"|tr '\n' ' '|cut -c1-100)'"; fi
eq "W2b variant file text has SET LOCAL lock_timeout" "$(grep -c "^SET LOCAL lock_timeout = '5s';" $SQLDIR/spend_nonneg_finite.sql)" "1"
sleep 5

# ============ VARIANT on database $FB
mkdb $FB; seed $FB
out=$(applyf $FB spend_nonneg_finite.sql); eq "V0 variant applies as non-superuser" "$out" ""
eq "V1 constraint definitions mention usd < Infinity on both tables" "$(val mig_ind $FB "select count(*) from pg_constraint where conname in ('spend_usd_ok','spend_month_usd_ok') and pg_get_constraintdef(oid) like '%Infinity%' and pg_get_constraintdef(oid) like '%>= (0)::numeric%' and pg_get_constraintdef(oid) like '%AND%'")" "2"
for T in "spend:day:2026-11-16" "spend_month:month:2026-11-01"; do IFS=: read tb col dv <<<"$T"
  for bv in "-0.01" "NaN" "Infinity" "-Infinity"; do
    err "V2 [$tb] INSERT ON CONFLICT $bv refused 23514" rt_ind $FB "INSERT INTO $tb(agent_id,$col,usd) VALUES ('v$RANDOM','$dv','$bv') ON CONFLICT (agent_id,$col) DO UPDATE SET usd=$tb.usd+EXCLUDED.usd;" 23514
    err "V3 [$tb] UPDATE to $bv refused 23514" rt_ind $FB "UPDATE $tb SET usd='$bv' WHERE agent_id='a2';" 23514
  done
  noerr "V4 [$tb] 0 allowed" rt_ind $FB "UPDATE $tb SET usd=0 WHERE agent_id='a1';"
  noerr "V4b [$tb] 1234567.89 allowed" rt_ind $FB "UPDATE $tb SET usd=1234567.89 WHERE agent_id='a2';"
  eq "V5 [$tb] negative delta via UPDATE RETURNING works" "$(val rt_ind $FB "UPDATE $tb SET usd=usd+(-0.89) WHERE agent_id='a2' RETURNING usd;" | head -c 10)" "1234567.00"
done
# both files together refused
out=$(applyf $FB spend_nonneg.sql); if printf '%s' "$out" | grep -q "42710"; then ok "V6 applying the default over the variant is refused (42710 duplicate constraint)"; else bad "V6" "$out"; fi
# DB-2 on variant DB too
out=$(applyf $FB spend_decrease_log.sql); eq "V7 DB-2 applies on top of the variant" "$out" ""
q rt_ind $FB "UPDATE spend SET usd=usd-1 WHERE agent_id='a2';" >/dev/null
eq "V7b lowering logged on variant DB" "$(val mig_ind $FB "select count(*) from spend_decrease_log")" "1"

adm "DROP DATABASE IF EXISTS $DB" >/dev/null; adm "DROP DATABASE IF EXISTS $FB" >/dev/null; adm "DROP DATABASE IF EXISTS $LB" >/dev/null; adm "DROP DATABASE IF EXISTS $LB2" >/dev/null
echo "SUMMARY pass=$P fail=$F"
[ $F -eq 0 ]
