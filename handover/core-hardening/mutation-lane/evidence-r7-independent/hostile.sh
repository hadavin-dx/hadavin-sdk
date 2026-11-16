#!/bin/bash
# EVIDENCE RUNNER own hostile inputs for run.py r7. Toy repo only. usage: RUN=.. H=<scratch> VENV=<venv> bash hostile.sh
RUN=${RUN:?}; H=${H:?}; VENV=${VENV:?}; GIT=$(command -v git)
T=$H/toy; export TMPDIR=$H/tmpstate; STATE=$TMPDIR/hadavin-mutation-lane-$(id -u)
rm -rf "${T:?}" "${TMPDIR:?}" "${H:?}/out"; mkdir -p "$T/repo/src" "$T/repo/tests" "$TMPDIR" "$H/out"
cd "$T/repo" || exit 9; git init -q
printf 'def f():\n    return 1\n' > src/mod.py
printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    time.sleep(20)\n    assert f() == 1\n' > tests/test_slow.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 1\n' > tests/test_fast.py
printf 'import os\ndef test_rm():\n    os.remove("src/mod.py")\n' > tests/test_rm.py
printf 'import os\ndef test_ln():\n    os.remove("src/mod.py"); os.symlink("/nonexistent-victim", "src/mod.py")\n' > tests/test_ln.py
printf 'import os\ndef test_perm():\n    os.chmod("src", 0o500); os.chmod("src/mod.py", 0o400)\n' > tests/test_perm.py
printf 'def test_corrupt():\n    open("src/mod.py","w").write("garbage\\n")\n' > tests/test_corrupt.py
mkdir docs; printf 'alpha\n' > docs/note.txt
git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD)
ORIG=$(git show "$SHA:src/mod.py" | sha256sum | cut -d' ' -f1)
fresh_root() { pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null; pkill -9 -f "$T/root-moved/.venv/bin/python -m pytest" 2>/dev/null; chmod -R u+w "$T/root" "$T/root-moved" 2>/dev/null; rm -rf "${STATE:?}" "${T:?}/root" "${T:?}/root-moved" "${H:?}/rawT"; mkdir "$T/root"; git -C "$T/repo" archive "$SHA" | tar -x -C "$T/root"; ln -s "$VENV" "$T/root/.venv"; }
base() { python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" "$@"; }
mut() { base --id m1 --file src/mod.py --old 'return 1' --new 'return 2' "$@"; }
lastl() { tail -1 "${1:-$T/root/src/mod.py}" 2>/dev/null | tr -d ' '; }
backhash() { sha256sum "${1:-$T/root/src/mod.py}" 2>/dev/null | cut -d' ' -f1; }
isback() { [ "$(backhash "$1")" = "$ORIG" ] && echo YES || echo NO; }
statefiles() { ls -A "$STATE" 2>/dev/null | grep -v lock | tr '\n' ' '; }
stray() { pgrep -f "$T/root.*/.venv/bin/python -m pytest" | wc -l; }
row() { echo "ROW|$1|$2" | tee -a "$H/out/rows.txt"; }
bg() { ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' "$@" -- tests/test_slow.py ) >"$H/out/bg.out" 2>&1 & RP=$!; }
waitplant() { for _ in $(seq 400); do [ "$(lastl)" = return2 ] && { sleep "${1:-0}"; return 0; }; sleep 0.02; done; return 1; }

killcase() { # name signal when(0=immediately at plant text, 3=after tests started) target(run|group)
  fresh_root; bg; waitplant "$3"
  if [ "$4" = group ]; then kill -"$2" -- -"$RP" 2>/dev/null || kill -"$2" $RP; else kill -"$2" $RP; fi
  wait $RP 2>/dev/null; rc=$?; sleep 1
  row "$1" "exit=$rc | original text back: $(isback) | marker/backup left: [$(statefiles)] | stray pytest: $(stray) | last line: $(lastl)"
  pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
  if [ -n "$(statefiles)" ]; then python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; row "$1 +--restore" "exit=$? | original text back: $(isback) | state: [$(statefiles)]"; fi
}
for s in INT TERM HUP QUIT USR1 USR2 ALRM; do killcase "K-$s-at-plant-instant" $s 0 run; killcase "K-$s-3s-after-plant" $s 3 run; done
for s in INT TERM HUP; do killcase "K-$s-to-whole-group-at-plant" $s 0 group; done
killcase "K-KILL-at-plant (expected: planted, restore needed)" KILL 3 run
fresh_root; bg; waitplant 0; kill -TERM $RP; kill -TERM $RP; kill -INT $RP; kill -HUP $RP; wait $RP; rc=$?; sleep 1
row "K-multi TERM,TERM,INT,HUP back-to-back" "exit=$rc | original text back: $(isback) | state: [$(statefiles)] | stray: $(stray)"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
for sig in TERM INT HUP; do bad=0; n=0; kept=0
  for d in 0.05 0.15 0.3 0.45 0.6 0.8 1.0 1.2 1.5 1.8 2.2 2.8 3.5; do
    fresh_root; bg; sleep $d; kill -$sig $RP 2>/dev/null; wait $RP 2>/dev/null; rc=$?; sleep 0.5; n=$((n+1))
    pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
    if [ "$(isback)" != YES ]; then if [ -n "$(statefiles)" ] && [ $rc -eq 3 ]; then kept=$((kept+1)); else bad=$((bad+1)); echo "   spray $sig delay=$d exit=$rc back=$(isback) state=[$(statefiles)]"; fi; fi
  done
  row "K-spray-$sig ($n delays 0.05..3.5s after start)" "cases where original text NOT back and no marker kept with exit 3: $bad | cases left planted-but-recoverable (exit 3, marker kept): $kept"
done

fresh_root; bg; waitplant 0; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
MK=$(ls "$STATE"/*.planted.json); BK=${MK%.planted.json}.backup
python3 - "$MK" <<'PY'
import json,sys
m=json.load(open(sys.argv[1])); m["file"]="../../victim.txt"; json.dump(m,open(sys.argv[1],"w"))
PY
echo victim-original > "$H/victim.txt"; python3 "$RUN" --root "$T/root" --restore > "$H/out/f1.out" 2>&1; rc=$?
row "F1 forged marker: file field = ../../victim.txt" "exit=$rc | victim file overwritten: $([ "$(cat $H/victim.txt)" = victim-original ] && echo NO || echo YES) | msg: $(tail -1 $H/out/f1.out | cut -c1-120)"
fresh_root; bg; waitplant 0; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
MK=$(ls "$STATE"/*.planted.json); BK=${MK%.planted.json}.backup
printf 'EVIL\n' > "$BK"; python3 - "$MK" "$BK" <<'PY'
import json,sys,hashlib
m=json.load(open(sys.argv[1])); m["file"]="docs/note.txt"; m["orig_sha256"]=hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest(); json.dump(m,open(sys.argv[1],"w"))
PY
python3 "$RUN" --root "$T/root" --restore > "$H/out/f1b.out" 2>&1; rc=$?
row "F2 forged marker (needs write access to the private state folder): file=docs/note.txt, backup swapped, hash matched" "exit=$rc | docs/note.txt now: $(head -1 $T/root/docs/note.txt) | msg: $(tail -1 $H/out/f1b.out | cut -c1-120)"
fresh_root; bg; waitplant 0; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
MK=$(ls "$STATE"/*.planted.json); printf 'not json' > "$MK"; python3 "$RUN" --root "$T/root" --restore > "$H/out/f3.out" 2>&1; rc=$?
row "F3 marker is not JSON" "exit=$rc | traceback: $(grep -c Traceback $H/out/f3.out) | file still planted: $([ "$(lastl)" = return2 ] && echo yes || echo no) | msg: $(tail -1 $H/out/f3.out | cut -c1-110)"
python3 - "$MK" <<'PY'
import json,sys; json.dump({"root":"/","file":"/etc/hostname","backup":"/etc/passwd","orig_sha256":"0"*64,"mutant":"x"},open(sys.argv[1],"w"))
PY
cp /etc/hostname "$H/hostname.copy"; python3 "$RUN" --root "$T/root" --restore > "$H/out/f4.out" 2>&1; rc=$?
row "F4 marker with absolute paths (/etc/hostname, /etc/passwd)" "exit=$rc | traceback: $(grep -c Traceback $H/out/f4.out) | /etc/hostname unchanged: $(cmp -s /etc/hostname $H/hostname.copy && echo yes || echo NO)"
rm -f "${MK:?}"; ln -s /etc/hostname "$MK"; python3 "$RUN" --root "$T/root" --restore > "$H/out/f5.out" 2>&1; rc=$?
row "F5 marker is a symlink to /etc/hostname" "exit=$rc | traceback: $(grep -c Traceback $H/out/f5.out) | /etc/hostname unchanged: $(cmp -s /etc/hostname $H/hostname.copy && echo yes || echo NO)"
rm -rf "${STATE:?}"

fresh_root; bg; waitplant 2; mv "$T/root" "$T/root-moved"; ln -s "$T/root-moved" "$T/root"; kill -TERM $RP; wait $RP; rc=$?; sleep 1
row "R1 --root replaced by a symlink to the moved folder, then SIGTERM" "exit=$rc | moved folder original text back: $(isback $T/root-moved/src/mod.py) | state: [$(statefiles)]"
pkill -9 -f "$T/root-moved/.venv/bin/python -m pytest" 2>/dev/null; rm -f "${T:?}/root"; mv "$T/root-moved" "$T/root"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; row "R1 +--restore after renaming back" "original text back: $(isback) | state: [$(statefiles)]"
fresh_root; bg; waitplant 2; mv "$T/root/src" "$T/root/src.moved"; ln -s "$T/root/src.moved" "$T/root/src"; kill -TERM $RP; wait $RP; rc=$?; sleep 1
row "R2 src/ folder swapped for a symlink mid-run, then SIGTERM" "exit=$rc | real file text back: $(isback $T/root/src.moved/mod.py) | state: [$(statefiles)]"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
fresh_root; ln -sfn "$T/root" "$H/rootlink"; python3 "$RUN" --root "$H/rootlink" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py > "$H/out/r3.out" 2>&1; rc=$?
row "R3 --root given as a symlink to the real folder" "exit=$rc | traceback: $(grep -c Traceback $H/out/r3.out) | file back: $(isback) | msg: $(tail -1 $H/out/r3.out | cut -c1-100)"

fresh_root; echo victim-o > "$H/victimo.txt"; ln -sf "$H/victimo.txt" "$H/outlink.json"
mut --out-json "$H/outlink.json" -- tests/test_fast.py > "$H/out/o1.out" 2>&1; rc=$?
row "O1 --out-json is a symlink to another file" "exit=$rc | victim text now: $(head -c 40 $H/victimo.txt | tr '\n' ' ') | file back: $(isback) | traceback: $(grep -c Traceback $H/out/o1.out)"
fresh_root; mut --out-json "$T/root/src/out.json" -- tests/test_fast.py > "$H/out/o2.out" 2>&1; rc=$?
row "O2 --out-json inside --root (src/)" "exit=$rc | out file exists: $([ -e $T/root/src/out.json ] && echo YES || echo no) | mutant ran: $([ -e $H/rawT/X-m1.txt ] && echo YES || echo no) | file back: $(isback)"
fresh_root; mut --out-json "$H/out/ok.json" -- tests/test_fast.py > "$H/out/o3.out" 2>&1; rc=$?
row "O3 control: --out-json outside (normal)" "exit=$rc | json written: $([ -s $H/out/ok.json ] && echo yes || echo no) | file back: $(isback)"
fresh_root; mut --out-json /dev/full -- tests/test_fast.py > "$H/out/o4.out" 2>&1; rc=$?
row "O4 --out-json /dev/full (write fails)" "exit=$rc | traceback: $(grep -c Traceback $H/out/o4.out) | file back: $(isback) | state: [$(statefiles)]"

fresh_root; cp "$T/root/src/mod.py" "$H/hl.tmp"; rm "$T/root/src/mod.py"; ln "$H/hl.tmp" "$T/root/src/mod.py"
mut -- tests/test_fast.py > "$H/out/l1.out" 2>&1; rc=$?
row "L1 file under test has a second name outside root (normal run)" "exit=$rc | traceback: $(grep -c Traceback $H/out/l1.out) | second name text: $(lastl $H/hl.tmp) | mutant ran: $([ -e $H/rawT/X-m1.txt ] && echo YES || echo no) | msg: $(tail -1 $H/out/l1.out | cut -c1-90)"
fresh_root; ln "$T/root/src/mod.py" "$T/root/src/alias.py"; mut -- tests/test_fast.py > "$H/out/l2.out" 2>&1; rc=$?
row "L2 file under test has a second name INSIDE root" "exit=$rc | both names back: $(isback $T/root/src/mod.py)/$(isback $T/root/src/alias.py) | traceback: $(grep -c Traceback $H/out/l2.out)"

python3 - "$H" <<'PY'
import json,sys
h=sys.argv[1]
w=lambda n,s: open(f"{h}/{n}","w").write(s)
w("j-deep.json","["*200000+"]"*200000)
w("j-obj.json",json.dumps({"id":"m1"}))
w("j-dup.json",json.dumps([{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"}]*2))
w("j-escape.json",json.dumps([{"id":"m1","file":"../../etc/hostname","old":"a","new":"b"}]))
w("j-abs.json",json.dumps([{"id":"m1","file":"/etc/hostname","old":"a","new":"b"}]))
w("j-nul.json",json.dumps([{"id":"m1","file":"src/mod.py","old":"return 1","new":"return\u0000 2"}]))
w("j-bignew.json",json.dumps([{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"+"#"*(60*1024*1024)}]))
w("j-many.json",json.dumps([{"id":f"m{i}","file":"src/mod.py","old":"return 1","new":"return 2"} for i in range(3)]+[{"id":"m%d"%i,"file":"src/mod.py","old":"zzz","new":"y"} for i in range(3,20000)]))
w("j-idweird.json",json.dumps([{"id":"../../escape","file":"src/mod.py","old":"return 1","new":"return 2"}]))
w("j-types.json",json.dumps([{"id":5,"file":["a"],"old":None,"new":{}}]))
w("j-bigint.json","[{\"id\":\"m1\",\"file\":\"src/mod.py\",\"old\":\"return 1\",\"new\":"+"9"*5000+"}]")
w("j-empty.json","[]")
w("j-bom.json","﻿"+json.dumps([{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"}]))
w("j-nan.json",'[{"id":"m1","file":"src/mod.py","old":"return 1","new":NaN}]')
PY
for j in deep obj dup escape abs nul bignew idweird types bigint empty bom nan; do
  fresh_root; ( ulimit -v 4000000; timeout 120 python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" --list "$H/j-$j.json" -- tests/test_fast.py ) > "$H/out/j-$j.out" 2>&1; rc=$?
  row "J-$j mutants file" "exit=$rc | traceback: $(grep -c Traceback $H/out/j-$j.out) | target file back: $(isback) | state: [$(statefiles)] | etc/hostname changed: $([ "$(cat /etc/hostname)" = "$(cat $H/hostname.copy)" ] && echo no || echo YES) | last: $(tail -1 $H/out/j-$j.out | cut -c1-100)"
done
fresh_root; ( timeout 300 python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" --list "$H/j-many.json" -- tests/test_fast.py ) > "$H/out/j-many.out" 2>&1; rc=$?
row "J-many 20000 mutants (3 plantable, rest do not apply)" "exit=$rc | traceback: $(grep -c Traceback $H/out/j-many.out) | file back: $(isback) | state: [$(statefiles)] | last: $(tail -1 $H/out/j-many.out | cut -c1-120)"

fresh_root; mut -- tests/test_fast.py <&- > "$H/out/i1.out" 2>&1; rc=$?
row "I1 standard input closed, normal run" "exit=$rc | traceback: $(grep -c Traceback $H/out/i1.out) | file back: $(isback) | msg: $(tail -1 $H/out/i1.out | cut -c1-90)"
fresh_root; ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --no-control --raw "$H/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py <&- >"$H/out/i2.out" 2>&1 ) & RP=$!; waitplant 0; kill -TERM $RP; wait $RP; rc=$?; sleep 1
row "I2 standard input closed, SIGTERM at plant" "exit=$rc | original text back: $(isback) | state: [$(statefiles)]"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
fresh_root; mut -- tests/test_fast.py >&- 2>&- ; rc=$?
row "I3 standard output and error closed, normal run" "exit=$rc | file back: $(isback) | state: [$(statefiles)]"
fresh_root; mut -- tests/test_fast.py > /dev/full 2>&1; rc=$?
row "I4 standard output is /dev/full" "exit=$rc | file back: $(isback) | state: [$(statefiles)]"
fresh_root; chmod 555 "$T/root/src"; chmod 444 "$T/root/src/mod.py"; mut -- tests/test_fast.py > "$H/out/p1.out" 2>&1; rc=$?
row "P1 src dir 555 and file 444 (running as uid $(id -u): root ignores modes)" "exit=$rc | traceback: $(grep -c Traceback $H/out/p1.out) | file back: $(isback) | mode: $(stat -c %a $T/root/src/mod.py)"
chmod -R u+w "$T/root"
fresh_root; if chattr +i "$T/root/src/mod.py" 2>/dev/null; then mut -- tests/test_fast.py > "$H/out/p2.out" 2>&1; rc=$?; chattr -i "$T/root/src/mod.py"; row "P2 file immutable (chattr +i)" "exit=$rc | traceback: $(grep -c Traceback $H/out/p2.out) | file back: $(isback) | state: [$(statefiles)] | msg: $(tail -1 $H/out/p2.out | cut -c1-100)"; else row "P2 file immutable (chattr +i)" "NOT RUN: chattr +i not supported here"; fi
fresh_root; if unshare -m bash -c "mount --bind $T/root/src $T/root/src && mount -o remount,ro,bind $T/root/src && python3 $RUN --root $T/root --sha $SHA --repo $T/repo --prefix X --no-control --raw $H/rawT --pythonpath $T/root/src --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py" > "$H/out/p3.out" 2>&1; then rc=0; else rc=$?; fi
row "P3 src/ is a read-only mount (unshare -m)" "exit=$rc | traceback: $(grep -c Traceback $H/out/p3.out) | file back: $(isback) | state: [$(statefiles)] | msg: $(tail -1 $H/out/p3.out | cut -c1-100)"
chmod -R u+w "$T/root" 2>/dev/null
for t in rm ln perm corrupt; do fresh_root; mut -- tests/test_$t.py > "$H/out/t-$t.out" 2>&1; rc=$?; chmod -R u+w "$T/root" 2>/dev/null
  row "T-$t test $t changes the file/dir under test during the run" "exit=$rc | traceback: $(grep -c Traceback $H/out/t-$t.out) | file is symlink: $([ -L $T/root/src/mod.py ] && echo yes || echo no) | file back: $(isback) | state: [$(statefiles)] | msg: $(grep -m1 -E 'RESTORE|restor|refus' $H/out/t-$t.out | cut -c1-100)"
done
fresh_root; rm -rf "${STATE:?}"; mkdir -p "$H/elsewhere"; ln -s "$H/elsewhere" "$STATE"; mut -- tests/test_fast.py > "$H/out/s1.out" 2>&1; rc=$?
row "S1 state folder is a symlink to another folder" "exit=$rc | files created in the target folder: $(ls -A $H/elsewhere | wc -l) | traceback: $(grep -c Traceback $H/out/s1.out) | msg: $(tail -1 $H/out/s1.out | cut -c1-100)"; rm -f "${STATE:?}"
fresh_root; python3 "$RUN" --root "$T/root" --restore > "$H/out/s2.out" 2>&1; rc=$?
row "S2 --restore with no marker at all" "exit=$rc | traceback: $(grep -c Traceback $H/out/s2.out) | msg: $(tail -1 $H/out/s2.out | cut -c1-100)"
echo "STRAY pytest at end: $(pgrep -f "$T/.*/.venv/bin/python -m pytest" | wc -l)"
echo HOSTILE-DONE
