"""Emulated mutant run (no pytest): apply each G8 mutant's old->new to TREE's redact.py in a temp copy, run rows.py, call it killed when the
row named by `expect` differs from the unmutated tree's output. SWEEP mutants (runmap/_JOINS, sweep tests) are not emulated."""
import sys, os, shutil, subprocess, json, tempfile, importlib
tree = os.path.abspath(sys.argv[1]); sys.path.insert(0, os.path.join(tree)); sys.path.insert(0, tree + "/src")
os.chdir(tree)
import tests.g8_mutants as GM
rows = os.path.abspath("../rows.py")
def run(d, out):
    env = dict(os.environ, PYTHONPATH=f"{d}/src:{d}")
    subprocess.run([sys.executable, rows, out], cwd=d, env=env, check=True, capture_output=True)
    return json.load(open(out))["out"]
tmp = tempfile.mkdtemp(dir="/tmp/claude-0/-home-user/1ecfcb92-30a8-505b-a8c3-27491ed2aff6/scratchpad/g11_work")
base = os.path.join(tmp, "t"); shutil.copytree(tree, base, ignore=shutil.ignore_patterns(".git", "__pycache__", "handover", "docs", "demos"))
ref = run(base, tmp + "/ref.json")
good = bad = skip = 0; notes = []
for mu in GM.M:
    exp = mu.expect
    if exp.startswith("SWEEP"): skip += 1; continue
    f = os.path.join(base, mu.file); src = open(f).read()
    if mu.old not in src: bad += 1; notes.append((mu.name, "old not found")); continue
    open(f, "w").write(src.replace(mu.old, mu.new))
    try:
        out = run(base, tmp + "/m.json")
    except subprocess.CalledProcessError: out = None
    open(f, "w").write(src)
    tag = exp.split()[1]; rid = f"row{tag}" if tag.isdigit() else tag
    if out is None or out.get(rid) != ref.get(rid): good += 1
    else: bad += 1; notes.append((mu.name, f"{rid} unchanged"))
print(f"emulated: {good} killed at the named row, {bad} not, {skip} sweep mutants skipped; {notes}")
shutil.rmtree(tmp)
