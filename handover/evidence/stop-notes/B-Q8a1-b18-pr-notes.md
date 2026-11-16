# Q8a-1 batch 18 - PR notes (builder, not reviewed by me; the lead runs EGM)

## Fail-before (b5b6c9fd, clean detached worktree, only the new test file copied in)
MEASURED: 27 tests collected, 23 failed, 4 passed. (The old copy of the test file wrapped the `code_words` import in try/except so collection would not stop; the file has since gained tests, count at the final head is in the report.)

## Tests that pass on the old code, with the reason
- shape[library_error_text]: CONTROL. Already hidden by the batch-17 rewrite; kept as a regression guard.
- shape[plain_value_error_hex]: CONTROL. Same.
- test_every_purge_method_of_the_store_is_declared_to_give_a_number: CONTROL. Reads an existing declaration; killed by mutant Z65.
- test_the_mutant_check_names_each_kind_of_mutant_that_cannot_apply: NEW HELPER. The helper (tests/_mutant_check.py) is copied together with the test; it tests itself on synthetic mutants and is killed by Z247 and Z248.

## Mutants removed (equivalence proofs)
- Z192-Z194: the three overrides they mutated (HiddenInputModel dead overrides) were removed from the code; nothing to mutate.
- Z209: `insert` is also in COLLECTORS, so removing it from STORE_CALL_PREFIXES changes no finding (equivalent).
- Z221: re-pointed, not removed.
- M16s (tools.py `error_where(field_names=True)` vs raw `loc`): the tool-entry model is a HiddenInputModel since Issue 2, so `exc.errors()` already holds `<unknown key>`; the mutant text is equivalent. Measured: it SURVIVED in the full run.
- M18v (strict_model.py `hide_input_in_errors=True`): HiddenInputModel (its base) closes the same channel; the flag is kept only because tests/test_q8a1_f_string_trace.py pins it. Measured: SURVIVED in the full run.

## Mutant ids re-pointed this batch after the test changes
Z152 now killed by plant R18e (a dict value given to a call; the Return branch no longer hides it). Z239 now has its own test (test_a_context_the_library_cannot_use_...), Z245 has an `input_value` assertion, Z197 and Z223 tests were strengthened (they passed for the wrong reason after the shown_name change / a wrong digest). Expected-reason strings of M15d, M15k, M17a, M18b, Z65, Z231-Z248, Z254 were set to the real first assertion line.

## Operator-usability conflict (Issue 7 vs the older decision D-2322 / batch 14)
Issue 7 makes `shown_name` return `<not shown>` when no loaded set exists. This overrides the batch-14 choice to show a bundle folder name. It costs operators a name in some config errors. Tied to OWNER question q-q8a1-hide-ids (Issue 10, owner-only; 5 REDACTED rows stay pinned, nothing built).

## Third-party / owner / impossible-now
- tools/mutation_runner.py changed (byte copy hash pinned in tests/fixtures/mutation_manifest.json and the CHANGELOG): other repositories that keep a byte copy must re-copy it (third party).
- Issue 10 items (E1, E2, error_reason): owner-only.
- IMPOSSIBLE-NOW: Python 3.12, semgrep, zizmor, trivy, pip-audit, Vault engine tests.

## More mutants removed after the filtered re-run (measured: each SURVIVED, reasons)
- Z159 (library receiver early return in the attribute check): a receiver that is a call result, an imported name or an except name is also refused by the later round-17 rule (a name bound to a call of a package class); the early return is redundant. Reasoned, plus measured survival.
- Z163 (number directives of a log call not removed): the plants R16o and R17c are proven numbers by other means (annotation, `-> int` declaration), so disabling the call changes no result for them. Measured: 52 tests passed with the mutant applied. Z190 and Z251 still kill the inner parts.
- Z250 (keyword of a store call): the general keyword scan just above the store branch already reads every keyword (except print keywords), so the batch-18 branch was dead and was REMOVED from tests/_text_guard.py; plant R18c stays as a control (passes by the general scan).
Re-pointed to the failing plant: Z154 (X11), Z190 (R17c), Z90 ([plain-error]), Z245 ([extra_forbidden]), Z248 (reason text).
R17t and R17u plants have no mutant of their own: they are CONTROLS (shapes that already passed).
