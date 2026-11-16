#!/bin/bash
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
g() { python3 -c "import sys;print('A'*int(sys.argv[1]),end='')" "$1"; }
echo "### K2 long -k/-m WITH --pythonpath (so the import check passes); uid $(id -u)"
for len in 99999 100000 100001; do for flag in -k -m; do
  fresh_root; E=$(g $len)
  $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- $flag "$E" tests/test_fast.py >$W/neg/k.out 2>&1; rc=$?
  echo "ROW|K2-$flag-$len|uid=$(id -u)|exit=$rc|traceback_lines=$(tbc $W/neg/k.out)|file_last=$(last)|state=$(ls -A $STATE|tr '\n' ' ')|$(tail -n 1 $W/neg/k.out|cut -c1-150)"
done; done
echo "### M2 marker mode 1755 (octal) = 1005 decimal, plain and --sha"
for how in plain sha; do
  fresh_root; plant_kill; setmode 1005
  if [ $how = plain ]; then $PY $RUN --root $W/neg/root --restore >$W/neg/m.out 2>&1; rc=$?; else $PY $RUN --root $W/neg/root --restore --sha $SHA --repo $W/neg/toy >$W/neg/m.out 2>&1; rc=$?; fi
  echo "ROW|M2-mode1755-$how|uid=$(id -u)|exit=$rc|traceback_lines=$(tbc $W/neg/m.out)|file_last=$(last)|file_mode=$(stat -c %a $W/neg/root/src/mod.py)|marker=$(ls $STATE/*.planted.json 2>/dev/null|wc -l)|$(tail -n 1 $W/neg/m.out|cut -c1-170)"
done
echo DONE
