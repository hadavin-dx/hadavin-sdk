# pdbind-06e762bc-codebase-r3: part 2 (bind guard), head 06e762bc, round 3, persona codebase details

Source: hand-back of the codebase reviewer (agent afee461e), saved by the lead (condensed). SECURITY / mode-safety path. Read-only; nothing run. 0 Blocker, 2 Major, 8 Minor, nits. Snapshot `/home/user/build/snap/pdbind-06e762bc` (three-dot).

## Major
- **M1** "Read-only config" is shallow: `Config` is `frozen=True` (config.py:62) but `check_modules`, `systems`, `tool_modules`, `sources` are plain list/dict (config.py:341-357). For a `build()` app these facts are not in `overrides`, and `real_services` reads the live `Config` at serve time. Failing input: build with sources/tool_modules/check_modules/systems set, then `app.config.sources.clear()` (and the other three), then `serve(app.approvals, config=app.config, host="0.0.0.0")`: accepted with no reason. No test covers it. Fix: snapshot the counted facts at `Approvals.__init__` (frozen tuple of `real_services(config)`), or freeze the containers (tuple, MappingProxyType, frozenset) in `Config`.
- **M2** The stand-in list can be extended by any code: `standins.stand_in` is public and `_CLASSES` is a mutable module set (standins.py:11-17; bindguard.py:69-76). `@stand_in class MyRealChannel` or `standins._CLASSES.add(...)` then `channel=` to `build()`/`Approvals`: a public bind is accepted with no reason. The test pins the list only inside the test process. Fix: also require `cls.__module__.startswith("hadavin_sdk.")`, or compare against a frozen literal of dotted names in bindguard.

## Minor
1. TOCTOU: `held_services()` read once in `serve()` (receiver.py:102); channel/store/detector stay writable after serve starts. Document "checked at start" or re-check per request.
2. Caller-owned `tools`/`sources` mapping recorded by reference (requests.py:79 copies outer dict only): `t.clear()` after build hides it. Low impact.
3. `serve` does not type-check `approvals`: a subclass may override `held_services()`/`config`; `if obj:` emptiness test (bindguard.py:126) lets a `__bool__`/`__len__` hide a real mapping, and a raising `__bool__` escapes as a non-BindRefused error.
4. A hand-built `Approvals` leaves `audit`, `registry`, `on_decided`, `clock` uncounted; documented, not verifiable.
5. deepcopy/pickle of an `Approvals` should now raise TypeError (mappingproxy); not in CHANGELOG; copy.copy shares `_config` and `_overrides`.
6. Listener-reach pin hole (test_bindguard.py:927-966): only calls on the bare name `approvals` are collected; `approvals.audit.write_outcome(...)`, `approvals.channel.send(...)`, `approvals.store.get_...` pass. B47 mutates only `decide`.
7. Widened server scan still misses: aliased import (`ThreadingHTTPServer as S`), `wsgiref.simple_server.make_server`, gRPC `add_insecure_port`, `websockets.serve`, positional `.run("0.0.0.0")`, direct `socketserver.BaseServer` subclass, `importlib`/`__import__`.
8. `listen(..., held=None)` defaults to counting nothing (fails open for a future caller); no test requires every caller to pass `held`.

## Nits
bindguard.py:12-14 long docstring lines; B50 expects only "BindRefused"; no mutant for dropping `store`/`detector` keys from `held_services`; no end-to-end test of build()'s own Approvals with a real override through `serve` (`_Built` re-assembles); a reason of ten identical characters passes (length gate only).

## Checked and found fine
Overrides captured before rebinding (app.py:81-92); `overrides` is MappingProxyType; `config`/`overrides` no setter; live channel/detector/store overwrite overrides in `held_services()`; stand-in match by exact class (subclass is real, `AnyOf` recursed only when exact); refusal text via `_shown`; `config=None` refused; `serve` passes `held=` to both checks; bind parsing fail-closed (leading zeros, scope ids, brackets, mapped, wildcard, names never looked up); reason min 10 pinned (9 refused, 10 accepted; B46, B23); IN_PROCESS pins (five kinds, 31 kinds pinned); CHANGELOG says Breaking and labels the 66-check run builder-run, `::1` and 3.12 owed to CI; B8/B9/B20/B28/B31 carry full text; 20 seeded scan fixtures; FakeLLM and FakeChannel have no network or process side effects.

## Not checked
Nothing executed (no pytest, mutants, import cycle bindguard -> guard.injection -> standins, 3.12 syntax of `def stand_in[T: type]`); DELTA beyond line 917; tests in test_loopback_sites/test_netguard/test_p7_tick/ci.yml; whether config-built fake channel/store/detector are exactly the registered classes (over-refusal if a wrapper); other callers of `Approvals(...)`/`serve(...)`; demos/tools servers; deep immutability of `Backends`/`KindSettings`.
