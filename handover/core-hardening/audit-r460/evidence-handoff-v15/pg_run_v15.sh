#!/usr/bin/env bash
# v15: private throwaway cluster (unix socket only, own folder, deleted after). Usage: bash pg_run_v15.sh <out_dir> <python> <src_dir>
set -u
OUT="${1:?out}"; PY="${2:?python}"; SRC="${3:?src}"
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hadavin_v15_exp
HERE="$(cd "$(dirname "$0")" && pwd)"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -A trust -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { echo "cluster did not start"; exit 1; }
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
runuser -u postgres -- psql -X -h $D -d postgres -At -c "select version()" > "$OUT/raw-pg-version-v15.txt"
"$PY" -I -B "$HERE/pg_v15.py" "$D" "$SRC" > "$OUT/raw-pg-v15.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-pg-v15.txt"
echo done
