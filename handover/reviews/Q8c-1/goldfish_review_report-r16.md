Status: resolved

# Goldfish Annotated Review Report (round 16, Q8c-1 batch 16, SECURITY path)

**Target:** `/home/user/build/snap/q8c1b16-43be04de/DIFF.patch` (full), code head 43be04de
**Inputs:** design r16 (4 Major N-A..N-D, Minor N-E, mutant gaps N-F1..F5), codebase r16 (0 Major, Minors 1-8, Nits 9-12). Runner a0509624 not yet reported; not waited for.
**Handoff:** accepted fixes 19 (4 Major + 8 codebase Minor + N-E + N-F1..F5, grouped into 4 classes below, one of them a design change); contested 0; escalated 0; declined 3 (nits 11, 12 and N-F5 as a code change: state it only); remaining unaddressed 0.

## Round verdict and stop rule
NOT clean: 4 unsettled Majors (N-A..N-D) on a security path. The stop rule (a round with no Blocker and no Major) does not hold. A batch 17 and a round 17 are required; security paths have no round cap. But rounds 13 to 16 found one class four times, so batch 17 must change the design, not add a fifth form.

## DECISION: the choke point (Class 1, replaces forms N-A, N-B, N-C, N-D and codebase 6, 7, 8)
Root cause: the notes check decides which test units a changed file reaches by enumerating pytest and Python forms. Every form it does not know silently reaches nothing, which is the unsafe default.
Fix, inverted default (fail closed):
- Reach is computed by a closure over the forms the check can read. A changed file under `tests/` (any extension that is imported, collected, configured or read by tests) lists EVERY test unit unless the closure PROVES it unreachable. Proof = the file is reached by no resolved edge AND no unresolved edge exists anywhere in the tests tree.
- "Unresolved edge" is one flag per file or tree, set whenever the resolver meets something it cannot read: an unreadable or dotted or relative import name, a by-name loader (`import_module`, `importorskip`, `find_spec`, `exec_module`, `runpy`, `__import__`, `getattr` on a module), `pytest_plugins` in any form, `-p` or `PYTEST_ADDOPTS` or entry points, `tests/__init__.py` and any `__init__.py` or conftest on the way, a fixture whose name or override cannot be matched, a test class with a base the resolver cannot find in the same file, `indirect` parametrize, a `getfixturevalue` with a non-literal. When the flag is set, a change to any file in `tests/` lists every unit (the existing "every Python file under tests" fallback made global rather than per file imports).
- Units to enumerate stay as today, but the enumerator must be a superset: every `def test*` or `Test*` class found anywhere in the module (nested, in `if/try/with`, assigned `test_x = factory()`, inherited from any base or mixin, unittest classes with any base) counts as a unit; an unknown base makes the whole class a unit of the file that defines it AND of every file that imports the base.
- tests/ files whose change CANNOT matter by form (a `.md` file no code reads) are the only exemption; it is decided by a short allow-list of suffixes, not by a deny-list of forms.
FIX BRIEF (builder: a new Sonnet builder resumed from the Q8c-1 branch `wip/cloud-q8c1-b16` code head 43be04de; the old builder a806b862 belongs to the guard):
- Files: `tools/notes_lines_check.py` (closure, `_dynamic_files`, `plugin_names`, `_starts_with_package_name`, test enumeration, fixture closure), `tests/test_notes_lines_check.py`, `tests/policy_mutants.py` (new B17 rows), `mutation_manifest.json` hashes, CHANGELOG, docstring.
- Change: add a single `unresolved_edge` collector; every branch that today returns "nothing" or skips a node calls it with a reason string; the final reach step lists every unit when any reason exists (printed reasons, first five). Delete the per-form exemption in `_starts_with_package_name` and the `chain[0] in imports` shortcut (codebase 8): a prefix that is not provably a child of a tests package is unreadable. Follow `tests/__init__.py`, `tests/<pkg>/__init__.py` like conftests (N-A). Follow the overridden fixture of the same name in the nearer and farther conftest (N-C). Add loaders `pytest.importorskip`, `importlib.util.find_spec`, `spec_from_file_location`, `runpy.run_module` and `run_path` to DYNAMIC_IMPORTS (N-D). Imported fixtures and `pytest_plugins +=`/`.append` count as edges (codebase 6, 7); `pytest.toml` and `.pytest.ini` read as config (codebase 7). Autouse by any non-literal form (`autouse=AUTO`, `=1`, `pytest.fixture(autouse=True)(_impl)`, nested class) makes the fixture autouse (N-E); bare `from helpers import x` is followed or flagged unresolved.
- Tests (each one input per branch; each must FAIL on 43be04de): `tests/__init__.py` change lists tests; inherited test (`class TestA(Base): pass`, Base in a mixin module); unittest class with base `IsolatedAsyncioTestCase`, `TC`, `FooTests(ProjectBase)`; tests inside module-level `if`, `try`, `with`, nested class; `test_x = factory()`; `def client(client)` override and nearer-conftest `def db(db)`; `import_module("." + n, "tests")`, f".{n}", constant ".helpers" with package, `f"{helpers.__name__}_v2"`, `make.__name__ + "x"`; `pytest.importorskip("tests.x")`, `find_spec` + `exec_module`, `runpy.run_module`; `autouse=AUTO`; `pytest_plugins +=`; `.pytest.ini`; imported fixture with an unreadable name.
- Mutants (B17 rows, each killed): remove each `unresolved_edge` call site (one mutant per site); change the global fallback to per-file; drop `tests/__init__.py` follow; drop the same-name override follow; drop each new loader; restore `chain[0] in imports`; plus N-F1..N-F4: removal of `chain[1] == "__name__"`, `chain[0] in imports`, `len(chain) == 2`; `_header_nodes` bases, class keywords, `kw_defaults`, annotations, returns each; `["lf"]` in LAZY_FIXTURES and bare `@fixture(name=...)`; `_printed_row_count`, the assertion helper and the tolerance expression.
- Fail-before: all new tests fail on 43be04de; run them there and record the failed ids.
- Docs: the docstring states the rule in one sentence ("a change under tests lists every test unless the check proves nothing can reach it"); N-F5 is only a sentence (resolver pass cap of 8 stated), no code; remove the over-claim "its hooks" of every conftest (N-E): say the 14 names it follows.
- Cost note: the check becomes more conservative (more tests listed per change, so more rows needed). That is the intended safe direction; the plants and the 36 / 1 / 35 figures are rerun and re-pinned from the fast plant test.

## Class 2: mutation runner links and junctions (codebase 4, 5)
`tools/mutation_runner.py`: check `_through_a_link` BEFORE `_inside` so a link to a file outside the tree is left out, as documented (or document the refusal: choose "left out", fewer surprises); apply `_refuse_junctions` to the folder part of every `extra_files` path; tests for the outside-link case and for a junction-like folder (Windows only: skip with reason elsewhere; on Linux test a folder symlink). Mutant for each. Fail-before: outside-link test fails on 43be04de. Refresh the manifest sha (733a19c8... is the new sha the reviewer could not hash: the runner must recompute).

## Class 3: pins that were asserted but not pinned (codebase 1, 3; N-F3, N-F4)
`_printed_row_count` and the printed-figure pin: add a negative test (a wrong figure fails; the "about 1 row" names figure asserts `asked` within 1..tolerance, not 0 allowed), a mutant for the regex, the helper and the tolerance; the names and kinds figures checked in the fast path too, not only `_renew_and_check`. Add the missing branch tests and mutants listed in codebase 3 (`kw_defaults`, annotations, `returns`, `lf`, keyword args of `getfixturevalue`/`usefixtures`, the `no:` branch of `-p`, `name=` of `__import__`, `*named` in `dynamic_names`) and the walrus-in-base-class case or remove "a base class" from the CHANGELOG sentence (prefer test).

## Class 4: wording and hygiene (codebase 2, 9, 10; N-E docstring)
CHANGELOG:217 quote each message separately (or drop quotes); CHANGELOG:216 say three mutant rows changed; fix the stale comment at tests/test_notes_lines_check.py:1226; keep k1b statement but confirm in the evidence run that the new k1b tests pass on old code (nit 12: runner confirmation, no edit). DECLINE: nit 11 (long docstring lines): not a defect unless ruff complains, and the runner's ruff passes at this head; re-wrap only if the gate fails.

## Findings table (all with a decision)
| Finding | Class | Decision |
|---|---|---|
| N-A tests/__init__.py not followed | 1 | PROPOSE FIX |
| N-B tests not enumerated | 1 | PROPOSE FIX |
| N-C fixture override | 1 | PROPOSE FIX |
| N-D dotted/relative names, loaders | 1 | PROPOSE FIX |
| N-E autouse forms, bare imports, over-claim | 1 | PROPOSE FIX |
| N-F1..F4 surviving mutants | 1, 3 | PROPOSE FIX |
| N-F5 pass cap undocumented | 1 | DECLINE as code; one sentence |
| codebase 1, 3 | 3 | PROPOSE FIX |
| codebase 2, 9, 10 | 4 | PROPOSE FIX |
| codebase 4, 5 | 2 | PROPOSE FIX |
| codebase 6, 7, 8 | 1 | PROPOSE FIX |
| codebase 11 | 4 | DECLINE |
| codebase 12 | 4 | DECLINE (runner confirms) |

No finding is contested: each cited lines in the snapshot; no ESCALATE.

## Rounds remaining
Round 17 is required after batch 17. If round 17 still finds a new form that the global fail-closed default should have covered, that is churn in the same class and means the fail-closed default has a hole: stop and report it to the lead as a design question rather than add another form.
