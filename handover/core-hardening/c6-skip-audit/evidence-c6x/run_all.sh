#!/bin/bash
# c6x run_all.sh. Order matters: the owner sheets may still be written by another agent, so check, snapshot, build, verify and negative controls run in one go.
# INPUTS (each missing one stops the run with one line naming it):
#   C6V_TREE   = the folder 'handover' of the copied demo tree (the audited demo files); you set it, there is no default.
#   C6V_STEPS  = optional: another copy of steps-edits (default: ../../steps-edits next to c6-skip-audit).
#   the whole core-hardening folder (this script sits in core-hardening/c6-skip-audit/evidence-c6x), and tests/test_no_reference_material.py of the repository (the list of banned names is read from it at run time).
set -u
E="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$(cd "$E/../.." && pwd)"
R="$(cd "$H/../.." && pwd)"
S=${C6V_STEPS:-$H/steps-edits}
miss=0
need() { if [ ! -e "$1" ]; then echo "MISSING INPUT: $2"; miss=1; fi; }
C6V_TREE="${C6V_TREE:-$E/tree/handover}"; need "$C6V_TREE/demo/VIDEO-RUNSHEET.md" "C6V_TREE (default: the 24 audited files shipped in evidence-c6x/tree/handover) has no demo/VIDEO-RUNSHEET.md"
need "$H/ORDERS.md" "core-hardening/ORDERS.md"
need "$H/REPORT.md" "core-hardening/REPORT.md"
need "$H/inputs" "core-hardening/inputs/ (the whole core-hardening tree is needed)"
need "$S" "steps-edits folder (C6V_STEPS or core-hardening/steps-edits)"
if [ -L "$S" ]; then echo "MISSING INPUT: steps-edits is a symbolic link ($S); use the real folder (set C6V_STEPS)"; miss=1; fi
if ! ls "$S"/OWNER-SHEET-v[0-9]*-[AB].md >/dev/null 2>&1; then echo "MISSING INPUT: no OWNER-SHEET-vN-A/B.md in $S"; miss=1; fi
need "$R/tests/test_no_reference_material.py" "tests/test_no_reference_material.py (the list of banned names)"
need "$H/c6-skip-audit/REPORT-c6s.md" "c6-skip-audit/REPORT-c6s.md (the report the base build starts from)"
if [ "$miss" -ne 0 ]; then echo "run_all.sh stopped: fix the missing input(s) above"; exit 2; fi
# FREEZE: the owner sheets and release notes are still being rewritten by another session while this report is checked, so every check reads a FROZEN copy of the files written up to the freeze time; later files are named in the report and compared by the build (see 'FILES WRITTEN AFTER THE FREEZE')
FREEZE="${C6V_FREEZE:-2026-11-16T19:30:00Z}"
rm -rf "$E/steps-frozen" && mkdir "$E/steps-frozen" && find "$S" -maxdepth 1 -type f \( -name 'OWNER-SHEET-v*.md' -o -name 'LEAD-RELEASE-NOTE-v*.md' \) ! -newermt "$FREEZE" -exec cp -p {} "$E/steps-frozen"/ \;
C6V_STEPS_LIVE="$S"; S="$E/steps-frozen"
export C6V_TREE C6V_STEPS="$S" C6V_STEPS_LIVE C6V_FREEZE="$FREEZE"
cd "$E"
echo "run_all.sh start $(date -u +%FT%TZ)" >> run-log.txt   # one line per full run; the check script counts these lines and compares them with the run count in the report and in c6x-CHANGES.md
bash static-checks.sh > static-checks-output.txt 2>&1; src=$?; echo "static-checks exit $src"; if [ "$src" -ne 0 ]; then tail -n 3 static-checks-output.txt; echo "run_all.sh stopped: static-checks.sh failed (see the lines above)"; exit 2; fi
( cd "$C6V_TREE/demo/n8n-flows-real-v5" && echo "## command: grep -il -E 'DELETE|archive' mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; echo exit \$?" && grep -il -E 'DELETE|archive' mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; echo "exit $? (1 = no file matches)" ) > contact-grep-output.txt 2>&1
rm -rf "$E/steps-snapshot" && mkdir "$E/steps-snapshot" && cp -p "$S"/OWNER-SHEET-v*.md "$S"/LEAD-RELEASE-NOTE-v*.md "$E/steps-snapshot"/
python3 -B -I build_c6x.py || exit 1
C6V_MAKE_CENSUS=1 python3 -B -I verify-c6x.py | tail -n 1
python3 -B -I scan_c6x.py > /dev/null 2>&1; scrc=$?; echo "scan exit $scrc"; tail -n 1 scan-c6x-output.txt
C6V_SNAPSHOT="$E/steps-snapshot" C6V_STEPS="$E/steps-snapshot" python3 -B -I neg_controls_c6x.py > /dev/null 2>&1; nrc=$?; echo "neg exit $nrc"; tail -n 1 neg-output.txt
rm -rf "$E/steps-snapshot"   # a temporary copy of the sheets for the negative controls
python3 -B -I verify-c6x.py > verify-c6x-output.txt 2>&1; vrc=$?; echo "verify exit $vrc"; tail -n 1 verify-c6x-output.txt | cut -c1-200
[ "$vrc" -eq 0 ] && [ "$nrc" -eq 0 ] && [ "$scrc" -eq 0 ]
