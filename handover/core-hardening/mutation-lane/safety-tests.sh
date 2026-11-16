#!/bin/bash
# Safety tests T1-T28 of run.py on a TOY repository with made-up files (never the real code).
# usage: RUN=/path/to/run.py SCRATCH=/some/scratch/dir VENV=/folder/with/bin/python ./safety-tests.sh   (prints PASS/FAIL per check)
# Against an older copy of run.py: STATEDIR=<its state folder name> NEWTESTS=0 (T20-T29 test features the old copy lacks).
RUN=${RUN:-$(dirname "$(readlink -f "$0")")/run.py}
S=${SCRATCH:?set SCRATCH to a scratch folder outside every repository}
VENV=${VENV:?set VENV to a folder with bin/python that has pytest}
GIT=$(command -v git)
T=$S/toy; export TMPDIR=$S/tmpstate; STATE=$TMPDIR/${STATEDIR:-hadavin-mutation-lane-$(id -u)}; NEWTESTS=${NEWTESTS:-1}
REALREPO=$(git -C "$(dirname "$RUN")" rev-parse --show-toplevel)
rm -rf "$T" "$TMPDIR"; mkdir -p "$T/repo/src" "$T/repo/tests" "$TMPDIR" "$S/wrap"
cd "$T/repo" || exit 9; git init -q
printf 'def f():\n    return 1\n' > src/mod.py
printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    time.sleep(20)\n    assert f() == 1\n' > tests/test_slow.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 1\n' > tests/test_fast.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    open("junk.txt", "w").write("x")\n    assert f() == 1\n' > tests/test_junk.py
git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD)
fresh_root() { rm -rf "$T/root"; mkdir "$T/root"; git -C "$T/repo" archive "$SHA" | tar -x -C "$T/root"; ln -s "$VENV" "$T/root/.venv"; rm -rf "$S/rawT"; }
fresh_root
base() { python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" "$@"; }
mut() { base --id m1 --file "${FILE:-src/mod.py}" --old 'return 1' --new 'return 2' "$@"; }
last() { tail -1 "$T/root/src/mod.py" | tr -d ' '; }
real_last() { tail -1 "$T/repo/src/mod.py" | tr -d ' '; }
state_files() { ls -A "$STATE" 2>/dev/null | grep -v lock | tr '\n' ' '; }
chk() { if eval "$2"; then echo "  PASS: $1"; else echo "  FAIL: $1"; FAILS=$((FAILS+1)); fi; }
FAILS=0
orphan_alive() { pgrep -f "$T/root/.venv/bin/python -m pytest" >/dev/null; }
# waits for ANY marker AND the planted text, then 3 s so that pytest has really started (it does not wait for
# a "pgid" field: the old copy has none, and waiting for it would make old-code FAILs timing artefacts, review 4 M1)
waitplant() { for _ in $(seq 120); do ls "$STATE"/*.planted.json >/dev/null 2>&1 && [ "$(last)" = return2 ] && { sleep 3; return 0; }; sleep 0.5; done; return 1; }
# exec: $RP must be the python process itself, not a subshell around it
bg() { ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RP=$!; }
echo "== T1 the real repository as --root is refused (exit 2)"
mut --root "$REALREPO" -- tests/test_fast.py 2>&1 | cut -c1-200; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T1 exit 2" "[ $rc -eq 2 ]"
echo "== T2 SIGKILL while a mutant is planted"
bg; waitplant; echo "  file now: $(last)"; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
chk "T2 file stays planted" "[ '$(last)' = return2 ]"
echo "== T3 the next run refuses and says how to restore"
mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T3 exit 2" "[ $rc -eq 2 ]"
echo "== T4 marker lost: the tree check against a fresh git archive still refuses"
mkdir -p "$S/mk"; mv "$STATE"/*.planted.json "$S/mk/"; mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T4 exit 2" "[ $rc -eq 2 ]"
mv "$S/mk"/*.planted.json "$STATE/"
echo "== T5 --restore puts the saved original back"
python3 "$RUN" --root "$T/root" --restore; chk "T5 file restored" "[ '$(last)' = return1 ]"; chk "T5 state folder empty" "[ -z '$(state_files)' ]"
echo "== T6 SIGTERM during a run restores the file and removes the marker"
bg; waitplant; kill -TERM $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T6 exit 143" "[ $rc -eq 143 ]"; chk "T6 file restored" "[ '$(last)' = return1 ]"; chk "T6 state empty" "[ -z '$(state_files)' ]"
echo "== T7 SIGINT likewise, exit code read directly from \$?"
bg; waitplant; kill -INT $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T7 exit 130" "[ $rc -eq 130 ]"; chk "T7 file restored" "[ '$(last)' = return1 ]"; chk "T7 state empty" "[ -z '$(state_files)' ]"
echo "== T8 two runs at once: the second is refused by the lock, and the first is still alive"
bg; waitplant; mut -- tests/test_fast.py 2>&1 | cut -c1-120; rc=${PIPESTATUS[0]}; echo "  second run exit code $rc"
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
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; chk "T15 orphan pytest alive" "orphan_alive"
python3 "$RUN" --root "$T/root" --restore; sleep 1; chk "T15 orphan stopped" "! orphan_alive"; chk "T15 file restored" "[ '$(last)' = return1 ]"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T16 SIGHUP restores too (exit 129)"
fresh_root; bg; waitplant; kill -HUP $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T16 exit 129" "[ $rc -eq 129 ]"; chk "T16 file restored" "[ '$(last)' = return1 ]"
echo "== T17 --restore while a run is live is refused (lock)"
fresh_root; bg; waitplant; python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-120; rc=${PIPESTATUS[0]}; echo "  exit code $rc"
chk "T17 exit 2" "[ $rc -eq 2 ]"; chk "T17 run still planted" "[ '$(last)' = return2 ]"; kill -TERM $RP; wait $RP 2>/dev/null
echo "== T18 a mutant id that climbs out of --raw is refused"
fresh_root; base --id ../escape --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T18 exit 2" "[ $rc -eq 2 ]"; chk "T18 no file outside raw" "[ ! -e '$S/escape.txt' ]"
echo "== T19 an error while the tests start (no .venv python) still removes the marker"
fresh_root; rm "$T/root/.venv"; mut -- tests/test_fast.py 2>&1 | cut -c1-160; rc=${PIPESTATUS[0]}; echo "  exit code $rc"; chk "T19 exit 2" "[ $rc -eq 2 ]"; chk "T19 file unchanged" "[ '$(last)' = return1 ]"; chk "T19 state empty" "[ -z '$(state_files)' ]"
[ "$NEWTESTS" = 1 ] && {
echo "== T20 four signals in a row while a mutant is planted (5 times): file restored, marker gone, exit 129/130/143"
echo "  (probabilistic: it cannot force the second signal into the exact window; see T21 for the deterministic part)"
for i in 1 2 3 4 5; do fresh_root; bg; waitplant; kill -TERM $RP; kill -INT $RP; kill -HUP $RP; kill -TERM $RP; wait $RP; rc=$?
  chk "T20.$i exit 129/130/143 (got $rc)" "[ $rc -eq 129 -o $rc -eq 130 -o $rc -eq 143 ]"; chk "T20.$i file restored" "[ '$(last)' = return1 ]"; chk "T20.$i state empty" "[ -z '$(state_files)' ]"; done
echo "== T21 signal handler logic (deterministic): a signal while planted is only remembered, then delivered once"
python3 - "$RUN" <<'PY'
import importlib.util, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
S = r.SIG
def raises(fn, *a):
    try: fn(*a)
    except KeyboardInterrupt as e: return e.args
    return None
S.critical, S.allow = True, False                                   # mutant planted, tests not awaited
assert raises(r._term, signal.SIGTERM, None) is None and S.first == signal.SIGTERM and not S.fired
assert raises(r._term, signal.SIGINT, None) is None and S.first == signal.SIGTERM   # second signal: remembered only
S.allow = True                                                      # tests awaited: the first one unwinds, once
assert raises(r._term, signal.SIGHUP, None) == (signal.SIGTERM,) and S.fired and not S.allow
assert raises(r._term, signal.SIGTERM, None) is None                # nothing raises a second time
S.critical, S.allow, S.fired, S.first = False, False, False, None   # nothing planted: a signal unwinds at once, once
assert raises(r._term, signal.SIGINT, None) == (signal.SIGINT,) and raises(r._term, signal.SIGTERM, None) is None
S.critical, S.allow, S.fired, S.first = True, False, False, None    # remembered during the plant, delivered after
assert raises(r._term, signal.SIGINT, None) is None and raises(r.deliver_pending) == (signal.SIGINT,) and raises(r.deliver_pending) is None
print("handler logic ok")
PY
chk "T21 handler logic" "[ $? -eq 0 ]"
echo "== T22 state folder checks: wrong mode, a link, another owner are refused (exit 2)"
fresh_root; rm -rf "$STATE"; mkdir -m 755 "$STATE"; mut -- tests/test_fast.py 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T22a mode 755 refused (got $rc)" "[ $rc -eq 2 ]"
rm -rf "$STATE"; mkdir -m 700 "$S/elsewhere"; ln -s "$S/elsewhere" "$STATE"; mut -- tests/test_fast.py 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T22b symlinked state folder refused (got $rc)" "[ $rc -eq 2 ]"; chk "T22b nothing written through the link" "[ -z \"\$(ls -A $S/elsewhere)\" ]"
rm -f "$STATE"; mkdir -m 700 "$STATE"; if [ "$(id -u)" = 0 ]; then chown 65534 "$STATE"; mut -- tests/test_fast.py 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T22c other owner refused (got $rc)" "[ $rc -eq 2 ]"; else echo "  (not root: T22c skipped)"; fi
rm -rf "$STATE" "$S/elsewhere"
echo "== T23 forged state: a backup whose hash differs, a marker that is a link, --restore inside the real repository: all refused, nothing written"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
BK=$(ls "$STATE"/*.backup); printf 'def f():\n    return 99\n' > "$BK"
python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T23a hash mismatch refused (got $rc)" "[ $rc -eq 2 ]"; chk "T23a file not written" "[ '$(last)' = return2 ]"
git -C "$T/repo" show "$SHA:src/mod.py" > "$BK"; MK=$(ls "$STATE"/*.planted.json); mv "$MK" "$S/marker.real"; ln -s "$S/marker.real" "$MK"
python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T23b marker as a link refused (got $rc)" "[ $rc -eq 2 ]"; chk "T23b file not written" "[ '$(last)' = return2 ]"
rm "$MK"; mv "$S/marker.real" "$MK"; python3 "$RUN" --root "$T/root" --restore; chk "T23 genuine restore still works" "[ '$(last)' = return1 ]"
python3 "$RUN" --root "$(dirname "$RUN")" --restore 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T23c --restore in the real repository refused (got $rc)" "[ $rc -eq 2 ]"
echo "== T24 import check: the tests would load the target from another tree (exit 2); the right tree passes and is recorded"
fresh_root; base --pythonpath "$T/repo/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-220; rc=${PIPESTATUS[0]}; chk "T24a refused (got $rc)" "[ $rc -eq 2 ]"; chk "T24a file unchanged" "[ '$(last)' = return1 ]"
fresh_root; mut -- tests/test_fast.py >/dev/null 2>&1; chk "T24b recorded in the raw file" "grep -q 'import check: import mod -> .*(== root/src/mod.py: True)' '$S/rawT/X-m1.txt'"; chk "T24b raw file lists 4 environment names" "grep -q 'environment: HOME, PATH, PYTHONDONTWRITEBYTECODE, PYTHONPATH only' '$S/rawT/X-m1.txt'"
echo "== T25 pytest options that move the root, config or import base are refused after --"
fresh_root; for o in --basetemp=/x --rootdir=/x --junitxml=/x/y.xml --confcutdir=/x --override-ini=addopts=-x -cfoo.ini -oaddopts=-x --import-mode=append; do mut -- tests/test_fast.py "$o" >/dev/null 2>&1; rc=$?; chk "T25 $o refused (got $rc)" "[ $rc -eq 2 ]"; done
chk "T25 file unchanged, state empty" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
echo "== T26 the start hook fails after the tests were started: the test group is still stopped (review 4 M2)"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def boom(pid): raise RuntimeError("start hook failed")
try: r.run_tests(pathlib.Path(sys.argv[2]), ["tests/test_slow.py"], sys.argv[2] + "/src", 60, boom)
except RuntimeError as e: print("RuntimeError as expected:", e)
PY
sleep 1; chk "T26 no orphan pytest left" "! orphan_alive"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T27 a mutant whose new text equals the old text is refused (exit 2)"
fresh_root; base --id m1 --file src/mod.py --old 'return 1' --new 'return 1' -- tests/test_fast.py 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T27 exit 2 (got $rc)" "[ $rc -eq 2 ]"
echo "== T28 a clean run leaves no temporary file in the state folder"
fresh_root; mut -- tests/test_fast.py >/dev/null 2>&1; chk "T28 state empty (ls -A)" "[ -z '$(state_files)' ]"
}
echo "FAILED CHECKS: $FAILS"
