#!/usr/bin/env bash
# v17: private throwaway cluster, scram-sha-256 only, unix socket only. Usage: bash run_pg_v17.sh <out_dir> <python> <src_dir> <script.py> <outfile> [held-v17] [held-v16]
set -u
OUT="${1:?out}"; PY="${2:?python}"; SRC="${3:?src}"; SCRIPT="${4:?script}"; OUTF="${5:?outfile}"
HERE="$(cd "$(dirname "$0")" && pwd)"; H17="${6:-$HERE/held-sql}"; H16="${7:-$HERE/../evidence-handoff-v16/held-sql}"
PGB=/usr/lib/postgresql/16/bin; D=/var/lib/postgresql/hadavin_v17_$$
export HV_ADMIN_PW="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
PWF="$(mktemp)"; chmod 644 "$PWF"; printf '%s' "$HV_ADMIN_PW" > "$PWF"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -U postgres -A scram-sha-256 --pwfile=$PWF -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { rm -f "$PWF"; echo "cluster did not start"; exit 1; }
rm -f "$PWF"
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
PGPASSWORD="$HV_ADMIN_PW" psql -X -h $D -U postgres -d postgres -At -c "select version()" > "$OUT/raw-pg-version-$OUTF"
"$PY" -I -B "$HERE/$SCRIPT" "$D" "$SRC" "$H17" "$H16" > "$OUT/$OUTF" 2>&1; echo "rc=$?" >> "$OUT/$OUTF"
echo done
