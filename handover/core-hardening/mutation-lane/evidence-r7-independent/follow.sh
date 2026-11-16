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


for t in rm ln; do fresh_root; mut -- tests/test_$t.py > "$H/out/t-$t.out" 2>&1; rc=$?
  python3 "$RUN" --root "$T/root" --restore > "$H/out/t-$t-restore.out" 2>&1; rr=$?
  row "T-$t then --restore" "run exit=$rc | restore exit=$rr | file regular+original back: $([ -L $T/root/src/mod.py ] && echo symlink || isback) | state: [$(statefiles)] | msg: $(tail -1 $H/out/t-$t-restore.out | cut -c1-160)"
done
fresh_root; bg; waitplant 2; mv "$T/root/src" "$T/root/src.moved"; ln -s "$T/root/src.moved" "$T/root/src"; kill -TERM $RP; wait $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"
python3 "$RUN" --root "$T/root" --restore > "$H/out/r2r.out" 2>&1; rr=$?
row "R2 then --restore (symlink still there)" "restore exit=$rr | real file text back: $(isback $T/root/src.moved/mod.py) | msg: $(tail -1 $H/out/r2r.out | cut -c1-160)"
rm -f "${T:?}/root/src"; mv "$T/root/src.moved" "$T/root/src"; python3 "$RUN" --root "$T/root" --restore > /dev/null 2>&1
row "R2 then rename back and --restore" "original text back: $(isback) | state: [$(statefiles)]"
echo FOLLOW-DONE
