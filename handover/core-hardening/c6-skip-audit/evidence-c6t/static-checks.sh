#!/bin/bash
# c6t: C-10c rerun over every owner sheet v19 and later (all variants), with the check time, the newest sheet and the newest release note named, and the
# modification time of every v28 to v30 sheet and of every release note v13 and later. Output: static-checks-output.txt. Paths are relative to this
# folder (c6-skip-audit/evidence-c6t -> ../../steps-edits), so the script runs on a copy of the whole c6-skip-audit and core-hardening layout.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$(cd "$HERE/../.." && pwd)"
S=${C6T_STEPS:-$H/steps-edits}
echo "## check time (UTC): $(date -u +%FT%TZ)"
echo "## C-10c: owner sheets, hits per phrase (grep -c -i: never deletes / read, create and change only / does not delete / read-only or read only any mention)"
for f in $(ls $S/OWNER-SHEET-v19.md $S/OWNER-SHEET-v[2-9][0-9]*.md 2>/dev/null); do
  echo "$(basename $f): $(grep -c -i 'never deletes' $f) / $(grep -c -i 'read, create and change only' $f) / $(grep -c -i 'does not delete' $f) / $(grep -c -i -E 'read-only|read only' $f)"; done
echo "## newest owner sheet by modification time (UTC), at the check time"; ls -l --time-style=+%FT%TZ $S | grep OWNER-SHEET | sort -k6 | tail -3 | awk '{print $6, $7}'
echo "## ORDERS: L-23NOV line and Q25 and Q27 lines"; grep -n -E "L-23NOV|^Q25|^Q27" $H/ORDERS.md | cut -c1-200
echo "## owner sheets with a version number above 30 (v31 or later)?"; ls $S | grep -E "OWNER-SHEET-v(3[1-9]|[4-9][0-9])" || echo "none on disk at the check time"
echo "## modification time of every v28, v29 and v30 file (UTC)"; ls -l --time-style=+%FT%TZ $S | grep -E 'OWNER-SHEET-v(28|29|30)' | awk '{print $6, $7}'
echo "## release notes: newest version on disk (LEAD-RELEASE-NOTE-v*.md, not SOURCE)"; ls $S | grep -E '^LEAD-RELEASE-NOTE-v[0-9]+\.md$' | sort -V | tail -1
echo "## modification time of every release note v13 and later (UTC)"; ls -l --time-style=+%FT%TZ $S | grep -E 'LEAD-RELEASE-NOTE-v(1[3-9]|[2-9][0-9])' | awk '{print $6, $7}'
echo "## G12 rows in the newest release note (grep -n)"; grep -n 'G12' $S/$(ls $S | grep -E '^LEAD-RELEASE-NOTE-v[0-9]+\.md$' | sort -V | tail -1) | cut -c1-200
echo "## the release note lines the report cites (LRN14:8, :33, :149, :150), first 60 characters"; for n in 8 33 149 150; do echo "$n: $(sed -n ${n}p $S/LEAD-RELEASE-NOTE-v14.md | cut -c1-60)"; done
