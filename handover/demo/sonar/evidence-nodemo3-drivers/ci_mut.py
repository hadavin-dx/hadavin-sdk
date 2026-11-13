import os, shutil, subprocess, sys, re
from pathlib import Path
R = Path("/tmp/work/nm3"); F = R / "F"
RT = R / "rt"
def add(d, name, body):
    p = d / "tests" / name; p.write_text(body)
    subprocess.run(["git", "add", str(p)], cwd=d, check=True)
FILL = lambda d, n: [add(d, f"test_zz{i}.py", "def test_ok():\n    assert True\n") for i in range(1, n + 1)]
def last(d, body, name="test_zz6_marker.py"):
    FILL(d, 5); add(d, name, body)
OK = "def test_ok():\n    assert True\n"
def m_baseline(d): pass
def m_crash_last(d): last(d, "import os\n\ndef test_die():\n    os._exit(0)\n", "test_zz6_marker.py")
def m_crash_first(d): FILL(d, 6); add(d, "test_zz7.py", "import os\n\ndef test_die():\n    os._exit(0)\n")
def m_pytest_exit(d): last(d, "import pytest\n\ndef test_stop():\n    pytest.exit('stop', returncode=0)\n", "test_zz6_marker.py")
def m_failed(d): last(d, "def test_bad():\n    assert False\n")
def m_error(d): last(d, "import pytest\n\n@pytest.fixture\ndef boom():\n    raise RuntimeError('x')\n\ndef test_e(boom):\n    pass\n")
def m_gap(d): add(d, "foo_test.py", OK)
def m_gap2(d): add(d, "testing_extra.py", OK)
def m_conftest_skip_all(d):
    p = d / "tests/conftest.py"; s = p.read_text()
    s = s.replace('r"^\\s*(?:from|import)', 'r".|^\\s*(?:from|import)', 1) if False else s
    s = s.replace("if not DEMO_PRESENT:\n\n    @pytest.hookimpl(tryfirst=True)\n    def pytest_pycollect_makemodule(module_path: Path, parent: Any) -> Any:\n        if _NEEDS_DEMO.search(module_path.read_text(encoding=\"utf-8\")):",
                  "if not DEMO_PRESENT:\n\n    @pytest.hookimpl(tryfirst=True)\n    def pytest_pycollect_makemodule(module_path: Path, parent: Any) -> Any:\n        if module_path.name != 'test_zz6_marker.py':", 1)
    assert "!= 'test_zz6_marker.py'" in s
    p.write_text(s)
def m_shim(mode):
    def f(d):
        last(d, OK)
        os.environ["SHIM_MODE"] = mode
    return f
CASES = [("baseline (expect green)", m_baseline, 0),
 ("os._exit(0) in the LAST chunk (reviewer's green case)", m_crash_last, 1),
 ("os._exit(0) in chunk 0", m_crash_first, 1),
 ("pytest.exit('stop', returncode=0) in the last chunk", m_pytest_exit, 1),
 ("1 failed test in the last chunk", m_failed, 1),
 ("1 error (fixture) in the last chunk", m_error, 1),
 ("tests/foo_test.py exists, no chunk would run it", m_gap, 1),
 ("tests/testing_extra.py exists (test*.py), no chunk would run it", m_gap2, 1),
 ("conftest skips every test file (floor)", m_conftest_skip_all, 1)] + [
 (f"last chunk ends with {txt}", m_shim(mode), 1) for mode, txt in [
  ("noran", "'no tests ran in 0.01s', exit 0"), ("empty", "an empty line, exit 0"), ("error1", "'1 error in 0.20s', exit 0"),
  ("failed1", "'1 failed, 5 passed in 0.20s', exit 0"), ("progress", "a progress line '....s....  [ 40%]', exit 0"),
  ("exitmsg", "'!!!! _pytest.outcomes.Exit: stop !!!!', exit 0"), ("rc1", "its real summary but exit code 1"), ("rc2", "its real summary but exit code 2")]]
only = sys.argv[1:] 
bad = 0
for i, (name, fn, want) in enumerate(CASES):
    if only and str(i) not in only: continue
    d = R / "Fm"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(F, d, symlinks=True)
    os.environ.pop("SHIM_MODE", None)
    fn(d)
    py = str(R / "shim/python")
    log = R / f"ci-mut-{i}.log"
    r = subprocess.run([sys.executable, str(R / "drv/run_step.py"), str(d / ".github/workflows/nodemo.yml"), "Tests without", str(d), str(RT), py],
                       capture_output=True, text=True)
    log.write_text(r.stdout + r.stderr)
    tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    reason = next((l for l in reversed(tail) if not l.startswith("exit")), "")
    ok = (r.returncode == 0) == (want == 0); bad += not ok
    print(f"{'ok   ' if ok else 'WRONG'} job exit {r.returncode} (want {want}) [{i}] {name}\n      last message: {reason}", flush=True)
print("WRONG VERDICTS:", bad)
