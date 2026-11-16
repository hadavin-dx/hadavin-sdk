#!/usr/bin/env bash
# EVIDENCE RUNNER (independent of the builder). Own scratch cluster, scram-sha-256 only, unix socket only, random passwords never printed.
# Usage: bash run_ind16.sh <out_dir> <python> <src_dir> <held_dir> <scratch_dir> [mode]   (mode: main | mut)
set -u
OUT="${1:?out}"; PY="${2:?python}"; SRC="${3:?src}"; HELD="${4:?held}"; SCR="${5:?scratch}"; MODE="${6:-main}"
PGB=/usr/lib/postgresql/16/bin
D=/var/lib/postgresql/hv16ind_$MODE
HERE="$(cd "$(dirname "$0")" && pwd)"
export HV_ADMIN_PW="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
PWF="$(mktemp)"; chmod 644 "$PWF"; printf '%s' "$HV_ADMIN_PW" > "$PWF"
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -U postgres -A scram-sha-256 --pwfile=$PWF -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" || { rm -f "$PWF"; echo "cluster did not start"; exit 1; }
rm -f "$PWF"
trap 'runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D' EXIT
PGPASSWORD="$HV_ADMIN_PW" psql -X -h $D -U postgres -d postgres -At -c "select version()" > "$OUT/raw-ind16-pg-version-$MODE.txt"
if [ "$MODE" = main ]; then
  "$PY" -I -B "$HERE/ind16.py" "$D" "$SRC" "$HELD" "$SCR" main > "$OUT/raw-ind16-main.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-ind16-main.txt"
else
  "$PY" -I -B "$HERE/ind16.py" "$D" "$SRC" "$HELD" "$SCR" mut > "$OUT/raw-ind16-mutations.txt" 2>&1; echo "rc=$?" >> "$OUT/raw-ind16-mutations.txt"
fi
echo done
