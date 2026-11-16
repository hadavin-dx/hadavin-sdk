#!/bin/bash
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
g() { python3 -c "import sys;print('A'*int(sys.argv[1]),end='')" "$1"; }
row() { echo "ROW|$1|uid=$(id -u)|exit=$2|tb=$(tbc $3)|file_last=$(last)|state=$(ls -A $STATE 2>/dev/null|tr '\n' ' ')|$(tail -n 1 $3|cut -c1-170)"; }
fresh_root
$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawj --out-json $W/neg/ojl -- tests/test_fast.py >/dev/null 2>&1
ln -sfn /etc/hostname $W/neg/oj; fresh_root
$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawx --out-json $W/neg/oj -- tests/test_fast.py >$W/neg/x.out 2>&1; row X-outjson-symlink $? $W/neg/x.out
for len in 59000 60000 61000 100000 120000 130000; do fresh_root
  $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old "$(g $len)" --new x --raw $W/neg/rawx -- tests/test_fast.py >$W/neg/x.out 2>&1; row X-old-$len $? $W/neg/x.out
  fresh_root
  $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new "$(g $len)" --raw $W/neg/rawx -- tests/test_fast.py >$W/neg/x.out 2>&1; row X-new-$len $? $W/neg/x.out
done
for len in 59000 59990 60000 60100; do fresh_root; E=$(g $len)
  $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawx -- -k "$E" tests/test_fast.py >$W/neg/x.out 2>&1; row X-k-$len $? $W/neg/x.out; done
echo DONE
