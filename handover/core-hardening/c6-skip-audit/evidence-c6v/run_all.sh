#!/bin/bash
# c6v run_all.sh. Order matters: the owner sheets may still be written by another agent, so check, snapshot, build, verify and negative controls run in one go.
# INPUTS (each missing one stops the run with one line naming it):
#   C6V_TREE   = the folder 'handover' of the copied demo tree (the audited demo files); you set it, there is no default.
#   C6V_STEPS  = optional: another copy of steps-edits (default: ../../steps-edits next to c6-skip-audit).
#   the whole core-hardening folder (this script sits in core-hardening/c6-skip-audit/evidence-c6v), and tests/test_no_reference_material.py of the repository (the list of banned names is read from it at run time).
set -u
E="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$(cd "$E/../.." && pwd)"
R="$(cd "$H/../.." && pwd)"
S=${C6V_STEPS:-$H/steps-edits}
miss=0
need() { if [ ! -e "$1" ]; then echo "MISSING INPUT: $2"; miss=1; fi; }
C6V_TREE="${C6V_TREE:-$E/tree/handover}"; need "$C6V_TREE/demo/VIDEO-RUNSHEET.md" "C6V_TREE (default: the 24 audited files shipped in evidence-c6v/tree/handover) has no demo/VIDEO-RUNSHEET.md"
need "$H/ORDERS.md" "core-hardening/ORDERS.md"
need "$H/REPORT.md" "core-hardening/REPORT.md"
need "$H/inputs" "core-hardening/inputs/ (the whole core-hardening tree is needed)"
need "$S" "steps-edits folder (C6V_STEPS or core-hardening/steps-edits)"
if [ -L "$S" ]; then echo "MISSING INPUT: steps-edits is a symbolic link ($S); use the real folder (set C6V_STEPS)"; miss=1; fi
if ! ls "$S"/OWNER-SHEET-v[0-9]*-[AB].md >/dev/null 2>&1; then echo "MISSING INPUT: no OWNER-SHEET-vN-A/B.md in $S"; miss=1; fi
need "$R/tests/test_no_reference_material.py" "tests/test_no_reference_material.py (the list of banned names)"
need "$H/c6-skip-audit/REPORT-c6s.md" "c6-skip-audit/REPORT-c6s.md (the report the base build starts from)"
if [ "$miss" -ne 0 ]; then echo "run_all.sh stopped: fix the missing input(s) above"; exit 2; fi
export C6V_TREE C6V_STEPS="$S"
cd "$E"
bash static-checks.sh > static-checks-output.txt 2>&1; src=$?; echo "static-checks exit $src"; if [ "$src" -ne 0 ]; then tail -n 3 static-checks-output.txt; echo "run_all.sh stopped: static-checks.sh failed (see the lines above)"; exit 2; fi
( cd "$C6V_TREE/demo/n8n-flows-real-v5" && echo "## command: grep -il -E 'DELETE|archive' mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; echo exit \$?" && grep -il -E 'DELETE|archive' mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; echo "exit $? (1 = no file matches)" ) > contact-grep-output.txt 2>&1
rm -rf "$E/steps-snapshot" && mkdir "$E/steps-snapshot" && cp -p "$S"/OWNER-SHEET-v*.md "$S"/LEAD-RELEASE-NOTE-v*.md "$E/steps-snapshot"/
python3 -B -I build_base.py || exit 1
python3 -B -I build_c6v.py || exit 1
C6V_MAKE_CENSUS=1 python3 -B -I verify-c6v.py | tail -n 1
python3 -B -I verify-c6v.py > verify-c6v-output.txt 2>&1; vrc=$?; echo "verify exit $vrc"; tail -n 1 verify-c6v-output.txt | cut -c1-200
C6V_SNAPSHOT="$E/steps-snapshot" C6V_STEPS="$E/steps-snapshot" python3 -B -I neg_controls_c6v.py > /dev/null 2>&1; nrc=$?; echo "neg exit $nrc"; tail -n 1 neg-output.txt
rm -rf "$E/steps-snapshot"   # a temporary copy of the sheets for the negative controls
python3 -B -I scan_c6v.py > /dev/null 2>&1; scrc=$?; echo "scan exit $scrc"; tail -n 1 scan-c6v-output.txt
[ "$vrc" -eq 0 ] && [ "$nrc" -eq 0 ] && [ "$scrc" -eq 0 ]
