# G12e build notes (fixes of G12d result review 1; branch wip/cloud-core-c/g12e, from origin/cloud/core-c 0e6216852)

Code: `src/hadavin_sdk/guard/redact.py` (`_core_is_declined`, `_issued`, `_ANY_TOKEN`, `_place`, `_rollback`, `_Redactor.__init__`, `_outside_lookalikes`, one closure). No edit to `_overlaps`/`_deep_hits`/`_expand`/`_place_union` (G9c). Defaults only, no config.

## Fixes
- M1: `_ANY_TOKEN` is built from `_LABELS`: real `<LABEL_n>`, real `‹LABEL_n›`, a cut-off opener only for a real label or a start of one (`<EMA`, `<EMAIL_1`) and only before a separator or the end. `<HUNTER2`, `‹ADMIN_1›`, `<ABCD1234!` no longer decline the core.
- M2: `self._map_chars`, a running count (init, `_place` x3, `_rollback`); `_core_is_declined` ends with `_map_chars + len(core) > _CORE_BUDGET` (`MAX_MAP_CHARS // 2` = 262,144), no 4,096 floor, no O(entries) sum. Decision: still SKIP the core over budget (fail open for the bare copy only, the full value is always registered); stated as residual in the docstring. Not changed to InputTooLarge.
- 3: new `_issued(label, number, counters)`: `f"{label}_{int(number)}" == f"{label}_{number}"` and number within the counter; used by `_core_is_declined` and `_outside_lookalikes`.
- 4: `_outside_lookalikes` protects only a look-alike that contains `original`; with none, one `replace(segment)` call.
- 5: residual leak stated in both docstrings. Nits: `rule=rule` removed; exact `len(key) == 262_134`; the TOKEN_2024 claim replaced by `EMAIL_2024` (EMAIL is in `_LABELS`, asserted; mutant G12e-M51 kills it).

## TESTED
- FAIL ON HEAD (0e6216852 redact.py, new tests): 10 of 12 new `-k g12e` tests fail (4 leaks `<HUNTER2, HUNTER2`, `‹ADMIN_1› then ADMIN_1`, `<ABCD1234! and ABCD1234`, `SECRET_001, SECRET_001`; `_ANY_TOKEN`, running count, 128-value map, budget, call count, `_issued`). Two pass on head by design: `EMAIL_2024` (a regression pin, killed by M51).
  Note: the first version of these tests failed on head with a TypeError (wrong constructor call), re-run after the fix of the tests: the 10 fail for the stated reasons.
- Map measured, 128 values of 4,095 chars + `,` with no digit (no `_PIECE` entry), `_place` per value: HEAD 256 entries, 1,048,448 characters (past MAX_MAP_CHARS 524,288 and MAX_FINDER_CHARS 786,432); NOW 160 entries, 655,328 characters (cores 131,040 bounded by the budget; fulls alone are 524,288 = MAX_MAP_CHARS). Under MAX_FINDER_CHARS; NOT under MAX_MAP_CHARS: the 128 fulls already reach it and the first 32 cores are inside the budget. The run's own `max_map_chars` check (`document_too_complex`) is what stops that, as before G12. The test asserts cores <= budget and map <= MAX_FINDER_CHARS.
- A digit-bearing (secret-shaped) value gets its bare span as a `_PIECE` entry that this budget does not cover (pieces are not cores): unchanged, not in scope.
- ruff check, ruff format: clean.
- pytest `-m ""`: test_redact_g12*.py, test_redact_own_output*.py, test_redact_context_after_sweep.py, test_redact_settle_loop.py, tests/test_p1d_a_*.py, test_redact_fold_property.py, test_redact_idempotent_property.py, test_redact_mutants_meta.py: 2,628 passed (the g12 file was edited for messages while this ran, then re-run alone: 211 passed).
- `python tests/g12_mutants.py`: 50 of 50 good (41 + 9 new: M43-M51; M19, M25, M39, M41 re-aimed at the new lines).
- `python tests/redact_mutants.py`: 130 of 130 good.
- Delta, property corpus (1,978 inputs through runmap.redact_text, fresh RunMap, head source vs now): 0 outputs differ, placeholder count 41,298 both: no fewer masks.

## NOT RUN
- Whole test suite, other mutant runners (g8, gate, stage, p1d_a, textnorm), a fresh code review.
