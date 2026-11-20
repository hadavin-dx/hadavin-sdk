# GATE-C build notes: mark honoured on ProviderExhausted

Change: `refused_before_response` (model_gate.py) now returns True for any `ProviderError` (incl. `ProviderExhausted` and subclasses) with the exact mark `True`; the call path is unchanged (marked -> settle 0, `provider_refused`; unmarked exhausted -> `provider_exhausted`, no settle). Docstring and the settle-rule comment say the gate cannot verify the mark.

Pins changed BY DESIGN (tests/test_model_gate.py):
1. UNSETTLED list: before `_flagged(ProviderExhausted(..))` -> unsettled, `provider_exhausted`; after: removed from it; replaced by truthy (1) and string "True" marks on Exhausted, still unsettled `provider_exhausted`.
2. `test_pin_the_mark_counts_only_on_a_provider_error_that_is_not_exhausted`: before `refused_before(_flagged(ProviderExhausted)) is False`; after True (plus subclass True, unmarked False, "True"/1 False).
3. `test_pin_a_flagged_exhausted_and_a_flagged_value_error_are_not_settled...`: renamed `..._a_flagged_value_error_and_an_unmarked_exhausted_...`; the flagged-Exhausted case moved to the new test `test_pin_a_marked_exhausted_is_settled_at_zero_with_the_refused_code` (settle 0, row failed/provider_refused, subclass too).
Kept: flagged ValueError, truthy non-True on ProviderError, raising mark.

Mutants: G12 (inverted: old rule now a mutant), G13 retargeted, new G13b, G13c, G13d. Count 105 -> 108 (MIN_MUTANTS = 108). The runner refuses to start here: baseline fails on pre-existing tests/test_runmap_enforce_map.py::test_e5b_* (fails on the base commit too, untouched). The 9 mutants G6a/b/e/f, G12, G13, G13b-d were run by hand against their killers: all KILLED.
Tests: test_model_gate + picked_up + install_callers: 267 passed, 1 skipped, 5 xfailed. Whole mutant file: NOT RUN.
