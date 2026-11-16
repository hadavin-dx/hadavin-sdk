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
        S = r.SIG; S.critical = S.allow = S.fired = False; S.first = None
        sys.argv = ["run.py", "--root", root, "--sha", sha, "--repo", repo, "--prefix", "X", "--raw", raw, "--pythonpath", root + "/src", "--id", "m1", "--file", "src/mod.py", "--old", "return 1", "--new", "return 2", "--", "tests/test_fast.py"]
        try: r.main(); code = 0
        except SystemExit as e: code = e.code
        txt = pathlib.Path(root, "src/mod.py").read_text()
        left = [f for f in os.listdir(r.STATE) if not f.endswith(".lock")]
        if code != 128 + sg or "return 1" not in txt or left: bad.append((window, sg, code, txt.strip()[-8:], left))
print(len(want) * 2, "cases (signal x window);", len(bad), "bad:", bad[:6], flush=True)
sys.exit(1 if bad or sorted(r.HANDLED_SIGNALS) != want else 0)
PY
chk "T47a all handled signals in the plant window and the restore window: exit 128+N, file restored, state empty" "[ $? -eq 0 ]"
echo "FAILED CHECKS: $FAILS (of $CHECKS)"
