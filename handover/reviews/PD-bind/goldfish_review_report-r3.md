Status: resolved

# Goldfish Annotated Review Report (round 3, part 2 network bind guard, head 06e762bc)

**Target:** `/home/user/build/snap/pdbind-06e762bc/DIFF.patch` (full file; three-dot diff origin/main...06e762bc). Security / mode-safety path. Findings: design r3 (0B/2M/9m) and codebase r3 (0B/2M/8m), both read in full. Independent evidence not yet available (runner still running); nothing below depends on it.

**Handoff counts:** PROPOSE FIX 17 (4 Major, 13 Minor, grouped into classes A-D), CONTEST 0, ESCALATE 0, DECLINE 4 Nits (plus 1 Nit taken as a fix), remaining unaddressed 0. A fourth fresh round is REQUIRED (security path, 2 Majors in this round). Ledger: PDBIND-r3-1..6 (already appended) and PDBIND-r3-7, PDBIND-r3-8 (appended now), all OPEN.

Honest note first: round 2's Major was closed for the cases it named, and rounds of this kind keep finding the next route. The class under all four Majors is the same: the guard answers once, from objects that can still change or can lie. The fix below moves the answer to where all callers route (the request handler and the Approvals constructor) instead of patching each route.

## Class A: the answer is given once, from objects that can change afterwards  (needs confirming round)
Findings: codebase M1 (config containers mutable), design M1 (check runs at bind time only; channel, store, detector are public and writable), codebase minors 1, 2, 3, design minors 5, 6, 8, 9.

### [Issue A1] [`codebase`, `design`] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/approvals/receiver.py` (serve, do_POST), `approvals/requests.py` (Approvals), `config.py:341-357`, `bindguard.py`.
*   **Discrepancy:** a real service put in after `serve()` returns (a replaced channel, store, detector, or a cleared or extended `sources`, `systems`, `tool_modules`, `check_modules`) is never counted; the check reads live objects once.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** a once-only check can never be complete for mutable objects; the choke point is the request handler (every request on every bind passes it) and the Approvals constructor (every route builds one).
*   ***FIX BRIEF:***
    1. `Approvals.__init__` computes `self._config_facts = real_services(config)` once (a tuple) and stores it; `config` and `overrides` stay read-only. `Approvals.held_services()` returns the live channel, detector and store plus overrides as now.
    2. New method `Approvals.real_now()` = `_config_facts` + `real_services(None-config, held_services())` parts (split `real_services` into `config_services(config)` and `held_services_found(held)`; no behaviour change for existing callers). A cleared container after build changes nothing because the facts were frozen.
    3. In `serve`, compute `needs_reason_check = public bind and no reason`. In `Handler.do_POST`, when `needs_reason_check`, call `Approvals.real_now(approvals)` (unbound call on the class, so a subclass override of `held_services` or `real_now` is not trusted); if it returns anything, answer 503 with an empty body and log one line naming the held object (`_shown`). Loopback and "reason given" binds do not pay the check.
    4. `serve` refuses an `approvals` whose exact type is not `Approvals` (`type(approvals) is Approvals`; tests that use stand-in objects use the real class with fakes).
    5. Make `channel`, `store`, `detector` read-through properties with a setter that is allowed only while `_sealed` is False; `serve` and `Approvals.__init__` end seal them. A later assignment raises `AttributeError` (set-once). `held_services()` is then stable; the per-request check remains for anything that bypasses the setter (private attributes), which is stated as "a person writing `vars(a)[...]` is outside the guard".
    6. `held` becomes a required argument of `listen`, `require_safe_bind` and `public_bind_problem` (callers pass `{}` explicitly). Emptiness of `tools`/`sources` is judged by `type(obj) is dict and not dict.__len__(obj)` style exact checks: only a plain empty `dict` or `MappingProxyType` is "empty"; any other mapping type counts as held (no `__bool__` or `__len__` of foreign code is called). A raising object is counted, not propagated: wrap in the held loop so any error counts as held.
    7. `build()` copies caller-owned `tools` and `sources` mappings (`dict(...)`) before recording overrides.
*   ***Tests:*** (a) build a stand-in app, serve on `0.0.0.0` without a reason, then try `app.approvals.channel = Real()`: `AttributeError`; bypass with `vars(a)["_channel"]`: the next POST gets 503 and one log line; (b) clear all four config containers after build: bind still refused at serve (facts frozen) when real ones were configured; (c) `class A(Approvals)` subclass refused by serve; (d) `LazyTools` with `__bool__` False counts as held; raising `__bool__` counts, no crash; (e) `held` omitted: `TypeError`; (f) loopback and reason-given binds answer normally.
*   ***Mutants:*** drop the per-request check; drop the freeze in `__init__`; unseal setter; use `bool(obj)` for emptiness; call `approvals.held_services()` (bound) instead of the unbound call; drop the exact-type check on serve; default `held=None` back.
*   ***Fail-before:*** all of (a) to (e) on 06e762bc src. Expect (a), (b), (c), (d), (e) to fail there.

## Class B: the stand-in registry can be extended or fooled  (needs confirming round)
Findings: codebase M2, design minors 3, 4, 5.

### [Issue B1] [`codebase`, `design`] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/standins.py:11-26`, `bindguard.py:69-76`.
*   **Discrepancy:** `stand_in` is public over a mutable module set; any class can be registered; membership is hash-based; a stand-in counts by class, not behaviour.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** "the core's own stand-ins" is only true if the registry accepts the core's own classes and nothing else, enforced at run time, not only in a test.
*   ***FIX BRIEF:***
    1. `stand_in` refuses (`TypeError`) unless `cls.__module__` starts with `hadavin_sdk.`; the stand-in module must also be one of an explicit literal of dotted module names kept in `standins.py` (`_ALLOWED_MODULES`, a `frozenset`). A new stand-in is thus a visible edit of two places.
    2. After the package import that registers them, the registry is sealed: `_CLASSES` becomes a `frozenset` held in a private module global; `stand_in` after sealing raises. Sealing is done by `bindguard` on first use (`standins.seal()`; idempotent). A test that registers late sees the refusal.
    3. `is_registered_stand_in` uses `any(type(obj) is c for c in _CLASSES)` (identity), not `in`.
    4. Behaviour: a stand-in instance counts only while `type(obj).__dict__` of its class and `vars(obj)` contain no callable overrides outside the class's own declared slots: implement as "every callable in `vars(obj)` is refused" (an instance attribute that is a function, method or class counts the object as real) and pin class attribute identity at seal time (`{name: id(attr)}` for the class's public methods; a changed one counts as real). A fake fed real secret values is out of scope for a class check; state that plainly in the docstring and CHANGELOG.
    5. `AnyOf.detectors` is copied to a tuple at construction and read per request through the same per-request check (class A).
*   ***Tests:*** register a class from `tests` or `__main__`: refused; `_CLASSES.add` after seal: `AttributeError` (frozenset); metaclass with `__hash__`/`__eq__` spoof is real; `fc.post_card = f` and `FakeChannel.send = f` make it real; late `AnyOf.detectors.append` has no effect.
*   ***Mutants:*** drop the module-prefix check; drop sealing; `in` instead of identity; drop the instance-callable rule; drop the class-attribute pin.
*   ***Fail-before:*** the five tests on 06e762bc; all except the subclass control should fail there.

## Class C: the server-scan test is by name and has holes  (batch only, plus one new control)
Findings: design M2, codebase minor 7.

### [Issue C1] [`design`, `codebase`] - Severity: Major
*   **Affected Scope:** `tests/test_bindguard.py:1020-1068`, fixtures `:1093-1114`.
*   **Discrepancy:** by-name scan misses alias imports, positional run hosts, wsgiref, werkzeug, websockets, trio, anyio, grpc, a `BaseServer` subclass, shell, Dockerfile and compose launchers, and directories beyond src, demos and tools.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** a name scan can never be complete; the stronger control is at the one place every server must pass: the bind call.
*   ***FIX BRIEF:***
    1. Runtime control (new test): patch `socket.socket.bind` and `socketserver.TCPServer.server_bind` (and `socketserver.BaseServer.server_activate` where a bind is skipped) to record the caller frame; run the whole receiver path (`serve` on loopback with stand-ins, real `serve` with reason) and assert the only frame that reaches either is `bindguard.listen`. Also import every module under `src/hadavin_sdk` and `tools` (not `demos` needing extras) with the patch active and assert no bind happens at import.
    2. Static scan: resolve import aliases first (`ImportFrom` with `asname`, `import x as y`), then match calls by the resolved dotted name; add the listed forms (wsgiref `make_server`, `WSGIServer`, werkzeug `run_simple`, `websockets.serve`, trio `serve_tcp`, anyio `create_tcp_listener`, grpc `add_insecure_port`/`add_secure_port`, any class whose bases resolve to `socketserver.BaseServer`, `.run(...)` with any literal first positional argument or `host=`); scan `src`, `demos`, `tools`, `tests/helpers` fixtures excluded by an explicit list, plus text scan of `*.sh`, `Dockerfile*`, `compose*.y*ml`, `.github/workflows` for `http.server`, `flask run`, `uvicorn`, `gunicorn`, `--host`, `0.0.0.0`.
    3. Docstring and CHANGELOG state plainly: the static scan lists forms; the runtime check proves only paths the tests execute; code run by another process (a launcher in a client's own repo) is out of reach.
*   ***Tests and mutants:*** one seeded fixture per new form (alias, positional, each library, base subclass, each launcher kind); mutant that drops the alias resolution; mutant that makes `listen` call `socket.bind` through a second function (the runtime control must catch it); mutant that removes the import-time check.
*   ***Fail-before:*** seeded fixtures against the old scan: all new forms should pass the old scan (that is the finding); the runtime control against a deliberately planted second bind must fail on the old code (no such control existed).

## Class D: remaining minors  (batch only, except D3)
### [Issue D1] [`codebase`] - Severity: Minor
*   Caller-owned mapping by reference: covered by A1 step 7. Test: `t = {...}; build(tools=t); t.clear()`: still counted.
### [Issue D2] [`design`] - Severity: Minor
*   `serve` trusts the object: covered by A1 step 3 and 4. `_config`/`_overrides` private attributes: state in docstring and CHANGELOG that `vars(a)` writes are outside the guard; make `_config`, `_overrides` slots (`__slots__`) so `vars(a)` fails with `TypeError`.
### [Issue D3] [`design`, `codebase`] - Severity: Minor  (needs confirming round: guard-behaviour pin)
*   IN_PROCESS pin: extend `test_the_listener_reaches_the_approvals_only_through_the_signature_check`: resolve one-step aliases (`a = approvals`) and every attribute chain rooted at `approvals`; assert the `record_only=True` keyword literal at the one `receive` call in `handle_slack_action`; add a mutant that flips it to `False` and one that calls `approvals.audit.write_outcome` from a handler (both must be killed).
### [Issue D4] [`design`, `codebase`] - Severity: Minor
*   deepcopy and pickle of an `Approvals` raise `TypeError` (read, not run): run it, then either support it (`__deepcopy__` returning a fresh sealed copy with the same facts) or refuse with a clear `TypeError` message and add the line to the CHANGELOG Breaking list. Recommended: refuse with a message (a copy would duplicate sealed state); test both.
### [Issue D5] [`design`] - Severity: Minor
*   CHANGELOG overstatements: remove "a real model, secrets provider or source given to `Approvals(...)`" (the constructor has no such parameters; only `build()` takes overrides); add `clock`, `on_decided`, `hold_run_ids` to the "Not read" list with the sentence that `clock()` runs on every unauthenticated POST and `audit.write_outcome` after a valid signature; say "checked at every request on a public bind with no reason" once class A lands; say `copy.copy` shares `_config`/`_overrides` (read-only, so harmless).
### [Issue D6] [`codebase`] - Severity: Minor
*   Hand-built `Approvals`: `audit`, `registry`, `on_decided`, `clock` uncounted; documented. Add one more refusal: a hand-built Approvals (config passed in by the caller, no `build()`) on a public bind without a reason is refused unless every counted field is a registered stand-in (`audit` and `registry` types included in `held_services()` for hand-built objects only). Test and mutant.
### [Issue D7] [`codebase`] - Severity: Minor
*   Missing mutants: drop the `"store"` or `"detector"` key from `held_services`; B50 asserts only "BindRefused" with `allow_crash`: pin the named object in the text; add an end-to-end test that sends `build()`'s own Approvals with a real override through `serve` (replace `_Built` re-assembly by a check module that counts as stand-in for the test).

## Nits
*   **DECLINE:** bindguard.py:12-14 long lines (ruff format passes; wrap only when touched); defaults.py wrapping; cyclic `AnyOf` recursion (raises, fails closed, already safe); reason of ten identical characters (a length gate by design; the reason is a log line, stated).
*   **Taken as a fix:** `held_services()` merge hiding an overridden object: with set-once in A1 the live attribute cannot differ from the override; add a test that both are counted when they differ (`vars` bypass).

## Batch rules
All items are one fix batch for the builder. Needs a confirming round: class A, class B, D3 (guard behaviour), and the runtime control in class C. Batch only: the rest. After the batch: one fresh independent evidence run (UTF8 Postgres, server-environment port, record interpreter version; IPv6 `::1` socket and Python 3.12 stay IMPOSSIBLE-NOW here, owed to CI or the laptop: `pytest tests/test_bindguard.py -k ipv6`) and a fourth fresh design + codebase pair.
