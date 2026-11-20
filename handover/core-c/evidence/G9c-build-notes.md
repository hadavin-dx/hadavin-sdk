# G9c build notes (G9b result review 1: M1a, M1b, M3, Nit)
Branch wip/cloud-core-c/g9c from origin/cloud/core-c bebea799e. Not merged. Defaults only, no lead decision taken; `SPELLED_MAX_WORK` (4,000,000) and the other stated limits kept. Measured on the Linux test machine, `time.thread_time()`, tracemalloc where stated.

## Changes (src/hadavin_sdk/guard/redact.py unless named)
- M1a `_overlaps`: 3 units per accepted occurrence (`_OCC_UNITS`), charged every 256 units as found (`_OCC_CHARGE_EVERY`, now a unit threshold), the remainder after the scans; the loop that turns occurrences into hits reads the deadline every 256 occurrences.
- M1b `add`: a rejected call (the `joins` rejection, including each prefix call) costs `_REJECT_UNITS` = 1. A call whose word has no rule is still uncharged (a dict miss).
- M3 `_deep_hits`: a place of the anchor found costs `len(anchor)//32 + 1` (was `len(anchor)`); first comparison of an edge and rule `2*(len(w)//1024 + 1)` plus 5 per chunk `_expand` built (was `2*len(w)+2` per character); each further place `len(w)//1024 + 3` (was `len(w)//32 + 1`). Constants `_ANCHOR_SHARE`, `_COMPARE_SHARE`, `_COMPARE_UNITS`, `_CHUNK_UNITS`.
- Nit: new `_held(label, full)`; `_register_written` and `_mask_ex` use it, so a SECRET-labelled find never reuses a non-secret placeholder (registers a SECRET entry; `_build` prefers it, the sweep rebuilds on map growth). Identifier finds still reuse any kind.
- Stale text: `_deep_hits` docstring (units), `_overlaps` docstring, `_close`/`_place_union` text, comment at the first comparison. `_union_upgraded` is now reset at the top of `_place_union` (G7 call path no longer leaves it set).
- defaults.py: the G9b/G9c block rewritten with the measured figures.

## MEASURED
M1a, nested chain at 90 percent of the cap (3.57 M units), untraced CPU / tracemalloc peak (a traced run is ~15x slower, so CPU is from the untraced run):
- depth 30, 2,500 copies: 3,572,410 units, ~1.19 M occurrences: 1.82 s CPU, 159 MB peak (~134 B per occurrence).
- depth 200, 60 copies: 3,629,640 units: 1.58 s CPU, 160 MB peak.
The G9b "82 MB at ~4M occurrences" was not at the cap (that run was refused early); it should not be cited. With 3 units the cap allows ~1.33 M tuples (~160 MB).
M1b: TENANT chain 200 x 17,000 (real limit): refused after 0.29 s CPU. G9b code on a 60 x 1,000 shape: 64,000 units counted, 0.77 s CPU with ~1.8 M calls uncounted (200 x 17,000 not finished).
M3 per-operation (microbench, 1,025-char anchor / 1,100-char rule): `find` place of a periodic anchor 2.5-2.9 us; further comparison 0.30-0.34 us (also at 8,000 chars); `_expand` 0.41-0.44 us per chunk of 4 characters (121 us for 275 chunks; G9b charged 1,100 + ... ~2,200 units = ~220 us at 0.1 us/unit for the first comparison but 33 us for a further place). Unit chosen at 0.1 us.
Periodic `S+"a"+S`, S = `ab` x n (units after G9c; whole-sweep CPU): len(S) 2,000: 28 k units; 4,000: 76 k; 8,000: 184 k, 0.04 s; 16,000: 448 k, 0.13 s; 32,000: 1.17 M, 0.47 s; 64,000: 3.34 M accepted, 2.06 s; 72,000: 4.05 M REFUSED; 96,000: 6.5 M. `_deep_hits` alone: 0.109 us per unit at 1.17 M, 0.33 s at 64,000. The rest of the CPU is `_sweep_once` (the literal sweep of the periodic value, quadratic, NOT counted by the units; 1.86 of 2.19 s at 64,000 under the profiler); the deadline (`REDACT_BUDGET_S`, 6.0 s) bounds it. New stated limit (replaces "7,000 accepted / 8,000 refused"): about 70,000 characters of S. Period 1 (`x` x n): `_deep_hits` 82 k units at n = 20,000 (0.3 s, in `_sweep_once`); the G9b remark "refuses around 5,000" does not hold now. 4-char keys beside a 1,100-char rule: 14-21 k units, 3-9 ms (G9b: 4 k units, same time: per-chunk now charged). No per-edge cap added: units track `_deep_hits` time near 0.1 us per unit up to the limit.
Loosening (stated, forced by measurement): the periodic limit moves from ~7,000 to ~70,000 characters because G9b's weights over-charged ~15x (0.006-0.009 us per unit measured). The security reading: a refusal of an honest 8,000-char periodic secret is gone; the cost bound is the same 4 M units.

## Tests / mutants
Changed: remainder and read-back pins derived from `R._OCC_UNITS`; feasibility test pins derived from `_deep_units(...)` (the module's constants); the 265,620 pin replaced by a derived test (linear in copies, limit exactly at the total accepted, one less refused); the periodic limit test is derived (limit set between measured units of two sizes). New (G9c): memory per occurrence (limit 400 k, < 250 B per occurrence allowed), 90 percent chain CPU (perf), clock in the hits loop, rejected calls charged (TENANT 60 x 1,000, limit = chars + accepted + 1,000), TENANT 200 x 17,000 (perf), exact total charge (depth 30, 10 copies: 341 + 3 x 4,650 units, more than 256 occurrences), each term of the anchored check charged (also: one read-back per edge and rule), `_held` (secret find). Mutants G9-38 .. G9-44 added, G9-15, 22, 33-37 re-anchored, N10 re-anchored; EXPECTED_COUNT 130 -> 137.
Observation, not examined: an occurrence that is the first token alone at index 0 of E is not found/charged (2 of 465 per run for the first copy in the exact-work shape). Harmless to the hits rule (token only), pre-existing.

## TESTED
All runs used the worktree's code (checked: `hadavin_sdk.guard.redact.__file__` is /tmp/core-c-g9c/src/..., `uv run` builds the worktree).
- ruff check, ruff format --check: clean.
- pytest (plain, `-m ""`, one process): test_redact_settle_loop, g12_trailing_punct, own_output, own_output_hardening, finder_cap, context_after_sweep, idempotent_property, mutants_meta, k1b_redaction, k1b_redaction_layers: 2,506 tests; 2,505 passed, 1 failed (mutants_meta: a search string occurred twice after `_held` reused the name `held`); renamed the local to `got`, test_redact_mutants_meta re-run: 6 passed.
- `python tests/redact_mutants.py` whole run: 137 of 137 good, problems: []. After that run only the rename above (and its G9-43 snippet) changed; G9-9, G9-43, N10, AL-3 re-run: good. The settle-loop file was not re-run after the rename (a local variable name).

## NOT RUN
- The whole suite, test_redact_fold_budget.py, test_redact_glued_rest.py (only the files listed above).
- Runmap `_rules_conflict`/enforce_map with two placeholders (TENANT_1, SECRET_2) for one value (review: unverified): not examined.
- The `_sweep_once` quadratic cost on a periodic value is outside the units (stated, deadline-bounded), not changed.
- G12d's `_place` / `_bare` edits: not touched, no merge attempted.
