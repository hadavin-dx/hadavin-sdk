"""plant.py TREE MUTANTS... : plant K6/K10 (once each), run pytest args after --, always restore."""
import hashlib, pathlib, subprocess, sys, os
tree = pathlib.Path(sys.argv[1]); i = sys.argv.index("--"); names = sys.argv[2:i]; cmd = sys.argv[i+1:]
M = {"K6": ("tests/keep_scan.py", 'if node.func.attr == "format":', "if False:"),
     "K10": ("tests/keep_scan.py", 'texts = [_PLACEHOLDER.sub("", t) for t in _texts(node)]', "texts = _texts(node)")}
orig = {}; 
try:
    for n in names:
        f, old, new = M[n]; p = tree / f
        orig.setdefault(f, p.read_bytes()); s = p.read_text()
        assert s.count(old) == 1, n
        p.write_text(s.replace(old, new, 1))
    env = dict(os.environ, TMPDIR=str(tree / ".tmp-run"), PYTHONPATH=str(tree / "src"))
    r = subprocess.run(cmd, cwd=tree, env=env)
finally:
    for f, b in orig.items():
        (tree / f).write_bytes(b)
        print("restored", f, hashlib.sha256(b).hexdigest()[:12])
sys.exit(r.returncode)
