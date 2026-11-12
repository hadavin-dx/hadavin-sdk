# PR H batch 6: builder notes (REDACTION path, no round cap)

Builder run 2026-11-12 from 02:21 UTC (07:51 IST). Worktree `/home/user/build/B-PRH-b6`, branch `core/prh-b6` from `origin/wip/cloud-prh-b5` (3db0d34d). This is the builder's own record. It is not independent evidence: the evidence runner and the `egm:*` reviewers judge the head.

## What failed or was not checked (read first)

- Full `pytest -m "not live and not perf"` at head 8d5f41d8: run 1 had 148 failed and 30 errors, all Postgres, caused by my own cluster being created with SQL_ASCII encoding (log kept as `B-PRH-b6-full-run1-pg-sqlascii.log`). Run 2 (UTF8) had 1 failed: `tests/demo_askdata/test_validate_harm.py` (dblink from the server could not find a socket because I had started the server without PGHOST/PGPORT in the SERVER environment; log kept as `B-PRH-b6-full-run2-dblink-fail.log`). Run 3 (server restarted with PGHOST/PGPORT): `12962 passed, 1 skipped, 62 deselected in 346.37s`, exit 0. No PRH test ever failed.
- Timing flake `test_the_timing_harness_flags_a_quadratic_stand_in`: did not fail in run 3; not touched.
- gitleaks: see the end of this file.
- Mutants (`tests/prh_mutants.py`, 81): run at 8d5f41d8 gave 79 of 81 good (42 and 53 survived: the new piece net hid them; logs `B-PRH-b6-mut-run1-2survivors.log`). I pointed 53 and 42 at piece-check-off tests. Run at 3c244d4c: 80 of 81, only 42 survived (log `B-PRH-b6-mut-run2-1survivor.log`). I then changed the 42 twin test to a hex secret leaked in capitals (the backstop reads hex in any case, the piece net does not); that test passes, but the FINAL mutant run at the head was still waiting for a heavy slot when I stopped: NOT VERIFIED that 42 is now killed. Next step: run `python tests/prh_mutants.py` in a detached worktree at the head.
- Cost compare (`tests/test_prh_perf.py --compare-main`): NOT RUN (no heavy slot in time). Before-numbers from batch 5: 2.78, 3.36, 4.68, 3.28 at 262,144 characters, S1-S5 0.98 to 1.03. Batch 6 adds `_has_piece` (at most 64 windows per form) and a second reading in `redact`; the effect is unmeasured.
- The full pytest run (12962 passed) was at 8d5f41d8; two test-only commits (mutant re-pointing, two new tests) followed. Those tests pass alone, the full suite was not re-run after them.
- Hostile-mix availability cost: 4000 seeds, 8000 outputs, 0 pieces of 4 or more characters standing, but about 38% of the hostile outputs are withheld (MARKER+TRUNCATED). That is a real loss of availability on hostile mixes only; plain text and single or double copies are unchanged (availability pin in the H1 rows).
- R5-1 (CONTESTED, 71 of 71): untouched as a claim. Mutants 58 and 59 had to be re-pointed because the code they patch moved (forced by the fix); the contest is not changed by this.
- Gates at head 8d5f41d8: ruff check exit 0 ("All checks passed!"); ruff format --check exit 0 (339 files already formatted); bandit -ll exit 0 (only the nosec B102 warning at tools.py:389); scan_repo exit 0; stage_mutants "37 of 37 good; problems: []".

## Findings and what changed

- H1 (blocker): the secrets found were compared as a set. Now per-reading COUNTS; the union is the most any reading holds; a reading must hold every secret at least as often, else MARKER+TRUNCATED. Reproduced `"x "+HAND+" y "+ESC+HAND` on 3db0d34d (leaked); now clean. Rows: single copy, two copies, copy before and after ESC, cut copy plus plain copy (H1b shape), equal-count case.
- H2 (major): `return raw` is gone; the first usable reading whose scrub changed is used, else fail closed. A piece net (`_has_piece`, window `piece_min` = 6, config `ScrubSettings.piece_min`) refuses any result with a 6-character stretch of a secret form. Fragment strip `_strip_fragment` handles the cut-first-letter fragment (found by the fuzz).
- H3 (guard): `runmap.py` now uses the spaced character reading (`characters_spaced`). The lead's input `KEY[:4]+ESC+"A"+KEY[4:]` does not reach that path (the grammar reading holds the whole key), so it passes on old code. A real failing input: `KEY[:3]+ESC+KEY[3:]` with the map holding the IP: old code `id AKI IOSFODNN7EXAMPLE` and glued `userhost.example.org`; fixed and has a row.
- Direct `redact()` d3 (fixed at the choke point `_Redactor.find`: now `id <APIKEY_1>`) and d11 (now returns the withheld note). Docstrings of `find` and `redact` updated.
- R5-3: mutant floor 55 -> 81. R5-4: pass-count test now asserts worst is 14 (it was 13 before the character pair; defaults comment and CHANGELOG say so).
- R5-2: ticket errata section 8.7 lists the extra files with one reason each: `defaults.py`, `scrub_settings.py` (new in batch 6), `prh_accidental_pairs.json`, `prh_main_passes.json`, `test_k5_fixes3.py` (the `_decoded` spy re-pointed to `_decoded_readings`). Note: the brief named 4 files; there are 5 because `scrub_settings.py` is new here.

## Tests that passed on the old code (7), and what kills them

| Test | Killed by |
|---|---|
| three tail rows | existing mutants 44b, 44c, 44d |
| undo entity cut | existing mutant 21b |
| refusal test (equal count) | new mutant 78 |
| two pass-bound tests | existing mutants 67, 68; new 80, 81 |

New-test fail-before check: 20 of the first 24 b6 tests fail on 3db0d34d; the others are controls (single copy, two plain copies, no-find text, and the H3 guard, which passes before because it protects a path the fix touches). The seeded fuzz fails on old code: 456 pieces left in 400 texts.

## Gate record

gitleaks: run before the push (see the report).

