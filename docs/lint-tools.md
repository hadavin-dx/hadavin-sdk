# Lint and static-check tools

This page lists every automatic check the repository runs beyond the unit tests, why each one is there, the exact version, its licence, how many problems it found on `main` before this change, and the proof that it turns red when a rule is broken. Facts were read on 2026-11-07.

## What runs where

| Check | Where it runs | Gate? |
|---|---|---|
| `ruff check`, `ruff format --check` | job `check` | yes (unchanged name) |
| `bandit -ll`, `pip-audit`, zizmor | job `security` | yes (unchanged name) |
| mypy, import-linter, deptry, vulture, actionlint | new job `lint-set` | not yet a required check: making it required is a repository setting, which only the owner changes |
| ruff (check and format) on commit | `.pre-commit-config.yaml` | local only |

CI never pushes a commit. The pre-commit hook may fix files on your machine (`ruff check --fix`, `ruff format`); CI only reports. A service such as autofix.ci would let CI push fixes back to a pull request. It is an option for the owner and is not enabled.

Run the set locally (after `uv sync --all-extras --group test --group lint`):

```
ruff check && ruff format --check
mypy
PYTHONPATH=demos/ask-your-data lint-imports
deptry .
vulture
actionlint -shellcheck=
```

## Tool table

SPDX is read from the first lines of the upstream LICENSE file on the default branch (raw text saved in the evidence folder, `licences-raw.txt`), and compared with the package index metadata.

| Tool | Version (release date) | SPDX read from LICENSE | First LICENSE line | Pin | Findings on `main` | Fail-before proof |
|---|---|---|---|---|---|---|
| ruff | 0.17.1 (2026-10-15) | MIT | "MIT License" | exact in `pyproject.toml`, hashes in `uv.lock` | wide rule set: 574 on src, tests, demos and tools together (see below) | planted unused import: F401, exit 1 |
| mypy | 2.4.1 (2026-10-28) | MIT | "Mypy (and mypyc) are licensed under the terms of the MIT license" | exact, hashes in `uv.lock` | 96 on `src` (33 files); 284 on everything | planted wrong type: `[assignment]`, exit 1 |
| import-linter | 2.15 (2026-09-04) | BSD-2-Clause | "BSD 2-Clause License" | exact, hashes in `uv.lock` | 0 (contracts written to pass on `main`) | three planted imports, each broke the matching contract, exit 1 |
| deptry | 0.25.1 (2026-03-18) | MIT | "MIT License" | exact, hashes in `uv.lock` | 396 with default settings; 0 after configuration and one missing pin (botocore) | planted `import requests`: DEP003, exit 1 |
| vulture | 2.16 (2026-03-25) | MIT | "The MIT License (MIT)" | exact, hashes in `uv.lock` | 221 raw (136 in `src`); 0 after fixes and `vulture_whitelist.py` | planted unused function: exit 3 |
| actionlint | 1.7.12 (2026-03-31) | MIT | "the MIT License" | release download checked against a SHA-256 in `ci.yml` | 0 | planted `github.evnt_name`: `[expression]`, exit 1 |
| zizmor | 1.31.1 pinned (2026-10-15); 1.32.0 also run | MIT | "The MIT License (MIT)" | exact, in the `scan` group | 0 findings on `main` and on the branch | already a gate on `main`; not re-proved here |
| pre-commit | 4.7.0 (2026-10-12) | MIT (licence text read; no SPDX line in the file) | "Copyright (c) 2014 pre-commit dev team" | run with `uvx --from pre-commit==4.7.0` | not a checker | n/a |
| ruff-pre-commit | v0.17.1, commit pinned by full hash | not read: the raw LICENSE URL returned 404 | not read | full commit hash in `.pre-commit-config.yaml` | n/a | n/a |
| types-pyyaml | 6.0.12.20261030 (2026-10-30) | Apache-2.0 (typeshed LICENSE, package index) | "The "typeshed" project is licensed under the terms of the Apache license" | exact | type stubs only | n/a |
| boto3-stubs, botocore-stubs | 1.43.122 (2026-10-29) | MIT | "MIT License" (mypy_boto3_builder) | exact; the newest release was too young for the 7-day wait | type stubs only | n/a |

Not used, and why:
- **pyright 1.1.414** (MIT) was trialled against mypy on `main` in basic mode: 113 errors on `src` (587 on everything) against 96 (284). mypy was chosen because it has fewer findings to clear, its pydantic plugin understands the settings models, and the stubs for boto3 are built for it. Raw outputs: `pyright-trial-*.txt`, `mypy-trial-*.txt`.
- **shellcheck** and **yamllint** are GPL-3.0 and are not used. actionlint calls shellcheck when it finds it, so CI passes `-shellcheck=` to switch that off.
- **lychee** and **ast-grep** were not added (no trial was run; see "Not verified"). If ast-grep is added later it must be 0.50.0 or newer, because 0.49 and older have two published advisories.
- **semgrep** (LGPL-2.1) stays as it was.

## The wide ruff rule set

`select` now has: E4, E7, E9, F, W, I, B, C4, SIM, PERF, ASYNC, RET, PIE, LOG, FURB, PGH, RSE, SLOT, FLY, YTT, PLE, PLW, PLC, RUF100 and the rules that were already on. Every finding was fixed in the code. No `noqa` and no per-file ignore was added; the `# noqa` comments that RUF100 found to do nothing were removed (their reason text stays as a plain comment).

`select` is used, not `extend-select`: with `extend-select` ruff 0.17.1 reported 0 findings for RUF100 on this tree while an explicit `select` reported 158 (66 once the other rules were counted). That was checked, not assumed.

Rules left off, with the reason:
- **PLC0415** (import not at top of file): lazy imports are the design here (optional vendor SDKs fail at start with an install hint). 19 in `src`, 430 in `tests`.
- **SIM112** (environment variable names in capitals): tests set `SystemRoot` on purpose, which is the real Windows name; changing the case breaks them.
- The wide noisy families (for example ANN, D, PLR, C90, PTH, S, T20, ERA, FBT, TRY, EM, G, N, COM, DTZ) are not on.

Tests, demos and tools are checked by ruff with the same set (0 findings). They are not checked by mypy or vulture (see ledger rows).

## Import contracts

Six contracts in `pyproject.toml`, all kept:
1. Packages that must stay free of secrets never reach a secret holder, directly or through other modules.
2. `tools` never reaches `actions`.
3. `stages` imports nothing else of the package.
4. Vendor cloud SDKs (boto3, botocore, anthropic, google, azure, kubernetes) are imported only in their own kind module (18 allowed imports listed).
5. The core never imports a demo.
6. A demo never reaches the executor or a secret holder.

The repository test `tests/test_lockin_guard.py` is kept. Contract 4 repeats its import table, but the test also checks that every vendor module is a registered kind and that no dynamic import slips through, which a contract cannot see. So the contract adds a second, independent check and replaces nothing. "Demos never import core internals" was not written as such: no list of what is public exists, and demos use `config`, `models`, `llm`, `audit` and `store` modules directly. Contract 6 is the narrower rule that can be stated today. Contract 6 needs `PYTHONPATH=demos/ask-your-data` so that the demo package can be found.

## Fail-before proofs

Each proof was run on a throwaway copy of the tree, one planted problem at a time, with no test run going on the same tree. Raw output: `fail-before-proofs.txt` in the evidence folder. The first actionlint plant turned red for a different reason than planned (a duplicated key), so it was redone with a misspelled context name; both are recorded.

## Not verified

- The GitHub Actions run itself (this was run locally on Linux only).
- Python 3.13 and the macOS and Windows runners.
- The licences of the tools' own dependencies, the wheel contents of the wrapper packages, and the ruff-pre-commit LICENSE.
- lychee and ast-grep.
- Whether `lint-set` should be a required check (owner decision).
