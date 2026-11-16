#!/bin/bash
# Safety tests T1-T88 of run.py on a TOY repository with made-up files (never the real code).
# usage: RUN=/path/to/run.py SCRATCH=/some/scratch/dir VENV=/folder/with/bin/python ./safety-tests.sh   (prints PASS/FAIL per check)
# Round 7: run.py now runs the baseline BY DEFAULT; the helper base()/mut() adds --no-control (the old behaviour) unless NCF is set: `NCF= mut ...` runs with the real default. Against the r6 copy of run.py (no --no-control option) export NCF= (empty).
# Against an older copy of run.py: STATEDIR=<its state folder name> (NEWTESTS=0 runs only T1-T19; T36-T88 (rounds 4 to 7) need the new code; SKIP_T35=1 skips the test that writes to the shared /tmp folder).
RUN=${RUN:-$(dirname "$(readlink -f "$0")")/run.py}
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
{
kill_planted() { fresh_root; bg; waitplant; kill -9 $RP; sleep 1; pkill -9 -f "$T/root/.venv/bin/python -m pytest"; wait $RP 2>/dev/null; }
keptstate() { [ -n "$(ls "$STATE"/*.planted.json 2>/dev/null)" ] && [ -n "$(ls "$STATE"/*.backup 2>/dev/null)" ]; }
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
python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1; rc=$?; chk "T76d guard: a forged backup (hash differs) is still exit 2 and nothing is written (got $rc)" "[ $rc -eq 2 ] && [ '$(last)' = return2 ]"
git -C "$T/repo" show "$SHA:src/mod.py" > "$BK"; python3 "$RUN" --root "$T/root" --restore >/dev/null 2>&1

echo "== T77 (review r6 M2) the baseline is the DEFAULT; --no-control gives exit 5 and never says COMPLETE"
fresh_root; NCF= mut -- tests/test_fail.py >"$S/t77a.out" 2>&1; rc=$?; cut -c1-200 "$S/t77a.out" | tail -2
chk "T77a no option at all, tree already failing: the baseline refuses the mutants, exit 2 (got $rc), baseline file says NO, no mutant raw file, file unchanged (r6: ran every mutant as KILLED)" "[ $rc -eq 2 ] && grep -q 'baseline usable: NO' '$S/rawT/X-baseline.txt' && [ ! -e '$S/rawT/X-m1.txt' ] && [ '$(last)' = return1 ]"
fresh_root; NCF= mut -- tests/test_fast.py >"$S/t77b.out" 2>&1; rc=$?
chk "T77b no option at all, healthy tree: baseline recorded and used, exit 0 (got $rc), 'baseline: rc 0, 1 passed' in the raw file, SUMMARY says COMPLETE" "[ $rc -eq 0 ] && grep -q 'baseline: rc 0, 1 passed' '$S/rawT/X-m1.txt' && grep -q 'baseline usable: yes' '$S/rawT/X-baseline.txt' && grep -qE '(^|[^N])COMPLETE \(a baseline ran' '$S/t77b.out'"
fresh_root; NCF= mut --no-control -- tests/test_fast.py >"$S/t77c.out" 2>&1; rc=$?
chk "T77c --no-control, every verdict clean: exit 5 (got $rc), SUMMARY says NO BASELINE and INCOMPLETE and never the word COMPLETE on its own, raw file says baseline NOT RUN, no baseline file" "[ $rc -eq 5 ] && grep -q 'NO BASELINE' '$S/t77c.out' && grep -q 'INCOMPLETE' '$S/t77c.out' && ! grep -qE '(^|[^N])COMPLETE' '$S/t77c.out' && grep -q 'baseline: NOT RUN' '$S/rawT/X-m1.txt' && [ ! -e '$S/rawT/X-baseline.txt' ]"
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
note = r.sweep_group(p.pid, before - 1000, before)    # the test group "ended" at `before`: the stranger started later
print("stranger case:", note, "| alive:", p.poll() is None, flush=True)
note2 = r.sweep_group(p.pid, before - 1000, r.boot_ticks())   # control: it started inside the window: ours, stopped
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

}
echo "FAILED CHECKS: $FAILS (of $CHECKS checks run; skipped:${SKIPPED:- none})"
