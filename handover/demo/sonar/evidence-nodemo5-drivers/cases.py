"""cases.py BASE NAME... : copy BASE tree, apply the named case, run Delete+Tests steps like the job (bash -e), print RESULT."""
import os, shutil, subprocess, sys, pathlib
base = sys.argv[1]; names = sys.argv[2:]
ROOT = "/tmp/work/sn-v4-m"
PYBIN = os.environ.get("PYBIN")
HDR = "import os, sys, signal, pytest\n"
C = {}
def case(name, files=None, edit=None, env=None, expect=""):
    C[name] = (files or {}, edit, env or {}, expect)
def conf(text):
    return lambda t: open(t+"/tests/conftest.py","a").write(text)
def pyproj(line):
    return lambda t: subprocess.run(["sed","-i","s/^testpaths = .*/&\\n"+line+"/",t+"/pyproject.toml"],check=True)
case("base", expect="GREEN")
case("sigkill", {"tests/test_aa_kill.py": HDR+"def test_k():\n    os.kill(os.getpid(), signal.SIGKILL)\n"}, expect="RED rc 137")
case("sigsegv", {"tests/test_aa_segv.py": HDR+"def test_k():\n    os.kill(os.getpid(), signal.SIGSEGV)\n"}, expect="RED rc 139")
case("fake-exit-normal", {"tests/test_aa_fake.py": HDR+"def test_k():\n    print('\\n16 passed in 1.0s', flush=True)\n    os._exit(0)\n"}, expect="RED")
case("fake-exit-capsys-disabled", {"tests/test_aa_fake.py": HDR+"def test_k(capsys):\n    with capsys.disabled():\n        print('\\n16 passed in 1.0s', flush=True)\n        os._exit(0)\n"}, expect="RED (the Major 2 case)")
case("collectonly-conftest", edit=conf("\n\ndef pytest_configure(config):\n    config.option.collectonly = True\n"), expect="RED")
case("sys-exit-0-import", {"tests/test_aa_exit.py": "import sys\nsys.exit(0)\n"}, expect="RED")
case("sys-exit-0-in-test", {"tests/test_aa_exit.py": "import sys\ndef test_k():\n    sys.exit(0)\n"}, expect="RED")
case("delete-junit-then-exit", {"tests/test_aa_del.py": HDR+"import glob\ndef test_k():\n    for f in glob.glob(os.environ['RUNNER_TEMP']+'/nodemo/*'):\n        os.remove(f)\n    os._exit(0)\n"}, expect="RED")
case("delete-junit-normal-end", {"tests/test_aa_del.py": HDR+"import glob\ndef test_k():\n    for f in glob.glob(os.environ['RUNNER_TEMP']+'/nodemo/chunk-*.xml'):\n        os.remove(f)\n"}, expect="GREEN (pytest rewrites the file with the true counts at its end)")
case("truncate-junit-then-exit", {"tests/test_aa_del.py": HDR+"import glob\ndef test_k():\n    for f in glob.glob(os.environ['RUNNER_TEMP']+'/nodemo/chunk-*.xml'):\n        open(f,'w').close()\n    os._exit(0)\n"}, expect="RED")
case("truncate-junit-normal-end", {"tests/test_aa_del.py": HDR+"import glob\ndef test_k():\n    for f in glob.glob(os.environ['RUNNER_TEMP']+'/nodemo/chunk-*.xml'):\n        open(f,'w').close()\n"}, expect="GREEN (rewritten with true counts)")
case("delete-exit-codes-file", {"tests/test_aa_del.py": HDR+"def test_k():\n    os.remove(os.environ['RUNNER_TEMP']+'/nodemo/exit-codes.txt')\n"}, expect="RED")
case("deselect-hook-reported", edit=conf("\n\ndef pytest_collection_modifyitems(config, items):\n    gone = items[:5]\n    items[:] = items[5:]\n    config.hook.pytest_deselected(items=gone)\n"), expect="RED")
case("delete-exit-codes-file-late", {"tests/test_zz_del.py": HDR+"def test_k():\n    os.remove(os.environ['RUNNER_TEMP']+'/nodemo/exit-codes.txt')\n"}, expect="RED (lines of earlier chunks lost)")
case("drop-crc-2pct", edit=conf("\n\nimport zlib\ndef pytest_collection_modifyitems(config, items):\n    items[:] = [i for i in items if zlib.crc32(i.nodeid.encode()) % 50]\n"), expect="GREEN (about 2 percent silently dropped, same on both sides: inside the margin)")
case("drop-crc-20pct", edit=conf("\n\nimport zlib\ndef pytest_collection_modifyitems(config, items):\n    items[:] = [i for i in items if zlib.crc32(i.nodeid.encode()) % 5]\n"), expect="RED (floor)")
case("drop-3-silently", edit=conf("\n\ndef pytest_collection_modifyitems(config, items):\n    items[:] = items[3:]\n"), expect="GREEN (inside the margin; documented)")
case("drop-100-silently", edit=conf("\n\ndef pytest_collection_modifyitems(config, items):\n    items[:] = items[100:]\n"), expect="RED (floor)")
case("addopts-q", edit=pyproj('addopts = "-q"'), expect="RED")
case("print-999-passed", {"tests/test_aa_print.py": "def test_k(capsys):\n    with capsys.disabled():\n        print('\\n999 passed in 1.0s', flush=True)\n"}, expect="GREEN")
case("xfail-xpass", {"tests/test_aa_xf.py": "import pytest\n@pytest.mark.xfail\ndef test_x1():\n    assert 0\n@pytest.mark.xfail\ndef test_x2():\n    pass\n@pytest.mark.xfail(strict=True, reason='r')\ndef test_x3():\n    raise RuntimeError\n"}, expect="GREEN")
case("xpass-strict", {"tests/test_aa_xf.py": "import pytest\n@pytest.mark.xfail(strict=True)\ndef test_x2():\n    pass\n"}, expect="RED (legit failure)")
case("atexit-print", {"tests/test_aa_atexit.py": "import atexit\natexit.register(lambda: print('bye'))\ndef test_k():\n    pass\n"}, expect="GREEN")
case("odd-names", {"tests/test_é.py": "def test_k():\n    pass\n", "tests/test_cr\r.py": "def test_k():\n    pass\n", "tests/test_﻿bom.py": "def test_k():\n    pass\n"}, expect="GREEN, 3 more tests")
case("nested-dir-and-nontests", {"tests/sub/test_deep.py": "def test_k():\n    pass\n", "tests/testdata.py": "x = 1\n", "tests/test.py": "def test_k():\n    assert 0\n", "tests/a_test.py": "def test_k():\n    pass\n"}, expect="GREEN (deep + a_test run; testdata/test.py not collected by pytest)")
case("skip-2-other", {"tests/test_aa_sk.py": "import pytest\ndef test_a():\n    pytest.skip('nope')\ndef test_b():\n    pytest.skip('nope2')\n"}, expect="GREEN (inside limit 2)")
case("skip-3-other", {"tests/test_aa_sk.py": "import pytest\ndef test_a():\n    pytest.skip('nope')\ndef test_b():\n    pytest.skip('nope2')\ndef test_c():\n    pytest.skip('nope3')\n"}, expect="RED message lists them and says what to edit")
case("failing-test", {"tests/test_aa_fail.py": "def test_k():\n    assert 0\n"}, expect="RED")
case("python_files-extra", {"tests/check_x.py": "def test_k():\n    pass\n"}, edit=pyproj('python_files = ["test_*.py", "*_test.py", "check_*.py"]'), expect="RED (tests/ collects more than the files run)")
case("floor-95pct", env={"OVR_MIN_PASSED_PERCENT":"95"}, expect="RED message names the env numbers")
case("env-fixture-added", {"tests/test_aa_env.py": "def test_k(env):\n    pass\n"}, expect="GREEN (one placeholder skip)")
def run(name):
    files, edit, env, expect = C[name]
    t = f"{ROOT}/c-{pathlib.Path(base).name}-{name}"
    shutil.rmtree(t, ignore_errors=True); shutil.copytree(f"{ROOT}/{base}", t, symlinks=True)
    for p, c in files.items():
        pp = pathlib.Path(t, p); pp.parent.mkdir(parents=True, exist_ok=True); pp.write_bytes(c.encode())
    if edit: edit(t)
    subprocess.run(["git","add","-A"],cwd=t,check=True)
    e = dict(os.environ); e.update(env)
    r = subprocess.run([sys.executable,"/tmp/work/sn-v4-drv/job.py",t,"Delete","Tests"],capture_output=True,text=True,env=e)
    out = (r.stdout+r.stderr).strip().splitlines()
    print(f"### {base} {name}: expect {expect}\n   job rc={r.returncode}\n   " + "\n   ".join(l[:400] for l in out if l.startswith("RESULT") or l.startswith("TOTAL")), flush=True)
    shutil.rmtree(t, ignore_errors=True)
for n in (names or C): run(n)
