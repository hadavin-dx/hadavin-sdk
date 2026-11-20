# G8T build notes (branch wip-g8t, base cloud/core-c 2c9be86fa): G8 / G7-F3 leftovers

Measured through redact() (base = `git archive 6a852c7d3^`, before G8; head = this branch). Test-only and comment-only: no regex changed.

## OL3 (G8 result review 2, N1)
Measured base output of the OL3 shape (`<20 chars>_<uuid>`): `<HIGHENTROPY_1><ACCOUNTID_1>` (two placeholders, nothing readable). The row in
tests/g8_cases.py was TRUE already; the RECORDS that said "one HIGHENTROPY" (E16, G8-build-notes.md "Review-fix round 1": "base masks all as one
`<HIGHENTROPY_1>`") are wrong for OL3 only (OL1, 2, 4-7 are one `<HIGHENTROPY_1>` as recorded). The test no longer asserts `base != after` (data vs
data); it asserts `base` is placeholders only and leaks none of the tail. Comment in g8_cases states the measured values.

## Wording (N2, N3, N4; G8 result review 2)
redact.py module docstring: L15 "set off by `_` or a letter", the remainder is under HIGHENTROPY's 40-character minimum (up to 39 readable).
Docstring and `_JOINS`/`_joins` comments: the patterns read a contiguous digit run glued to a letter as a phone only after a phone word (entry 8,
`tel4155550132`) and beside `_` (entry 7); the sweep covers the rest (once the number is known a letter-glued copy is swept). The sweep call
sites carry no such comment any more (only `_joins`). Test docstrings of `test_phone_before_a_full_stop_is_masked` (F1-F6 named: F1 dashed, F2
contiguous, F3 `+`, F4 after a letter, F5 `_`, F6 phone word) and the F5/F6 test name them correctly.

## G7-F3 review 1 leftovers
- N2: rows 102 (`call +44 20 7946 0958.Thanks` -> `call <PHONE_1> 0958.Thanks`) and 103 (`call 0044 20 5550 1234.5` -> `call <PHONE_1> 1234.5`):
  limit L7 (narrower), strict xfail, base identical (measured). No regex change; a fix would refuse a backtracked end followed by `[ \-]\d`.
- N3: K91-K93 (`tok 4155550132.-Ab9 x`, `.+Ab9`, `./Ab9`): masked to `tok <PHONE_1>.-Ab9 x` (the base kept them): an over-mask, pinned as measured;
  the desired unchanged output is a strict xfail (`test_dotted_token_with_a_symbol_segment_is_kept`).
- N1: AT10 pins the follow-on as a stated consequence, not a defect: `ref 1234567890. Next then 1234567890.tar and 1732095071.123` ->
  `ref <PHONE_1>. Next then <PHONE_1>.tar and 1732095071.123` (map `<PHONE_1>` = 1234567890, storable); epoch `1732095071.123` stays. K86 holds only
  when no copy was masked earlier in the same text (the sweep rule).
- Counts (history figures elsewhere untouched): rows 103 (was 101), LIMITS 35 (was 33), KEEP 93 (was 90), FULL_STOP 6, AT_REST 10 (was 9),
  OPAQUE_LIMITS 7. G8 file `483 passed, 46 xfailed` (was 451/43 at the G8 round-1 fix, then -2 xfail F5/F6 by G7-F3, +2 L7 rows, +3 K91-K93).
- Mutants: the real current count of tests/g8_mutants.py is 43 (I 5, U 2, V 7, C 2, P 20, S 7). The "34 of 34" (G8-build-notes.md:11) and "35 of 35"
  (:38) lines are history. G8-P19's expected killer was `ROW K87 ` but the first failing row is K85 (`ts <PHONE_1>.123`; both fail): `expect` changed to
  `ROW K85 ` (P19 was reported WRONG_REASON on this base before the change; killed non-vacuously now). `python tests/g8_mutants.py` whole: `43 of 43 good; problems: []`.

## Runs (TESTED)
tests/test_redact_glued_rest.py + test_redact_g3_port.py + test_redact_idempotent_property.py: `2544 passed, 46 xfailed` (glued_rest alone `483 passed, 46 xfailed`).
`python tests/g8_mutants.py` whole: 43 of 43 good. bandit -ll: no issues (warnings only). NOT RUN: full suite, perf, g8_cost, other mutant suites.
Deviation: installed ruff is 0.16.9 (pyproject pins 0.17.1): `ruff format` on the 4 touched files changed only my lines; repo-wide `ruff check`/`format --check`
report pre-existing findings with this version (not compared with 0.17.1).
