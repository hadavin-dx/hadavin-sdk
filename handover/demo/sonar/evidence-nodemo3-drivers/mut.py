import os, subprocess, sys
from pathlib import Path
ROOT = Path("/tmp/work/nm3")
PY = "/tmp/work/rv18-1/v/bin/python"
ENV = dict(os.environ, GITLEAKS_BIN="/tmp/work/gl/gitleaks", DPLD_REQUIRE_SCAN="1")
def run(cwd, files, extra=None):
    r = subprocess.run([PY, "-u", "-m", "pytest", "-q", "-p", "no:cacheprovider", *files], cwd=cwd, env=dict(ENV, **(extra or {})), capture_output=True, text=True)
    l = [x for x in r.stdout.strip().splitlines() if x.strip()]
    return l[-1] if l else "(no output) " + r.stderr[-200:]
def mutate(p, old, new):
    s = p.read_text(); assert old in s, old; p.write_text(s.replace(old, new, 1)); return s
EXC = "tests/test_except_clause_hierarchy.py"
HYG = ["tests/test_hygiene.py", "tests/test_no_placeholders.py"]
GUARD = [
 ("G1 skip product rows too (drop startswith)", 'demo_gone and str(r[0]).startswith(DEMO_DIR + "/")', "demo_gone"),
 ("G2a DEMO_GONE always True", 'DEMO_GONE = not (REPO / DEMO_DIR).is_dir()', "DEMO_GONE = True"),
 ("G2b _present ignores its argument (always True)", 'demo_gone and str(r[0]).startswith(DEMO_DIR + "/")', 'True and str(r[0]).startswith(DEMO_DIR + "/")'),
 ("G3 or instead of and", 'demo_gone and str(r[0]).startswith', 'demo_gone or str(r[0]).startswith'),
 ("G4 never skip", 'demo_gone and str(r[0]).startswith(DEMO_DIR + "/")', "False"),
 ("G5 wrong folder name", 'DEMO_DIR = "demo_only"', 'DEMO_DIR = "demo_onl"'),
 ("G6 prefix without slash", 'startswith(DEMO_DIR + "/")', 'startswith(DEMO_DIR)'),
 ("G7 is_file on the folder", '(REPO / DEMO_DIR).is_dir()', '(REPO / DEMO_DIR).is_file()'),
 ("G8 probe fakes.py instead of the folder", '(REPO / DEMO_DIR).is_dir()', '(REPO / DEMO_DIR / "fakes.py").is_file()'),
 ("G9 call site passes False (guarded test never skips)", '_present(list(HANDLERS), DEMO_GONE)', '_present(list(HANDLERS), False)'),
]
OPT = [
 ("O1 helper never skips", 'if not (REPO / ".git").exists():', "if False:"),
 ("O2 _git does not call helper", "    if cwd == REPO:\n        _need_git_work_tree()\n", ""),
 ("O3 scan test does not call helper", "    _need_git_work_tree()  # the canaries", "    pass  # the canaries"),
 ("O4 .git must be a dir (worktree/submodule .git file misread)", '(REPO / ".git").exists()', '(REPO / ".git").is_dir()'),
 ("O5 REPO one level too low", "Path(__file__).resolve().parent.parent  # not from support", "Path(__file__).resolve().parent  # not from support"),
 ("O6 helper inverted", 'if not (REPO / ".git").exists():', 'if (REPO / ".git").exists():'),
 ("O7 _git skips for any folder, not only REPO", "    if cwd == REPO:\n        _need_git_work_tree()\n", "    _need_git_work_tree()\n"),
 ("O8 .git must be a file (clone folder misread)", '(REPO / ".git").exists()', '(REPO / ".git").is_file()'),
]
which = sys.argv[1]
if which == "guard":
    for name, old, new in GUARD:
        print(name)
        for label, d, env in (("demo present", "P", {"DPLD_REQUIRE_DEMO": "1"}), ("demo deleted", "B", {})):
            p = ROOT / d / EXC; orig = mutate(p, old, new)
            try: print(f"    {label}: whole file: {run(ROOT/d,[EXC],env)}")
            finally: p.write_text(orig)
        sys.stdout.flush()
else:
    for name, old, new in OPT:
        if len(sys.argv) > 2 and not name.startswith(sys.argv[2]):
            continue
        print(name)
        for label, d in (("git copy, demo deleted (B)", "B"), ("no-git copy (C)", "C")):
            p = ROOT / d / "tests/test_hygiene.py"; orig = mutate(p, old, new)
            try: print(f"    {label}: {run(ROOT/d,HYG)}")
            finally: p.write_text(orig)
        sys.stdout.flush()
