Status: resolved

# Goldfish Annotated Review Report, PD Part 2 (bind guard), round 9

**Target:** `/home/user/build/snap/pdbind-83cdb7a2/DIFF.patch` (full), head `83cdb7a293b7d5ba7d79bedaf3c8990fe99c4ee4`, money/approval path (no round cap).
**Inputs:** `pdbind-83cdb7a2-design-r9.md` (0 Blocker, 3 Major, 4 Minor, 1 Nit) and `pdbind-83cdb7a2-codebase-r9.md` (1 Blocker, 5 Major, 7 Minor, 7 Nit).
**Not available to the reviewers:** `models.py` and `runtime/tick.py` were not in the snapshot; the independent runner abd6af72 had not reported when this was written (its findings are an addendum for the builder). The full pytest and the complete mutant table of this head run on the laptop.
**Method:** every finding was checked against what the reviewers could read. No finding is contested. The two reviewers independently found the cost issue (design M3 = codebase 5) and the vacuous bookkeeping test (design m5 = codebase 2), so those are merged. 24 findings merge into 14 issues below.

## Handoff counts

- PROPOSE FIX accepted: 14 issues (covering all 3 + 1 Blocker/Major design/codebase items and all minors).
- CONTEST: 0. ESCALATE: 0.
- DECLINE: 0 as a whole; only item N-DECL below (Nit 13, note only) is recorded without code change.
- Remaining unaddressed: 0 in this report. Round 10 is REQUIRED (Blocker plus fail-open Majors on a money path).

## Prioritized findings

### Issue 1, Blocker, class TEXT (codebase 1, design m4)
CHANGELOG.md:16 says `allow_public_bind_reason` is "10 to 200 printable characters" but `bindguard.py:244-248` also requires ASCII (a breaking change, not stated). CHANGELOG.md:22 says a name is shown for "an identifier of at most 40 characters"; the code (`bindguard.py:207-212,223`) needs an ASCII identifier, and the `_HOST_CHARS` shown-rule (`bindguard.py:185-198`: letters, digits and `. : - _ [ ] %`, else "(unreadable)") is undocumented. AI suggestion: PROPOSE FIX.

### Issue 2, Major, class ATOM (design M1)
`standins.py:577` judges atoms at the last depth level by type only, while `_entered` (498-502) applies `plain_datetime` and `_path_slots_plain`. A datetime with a foreign tzinfo, or a Path holding a real object in a slot, at level 9 reads as plain, so a real service is called a stand-in (fail-open). AI suggestion: PROPOSE FIX.

### Issue 3, Major, class INSTANCE-SHADOW (design M2, m5, codebase 2)
`requests.py:58-73` `_runtime_ok` pins the Runtime class but Runtime has no `__slots__`/`__setattr__`, so `rt.on_decided = evil` or `rt.tick = ...` on the instance shadows the pinned class method. Only a class-level patch test exists (`test_bindguard.py:4322`). Also hooks, registry, audit, agents and limits are not judged. `hold_run_ids` is not recorded as an override and the evidence for that (test at `test_bindguard.py:4542`) is vacuous: it uses `SRC / "hadavin_sdk" / "approvals"` but `SRC` is already `src/hadavin_sdk`, so the glob is empty and nothing is asserted. A text grep of `approvals/*.py` would not prove `holder["rt"].hooks.hold_run_ids` is unreachable anyway. AI suggestion: PROPOSE FIX.

### Issue 4, Major, class COST (design M3, codebase 5)
`held_services_found` (`bindguard.py:153`) calls the verdict per held object with a fresh 250,000-node budget, and `_runtime_ok` then judges the same store, llm and detector again with fresh budgets. The runtime store is the same object as the held store, so it is scanned twice per unauthenticated POST. The CHANGELOG figures (40 ms, 100 ms) are per object, understating the per-request cost 2x-3x. AI suggestion: PROPOSE FIX.

### Issue 5, Major, class MUTANT-KILLER (codebase 3)
B232 (`bind_mutants.py:2100-2108`) sets `SCAN_NODES=100_000` while 1,000 rows cost 96,000-104,000 nodes: a coin flip that may survive. B219 is killed only if a Run dict has about 16 values; the charge is not asserted directly. AI suggestion: PROPOSE FIX.

### Issue 6, Major, class MUTANT-KILLER (codebase 4)
B57's `expect` "Regex pattern did not match" is pytest's own text; the kill comes from the pin check at `receiver.py:136,149`, not the exact-type guard at `receiver.py:127`. AI suggestion: PROPOSE FIX.

### Issue 7, Major, class TEXT-TEST (codebase 6)
`test_bindguard.py:4517-4538` (CHANGELOG pin list vs code) is nearly vacuous: it only checks that names like Run, Plan, Card appear somewhere. "20 of 22" is not tied to the code constants and "1,000 mixed rows" is compared with a local constant. AI suggestion: PROPOSE FIX.

### Issue 8, Minor, class LIVE-CLASS (codebase 7)
The `live_class` change (`isinstance(cls, type)` to `issubclass(type(cls), type)`, `standins.py:199-208`) has no test or mutant row for a spoofed `__class__`. AI suggestion: PROPOSE FIX.

### Issue 9, Minor, class MUTANT-TABLE (codebase 8, 20 and the pin note)
B210, B230, B231 apply the identical edit at `requests.py:145`; B31 and B221 the same edit; B212 and B213 have the same expect and killer. The nine equivalent serve-slot rows are argued only in the builder's report. Two tests pass on 3db352f5 (`test_a_text_or_number_subclass_is_not_a_plain_atom` B137, `test_every_build_argument_...` B235) but are not labelled as pins. B224 is missing from the table header note. AI suggestion: PROPOSE FIX.

### Issue 10, Minor, class TEXT (codebase 9, 10, nits 14, 16, 18, 19)
Stale comments and names: `standins.py:192-193` and `:18` ("pin taken at the first question"), `test_bindguard.py:3973-3977` ("the three", now two), the dead isdecimal-replaces-isdigit comment at `bindguard.py:223-227`, the dead `(...) if False else (...)` at `test_bindguard.py:4256` (and in `test_models_now_with_its_code_replaced_is_counted`), the unclosed server in the serve-refusal test, `_NumberWithCode(int): pass` name without a code, and the unstated deviation of the over-budget label ("over budget (too many values to check)"). `reason_problem` calls `reason.strip()` after an `isinstance(str)` check; a str subclass would run its own `strip`. AI suggestion: PROPOSE FIX.

### Issue 11, Minor, class OUTAGE-GUARD (codebase 12)
The eager pinning of 13 pydantic classes is exercised only on Run in a fresh interpreter. A deferred build replacing `__pydantic_validator__` could make every store read as real (503 outage). AI suggestion: PROPOSE FIX (fresh-interpreter test that instantiates all 13).

### Issue 12, Minor, class PY-3.14 (codebase 11)
Python 3.14 is unverified: Path slot `_info` (PathInfo/DirEntryInfo) read as real would 503; the B158 equivalence on 3.14 (annotations cache) is assumed. AI suggestion: PROPOSE FIX (check on 3.14 if an interpreter exists in the cloud environment, otherwise state in the CHANGELOG and the evidence file that it is unverified and goes to the laptop).

### Issue 13, Minor, class CLOCK/GLOBALS (design m6, m7, codebase nit 15)
`real_now` judges the clock, then `receive` (`requests.py:357`) runs `self.clock().timestamp()` and `Approvals.clock` is re-settable: the check-versus-use race is named for the channel only. `models.now` is trusted by `__code__` identity but its globals (`models.datetime`, `models.UTC`) and defaults are not pinned. AI suggestion: PROPOSE FIX: pin them (globals compared by identity against the values at import) or state both as limits in the CHANGELOG with the in-process threat-model sentence the lead already approved. Prefer the pin for `models.datetime` and `models.UTC` (cheap, reads no foreign code) and the stated limit for the clock race.

### Issue 14, Nit-to-Minor, class MUTANT-TABLE (codebase nit 17 and the B224 note)
Covered by issues 9 and 10. Recorded for the ledger as merged.

### N-DECL, Nit (codebase 13)
`plain_datetime` treats every datetime as real unless tzinfo is None or `datetime.UTC`; pydantic-parsed aware datetimes carry pydantic-core's TzInfo. It fails closed and the rule is stated. DECLINE with no code change; the CHANGELOG sentence from issue 1 mentions it in one line.

## ONE FIX BRIEF (single small builder, batch 10; fast-forward only onto `wip/cloud-pd-bind`)

Rules for the builder: fix by CLASS at the choke point; no suppressions; no weakened or deleted tests; fake credentials built from parts; `_BUILD_TOKEN` reachable from in-process code stays inside the threat model (no code change); Part 6 must not call `is_stand_in` until Part 2 merges. Cloud limits: no full suite, at most 2 heavy processes, focused tests plus the focused mutant rows; set `PYTHONPATH` to the worktree `src` and print the module path before any run (venv hazard). Every new test must be shown FAILING on 83cdb7a2 (run on the old source) and passing on the new; every new mutant row must be shown killed by its named test.

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | ATOM | `standins.py` around line 577: at the depth limit call the same atom judge `_entered` uses (`plain_datetime`, `_path_slots_plain`, and the exact-type text/number check) instead of a type-only test. Put the judge in one helper used by both places so they cannot drift. | Depth-9 datetime with a foreign tzinfo reads as real; depth-9 Path with a real object in a slot reads as real; depth-9 plain datetime and plain Path stay plain; str and int subclasses at depth 9 are real. | One row for each of the helper's three checks at the last level (replace the call with the type-only test; drop the datetime check; drop the path check). | Run the new tests on 83cdb7a2: they must fail there. |
| B | INSTANCE-SHADOW | `requests.py:58-73` `_runtime_ok`: besides the class pin, require the instance `__dict__` keys to equal exactly the set `Runtime.__init__` writes (derive the set from a probe instance built at import, or write it as a pinned constant checked by a test against `__init__`), and also judge hooks, registry, audit, agents and limits (same verdict as store/llm/detector). Reject any instance key equal to a class method name. `hold_run_ids`: record it in `overrides` in the Part 6 style (a named override with a reason) AND add a test on a real Runtime proving `holder["rt"].hooks.hold_run_ids` replaced by a non-plain callable makes the verdict real, so it cannot be reached from a POST. | Instance `rt.on_decided = f`, `rt.tick = f`, an extra instance key, each judged real; replacing `hooks.hold_run_ids` judged real; a normal Runtime still plain. | Rows: drop the key-set check; drop each of the five newly judged members; drop the hold_run_ids override record. Add one row for the spoofed `__class__` (Issue 8). | Instance-shadow tests fail on 83cdb7a2. |
| C | BOOKKEEPING TEST | Fix `test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service` (`test_bindguard.py:4542`): use `SRC / "approvals"`; assert the glob is non-empty first and fail if empty; also assert the recorded-override names equal the `build()` parameter list (9). Label it a pin in the docstring if it passes on the old source. | The test itself, plus a self-check that fails when the path is empty. | Existing B235 stays; add a row that points the glob at a wrong path. | Show the test failing on the empty-glob variant. |
| D | COST | `bindguard.py:153` and `requests.py:58-73`: share ONE budget object across `real_now`, `held_services_found` and `_runtime_ok` per request, or reuse the held store's verdict for `runtime.store` so the store is scanned once. State the per-request worst case in the CHANGELOG as measured on this machine (time the whole pre-authentication path with a worst-case holder, not one object). | A call counter: the runtime store is scanned once per request, not twice with a fresh budget; and the per-request worst case with all objects at the budget limit stays below the stated figure. | Row: give `_runtime_ok` a fresh budget again; row: remove the shared budget from `real_now`. | Counter test fails on 83cdb7a2. |
| E | MUTANT KILLERS | `bind_mutants.py`: B232 use `SCAN_NODES` about 60,000 (clearly below the measured 96,000 to 104,000) and re-measure in the evidence; B219 assert the charge directly (a number of nodes charged for a Run dict) instead of relying on about 16 values; B57 `expect` names the intended exact-type guard text (`receiver.py:127`) and a second row for the pin check at `receiver.py:136,149`; B212 and B213 get distinct expects and killers; B210/B230/B231 and B31/B221: give each its own killer or merge the rows and say so in one comment; add a comment block arguing the nine equivalent serve-slot rows (`_audit_sink` and `_registry` pinned by B200 and B207); add B224 to the header note; docstrings label the tests that pass on 3db352f5 as pins (B137 test, the B235 test). | The rows' own killers. | The row edits above. | Each re-pointed row shown killed on the final head. |
| F | TEXT | CHANGELOG: the ASCII rule for `allow_public_bind_reason` (breaking, say so), the identifier rule (ASCII), the `_HOST_CHARS` shown-rule with "(unreadable)", the over-budget label deviation, the per-request cost (Issue 4), the pydantic-TzInfo note (N-DECL), the Python 3.14 status (Issue 12), clock race and `models.now` globals (Issue 13). Fix the stale comments (`standins.py:18`, `:192-193`; test docstring "three" to the real count; dead isdecimal comment; dead `if False` expressions at `test_bindguard.py:4256` and in `test_models_now_with_its_code_replaced_is_counted`; rename `_NumberWithCode` or give it a code; close the server in the serve-refusal test with try/finally; `reason_problem` check exact `str` type before `strip`). Replace the CHANGELOG-vs-code test (`4517-4538`) so it parses the pin-list sentence and ties the key count (22) and the pinned count (20) and the 1,000-row count to the code constants (`PIN` table length, `pin_all` / `pin_module` split, the row-count constant used by the cost test). | The new parsing test. | Row: change the code count by one and the test must fail. | Fails on 83cdb7a2 for the count tie (the old test passes). |
| G | OUTAGE-GUARD and LIVE-CLASS | New fresh-interpreter test (subprocess, `-I`) that instantiates all 13 pinned data classes, then asks for the verdict of a normal store and requires "plain" (a 503 outage guard). Test for a spoofed `__class__` on `live_class` (an object whose `__class__` property returns a type). | Both. | Row for the `live_class` revert to `isinstance`; row for skipping the eager pin of one class. | Both new tests fail on 83cdb7a2 where they test new behaviour; pins are labelled. |
| H | PIN `models` | Pin `models.datetime` and `models.UTC` by identity next to the existing `models.now` `__code__` check (read by slot or identity, no foreign code run). | Replacing either global makes the clock read real. | Row for each. | Fails on 83cdb7a2. |

Builder reports once when ALL of A to H are done, with the new head sha. No intermediate review pushes.

## Round 10 and evidence for the final head

- **Round 10 is required.** Reason: one Blocker (text contradicts code) and Majors 2 and 3 are fail-open by an in-process value, on a money/approval path (no cap).
- **Cloud evidence (runner, records only):** focused tests for atom judge, instance shadow, cost counter, CHANGELOG parse, outage guard on Python 3.12 and 3.13 (and 3.14 if an interpreter exists); the new and changed mutant rows only plus a 60-row sample; the per-request timing measurement on the cloud machine; "fails on 83cdb7a2" proof for each new test. The runner abd6af72 findings on 83cdb7a2 are an addendum to this brief and become ledger rows when they land.
- **RUN ON LAPTOP (final head only):** hadavin-sdk `<new head sha>` `pytest -q` full suite plus the COMPLETE bind_mutants table (227 rows now; 227 plus the new rows after batch 10; 226 on 3.14 before additions) and the timing/perf tests alone.
- Ledger rows are added by the caller. Row ids should carry the prefix PDBIND-r9-n for the 14 issues above.
