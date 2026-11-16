# pdbind-d5537f99-codebase-r5: Part 2 bind guard, head d5537f99, round 5, persona codebase details

Source: hand-back of agent a4b8a8b39de71ba4a, saved by the lead (condensed). SECURITY path. Read-only, nothing run. 0 Blocker, 2 Major, 6 Minor, 7 Nits. Snapshot /home/user/build/snap/pdbind-d5537f99.

## Major
- **M1** Approvals set-once defeated by `del a._channel` then `a._channel = X` (requests.py:151-165; no `__delattr__`). Same for _config_facts, _overrides, _hand_built, _store, _detector. CHANGELOG and requests.py:66-67 "the one way left" are false. A deleted slot makes `_recheck` raise AttributeError in do_POST (dropped connection, not 503). Fix: `__delattr__` always raises, plus a test; mutant B88 does not cover it.
- **M2** Instance scan rejects only `callable(value)` (standins.py:104-131): a non-callable plain object with `__enter__`/`__exit__` (or Session, SimpleNamespace, MappingProxyType, UserDict, ChainMap) held in an attribute passes. Fix: reject any held value that is not a builtin scalar or an entered container, or state the gap.

## Minor
- m1 "never raises on a hostile key" false for a str subclass whose isprintable raises (bindguard.py:148-149; handler calls `_shown` again). Use a fixed label.
- m2 SCAN_NODES counted per value; scan runs on every unauthenticated POST on a public bind (receiver.py:46-51). MemoryStore with over 100000 values reads REAL (503 for all): fails closed but availability risk; memoise or scan only own attributes.
- m3 Ruff E731 at tests/test_bindguard.py:1639 (`go = lambda self: 1`): CI lint would fail.
- m4 Three new tests are not fail-before (forged class same module and name; metaclass faking eq and hash; module dict not getattr). They are pins (B96, B70, B97). Do not describe them as fail-before.
- m5 `_LAST_LOGGED` (receiver.py:54-67) not thread-safe (KeyError or RuntimeError on concurrent eviction) and evicts by first insertion not last use (breaks "one a minute" after 64 sets). Lock; pop then re-insert.
- m6 Mutant gaps: `_values` iterating via iter(container); a sixth pair in `_ALLOWED`; `vw is vi` to `==`; `type(ki) is str` guard in `_same_shape`; class-level container edited in place (pin by identity).

## Nits
n1 SCAN_DEPTH wording (instance `__dict__` is level 1). n2 pin fragility: `cls.__annotations__` access inserts `{}` on 3.10-3.13, importlib.reload too (fails closed). n3 mutant numbering order. n4 B84 and B85 same killer and effect. n5 odd assert at test_bindguard.py:1650. n6 two comments run together bindguard.py:63-65. n7 defaults.py:324 long trailing comment, ruff format may differ.

## Verified correct (reviewer)
Module-dict lookup behind `type(module) is ModuleType`; `type(obj) is cls`; pin by metaclass, mro, vars; fail-closed `_SEEN`/`_PINNED`; budget exactly 100000; AnyOf depth, cycle, tuple checks; Approvals `__setattr__` with slots, re-init refused, `__class__` refused; receiver `_recheck` only when recheck true; mutant count 130 static, search strings unique; removed B42, B68, B69 justified; B100-112 per-word mutants.

## Not checked
Anything dynamic (tests, mutants, ruff, mypy); siblings not in files/ (memory.py, injection.py, channel.py, mutation_runner.py); demos/docs importers of `standins.stand_in`; Python 3.12/3.13 vars differences.
