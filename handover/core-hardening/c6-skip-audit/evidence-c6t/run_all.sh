#!/bin/bash
# Order matters: the owner sheets may still be written by another agent, so check, snapshot, build, verify and negative controls run in one go.
# All paths are relative to this script's own folder (c6-skip-audit/evidence-c6t), so it runs on a copy of the folder layout (C6T_STEPS may point at a copy of steps-edits).
set -u
E="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$(cd "$E/../.." && pwd)"
S=${C6T_STEPS:-$H/steps-edits}
cd "$E"
bash static-checks.sh > static-checks-output.txt 2>&1
rm -rf "$E/steps-snapshot" && mkdir "$E/steps-snapshot" && cp -p "$S"/OWNER-SHEET-v*.md "$S"/LEAD-RELEASE-NOTE-v*.md "$E/steps-snapshot"/
python3 -B -I build_c6t.py || exit 1
python3 -B -I verify-c6t.py > verify-c6t-output.txt 2>&1; echo "verify exit $?"; tail -n 1 verify-c6t-output.txt | cut -c1-200
C6T_SNAPSHOT="$E/steps-snapshot" C6T_STEPS="$E/steps-snapshot" python3 -B -I neg_controls_c6t.py > /dev/null 2>&1; echo "neg exit $?"; tail -n 1 neg-output.txt
