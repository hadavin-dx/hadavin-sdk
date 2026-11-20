# G12d build notes (fixes for G12c result review 1, codebase)

Branch wip/cloud-core-c/g12d on origin/cloud/core-c 2a7081ace. Code commit ef629f793. Defaults only, no lead decisions.
(handover/core-c/evidence/G12c-build-notes.md does not exist on this tree; the ticket was read.)

## Changes (src/hadavin_sdk/guard/redact.py)
- `_core_is_declined(core, full, start, end, redactor)` replaces `_placeholder_like`, `_cut_a_lookalike_bracket`, the `_LOOKALIKE.search(full)` guard and the 4096/16 rule; `_bare_span` gives the span (`_bare` kept).
- M1: a label-text core (`<label>_<digits>`) is declined only when `<core>` is a mapping key or the number is within the label's counter (digits capped at 9 to avoid int() limits). `password=SECRET_123, SECRET_123` now sweeps the bare copy. NOTE: `TOKEN` is not in `_LABELS` on this tree, so the review's `TOKEN_2024` example was never declined; the test uses `SECRET_123` (and keeps TOKEN_2024).
- M2: budget rule: a core of 4096+ chars is skipped only when sum(map value lengths) + len(core) > MAX_MAP_CHARS // 2 (262,144). `password=<5000>, <same 5000>` now swept; 262,138-char PRIVKEY still gets no core. The `qwxz*2000` test is re-pinned: the core IS registered now.
- 3: `‹HUNTER2,`, `‹hunter2zz›`, `12‹EMAIL_1›34,`, `hunter2‹X_1›,` register the core. Declined still: value of tokens only (E9 shape), the body of a real label with a cut `‹` (`‹SECRET_x`, `‹SECRET_x›`), a core that starts right after a cut `‹` with `LABEL_n›` or ends right before a cut `›` with `‹LABEL_n` (`‹SECRET_1›xy`).
- 4: `_sweep_once` leaves an escaped look-alike `‹LABEL_n›` of a real label alone for an original without ‹ or › when the number is within the label's counter or the original is only part of the token (`MAIL_1` in `‹EMAIL_1›`); a look-alike that is the whole value beyond the counter (`‹SECRET_123›` for value `SECRET_123`) is still swept (secrecy over integrity).
- 5: `<core` declines only with the `<` directly before the core (uses the real span, not `find`).
- Perf: `_bare_span` tries the close search only when the last char is in `;>%` or alphanumeric.
- Comments/docstrings (~963 edge comment, `_place` docstring) updated; unused `_LOOKALIKE` removed.

## Deviation to flag
`test_only_the_exact_escaped_shape_is_left_alone` listed `‹hunter2zz›` (mapping == {full}); the ticket's case (3) requires its core to be registered, so that one entry moved to a new test `test_a_secret_in_look_alike_brackets_is_masked_and_its_core_swept` (tests/test_redact_own_output.py). Everything else in that test and all E9 tests are unchanged.

## Tests added/changed (tests/test_redact_g12_trailing_punct.py)
Renamed `..._takes_at_most_two_entries` -> `..._takes_one_extra_entry_besides_its_own`; new G12-29..G12-35 tests (look-alike edges register core, tail-of-label never corrupts `‹EMAIL_1›`, beyond-counter label value, look-alike that is the value, `PW<em/>` at the end, call-count guard (close search not tried for 500k `!`/`-`), `<` directly before core, tokens-only). tests/g12_mutants.py: 41 mutants (was 35); EQUIVALENT note corrected; old M19-M25/M33-M35 replaced by M18-M25, M33-M42 on the new code; M36 = `PW<em/>` end mutant.

## Measured (TESTED)
- Perf, thread CPU, 500,000 `!` (and `-`) after `password=`: `_bare` 0.90 s -> 0.10 s; whole `redact` ~3.0 s -> ~2.1 s (rest of the time is outside `_bare`; machine load 1-4, so +-30%).
- Property corpus (tests/test_redact_idempotent_property.CORPUS, 1,978 inputs through runmap.redact_text with a fresh RunMap): outputs byte-identical before/after, placeholder count 41,298 both: no fewer masks.
- ruff check, ruff format --check: clean (src, tests).
- pytest -n 0 -m "": test_redact_g12_trailing_punct, test_redact_own_output, test_redact_own_output_hardening, test_redact_context_after_sweep, test_redact_settle_loop, test_p1d_a_paths, test_p1d_a_rows, test_redact_idempotent_property, test_redact_mutants_meta: 2,612 passed.
- tests/g12_mutants.py: 41 of 41 good. tests/redact_mutants.py whole: 130 of 130 good; EXPECTED_COUNT stays 130 (that file's mutants unchanged).

## NOT RUN
Full test suite, tests/test_k5_perf.py -m perf, other mutant files (g8/g9), bandit. Not read: runmap escape_placeholders internals beyond the tests that cover it.
