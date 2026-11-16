#!/bin/bash
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
row() { echo "ROW|$1|uid=$(id -u)|exit=$2|traceback_lines=$(tbc $3)|file_last=$(last)|state=$(ls -A $STATE 2>/dev/null|tr '\n' ' ')|$(tail -1 $3|cut -c1-140)"; }
echo "### M forged marker modes (uid $(id -u)); plain --restore and --restore --sha; modes 4755 2755 1755 0777 0664"
for mode in 2541 1517 989 511 436; do for how in plain sha; do
  fresh_root; plant_kill; setmode $mode
  if [ $how = plain ]; then $PY $RUN --root $W/neg/root --restore >$W/neg/m.out 2>&1; rc=$?; else $PY $RUN --root $W/neg/root --restore --sha $SHA --repo $W/neg/toy >$W/neg/m.out 2>&1; rc=$?; fi
  echo "ROW|M-mode$(printf %o $mode)-$how|uid=$(id -u)|exit=$rc|traceback_lines=$(tbc $W/neg/m.out)|file_last=$(last)|file_mode=$(stat -c %a $W/neg/root/src/mod.py)|marker=$(ls $STATE/*.planted.json 2>/dev/null|wc -l)|state=$(ls -A $STATE|tr '\n' ' ')|$(tail -1 $W/neg/m.out|cut -c1-170)"
done; done
echo "### P path lengths (uid $(id -u))"
g() { python3 -c "import sys;print('A'*int(sys.argv[1]),end='')" "$1"; }
for len in 4095 4096 120000; do
  V=$(g $len); P="/$(g $((len-1)))"
  for mode in restore run; do
    for opt in root sha file repo; do
      fresh_root
      if [ $mode = restore ]; then
        case $opt in
          root) a=(--root "$V" --restore);; sha) a=(--root $W/neg/root --sha "$V" --repo $W/neg/toy --restore);;
          file) a=(--root $W/neg/root --file "$V" --restore);; repo) a=(--root $W/neg/root --sha $SHA --repo "$V" --restore);;
        esac
      else
        base=(--root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --id m1 --file src/mod.py --old 'return 1' --new 'return 2')
        case $opt in
          root) a=("${base[@]}" --root "$V" -- tests/test_fast.py);; sha) a=("${base[@]}" --sha "$V" -- tests/test_fast.py);;
          file) a=("${base[@]}" --file "$V" -- tests/test_fast.py);; repo) a=("${base[@]}" --repo "$V" -- tests/test_fast.py);;
        esac
      fi
      $PY $RUN "${a[@]}" >$W/neg/p.out 2>&1; rc=$?; row "P-$mode-$opt-$len" $rc $W/neg/p.out
      # same with a path-shaped value (leading slash, total len)
      if [ $opt != sha ]; then
        a2=("${a[@]/$V/$P}"); $PY $RUN "${a2[@]}" >$W/neg/p.out 2>&1; rc=$?; row "P-$mode-$opt-path$len" $rc $W/neg/p.out; fi
    done
  done
done
echo "### K long -k/-m expressions"
for len in 100000 100001; do for flag in -k -m; do
  fresh_root; E=$(g $len)
  $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- $flag "$E" tests/test_fast.py >$W/neg/k.out 2>&1; rc=$?; row "K-$flag-$len" $rc $W/neg/k.out
done; done
echo DONE
