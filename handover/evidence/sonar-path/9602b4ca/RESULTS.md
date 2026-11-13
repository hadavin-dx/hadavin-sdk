# Evidence: SONAR-PATH round 3, head 9602b4ca300b17fdbd3673378ab797f8e36cda62

Evidence runner record. Records only, no judgement. Raw logs: `/home/user/build/evidence-raw/sonarpath-9602b4ca/`.
Worktree: `/home/user/build/ER-sonarpath-b3` (detached at the head, `git rev-parse HEAD` matched, status clean at start and at end). Own venvs (3.13 and 3.12). `hadavin_sdk.__file__` printed inside the worktree for every run (3.13, 3.12, probes, and each fail-before worktree).
Environment names present at start and unset for every run (values never printed): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_CA_BUNDLE`, `GH_TOKEN`, `GITHUB_TOKEN`, `ANTHROPIC_BASE_URL`. (`tests/conftest.py` itself sets fake AWS keys built from parts; that is the repo's own behaviour.)

## 1. Not run and deviations
- Not run, by order: full pytest, Playwright, the full pathguard and stage mutant tables on the laptop, `tests/stage_mutants.py`.
- Focused test file list was chosen by a grep (73 files: `focused-files.txt`), minus `fixtures/`, `*_mutants.py`, `*_support.py`, `contracts/kinds`. 64 test files ran per interpreter; a test file that imports the converted modules only indirectly is not in the list.
- Postgres tests were skipped (no `HADAVIN_TEST_PG_DSN`, no database here). Skips are in `skips-313.txt`.
- Item 3 sample: the changed-or-added rows (83 added, 12 changed since e29cc269, by comparing the `Mutant` objects of both files) leave only 35 other rows, fewer than 60, so the "60-row sample" is all 35 and **all 130 rows ran** (seed 10 was irrelevant). Driver `mdrive.py` (own wrapper around `tools.mutation_runner.run_mutants`, because the repo script filters only by name text).
- Item 4: `ddf1d584` is NOT an ancestor of 9602b4ca or e29cc269 (it sits on an older lineage: parent `b096ad48`). It was tested as given. `git log 81a5aadb..HEAD` is 4 commits: 445dfcae, 5755b3c3, e29cc269, 9602b4ca. `origin/main` is now 51c9fc4f; the merge base with HEAD is 81a5aadb.
- Item 5 (c) CLI: driven through `cli.main` with `HADAVIN_DEBUG=1`; no case reached exit 3, so no traceback was printed to check (exit 2 messages only). Not checked: exit 3 paths.
- Scratch probe scripts are in the scratchpad (`probe_a.py`, `probe_b.py`, `probe_cfg.py`, `probe_c.py`); outputs are in the raw folder (`probe-a.txt`, `probe-b.txt`, `probe_cfg.txt`, `probe_c.txt`).
- `probe_b` section "config golden/inputs" first run was spoiled by my own script (stripped `inputs_dir` too); the corrected run is `probe_cfg.txt`.

## 2. Results table
| Item | Command (short) | Exit | Last line |
|---|---|---|---|
| 1a pathguard tests, py3.13 | `pytest tests/test_pathguard*.py` | 0 | 254 passed in 4.29s |
| 1b focused set, py3.13 | `pytest <64 files>` | 0 | 7544 passed, 25 skipped in 130.76s |
| 1c focused set, py3.12 | same, 3.12 venv | 0 | 7544 passed, 25 skipped in 139.17s |
| 2a ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b ruff format | `ruff format --check src tests demos tools` | 0 | 332 files already formatted |
| 2c bandit | `bandit -q -r src demos tools -ll` (global install, not in the venv) | 0 | only warnings: `nosec encountered (B102), but no failed test` at src/hadavin_sdk/tools.py:389 and two "Test in comment" warnings |
| 2d gitleaks | `gitleaks git --redact ... --log-opts origin/main..HEAD` | 0 | no leaks found (scanned ~253 KB, 4 commits) |
| 3 mutants | 130 rows in 3 slices | 0 | 130 rows, 130 good: 115 KILLED, 15 CRASH (every CRASH row is allowed by its declared `allow_crash`/`crash_type`) |
| 3 after | `git status`, `git diff` | - | both empty at HEAD |
| 4 fail-before | see section 4 | - | see section 4 |
| 5 probes | see section 5 | - | see section 5 |

Skips (3.13, 25 in all): 24 need the postgres DSN, 1 is a stubber test (`skips-313.txt`).

### Suppression markers (counts of the text in src / tests; list only)
| marker | origin/main (51c9fc4f) | 81a5aadb (merge base) | HEAD |
|---|---|---|---|
| NOSONAR | 5 / 0 | 5 / 0 | 0 / 0 |
| noqa | 72 / 85 | 72 / 85 | 72 / 85 |
| type: ignore | 5 / 6 | 5 / 6 | 5 / 6 |
| fmt: skip | 1 / 59 | 1 / 59 | 1 / 56 |
| nosec | 6 / 0 | 6 / 0 | 6 / 0 |

## 3. Mutants
All 130 rows (83 added + 12 changed since e29cc269 + 35 unchanged) ran in 3 slices (`mut-slice-0.log`, `-45`, `-90`; plus a 6-row smoke `mut-slice-00.log`). Every row: verdict, killing test name. Verdicts: 115 KILLED, 15 CRASH counted good by the runner. The 15 CRASH rows: R10b, S-bundles load_bundles, S-score _check_layout, S-replay outputs_files, S-signer private key, X7, X8, S-replay marker error, S-causelist chain (bad JSON), S-signer key_path makes the folder first, S-local_dir reconcile, S-judge qualify, S-signer public key, S-vault jwt path, S-config root. No BAD row. After the runs: git status empty, git diff empty.

## 4. Fail-before (new and changed test files of 9602b4ca copied into the old tree; same venv, PYTHONPATH on the old src; raw: `fb-*`, `fb-all-results.txt`)
Files copied: the 8 test files below, `tests/pathguard_mutants.py`, and the 3 fixtures. Counts are pass/fail per file (collection error counts as 1 failure).
| file | e29cc269 | ddf1d584 | 81a5aadb |
|---|---|---|---|
| test_pathguard_batch3 | 58 pass, 33 fail | 44 pass, 47 fail | collection error |
| test_pathguard | 48 pass, 1 fail | 48 pass, 1 fail | collection error |
| test_pathguard_sites | 34 pass, 1 fail | 10 pass, 25 fail | collection error |
| test_pathguard_tripwire | 73 pass, 1 fail | 72 pass, 2 fail | collection error |
| test_pathguard_callers | 5 pass, 0 fail | 4 pass, 1 fail | 3 pass, 2 fail |
| test_changelog_claims | collection error (StopIteration) | collection error | collection error |
| test_k1b_cli | 21 pass | 21 pass | 20 pass, 1 fail |
| test_k1b_replay | 49 pass | 49 pass | 49 pass |

Builder claim check: batch3 has 91 cases (74 new test functions, some parametrized): matches. e29cc269: 33 fail, 58 pass: matches. All 58 passing are named `test_pin_*` or `test_control_*`: matches (names in `fb-all-results.txt`). ddf1d584: 47 fail, 44 pass: matches. 81a5aadb: 5 of the 8 files fail at collection (changelog_claims, pathguard, batch3, sites, tripwire); the other three give 1 + 2 failures.
First failing line of each failing test: `fb-all-results.txt` (e.g. e29: `test_pin_r4_range_02: DID NOT RAISE PathRefused`; `AttributeError: module 'hadavin_sdk.pathguard' has no attribute 'CONTROL_RANGES'`; `operator_dir() got an unexpected keyword argument 'unusable'`; `FileExistsError` for a taken temp name; `IsADirectoryError` for a folder target; `'LocalDirSink' object has no attribute 'refused_events'`; `the error was chained to another one`).
AST count of test functions (name not in the old file, or its AST differs): vs e29cc269 new 99, changed 9; vs 81a5aadb new 188, changed 1 (`ast-counts.txt`). Note several fail on e29 because the API did not exist yet (AttributeError / TypeError), not because of a behaviour difference.
Test files that PASS on e29cc269 but are new or changed in this round: all 58 above, plus every test in test_k1b_cli, test_k1b_replay, test_pathguard_callers.

## 5. Hostile probes (answers only; raw in probe-*.txt)
(a) `atomic_write(base, name, text)`: folder target: PathRefused R13 "a folder is not replaced". Taken temp name (token forced): PathRefused R13 "the name is already in use"; the taken file left untouched, no target written. NUL, U+00AD, U+2060, U+180E, tag characters U+E0041 and U+E007F: PathRefused R4 "contains a control character". Name of 4097 chars, of 4096 chars, and 3000 two-byte chars: PathRefused R5 "too long". Symlink name (dangling and existing target): PathRefused R8 "path escapes its folder"; link target left unchanged. Slash name: R2. `..` and empty name: R1. Run folder swapped for a link after write 1 (`replay._run_dir`, `_write_json`): PathRefused R8 on the second write; the other folder stayed empty. No message contained the path.
(b) Read sites (exception type; message holds the path?):
- load_answers: symlink to a file: followed, content parsed (ConfigError about its shape); path outside base (an operator path): followed the same way; NUL: ConfigError "missing or not valid JSON"; missing: same. No path in any message.
- _recorded_digest: symlink out: returns "" (unreadable); missing: None; NUL base: ""; no exception.
- _read_json: symlink, `..`, NUL, missing: ConfigError "output file 1 is missing or not valid JSON"; no path.
- hash_files: symlink and `..`: ConfigError "path escapes its folder: <given relative name>"; NUL in name: ConfigError; missing: "not a file: <name>"; NUL root: PathRefused R4. Only the caller's relative name appears, not the base path.
- secrets_file._fetch: symlink and `..`: ConfigError "path escapes its folder: <name>"; NUL: PathRefused R4; missing: ConfigError "secret 'nope' not found in the mounted folder".
- signer: `key_path` symlink and outside: ValueError and the message DOES contain the full path (pinned wording); NUL: PathRefused R4; missing file in folder: returns the path. `load_private_key`: symlink followed (PEM error); NUL R4; missing R10 "cannot be resolved". `load_public_key`: missing R10, NUL R4.
- config: `golden_dir` as a symlink out, as `../../outside` and missing: accepted (operator setting; resolved path returned); NUL: PathRefused R4. Golden file reads via `confined`: symlink out and `..`: ConfigError "path escapes its folder: <name>"; NUL: PathRefused R4; missing file: returns the path (no error).
- causelist: symlinked services.json: ConfigError "must be a file inside the directory"; NUL dir and missing dir: "directory not found"; a folder that is a symlink to a folder: accepted; bad JSON: ConfigError, no path. 
- bundle: NUL folder name and missing folder: BundleError "folder name must look like case-001" (the NUL character is in the text); manifest symlink out: BundleError "bundle file: path escapes its folder"; bad JSON: BundleError; folder symlink: refused; manifest listing `../../outside/secret`: "files on disk and in the manifest differ"; bundles root NUL: PathRefused R4; missing: ConfigError "bundles folder does not exist".
(c) Traceback canary (the base folder name held the text CANARYPATH): in causelist and bundle probes the printed traceback text held no path; the exception objects still carry the earlier exception as `__context__` (with `from None` set, so it is not printed): e.g. `PathRefused`, `FileNotFoundError` (whose `.filename` holds a path) and `JSONDecodeError` are reachable in memory, not in the printed text. Via `cli.main` with `HADAVIN_DEBUG=1` (replay: missing, NUL, bad-JSON cause list; missing and bad-JSON bundles; score: missing outputs, missing and NUL answers, bad cause list, bad bundle, dangling-link outputs; bad `--config`): all exit 2, no case printed a path in stderr, no traceback printed. A successful replay prints the output path on stdout (the normal result line). Only `signer.key_path` messages hold a full path (above).

## Cleanup
Temp worktrees removed (ER-sonarpath-b3, ER-sp-b3-old, ER-sp-b3-ddf, ER-sp-b3-main), venvs and temp folder removed; no background process left; nothing committed or pushed.
