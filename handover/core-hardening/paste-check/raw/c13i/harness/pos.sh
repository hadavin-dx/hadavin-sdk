#!/bin/bash
# full positive reset + flow. output to pos-run.txt
cd /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev13i
rm -rf hb; cp -a snap-A8 hb
PFH=hb/hbroot/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md
sed -i '3s#C:\\Users\\rakes\\Downloads\\Hadavin\\egm\\duplicate-proof-lead-desk\\wp6\\plan-wp6-resmoke-v5.md#Z:\\hbroot\\egm\\duplicate-proof-lead-desk\\wp6\\plan-wp6-resmoke-v5.md#; 3s#PF=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md;#PF=Z:/hbroot/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md;#g' $PFH
python3 -I tools/mkrepo.py hb/hbroot >/dev/null; PIN=$(cat hb/hbroot/../../pin.txt 2>/dev/null || git -C hb/hbroot/_local/scratch/wt/nlite-fix5 rev-parse HEAD)
OLD=$(git -C hb/hbroot/_local/scratch/wt/nlite-fix5 rev-parse --short=7 HEAD~1)
echo "WTN=nlite-fix5; W3N=nlite-fix3; HB='/z/hbroot'; CH='/z/ch'; CHAIN=4; PF_CONFIRMED=yes; L1_RULED=yes; FINAL5=yes; NAMES_OK=yes; PIN=$PIN; BR=take/nlite-int-r5; OLD=$OLD" > v-pos.txt
tools/run.sh v-pos.txt b14 b15 b16 b17 b18 b19 b20 > pos-run-1.txt 2>&1
P=hb/hbroot/_local/scratch/wp6-smoke/pastes
{ printf 'P-4b.sh sha256 %s\n' "$(sha256sum $P/P-4b.sh | cut -d' ' -f1)"; echo 'P-4b-HIT pid=4242'; } > $P/P-4b.control.txt
printf 'gone control=%s\n' "$(sha256sum $P/P-4b.control.txt | cut -c1-16)" > $P/standin-gone.txt
EVD=hb/hbroot/egm/duplicate-proof-lead-desk/wp6/evidence-2; mkdir -p $EVD; printf 'P-3a done 2026-11-16T13:00Z\n' > $EVD/PROGRESS.md
tools/run.sh v-pos.txt b27 b28 b29 b30 > pos-run-2a.txt 2>&1
rm -rf snap-preC4; cp -a hb snap-preC4; cp v-pos.txt v-pos.keep
tools/run.sh v-pos.txt b31 blocks/x-accept1.sh blocks/x-accept6.sh b32 b33 b34 b35 b36 > pos-run-2.txt 2>&1
rm -rf snap-C9; cp -a hb snap-C9
tools/run.sh v-pos.txt b37 > pos-run-3.txt 2>&1
