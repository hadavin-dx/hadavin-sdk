#!/bin/bash
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
g() { python3 -c "import sys;print('A'*int(sys.argv[1]),end='')" "$1"; }
echo "### R --raw edge cases (uid $(id -u)); run form with --no-control"
rr() { name=$1; shift; fresh_root; rm -rf $W/neg/rawx; "$@" >$W/neg/r.out 2>&1; rc=$?
  echo "ROW|$name|uid=$(id -u)|exit=$rc|traceback_lines=$(tbc $W/neg/r.out)|file_last=$(last)|state=$(ls -A $STATE 2>/dev/null|tr '\n' ' ')|$(tail -n 1 $W/neg/r.out|cut -c1-160)"; }
B() { $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' "$@" -- tests/test_fast.py; }
rr R01-normal B --raw $W/neg/rawx
rr R02-empty B --raw ""
rr R03-relative B --raw rawrel
rr R04-inside-root B --raw $W/neg/root/rawin
rr R05-is-root B --raw $W/neg/root
rr R06-dot B --raw .
rr R07-slash B --raw /
rr R08-devnull B --raw /dev/null
rr R09-existing-file bash -c "echo x > $W/neg/afile; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/afile -- tests/test_fast.py"
rr R10-symlink-to-dir bash -c "mkdir -p $W/neg/realraw; ln -sfn $W/neg/realraw $W/neg/rawlink; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawlink -- tests/test_fast.py"
rr R11-parent-is-file bash -c "echo x > $W/neg/pf; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/pf/sub -- tests/test_fast.py"
rr R12-dotdot B --raw $W/neg/root/../rawdd
rr R13-4095 B --raw "/$(g 4094)"
rr R14-4096 B --raw "/$(g 4095)"
rr R15-120000 B --raw "/$(g 119999)"
rr R16-name-300 B --raw "$W/neg/$(g 300)"
rr R17-newline-in-name B --raw "$W/neg/ra
w"
rr R18-control-char-name B --raw "$W/neg/ra$(printf '\033[31m')w"
rr R19-unicode B --raw "$W/neg/rawé日本"
rr R20-readonly-parent bash -c "mkdir -p $W/neg/ro; chmod 555 $W/neg/ro; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/ro/sub -- tests/test_fast.py; r=\$?; chmod 755 $W/neg/ro; exit \$r"
rr R21-out-json-inside-root B --raw $W/neg/rawx --out-json $W/neg/root/o.json
rr R22-out-json-symlink bash -c "ln -sfn /etc/hostname $W/neg/oj; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawx --out-json $W/neg/oj -- tests/test_fast.py; cat /etc/hostname >/dev/null"
rr R23-prefix-long B --raw $W/neg/rawx --prefix "$(g 5000)"
rr R24-old-8MB bash -c "$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old \"\$(python3 -c \"print('A'*8000000)\")\" --new x --raw $W/neg/rawx -- tests/test_fast.py"
rr R25-many-test-args bash -c "$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --raw $W/neg/rawx -- tests/test_fast.py \$(for i in \$(seq 3000); do echo tests/nofile\$i.py; done)"
echo "### R-end: file_last must be return1 everywhere above unless a run completed"
echo DONE
