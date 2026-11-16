#!/bin/bash
# f8-r11: repeat-run test. Runs run_all.sh N times in a row (default 5; one at a time, a full run takes about 4 minutes) and requires the same exit status and the same summary lines every time.
# Usage: bash repeat_run_all.sh [N] [OUTDIR (must not exist)]    Detach it for N > 5 (a background task is stopped after about 30 minutes).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
N=${1:-5}; [[ $N =~ ^[0-9]+$ ]] && [ "$N" -ge 2 ] || { echo "usage: bash repeat_run_all.sh [N>=2] [OUTDIR]"; exit 2; }
if [ -n "${2:-}" ]; then [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }; O=$2; mkdir -p -- "$O" || exit 2; else O=$(mktemp -d "${TMPDIR:-/tmp}/rep.XXXXXX") || exit 2; fi
echo "outputs in $O"
for i in $(seq 1 "$N"); do
  bash "$HERE/run_all.sh" > "$O/run-$i.txt" 2>&1; echo $? > "$O/run-$i.rc"
  # the lines that carry the result (case counts, exit statuses, open decisions); folder names and times are removed
  grep -E '^(\[selftest exit=|COUNTS |COUNT DRIFT|\[take_check.sh exit=|run_all exit status|OPEN LEAD DECISIONS|exit=|RESULT)' "$O/run-$i.txt" > "$O/sum-$i.txt"
  echo "run $i: exit $(cat "$O/run-$i.rc"), $(wc -l < "$O/sum-$i.txt") summary lines"
done
BAD=0
for i in $(seq 2 "$N"); do
  cmp -s "$O/sum-1.txt" "$O/sum-$i.txt" && [ "$(cat "$O/run-1.rc")" = "$(cat "$O/run-$i.rc")" ] || { echo "DIFFERENT: run $i differs from run 1"; BAD=$((BAD+1)); }
done
[ "$(cat "$O/run-1.rc")" = 0 ] || { echo "run 1 did not exit 0"; BAD=$((BAD+1)); }
[ -s "$O/sum-1.txt" ] || { echo "no summary lines found in run 1"; BAD=$((BAD+1)); }
echo "repeat_run_all: $N runs, $BAD problems"; cat "$O/sum-1.txt"
[ "$BAD" = 0 ]
