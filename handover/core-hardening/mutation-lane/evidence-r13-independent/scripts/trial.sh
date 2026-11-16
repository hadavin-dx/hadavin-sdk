#!/bin/bash
# hostile git first on PATH; script named git in other folders; symlink git -> /bin/sh; other .venv/bin/python as VENV
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
tbc() { grep -c 'Traceback\|^  File ' "$1"; }
LOG=$W/neg/fake.log; rm -f $LOG
mkdir -p $W/neg/fb $W/neg/cwdgit $W/neg/fakevenv/bin
printf '#!/bin/sh\necho "FAKE-GIT-RAN uid=$(id -u) args=$*" >> %s\nexec /usr/bin/git "$@"\n' $LOG > $W/neg/fb/git; chmod 755 $W/neg/fb/git
cp $W/neg/fb/git $W/neg/cwdgit/git
printf '#!/bin/sh\necho "FAKE-PY-RAN uid=$(id -u) args=$*" >> %s\nexec %s "$@"\n' $LOG $(readlink -f $VENV/bin/python) > $W/neg/fakevenv/bin/python; chmod 755 $W/neg/fakevenv/bin/python
ln -sfn /bin/sh $W/neg/fb/sh-as-git
row() { echo "ROW|$1|uid=$(id -u)|exit=$2|tb=$(tbc $3)|fake_log_lines=$(cat $LOG 2>/dev/null | wc -l)|file_last=$(last)|state=$(ls -A $STATE 2>/dev/null|tr '\n' ' ')|$(tail -n 1 $3|cut -c1-170)"; }
runfull() { $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix T --no-control --raw $W/neg/rawt --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py; }
echo "### G1 control: normal run"; fresh_root; rm -f $LOG; runfull >$W/neg/g.out 2>&1; row G1-control $? $W/neg/g.out
echo "### G2 hostile git FIRST on PATH, run form"; fresh_root; rm -f $LOG; ( PATH=$W/neg/fb:$PATH runfull ) >$W/neg/g.out 2>&1; row G2-path-git-first $? $W/neg/g.out; cat $LOG 2>/dev/null | head -3
echo "### G3 hostile git FIRST on PATH, --restore with --sha"; fresh_root; plant_kill; rm -f $LOG; ( PATH=$W/neg/fb:$PATH $PY $RUN --root $W/neg/root --restore --sha $SHA --repo $W/neg/toy ) >$W/neg/g.out 2>&1; row G3-path-git-first-restore $? $W/neg/g.out; cat $LOG 2>/dev/null | head -3
echo "### G4 cwd holds a script named git, PATH has '.' first"; fresh_root; rm -f $LOG; ( cd $W/neg/cwdgit && PATH=.:$PATH $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix T --no-control --raw $W/neg/rawt --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py ) >$W/neg/g.out 2>&1; row G4-cwd-git-dot-path $? $W/neg/g.out
echo "### G5 symlink named git -> /bin/sh first on PATH"; fresh_root; rm -f $LOG; mkdir -p $W/neg/fb2; ln -sfn /bin/sh $W/neg/fb2/git; ( PATH=$W/neg/fb2:$PATH runfull ) >$W/neg/g.out 2>&1; row G5-symlink-git-sh-first $? $W/neg/g.out
echo "### G6 --repo is a folder whose own git is hostile: repo folder with a script named git in cwd"; fresh_root; rm -f $LOG; ( cd $W/neg/cwdgit && runfull ) >$W/neg/g.out 2>&1; row G6-cwd-git-no-dot $? $W/neg/g.out
echo "### G7 other .venv/bin/python: root/.venv -> fakevenv (python is a logging wrapper)"; fresh_root; rm -f $W/neg/root/.venv; ln -s $W/neg/fakevenv $W/neg/root/.venv; rm -f $LOG; runfull >$W/neg/g.out 2>&1; row G7-other-venv-python $? $W/neg/g.out; head -2 $LOG 2>/dev/null
echo "### G8 --pythonpath pointing at another folder with a fake mod"; fresh_root; mkdir -p $W/neg/evilpp; printf 'def f():\n    return 1\n' > $W/neg/evilpp/mod.py; $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix T --no-control --raw $W/neg/rawt --pythonpath $W/neg/evilpp --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py >$W/neg/g.out 2>&1; row G8-pythonpath-elsewhere $? $W/neg/g.out
echo "### G9 hostile git via GIT_EXEC_PATH / GIT_DIR / LD_PRELOAD-name env set in the caller"; fresh_root; rm -f $LOG; ( GIT_EXEC_PATH=$W/neg/fb GIT_DIR=/nonexistent GIT_WORK_TREE=/ GIT_CONFIG_GLOBAL=/nonexistent PYTHONPATH=$W/neg/evilpp runfull ) >$W/neg/g.out 2>&1; row G9-git-env $? $W/neg/g.out
echo DONE
