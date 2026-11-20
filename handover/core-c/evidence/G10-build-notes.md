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
