# pdbind-b8c88cac-codebase-r6: Part 2 batch 6, head b8c88cac, round 6, persona codebase details

Source: hand-back of the codebase reviewer (agent a1303f85258984e9f), saved by the lead (condensed). SECURITY path. Static read only; read standins.py, bindguard.py, whole DELTA; not seen: receiver.py 80-170, models.py, memory.py, fake.py, channel.py, full test file. Verdict: 1 Blocker, 2 Major, Minors 4-6, Nit 7.

## Blocker
- **B1** Exact-type allowlist is not identity-safe (standins.py:266-273 `_entered`, :305): `kind in _ATOMS`, `kind in leaf`, `kind in _PLAIN_CONTAINERS` (tuple), `kind in data` use hash and `==` on `kind = type(value)`. A metaclass with `__hash__` = hash(int) and `__eq__` True makes a held `Evil()` read as `dict`/atom: `MemoryStore().client = Evil()` then `is_stand_in(s)` is True. Existing test test_bindguard.py:1738 only covers the top-level object (`kind is cls`). `_held_shapes()` has no spoofed value; no mutant. Docstring/CHANGELOG say a class faking == or hash is real. Fix: identity-only membership (`any(kind is t ...)` or id set), a spoofed-metaclass value in `_held_shapes`, a mutant going back to `in`.

## Major
- **N2** Depth 4 probably 503s a store holding real model rows: instance dict 1, `_plans` 2... `ChainStep` fields land at level 5 and are not atoms (needs models.py check). `_populated_store` holds only a Run; no test populates plans or approval requests. Fix: populated-store test (plan with steps, approval request, dead letter) or do not count a data-class instance as a depth level.
- **N3** Scan cost not bounded by SCAN_NODES (standins.py:234-243 `_values`, :295-299): a whole container is copied to a tuple before the budget check; `big = list(range(10**7))` referenced 1000 times materialises 1000 tuples. Memory/CPU unbounded on every unauthenticated POST. Fix: lazy iteration with budget check or builtin len() before copy.

## Minor
- **N4** B87 is a wording mutant (two layers guard the exact-Approvals check: `_recheck` and `is_pinned_instance`); B52, B117, B119 disable two layers; name B117's second layer.
- **N5** "3 of 22 new tests pass on old code" under-counted: also the 100-thread test, the no-cache function test, the no-class-level-container test, `..attribute_equal_to_the_pinned_one..`, `..class_dictionary_key_that_is_a_text_subclass..`. B158 (annotations touch) equivalent on Python 3.14+, docstring says 3.10-3.13 while requires-python >= 3.12. `int(str(FakeChannel.max_card_chars))` returns a cached int if <= 256, so the monkeypatch would do nothing: verify value.
- **N6** `RunState` is a leaf and is not entered (standins.py:266, :108): an attribute hung on an enum member is invisible. Pin it or check `__members__` with empty `__dict__`.

## Nit
- **N7** Test `..five_stand_in_classes_hold_no_class_level_container` checks seven classes and only seven container types by isinstance; six `noqa: BLE001` in touched files (standins.py:230,337; bindguard.py:133,149; receiver.py:58,84), brief said four (all have reasons); no E731 in src.

## Checked and correct
`_ALLOWED` five entries + detector list + APPROVALS = seven keys; six eager pins, FakeSecretProvider the exception (text, test, CHANGELOG agree); dict keys read with dict.keys/values, other containers with base.__iter__; defaultdict factory by identity; depth and budget fail closed (except N3 cost); `Approvals.__setattr__`/`__delattr__` consistent; `_recheck` wraps all (B152); `_refused` lock, last-use eviction, B154-B157; hostile key fixed label; mutant table 154 rows B1-B160 minus six numbers, old texts current, B85 removed without collision.

## Not checked
Nothing run (154 of 154 untested); `__annotations__` on 3.12/3.13; model field shapes; channel.py; full test file; whether every old string occurs exactly once.
