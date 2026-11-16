#!/bin/bash
# Order matters: the owner sheets are still being written by another agent, so check, snapshot, build, verify and negative controls run in one go.
set -u
E=/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/evidence-c6s
S=/home/user/hadavin-sdk/handover/core-hardening/steps-edits
cd "$E"
bash static-checks.sh > static-checks-output.txt 2>&1
rm -rf "$E/steps-snapshot" && mkdir "$E/steps-snapshot" && cp -p "$S"/OWNER-SHEET-v*.md "$S"/LEAD-RELEASE-NOTE-v*.md "$E/steps-snapshot"/
python3 -B -I build_c6s.py || exit 1
python3 -B -I verify-c6s.py > verify-c6s-output.txt 2>&1; echo "verify exit $?"; tail -n 1 verify-c6s-output.txt | cut -c1-200
C6S_SNAPSHOT="$E/steps-snapshot" C6S_STEPS="$E/steps-snapshot" python3 -B -I neg_controls_c6s.py > /dev/null 2>&1; echo "neg exit $?"; tail -n 1 neg-output.txt
