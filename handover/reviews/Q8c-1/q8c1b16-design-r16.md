# q8c1b16-design-r16: Q8c-1 batch 16, code head 43be04de, round 16, persona design

Source: hand-back of the design reviewer (agent a65a7cd6), saved by the lead (condensed). SECURITY path. Read only; no code run. Snapshot `/home/user/build/snap/q8c1b16-43be04de`. Verdict: round 15 findings fixed; the notes check still has new bypasses (4 Major), 1 Minor group, surviving mutants. Standard "never passes when a reading test has no row" not yet met.

## Round 15 confirmed fixed
N1 (notes_lines_check.py 659-668 every `.py` under tests for an unreadable name; keyword `name=` at 454/461; aliases, `map(import_module,...)`, getfuncargvalue, lazy_fixture, parametrize indirect, fixture alias, walrus in headers each with a test and a B16 mutant); N3 (`_printed_row_count`, tolerance `max(5, printed//2)`; mutant gap N-F4); N5 limits stated and pinned; N6 `_through_a_link` and mkdir with three mutants, EXPECTED_MUTANTS 65; kubernetes docstring uses the POLICY wording (no test pins the text; minor); 25 B16 mutants counted.

## Major (new)
- **N-A** notes_lines_check.py:894-897, 1053-1072: `tests/__init__.py` and `tests/<pkg>/__init__.py` are not followed (pytest runs them on collection) and have no `kind_of`; a change there (env var, import-time patch, register_assert_rewrite) lists no test and needs no row. Treat them like conftests.
- **N-B** :840-847, 885-898: tests not enumerated get no unit: inherited test methods (`class TestA(Base): pass` with Base in a mixin module); a unittest class whose base is not literally `TestCase` (`IsolatedAsyncioTestCase`, `TestCase as TC`, `FooTests(ProjectBase)`); tests inside module-level `if/try/with` or a nested Test class; `test_x = factory()`. Enumerate them or state limits and pin with a test.
- **N-C** closure :803-812: a fixture override of the same name (`def client(client)`, or a nearer conftest `def db(db)`) never follows the overridden fixture; a change to it lists none of its tests; no test covers an override.
- **N-D** :463-466, 546-563, 647-651, 659-668: unreadable relative run-time import names starting with a dot (`import_module("." + n, "tests")`, `f".{n}"`, constant `".helpers"` with package) reach nothing; `_starts_with_package_name` exempts any `chain[0] in imports` (even a non-module) and ignores text after `__name__` (`f"{helpers.__name__}_v2"`); by-name loaders `pytest.importorskip("tests.x")`, `importlib.util.find_spec` + `exec_module`, `runpy.run_module` not in DYNAMIC_IMPORTS. Fix: a prefix that does not start with `tests` is unreadable (reach every file); add loaders or state limits.

## Minor
- N-E autouse by form (`autouse=AUTO`, `=1`, `pytest.fixture(autouse=True)(_impl)`, nested class) not seen; bare `from helpers import x` not followed and not stated; docstring says "its hooks" of every conftest but code follows only the 14 `SWITCH_NAMES` (over-claim).
- N-F1 nothing kills removal of `chain[1] == "__name__"`, `chain[0] in imports`, `len(chain) == 2` (line 542). N-F2 `_header_nodes` bases/class keywords/kw_defaults/annotations/returns untested, CHANGELOG "a base class" over-claims. N-F3 `["lf"]` in LAZY_FIXTURES and bare `@fixture(name=...)` untested. N-F4 no mutant for `_printed_row_count`, the assertion helper or the tolerance expression. N-F5 (nit) `_dynamic_aliases` caps at 8 passes, undocumented.

## Not checked
manifest sha256 of the runner, first half of policy_page.py, secrets_vault.py, signer_vault.py, table.py, docs/declared-permissions.md, ci.yml, whether plants run in normal CI, tests beyond the delta, whether `tests/__init__.py` exists in the base, Windows symlinks.

## Lead note (class)
Rounds 13-16 are the same class: the notes check enumerates pytest/Python forms one by one. A choke-point fix is the opposite default: any changed file under tests/ (or any dependency the closure cannot resolve) lists EVERY test unit unless the closure proves it unreachable; the resolver must never silently reach nothing. Ask resolve to decide.
