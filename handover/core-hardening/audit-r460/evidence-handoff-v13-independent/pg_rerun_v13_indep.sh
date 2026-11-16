#!/usr/bin/env bash
# Independent re-run (v13) of the builder's Postgres experiments. Private scratch cluster owned by the `postgres` OS user,
# unix socket only (no network port), folder created and deleted here. Touches no other database. No secrets.
# usage: bash pg_rerun_v13_indep.sh <sql_dir> <out_dir>
set -u
SQL="$1"; OUT="$2"
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hadavin_v13_indep_scratch
mkdir -p "$OUT"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -A trust -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { echo "cluster did not start"; exit 1; }
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
runuser -u postgres -- psql -X -h $D -d postgres -At -c "select version()" > "$OUT/raw-pg-version-indep.txt"
for n in b1 m1 m3; do
  runuser -u postgres -- psql -X -h $D -d postgres -c "create database exp_$n" >/dev/null
  cp "$SQL/pg_$n.sql" "$D/pg_$n.sql"; chown postgres "$D/pg_$n.sql"
  runuser -u postgres -- psql -X -v ON_ERROR_STOP=0 -h $D -d exp_$n -f "$D/pg_$n.sql" > "$OUT/raw-pg-$n-indep.txt" 2>&1
done
echo done
