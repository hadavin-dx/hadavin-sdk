# P5a evidence (order 83; raw output, no judgement beyond the stated counts)

Head SHA at the end of the build: ea2d254 (branch core/P5a; the lead's order 86 WIP commit was 1a99a06; history is kept, nothing amended).
Dependency merge: core/P5a contains `origin/core/P1b` (which includes P1a), merged as a4476b8, because `guard/textnorm.py` and `scan_keyset` are not in main.
BN-24 ("not released to build start"): lead order 83 overrides; the whole ticket was built (see BN.md item 1).

## What did NOT go as planned (read first)
1. The FIRST mutation run (head 9fc53fe) was 19 of 33 good, not 33: 7 SURVIVED, 6 WRONG_REASON, 1 OTHER_TEST. Cause: weak killers (the table test iterated the table it tested, so a removed row was never checked; a psycopg test never loaded psycopg; the `os.environ` and look-alike-class cases never ran under own code; parametrised killers cannot be pinned by the runner). Killers were rewritten, not mutants dropped. Run 2 (8f79440): 30 of 33 (2 SURVIVED: the table-row mutants; 1 WRONG_REASON: gaierror). Run 3 (ea2d254): 33 of 33. All three raw logs are in this folder.
2. The 3.12 full run collected its tests at 8f79440; two later commits (9fc53fe..ea2d254: `tests/test_diagnostic_codes.py`, `tests/test_diagnostic.py`, `tests/diagnostic_mutants.py` only, no `src/` change) were after its collection. The 3.13 run collected at ea2d254. Test counts are equal (10579 passed on both). The two changed test files were re-run at ea2d254 (200 passed in the four new test files, see below).
3. 455 tests are skipped in the full runs (the Postgres service, optional extras and Windows-only tests are not present on this machine); none of the skips is in the P5a files (`pytest --co` of the four new files shows 0 skips; the psycopg rows ran).
4. `bandit` is not in the uv test group; run with `uv run --with bandit`.
5. Load average seen: 7.4 (4 cores, 3 heavy slots shared with other builders). The heavy jobs waited 16 to 30 minutes for a slot. No test was timing sensitive in a way that failed.
6. NOT done by me by design: the EGM reviews and the evidence-runner pass (lead's job). No wheel-install locator run (`test_locator_on_installed_layout` is REPORT-ONLY in the ticket and was not run: not done).

## Commands and results at the head
```
$ uv run --all-extras --group test ruff check .  /  ruff format --check .  /  bandit
$ uv run --all-extras --group test ruff check .
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
$ uv run --all-extras --group test ruff format --check .
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
336 files already formatted
$ uv run --with bandit bandit -ll -q -r src   (bandit is not in the uv test group)
bandit exit/issue count: exit=0 issues=0
```
```
$ <build>/heavy.sh uv run --python 3.13 --all-extras --group test pytest -q -p no:cacheprovider   (collected at ea2d254)
10579 passed, 455 skipped, 81 xfailed in 463.55s (0:07:43)
$ PYTHONPATH=$PWD/src <build>/heavy.sh <build>/venv312/bin/python -m pytest -q -p no:cacheprovider   (python 3.12.1; collected at 8f79440, see item 2)
10579 passed, 455 skipped, 81 xfailed in 601.09s (0:10:01)
$ uv run --all-extras --group test pytest tests/test_diagnostic.py tests/test_diagnostic_codes.py tests/test_diagnostic_validation.py tests/test_diagnostic_hostile.py -q
200 passed in 1.89s   (at ea2d254)
```

## Fail-before (the new surface has no old behaviour; the honest fail-before is the hostile rows against today's writers)
Throwaway worktree `<build>/P5a-failbefore` at a4476b8 (the branch base, i.e. the P1b merge) plus ONLY `codes.py`, `tests/data/__init__.py`, `tests/data/c18a_hostile_corpus.py`, `tests/data/c18a_oracle.py` and `tests/test_diagnostics_old_writers.py` (git status there: 3 untracked entries, nothing else).
```
base (a4476b8 + 5 files):  $ pytest tests/test_diagnostics_old_writers.py -q
53 passed, 81 xfailed in 78.26s
head (ea2d254):            $ pytest tests/test_diagnostics_old_writers.py -q
53 passed, 81 xfailed in 79.12s
```
Equal on base and head (P5a changes no writer). 134 rows went through `run_tick` (exception rows) or `extract.extract` (validation rows): 53 clean, 73 LEAK a canary (OLD_WRITER_LEAKS), 8 CRASH the writer (OLD_WRITER_CRASHES: SystemExit 1, RuntimeError 3, RecursionError 1, AttributeError 3), 0 "no path". All 81 are strict xfails naming P5b3 (R3c). Frozen tuples are in the test file.
Also on base, the four new test files fail at collection with `ModuleNotFoundError: No module named 'hadavin_sdk.guard.diagnostic'` ("new surface: no old behaviour; guarded by mutants").
An earlier base run had 1 FAILED (HC-builtin_text-03 leaked but was not yet in the frozen tuple after its factory was corrected); it was added and both trees re-run (the numbers above).

## Mutants (P1m runner, `tests/diagnostic_mutants.py`, 33 mutants), run 3 at ea2d254
```
$ <build>/heavy.sh uv run --all-extras --group test python tests/diagnostic_mutants.py   -> 33 of 33 good; problems: []
ok  KILLED       code set: a member is removed  [test_code_set_is_the_frozen_list]
ok  KILLED       table: NotFound row removed  [test_pinned_code_per_class]
ok  KILLED       table: VaultError set back to config_invalid  [test_pinned_code_per_class]
ok  KILLED       table: TextnormError row removed  [test_textnorm_error_family_maps_to_scan_failed]
ok  KILLED       identity check removed from the own-class lookup  [test_spoofed_class_gets_no_own_code]
ok  KILLED       step token: a Where name as text is accepted  [test_step_token_is_closed_and_final]
ok  KILLED       timeout is not tested before os error  [test_family_order_timeout_before_os_error]
ok  KILLED       gaierror handled as a plain os error  [test_gaierror_gives_gai_not_errno]
ok  KILLED       a bool is accepted as a number  [test_facts_bounds_table]
ok  KILLED       the upper bound is off by one  [test_facts_bounds_table]
ok  KILLED       sqlstate uses match instead of fullmatch  [test_fact_patterns_use_fullmatch]
ok  KILLED       phase: 08 and 28 swapped  [test_psycopg_phase_is_sqlstate_class_only]
ok  KILLED       psycopg also detected by module name  [test_psycopg_claimed_module_name_is_not_trusted]
ok  KILLED       facts merged from the more than 12 limit removed  [test_more_than_12_facts_keeps_priority_12]
ok  KILLED       group: nested groups are walked  [test_exception_group_takes_first_member_code]
ok  KILLED       internal_bug is decided on any counted frame, not the raise frame  [test_internal_bug_is_decided_on_the_raise_frame]
ok  KILLED       built-in identity check removed  [test_internal_bug_is_decided_on_the_raise_frame]
ok  KILLED       the traceback step bound is removed  [test_long_traceback_is_foreign]
ok  KILLED       diagnose catches BaseException  [test_baseexception_from_hostile_getattr_propagates]
ok  KILLED       the fallback fp is changed  [test_fallback_fp_is_pinned]
ok  KILLED       kind identity check removed  [test_kind_identity_rule]
ok  KILLED       the foreign package list is not checked  [test_off_list_foreign_class_prints_foreign_class]
ok  KILLED       the fp ignores the relative path  [test_locator_and_fp]
ok  KILLED       frame rule a removed  [test_frame_rule_a_name_must_be_exactly_str]
ok  KILLED       frame rule b removed  [test_frame_rule_b_globals_must_be_the_module_namespace]
ok  KILLED       frame rule c removed  [test_frame_rule_c_filename_must_be_the_module_file]
ok  KILLED       the per-frame try/except is removed  [test_frame_check_that_raises_means_not_counted]
ok  KILLED       the line cap is off by one  [test_grammar_a_shape_and_cap_boundary]
ok  KILLED       the line cap is removed  [test_grammar_a_shape_and_cap_boundary]
ok  KILLED       pydantic input is requested  [test_pydantic_error_reads_are_closed_ast]
ok  KILLED       more than 5 types are printed  [test_more_than_5_errors_gives_plus_n_more]
ok  KILLED       the +N more tail is wrong  [test_more_than_5_errors_gives_plus_n_more]
ok  KILLED       a type outside the closed list is printed  [test_a_type_outside_the_closed_list_prints_other]
```
Runs 1 and 2: `mutants-run1-at-9fc53fe.log` (19/33) and `mutants-run2-at-8f79440.log` (30/33).
Equivalent, stated and not run: removing `type(frame.f_code.co_filename) is str` from frame rule (c) (no such frame can be built); a mutant of `StepToken.of`'s "in TICK_STEPS" check (the constructor checks the same set again, so no input tells them apart; the mutant that removes the Where-name handling is run instead).
Not mutated (test only): the corpus meta tests, the old-writers file, the MRO walk (no subclass row in the table test).

## Counts
- Corpus: 161 rows = 135 active + 24 later + 2 not applicable; 24 classes; all 51 ledger ids covered (`test_every_ledger_id_is_covered`).
- New tests: 200 in four files (+ 134 in the old-writers file).
- Time: started 11:58Z; commits 1a99a06 .. ea2d254 before 12:50Z.

## Order 93 (head 21ca680; merged origin/main 13ebfaf)
- Guards: 9 `except Exception` sites remain in `guard/diagnostic.py`, each `# noqa: BLE001 - <reason>` on the same line, each calling `_guard_failed(site)` (a count by site name; no text, no type of the exception). Two sites were narrowed away (`SafeToken.of`, `StepToken.of`). Four P1b test guards and four P5a test guards were narrowed (`pytest.raises`, `ValidationError`, `ConfigError`, `SystemExit/RuntimeError/AttributeError`). List: `noqa_sites.txt`. Tests: `tests/test_diagnostic_guards.py` (63 tests: caught, recorded, KeyboardInterrupt/SystemExit/GeneratorExit propagate, per site; plus the line-format check).
- Merge: plain merge, two conflicts (CHANGELOG.md, app.py: kept `is_live` and the pinned-Unicode call). Merge also broke three things, all fixed: `config._RenamedStage` added to `OWN_CODES` (config_invalid) and the pinned table test; `tests/test_textnorm_app.py` used the removed `dev_cfg` and `deferred.LIVE`; two mutant search strings re-copied.
- ruff check: All checks passed. ruff format --check: 340 files already formatted. bandit -ll -r src: rc=0 (bandit.txt).
- Full py3.13 (own env, import path checked to be this worktree): 10741 passed, 455 skipped, 81 xfailed (pytest313-final.log). Full py3.12: 10741 passed, 455 skipped, 81 xfailed (pytest312-final.log).
- Mutation (P1m runner, all 33): 33 of 33 good; problems: [] (mutants-final.log). A first final run showed 32/33 because a search string had a stale indent; fixed, re-run.
- Blame of the lint debt (BLE001 is not in the ruff select list of this repo): origin/main already holds 62 `noqa: BLE001` sites, none from P5a: 21 from K5-core, 8 each from Slice 2 P7, P3 and K3, 5 Slice 1, 4 tick exit code, 2 Ask-your-data P2, 2 Slice 2 P3b, and the rest (a few each) older. All are older than this PR.
