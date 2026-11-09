# Lint and static-check tools

This page lists every automatic check the repository runs beyond the unit tests, why each one is there, the exact version, its licence, how many problems it found on `main` before this change, and the proof that it turns red when a rule is broken. Facts were read on 2026-11-07.

## What runs where

| Check | Where it runs | Gate? |
|---|---|---|
| `ruff check`, `ruff format --check` | job `check` | yes (unchanged name) |
| `bandit -ll`, `pip-audit`, zizmor | job `security` | yes (unchanged name) |
| mypy, the mypy ratchet, import-linter, deptry, vulture, the whitelist check, the licence check, the ruff-version check, actionlint | new job `lint-set` | not yet a required check: making it required is a repository setting, which only the owner changes |
| ruff (check and format) on commit | `.pre-commit-config.yaml` | local only |

CI never pushes a commit. The pre-commit hook may fix files on your machine (`ruff check --fix`, `ruff format`); CI only reports. A service such as autofix.ci would let CI push fixes back to a pull request. It is an option for the owner and is not enabled.

Run the set locally (after `uv sync --all-extras --group test --group lint`):

```
ruff check && ruff format --check
mypy
python tools/mypy_ratchet.py
PYTHONPATH=demos/ask-your-data lint-imports
deptry .
vulture
python tools/vulture_whitelist_check.py
actionlint -shellcheck=
# licences: uv export --locked --all-extras --group test --group lint --no-hashes --no-emit-project > /tmp/locked.txt
#           python tools/licence_check.py /tmp/locked.txt tools/licence_exceptions.txt
```

## Tool table

SPDX is read from the first lines of the upstream LICENSE file on the default branch (raw text saved in `handover/evidence/cilint/licences-raw.txt`), and compared with the package index metadata.

| Tool | Version (release date) | SPDX read from LICENSE | First LICENSE line | Pin | Findings on `main` | Fail-before proof |
|---|---|---|---|---|---|---|
| ruff | 0.17.1 (2026-10-15) | MIT | "MIT License" | exact in `pyproject.toml`, hashes in `uv.lock` | wide rule set: 574 on src, tests, demos and tools together with the wide set, counted before the fixes (see below) | planted unused import: F401, exit 1 |
| mypy | 2.4.1 (2026-10-28) | MIT | "Mypy (and mypyc) are licensed under the terms of the MIT license" | exact, hashes in `uv.lock` | 96 on `src` (33 files, measured before the stubs were installed; 15 of them were `import-untyped`); 79 in 28 files once the stubs are installed (the same 79 on `main`'s `src`, checked); 284 on everything (also before the stubs) | planted wrong type: `[assignment]`, exit 1; ratchet: a clean module listed, and a missing module listed, both exit 1 |
| import-linter | 2.15 (2026-09-04) | BSD-2-Clause | "BSD 2-Clause License" | exact, hashes in `uv.lock` | 0 (contracts written to pass on `main`) | three planted imports, each broke the matching contract, exit 1 |
| deptry | 0.25.1 (2026-03-18) | MIT | "MIT License" | exact, hashes in `uv.lock` | 396 with default settings; 0 after configuration and one missing pin (botocore) | planted `import requests`: DEP003, exit 1 |
| vulture | 2.16 (2026-03-25) | MIT | "The MIT License (MIT)" | exact, hashes in `uv.lock` | 221 raw (136 in `src`); 0 after fixes and `vulture_whitelist.py` | planted unused function: exit 3; whitelist check: a gone name and a duplicate line, both exit 1 |
| actionlint | 1.7.12 (2026-03-31) | MIT | "the MIT License" | release download checked against a SHA-256 in `ci.yml` | 0 | planted `github.evnt_name`: `[expression]`, exit 1 |
| zizmor | 1.31.1 pinned (2026-10-15); 1.32.0 also run | MIT | "The MIT License (MIT)" | exact, in the `scan` group | 0 findings on `main` and on the branch | already a gate on `main`; not re-proved here |
| pre-commit | 4.7.0 (2026-10-12) | MIT (licence text read; no SPDX line in the file) | "Copyright (c) 2014 pre-commit dev team" | run with `uvx --from pre-commit==4.7.0` | not a checker | n/a |
| ruff-pre-commit | v0.17.1, commit 38bfb07c0c64c304f47eb52090f8288150c77730 | MIT and Apache-2.0 (two files, read at the pinned commit) | "MIT License" (LICENSE-MIT) and "Apache License, Version 2.0" (LICENSE-APACHE) | full commit hash in `.pre-commit-config.yaml`; CI checks its version equals the ruff pin | n/a | hook run once: both hooks passed |
| types-pyyaml | 6.0.12.20261030 (2026-10-30) | Apache-2.0 (typeshed LICENSE, package index) | "The "typeshed" project is licensed under the terms of the Apache license" | exact | type stubs only | n/a |
| boto3-stubs, botocore-stubs | 1.43.122 (2026-10-29) | MIT | "MIT License" (mypy_boto3_builder) | exact; the newest release was too young for the 7-day wait | type stubs only | n/a |

Not used, and why:
- **pyright 1.1.414** (MIT; the newest release on 2026-11-07 on both PyPI and npm) was trialled against mypy on `main` in basic mode: 113 errors on `src` (587 on everything) against 96 (284). mypy was chosen because it has fewer findings to clear, its pydantic plugin understands the settings models, and the stubs for boto3 are built for it. The first trial's raw files were not kept; it was repeated on 2026-11-09 on `main` 0dabf1f with the stub packages installed and mypy without the pydantic plugin: pyright 117 errors, mypy 85 (the earlier 113 and 96 were counted before the stubs were installed, so the two sets are not the same measurement; the order, mypy with fewer, is unchanged). Raw outputs: `handover/evidence/cilint/pyright-trial-src.txt`, `handover/evidence/cilint/mypy-trial-src.txt` (src only; the 587 and 284 figures for everything were not repeated).
- **shellcheck** and **yamllint** are GPL-3.0 and are not used. actionlint calls shellcheck when it finds it, so CI passes `-shellcheck=` to switch that off.
- **lychee** and **ast-grep** were not added (no trial was run; see "Not verified"). If ast-grep is added later it must be 0.50.0 or newer, because 0.49 and older have two published advisories.
- **semgrep** (LGPL-2.1) stays as it was.

## Licences of the locked package set

`tools/licence_check.py` (a CI step) reads the metadata of every package in the locked set (the `uv export` output, with exact versions) and fails when:
- a declared licence matches the copyleft pattern: GPL, LGPL, AGPL in any spelling (GPLv3, GPL-2.0-or-later, LGPL-2.1+, AGPLv3), "GNU", "Affero", "Lesser General Public", "General Public License", SSPL, EUPL, and SPDX `WITH` forms (the whole `License` value is scanned, however long). `tests/test_licence_check.py` holds the spelling table (21 copyleft spellings, 13 permissive ones that must pass) and the failure cases;
- a package is not installed and not listed as `unchecked` (a wrong environment or a partial sync fails on every package);
- a package has no licence field, or the installed version differs from the lock;
- an exception in `tools/licence_exceptions.txt` is stale (package gone, version changed, no longer needed).

Result on 2026-11-07 (raw: `handover/evidence/cilint/licence-scan.txt`, re-run on the final head of the batch-3 fixes): 92 packages read, 3 copyleft, 3 skipped by platform marker (colorama BSD, tzdata Apache-2.0, httpx2-jsfetch BSD-3-Clause; licences read by hand from the package index and entered as `unchecked`). The 3 copyleft packages are already on `main`; their `allow` lines were NOT approved by the owner and await his written decision (studio rule: a non-permissive licence needs it before use in a client deliverable):
- pglast 8.7: GPL-3.0-or-later. `test` group only; never imported by `src/`.
- psycopg 3.3.6 and psycopg-binary 3.3.6: LGPL-3.0-only. Runtime extras `pg` and `askdata`; intended to stay an unmodified, separate dependency (not verified).
Options for the owner: (a) accept the LGPL driver in writing as an unmodified separate dependency; (b) a permissive driver behind the store kind; (c) drop pglast from the test group.

Weak copyleft, not caught by the check: pathspec 1.1.1 (a dependency of mypy, development only) and certifi 2026.10.19 (a dependency of the HTTP stack; shipped with the runtime extras that use it) are both MPL-2.0 (file-level copyleft).

Newly locked by this branch, from each package's own metadata: ast-serialize 0.13.1 MIT; boto3-stubs 1.43.122 MIT; botocore-stubs 1.43.122 MIT; click 8.5.1 BSD-3-Clause; deptry 0.25.1 MIT; grimp 3.19 BSD-2-Clause; import-linter 2.15 BSD-2-Clause; librt 0.16.0 MIT; mypy 2.4.1 MIT; mypy-extensions 1.2.0 MIT; pathspec 1.1.1 MPL-2.0; requirements-parser 0.13.1 Apache-2.0; types-pyyaml 6.0.12.20261030 Apache-2.0; types-s3transfer 0.19.3 MIT; vulture 2.16 MIT. The check reads declared metadata only (PEP 639 `License-File` entries are not cross-checked), which a package can get wrong; licence texts were not read.

`uv.lock` was written with uv 0.13.6 (the version CI installs). A different uv (0.11.32 was tried) rewrites the lock format.

## The wide ruff rule set

`select` now has: E4, E7, E9, F (ruff's own default, restated), W (0 findings), I, B, DTZ, S, TID, UP and, new in this branch, C4, SIM, PERF, ASYNC, RET, PIE, LOG, FURB, PGH, RSE, SLOT, FLY, YTT, PLE, PLW, PLC and RUF100. Every finding was fixed in the code. No `noqa` was added; the `# noqa` comments that RUF100 found to do nothing were removed (their reason text stays as a plain comment). An earlier version of this branch dropped E4/E7/E9 by mistake (it replaced ruff's default); a review caught it, and restoring them found 5 findings (3 lambda assignments, 2 ambiguous names), fixed in tests.

`select` is used, not `extend-select`: with `extend-select` ruff 0.17.1 reported 0 findings for RUF100 on this tree while an explicit `select` reported 158 (66 once the other rules were counted). That was checked, not assumed.

No rule is switched off for the whole repository. Three selected rules are exempted by file name in `[tool.ruff.lint.per-file-ignores]` (a rule setting, not a `noqa`), each with its reason in `pyproject.toml`:
- **PLC0415** (import not at top of file): all of `tests/**` (430 findings; tests import inside the test so one broken module fails one test), and 9 files in `src/` plus 4 in the demo (27 findings) where the lazy import is the design: optional extras, platform modules, the command line, and cycle breaking.
- **S603** (subprocess call): `tools/mypy_ratchet.py` only. It runs mypy with a fixed argv and cannot import mypy (deptry would read that as a dev dependency in shipped code).
- **SIM112** (environment variable names in capitals): `tools/mutation_runner.py` and its test set `SystemRoot` on purpose, which is the real Windows name.

The wide noisy families (for example ANN, D, PLR, C90, PTH, T20, ERA, FBT, TRY, EM, G, N, COM) are not on.

Tests, demos and tools are checked by ruff with the same set (0 findings). They are not checked by mypy or vulture (see ledger rows).

## Import contracts

Six contracts in `pyproject.toml` (the root packages are `hadavin_sdk` and `askdata`), all kept:
1. Packages that must stay free of secrets never reach a secret holder, directly or through other modules.
2. `tools` never reaches `actions`.
3. `stages` imports nothing else of the package.
4. Vendor cloud SDKs (boto3, botocore, anthropic, google, azure, kubernetes) are imported only in their own kind module (18 allowed imports listed).
5. The core never imports a demo.
6. A demo never reaches the executor or a secret holder.

The repository test `tests/test_lockin_guard.py` is kept. Contract 4 repeats its import table, but the test also checks that every vendor module is a registered kind and that no dynamic import slips through, which a contract cannot see. So the contract adds a second, independent check and replaces nothing. "Demos never import core internals" was not written as such: no list of what is public exists, and demos use `config`, `models`, `llm`, `audit` and `store` modules directly. Contract 6 is the narrower rule that can be stated today. Contract 6 needs `PYTHONPATH=demos/ask-your-data` so that the demo package can be found.

## Fail-before proofs

Each proof was run on a throwaway copy of the tree, one planted problem at a time, with no test run going on the same tree. Raw output: `handover/evidence/cilint/fail-before-proofs.txt` and `handover/evidence/cilint/fail-before-proofs-2.txt` (round 2 adds PLW, SIM, RUF100 and E722 plants, the mypy ratchet, the whitelist check, the ruff-version check and the licence check). The first actionlint plant turned red for a different reason than planned (a duplicated key), so it was redone with a misspelled context name; both are recorded.

## The mypy rollout list

28 modules (79 findings) are listed under `[[tool.mypy.overrides]] ignore_errors = true`. They are still read, so their types help the clean files; only their own findings are not reported. `python tools/mypy_ratchet.py` runs mypy without that override (the TOML is parsed; every override block is removed) and compares per file with `tools/mypy_baseline.json`: it fails when a listed module is missing or clean, has more findings than its baseline (growth) or fewer (lower the baseline with `--write`), or when an unlisted module has a finding. The list can only shrink and no listed file can get worse. The list is ordered by risk, highest first: redaction, approvals, executor and tool boxes; then the audit trail, signers and database; then configuration and wiring; last the two files blocked by the boto3 stubs (the stubs give `client()` one overload per service name, and a non-literal name fails). Fixing the first group needs its own review round (money and redaction paths), which is why it was not done inside a lint change.

Why 96 and 79: the trial on `main` (96) ran before the stub packages were installed; 15 of its errors were `import-untyped` (boto3, botocore, yaml). With the stubs installed, `main`'s `src/` gives 79 in 28 files, and so does this branch (no mypy finding was fixed in code here; the code edits were for ruff). The other 2 of the 17 only appear without the stubs (not traced one by one).

## Vulture whitelist

81 entries, each `name  # kind in file`. vulture matches by bare name, so an entry hides that name in every file; `tools/vulture_whitelist_check.py` ties each entry to the file(s) it names (the file must still DEFINE the name, read with `ast`; a mention in a comment does not count) and fails on a stale or duplicate entry. Three entries are kept on purpose and are not in use: `gate._rendered` (with `_views`, which vulture does not flag because `runmap.py` defines and calls its own `_views` and vulture matches by bare name; `_ANSI_AS_TEXT`, `_RENDERED_MARKUP`, restored after review) is the unfinished fix for the open card-text redaction hole (ticket P1d; base commit 0dabf1f, file `src/hadavin_sdk/approvals/gate.py`); `tools.START_MARKER` and `tools.MIN_REDACTION_WINDOW` are public module names. Names used only by tests, demos or tools count as dead code if nothing in `src/` uses them, unless whitelisted with a reason.

## Not verified

- The GitHub Actions run itself (this was run locally on Linux only).
- `bandit -ll` was run on `tools/` once locally (rc 0, no finding); it is not a CI step for that folder.
- The macOS and Windows runners.
- Licence texts (only declared metadata was read) and the wheel contents of the wrapper packages.
- lychee and ast-grep (not trialled).
- `stage_mutants` and the perf tests at the final head (queued). The full test suite on Python 3.13 and 3.12 and the lint-set commands are recorded in `handover/evidence/cilint/gates.txt`.
- Whether `lint-set` should be a required check (owner decision).
