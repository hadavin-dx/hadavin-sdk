import os, sys, textwrap
root = sys.argv[1]
def w(path, text):
    p = os.path.join(root, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(textwrap.dedent(text).lstrip("\n"))
Z = "tests/zzev/"
w(Z+"__init__.py", "")
w(Z+"h_c.py", '''
    def leaf1(): return 1
    def leaf2(): return 1
    def leaf3(): return 1
    def leaf4(): return 1
    def leaf5(): return 1
    def leaf6(): return 1
    def leaf_build(): return 1
    class BaseCase:
        def inherited(self): return 1
''')
w(Z+"h_b.py", '''
    from tests.zzev.h_c import leaf1
    def g(): return leaf1()
''')
w(Z+"h_a.py", '''
    from tests.zzev.h_b import g
    def f(): return g()
''')
w(Z+"test_deep.py", '''
    from tests.zzev.h_a import f
    from tests.zzev import h_c
    import tests.zzev.h_c as hc
    from .h_c import leaf4
    def test_deep_chain(): assert f()
    def test_deep_attr(): assert h_c.leaf2()
    def test_deep_alias(): assert hc.leaf3()
    def test_deep_rel(): assert leaf4()
    def test_deep_inner():
        from tests.zzev.h_c import leaf5
        assert leaf5()
    def test_deep_unrelated(): assert True
''')
w(Z+"test_assign.py", '''
    import sys
    from tests.zzev.h_c import leaf_build
    BASE = 1
    SIZE = BASE + 1
    LIM: int = 5
    ITEMS = [1]
    ITEMS += [2]
    X, Y = 1, 2
    V = leaf_build()
    CFG = {}
    CFG["k"] = 1
    P = Q = 1
    if sys.platform:
        Z = 1
    else:
        Z = 2
    for _i in range(2):
        LOOP = _i
    W = (WALRUS := 1)
    class _O: pass
    OBJ = _O()
    OBJ.attr = 1
    LIM2 = 7
    def _helper(): return LIM2
    def test_as_base(): assert SIZE
    def test_as_lim(): assert LIM
    def test_as_items(): assert ITEMS
    def test_as_tuple(): assert Y
    def test_as_call(): assert V
    def test_as_subscript(): assert CFG
    def test_as_chain(): assert Q
    def test_as_if(): assert Z
    def test_as_for(): assert LOOP
    def test_as_walrus(): assert WALRUS
    def test_as_attr(): assert OBJ.attr
    def test_as_viahelper(): assert _helper()
    def test_as_unrelated(): assert True
''')
w(Z+"test_setup.py", '''
    CALLS = []
    def setup_module(module): CALLS.append("sm")
    def teardown_module(module): CALLS.append("tm")
    def setup_function(function): CALLS.append("sf")
    def teardown_function(function): CALLS.append("tf")
    def test_s_a(): pass
    def test_s_b(): pass
    class TestSetupCls:
        def setup_method(self, method): pass
        def teardown_method(self, method): pass
        @classmethod
        def setup_class(cls): pass
        @classmethod
        def teardown_class(cls): pass
        def helper_m(self): return 1
        def test_cls_a(self): assert self.helper_m()
        def test_cls_b(self): pass
    class TestOther:
        def test_other_a(self): pass
''')
w(Z+"test_ut.py", '''
    import unittest
    from tests.zzev.h_c import BaseCase
    CONST_UT = 1
    class TestUt(unittest.TestCase):
        def setUp(self): self.x = 1
        @classmethod
        def setUpClass(cls): pass
        def helper(self): return CONST_UT
        def test_ut_a(self): self.assertTrue(self.helper())
        def test_ut_b(self): pass
    class PlainUt(unittest.TestCase):
        def test_plain_ut(self): self.assertEqual(CONST_UT, 1)
    class MixinBase:
        def helper_b(self): return 1
    class TestMix(MixinBase, unittest.TestCase):
        def test_mix(self): self.assertTrue(self.helper_b())
    class TestInh(BaseCase):
        def test_inh(self): assert self.inherited()
''')
w(Z+"test_fx.py", '''
    import pytest
    SKIPFLAG = False
    @pytest.fixture
    def base_fx(): return 1
    @pytest.fixture
    def mid_fx(base_fx): return base_fx
    @pytest.fixture
    def pf_fx(request): return request.param
    @pytest.fixture(autouse=True)
    def file_auto(): yield 1
    def test_fx_chain(mid_fx): assert mid_fx
    @pytest.mark.usefixtures("base_fx")
    def test_fx_usefix(): pass
    def test_fx_dyn(request): request.getfixturevalue("base_fx")
    @pytest.mark.parametrize("pf_fx", [1, 2], indirect=True)
    def test_fx_indirect(pf_fx): assert pf_fx
    @pytest.mark.parametrize("v", [1, 2])
    def test_fx_param(v): assert v
    @pytest.mark.skipif(SKIPFLAG, reason="r")
    def test_fx_skipif(): pass
    def test_fx_plain(): pass
    class TestFxClass:
        @pytest.fixture(autouse=True)
        def cls_auto(self): yield 1
        def test_fx_in_cls(self): pass
        def test_fx_in_cls2(self): pass
''')
w(Z+"cf/__init__.py", "")
w(Z+"cf/conftest.py", '''
    import pytest
    COLLECT_CONST = 1
    @pytest.fixture(autouse=True)
    def auto_fx(): yield 1
    @pytest.fixture
    def named_fx(): return 1
    def pytest_collection_modifyitems(config, items): pass
    def pytest_runtest_setup(item): pass
    def pytest_configure(config): pass
    def pytest_generate_tests(metafunc): pass
''')
w(Z+"cf/test_cf.py", '''
    def test_cf_a(named_fx): assert named_fx
    def test_cf_b(): pass
''')
w(Z+"cf/sub/__init__.py", "")
w(Z+"cf/sub/test_sub.py", '''
    def test_sub(): pass
''')
w(Z+"other/__init__.py", "")
w(Z+"other/test_other.py", '''
    def test_other(): pass
''')
w(Z+"test_gen.py", '''
    def pytest_generate_tests(metafunc):
        if "gv" in metafunc.fixturenames:
            metafunc.parametrize("gv", [1, 2])
    def test_gen_a(gv): assert gv
    def test_gen_b(): pass
''')
w(Z+"test_skip.py", '''
    import pytest
    def test_sk_a(): pass
    def test_sk_b(): pass
''')
w(Z+"dyn_a.py", "def da(): return 1\n")
w(Z+"dyn_b.py", "def db(): return 1\n")
w(Z+"dyn_c.py", "def dc(): return 1\n")
w(Z+"plugpkg/__init__.py", "")
w(Z+"plugpkg/m1.py", "def pm(): return 1\n")
w(Z+"test_dyn.py", '''
    import importlib, pkgutil
    from tests.zzev import plugpkg
    def test_dyn_import_module(): assert importlib.import_module("tests.zzev.dyn_a").da()
    def test_dyn_dunder(): assert __import__("tests.zzev.dyn_b", fromlist=["x"]).db()
    def test_dyn_computed():
        n = "c"
        assert importlib.import_module(f"tests.zzev.dyn_{n}").dc()
    def test_dyn_pkgutil():
        for m in pkgutil.iter_modules(plugpkg.__path__):
            importlib.import_module("tests.zzev.plugpkg." + m.name)
    def test_dyn_unrelated(): pass
''')
w(Z+"pp/__init__.py", "")
w(Z+"pp/conftest.py", '''
    pytest_plugins = ["tests.zzev.plugmod"]
''')
w(Z+"plugmod.py", '''
    import pytest
    @pytest.fixture(autouse=True)
    def pm_fx(): yield 1
    def pytest_collection_modifyitems(config, items): pass
''')
w(Z+"pp/test_pp.py", '''
    def test_pp(): pass
''')
