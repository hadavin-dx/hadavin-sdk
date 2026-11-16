#!/bin/bash
# Safety tests T1-T20 of run.py on a TOY repository with made-up files (never the real code).
# usage: RUN=/path/to/run.py SCRATCH=/some/scratch/dir ./safety-tests.sh   (prints PASS/FAIL per check)
RUN=${RUN:-$(dirname "$(readlink -f "$0")")/run.py}
S=${SCRATCH:?set SCRATCH to a scratch folder outside every repository}
VENV=${VENV:?set VENV to a folder with bin/python that has pytest}
GIT=$(command -v git)
T=$S/toy; export TMPDIR=$S/tmpstate; STATE=$TMPDIR/hadavin-mutation-lane
rm -rf "$T" "$TMPDIR"; mkdir -p "$T/repo/src" "$T/repo/tests" "$TMPDIR" "$S/wrap"
cd "$T/repo" || exit 9; git init -q
printf 'def f():\n    return 1\n' > src/mod.py
printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    time.sleep(20)\n    assert f() == 1\n' > tests/test_slow.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 1\n' > tests/test_fast.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    open("junk.txt", "w").write("x")\n    assert f() == 1\n' > tests/test_junk.py
git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD)
fresh_root() { rm -rf "$T/root"; mkdir "$T/root"; git -C "$T/repo" archive "$SHA" | tar -x -C "$T/root"; ln -s "$VENV" "$T/root/.venv"; rm -rf "$S/rawT"; }
fresh_root
base() { python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" "$@"; }
mut() { base --id m1 --file "${FILE:-src/mod.py}" --old 'return 1' --new 'return 2' "$@"; }
last() { tail -1 "$T/root/src/mod.py" | tr -d ' '; }
real_last() { tail -1 "$T/repo/src/mod.py" | tr -d ' '; }
state_files() { ls "$STATE" 2>/dev/null | grep -v lock | tr '\n' ' '; }
chk() { if eval "$2"; then echo "  PASS: $1"; else echo "  FAIL: $1"; FAILS=$((FAILS+1)); fi; }
FAILS=0
bg() { mut "$@" -- tests/test_slow.py >/dev/null 2>&1 & RP=$!; }
echo "== T1 the real repository as --root is refused (exit 2)"
mut --root /home/user/hadavin-sdk -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T1 exit 2" "[ $rc -eq 2 ]"
echo "== T2 SIGKILL while a mutant is planted"
bg; sleep 4; echo "  file now: $(last)"; kill -9 $RP; sleep 1; pkill -9 -f "tests/test_slow.py"; wait $RP 2>/dev/null
chk "T2 file stays planted" "[ '$(last)' = return2 ]"
echo "== T3 the next run refuses and says how to restore"
mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T3 exit 2" "[ $rc -eq 2 ]"
echo "== T4 marker lost: the tree check against a fresh git archive still refuses"
mkdir -p "$S/mk"; mv "$STATE"/*.planted.json "$S/mk/"; mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T4 exit 2" "[ $rc -eq 2 ]"
mv "$S/mk"/*.planted.json "$STATE/"
echo "== T5 --restore puts the saved original back"
python3 "$RUN" --root "$T/root" --restore; chk "T5 file restored" "[ '$(last)' = return1 ]"; chk "T5 state folder empty" "[ -z '$(state_files)' ]"
echo "== T6 SIGTERM during a run restores the file and removes the marker"
bg; sleep 4; kill -TERM $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T6 exit 143" "[ $rc -eq 143 ]"; chk "T6 file restored" "[ '$(last)' = return1 ]"; chk "T6 state empty" "[ -z '$(state_files)' ]"
echo "== T7 SIGINT likewise, exit code read directly from \$?"
bg; sleep 4; kill -INT $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T7 exit 130" "[ $rc -eq 130 ]"; chk "T7 file restored" "[ '$(last)' = return1 ]"; chk "T7 state empty" "[ -z '$(state_files)' ]"
echo "== T8 two runs at once: the second is refused by the lock, and the first is still alive"
bg; sleep 4; mut -- tests/test_fast.py 2>&1 | cut -c1-120; rc=${PIPESTATUS[0]}; echo "  second run exit code $rc"
chk "T8 second refused (2)" "[ $rc -eq 2 ]"; chk "T8 first run still alive" "kill -0 $RP"; chk "T8 file still planted by the first" "[ '$(last)' = return2 ]"
kill -TERM $RP; wait $RP 2>/dev/null; chk "T8 file restored after" "[ '$(last)' = return1 ]"
echo "== T9 a clean run to the end: KILLED, backup gone, tree diff clean, exit 0"
mut -- tests/test_fast.py; rc=$?; echo "  exit code $rc"; chk "T9 exit 0" "[ $rc -eq 0 ]"; chk "T9 state empty" "[ -z '$(state_files)' ]"; grep -E "differing files|rc:" "$S/rawT/X-tree-diff.txt" | head -2
echo "== T10 absolute path as the mutant file is refused (exit 2), nothing planted"
FILE="$T/root/src/mod.py" mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T10 exit 2" "[ $rc -eq 2 ]"; chk "T10 file unchanged" "[ '$(last)' = return1 ]"; chk "T10 state empty" "[ -z '$(state_files)' ]"
echo "== T11 '..' in the mutant file is refused (exit 2)"
FILE="../root/src/mod.py" mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T11 exit 2" "[ $rc -eq 2 ]"; chk "T11 file unchanged" "[ '$(last)' = return1 ]"
echo "== T12 symlinked folders inside the scratch root"
fresh_root; ln -s "$T/repo" "$T/root/evil"
mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  (extra symlinked folder 'evil') exit code $rc"; chk "T12b exit 2" "[ $rc -eq 2 ]"; chk "T12b real repo file unchanged" "[ '$(real_last)' = return1 ]"
fresh_root; rm -rf "$T/root/src"; ln -s "$T/repo/src" "$T/root/src"
mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  (src itself is a link to the real repo) exit code $rc"; chk "T12a exit 2" "[ $rc -eq 2 ]"; chk "T12a real repo file unchanged" "[ '$(real_last)' = return1 ]"
echo "== T13 git cannot tell (rev-parse fails): fail closed"
printf '#!/bin/bash\nif [[ "$*" == *"--is-inside-work-tree"* ]]; then echo "fatal: detected dubious ownership in repository" >&2; exit 128; fi\nexec %s "$@"\n' "$GIT" > "$S/wrap/git"; chmod +x "$S/wrap/git"
fresh_root; PATH="$S/wrap:$PATH" mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  (work-tree check fails) exit code $rc"; chk "T13a exit 2" "[ $rc -eq 2 ]"
printf '#!/bin/bash\nif [[ "$*" == *"--show-toplevel"* ]]; then echo "fatal: detected dubious ownership in repository" >&2; exit 128; fi\nexec %s "$@"\n' "$GIT" > "$S/wrap/git"
fresh_root; PATH="$S/wrap:$PATH" mut -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  (show-toplevel fails) exit code $rc"; chk "T13b exit 2" "[ $rc -eq 2 ]"
rm -f "$S/wrap/git"
echo "== T14 a leftover file after the loop gives a non-zero exit; a declared --extra does not"
fresh_root; mut -- tests/test_junk.py >/dev/null 2>&1; rc=$?; echo "  undeclared leftover: exit code $rc"; chk "T14a exit 4" "[ $rc -eq 4 ]"
fresh_root; mut --extra junk.txt -- tests/test_junk.py >/dev/null 2>&1; rc=$?; echo "  declared --extra: exit code $rc"; chk "T14b exit 0" "[ $rc -eq 0 ]"
echo "== T15 SIGKILL of run.py leaves the test group alive; --restore stops it and restores"
fresh_root; bg; sleep 4; kill -9 $RP; sleep 1; chk "T15 orphan pytest alive" "pgrep -f 'pytest.*test_slow' >/dev/null"
python3 "$RUN" --root "$T/root" --restore; sleep 1; chk "T15 orphan stopped" "! pgrep -f 'pytest.*test_slow' >/dev/null"; chk "T15 file restored" "[ '$(last)' = return1 ]"
pkill -9 -f "pytest.*test_slow" 2>/dev/null
echo "== T16 SIGHUP restores too (exit 129)"
fresh_root; bg; sleep 4; kill -HUP $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T16 exit 129" "[ $rc -eq 129 ]"; chk "T16 file restored" "[ '$(last)' = return1 ]"
echo "== T17 --restore while a run is live is refused (lock)"
fresh_root; bg; sleep 4; python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-120; rc=${PIPESTATUS[0]}; echo "  exit code $rc"
chk "T17 exit 2" "[ $rc -eq 2 ]"; chk "T17 run still planted" "[ '$(last)' = return2 ]"; kill -TERM $RP; wait $RP 2>/dev/null
echo "== T18 a mutant id that climbs out of --raw is refused"
fresh_root; base --id ../escape --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T18 exit 2" "[ $rc -eq 2 ]"; chk "T18 no file outside raw" "[ ! -e '$S/escape.txt' ]"
echo "== T19 an error while the tests start (no .venv python) still removes the marker"
fresh_root; rm "$T/root/.venv"; mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T19 exit 2" "[ $rc -eq 2 ]"; chk "T19 file unchanged" "[ '$(last)' = return1 ]"; chk "T19 state empty" "[ -z '$(state_files)' ]"
echo "FAILED CHECKS: $FAILS"
