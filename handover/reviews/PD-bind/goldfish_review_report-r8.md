Status: resolved

# Goldfish Annotated Review Report: PD Part 2 (public-bind refusal, stand-in guard), round 8

**Target:** `/home/user/build/snap/pdbind-3db352f5/DIFF.patch` (full), head 3db352f5f23dbe1117b3286a1d315baa68c80346. Path: SECURITY (no round cap). Mode: automated; every valid finding is PROPOSE FIX and auto-accepted into the one fix brief below. No source, snapshot or ledger file was edited by this step.

**Handoff counts:** findings 19 (design 6, codebase 14 with overlap: 2 duplicates merged) | PROPOSE FIX accepted: 17 | CONTESTED: 0 | ESCALATED: 0 | DECLINED (Nit, recorded, no fix): 2 (C-N6 partly, C-N9 partly, see below) | remaining unaddressed: 0 | Round 9 required: YES.

## Facts the builder and the reviewers get (not a verdict)

- Independent runner (RESULTS.md at handover/evidence/PD-bind/3db352f5/): full pytest 10866 passed, 2 skipped; bind mutants 198 of 198 good (189 killed, 9 crash, 0 bad); stage mutants 37 of 37; lint, bandit, gitleaks, handover check all exit 0. Hostile probes (metaclass spoofs 13/13, depth 1-9, all 11 `Approvals` slots, holder bypass, hostile keys, 100 threads) found no bypass. The reviewers found their issues by reading, not by running: the Blocker is a code reading the probes did not try (a clock datetime holding a hostile tzinfo).
- Builder admitted: 14 of 37 new cases pass on old code, 4 without a mutant row. Runner counted 13 of 38 and 2 without any killing row (the two Counter tests). The class-name-that-raises test was never re-run on old code by the builder (runner: killed by B59 only). Seven serve-slot cases are killed only by B175.
- CHANGELOG-vs-code tests skip in the mutation copy (so no mutant row can fail them; they have the separate ten-change control the runner ran).
- Cost of the full bind-mutant run is 12 min 51 s here; row B197 reached about 7.9 GB resident and about 8 minutes before its own timeout.
- `_BUILD_TOKEN` is importable by in-process code. That is inside the threat model (code already running in the server process can do anything the server can). One plain sentence in the CHANGELOG states it; no code change.

## Prioritized findings

### [Issue 1] [design Blocker 1 + codebase M1] - Severity: Blocker
*   **Scope:** requests.py 116-121 (`_is_core_clock`), 329 (`receive` calls `self.clock().timestamp()` before the signature check), `decide` clock compare; standins.py 144-157 (datetime listed as a plain atom), 425-426 (`_no_instance_state` returns () for datetime).
*   **Discrepancy:** `fixed_clock(datetime)` is trusted by exact type; a datetime carrying a hostile `tzinfo` runs `utcoffset` (foreign code) on every unauthenticated POST. The scan calls it a stand-in.
*   ***AI Suggestion:*** PROPOSE FIX (class: identity/type-only trust of a value whose content runs code).
*   ***Justification:*** Valid. Same class as r7 Issue 1: type judged, content not. The runner probes covered datetime subclass and lambda but not a tzinfo-carrying exact datetime.
*   ***Proposed Edit:*** see Fix class 1.

### [Issue 2] [codebase B1 + design 5] - Severity: Blocker
*   **Scope:** CHANGELOG 9 and 270; standins.py 115 (`_PINNED_KEYS`), 123 (`_DATA_CLASSES`), 263-273 (`pin_all`), 427, 440; receiver.py 200.
*   **Discrepancy:** CHANGELOG says model classes are pinned at import; code pins the 12 pydantic rows plus `Card` at the first scan that meets an instance, `RunState` never, `Runtime` by identity at first sight. A patch to `Run` between import and the first question is absorbed. Stale comment says `FakeSecretProvider` is pinned "at the first question".
*   ***AI Suggestion:*** PROPOSE FIX (class: text claims pin moment the code does not have; pinned-late class).
*   ***Justification:*** Valid and a real gap, not only text (order-dependent test pollution; a pre-first-question patch is accepted).
*   ***Proposed Edit:*** see Fix class 2.

### [Issue 3] [design Major 2 + codebase M2] - Severity: Major
*   **Scope:** requests.py 49-76 (`_core_runtime_class`, `_RUNTIME_PIN`, `_holder_ok`).
*   **Discrepancy:** a hand-built `Runtime` (real store, model or hooks) in the holder is believed by class identity; a later `Runtime.on_decided = evil` is unseen.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** Valid. `_BUILD_TOKEN` is not the guard here (in-process code is in the threat model); the guard is that the holder contents are data-judged. Reuse `standins.is_pinned_instance(obj, key)`; remove the ad hoc `_RUNTIME_PIN`.
*   ***Proposed Edit:*** see Fix class 2.

### [Issue 4] [design Major 3 + codebase M3] - Severity: Major
*   **Scope:** receiver.py 161; standins.py 92-96 (`SCAN_NODES` 100000, `STAND_IN_WEIGHT` 50); CHANGELOG 270; bindguard.py 155-158 (over-budget label).
*   **Discrepancy:** up to 100000 nodes per unauthenticated POST, no wall-time figure; weight 50 means a store of about 1500-2000 data rows is over budget and the public bind answers 503 forever (CHANGELOG says "more than 100000 values"); "over budget" label is order-dependent.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** Valid. No cache (declined earlier; a cached verdict is a stale pass token). Measure, then set the weight so a realistic made-up demo store passes, and state the effective figure.
*   ***Proposed Edit:*** see Fix class 3.

### [Issue 5] [codebase M4] - Severity: Major
*   **Scope:** bind_mutants.py 1458-1483 (B161-B163); test_bindguard.py 3014-3050, 3061-3065.
*   **Discrepancy:** each row reverts several guards at once; the single identity swap is never pinned; `_spoof` always adds a `client` attribute so the second layer masks the first. CHANGELOG "each reverts one guard" is false.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Proposed Edit:*** see Fix class 4.

### [Issue 6] [codebase M5] - Severity: Major
*   **Scope:** bind_mutants.py 1246-1254 (B137), test_bindguard.py 2513.
*   **Discrepancy:** B137 expects a control message, so it is killed by collateral damage at the first shape.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Proposed Edit:*** see Fix class 4.

### [Issue 7] [runner facts + codebase N8] - Severity: Major (mutant-table class, evidence from the runner)
*   **Scope:** two Counter tests with no killing row; seven serve-slot cases killed only by B175 (B200 pinned to one case); B195/B197; `_counting` swallowed AssertionError (test_bindguard.py 3771-3785); B197 8 min and 7.9 GB.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** Fail-before honesty: tests that pass on old code and no row fails them are pins, not proofs; B197 as built cannot run in a 2-heavy-process container.
*   ***Proposed Edit:*** see Fix class 4.

### [Issue 8] [codebase N1] - Severity: Minor
*   serve() does not check the pin at start (receiver.py 124-143). PROPOSE FIX: call `is_pinned_instance` in the same try as the slot reads; test: `Approvals.held_services` patched before `serve` raises `BindRefused`.

### [Issue 9] [codebase N2] - Severity: Nit
*   Depth wording off by one (standins docstring line 36, line 91 comment, CHANGELOG 270 versus code 460-478 and test 3215-3217). PROPOSE FIX: one sentence, derived from `SCAN_DEPTH`, plus a test that parses the sentence number.

### [Issue 10] [codebase N3] - Severity: Minor
*   Refusal-text filter narrower than documented (bindguard.py 110, 195, 208, 245). PROPOSE FIX: `_is_plain_word` adds `.isascii()`; `_is_plain_name` uses `isdecimal()` plus `.isascii()`; `_shown(host)`, `_shown(bind)` and the reason go through the same plain-word-or-fixed-label rule; fuzz test with a Cyrillic confusable, a superscript digit, a host `x, held channel: FakeChannel`.

### [Issue 11] [codebase N4 + design 4] - Severity: Minor
*   Slots of allowlisted atoms not scanned (`PosixPath._str`). PROPOSE FIX: judge `Path` through `str(value)`-free state: require slots `str`, `list` or None for `Path` atoms, or reject `Path` atoms whose class has writable slots holding non-plain values; test `p._str = RealClient()` reads as real.

### [Issue 12] [codebase N5] - Severity: Nit
*   `defaultdict` factory wording (standins.py 173). PROPOSE FIX: CHANGELOG lists the six exact factories from `_DEFAULT_FACTORIES`, derived by the existing code-vs-text test.

### [Issue 13] [codebase N6] - Severity: Minor (PROPOSE FIX in the clock class)
*   `models.now` trusted by identity (`_is_core_clock`, requests.py 119). PROPOSE FIX inside Issue 1: also compare `now.__code__` to a pinned code object taken at import (same way the closure is pinned).

### [Issue 14] [codebase N7] - Severity: Minor
*   r7 CHANGELOG items missing (RunState member-key check; size-before-copy rule). PROPOSE FIX: add the two sentences; the code-vs-text test lists them.

### [Issue 15] [codebase N8] - Severity: Minor
*   `_counting` raises AssertionError inside code that `verdict()` catches as "real"; B195 reaches its expect text by accident. PROPOSE FIX in Fix class 4: record counts in a list, assert after the call.

### [Issue 16] [codebase N9] - Severity: Nit (partly DECLINE)
*   `_one_cell` annotation and `_NONE` order (fix), `_EPOCH` (fix: build the code object once, comment why), `dict.get(holder, "rt")` hostile key `__eq__` (fix; same as design 6), `live_class` uses `isinstance(cls, type)` (fix: `issubclass(type(cls), type)`). DECLINE only the style point on `_EPOCH` naming. Recorded.

### [Issue 17] [design Nit 6] - Severity: Nit
*   Hostile str key in `_holder_ok`; `Card` skips `_data_state_ok`; `hold_run_ids` and `timeout_s` not in overrides. PROPOSE FIX: read the one holder key with `next(iter(holder))` after an exact-str check, no `==`; run `_data_state_ok` for `Card`; decide `hold_run_ids` and `timeout_s` in the Part 6 style (record them in overrides, since a POST can reach `hold_run_ids`), with a signature-versus-`OVERRIDES` test.

### [Issue 18] [runner finding] - Severity: Minor
*   Builder-versus-runner count mismatch (14 of 37 versus 13 of 38). PROPOSE FIX: the builder lists every new case by name in NOTES with its fail-before result from `fb-summary.txt`; no claim of "N pass on old code" without that list.

### [Issue 19] [CHANGELOG boundary, lead order D] - Severity: Minor
*   State the `_BUILD_TOKEN` boundary. PROPOSE FIX: one sentence in the CHANGELOG: "The build token can be imported by code already running in the server process; that code is already inside the trust boundary, and the guard does not try to stop it."

## ONE FIX BRIEF (batch 9, one small builder, fast-forward only to wip/cloud-pd-bind, no handover files, no pyproject.toml or uv.lock change)

Rules for the builder: fix by class at the choke point; for every new test run it against the 3db352f5 `src` and list which fail (name by name); a test that passes on old code is labelled a pin, not a proof, and has a mutant row or says why not; no claim without the list. Focused tests only while building; do NOT run the full suite or the full bind-mutant table here (see Evidence).

**Fix class 1: clock and every exact-type atom judged by type only**
- File: requests.py `_is_core_clock`; standins.py datetime atom (144-157, 425-426).
- Change: a clock datetime is accepted only if `tzinfo is None` or `tzinfo is datetime.UTC` (identity); `models.now` also has its `__code__` pinned at import. In the scan, a datetime atom is judged by the same helper (tzinfo None or UTC by identity, else real). Order of calls in `receive`: nothing may call into a value's methods before the signature check unless the value was judged (comment the order; test it with a counting tzinfo).
- Tests: tzinfo subclass whose `utcoffset` records a call: `serve()` refuses and no POST ever calls it (count 0); via `build(clock=...)` too; datetime with `timezone(timedelta(0))` subclass, with `ZoneInfo`-like object (read as real); controls (None, `UTC`, `models.now`) stay served.
- Mutants: one row each: tzinfo identity test removed; datetime scan branch removed; `now.__code__` pin removed.
- Fail-before: all new cases fail on 3db352f5 src (expected: yes for the tzinfo ones).

**Fix class 2: classes pinned eagerly, by shape**
- File: standins.py `_PINNED_KEYS`, `pin_all`, `pin_module`; requests.py `_core_runtime_class`, `_RUNTIME_PIN`, `_holder_ok`; receiver.py `serve`.
- Change: add the 12 pydantic rows, `Card`, `RunState` and `Runtime` as keys of the eager pin (`pin_all` runs at receiver import); remove `_RUNTIME_PIN` and the first-sight code; `_holder_ok` calls `standins.is_pinned_instance(rt, _RUNTIME_KEY)` and judges the instance state with the scan (a hand-built `Runtime` holding a real store is real). `serve()` calls `is_pinned_instance` for `Approvals` in the one try with the slot reads. Fix the stale `pin_all` comment and standins.py lines 8-12 and 28-30, and CHANGELOG 9 and 270 to what the code does.
- Tests: `Run.some_attr = evil` after import and before the first question reads as real (503, fail); `Runtime.on_decided = evil` likewise; hand-built `Runtime(real_store, ...)` in `make_on_decided({"rt": ...})` is refused; `Approvals.held_services` patched before `serve()` raises `BindRefused`; a test that every key in the CHANGELOG pin list equals `_PINNED_KEYS`.
- Mutants: remove one key from `_PINNED_KEYS` (one row for the data classes, one for `Runtime`, one for `RunState`); remove the `serve` pin call.
- Fail-before: new cases fail on 3db352f5 src.

**Fix class 3: pre-authentication cost, measured**
- File: standins.py `SCAN_NODES`, `STAND_IN_WEIGHT`, `_Budget`; bindguard.py over-budget label; CHANGELOG 270.
- Change: measure on a made-up `MemoryStore` of 1000 mixed rows (runs, plans, approvals, tool-call records) the nodes visited and wall time per question at the current weight; choose the weight so that store reads as a stand-in with 2x headroom and a worst-case budget still costs at most a stated wall time (state the CI-machine figure in the CHANGELOG with the effective row count, not "100000 values"). No verdict cache. The label becomes "too large to check, treated as real" and the scan finishes the real-object check on the remaining sibling values within the same budget before answering (so a real object met later is never named "over budget" first).
- Tests: the 1000-row store is a stand-in (served 401); a store over the stated limit is refused (503) with the over-budget label; a real object placed after a big container is labelled as real; wall-time test uses counted nodes, not seconds.
- Mutants: weight constant changed; budget not charged for rows.

**Fix class 4: mutant tables and test honesty**
- File: tests/bind_mutants.py, tests/test_bindguard.py.
- B161, B162, B163: each reverts exactly one guard (one identity swap per row); add `_spoof_empty(cls)` (empty `__dict__` or `__slots__=()`) for the atom, container and model sites and use it in those killers; CHANGELOG "each reverts one guard" kept only if true.
- B137: assert the controls before the loop; give the row its own shape and message for the `_TextWithCode`/`int_subclass` shapes.
- Rows for the two Counter tests (`test_the_fake_model_with_its_own_counter_...`, `test_only_the_counter_among_the_allowlisted_types_...`); the seven serve-slot cases get one row each (not only B175); B200 pinned to the slot it names.
- B195 and `_counting`: record calls in a list and assert after the call (no AssertionError inside `verdict()`'s catch); B197: bound it: shrink the budget by monkeypatch in that test and assert on counted calls (no 8 minutes, no multi-GB child); its expect text is the real failing line.
- Fail-before: list per test (name, old-code result, killing rows).

**Fix class 5: minors in the same push** (Issues 8-12, 14, 16-17): serve pin check; depth sentence derived from `SCAN_DEPTH`; refusal-text ascii rules and fuzz test; `Path` slots; defaultdict wording from `_DEFAULT_FACTORIES`; r7 CHANGELOG items; `_one_cell` annotation and `_NONE` order; `live_class` with `issubclass(type(cls), type)`; holder key read without `==`; `Card` data-state check; `hold_run_ids`/`timeout_s` decided and tested against `inspect.signature(build)`; the `_BUILD_TOKEN` boundary sentence.

## Round 9 and evidence

- **Round 9 is required** (security path, no cap). Reviewers get the snapshot of the new head, DELTA-vs-3db352f5.patch and the facts above, not the builder's verdict. Round 9 needs two reviewers (design, codebase-details) in parallel with the runner.
- **Evidence for the final head (one runner per final head, never on a head that gets another batch):**
  - Cloud, each under 8 minutes and resumable (checkpoint file per chunk), at most 2 heavy processes: focused new tests; fail-before on the delta test files against 3db352f5 src; the changed and new mutant rows only plus a 60-row sample of `bind_mutants.py` in chunks; `stage_mutants` (37, short); ruff, ruff format --check, bandit -ll, scan_repo, server_scan, gitleaks, check-no-handover-files; hostile probes (clock tzinfo, Runtime holder, pre-first-question patch, 1000-row store, 10**6 shared values).
  - **RUN ON LAPTOP (lead order of 02:12Z):** the full pytest of the final head (about 6 minutes here) and the complete `bind_mutants.py` table (about 13 minutes here), each with the exact sha; raw output goes onto the branch.
- Ledger rows for these findings: added by the caller (PDBIND-r8-1..N already exist for the design Blocker and Majors; r8-4..10 for the codebase ones).
