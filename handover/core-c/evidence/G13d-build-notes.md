# G13d build notes (fixes for G13c result review 1; branch wip/cloud-core-c/g13d from origin/cloud/core-c 126c17883)

## Changes
- M1 (src/hadavin_sdk/guard/runmap.py `_touching_piece`, both sides): every head hit is charged `1 + len(piece) // _LOOKUP_COST` BEFORE the `seen` test; the lookup charge `min(len(piece), _LOOKUP_COST)` stays once per distinct piece. Deviation from the order's literal `spend_chars(min(len(piece), 64))` per hit (the order allowed an equivalent cheaper scheme): the literal form breaks test_g13b_4 (378,000 repeated short heads must stay under 1M charged; it would charge about 22M against the 8.39M budget). The chosen form charges the real extra work of a repeat (the cut and digest, O(piece)): a short repeated head costs 1, a 4,000-character repeated piece about 63.
- M2: NO behaviour change. Pinned test E::test_g13d_1 (whitespace-only, `********` and tab-space values: a run of 4 before/after a key refuses, a run of 3 does not); stated limit in the `_touching_piece` docstring and the model_gate SECURITY block; question in ESCALATIONS.md E24.
- Nits: mutants for the `hits % 256` deadline read (left, right), the right-side lookup charge, the right-side digest line, the repeat charge (left, right), the separator pin; right-side memory test; docstring refs fixed (G13c-7 -> E::test_g13c_6 / 6b, `_piece_index` wording on `MapSnapshot.pieces`, E::test_g13c_* refs in both docstrings; in model_gate they are E:: because T:: is test_model_gate.py); notes on letter case (only the public auth words match in any case) and on the cap trigger (PEM head beside a dash/equals run over 4,096).
- Tests added (tests/test_runmap_enforce_map.py): test_g13c_7, _8 (reviewer shape `"a"*4090+"b<K>"`, 16k and 65k values), _9 (deadline reads), _10 (right memory), test_g13d_1. Existing E19f mutant anchor re-pointed. gate_mutants.py: 8 new mutants (140 -> 147 total); MIN_MUTANTS 140 -> 147.

## TESTED (uv run --all-extras --group test, one pytest at a time, load under 2)
- ruff check and ruff format --check: clean.
- tests/test_model_gate.py tests/test_runmap_enforce_map.py tests/test_runmap_map_write.py: 353 passed, 1 xfailed (before MIN_MUTANTS edit); then test_gate_mutants_picked_up + gate + enforce_map + g13/g13c selection: 346 passed, 1 skipped, 1 xfailed.
- python tests/gate_mutants.py (whole): 146 of 147 good; problems: only R8 (known equivalent, E20).
- Speed (MEASURED, own shape `"a"*4000+"b<HOST_1>"` x 16, 65,536-char value starting aaaa): 0.258 s new vs 0.244 s before the change (same). Memory (16,380-char value, 6 keys, 10 kB gaps): 1.7 MB peak.

## NOT RUN
- The whole test suite (only gate/runmap/enforce_map/g13 files above); perf-marked tests; redact_mutants/g8_mutants/other mutant runners; the 1,978-input property corpus and the model_gate gate tests outside test_model_gate.py.
- Whether producers can register separator-only secrets (unverified, E24).
