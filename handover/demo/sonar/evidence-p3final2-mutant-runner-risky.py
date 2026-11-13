import subprocess, sys, shutil, os
os.chdir(sys.argv[1])
T = "tests/test_path_confinement.py"
P = "tools/pathconfine.py"
CI = "load_tools/check_invariants.py"
M = [
 ("R01 a working folder that is a file-system top is allowed", P, '    if not os.path.splitroot(real)[2]:\n        return True', '    if False:\n        return True'),
 ("R02 a working folder that is the home folder is allowed", P, '    return os.path.normcase(real) == os.path.normcase(os.path.realpath(os.path.expanduser("~")))', '    return False'),
 ("R03 working folder wide check dropped", P, 'here = [r for r in [os.path.realpath(os.getcwd())] if not _is_wide(r)]', 'here = [os.path.realpath(os.getcwd())]'),
 ("R04 a written file is found by its loose name", P, '        if last and entry.name != part:', '        if False:'),
 ("R05 folders on the way compared exactly on a write", P, '        if last and entry.name != part:', '        if entry.name != part:'),
]
only = sys.argv[2:] 
res = []
for k, f, a, b in M:
    if only and not any(k.startswith(o) for o in only): continue
    orig = open(f).read()
    assert orig.count(a) == 1, (k, orig.count(a))
    open(f, "w").write(orig.replace(a, b, 1))
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", T, "-q", "-x", "-p", "no:cacheprovider"] + (["-k", os.environ["MUT_K"]] if os.environ.get("MUT_K") else []), capture_output=True, text=True, timeout=400)
        last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))]
        res.append((k, "KILLED" if r.returncode else "SURVIVED", (last[0][:120] if last else "")))
    except subprocess.TimeoutExpired:
        res.append((k, "KILLED(timeout)", ""))
    finally:
        open(f, "w").write(orig)
    print(res[-1], flush=True)
print("mutants:", len(res), "killed:", sum(1 for r in res if r[1].startswith("KILLED")), "survived:", [r[0] for r in res if r[1]=="SURVIVED"])
