# G9b build notes (G9 result review 2: M1, M2, M3, N1-N4)
Branch wip/cloud-core-c/g9b from origin/cloud/core-c 64948390a. Code commit 24f1983fc (+ a follow-up for the mutant `expect` strings). Not merged.

## Changes (src/hadavin_sdk/guard/redact.py unless named)
- M1 `_overlaps`: occurrences are charged every `_OCC_CHARGE_EVERY` (256) found, inside `add`, and the remainder after the scans; same total (one unit per occurrence). Nested chain (200 secrets, 17,000 copies, 221,000 chars): refused `SpelledWorkTooMuch`, 2.8 s CPU and 82 MB peak under tracemalloc (base: not finished in 120 s).
- M2 `_place_union`: a SECRET union whose value is held under a non-secret kind registers a SECRET entry of its own (`_build` already prefers the SECRET rule for a value); `_union_upgraded` makes `_close` rebuild the rules so a standalone copy is swept as the SECRET. Non-secret unions and secret-on-secret still reuse the held placeholder. The old G9-9 test pinned TENANT reuse for a SECRET run; it now pins reuse under APIKEY and for identifiers, and the new test pins the downgrade refusal.
- M3 `_deep_hits`: the text is read back once per (edge, rule) (`2*len(w)+2` units, as before for the first place); each further place of the anchor costs `len(w)//_COMPARE_SHARE + 1` (32). `S+"a"+S`, S=`ab`*2000, 12,002 chars: 1.94 M units, accepted (base 11.9 M, refused). Stated limit with numbers in defaults.py: S of 6,000 chars accepted, 8,000 refused (4.50 M units); 0.01-0.02 us per unit measured. defaults.py also states: all clocks are `time.thread_time()` (CPU); the E17 "10 s" is a wall figure of the measuring run, not a CPU budget (read from the E17 text, not re-measured).
- N1 enforce_map docstring (runmap.py), N2 comment at `SpelledNotSettled` (stated, behaviour unchanged), N3 cap-order comment in defaults.py (wording of the review), N4 numbering note in tests/redact_mutants.py (no G9-6).

## Tests / mutants
New in tests/test_redact_settle_loop.py: M1 small shape (peak < 40 MB, limit 200,000), remainder pin (23 units), 200-chain (perf-marked); M2 downgrade test; M3 12k acceptance, 265,620-unit exact pin and 1,500-copy refusal, numeric limit pin. Mutants G9-31..G9-37 added; EXPECTED_COUNT 123 -> 130. G9-15 and G9-9 re-anchored; G9-22's killer renamed (its old test asserted the refusal that M3 removes for that shape: stated change of a stated limit, not a loosening of a security pin: the periodic shape still refuses at 1,500 copies).

## TESTED
- ruff check, ruff format: clean.
- pytest (plain, no xdist installed, `-m ""` so perf runs): test_redact_settle_loop, g12_trailing_punct, own_output, own_output_hardening, finder_cap, context_after_sweep, idempotent_property, mutants_meta, k1b_redaction, k1b_redaction_layers: 2498 passed (197.9 s).
- tests/redact_mutants.py first full run: 123 of 130 good, the 7 bad were KILLED with a different first line than declared (expect strings / crash_type); fixed. Full re-run after the fix (TESTED): 130 of 130 good, problems: [].
## NOT RUN
- test_redact_fold_budget.py / test_redact_glued_rest.py / the whole suite (only the files above); E22 perf failure not touched.
- The M3 recalibration of the unit weights vs the review's 10-40x microsecond claim was not reproduced beyond the per-unit figures above.
