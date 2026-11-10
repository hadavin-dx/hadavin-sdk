# A15 PR74 fix1 builder report (branch core/P5a-fix1, base 21ca680)

## What failed, was not run, or is open (read first)
- NOT PUSHED. core/P5a-fix1 is local in /home/user/build/WT-A15fix. No PR opened or changed; core/P5a untouched.
- The pydantic nit "slice errors() before the build" is NOT done: the pydantic API has no limit parameter (impossible now; the read stays inside the one helper and is cut to 5 entries after the call).
- `bandit` is not installed in the project environment: inside the heavy gate script `uv run ... bandit` failed to spawn (rc=2). I ran it by `uvx bandit -q -r src demos -ll`: rc=0, no issues. Not run inside heavy.sh.
- The Postgres tests were SKIPPED (HADAVIN_TEST_PG_DSN not set; I had no DSN with credentials, so pg_a15fix was not used). 454 skipped in the full run, the Postgres ones among them.
- Mutant runs of tests/diagnostic_mutants.py (about 1 minute for 46 single-test mutants) were run directly, not through heavy.sh, because all 3 slots were held by other jobs for over 20 minutes. The full suite did go through heavy.sh.
- tests/textnorm_mutants.py was NOT re-run. textnorm.py changed (G7 time budget); no mutant anchor text I touched is a mutant anchor (the `for step in (_pass_a, _pass_b)` line and the FoldNotConverged text are intact), but this is unverified by a run. The P1b run of that file is owned by the lead's evidence runner.
- Two items I did not make mutants for: the `exc.code` read and the "facts merged from __cause__" mutants (no stable anchor in the code; the killer tests exist and pass). The `type(mod) is str` check in `_own_code` is an equivalent mutant (stated in the mutants file docstring; the test pins the behaviour).
- Earlier summary said "ten noqa BLE001 sites": it is nine (tests/noqa_sites.txt has nine rows, diagnostic.py has nine).
- The object.__setattr__ bypass of SafeToken is declined by the resolve; a test documents it.

## Commits
8aaaea5 A15 fix1: lint (FLY002) in the safe token test
3d4fd8c A15 fix1: CHANGELOG mutant count from the run
cb7f66e A15 fix1 G4 G9: 10 new diagnostics mutants (46 in all, all killed), oracle and corpus mutants, stale anchors fixed, textnorm hash recomputed, old-writer meta test moved to its own file
a003b05 A15 fix1 nits: private mint, locked guard counters, one traceback walk, render fact cap, count tail noted, __main__ refused, noqa sites keyed by symbol
fa587a2 A15 fix1 G1 G2 G3 G8: hard-gate and teeth tests, the ten missing tests, bogus handler names removed, old-writer ledger marked
22d2dab A15 fix1 G5 G6 G7: Unicode guard before the secrets provider, py3.12 upgrade step, scan time budget

## Per group
- G5, G6, G7 (22d2dab): guard before secrets provider in app.py (new test fails on the old order, verified); CHANGELOG py3.12 upgrade step; scan time budget in textnorm (`REDACT_BUDGET_S`, TextTooLong), two new scan tests, perf ceiling `2 * REDACT_BUDGET_S`.
- G1, G2, G3, G8 (fa587a2): reverse check (120 of 124, 96.8 percent), teeth test (cap 15, 10 exempt), the ten missing tests, bogus handler names removed, old-writer status ledger with named wiring rows (73 leaks, 8 crashes).
- Nits (a003b05): private mint, locked guard counters, one traceback walk, render fact cap, count tail clamped, `__main__` refused, noqa sites keyed by symbol.
- G4 (cb7f66e, 8aaaea5): 46 mutants in tests/diagnostic_mutants.py, 46 of 46 KILLED on the final head (`ok` lines 46, `46 of 46 good; problems: []`). 13 added: reserved code row, fact priority swap, SafeToken caller object, ProviderExhausted row, fingerprint with line, group message read, kind identity, pydantic read outside helper, KeyboardInterrupt internal_bug, oracle blind, oracle fold removed, ledger range, corpus step. Two stale anchors fixed. The old-writer meta test moved from the hostile file to test_diagnostics_old_writers.py so the hostile file's baseline passes in the runner copy.
- G9 (cb7f66e): ticket handover/tickets/P5a.md has a "Build note after fix1" (file list, `guard_failures()` public, psycopg-only `db_error` v1.1 row, scan budget); textnorm.py sha256 recomputed in tests/fixtures/textnorm_manifest.json and the CHANGELOG re-copy list (c24e100d...); CHANGELOG mutant count 46 (P1a block 53 is the superseded block, P1b block 71 unchanged).

## Evidence (raw tails)
- Full suite via heavy.sh (log /home/user/build/A15fix-full.log, head 8aaaea5): `10733 passed, 454 skipped, 31 deselected, 81 xfailed in 418.66s (0:06:58)`, `PYTEST_RC=0`, `exit=0`.
- `ruff check src tests demos`: `All checks passed!` RUFF_RC=0. `ruff format --check`: `331 files already formatted` FMT_RC=0.
- `bandit -q -r src demos -ll` (uvx): rc=0, 0 issues. `python3 tools/scan_repo.py`: rc=0, no output.
- Repo guard tests plus callers, app, guards files directly: `221 passed in 5.47s`.
- Mutants: `46 of 46 good; problems: []` (log scratchpad/mut4.log).

## Pull request text (not posted)
Stacked: review the diff against the P1b head. Stacked files (not this package's work): textnorm.py, _confusables.py, _scripts.py, gen_confusables.py, the Unicode data files, the CHANGELOG P1a and P1b blocks. Evidence file: handover/reviews/P5a/evidence.md (named in the PR text, not in the public docstring). Nine `noqa: BLE001` sites are listed with a reason and a test per site in tests/noqa_sites.txt. The PR stays stacked behind P1a (PR63) and P1b (PR70).
