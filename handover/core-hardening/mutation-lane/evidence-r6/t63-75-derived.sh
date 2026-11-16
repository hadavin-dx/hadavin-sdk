#!/bin/bash
# Safety tests T1-T75 of run.py on a TOY repository with made-up files (never the real code).
# usage: RUN=/path/to/run.py SCRATCH=/some/scratch/dir VENV=/folder/with/bin/python ./safety-tests.sh   (prints PASS/FAIL per check)
# Against an older copy of run.py: STATEDIR=<its state folder name> (NEWTESTS=0 runs only T1-T19; T36-T75 (rounds 4 to 6) need the new code; SKIP_T35=1 skips the test that writes to the shared /tmp folder).
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
git add -A; git -c user.email=a@b -c user.name=n commit -qm init; SHA=$(git rev-parse HEAD); REALREPO=$T/repo   # the toy repository stands in for "the real repository" (this folder is not inside a git repository)
reset_state() { pkill -9 -f "$T/root/.venv/bin/python -m pytest" 2>/dev/null; rm -rf "$STATE"; }
# every scenario starts from a fresh state folder, so a crash in one cannot make the next ones fail (review r2 safety M2)
fresh_root() { reset_state; rm -rf "$T/root"; mkdir "$T/root"; git -C "$T/repo" archive "$SHA" | tar -x -C "$T/root"; ln -s "$VENV" "$T/root/.venv"; rm -rf "$S/rawT"; }
fresh_root
printf '[{"id":"m1","file":"src/mod.py","old":"return 1","new":"return 2"},{"id":"m2","file":"src/mod.py","old":"return 1","new":"return 3"}]' > "$S/two.json"
base() { python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" "$@"; }
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
bg() { ( exec python3 "$RUN" --root "$T/root" --sha "$SHA" --repo "$T/repo" --prefix X --raw "$S/rawT" --pythonpath "$T/root/src" --id m1 --file src/mod.py --old 'return 1' --new 'return 2' -- tests/test_slow.py ) >/dev/null 2>&1 & RP=$!; }
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
sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
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
chk "T64b the text in run.py no longer says a real fault 'acts like SIGKILL' and says it spins" "! grep -q 'acts like SIGKILL' '$RUN' && grep -q 'spins at full speed' '$RUN'"

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
fresh_root; mut -- tests/test_fast.py >/dev/null 2>&1; chk "T66f no --control: every raw file says 'baseline: NOT RUN'" "grep -q 'baseline: NOT RUN' '$S/rawT/X-m1.txt'"

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
fresh_root; mut -- tests/test_fast.py >"$S/t67e.out" 2>&1; rc=$?
chk "T67e guard: every mutant killed: exit 0 (got $rc), summary says COMPLETE" "[ $rc -eq 0 ] && grep -q 'COMPLETE' '$S/t67e.out' && ! grep -q INCOMPLETE '$S/t67e.out'"
fresh_root; mut --extra junk.txt -- tests/test_junk.py >/dev/null 2>&1; rc=$?; chk "T67f guard: a clean verdict with a declared --extra file keeps exit 0 (got $rc)" "[ $rc -eq 0 ]"
fresh_root; base --list "$S/two.json" -- tests/test_junk.py >/dev/null 2>&1; rc=$?; chk "T67g exit 4 (tree not clean) still wins over exit 5 (got $rc)" "[ $rc -eq 4 ]"

echo "== T68 (review r5 nit 3) --restore with no marker anywhere says it CANNOT TELL, not 'nothing to restore'"
fresh_root; out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-240
chk "T68 text says 'CANNOT TELL' and no longer 'nothing to restore' (exit $rc, still 0)" "[ $rc -eq 0 ] && printf %s '$out' | grep -q 'CANNOT TELL' && ! printf %s '$out' | grep -q 'nothing to restore'"

echo "== T69 (review r5 nit 4) a control marker: invalid JSON is a refusal; a group that cannot be settled keeps the marker"
fresh_root; KEY=$(printf %s "$(readlink -f "$T/root")" | sha256sum | cut -c1-16); mkdir -m 700 -p "$STATE"; printf 'this is not json' > "$STATE/$KEY.control.json"
out=$(python3 "$RUN" --root "$T/root" --restore 2>&1); rc=$?; echo "$out" | cut -c1-200
chk "T69a invalid JSON in the control marker: exit 2 (got $rc), 'REFUSED', no traceback" "[ $rc -eq 2 ] && printf %s '$out' | grep -q REFUSED && ! printf %s '$out' | grep -q Traceback"
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
fresh_root; mut --sha "${SHA:0:7}" -- tests/test_fast.py >/dev/null 2>&1; rc=$?
chk "T74a a short id works (rc $rc) and the raw file records the FULL id (and how it was given)" "[ $rc -eq 0 ] && grep -q 'base commit: $SHA (given as ${SHA:0:7})' '$S/rawT/X-m1.txt' && grep -q 'compared: <fresh git archive $SHA' '$S/rawT/X-tree-diff.txt'"
TREEID=$(git -C "$T/repo" rev-parse 'HEAD^{tree}'); fresh_root; mut --sha "$TREEID" -- tests/test_fast.py >"$S/t74b.out" 2>&1; rc=$?; cut -c1-200 "$S/t74b.out"
chk "T74b the id of a TREE (git archive would accept it) is refused, exit 2 (got $rc), nothing planted" "[ $rc -eq 2 ] && [ '$(last)' = return1 ]"
fresh_root; mut --sha 1234567890abcdef -- tests/test_fast.py >/dev/null 2>&1; rc=$?; chk "T74c guard: an unknown id is refused, exit 2 (got $rc)" "[ $rc -eq 2 ]"

echo "== T75 (review r5 smaller point) git and patch run with a clean environment: GIT_DIR and GIT_WORK_TREE of the caller do not reach them"
fresh_root; GIT_DIR=/nonexistent/gitdir GIT_WORK_TREE=/nonexistent/tree mut -- tests/test_fast.py >"$S/t75.out" 2>&1; rc=$?; cut -c1-200 "$S/t75.out" | tail -2
chk "T75 with a bogus GIT_DIR and GIT_WORK_TREE in the caller's environment the run still works (exit 0, got $rc)" "[ $rc -eq 0 ]"

echo "FAILED CHECKS: $FAILS (of $CHECKS)"
