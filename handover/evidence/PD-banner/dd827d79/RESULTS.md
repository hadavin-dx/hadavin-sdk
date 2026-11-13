# EVIDENCE RUNNER results: PD banner batch 9, head dd827d79e00bea6da81e757e0fa0746bbbd3449d (previous head 07bfda12)

Records only, no judgement. Run on the cloud box 2026-11-13 (about 02:20Z to 03:20Z). Worktree /home/user/build/wt/ER-pdbanner9 (detached at the head, HEAD verified equal, `git status` clean before and after). Venv /home/user/build/pdbanner-b8-venv reused; PYTHONPATH set to this worktree's src; module path confirmed as `/home/user/build/wt/ER-pdbanner9/src/hadavin_sdk/__init__.py`. Raw logs: /home/user/build/evidence-raw/pdbanner9-runner/ (not in git). No pyproject or uv.lock change.

## FAILURES AND DEVIATIONS FIRST
1. **banner_mutants: 1 BAD row of 283: `B12 the lists get a default again (nothing real unless said)` SURVIVED** (no test failed). Reproduced twice (once in chunk 0-100, once alone) and by hand in a scratch copy: with the mutation applied, `tests/test_mode_banner.py::test_the_lists_are_required_so_an_unchecked_call_cannot_say_nothing_real` still PASSES. Reason seen in the hand run: `_banner_for("demo")` and `_banner_for("demo", real_services=[])` still raise TypeError, but now because the keyword-only `overridden` has no default ("missing 1 required keyword-only argument: 'overridden'"); the positional call raises because of the `*`. So the killer cannot tell the mutated code from the real code. Not fixed (I record only).
2. **`copy.deepcopy` of a built App raises `TypeError: cannot pickle '_thread.lock' object`** from deepcopy itself (before any banner call); so "deepcopy gives unconfirmed" could not be observed, the copy cannot be made at all. Recorded, not judged.
3. The shell environment had `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_CA_BUNDLE` set (names only seen, values never printed). My first focused pytest run (338 passed) had them set; I re-ran it with all three unset (`env -u`) and every later run used `env -u`. Both runs passed.
4. My own slip: the first mutant chunk (0-100) was launched while I assumed about 12 s per row; it took 97 s. No harm. The 25-26 re-run waited in the heavy-slot queue behind other agents' jobs.
5. Not run (cloud limit): full pytest, Playwright, one-run complete banner_mutants.

## (1) Focused pytest (no cloud variables set)
Files: tests/test_mode_banner.py tests/test_demo_only_guard.py tests/test_demo_only_guard_ci.py tests/test_banner_mutant_table.py tests/test_repo_rules.py tests/test_no_reference_material.py. The other files in `git diff 07bfda12 dd827d79 --name-only` are src/tools/templates/CHANGELOG, the mutant table (covered by test_banner_mutant_table) and tests/mode_banner_probe.js (used by test_mode_banner). Result: **338 passed in 19.25 s, rc 0** (pytest-focused-nocloud.log; first run with cloud variables set: 338 passed, 21.57 s).

## (2) Fail-before
Second worktree at 07bfda12 (src, tools, templates of that commit), with these files copied in from dd827d79: tests/test_mode_banner.py, tests/test_demo_only_guard.py, tests/test_banner_mutant_table.py, tests/banner_mutants.py, tests/mode_banner_probe.js. Command: those three test files, `-rA`. Result: **287 tests, 255 passed, 32 failed**: matches the builder's figures. (Worktree removed afterwards.)
- The 32 failing tests by name: `fail-before-failing-tests.txt` next to this file (31 in test_mode_banner.py / test_demo_only_guard.py plus `test_banner_mutant_table.py::test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once`).
- "New or changed" by AST comparison of test function bodies old vs new: **59** (list: `new-or-changed-tests.txt`), builder says 60. Of those 59, **31 fail on the old code and 28 pass on the old code (pins)**; the 28 names are in `fail-before-pins-passing-on-old.txt`. The 32nd failure (the mutant table test) is a changed test not counted in the 59 (it is a changed function in that file's logic through the table content, not its body). Two lines `test_needs_folder` and `test_env` seen in the log with FAILED are inner pytest runs printed by tests that plant files; they are not outer failures (outer summary says 32 failed).

## (3) banner_mutants, all rows, in 7 chunks (driver /home/user/build/evidence-raw/pdbanner9-runner/driver.py calls `tools.mutation_runner.run_mutants` with the same arguments as `tests/banner_mutants.py`: tests [T_MB, T_G], extra_dirs tests/tools/templates/demos)
- Real row count: **283** (matches builder). Chunks 0-100, 100-130, 130-160, 160-190, 190-220, 220-250, 250-283; 40 to 97 s each. Each chunk wrote a checkpoint json.
- Good: **282 of 283**. BAD: **1** (B12, above; verdict SURVIVED).
- `shared_first_lines` over all 283 first failing lines: **[]** (clean). `non_unique_rows()`: **[]** (clean).

## (4) stage_mutants
**37 rows, 37 good, 0 bad** (one chunk, 43 s).

## (5) Static checks (all at dd827d79, no cloud variables)
- `ruff check`: All checks passed (rc 0). `ruff format --check`: 331 files already formatted (rc 0).
- `bandit -ll -r src tools`: rc 0, no issue lines (only tool warnings such as "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389").
- `tools/scan_repo.py`: rc 0, no output. `tools/demo_only_guard.py`: rc 0, no output.
- gitleaks `origin/main..HEAD`: 20 commits scanned, no leaks found, rc 0.
- `check-no-handover-files.sh wip/cloud-pd-banner dd827d79`: rc 0, no output.

## (6) Hostile probes (made-up data; fake secrets built from parts). Script: probes.py, log: probes.log
Tone is the `tone` of `App.mode_banner()`; an app is "sealed" with `_seal(())` so an untouched one says `demo`.
- Untouched sealed app: demo. Each part replaced: hooks members request_approval, execute, verify, rollback, post_card, level_override, toolbox, validate_proposal, hold_run_ids, restored_key; a new Hooks; a tool entry; app.store/audit/executor/limits/registry/config/approvals; runtime.store/audit/registry/llm/detector/limits; the approvals channel; a source added; a store attribute: **all 28 read unconfirmed**.
- Sources: source added then re-sealed: demo; new attribute on it: unconfirmed; attribute value replaced in place: unconfirmed; entry replaced by an equal-looking object: unconfirmed.
- Freed-object id reuse: I could not get an object with the old id (20000 tries); the sealed record keeps the old object alive, so reuse cannot happen while the seal exists. Replacing the store with another object: unconfirmed. (Not an observed reuse.)
- `app.runtime=object()`: unconfirmed; `runtime=None`: unconfirmed; `sources=None`: unconfirmed, no raise, no warning.
- Mixed key types in `sources` (int, str, tuple, None): added after seal: unconfirmed; sealed with them (int, str, None): demo.
- `copy.copy`: demo (same parts). `dataclasses.replace`: unconfirmed. `copy.deepcopy`: raised TypeError in deepcopy itself (see failures).
- `app.overridden` reset to None, ("tools",), ["x"], "tools", 5: unconfirmed; to `()`: demo (the same as the sealed record). `_sealed=None`, forged `((),())`, forged `("x",)`: unconfirmed. Extra attribute set on the app: unconfirmed.
- Page script under node (tests/mode_banner_probe.js against templates/mode-banner/mode_banner.js), shown tone, no throw, no HTML writes in every case: demo + non-empty overridden: unconfirmed; demo + duplicate names: unconfirmed; unconfirmed with names in the wrong order: unconfirmed; quiet + overridden: unconfirmed; demo + empty overridden: demo; demo with no overridden field: demo; overridden not a list: unconfirmed.
- Masker (`tools/demo_only_guard.py::_hide_secrets`): quoted value with space, double-quoted value, inner escaped quote, ampersand after a token: secret hidden. URL password containing `@` and `/` or a second `@`: hidden, host kept. `Authorization: Digest ...`: whole rest of line hidden. Bare `Bearer` + 11 characters: shown; + 12: hidden. Bare `Basic` + 7: shown; + 8: hidden. `bypass=true`: shown; `bypass_key=<fake>`: hidden. (11 and 7 stay visible by the table's own rule.)
- 10000-character and 200000-character lines (pairs, a secret at the end, `://` followed by `@` run, a run of `=`): 0.001 to 0.04 s, secret at the end hidden, no raise.
- Non-UTF8 bytes plus a 10000-character run plus a fake password in git's message (`_git_failure`): no raise, message 283 characters, secret not present, bad bytes shown as replacement characters. A URL credential and a password pair in git's message: both hidden. `printable` on 20000 repeated control/escape characters: no raise.

## Processes and cleanup
Started and finished by me: focused pytest x2, fail-before pytest, 8 mutant driver runs (7 banner + 1 re-run of B12) + 1 stage run, probes.py, ruff, bandit, scan_repo, demo_only_guard, gitleaks, node probe calls. No process of mine is still running (pgrep checked, 0). Nothing killed. Second worktree and the scratch copy removed; worktree /home/user/build/wt/ER-pdbanner9 kept (clean, HEAD dd827d79). Nothing committed or pushed.

RUN ON LAPTOP: hadavin-sdk dd827d79e00bea6da81e757e0fa0746bbbd3449d pytest -q full + banner_mutants complete
