# Evidence PD part 6 (mode banner, demo-only folder guard): head dd5c72422b47a3dd7128a1a48e7b48983ad253c9

EVIDENCE RUNNER: records only, no judgement. Head from `origin/wip/cloud-pd-banner`, clean detached worktree `/home/user/build/ER-pdbanner` (`git rev-parse HEAD` equals the sha, `git status` clean after all runs). Own venv, own temp folder, no cloud credentials set. Raw logs outside the repo: `/home/user/build/evidence-raw/pdbanner-dd5c7242/`.

## Not run / deviations (first)
- **Full suite: 1 test failed in the first complete run** (`tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`). Cause in the log: the database server's own `dblink_connect('dbname=postgres')` looked for the default socket `/var/run/postgresql/.s.PGSQL.5432`, which does not exist because my private Postgres listens on port 57213. Not a banner file. After restarting my own Postgres with `PGHOST=127.0.0.1 PGPORT=57213` in the server's environment, that whole file passed (253 passed). I did NOT re-run the whole suite after this; the full-suite line below stays "1 failed".
- First full-suite attempt ended at collection (16 errors: `boto3`, `cryptography`, `psycopg` missing) because I first ran `uv sync --locked` without extras. Kept as `full-pytest-attempt1-missing-extras.log`. I then ran `uv sync --locked --all-extras --group test` and re-ran. **Stage mutants and banner mutants ran in the first (extras-missing) environment** and were not repeated; their tests do not import those packages, and both runs ended with all mutants good.
- Skip in the full run: 1 (`tests/contracts/test_llm.py:95`, Stubber); `HADAVIN_TEST_VAULT_ADDR` was not set, and the log shows no other skip.
- The brief asked for a test "no module keeps its own loopback list". **No test with that purpose exists at this head** (searched `tests/` for loopback, "own list", the three new test files, `test_stage_names.py`). Not run; nothing to run on old code.
- Postgres: port 54871 was already in use by another runner's server; I did not touch it and used my own on 57213 (`/home/user/build/er-pdbanner-pg`, started and stopped by me).
- Heavy jobs queued about 35 minutes behind priority-1 jobs before starting.
- Fail-before ran with `PYTHONPATH` = old `src` (checked: `hadavin_sdk.__file__` printed the old worktree path).
- Not checked: gitleaks only over `origin/main..HEAD`; CodeQL, SonarCloud, CodeRabbit not run (CI only); the page script was run under node with a stand-in page object, not a real browser.

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own PG, `HADAVIN_TEST_PG_DSN`) | 1 | `1 failed, 10570 passed, 1 skipped, 28 deselected in 251.70s (0:04:11)` |
| 1b dblink file re-run (server env fixed) | `pytest tests/demo_askdata/test_validate_harm.py` | 0 | `253 passed in 23.21s` |
| 1c the 3 new test files, `HADAVIN_REQUIRE_NODE=1` | `pytest tests/test_mode_banner.py tests/test_demo_only_guard.py tests/test_demo_only_guard_ci.py` | 0 | `47 passed in 1.80s` (18 + 28 + 1) |
| 2 Stage mutants | `heavy.sh python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 3 Banner mutants | `heavy.sh python tests/banner_mutants.py` | 0 | `28 of 28 good; problems: []` (27 `KILLED`, 1 `CRASH` = B1 "an unknown stage is accepted", marked as an allowed crash) |
| 4a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b ruff format | `ruff format --check src tests demos tools` | 0 | `324 files already formatted` |
| 4c bandit | `bandit -q -r src demos tools -ll` | 0 | only the warning "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" |
| 4d scan_repo | `python tools/scan_repo.py` | 0 | no output apart from a uv deprecation warning |
| 4e gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts origin/main..HEAD` | 0 | `no leaks found` |

## 5 Fail-before (old code 2a8c2aac src, new test files copied in)
New test files: `test_mode_banner.py` (18 tests), `test_demo_only_guard.py` (28), `test_demo_only_guard_ci.py` (1), plus `tests/mode_banner_probe.js`. Command: `pytest --continue-on-collection-errors` of the three files.
- `test_mode_banner.py`: collection error `ImportError: cannot import name 'mode_banner' from 'hadavin_sdk'` (18 tests not run).
- `test_demo_only_guard.py`: collection error `ImportError: cannot import name 'demo_only_guard' from 'tools'` (28 tests not run).
- `test_demo_only_guard_ci.py`: 1 test, FAILED (`'run: python tools/demo_only_guard.py'` not in old `ci.yml`).
- Line: `1 failed, 2 errors`. On the head the same 47 tests pass.
- Test "no module keeps its own loopback list": does not exist (see deviations).

## 6 Hostile probes (scripts in `/home/user/build/er-pdbanner-tmp/probes/`, raw output `probe-a..d.log`)
**6a banner_for, 40 inputs.** Refused (raised): mode `dev`, empty, None, a list, `DEMO`, `"demo "`, a Cyrillic look-alike `dеmo`; a bare string, bytes, int or None as a service list; names holding newline, CR, NUL, ESC, `<script>`, a quote, a trailing newline, an empty entry, 41 characters, non-ASCII letters, full-width digits, a right-to-left override, a zero-width space; `names` mapping to `<b>`, to an int, or to text with a newline. Accepted: empty lists (demo: tone `demo`, made-up text plus "No real service is connected."; pilot and prod: tone `quiet`, "No real service is connected."), a 40-character name, 10000 names in the real list (tone `real`, all named, order kept) or the stand-in list, a generator, **a dict passed as the list (its keys are read)**, a service listed as both real and stand-in (shown as real only), two keys mapped to one shown name (shown once). Count of banners that said "made-up" while a real service was listed: **0 of 40**. In prod with only a stand-in listed, the banner is tone `quiet` and the stand-in line is empty (the stand-in is in the `stand_ins` field only).
**6b demo_only_guard, 17 made-up trees** (exit; matched text printed?): clean with fake ids in the folder at the root 0; folder inside `src` 1; product file naming the folder 1 (`src/a.py:1: names-demo-only-folder`); fake-id pattern in a string 1 (`fake-record-id`, id not printed); BOM file 1; CRLF file 1 (right line, 3); ~48 MB file 1 (line 8000001); missing product root 1; `.bin` fake id not scanned plus an invalid-UTF-8 `.py` naming the folder 1 (both `.py` files hit); `--require` with folder missing 2; `--require` with folder present 0; stale loader 1; loader naming the folder 0; folder name inside `__pycache__` 0; upper-case `DEMO_ONLY` 0; symlink loop dir 0. **Symlinks: a symlinked `.py` file and a symlinked directory that both name the folder gave exit 0 (symlinks are not scanned).** In all 17 runs the planted fake id and the planted word were never printed.
**6c --without-folder, 3 made-up trees**: test needing nothing from the folder, exit 0 (`1 passed`, and the copy had no `demo_only`, `.git` or `.venv`); test reading a file inside the folder, exit 1 (`1 failed`); pytest args `-k nomatch`, exit 5. The original tree kept its folder in all three.
**6d page script under node, 15 objects** (null, undefined, array, empty object, number, string, missing tone, bad tone, missing text, text of 601 characters, non-string standins, tone as array, markup in tag/text/standins/mode, markup only in real names, non-string mode, object with a throwing getter): every non-usable object painted the "UNCONFIRMED" line; markup strings were painted as text through `textContent` on `span`/`div` only; calls to `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `append`, `prepend`, `document.write`: **0 across all cases**. The object with a throwing getter made `paint` throw (`boom`), painting nothing. A banner object that is internally inconsistent but well formed (tone `real` with the made-up sentence) was painted as given (the page script does not cross-check).

## Cleanup
My Postgres stopped (verified `server stopped`); no other process of mine is running. Worktrees left in place for the lead: `/home/user/build/ER-pdbanner` (clean), `/home/user/build/ER-pdbanner-old` (old sha, with the 4 copied test files untracked).
R-numbers: none cited (bible folder not present in this repository).
