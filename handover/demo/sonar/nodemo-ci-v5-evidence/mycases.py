import sys, os, shutil, subprocess
sys.path.insert(0, "/tmp/work/rv37-main/drv")
import cases as C
WF = os.environ.get("WF", "/tmp/work/nd5/v5/nodemo.yml")
N = "/tmp/work/nd5"
EXTRA = {}
def sh(cmd, cwd): subprocess.run(cmd, shell=True, cwd=cwd, check=True)
def modskip(r):
    C.w(r, "tests/test_zz_ios.py", "import pytest\npytest.importorskip('not_a_module_xyz')\ndef test_a(): pass\n")
def modskip2(r):
    C.w(r, "tests/test_zz_ms.py", "import pytest\npytest.skip('no thanks', allow_module_level=True)\ndef test_a(): pass\n")
def skip_n(k):
    def f(r):
        body = "import pytest\n" + "".join(f"@pytest.mark.skip('flaky on ci')\ndef test_{i}(): pass\n" for i in range(k))
        C.w(r, "tests/test_zz_sk.py", body)
    return f
def env_skip_reasons(r):
    C.w(r, "tests/test_zz_env.py", "import pytest\n@pytest.mark.skip('needs root to start as another user')\ndef test_a(): pass\n@pytest.mark.skip('ntpath.isreserved needs Python 3.13')\ndef test_b(): pass\n")
def env_skip_many(r):
    C.w(r, "tests/test_zz_env.py", "import pytest\n" + "".join(f"@pytest.mark.skip('needs root to start as another user')\ndef test_{i}(): pass\n" for i in range(7)))
def collect_only_tests(r):  # a file counted only when given tests/: conftest changes collection by invocation
    C.w(r, "tests/conftest_extra.py", "")
    with open(r + "/tests/conftest.py", "a") as fh:
        fh.write("\n\ndef pytest_collection_modifyitems(config, items):\n    if len(config.args) == 1 and config.args[0] == 'tests':\n        pass\n")
def more_when_dir(r):
    # extra test found only when pytest is given the directory (python_files via conftest hook is not possible; use a name pytest finds but git list lacks): an untracked-then-ignored file
    C.w(r, "tests/test_zz_ign.py", "def test_ign(): pass\n")
    sh("printf 'tests/test_zz_ign.py\\n' >> .git/info/exclude", r)
import re
def rm_n(k):
    def f(r):
        tot = 0; cands = []
        for fn in sorted(os.listdir(r + "/tests")):
            if fn.startswith("test_") and fn.endswith(".py"):
                tx = open(r + "/tests/" + fn, encoding="utf-8").read()
                if re.search(r"^\s*(?:from|import)\s+(?:demo_only|support|edge_case_helpers|test_\w+)\b|^def test_\w+\([^)]*\benv\b", tx, re.M): continue
                cands.append((len(re.findall(r"^def test_", tx, re.M)), fn))
        cands.sort()
        for n, fn in cands:
            if tot >= k: break
            sh(f"git rm -qf tests/{fn}", r); tot += n
        print("removed approx", tot)
    return f
CASES = dict(C.CASES)
for _k in (30, 50, 100, 300): CASES[f"remove-files-{_k}"] = rm_n(_k)
CASES["remove-biggest-test-file"] = lambda r: (lambda b: sh(f"git rm -qf tests/{b[1]}", r))(C.biggest(r))
CASES.update({"module-importorskip": modskip, "module-skip-allow": modskip2, "skip-3": skip_n(3), "skip-4": skip_n(4),
              "env-skip-reasons": env_skip_reasons, "env-skip-7": env_skip_many, "untracked-ignored-test-file": more_when_dir})
def main(stack, names, envx=None):
    for n in names:
        r = f"{N}/cs/{stack}-{n}"
        shutil.rmtree(r, ignore_errors=True); os.makedirs(f"{N}/cs", exist_ok=True)
        shutil.copytree(f"{N}/{stack}S", r, symlinks=True)
        shutil.copy(WF, r + "/.github/workflows/nodemo.yml")
        CASES[n](r)
        sh("git add -A", r)
        env = dict(os.environ); env.update(envx or {})
        if env.get("GITHUB_BASE_REF"):
            sh("git update-ref refs/remotes/origin/" + env["GITHUB_BASE_REF"] + " HEAD", r)
        sh("git -c user.name=t -c user.email=t@example.invalid commit -q --no-verify -m case", r)
        p = subprocess.run(["python3.12", "/tmp/work/nd5/drv/runjob2.py", r, C.VENV], capture_output=True, text=True, env=env, timeout=1500)
        out = p.stdout + p.stderr
        open(f"{N}/cs/{stack}-{n}.log", "w").write(out)
        lines = [l for l in out.splitlines() if l.strip()]
        tail = [l for l in lines if l.startswith(("TOTAL", "RED", "RESULT", "collecting", "pytest finds", "Test files", "Same test", "no '"))]
        print(f"### [{stack}] {n}: " + " || ".join(t[:700] for t in tail[-6:]), flush=True)
        shutil.rmtree(r, ignore_errors=True); shutil.rmtree(f"{N}/cs/rt-{stack}-{n}", ignore_errors=True)
if __name__ == "__main__":
    mode = sys.argv[1]; stack = sys.argv[2]
    main(stack, sys.argv[3:], dict({"NORUFF": "1"}, **({"GITHUB_BASE_REF": "base"} if mode == "pr" else {"TEST_BEFORE": "3598120506f7542cd40957fdf33d7f389275d21b"})))
