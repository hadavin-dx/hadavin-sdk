# pdbind-d5537f99-design-r5: Part 2 (bind guard), head d5537f99, round 5, persona design

Source: hand-back of agent a2580f73d28520a74, saved by the lead (condensed). SECURITY path. Static read of snapshot `/home/user/build/snap/pdbind-d5537f99`; nothing run, every failing input traced by reading. 0 Blocker, 3 Major, 5 Minor, 1 Nit. NOT clean. The r4 Blocker (forged `__module__`) and r4 Majors are answered; no way through found there.

## Major
- **M1** Depth limit fails open (standins.py:116-131). `_holds_a_function` loops SCAN_DEPTH (4) times then `return False`; a container still in `level` is never entered. `fake_llm.routes = [[[[fn]]]]` passes (`[[[fn]]]` is caught). Node budget and AnyOf nesting fail closed; container depth fails open. Fix: after the loop `return bool(level)`; update docstring, CHANGELOG and depth mutant.
- **M2** Instance scan sees only callables, not foreign objects (standins.py:104-131). `class R(dict): __getitem__ = lambda s,k: real_llm_call(k)`; `fake_llm.routes = R()` passes (the pinned FakeLLM reads `self.routes[...]`); same for a dict subclass with `__setitem__` writing to a real database, a Path-like, a non-callable client object, `defaultdict(real_factory)`. The r4 brief said "callables or non-stand-in objects read as real". Fix: a value reads as real unless its exact type is on an allowlist (str, bytes, int, float, bool, None, Decimal, datetime, Path, exact builtin containers, the model types the stand-ins hold); tests for defaultdict and dict subclass with mutants.
- **M3** `Approvals` itself not pinned (approvals/requests.py:117-145,181-209; receiver.py:46-51). Guard reads private slots; runtime uses public properties. `Approvals.channel = property(lambda s: RealSlack())`, `Approvals.held_services = lambda s: {}`, `Approvals.real_now = lambda s: ()` pass `_recheck`; `type(approvals) is Approvals` is identity only. Not in stated limits. Fix: pin `Approvals` vars and mro with the same `_class_ok` shape in `_recheck`, and make the guard read the accessor the runtime uses (or the runtime read the slots); or state the limit.

## Minor
- m1 set-once undone by `del a._channel; a._channel = x` (no `__delattr__`); fails closed if slot left empty. Define `__delattr__` to refuse; test.
- m2 pin taken at first question can follow tampering (e.g. a fixture patching `FakeChannel.send` before first serve pins the patched class). Unsafe direction. Eager pin via `standins.pin_all()` from `hadavin_sdk/__init__`, or state it.
- m3 per-request cost and lever on the unauthenticated path: each POST runs `real_now` (up to 100000 values per object) before authentication; a MemoryStore over the budget gives 503 for all requests. Cache per object keyed on pin and cheap size check, or state the budget and 503 consequence.
- m4 pin comparison can give false "real": `vars(cls)` gains entries lazily (3.12 `__annotations__`); add a test that introspects the five classes after pinning.
- m5 class-level mutable data compared by identity only; add a test that none of the five classes has such an attribute, or scan class-level container values.

## Nit
n1 `_LAST_LOGGED` (receiver.py:54-67) bare dict mutated from threads; `next(iter())` plus `pop` can raise before the 503 is written; add a lock or try.

## Limits honesty
Pin at first question: stated, unsafe direction. Depth 4: stated, unsafe direction as coded (M1). 100000-value budget reads as real: safe, but a cost (m3). `sys.modules` rewrite and `object.__setattr__`: honest. Missing from limits: class-attribute patch of `Approvals` (M3), `del a._x` (m1).

## Settled, not re-opened
Forged `__module__`/`__qualname__`; stand-in fed real data as plain data; hand-built `overrides={}` believed; `clock` and `on_decided` not read; listen bind-host and mapped-address rules.

## Not checked
Nothing run (no pytest, mutants, real scan); tools/server_scan.py cursory; tests/test_bindguard.py, bind_mutants.py beyond the delta, test_netguard.py, test_p7_tick.py, LAUNCHER_ALLOWED, CI workflow change, config.py, backends/table.py and others not read; the five stand-in class bodies not read (m5); r4 design and codebase reviews and the ticket not read; IPv6, Python 3.12, first-pin thread safety.
