# G14 build notes (P8 items 4 and 7, defaults only), branch wip/cloud-core-c/g14

Files: guard/model_gate.py, defaults.py (GATE_CACHE_MAX_ENTRIES = 1024), tests/test_model_gate.py, tests/gate_mutants.py (MIN_MUTANTS 151 -> 159, +8: G14a-h), tests/test_gate_mutants_picked_up.py.

## Item 4: per-message cache
- Design: BoundGate keeps `_cache[(role is assistant, tool names, sha256(content))] = enforced text`, valid for ONE map content. Each call compares the snapshot's entries with the ones the cache was made against (exact dict comparison, no digest); any difference (growth OR a changed value) bumps `map_version` and empties the cache. Only successes are cached; max 1024 entries, then emptied. Documents are not cached.
- Public counters on BoundGate: `map_version`, `message_passes` (real passes), `cache_hits`.
- TESTED: stable map, 50 growing messages: 1275 -> 50 message passes (test_g14_a_stable_map_run_...). Hostile: a value registered later and present in an earlier cached message is masked on the next call (test_g14_a_value_registered_later_...); a changed value under an existing key also invalidates; tool-name list is part of the key; a refusal is not cached; bound holds.
- Budget (shared 6 s CPU, 262,144 chars, 32,768 steps per call, runmap EnforceBudget): UNCHANGED in semantics: still one budget per call shared by snapshot build, messages and documents. A cache hit spends none of it, so the budget never gets smaller for a call and no call spends more than before. One visible effect, pinned by test_g14_a_repeated_message_in_one_call_...: identical messages inside ONE call are enforced once (budget spent once); test_r2_m3 was changed to use distinct texts for that reason.
- NOT changed / not done: framing_free still scans the whole history every call (cheap regex); the snapshot build per call; a map that grows every call gets no saving; no quarantine/drop path for a planted value that forces a permanent refusal (second half of item 4); K41 and the shared CPU numbers not re-measured (NOT RUN).

## Item 7: audit rows
- `audit_dropped` on BoundGate (own rows) and ModelGate (sum over its bound gates), incremented where the sink write raises an Exception. audit=None counts nothing; a BaseException is not swallowed and not counted. TESTED (test_g14_audit_rows_...).
- `object_ref` on reserve_interrupted / reservation_invalid: NOT DONE. There is no usable reservation id on those paths (the meter raised, or returned a value that is no id); documented in the gate docstring. Item 7's masked-flag, K16 (KeyboardInterrupt in _settle) not done.

## Runs
- TESTED: ruff check/format on src and the touched tests clean; pytest test_model_gate, test_runmap_enforce_map (holds the G13 net tests), test_runmap_map_write, test_gate_install_callers, test_gate_mutants_picked_up, test_s3_gate: 401 passed, 1 skipped, 7 xfailed.
- TESTED: `python tests/gate_mutants.py` whole (159): all good except R8 (SURVIVED, known), before two G14 expect-text fixes and a new test for G14e; after the fix `G14` subset 9 of 9 good. The whole run was not repeated after those test-only fixes (NOT RUN as a whole).
- NOT RUN: whole test suite, reply masking, worst-case floors, independent substring net (not in scope).
