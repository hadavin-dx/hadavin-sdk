export TMPDIR=$W/neg/tmpstate; STATE=$TMPDIR/hadavin-mutation-lane-$(id -u)
PY="python3 -B -I"
mk_toy() { rm -rf $W/neg/toy; mkdir -p $W/neg/toy/src $W/neg/toy/tests $TMPDIR; cd $W/neg/toy; git init -q
  printf 'def f():\n    return 1\n' > src/mod.py
  printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    time.sleep(40)\n    assert f() == 1\n' > tests/test_slow.py
  printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 1\n' > tests/test_fast.py
  git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD); }
fresh_root() { rm -rf "$STATE" $W/neg/root; mkdir -p $W/neg/root $TMPDIR; git -C $W/neg/toy archive $SHA | tar -x -C $W/neg/root; ln -s $VENV $W/neg/root/.venv; rm -rf $W/neg/raw; }
plant_kill() { ( $PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --pythonpath $W/neg/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py > $W/neg/plant.out 2>&1 ) &
  local i; for i in $(seq 100); do ls $STATE/*.planted.json >/dev/null 2>&1 && [ "$(last)" = return2 ] && break; sleep 0.2; done; sleep 1.5
  pkill -9 -f "$RUN --root $W/neg/root"; sleep 0.5; pkill -9 -f "$W/neg/root/.venv/bin/python -m pytest"; sleep 0.5; wait 2>/dev/null; }
last() { tail -1 $W/neg/root/src/mod.py | tr -d ' '; }
forge() { $PY - "$STATE" <<'PY'
import glob, hashlib, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; bk = glob.glob(sys.argv[1] + "/*.backup")[0]
evil = b"def f():\n    return 99  # forged\n"
open(bk, "wb").write(evil)
m = json.load(open(mk)); m["orig_sha256"] = hashlib.sha256(evil).hexdigest(); json.dump(m, open(mk, "w"))
PY
}
setmode() { $PY - "$STATE" "$1" <<'PY'
import glob, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; m = json.load(open(mk)); m["mode"] = int(sys.argv[2]); json.dump(m, open(mk, "w"))
PY
}
