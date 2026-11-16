#!/bin/bash
# c6u run_all.sh. Order matters: the owner sheets may still be written by another agent, so check, snapshot, build, verify and negative controls run in one go.
# INPUTS (each missing one stops the run with one line naming it):
#   C6U_TREE   = the folder 'handover' of the copied demo tree (the audited demo files); you set it, there is no default.
#   C6U_STEPS  = optional: another copy of steps-edits (default: ../../steps-edits next to c6-skip-audit).
#   the whole core-hardening folder (this script sits in core-hardening/c6-skip-audit/evidence-c6u), and tests/test_no_reference_material.py of the repository (the list of banned names is read from it at run time).
set -u
E="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$(cd "$E/../.." && pwd)"
R="$(cd "$H/../.." && pwd)"
S=${C6U_STEPS:-$H/steps-edits}
miss=0
need() { if [ ! -e "$1" ]; then echo "MISSING INPUT: $2"; miss=1; fi; }
if [ -z "${C6U_TREE:-}" ]; then echo "MISSING INPUT: C6U_TREE is not set (the 'handover' folder of the copied demo tree)"; miss=1; else need "$C6U_TREE" "C6U_TREE points at a folder that does not exist"; fi
need "$H/ORDERS.md" "core-hardening/ORDERS.md"
need "$H/REPORT.md" "core-hardening/REPORT.md"
need "$H/inputs" "core-hardening/inputs/ (the whole core-hardening tree is needed)"
need "$S" "steps-edits folder (C6U_STEPS or core-hardening/steps-edits)"
need "$R/tests/test_no_reference_material.py" "tests/test_no_reference_material.py (the list of banned names)"
need "$H/c6-skip-audit/REPORT-c6t.md" "c6-skip-audit/REPORT-c6t.md (the report the build starts from)"
if [ "$miss" -ne 0 ]; then echo "run_all.sh stopped: fix the missing input(s) above"; exit 2; fi
export C6U_TREE C6U_STEPS="$S"
cd "$E"
bash static-checks.sh > static-checks-output.txt 2>&1; echo "static-checks exit $?"
rm -rf "$E/steps-snapshot" && mkdir "$E/steps-snapshot" && cp -p "$S"/OWNER-SHEET-v*.md "$S"/LEAD-RELEASE-NOTE-v*.md "$E/steps-snapshot"/
python3 -B -I build_c6u.py || exit 1
python3 -B -I verify-c6u.py > verify-c6u-output.txt 2>&1; vrc=$?; echo "verify exit $vrc"; tail -n 1 verify-c6u-output.txt | cut -c1-200
C6U_SNAPSHOT="$E/steps-snapshot" C6U_STEPS="$E/steps-snapshot" python3 -B -I neg_controls_c6u.py > /dev/null 2>&1; nrc=$?; echo "neg exit $nrc"; tail -n 1 neg-output.txt
[ "$vrc" -eq 0 ] && [ "$nrc" -eq 0 ]
