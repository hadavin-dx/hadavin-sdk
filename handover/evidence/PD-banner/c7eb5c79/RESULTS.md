# Evidence for PD Part 6 head c7eb5c79 (full sha c7eb5c7940e95cbf38b3f2ee43e9f27a90e6120b), remote wip/cloud-pd-banner

EVIDENCE RUNNER output. Raw files are in `raw/` next to this file. Nothing here judges the work. Not committed.
Base used for the diffs: origin/main 51c9fc4f (merge-base 2a8c2aac). Python 3.13.18 (venv q8c1-b17fix) and 3.12.3 (new venv, same pins as pyproject
plus `anthropic[vertex]==2.1.0`). Every run printed `hadavin_sdk.__file__` under the matching worktree (first line of each raw file).

## FAILURES AND GAPS FIRST

1. **FAILS ON THE HEAD (both Python 3.12 and 3.13): `tests/test_stage_names.py::test_the_old_stage_word_is_gone`.**
   It flags `tests/test_mode_banner.py:3597` (`app = _sealed_app(tmp_path, f"stage-{stage}")`) and `:3598`
   (`object.__setattr__(app.config, "environment", stage)`) as "value after a stage name". This is the new batch-12 test
   `test_a_stage_changed_after_build_reads_unconfirmed`. Proof it is caused by the head: on a pristine 06ed4b4c checkout
   `test_stage_names.py` + `test_mode_banner.py` = 268 passed (`raw/stage-06ed-pristine.txt`). `test_stage_names.py` is not in the
   builder's focused list, so this is probably not yet seen. CI runs the full suite, so it would fail CI. Raw: `raw/n312/test_stage_names.txt`, `raw/n313/test_stage_names.txt`.
2. `tests/test_p5p6_followups.py::test_each_network_kind_names_its_hosts` failed on the first Python 3.12 run only because my fresh venv had no `anthropic`
   extra (ModuleNotFoundError). After installing `anthropic[vertex]==2.1.0` it passes (46 passed, `raw/n312b/`). It passed on 3.13 first time. Environment, not the head.
3. Not run (limits): full suite, Playwright, live/Postgres (the two `*_postgres` files skip with no database: 1 skipped each), anything networked.
   `test_k3_pilot_env` 1 skip (both Pythons). The node-based banner page tests ran (node v22.23.4; none skipped in test_mode_banner).
4. The guard masker is WEAKER than main in 3 probe rows: `authorization=Bearer <8, 10 or 11 chars>` stays visible in the guard,
   hidden by `hadavin_sdk.guard.redact` on main (see section 7). The 12+ / 8+ rule and the `token=` name form equal main.
5. ruff waivers: `BLE001` is waived for two whole files (`app.py`, `mode_banner.py`) but the comment in pyproject.toml says "four sites"; I count five
   `except Exception` in the two files (app.py 295, 312, 471; mode_banner.py 731, 759). Site 471 is the approval-card post (not a banner site). Whole-file waiver
   also covers any future broad except in those files.
6. ci.yml bandit command is `bandit -q -r src demos tools -ll` (line 195): it does NOT scan `tests/`. `bandit -r tests -ll` exits 1 (74 medium, 4390 high, 188 low), but every finding is in
   files this head did not change (e.g. tests/demo_askdata/corpus.py x185, test_p7_tick.py, test_ci_gitleaks_scope.py).
7. Observation from the page probes: the page script paints a banner whose tone is `demo` with ANY text or tag as given (reworded text, tag "LIVE"). Existing test
   `test_the_page_trusts_the_tone_it_is_given_and_python_checks_the_sentences` states this on purpose (Python is the check). Recorded, not a test failure.
8. `copy.copy(app)` keeps the made-up banner (same parts); `copy.deepcopy` raises TypeError; `app._seal(())` raises TypeError. Matches the tests (by design).

## (1) Focused tests (36 files: all test files that import mode_banner, demo_only_guard, hadavin_sdk.app, banner_mutants, plus the five named)
Per-file results in `raw/n312/`, `raw/n313/`, summaries `raw/n312.summary`, `raw/n313.summary` (and `raw/n312b/` for the p5p6 rerun).
| Python | passed | failed | skipped |
|---|---|---|---|
| 3.13.18 | 1529 | 1 (test_stage_names) | 3 |
| 3.12.3 | 1525 (+46 after p5p6 rerun with anthropic installed) | 2 (test_stage_names, p5p6 = env, fixed on rerun) | 6 |
Named files on both Pythons, all pass except the one above: test_mode_banner 176, test_demo_only_guard 147, test_demo_only_guard_ci 8, test_banner_mutant_table 20,
test_changelog_numbers 6, test_repo_rules 40, test_scan_repo 31 (1 skip on 3.12 list line), test_workflow_files_parse 4.

## (2) Mutant table (`python tests/banner_mutants.py <names>`, head worktree, Python 3.13)
Table has 320 rows. Raw: `raw/mut_req.txt`, `raw/mut_req2.txt`, `raw/mut_sample.txt`, sample list `raw/sample.txt`.
| Group | rows | killed good | problems |
|---|---|---|---|
| R12B1, R12C1, R12C2, B12 | 4 | 4 | none (B12 is KILLED on this head by `test_pin_the_lists_are_required_so_an_unchecked_call_cannot_...`) |
| all R11* (10), R10* (25), R9D* (14) | 49 | 49 | none |
| sample of 60 of the other 267 rows, `random.Random(12).sample(rest, 60)` in name order | 60 | 60 | none |
`git status` of the head worktree after the runs: clean (the runner mutates temp copies). Main repo had no leftover mutation. Not run: the other 207 rows.

## (3) Fail-before (head's tests/ files copied onto detached dd827d79 and 06ed4b4c; src, tools, templates left old)
Files run (per-file, Python 3.13, `--tb=line`): test_mode_banner, test_demo_only_guard, test_demo_only_guard_ci, test_banner_mutant_table, test_changelog_numbers,
test_repo_rules, test_scan_repo, test_workflow_files_parse, test_stage_names. Raw: `raw/fb-dd82/`, `raw/fb-06ed/`, first lines `raw/fb_lines.txt`.
| Tree | passed | failed |
|---|---|---|
| head | all pass except test_stage_names (1) | 1 |
| 06ed4b4c + new tests | 6 fail: 2 test_banner_mutant_table, 2 test_changelog_numbers, 1 test_mode_banner (`a stage changed after build (demo to pilot) was read as 'quiet'`, line 3600), 1 test_stage_names | 6 |
| dd827d79 + new tests | 33 test_mode_banner + 9 test_demo_only_guard + 3 test_banner_mutant_table + 4 test_changelog_numbers + 1 test_stage_names = 50 fail | 50 |
First failing line of each failing test is in `raw/fb_lines.txt` (all AssertionError with a message, listed with file:line).
`test_pin_*`: 61 tests across the 6 files holding them (test_banner_mutant_table 9, test_changelog_numbers 2, test_demo_only_guard 15, test_demo_only_guard_ci 1, test_k5_round6 1, test_mode_banner 33):
61 pass on head, 61 pass on dd827d79, 61 pass on 06ed4b4c (`raw/pins-new.txt`, `pins-dd82.txt`, `pins-06ed.txt`). (test_k5_round6's pin is old, not changed by the head.)
Fail on old code ONLY by a missing new name: ImportError/collection errors: none (0). One AttributeError: `module 'hadavin_sdk.app' has no attribute '_UNREADABLE'` (dd827d79 only, test_each_unreadable_shape_seals_as_unreadable...; it passes at 06ed4b4c).
`_given`: test helper `_given()` in tests/test_mode_banner.py line 2217 returns `getattr(app_mod, "_Given", tuple)(names)`, so it runs on trees with no `_Given`; the pin on `_given_overrides` passes on both old trees. Confirmed tolerant.
Note: test_stage_names fails on both old trees only because the new test file trips it (same cause as failure 1).

## (4) Suppressions
`git diff origin/main...c7eb5c79` added lines: noqa 0, type: ignore 0, fmt: skip 0, pragma: no cover 0 (also nosec, NOSONAR, pylint: disable, ruff: noqa: 0). Removed lines holding a marker: 3 (not examined).
pyproject.toml diff vs origin/main (only change; uv.lock unchanged), under `[tool.ruff.lint.per-file-ignores]`:
```
+"src/hadavin_sdk/app.py" = ["BLE001"]
+"src/hadavin_sdk/mode_banner.py" = ["BLE001"]
+"tests/fixed_run.py" = ["S603"]
+"tools/demo_only_guard.py" = ["S603"]
+"tools/scan_repo.py" = ["S603"]
```
plus explanatory comment lines. 5 per-file waivers added (2 rules, 5 files). No dependency change.

## (5) Lint and bandit (head, ruff 0.17.1)
- `ruff check .` rc=0 "All checks passed!" (3.13 venv ruff; 3.12 venv ruff also rc=0). `ruff format --check .` rc=0, 334 files already formatted.
- `bandit -q -ll` on the 16 changed .py files in src, tools, tests: rc=0, no output.
- ci.yml command `bandit -q -r src demos tools -ll`: rc=0 (only nosec warnings, e.g. src/hadavin_sdk/tools.py:389, not changed by the head). ci.yml does not scan tests (see gap 6).

## (6) Hostile probes (head, `raw/probes.py`, `raw/probes_page.py`; output `raw/probes_py.txt`, `raw/probes_page.txt`)
All reads of the banner after a hostile change gave tone `unconfirmed` / tag UNCONFIRMED except the expected controls:
- sealed app: deleted tool spec, deleted/replaced registry.agents entry, cleared config.sources, toolbox `_fns` replaced, toolbox specs entry replaced / cleared, config.sources attribute removed,
  registry.tools = None, config.systems = None, config.systems cleared, system entry added, `dataclasses.replace(app)`, never-sealed app, forced `object.__setattr__(config.environment, 'pilot' / 'prod')` from demo: all unconfirmed.
- `copy.copy(app)`: demo (same parts; by design). `copy.deepcopy(app)`: TypeError "an App cannot be deep-copied". `app._seal(())`: TypeError; the app's banner afterwards: unchanged (demo if it was sealed, unconfirmed if not).
- surprise exception (`class Surprise(Exception)`) at each site: app.py 295 (`_stage` raises; `_connected_parts` raises) -> unconfirmed, one warning "connected parts could not be read (Surprise)";
  app.py 312 (`banner_or_unconfirmed` raises) -> unconfirmed, warning "the app could not be read (Surprise)"; mode_banner.py 731 (`banner_from_config` raises) via app and direct -> unconfirmed, warning "mode banner could not be built (Surprise)";
  mode_banner.py 759 (words getter raises) -> unconfirmed fixed-default banner; 731 + 759 together -> unconfirmed. app.py 471 (channel `post_card` raises Surprise) -> `Delivery(ok=False, reason='Surprise')`, no crash (not a banner site).
  A built app given `channel=` is unconfirmed by design (an override is recorded), so the post-card check used a separate app.
- Page script (node): `overridden` missing, null, a list, a string, demo tone with real services listed, quiet tone with overridden missing/null, mode=prod under demo tone: all painted `unconfirmed`. Undefined banner: unconfirmed.
  Demo tone with reworded text or tag "LIVE": painted as demo with those words (see observation 7).

## (7) Guard masker probe (`raw/probe_masker.txt`, compared with `hadavin_sdk.guard.redact(...).text`; src/hadavin_sdk/guard.py is unchanged vs main)
- `token=Bearer <11 chars>` visible and `token=Bearer <12>` hidden; `token=Basic <7>` visible and `<8>` hidden: equals main (expected).
- Differences (6 of 36 rows): header form `Authorization: Basic <4, 6, 7 chars>` is hidden by the guard, visible on main (guard stricter);
  `authorization=Bearer <8, 10, 11 chars>` is visible in the guard, hidden on main (guard weaker; 3 rows). `authorization=Basic <4..7>` visible in both.

## Housekeeping
Worktrees ER-pdbanner12-{new,dd82,06ed} removed at the end. No spend, no secrets, no network script run, no prompt appeared, nothing under handover/ committed.
A foreign pytest process (venv pdbind-b8, mutant run) was running; not mine, left alone.
