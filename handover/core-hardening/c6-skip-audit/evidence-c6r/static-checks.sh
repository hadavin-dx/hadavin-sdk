#!/bin/bash
# c6r: C-10c rerun over every owner sheet v19 to v29 (all variants), with the check time and the newest file named. Output: static-checks-output.txt (run from this folder)
H=/home/user/hadavin-sdk/handover/core-hardening
S=$H/steps-edits
echo "## check time (UTC): $(date -u +%FT%TZ)"
echo "## C-10c: owner sheets, hits per phrase (grep -c -i: never deletes / read, create and change only / does not delete / read-only or read only any mention)"
for f in $(ls $S/OWNER-SHEET-v19.md $S/OWNER-SHEET-v2[0-9]*.md 2>/dev/null); do
  echo "$(basename $f): $(grep -c -i 'never deletes' $f) / $(grep -c -i 'read, create and change only' $f) / $(grep -c -i 'does not delete' $f) / $(grep -c -i -E 'read-only|read only' $f)"; done
echo "## newest owner sheet by modification time (UTC), at the check time"; ls -l --time-style=+%FT%TZ $S | grep OWNER-SHEET | sort -k6 | tail -3 | awk '{print $6, $7}'
echo "## v28 A and B: owner deletes by hand present (count of 'delete' lines)"; for f in $S/OWNER-SHEET-v28-A.md $S/OWNER-SHEET-v28-B.md; do echo "$(basename $f): $(grep -c -i 'delete' $f)"; done
echo "## ORDERS: L-23NOV line and Q25 and Q27 lines"; grep -n -E "L-23NOV|^Q25|^Q27" $H/ORDERS.md | cut -c1-200
echo "## all owner-sheet files newer than v29 (v30 or later)?"; ls $S | grep -E "OWNER-SHEET-v([3-9][0-9])" || echo "none on disk at the check time"
echo "## modification time of every v28 and v29 file (UTC)"; ls -l --time-style=+%FT%TZ $S | grep -E 'OWNER-SHEET-v2[89]' | awk '{print $6, $7}'
