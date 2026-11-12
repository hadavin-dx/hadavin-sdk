#!/bin/bash
# Run BEFORE every timed run. Writes the sample into $1 (a file). Exit 0 = quiet, exit 3 = another lane is running: STOP, wait, retry.
OUT=${1:-quiet.txt}
{ date -u +%FT%TZ; nproc; uptime; top -bn1 | head -15; } > "$OUT" 2>&1
# other pytest/node/docker/playwright processes that are not ours
OTHER=$(ps -eo pid,pcpu,args --sort=-pcpu | grep -E 'pytest|playwright|chromium' | grep -v grep | grep -v "$$" | head -5)
LOAD=$(cut -d' ' -f1 /proc/loadavg)
echo "load1=$LOAD" >> "$OUT"; echo "other=$OTHER" >> "$OUT"
# quiet = nothing test-like running and 1-minute load below 1.0
if [ -n "$OTHER" ] || awk "BEGIN{exit !($LOAD >= 1.0)}"; then echo "NOT QUIET: see $OUT"; exit 3; fi
echo "quiet"
