#!/bin/bash
cd /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev13i
rm -rf negraw; mkdir negraw
tools/pos.sh
. <(tr ';' '\n' < v-pos.keep | grep -E '^ *(PIN|OLD)=' | tr -d ' ')
N=tools/neg.sh
for o in 'OLD=HEAD' 'OLD=abc12' 'OLD=-p' "OLD=''" 'OLD=ABCDEF1' "OLD='$OLD;touch /z/hbroot/PWNED'"; do tag=$(printf '%s' "$o" | tr -c 'A-Za-z0-9=' _ | cut -c1-30); VARX="$o" $N N1-old-$tag : b32 b33 b37; done >/dev/null
VARX="OLD=${PIN:0:7}" $N N2-old-equals-pin7 : b32 b33 b37 >/dev/null
VARX="OLD=$PIN" $N N2b-old-equals-pin40 : b32 b33 b37 >/dev/null
$N N0-positive-control : b32 b33 b37 >/dev/null
$N N3-progress-symlink 'mv $EVD/PROGRESS.md $EVD/real.md; ln -s real.md $EVD/PROGRESS.md' b37 b29 >/dev/null
$N N3c-b25-progress-symlink-victim 'echo victim > $EVD/victim.txt; rm $EVD/PROGRESS.md; ln -s victim.txt $EVD/PROGRESS.md' blocks/x-b25-sp.sh >/dev/null
$N N3d-b25-control-normal : blocks/x-b25-sp.sh >/dev/null
$N N4-PF-symlink 'mv $PF $WK/pf-real.md; ln -s $WK/pf-real.md $PF' b34 b31 b35 b37 b18 >/dev/null
$N N4b-control-symlink 'mv $PS/P-4b.control.txt $PS/real.ctl; ln -s real.ctl $PS/P-4b.control.txt' b27 b36 b37 >/dev/null
$N N4c-standin-gone-symlink 'mv $PS/standin-gone.txt $PS/real.gone; ln -s real.gone $PS/standin-gone.txt' b36 b37 >/dev/null
$N N4d-P4bsh-symlink 'mv $PS/P-4b.sh $PS/real.sh; ln -s real.sh $PS/P-4b.sh' b27 b36 b37 >/dev/null
$N N5-PF-missing 'rm $PF' b34 b31 b35 b37 >/dev/null
SNAP=snap-preC4 $N N6-C4-S7-keeps-backslashes 'sed -i "s/^S7\t.*$/S7\tn8n_start.sh\tN8N_*\\\\|DB_*\\\\|EXECUTIONS_*\\\\|WEBHOOK_URL\\\\|GENERIC_TIMEZONE\\\\|TZ) ;;/" $SM/strings.txt' b30 b31 blocks/x-accept6.sh b37 >/dev/null
SNAP=snap-preC4 $N N6b-C4-control-S7-plain : b30 b31 blocks/x-accept6.sh >/dev/null
SNAP=snap-preC4 $N N6c-C4-string-not-in-plan-row 'sed -i "s/^S3\t\(.*\)\t.*$/S3\t\1\tflock -n 99/" $SM/strings.txt' b30 b31 blocks/x-accept6.sh >/dev/null
$N N7-banned-kill-in-P4b-source 'rm $PS/P-4b.sh; sed -i "/^#!\/bin\/bash/a # kill the thing" $WK/../../../../ch/paste-check/LEAD-FILL-list-v5.md 2>/dev/null || sed -i "/^#!\/bin\/bash/a # kill the thing" hb/ch/paste-check/LEAD-FILL-list-v5.md' b20 b20 b27 b36 b37 >/dev/null
$N N7b-banned-envsh-in-P4b-source 'rm $PS/P-4b.sh; sed -i "/^#!\/bin\/bash/a # source env.sh" hb/ch/paste-check/LEAD-FILL-list-v5.md' b20 b27 b37 >/dev/null
VARX='HBW=/z/hbroot' $N N8-WSL3-no-hit-STOP-then-later 'rm $PS/P-4b.control.txt $PS/standin-gone.txt' b24 b26 b27 b36 b37 >/dev/null
VARX='HBW=/z/hbroot' $N N8b-WSL1-as-root : b22 >/dev/null
$N N8c-P4b-changed-after-control 'echo "# edit" >> $PS/P-4b.sh' b27 b36 b37 >/dev/null
$N N8d-control-without-hit 'sed -i 2d $PS/P-4b.control.txt; printf "gone control=%s\n" "$(sha256sum $PS/P-4b.control.txt | cut -c1-16)" > $PS/standin-gone.txt' b27 b36 b37 >/dev/null
$N N8e-standin-gone-stale 'echo "gone control=0000000000000000" > $PS/standin-gone.txt' b36 b37 >/dev/null
$N N9b-PF-has-CR 'sed -i "5s/\$/\r/" $PF' b34 b37 >/dev/null
$N N9c-PF-edited-after-C8 'echo "extra line" >> $PF' b37 >/dev/null
$N N9d-second-sha-in-PF 'echo "stray 1111111111111111111111111111111111111111" >> $PF' b34 b37 >/dev/null
$N N9e-PF-missing-C9-but-C6-not-run 'rm -f $WK/proof-c6.txt' b37 >/dev/null
for f in negraw/*.txt; do printf '%-62s' "$(basename $f .txt)"; grep -o 'exit=[0-9]*' $f | tr '\n' ' '; echo; done > negraw/_SUMMARY.txt
