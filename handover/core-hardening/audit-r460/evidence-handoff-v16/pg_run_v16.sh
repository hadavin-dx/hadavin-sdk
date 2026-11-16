#!/usr/bin/env bash
# v16: private throwaway cluster, PASSWORD authentication (scram-sha-256 for every connection, no trust), unix socket only.
# Usage: bash pg_run_v16.sh <out_dir> <python> <src_dir> <run_number>. Passwords are random, never printed.
set -u
OUT="${1:?out}"; PY="${2:?python}"; SRC="${3:?src}"; N="${4:?run number}"
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hadavin_v16_exp$N
HERE="$(cd "$(dirname "$0")" && pwd)"
export HV_ADMIN_PW="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
PWF="$(mktemp)"; chmod 644 "$PWF"; printf '%s' "$HV_ADMIN_PW" > "$PWF"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -U postgres -A scram-sha-256 --pwfile=$PWF -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { rm -f "$PWF"; echo "cluster did not start"; exit 1; }
rm -f "$PWF"
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
PGPASSWORD="$HV_ADMIN_PW" psql -X -h $D -U postgres -d postgres -At -c "select version()" > "$OUT/raw-pg-version-v16.txt"
"$PY" -I -B "$HERE/pg_v16.py" "$D" "$SRC" > "$OUT/raw-pg-v16-run$N.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-pg-v16-run$N.txt"
echo done
