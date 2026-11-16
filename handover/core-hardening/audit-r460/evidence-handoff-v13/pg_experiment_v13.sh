#!/usr/bin/env bash
# Throwaway-Postgres experiment for hand-off v13 (B1, M1, M3 of the v12 reviews). Runs ONLY against a private
# cluster that this script starts under the `postgres` operating-system user, on a unix socket (no network port),
# in a folder it creates and deletes. It touches no other database. Usage: bash pg_experiment_v13.sh <out_dir>
# No secrets, no real data. Roles are throwaway and die with the cluster.
set -u
OUT="${1:?output folder}"
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hadavin_v13_exp
mkdir -p "$OUT"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -A trust -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { echo "cluster did not start"; exit 1; }
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
P() { runuser -u postgres -- psql -X -v ON_ERROR_STOP=0 -h $D -d "$1" -f "$2"; }
runuser -u postgres -- psql -X -h $D -d postgres -c "select version()" -At > "$OUT/raw-pg-version-v13.txt"
runuser -u postgres -- psql -X -h $D -d postgres -c "create database exp" >/dev/null
for f in "$@"; do :; done
HERE="$(cd "$(dirname "$0")" && pwd)"
for n in b1 m1 m3; do
  cp "$HERE/pg_$n.sql" "$D/pg_$n.sql"; chown postgres "$D/pg_$n.sql"
  P exp "$D/pg_$n.sql" > "$OUT/raw-pg-$n-v13.txt" 2>&1
  runuser -u postgres -- psql -X -h $D -d postgres -c "drop database exp" -c "create database exp" >/dev/null
done
echo done
