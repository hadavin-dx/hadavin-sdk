# Note for PR #71 (pglast guard test)

What the guard `tests/test_no_pglast_in_runtime.py` checks (pglast is GPL, so it may only be in the `test` group):

Scanned:
- Python files under `src`, `demos` and `tools`: `.py`, `.pyi`, `.pyw` and suffix-less files whose first line is a python shebang. Flagged: imports of `pglast` or `_pglast` (including `from . import pglast`), and string literals that are exactly a pglast module name. A byte order mark is allowed.
- Folders named like pglast (`pglast`, `pglast.libs`, `pglast-8.7.dist-info`, `_pglast`; not `pglastic` or `pglast_utils`) and packed copies by name (`.whl`, `.egg`, `.zip`, `.tar.gz`, `.tgz`, `.a`). ANY compiled file (`.so`, `.pyd`, `.dylib`, `.dll`, also `.so.1` style versions, any letter case) under the three trees fails with "compiled <name>", whatever its name.
- `pyproject.toml`: runtime dependencies, optional extras, every dependency group except `test` (include-group resolved, group names compared in normalised form; two names that collide after normalising are reported), `tool.uv` dev/constraint/override lists and `tool.uv.sources`. Dependency names are cut at any whitespace, `;`, `[`, a comparison sign, `@` or `(`.
- `uv.lock`: the file must exist. For every package except pglast itself: its `dependencies`, each `optional-dependencies` extra, each `dev-dependencies` group, `metadata.requires-dist`, and each `metadata.requires-dev` group. The `test` group is skipped only for the project's own package (the project may use pglast for tests); a `test` group of any other package is checked.

Not scanned (deliberate: the repository has no `requirements*.txt`, `setup.py` or Dockerfile today, so a check would test nothing; add one in the same PR if such a file appears):
- `requirements*.txt`, `setup.py`, Dockerfiles, CI `pip install` lines, `[build-system] requires`, other build tools' tables (hatch, poetry, pdm).
- Code built at run time (`"pg" + "last"`, `f"pglast.{x}"`), copies under another name, `.pyc`, `.pyx`, code behind a symbolic link with another name.
- Top-level `.venv` and `node_modules` under a tree are skipped on purpose; this is a bypass (pglast placed there is not seen).

Counts: 58 planted cases (`MUTANTS`) plus 4 other tests, 62 tests in the file. Before the first fix commit (f0de7b75) it was 35 cases (counted from the code), then 46 (11 added), now 58 (12 added).
Fail-before: the new cases were run against the guard code of f0de7b75 with all 62 tests of that mixed file executed: 22 failed, 40 passed (raw: /home/user/build/PD-P0a-FIX2-failbefore-raw.txt). Of the 22, 9 are new cases and 13 are old cases whose expected message changed ("vendored X" became "compiled X"; "vendored dir" now names the folder). The 3 new negative controls pass on both. The repository's mutant tools do not cover this file; each planted case is its own mutant.
