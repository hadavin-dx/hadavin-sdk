#!/usr/bin/env bash
# Independent v14 run. Own scratch cluster owned by the `postgres` OS user, unix socket only, folder created and deleted here.
# usage: bash pg_rerun_v14_indep.sh <audit_dir> <out_dir>   (audit_dir = .../audit-r460)
set -u
A="$1"; OUT="$2"; ROOT=/home/user/hadavin-sdk; PY=$ROOT/.venv/bin/python
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hadavin_v14_indep_scratch
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -A trust -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { echo "cluster did not start"; exit 1; }
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
export PYTHONDONTWRITEBYTECODE=1
runuser -u postgres -- psql -X -h $D -d postgres -At -c "select version()" > "$OUT/raw-pg-version-indep-v14.txt"
E=$A/evidence-handoff-v14
for n in b1 tmp m3; do
  runuser -u postgres -- psql -X -h $D -d postgres -c "create database exp" >/dev/null   # builder's SQL files name the database exp
  cp "$E/pg_$n.sql" "$D/pg_$n.sql"; cp "$E"/held-sql/*.sql "$D/"; chown postgres "$D"/*.sql
  (cd $D && runuser -u postgres -- psql -X -v ON_ERROR_STOP=0 -h $D -d exp -f "$D/pg_$n.sql") > "$OUT/raw-pg-$n-indep-v14.txt" 2>&1
  runuser -u postgres -- psql -X -h $D -d postgres -c "drop database exp" >/dev/null
done
# builder's real-code script re-run, unmodified, on my cluster
"$PY" -I "$E/pg_real_code_v14.py" "$D" "$ROOT/src" > "$OUT/raw-pg-real-code-indep-v14.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-pg-real-code-indep-v14.txt"
# my own checks (own roles/databases; builder script used different names)
"$PY" -I "$OUT/pg_indep_v14.py" "$D" "$ROOT/src" "$E/held-sql" "$A/evidence-handoff-v13/held-sql" > "$OUT/raw-pg-own-checks-v14.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-pg-own-checks-v14.txt"
echo done
