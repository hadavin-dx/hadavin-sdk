| as1 | plain constant behind `SIZE = BASE + 1` | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as2 | annotated assignment | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as3 | augmented assignment | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as4 | tuple target | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as5 | value behind a call `V = leaf_build()`, body in another module | 1 | 3 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as6 | subscript assignment at module level | 1 | 13 | none | test_as_attr; test_as_base; test_as_call; test_as_chain; test_as_for; test_as_if; test_as_items; test_as_lim; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as7 | chained assignment | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as9 | assignment inside a `for` at module level | 1 | 13 | none | test_as_attr; test_as_base; test_as_call; test_as_chain; test_as_if; test_as_items; test_as_lim; test_as_subscript; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as10 | walrus assignment at module level | 0 | 0 | test_as_walrus | none |  |
| as11 | attribute assignment on a module-level object | 1 | 13 | none | test_as_base; test_as_call; test_as_chain; test_as_for; test_as_if; test_as_items; test_as_lim; test_as_subscript; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| as12 | constant read through a non-test helper function | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh1 | helper of helper of helper (f -> g -> leaf1, three modules) | 1 | 3 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh2 | middle helper g changed | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh3 | `from tests.zzev import h_c` then `h_c.leaf2()` | 1 | 2 | none | test_deep_alias | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh4 | `import tests.zzev.h_c as hc` then `hc.leaf3()` | 1 | 2 | none | test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh5 | relative import `from .h_c import leaf4` | 1 | 3 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh6 | import inside the test function | 1 | 3 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| hh7 | control: leaf6 used by no test (nothing should need a row) | 1 | 2 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su1 | setup_module body | 1 | 5 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su2 | teardown_module body | 1 | 5 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su3 | setup_function body | 1 | 5 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su4 | teardown_function body | 1 | 5 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su5 | setup_method of a class | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su6 | teardown_method of a class | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su7 | setup_class of a class | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su8 | teardown_class of a class | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| su9 | non-test helper method of a class | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| ut1 | unittest setUp | 0 | 0 | TestUt::test_ut_a; TestUt::test_ut_b | none |  |
| ut2 | unittest setUpClass | 0 | 0 | TestUt::test_ut_a; TestUt::test_ut_b | none |  |
| ut3 | unittest class helper method | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| ut4 | constant used by a TestCase not named Test* | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| ut5 | method of a mixin base in the same file | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| ut6 | inherited method; base class in another module; class named Test* but not a TestCase | 1 | 3 | none | test_deep_alias; test_deep_attr | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx1 | fixture used by a fixture chain, by usefixtures, and by request.getfixturevalue | 1 | 1 | test_fx_usefix; test_fx_dyn | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx2 | autouse fixture of the file | 1 | 9 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx3 | autouse fixture of a class | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx4 | fixture used by parametrize(indirect=True) | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx5 | constant behind skipif | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| fx6 | parametrize values | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf1 | autouse fixture of a conftest (also a test in a sub folder) | 1 | 10 | none | COLLECT_CONST; auto_fx; named_fx; pytest_collection_modifyitems; pytest_configure; pytest_generate_tests; pytest_runtest_setup | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf2 | named fixture of a conftest | 1 | 2 | none | named_fx | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf3 | collection hook of a conftest | 1 | 4 | none | pytest_collection_modifyitems | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf4 | run hook of a conftest | 1 | 4 | none | pytest_runtest_setup | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf5 | configure hook of a conftest | 1 | 4 | none | pytest_configure | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf6 | generate hook of a conftest | 1 | 4 | none | pytest_generate_tests | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf7 | control: constant of a conftest that nothing names | 1 | 1 | none | COLLECT_CONST | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf8 | pytest_generate_tests in a test file | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf9 | pytest_plugins list of a conftest gains a module | 1 | 2 | none | pytest_plugins | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| cf10 | autouse fixture inside a module named by pytest_plugins | 0 | 0 | test_pp | none |  |
| cf11 | collection hook inside a module named by pytest_plugins | 0 | 0 | test_pp | none |  |
| rt1 | importlib.import_module with a text | 1 | 5 | none | test_dyn_computed; test_dyn_dunder; test_dyn_pkgutil; test_dyn_unrelated | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| rt2 | __import__ with a text | 1 | 5 | none | test_dyn_computed; test_dyn_import_module; test_dyn_pkgutil; test_dyn_unrelated | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| rt3 | import_module with a name worked out at run time (f-string) | 0 | 0 | test_dyn_computed | none |  |
| rt4 | module found by pkgutil.iter_modules | 1 | 5 | none | test_dyn_computed; test_dyn_dunder; test_dyn_import_module; test_dyn_unrelated | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk1 | module-level pytestmark skip | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk2 | module-level pytestmark xfail | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk3 | __test__ = False | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk4 | module-level importorskip of a missing module | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk5 | pytestmark inside an `if` | 1 | 2 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk6 | skip decorator on one test | 1 | 1 | none | none | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk7 | NEW tests/zzev/conftest.py with collect_ignore (the file is no longer collected) | 1 | 53 | none | PlainUt::test_plain_ut; TestFxClass::test_fx_in_cls; TestFxClass::test_fx_in_cls2; TestInh::test_inh; TestMix::test_mix; TestOther::test_other_a; TestSetupCls::test_cls_a; TestSetupCls::test_cls_b; TestUt::test_ut_a; TestUt::test_ut_b; collect_ignore; test_as_attr; test_as_base; test_as_call; test_as_chain; test_as_for; test_as_if; test_as_items; test_as_lim; test_as_subscript; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus; test_cf_a; test_cf_b; test_deep_alias; test_deep_attr; test_deep_chain; test_deep_inner; test_deep_rel; test_deep_unrelated; test_dyn_computed; test_dyn_dunder; test_dyn_import_module; test_dyn_pkgutil; test_dyn_unrelated; test_fx_chain; test_fx_dyn; test_fx_indirect; test_fx_param; test_fx_plain; test_fx_skipif; test_fx_usefix; test_gen_a; test_gen_b; test_other; test_pp; test_s_a; test_s_b; test_sub | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk8 | NEW conftest with a skip-everything collection hook | 1 | 53 | ? | PlainUt::test_plain_ut; TestFxClass::test_fx_in_cls; TestFxClass::test_fx_in_cls2; TestInh::test_inh; TestMix::test_mix; TestOther::test_other_a; TestSetupCls::test_cls_a; TestSetupCls::test_cls_b; TestUt::test_ut_a; TestUt::test_ut_b; pytest_collection_modifyitems; test_as_attr; test_as_base; test_as_call; test_as_chain; test_as_for; test_as_if; test_as_items; test_as_lim; test_as_subscript; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus; test_cf_a; test_cf_b; test_deep_alias; test_deep_attr; test_deep_chain; test_deep_inner; test_deep_rel; test_deep_unrelated; test_dyn_computed; test_dyn_dunder; test_dyn_import_module; test_dyn_pkgutil; test_dyn_unrelated; test_fx_chain; test_fx_dyn; test_fx_indirect; test_fx_param; test_fx_plain; test_fx_skipif; test_fx_usefix; test_gen_a; test_gen_b; test_other; test_pp; test_s_a; test_s_b; test_sk_a; test_sk_b; test_sub | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk9 | NEW conftest with an xfail-everything collection hook | 1 | 53 | ? | PlainUt::test_plain_ut; TestFxClass::test_fx_in_cls; TestFxClass::test_fx_in_cls2; TestInh::test_inh; TestMix::test_mix; TestOther::test_other_a; TestSetupCls::test_cls_a; TestSetupCls::test_cls_b; TestUt::test_ut_a; TestUt::test_ut_b; pytest_collection_modifyitems; test_as_attr; test_as_base; test_as_call; test_as_chain; test_as_for; test_as_if; test_as_items; test_as_lim; test_as_subscript; test_as_tuple; test_as_unrelated; test_as_viahelper; test_as_walrus; test_cf_a; test_cf_b; test_deep_alias; test_deep_attr; test_deep_chain; test_deep_inner; test_deep_rel; test_deep_unrelated; test_dyn_computed; test_dyn_dunder; test_dyn_import_module; test_dyn_pkgutil; test_dyn_unrelated; test_fx_chain; test_fx_dyn; test_fx_indirect; test_fx_param; test_fx_plain; test_fx_skipif; test_fx_usefix; test_gen_a; test_gen_b; test_other; test_pp; test_s_a; test_s_b; test_sk_a; test_sk_b; test_sub | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk10 | NEW conftest in the folder of one test: collect_ignore_glob = ['*'] | 1 | 2 | none | collect_ignore_glob | the change has no builder notes file (handover/evidence/**/NOTES.md) |
| sk11 | control: a new helper function that nothing calls | 0 | 0 | none | none |  |
