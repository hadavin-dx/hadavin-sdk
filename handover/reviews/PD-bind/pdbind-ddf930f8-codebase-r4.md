# pdbind-ddf930f8-codebase-r4: Part 2 bind guard, head ddf930f8, round 4, persona codebase details

Source: hand-back of the codebase reviewer (agent adf6121d), saved by the lead (condensed). SECURITY path. Read only; no code run. Snapshot `/home/user/build/snap/pdbind-ddf930f8`. 0 Blocker, 3 Major, Minors 4-9, Nit 10.

## Major
- **M1** receiver.py:68, 86-98; approvals/requests.py:57-80, 161-181. `a.__class__ = S` (S a subclass of Approvals with `__slots__ = ()`) is a plain assignment and passes; `serve` checks `type(approvals) is Approvals` once. `held_services` and `real_now` read private slots directly while `receive`, `decide`, `_send` go through properties that S can override: the guard sees a stand-in, the live path a real object. Not covered by the per-request recheck, the `object.__setattr__` caveat, or any test. Caveat wording understates: a plain `a._channel = x` also works (no `__setattr__` guard). Fix: add `type(approvals) is Approvals` to the per-request recheck, or have `real_now` return a non-empty answer when `type(self)` is not Approvals; correct the wording; test and mutant.
- **M2** standins.py:8-10 vs 42-52. Docstring says the registry takes classes only from a module of this package, code compares only `f"{cls.__module__}.{cls.__qualname__}"` with `_ALLOWED`; both are attacker-writable (`class MemoryStore: __module__ = "hadavin_sdk.store.memory"` then `@stand_in`). Instances then read as stand-ins. Test only uses a different name. Fix: resolve by module attribute (`sys.modules[mod].__dict__.get(qualname) is cls`) or check the registering frame's `__name__`; test the spoof. (Same as the lead's planned lazy resolution.)
- **M3** bindguard.py:70-77 with guard/injection.py:63-81. `AnyOf` trusted on exact type alone: no `_changed` treatment. `any_of.check = real_fn`, a patched class, or `any_of.detectors = <empty iterable>` (all() vacuous) is not noticed; foreign `__iter__` runs inside the guard. Fix: require `type(obj.detectors) is tuple`, apply `_changed` checks to AnyOf, or make it slotted and read-only.

## Minor
- 4: `__slots__` has no `__weakref__` (weakref.ref raises, CHANGELOG silent); dead branches in `standins._changed` (62-66).
- 5: CHANGELOG set-once list omits `audit`, `registry`, `on_decided` (read-only properties); sentence names `hold_run_ids` which is not an Approvals attribute (it is Runtime, app.py:72, 241). Demos/other tests not grepped for assignments to these names.
- 6: `real_services(..., held=None)` still defaulted and public; config-only answer silently.
- 7: server_scan gaps: `from socketserver import *` stores key `*`, bare `TCPServer(...)` not flagged; flat alias dict (BFS) lets a later/nested import re-point an alias; SERVER_ROOTS only for import_module (`importlib.import_module("socketserver")` unflagged despite CHANGELOG); `from waitress import serve` + `serve(app, host=...)`; `_host_like` regex matches words ("add", "bad", "cafe") and duplicates netguard helpers (pin false positives); LAUNCHER_GLOBS omits Makefile, *.bash, *.ps1, k8s yaml, entrypoint*, pyproject scripts.
- 8: tests/mutants: B58 only `listen` (defaults on `require_safe_bind`, `public_bind_problem` unmutated); B53 only wholesale (nothing for `recheck = True` or dropping the loopback/reason term); B78 removes uvicorn, gunicorn, 0.0.0.0 together (flask run, --host, serve_forever, nc -l, socat, python -m *server untested); registry frozen test proves only frozenset has no add (not rebinding `_CLASSES` or clearing `_PINNED`; clearing fails closed); test_bindguard.py:1321-1326 leaks a bound socket; B81-B83 only see chains rooted at `approvals` (`Approvals.real_now(approvals)` invisible).
- 9: refused request logs a WARNING per request, no rate limit (volume only).

## Nit
10: "83 bind mutants" not recounted.

## Verified OK
held callers; exact-class check (except `__class__` assignment); slotted design; copy/deepcopy/pickle raise (B63, B64); `type(obj) is cls` identity; `_changed` per-item identity and 3.12/3.13 class dict extras; no over-refusal for the five stand-ins; run-time bind spy frames; B77; IPv4/IPv6 consistency; ast alias handling.

## Not checked
No test or mutant run; guard/egress.py vs netguard; demos/docs/conftest/pyproject greps; IPv6 test skipped on CI?; Python 3.14.
