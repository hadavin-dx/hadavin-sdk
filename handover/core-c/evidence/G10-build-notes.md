# G10 build notes (builder, 2026-11-20)

Branch wip-g10 on cloud/core-c 555ef68fa. Built from handover/core-c/tickets/G10-textfold-deadline-v4.md and G10-files/ (sha256 of the four files matched section 0.1). D1..D10 defaults only (unapproved by the lead). SECURITY files untouched (D9). redact.py untouched.

## Results (TESTED unless marked)
- Both diffs `git apply --check` clean on 555ef68fa (HEAD moved from f91f56a04; only gate.py, redact.py and two redact tests differ).
- Phase 0: new test file alone -> 1 collection error, `ImportError: cannot import name 'DeadlinePassed'`, as the ticket says.
- Phase 1 (textnorm.py + 4 pin files; test file deleted): 3 failed, 1233 passed (manifest, meta g, meta split) = the ticket's three reds.
- Phase 2 (injection.py, defaults.py, round2 row): same 3 failed, 1233 passed.
- Phase 3 (test file + mutant list + meta): deadline + meta files 25 passed, 1 failed (meta test i, CHANGELOG count; needs phase 5).
- textnorm.py sha256 = 9f7e0ad0c087e4d61e7790e0eda9e26069694a8c8e4a7a02549b5bc98362b237 (equals the prototype); manifest and CHANGELOG take it.
- Phase 5 + MUST-STAY-GREEN: `pytest -n 2 -m "not live and not perf" tests/test_textnorm*.py $INJ $CANARY` -> 1,247 passed (238 s). Deadline + meta + manifest test: 27 passed.
- Perf rows: `-m perf tests/test_textnorm_round2.py tests/test_textnorm_perf.py` -> 19 passed, 11 deselected (52 s).
- Mutants (tools/mutation_runner.py via tests/textnorm_mutants.py, 13 filters): 24 of 24 good, all KILLED (15 new: 241-255; 9 re-pointed). Header: 255 mutants, 243 behaviour, 12 wording.
- ruff format --check src tests tools: clean (355 files). ruff check src tests: clean. bandit -r src -ll: no findings (only nosec warnings).

## Deviations from the ticket
1. Phase order: phase 4's baseline (unmutated copy over the 11 killer files) fails ("the unmutated copy does not pass its tests") until the manifest hash and the CHANGELOG item are in (the manifest test and meta test i are red before phase 5). First attempt of phase 4 failed for that reason; I did phase 5's manifest and CHANGELOG edits first, then re-ran phase 4 (second try, green). Ticket estimate for phase 3 ("manifest test only red") missed meta test i.
2. Base is 555ef68fa, not f91f56a04; diffs applied unchanged.
3. Phase-1/2 runs used `-p no:cacheprovider` (no effect on results).

## Not run
- Python 3.12, other platforms, full suite outside TN_ALL/INJ/CANARY, the 255-mutant full run (only the 24 of phase 4), evidence-script remeasurements of section 12 (not re-run; numbers are the ticket's).

## Review-fix round 1 (builder, wip-g10b)
- M1: T3 = "测试" * 5000 (V = 密码测试): measured, the second loop of `_holds_with_one_insertion` ticks once (hit 4,096), the first loop never; same reading sequence as T2 (POINTS_T3 = POINTS_T2). New mutant 256 "deadline: no reading in the second loop of the insertion match", killed by D-3 (DEADLINE-POINTS). Counts: 256 mutants (244 behaviour, 12 wording), names[28:] 228, names[240:] 16, test_textnorm_deadline.py 13 tests (D-2b zero budget on a frozen clock, D-8b fake detector raising DeadlinePassed over alone/AnyOf/nested/combine). N2 `>=` pinned by D-2b (no mutant added for it).
- defaults.py comment: "slowest ORDINARY text ... (16.0 s; a constructed text took 185 s)". textnorm.py docstring: "never a False in place of the error", overrun "of the text work", value work 7.2-7.5 s longer. Long lines reflowed (injection.py _deadline, defaults.py).
- New textnorm.py sha256 5938ea86571ad4c42057bf49c8638aaf58dd03cb3e6b50d8921e1969a4ca2879 (manifest and CHANGELOG item updated; CHANGELOG count text 13 tests, 256 mutants, 16 of G10, 244).
- Runs: mutant runner (deadline: + 12 named) 25 of 25 good; gate 1,248 passed + 1 red (meta names[28:] 227 -> 228, fixed, meta+deadline re-run 28 passed); ruff, format, bandit clean. NOT RUN: perf rows, a re-run of the whole gate after the one-number fix.
