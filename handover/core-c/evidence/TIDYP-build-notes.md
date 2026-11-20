# TIDYP build notes (branch wip-tidyp, base cloud/core-c ca469a0bf)

## Gate mutant R15 (tests/gate_mutants.py, tests/test_model_gate.py)
- Why it survived: the old killer (`test_r3_m2_a_deadline_already_past_stops_the_sweep_itself`) sets `REDACT_BUDGET_S = -1` BEFORE the
  snapshot, so building the patterns (`redactor.sweep("", deadline)` in `snapshot`) already refuses; the sweep inside `enforce_map`
  is never the first to refuse, with or without `deadline`.
- Killer: `test_r15_the_sweep_is_given_the_calls_deadline_...` (end of tests/test_model_gate.py): snapshot built normally,
  `EnforceBudget.check` switched off, `snap.budget.cpu_deadline = -1.0`, `enforce_map(text with a known value, snap)` must raise
  `InputTooLarge`. The R15 row now names it (and runs in tests/test_model_gate.py, `file=RUNMAP`).
- MEASURED: `python tests/gate_mutants.py R15` -> `1 of 1 good` (KILLED). Whole-file run NOT RUN (load).
- MEASURED p1d_a_mutants (whole file, load 0): before at this head: runner REFUSED to start (baseline red: PU1); laptop 48 of 51 (pre-G4). After: 50 of 51 killed, only A15 (known equivalent) survives; A3d and A43 KILLED.

## p1d_a_mutants.py
- A3d: stale anchor. The code is now `return _outside_code(text, _undefang_prose, certain=True)` (added by the G2 fix, 34e14bbe0
  / a2dea639f line); row re-anchored; killer unchanged (test_row_L10_slack).
- A43 (`_per_part`: `[line] if "``" in line`): `undefang_text`/`defang_text` go through `_outside_code(certain=True)`, which takes the
  whole line as prose for a double backtick run BEFORE `_per_part`; so the old killer (test_row_G2_undefang) cannot reach the guard.
  The guard is live only through `_defang_outside_code` (line level, used by `_clean_line`/`_clean_prose`). New killer
  `test_row_G2b_defang` in tests/test_p1d_a_rows.py; the A43 row points to it.
- A15 KNOWN EQUIVALENT (not deleted, row and runner unchanged, still reports as a survivor): dropping the query lookbehind from the
  `SECRET` query pattern changes only where a match may START; the plain pattern before it (`(?<![\w.\-?&])(?<!&amp;)[\w.\-]*...`)
  takes every key not preceded by `?`, `&` or `&amp;` (by its whole name run), and the query pattern takes the rest identically.
  Random comparison: 40,000 strings (3 to 18 tokens of `? & &amp; password token api_key secret = : quotes ...`), `redact_text`
  on the base tree vs a copy with the lookbehind removed: identical sha256 over all outputs (6,113 texts held a SECRET).
- BASELINE WAS RED at this head: `test_row_PU1_card/model` (also red at d462a4c80, see G13 notes). `password=ab&amp; x` now gives
  `password=<SECRET_3> x`: the map holds `ab&amp;`, `ab&amp`, `ab&` (G4 views / G9 fixed point settle one value shorter each
  pass). Same shape, nothing readable, one more number. RE-PINNED in tests/fixtures/p1d_cases.py (SECRET_2 -> SECRET_3), a
  measured re-pin, LEAD to confirm (precedent: MIX re-pins TB-2.8/3.4/2.11). Without it the runner refuses to start.
