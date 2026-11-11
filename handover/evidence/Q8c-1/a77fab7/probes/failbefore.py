import ast, os, re, subprocess, sys, xml.etree.ElementTree as ET
B = "/home/user/build"; R = B + "/evidence-raw/Q8c1-a77fab7"
PY = B + "/venv-evq8c1/bin/python"
FILES = ["tests/test_policy_guard.py", "tests/test_policy_docs.py", "tests/test_policy_engine.py"]
def names(src):
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
def git(*a): return subprocess.run(["git", "-C", "/home/user/hadavin-sdk", *a], capture_output=True, text=True).stdout
new = set(); old_all = set()
for f in FILES:
    head = names(git("show", f"a77fab72:{f}"))
    prev = names(git("show", f"7af13809:{f}")) if git("show", f"7af13809:{f}") else set()
    new |= {f"{f}::{n}" for n in head - prev}
print("test functions new in head vs 7af13809:", len(new))
env = dict(os.environ)
for k in ["AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","AWS_CA_BUNDLE","ANTHROPIC_BASE_URL","GH_TOKEN","GITHUB_TOKEN","CLOUDSDK_AUTH_ACCESS_TOKEN","VAULT_TOKEN","VAULT_SECRET_ID"]: env.pop(k, None)
for tag, d in [("prev-head-7af13809 (+head tests)", "prev"), ("origin/main (+head tests +head tools/policy_page.py)", "main"), ("head with ONLY the 3 src files reverted to 7af13809", "srcrev")]:
    wd = f"{B}/EV-Q8c1-fb-{d}"
    env["PYTHONPATH"] = wd + "/src"
    x = f"{R}/fb-{d}.xml"
    r = subprocess.run([PY, "-m", "pytest", *FILES, "-q", "-p", "no:cacheprovider", "--no-header", f"--junitxml={x}", "-rN"], cwd=wd, capture_output=True, text=True, env=env)
    open(f"{R}/fb-{d}.log", "w").write(r.stdout + r.stderr)
    last = [l for l in r.stdout.splitlines() if l.strip()][-1] if r.stdout.strip() else "(no output) " + r.stderr[-200:]
    try:
        tree = ET.parse(x); res = {}
        for tc in tree.iter("testcase"):
            cn = tc.get("classname", "").replace(".", "/"); nm = tc.get("name")
            base = nm.split("[")[0]
            file = next((f for f in FILES if cn.endswith(f[:-3]) ), None)
            st = "failed" if tc.find("failure") is not None or tc.find("error") is not None else ("skipped" if tc.find("skipped") is not None else "passed")
            res[(file, nm)] = st
        tot = {s: sum(1 for v in res.values() if v == s) for s in ("passed", "failed", "skipped")}
        newres = [(k, v) for k, v in res.items() if f"{k[0]}::{k[1].split('[')[0]}" in new]
        nt = {s: sum(1 for k, v in newres if v == s) for s in ("passed", "failed", "skipped")}
        print(f"{tag} | exit {r.returncode} | {last} | all collected: {tot} | among new test functions' cases ({len(newres)}): {nt}")
    except Exception as e:
        print(f"{tag} | exit {r.returncode} | {last} | junit unreadable: {type(e).__name__}")
