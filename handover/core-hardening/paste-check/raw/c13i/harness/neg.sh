#!/bin/bash
# neg.sh NAME 'setup shell snippet (cwd=ev13i, hb restored from snap-C9)' blocks...   ; VARX env = extra var assignments appended to vars
cd /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev13i
n=$1; setup=$2; shift 2
rm -rf hb; cp -a ${SNAP:-snap-C9} hb
cp v-pos.keep v-neg.txt; [ -n "$VARX" ] && printf '\n%s\n' "$VARX" >> v-neg.txt
D=hb/hbroot; PF=$D/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md; EVD=$D/egm/duplicate-proof-lead-desk/wp6/evidence-2; PS=$D/_local/scratch/wp6-smoke/pastes; SM=$D/_local/scratch/wp6-smoke; WK=$D/_local/scratch/lead-plan-work
eval "$setup"
{ echo "NEGATIVE $n  setup: $setup  VARX: $VARX"; tools/run.sh v-neg.txt "$@" 2>&1 | cut -c1-300; } > negraw/$n.txt
grep -E '^#####.*exit=|^STOP|STOP' negraw/$n.txt | cut -c1-200
