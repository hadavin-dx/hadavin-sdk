# Evidence, Part 6 (demo-only banner), head 2cf0f742b107e48226e1f66e5368bca7c982015d (origin/wip/cloud-pd-banner)

Evidence runner: records only, no judgement, nothing fixed. Clean detached worktree of that sha, `git status` clean before and after.
Raw logs: `/home/user/build/evidence-raw/pdbanner-2cf0f742/` (outside the repository). Times are real clock, UTC.
Parent of the delta: dd5c7242. Delta: 11 files (ci.yml, CHANGELOG, mode_banner.py, mode_banner.js, banner_mutants.py, mode_banner_probe.js, 3 test files, demo_only_guard.py and .toml).

## Failed or not run (first)

1. **Full pytest FAILED: exit 1, 225 failed, 10363 passed, 1 skipped, 28 deselected, 30 errors (253 s).** Run twice (first on a Postgres cluster the suite shared with a parallel check, then on a fresh cluster with PGHOST/PGPORT set): identical counts both times. Split of the failures by cause:
   - **76 failures: `.github/workflows/ci.yml` at this head is not valid YAML** (`yaml.scanner.ScannerError: mapping values are not allowed here`, line 87, column 81, the step name "Demo-only folder copy run (only when the repository has the folder: tests must pass without it)" holds a colon followed by a space). `tests/test_ci_gitleaks_scope.py`: 76 failed, 12 passed on 2cf0f742; the same file: 88 passed on dd5c7242. ci.yml parses on 2a8c2aac, dd5c7242 and origin/main.
   - **1 failure: `tests/test_stage_names.py::test_the_old_stage_word_is_gone`**: it reports the old stage word quoted in the new `tests/test_mode_banner.py` at lines 228, 267 and 444. `test_stage_names.py` + `test_peel_run_id.py`: 130 passed, 1 failed, 1 skipped on 2cf0f742; 131 passed, 1 skipped on dd5c7242.
   - **about 148 failures and 30 setup errors in Postgres-backed tests** (`transaction is not read-only (SQLSTATE 25006)`, `TypeError: sequence item 0: expected str instance, bytes found` in store/migrate.py, and similar). The same three files (test_cli, test_verify_readonly, test_k2_migrations) give 31 failed, 46 passed on dd5c7242 as well as on 2cf0f742, on my own Postgres 16.15 cluster (also with the older venv of another runner): so they are not caused by this delta. I did not find the cause in this environment. The known dblink-connect test is among the failing Postgres tests; it is not separated out.
2. **`python tests/stage_mutants.py`: exit 1, did not run any mutant**: `RuntimeError: the unmutated copy does not pass its tests` (it runs `tests/test_stage_names.py`, which fails at this head, item 1 above). 0 of 37 judged.
3. **`python tests/banner_mutants.py`: exit 1, 78 of 79 good.** The not-good row: `G6 a missing product root is not a hit`: `BAD ERROR ... [SNIPPET NOT FOUND]` (the text the mutant must replace was not found in tools/demo_only_guard.py at this head). Also recorded: `B13 ... CRASH` counts as good ("ok  CRASH"). 77 rows are `ok  KILLED`.
4. Not run: nothing from the brief list was skipped. The "own Postgres" is a private cluster on 127.0.0.1 port 57332 (stopped at the end).

## Table

| Command | Exit | Last line | Seconds |
|---|---|---|---|
| (1) `HADAVIN_REQUIRE_NODE=1 pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh, run 1 | 1 | 225 failed, 10363 passed, 1 skipped, 28 deselected, 2 warnings, 30 errors in 265.13s | 267 |
| same, run 2 (fresh cluster, PGHOST/PGPORT set) | 1 | 225 failed, 10363 passed, 1 skipped, 28 deselected, 2 warnings, 30 errors in 251.18s | 253 |
| (2) `python tests/stage_mutants.py` via heavy.sh | 1 | RuntimeError: the unmutated copy does not pass its tests | 2 |
| (3) `python tests/banner_mutants.py` via heavy.sh | 1 | 78 of 79 good; problems: ['G6 a missing product root is not a hit'] | 46 |
| `ruff check src tests demos tools` | 0 | All checks passed! | <1 |
| `ruff format --check src tests demos tools` | 0 | 324 files already formatted | <1 |
| `uvx bandit -ll -r src demos tools` | 0 | Medium 0, High 0 severity (23 Low, below the -ll cut) | 2 |
| `python tools/scan_repo.py` | 0 | (no output) | <1 |
| `python tools/demo_only_guard.py` | 0 | (no output) | <1 |
| `python tools/demo_only_guard.py --without-folder-if-present` (as ci.yml) | 0 | (no output; the repo has no demo_only folder) | <1 |
| `gitleaks git --log-opts=origin/main..HEAD` | 0 | 4 commits scanned, no leaks found | 1 |
| fail-before: new/changed test files (test_demo_only_guard, test_demo_only_guard_ci, test_mode_banner, mode_banner_probe.js) copied onto dd5c7242 src/tools/templates | 1 | 81 failed, 13 passed in 1.84s | 3 |
| the same 3 test files on 2cf0f742 | 0 | 94 passed in 5.59s | 6 |

Note on fail-before: the brief names old head dd5c7242 (the previous round), not origin/main (a8b4d8e8). Not run against origin/main.

## Hostile probes (planted only in a throwaway worktree of 2cf0f742, `demo_only_guard.py`; raw: probes.log)

| Probe | Exit | Output |
|---|---|---|
| baseline, no plant | 0 | none |
| symlink `src/hadavin_sdk/linkto_demo` -> `../../demo_only` (folder exists) | 1 | `src/hadavin_sdk/linkto_demo: symlink-in-product-root` (plus `copy-run-not-wired`, because the folder existed) |
| `x DEMO_ONLY/data` in a templates file (folder exists / folder absent) | 1 / 1 | `templates/mode-banner/probe_upper.txt:1: names-demo-only-folder` |
| `load demo_only\fixtures\a.json` in a templates file (folder exists / absent) | 1 / 1 | `names-demo-only-folder` |
| `see Demo_Only\data` mixed case | 1 | `names-demo-only-folder` |
| directory `templates/DEMO_ONLY/` (upper-case folder name) | 1 | `templates/DEMO_ONLY: folder-inside-product-root` |
| `banner_from_config`, component with unknown kind `zzz_unknown_kind`, stage pilot | returned | tone `real`, real = ('component signer',) (shown as real, not hidden); same at stage demo |
| `banner_from_config`, empty kind | raised | ValueError: a component without a name or a kind cannot be placed in the banner |
| `banner_from_config`, stage `dev` | raised | ValueError: mode 'dev' is not one of demo, pilot, prod |
| `banner_from_config`, 1000-character name | raised | ValueError: the name shown for a service must be plain words (... at most 40 characters ...) |
| `banner_from_config`, name containing the word "Demo" | raised | the same ValueError |
| page script (`mode_banner.js` via `tests/mode_banner_probe.js`) scenarios throwing-doc, throwing-getter, proxy, throwing-list, failing-append, null-el | 0 each | no exception escaped; each shows the UNCONFIRMED banner text (throwing-doc and failing-append: no child lines, text set directly; null-el: target null, `shownTone` demo) |

My first probe-3 script passed bare tuples instead of setting objects and raised the wrong error; the table shows the rerun with proper objects (both are in probes.log).

## Tokens
This runner's own token use is not measured here.
