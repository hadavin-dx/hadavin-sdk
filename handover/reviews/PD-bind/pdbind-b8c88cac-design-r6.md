# pdbind-b8c88cac-design-r6: Part 2 batch 6, head b8c88cac, round 6, persona design

Source: hand-back of the design reviewer (agent a3b20455465ce4e22), saved by the lead (condensed). SECURITY path (no round cap). Static read only, nothing run; read standins.py, receiver.py, bindguard.py, CHANGELOG and delta lines 1-641 of 1577 (lines 642-1577, `models.py`, mutant bodies not read). Verdict: NOT clean, 1 Blocker (B1), Minors M1-M6, Nits.

## Blocker
- **B1** The exact-type allowlist is judged by set or tuple membership, not identity (src/hadavin_sdk/standins.py:266 `kind in _ATOMS or kind in leaf`, :268 `kind in _PLAIN_CONTAINERS`, :273 `kind in data`, :305 `type(value) not in _ATOMS`). `kind = type(value)` of a held value is attacker-controlled: a metaclass with `__hash__ = hash(str)` and `__eq__ = True` passes as an atom, so a class holding a real client counts as plain data, `is_stand_in` is True and the public bind is accepted. Same at the depth tail and for dict keys. Existing test tests/test_bindguard.py:1738 only spoofs the top-level class (`kind is cls`, safe). Docstring (standins.py:21-22) and CHANGELOG:23 say "type(v) is T", which is false for the allowlist. Fix: identity only (`any(kind is t for t in ...)` or require `type(kind) is type`) at all four sites; tests and mutants for a held spoof at level 1, as dict key, and at the depth tail.

## Minor
- **M1** No cache: pre-auth scan up to 100000 values per POST on a single-threaded server (receiver.py:137); large legitimate MemoryStore crosses the budget and 503s every callback and refuses serve(). CHANGELOG should say over-budget is an outage until the store shrinks. Depth 4 enough for legitimate rows (ChainStep with nested args)? Unverified.
- **M2** Model classes read through `object.__getattribute__(value, "__dict__")` (standins.py:92-106, 273-274): pydantic v2 `__pydantic_extra__`/`__pydantic_private__` or `__slots__` state may not be in `__dict__`. Possible Major; confirm how models.py builds them.
- **M3** FakeSecretProvider pinned at first question not at import (standins.py:203-221, CHANGELOG:12,23): judged an accepted, accurately stated gap (first question is serve() itself; unloaded module reads as real).
- **M4** Time of check vs time of use between recheck and use (receiver.py:137-154) not documented; CHANGELOG says "checked at every request".
- **M5** `on_decided` and `clock` not read (CHANGELOG:18): a callable can close over a real service; state it plainly or check it.
- **M6** `serve()` can raise a non-BindRefused error from `Approvals.held_services(approvals)` outside any try (receiver.py:169); fails closed, type differs from the documented "never raises".

## Nits
bindguard.py:63-65 stray blank line; CHANGELOG:23 one very long line; the 154 of 154 count is the runner's claim.

## Holds
Class C (`__delattr__` raises, `_recheck` wraps everything so 503, pin at import, accessors); class D (lock, LRU, fixed label `held (unreadable)`, `type(item[0]) is str`); class B (over-budget reads as real, tail must be exact atoms, nested stand-ins by pin, cycles bounded); dict keys only iterated, never hashed; container subclasses refused by exact type.
