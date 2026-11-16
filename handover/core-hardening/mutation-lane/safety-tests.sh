#!/bin/bash
# Safety tests T1-T96 of run.py on a TOY repository with made-up files (never the real code).
# usage: RUN=/path/to/run.py SCRATCH=/some/scratch/dir VENV=/folder/with/bin/python ./safety-tests.sh   (prints PASS/FAIL per check)
# Round 7: run.py now runs the baseline BY DEFAULT; the helper base()/mut() adds --no-control (the old behaviour) unless NCF is set: `NCF= mut ...` runs with the real default. Against the r6 copy of run.py (no --no-control option) export NCF= (empty).
# Against an older copy of run.py: STATEDIR=<its state folder name> (NEWTESTS=0 runs only T1-T19; T36-T96 (rounds 4 to 9) need the new code; SKIP_T35=1 skips the test that writes to the shared /tmp folder).
# Round 8: ONLY="T76 T87" runs just those blocks. The shorter script is cut out of THIS file's own text at run time (the
# header, the chosen blocks, the closing lines), so a block that runs is byte-for-byte the shipped block; there is no separate
# copy to keep in step. A block that needs a helper defined inside another block must be listed together with it.
# Round 8: NOBASE_OPT=<empty> against the r6 copy of run.py (it has no --no-control option and runs without a baseline by default).
if [ -n "${ONLY:-}" ] && [ -z "${ONLY_CHILD:-}" ]; then
  SELF=$(readlink -f "$0"); DER=$(mktemp "${TMPDIR:-/tmp}/safety-only.XXXXXX.sh")
  awk -v only=" $ONLY " -v total="$(wc -l < "$SELF")" '
    NR >= total - 1 { next }
    !started && /^echo "== T1 / { started = 1; print "{" }
    started && /^echo "== T[0-9]+ / { match($0, /T[0-9]+/); tag = substr($0, RSTART, RLENGTH); keep = (index(only, " " tag " ") > 0) }
    started && $0 == "[ \"$NEWTESTS\" = 1 ] && {" { next }
    !started || keep { print }
    END { print "}"; print "echo \"FAILED CHECKS: $FAILS (of $CHECKS checks run; skipped:${SKIPPED:- none})\"" }
  ' "$SELF" > "$DER"
  ONLY_CHILD=1 bash "$DER"; rc=$?; rm -f "$DER"; exit $rc
fi
SELF_PATH=$(readlink -f "$0")
RUN=${RUN:-$(dirname "$SELF_PATH")/run.py}
S=${SCRATCH:?set SCRATCH to a scratch folder outside every repository}
VENV=${VENV:?set VENV to a folder with bin/python that has pytest}
GIT=$(command -v git)
T=$S/toy; export TMPDIR=$S/tmpstate; STATE=$TMPDIR/${STATEDIR:-hadavin-mutation-lane-$(id -u)}; NEWTESTS=${NEWTESTS:-1}
rm -rf "$T" "$TMPDIR"; mkdir -p "$T/repo/src" "$T/repo/tests" "$TMPDIR" "$S/wrap"
SL=$S/sleepbin; ln -sf "$(command -v sleep)" "$SL"   # a private name for sleep: pgrep/pkill on it never touch another run (parallel runs)
cd "$T/repo" || exit 9; git init -q
printf 'def f():\n    return 1\n' > src/mod.py
printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    time.sleep(20)\n    assert f() == 1\n' > tests/test_slow.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 1\n' > tests/test_fast.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    open("junk.txt", "w").write("x")\n    assert f() == 1\n' > tests/test_junk.py
mkdir docs; printf 'alpha\n' > docs/note.txt
printf 'import subprocess, sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_spawn():\n    subprocess.Popen(["'"$SL"'", "3137"])\n    time.sleep(30)\n' > tests/test_spawn.py
printf 'import sys, time\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_a():\n    print("before-timeout-marker", flush=True)\n\ndef test_b():\n    time.sleep(30)\n' > tests/test_partial.py
printf 'import os\nBAD = [k for k in os.environ if (k.startswith("PYTEST_") and k not in ("PYTEST_CURRENT_TEST", "PYTEST_VERSION")) or k in ("PYTHONSTARTUP", "PYTHONHOME", "PYTHONINSPECT", "PYTHONWARNINGS", "PYTHONUSERBASE")]\ndef test_env_clean():\n    assert BAD == [], BAD\n' > tests/test_env.py
printf 'def test_w():\n    open("conftest.py", "w").write("# written by a test\\n")\n' > tests/test_writeconf.py
printf 'def test_w():\n    open("data.bin", "w").write("x")\n' > tests/test_writedata.py
printf 'import subprocess\ndef test_bg():\n    subprocess.Popen(["'"$SL"'", "3141"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n' > tests/test_bg.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    assert f() == 99\n' > tests/test_fail.py
printf 'import pytest\n@pytest.mark.skip(reason="all skipped")\ndef test_s():\n    assert False\n' > tests/test_skip.py
printf 'X = 1\nopen("sidefx.txt", "w").write("x")\n' > src/sideeffect.py
printf 'import sys\nsys.path.insert(0, "src")\nfrom mod import f\ndef test_f():\n    open("'"$S"'/flipflag", "w").write("x")\n    assert f() == 1\n' > tests/test_flip.py
printf 'import os\ndef test_c():\n    os.chmod("src/mod.py", 0o600)\n' > tests/test_chmod.py
printf 'import os\ndef test_c():\n    os.chmod("src/mod.py", 0o444)\n' > tests/test_chmod_ro.py
printf 'import os\ndef test_c():\n    os.chmod("src/mod.py", 0o000)\n' > tests/test_chmod_000.py
printf 'import subprocess\ndef test_bg():\n    subprocess.Popen(["setsid", "'"$SL"'", "3143"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n' > tests/test_setsid.py
git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD); REALREPO=$T/repo   # the toy repository stands in for "the real repository" (this folder is not inside a git repository)
reset_state() { pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null; rm -rf "$STATE"; }
# every scenario starts from a fresh state folder, so a crash in one cannot make the next ones fail (review r2 safety M2)
fresh_root() { reset_state; rm -rf "$T/root"; mkdir "$T/root"; git -C "$T/repo" archive "$SHA" | tar -x -C "$T/root"; ln -s "$VENV" "$T/root/.venv"; rm -rf "$S/rawT"; }
fresh_root
printf '[{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"},{"id":"m2","file":"src/mod.py","old":"return 1","new":"return 3"}]' > "$S/two.json"
base() { python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" "$@"; }
mut() { base --id m1 --file "${FILE:-src/mod.py}" --old 'return 1' --new 'return 2' "$@"; }
last() { tail -1 "$T/root/src/mod.py" | tr -d ' '; }
real_last() { tail -1 "$T/repo/src/mod.py" | tr -d ' '; }
state_files() { ls -A "$STATE" 2>/dev/null | grep -v lock | tr '\n' ' '; }
CHECKS=0; SKIPPED=""
chk() { CHECKS=$((CHECKS+1)); if eval "$2"; then echo "  PASS: $1"; else echo "  FAIL: $1"; FAILS=$((FAILS+1)); fi; }
FAILS=0
orphan_alive() { pgrep -f "$T/root/.venv/bin/python -m pytest" >/dev/null; }
# waits for ANY marker AND the planted text, then 3 s so that pytest has really started (it does not wait for
# a "pgid" field: the old copy has none, and waiting for it would make old-code FAILs timing artefacts, review 4 M1)
waitplant() { for _ in $(seq 120); do ls "$STATE"/*.planted.json >/dev/null 2>&1 && [ "$(last)" = return2 ] && { sleep 3; return 0; }; sleep 0.5; done; return 1; }
# exec: $RP must be the python process itself, not a subshell around it
bg() { ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RP=$!; }
kill_planted() { fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null; }
keptstate() { [ -n "$(ls "$STATE"/*.planted.json 2>/dev/null)" ] && [ -n "$(ls "$STATE"/*.backup 2>/dev/null)" ]; }
inplace_restore() { python3 - "$RUN" "$T/root" "$1" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def boom(*a, **k): raise RuntimeError("an internal bug")
setattr(r, sys.argv[3], boom)
sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
r.main()
PY
}
planted_kept() { [ "$(last)" = return2 ] && keptstate; }
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
NCF= mut -- tests/test_fast.py; rc=$?; echo "  exit code $rc"; chk "T9 exit 0" "[ $rc -eq 0 ]"; chk "T9 state empty" "[ -z '$(state_files)' ]"; grep -E "differing files|rc:" "$S/rawT/X-tree-diff.txt" | head -2
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
fresh_root; NCF= mut --extra junk.txt -- tests/test_junk.py >/dev/null 2>&1; rc=$?; echo "  declared --extra: exit code $rc"; chk "T14b exit 0" "[ $rc -eq 0 ]"
echo "== T15 SIGKILL of run.py leaves the test group alive; --restore stops it and restores"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; chk "T15 orphan pytest alive" "orphan_alive"
python3 "$RUN" --root "$T/root" --restore; sleep 1; chk "T15 orphan stopped" "! orphan_alive"; chk "T15 file restored" "[ '$(last)' = return1 ]"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T16 SIGHUP restores too (exit 129)"
fresh_root; bg; waitplant; kill -HUP $RP; wait $RP; rc=$?; echo "  exit code $rc"; chk "T16 exit 129" "[ $rc -eq 129 ]"; chk "T16 file restored" "[ '$(last)' = return1 ]"
echo "== T17 --restore while a run is live is refused (lock): exit 3, because that run's mutant is planted (r7 review M1; r7 code: 2)"
fresh_root; bg; waitplant; python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-120; rc=${PIPESTATUS[0]}; echo "  exit code $rc"
chk "T17 exit 3 (got $rc)" "[ $rc -eq 3 ]"; chk "T17 run still planted" "[ '$(last)' = return2 ]"; kill -TERM $RP; wait $RP 2>/dev/null
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
python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T23a hash mismatch refused, exit 3 because a marker exists and the mutant may still be planted (got $rc)" "[ $rc -eq 3 ]"; chk "T23a file not written" "[ '$(last)' = return2 ]"
git -C "$T/repo" show "$SHA:src/mod.py" > "$BK"; MK=$(ls "$STATE"/*.planted.json); mv "$MK" "$S/marker.real"; ln -s "$S/marker.real" "$MK"
python3 "$RUN" --root "$T/root" --restore 2>&1 | cut -c1-150; rc=${PIPESTATUS[0]}; chk "T23b marker as a link refused, exit 3 (got $rc)" "[ $rc -eq 3 ]"; chk "T23b file not written" "[ '$(last)' = return2 ]"
rm "$MK"; mv "$S/marker.real" "$MK"; python3 "$RUN" --root "$T/root" --restore; chk "T23 genuine restore still works" "[ '$(last)' = return1 ]"
out=$(python3 "$RUN" --root "$T/repo" --repo "$T/repo" --restore 2>&1); rc=$?; echo "$out" | cut -c1-150; hit=$(printf %s "$out" | grep -c 'real repository'); chk "T23c --restore in the real repository refused for that reason (got $rc, reason hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"
echo "== T24 import check: the tests would load the target from another tree (exit 2); the right tree passes and is recorded"
fresh_root; base --pythonpath "$T/repo/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py 2>&1 | cut -c1-220; rc=${PIPESTATUS[0]}; chk "T24a refused (got $rc)" "[ $rc -eq 2 ]"; chk "T24a file unchanged" "[ '$(last)' = return1 ]"
fresh_root; mut -- tests/test_fast.py >/dev/null 2>&1; chk "T24b recorded in the raw file" "grep -q 'import check: import mod -> .*(== root/src/mod.py: True)' '$S/rawT/X-m1.txt'"; chk "T24b raw file lists 4 environment names" "grep -q 'environment: HOME, PATH, PYTHONDONTWRITEBYTECODE, PYTHONPATH only' '$S/rawT/X-m1.txt'"
echo "== T25 TESTS is an allowlist: every bypass named in review r2 is refused by the argument check (exit 2, message 'TESTS argument'), one check each"
fresh_root; printf -- '--collect-only\n' > "$S/args.txt"; ln -s "$T/repo/tests" "$T/root/linkout"
refuse() { lbl=$1; shift; out=$(mut -- tests/test_fast.py "$@" 2>&1); rc=$?; hit=$(printf %s "$out" | grep -c 'TESTS argument'); chk "T25 $lbl refused by the argument check (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"; }
refuse "@argsfile" "@$S/args.txt"
refuse "-k @argsfile" -k "@$S/args.txt"
refuse "-qc (clustered c)" -qc "$S/x.ini"
refuse "-qo (clustered o)" -qo "addopts=-x"
refuse "-qp (clustered p)" -qp "no:cacheprovider"
refuse "-c" -c "$S/x.ini"
refuse "-cfoo.ini" -cfoo.ini
refuse "-oaddopts=-x" -oaddopts=-x
refuse "--collect-only" --collect-only
refuse "--co" --co
refuse "--setup-plan" --setup-plan
refuse "--setup-only" --setup-only
refuse "--help" --help
refuse "-h" -h
refuse "--version" --version
refuse "-V" -V
refuse "--noconftest" --noconftest
refuse "--ignore=tests" --ignore=tests
refuse "--ignore tests" --ignore tests
refuse "-p other" -p other
refuse "-pother" -pother
refuse "-p (no value)" -p
refuse "-k (no value)" -k
refuse "--basetemp" --basetemp=/x
refuse "--rootdir" --rootdir=/x
refuse "--junitxml" --junitxml=/x/y.xml
refuse "--confcutdir" --confcutdir=/x
refuse "--override-ini" --override-ini=addopts=-x
refuse "--import-mode" --import-mode=append
for pl in runner skipping python terminal mark assertion capture fixtures logging main warnings debugging setuponly setupplan unittest faulthandler doctest monkeypatch recwarn stepwise junitxml pastebin; do refuse "-p no:$pl (core plugin)" -p "no:$pl"; done
refuse "-pno:runner (attached form)" -pno:runner
refuse "-p no:RANDOMLY (plugin names are exact)" -p no:RANDOMLY
refuse "-p no:randomly.runner" -p no:randomly.runner
refuse "-p no: (empty name)" -p no:
refuse "path ../ outside root" ../repo/tests
refuse "absolute path outside root" /etc
refuse "path through a link out of the root" linkout
refuse "-- terminator" --
chk "T25 file unchanged, state empty" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
fresh_root; NCF= mut -- -q -x -p no:randomly -k test_f -m "not slow" tests/test_fast.py::test_f >/dev/null 2>&1; rc=$?; chk "T25 the allowed forms still run (-q -x -p no:NAME -k -m path::node) (got $rc)" "[ $rc -eq 0 ]"
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
echo "== T29 stopping the test group fails (no permission): the leader is still stopped and signals stay disarmed (review r2 nit)"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def boom(pid): raise RuntimeError("start hook failed")
def cannot(pgid): raise PermissionError("not allowed")
r.stop_group = cannot
r.SIG.allow = True
try: r.run_tests(pathlib.Path(sys.argv[2]), ["tests/test_slow.py"], sys.argv[2] + "/src", 60, boom)
except (RuntimeError, PermissionError) as e: print("raised as expected:", type(e).__name__)
print("SIG.allow after:", r.SIG.allow)
sys.exit(0 if r.SIG.allow is False else 1)
PY
chk "T29 SIG.allow is False afterwards" "[ $? -eq 0 ]"
sleep 1; chk "T29 no orphan pytest left although stop_group failed" "! orphan_alive"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T30 import check fails closed: a target that is not a .py module is refused unless --skip-import-check (recorded)"
fresh_root; out=$(base --id m1 --file docs/note.txt --old alpha --new beta -- tests/test_fast.py 2>&1); rc=$?; echo "$out" | cut -c1-200; hit=$(printf %s "$out" | grep -c 'import check'); chk "T30a refused (rc $rc, 'import check' hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"; chk "T30a file unchanged" "[ \"\$(cat $T/root/docs/note.txt)\" = alpha ]"
fresh_root; NCF= base --skip-import-check --id m1 --file docs/note.txt --old alpha --new beta -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T30b with --skip-import-check it runs (rc $rc) and the raw file says so" "[ $rc -eq 0 ] && grep -q 'SKIPPED by --skip-import-check' '$S/rawT/X-m1.txt'"
echo "== T31 a timeout keeps the output printed before it"
fresh_root; base --timeout 6 --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_partial.py >/dev/null 2>&1; chk "T31 raw file says TIMEOUT and holds the early output" "grep -q 'VERDICT: TIMEOUT' '$S/rawT/X-m1.txt' && grep -q 'before-timeout-marker\\|^\\.' '$S/rawT/X-m1.txt'"; grep -A3 'output printed before' "$S/rawT/X-m1.txt" | head -5
chk "T31 file restored" "[ '$(last)' = return1 ]"
echo "== T32 special files are never read: a FIFO in the tree, and a FIFO as the marker, give a refusal (exit 2) instead of a hang"
fresh_root; mkfifo "$T/root/fifo"; timeout -s KILL 30 python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T32a FIFO in the tree refused, no hang (got $rc; 124 or 137 = hung)" "[ $rc -eq 2 ]"
fresh_root; KEY=$(printf %s "$(readlink -f "$T/root")" | sha256sum | cut -c1-16); mkdir -m 700 -p "$STATE"; mkfifo "$STATE/$KEY.planted.json"; timeout -s KILL 30 python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc=$?; chk "T32b FIFO as marker refused, no hang, exit 3 (got $rc; 124 or 137 = hung)" "[ $rc -eq 3 ]"
echo "== T33 a .venv folder deeper than the top is compared like any other folder (exit 2)"
fresh_root; mkdir -p "$T/root/src/.venv"; echo x > "$T/root/src/.venv/hidden.py"; mut -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T33 nested .venv refused (got $rc)" "[ $rc -eq 2 ]"
echo "== T34 test output that is not UTF-8 is replaced, not an error (fake python that prints byte 0xff and fails)"
fresh_root; rm "$T/root/.venv"; mkdir -p "$S/fakevenv/bin"; printf '#!/bin/sh\nprintf "\\377\\n"\nexit 1\n' > "$S/fakevenv/bin/python"; chmod +x "$S/fakevenv/bin/python"; ln -s "$S/fakevenv" "$T/root/.venv"
mut --skip-import-check -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T34 run ends normally (rc $rc: 5 = INCOMPLETE because of --no-control, r7) with verdict KILLED in the raw file" "[ $rc -eq 5 ] && grep -q 'VERDICT: KILLED' '$S/rawT/X-m1.txt'"; chk "T34 file restored" "[ '$(last)' = return1 ]"
echo "== T35 --restore with another TMPDIR: the marker kept by a run that used the default folder is found; exit 3 while the file is still planted"
if [ "${SKIP_T35:-0}" = 1 ]; then echo "  (T35 skipped on request: an older copy would write into a shared /tmp folder)"; SKIPPED="$SKIPPED T35"; elif [ -e "/tmp/hadavin-mutation-lane-$(id -u)" ]; then echo "  (skipped: /tmp/hadavin-mutation-lane-$(id -u) already exists and is not ours to touch)"; SKIPPED="$SKIPPED T35"; else
fresh_root; ( export TMPDIR=/tmp; exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RP=$!
for _ in $(seq 120); do ls /tmp/hadavin-mutation-lane-$(id -u)/*.planted.json >/dev/null 2>&1 && [ "$(last)" = return2 ] && { sleep 3; break; }; sleep 0.5; done
kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-220; chk "T35a exit 3 (got $rc) and the file is still planted" "[ $rc -eq 3 -a '$(last)' = return2 ]"
TMPDIR=/tmp python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T35b restoring with the right TMPDIR works" "[ '$(last)' = return1 ]"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; chk "T35c nothing planted anywhere: exit 0 (got $rc)" "[ $rc -eq 0 ]"
rm -f "/tmp/hadavin-mutation-lane-$(id -u)/$(printf %s "$(readlink -f "$T/root")" | sha256sum | cut -c1-16).lock"; rmdir "/tmp/hadavin-mutation-lane-$(id -u)" 2>/dev/null   # remove only what this test made
fi
echo "== T36 hard links (review r3 safety Major B): a target with two names would plant the mutant in the other file"
fresh_root; rm "$T/root/src/mod.py"; ln "$T/repo/src/mod.py" "$T/root/src/mod.py"; M0=$(stat -c %y "$T/repo/src/mod.py")
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; echo "$out" | cut -c1-200; hit=$(printf %s "$out" | grep -c 'exactly one name')
chk "T36a target hard-linked to a real repository file: refused for that reason (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"
chk "T36a the real repository file was not even touched (content and modification time)" "[ '$(real_last)' = return1 -a '$(stat -c %y "$T/repo/src/mod.py")' = '$M0' ]"
fresh_root; rm -rf "$S/plain"; mkdir "$S/plain"; git -C "$T/repo" archive "$SHA" | tar -x -C "$S/plain"; rm -rf "$T/root"; cp -al "$S/plain" "$T/root"; ln -s "$VENV" "$T/root/.venv"; M1=$(stat -c %y "$S/plain/src/mod.py")
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; hit=$(printf %s "$out" | grep -c 'exactly one name')
chk "T36b tree built with cp -al: refused (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"
chk "T36b the linked original was not touched" "[ '$(stat -c %y "$S/plain/src/mod.py")' = '$M1' ]"
rm -rf "$S/plain"
python3 - "$RUN" "$S" <<'PY'
import importlib.util, os, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
d = pathlib.Path(sys.argv[2]) / "hl"; d.mkdir(exist_ok=True)
a, b, c = d / "a.txt", d / "b.txt", d / "c.txt"
for x in (a, b, c): x.unlink(missing_ok=True)
a.write_bytes(b"original"); os.link(a, b); c.write_bytes(b"single")
try: r.write_target(a, b"CHANGED"); print("no refusal")
except r.Refused as e: print("refused:", str(e)[:90])
r.write_target(c, b"rewritten")
ok = a.read_bytes() == b"original" and b.read_bytes() == b"original" and c.read_bytes() == b"rewritten"
print("both names unchanged and a one-name file still written:", ok)
sys.exit(0 if ok else 1)
PY
chk "T36c write_target itself refuses a two-name file before truncating it, and still writes a one-name file" "[ $? -eq 0 ]"
echo "== T37 an ini file ABOVE --root would change what pytest runs (review r3 minor)"
fresh_root; printf '[pytest]\naddopts = --collect-only\n' > "$T/pytest.ini"
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; echo "$out" | cut -c1-200; hit=$(printf %s "$out" | grep -c 'outside --root')
chk "T37a pytest.ini above the root refused (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"; chk "T37a file unchanged, state empty" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
rm -f "$T/pytest.ini"; fresh_root; printf '[tool.pytest.ini_options]\naddopts = "--collect-only"\n' > "$T/pyproject.toml"
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; hit=$(printf %s "$out" | grep -c 'outside --root'); chk "T37b pyproject.toml with a pytest section above the root refused (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ]"
rm -f "$T/pyproject.toml"; fresh_root; printf '[metadata]\nname = x\n' > "$T/setup.cfg"
NCF= mut -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T37c a setup.cfg above WITHOUT a pytest section is no setting: the run goes ahead (rc $rc)" "[ $rc -eq 0 ]"; rm -f "$T/setup.cfg"
echo "== T38 --restore re-creates a deleted target with its recorded mode (review r3 minor)"
fresh_root; chmod 640 "$T/root/src/mod.py"; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
rm "$T/root/src/mod.py"; out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T38 exit 0 and the file is back with the original text (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ]"; chk "T38 mode 640 restored" "[ '$(stat -c %a "$T/root/src/mod.py" 2>/dev/null)' = 640 ]"; chk "T38 state empty" "[ -z '$(state_files)' ]"
echo "== T39 the orphan cannot be stopped (no permission) during --restore: the file is still restored (review r3 minor)"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; wait $RP 2>/dev/null
out=$(python3 - "$RUN" "$T/root" <<'PY' 2>&1
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def cannot(pgid): raise PermissionError(1, "Operation not permitted")
r.stop_group = cannot
ok, text = r.restore_from_marker(pathlib.Path(sys.argv[2]).resolve()); print(ok, text)
sys.exit(0 if ok else 1)
PY
); rc=$?; echo "$out" | cut -c1-260 | tail -3
chk "T39 file restored although stop_group raised PermissionError, and the result is NOT ok (the orphan may still run; r8 N2) (rc $rc)" "[ $rc -eq 1 -a '$(last)' = return1 ]"; chk "T39 the report says the orphan was not stopped" "printf %s '$out' | grep -q 'could NOT stop'"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T40 a signal right after the leader was reaped must not signal its (maybe reused) number (review r3 minor)"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, pathlib, signal, subprocess, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root = pathlib.Path(sys.argv[2]); calls = []
r.stop_group = lambda pgid: calls.append(pgid)
Real = subprocess.Popen; state = {"n": 0}
class P(Real):
    def communicate(self, *a, **k):
        res = super().communicate(*a, **k)               # the leader is waited for (reaped) here
        state["n"] += 1
        if state["n"] == 1: raise KeyboardInterrupt(int(signal.SIGTERM))   # the signal arrives just after
        return res
subprocess.Popen = P
try: r.run_tests(root, ["tests/test_fast.py"], str(root / "src"), 60)
except KeyboardInterrupt: print("interrupted as expected")
print("stop_group calls:", calls)
sys.exit(0 if not calls else 1)
PY
chk "T40 no signal was sent to the reaped leader's number" "[ $? -eq 0 ]"
echo "== T41 control run: a signal right after the fork, before the handle is stored, must not leak the test group (review r3 minor)"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, pathlib, signal, subprocess, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root = pathlib.Path(sys.argv[2]); Real = subprocess.Popen
def P(*a, **k):
    proc = Real(*a, **k)
    r._term(signal.SIGTERM, None)       # the handler runs here: after the fork, before `proc = ...` in run_tests
    return proc
subprocess.Popen = P
try: r.run_tests(root, ["tests/test_slow.py"], str(root / "src"), 60)
except KeyboardInterrupt as e: print("interrupted as expected", e.args)
PY
sleep 1; chk "T41 no orphan pytest left" "! orphan_alive"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T42 signals that used to kill run.py with the file still planted (review r3 minor): QUIT ABRT USR1 USR2 ALRM XCPU VTALRM PROF IO PWR"
ulimit -c 0
for sg in QUIT ABRT USR1 USR2 ALRM XCPU VTALRM PROF IO PWR; do
  fresh_root; bg; waitplant; kill -s $sg $RP; wait $RP; rc=$?; exp=$((128 + $(kill -l $sg))); sleep 1
  chk "T42 $sg exit $exp (got $rc)" "[ $rc -eq $exp ]"; chk "T42 $sg file restored" "[ '$(last)' = return1 ]"; chk "T42 $sg state empty" "[ -z '$(state_files)' ]"; chk "T42 $sg no orphan pytest" "! orphan_alive"
  pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
done
# edit the marker of a killed run: name=value sets a number, name= removes the field
setmarker() { python3 - "$STATE" "$@" <<'PY'
import glob, json, sys
f = glob.glob(sys.argv[1] + "/*.planted.json")[0]; m = json.load(open(f))
for a in sys.argv[2:]:
    k, _, v = a.partition("=")
    if v == "": m.pop(k, None)
    else: m[k] = json.loads(v)
open(f, "w").write(json.dumps(m))
PY
}
echo "== T43 --restore must not stop a stranger that has the orphan's number (review r3 minor: start time + full argument list)"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
( cd "$T/root" && exec setsid "$T/root/.venv/bin/python" -m pytest -q -p no:cacheprovider tests/test_slow.py >/dev/null 2>&1 ) & DP=$!; sleep 3
chk "T43 setup: the stranger (a pytest of its own that names the root) is its own group leader" "[ \"\$(ps -o pgid= -p $DP | tr -d ' ')\" = $DP ]"
setmarker pgid=$DP
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T43a restore exit 0 and the file is back (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ]"; chk "T43a the stranger was left alone" "kill -0 $DP"
kill -9 $DP 2>/dev/null; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null; wait $DP 2>/dev/null
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; wait $RP 2>/dev/null
setmarker start_ticks= argv=
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T43b a marker with a group but no recorded identity: file restored (rc $rc) and the group found by the recorded command (review r4 nit 7: fallback)" "[ $rc -eq 0 -a '$(last)' = return1 ] && ! orphan_alive"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; wait $RP 2>/dev/null
setmarker start_ticks= argv= cmd_argv= cmd_head= run_start_ticks=
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T43c a marker with a group and NO identity and NO command at all: file restored (rc $rc), nothing stopped on a guess, exit 3 because the group is unsettled (r8 N2)" "[ $rc -eq 3 -a '$(last)' = return1 ] && orphan_alive"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T44 the leader is dead but a member of the test group still runs: --restore stops it (review r3 minor)"
fresh_root; ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_spawn.py ) >/dev/null 2>&1 & RP=$!
waitplant; sleep 2
LEADER=$(pgrep -f "$T/root/.venv/bin/python -m pytest" | head -1); kill -9 $RP; kill -9 $LEADER; sleep 1; wait $RP 2>/dev/null
chk "T44 setup: the leader is gone, 'sleep 3137' (a member of its group) still runs" "pgrep -f '$SL 3137' >/dev/null && ! pgrep -f '$T/root/.venv/bin/python -m pytest' >/dev/null"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-220; sleep 1
chk "T44 restore exit 0, file back (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ]"; chk "T44 the surviving member was stopped" "! pgrep -f '$SL 3137' >/dev/null"; pkill -9 -f "$SL 3137" 2>/dev/null
echo "== T45 SIGKILL before the second marker (no group recorded yet): --restore finds the group by the command the first marker names (review r3 minor)"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; wait $RP 2>/dev/null
setmarker pgid= start_ticks= argv=
chk "T45 setup: the orphan runs" "orphan_alive"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200; sleep 1
chk "T45 restore exit 0, file back (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ]"; chk "T45 the orphan was stopped" "! orphan_alive"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T46 timeout branch with stop_group failing: signals disarmed BEFORE stop_group is called, the leader still stopped, and the result is a TIMEOUT verdict, not a traceback (review r4 evidence)"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
seen = []
def cannot(pgid): seen.append(r.SIG.allow); raise PermissionError("not allowed")
r.stop_group = cannot
try: res = r.run_tests(pathlib.Path(sys.argv[2]), ["tests/test_slow.py"], sys.argv[2] + "/src", 3)
except PermissionError as e: print("raised (old behaviour):", type(e).__name__); sys.exit(1)
print("rc:", res[1], "SIG.allow seen inside stop_group:", seen, "after:", r.SIG.allow)
sys.exit(0 if res[1] is None and "TIMEOUT" in res[2] and seen and seen[0] is False and r.SIG.allow is False else 1)
PY
chk "T46 SIG.allow was already False when the timeout branch called stop_group, and the result is TIMEOUT (no traceback)" "[ $? -eq 0 ]"
sleep 1; chk "T46 no orphan pytest left although stop_group failed in the timeout branch" "! orphan_alive"; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
fresh_root; python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >/dev/null 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
def cannot(pgid): raise PermissionError("not allowed")
r.stop_group = cannot
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--timeout", "3", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_slow.py"]
r.main()
PY
rc=$?
chk "T46b through run.py itself (stop_group failing, timeout 3 s): exit 5 INCOMPLETE (a TIMEOUT is no complete run; r5: 0) (got $rc), raw file says VERDICT: TIMEOUT, file restored, state empty" "[ $rc -eq 5 ] && grep -q 'VERDICT: TIMEOUT' '$S/rawT/X-m1.txt' && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null

echo "== T47 (review r4 M1) every signal that ends a process is handled, also while the file is planted and while it is restored"
fresh_root; python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY'
import importlib.util, os, pathlib, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
skip = {int(getattr(signal, n)) for n in ("SIGKILL", "SIGSTOP", "SIGCHLD", "SIGCONT", "SIGWINCH", "SIGURG", "SIGTSTP", "SIGTTIN", "SIGTTOU", "SIGPIPE", "SIGXFSZ") if hasattr(signal, n)}
want = sorted(int(x) for x in signal.valid_signals() if int(x) not in skip)
print("set equals valid_signals minus the six-plus-five excluded:", sorted(r.HANDLED_SIGNALS) == want, "(%d signals)" % len(want), flush=True)
orig = r.write_target; orig_rt = getattr(r, "restore_target", None)
bad = []
for window in ("plant", "restore"):
    for sg in want:
        n = {"c": 0}
        def wt(path, data, *a, _n=n, **k):
            _n["c"] += 1
            if _n["c"] == (1 if window == "plant" else 2): os.kill(os.getpid(), sg)   # the signal arrives INSIDE this window (r5 code: the restore is the 2nd write_target)
            return orig(path, data, *a, **k)
        def rt(*a, _n=n, **k):
            _n["c"] += 1
            if window == "restore" and _n["c"] == 1: os.kill(os.getpid(), sg)          # r6 code: the restore is restore_target
            return orig_rt(*a, **k)
        if hasattr(r, "restore_target"):
            r.restore_target = rt
            def wt2(path, data, *a, _n=n, **k):
                if window == "plant" and _n["c"] == 0: _n["c"] += 1; os.kill(os.getpid(), sg)
                return orig(path, data, *a, **k)
            r.write_target = wt2
        else: r.write_target = wt
        S = r.SIG; S.critical = S.allow = S.fired = S.exiting = False; S.first = None
        sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
        try: r.main(); code = 0
        except SystemExit as e: code = e.code
        txt = pathlib.Path(root, "src/mod.py").read_text()
        left = [f for f in os.listdir(r.STATE) if not f.endswith(".lock")]
        if code != 128 + sg or "return 1" not in txt or left: bad.append((window, sg, code, txt.strip()[-8:], left))
print(len(want) * 2, "cases (signal x window);", len(bad), "bad:", bad[:6], flush=True)
sys.exit(1 if bad or sorted(r.HANDLED_SIGNALS) != want else 0)
PY
chk "T47a all handled signals in the plant window and the restore window: exit 128+N, file restored, state empty" "[ $? -eq 0 ]"
echo "  T47b real signals sent from outside while the tests are awaited: TRAP RTMIN RTMAX SYS STKFLT(16) SEGV BUS FPE ILL"
ulimit -c 0
for sg in TRAP RTMIN RTMAX SYS 16 SEGV BUS FPE ILL; do
  fresh_root; bg; waitplant; kill -s $sg $RP; wait $RP; rc=$?; if [ "$sg" = 16 ]; then num=16; else num=$(kill -l $sg); fi; exp=$((128 + num)); sleep 1
  chk "T47b $sg exit $exp (got $rc), file restored, state empty, no orphan" "[ $rc -eq $exp ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ] && ! orphan_alive"
  pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
done
echo "== T48 (review r4 M2) pytest cannot take its root, settings or conftest from above --root"
fresh_root; mut -- tests/test_fast.py >/dev/null 2>&1; chk "T48a the command carries --rootdir and --confcutdir (both = root)" "grep -q -- '--rootdir=$T/root --confcutdir=$T/root' '$S/rawT/X-m1.txt'"
refuse_above() { lbl=$1; fresh_root; eval "$2"; out=$(mut -- tests/test_fast.py 2>&1); rc=$?; hit=$(printf %s "$out" | grep -c 'outside --root'); chk "T48 $lbl above the root refused (rc $rc, hits $hit)" "[ $rc -eq 2 -a $hit -ge 1 ] && [ '$(last)' = return1 -a -z '$(state_files)' ]"; rm -f "$T/setup.py" "$T/conftest.py" "$T/pyproject.toml" "$T/tox.ini" "$T/setup.cfg" "$T/pytest.ini"; }
refuse_above "setup.py" "printf 'from setuptools import setup\nsetup()\n' > '$T/setup.py'"
refuse_above "conftest.py" "printf 'def pytest_collection_modifyitems(items):\n    items.clear()\n' > '$T/conftest.py'"
refuse_above "pyproject.toml WITHOUT a pytest section" "printf '[project]\nname = \"x\"\n' > '$T/pyproject.toml'"
refuse_above "pyproject.toml with a dotted-key pytest setting" "printf 'tool.pytest.ini_options.addopts = \"--collect-only\"\n' > '$T/pyproject.toml'"
refuse_above "tox.ini with a pytest section" "printf '[pytest]\naddopts = --collect-only\n' > '$T/tox.ini'"
refuse_above "setup.cfg with a pytest section" "printf '[tool:pytest]\naddopts = --collect-only\n' > '$T/setup.cfg'"
fresh_root; printf '[pytest]\naddopts = -q\n' > "$T/root/pytest.ini"; NCF= mut --extra pytest.ini -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T48 an ini file INSIDE the root is accepted (rc $rc) and the raw file records a normal verdict" "[ $rc -eq 0 ] && grep -q 'VERDICT: KILLED' '$S/rawT/X-m1.txt'"
python3 - "$RUN" "$S" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
d = pathlib.Path(sys.argv[2]) / "cfgparse"; d.mkdir(exist_ok=True)
cases = {
 "dotted": ('tool.pytest.ini_options.addopts = "-x"\n', True),
 "inline table": ('tool = { pytest = { ini_options = { addopts = "-x" } } }\n', True),
 "standard table": ('[tool.pytest.ini_options]\naddopts = "-x"\n', True),
 "native table": ('[tool.pytest]\naddopts = ["-x"]\n', True),
 "no pytest section": ('[project]\nname = "x"\n[tool.ruff]\nline-length = 100\n', False),
 "other tool only": ('[tool.pytester]\nx = 1\n', False),
 "not valid toml": ('[tool.pytest\n', True),
}
bad = []
for name, (text, want) in cases.items():
    (d / "pyproject.toml").write_text(text)
    got = bool(r.pytest_config_in(d))
    if got != want: bad.append((name, got, want))
print("pyproject cases wrong:", bad)
sys.exit(1 if bad else 0)
PY
chk "T48 pyproject.toml is parsed: dotted keys, inline tables, native table found; no section and look-alike table not; invalid TOML counted (fail closed)" "[ $? -eq 0 ]"
echo "== T49 (review r4 M3) a mutant's tests that change the tree stop the loop before the next mutant"
printf '[{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"},{"id":"m2","file":"src/mod.py","old":"return 1","new":"return 3"}]' > "$S/two.json"
for tf in test_writeconf.py test_writedata.py; do
  fresh_root; out=$(base --list "$S/two.json" -- tests/$tf 2>&1); rc=$?; echo "$out" | cut -c1-200 | tail -3
  chk "T49 $tf: exit 4 (got $rc), the loop stopped after m1 (no X-m2.txt), m1's raw file records the changed file" "[ $rc -eq 4 ] && [ ! -e '$S/rawT/X-m2.txt' ] && grep -q 'tree integrity after this mutant: .*differing files (1; 0 = clean)' '$S/rawT/X-m1.txt'"
  chk "T49 $tf: target file restored, state empty" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
done
fresh_root; NCF= base --list "$S/two.json" -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T49 a clean two-mutant run: exit 0 (got $rc), both raw files record 'differing files (0; 0 = clean): []' and a digest" "[ $rc -eq 0 ] && grep -q 'digest [0-9a-f]\{16\}; differing files (0; 0 = clean): \[\]' '$S/rawT/X-m1.txt' && grep -q 'differing files (0; 0 = clean): \[\]' '$S/rawT/X-m2.txt'"
echo "== T50 (review r4 evidence) unreaped_child and the reaped-leader guard, tested directly"
fresh_root; python3 - "$RUN" "$T/root" <<'PY'
import importlib.util, os, pathlib, signal, subprocess, sys, time
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root = pathlib.Path(sys.argv[2])
c = subprocess.Popen(["sleep", "30"]); ok1 = r.unreaped_child(c.pid)
c.kill(); time.sleep(0.3); ok2 = r.unreaped_child(c.pid)          # exited, not yet waited for (zombie)
c.wait(); ok3 = r.unreaped_child(c.pid)                          # reaped
print("running:", ok1, "zombie:", ok2, "reaped:", ok3)
if not (ok1 and ok2 and not ok3): sys.exit(1)
# the leader is reaped behind Popen's back (returncode still None) and the signal arrives: no stop_group call
calls = []; r.stop_group = lambda pgid: calls.append(pgid)
Real = subprocess.Popen; st = {"n": 0}
class P(Real):
    def communicate(self, *a, **k):
        st["n"] += 1
        if st["n"] == 1:
            os.waitpid(self.pid, 0); raise KeyboardInterrupt(int(signal.SIGTERM))   # reaped by someone else, returncode None
        return ("", 0)
subprocess.Popen = P
try: r.run_tests(root, ["tests/test_fast.py"], str(root / "src"), 60)
except KeyboardInterrupt: pass
print("returncode still None, leader reaped: stop_group calls:", calls)
sys.exit(0 if not calls else 1)
PY
chk "T50 unreaped_child true while running and as a zombie, false once reaped; no stop_group call for a reaped leader whose returncode is None" "[ $? -eq 0 ]"
echo "== T51 (review r4 evidence) --restore identity checks: start time, dead leader, works_in"
getm() { python3 - "$STATE" "$1" <<'PY'
import glob, json, sys
m = json.load(open(glob.glob(sys.argv[1] + "/*.planted.json")[0])); print(json.dumps(m[sys.argv[2]]))
PY
}
startof() { python3 -c 'import sys; d=open("/proc/%s/stat"%sys.argv[1]).read(); print(d[d.rindex(")")+2:].split()[19])' "$1"; }
mapfile_argv() { ARGV=(); while IFS= read -r l; do ARGV+=("$l"); done < <(python3 -c 'import json,sys; print("\n".join(json.loads(sys.argv[1])))' "$1"); }
# a) same command line, different start time: left alone; with the start time equal it is taken for the orphan (so the start time is the discriminator)
for variant in different equal; do
  fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
  mapfile_argv "$(getm argv)"
  ( cd "$T/root" && exec setsid "${ARGV[@]}" >/dev/null 2>&1 ) & DP=$!; sleep 3
  [ $variant = equal ] && setmarker pgid=$DP start_ticks=$(startof $DP) || setmarker pgid=$DP
  out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200; sleep 1
  if [ $variant = different ]; then chk "T51a identical command line, other start time: stranger left alone, file restored (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ] && kill -0 $DP"
  else chk "T51a (control) identical command line AND identical start time: stopped (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ] && ! kill -0 $DP 2>/dev/null"; fi
  kill -9 $DP 2>/dev/null; wait $DP 2>/dev/null; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
done
# b) the leader is dead, a member of its group lives on: stopped only if it started after the recorded start AND works in root
member() { # $1 = folder the member works in
  ( cd "$1" && exec setsid sh -c "$SL 3142 & exec $SL 3143" >/dev/null 2>&1 ) & DP=$!; sleep 1; kill -9 $DP 2>/dev/null; wait $DP 2>/dev/null; sleep 0.5; }
for variant in outside-root early-start control; do
  fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
  if [ $variant = outside-root ]; then member /; else member "$T/root"; fi
  if [ $variant = early-start ]; then setmarker pgid=$DP start_ticks=99999999999; else setmarker pgid=$DP start_ticks=1; fi
  chk "T51b $variant setup: the member of the dead leader's group runs" "pgrep -f '$SL 3142' >/dev/null"
  out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200; sleep 1
  if [ $variant = control ]; then chk "T51b control (member works in root, started after the recorded start): stopped (rc $rc)" "[ $rc -eq 0 -a '$(last)' = return1 ] && ! pgrep -f '$SL 3142' >/dev/null"
  else chk "T51b $variant: member left alone, file restored, exit 3 because the group is unsettled (r8 N2) (rc $rc)" "[ $rc -eq 3 -a '$(last)' = return1 ] && pgrep -f '$SL 3142' >/dev/null && keptstate"; fi
  pkill -9 -f "$SL 314[23]" 2>/dev/null
done
# c) works_in matches whole path parts
python3 - "$RUN" "$T" <<'PY'
import importlib.util, pathlib, subprocess, sys, time
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
t = pathlib.Path(sys.argv[2]); root = t / "root"
def start(arg, cwd="/"):
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", arg], cwd=cwd)
ps = {"sibling prefix (root2/x)": (start(str(t / "root2/x")), False), "inside (root/x)": (start(str(root / "x")), True),
      "root itself": (start(str(root)), True), "cwd inside root": (start("zzz", str(root)), True), "unrelated": (start("/etc/hosts"), False)}
time.sleep(0.5); bad = []
for name, (p, want) in ps.items():
    got = r.works_in(p.pid, root)
    if got != want: bad.append((name, got, want))
    p.kill(); p.wait()
print("works_in wrong:", bad); sys.exit(1 if bad else 0)
PY
chk "T51c works_in matches whole path parts: /root2/x is not inside /root" "[ $? -eq 0 ]"
echo "== T52 (review r4 nit 1) a plant that fails on the open file is a clean refusal, not RESTORE FAILED; --restore with the file already original clears the marker"
fresh_root; python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >"$S/t52.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
def ro(path, data, *a, **k): raise PermissionError(13, "Permission denied")   # a read-only file: the open fails every time
r.write_target = ro
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t52.out"
chk "T52a read-only target: exit 2 (got $rc) with 'cannot plant', no 'RESTORE FAILED', file unchanged, state empty" "[ $rc -eq 2 ] && grep -q 'cannot plant' '$S/t52.out' && ! grep -q 'RESTORE FAILED' '$S/t52.out' && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
git -C "$T/repo" show "$SHA:src/mod.py" > "$S/orig-mod.txt"; rm "$T/root/src/mod.py"; ln "$S/orig-mod.txt" "$T/root/src/mod.py"   # already the original text, but with two names
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T52b file already equals the backup (two names): --restore exit 0 (got $rc), marker and backup cleared, nothing written" "[ $rc -eq 0 ] && [ -z '$(state_files)' ] && [ '$(last)' = return1 ]"
echo "== T53 (review r4 nit 2) a FIFO in place of the target: --restore refuses instead of hanging"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
rm "$T/root/src/mod.py"; mkfifo "$T/root/src/mod.py"; timeout -s KILL 30 python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc=$?
chk "T53 FIFO as the target at --restore (valid marker): exit 3 (restore failed, r6 review M1; r6 code: 2), no hang (got $rc; 124 or 137 = hung), marker and backup kept" "[ $rc -eq 3 ] && [ -n \"\$(ls $STATE/*.planted.json 2>/dev/null)\" ] && [ -n \"\$(ls $STATE/*.backup 2>/dev/null)\" ]"
rm -f "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T53 and the genuine restore works afterwards" "[ '$(last)' = return1 ]"
echo "== T54 (review r4 nit 4) ANY file in the tree with two names is refused, not only the target"
fresh_root; echo alpha > "$S/outside-note.txt"; rm "$T/root/docs/note.txt"; ln "$S/outside-note.txt" "$T/root/docs/note.txt"
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; echo "$out" | cut -c1-200; hit=$(printf %s "$out" | grep -c 'docs/note.txt.*exactly one name')
chk "T54 hard-linked docs/note.txt refused naming the file (rc $rc, hits $hit); target untouched" "[ $rc -eq 2 -a $hit -ge 1 ] && [ '$(last)' = return1 -a -z '$(state_files)' ]"
echo "== T55 (review r4 nit 5) a background process that outlives the test leader is stopped and recorded"
fresh_root; base --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_bg.py >/dev/null 2>&1; rc=$?; sleep 1
chk "T55a leftover 'sleep 3141' stopped (rc $rc), the raw file says so" "! pgrep -f '$SL 3141' >/dev/null && grep -q 'STOPPED 1 process' '$S/rawT/X-m1.txt'"; pkill -9 -f "$SL 3141" 2>/dev/null
echo "  T55b control run killed with SIGKILL: --restore stops its test group"
fresh_root; ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --control --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RP=$!
for _ in $(seq 60); do orphan_alive && break; sleep 0.5; done; sleep 3
kill -9 $RP; sleep 1; wait $RP 2>/dev/null; chk "T55b setup: the control run's pytest still runs" "orphan_alive"
out=$(mut -- tests/test_fast.py 2>&1); rc=$?; chk "T55b the next run refuses and points at --restore (rc $rc)" "[ $rc -eq 2 ] && printf %s '$out' | grep -q -- '--restore'"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200; sleep 1
chk "T55b --restore exit 0 (got $rc), the orphaned control test group stopped, state empty, file unchanged" "[ $rc -eq 0 ] && ! orphan_alive && [ -z '$(state_files)' ] && [ '$(last)' = return1 ]"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
echo "== T56 (review r4 nit 9) no /proc, no waitid: a refusal at the start, on any option"
python3 - "$RUN" "$T/root" <<'PY' >"$S/t56.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
sys.platform = "darwin"; sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t56.out"; chk "T56 non-Linux: exit 2 (got $rc) with 'Linux only'" "[ $rc -eq 2 ] && grep -q 'Linux only' '$S/t56.out'"
echo "== T57 (review r4 nit 10) the restore command in the refusal carries --repo; --restore needs no git repository"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
out=$(mut -- tests/test_fast.py 2>&1); echo "$out" | cut -c1-260
chk "T57a the printed command contains --repo $T/repo" "printf %s '$out' | grep -q -- '--repo $T/repo'"
rm -rf "$S/nogit"; mkdir "$S/nogit"; cp "$RUN" "$S/nogit/run.py"
out=$(python3 "$S/nogit/run.py" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T57b --restore from a copy of the script in a folder that is no git repository: exit 0 (got $rc), file back" "[ $rc -eq 0 -a '$(last)' = return1 ]"
out=$(python3 "$S/nogit/run.py" --root "$T/repo" --restore 2>&1); rc=$?; hit=$(printf %s "$out" | grep -c 'git entry\|real repository\|\.git entry'); chk "T57c a restore on the real repository is still refused without --repo (rc $rc)" "[ $rc -eq 2 ]"
rm -rf "$S/nogit"
echo "== T58 (review r4 nit 11) output files never follow a link; reap waits for the leader it killed"
fresh_root; echo untouched > "$S/victim.txt"; mkdir -p "$S/rawT"; ln -s "$S/victim.txt" "$S/rawT/X-m1.txt"
mut -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T58a --raw file is a link: exit 2 (got $rc), the victim is untouched, nothing planted" "[ $rc -eq 2 ] && [ \"\$(cat $S/victim.txt)\" = untouched ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
fresh_root; mkdir -p "$S/rawT"; ln -s "$S/victim.txt" "$S/out.json"
mut --out-json "$S/out.json" -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T58b --out-json is a link: exit 2 (got $rc), victim untouched, nothing planted" "[ $rc -eq 2 ] && [ \"\$(cat $S/victim.txt)\" = untouched ] && [ '$(last)' = return1 ]"
fresh_root; rm -rf "$S/rawlink" "$S/rawreal"; mkdir "$S/rawreal"; ln -s "$S/rawreal" "$S/rawlink"
python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawlink" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T58c --raw is a symbolic link to a folder: exit 2 (got $rc), nothing written into it" "[ $rc -eq 2 ] && [ -z \"\$(ls -A $S/rawreal)\" ]"
rm -rf "$S/rawlink" "$S/rawreal" "$S/out.json" "$S/victim.txt"
python3 - "$RUN" <<'PY'
import importlib.util, os, subprocess, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
p = subprocess.Popen(["sleep", "100"], stdout=subprocess.PIPE, start_new_session=True)
r.reap(p, wait=1)
try: os.waitpid(p.pid, os.WNOHANG); zombie_or_alive = True    # still our child: not waited for
except ChildProcessError: zombie_or_alive = False
print("returncode after reap:", p.returncode, "still unreaped child:", zombie_or_alive)
sys.exit(0 if p.returncode is not None and not zombie_or_alive else 1)
PY
chk "T58d reap kills AND waits: no zombie, returncode set" "[ $? -eq 0 ]"
echo "== T59 (review r4 nit 12) the restored mode does not depend on the umask"
fresh_root; chmod 640 "$T/root/src/mod.py"; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
rm "$T/root/src/mod.py"; ( umask 077; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1 )
chk "T59 mode 640 after a restore under umask 077 (got $(stat -c %a "$T/root/src/mod.py" 2>/dev/null))" "[ '$(stat -c %a "$T/root/src/mod.py" 2>/dev/null)' = 640 -a '$(last)' = return1 ]"
echo "== T60 (review r4 nit 3) a folder swapped for a link between the path check and the write is not followed"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
mkdir -p "$S/evil"; printf 'def f():\n    return 424242\n' > "$S/evil/mod.py"
python3 - "$RUN" "$T/root" "$S/evil" <<'PY' >"$S/t60.out" 2>&1
import importlib.util, os, pathlib, shutil, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, evil = pathlib.Path(sys.argv[2]), sys.argv[3]
real = r.safe_rel
def swapped(base, rel, what, must_exist=True):
    out = real(base, rel, what, must_exist)          # the checks pass ...
    if what == "marker file":                         # ... and then the folder is replaced by a link
        shutil.move(str(root / "src"), str(root / "src.moved")); os.symlink(evil, root / "src")
    return out
r.safe_rel = swapped
try: print(r.restore_from_marker(root))
except r.Refused as e: print("REFUSED:", str(e)[:150])
PY
cut -c1-220 "$S/t60.out"
chk "T60 the file behind the swapped link was not written" "[ \"\$(tail -1 $S/evil/mod.py | tr -d ' ')\" = return424242 ]"
rm -rf "$S/evil"
echo "== T62 (review r4 nit 4) a bind mount inside the root (one name per file, same filesystem) is refused"
fresh_root; rm -rf "$S/mntsrc"; mkdir -p "$S/mntsrc"; cp -a "$T/root/docs/." "$S/mntsrc/"   # same content as docs/: the tree comparison alone cannot see the mount
if mount --bind "$S/mntsrc" "$T/root/docs" 2>/dev/null; then
  mut -- tests/test_fast.py > "$S/t62.out" 2>&1; rc=$?; umount "$T/root/docs"; cut -c1-200 "$S/t62.out"
  chk "T62 mount point docs/ refused for that reason (rc $rc)" "[ $rc -eq 2 ] && grep -q 'mount point' '$S/t62.out'"
  chk "T62 nothing planted, bind source untouched" "[ '$(last)' = return1 -a -z '$(state_files)' ] && [ \"\$(cat $S/mntsrc/note.txt)\" = alpha ]"
else echo "  (mount --bind not permitted here: T62 skipped)"; SKIPPED="$SKIPPED T62"; fi
rm -rf "$S/mntsrc"
python3 - "$RUN" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
real_mp = r.mount_points
r.mount_points = lambda: [pathlib.Path("/"), pathlib.Path("/a/root"), pathlib.Path("/a/root/.venv"), pathlib.Path("/a/root/with space/m"), pathlib.Path("/a/root2/x")]
root = pathlib.Path("/a/root")
ok = True
try: r.refuse_mounts(root); ok = False; print("no refusal for a mount inside")
except r.Refused as e: print("refused:", str(e)[:80])
r.mount_points = lambda: [pathlib.Path("/"), pathlib.Path("/a/root"), pathlib.Path("/a/root/.venv"), pathlib.Path("/a/root2/x")]
r.refuse_mounts(root); print("root itself, .venv and a sibling prefix (/a/root2) are no refusal")
got = real_mp("36 25 0:31 / /a/root/with\\040space/m rw - tmpfs tmpfs rw\n37 25 0:32 / /a/root/back\\134slash rw - tmpfs tmpfs rw\n")
print("parsed:", [str(x) for x in got])
ok = ok and [str(x) for x in got] == ["/a/root/with space/m", "/a/root/back\\slash"]
sys.exit(0 if ok else 1)
PY
chk "T62b refuse_mounts logic: a mount inside is refused; the root, .venv and a sibling prefix are not" "[ $? -eq 0 ]"
echo "== T61 (review r4 evidence) PYTEST_ADDOPTS, PYTEST_PLUGINS and other steering variables of the caller never reach the tests"
fresh_root; PYTEST_ADDOPTS="--collect-only" PYTEST_PLUGINS="no_such_plugin_xyz" PYTHONSTARTUP=/nonexistent PYTEST_DEBUG=1 NCF= mut -- tests/test_env.py >/dev/null 2>&1; rc=$?
chk "T61 with those set in the caller's environment the tests run and see none of them (rc $rc, verdict SURVIVED, '1 passed')" "[ $rc -eq 0 ] && grep -q 'VERDICT: SURVIVED' '$S/rawT/X-m1.txt' && grep -q 'pytest summary line: 1 passed' '$S/rawT/X-m1.txt'"

echo "== T63 (review r5 M3) a decoy folder that holds the ORIGINAL bytes: the restore must not report success on the decoy"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null
rm -rf "$S/decoy"; mkdir -p "$S/decoy"; git -C "$T/repo" show "$SHA:src/mod.py" > "$S/decoy/mod.py"
python3 - "$RUN" "$T/root" "$S/decoy" <<'PY' >"$S/t63a.out" 2>&1
import importlib.util, os, pathlib, shutil, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, decoy = pathlib.Path(sys.argv[2]), sys.argv[3]
real = r.safe_rel
def swapped(base, rel, what, must_exist=True):
    out = real(base, rel, what, must_exist)          # the checks pass ...
    if what == "marker file":                         # ... then the folder is replaced by a link to a decoy that holds the ORIGINAL bytes
        shutil.move(str(root / "src"), str(root / "src.moved")); os.symlink(decoy, root / "src")
    return out
r.safe_rel = swapped
try: print(r.restore_from_marker(root))
except r.Refused as e: print("REFUSED:", str(e)[:150])
PY
cut -c1-220 "$S/t63a.out"
chk "T63a --restore through a swapped folder: NOT reported as restored; marker and backup kept; the planted file behind the swap is still planted (r5 cleared the marker and left it planted); decoy untouched" "[ -n \"\$(ls $STATE/*.planted.json 2>/dev/null)\" ] && [ -n \"\$(ls $STATE/*.backup 2>/dev/null)\" ] && [ \"\$(tail -1 $T/root/src.moved/mod.py | tr -d ' ')\" = return2 ] && ! grep -q 'hash matches saved original: True' '$S/t63a.out' && [ \"\$(tail -1 $S/decoy/mod.py | tr -d ' ')\" = return1 ]"
rm -f "$T/root/src"; mv "$T/root/src.moved" "$T/root/src"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
chk "T63a the kept marker still allows a genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
fresh_root
python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" "$S/decoy" <<'PY' >"$S/t63b.out" 2>&1
import importlib.util, os, shutil, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw, decoy = sys.argv[2:7]
real = r.safe_rel
def swapped(base, rel, what, must_exist=True):
    out = real(base, rel, what, must_exist)
    if "before restore" in what:                      # right before the restore of the run itself
        shutil.move(os.path.join(root, "src"), os.path.join(root, "src.moved")); os.symlink(decoy, os.path.join(root, "src"))
    return out
r.safe_rel = swapped
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t63b.out" | tail -3
chk "T63b the run's own restore through a swapped folder: exit 3 (got $rc), marker and backup kept, the planted file is still planted behind the swap (r5: exit 0 or 4, marker cleared)" "[ $rc -eq 3 ] && [ -n \"\$(ls $STATE/*.planted.json 2>/dev/null)\" ] && [ -n \"\$(ls $STATE/*.backup 2>/dev/null)\" ] && [ \"\$(tail -1 $T/root/src.moved/mod.py | tr -d ' ')\" = return2 ]"
rm -f "$T/root/src"; mv "$T/root/src.moved" "$T/root/src"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
chk "T63b genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
rm -rf "$S/decoy"
echo "== T63c restore_target itself: one descriptor, a swap during the write does not matter, read-only, two names, FIFO, re-creation"
fresh_root; python3 - "$RUN" "$S" <<'PY' >"$S/t63c.out" 2>&1
import errno, importlib.util, os, pathlib, shutil, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
base = pathlib.Path(sys.argv[2]) / "rt"; shutil.rmtree(base, ignore_errors=True); base.mkdir()
bad = []
if not hasattr(r, "restore_target"): print("restore_target missing"); sys.exit(1)
ORIG, MUT = b"original\n", b"mutated\n"
def fresh(sub="d"):
    d = base / sub; shutil.rmtree(d, ignore_errors=True); d.mkdir(); f = d / "f.txt"; f.write_bytes(MUT); return d, f
# 1 plain: differs -> written, verified from the same file
d, f = fresh(); already, back = r.restore_target(f, ORIG, base)
if (already, back, f.read_bytes()) != (False, ORIG, ORIG): bad.append("plain")
# 2 already original -> no write (modification time unchanged)
d, f = fresh(); f.write_bytes(ORIG); m0 = os.stat(f).st_mtime_ns; already, back = r.restore_target(f, ORIG, base)
if (already, back) != (True, ORIG) or os.stat(f).st_mtime_ns != m0: bad.append("already")
# 3 the folder is swapped for a decoy (original bytes) DURING the write: the write and the verification stay on the real file
d, f = fresh("swap"); decoy = base / "decoyd"; shutil.rmtree(decoy, ignore_errors=True); decoy.mkdir(); (decoy / "f.txt").write_bytes(ORIG)
real_fsync = os.fsync
def swap(fd):
    shutil.move(str(d), str(base / "swap.moved")); os.symlink(decoy, d); return real_fsync(fd)
os.fsync = swap
try: already, back = r.restore_target(f, ORIG, base)
finally: os.fsync = real_fsync
if back != ORIG or (base / "swap.moved" / "f.txt").read_bytes() != ORIG or (decoy / "f.txt").read_bytes() != ORIG: bad.append("swap during write")
# 4 folder is already a link: refused, nothing written
d, f = fresh("lnk"); shutil.move(str(d), str(base / "lnk.moved")); os.symlink(decoy, d)
try: r.restore_target(f, ORIG, base); bad.append("link not refused")
except r.Refused: pass
if (base / "lnk.moved" / "f.txt").read_bytes() != MUT: bad.append("link: file touched")
# 5 read-only (EACCES on O_RDWR is simulated): equal -> fine, different -> PermissionError, never written
real_open = os.open
def ro_open(path, flags, *a, **k):
    if flags & os.O_RDWR: raise PermissionError(errno.EACCES, "Permission denied")
    return real_open(path, flags, *a, **k)
d, f = fresh("ro"); f.write_bytes(ORIG); os.open = ro_open
try:
    already, back = r.restore_target(f, ORIG, base)
    if (already, back) != (True, ORIG): bad.append("ro equal")
    f.write_bytes(MUT)
    try: r.restore_target(f, ORIG, base); bad.append("ro differs not refused")
    except PermissionError: pass
finally: os.open = real_open
if f.read_bytes() != MUT: bad.append("ro: written")
# 6 two names: equal -> fine (nothing written); different -> Refused, both names unchanged
d, f = fresh("two"); g = d / "g.txt"; f.write_bytes(ORIG); os.link(f, g); already, back = r.restore_target(f, ORIG, base)
if (already, back) != (True, ORIG): bad.append("two equal")
f.write_bytes(MUT)
try: r.restore_target(f, ORIG, base); bad.append("two not refused")
except r.Refused: pass
if g.read_bytes() != MUT: bad.append("two: written")
# 7 FIFO: refused, no hang
d, f = fresh("fifo"); f.unlink(); os.mkfifo(f)
try: r.restore_target(f, ORIG, base); bad.append("fifo not refused")
except r.Refused: pass
# 8 re-creation with the recorded mode whatever the umask
d = base / "gone"; shutil.rmtree(d, ignore_errors=True); old = os.umask(0o077)
try: already, back = r.restore_target(d / "sub" / "f.txt", ORIG, base, create=True, mode=0o640)
finally: os.umask(old)
if (already, back) != (False, ORIG) or oct((d / "sub" / "f.txt").stat().st_mode & 0o777) != "0o640": bad.append("create")
print("bad:", bad); sys.exit(1 if bad else 0)
PY
rc=$?; cut -c1-220 "$S/t63c.out"; chk "T63c restore_target: plain, already-original (no write), swap during the write, link refused, read-only, two names, FIFO, re-creation (rc $rc)" "[ $rc -eq 0 ]"

echo "== T64 (review r5 nit 1) a REAL memory fault is not recovered by the signal handler: the process hangs (measured), as the text now says"
python3 - "$RUN" <<'PY' >"$S/t64.out" 2>&1 &
import ctypes, importlib.util, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
for sg in r.HANDLED_SIGNALS:
    try: signal.signal(sg, r._term)
    except (OSError, ValueError): pass
print("armed", flush=True)
ctypes.string_at(0)          # a real SIGSEGV raised by the CPU
print("returned from the fault (unexpected)", flush=True)
PY
FP=$!; sleep 4; kill -0 $FP 2>/dev/null; alive=$?; kill -9 $FP 2>/dev/null; wait $FP 2>/dev/null
chk "T64a the process with run.py's handlers is still alive 4 s after a real memory fault (hung, handler never ran): 'acts like SIGKILL' would be wrong (alive=$alive, 0 = alive)" "[ $alive -eq 0 ] && grep -q armed '$S/t64.out' && ! grep -q 'returned from the fault' '$S/t64.out'"
chk "T64b the text in run.py no longer says a real fault 'acts like SIGKILL' or calls it 'the SIGKILL case' (r6 comment, review r6 nit 1), says it spins, and names kill -9" "! grep -q 'acts like SIGKILL' '$RUN' && ! grep -q 'SIGKILL case' '$RUN' && grep -q 'spins at full speed' '$RUN' && grep -q 'kill -9' '$RUN'"

echo "== T65 (review r5 nit 2) a failure that is no signal, then a signal in the first moment of the cleanup: the test group is still stopped"
for variant in planted control; do
fresh_root; python3 - "$RUN" "$T/root" $variant <<'PY' >"$S/t65.out" 2>&1
import importlib.util, linecache, pathlib, signal, subprocess, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, variant = pathlib.Path(sys.argv[2]), sys.argv[3]
src = open(sys.argv[1]).read().splitlines()
first = next(i + 1 for i, l in enumerate(src) if "first statement: nothing below can raise a second time" in l)
Real = subprocess.Popen
class P(Real):
    def communicate(self, *a, **k): raise OSError(5, "simulated read error (no signal)")
subprocess.Popen = P
state = {"fired": False}
code = r.run_tests.__code__
def tracer(frame, event, arg):
    if frame.f_code is code:
        def local(fr, ev, ar):
            if ev == "line" and fr.f_lineno == first and not state["fired"]:
                state["fired"] = True
                r._term(signal.SIGTERM, None)          # the handler runs exactly here, before the first statement of the cleanup
            return local
        return local
sys.settrace(tracer)
r.SIG.critical, r.SIG.allow, r.SIG.fired, r.SIG.first = variant == "planted", False, False, None
try: r.run_tests(root, ["tests/test_slow.py"], str(root / "src"), 60)
except OSError as e: print("OSError (the failure itself) came out:", e)
except KeyboardInterrupt as e: print("KeyboardInterrupt came out instead of the failure:", e.args)
finally: sys.settrace(None)
print("line hit:", state["fired"], "SIG.allow:", r.SIG.allow, "first:", r.SIG.first, "critical:", r.SIG.critical)
PY
sleep 1; cut -c1-200 "$S/t65.out" | tail -3
chk "T65 $variant: the group is stopped although a signal came in the first moment of the cleanup (no orphan pytest left, the failure itself came out)" "! orphan_alive && grep -q 'OSError (the failure itself) came out' '$S/t65.out' && grep -q 'line hit: True' '$S/t65.out'"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
done

echo "== T66 (review r5 M1) the baseline: a failing or empty baseline refuses the mutants; a result without a passed test is no survivor; a kill that equals the baseline is flagged"
fresh_root; mut --control -- tests/test_fail.py >"$S/t66a.out" 2>&1; rc=$?; cut -c1-200 "$S/t66a.out" | tail -2
chk "T66a baseline FAILS: mutants refused, exit 2 (got $rc), baseline file says 'baseline usable: NO', no raw file for the mutant, file unchanged, state empty" "[ $rc -eq 2 ] && grep -q 'baseline usable: NO' '$S/rawT/X-baseline.txt' && [ ! -e '$S/rawT/X-m1.txt' ] && [ '$(last)' = return1 -a -z '$(state_files)' ]"
fresh_root; mut --control -- tests/test_skip.py >"$S/t66b.out" 2>&1; rc=$?
chk "T66b baseline with every test skipped (pytest exit 0, nothing passed): refused, exit 2 (got $rc), 'no test passed' in the baseline file, no mutant file" "[ $rc -eq 2 ] && grep -q 'no test passed' '$S/rawT/X-baseline.txt' && [ ! -e '$S/rawT/X-m1.txt' ]"
fresh_root; mut -- tests/test_skip.py >"$S/t66c.out" 2>&1; rc=$?
chk "T66c no control, every test skipped: verdict NO-TEST-PASSED (not SURVIVED), exit 5 (got $rc)" "[ $rc -eq 5 ] && grep -q 'VERDICT: NO-TEST-PASSED' '$S/rawT/X-m1.txt'"
fresh_root; rm "$T/root/.venv"; rm -rf "$S/fakevenv2"; mkdir -p "$S/fakevenv2/bin"
printf '#!/bin/sh\nif grep -q "return 2" src/mod.py; then echo "1 error in 0.01s"; exit 1; fi\necho "1 passed in 0.01s"\nexit 0\n' > "$S/fakevenv2/bin/python"; chmod +x "$S/fakevenv2/bin/python"; ln -s "$S/fakevenv2" "$T/root/.venv"
mut --control --skip-import-check -- tests/test_fast.py >"$S/t66d.out" 2>&1; rc=$?; grep -E "SUMMARY|FLAGGED" "$S/t66d.out" | cut -c1-200
chk "T66d a KILLED whose failing tests equal the baseline's (none named) is FLAGGED: exit 5 (got $rc), 'flags:' line in the raw file, '1 flagged' in the summary" "[ $rc -eq 5 ] && grep -q 'flags: the failing tests are the same as the baseline' '$S/rawT/X-m1.txt' && grep -q '1 flagged' '$S/t66d.out'"
fresh_root; mut --control -- tests/test_fast.py >"$S/t66e.out" 2>&1; rc=$?
chk "T66e guard: a normal kill with --control (a named failing test) is not flagged: exit 0 (got $rc), 'flags: none', baseline recorded" "[ $rc -eq 0 ] && grep -q 'flags: none' '$S/rawT/X-m1.txt' && grep -q 'baseline: rc 0, 1 passed' '$S/rawT/X-m1.txt' && grep -q 'baseline usable: yes' '$S/rawT/X-baseline.txt'"
fresh_root; mut --no-control -- tests/test_fast.py >"$S/t66f.out" 2>&1; rc=$?; chk "T66f --no-control: every raw file says 'baseline: NOT RUN', the SUMMARY says NO BASELINE and not COMPLETE, exit 5 (got $rc)" "[ $rc -eq 5 ] && grep -q 'baseline: NOT RUN' '$S/rawT/X-m1.txt' && grep -q 'NO BASELINE' '$S/t66f.out' && ! grep -qE '(^|[^N])COMPLETE' '$S/t66f.out'"

echo "== T67 (review r5 M2) exit 0 means every mutant ran: COULD-NOT-PLANT, TIMEOUT and ERROR give exit 5 and a SUMMARY line"
fresh_root; out=$(base --id m1 --file src/mod.py --old 'return 77' --new 'return 2' -- tests/test_fast.py 2>&1); rc=$?; printf '%s\n' "$out" | grep -E "SUMMARY|INCOMPLETE" | cut -c1-230
chk "T67a COULD-NOT-PLANT (old text absent): exit 5 (got $rc), SUMMARY counts it, raw says so" "[ $rc -eq 5 ] && printf %s '$out' | grep -q '1 COULD-NOT-PLANT' && grep -q 'VERDICT: COULD-NOT-PLANT' '$S/rawT/X-m1.txt' && [ '$(last)' = return1 ]"
fresh_root; base --timeout 6 --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_partial.py >"$S/t67b.out" 2>&1; rc=$?
chk "T67b TIMEOUT: exit 5 (got $rc), SUMMARY counts it" "[ $rc -eq 5 ] && grep -q '1 TIMEOUT' '$S/t67b.out' && [ '$(last)' = return1 ]"
fresh_root; mut -- -k no_such_test_zzz tests/test_fast.py >"$S/t67c.out" 2>&1; rc=$?
chk "T67c ERROR (pytest exit 5, no test selected): exit 5 (got $rc), SUMMARY counts it" "[ $rc -eq 5 ] && grep -q '1 ERROR' '$S/t67c.out' && grep -q 'VERDICT: ERROR rc=5' '$S/rawT/X-m1.txt'"
fresh_root; printf '[{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"},{"id":"m2","file":"src/mod.py","old":"return 55","new":"return 3"}]' > "$S/mixed.json"
base --list "$S/mixed.json" -- tests/test_fast.py >"$S/t67d.out" 2>&1; rc=$?; grep SUMMARY "$S/t67d.out" | cut -c1-230
chk "T67d two mutants, one killed and one that could not be planted: exit 5 (got $rc), both raw files, counts '1 KILLED, 0 SURVIVED, 0 TIMEOUT, 1 COULD-NOT-PLANT', summary file written" "[ $rc -eq 5 ] && [ -e '$S/rawT/X-m1.txt' -a -e '$S/rawT/X-m2.txt' ] && grep -q '1 KILLED, 0 SURVIVED, 0 TIMEOUT, 1 COULD-NOT-PLANT' '$S/t67d.out' && grep -q 'SUMMARY' '$S/rawT/X-summary.txt'"
fresh_root; NCF= mut -- tests/test_fast.py >"$S/t67e.out" 2>&1; rc=$?
chk "T67e guard: every mutant killed: exit 0 (got $rc), summary says COMPLETE" "[ $rc -eq 0 ] && grep -q 'COMPLETE' '$S/t67e.out' && ! grep -q INCOMPLETE '$S/t67e.out'"
fresh_root; NCF= mut --extra junk.txt -- tests/test_junk.py >/dev/null 2>&1; rc=$?; chk "T67f guard: a clean verdict with a declared --extra file keeps exit 0 (got $rc)" "[ $rc -eq 0 ]"
fresh_root; base --list "$S/two.json" -- tests/test_junk.py >/dev/null 2>&1; rc=$?; chk "T67g exit 4 (tree not clean) still wins over exit 5 (got $rc)" "[ $rc -eq 4 ]"

echo "== T68 (review r5 nit 3) --restore with no marker anywhere says it CANNOT TELL, not 'nothing to restore'"
fresh_root; out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-240
chk "T68 text says 'CANNOT TELL' and no longer 'nothing to restore' (exit $rc; r9: 2, was 0: the files are unknown, so exit 0 would claim nothing is planted)" "[ $rc -eq 2 ] && printf %s '$out' | grep -q 'CANNOT TELL' && ! printf %s '$out' | grep -q 'nothing to restore'"

echo "== T69 (review r5 nit 4) a control marker: invalid JSON is a refusal; a group that cannot be settled keeps the marker"
fresh_root; KEY=$(printf %s "$(readlink -f "$T/root")" | sha256sum | cut -c1-16); mkdir -m 700 -p "$STATE"; printf 'this is not json' > "$STATE/$KEY.control.json"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T69a invalid JSON in the control marker (its test group cannot be settled): exit 3 (got $rc; r7: 2), 'RESTORE FAILED', control marker KEPT, no traceback" "[ $rc -eq 3 ] && printf %s '$out' | grep -q 'RESTORE FAILED' && [ -e '$STATE/$KEY.control.json' ] && ! printf %s '$out' | grep -q Traceback"
RT=$(readlink -f "$T/root"); printf '{"root": "%s"}' "$RT" > "$STATE/$KEY.control.json"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-240
chk "T69b control marker with no test group recorded (cannot be verified): marker KEPT, exit 3 (got $rc), text says KEPT" "[ $rc -eq 3 ] && [ -e '$STATE/$KEY.control.json' ] && printf %s '$out' | grep -q KEPT"
printf '{"root": "%s", "pgid": 999999, "start_ticks": 1, "argv": ["x"], "cmd_head": ["x"], "run_start_ticks": 1}' "$RT" > "$STATE/$KEY.control.json"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-240
chk "T69c guard: a control marker whose group is provably gone is removed, exit 0 (got $rc)" "[ $rc -eq 0 ] && [ ! -e '$STATE/$KEY.control.json' ]"
rm -f "$STATE/$KEY.control.json"

echo "== T70 (review r5 nit 5) the import check is repeated before EACH mutant"
fresh_root; rm -f "$S/flipflag"; rm "$T/root/.venv"; rm -rf "$S/flipvenv"; mkdir -p "$S/flipvenv/bin"
printf '#!/bin/sh\nif [ "$1" = "-c" ] && [ -e "%s/flipflag" ]; then echo /elsewhere/mod.py; exit 0; fi\nexec "%s/bin/python" "$@"\n' "$S" "$VENV" > "$S/flipvenv/bin/python"; chmod +x "$S/flipvenv/bin/python"; ln -s "$S/flipvenv" "$T/root/.venv"
base --list "$S/two.json" -- tests/test_flip.py >"$S/t70.out" 2>&1; rc=$?; cut -c1-200 "$S/t70.out" | tail -4
chk "T70 after the first mutant's tests changed what the tests import, the second mutant is NOT planted: COULD-NOT-PLANT (import check), exit 5 (got $rc)" "[ $rc -eq 5 ] && grep -q 'VERDICT: COULD-NOT-PLANT (import check failed just before this mutant' '$S/rawT/X-m2.txt' && [ '$(last)' = return1 ]"
chk "T70 the first mutant ran normally and records the repeated check" "grep -q 'checked again before this mutant' '$S/rawT/X-m1.txt'"
rm -f "$S/flipflag"; rm -rf "$S/flipvenv"

echo "== T71 (review r5 nit 6) a change to the tree made BEFORE the first mutant (control tests, the import check) stops the run before it is planted"
fresh_root; base --control --list "$S/two.json" -- tests/test_junk.py >"$S/t71a.out" 2>&1; rc=$?; tail -2 "$S/t71a.out" | cut -c1-200
chk "T71a the control run's tests wrote a file: exit 4 (got $rc) BEFORE mutant m1 (no X-m1.txt), 'STOPPED before the first mutant'" "[ $rc -eq 4 ] && [ ! -e '$S/rawT/X-m1.txt' ] && grep -q 'STOPPED before the first mutant' '$S/t71a.out' && [ '$(last)' = return1 ]"
fresh_root; base --id m1 --file src/sideeffect.py --old 'X = 1' --new 'X = 2' -- tests/test_fast.py >"$S/t71b.out" 2>&1; rc=$?; tail -2 "$S/t71b.out" | cut -c1-200
chk "T71b importing the target module wrote a file (import check): exit 4 (got $rc) before the mutant is planted (no X-m1.txt)" "[ $rc -eq 4 ] && [ ! -e '$S/rawT/X-m1.txt' ] && grep -q 'STOPPED before the first mutant' '$S/t71b.out'"

echo "== T72 (review r5 nit 7) mutant ids that name other raw files are refused"
for rid in baseline tree-diff summary; do fresh_root; base --id $rid --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_fast.py >"$S/t72.out" 2>&1; rc=$?
  chk "T72 id '$rid' refused, exit 2 (got $rc), nothing planted, no raw file named after it" "[ $rc -eq 2 ] && [ '$(last)' = return1 ] && [ ! -e '$S/rawT/X-$rid.txt' ] && [ -z '$(state_files)' ]"; done

echo "== T73 (review r5 nit 8) an old Python (version and tomllib simulated) is refused at the start with a message, also for --restore"
python3 - "$RUN" "$T/root" <<'PY' >"$S/t73.out" 2>&1
import argparse, configparser, errno, fcntl, hashlib, io, json, os, pathlib, re, shlex, shutil, signal, stat, subprocess, sys, tarfile, tempfile, time, runpy   # everything run.py imports, loaded before the version is changed
sys.modules["tomllib"] = None                                     # `import tomllib` raises ImportError, as on Python < 3.11
sys.version_info = (3, 10, 12, "final", 0)
runfile = sys.argv[1]; sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
runpy.run_path(runfile, run_name="__main__")
PY
rc=$?; cut -c1-200 "$S/t73.out" | tail -2
chk "T73 exit 2 (got $rc) with a message naming Python 3.11.4, no traceback" "[ $rc -eq 2 ] && grep -q '3.11.4' '$S/t73.out' && ! grep -q Traceback '$S/t73.out'"

echo "== T74 (review r5 nit 9) --sha is pinned: the full id of a COMMIT is recorded; an id that is no commit is refused"
fresh_root; NCF= mut --sha "${SHA:0:7}" -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T74a a short id works (rc $rc) and the raw file records the FULL id (and how it was given)" "[ $rc -eq 0 ] && grep -q 'base commit: $SHA (given as ${SHA:0:7})' '$S/rawT/X-m1.txt' && grep -q 'compared: <fresh git archive $SHA' '$S/rawT/X-tree-diff.txt'"
TREEID=$(git -C "$T/repo" rev-parse 'HEAD^{tree}'); fresh_root; mut --sha "$TREEID" -- tests/test_fast.py >"$S/t74b.out" 2>&1; rc=$?; cut -c1-200 "$S/t74b.out"
chk "T74b the id of a TREE (git archive would accept it) is refused, exit 2 (got $rc), nothing planted" "[ $rc -eq 2 ] && [ '$(last)' = return1 ]"
fresh_root; mut --sha 1234567890abcdef -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T74c guard: an unknown id is refused, exit 2 (got $rc)" "[ $rc -eq 2 ]"

echo "== T75 (review r5 smaller point) git and patch run with a clean environment: GIT_DIR and GIT_WORK_TREE of the caller do not reach them"
fresh_root; GIT_DIR=/nonexistent/gitdir GIT_WORK_TREE=/nonexistent/tree NCF= mut -- tests/test_fast.py >"$S/t75.out" 2>&1; rc=$?; cut -c1-200 "$S/t75.out" | tail -2
chk "T75 with a bogus GIT_DIR and GIT_WORK_TREE in the caller's environment the run still works (exit 0, got $rc)" "[ $rc -eq 0 ]"

echo "== T76 (review r6 M1) --restore with a VALID marker: every failure to write back exits 3 (mutant may be planted, marker and backup kept); 2 only for a forged or wrong marker"
kill_planted; mv "$T/root/src" "$T/root/src.moved"; mkdir -p "$S/decoy76/src"; ln -s "$S/decoy76/src" "$T/root/src"
python3 "$RUN" --root "$T/root" --restore >"$S/t76b.out" 2>&1; rc=$?; cut -c1-200 "$S/t76b.out"
chk "T76a symbolic link on the way to the target at --restore: exit 3 (got $rc), text says RESTORE FAILED, marker and backup kept, the planted file behind it still planted" "[ $rc -eq 3 ] && grep -q 'RESTORE FAILED' '$S/t76b.out' && keptstate && [ \"\$(tail -1 $T/root/src.moved/mod.py | tr -d ' ')\" = return2 ]"
rm -f "$T/root/src"; mv "$T/root/src.moved" "$T/root/src"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T76a the kept marker still allows a genuine restore" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted; cp "$T/root/src/mod.py" "$S/planted76.txt"; rm "$T/root/src/mod.py"; ln "$S/planted76.txt" "$T/root/src/mod.py"   # planted text, two names
python3 "$RUN" --root "$T/root" --restore >"$S/t76c.out" 2>&1; rc=$?; cut -c1-200 "$S/t76c.out"
chk "T76b file with two names that still holds the planted text: exit 3 (got $rc), marker and backup kept, the other name untouched" "[ $rc -eq 3 ] && keptstate && [ \"\$(tail -1 $S/planted76.txt | tr -d ' ')\" = return2 ]"
rm -f "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T76b genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted
python3 - "$RUN" "$T/root" <<'PY' >"$S/t76d.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def denied(*a, **k): raise PermissionError(13, "Permission denied")   # an unwritable file after a valid marker
r.restore_target = denied
sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t76d.out"
chk "T76c unwritable target (restore_target raises PermissionError): exit 3 (got $rc), file still planted, marker and backup kept" "[ $rc -eq 3 ] && keptstate && [ '$(last)' = return2 ]"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T76c genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted; BK=$(ls "$STATE"/*.backup); printf 'def f():\n    return 99\n' > "$BK"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc=$?; chk "T76d a damaged backup (hash differs from the marker): nothing is written, but the mutant is still planted, so exit 3 (got $rc; r7 pinned 2), marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && keptstate"
git -C "$T/repo" show "$SHA:src/mod.py" > "$BK"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1

echo "== T77 (review r6 M2) the baseline is the DEFAULT; --no-control gives exit 5 and never says COMPLETE"
fresh_root; NCF= mut -- tests/test_fail.py >"$S/t77a.out" 2>&1; rc=$?; cut -c1-200 "$S/t77a.out" | tail -2
chk "T77a no option at all, tree already failing: the baseline refuses the mutants, exit 2 (got $rc), baseline file says NO, no mutant raw file, file unchanged (r6: ran every mutant as KILLED)" "[ $rc -eq 2 ] && grep -q 'baseline usable: NO' '$S/rawT/X-baseline.txt' && [ ! -e '$S/rawT/X-m1.txt' ] && [ '$(last)' = return1 ]"
fresh_root; NCF= mut -- tests/test_fast.py >"$S/t77b.out" 2>&1; rc=$?
chk "T77b no option at all, healthy tree: baseline recorded and used, exit 0 (got $rc), 'baseline: rc 0, 1 passed' in the raw file, SUMMARY says COMPLETE" "[ $rc -eq 0 ] && grep -q 'baseline: rc 0, 1 passed' '$S/rawT/X-m1.txt' && grep -q 'baseline usable: yes' '$S/rawT/X-baseline.txt' && grep -qE '(^|[^N])COMPLETE \(a baseline ran' '$S/t77b.out'"
fresh_root; NCF= mut ${NOBASE_OPT---no-control} -- tests/test_fast.py >"$S/t77c.out" 2>&1; rc=$?
chk "T77c a run WITHOUT a baseline (the option --no-control; on the r6 copy NOBASE_OPT= is empty: r6 runs without one by default, this is the behaviour itself), every verdict clean: exit 5 (got $rc), SUMMARY says NO BASELINE and INCOMPLETE and never the word COMPLETE on its own, raw file says baseline NOT RUN, no baseline file" "[ $rc -eq 5 ] && grep -q 'NO BASELINE' '$S/t77c.out' && grep -q 'INCOMPLETE' '$S/t77c.out' && ! grep -qE '(^|[^N])COMPLETE' '$S/t77c.out' && grep -q 'baseline: NOT RUN' '$S/rawT/X-m1.txt' && [ ! -e '$S/rawT/X-baseline.txt' ]"
fresh_root; NCF= mut --no-control --control -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T77d the last of --no-control/--control wins: --control after --no-control runs the baseline, exit 0 (got $rc)" "[ $rc -eq 0 ] && [ -e '$S/rawT/X-baseline.txt' ]"
fresh_root; NCF= mut --control --no-control -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T77e --no-control after --control: no baseline, exit 5 (got $rc)" "[ $rc -eq 5 ] && [ ! -e '$S/rawT/X-baseline.txt' ]"
fresh_root; NCF= mut --no-control -- tests/test_junk.py >/dev/null 2>&1; rc=$?; chk "T77f guard: exit 4 (tree not clean) still wins over the no-baseline exit 5 (got $rc)" "[ $rc -eq 4 ]"

echo "== T78 (review r6 nit 2) --restore is signal-guarded: a signal in the middle of the write-back does not leave the file planted"
kill_planted
python3 - "$RUN" "$T/root" <<'PY' >"$S/t78.out" 2>&1
import importlib.util, os, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
real, state = os.fsync, {"n": 0}
def fsync(fd):
    state["n"] += 1
    if state["n"] == 1: os.kill(os.getpid(), signal.SIGTERM)   # the signal comes inside restore_target, after the write
    return real(fd)
os.fsync = fsync
sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t78.out" | tail -3
chk "T78a SIGTERM inside the restore write: the restore finishes (file back, marker and backup gone), exit 0 (got $rc), the signal is reported (r6: unwound, exit 143, file still planted)" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ] && grep -q 'arrived during the restore' '$S/t78.out'"
fresh_root
python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >"$S/t78b.out" 2>&1
import importlib.util, os, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
real, hit = r.shutil.rmtree, {"n": 0}
def rmtree(path, *a, **k):
    if "mutation-ref-" in str(path) and not hit["n"]:
        hit["n"] += 1; os.kill(os.getpid(), signal.SIGTERM)    # a signal while the process is already leaving with exit 5
    return real(path, *a, **k)
r.shutil.rmtree = rmtree
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 77", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t78b.out" | tail -3
chk "T78b a signal while the process leaves with exit 5 (COULD-NOT-PLANT): the exit code stays 5 (got $rc; r6: a traceback or 130/143)" "[ $rc -eq 5 ] && ! grep -q Traceback '$S/t78b.out'"

echo "== T79 (review r6 nit 3) sweep_group: a stranger that holds the number of the finished test group is left alone"
python3 - "$RUN" "$SL" <<'PY' >"$S/t79.out" 2>&1
import importlib.util, os, subprocess, sys, time
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
before = r.boot_ticks()
time.sleep(0.2)
p = subprocess.Popen([sys.argv[2], "3150"], start_new_session=True)     # a stranger: its own session and group, started AFTER `before`
time.sleep(0.3)
import inspect
three = len(inspect.signature(r.sweep_group).parameters) >= 3      # r6 had only (pgid): the stranger case is then run the old way and the stranger is killed
note = r.sweep_group(p.pid, before - 1000, before) if three else r.sweep_group(p.pid)    # the test group "ended" at `before`: the stranger started later
print("stranger case:", note, "| alive:", p.poll() is None, flush=True)
note2 = r.sweep_group(p.pid, before - 1000, r.boot_ticks()) if three else r.sweep_group(p.pid)   # control: it started inside the window: ours, stopped
time.sleep(0.5)
print("control case:", note2[:60], "| alive:", p.poll() is None, flush=True)
p.kill(); p.wait()
PY
cut -c1-220 "$S/t79.out"
chk "T79 the stranger started after the group ended is left alone (still alive), the control inside the window is stopped" "grep -q 'stranger case: .*left alone.*alive: True' '$S/t79.out' && grep -q 'control case: STOPPED.*alive: False' '$S/t79.out'"

echo "== T80 (review r6 nit 4) output paths are checked BEFORE anything is planted: --out-json inside --root, a missing folder, a file with two names, --raw inside --root"
fresh_root; mut --out-json "$T/root/out.json" -- tests/test_fast.py >"$S/t80a.out" 2>&1; rc=$?; cut -c1-200 "$S/t80a.out" | tail -1
chk "T80a --out-json inside --root: refused, exit 2 (got $rc), no mutant run (no X-m1.txt), file unchanged, no out file" "[ $rc -eq 2 ] && [ ! -e '$S/rawT/X-m1.txt' ] && [ '$(last)' = return1 ] && [ ! -e '$T/root/out.json' ]"
fresh_root; mut --out-json "$S/no-such-folder/out.json" -- tests/test_fast.py >"$S/t80b.out" 2>&1; rc=$?; cut -c1-200 "$S/t80b.out" | tail -1
chk "T80b --out-json in a folder that does not exist: refused before planting, exit 2 (got $rc), no X-m1.txt (r6: ran everything, failed at the end)" "[ $rc -eq 2 ] && [ ! -e '$S/rawT/X-m1.txt' ] && [ '$(last)' = return1 ]"
fresh_root; echo precious > "$S/precious80.txt"; ln "$S/precious80.txt" "$S/out80.json"
mut --out-json "$S/out80.json" -- tests/test_fast.py >"$S/t80c.out" 2>&1; rc=$?; cut -c1-200 "$S/t80c.out" | tail -1
chk "T80c --out-json that has two names: refused, exit 2 (got $rc), the other name still holds 'precious', no X-m1.txt" "[ $rc -eq 2 ] && [ '$(cat "$S/precious80.txt")' = precious ] && [ ! -e '$S/rawT/X-m1.txt' ]"
rm -f "$S/out80.json" "$S/precious80.txt"
fresh_root; mkdir -p "$S/rawT"; echo precious > "$S/precious80b.txt"; ln "$S/precious80b.txt" "$S/rawT/X-m1.txt"
mut -- tests/test_fast.py >"$S/t80d.out" 2>&1; rc=$?; cut -c1-200 "$S/t80d.out" | tail -1
chk "T80d a raw file that has two names: refused before planting, exit 2 (got $rc), the other name untouched, file unchanged" "[ $rc -eq 2 ] && [ '$(cat "$S/precious80b.txt")' = precious ] && [ '$(last)' = return1 ]"
rm -rf "${S:?}/rawT" "${S:?}/precious80b.txt"
fresh_root; mut --raw "$T/root/rawinside" -- tests/test_fast.py >"$S/t80e.out" 2>&1; rc=$?; cut -c1-200 "$S/t80e.out" | tail -1
chk "T80e --raw inside --root: refused, exit 2 (got $rc), nothing created there, file unchanged" "[ $rc -eq 2 ] && [ ! -e '$T/root/rawinside' ] && [ '$(last)' = return1 ]"

echo "== T81 (review r6 nit 5) a bad archive, a bad interpreter, a bad list, a lone surrogate and an internal bug are refusals, never a traceback with exit 1"
rm -rf "${S:?}/repo81"; mkdir -p "$S/repo81"; ( cd "$S/repo81" && git init -q && ln -s /etc/passwd evil-link && printf 'x\n' > a.txt && git add -A && git -c user.email=a@b -c user.name=n commit -qm l ); SHA81=$(git -C "$S/repo81" rev-parse HEAD)
fresh_root; mut --repo "$S/repo81" --sha "$SHA81" -- tests/test_fast.py >"$S/t81a.out" 2>&1; rc=$?; cut -c1-240 "$S/t81a.out" | tail -2
chk "T81a a tracked absolute symbolic link makes the archive extraction fail (tarfile FilterError): refused, exit 2 (got $rc), no traceback (r6: exit 1)" "[ $rc -eq 2 ] && ! grep -q Traceback '$S/t81a.out' && grep -q 'cannot be extracted safely' '$S/t81a.out'"
fresh_root; rm "$T/root/.venv"; rm -rf "${S:?}/badvenv"; mkdir -p "$S/badvenv/bin"; printf 'not a program' > "$S/badvenv/bin/python"; chmod +x "$S/badvenv/bin/python"; ln -s "$S/badvenv" "$T/root/.venv"
mut -- tests/test_fast.py >"$S/t81b.out" 2>&1; rc=$?; cut -c1-240 "$S/t81b.out" | tail -2
chk "T81b an interpreter that cannot be started (exec format error) in the import check: refused, exit 2 (got $rc), no traceback" "[ $rc -eq 2 ] && ! grep -q Traceback '$S/t81b.out' && grep -q 'cannot start' '$S/t81b.out'"
fresh_root; printf '[{"id":"m1","file":"src/mod.py","old":"return 1","new":"return \\ud800"}]' > "$S/surr.json"
base --list "$S/surr.json" -- tests/test_fast.py >"$S/t81c.out" 2>&1; rc=$?; cut -c1-240 "$S/t81c.out" | tail -2
chk "T81c a lone surrogate in a mutant text: refused, exit 2 (got $rc), no traceback, file unchanged, state empty" "[ $rc -eq 2 ] && ! grep -q Traceback '$S/t81c.out' && grep -q 'lone surrogate' '$S/t81c.out' && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
fresh_root; printf 'this is not json' > "$S/badlist.json"; base --list "$S/badlist.json" -- tests/test_fast.py >"$S/t81d.out" 2>&1; rc=$?
chk "T81d a mutant list that is not JSON: refused, exit 2 (got $rc), no traceback" "[ $rc -eq 2 ] && ! grep -q Traceback '$S/t81d.out'"
base --list "$S/does-not-exist.json" -- tests/test_fast.py >"$S/t81e.out" 2>&1; rc=$?; chk "T81e a mutant list that does not exist: refused, exit 2 (got $rc), no traceback" "[ $rc -eq 2 ] && ! grep -q Traceback '$S/t81e.out'"
fresh_root
python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >"$S/t81f.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
def boom(*a, **k): raise RuntimeError("simulated bug after the loop")
r.tree_check = boom
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", *([__import__("os").environ.get("NCF", "--no-control")] if __import__("os").environ.get("NCF", "--no-control") else []), "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t81f.out" | tail -2
chk "T81f an internal bug (exception that is no refusal): INTERNAL ERROR text, exit 2 (got $rc; r6: Python's own exit 1), file restored, state empty" "[ $rc -eq 2 ] && grep -q 'INTERNAL ERROR' '$S/t81f.out' && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"

echo "== T82 (review r6 nit 6) patch runs with --batch, --forward, --no-backup-if-mismatch and stdin from /dev/null; a reversed patch is refused, never applied reversed"
fresh_root; mkdir -p "$S/wrap2"; REALPATCH=$(command -v patch)
printf '#!/bin/bash\necho "$*" > "%s/patch.args"\nreadlink /proc/$$/fd/0 > "%s/patch.stdin"\nexec %s "$@"\n' "$S" "$S" "$REALPATCH" > "$S/wrap2/patch"; chmod +x "$S/wrap2/patch"
printf -- '--- a/docs/note.txt\n+++ b/docs/note.txt\n@@ -1 +1 @@\n-alpha\n+beta\n' > "$S/note.patch"; printf 'beta\n' > "$T/root/docs/note.txt"
rm -f "$S/patch.args" "$S/patch.stdin"; PATH="$S/wrap2:$PATH" mut --patch "$S/note.patch" -- tests/test_fast.py >"$S/t82a.out" 2>&1 </dev/zero; rc=$?; cut -c1-200 "$S/t82a.out" | tail -2
chk "T82a the patch call carries --batch, --forward and --no-backup-if-mismatch (args: $(cat "$S/patch.args" 2>/dev/null | cut -c1-100))" "grep -q -- '--batch' '$S/patch.args' && grep -q -- '--forward' '$S/patch.args' && grep -q -- '--no-backup-if-mismatch' '$S/patch.args'"
chk "T82b the patch call's standard input is /dev/null (got: $(cat "$S/patch.stdin" 2>/dev/null))" "[ '$(cat "$S/patch.stdin" 2>/dev/null)' = /dev/null ]"
fresh_root; printf -- '--- a/docs/note.txt\n+++ b/docs/note.txt\n@@ -1 +1 @@\n-beta\n+alpha\n' > "$S/rev.patch"   # looks REVERSED for this archive (it already says alpha)
printf 'y\ny\ny\n' | mut --patch "$S/rev.patch" -- tests/test_fast.py >"$S/t82c.out" 2>&1; rc=$?; cut -c1-240 "$S/t82c.out" | tail -1
chk "T82c a patch that looks reversed, with 'y' answers waiting on the input: refused as 'does not apply' (got $rc), never applied reversed (r6: asked its question on the caller's input)" "[ $rc -eq 2 ] && grep -q 'does not apply' '$S/t82c.out'"

echo "== T83 (review r6 nit 7) a short --sha that is also the NAME of a branch is refused, the id must start with the typed hex"
fresh_root; for nm in cafe beef dead face; do case "$SHA" in $nm*) ;; *) BR=$nm; break;; esac; done
git -C "$T/repo" branch "$BR" "$SHA"
mut --sha "$BR" -- tests/test_fast.py >"$S/t83.out" 2>&1; rc=$?; cut -c1-240 "$S/t83.out" | tail -1
chk "T83 --sha $BR (a branch name made of hex digits, pointing at HEAD) is refused, exit 2 (got $rc), no mutant run (r6: resolved the branch)" "[ $rc -eq 2 ] && [ ! -e '$S/rawT/X-m1.txt' ] && grep -q 'branch or tag' '$S/t83.out'"
git -C "$T/repo" branch -D "$BR" >/dev/null 2>&1

echo "== T84 (review r6 nit 8) --root renamed away and replaced by a decoy folder during the run: the run's restore must not report success on the decoy"
fresh_root; bg; waitplant; mv "$T/root" "$T/root-moved"; mkdir -p "$T/root/src"; git -C "$T/repo" show "$SHA:src/mod.py" > "$T/root/src/mod.py"
kill -TERM $RP; wait $RP; rc=$?; echo "  exit code $rc"
chk "T84a exit 3 (got $rc), marker and backup kept, the planted file in the renamed folder is still planted (r6: restored on the decoy, exit 143, marker cleared)" "[ $rc -eq 3 ] && keptstate && [ \"\$(tail -1 $T/root-moved/src/mod.py | tr -d ' ')\" = return2 ]"
python3 "$RUN" --root "$T/root" --restore >"$S/t84b.out" 2>&1; rc=$?; cut -c1-200 "$S/t84b.out"
chk "T84b --restore at the path that now holds the decoy: exit 3 (got $rc), text names the renamed folder problem, marker kept" "[ $rc -eq 3 ] && keptstate && grep -q 'not the folder the mutant was planted in' '$S/t84b.out'"
pkill -9 -f "$T/root-moved/.venv/bin/python -m pytest" 2>/dev/null; rm -rf "${T:?}/root"; mv "$T/root-moved" "$T/root"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T84c renamed back: --restore works and the file is back" "[ '$(last)' = return1 -a -z '$(state_files)' ]"

echo "== T85 (review r6 nit 8) a test that changes the mode of the file under test: the mode is set back"
fresh_root; chmod 640 "$T/root/src/mod.py"
mut -- tests/test_chmod.py >"$S/t85.out" 2>&1; rc=$?; cut -c1-200 "$S/t85.out" | tail -2
chk "T85 mode 640 before, a test chmods the file to 600: it is 640 again after the run (got $(stat -c %a "$T/root/src/mod.py")), content restored" "[ '$(stat -c %a "$T/root/src/mod.py")' = 640 ] && [ '$(last)' = return1 ]"

echo "== T86 (found while testing r7) a -q from the caller on top of the tool's own -q must not drop pytest's summary line (then no passed test is counted: a survivor became NO-TEST-PASSED and a baseline became 'no test passed')"
fresh_root; NCF= base --skip-import-check --id m1 --file docs/note.txt --old alpha --new beta -- -q tests/test_fast.py >"$S/t86.out" 2>&1; rc=$?; cut -c1-200 "$S/t86.out" | tail -2
chk "T86 a surviving mutant with the caller's -q: verdict SURVIVED, 'pytest summary line: 1 passed', exit 0 (got $rc); the baseline counts the passed test too" "[ $rc -eq 0 ] && grep -q 'VERDICT: SURVIVED' '$S/rawT/X-m1.txt' && grep -q 'pytest summary line: 1 passed' '$S/rawT/X-m1.txt'"


echo "== T87 (review r7 M1, class: an exit code that says nothing is planted while the mutant is planted) --restore with a marker for this root: every failure exits 3, only a marker naming another root or backup path exits 2"
kill_planted; MK=$(ls "$STATE"/*.planted.json); BK=$(ls "$STATE"/*.backup); rm -f "$BK"
python3 "$RUN" --root "$T/root" --restore >"$S/t87a.out" 2>&1; rc=$?; cut -c1-200 "$S/t87a.out"
chk "T87a the backup file is missing: exit 3 (got $rc; r7: 2), file still planted, marker kept, text says RESTORE FAILED" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && [ -e '$MK' ] && grep -q 'RESTORE FAILED' '$S/t87a.out'"
kill_planted; MK=$(ls "$STATE"/*.planted.json); BK=$(ls "$STATE"/*.backup); cp "$BK" "$S/bk87.copy"; rm -f "$BK"; ln -s "$S/bk87.copy" "$BK"
python3 "$RUN" --root "$T/root" --restore >"$S/t87b.out" 2>&1; rc=$?; cut -c1-200 "$S/t87b.out"
chk "T87b the backup is a symbolic link (to a file with the right content): exit 3 (got $rc; r7: 2), nothing written (file still planted), marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && [ -e '$MK' ]"
kill_planted; MK=$(ls "$STATE"/*.planted.json); BK=$(ls "$STATE"/*.backup); rm -f "$BK"; mkfifo "$BK"
timeout -s KILL 30 python3 "$RUN" --root "$T/root" --restore >"$S/t87c.out" 2>&1; rc=$?; cut -c1-200 "$S/t87c.out"
chk "T87c the backup is a FIFO: exit 3 (got $rc; r7: 2; 124 or 137 = hung), no hang, file still planted, marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && [ -e '$MK' ]"
kill_planted; MK=$(ls "$STATE"/*.planted.json); printf 'this is not json' > "$MK"
python3 "$RUN" --root "$T/root" --restore >"$S/t87d.out" 2>&1; rc=$?; cut -c1-200 "$S/t87d.out"
chk "T87d the marker is not valid JSON: exit 3 (got $rc; r7: 2), file still planted, marker kept, no traceback" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && [ -e '$MK' ] && ! grep -q Traceback '$S/t87d.out'"
kill_planted; MK=$(ls "$STATE"/*.planted.json); printf '{"root": "x"}' > "$MK"
python3 "$RUN" --root "$T/root" --restore >"$S/t87e.out" 2>&1; rc=$?; cut -c1-200 "$S/t87e.out"
chk "T87e the marker lacks required fields: exit 3 (got $rc; r7: 2), file still planted, marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && [ -e '$MK' ]"
kill_planted; BK=$(ls "$STATE"/*.backup); chmod 755 "$STATE"
python3 "$RUN" --root "$T/root" --restore >"$S/t87f.out" 2>&1; rc=$?; cut -c1-200 "$S/t87f.out"; chmod 700 "$STATE"
chk "T87f the state folder has mode 755 (refused by ensure_state): exit 3 (got $rc; r7: 2), file still planted, marker kept" "[ $rc -eq 3 ] && planted_kept"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T87f the kept marker still allows a genuine restore" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted
python3 "$RUN" --root "$T/root" --restore --real-repo "$T/root" >"$S/t87g.out" 2>&1; rc=$?; cut -c1-200 "$S/t87g.out"
chk "T87g the real-repository check refuses (--real-repo is the root) while a marker exists: exit 3 (got $rc; r7: 2), file still planted, marker kept" "[ $rc -eq 3 ] && planted_kept"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T87g genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted; inplace_restore restore_target >"$S/t87h.out" 2>&1; rc=$?; cut -c1-200 "$S/t87h.out" | tail -2
chk "T87h an internal bug inside --restore (restore_target raises RuntimeError): exit 3 (got $rc; r7: 2 with INTERNAL ERROR), file still planted, marker kept" "[ $rc -eq 3 ] && planted_kept"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T87h genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
kill_planted; MK=$(ls "$STATE"/*.planted.json); python3 - "$MK" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); m["root"] = "/somewhere/else"; json.dump(m, open(sys.argv[1], "w"))
PY
python3 "$RUN" --root "$T/root" --restore >"$S/t87i.out" 2>&1; rc=$?; cut -c1-200 "$S/t87i.out"
chk "T87i guard: a marker that names another root is a forged marker: exit 2 (got $rc), nothing written, marker kept" "[ $rc -eq 2 ] && planted_kept"
kill_planted; MK=$(ls "$STATE"/*.planted.json); python3 - "$MK" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); m["backup"] = "/somewhere/else.backup"; json.dump(m, open(sys.argv[1], "w"))
PY
python3 "$RUN" --root "$T/root" --restore >"$S/t87j.out" 2>&1; rc=$?; cut -c1-200 "$S/t87j.out"
chk "T87j guard: a marker that names another backup path is forged: exit 2 (got $rc), nothing written, marker kept" "[ $rc -eq 2 ] && planted_kept"
fresh_root; python3 "$RUN" --root "$T/root" --restore --real-repo "$T/root" >"$S/t87k.out" 2>&1; rc=$?; cut -c1-200 "$S/t87k.out"
chk "T87k guard: no marker anywhere and the real-repository check refuses: still exit 2 (got $rc), nothing recorded as planted" "[ $rc -eq 2 ] && [ '$(last)' = return1 ]"

echo "== T88 (review r7 N7) as a NORMAL USER: real permission bits (as root a mode bit never blocks a write, so the earlier suite never ran this path)"
if [ "$(id -u)" = 0 ] && [ -z "${NONROOT_CHILD:-}" ]; then
  NR=$(mktemp -d /tmp/r8nonroot.XXXXXX); chmod 755 "$NR"; cp -a "$VENV" "$NR/venv"; cp "$RUN" "$NR/run.py"; cp "$SELF_PATH" "$NR/safety-tests.sh"; mkdir "$NR/s"; chown -R nobody "$NR" 2>/dev/null
  if setpriv --reuid=65534 --regid=65534 --clear-groups true 2>/dev/null; then
    ( cd "$NR" && setpriv --reuid=65534 --regid=65534 --clear-groups env -i PATH="$PATH" HOME="$NR" NONROOT_CHILD=1 RUN="$NR/run.py" SCRATCH="$NR/s" VENV="$NR/venv" ONLY="${NONROOT_ONLY:-T52 T53 T76 T85 T87 T88 T92 T93 T94 T96}" NCF="${NCF---no-control}" bash "$NR/safety-tests.sh" ) >"$S/t88child.out" 2>&1; rc=$?
    grep -E "^== |FAIL" "$S/t88child.out" | cut -c1-200 | head -60; tail -1 "$S/t88child.out"
    chk "T88 the blocks ${NONROOT_ONLY:-T52 T53 T76 T85 T87 T88 T92 T93 T94 T96} run again as the unprivileged user nobody (uid 65534): 0 failed checks (child exit $rc)" "grep -q '^FAILED CHECKS: 0 (of [1-9][0-9]* checks run' '$S/t88child.out' && grep -q 'PASS: T88a' '$S/t88child.out' && grep -q 'PASS: T88d' '$S/t88child.out'"
  else
    echo "  (cannot switch to an unprivileged user here: the permission checks are UNVERIFIED)"; SKIPPED="$SKIPPED T88"
  fi
  rm -rf "$NR"
else
  fresh_root; chmod 444 "$T/root/src/mod.py"
  mut -- tests/test_fast.py >"$S/t88a.out" 2>&1; rc=$?; cut -c1-200 "$S/t88a.out" | tail -2
  chk "T88a the file under test is read-only (444) when planting: clean refusal exit 2 (got $rc), 'cannot plant', file and mode unchanged, state empty" "[ $rc -eq 2 ] && grep -q 'cannot plant' '$S/t88a.out' && [ '$(last)' = return1 ] && [ '$(stat -c %a "$T/root/src/mod.py")' = 444 ] && [ -z '$(state_files)' ]"
  fresh_root; mut -- tests/test_chmod_ro.py >"$S/t88b.out" 2>&1; rc=$?; cut -c1-200 "$S/t88b.out" | tail -2
  chk "T88b a test makes the planted file read-only (444) (no baseline here, since the baseline run itself would change the mode: exit 5 is the no-baseline result): original text AND mode 644 written back, verdict SURVIVED, exit 5 (got $rc; r7: exit 3, file left planted), state empty" "[ $rc -eq 5 ] && grep -q 'VERDICT: SURVIVED' '$S/rawT/X-m1.txt' && [ '$(last)' = return1 ] && [ '$(stat -c %a "$T/root/src/mod.py")' = 644 ] && [ -z '$(state_files)' ]"
  fresh_root; mut -- tests/test_chmod_000.py >"$S/t88f.out" 2>&1; rc=$?; cut -c1-200 "$S/t88f.out" | tail -2
  chk "T88f a test makes the planted file mode 000 (neither readable nor writable): original text and mode 644 written back, verdict SURVIVED, exit 5 (got $rc), state empty" "[ $rc -eq 5 ] && grep -q 'VERDICT: SURVIVED' '$S/rawT/X-m1.txt' && [ '$(last)' = return1 ] && [ '$(stat -c %a "$T/root/src/mod.py")' = 644 ] && [ -z '$(state_files)' ]"
  kill_planted; chmod 444 "$T/root/src/mod.py"
  python3 "$RUN" --root "$T/root" --restore >"$S/t88c.out" 2>&1; rc=$?; cut -c1-200 "$S/t88c.out"
  chk "T88c --restore of a planted file that is now read-only (444): restored, exit 0 (got $rc; r7: 3), mode back to 644, state empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ '$(stat -c %a "$T/root/src/mod.py")' = 644 ] && [ -z '$(state_files)' ]"
  kill_planted; git -C "$T/repo" show "$SHA:src/mod.py" > "$T/root/src/mod.py"; chmod 444 "$T/root/src/mod.py"
  python3 "$RUN" --root "$T/root" --restore >"$S/t88d.out" 2>&1; rc=$?; cut -c1-200 "$S/t88d.out"
  chk "T88d guard: a read-only file that already holds the original: exit 0 (got $rc), marker cleared, mode left at 444 (nothing needed changing)" "[ $rc -eq 0 ] && [ -z '$(state_files)' ] && [ '$(stat -c %a "$T/root/src/mod.py")' = 444 ]"
  kill_planted; cp "$T/root/src/mod.py" "$S/planted88.txt"; rm "$T/root/src/mod.py"; ln "$S/planted88.txt" "$T/root/src/mod.py"; chmod 444 "$S/planted88.txt"
  python3 "$RUN" --root "$T/root" --restore >"$S/t88e.out" 2>&1; rc=$?; cut -c1-200 "$S/t88e.out"
  chk "T88e negative: a read-only file with TWO names and the planted text is never made writable: exit 3 (got $rc), mode of both names still 444, other name untouched" "[ $rc -eq 3 ] && [ '$(stat -c %a "$S/planted88.txt")' = 444 ] && [ \"\$(tail -1 $S/planted88.txt | tr -d ' ')\" = return2 ] && keptstate"
  chmod 644 "$S/planted88.txt"; rm -f "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T88e genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"
fi

echo "== T89 (review r7 N5) a test process that leaves the process group (setsid) is NOT stopped: this is named in the docstring; the check pins what is true and the escapee is stopped here by the test"
fresh_root; NCF= mut -- tests/test_setsid.py >"$S/t89.out" 2>&1; rc=$?; cut -c1-200 "$S/t89.out" | tail -2
sleep 1; ALIVE=0; pgrep -f "$SL 3143" >/dev/null && ALIVE=1; pkill -9 -f "$SL 3143" 2>/dev/null
chk "T89 the escapee (setsid) outlived the run (documented): alive=$ALIVE (1), the run itself is clean: exit 0 (got $rc), file restored, raw file says no process of the test group left" "[ $ALIVE -eq 1 ] && [ $rc -eq 0 ] && [ '$(last)' = return1 ] && grep -q 'no process of the test group left' '$S/rawT/X-m1.txt'"
grep -q "PROCESS GROUP ONLY" "$RUN"; chk "T89 the docstring of run.py names this limit (PROCESS GROUP ONLY)" "[ $? -eq 0 ]"

echo "== T90 (review r7 N4) an output file that is also an input of the run (run.py itself, --list, --patch) or another output is refused before anything is planted"
fresh_root; cp "$RUN" "$S/runcopy.py"; H1=$(sha256sum < "$S/runcopy.py")
NCF= python3 "$S/runcopy.py" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' --out-json "$S/./runcopy.py" -- tests/test_fast.py >"$S/t90a.out" 2>&1; rc=$?; cut -c1-200 "$S/t90a.out" | tail -1
chk "T90a --out-json is the running script itself (another spelling of its path): exit 2 (got $rc; r7: ran and truncated it), script unchanged, nothing planted" "[ $rc -eq 2 ] && [ \"\$(sha256sum < $S/runcopy.py)\" = '$H1' ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
fresh_root; cp "$S/two.json" "$S/two.keep"
NCF= base --list "$S/two.json" --out-json "$S/two.json" -- tests/test_fast.py >"$S/t90b.out" 2>&1; rc=$?; cut -c1-200 "$S/t90b.out" | tail -1
chk "T90b --out-json is the --list file: exit 2 (got $rc; r7: the list was overwritten by the results), list unchanged" "[ $rc -eq 2 ] && cmp -s '$S/two.json' '$S/two.keep' && [ '$(last)' = return1 ]"
fresh_root; printf -- '--- a/docs/note.txt\n+++ b/docs/note.txt\n@@ -1 +1 @@\n-alpha\n+beta\n' > "$S/note90.patch"; printf 'beta\n' > "$T/root/docs/note.txt"; cp "$S/note90.patch" "$S/note90.keep"
NCF= mut --patch "$S/note90.patch" --out-json "$S/note90.patch" -- tests/test_fast.py >"$S/t90c.out" 2>&1; rc=$?; cut -c1-200 "$S/t90c.out" | tail -1
chk "T90c --out-json is a --patch file: exit 2 (got $rc; r7: the patch was overwritten), patch unchanged" "[ $rc -eq 2 ] && cmp -s '$S/note90.patch' '$S/note90.keep'"
fresh_root; NCF= mut --out-json "$S/rawT/X-m1.txt" -- tests/test_fast.py >"$S/t90d.out" 2>&1; rc=$?; cut -c1-200 "$S/t90d.out" | tail -1
chk "T90d --out-json is the same path as a raw file of this run: exit 2 (got $rc), file unchanged" "[ $rc -eq 2 ] && grep -q 'same path' '$S/t90d.out' && [ '$(last)' = return1 ]"
fresh_root; rm -f "$S/o90.json"; NCF= mut --out-json "$S/o90.json" -- tests/test_fast.py >"$S/t90e.out" 2>&1; rc=$?
chk "T90e guard: an ordinary --out-json still works: exit 0 (got $rc), the file exists" "[ $rc -eq 0 ] && [ -s '$S/o90.json' ]"

echo "== T91 (review r7 N6) a run with ANOTHER TMPDIR on the same root: its lock is found (TMP names the other place) and this run is refused"
fresh_root; OT=$S/othertmp91; rm -rf "$OT"; mkdir -p "$OT"
( export TMPDIR=$OT; exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawA" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RPA=$!
for _ in $(seq 60); do ls "$OT"/hadavin-mutation-lane-*/*.lock >/dev/null 2>&1 && break; sleep 0.5; done; sleep 3
TMP=$OT mut -- tests/test_fast.py >"$S/t91a.out" 2>&1; rc=$?; cut -c1-240 "$S/t91a.out" | tail -1
chk "T91a run A (TMPDIR=other) is in its baseline; run B (default TMPDIR, TMP=other) is refused: exit 2 (got $rc; r7: B ran too), text names the other TMPDIR" "[ $rc -eq 2 ] && grep -q 'another TMPDIR' '$S/t91a.out'"
kill -TERM $RPA; wait $RPA 2>/dev/null; pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null
fresh_root; TMP=$OT NCF= mut -- tests/test_fast.py >"$S/t91b.out" 2>&1; rc=$?
chk "T91b guard: after run A has ended its lock is free: the same B now runs, exit 0 (got $rc)" "[ $rc -eq 0 ]"
rm -rf "$OT"

echo "== T92 (review r7 N3) a signal that arrives AFTER the result 'clean, exit 0' is decided (while the folders are removed) cannot change it"
fresh_root; python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >"$S/t92.out" 2>&1
import importlib.util, os, shutil, signal, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
real = shutil.rmtree
def rm(path, *a, **k):
    if os.path.basename(str(path)).startswith("mutation-ref-"):
        os.kill(os.getpid(), signal.SIGTERM)       # the real signal, delivered while main() is leaving normally
    return real(path, *a, **k)
shutil.rmtree = rm
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
print("MAIN RETURNED NORMALLY (exit 0 stands)")
PY
rc=$?; tail -3 "$S/t92.out" | cut -c1-200
chk "T92 SIGTERM during the final clean-up of a clean run: main returns normally, exit 0 (got $rc; r7: KeyboardInterrupt out of main, exit 130/143)" "[ $rc -eq 0 ] && grep -q 'MAIN RETURNED NORMALLY' '$S/t92.out'"

echo "== T93 (review r7 N1, N2) --restore with a damaged control marker still restores the planted file; an orphaned test group that cannot be stopped keeps the marker"
kill_planted; KEY=$(basename "$(ls "$STATE"/*.planted.json)" .planted.json); printf 'not json' > "$STATE/$KEY.control.json"
python3 "$RUN" --root "$T/root" --restore >"$S/t93a.out" 2>&1; rc=$?; cut -c1-240 "$S/t93a.out"
chk "T93a a planted marker AND a control marker that is not valid JSON: the planted file IS restored (r7: refused, still planted), planted marker cleared, exit 3 (got $rc), control marker KEPT" "[ $rc -eq 3 ] && [ '$(last)' = return1 ] && [ ! -e '$STATE/$KEY.planted.json' ] && [ -e '$STATE/$KEY.control.json' ]"
kill_planted; KEY=$(basename "$(ls "$STATE"/*.planted.json)" .planted.json); ln -s /nonexistent/control "$STATE/$KEY.control.json"
python3 "$RUN" --root "$T/root" --restore >"$S/t93b.out" 2>&1; rc=$?; cut -c1-240 "$S/t93b.out"
chk "T93b the control marker is a symbolic link: the planted file IS restored, exit 3 (got $rc), link kept" "[ $rc -eq 3 ] && [ '$(last)' = return1 ] && [ -L '$STATE/$KEY.control.json' ]"
kill_planted; KEY=$(basename "$(ls "$STATE"/*.planted.json)" .planted.json); printf '{"root": "/somewhere/else"}' > "$STATE/$KEY.control.json"
python3 "$RUN" --root "$T/root" --restore >"$S/t93c.out" 2>&1; rc=$?; cut -c1-240 "$S/t93c.out"
chk "T93c the control marker names another root: the planted file IS restored, exit 3 (got $rc), control marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return1 ] && [ -e '$STATE/$KEY.control.json' ]"
fresh_root; bg; waitplant; kill -9 $RP; sleep 1
python3 - "$RUN" "$T/root" <<'PY' >"$S/t93d.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
def cannot(pgid): raise PermissionError(1, "Operation not permitted")      # the orphaned group cannot be signalled
r.stop_group = cannot
sys.argv = ["run.py", "--root", sys.argv[2], "--restore"]
r.main()
PY
rc=$?; cut -c1-300 "$S/t93d.out"; ALIVE=0; orphan_alive && ALIVE=1
chk "T93d an orphaned test group that cannot be stopped: the file is restored, but exit 3 (got $rc; r7: 0 and the marker cleared), marker and backup KEPT, text says the group may still run (orphan alive=$ALIVE)" "[ $rc -eq 3 ] && [ '$(last)' = return1 ] && keptstate && grep -q 'STILL RUN' '$S/t93d.out' && [ $ALIVE -eq 1 ]"
python3 "$RUN" --root "$T/root" --restore >"$S/t93e.out" 2>&1; rc=$?; sleep 1
chk "T93e the next --restore (nothing in the way) stops the orphan and clears the state: exit 0 (got $rc), orphan gone" "[ $rc -eq 0 ] && ! orphan_alive && [ -z '$(state_files)' ]"
pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null

echo "== T94 (review r7 M1, sibling in a normal run) the restore at the end of a mutant fails with a bug that is no refusal: exit 3, file left planted, marker kept (r7: exit 2 'INTERNAL ERROR')"
fresh_root; python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$S/rawT" <<'PY' >"$S/t94.out" 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
root, sha, repo, raw = sys.argv[2:6]
def boom(*a, **k): raise RuntimeError("an internal bug while writing the original back")
r.restore_target = boom
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
r.main()
PY
rc=$?; cut -c1-200 "$S/t94.out" | tail -3
chk "T94 normal run, restore_target raises RuntimeError: exit 3 (got $rc), file still planted, marker and backup kept" "[ $rc -eq 3 ] && planted_kept"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; chk "T94 genuine restore afterwards" "[ '$(last)' = return1 -a -z '$(state_files)' ]"


echo "== T95 (lead's four findings from the independent r7 run) (a) output that cannot be written, (b) a 200000-deep JSON, (c) a link left in place of the file, (d) forged marker with a swapped backup"
fresh_root; NCF= mut -- tests/test_fast.py >/dev/full 2>"$S/t95a.err"; rc=$?
chk "T95a standard output is /dev/full (every write fails): the run ends with the tool's own code 0 (got $rc; r7: 1), file restored, state empty, raw summary written" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ] && [ -s '$S/rawT/X-summary.txt' ]"
fresh_root; NCF= mut -- tests/test_fast.py >&- 2>&-; rc=$?
chk "T95a2 standard output AND error closed: exit 0 (got $rc), file restored, state empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
fresh_root; python3 -c "print('['*200000+']'*200000)" > "$S/deep.json"
base --list "$S/deep.json" -- tests/test_fast.py >"$S/t95b.out" 2>&1; rc=$?; cut -c1-200 "$S/t95b.out" | tail -2
chk "T95b a mutants file nested 200000 deep: clean refusal exit 2 (got $rc), REFUSED text, no INTERNAL ERROR, no Traceback, short output ($(wc -l < "$S/t95b.out") lines; r7: INTERNAL ERROR with a traceback)" "[ $rc -eq 2 ] && grep -q REFUSED '$S/t95b.out' && ! grep -q 'INTERNAL ERROR' '$S/t95b.out' && ! grep -q Traceback '$S/t95b.out' && [ \$(wc -l < '$S/t95b.out') -lt 10 ]"
kill_planted; MK=$(ls "$STATE"/*.planted.json); python3 -c "print('['*200000+']'*200000)" > "$MK"
python3 "$RUN" --root "$T/root" --restore >"$S/t95b2.out" 2>&1; rc=$?; cut -c1-200 "$S/t95b2.out" | tail -2
chk "T95b2 a marker nested 200000 deep: exit 3 (got $rc; r7: 2 with INTERNAL ERROR), no Traceback, file still planted" "[ $rc -eq 3 ] && ! grep -q 'INTERNAL ERROR' '$S/t95b2.out' && ! grep -q Traceback '$S/t95b2.out' && [ '$(last)' = return2 ]"
kill_planted; rm "$T/root/src/mod.py"; ln -s /nonexistent/nowhere "$T/root/src/mod.py"
python3 "$RUN" --root "$T/root" --restore >"$S/t95c.out" 2>&1; rc=$?; cut -c1-400 "$S/t95c.out"
chk "T95c a dangling symbolic link in place of the file: exit 3 (got $rc), nothing written through it, the text gives the exact command (rm -- ... mod.py) and the restore command" "[ $rc -eq 3 ] && grep -q 'rm -- .*src/mod.py' '$S/t95c.out' && grep -q -- '--restore' '$S/t95c.out' && [ -L '$T/root/src/mod.py' ] && [ ! -e /nonexistent/nowhere ]"
rm -- "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc=$?; chk "T95c after the advised rm, --restore re-creates the original: exit 0 (got $rc), file back, state empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"
kill_planted; mv "$T/root/src" "$T/root/src.moved"; mkdir -p "$S/decoy95/src"; ln -s "$S/decoy95/src" "$T/root/src"
python3 "$RUN" --root "$T/root" --restore >"$S/t95c2.out" 2>&1; rc=$?; cut -c1-400 "$S/t95c2.out"
chk "T95c2 a folder on the way is a link: exit 3 (got $rc), the text names the folder and says 'mv --' and the restore command" "[ $rc -eq 3 ] && grep -q 'a folder on the way is a symbolic link' '$S/t95c2.out' && grep -q 'mv -- ' '$S/t95c2.out'"
rm -f "$T/root/src"; mv "$T/root/src.moved" "$T/root/src"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
forge_backup() { python3 - "$STATE" <<'PY'
import glob, hashlib, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; bk = glob.glob(sys.argv[1] + "/*.backup")[0]
evil = b"def f():\n    return 99  # swapped by someone who can write the state folder\n"
open(bk, "wb").write(evil)
m = json.load(open(mk)); m["orig_sha256"] = hashlib.sha256(evil).hexdigest(); json.dump(m, open(mk, "w"))
PY
}
kill_planted; forge_backup
python3 "$RUN" --root "$T/root" --restore >"$S/t95d1.out" 2>&1; rc=$?; cut -c1-200 "$S/t95d1.out"
chk "T95d1 HONEST LIMIT, pinned: marker and backup forged TOGETHER (hash matches) by someone who can write the private state folder: a plain --restore accepts them (exit $rc) and the swapped text is written; this cannot be closed without a key the user cannot read (see the docstring)" "[ $rc -eq 0 ] && grep -q 'return 99' '$T/root/src/mod.py'"
kill_planted; forge_backup
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t95d2.out" 2>&1; rc=$?; cut -c1-300 "$S/t95d2.out"
chk "T95d2 the same forged state with --restore --sha COMMIT: refused, exit 3 (got $rc; r7 ignored --sha and accepted), the swapped text is NOT written (file still planted return2), marker kept" "[ $rc -eq 3 ] && [ '$(last)' = return2 ] && grep -q 'differs from' '$S/t95d2.out' && [ -n \"\$(ls $STATE/*.planted.json)\" ]"
kill_planted; python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t95d3.out" 2>&1; rc=$?
chk "T95d3 guard: genuine state with --restore --sha COMMIT: restored, exit 0 (got $rc), state empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"

echo "== T96 (r9: review r8 B1 and M1, class: an exit code that says nothing is planted while planted-ness is unknown; docs must match code) --restore with NO marker, --restore --sha, other TMPDIR, documented exit codes"
# a) no marker anywhere, no --sha: the files are unknown: exit 2 (r8: exit 0), nothing written
fresh_root; python3 "$RUN" --root "$T/root" --restore >"$S/t96a.out" 2>&1; rc=$?; cut -c1-300 "$S/t96a.out"
chk "T96a --restore with no marker anywhere and no --sha: exit 2 (got $rc; r8: 0), text says CANNOT TELL and names both ways out (TMPDIR of the killed run, --sha), file untouched" "[ $rc -eq 2 ] && grep -q 'CANNOT TELL' '$S/t96a.out' && grep -q -- '--sha COMMIT' '$S/t96a.out' && grep -q 'TMPDIR=' '$S/t96a.out' && [ '$(last)' = return1 ]"
# b) with --sha git decides: equal tree 0, different tree 3
fresh_root; python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t96b.out" 2>&1; rc=$?; cut -c1-300 "$S/t96b.out"
chk "T96b --restore --sha COMMIT, no marker, tree equals git: exit 0 (got $rc), text says the tree equals the git archive (r8: ignored --sha, said CANNOT TELL)" "[ $rc -eq 0 ] && grep -q 'tree equals the git archive' '$S/t96b.out'"
kill_planted; rm -f "$STATE"/*.planted.json "$STATE"/*.backup
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t96b2.out" 2>&1; rc=$?; cut -c1-300 "$S/t96b2.out"
chk "T96b2 marker LOST while the file is planted, --restore --sha COMMIT: exit 3 (got $rc; r8: 0), names src/mod.py, file still planted (nothing is guessed), a hand copy from git then gives exit 0" "[ $rc -eq 3 ] && grep -q 'src/mod.py' '$S/t96b2.out' && [ '$(last)' = return2 ]"
git -C "$T/repo" show "$SHA:src/mod.py" > "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >/dev/null 2>&1; rc=$?; chk "T96b3 after the hand copy from git: exit 0 (got $rc)" "[ $rc -eq 0 ]"
# c) the killed run used a TMPDIR outside the places that are searched
fresh_root; OT=$S/othertmp96; rm -rf "$OT"; mkdir -p "$OT"
( export TMPDIR=$OT; exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RPC=$!
for _ in $(seq 120); do ls "$OT"/hadavin-mutation-lane-*/*.planted.json >/dev/null 2>&1 && [ "$(last)" = return2 ] && { sleep 3; break; }; sleep 0.5; done
kill -9 $RPC; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RPC 2>/dev/null
python3 "$RUN" --root "$T/root" --restore >"$S/t96c1.out" 2>&1; rc1=$?
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t96c2.out" 2>&1; rc2=$?
chk "T96c killed run with TMPDIR outside the searched places, file planted: plain --restore exits 2 (got $rc1; r8: 0 'nothing recorded'), --restore --sha exits 3 (got $rc2; r8: 0), the file is still planted" "[ $rc1 -eq 2 ] && [ $rc2 -eq 3 ] && [ '$(last)' = return2 ]"
TMPDIR=$OT python3 "$RUN" --root "$T/root" --restore >"$S/t96c3.out" 2>&1; rc=$?
chk "T96c3 guard: --restore with the TMPDIR of the killed run restores it: exit 0 (got $rc), file back, its state folder empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z \"\$(ls $OT/hadavin-mutation-lane-*/*.planted.json 2>/dev/null)\" ]"
rm -rf "$OT"
# d) documented exit codes match the code: the table in the docstring is parsed and each observed exit code must sit in the row that describes it
fresh_root
python3 - "$RUN" "$T/root" "$SHA" "$T/repo" "$STATE" <<'PY' >"$S/t96e.out" 2>&1; rc=$?
import importlib.util, json, os, re, subprocess, sys
run, root, sha, repo, state = sys.argv[1:6]
spec = importlib.util.spec_from_file_location("runmod", run); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
doc = r.__doc__
head = doc[doc.index("Exit codes"):doc.index("A line `SUMMARY")]
rows, cur = {}, None
for line in head.splitlines()[1:]:
    m = re.match(r"^  (\d+|128\+N)\s+(.*)$", line)
    if m: cur = m.group(1); rows[cur] = m.group(2)
    elif cur and line.startswith("       "): rows[cur] += " " + line.strip()
bad = []
codes = {str(v) for k, v in vars(r).items() if k.startswith("EXIT_")} | {"0", "128+N"}
if set(rows) != codes: bad.append(f"docstring rows {sorted(rows)} != exit codes in the code {sorted(codes)}")
def go(*args):
    return subprocess.run([sys.executable, run, "--root", root, "--restore", *args], capture_output=True, text=True).returncode
mod = os.path.join(root, "src/mod.py"); orig = open(mod).read()
key = r.key_for(__import__("pathlib").Path(root).resolve())
scen = []
scen.append((go(), "NO marker for this root exists anywhere"))
scen.append((go("--sha", sha, "--repo", repo), "found the whole tree equal"))
open(mod, "w").write(orig.replace("return 1", "return 2"))
scen.append((go("--sha", sha, "--repo", repo), "when the tree differs from git"))
open(mod, "w").write(orig)
os.makedirs(state, mode=0o700, exist_ok=True)
mk = os.path.join(state, key + ".planted.json"); open(mk, "w").write(json.dumps({"root": "/nowhere/else", "backup": "x"}))
scen.append((go(), "names another root or another backup path"))
os.unlink(mk)
for rc, phrase in scen:
    where = [k for k, v in rows.items() if phrase in v]
    print(f"exit {rc}: the docstring rows that contain {phrase!r}: {where}")
    if where != [str(rc)]: bad.append(f"exit {rc} observed, but the docstring puts {phrase!r} under {where}")
for opt in ("--restore", "--sha", "--discard-marker", "--helper-timeout"):
    if opt not in doc: bad.append(f"option {opt} is not in the docstring")
print("BAD:", bad); sys.exit(1 if bad else 0)
PY
cut -c1-300 "$S/t96e.out"; chk "T96d the exit-code table of the docstring is parsed; every code in the code has a row, and four observed --restore results (no marker, --sha equal, --sha different, marker for another root) sit in the row that says so; the new options are named (exit $rc; r8: fails)" "[ $rc -eq 0 ]"
# e) a marker that cannot be used is removed with --discard-marker, only when git confirms the files
kill_planted; git -C "$T/repo" show "$SHA:src/mod.py" > "$T/root/src/mod.py"
python3 - "$STATE" <<'PY'
import glob, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; m = json.load(open(mk)); m["root_ino"] += 1; json.dump(m, open(mk, "w"))
PY
python3 "$RUN" --root "$T/root" --restore >"$S/t96f1.out" 2>&1; rc1=$?
python3 "$RUN" --root "$T/root" --restore --discard-marker >"$S/t96f2.out" 2>&1; rc2=$?
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" --discard-marker >"$S/t96f3.out" 2>&1; rc3=$?; cut -c1-250 "$S/t96f3.out"
chk "T96e stale folder identity in the marker: --restore exits 3 for ever (got $rc1); --discard-marker without --sha is refused, exit 2 (got $rc2); with --sha and an equal tree it removes marker and backup: exit 0 (got $rc3; r8: unknown option, exit 2), state empty" "[ $rc1 -eq 3 ] && [ $rc2 -eq 2 ] && [ $rc3 -eq 0 ] && [ -z '$(state_files)' ] && [ '$(last)' = return1 ]"
kill_planted
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" --discard-marker >"$S/t96f4.out" 2>&1; rc=$?; cut -c1-250 "$S/t96f4.out"
chk "T96e2 --discard-marker while the file is STILL planted (tree differs from git): exit 3 (got $rc; r8: 2), nothing removed, file still planted" "[ $rc -eq 3 ] && planted_kept"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
# f) a write that fails half way (the file-size limit of the process): fail closed, marker kept, a second restore finishes
SHA0=$SHA; git -C "$T/repo" checkout -q -b r9big 2>/dev/null; python3 -c "print('X = 1'); print('# ' + 'filler ' * 400)" > "$T/repo/src/big.py"; git -C "$T/repo" add -A; git -C "$T/repo" -c user.email=a@b -c user.name=n commit -qm big; SHA=$(git -C "$T/repo" rev-parse HEAD)
fresh_root; ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X ${NCF---no-control} --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/big.py --old 'X = 1' --new 'X = 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RPF=$!
for _ in $(seq 120); do ls "$STATE"/*.planted.json >/dev/null 2>&1 && grep -q 'X = 2' "$T/root/src/big.py" && { sleep 3; break; }; sleep 0.5; done
kill -9 $RPF; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RPF 2>/dev/null
( ulimit -f 1; python3 "$RUN" --root "$T/root" --restore ) >"$S/t96g1.out" 2>&1; rc1=$?; cut -c1-250 "$S/t96g1.out"
SZ=$(wc -c < "$T/root/src/big.py"); kept=0; keptstate && kept=1
git -C "$T/repo" show "$SHA:src/big.py" > "$S/big.orig"
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc2=$?
chk "T96f GUARD (passes on r8 too: it pins the behaviour): the write is cut short by a 1 KiB file-size limit: exit 3 (got $rc1), 'RESTORE FAILED', the file holds only a part ($SZ bytes), marker and backup KEPT ($kept); the second restore without the limit: exit 0 (got $rc2), file equals git, state empty" "[ $rc1 -eq 3 ] && grep -q 'RESTORE FAILED' '$S/t96g1.out' && [ $SZ -lt 2000 ] && [ $kept -eq 1 ] && [ $rc2 -eq 0 ] && cmp -s '$T/root/src/big.py' '$S/big.orig' && [ -z '$(state_files)' ]"
git -C "$T/repo" checkout -q - 2>/dev/null || git -C "$T/repo" checkout -q master 2>/dev/null || git -C "$T/repo" checkout -q main; SHA=$SHA0; rm -f "$T/repo/src/big.py"
# g) a file with two names: refused BEFORE the mode is changed
kill_planted; chmod 600 "$T/root/src/mod.py"; rm -f "$S/othername96"; ln "$T/root/src/mod.py" "$S/othername96"
python3 "$RUN" --root "$T/root" --restore >"$S/t96h.out" 2>&1; rc=$?; MODE=$(stat -c %a "$T/root/src/mod.py"); cut -c1-250 "$S/t96h.out"
chk "T96g the planted file got a second name after the plant: exit 3 (got $rc), the text says 'mode not changed', the mode is still 600 (got $MODE; r8 set it to 644 first), file still planted, marker kept" "[ $rc -eq 3 ] && grep -q 'mode not changed' '$S/t96h.out' && [ '$MODE' = 600 ] && planted_kept"
rm -f "$S/othername96"; chmod 644 "$T/root/src/mod.py"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
# h) a target the tree comparison does not look at is refused
fresh_root; mkdir -p "$T/root/src/__pycache__" "$T/root/.pytest_cache"; printf 'def g():\n    return 1\n' > "$T/root/src/__pycache__/m2.py"; printf 'x = 1\n' > "$T/root/.pytest_cache/c.py"
FILE=src/__pycache__/m2.py mut -- tests/test_fast.py >"$S/t96i1.out" 2>&1; rc1=$?; head -c 300 "$S/t96i1.out"
FILE=.pytest_cache/c.py mut -- tests/test_fast.py >"$S/t96i2.out" 2>&1; rc2=$?
mut --extra src/__pycache__/m2.py -- tests/test_fast.py >"$S/t96i3.out" 2>&1; rc3=$?
chk "T96h a mutant file inside __pycache__ (exit $rc1) or .pytest_cache (exit $rc2), or an --extra there (exit $rc3): all exit 2 (r8: planted them: not 2), nothing planted, state empty" "[ $rc1 -eq 2 ] && [ $rc2 -eq 2 ] && [ $rc3 -eq 2 ] && grep -q 'does not look at' '$S/t96i1.out' && grep -q 'return 1' '$T/root/src/__pycache__/m2.py' && [ -z '$(state_files)' ]"
# i) an output file in the state folder could pose as a marker
fresh_root; mkdir -p -m 700 "$STATE"
mut --out-json "$STATE/zz.planted.json" -- tests/test_fast.py >"$S/t96j1.out" 2>&1; rc1=$?
mut --raw "$STATE/rawdir" -- tests/test_fast.py >"$S/t96j2.out" 2>&1; rc2=$?
chk "T96i --out-json or --raw inside the state folder: exit 2 (got $rc1, $rc2; r8 wrote there), no file created, nothing planted" "[ $rc1 -eq 2 ] && [ $rc2 -eq 2 ] && [ ! -e '$STATE/zz.planted.json' ] && [ ! -e '$STATE/rawdir' ] && [ '$(last)' = return1 ]"
# j) --restore --sha: a signal before the first write ends it; a stalled git is stopped
printf '#!/bin/bash\nfor a in "$@"; do [ "$a" = archive ] && exec %s 3151; done\nexec %s "$@"\n' "$SL" "$GIT" > "$S/wrap/git"; chmod +x "$S/wrap/git"
kill_planted
( PATH="$S/wrap:$PATH" exec python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" ) >"$S/t96k1.out" 2>&1 & RR=$!
for _ in $(seq 40); do pgrep -f "$SL 3151" >/dev/null && break; sleep 0.25; done; kill -TERM $RR
for _ in $(seq 40); do kill -0 $RR 2>/dev/null || break; sleep 0.25; done
if kill -0 $RR 2>/dev/null; then kill -9 $RR; rc=999; else wait $RR; rc=$?; fi; pkill -9 -f "$SL 3151" 2>/dev/null
chk "T96j1 SIGTERM while 'git archive' stalls inside --restore --sha: ends at once with 143 (got $rc; r8: the signal was only remembered and the run hung), the file is still planted and marker and backup are kept (nothing was written)" "[ $rc -eq 143 ] && planted_kept"
( PATH="$S/wrap:$PATH" exec python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" --helper-timeout 2 ) >"$S/t96k2.out" 2>&1 & RR=$!
for _ in $(seq 60); do kill -0 $RR 2>/dev/null || break; sleep 0.25; done
if kill -0 $RR 2>/dev/null; then kill -9 $RR; rc=999; else wait $RR; rc=$?; fi; pkill -9 -f "$SL 3151" 2>/dev/null; cut -c1-250 "$S/t96k2.out"
chk "T96j2 a stalled 'git archive' with --helper-timeout 2: stopped, exit 3 (got $rc; r8: unknown option), text 'did not finish within 2 s', marker kept, file still planted" "[ $rc -eq 3 ] && grep -q 'did not finish within 2 s' '$S/t96k2.out' && planted_kept"
rm -f "$S/wrap/git"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1
# k) the state folder is synced after a write and a removal (calls are recorded: this proves the calls, not the disk)
python3 - "$RUN" <<'PY' >"$S/t96l.out" 2>&1; rc=$?
import importlib.util, os, pathlib, stat, sys, tempfile
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
d = tempfile.mkdtemp(); os.chmod(d, 0o700); r.STATE = pathlib.Path(d)
dirs, real = [], os.fsync
def rec(fd): dirs.append(stat.S_ISDIR(os.fstat(fd).st_mode)); real(fd)
os.fsync = rec
r.write_state(r.STATE / "a.json", b"x"); n1 = dirs.count(True)
r.unlink_state(r.STATE / "a.json"); n2 = dirs.count(True)
os.fsync = real
print("folder syncs after write:", n1, "after removal:", n2)
sys.exit(0 if (n1, n2) == (1, 2) and not (r.STATE / "a.json").exists() else 1)
PY
cut -c1-200 "$S/t96l.out"; chk "T96k write_state syncs the state FOLDER once, unlink_state removes and syncs it again (exit $rc; r8: no folder sync, no unlink_state)" "[ $rc -eq 0 ]"
# l) a forged mode in the marker is refused when git is the authority (--sha)
kill_planted; python3 - "$STATE" <<'PY'
import glob, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; m = json.load(open(mk)); m["mode"] = 0o777; json.dump(m, open(mk, "w"))
PY
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >"$S/t96m.out" 2>&1; rc=$?; cut -c1-250 "$S/t96m.out"
chk "T96l marker mode 0777 (git has no execute bit for this file) with --restore --sha: exit 3 (got $rc; r8: restored and wrote 0777), 'execute bits', file still planted" "[ $rc -eq 3 ] && grep -q 'execute bits' '$S/t96m.out' && [ '$(last)' = return2 ]"
python3 - "$STATE" <<'PY'
import glob, json, sys
mk = glob.glob(sys.argv[1] + "/*.planted.json")[0]; m = json.load(open(mk)); m["mode"] = 0o644; json.dump(m, open(mk, "w"))
PY
python3 "$RUN" --root "$T/root" --restore --sha "$SHA" --repo "$T/repo" >/dev/null 2>&1; rc=$?; chk "T96l2 guard: the genuine mode with --sha restores: exit 0 (got $rc), state empty" "[ $rc -eq 0 ] && [ '$(last)' = return1 ] && [ -z '$(state_files)' ]"

}
echo "FAILED CHECKS: $FAILS (of $CHECKS checks run; skipped:${SKIPPED:- none})"
