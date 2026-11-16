#!/bin/bash
RUN=${RUN:?}; VENV=${VENV:?}; W=${W:?}

. $W/neg/lib.sh
mk_toy
R() { $PY $RUN --root $W/neg/root "$@" 2>&1 | cut -c1-300; return ${PIPESTATUS[0]}; }
row() { echo "ROW|$1|exit=$2|file_last=$(last)|$3"; }
marker() { ls $STATE/*.planted.json 2>/dev/null | head -1; }
forge() { # $1 = python expr applied to dict d (marker), swaps backup to planted text w/ matching hash
python3 - "$(marker)" <<'PY'
import json,sys,hashlib,os
m=sys.argv[1]; d=json.load(open(m)); b=d["backup"]
new=b"def f():\n    return 666\n"; open(b,"wb").write(new); d["orig_sha256"]=hashlib.sha256(new).hexdigest()
json.dump(d,open(m,"w"))
PY
}
echo "### N0 sanity: really planted (SIGKILL) then plain --restore"
fresh_root; plant_kill; echo "planted last=$(last) state=$(ls -A $STATE|tr '\n' ' ')"
R --restore; rc=$?; row N0 $rc "expect 0 file original"

echo "### N1 no marker, no --sha, file planted by hand"
fresh_root; sed -i 's/return 1/return 2/' $W/neg/root/src/mod.py
R --restore; rc=$?; row N1 $rc "expect 2 (not 0); file stays planted"
R --restore --sha $SHA --repo $W/neg/toy; rc=$?; row N1b $rc "with --sha: expect 3 (tree differs)"

echo "### N2 forged marker+backup (matching hash), plain --restore"
fresh_root; plant_kill; forge; R --restore; rc=$?; row N2 $rc "documented limit (d): plain restore accepts forged state; planted text 666 would be 'return666'"
echo "### N2b same forge + --sha"
fresh_root; plant_kill; forge; R --restore --sha $SHA --repo $W/neg/toy; rc=$?; row N2b $rc "expect 3 (backup differs from git)"

echo "### N3 symlinked target: after planting, replace src/mod.py by symlink to decoy"
fresh_root; plant_kill; printf 'decoy\n' > $W/neg/decoy.txt; mv $W/neg/root/src/mod.py $W/neg/mod.moved; ln -s $W/neg/decoy.txt $W/neg/root/src/mod.py
R --restore; rc=$?; row N3 $rc "expect 3; decoy must stay 'decoy'; decoy=$(cat $W/neg/decoy.txt|tr -d '\n') ; moved_planted=$(tail -1 $W/neg/mod.moved|tr -d ' ')"
echo "### N3b symlinked parent folder: src -> srcreal"
fresh_root; plant_kill; mv $W/neg/root/src $W/neg/srcreal; ln -s $W/neg/srcreal $W/neg/root/src
R --restore; rc=$?; echo "ROW|N3b|exit=$rc|planted_in_real=$(tail -1 $W/neg/srcreal/mod.py|tr -d ' ')|expect 3, srcreal still planted (not written through the link)"; rm -f $W/neg/root/src; mv $W/neg/srcreal $W/neg/root/src

echo "### N4 target in .venv (real file under root/.venv)"
fresh_root; rm $W/neg/root/.venv; mkdir -p $W/neg/root/.venv/lib; printf 'def f():\n    return 1\n' > $W/neg/root/.venv/lib/mod.py
$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --id m1 --file .venv/lib/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-250 | tail -3; rc=${PIPESTATUS[0]}; echo "ROW|N4|exit=$rc|venv_file=$(tail -1 $W/neg/root/.venv/lib/mod.py|tr -d ' ')|expect 2 refusal, nothing planted"
echo "### N4b target in __pycache__"
fresh_root; mkdir -p $W/neg/root/src/__pycache__; printf 'def f():\n    return 1\n' > $W/neg/root/src/__pycache__/mod.py
$PY $RUN --root $W/neg/root --sha $SHA --repo $W/neg/toy --prefix N --no-control --raw $W/neg/raw --id m1 --file src/__pycache__/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-250 | tail -2; rc=${PIPESTATUS[0]}; echo "ROW|N4b|exit=$rc|expect 2"

echo "### N5 two-name file: hard link to planted file"
fresh_root; plant_kill; ln $W/neg/root/src/mod.py $W/neg/root/src/mod_alias.py
R --restore; rc=$?; row N5 $rc "expect 3; alias=$(tail -1 $W/neg/root/src/mod_alias.py|tr -d ' ')"
echo "### N5b two-name via link outside root"
fresh_root; plant_kill; ln $W/neg/root/src/mod.py $W/neg/outside_alias.py
R --restore; rc=$?; row N5b $rc "expect 3; outside=$(tail -1 $W/neg/outside_alias.py|tr -d ' ')"; rm -f $W/neg/outside_alias.py

echo "### N6 marker with wrong mode (0777), plain then with --sha"
fresh_root; plant_kill; python3 - "$(marker)" <<'PY'
import json,sys; m=sys.argv[1]; d=json.load(open(m)); d["mode"]=0o777; json.dump(d,open(m,"w"))
PY
R --restore --sha $SHA --repo $W/neg/toy; rc=$?; row N6b $rc "with --sha expect 3 (execute bits); mode now $(stat -c %a $W/neg/root/src/mod.py)"
R --restore; rc=$?; row N6 $rc "plain: limit d: likely 0 and mode written; mode now $(stat -c %a $W/neg/root/src/mod.py)"
echo "### N7 marker for other root (forged root field)"
fresh_root; plant_kill; python3 - "$(marker)" <<'PY'
import json,sys; m=sys.argv[1]; d=json.load(open(m)); d["root"]="/nonexistent/elsewhere"; json.dump(d,open(m,"w"))
PY
R --restore; rc=$?; row N7 $rc "expect 2 (names another root), file stays planted"
echo "### N8 marker deleted by hand but file planted, plain"
fresh_root; plant_kill; rm -f $STATE/*.planted.json; R --restore; rc=$?; row N8 $rc "expect 2 not 0"
echo "### N9 damaged marker (garbage)"
fresh_root; plant_kill; printf 'garbage' > "$(marker)"; R --restore; rc=$?; row N9 $rc "expect 3 per docstring"
echo "### N10 marker present, backup deleted"
fresh_root; plant_kill; rm -f $(python3 -c "import json;print(json.load(open('$(marker)'))['backup'])"); R --restore; rc=$?; row N10 $rc "expect 3"
echo DONE
