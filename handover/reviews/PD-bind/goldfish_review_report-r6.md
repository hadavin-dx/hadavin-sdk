Status: resolved

# Goldfish Annotated Review Report (round 6, Part 2 bind guard, head b8c88cac)

**Target:** `/home/user/build/snap/pdbind-b8c88cac/DIFF.patch` (full file). SECURITY path: no round cap, a clean round is needed. Automated mode, recommended option on every item. Source reports: `pdbind-b8c88cac-design-r6.md`, `pdbind-b8c88cac-codebase-r6.md`. The independent runner a505c184 had not reported when this was written; nothing here relies on it.

Checked by the resolver against the code on `origin/wip/cloud-pd-bind` (`models.py`, `channel.py`, `standins.py`, a grep for siblings):
- Model classes are pydantic `BaseModel`s with `extra="forbid"` and no private attributes declared. So `__pydantic_extra__` and `__pydantic_private__` are empty and all state a row holds is in `__dict__` (design M2: not a defect today; pin it so it stays true).
- Depth count (codebase N2) is confirmed by counting: instance dict = level 1, `_approvals` dict = 2, `ApprovalRequest` = 3, `steps` list = 4, `ChainStep` = 4 entered, so its values (`approver_ids` list) land at level 5 and read as real. A store holding one approval request would answer 503 on every request of a public bind. Fail-closed, but wrong.
- `FakeChannel.max_card_chars` is a declared `int` field (`approvals/channel.py:71`); its value was not read (builder to check).
- Sibling sweep: outside `standins.py` the only `type(x) in` / `kind in` hit under `src` is `guard/redact.py:902` (`kind in self.counters`, a dict of the module's own labels; not a held value, not attacker-controlled). No other site.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` and `codebase`] - Severity: Blocker (B1, found by both reviewers)
*   **Affected Scope:** src/hadavin_sdk/standins.py lines 266, 268, 273, 305 (`_entered`, `_holds_real`)
*   **Discrepancy Description:** the allowlist is judged by `kind in <frozenset or tuple>` where `kind = type(value)` of a held value. A metaclass defining `__hash__` and `__eq__` (always True) makes a foreign class pass as an atom or as a plain container, so `MemoryStore().client = Evil()` reads as a stand-in.
*   **Rationale:** the choke point of the whole guard; the docstring and CHANGELOG claim exact-type identity, which the code does not keep. The existing test only spoofs the top-level object.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid and reproducible by reading CPython's membership rule (reflected `__eq__` of a `type` subclass runs first; frozenset needs a matching hash). Class: identity must never be decided by hash or equality of a type the held value controls.
*   ***Proposed Edit:***
    *   Location: `_entered`, the final-level loop in `_holds_real`, `_values` (the `issubclass` calls are on the real builtin types, which is safe because `issubclass(kind, base)` does not call `kind.__eq__`; still confirm `__subclasscheck__` of a metaclass on `kind` is not consulted: `issubclass(kind, dict)` asks `type(dict).__subclasscheck__`, i.e. `type`, not `kind`'s metaclass, so it is safe)
    *   Change: add one helper `_is_one_of(kind, types) -> bool` that returns `any(kind is t for t in types)` (iterating a tuple built once from the frozensets, never `in`); use it at all four sites; first require `type(kind) is type` (or `type(kind) is ABCMeta`/`EnumType` only for the listed leaf enum, which is matched by identity) so a type with a foreign metaclass reads as real before any comparison. Keep `_ATOMS`, `leaf`, `data` as frozensets of classes only for building the tuple. Docstring and CHANGELOG then true.

### [Issue 2] [`codebase`] - Severity: Major (N2; design M1 second half and M2)
*   **Affected Scope:** standins.py `SCAN_DEPTH = 4`, `_holds_real` lines 285-307; tests `_populated_store`
*   **Discrepancy Description:** depth 4 cannot cover a store holding an approval request with steps; no test populates plans, approval requests or dead letters.
*   **Rationale:** the claim "model rows the stand-ins really hold" is unproven and a plain demo store would be refused on a public bind (503 on every request).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** confirmed by counting above. Decision (recommended): raise the scan depth for held values to 8 (own constant `SCAN_DEPTH_VALUES = 8`; the detector-list nesting limit keeps its own constant) and keep the fail-closed tail rule; do NOT make data classes free of depth (that would let a cycle of data objects run to the budget instead of failing early). The budget (100000 nodes) stays the hard bound.
*   ***Proposed Edit:***
    *   Location: standins.py constants and `_holds_real`; tests/test_bindguard.py
    *   Change: constant as above, message updated; a test that fills a `MemoryStore` with one of each model the stand-ins keep (run, plan with target, gate decision, approval request with two chain steps, approval decision, dead letter, tick state, tool-call record, kill switch) and asserts `is_stand_in` is True; a test that nests a real object one level deeper than the new limit and asserts False; pin test that every class in `_DATA_CLASSES` has `model_config["extra"] == "forbid"` and no `__private_attributes__` and no `__slots__` (so `__dict__` is all the state), failing if one is added.

### [Issue 3] [`codebase`] - Severity: Major (N3)
*   **Affected Scope:** standins.py lines 234-243 (`_values`) and 295-299
*   **Discrepancy Description:** `_values` copies a whole container into a tuple before any budget check; one big list referenced 1000 times builds 1000 large tuples; cost is not bounded by `SCAN_NODES` and the scan runs before authentication on every POST.
*   **Rationale:** the docstring claims a bounded cost; a held-value structure (own or hostile) can exhaust memory and CPU of the receiver.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid; class: every read of attacker-shaped size must be charged before it is made.
*   ***Proposed Edit:***
    *   Location: `_values`, `_holds_real`
    *   Change: `_values(container, budget)` reads the size with the builtin (`dict.__len__`, `list.__len__`, `tuple.__len__`, `set.__len__`, `frozenset.__len__`, `deque.__len__`) and returns `None` (reads as real) when the size is larger than the remaining budget; otherwise copies. `_holds_real` charges the size of every container when it is entered (not only per value visited), so a shared container referenced 1000 times is charged 1000 times. Tests: one `list(range(10**6))` referenced 1000 times answers False (real) quickly without allocating more than a small multiple of the budget (measure with `tracemalloc` peak under a stated bound); a dict with 10**6 keys at the top level; the legitimate populated store still passes. Mutant: remove the size check.

### [Issue 4] [`codebase`] - Severity: Minor (N4, N5, N6) and Nit (N7)
*   **Affected Scope:** tests/bind_mutants.py B87, B117, B52, B119, B158; test names and counts; `RunState` leaf; `FakeChannel.max_card_chars` test
*   **Discrepancy Description:** B87 and B117 are guarded by two layers and named as if by one; "3 of 22 pass on old code" under-counted; B158 equivalent on 3.14 and later; cached-int risk in the `max_card_chars` test; enum member `__dict__` not scanned; test name says five classes but checks seven; count of `noqa: BLE001`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid; each is small. `RunState` members: treat an enum member as a leaf only when `kind is RunState` AND `value is` one of `RunState.__members__.values()` AND its `__dict__` holds only the enum's own keys (`_value_`, `_name_`, `__objclass__`, `_sort_order_`); otherwise real.
*   ***Proposed Edit:***
    *   Location: tests/bind_mutants.py, tests/test_bindguard.py, CHANGELOG.md, standins.py
    *   Change: rename B87 and B117 to say "second layer also refuses; this row pins the log text" and name the other layer; list every new test that passes on old code with its reason (threads, no-cache, class-level-container, pinned-attribute, text-subclass key) in NOTES; B158 docstring says "3.12 and 3.13" and the row is marked equivalent on 3.14 and later with a skip reason; the `max_card_chars` test uses a value above 256 (or `object()` sentinel with `is` check) and asserts the monkeypatch took effect; rename the class-level-container test to "seven classes" and cover mutable instances by walking `vars(cls)` for anything not a function, descriptor, class or atom; state the real count of `noqa: BLE001` (6) in NOTES.

### [Issue 5] [`design`] - Severity: Minor (M1 wording, M3, M4, M5, M6)
*   **Affected Scope:** CHANGELOG.md lines 12, 18, 23; receiver.py:137-154, 169
*   **Discrepancy Description:** over-budget outage not stated; pin at first question; check-versus-use not stated; `on_decided` and `clock` not read; `serve()` can raise an error other than `BindRefused`.
*   **Rationale:** honest wording and one type of refusal.
*   ***AI Suggestion:*** PROPOSE FIX (M3 accepted as stated: first question is `serve()` itself; wording kept, with a sentence that the window is import to `serve()`)
*   ***Justification:*** M5 is the one that matters: a callable that runs after a valid signature can close over a real service, so say plainly that the guard does not read it and that a real service held ONLY there is not seen; and add a check that `on_decided` is None or a plain function of the core's own module (identity against a small allowlist), else the held-service answer is real. If that check is too wide for current callers, state the limit in the page and the CHANGELOG as an exception 2(a)-style written limit with the next step.
*   ***Proposed Edit:***
    *   Location: CHANGELOG, receiver.py `serve`, `_recheck`
    *   Change: wrap `Approvals.held_services(approvals)` in `serve()` in the same try as the other refusals and raise `BindRefused` with the fixed text; CHANGELOG: one sentence each for the over-budget outage (503 until the store is smaller, `serve()` refused at start), check versus use (single-threaded stdlib server; another thread swapping a channel between check and use is not covered), `on_decided` and `clock`; split line 23 into short lines; remove the stray blank line at bindguard.py:63-65.

### [Issue 6] [`design`] - Severity: Nit
*   **Affected Scope:** "154 of 154" count; stray blank line
*   **Discrepancy Description:** the count is the builder's claim; blank line.
*   ***AI Suggestion:*** DECLINE (count) / PROPOSE FIX (blank line, in Issue 5)
*   ***Justification:*** the independent runner re-runs the table; nothing to change.
*   ***Proposed Edit:*** none for the count.

## ONE FIX BRIEF (small builder, branch `wip/cloud-pd-bind` from b8c88cac, no force-push, nothing under handover/)

| Class | File and change | Test | Mutant | Fail-before |
|---|---|---|---|---|
| A identity-only judgement (Issue 1) | standins.py: `_is_one_of` helper (identity over a tuple, `type(kind) is type` first); use at the four sites; fix docstring and CHANGELOG sentence | held spoof (metaclass with `__hash__` of int and `__eq__` True, with a fake client attribute) at level 1, as a dict key, at the depth tail, inside a nested `AnyOf` member, in FakeLLM, FakeChannel, MemoryStore state; each must read as real | 4 rows: each site back to `in`; one row removes the `type(kind) is type` check | new tests must FAIL on b8c88cac src |
| B depth and populated store (Issue 2) | `SCAN_DEPTH_VALUES = 8`, detector nesting keeps its own limit; message text | populated store with one of each model; depth-plus-one real object is refused; pin test on `extra="forbid"`, no private attributes, no `__slots__` in every `_DATA_CLASSES` class | row: depth back to 4 (killed by the populated-store test); row: tail rule removed | populated-store test fails on old code (503) |
| C cost before copy (Issue 3) | `_values` charges and checks size with the builtin `__len__` before copying; containers charged at every visit | shared huge list (10**6 items, 1000 references) and a 10**6-key dict answer real within a stated memory bound; legitimate store passes | row: size check removed; row: charge only on first visit | fail on old code (memory bound exceeded) |
| D minors (Issues 4, 5) | `RunState` member check; `on_decided` check or stated limit; `serve()` try; CHANGELOG sentences; row names; B158 note; `max_card_chars` value; test names | `RunState` member with an attribute hung on it reads as real; `on_decided` closing over a fake real service on a public bind; `serve()` with a hostile mapping raises `BindRefused` | rows for `RunState` check, `on_decided` check, `serve()` try | each new test fails on old code or is listed as a pin that passes on old code with the reason |

Gates the builder runs once at the final head: ruff check and format --check, bandit -ll, scan_repo, `tools/server_scan.py`, the full pytest once via heavy.sh with a priority, `tests/bind_mutants.py` (all rows) and `tests/stage_mutants.py` (37), gitleaks, `check-no-handover-files.sh wip/cloud-pd-bind`. Box 60 minutes, checkpoint every 30.

## Round 7 needed? YES.
Security path, Blocker raised this round; a clean round (0 Blocker and 0 Major from both reviewers) is required. Evidence the final head needs (independent runner, UTF8 Postgres with PGHOST and PGPORT in the server environment, own folder): full pytest with every skip grouped (explain the 457/458 skips: database and Vault tests without a DSN, confirm against CI), bind mutants (all rows), stage mutants (37), fail-before against b8c88cac for every new test, the hostile probes (metaclass spoof held at four places, populated store 503 check, 10**6 shared list memory peak, hostile key label, 100 threads), lint, bandit, scan_repo, server_scan, gitleaks, handover-files check.

## Handoff counts
Accepted fixes (PROPOSE FIX): 5 issues (Blocker 1, Major 2, Minor groups 2). Contested: 0. Escalated: 0. Declined: 1 (Nit: the mutant count claim). Remaining unaddressed: 0 (all fixes are in the brief, none applied yet; source and snapshot untouched).
