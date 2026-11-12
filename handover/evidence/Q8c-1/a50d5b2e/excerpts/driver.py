import subprocess, sys, re, os, json
B = "/home/user/build/EV-Q8c1b14-a50d5b2e"; S = B + "/scratch"; P0 = open(B + "/plants/P0.txt").read().strip()
PY = B + "/venv/bin/python"
Z = "tests/zzev/"
def git(*a): return subprocess.run(["git", "-c", "user.email=ev@example.invalid", "-c", "user.name=ev", *a], cwd=S, capture_output=True, text=True)
# (id, file, old, new, expected-listed names (test names), description)
# old=None: append `new` to the file (create if missing)
A = Z + "test_assign.py"; D = Z + "test_deep.py"; T = Z + "test_setup.py"; U = Z + "test_ut.py"; F = Z + "test_fx.py"
P = []
def p(i, f, old, new, exp, desc): P.append((i, f, old, new, exp, desc))
# --- assignments
p("as1", A, "BASE = 1\n", "BASE = 2\n", ["test_as_base"], "plain constant behind `SIZE = BASE + 1`")
p("as2", A, "LIM: int = 5", "LIM: int = 6", ["test_as_lim"], "annotated assignment")
p("as3", A, "ITEMS += [2]", "ITEMS += [3]", ["test_as_items"], "augmented assignment")
p("as4", A, "X, Y = 1, 2", "X, Y = 1, 3", ["test_as_tuple"], "tuple target")
p("as5", Z+"h_c.py", "def leaf_build(): return 1", "def leaf_build(): return 2", ["test_as_call"], "value behind a call `V = leaf_build()`, body in another module")
p("as6", A, 'CFG["k"] = 1', 'CFG["k"] = 2', ["test_as_subscript"], "subscript assignment at module level")
p("as7", A, "P = Q = 1", "P = Q = 2", ["test_as_chain"], "chained assignment")
p("as8", A, "        Z = 1\n", "        Z = 3\n", ["test_as_if"], "assignment inside an `if` at module level")
p("as9", A, "range(2)", "range(3)", ["test_as_for"], "assignment inside a `for` at module level")
p("as10", A, "(WALRUS := 1)", "(WALRUS := 2)", ["test_as_walrus"], "walrus assignment at module level")
p("as11", A, "OBJ.attr = 1", "OBJ.attr = 2", ["test_as_attr"], "attribute assignment on a module-level object")
p("as12", A, "LIM2 = 7", "LIM2 = 8", ["test_as_viahelper"], "constant read through a non-test helper function")
# --- helper chains
p("hh1", Z+"h_c.py", "def leaf1(): return 1", "def leaf1(): return 2", ["test_deep_chain"], "helper of helper of helper (f -> g -> leaf1, three modules)")
p("hh2", Z+"h_b.py", "def g(): return leaf1()", "def g(): return leaf1() + 0", ["test_deep_chain"], "middle helper g changed")
p("hh3", Z+"h_c.py", "def leaf2(): return 1", "def leaf2(): return 2", ["test_deep_attr"], "`from tests.zzev import h_c` then `h_c.leaf2()`")
p("hh4", Z+"h_c.py", "def leaf3(): return 1", "def leaf3(): return 2", ["test_deep_alias"], "`import tests.zzev.h_c as hc` then `hc.leaf3()`")
p("hh5", Z+"h_c.py", "def leaf4(): return 1", "def leaf4(): return 2", ["test_deep_rel"], "relative import `from .h_c import leaf4`")
p("hh6", Z+"h_c.py", "def leaf5(): return 1", "def leaf5(): return 2", ["test_deep_inner"], "import inside the test function")
p("hh7", Z+"h_c.py", "def leaf6(): return 1", "def leaf6(): return 2", [], "control: leaf6 used by no test (nothing should need a row)")
# --- setup / teardown
allT = ["test_s_a", "test_s_b", "TestSetupCls::test_cls_a", "TestSetupCls::test_cls_b", "TestOther::test_other_a"]
clsT = ["TestSetupCls::test_cls_a", "TestSetupCls::test_cls_b"]
p("su1", T, 'def setup_module(module): CALLS.append("sm")', 'def setup_module(module): CALLS.append("sm2")', allT, "setup_module body")
p("su2", T, 'def teardown_module(module): CALLS.append("tm")', 'def teardown_module(module): CALLS.append("tm2")', allT, "teardown_module body")
p("su3", T, 'def setup_function(function): CALLS.append("sf")', 'def setup_function(function): CALLS.append("sf2")', allT, "setup_function body")
p("su4", T, 'def teardown_function(function): CALLS.append("tf")', 'def teardown_function(function): CALLS.append("tf2")', allT, "teardown_function body")
p("su5", T, "def setup_method(self, method): pass", "def setup_method(self, method): raise RuntimeError('x')", clsT, "setup_method of a class")
p("su6", T, "def teardown_method(self, method): pass", "def teardown_method(self, method): raise RuntimeError('x')", clsT, "teardown_method of a class")
p("su7", T, "def setup_class(cls): pass", "def setup_class(cls): raise RuntimeError('x')", clsT, "setup_class of a class")
p("su8", T, "def teardown_class(cls): pass", "def teardown_class(cls): raise RuntimeError('x')", clsT, "teardown_class of a class")
p("su9", T, "def helper_m(self): return 1", "def helper_m(self): return 0", ["TestSetupCls::test_cls_a"], "non-test helper method of a class")
# --- unittest
p("ut1", U, "def setUp(self): self.x = 1", "def setUp(self): self.x = 2", ["TestUt::test_ut_a", "TestUt::test_ut_b"], "unittest setUp")
p("ut2", U, "def setUpClass(cls): pass", "def setUpClass(cls): raise RuntimeError('x')", ["TestUt::test_ut_a", "TestUt::test_ut_b"], "unittest setUpClass")
p("ut3", U, "def helper(self): return CONST_UT", "def helper(self): return 0", ["TestUt::test_ut_a"], "unittest class helper method")
p("ut4", U, "CONST_UT = 1", "CONST_UT = 2", ["TestUt::test_ut_a", "PlainUt::test_plain_ut"], "constant used by a TestCase not named Test*")
p("ut5", U, "def helper_b(self): return 1", "def helper_b(self): return 0", ["TestMix::test_mix"], "method of a mixin base in the same file")
p("ut6", Z+"h_c.py", "def inherited(self): return 1", "def inherited(self): return 0", ["TestInh::test_inh"], "inherited method; base class in another module; class named Test* but not a TestCase")
# --- fixtures
p("fx1", F, "def base_fx(): return 1", "def base_fx(): return 2", ["test_fx_chain", "test_fx_usefix", "test_fx_dyn"], "fixture used by a fixture chain, by usefixtures, and by request.getfixturevalue")
p("fx2", F, "def file_auto(): yield 1", "def file_auto(): yield 2", ["test_fx_chain", "test_fx_usefix", "test_fx_dyn", "test_fx_indirect", "test_fx_param", "test_fx_skipif", "test_fx_plain", "TestFxClass::test_fx_in_cls", "TestFxClass::test_fx_in_cls2"], "autouse fixture of the file")
p("fx3", F, "def cls_auto(self): yield 1", "def cls_auto(self): yield 2", ["TestFxClass::test_fx_in_cls", "TestFxClass::test_fx_in_cls2"], "autouse fixture of a class")
p("fx4", F, "def pf_fx(request): return request.param", "def pf_fx(request): return request.param + 0", ["test_fx_indirect"], "fixture used by parametrize(indirect=True)")
p("fx5", F, "SKIPFLAG = False", "SKIPFLAG = True", ["test_fx_skipif"], "constant behind skipif")
p("fx6", F, "[1, 2])\ndef test_fx_param", "[1, 2, 3])\ndef test_fx_param", ["test_fx_param"], "parametrize values")
# --- conftest
cfT = ["test_cf_a", "test_cf_b", "test_sub"]
CF = Z + "cf/conftest.py"
p("cf1", CF, "def auto_fx(): yield 1", "def auto_fx(): yield 2", cfT, "autouse fixture of a conftest (also a test in a sub folder)")
p("cf2", CF, "def named_fx(): return 1", "def named_fx(): return 2", ["test_cf_a"], "named fixture of a conftest")
p("cf3", CF, "def pytest_collection_modifyitems(config, items): pass", "def pytest_collection_modifyitems(config, items): items.clear()", cfT, "collection hook of a conftest")
p("cf4", CF, "def pytest_runtest_setup(item): pass", "def pytest_runtest_setup(item): raise RuntimeError('x')", cfT, "run hook of a conftest")
p("cf5", CF, "def pytest_configure(config): pass", "def pytest_configure(config): raise RuntimeError('x')", cfT, "configure hook of a conftest")
p("cf6", CF, "def pytest_generate_tests(metafunc): pass", "def pytest_generate_tests(metafunc): metafunc.parametrize('zz', [])", cfT, "generate hook of a conftest")
p("cf7", CF, "COLLECT_CONST = 1", "COLLECT_CONST = 2", [], "control: constant of a conftest that nothing names")
p("cf8", Z+"test_gen.py", "metafunc.parametrize(\"gv\", [1, 2])", "metafunc.parametrize(\"gv\", [1])", ["test_gen_a", "test_gen_b"], "pytest_generate_tests in a test file")
p("cf9", Z+"pp/conftest.py", '["tests.zzev.plugmod"]', '["tests.zzev.plugmod", "tests.zzev.dyn_a"]', ["test_pp"], "pytest_plugins list of a conftest gains a module")
p("cf10", Z+"plugmod.py", "def pm_fx(): yield 1", "def pm_fx(): yield 2", ["test_pp"], "autouse fixture inside a module named by pytest_plugins")
p("cf11", Z+"plugmod.py", "def pytest_collection_modifyitems(config, items): pass", "def pytest_collection_modifyitems(config, items): items.clear()", ["test_pp"], "collection hook inside a module named by pytest_plugins")
# --- run-time imports
p("rt1", Z+"dyn_a.py", "def da(): return 1", "def da(): return 0", ["test_dyn_import_module"], "importlib.import_module with a text")
p("rt2", Z+"dyn_b.py", "def db(): return 1", "def db(): return 0", ["test_dyn_dunder"], "__import__ with a text")
p("rt3", Z+"dyn_c.py", "def dc(): return 1", "def dc(): return 0", ["test_dyn_computed"], "import_module with a name worked out at run time (f-string)")
p("rt4", Z+"plugpkg/m1.py", "def pm(): return 1", "def pm(): return 0", ["test_dyn_pkgutil"], "module found by pkgutil.iter_modules")
# --- ways to switch tests off (c)
SK = Z + "test_skip.py"
skT = ["test_sk_a", "test_sk_b"]
p("sk1", SK, "import pytest\n", "import pytest\npytestmark = pytest.mark.skip(reason='x')\n", skT, "module-level pytestmark skip")
p("sk2", SK, "import pytest\n", "import pytest\npytestmark = pytest.mark.xfail(reason='x')\n", skT, "module-level pytestmark xfail")
p("sk3", SK, "import pytest\n", "import pytest\n__test__ = False\n", skT, "__test__ = False")
p("sk4", SK, "import pytest\n", "import pytest\npytest.importorskip('no_such_module_zz')\n", skT, "module-level importorskip of a missing module")
p("sk5", SK, "import pytest\n", "import pytest\nif True:\n    pytestmark = pytest.mark.skip(reason='x')\n", skT, "pytestmark inside an `if`")
p("sk6", SK, "def test_sk_a(): pass", "@pytest.mark.skip(reason='x')\ndef test_sk_a(): pass", ["test_sk_a"], "skip decorator on one test")
p("sk7", Z+"conftest.py", None, "collect_ignore = ['test_skip.py']\n", skT, "NEW tests/zzev/conftest.py with collect_ignore (the file is no longer collected)")
p("sk8", Z+"conftest.py", None, "import pytest\ndef pytest_collection_modifyitems(config, items):\n    for i in items:\n        i.add_marker(pytest.mark.skip(reason='x'))\n", ["(any test under tests/zzev)"], "NEW conftest with a skip-everything collection hook")
p("sk9", Z+"conftest.py", None, "import pytest\ndef pytest_collection_modifyitems(config, items):\n    for i in items:\n        i.add_marker(pytest.mark.xfail(reason='x'))\n", ["(any test under tests/zzev)"], "NEW conftest with an xfail-everything collection hook")
p("sk10", Z+"other/conftest.py", None, "collect_ignore_glob = ['*']\n", ["test_other"], "NEW conftest in the folder of one test: collect_ignore_glob = ['*']")
p("sk11", Z+"test_skip.py", "def test_sk_b(): pass", "def test_sk_b(): pass\ndef helper_sk(): pytest.skip('x')\n", [], "control: a new helper function that nothing calls")
json.dump(P, open(B + "/plants/plants.json", "w"))
out = open(B + "/plants/results.md", "w"); raw = open(B + "/plants/raw.log", "w")
for (i, f, old, new, exp, desc) in P:
    git("reset", "-q", "--hard", P0); git("clean", "-qfd")
    path = os.path.join(S, f)
    if old is None:
        txt = new if not os.path.exists(path) else open(path).read() + new
    else:
        txt = open(path).read()
        if txt.count(old) != 1: print(i, "OLD TEXT COUNT", txt.count(old)); raw.write(f"## {i} PLANT NOT APPLIED (old text count {txt.count(old)})\n"); continue
        txt = txt.replace(old, new)
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(txt)
    git("add", "-A"); c = git("commit", "-qm", "plant " + i)
    r = subprocess.run([PY, "tools/notes_lines_check.py", "--auto", P0], cwd=S, capture_output=True, text=True)
    outp = (r.stdout + r.stderr).strip()
    raw.write(f"## {i}: {desc}\nexit {r.returncode}; lines {len(outp.splitlines())}\n{outp}\n\n"); raw.flush()
    names = sorted(set(re.findall(r"the test (\S+) is new or changed", outp)))
    other = [l for l in outp.splitlines() if "the test " not in l and "UV_NATIVE" not in l]
    miss = [e for e in exp if e not in names] if not any(e.startswith("(") for e in exp) else ["?"]
    extra = [n for n in names if n not in exp]
    out.write(f"| {i} | {desc} | {r.returncode} | {len(names)} | {'; '.join(miss) or 'none'} | {'; '.join(extra) or 'none'} | {(other[0][:150] if other else '')} |\n"); out.flush()
git("reset", "-q", "--hard", P0)
