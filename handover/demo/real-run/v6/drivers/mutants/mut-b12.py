import subprocess, sys, shutil, json
from pathlib import Path
root = Path(sys.argv[1]); muts = json.loads(Path(sys.argv[2]).read_text()); tests = sys.argv[3:]
py = "/tmp/work/fresh-venv5/bin/python"
for name, f, old, new in muts:
    p = root / f; orig = p.read_text(encoding="utf-8")
    if orig.count(old) < 1:
        print(f"{name}\tNOT-APPLIED (pattern missing)"); continue
    p.write_text(orig.replace(old, new, 1), encoding="utf-8")
    try:
        r = subprocess.run([__import__("os").environ.get("MUT_RUN","/tmp/work/b12-harness/run.sh"), "/tmp/work/b12-harness/logm.txt", py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *tests],
                           capture_output=True, text=True, timeout=900, env={"PATH": "/usr/bin:/bin"})
        last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
        print(f"{name}\t{'SURVIVED' if r.returncode == 0 else 'killed'}\t{last}")
    finally:
        p.write_text(orig, encoding="utf-8")
