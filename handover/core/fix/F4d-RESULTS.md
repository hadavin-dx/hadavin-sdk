# F4d RESULTS (final docs round; baseline = HEAD e1bc257 of RR/tree-F4c; deliverable = fix.patch = `git diff HEAD`)

**Failed or uncertain first.**
1. In the 20-file doc-reader run on the first try, `tests/test_hygiene.py::test_hygiene_scan_public` FAILED: my own new text matched the repo's hardcoded-literal patterns (a clock reading `0:01:01` reads as an IPv6-like address; `\d\d:\d\d` in my regex read as a drive path `d:\d`). That was my slip. Fixed (regex written with `[0-9]`, the clock built from parts in the test, the page says `(H:MM:SS)`); docs + hygiene files re-run: 36 passed, 4 skipped (no gitleaks program here).
2. Not run: CI of any kind, Windows/macOS, a fresh clone, gitleaks (4 hygiene tests skip), the browser tests (the tree's venv has no `playwright`, so 32 skips in the 20-file run, all "could not import" / no gitleaks / root / Python 3.13). The final 20-file re-run on the final tree: see `readers-final.log` (status written at the end of this file).
3. Major 1 (evidence on the final head) is the evidence runner's job; not done here.

**Review claims checked against code**
- Major 2: confirmed. `_collect` asserts `returncode == 0` (test_docs_match_tools.py:48), so an import error FAILS. What really changes the last line (raw output, scratch folder in RR/tmp-F4d, pytest 9.2.0, 2026-11-13):
  - plain: `2 tests collected in 0.00s`, rc 0
  - `-k test_1` and `--deselect ...`: `1/2 tests collected (1 deselected) in 0.00s`, rc 0 (not plain: skip, or fail with DPLD_REQUIRE_COUNT)
  - a test file with `import nonexistent_mod_xyz`: `2 tests collected, 1 error in 0.08s`, **rc 2** (fails at the returncode assert either way)
  - a run of 61 s (test file that sleeps 61 s): `1 test collected in 61.00s (0:01:01)`, rc 0. The old regex refused this; the new one accepts it.
  - module-level `pytest.importorskip` of a missing module: the module is skipped, the count shrinks, last line plain (a stale number then FAILS, not skips); importorskip inside a test function (what all 6 browser tests do, grep above) leaves the count unchanged (`2 tests collected`, rc 0).
  - NOT run: a deselection coming from a config-file `addopts` or a plugin (the test removes PYTEST_ADDOPTS from the environment; pyproject has no addopts). The pages claim only the forms above.
  - The old claim "no browser tools can change this line" is gone from the test and from docs/tests.md; settings.md bullet reworded (docs/settings.md:129). Note: this venv has no playwright and still counts 3998, which is consistent.
- Major 3: confirmed. desk.py:1426-1427: for `last_error` in `(NO_DESCRIPTORS_ERROR, *BUSY_ERRORS)` the row is due only after `updated_at + wait_before_drive(...)` even when `auto_attempts == 0`; gate.py:61,66,82-85 give 5 s. New wording added in README.md:20,37,96, docs/tests.md:103, contract.md:178, contract.md:303 and the test constants. The test now calls `gate.wait_before_drive(0, NO_DESCRIPTORS_ERROR) == 5` and `(0, MODEL_BUSY_ERROR) == 5` (real function, not text).
- Minor 4: contract.md:178 `; If` -> `. If`.
- Minor 5: regex now `^(\d+) tests collected in [0-9.]+s( \([0-9]+:[0-9]{2}:[0-9]{2}\))?$` (same meaning as the one given, `[0-9]` for the hygiene scan). New test `test_the_total_line_parser_reads_the_forms_pytest_prints_and_refuses_the_others` (line 80): plain, with clock, deselected, error forms.
- Minor 6: the repeat test now asserts that the behaviour tests `test_replays_cannot_burn_the_cap` and `test_replay_drives_once_due` (tests/test_desk_http_edge_cases.py:1488,1496) exist. No new replay-within-resource-backoff behaviour test was added (they cover the "not due" and "due" cases; the 5 s resource case is pinned through `wait_before_drive` and the `_pending_and_due` source line only).
- Minor 7: docs/hubspot-probe.md:52 now says a bad name is refused "when you give `--yes-spend-calls 7` (the planned count; with any other count it is refused for the count first...)". hubspot_probe.py:300-305 checks the count before the name. Test pinned (`PLANNED_CALLS == 7` + both phrases).
- Minor 8 (README.md:148, not :92): new test `test_the_helper_module_that_the_readme_says_prints_nothing_prints_nothing` runs `python -I scripts/precheck.py`: rc 0, empty stdout and stderr.
- "CI sets it; no CI run has been seen": docs/settings.md:129 now says the two workflow files set it to `1` and that no CI run has been seen by whoever wrote the page. New test `test_the_settings_page_says_what_the_require_count_switch_really_does` (line 104) checks the bullet and both workflow files (.github/workflows/lint.yml:100, sonar.yml:52).

**Bug class:** a documentation claim never checked against the tool's own output (breaks: the page says what a command prints or when it skips, and the command does otherwise). Choke point: tests/test_docs_match_tools.py (already reads the pages and runs the commands).

**New counts:** 3 tests added (3995 -> 3998), 97 test files. docs/tests.md:60 says "3998 tests in 97 test files"; the existing count test checks it (`env -u PYTEST_ADDOPTS pytest --collect-only -q | tail -1` = `3998 tests collected in 0.93s`; `-qq` file lines = 97).
Siblings swept: the 2516/2465/2464 figures stay marked "earlier commit" (existing test); `grep "no automatic try yet"` lists all 5 pages + 1 source docstring + 3 tests, all updated or are code text.

**Fails before / passes after**
- failing-before.log: new tests against the old page text: 5 failed, 11 passed (q-form pins, settings bullet, page count 3995 vs 3998, probe page, repeated-request wording). The old regex on the clock form: `old: False new: True`.
- passing-after.log: docs file with DPLD_REQUIRE_COUNT=1: 16 passed (before the hygiene fix); final docs+hygiene: 36 passed, 4 skipped.
- ruff (repo pyproject, whole tree): `ruff check .` All checks passed; `ruff format --check .` 167 files already formatted.

**Final 20-file doc-reader run on the final tree (readers-final.log, DPLD_REQUIRE_COUNT=1): 1563 passed, 33 skipped, rc 0** (the earlier 1 failure is the hygiene slip, fixed; skips: no gitleaks, no playwright, root, Python 3.13).
