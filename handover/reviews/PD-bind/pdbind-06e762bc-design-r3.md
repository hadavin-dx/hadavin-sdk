# pdbind-06e762bc-design-r3: part 2 (bind guard), head 06e762bc, round 3, persona design

Source: hand-back of the design reviewer (agent a31238bd), saved by the lead (condensed). SECURITY / mode-safety path. Read-only; nothing run. 0 Blocker, 2 Major, 9 Minor (3-11), nits. Snapshot `/home/user/build/snap/pdbind-06e762bc`. Verdict: M1 of round 2 fixed for what it names (overrides, constructor objects, a replaced attribute seen at serve(), read-only config property, overrides as MappingProxyType); not fixed for changes after the server is up, and the check trusts the object that reports on itself.

## Major
- **M1** The check runs once, at bind time (receiver.py:96-103; handler closure :74-94 reads `approvals` live per request; requests.py:72, :90-99 public mutable `channel`, `store`, `detector`). Failing input: `a = build(..., channel=FakeChannel(...))` with stand-in config; `srv = serve(a.approvals, config=a.config, host="0.0.0.0")` accepted; then `a.approvals.channel = SlackChannel(...)` or `.store = PgStore(...)`; `srv.serve_forever()` serves a real channel and store on a public address with no reason and no log line. Same with `cfg.tool_modules.append(...)`, `cfg.sources[...] = ...` (Config frozen, list/dict fields mutable). Test pins only a swap before serve (test_bindguard.py:836-844); docstring "so a replaced attribute is seen" overstates. Fix: on a public bind with no reason, re-run `real_services(config, approvals.held_services())` per request in `Handler.do_POST` and answer 503, or make channel/store/detector set-once.
- **M2** The server-scan test has hole forms; by name only (test_bindguard.py:1020-1068, fixtures :1093-1114). Inputs: alias import `from http.server import ThreadingHTTPServer as S; S(('', 80), H)`; positional `app.run("0.0.0.0", 5000)`. Missing forms: wsgiref make_server/WSGIServer, werkzeug run_simple, websockets.serve, trio.serve_tcp, anyio.create_tcp_listener, grpc add_insecure_port, a `socketserver.BaseServer` subclass, non-.py launchers (shell, Dockerfile, compose: `python -m http.server`, `flask run --host`), directories other than src/demos/tools.

## Minor
3. `stand_in` public decorator over a mutable module set (standins.py:11-26): `@stand_in class MyRealChannel` or `_CLASSES.add(X)`; only the test pins the list. Fix: refuse unless `cls.__module__` starts with `hadavin_sdk.`, or freeze at end of package import.
4. "Exact class" test is hash-based (standins.py:22 `type(obj) in _CLASSES`): metaclass with `__hash__`/`__eq__` spoof. Fix: `any(type(obj) is c for c in _CLASSES)`.
5. A stand-in counts by class, not behaviour: `fc.post_card = real_post`, `FakeChannel.send = real_send`; FakeSecretProvider/FakeChannel fed real secrets; `AnyOf.detectors` mutable and read only at bind time.
6. `serve` trusts the object that reports on itself (receiver.py:63-72, :102): no `type(approvals) is Approvals` check; subclass overriding `held_services()` or duck-typed object; `_config`/`_overrides` plain private attributes (`vars(a)["_overrides"] = {}`); CHANGELOG "cannot be assigned" true only for public names.
7. `overrides` is a declaration, not an observation: `clock`, `hold_run_ids` uncounted; hand-built Approvals sees a real model/secrets/source only if passed in `overrides=`; CHANGELOG line "a real model, secrets provider ... given to Approvals(...)" overstates (constructor has no such parameters); `clock` and `on_decided` not named in the "Not read" docstring.
8. Emptiness by truthiness (bindguard.py ~125 `if obj:`): `LazyTools` with `__len__` 0 or `__bool__` False hides a real mapping.
9. `listen(..., held=None)` default counts nothing; make `held` required.
10. IN_PROCESS pin does not cover `record_only=True`: flipping it to False runs `on_decided` and `channel.update` after a valid signature and no bindguard test fails (test_bindguard.py:939-966); name-based AST evaded by `a = approvals; a.decide(...)`.
11. Possible regression from MappingProxyType: deepcopy/pickle of an Approvals raise TypeError (reading only; not in CHANGELOG).

## Nits
`held_services()` merge hides an overridden object once the live attribute is replaced; cyclic `AnyOf` recurses without bound (raises, fails closed); a reason of ten identical characters passes; odd wrapping in defaults.py BIND_* lines.

## Round 2 items
Reason min length fixed. IN_PROCESS pins partly fixed (Minor 10). CHANGELOG mostly fixed (Minor 6, 7 overstatements remain). Widened scan: Major 2 stands.

## Checked and found fine
Config read-only property, serve refuses None and a foreign config; override names match build() arguments, taken before rebinding; sources=/tools= refused by build() in live stages; subclass of a stand-in is real, look-alike name is real, AnyOf stand-in only if every entry is; an unimported stand-in module is unregistered (fails closed); `localhost` any case becomes 127.0.0.1; wildcards, empty string, bytes, names, 127.1, leading zero, scope id, brackets round IPv4, `::ffff:` with non-loopback inside, NAT64 refused or fail closed; `listen` never resolves a name; reason control characters and bidi refused by isprintable; handler reaches only `receive`.

## Not checked
Nothing run (no tests, mutants, `::1` socket, 3.12); test_netguard/test_loopback_sites bodies, most of test_bindguard.py 1-690, which of B1-B52 are killed; DELTA beyond line 400, DIFF beyond line 749; other injectable callables of FakeLLM/FakeChannel; whether anything beyond the receiver reaches Approvals attributes; deepcopy/pickle behaviour; store/postgres._is_local and tools.py; entry-point plugins adding kinds to TABLE.
