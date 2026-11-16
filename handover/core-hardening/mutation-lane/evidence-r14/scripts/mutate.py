#!/usr/bin/env python3
"""r14 mutation table: one hand-planted change per guard in a COPY of run.r14.py (never the real file), run against the test block
that is meant to catch it. Usage: mutate.py <run.r14.py> <safety-tests.r14.sh> <out dir> <scratch dir> <venv> [name ...]"""
import os, re, subprocess, sys, time
RUN, TESTS, OUT, SCR, VENV = map(os.path.abspath, sys.argv[1:6])
ONLY_NAMES = set(sys.argv[6:])
src = open(RUN).read()
C = "T102"; M = "T103"
# (name, block, old, new, expected: set of check ids that must fail, or "SURVIVES" with the reason)
MUT = [
 ("child-args-type", C, 'if type(args) is not list or not args or not all(type(a) is str for a in args):', 'if not args:', {"T102.args-type"}),
 ("child-abs-program", C, 'if not os.path.isabs(args[0]):', 'if False:', {"T102.abs-program"}),
 ("child-identity-compare", C, 'return _identity(prog) == _TRUSTED[name]', 'return True', {"T102.identity-compare", "T102.identity-fields", "T102.identity-ctime"}),
 ("child-pathtext", C, 'prog != _FOUND[name]', 'False', {"T102.program-pathtext"}),
 ("child-trust-first-find", C, 'if name not in _TRUSTED:', 'if True:', {"T102.trust-first-find"}),
 ("child-tool-location-skip", C, 'elif name in _TRUSTED and not tool_location_ok(_TRUSTED[name][0]):', 'elif False:', {"T102.tool-location"}),
 ("child-tool-location-owner", C, 'if st.st_uid != 0 or st.st_mode & 0o022:', 'if False:', {"T102.tool-location"}),
 ("child-seal-missing", C, '_MISSING.add(name)', 'pass', {"T102.seal-missing"}),
 ("child-nul", C, 'if any("\\0" in a for a in args):', 'if False:', {"T102.nul-arg"}),
 ("child-shell", C, 'if kwargs.get("shell"):', 'if False:', {"T102.shell"}),
 ("child-kw-allowed", C, 'if unknown:', 'if False:', {"T102.kw-allowed"}),
 ("child-env-none", C, 'if env is None:', 'if False:', {"T102.env-none"}),
 ("child-env-dict-type", C, 'if type(env) is not dict or not all(', 'if not isinstance(env, dict) or not all(', {"T102.env-type"}),
 ("child-env-text-types", C, 'type(k) is str and type(v) is str for k, v in env.items()', 'True for k, v in env.items()', {"T102.env-type"}),
 ("child-env-allowlist", C, 'extra = sorted(set(env) - CHILD_ENV_ALLOWED)', 'extra = []', {"T102.env-allowlist"}),
 ("child-env-value-nul", C, 'if extra or any("\\0" in v for v in env.values()):', 'if extra:', {"T102.env-value-nul"}),
 ("child-cwd-abs", C, 'not isinstance(cwd, (str, os.PathLike)) or not os.path.isabs(os.fspath(cwd))', 'not isinstance(cwd, (str, os.PathLike))', {"T102.cwd-abs"}),
 ("child-cwd-real", C, 'if cwd is not None and os.path.realpath(os.fspath(cwd)) != os.fspath(cwd):', 'if False:', {"T102.cwd-real"}),
 ("child-start-new-session", C, 'kwargs["start_new_session"] is not True', 'False', {"T102.start-new-session"}),
 ("child-git-show-toplevel-loose", C, 'if rest in (["rev-parse", "--show-toplevel"], ["rev-parse", "--is-inside-work-tree"]):', 'if rest[:2] == ["rev-parse", "--show-toplevel"] or rest == ["rev-parse", "--is-inside-work-tree"]:', {"T102.git-show-toplevel"}),
 ("child-git-is-inside-loose", C, 'if rest in (["rev-parse", "--show-toplevel"], ["rev-parse", "--is-inside-work-tree"]):', 'if rest == ["rev-parse", "--show-toplevel"] or rest[:2] == ["rev-parse", "--is-inside-work-tree"]:', {"T102.git-is-inside"}),
 ("child-git-any-rev-parse", C, 'if rest in (["rev-parse", "--show-toplevel"], ["rev-parse", "--is-inside-work-tree"]):', 'if rest[:1] == ["rev-parse"] and len(rest) == 2:', {"T102.git-subcommand"}),
 ("child-git-verify-option", C, 'return not rest[3].startswith("-")', 'return True', {"T102.git-verify"}),
 ("child-git-verify-len", C, 'rest[:3] == ["rev-parse", "--verify", "--quiet"] and len(rest) == 4', 'rest[:3] == ["rev-parse", "--verify", "--quiet"] and len(rest) >= 4', {"T102.git-verify"}),
 ("child-git-archive-option", C, 'return rest[0] == "archive" and len(rest) == 2 and not rest[1].startswith("-")', 'return rest[0] == "archive" and len(rest) == 2', {"T102.git-archive"}),
 ("child-git-archive-len", C, 'return rest[0] == "archive" and len(rest) == 2 and not rest[1].startswith("-")', 'return rest[0] == "archive" and not rest[1].startswith("-")', {"T102.git-archive"}),
 ("child-git-dash-C", C, 'if len(a) < 4 or a[1] != "-C":', 'if len(a) < 4:', {"T102.git-C"}),
 ("child-git-min-len", C, 'if len(a) < 4 or a[1] != "-C":', 'if a[1] != "-C":', {"T102.git-C"}),
 ("child-patch-len", C, 'len(a) == 10\n', 'len(a) >= 10\n', {"T102.patch-shape"}),
 ("child-patch-abs-d", C, 'and os.path.isabs(a[7])', 'and True', {"T102.patch-shape"}),
 ("child-patch-abs-i", C, 'and os.path.isabs(a[9])', 'and True', {"T102.patch-shape"}),
 ("child-patch-order", C, 'and a[8] == "-i"', 'and True', {"T102.patch-shape"}),
 ("child-set-root-none", C, '    _CHILD_PYTHON = None if root is None else os.path.join(os.fspath(root), ".venv/bin/python")', '    if root is None:\n        return\n    _CHILD_PYTHON = os.path.join(os.fspath(root), ".venv/bin/python")', {"T102.python-root-none"}),
 ("child-python-endswith", C, 'prog == _CHILD_PYTHON and _CHILD_PYTHON_ID is not None', 'prog.endswith("/.venv/bin/python") and _CHILD_PYTHON_ID is not None', {"T102.python-path-text"}),
 ("child-python-probe-any", C, 'return a[2] == IMPORT_PROBE_CODE and not a[3].startswith("-")', 'return True', {"T102.python-shape-probe"}),
 ("child-python-probe-option", C, 'return a[2] == IMPORT_PROBE_CODE and not a[3].startswith("-")', 'return a[2] == IMPORT_PROBE_CODE', {"T102.python-shape-probe"}),
 ("child-python-pytest-head", C, 'return a[1 : 1 + len(head)] == head and', 'return a[1:3] == head[:2] and', {"T102.python-shape-pytest"}),
 ("child-python-pytest-tail", C, ' and a[1 + len(head) : 3 + len(head)] == list(\n        PYTEST_FIXED_TAIL\n    )', '', {"T102.python-shape-pytest"}),
 ("child-python-pin-off", C, 'if _identity(prog) == _CHILD_PYTHON_ID:', 'if True:', {"T102.python-pin", "T102.python-pin-ctime"}),
 ("child-identity-r13-fields", C, 'return real, st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns', 'return real, st.st_dev, st.st_ino', {"T102.identity-fields", "T102.identity-ctime", "T102.python-pin", "T102.python-pin-ctime"}),
 ("child-identity-no-ctime", C, 'return real, st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns', 'return real, st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns', {"T102.identity-ctime", "T102.python-pin-ctime"}),
 ("child-identity-no-size", C, 'return real, st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns', 'return real, st.st_dev, st.st_ino, st.st_mtime_ns, st.st_ctime_ns', "SURVIVES: equivalent, st_size is redundant next to st_ctime_ns (any write changes the change time)"),
 ("child-identity-no-mtime", C, 'return real, st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns', 'return real, st.st_dev, st.st_ino, st.st_size, st.st_ctime_ns', "SURVIVES: equivalent, st_mtime_ns is redundant next to st_ctime_ns (any write changes the change time)"),
 ("raw-dots", M, 'if set(value.split("/")) & {"..", "."}:', 'if False:', {"T103a.raw-dots", "T103a.outjson-dots"}),
 ("raw-symlink", M, 'if os.path.islink(cur):', 'if False:', {"T103a.raw-symlink", "T103a.outjson-symlink", "T103b.4", "T103b.5", "T103b.8", "T103b.9"}),
 ("raw-levels", M, 'if len(levels) < 2:', 'if False:', {"T103a.raw-levels", "T103a.outjson-levels", "T103b.1", "T103b.2", "T103b.6"}),
 ("raw-no-toplevel (uid 65534 run T103b)", M, 'if len(levels) < 2:', 'if len(levels) < 1:', {"T103a.raw-levels", "T103b.2", "T103b.6"}),
 ("raw-system", M, 'if levels[0] in SYSTEM_TOP_FOLDERS and not', 'if False and not', {"T103a.raw-system", "T103a.outjson-system", "T103b.3", "T103b.7"}),
 ("raw-var-tmp-not-allowed", M, 'not (levels[0] == "var" and levels[1] == "tmp")', 'True', {"T103a.raw-system"}),
 ("raw-sharedtmp", M, 'if is_folder and real in SHARED_TEMP_FOLDERS:', 'if False:', {"T103a.raw-sharedtmp"}),
 ("raw-no-resolve", M, 'real = os.path.realpath(here)', 'real = here', "SURVIVES: layered, a link on the way is already refused by the symbolic-link guard before the resolved path is looked at; the two layers cover the same cases on Linux"),
 ("raw-not-wired", M, '("--raw", a.raw, True)', '("--raw", None, True)', {"T103b.1", "T103b.2", "T103b.3", "T103b.4", "T103b.5"}),
 ("out-json-not-wired", M, ', ("--out-json", a.out_json, False)', '', {"T103b.6", "T103b.7", "T103b.8", "T103b.9"}),
 ("leader-no-module-check", M, 'and argv[1:3] == ["-m", "pytest"]', '', {"T103a.leader-shape"}),
 ("leader-no-rootdir", M, 'and f"--rootdir={os.fspath(root)}" in argv', '', {"T103a.leader-shape"}),
 ("leader-no-python-path", M, 'and argv[0] == os.path.join(os.fspath(root), ".venv/bin/python")', '', {"T103a.leader-shape"}),
 ("leader-not-used-pgid-branch", M, '                and is_test_leader(rec_argv, root)\n', '', {"T103c"}),
 ("leader-not-used-command-branch", M, '            and is_test_leader(argv, root)\n', '', {"T103c3"}),
 ("leader-always-false", M, 'return (\n        isinstance(argv, list)', 'return False and (\n        isinstance(argv, list)', {"T103a.leader-shape", "T103c2"}),
 ("note-always-long", M, 'if mode & 0o002 or mode_note:', 'if True:', {"T103d"}),
]
os.makedirs(OUT, exist_ok=True)
rows = []
for name, block, old, new, exp in MUT:
    if ONLY_NAMES and name not in ONLY_NAMES:
        continue
    if src.count(old) != 1:
        rows.append((name, block, "NOT PLANTED: old text occurs %d times" % src.count(old), "", exp, "ERROR")); print(rows[-1], flush=True); continue
    fn = os.path.join(OUT, "run.mut-%s.py" % re.sub(r"[^a-z0-9-]", "", name.split(" ")[0]))
    open(fn, "w").write(src.replace(old, new)); os.chmod(fn, 0o755)
    scr = os.path.join(SCR, "m-" + re.sub(r"[^a-z0-9-]", "", name.split(" ")[0])); subprocess.run(["rm", "-rf", scr]); os.makedirs(scr)
    env = dict(os.environ, RUN=fn, SCRATCH=scr, VENV=VENV, ONLY=block)
    t0 = time.time()
    cp = subprocess.run(["bash", TESTS], env=env, capture_output=True, text=True, timeout=900)
    out = cp.stdout + cp.stderr
    open(os.path.join(OUT, "out-%s.txt" % re.sub(r"[^a-z0-9-]", "", name.split(" ")[0])), "w").write(out)
    failed = re.findall(r"^  FAIL: (\S+)", out, re.M)
    ran = re.search(r"FAILED CHECKS: (\d+) \(of (\d+) checks run", out)
    verdict = "KILLED" if failed else "SURVIVED"
    if isinstance(exp, set):
        ok = verdict == "KILLED" and exp <= {f.rstrip(":") for f in failed}
        status = "as expected" if ok else "UNEXPECTED (wanted %s)" % sorted(exp)
    else:
        status = "as expected (%s)" % exp if verdict == "SURVIVED" else "UNEXPECTED, expected to survive"
    cmd = f"ONLY={block} RUN=<{os.path.basename(fn)}> bash safety-tests.r14.sh"
    rows.append((name, block, cmd, ", ".join(failed) if failed else "(none)", ran.group(2) if ran else "?", verdict + " - " + status, round(time.time() - t0)))
    print(rows[-1], flush=True)
with open(os.path.join(OUT, "..", "MUTATION-TABLE.md" if not ONLY_NAMES else "MUTATION-TABLE-partial.md"), "w") as f:
    f.write("| mutant | block run | command | failing check ids | checks run | verdict | seconds |\n|---|---|---|---|---|---|---|\n")
    for r in rows:
        if len(r) == 7:
            f.write("| %s | %s | `%s` | %s | %s | %s | %s |\n" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
        else:
            f.write("| %s | %s | %s | | | %s | |\n" % (r[0], r[1], r[2], r[5]))
