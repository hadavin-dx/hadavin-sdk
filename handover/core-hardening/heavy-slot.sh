#!/bin/sh
# heavy-slot.sh: run ONE heavy command (full test suite, mutation run, 40+ plant run, Postgres suite) in one of 3 slots.
# Usage: sh heavy-slot.sh <command> [args...]
# Waits up to 25 minutes for a free slot (checks every 10 s), then runs the command and frees the slot when it ends.
# Light work (reading, writing, small checks, one test file) does not need a slot.
i=0
while [ "$i" -lt 150 ]; do
  for n in 1 2 3; do
    exec 9>"/tmp/core-hardening-slot-$n.lock"
    if flock -n 9; then
      echo "heavy-slot: slot $n taken at $(date -u +%FT%TZ)" >&2
      "$@"; rc=$?
      echo "heavy-slot: slot $n freed, exit $rc" >&2
      exit "$rc"
    fi
    exec 9>&-
  done
  i=$((i+1)); sleep 10
done
echo "heavy-slot: no free slot after 25 minutes, command NOT run" >&2
exit 75
