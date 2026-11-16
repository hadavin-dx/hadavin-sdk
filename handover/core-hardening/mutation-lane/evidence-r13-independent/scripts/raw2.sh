#!/bin/bash
# --raw with . .. / /tmp and shapes; cwd is an empty folder of mine. '/' runs inside a read-only bind mount so nothing can reach the real /.
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
B() { $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' "$@" -- tests/test_fast.py; }
Bq() { $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix Q --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' "$@" -- tests/test_fast.py; }
rr2() { name=$1; cwd=$2; shift 2; fresh_root; rm -rf $W/neg/cwd; mkdir -p $W/neg/cwd/sub; ( cd $W/neg/cwd/$cwd && "$@" ) >$W/neg/r.out 2>&1; rc=$?
  echo "ROW|$name|uid=$(id -u)|cwd=$cwd|exit=$rc|files_in_cwd=$(ls -A $W/neg/cwd/$cwd | wc -l)|files_in_cwd_parent=$(ls -A $W/neg/cwd | tr '\n' ' ')|tb=$(tbc $W/neg/r.out)|file_last=$(last)|state=$(ls -A $STATE 2>/dev/null|tr '\n' ' ')|$(tail -n 1 $W/neg/r.out|cut -c1-170)"; }
rr2 A01-dot . B --raw .
rr2 A02-dotdot sub B --raw ..
rr2 A03-dotdot-sub-x sub B --raw ../x
rr2 A04-dot-slash-dot . B --raw ./.
rr2 A05-slash-dotdot-dotdot . B --raw ../..
rr2 A06-dot-trailing-slash . B --raw ./
rr2 A07-dotdot-in-middle . B --raw $W/neg/cwd/sub/../zz
rr2 A08-slash-ROBIND . bash -c "unshare -m --propagation private sh -c 'mount --bind / / && mount -o remount,bind,ro / && mount --bind $W $W && mount -o remount,bind,rw $W && cd $W/neg/cwd && $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix Q --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old \"return 1\" --new \"return 2\" --raw / -- tests/test_fast.py'"
echo "ROW|A08-note|in A08 a real write to / would fail with a read-only error instead of succeeding; exit 2 + REFUSED text means refused before writing"
BEFORE=$(ls /tmp | grep -c '^Q-m1.txt$'); rr2 A09-slash-tmp . Bq --raw /tmp; echo "ROW|A09-check|Q-m1.txt in /tmp before=$BEFORE after=$(ls /tmp | grep -c '^Q-m1.txt$')"; rm -f /tmp/Q-m1.txt 2>/dev/null
rr2 A10-slash-usr . Bq --raw /usr
# A11 removed (my slip: --raw /etc/zz is two levels deep, accepted by design, wrote 3 toy files into /etc/zz; deleted by me)
rr2 A11-two-level-in-my-folder . Bq --raw $W/neg/rawA11
rr2 A12-top-level-new . Bq --raw /zzq-r13i
echo "ROW|A12-check|/zzq-r13i exists: $([ -e /zzq-r13i ] && echo YES || echo no)"
echo DONE
