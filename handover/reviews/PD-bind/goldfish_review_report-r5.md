Status: resolved

# Goldfish Annotated Review Report, round 5

**Target:** `/home/user/build/snap/pdbind-d5537f99/DIFF.patch` (full), Part 2 bind guard, head d5537f99, SECURITY path (no round cap), automated mode.
Inputs: pdbind-d5537f99-design-r5.md (3 Major, 5 minor, 1 nit) and pdbind-d5537f99-codebase-r5.md (2 Major, 6 minor, 7 nits). Both Major sets overlap: design M1/M2/M3 and codebase M1/M2 reduce to FOUR classes below.

## Classes and decisions (every item PROPOSE FIX, auto-accepted)

### Class A: held values are judged by an allowlist, not by "callable" (design M2, codebase M2, design m5)
Standard: deny by default (least privilege rule); the scan must accept only what it can prove is plain data.
*   Where: src/hadavin_sdk/standins.py `_values`, `_holds_a_function` (about lines 104-131).
*   Change: a held value is accepted only if its EXACT type (`type(v) is T`) is in a literal allowlist: str, bytes, int, float, bool, NoneType, Decimal, date, datetime, timedelta, Path, and the exact builtin containers dict, list, tuple, set, frozenset, deque (these are entered). Anything else reads as real: subclasses of dict or list, defaultdict, UserDict, ChainMap, MappingProxyType, SimpleNamespace, Session, objects with `__enter__`, functions, classes, and non-callable foreign objects. A value whose type is the pinned stand-in class itself (nested stand-in) is judged by the same pin check. Add to the allowlist only the model types the five stand-ins really hold (find them from the five class bodies; each addition needs a test and a reason).
*   Class-level data (design m5): add a test that none of the five classes has a class attribute that is a mutable container, or scan class-level container values with the same allowlist and compare by value shape in the pin.
*   Tests: one per rejected shape (dict subclass with `__getitem__`, defaultdict(real_factory), non-callable object with `__enter__`/`__exit__`, SimpleNamespace, MappingProxyType, UserDict, ChainMap, requests-like Session stand-in built from a plain class); one per accepted shape (the real stand-ins used by the whole suite still read as stand-ins).
*   Mutants: allowlist widened by `isinstance`; `callable` check restored; container entry by `iter()` instead of the builtin base iterator (codebase m6); a sixth pair added to `_ALLOWED`.
*   Fail-before: all rejected-shape tests must fail on d5537f99.

### Class B: depth and size limits fail closed (design M1, design m3, codebase m2)
*   Where: standins.py `_holds_a_function` end of loop; receiver.py `_recheck` lines 46-51.
*   Change 1: after the depth loop `return bool(level)` (a container still unexplored reads as real). Fix the SCAN_DEPTH docstring to state the counting rule once (codebase n1: instance `__dict__` is level 1).
*   Change 2 (cost and lever): cache the verdict per object id inside the pinned guard, keyed on (id, a cheap mutation signature such as len of the top-level `vars(obj)` plus the identities of its values, bounded size); on a cache miss run the scan. State in CHANGELOG the budget of 100000 values and that an over-budget store gives 503 (fail-closed, disclosed). Do NOT scan store contents on every request.
*   Tests: `routes = [[[[fn]]]]` reads real (fail-before); a depth-4 plain-data list still reads as stand-in; two requests in a row run the scan once (counter on the scan function); a change to an attribute invalidates the cache.
*   Mutants: `return False` after the loop; cache never invalidated; cache keyed on id only.

### Class C: Approvals is pinned and its slots cannot be undone (design M3, design m1, codebase M1)
*   Where: src/hadavin_sdk/approvals/requests.py (`__setattr__` about 151-165), receiver.py `_recheck`.
*   Change 1: add `__delattr__` that always raises (AttributeError with a plain message). Correct the CHANGELOG and requests.py:66-67 text: the one way left is `object.__setattr__` and `object.__delattr__`.
*   Change 2: pin `Approvals` (metaclass, mro, per-class vars items, same `_class_ok` shape as the stand-ins) at first use, and compare in `_recheck` before any slot is read. Make the guard read through the same accessors the runtime uses (`channel`, `held_services`, `real_now`) so a patched property cannot differ from the private slot; if that is not possible, make the runtime read the slots.
*   Change 3 (design m2): pin eagerly. Call `standins.pin_all()` (new, literal list of the five classes plus Approvals) at import of the module that builds the receiver, not at the first question; keep the lazy path as a fail-closed fallback. State in the module text that a test fixture patching before import is outside the model.
*   Change 4 (codebase M1 side effect): a deleted slot must give 503 not a dropped connection: `_recheck` catches AttributeError on a slot read and treats it as real.
*   Tests: `del a._channel` raises; `del` then assign raises; class-attribute patch of `Approvals.channel` (property), `Approvals.held_services` and `Approvals.real_now` each give 503; eager pin test (pin exists after import, before first request); `object.__delattr__` path gives 503, not a dropped connection.
*   Mutants: `__delattr__` removed; `Approvals` pin skipped; guard reads private slot not accessor; eager pin removed (the pin test must kill it); AttributeError catch removed.
*   Fail-before: all Class C tests fail on d5537f99.

### Class D: small defects in the same files (codebase m1, m3, m5, m4-label, design m4, n7, nits)
*   `_shown` hostile str key (bindguard.py:148-149): the except handler uses a fixed label "held (unreadable)", never calls a method on the key again. Test with `class K(str)` whose `isprintable` raises; mutant: handler calls `_shown`.
*   E731: tests/test_bindguard.py:1639 `go = lambda self: 1` becomes `def go(self): return 1`. Builder runs `ruff check` and `ruff format --check` on every changed file before pushing (the CI lint step).
*   `_LAST_LOGGED` (receiver.py:54-67): guard with a `threading.Lock`; on every log do `pop(key, None)` then re-insert so eviction is by last use; eviction wrapped so no exception can escape before the 503 is written. Tests: 100 threads logging 100 distinct sets raise nothing; a key logged again within 60 s moves to the end and survives 64 other keys (fail-before: old code evicts it); mutants: lock removed, re-insert removed.
*   Design m4: a test that introspects the five classes and `Approvals` after pinning (read `__annotations__`, `vars`) and asserts the verdict is still stand-in (3.12 lazy entries); add the one-time touch of `__annotations__` at pin time so the pin includes it.
*   Codebase m4: three tests (forged same-name class, metaclass faking eq and hash, module dict not getattr) stay as pins; the commit message and CHANGELOG must NOT call them fail-before.
*   Nits accepted as free fixes (same push, no new review): bindguard.py:63-65 separate the two comments; tests/test_bindguard.py:1650 remove the odd always-true conjunct; defaults.py:324 wrap the long comment like KEYS (:325-327) and run `ruff format --check`; mutant numbering header note; B85 keep only if it has its own killer, otherwise delete with a note. n2 (pin fragility) is documented as fail-closed in standins.py.

### Declined
*   Codebase m6 last bullets "`vw is vi` to `==`" and "`type(ki) is str` in `_same_shape`": ACCEPTED as small mutants, not declined (add one mutant each). Nothing declined this round; no CONTEST, no ESCALATE.

## Handoff counts
*   Findings read: 3 Major (design) + 2 Major (codebase) + 11 minors + 8 nits.
*   PROPOSE FIX accepted: 5 Major + 11 minor + 6 nits.
*   CONTEST: 0. ESCALATE: 0. DECLINE: 2 nits (n3 numbering renumbering, n2 documented only).
*   Unaddressed: none in the brief; owner-only: none.

## ONE FIX BRIEF (small builder, batch 6, branch wip/cloud-pd-bind from d5537f99)
Order: Class C change 1 and 4 first (smallest), then B, then A, then D, then C changes 2 and 3. One push at the end with ALL findings fixed (no intermediate review).
Per class: file, change, test, mutant and fail-before are listed above. Rules for the builder:
1.  Fix at the choke point (`standins.py` scan, `requests.py` `__setattr__`/`__delattr__`, `receiver.py` `_recheck`); no per-call patching.
2.  Every new test must fail on d5537f99 except the three pin tests named in Class D. Record the fail-before list (test id and old-code message).
3.  Every new rule gets a mutant in tests/bind_mutants.py (unique search string, expect fragment found in the killer's message, no E402). Record the new total (was 130).
4.  Run ruff check, ruff format --check, bandit -ll, tools/server_scan.py and the check-no-handover-files script before pushing; do not commit handover/evidence, reviews or tickets.
5.  CHANGELOG: correct the three false sentences (`object.__setattr__` the one way left; never raises on hostile key; at most one log a minute) and state the allowlist, the fail-closed depth, the cache, the eager pin and the budget 503.
6.  Time box 60 minutes, checkpoint every 30; write NOTES with failures and gaps first.

## Round 6 and evidence
Round 6 IS needed (security path, no cap): a clean round means 0 Blocker and 0 Major from a fresh design reviewer and a fresh codebase reviewer on the batch 6 head (DELTA vs d5537f99 plus the whole Part 2 diff). Expect the reviewers to probe: other held-value shapes (iterators, generators, memoryview, bytearray, type objects), `Approvals` subclass and `__class__` assignment, the cache keyed on id after garbage collection, pin_all ordering at import.
Final-head evidence (independent EVIDENCE RUNNER, UTF8 Postgres with PGHOST and PGPORT set): full suite once; bind mutants all killed (about 135-145); tools/server_scan.py; stage mutants if touched; fail-before run of the new tests on d5537f99 src; ruff check and format; bandit -ll; gitleaks on origin/main..HEAD; check-no-handover-files; hostile probes for every Class A shape and the Approvals class patches against the head; a threaded test of `_LAST_LOGGED` repeated 20 times. The d5537f99 evidence (partial) goes stale when batch 6 lands; the runner abaa885e result is not needed for this decision.
