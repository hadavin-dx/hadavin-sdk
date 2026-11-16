Status: resolved

# Goldfish Annotated Review Report (round 4, Part 2 bind guard, SECURITY path)

**Target:** `/home/user/build/snap/pdbind-ddf930f8/DIFF.patch` (full file), head ddf930f8
**Inputs:** design r4 (1 Blocker N1, 3 Major N2-N4, minors N5-N11), codebase r4 (0 Blocker, 3 Major M1-M3, minors 4-9, nit 10). Independent runner afb60e5f not yet reported; not waited for.
**Handoff:** accepted fixes 15 (in 6 classes, below); contested 0; escalated 0; declined 2 (nits); remaining unaddressed 0.

## Round verdict and stop rule
Round 4 is NOT clean: one Blocker (N1) and six Majors, counted after merging duplicates: N1 = codebase M2 (one finding, same scope); N2 = M3; N5 = M1; N3 and N4 are design-only Majors. This is a security path, so there is no round cap and the stop rule needs a round with no Blocker and no Major. A fix batch (batch 5) and a round 5 (design and codebase reviewers, fresh runner) are required. Minors go in the same batch with no separate review (ORDER 256 applies only to a clean round).

## Findings by class (all PROPOSE FIX unless stated). FIX BRIEFS for builder a1a94207

### Class 1: who may be a stand-in (identity of trusted classes). Blocker N1 = M2; Major N3.
Root cause: trust is decided from values the class author writes (`__module__`, `__qualname__`, registration at import time), not from the module that really holds the class.
- Files: `src/hadavin_sdk/standins.py` (and the five stand-in modules lose the `@stand_in` decorator), `bindguard.py` call sites.
- Change: delete the registration decorator. Keep `_ALLOWED` as literal `(module, name)` pairs. `is_stand_in(obj)` resolves lazily: `mod = sys.modules.get(module)`; `cls = mod.__dict__.get(name)` (module dict, not `getattr`, so no module `__getattr__`); true only when `type(obj) is cls` and `cls` is not None. A class that is not (yet) imported is never a match. Pin per class `__mro__` and `vars()` of every class in the mro except `object` (N3), compared by length and item identity; computed on first resolve and kept in a module dict that is read inside `try` (a missing key means "real", fail closed).
- Tests: (a) forged class with `__module__ = "hadavin_sdk.llm.fake"` and the same `__qualname__` is NOT a stand-in and no `stand_in` name is importable; (b) a method replaced on a base class, and `__bases__` changed, make the stand-in read as real; (c) module not imported gives real; (d) the real five still pass.
- Mutants: B-reg-1 compare `type(obj).__name__` instead of identity; B-reg-2 use `getattr` instead of the module dict; B-reg-3 drop the mro pin; B-reg-4 drop the `type(obj) is cls` identity (use `isinstance`).
- Fail-before: tests (a) and (b) on ddf930f8 must fail. CHANGELOG: stop saying "refused with TypeError from client code"; say what is checked now and that a client class never matches.

### Class 2: pin everything trusted, not only the registry. Major N2 = M3; Major N4.
- Files: `bindguard.py:70-77`, `guard/injection.py` (`AnyOf`).
- Change: `AnyOf` gets the same `_changed` treatment (pinned class, mro, instance dict scanned). Require `type(obj.detectors) is tuple` and each member itself a stand-in (recursive, depth limit 4, cycle-safe by id set); a failed check, a non-tuple or a foreign `__iter__` reads as "real". Instance dict scan for the five stand-ins and `AnyOf` goes to a bounded depth (4): dict, list, tuple, set values, callables or non-stand-in objects read as real (N4). State depth limit in docstring and CHANGELOG.
- Tests: `any_of.check = real_fn`, patched `AnyOf.check`, `detectors` replaced with an empty-iterating object or a list, a nested callable inside `FakeLLM(routes)`: each reads real. Mutants: drop tuple check; drop depth scan; scan depth 1 only.
- Fail-before: all four tests fail on ddf930f8.

### Class 3: the live object keeps its type per request. Major M1 = N5; minors 4, 5.
- Files: `approvals/receiver.py` (`do_POST` recheck), `approvals/requests.py`.
- Change: add `type(approvals) is Approvals` to the per-request recheck (refuse with 503 when false). Add a `__setattr__` on `Approvals` that refuses any name not in the documented set-once or `clock` list, including `__class__` and every private slot name; `object.__setattr__` is named as the one remaining way and is covered by the per-request recheck of the pinned slot values. Add `__weakref__` to `__slots__` or state in CHANGELOG that weak references are refused (pick: state it, fewer moving parts). CHANGELOG: correct the set-once list (`audit`, `registry`, `on_decided` added), remove `hold_run_ids` from the Approvals sentence (it belongs to Runtime), word "set-once" instead of "sealed" in the docs and both TypeError messages (N7), and say plainly that a plain `a._channel = x` is stopped by the new `__setattr__`.
- Tests: `a.__class__ = SlotSub`, `a._channel = x`, `a.__dict__` access, each refused or answered 503; weakref statement pinned. Mutants: drop the recheck term; drop `__setattr__` name check. Fail-before: first two fail on ddf930f8.

### Class 4: guard code must not raise on hostile input. Minor N8, 6.
- `bindguard.py:132,137`: move the sort with `str(item[0])` and the `name in _COUNTED_WHEN_NOT_EMPTY` test inside the `try`; a hostile key makes the answer "real", never an exception out of the guard. `real_services(..., held=None)`: make `held` required (no default) like the other deciders. Tests with hostile keys (key whose `__str__` raises, unhashable-style objects) and a mutant that moves the sort out. Fail-before: hostile-key test fails on ddf930f8.

### Class 5: scanner and mutant coverage. Minors N9, N10, N11, 7, 8; Major-adjacent mutant gaps.
- `tools/server_scan.py`: resolve `from m import *` for the server modules; alias dict scoped per scope (module, function, class) not flat; `SERVER_ROOTS` applied to `importlib.import_module` (`socketserver`, `http.server`); resolve `from waitress import serve` then `serve(app, host=...)`; reuse `netguard.parse_ip_literal` and `is_localhost_name` for `_host_like` and pin the old false positives ("add", "bad", "cafe") with a test; `LAUNCHER_GLOBS` add Makefile, justfile, `*.bash`, `*.ps1`, k8s yaml, `entrypoint*`, pyproject scripts; `LAUNCHER_ALLOWED` keyed by (file, word, count) so a second `0.0.0.0` fails (N9). Add `_socket.socket().bind` to the stated limits and to the run-time spy if cheap (N10).
- Mutants: B53 split into recheck always true, drop loopback term, drop reason term (N11); B58 extended to `require_safe_bind` and `public_bind_problem` defaults; B78 split so each of uvicorn, gunicorn, `0.0.0.0`, `flask run`, `--host`, `serve_forever`, `nc -l`, `socat`, `python -m *server` is its own mutant with its own fixture; B81-B83 also see `Approvals.real_now(approvals)` style calls (argument position); registry test: rebinding `standins._CLASSES` and clearing `_PINNED` fail closed (add with Class 1 design). Fail-before: new scanner cases fail on ddf930f8.

### Class 6: hygiene. Minors 4 (dead branches), 9, nit 10.
- Remove the dead `except AttributeError` and `type(own) is dict else True` branches in `standins._changed` or add the test that reaches them (prefer remove). Close the leaked socket from the first `serve(...)` in test_bindguard.py:1321-1326. Log refused requests at WARNING at most once per minute per class name (rate limit by a monotonic counter), with a test. Recount the mutants and write the exact number in CHANGELOG (nit 10: ACCEPT, the count is generated by the runner).

## DECLINE
- N6 wording nit overlap: covered by Class 1 (registry now has no mutable registry to "add to"); no separate edit.
- Nit 10 count: recount only, no mutant change (counts are written from the runner output).

## Not contested; why
No finding is inaccurate: the forged-`__module__` bypass and the `__class__` assignment are both reachable by plain assignment in Python and each reviewer cited the lines. No ESCALATE: every fact is in the snapshot.

## Gates for batch 5 (builder)
Full pytest once on the final head, stage mutants, one full bind mutant run (sample while iterating), ruff, bandit, gitleaks, check-no-handover-files.sh, fail-before list, snapshot for round 5 with DELTA vs ddf930f8, then fresh design and codebase reviewers plus a fresh runner (UTF8 Postgres). Round 5 is required.
