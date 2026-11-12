# pdbind-ddf930f8-design-r4: Part 2 bind guard, head ddf930f8, round 4, persona design

Source: hand-back of the design reviewer (agent a9bf2c0b), saved by the lead (condensed). SECURITY path. Text only, nothing run. Snapshot `/home/user/build/snap/pdbind-ddf930f8`. Verdict: NOT ready. 1 Blocker, 3 Major, 6 Minor, 1 Nit. The core (exact-class identity, frozen config facts, per-request recheck, exact-Approvals check, required `held`) holds.

## Blocker
- **N1** standins.py:44-52 (docstring :6-8, CHANGELOG "any other class is refused with TypeError"): `stand_in()` decides from `cls.__module__` and `cls.__qualname__`, which the class author writes. `class FakeLLM: __module__ = "hadavin_sdk.llm.fake"` then `standins.stand_in(it)` makes a real service count as a stand-in. No check of the calling module; the test uses a name not in `_ALLOWED`; mutant B68 caught only by that test. An early `seal()` would not help. Fix: (a) resolve lazily: for each `_ALLOWED` name take `sys.modules.get(module)` and `getattr` the class, compare `type(obj) is that class`, drop the decorator; or (b) require the caller's globals equal that module's dict, module starts with `hadavin_sdk.`, refuse a second class under a registered name. Test with a forged class plus a mutant; stop claiming "refused from client code" until true.

## Major
- **N2** bindguard.py:75-76, guard/injection.py `AnyOf` (:66): `AnyOf` trusted by `type(obj) is AnyOf` only, not pinned; patching `AnyOf.check` or setting `a.check` on an instance stays a stand-in, contradicting the claim. Pin it like the others; test and mutant.
- **N3** standins.py:55-66: limit "base classes unseen" understated and closable: `_PINNED` copies only `vars(cls)`; replacing a method on a base class or `__bases__` is unseen. Pin `__mro__` and `vars` of each class in it except `object`; or name the limit in the CHANGELOG.
- **N4** standins.py:60-66: the instance rule reads only direct `__dict__` values; a dict or list of callables (e.g. `FakeLLM(routes)`) carries code or a real address through. State "shallow" in docstring and CHANGELOG, or scan dict, list, tuple, set values to a bounded depth.

## Minor
N5 receiver `serve`/`do_POST`: `approvals.__class__ = Sub` (slot-compatible) after the one exact-type check; add `type(approvals) is Approvals` to the recheck or name the limit. N6 "cannot be added to from outside" holds only for `.add`; `_CLASSES` rebinding and `_PINNED` mutation work; soften wording or use a closure. N7 requests.py docs and the two TypeError messages say "sealed" but there is no `seal()`: say "set-once". N8 bindguard.py:132,137: sort with `str(item[0])` and `name in _COUNTED_WHEN_NOT_EMPTY` outside the `try`; hostile keys can raise out of the guard; move into the `try`. N9 tools/server_scan.py: `_aliases` ignores star imports, assignment aliases, `getattr(module,"TCPServer")`; `LAUNCHER_GLOBS` omits Makefile, justfile, k8s manifests; `LAUNCHER_ALLOWED` keyed by (file, word) lets a second `0.0.0.0` in ci.yml pass; add cases and mutants. N10 run-time spy patches `socket.socket.bind`; `_socket.socket().bind` bypasses it; add to the stated limits.

## Nit
N11 only B53 targets the recheck; no mutant for `recheck = reason is None and not is_loopback_host(host)` (always-recheck, recheck with a reason); add two.

## Known deviation (no explicit seal())
Acceptable only after N1 is fixed; lazy resolution by module attribute removes the registration race and makes `seal()` unnecessary.

## Stated limits
Class pin at registration: understated, closable. Fake fed real data: understated (nested callables are code). Run-time control only exercised paths: correct, add `_socket`. tests/ and docs/ not scanned: fine. Hand-given overrides: fine. `object.__setattr__`: fine, add `__class__` assignment.

## Not read
DIFF.patch beyond the delta, old `server_sockets` scan, backends/table.py, config.py, pre-existing parts of test_bindguard.py.
